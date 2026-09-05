#!/usr/bin/env bash
# check-fork-gap-orphan-annotation.sh — a later annotation must be reachable FROM the entry it annotates.
#
# fork-gaps.md is an append-only log past 5,000 lines, so an annotation of an older entry
# necessarily lands far from it. Anyone reaching the original the normal way — a grep, a
# triage sweep, the stale-open detector — reads its header and never learns the annotation
# exists. Orphaning is the DEFAULT outcome here, not the exception.
#
# Origin (2026-07-28): FG-2026-07-26-04's re-confirmation landed 2,170 lines below it. The
# orphaned content was the inoculation against a REPRODUCIBLE FALSE DIAGNOSIS every blocked
# agent derives independently — exactly what a blocked reader needs, and exactly what they
# would not have found. On its first run this check found 4 further orphans, one of them
# created the same day by the session that wrote the check.
#
# WARN-ONLY and the remedy is ADDITIVE: add `see_also` to the referenced entry. It never asks
# anyone to alter a prior finding — that is the quiet history-rewrite the append-only
# discipline exists to prevent. A pointer is metadata, not a claim.
#
# Parser + rules: tools/lib/fork_gap_lint.py (one parser shared by all four checks).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" orphan-annotation
