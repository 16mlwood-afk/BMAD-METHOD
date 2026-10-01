#!/usr/bin/env bash
# check-fork-gap-stale-open.sh — the same check, two meanings.
#
#   --creation-mode  a NEW entry (added in the staged diff) whose marker ALREADY exists in
#                    its target is an ERROR: either the marker is too generic to prove
#                    anything, or the gap is already fixed and should not be logged open.
#                    This is the check that would have caught both bad markers written on
#                    2026-07-25 (`.claude/worktrees/`, `inert-scope sweep`).
#   (default/sweep)  a pre-existing entry whose marker is present is a WARNING — a
#                    stale-open candidate for a human to verify.
#
# NEVER closes anything, NEVER mutates the register. A marker proves a STRING exists, not
# that a gap is resolved: open the implementing section and read it before changing state.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" stale-open "$@"
