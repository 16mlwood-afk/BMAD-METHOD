#!/usr/bin/env bash
# warn-githook-distribution.sh — FG-2026-07-25-09, fix (1).
#
# Fires at fork-commit time when a custom/githooks/*.sh change is staged, to say
# the one thing nothing else in the loop says: THIS HOOK FIRES IN ZERO PROJECTS
# UNTIL SYNC.
#
# WHY THIS AND NOT sync --check. `sync-bmad-workflows.sh --check` ALREADY reports
# per-project githook drift ("↳ githooks (N entrypoint(s) missing/outdated)") — the
# detection exists and is good. But it is PULL-based: it tells you only if you
# think to ask, and the dangerous moment is the one where you DON'T, because you
# just authored the hook, measured its behaviour against real files, and are about
# to describe it as a live deterministic tier. That is exactly what happened on
# 2026-07-25: a B7 clause was added to check-design-brief-completeness.sh, measured
# at 6 true fires / 0 false positives across 44 briefs, and reported as an
# operative commit-time warn — while the project copies were byte-stale and it
# fired nowhere. The measurement was real; the deployment was zero.
#
# A stale githook is not ordinary sync lag. Stale workflow PROSE degrades
# gracefully (a session behaves like last week). A stale HOOK makes the fork file,
# any honest-tiering table citing it, and the wave's own measurement all assert a
# deterministic tier that does not exist anywhere — and the enforcement-honesty
# doctrine forbids describing a tier as live when it is not.
#
# WARN-ONLY, ALWAYS EXIT 0. This is a legibility signal, not a gate: blocking a
# fork commit because distribution hasn't happened yet would be wrong (authoring
# and distribution are deliberately separate tracks, and the fleet re-sync is
# owner-gated). It exists to make the claim honest at the moment the claim is made.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

staged=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '^custom/githooks/.*\.sh$' || true)
[ -z "$staged" ] && exit 0

printf '\n' >&2
printf 'githook-distribution [WARN]: staged fork githook change(s):\n' >&2
printf '%s\n' "$staged" | sed 's/^/  · /' >&2
printf '\n' >&2
printf '  These fire in ZERO projects until sync-bmad-workflows.sh runs.\n' >&2
printf '  The fork copy is NOT the running gate — each project runs its own .githooks/ copy.\n' >&2
printf '\n' >&2
printf '  Before describing this as a live DETERMINISTIC tier anywhere (a tiering table,\n' >&2
printf '  a STATUS entry, a PR body, a report to the owner): either run the sync, or say\n' >&2
printf '  plainly that the check is AUTHORED, NOT DEPLOYED. A measurement against real\n' >&2
printf '  files proves the LOGIC, never the DEPLOYMENT.\n' >&2
printf '\n' >&2
printf '  Check where it stands:  ./sync-bmad-workflows.sh --check\n' >&2
printf '  Distribute:             ./sync-bmad-workflows.sh          (fleet fan-out is owner-gated)\n' >&2
printf '\n' >&2

exit 0
