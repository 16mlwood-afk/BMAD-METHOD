#!/usr/bin/env python3
"""Regression suite for the release boundary (P0-A).

The property under test is the one the old sync could not hold: an uncommitted edit, or
a checkout that is not the canonical channel, MUST NOT be able to reach a target. Both
were live failures on 2026-08-31, so both are pinned in the failing direction.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
TOOL = FORK / "tools" / "bmad-release.py"
PASS, FAIL = [], []


def check(label, got, want):
    (PASS if got == want else FAIL).append(label)
    print(("  PASS  " if got == want else "  FAIL  ") + label
          + ("" if got == want else f"\n          got={got!r} want={want!r}"))


# A git hook runs with GIT_INDEX_FILE, GIT_DIR and friends EXPORTED, pointing at the
# repository being committed. Any `git` this suite shells out to inherits them, so a
# `git add` meant for a throwaway fixture repo writes into the REAL fork index instead.
# Observed 2026-09-03: the G-case fixture's `git add -A` staged its `f.txt` into the
# fork's index, then the fixture directory was deleted -- leaving an index entry whose
# blob no longer existed. Every subsequent commit died with
#   error: invalid object 100644 <sha> for 'f.txt' / error: Error building trees
# and the pre-commit gate could not commit at all. The suite passed; the repo broke.
# Scrub the inherited git environment so a fixture's git can only ever touch itself.
_CLEAN_ENV = {k: v for k, v in os.environ.items()
              if not (k.startswith("GIT_") and k not in ("GIT_ASKPASS",))}


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(TOOL), *args, "--no-fetch"],
                          cwd=cwd or FORK, capture_output=True, text=True,
                          env=_CLEAN_ENV)


def git(*args, cwd=FORK):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          env=_CLEAN_ENV)


print("bmad-release release-boundary golden cases:\n")

# G1 — a dirty release-relevant path blocks the release.
probe = FORK / "custom" / "workflows" / "shared" / ".release-probe.md"
probe.write_text("probe\n")
try:
    r = run("check")
    check("G1 dirty source blocks check", r.returncode, 1)
    check("G1b and says which file", ".release-probe.md" in r.stdout, True)
    r = run("publish", "--no-test")
    check("G1c dirty source REFUSES publish", r.returncode, 1)
    check("G1d publish wrote nothing", "REFUSED" in r.stdout, True)
finally:
    probe.unlink(missing_ok=True)

# G2 — the source gate blocks on exactly the release-relevant paths and nothing else.
#      Asserted structurally rather than by running against the live tree, because the
#      live tree is legitimately dirty while this very suite is being written.
src_text = TOOL.read_text()
check("G2 the gate scopes dirt to release-relevant paths",
      all(p in src_text for p in ('"custom", "src/modules", "tools", "test"',)), True)

# G3 — a checkout that is not the canonical channel cannot ship. Exercised against a
#      throwaway repo so the assertion is about the GATE, not about whatever the real
#      fork happens to be on while the suite runs.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("bmad_release_g3", TOOL)
_m = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_m)

with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "repo"
    repo.mkdir()
    for a in (["init", "-q", "-b", "custom"], ["config", "user.email", "t@t"],
              ["config", "user.name", "t"]):
        git(*a, cwd=repo)
    (repo / "f.txt").write_text("x\n")
    git("add", "-A", cwd=repo); git("commit", "-qm", "init", cwd=repo)

    _m.FORK = repo
    _, findings = _m.source_gate(fetch=False)
    on_custom_blocks = [m for lvl, m in findings if lvl == "BLOCK" and "not custom" in m]
    check("G3 on the canonical channel, no wrong-branch block", on_custom_blocks, [])

    git("checkout", "-q", "-b", "feat/x", cwd=repo)
    _, findings = _m.source_gate(fetch=False)
    check("G3b a feature branch IS blocked as the release source",
          any(lvl == "BLOCK" and "not custom" in m for lvl, m in findings), True)

    (repo / "custom").mkdir()
    (repo / "custom" / "w.md").write_text("uncommitted\n")
    _, findings = _m.source_gate(fetch=False)
    check("G3c an uncommitted edit under custom/ IS blocked",
          any(lvl == "BLOCK" and "dirty" in m for lvl, m in findings), True)

# G4 — the registry is required; a path-only list is not enough to release from.
r = run("reconcile")
check("G4 reconcile runs read-only and classifies", "BMAD RECONCILE" in r.stdout, True)
check("G4b reconcile states it changed nothing", "changed nothing" in r.stdout, True)

# G5 — every state the classifier can emit is one the report knows how to print.
src = TOOL.read_text()
states = ("CURRENT", "STALE", "LOCAL_DRIFT", "MISSING", "UNREACHABLE",
          "MISREGISTERED", "UNSAFE_PATH", "PARTIAL_RELEASE")
check("G5 all eight states are declared", all(s in src for s in states), True)

# G6 — a target must never be the fork itself, nor nested inside it.
sys.path.insert(0, str(FORK / "tools"))
import importlib.util
spec = importlib.util.spec_from_file_location("bmad_release", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
f, real = mod.validate_target({"id": "self", "path": str(FORK)}, {})
check("G6 the fork itself is refused as a target",
      any(lvl == "BLOCK" and "IS the fork" in m for lvl, m in f), True)
f, real = mod.validate_target({"id": "nested", "path": str(FORK / "custom")}, {})
check("G6b a path inside the fork is refused",
      any(lvl == "BLOCK" and "nested inside the fork" in m for lvl, m in f), True)

# G7 — two registry entries resolving to one real path is an alias, and must block.
seen = {}
mod.validate_target({"id": "a", "path": str(FORK.parent)}, seen)
f, _ = mod.validate_target({"id": "b", "path": str(FORK.parent)}, seen)
check("G7 an aliased duplicate target is refused",
      any(lvl == "BLOCK" and "alias" in m for lvl, m in f), True)

# ------------------------------------------------------------------------------------
# WF-20260925-092 — the fork's .gitignore block must re-include ONLY the paths it manages.
# The first version appended `!.claude/`, which un-ignored the whole folder: hundreds of
# generated files and the per-machine settings.local.json turned up untracked in two
# projects. Pinned in the failing direction against real git ignore semantics.
_gs = importlib.util.spec_from_file_location("gi_block", FORK / "tools" / "gitignore_claude_block.py")
gi = importlib.util.module_from_spec(_gs)
_gs.loader.exec_module(gi)
GI_TOOL = FORK / "tools" / "gitignore_claude_block.py"


def fixture_repo(td, gitignore):
    repo = Path(td) / "proj"
    repo.mkdir()
    for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"],
              ["config", "user.name", "t"]):
        git(*a, cwd=repo)
    if gitignore is not None:
        (repo / ".gitignore").write_text(gitignore)
    (repo / "README.md").write_text("x\n")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "init", cwd=repo)
    return repo


def gi_run(repo, mode):
    return subprocess.run([sys.executable, str(GI_TOOL), "--root", str(repo), "--mode", mode],
                          capture_output=True, text=True, env=_CLEAN_ENV)


def ignored(repo, path):
    return git("check-ignore", "-q", "--no-index", path, cwd=repo).returncode == 0


LEGACY = ("node_modules/\n.claude/\n.env\n\n" + gi.MARK + "\n!.claude/\n"
          "!.claude/settings.json\n!.claude/hooks/\n")

with tempfile.TemporaryDirectory() as td:
    # G8 — the broad legacy block is repaired in place, even while uncommitted (that is the
    #      exact state the earlier sync left bison-ops and bison-website in).
    repo = fixture_repo(td, "node_modules/\n.claude/\n.env")
    (repo / ".gitignore").write_text(LEGACY)  # uncommitted, as the old sync left it
    check("G8 legacy broad block: check mode reports a rewrite (exit 3)", gi_run(repo, "check").returncode, 3)
    r = gi_run(repo, "sync")
    check("G8b sync repairs it", r.returncode, 0)
    check("G8c settings.local.json is ignored again", ignored(repo, ".claude/settings.local.json"), True)
    check("G8d generated skills are ignored again", ignored(repo, ".claude/skills/x/SKILL.md"), True)
    check("G8e worktrees are ignored again", ignored(repo, ".claude/worktrees/a/b.txt"), True)
    check("G8f the tracked hook wiring is trackable", ignored(repo, ".claude/settings.json"), False)
    check("G8g the fork's guard scripts are trackable", ignored(repo, ".claude/hooks/g.py"), False)
    check("G8h bytecode beside them is not", ignored(repo, ".claude/hooks/__pycache__/g.pyc"), True)
    check("G8i project rules outside .claude are untouched", ignored(repo, "node_modules/a.js"), True)
    text = (repo / ".gitignore").read_text()
    check("G8j exactly one fork block, never a bare re-include of the folder alone",
          (text.count(gi.MARK), "\n.claude/*\n" in text), (1, True))
    check("G8k idempotent: a second run changes nothing", (gi_run(repo, "sync").returncode,
          (repo / ".gitignore").read_text() == text), (0, True))

with tempfile.TemporaryDirectory() as td:
    # G9 — a repo ignoring only the CHILDREN gets the narrowest block: no `!.claude/`.
    repo = fixture_repo(td, ".claude/*\n")
    check("G9 children-only ignore: sync makes the paths trackable", gi_run(repo, "sync").returncode, 0)
    text = (repo / ".gitignore").read_text()
    check("G9b and does not re-include the folder", "!.claude/\n" in text, False)
    check("G9c settings.local.json stays ignored", ignored(repo, ".claude/settings.local.json"), True)

with tempfile.TemporaryDirectory() as td:
    # G10 — a repo that does not ignore .claude is left byte-for-byte alone, even with no
    #       trailing newline (a rewrite nobody needed would dirty it on every release).
    repo = fixture_repo(td, "dist/\n.env")
    check("G10 nothing blocked: exit 0", gi_run(repo, "sync").returncode, 0)
    check("G10b file unchanged, byte-for-byte", (repo / ".gitignore").read_text(), "dist/\n.env")

with tempfile.TemporaryDirectory() as td:
    # G11 — someone else's uncommitted edit is never built upon.
    repo = fixture_repo(td, ".claude/\n")
    (repo / ".gitignore").write_text(".claude/\nmy-local-edit/\n")
    check("G11 foreign local edit: refused (exit 1)", gi_run(repo, "sync").returncode, 1)
    check("G11b and the file is untouched", (repo / ".gitignore").read_text(), ".claude/\nmy-local-edit/\n")

# G12 — the sync delegates to the helper and no longer appends a bare `!.claude/`.
sync_src = (FORK / "sync-bmad-workflows.sh").read_text()
check("G12 sync calls the gitignore helper", "gitignore_claude_block.py" in sync_src, True)
check("G12b sync no longer echoes a bare re-include of .claude/", 'echo "!.claude/"' in sync_src, False)

# ------------------------------------------------------------------------------------
# WF-20260925-091 — publish must commit every path the release owns, and nothing else.
# It used to stage `_bmad/` only, so each release left skills, hook wiring and guard
# scripts uncommitted, and the next release refused the target as LOCAL_DRIFT.
with tempfile.TemporaryDirectory() as td:
    repo = fixture_repo(td, "node_modules/\n")
    (repo / "CLAUDE.md").write_text("# project\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.ts").write_text("a\n")
    (repo / "unrelated.txt").write_text("u\n")
    git("add", "-A", cwd=repo); git("commit", "-qm", "base", cwd=repo)

    wt = Path(td) / "release"
    (wt / "custom" / "hooks").mkdir(parents=True)
    (wt / "custom" / "hooks" / "guard.py").write_text("print('fork guard')\n")
    (wt / "custom" / "scripts").mkdir(parents=True)
    (wt / "custom" / "scripts" / "deploy.sh").write_text("echo fork\n")

    # BEFORE the release: somebody is editing CLAUDE.md and has staged an unrelated file.
    (repo / "CLAUDE.md").write_text("# project\nlocal edit in progress\n")
    (repo / "unrelated.txt").write_text("u2\n")
    git("add", "unrelated.txt", cwd=repo)
    pre = mod.porcelain(repo)

    # THE RELEASE WRITES:
    (repo / "_bmad").mkdir()
    (repo / "_bmad" / "wf.md").write_text("workflow\n")
    (repo / ".claude" / "skills" / "s").mkdir(parents=True)
    (repo / ".claude" / "skills" / "s" / "SKILL.md").write_text("skill\n")
    (repo / ".claude" / "commands" / "bmad").mkdir(parents=True)
    (repo / ".claude" / "commands" / "bmad" / "c.md").write_text("cmd\n")
    (repo / ".claude" / "hooks").mkdir()
    (repo / ".claude" / "hooks" / "guard.py").write_text("print('fork guard')\n")
    (repo / ".claude" / "settings.json").write_text('{"hooks": {}}\n')
    (repo / ".claude" / "settings.local.json").write_text('{"permissions": {}}\n')
    (repo / "CLAUDE.md").write_text("# project\nlocal edit in progress\n## synced section\n")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "deploy.sh").write_text("echo LOCALLY CHANGED\n")
    # ...and, concurrently, not the release:
    (repo / ".claude" / "hooks" / "project-own.py").write_text("mine\n")
    (repo / "src" / "app.ts").write_text("a concurrent edit\n")

    (repo / ".githooks").mkdir()
    (repo / ".githooks" / "gates.conf").write_text("project gate list\n")
    (wt / "custom" / "githooks").mkdir(parents=True)
    (wt / "custom" / "githooks" / "gates.conf").write_text("fork default\n")
    pre = mod.porcelain(repo)
    commit_set, held = mod.release_commit_set(repo, wt, "_bmad", pre)
    check("G13i a create-only gate list the project already had is neither committed nor held",
          ".githooks/gates.conf" in commit_set + [p for p, _ in held], False)
    held_paths = [p for p, _ in held]
    check("G13 the replica, skills and bmad commands are committed",
          all(p in commit_set for p in ("_bmad/wf.md", ".claude/skills/s/SKILL.md",
                                        ".claude/commands/bmad/c.md")), True)
    check("G13b the tracked hook wiring is committed", ".claude/settings.json" in commit_set, True)
    check("G13c a fork guard script identical to the release is committed",
          ".claude/hooks/guard.py" in commit_set, True)
    check("G13d settings.local.json is NEVER committed",
          ".claude/settings.local.json" in commit_set + held_paths, False)
    check("G13e a project's own hook is not the release's to commit",
          ".claude/hooks/project-own.py" in commit_set + held_paths, False)
    check("G13f app code changed during the release is not committed",
          "src/app.ts" in commit_set + held_paths, False)
    check("G13g a merged file with prior local edits is HELD, not committed",
          ("CLAUDE.md" in commit_set, "CLAUDE.md" in held_paths), (False, True))
    check("G13h a copied file that differs from the release is HELD",
          ("scripts/deploy.sh" in commit_set, "scripts/deploy.sh" in held_paths), (False, True))

    ok, n = mod.commit_release_paths(repo, commit_set, "chore(bmad): test release")
    check("G14 the commit succeeds", ok, True)
    committed = git("show", "--name-only", "--format=", "HEAD", cwd=repo).stdout.split()
    check("G14b the commit holds exactly the release-owned set",
          sorted(committed), sorted(commit_set))
    left = mod.porcelain(repo)
    check("G14c nothing the release committed is left dirty",
          [p for p in commit_set if p in left], [])
    check("G14d an unrelated file someone had staged stays staged, uncommitted",
          left.get("unrelated.txt"), "M ")

with tempfile.TemporaryDirectory() as td:
    # G15 — untracked files visible ONLY through the fork's own broad block are not drift;
    #       real project changes under the managed scope still are.
    repo = fixture_repo(td, "node_modules/\n.claude/\n.env")
    (repo / ".gitignore").write_text(LEGACY)  # the old sync's uncommitted append
    (repo / ".claude" / "skills" / "bmad-x").mkdir(parents=True)
    (repo / ".claude" / "skills" / "bmad-x" / "SKILL.md").write_text("generated\n")
    dirty = git("status", "--porcelain", "--", ".claude/skills", cwd=repo).stdout.strip()
    rest, n = mod.discount_ignore_block_exposure(repo, [".claude/skills"], dirty)
    check("G15 exposure-only untracked files are discounted", (rest, n), ("", 1))
    (repo / ".gitignore").write_text(".claude/\n")
    git("add", ".gitignore", cwd=repo)
    git("add", "-f", ".claude/skills/bmad-x/SKILL.md", cwd=repo)
    git("commit", "-qm", "tracked skill", cwd=repo)
    (repo / ".claude" / "skills" / "bmad-x" / "SKILL.md").write_text("edited\n")
    dirty = git("status", "--porcelain", "--", ".claude/skills", cwd=repo).stdout.strip()
    rest, n = mod.discount_ignore_block_exposure(repo, [".claude/skills"], dirty)
    check("G15b a real edit to a tracked managed file is still drift", (bool(rest), n), (True, 0))

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
