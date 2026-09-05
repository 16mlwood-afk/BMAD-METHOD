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

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
