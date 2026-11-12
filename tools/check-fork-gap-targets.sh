#!/usr/bin/env bash
# check-fork-gap-targets.sh — the `target:` pointer an actioning session depends on.
#
# Every entry names a target — the load-bearing pointer a cold session uses days later to find
# what to edit. Under schema v1 that pointer lives in the typed header, so severity can finally
# be SCOPE-AWARE: a `scope: fork` target that does not resolve in the fork tree is rot and an
# ERROR; any other scope (project / machine-local / harness) legitimately does not resolve from
# here and is a WARNING.
#
# Before the typed header this could only ever warn, because a prose target and a rotted path
# were indistinguishable — which is how six pointers rotted past a directory reorg with nothing
# failing (fork-gaps 2026-07-11 "Target file unvalidated").
#
# Scoped to touched entries since 2026-07-31, same rule and same reason as the schema check:
# rot you did not write and are not editing is REPORTED IN FULL but does not block your commit.
# The case that forced it — FG-2026-07-30-10's target rotted in a directory reorg and blocked
# two unrelated sessions' entries for a day. Scoping applies only when the register is staged;
# a manual run (or `--all`) audits everything.
#
# Parser + rules: tools/lib/fork_gap_lint.py (one parser shared by all three checks).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" targets
