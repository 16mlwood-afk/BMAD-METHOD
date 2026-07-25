#!/usr/bin/env sh
# .githooks/check-design-brief-completeness.sh — STD-HOOKACTIVATE-001
#
# Warn-first (Phase 1) PRODUCER-side gate for design-handoff briefs — the
# deterministic tier-6 companion to the in-flow assertion in design-handoff
# step-04 §3. When a design-brief-*.md is staged, it verifies the Block B
# `frames:` contract (what design-implement step-01 §SHARED.1b diffs the bundle
# against) is present, non-empty, unique, and mirrored in the §7 body — at commit
# time, outside the agent, independent of whether the design-handoff workflow ran.
#
# PHASE 1 = WARN ONLY: prints findings to stderr and ALWAYS exits 0, so it never
# blocks a commit while the false-positive rate is being observed. Promote to a
# hard gate (exit 1 on a finding) only after the warn phase proves quiet
# (warn-then-gate). The dispatcher's override is `git commit --no-verify` (logged).
#
# SCOPE (honest cede): INTERNAL consistency of the artifact only. It does NOT
# verify completeness-against-the-schema (whether every drawer that SHOULD exist
# was captured) — that needs the gather context and stays with design-handoff
# step-01 §5f + step-03 §3 + the downstream synthesize/implement gates.
#
# Registered in .githooks/gates.conf as: pre-commit .githooks/check-design-brief-completeness.sh
# Graceful: no-ops when no design-brief is staged, so it is safe in every project.
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
staged=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '(^|/)design-brief-[^/]*\.md$' || true)
[ -z "$staged" ] && exit 0

findings=0
warn() { printf 'design-brief-completeness [WARN]: %s\n' "$1" >&2; findings=$((findings + 1)); }

# Check ONE brief file's frames/§7 internal consistency. Mirrors design-handoff
# step-04 §3 (the in-flow tier). Uses while-read+case, never `for f in $frames`,
# so it is correct under both sh and zsh.
check_brief() {
  brief="$1"
  [ -f "$brief" ] || return 0

  frames=$(awk '
    NR==1 && $0=="---"{infm=1; next}
    infm && $0=="---"{exit}
    infm && /^frames:/{
      if ($0 ~ /\[/){ s=$0; sub(/^[^[]*\[/,"",s); sub(/\].*/,"",s); gsub(/,/," ",s); print s; next }
      blk=1; next }
    infm && blk && /^[[:space:]]*-[[:space:]]/{ s=$0; sub(/^[[:space:]]*-[[:space:]]*/,"",s); print s; next }
    infm && blk && /^[^[:space:]]/{ blk=0 }
  ' "$brief" | tr -d "\"'," | tr -s " " "\n" | sed '/^$/d')

  n=$(printf '%s\n' "$frames" | sed '/^$/d' | wc -l | tr -d ' ')
  if [ "$n" -eq 0 ]; then
    warn "$brief: no non-empty 'frames:' in Block B (brief-revision-policy.md §2 invariant 1a) — ships UNVERIFIED; design-implement's §SHARED.1b gate cannot bite."
    return 0
  fi

  dupes=$(printf '%s\n' "$frames" | sort | uniq -d)
  [ -n "$dupes" ] && warn "$brief: duplicate frame id(s) in 'frames:': $dupes — frame names must be unique."

  body=$(awk 'NR==1 && $0=="---"{infm=1;next} infm && $0=="---"{infm=0;next} !infm{print}' "$brief")
  missing=""
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$body" in *"$f"*) : ;; *) missing="$missing $f" ;; esac
  done <<EOF
$frames
EOF
  [ -n "$missing" ] && warn "$brief: frame id(s) in 'frames:' absent from the body / §7 Surface Inventory:$missing — Block B 'frames' must mirror the §7 rows."

  if printf '%s' "$body" | grep -qiE '^#+.*linked records'; then
    printf '%s' "$body" | grep -qiE 'surface inventory' \
      || warn "$brief: has a Linked Records (§2a) section but no §7 Surface Inventory — each linked record needs a lookup-drawer frame."
  fi

  # --- Handheld-First Declaration (design-handoff gate class (f)) --------------
  # WHY: gate (e) makes the deliverable be DRAWN at the canonical viewport; it does
  # not stop the artifact being a REVIEW BOARD at that viewport — co-equal comps,
  # rationale competing with the surface, state variants as peer mini-products.
  # Contract: custom/workflows/design/shared/operator-artifact-contract.md (B1-B6).
  # This is the deterministic-DETECTION tier for the brief artifact: it fires on the
  # staged file whether or not the workflow ran. Phase-1 WARN, like every check here.
  #
  # CONSERVATIVE BY CONSTRUCTION — it fires only on a brief that has ALREADY declared
  # itself handheld-first (a viewport contract naming mobile-first/handheld-first).
  # A desktop-only brief, an owner brief with an OPEN ambition, and any brief with no
  # viewport contract at all are silently skipped: the gate must never become a back
  # door that flags work the warn-only pending-policy path deliberately lets continue.
  #
  # MEASURED (2026-07-25, cash-recovery corpus of 41 real design briefs): fires on
  # exactly 2 — both handheld-first /inbound briefs that genuinely predate the
  # contract. Zero fires on the 39 desktop-only / owner / legacy briefs.
  #
  # KNOWN COVERAGE GAP (honest — do not claim this catches every handheld brief):
  # only 2 of those 41 briefs carry a `primary_viewport_class` field at all, so a
  # brief that declares its handheld posture in PROSE only (e.g. the 2026-07-19
  # /receive brief, which says "handheld-first" and "phone-primary" five times and
  # has no viewport-contract field) is invisible here. Widening the trigger to a bare
  # "mentions handheld-first" would fire on any brief that merely REFERENCES the
  # posture — including a desktop-only grading brief noting it was NOT flipped — so
  # the miss is accepted deliberately. Every brief generated by the current
  # brief-template renders §4g with the field, so the gap closes as the corpus turns
  # over; it is not a reason to loosen detection.
  check_handheld_declaration() {
    printf '%s' "$body" | grep -qiE 'primary_viewport_class' || return 0
    printf '%s' "$body" | grep -qiE 'mobile-first|handheld-first' || return 0

    if ! printf '%s' "$body" | grep -qiE 'handheld-first declaration'; then
      warn "$brief: declares a handheld-first viewport posture but carries no Handheld-First Declaration (§4g) — gate class (f). Five fields required: surface class · canonical viewport · additive viewports · scan/next-step loop · offline/degraded state treatment. See shared/operator-artifact-contract.md."
      return 0
    fi

    # Each of the two composition-specific fields must be present AND answered.
    # 'TBD' / 'responsive' / 'see policy' are non-answers by contract: "responsive"
    # names a technique, not a canonical viewport, and is the exact phrasing that
    # lets a generator pick desktop as the design.
    for label in 'scan */ *next-step loop' 'offline */ *degraded state treatment'; do
      row=$(printf '%s\n' "$body" | grep -iE "\| *${label} *\|" | head -1)
      if [ -z "$row" ]; then
        warn "$brief: Handheld-First Declaration is missing the '$(printf '%s' "$label" | tr -d '*')' field — gate class (f)."
        continue
      fi
      val=$(printf '%s' "$row" | cut -d'|' -f4 | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
      case "$val" in
        ''|-|[Nn]/[Aa]|TBD|tbd|[Tt][Bb][Dd]*|[Rr]esponsive*|[Ss]ee\ policy*)
          warn "$brief: Handheld-First Declaration field '$(printf '%s' "$label" | tr -d '*')' is a non-answer ('$val') — gate class (f) requires a real value."
          ;;
      esac
    done

    # §7 must carry the composition sequence, not just the frame list. Without it the
    # brief tells the designer WHAT to draw and never WHAT SHAPE to arrange it in —
    # which is the unspecified slot a generator fills with a review board.
    printf '%s' "$body" | grep -qiE 'states of this surface|canonical operational surface|artifact composition' \
      || warn "$brief: handheld-first brief whose §7 carries no artifact-composition instruction (canonical surface first → states strip → additive group → rationale LAST) — gate class (f). A frame list without a composition order commissions a review board."
  }
  check_handheld_declaration

  # Provenance of the depth passes (§4d rigor / §4e decision analysis).
  # WHY: both sections have a sanctioned by-hand fallback that renders an
  # IDENTICAL-looking block to the skill path, and every consumer (design-review-pr
  # step-01 -> {brief_rigor_map}) treats a populated section as evidence the pass
  # ran. Undeclared, the fallback manufactures the evidence that enforcement
  # succeeded — and C-RIGOR-01/C-DECISION-01 check the RENDERED SURFACE against
  # these sections, taking them as ground truth, so they structurally cannot catch
  # it. Net effect without this check: the only section the gate can fail is an
  # HONEST one (declared gaps give a reviewer something to flag; a hand-waved block
  # reads clean). Presence-of-a-declaration is the deterministic sliver; the
  # declaration itself stays SELF-REPORTED (tier-7 marker is the proof layer).
  if printf '%s' "$body" | grep -qiE '^#+[[:space:]]*4d\.'; then
    printf '%s' "$body" | grep -qE 'rigor_source' \
      || warn "$brief: has a §4d (Analytic depth) but no 'rigor_source' declaration — cannot tell whether the analytics-rigor skill ran or the inline fallback wrote it. Add 'rigor_source: skill | inline-fallback | not-applicable' (design-handoff step-01b §5c-2)."
  fi
  if printf '%s' "$body" | grep -qiE '^#+[[:space:]]*4e\.'; then
    printf '%s' "$body" | grep -qE 'decision_source' \
      || warn "$brief: has a §4e (Decision analysis) but no 'decision_source' declaration — a modelled distribution and a position size with unstated provenance. Add 'decision_source: skill | inline-fallback | not-applicable' (design-handoff step-01b §5c-3)."
  fi

  # Tier-7 cross-check: a `skill` claim is only evidence unless a matching
  # invocation marker exists. The PostToolUse:Skill hook (hooks.json) appends to
  # .claude/.depth-pass-invocations.jsonl whenever analytics-rigor or
  # decision-analysis is actually invoked.
  #
  # HONEST DEGRADATION — read this before trusting a silent pass: the marker file
  # is absent in any project where that hook is not installed (hooks ship on the
  # onboarding/hooks track, NOT via BMAD workflow sync). So "no marker file" means
  # UNVERIFIABLE, never verified — we do not warn on it, because warning on every
  # brief in every un-hooked project would be pure noise and would get the whole
  # gate ignored. The hole is real and named; do not read a quiet gate as proof.
  markers="$ROOT/.claude/.depth-pass-invocations.jsonl"
  if [ -f "$markers" ]; then
    if printf '%s' "$body" | grep -qE 'rigor_source:[[:space:]]*skill'; then
      grep -q '"skill":"analytics-rigor"' "$markers" 2>/dev/null \
        || warn "$brief: declares 'rigor_source: skill' but no analytics-rigor invocation marker exists in .claude/.depth-pass-invocations.jsonl — the claim is unsupported. Either the skill did not run, or the declaration is wrong."
    fi
    if printf '%s' "$body" | grep -qE 'decision_source:[[:space:]]*skill'; then
      grep -q '"skill":"decision-analysis"' "$markers" 2>/dev/null \
        || warn "$brief: declares 'decision_source: skill' but no decision-analysis invocation marker exists — the claim is unsupported."
    fi
  fi
}

# sh/dash word-splits unquoted $staged on newlines (design-brief filenames are
# kebab-case, no spaces); fine here. (zsh wouldn't, but the dispatcher runs `sh`.)
for brief in $staged; do
  check_brief "$ROOT/$brief"
done

if [ "$findings" -gt 0 ]; then
  printf 'design-brief-completeness: %s finding(s) (Phase-1 WARN — commit NOT blocked). Fix the §7/frames contract in design-handoff, or re-run delivery.\n' "$findings" >&2
fi
exit 0
