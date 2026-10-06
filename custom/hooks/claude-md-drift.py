#!/usr/bin/env python3
"""Tell a running session when CLAUDE.md changed underneath it, and show the diff.

WHY THIS EXISTS, with the worked case that caused it.

On 2026-09-08 one session captured an owner instruction — "A record id is not an answer",
about never naming a box id as the subject of a sentence — and committed it to CLAUDE.md
at 15:16. Another session had loaded CLAUDE.md at 14:54. That second session never saw the
rule, and at 22:00 Mason had to give the same instruction a second time.

A session reads the project instructions ONCE, at startup, and never again. Eleven sessions
ran in parallel that day, so a rule captured by one of them reached roughly none of the
others. The capture worked perfectly. There was simply no delivery.

WHAT THIS DOES. Records a hash of CLAUDE.md the first time it sees a session, compares on
every prompt, and when it differs injects THE DIFF ITSELF.

Injecting the diff rather than "CLAUDE.md has changed, go and re-read it" is the whole
point. A nudge to re-read is the same compliance problem one step removed — it depends on
the model choosing to act on it, and this file exists precisely because that dependency
failed. The changed text arrives in context whether or not anyone decides to fetch it.

WHAT IT DELIBERATELY DOES NOT DO.

  - It never blocks. A prompt is not the place to stop work, and a hook that interrupts on
    a routine edit to CLAUDE.md gets switched off — which is how three other mechanisms in
    this repo came to fire nowhere.
  - It says nothing when nothing changed. Silence is the normal case and must stay free.
  - It does not judge whether the change matters. It cannot: that is a judgement, and a
    keyword filter for importance would drop the one line that mattered.

ENFORCEMENT TIER: DETERMINISTIC. A file either changed or it did not; no intent is read and
no model choice is involved. That is why this is the part of the design that got built
first — the rest of the capture problem is probabilistic and is specified rather than
wired (docs/specs/context-capture-and-delivery.md).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import sys
from pathlib import Path

# A cap, because the whole point is that this lands IN the prompt. A rewrite of the file
# would otherwise flood the context it is trying to help.
MAX_DIFF_CHARS = 3000


def project_root() -> Path:
    """The checkout, resolved the same way the sibling hooks resolve it.

    A worktree lives at <root>/.claude/worktrees/<name>, and its CLAUDE.md is the one the
    session is actually working against, so the worktree path is NOT unwound here — unlike
    research-pointer.py, which unwinds it to find a script that only exists in the root.
    """
    for env in ("CLAUDE_PROJECT_DIR",):
        value = os.environ.get(env)
        if value and (Path(value) / "CLAUDE.md").exists():
            return Path(value)
    return Path.cwd()


def state_path(root: Path, session_id: str) -> Path:
    """Per-session, under the run directory, keyed by session id.

    Not a single shared file: two sessions started at different times have legitimately
    different baselines, and one overwriting the other's would make each blind to the
    other's changes — the exact failure this hook exists to fix.
    """
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:64] or "unknown"
    return root / ".claude" / "state" / f"claude-md-{safe}.json"


def read_stdin_json() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def diff_for(previous_text: str, current_text: str) -> str:
    """The change, computed against the text this session actually started with.

    NOT from `git log`. An earlier version of this hook asked git for the last few commits
    touching CLAUDE.md, and that is wrong in the case that matters most: a file edited but
    not yet committed still changes the hash, and git log then answers with an OLDER
    commit's diff — announcing a change and showing text that has nothing to do with it.
    A confident wrong answer is worse than silence. Caught by AC7 of the golden suite.

    Comparing stored baseline text also removes the dependency on the checkout being a git
    repository at all.
    """
    return "".join(
        difflib.unified_diff(
            previous_text.splitlines(keepends=True),
            current_text.splitlines(keepends=True),
            fromfile="CLAUDE.md (as loaded into this session)",
            tofile="CLAUDE.md (now)",
            n=2,
        )
    )


def main() -> int:
    payload = read_stdin_json()
    session_id = str(payload.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or "")

    root = project_root()
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return 0

    try:
        current_text = claude_md.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    current = hashlib.sha256(current_text.encode("utf-8")).hexdigest()

    path = state_path(root, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        return 0

    previous = None
    previous_text = ""
    if path.exists():
        try:
            stored = json.loads(path.read_text())
            previous = stored.get("sha256")
            previous_text = stored.get("text", "")
        except Exception:
            previous = None

    if previous == current:
        return 0

    try:
        # The BASELINE TEXT is stored, not merely its hash. A hash cannot be turned back
        # into the thing that changed, and the diff is the entire value here.
        path.write_text(json.dumps({"sha256": current, "text": current_text}))
    except Exception:
        # A state file we cannot write means we would re-announce every prompt. Better to
        # say nothing than to become noise.
        return 0

    # First sight of this session: record the baseline, say nothing. There is no change
    # to report yet, and announcing the file's existence on every new session is noise.
    if previous is None:
        return 0

    diff = diff_for(previous_text, current_text)
    if not diff.strip():
        return 0
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n… (truncated — read CLAUDE.md for the rest)"

    print(
        "CLAUDE.md CHANGED SINCE THIS SESSION STARTED, and a session never re-reads it on "
        "its own — so the change is below rather than as a pointer. Another session has "
        "committed a project rule that is NOT in the copy loaded into this context. Read "
        "it as current and binding; where it conflicts with what you were told at startup, "
        "the version below is newer.\n\n"
        f"{diff}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
