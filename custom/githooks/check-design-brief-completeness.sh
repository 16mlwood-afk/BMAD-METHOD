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

# REACHABILITY SELF-CHECK — a gate that no-ops because its input is INVISIBLE must say so,
# or its silence reads as a pass (fork-gaps FG-2026-07-25-10).
#
# This gate only ever sees STAGED files. In a project whose .gitignore covers the artifacts
# dir (`/_bmad-output/*` — the shape the fork's own onboarding establishes), a brand-new
# brief cannot be staged without `git add -f`, so it NEVER reaches this check. Already-tracked
# briefs stage normally, so EDITS are covered while NEW briefs are not — the worst possible
# coverage shape, because a brand-new brief is exactly what a fresh `design-handoff` emits.
# The measurement that made this gate look armed ("6 true fires / 0 false positives across 44
# briefs") was real as LOGIC and would not have fired on a single new brief in practice.
#
# So: when briefs exist on disk, none are staged, and at least one of them is IGNORED, announce
# it once. Cheap (one check-ignore call), quiet in a correctly-configured repo, and never
# blocking.
if [ -z "$staged" ]; then
  # NOTE: deliberately WITHOUT --exclude-standard — omitting it is what makes `--others`
  # include IGNORED files, which are the whole point of this check.
  ondisk=$(git ls-files --others --cached 2>/dev/null \
    | grep -E '(^|/)design-brief-[^/]*\.md$' | head -50 || true)
  [ -z "$ondisk" ] && exit 0
  ignored=$(printf '%s\n' "$ondisk" | git check-ignore --stdin 2>/dev/null | head -3 || true)
  if [ -n "$ignored" ]; then
    n=$(printf '%s\n' "$ignored" | wc -l | tr -d ' ')
    printf 'design-brief-completeness [REACHABILITY]: %s brief(s) on disk are GITIGNORED — this gate cannot see NEW briefs in this repo, only edits to already-tracked ones.\n' "$n" >&2
    printf '  e.g. %s\n' "$(printf '%s\n' "$ignored" | head -1)" >&2
    printf '  Fix (one line in .gitignore): un-ignore the artifacts dir, re-ignore its contents, then negate design-brief-*.md — see fork-gaps FG-2026-07-25-10 for the verified shape.\n' >&2
    printf '  Until then, treat this gate as covering the LOW-risk path only. Not blocking.\n' >&2
  fi
  exit 0
fi

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
  # TRIGGER = THE DECLARED VALUE, NEVER A MENTION (fixed 2026-07-25, same day, after
  # a real false positive). The first cut matched `mobile-first|handheld-first`
  # ANYWHERE in the body. That fires on a brief that merely REFERENCES the posture —
  # and the canonical example is a desktop-only one: the /clerk grading brief says
  # "§8.2d binds handheld-first classes only, it does NOT bind this surface" and
  # "grading-on-handheld remains an OPEN follow-up". Correct, necessary prose; three
  # bogus warnings. Worse, the brief also contains the literal string "Handheld-First
  # Declaration" inside that same disclaimer, so the presence check passed and the
  # field checks ran against a table that should not exist.
  #
  # So: read the VALUE of the `primary_viewport_class` row and match on that alone.
  # A brief may say "handheld-first" as many times as it likes in prose; only what it
  # DECLARES itself to be decides whether gate (f) binds. This is the same discipline
  # as the authorship rule — a readable field that looks like identity, isn't.
  #
  # MEASURED after the fix (cash-recovery corpus, 41 real briefs + 6 fixtures):
  # fires on the 2 /inbound briefs that genuinely predate the contract; SILENT on the
  # desktop-only /clerk brief that triggered the false positive, and on the other 38.
  #
  # KNOWN COVERAGE GAP (honest — do not claim this catches every handheld brief): a
  # brief that declares its posture in PROSE ONLY, with no `primary_viewport_class`
  # row, is invisible here. That miss is accepted deliberately — the alternative is
  # the mention-matching that just misfired. Every brief the current brief-template
  # generates renders §4g with the field, so the gap closes as the corpus turns over.
  check_handheld_declaration() {
    # The declared value, not any occurrence of the token.
    vp_row=$(printf '%s\n' "$body" | grep -iE '\| *`?primary_viewport_class`? *\|' | head -1)
    [ -z "$vp_row" ] && return 0
    vp_val=$(printf '%s' "$vp_row" | cut -d'|' -f3)
    printf '%s' "$vp_val" | grep -qiE 'mobile-first|handheld-first|mobile-primary' || return 0

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

    # --- B7 in-surface composition (gate class (f), v12) ----------------------
    # The check above asks whether the ARTIFACT's arrangement is specified. This asks
    # whether the composition INSIDE the canonical render is — a separate slot, and a
    # brief can fill the first and leave this one empty. When it does, the generator
    # fills it with its default: a hero row plus a chip wall above the worklist. That
    # output passes every artifact-level rule AND the squint test, because a billboard
    # CTA is genuinely the loudest thing on the page. B5 measures hierarchy; only B7
    # measures compression.
    #
    # FALSE-POSITIVE DISCIPLINE (same shape as the primary_viewport_class fix above):
    # B7 binds TABLE-FIRST surfaces, and this hook cannot read a rendered comp — so it
    # fires only when the brief itself gives a table-first signal AND carries none of
    # the B7 markers. A handheld brief for a single-record cockpit has no list signal
    # and is never warned. Prose that merely mentions the words is not a signal: the
    # match is anchored to worklist/table/queue/list *frame or content* language.
    #
    # MARKER DISCIPLINE — measured 2026-07-25, and the first cut was WRONG. Matching
    # on 'dashboard opener' or 'chip wall' silently PASSED all five /inbound briefs,
    # because they already carry an analytics-band rule banning "the generic
    # enterprise-dashboard opener". That rule is real but it is NOT the B7 spec: it is
    # scoped to analytics bands and phrased as a ban on "three summary cards", which a
    # hero row plus a chip wall does not literally match — and those briefs are exactly
    # the ones that produced the defect. A marker that matches a PROHIBITION rather than
    # the SPECIFICATION manufactures a false negative on the highest-risk population.
    # So the match requires the affirmative B7 phrasing the template emits, and nothing
    # a generic anti-dashboard sentence would trip.
    if printf '%s' "$body" | grep -qiE 'worklist|primary content is a (list|table|queue)|table-first'; then
      printf '%s' "$body" | grep -qiE 'compressed operational stack|inline (in|within) the worklist header' \
        || warn "$brief: table-first handheld-first brief whose §7 carries no IN-SURFACE composition instruction (B7) — gate class (f). Required: compact header block reading as the TOP of the list · count + primary action loud but INLINE in the worklist header (no hero/banner, no billboard CTA row, no large empty half, no separate summary card) · secondary counts/caveats/filters/sorts collapsed at label weight (no chip wall) · at least one real data row visible at rest. Without it the brief commissions a DASHBOARD OPENER, which passes every artifact-composition rule and the squint test. See shared/operator-artifact-contract.md B7 / check C5."
    fi
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
