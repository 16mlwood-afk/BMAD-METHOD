#!/usr/bin/env python3
"""PreToolUse(Bash) — ask before a branch switch makes recognisable files VANISH.

WHY THIS EXISTS
---------------
2026-09-14.  A session created a short branch off main to deliver a change, merged
it, and switched this working copy back to its long-running branch.  That branch was
started before `docs/box-size-policy.md` existed, so the switch took the file out of
the working FOLDER.  The owner's editor showed:

    Deleted  docs/box-size-policy.md  (+0 -303)

and he asked whether it had been deleted by accident.  It had not — all 303 lines
were on main the whole time, and the file came back the moment the copy was brought
current.  Nothing was lost and nothing was ever at risk.

THE COST IS NOT DATA.  IT IS THE OWNER'S CONFIDENCE, AND IT IS NOT FREE.
This was the SECOND time in two days he had to ask that question.
`stash-untracked-guard.py` carries the first, on 2026-09-13, where `git stash -u`
swept 191 untracked files out of the shared checkout and another session's diff
showed its own hooks as deleted.  Different command, different mechanism, identical
experience at his end — a file he had just been told about, showing as deleted, with
no way to tell a branch switch from somebody destroying work.  A guard that removes a
recurring false alarm earns its interruptions.

WHY THIS IS `ask` AND NOT `deny`
--------------------------------
The switch is legitimate and routine; it is how work gets delivered here.  Denying it
would break ordinary delivery to prevent a surprise.  And the requirement is that
MASON is warned, not that the agent knows — `additionalContext` reaches the model,
which can then forget to mention it.  An ask prompt is the only channel that reaches
him deterministically, at the moment, with the file names in it.

WHY IT IS NARROW, AND THE MEASUREMENT THAT FORCED THAT
------------------------------------------------------
The obvious rule — warn whenever a switch removes a tracked file — was measured before
it was written.  It fires on 38 of 40 remote branches, frequently on 1,000+ files at
once.  That is the indiscriminate gate this project's enforcement doctrine names: it
would be switched off within a week and then guard nothing.

So two filters, both measured on the 14 most recently updated branches:

  * RECENT — the file was added to `origin/main` within 7 days.  A file the owner has
    never seen cannot alarm him, and ancient branches differ from HEAD mostly in files
    that predate this week.
  * RECOGNISABLE — the path is under `docs/`, under `data/`, or is `CLAUDE.md`.  These
    are the surfaces he reads.  `src/` churn is real work but he does not watch it, and
    including it is what turns 2 names into 33.

Measured result: 4 of the 14 fire not at all, and the other 10 name between 2 and 5
files each.  That is a prompt a person can read and believe.

WHAT IT DOES NOT CATCH, stated so nobody reads more into a silent run
---------------------------------------------------------------------
It reads a shell string.  It does not expand `$VAR`, command substitution, aliases, a
script's contents, or `bash -c`.  A switch issued from inside a script passes unseen.
It matches `git checkout <ref>`, `git switch <ref>` and `git reset --hard <ref>`; it
deliberately ignores `-b` / `-c` (a new branch starts at HEAD and removes nothing) and
any form carrying a ` -- ` path separator (a file restore, not a switch).  It cannot
see `git worktree remove`, `ExitWorktree`, or a merge that deletes files.

IT FAILS OPEN, AND SAYS SO.  If git cannot resolve the target ref, or the diff cannot
be computed, the call is ALLOWED — a guard that blocks delivery because it could not
look is worse than the surprise it prevents.  A silent run therefore means EITHER
nothing recognisable would be removed OR the check could not run; those are not the
same thing, and this paragraph is the only place that distinction is recorded.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

RECENT_WINDOW = '7 days ago'
RECOGNISABLE = re.compile(r'^(?:docs/|data/|CLAUDE\.md$)')
MAX_NAMED = 8

# `git checkout <ref>` / `git switch <ref>` / `git reset --hard <ref>`, capturing the ref.
# The negative lookahead drops flag forms (`-b`, `-c`, `--detach`) — a new branch starts
# at HEAD and removes nothing.
SWITCH = re.compile(
    r'\bgit\s+(?:checkout|switch)\s+(?!-)(?P<ref>[^\s;&|]+)'
    r'|\bgit\s+reset\s+--hard\s+(?!-)(?P<ref2>[^\s;&|]+)'
)


def git(args: list[str], cwd: str) -> str | None:
    """Run git, returning stdout, or None if it failed for any reason at all."""
    try:
        done = subprocess.run(
            ['git', *args], cwd=cwd, capture_output=True, text=True, timeout=20
        )
    except Exception:
        return None
    return done.stdout if done.returncode == 0 else None


def targets(command: str) -> list[str]:
    """Every ref this command would switch to. A ` -- ` form is a path restore, not a switch."""
    if ' -- ' in command:
        return []
    refs = []
    for match in SWITCH.finditer(command):
        ref = match.group('ref') or match.group('ref2')
        if ref:
            refs.append(ref)
    return refs


def vanishing(ref: str, cwd: str) -> list[str] | None:
    """Recognisable, recently-added files this switch would take off the disk.

    None means the check could not run — the caller must ALLOW, never assume clean.
    """
    if git(['rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}'], cwd) is None:
        return None
    removed = git(['diff', '--diff-filter=D', '--name-only', 'HEAD', ref], cwd)
    if removed is None:
        return None
    candidates = {p for p in removed.splitlines() if p and RECOGNISABLE.match(p)}
    if not candidates:
        return []
    added = git(
        [
            'log',
            f'--since={RECENT_WINDOW}',
            '--diff-filter=A',
            '--name-only',
            '--pretty=format:',
            'origin/main',
        ],
        cwd,
    )
    if added is None:
        return None
    return sorted(candidates & {p for p in added.splitlines() if p})


def reason_for(named: list[str]) -> str:
    shown = named[:MAX_NAMED]
    more = len(named) - len(shown)
    lines = '\n'.join(f'  - {p}' for p in shown)
    tail = f'\n  ...and {more} more' if more else ''
    return (
        f'THIS SWITCH TAKES {len(named)} RECENTLY-ADDED FILE(S) OFF THE DISK. They are '
        'NOT being deleted - they stay in git and come back the moment this copy is '
        'brought up to date - but your editor will show them as deleted, which is why '
        f'you are being told first:\n{lines}{tail}\n\n'
        'Approve to continue. Whoever runs this should bring the copy back up to date '
        'with main straight afterwards, so nothing stays missing.'
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get('tool_name') != 'Bash':
        return 0
    command = payload.get('tool_input', {}).get('command', '')
    if not command:
        return 0

    cwd = payload.get('cwd') or os.getcwd()
    named: list[str] = []
    for ref in targets(command):
        found = vanishing(ref, cwd)
        if found:
            named.extend(found)
    if not named:
        return 0

    print(
        json.dumps(
            {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'ask',
                    'permissionDecisionReason': reason_for(sorted(set(named))),
                }
            }
        )
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
