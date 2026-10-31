#!/usr/bin/env python3
"""audit-override-log.py — periodic review of edit-guard override use.

Run: python3 .claude/hooks/audit-override-log.py [--days N] [--log PATH]

WHAT THIS IS. `BMAD_ALLOW_MAIN_EDIT=1` is the ONLY sanctioned way to write a tracked
main-checkout file from an ad hoc shell command (CLAUDE.md § Edit guard overrides). Every
use is logged by `bash_edit_guard.py`. An override that nobody ever reviews is an override
that quietly becomes routine — which is precisely how an escape hatch stops being a signal
and starts being the path of least resistance. This is the review.

WHAT IT DELIBERATELY CANNOT TELL YOU. The log stores **paths only, never the command
string** — a command line can carry secrets, and an audit log is exactly the wrong place
for them. So this reports WHEN, WHERE (cwd) and WHICH FILES. It cannot report the command,
and it cannot attribute a human vs an agent: the harness does not stamp a principal onto a
Bash call, so "who" is UNKNOWN and is reported as unknown rather than guessed. (Same
discipline as the authorship rule: no signal is not a story.)

FLAGS RAISED (heuristics, stated as such — this reports, it never blocks):
  * frequency   — more overrides than the threshold in the window
  * repetition  — the same target overridden repeatedly (a standing workaround, not an
                  exception; that target probably wants an allowlist entry or a real fix)
  * suspicious  — a target outside the "small deliberate local edit" envelope the policy
                  allows: source dirs, migrations, lockfiles, CI config, or a bulk write
                  touching many files in one call
"""
import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

DEFAULT_LOG = os.path.join(os.path.expanduser("~"), ".claude", "logs",
                           "bash-edit-guard-override.jsonl")

# Paths the override policy does NOT cover. CLAUDE.md allows small deliberate local edits
# (CLAUDE.md itself, runbooks, docs, machine-local config); it forbids bulk refactors and
# shell-driven cross-project edits. These patterns are the forbidden half made checkable.
SUSPICIOUS = [
    (re.compile(r"(^|/)src/"), "application source"),
    (re.compile(r"(^|/)drizzle/|(^|/)migrations?/"), "database migration"),
    (re.compile(r"package(-lock)?\.json$|pnpm-lock|yarn\.lock"), "dependency manifest/lockfile"),
    (re.compile(r"(^|/)\.github/"), "CI configuration"),
    (re.compile(r"(^|/)scripts/.*\.(sh|mjs|ts|js)$"), "operational script"),
]
BULK_TARGETS = 3           # >= this many files in ONE override call is a bulk write
FREQUENCY_LIMIT = 5        # overrides per window before frequency is flagged
REPEAT_LIMIT = 3           # same target this many times = standing workaround


def load(path, days):
    if not os.path.exists(path):
        return None, []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows, skipped = [], 0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            at = datetime.strptime(r["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            skipped += 1
            continue
        if at >= cutoff:
            r["_at"] = at
            rows.append(r)
    if skipped:
        print(f"  ⚠ {skipped} unparseable row(s) skipped — malformed, not empty. Do not read as zero.")
    return len(rows), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--log", default=DEFAULT_LOG)
    a = ap.parse_args()

    n, rows = load(a.log, a.days)
    print(f"\nedit-guard override audit · last {a.days} day(s) · {a.log}")
    if n is None:
        print("  no log file — the override has never been exercised on this machine "
              "(or the guard is not wired; prove it with the guard-health check).")
        return 0
    if not rows:
        print("  0 overrides in the window. Nothing to review.")
        return 0

    print(f"  {len(rows)} override event(s):\n")
    for r in rows:
        files = r.get("protected") or r.get("targets") or []
        print(f"    {r['at']}  who=UNKNOWN (not stamped by the harness)  cwd={r.get('cwd','?')}")
        for f in files:
            print(f"        → {f}")

    flags = []
    if len(rows) > FREQUENCY_LIMIT:
        flags.append(f"FREQUENCY: {len(rows)} overrides in {a.days} days (>{FREQUENCY_LIMIT}). "
                     "An exception used this often is a workflow, not an exception — find what is "
                     "forcing it.")

    counts = collections.Counter(f for r in rows for f in (r.get("protected") or []))
    for target, c in counts.items():
        if c >= REPEAT_LIMIT:
            flags.append(f"REPETITION: {target} overridden {c}× — a standing workaround. Either "
                         "allowlist it deliberately or fix the underlying need; do not keep "
                         "spending the override on it.")

    for r in rows:
        files = r.get("protected") or []
        if len(files) >= BULK_TARGETS:
            flags.append(f"BULK: {r['at']} overrode {len(files)} files in one call — CLAUDE.md "
                         "forbids bulk refactors via the override.")
        for f in files:
            for pat, label in SUSPICIOUS:
                if pat.search(f):
                    flags.append(f"SUSPICIOUS TARGET: {f} ({label}) at {r['at']} — outside the "
                                 "small-local-edit envelope the policy allows.")

    print()
    if flags:
        print(f"  ⚠ {len(flags)} flag(s) — heuristics, for review, not verdicts:")
        for f in dict.fromkeys(flags):
            print(f"      • {f}")
        print("\n  Per CLAUDE.md, every override owes a `git diff`/`git status` check or a "
              "maintenance-log note. If a flagged event has neither, that is the finding.")
    else:
        print("  ✓ no flags: within frequency, no repeated target, no suspicious path, no bulk write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
