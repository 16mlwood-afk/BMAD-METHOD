#!/usr/bin/env python3
"""PreToolUse(Bash) — refuse `git stash` variants that sweep UNTRACKED files.

WHY THIS EXISTS
---------------
2026-09-13, and it was this repository's own agent that did it.  A session wanted
to pull 17 commits and ran, in the shared checkout:

    git stash push -u -m "close-out-..."

`-u` takes untracked files too.  In most repos that is a tidy convenience.  In
THIS one the untracked set is load-bearing: `.githooks/` — eleven files including
four gate scripts another session had just written and wired — plus
`.worktreeinclude`, `AGENT-NOTE.md`, `_bmad-output/**` and roughly a hundred loose
`.ts` files at the root.  All of it vanished from the working tree in one command.

Nothing was lost; it was in `stash@{0}` the whole time.  But another session had a
diff open and saw `Deleted .githooks/check-payload-roundtrip.sh (+0 -82)`, which is
indistinguishable from somebody deleting their work.  The owner had to ask what had
been deleted, and the answer took three commands to establish.

WHY A HARD DENY AND NOT A WARNING
---------------------------------
The trigger is a LITERAL FLAG in the command string.  There is no judgement here and
no false-positive class to worry about: `-u`/`--include-untracked` means exactly one
thing, and `-a`/`--all` is strictly worse (it takes ignored files as well).  A guard
that can be matched exactly and whose harm is cross-session should deny rather than
warn — a warning on a shared checkout is a warning the other session never sees.

`git stash` WITHOUT those flags is untouched and always has been.  That is the
command the incident actually needed: only one TRACKED file was in the way.

WHAT IT DOES NOT CATCH, stated so nobody reads more into a green run
-------------------------------------------------------------------
This reads a shell string.  It does not expand `$VAR`, command substitution, aliases
or a script's contents, and it cannot see through `bash -c`.  A stash issued from
inside a script file passes unseen.  It is a matcher for the shape a session reaches
for directly, which is the shape that caused the incident — not a proof that
untracked files cannot be swept.

`git clean` is a different and more destructive command with the same blast radius.
It is NOT covered here, deliberately: it is already refused by the auto-mode
classifier as an irreversible delete, and adding a second half-overlapping matcher
would make both harder to reason about.  Recorded rather than silently omitted.

BEING WIRED IS NOT BEING LIVE
-----------------------------
The first settings.json entry for this hook read
`[ -f "$S" ] && python3 "$S" || exit 0`.  In `sh`, `||` catches this script's exit 2
and runs `exit 0`, so every refusal became an ALLOW.  The script was correct, its
28 cases passed, and the guard was a no-op.  Two of the golden cases now run the
command string out of settings.json itself, because a hook that is configured and
a hook that fires are different facts.

OVERRIDE
--------
`STASH_UNTRACKED_OVERRIDE=1` in the command.  Use it when you genuinely mean to
sweep untracked files and have said so to the owner — never to get past this on your
own convenience, and never in the shared checkout while other sessions are live.
"""

import json
import re
import sys

# `git stash` with any of these takes files git is not tracking.  `-a`/`--all` also
# takes ignored ones, which in this repo includes `output/` and every export.
UNTRACKED_FLAGS = {"-u", "--include-untracked", "-a", "--all"}

# Subcommands that READ a stash or move one back.  `git stash show
# --include-untracked` carries the flag and sweeps nothing — it is how you
# INSPECT a stash, and blocking it would block the recovery from this very
# incident.  Found by the golden cases, not by review.
READ_SUBCOMMANDS = {"show", "list", "apply", "pop", "drop", "branch", "clear"}

# `git -C <dir>` and `git -c k=v` take a VALUE, so the token after them is not a
# subcommand.  Missing this let `git -C /repo stash push -u` through.
GIT_OPTIONS_WITH_VALUES = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

OVERRIDE = "STASH_UNTRACKED_OVERRIDE=1"


def _sweeps_untracked(tokens: list[str]) -> bool:
    """True when a bundled or long flag in these tokens takes untracked files."""
    for t in tokens:
        if t in UNTRACKED_FLAGS:
            return True
        # Bundled shorts: `-um`, `-au`. Not `--foo`, and not a bare `-`.
        if len(t) > 1 and t[0] == "-" and t[1] != "-" and ("u" in t[1:] or "a" in t[1:]):
            return True
    return False


def offending_segments(command: str) -> list[str]:
    """Segments that are a `git stash` WRITE carrying an untracked-sweeping flag.

    Split on separators first so a flag belonging to a neighbouring command
    cannot be read as belonging to the stash — `git add -u && git stash` is
    ordinary and must stay silent.
    """
    out: list[str] = []
    for segment in re.split(r"&&|\|\||[;|\n]", command):
        tokens = segment.split()
        if "git" not in tokens:
            continue
        i = tokens.index("git") + 1

        # Walk past git's own options to reach the subcommand.
        while i < len(tokens) and tokens[i].startswith("-"):
            if tokens[i] in GIT_OPTIONS_WITH_VALUES:
                i += 1  # skip its value too
            i += 1
        if i >= len(tokens) or tokens[i] != "stash":
            continue

        rest = tokens[i + 1 :]
        # `git stash show --include-untracked` reads; it does not sweep.
        if rest and rest[0] in READ_SUBCOMMANDS:
            continue
        if _sweeps_untracked(rest):
            out.append(segment.strip())
    return out


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # Unreadable input is not a finding. Never block on our own fault.

    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if OVERRIDE in command:
        return 0

    hits = offending_segments(command)
    if not hits:
        return 0

    print(
        "REFUSED: `git stash` with -u/--include-untracked/-a sweeps UNTRACKED files, and in "
        "this repository those are load-bearing.\n\n"
        f"  {hits[0][:200]}\n\n"
        "On 2026-09-13 this exact command removed `.githooks/` — eleven files including four "
        "gate scripts another session had just wired — plus `.worktreeinclude`, `AGENT-NOTE.md` "
        "and ~100 loose scripts, from the shared checkout while other sessions were working in "
        "it. Nothing was lost (it was in the stash), but another session's diff showed its own "
        "hooks as deleted.\n\n"
        "WHAT TO DO INSTEAD:\n"
        "  • `git stash push <paths>` — name the tracked files that are actually in your way. "
        "This is almost always what was meant.\n"
        "  • To pull with a dirty tree: `git stash push -m \"<tag>\"` (no -u) then "
        "`git pull --ff-only`.\n"
        "  • A temporary WIP commit on your own branch, if the work is yours.\n\n"
        "If you truly mean to sweep untracked files, say so to the owner first, then prefix "
        f"the command with {OVERRIDE}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
