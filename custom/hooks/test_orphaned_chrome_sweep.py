#!/usr/bin/env python3
"""Golden cases for orphaned-chrome-sweep.py.

WEIGHTED TOWARDS WHAT IT MUST NEVER KILL, deliberately. This hook sends SIGKILL to a
process group with no confirmation and no undo, so the expensive failure is not
"missed an orphan" — it is "killed a browser somebody was using", which surfaces as
a render that silently never finishes. Most cases below therefore assert that a
process is LEFT ALONE.

The live-process cases at the end spawn real processes and kill them, because the
thing under test is an interaction with the kernel's reparenting. A test that only
fed strings to the matcher would have passed on 2026-09-16 while the real question —
does a live launcher's browser look orphaned — went unasked.

    python3 .claude/hooks/test_orphaned_chrome_sweep.py
"""

from __future__ import annotations

import importlib.util
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = Path(__file__).with_name("orphaned-chrome-sweep.py")
spec = importlib.util.spec_from_file_location("sweep", HOOK)
assert spec and spec.loader
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)

TMP = tempfile.gettempdir()
OURS = os.path.join(TMP, "fba-chrome-pdf-AbC123")

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        failures.append(f"{name}\n    expected: {want!r}\n    got:      {got!r}")


# ---------------------------------------------------------------- profile matching

check(
    "a profile under our prefix is ours",
    sweep.our_profile_dir(f"/Chrome --headless=new --user-data-dir={OURS}"),
    OURS,
)
check(
    "a temp profile that is NOT ours is left alone",
    sweep.our_profile_dir(f"/Chrome --headless=new --user-data-dir={TMP}/puppeteer_dev_x"),
    None,
)
check(
    "another project's chrome- profile is not ours either",
    sweep.our_profile_dir(f"/Chrome --headless=new --user-data-dir={TMP}/chrome-pdf-old"),
    None,
)
check(
    "a profile outside the temp dir is never ours",
    sweep.our_profile_dir("/Chrome --headless --user-data-dir=/Users/masonwood/Library/Chrome"),
    None,
)
check(
    "no --user-data-dir at all is not ours",
    sweep.our_profile_dir("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    None,
)
check(
    "a prefix appearing elsewhere in the line does not count",
    sweep.our_profile_dir(f"/Chrome --headless --screenshot={OURS}/x.png --user-data-dir=/tmp/o"),
    None,
)

# The prefix must be anchored at the temp root, not matched loosely anywhere.
check(
    "a lookalike path that merely contains the prefix is not ours",
    sweep.our_profile_dir(f"/Chrome --headless --user-data-dir=/Users/x/fba-chrome-pdf-Ab"),
    None,
)

# ---------------------------------------------------------------- prefix agreement

check(
    "the prefix is the one the TypeScript mints",
    sweep.CHROME_PROFILE_PREFIX,
    "fba-chrome-",
)
check(
    "the profile root is anchored at the temp dir",
    sweep.profile_root(),
    os.path.join(TMP, "fba-chrome-"),
)

# ---------------------------------------------------------------- live processes


def spawn_browserish(profile_dir: str, detached: bool = True) -> subprocess.Popen:
    """A stand-in carrying the two marks the sweep reads: --headless and our profile."""
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(60)",
            "--headless=new",
            f"--user-data-dir={profile_dir}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=detached,
    )


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def gone_within(pid: int, seconds: float) -> bool:
    until = time.time() + seconds
    while time.time() < until:
        if not alive(pid):
            return True
        time.sleep(0.05)
    return not alive(pid)


made = tempfile.mkdtemp(prefix="fba-chrome-test-")

# THE CASE THAT MATTERS MOST: a browser whose launcher is ALIVE is never touched.
# This is the one that would have cost a working session, and it is the property the
# whole design rests on — `detached` changes the process group, not the parent link.
live = spawn_browserish(made)
time.sleep(0.4)
listed = [pid for pid, _ in sweep.orphans()]
check("a browser with a live launcher is NOT an orphan", live.pid in listed, False)
check("...and it is still running afterwards", alive(live.pid), True)
os.killpg(live.pid, signal.SIGKILL)
gone_within(live.pid, 3)

# A browser of ours whose launcher is dead IS swept. Built by having an intermediate
# process spawn it and then die, which is exactly the SIGKILL path no handler covers.
orphan_maker = subprocess.Popen(
    [
        sys.executable,
        "-c",
        (
            "import subprocess,sys,time,os\n"
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)',"
            "'--headless=new','--user-data-dir=%s'],start_new_session=True,"
            "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
            "print(p.pid,flush=True)\n"
            "time.sleep(60)\n" % made
        ),
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
)
orphan_pid = int(orphan_maker.stdout.readline().strip())
orphan_maker.kill()  # SIGKILL — nothing in the launcher gets to run
time.sleep(1.0)

check("the orphan really was reparented to pid 1", os.getppid() > 0, True)
listed_after = [pid for pid, _ in sweep.orphans()]
check("a browser whose launcher is dead IS an orphan", orphan_pid in listed_after, True)
check("killing it reports success", sweep.kill_group(orphan_pid), True)
check("and it is actually gone", gone_within(orphan_pid, 3), True)

# A dead launcher's process that is NOT headless is left alone — the shape of
# Mason's own Chrome, which must survive this hook under every circumstance.
not_headless = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(30)", f"--user-data-dir={made}"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
time.sleep(0.3)
check(
    "a non-headless process is never swept, whatever its parentage",
    not_headless.pid in [pid for pid, _ in sweep.orphans()],
    False,
)
os.killpg(not_headless.pid, signal.SIGKILL)

# Killing something already gone is quiet and false, never an exception.
check("killing a dead pid returns False rather than raising", sweep.kill_group(orphan_pid), False)
check("pid 1 is never signalled", sweep.kill_group(1), False)

# ---------------------------------------------------------------- output discipline

result = subprocess.run(
    [sys.executable, str(HOOK)], capture_output=True, text=True, timeout=30
)
check("the hook exits 0 with nothing to do", result.returncode, 0)
check("and says nothing at all", result.stdout.strip(), "")

if failures:
    print(f"FAILED {len(failures)} of {len(failures)} checks shown:\n")
    for f in failures:
        print(f"  - {f}\n")
    sys.exit(1)

print("orphaned-chrome-sweep: all golden cases pass")
