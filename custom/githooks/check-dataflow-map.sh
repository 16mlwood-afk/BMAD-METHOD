#!/usr/bin/env bash
# ============================================================================
# check-dataflow-map.sh — deterministic backstop for STD-DATAFLOW-001.
#
# Implements the enforcement tier behind the prose in shared/dataflow-standard.md.
# Prose asks the author to document a seam; THIS script checks the OBSERVED diff so
# a cross-boundary change can't land while docs/data-flows.md silently goes stale.
#
# It guards CHANGE↔MAP CORRESPONDENCE, not prose quality: if a tracked seam file
# changed in this commit but the data-flow map did NOT, it flags it. It cannot see a
# brand-new integration outside the tracked paths — that stays awareness-tier (the
# CLAUDE.md pointer + the seam-touching workflows' "update the map?" step).
#
# Invoked as a pre-commit gate by the .githooks dispatcher (reads staged files).
#
# MODE (warn vs gate) + paths come from _bmad/bmm/config.yaml → dataflow:
#   dataflow.mode       warn | gate     (default: warn)
#   dataflow.map_path   path            (default: docs/data-flows.md)
# In `warn` mode this script ALWAYS exits 0 (prints findings, never blocks).
# In `gate` mode it exits 2 when a seam changed without a map update.
# Promote a project warn→gate only once its false-positive rate is proven low.
#
# Override-with-logging (gate mode only): set DATAFLOW_OVERRIDE="<reason>" to pass
# despite a finding. The reason is printed so it lands in the record. Never silent.
#
# Synced from ~/bmad-method-v6/custom/githooks/ into every BMAD-managed project's
# ./.githooks/. DO NOT edit in projects directly — edit the fork source and re-sync.
# ============================================================================

set -uo pipefail

if ! REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  echo "dataflow-map: not in a git repo — skipping." >&2
  exit 0
fi
CONFIG="$REPO_ROOT/_bmad/bmm/config.yaml"

cfg() { # cfg <key> <default> — reads the `dataflow:`-block scalar `<key>: value`
  local key="$1" def="$2" val=""
  if [[ -f "$CONFIG" ]]; then
    val=$(awk -v k="$key" '
      /^dataflow:/ {inblk=1; next}
      /^[^[:space:]]/ {inblk=0}
      inblk && $1 == k":" {sub(/^[[:space:]]*[^:]+:[[:space:]]*/,""); gsub(/[[:space:]]+#.*/,""); gsub(/^"|"$/,""); print; exit}
    ' "$CONFIG")
  fi
  printf '%s' "${val:-$def}"
}

MODE=$(cfg mode warn)
MAP_PATH=$(cfg map_path "docs/data-flows.md")

# Tracked cross-boundary seam paths (the conservative set — bias to few false positives).
# A change under these, without a map change, is what we flag.
is_seam() {
  case "$1" in
    schema-server/src/schemas/*) return 0 ;;   # cross-boundary schemas (canonical)
    */webhooks/*|webhooks/*)     return 0 ;;   # webhook handlers/validators/routes
    *) return 1 ;;
  esac
}

# Staged files for this commit (added/copied/modified/renamed).
CHANGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null)
[[ -z "$CHANGED" ]] && exit 0   # nothing staged -> nothing to check

seam_hits=()
map_changed=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  [[ "$f" == "$MAP_PATH" ]] && map_changed=1
  is_seam "$f" && seam_hits+=("$f")
done <<< "$CHANGED"

# No seam touched, or the map was updated alongside -> all good, stay quiet.
[[ ${#seam_hits[@]} -eq 0 ]] && exit 0
[[ $map_changed -eq 1 ]] && exit 0

# A tracked seam changed with no matching map update.
{
  echo ""
  echo "⚠ STD-DATAFLOW-001: a cross-boundary seam changed but $MAP_PATH was not updated."
  echo "  Seam files in this commit:"
  for f in "${seam_hits[@]}"; do echo "    - $f"; done
  echo "  → Update $MAP_PATH (source · ingress · payload · direction · authority) so the"
  echo "    data-flow map stays in sync. See shared/dataflow-standard.md."
} >&2

if [[ "$MODE" == "gate" ]]; then
  if [[ -n "${DATAFLOW_OVERRIDE:-}" ]]; then
    echo "  dataflow-map: OVERRIDE — proceeding despite finding. Reason: $DATAFLOW_OVERRIDE" >&2
    exit 0
  fi
  echo "  (gate mode: blocking. Set dataflow.mode: warn in config.yaml, update the map, or set DATAFLOW_OVERRIDE=\"reason\".)" >&2
  exit 2
fi

echo "  (warn-only: not blocking. Set dataflow.mode: gate in config.yaml to enforce.)" >&2
exit 0
