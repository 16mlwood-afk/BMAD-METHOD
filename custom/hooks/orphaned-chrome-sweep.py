#!/usr/bin/env python3
"""SessionStart: kill headless browsers of ours whose launcher is dead.

WHY THIS EXISTS. Owner instruction, 2026-09-16, after his laptop ran hot: *"can you
set something up so that if orphans and IF ARE DEAD claude will kill them???"*

The cause that day was seven orphaned headless browsers, every one reparented to
launchd, pegging roughly ten cores between them for three to eighteen hours. Load
average 25 on a machine that idles near 2. `src/chrome-process-lifecycle.ts` now
cleans up on every exit path a process can observe — but it cannot observe the one
that produced those orphans: a `SIGKILL` to the launcher, or the machine losing
power. No handler of any kind runs on that path. This hook is the only cover for
it: a later session cleaning up after an earlier one that died badly.

"DEAD" IS MEASURED, NOT GUESSED, and that is the whole safety case. The kernel
reparents an orphan to pid 1, so `ppid == 1` means the launcher is gone. Verified
both directions on 2026-09-16 before this was written: a browser whose launcher is
alive reports that launcher's real pid even when spawned `detached`, because
`detached` changes the process GROUP and not the parent link; the same browser
reports 1 within a second of its launcher being SIGKILLed. **So a browser another
session is using right now cannot match, no matter how long it has been running.**

AGE IS DELIBERATELY NOT A SIGNAL. "It has been running a while" would kill a slow
render belonging to a session that is still working, and the failure would be
invisible — a screenshot that silently never arrives. Parentage answers the actual
question, and it answers it exactly.

THREE CONDITIONS, ALL REQUIRED: ours by profile prefix, headless, and parentless.
The prefix alone would be enough on this machine today and is not enough as a rule.
It is the conjunction that makes it impossible to touch Mason's own Chrome, which
is neither headless nor running out of our temp directory.

DELIBERATELY SIMPLER THAN THE TYPESCRIPT. `sweepOrphanedChrome` in
`src/chrome-process-lifecycle.ts` is the same three predicates and runs before every
browser launch. Nothing else is reimplemented here. The one thing that crosses the
language boundary is the profile prefix, and `src/chrome-sweep-hook-parity.test.ts`
pins it from the TypeScript side: change it there without changing it here and that
test fails naming both files.

SILENT WHEN THERE IS NOTHING TO KILL. A session-start line that appears every time
becomes wallpaper within a week, and then the session that needed it does not read
it. It speaks only when it actually killed something.

NEVER FAILS A SESSION. An unreadable `ps`, a malformed line, a process that dies
between the listing and the signal — all exit quietly. The worst outcome of a bug in
here must be an orphan surviving, never a session that will not start.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import tempfile

# MUST MATCH `CHROME_PROFILE_PREFIX` in src/chrome-process-lifecycle.ts.
# Pinned across the boundary by src/chrome-sweep-hook-parity.test.ts.
CHROME_PROFILE_PREFIX = "fba-chrome-"

PS_LINE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(.*)$")
PROFILE_ARG = re.compile(r"--user-data-dir=(\S+)")


def profile_root() -> str:
    """The directory our profiles are minted under, with the trailing prefix.

    `tempfile.gettempdir()` and Node's `os.tmpdir()` agree on macOS (both read
    TMPDIR), which is what lets one prefix serve both sides.
    """
    return os.path.join(tempfile.gettempdir(), CHROME_PROFILE_PREFIX)


def our_profile_dir(command: str) -> str | None:
    """The --user-data-dir in a command line, but only when it is one of ours."""
    found = PROFILE_ARG.search(command)
    if not found:
        return None
    directory = found.group(1)
    return directory if directory.startswith(profile_root()) else None


def orphans() -> list[tuple[int, str]]:
    """Every (pid, profile_dir) that is ours, headless, and parentless.

    An unreadable `ps` returns an empty list and the caller says nothing — but that
    is a failure to look, not a clean machine, so it must never be reported as one.
    The caller prints nothing either way, which keeps the two indistinguishable in
    output and harmless in effect.
    """
    try:
        listed = subprocess.run(
            ["ps", "-Ao", "pid=,ppid=,command="],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if listed.returncode != 0:
        return []

    found: list[tuple[int, str]] = []
    for line in listed.stdout.splitlines():
        parsed = PS_LINE.match(line)
        if not parsed:
            continue
        raw_pid, raw_ppid, command = parsed.groups()

        if raw_ppid != "1":
            continue  # its launcher is alive — not ours to touch
        if "--headless" not in command:
            continue  # a real browser somebody is looking at
        directory = our_profile_dir(command)
        if directory is None:
            continue  # not a profile we minted

        pid = int(raw_pid)
        if pid <= 1 or pid == os.getpid():
            continue
        found.append((pid, directory))
    return found


def kill_group(pid: int) -> bool:
    """Kill the whole process group, which is where the CPU actually goes.

    The orphaned roots on 2026-09-16 sat at 0.0% CPU while their GPU children ran at
    400%, so signalling the root alone would have left the expensive half running.
    A negative pid addresses the group; `detached` at spawn is what made the browser
    a group leader so this reaches its helpers.
    """
    try:
        os.killpg(pid, signal.SIGKILL)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        # Gone between the listing and the signal, or not ours to signal after all.
        # Either way there is nothing to report and nothing to fix.
        return False


def main() -> int:
    killed = [pid for pid, _ in orphans() if kill_group(pid)]
    if not killed:
        return 0

    count = len(killed)
    noun = "browser" if count == 1 else "browsers"
    print(
        f"Cleaned up {count} abandoned headless {noun} left by a session that was "
        f"killed before it could tidy up. Each one burns a CPU core until something "
        f"stops it. Nothing running was touched — only browsers whose owning process "
        f"is already dead."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A hook must never be the reason a session fails to start.
        sys.exit(0)
