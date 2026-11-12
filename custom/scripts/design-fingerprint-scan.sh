#!/usr/bin/env bash
# ============================================================================
# design-fingerprint-scan.sh — deterministic returned-artifact scan for the
# machine-detectable subset of the AI-fingerprint taxonomy in
# _bmad/bmm/workflows/design/shared/design-standards.md § AI Fingerprint
# Detection (skills-layout projects: _bmad/bmad-shared/design-standards.md).
#
# Scans design artifacts (.dc.html frames, tokens.css, component .tsx/.html)
# for taxonomy rows that have a reliable markup/CSS signature. Everything else
# in the taxonomy is ADVISORY — this script names that remainder in its own
# output so a clean scan can never be read as design compliance.
#
# Invoked from:
#   1. design-ingest step-03 (ingest boundary) — findings are stamped into the
#      manifest's fingerprint_scan: block; they never block the emit.
#   2. design-review-pr step-02 §8 (F-FPSCAN-01, source-grep lane) — findings
#      become P1/P2 rule entries.
#   3. Ad hoc: scripts/design-fingerprint-scan.sh [options] <file>...
#
# Options:
#   --allow <rule-id>[,<rule-id>...]   Declared brand-identity exceptions.
#       Matches for these rules are still REPORTED (DECLARED-EXCEPTION lines —
#       visibility is the point) but do not fail the scan. Only pass rules the
#       project's brand identity / design policy explicitly declares.
#
# Exit codes: 0 = no failing deterministic findings (declared exceptions may
# exist); 1 = at least one failing deterministic finding; 2 = usage error.
#
# CEILING, stated plainly: this scan proves the PRESENCE of a signature, never
# the truth of "this design is fine". Zero matches ≠ compliant — most of the
# taxonomy (layout, content, structural categories) is not machine-decidable.
# ============================================================================
set -euo pipefail

ALLOW=""
FILES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow)
      [[ $# -ge 2 ]] || { echo "usage: --allow <rule-id>[,<rule-id>...]" >&2; exit 2; }
      ALLOW="${ALLOW:+$ALLOW,}$2"; shift 2 ;;
    --help|-h)
      sed -n '2,33p' "$0"; exit 0 ;;
    -*)
      echo "unknown option: $1" >&2; exit 2 ;;
    *)
      FILES+=("$1"); shift ;;
  esac
done
[[ ${#FILES[@]} -gt 0 ]] || { echo "usage: design-fingerprint-scan.sh [--allow ids] <file>..." >&2; exit 2; }

is_allowed() { [[ ",$ALLOW," == *",$1,"* ]]; }

# Rule table: id | grep -E pattern (line-level, case-insensitive) | taxonomy row
# Signatures are deliberately conservative — a missed cosmetic match is
# recoverable at review; a false positive erodes trust in the scan.
RULES=(
  # Category 3 — Left-border accent containers: CSS inline/stylesheet form.
  'left-border-accent|border-left:[[:space:]]*[2-9]px[[:space:]]+solid|Cat.3 Left-border accent containers'
  # Same rule, Tailwind form: a border-l width ≥2 (border-l-2/-4/-8/-[Npx]).
  'left-border-accent|border-l-(2|4|8|\[[0-9]+px\])|Cat.3 Left-border accent containers'
  # Category 3 — Gradient anything.
  'gradient|bg-gradient-to-|Cat.3 Gradient anything'
  'gradient|(linear|radial|conic)-gradient\(|Cat.3 Gradient anything'
  # Category 3 — AI purple (Tailwind classes + the common purple hexes).
  'ai-purple|(violet|indigo|purple)-(400|500|600|700)|Cat.3 AI purple'
  'ai-purple|#(6d28d9|7c3aed|8b5cf6|6366f1|4f46e5|a855f7|9333ea)|Cat.3 AI purple'
  # Category 3 — Shadow stacking (Tailwind heavy shadows).
  'shadow-heavy|shadow-(lg|xl|2xl)|Cat.3 Shadow stacking'
  # Category 4 — Glassmorphism.
  'glassmorphism|backdrop-blur|Cat.4 Glassmorphism'
  'glassmorphism|backdrop-filter:[[:space:]]*blur|Cat.4 Glassmorphism'
  # Category 4 — Hover scale/lift transforms (Tailwind form).
  'hover-transform|hover:(scale-|-translate-y-)|Cat.4 Hover scale/lift'
  # Category 2 — uppercase + letter-spacing labels (both tokens on one line).
  'uppercase-tracking|uppercase[^\n]*tracking-(wide|wider|widest)|Cat.2 ALL CAPS labels'
  'uppercase-tracking|tracking-(wide|wider|widest)[^\n]*uppercase|Cat.2 ALL CAPS labels'
  'uppercase-tracking|text-transform:[[:space:]]*uppercase[^\n]*letter-spacing|Cat.2 ALL CAPS labels'
  'uppercase-tracking|letter-spacing:[[:space:]]*0?\.[0-9]+em[^\n]*text-transform:[[:space:]]*uppercase|Cat.2 ALL CAPS labels'
)

FINDINGS=0
EXCEPTIONS=0

for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "SKIP (not a file): $f" >&2
    continue
  fi
  # seen-set per file so the two patterns of one rule don't double-count a line
  seen=""
  for rule in "${RULES[@]}"; do
    id="${rule%%|*}"; rest="${rule#*|}"; pat="${rest%|*}"; row="${rest##*|}"
    while IFS= read -r hit; do
      [[ -n "$hit" ]] || continue
      line="${hit%%:*}"
      key="$id:$line"
      [[ ",$seen," == *",$key,"* ]] && continue
      seen="$seen,$key"
      construct="$(echo "${hit#*:}" | sed -e 's/^[[:space:]]*//' | cut -c1-160)"
      if is_allowed "$id"; then
        echo "DECLARED-EXCEPTION $id $f:$line :: $construct  [$row]"
        EXCEPTIONS=$((EXCEPTIONS + 1))
      else
        echo "FINDING $id $f:$line :: $construct  [$row]"
        FINDINGS=$((FINDINGS + 1))
      fi
    done < <(grep -inE "$pat" "$f" 2>/dev/null || true)
  done
done

echo ""
echo "ADVISORY (no machine signature — these taxonomy rows still require agent/human review):"
echo "  Cat.1 all rows (stat cards, bento, card-wrapping, symmetric padding, hero, dashboard-as-default);"
echo "  Cat.2 size hierarchy / monospace misuse / decorative titles; Cat.3 multi-color badges,"
echo "  colored icon backgrounds, general colored borders; Cat.4 stat-card-with-icon, segmented"
echo "  controls, empty-state illustrations, animated counters, skeletons, toasts, dividers,"
echo "  rounded-full controls; Cat.5 all rows (emoji, copy, placeholders, marketing, tooltips);"
echo "  Cat.6 all rows; and the composite-test verdict itself."
echo ""
echo "SCAN RESULT: $FINDINGS deterministic finding(s), $EXCEPTIONS declared exception(s)."
echo "Zero findings is NOT design compliance — the advisory rows above are unexamined by this scan."

[[ $FINDINGS -eq 0 ]] && exit 0 || exit 1
