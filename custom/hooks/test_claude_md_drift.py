#!/usr/bin/env python3
"""Golden cases for claude-md-drift.py.

MOST OF THESE ASSERT SILENCE. That is deliberate and is the main risk being guarded: a
hook that speaks on ordinary prompts gets switched off, and this repo already holds three
mechanisms that fire nowhere because nobody noticed they had died. A noisy one dies the
same way, faster.

Run: python3 .claude/hooks/test_claude_md_drift.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "claude-md-drift.py"

PASS: list[str] = []
FAIL: list[str] = []


def run(root: Path, session_id: str = "sess-1") -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"session_id": session_id}),
        capture_output=True,
        text=True,
        cwd=str(root),
        env=env,
        timeout=20,
    )
    assert out.returncode == 0, f"hook exited {out.returncode}: {out.stderr}"
    return out.stdout


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASS if condition else FAIL).append(name if not detail else f"{name} — {detail}")


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)


def new_repo(tmp: Path) -> Path:
    root = tmp / "repo"
    (root / ".claude").mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    (root / "CLAUDE.md").write_text("# Project\n\nOriginal rule.\n")
    git(root, "add", "CLAUDE.md")
    git(root, "commit", "-qm", "initial")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = new_repo(tmp)

        # 1. First sight of a session records the baseline and says NOTHING. Announcing
        #    the file's existence to every new session is pure noise.
        check("AC1 silent on first sight", run(root) == "")

        # 2. An unchanged file stays silent, every prompt, forever. This is the normal
        #    case and the one that decides whether the hook survives.
        check("AC2 silent when unchanged", run(root) == "")
        check("AC2b still silent on a third prompt", run(root) == "")

        # 3. A real change speaks, and carries the CHANGED TEXT — not a pointer. A nudge
        #    to go and re-read is the same compliance problem one step removed, and this
        #    hook exists because that dependency failed.
        (root / "CLAUDE.md").write_text("# Project\n\nOriginal rule.\n\nA record id is not an answer.\n")
        git(root, "add", "CLAUDE.md")
        git(root, "commit", "-qm", "docs: a record id is not an answer")
        spoke = run(root)
        check("AC3 speaks when CLAUDE.md changed", spoke != "")
        check("AC3b carries the actual new text", "a record id is not an answer" in spoke.lower())
        check("AC3c says the loaded copy is stale", "not in the copy loaded" in spoke.lower())

        # 4. Having spoken once, it goes quiet again — it reports a change, not a state.
        check("AC4 silent after reporting", run(root) == "")

        # 5. Two sessions keep INDEPENDENT baselines. A shared one would let the first
        #    session's read blind the second — the exact failure being fixed.
        (root / "CLAUDE.md").write_text("# Project\n\nOriginal rule.\n\nSecond change.\n")
        git(root, "add", "CLAUDE.md")
        git(root, "commit", "-qm", "second")
        first = run(root, "sess-1")
        second = run(root, "sess-2")
        check("AC5 session 1 is told", first != "")
        check("AC5b a session seeing it first time is silent", second == "")

        # 6. No CLAUDE.md at all is silence, not a crash.
        bare = tmp / "bare"
        (bare / ".claude").mkdir(parents=True)
        check("AC6 silent with no CLAUDE.md", run(bare) == "")

        # 7. A file changed but not committed produces no git history to show. Silence
        #    beats "something changed" with nothing to show for it.
        root2 = new_repo(tmp / "b")
        run(root2)
        (root2 / "CLAUDE.md").write_text("# Project\n\nUncommitted edit.\n")
        out = run(root2)
        check(
            "AC7 says nothing it cannot evidence",
            out == "" or "uncommitted edit" in out.lower(),
            f"got: {out[:80]!r}",
        )

        # 8. Never blocks. Exit code is always 0 — asserted inside run().
        check("AC8 never blocks", True)

    for name in PASS:
        print(f"  ok   {name}")
    for name in FAIL:
        print(f"  FAIL {name}")
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
