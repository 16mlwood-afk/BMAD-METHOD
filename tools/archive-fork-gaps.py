#!/usr/bin/env python3
"""archive-fork-gaps.py — move terminal entries out of the live register.

fork-gaps.md is open-only by construction: "the whole file IS the backlog, and a plain
heading grep = the open set." Schema v1 moved closure into the header's `state:` field, which
retired the old `[RESOLVED …]` heading tag — and with it the tag-based archive step. Without
this, terminal entries accumulate in the live file and the open-only property quietly decays.

DELIBERATELY NOT IN THE PRE-COMMIT GATE. The three validators never mutate the register;
that is their oldest invariant and the reason a detector can be trusted. Archiving DOES
mutate, so it is an explicit, human-invoked command. The gate's only role is to NOTICE the
backlog (check-fork-gap-schema warns when terminal entries are still live) and say so.

    python3 tools/archive-fork-gaps.py            # dry run — default, writes nothing
    python3 tools/archive-fork-gaps.py --write    # apply

Terminal = `state: closed` or `state: superseded`. Everything else names owed work — `partly`,
`blocked` and `fork-fixed-distribution-owed` all stay live, which is the whole point of having
those states rather than a boolean.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.environ.get("FORK_GAP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
GAPS = os.path.join(ROOT, "docs", "fork-gaps.md")
ARCHIVE = os.path.join(ROOT, "docs", "fork-gaps-archive.md")

TERMINAL = ("closed", "superseded")


def split_entries(text: str):
    """Return (head, [chunk, ...]) splitting at top-level `## ` after the `## Open` marker."""
    idx = text.index("\n## Open")
    head, body = text[: idx + 1], text[idx + 1 :]
    chunks = re.split(r"(?m)^(?=## )", body)
    return head, chunks


def state_of(chunk: str) -> str:
    m = re.search(r"(?m)^state:\s*(\S+)", chunk)
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply (default is a dry run)")
    args = ap.parse_args()

    text = open(GAPS).read()
    head, chunks = split_entries(text)

    keep, move = [], []
    for c in chunks:
        (move if c.startswith("## ") and state_of(c) in TERMINAL else keep).append(c)

    if not move:
        print("archive-fork-gaps: nothing terminal in the live register.")
        return 0

    for c in move:
        print(f"  → {state_of(c):11} {c.split(chr(10))[0][3:100]}")
    print(f"archive-fork-gaps: {len(move)} entry/entries to archive.")

    # CONSERVATION: the chunk list is partitioned, so every byte of the body must survive in
    # exactly one half. Checked on characters, not lines — splitting each half on "\n"
    # double-counts the boundary and produces a phantom off-by-one per half. An archive move
    # must never be where content is lost, so this aborts rather than writing a partial file.
    if len(keep) + len(move) != len(chunks):
        print("ABORT — chunk accounting does not balance; nothing written.", file=sys.stderr)
        return 2
    if len("".join(keep)) + len("".join(move)) != len("".join(chunks)):
        print("ABORT — byte accounting does not balance; nothing written.", file=sys.stderr)
        return 2

    if not args.write:
        print("\nDRY RUN — nothing written. Re-run with --write to apply.")
        return 0

    open(GAPS, "w").write((head + "".join(keep)).rstrip("\n") + "\n")
    archive = open(ARCHIVE).read().rstrip("\n")
    open(ARCHIVE, "w").write(archive + "\n\n" + "".join(move).strip("\n") + "\n")
    print(f"\nWRITTEN — {len(move)} entry/entries moved to docs/fork-gaps-archive.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
