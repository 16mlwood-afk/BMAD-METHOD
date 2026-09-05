#!/usr/bin/env bash
# check-fork-gap-schema.sh — schema gate for docs/fork-gaps.md (typed ledger, schema v1).
#
# ALL findings are ERRORS, because every one of them is mechanical: a missing required field,
# an unknown enum value, a conditional field absent for the state that requires it, a marker
# too short to prove anything, a state blob left on a heading, or a missing ### Incident
# block. Nothing here is a judgement call — judgement lives in check-fork-gap-stale-open.sh,
# which never blocks on a sweep.
#
# WHICH findings BLOCK is scoped to the entries a commit actually touches (2026-07-31). The
# rules are unchanged and just as strict; what changed is blast radius. This is ONE
# append-only file written by many sessions, and blocking the whole commit on any finding
# anywhere in it meant one bad entry froze gap logging for everyone — a session would author
# a valid entry, hit a wall left days earlier by someone else, abandon the commit, and leave
# its entry dirty. Three entries were stranded that way before it was noticed; logging fell
# from 12-14/day to 1-4/day.
#
# Scoping applies ONLY when the register is staged (the only path the pre-commit gate takes).
# A manual run, or `--all`, has no staged diff to scope against and audits the whole file —
# so this stays a real sweep tool, and pre-existing rot is always printed either way.
#
# Parser + rules: tools/lib/fork_gap_lint.py (one parser shared by all three checks).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" schema
