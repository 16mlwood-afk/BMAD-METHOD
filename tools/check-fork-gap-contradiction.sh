#!/usr/bin/env bash
# check-fork-gap-contradiction.sh — prose says the fix landed; the field still says it hasn't.
#
# WARN-ONLY BY DESIGN, and the reason is not timidity. The register's schema gate is armed in
# pre-commit, so an ERRORING keyword heuristic would block EVERY session's commit to this file
# on a single false positive — which happened twice this week from unrelated schema omissions.
# A gate that stops the whole team on a guess is the one that gets deleted. Promotion to error
# needs the same bar as every other gate here: a proven-quiet window.
#
# Rule + rationale: tools/lib/fork_gap_lint.py (one parser shared by all checks).
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/tools/lib/fork_gap_lint.py" contradiction
