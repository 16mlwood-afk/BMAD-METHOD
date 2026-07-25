#!/usr/bin/env bash
# check-fork-gap-schema.sh — schema gate for docs/fork-gaps.md (typed ledger, schema v1).
#
# ALL findings are ERRORS and block the commit, because every one of them is mechanical:
# a missing required field, an unknown enum value, a conditional field absent for the state
# that requires it, a marker too short to prove anything, a state blob left on a heading,
# or a missing ### Incident block. Nothing here is a judgement call — judgement lives in
# check-fork-gap-stale-open.sh, which never blocks on a sweep.
#
# Parser + rules: tools/lib/fork_gap_lint.py (one parser shared by all three checks).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" schema
