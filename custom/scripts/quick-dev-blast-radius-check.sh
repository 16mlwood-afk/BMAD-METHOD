#!/usr/bin/env bash
# ============================================================================
# quick-dev-blast-radius-check.sh — deterministic backstop for quick-dev's
# scope ceiling (the "blast-radius eligibility gate").
#
# Implements the enforcement tier behind the prose classification in
# _bmad/bmm/workflows/shared/blast-radius-eligibility.md. Prose asks the agent
# to classify honestly; THIS script checks the OBSERVED diff so an autonomous
# run cannot rationalize past a schema/auth/payments/infra change or a diff
# that has quietly outgrown "small, decided work".
#
# Invoked two ways:
#   1. From quick-dev step-07, before commit:   (LAYER B, agent-invoked)
#        scripts/quick-dev-blast-radius-check.sh <baseline_commit>
#      → inspects <baseline_commit>..HEAD + working tree.
#   2. From a git pre-push hook:                 (LAYER C, agent-independent)
#        scripts/quick-dev-blast-radius-check.sh
#      → inspects the commits being pushed (merge-base with the default branch).
#
# MODE (warn vs gate) and thresholds come from _bmad/bmm/config.yaml → quick_dev:
#   quick_dev.mode            warn | gate     (default: warn)
#   quick_dev.max_files       integer         (default: 15)
#   quick_dev.max_diff_lines  integer         (default: 600)
# In `warn` mode this script ALWAYS exits 0 (prints findings, never blocks).
# In `gate` mode it exits 2 when a HARD trigger fires (override: see below).
# Promote a project warn→gate only once its false-positive rate is proven low.
#
# Override-with-logging (gate mode only): set QUICK_DEV_OVERRIDE="<reason>" to
# pass despite a trigger. The reason is printed so it lands in the record.
# Never a silent override.
#
# Synced from ~/bmad-method-v6/custom/scripts/ into every BMAD-managed project's
# ./scripts/. DO NOT edit in projects directly — edit the fork source and re-sync.
# ============================================================================

set -uo pipefail

# --- Resolve roots (worktree-safe) -----------------------------------------
if ! REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  echo "quick-dev blast-radius: not in a git repo — skipping." >&2
  exit 0
fi
CONFIG="$REPO_ROOT/_bmad/bmm/config.yaml"

# --- Config (lightweight scalar reads; defaults if absent) -----------------
cfg() { # cfg <key> <default> — reads `quick_dev:`-block scalar `<key>: value`
  local key="$1" def="$2" val=""
  if [[ -f "$CONFIG" ]]; then
    val=$(awk -v k="$key" '
      /^quick_dev:/ {inblk=1; next}
      inblk && /^[^[:space:]]/ {inblk=0}
      inblk && $1 == k":" {print $2; exit}
    ' "$CONFIG" 2>/dev/null | tr -d '"'"'"'')
  fi
  echo "${val:-$def}"
}
MODE=$(cfg mode warn)
MAX_FILES=$(cfg max_files 15)
MAX_LINES=$(cfg max_diff_lines 600)

# --- Determine the diff range ----------------------------------------------
# Arg = baseline commit (step-07). No arg = pre-push: merge-base with default branch.
RANGE_DESC=""
if [[ $# -ge 1 && -n "${1:-}" && "$1" != "NO_GIT" ]]; then
  BASE="$1"
  RANGE_DESC="$BASE..working-tree"
  CHANGED=$(git diff --name-only "$BASE" 2>/dev/null; git diff --name-only --cached "$BASE" 2>/dev/null)
  NUMSTAT=$(git diff --numstat "$BASE" 2>/dev/null)
else
  # pre-push: compare against the default branch's merge-base
  DEFAULT_REF=""
  for ref in origin/main origin/master main master; do
    if git rev-parse --verify --quiet "$ref" >/dev/null 2>&1; then DEFAULT_REF="$ref"; break; fi
  done
  if [[ -z "$DEFAULT_REF" ]]; then
    echo "quick-dev blast-radius: no default branch to compare against — skipping." >&2
    exit 0
  fi
  BASE=$(git merge-base HEAD "$DEFAULT_REF" 2>/dev/null)
  RANGE_DESC="$DEFAULT_REF..HEAD"
  CHANGED=$(git diff --name-only "$BASE" HEAD 2>/dev/null)
  NUMSTAT=$(git diff --numstat "$BASE" HEAD 2>/dev/null)
fi

# Exclude BMAD-managed / deploy-irrelevant paths — planning docs and workflow
# text are not code blast radius. Mirrors the deploy contract's irrelevant-paths
# filter. Conservative by design: judge real code surface, not doc churn.
CHANGED=$(printf '%s\n' "$CHANGED" | sed '/^$/d' \
  | grep -vE '^(_bmad/|_bmad-output/|\.claude/|docs/)' | sort -u)
[[ -z "$CHANGED" ]] && { echo "quick-dev blast-radius: no code changes detected ($RANGE_DESC)."; exit 0; }

FILE_COUNT=$(printf '%s\n' "$CHANGED" | grep -c . )
# Sum added+deleted lines (numstat: adds<TAB>dels<TAB>path), excluding the same
# deploy-irrelevant paths and binary files (numstat marks those with "-").
LINE_COUNT=$(printf '%s\n' "$NUMSTAT" | awk '
  $3 ~ /^(_bmad\/|_bmad-output\/|\.claude\/|docs\/)/ {next}
  $1 ~ /^[0-9]+$/ {a+=$1; d+=$2}
  END {print a+d+0}')

# --- HARD-trigger path globs (defaults; project may add via config later) --
declare -a TRIGGERS=()
hit() { printf '%s\n' "$CHANGED" | grep -iE "$1" | head -3; }

m=$(hit '(^|/)(migrations?|drizzle)/|schema\.(ts|sql|prisma)$|\.sql$'); [[ -n "$m" ]] && TRIGGERS+=("schema/migration → $(echo "$m" | tr '\n' ' ')")
m=$(hit '(^|/)(auth|authentication|authz|permissions?|middleware|session)/|auth\.(ts|tsx)$|api-?key'); [[ -n "$m" ]] && TRIGGERS+=("auth/permissions → $(echo "$m" | tr '\n' ' ')")
m=$(hit '(^|/)(payments?|billing|checkout|ledger|invoice|pricing)/|(payment|billing|ledger)\.(ts|tsx)$'); [[ -n "$m" ]] && TRIGGERS+=("payments/billing → $(echo "$m" | tr '\n' ' ')")
# Infra is matched by directory or specific filename, NOT loose substrings —
# a UI file like `listing-queue-view.tsx` must not trip "queue".
m=$(hit 'instrumentation\.(ts|js)$|(^|/)(workers?|queues)/|bullmq|(^|/)\.env|(^|/)(railway\.(toml|json)|Dockerfile|docker-compose\.ya?ml)$|(^|/)schema-server/'); [[ -n "$m" ]] && TRIGGERS+=("shared-infra → $(echo "$m" | tr '\n' ' ')")

OVER=""
[[ "$FILE_COUNT" -gt "$MAX_FILES" ]] && OVER="$OVER files=$FILE_COUNT>$MAX_FILES"
[[ "$LINE_COUNT" -gt "$MAX_LINES" ]] && OVER="$OVER lines=$LINE_COUNT>$MAX_LINES"
[[ -n "$OVER" ]] && TRIGGERS+=("size over threshold →$OVER")

# --- Report ----------------------------------------------------------------
echo "── quick-dev blast-radius check ($RANGE_DESC) ──"
echo "   files=$FILE_COUNT (max $MAX_FILES)  diff-lines=$LINE_COUNT (max $MAX_LINES)  mode=$MODE"

if [[ ${#TRIGGERS[@]} -eq 0 ]]; then
  echo "   ✓ in-bounds for quick-dev."
  exit 0
fi

echo "   ⚠ HARD trigger(s) — this task may have outgrown quick-dev:"
for t in "${TRIGGERS[@]}"; do echo "     • $t"; done
echo "   → quick-dev ships small, decided work. Consider rerouting to quick-spec/PRD."

if [[ "$MODE" != "gate" ]]; then
  echo "   (warn-only: not blocking. Set quick_dev.mode: gate in config.yaml to enforce.)"
  exit 0
fi

if [[ -n "${QUICK_DEV_OVERRIDE:-}" ]]; then
  echo "   ⚠ OVERRIDE: proceeding despite trigger. Reason: $QUICK_DEV_OVERRIDE"
  echo "   (Logged — record this in the PR description.)"
  exit 0
fi

echo "   ✗ BLOCKED (gate mode). To override: QUICK_DEV_OVERRIDE=\"reason\" with the reason logged."
exit 2
