#!/usr/bin/env bash
# new-fork-gap.sh — print a correctly-shaped skeleton for a NEW docs/fork-gaps.md entry.
#
# WHY THIS EXISTS. The register is strict (seven required fields, a conditional field per
# state, an enum pair, a >=3-char marker, an `### Incident` block, a unique correctly-dated
# id) and until now the only machine-readable affordance was a validator that tells you the
# entry is wrong AFTER you hand-built it. That is backwards for the one activity the register
# depends on, and it is a tax at exactly the moment a session is closing out and least
# inclined to pay it. Logging rate is the thing we want to go UP; authoring cost is the lever.
#
# IT DOES NOT WRITE. Nothing in this tooling mutates the register — an appender would have to
# pick an insertion point in a file many sessions edit concurrently, which is the
# read-modify-write race the manifest contract already documents. Redirect it yourself.
#
# AN UNFILLED SKELETON CANNOT BE COMMITTED. Every slot prints as `<<FILL: …>>`, and
# check-fork-gap-schema REJECTS any field or body still carrying one. So the scaffold cannot
# become a machine for hollow entries that pass every mechanical rule.
#
#   bash tools/new-fork-gap.sh --title "the thing that broke" --scope fork \
#        --target custom/workflows/foo/steps/step-01.md --marker "some string" \
#        >> docs/fork-gaps.md
#
# Then fill the <<FILL:…>> slots and run:  bash tools/check-fork-gap-schema.sh
#
# Omit any flag to get a guided placeholder for it. `--help` lists them all.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" new-entry "$@"
