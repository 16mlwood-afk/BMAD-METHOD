#!/usr/bin/env python3
"""Golden cases for hook-resolve-check.py — both findings it reports.

WEIGHTED TOWARDS SILENCE, deliberately. This runs at SessionStart in every
project the fork syncs. A banner that prints on a healthy session becomes
wallpaper, and wallpaper is how the real warning gets skipped. Most cases here
assert the check says NOTHING.

TWO FINDINGS, ONE FAMILY.

  1. WIRED BUT ABSENT (the original, FG-2026-07-31-15) — settings name a hook
     script that is not on disk. Configured and not running.

  2. PRESENT BUT NOT CARRIED (added 2026-09-21) — the script is on disk, and
     the VCS is set to ignore it. The repository LOOKS guarded. A fresh clone,
     a second machine or CI gets a repository with no guards at all, and
     nothing says so until somebody happens to run a sync.

     Measured 2026-09-21 across the fourteen registered targets: four projects
     ignore `.claude/hooks/` wholesale and each already held six fork-delivered
     hook files with ZERO tracked.

THE DISTINCTION THAT DECIDES WHETHER THIS IS USABLE. A hook file that is merely
NEW AND UNCOMMITTED is ordinary work — it is what every hook looks like in the
minute after it is written, and a check that fires on it gets switched off
within a week. So "untracked" is never the trigger. IGNORED is. `check-ignore`
answers that exactly and without heuristics, and cases N1-N3 below pin it.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "hook-resolve-check.py"
PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + ("" if ok else f"\n          got={got!r} want={want!r}"))


def run(cwd):
    """Invoke the hook the way SessionStart does: JSON on stdin."""
    r = subprocess.run([sys.executable, str(HOOK)],
                       input=json.dumps({"cwd": str(cwd)}),
                       capture_output=True, text=True)
    return r.stdout


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def repo(root, *, init=True):
    (root / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    if init:
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "t@t")
        git(root, "config", "user.name", "t")
    return root


def wire(root, names, settings="settings.json", event="SessionStart"):
    """Register each hook by the .claude/hooks/<name> fragment the check reads."""
    cfg = {"hooks": {event: [{"hooks": [
        {"type": "command",
         "command": f'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/{n}"'}
        for n in names]}]}}
    (root / ".claude" / settings).write_text(json.dumps(cfg, indent=2))


def put(root, name, body="#!/usr/bin/env python3\nprint()\n"):
    (root / ".claude" / "hooks" / name).write_text(body)


def commit(root, *paths):
    git(root, "add", "-f", *paths)
    git(root, "commit", "-qm", "x")


print("hook-resolve-check golden cases:\n")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)

    # === SILENCE CASES ====================================================

    # S1 — everything tracked and wired: the healthy project, says nothing.
    r1 = repo(td / "s1")
    put(r1, "guard.py")
    wire(r1, ["guard.py"])
    commit(r1, ".claude/hooks/guard.py", ".claude/settings.json")
    check("S1  a tracked, wired guard produces no output", run(r1), "")

    # S2 — NOT A REPOSITORY. Nothing to say about what a clone would get.
    r2 = repo(td / "s2", init=False)
    put(r2, "guard.py")
    wire(r2, ["guard.py"])
    check("S2  a non-repository is silent", run(r2), "")

    # S3 — no hooks directory at all.
    r3 = td / "s3"
    (r3 / ".claude").mkdir(parents=True)
    check("S3  a project with no hooks dir is silent", run(r3), "")

    # S4 — THE STOP CONDITION. A hook just written and not yet committed is
    #      ordinary work. It is untracked, it is NOT ignored, and the check
    #      must not mention it. This is the case that decides whether the
    #      whole check is usable or noise.
    r4 = repo(td / "s4")
    put(r4, "brand-new-guard.py")
    wire(r4, ["brand-new-guard.py"])
    commit(r4, ".claude/settings.json")
    check("S4  a NEW, uncommitted, un-ignored hook is silent (ordinary work)",
          run(r4), "")

    # S5 — settings.local.json is gitignored BY DESIGN (it holds per-machine
    #      permissions and trust). Reporting it would fire in every project
    #      forever, which is how a check gets switched off.
    r5 = repo(td / "s5")
    put(r5, "guard.py")
    wire(r5, ["guard.py"], settings="settings.local.json")
    (r5 / ".gitignore").write_text(".claude/settings.local.json\n")
    commit(r5, ".claude/hooks/guard.py", ".gitignore")
    check("S5  an ignored settings.local.json is silent (ignored by design)",
          run(r5), "")

    # S6 — a non-script file in the hooks dir is not a guard.
    r6 = repo(td / "s6")
    put(r6, "guard.py")
    (r6 / ".claude" / "hooks" / "notes.md").write_text("x\n")
    (r6 / ".claude" / "hooks" / "__pycache__").mkdir()
    (r6 / ".gitignore").write_text(".claude/hooks/notes.md\n.claude/hooks/__pycache__/\n")
    wire(r6, ["guard.py"])
    commit(r6, ".claude/hooks/guard.py", ".claude/settings.json", ".gitignore")
    check("S6  an ignored non-script file in the hooks dir is silent", run(r6), "")

    # === FINDING 2: PRESENT BUT NOT CARRIED ================================

    # N1 — the measured defect. Whole hooks dir ignored, files on disk.
    n1 = repo(td / "n1")
    for n in ("bash_edit_guard.py", "guard-wiring-check.sh", "hook-resolve-check.py"):
        put(n1, n)
    wire(n1, ["bash_edit_guard.py"])
    (n1 / ".gitignore").write_text(".claude/*\n!.claude/settings.json\n")
    commit(n1, ".claude/settings.json", ".gitignore")
    o1 = run(n1)
    check("N1  an ignored hooks directory is REPORTED", o1 != "", True)
    check("N1b it names each guard the repository will not carry",
          all(n in o1 for n in ("bash_edit_guard.py", "guard-wiring-check.sh",
                                "hook-resolve-check.py")), True)
    check("N1c it says plainly what a fresh clone gets",
          "fresh clone" in o1.lower(), True)
    check("N1d it does not describe them as missing (they are on disk)",
          "MISSING" in o1, False)

    # N2 — MIXED. Only the ignored one is reported; the tracked one is not.
    n2 = repo(td / "n2")
    put(n2, "carried.py")
    put(n2, "not-carried.py")
    (n2 / ".gitignore").write_text(".claude/hooks/not-carried.py\n")
    wire(n2, ["carried.py", "not-carried.py"])
    commit(n2, ".claude/hooks/carried.py", ".claude/settings.json", ".gitignore")
    o2 = run(n2)
    check("N2  the ignored guard is reported", "not-carried.py" in o2, True)
    check("N2b the tracked guard is NOT reported", "carried.py" in o2.replace("not-carried.py", ""), False)

    # N3 — ignored AND new-and-uncommitted together: only the ignored one.
    n3 = repo(td / "n3")
    put(n3, "ignored-guard.py")
    put(n3, "fresh-guard.py")
    (n3 / ".gitignore").write_text(".claude/hooks/ignored-guard.py\n")
    wire(n3, ["ignored-guard.py", "fresh-guard.py"])
    commit(n3, ".claude/settings.json", ".gitignore")
    o3 = run(n3)
    check("N3  the ignored guard is reported", "ignored-guard.py" in o3, True)
    check("N3b the merely-new guard is NOT reported alongside it",
          "fresh-guard.py" in o3, False)

    # N4 — THE WIRING ITSELF. A tracked settings.json is what makes a guard
    #      survive a clone; if it is ignored, the clone gets the scripts and
    #      no registration, which is a repository that cannot fire any of them.
    n4 = repo(td / "n4")
    put(n4, "guard.py")
    wire(n4, ["guard.py"])
    (n4 / ".gitignore").write_text(".claude/settings.json\n")
    commit(n4, ".claude/hooks/guard.py", ".gitignore")
    o4 = run(n4)
    check("N4  an ignored settings.json is reported as wiring not carried",
          "settings.json" in o4, True)

    # === FINDING 1: the original behaviour must survive unchanged ==========

    # W1 — wired, absent from disk.
    w1 = repo(td / "w1")
    wire(w1, ["vanished.py"])
    put(w1, "present.py")
    commit(w1, ".claude/hooks/present.py", ".claude/settings.json")
    ow1 = run(w1)
    check("W1  a wired hook with no file is still reported", "vanished.py" in ow1, True)
    check("W1b and still named as MISSING", "MISSING" in ow1, True)

    # W2 — BOTH findings at once render both, not one.
    w2 = repo(td / "w2")
    put(w2, "on-disk-but-ignored.py")
    wire(w2, ["on-disk-but-ignored.py", "gone.py"])
    (w2 / ".gitignore").write_text(".claude/hooks/on-disk-but-ignored.py\n")
    commit(w2, ".claude/settings.json", ".gitignore")
    ow2 = run(w2)
    check("W2  both findings render together — absent hook named",
          "gone.py" in ow2, True)
    check("W2b  both findings render together — uncarried guard named",
          "on-disk-but-ignored.py" in ow2, True)

    # W3 — a worktree resolves to the main checkout rather than reporting
    #      a false everything-missing from a tree that has no .claude of its own.
    w3 = repo(td / "w3")
    put(w3, "guard.py")
    wire(w3, ["guard.py"])
    commit(w3, ".claude/hooks/guard.py", ".claude/settings.json")
    wt = w3 / ".claude" / "worktrees" / "agent-1"
    wt.mkdir(parents=True)
    check("W3  a worktree path resolves to the main checkout and stays silent",
          run(wt), "")

    # W4 — FAIL OPEN. Malformed settings must not make the check throw.
    w4 = repo(td / "w4")
    put(w4, "guard.py")
    (w4 / ".claude" / "settings.json").write_text("{ not json")
    commit(w4, ".claude/hooks/guard.py")
    check("W4  malformed settings is survived in silence", run(w4), "")

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
