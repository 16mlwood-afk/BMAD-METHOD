---
name: operator-domain-pass
description: >
  Extract the operator ROLE semantics a blank-canvas cockpit redesign must preserve, from a
  decide-one operator surface (a grading bench, a claim-filing station, a VAT filer, a mapping/triage
  queue, a per-unit review/pricing/publish gate). Returns a structured operator-domain appendix — who
  the operator is, the trust boundary, what the system already knows before each ask, what the operator
  must decide, the evidence required BEFORE input, the forbidden asks, a must-not-infer list, and the
  ordering invariants — for design-handoff step-01 §3e to capture and brief §4f to render. Use when the
  surface is a decide-one operator cockpit (`{is_processing_cockpit}` = true); skip otherwise. Do NOT
  use for visual treatment, layout, composition, cards, drawers, tokens, or the M1–M6 cockpit floor
  (that is the project design policy + the operational-cockpit skill). Never invents operator facts,
  never resolves a policy collision, never decides a may-not-decide boundary — it flags them. Twin of
  finance-domain-pass, for OPERATOR ROLE instead of MONEY.
metadata:
  short-description: Operator ROLE semantics of a cockpit for brief enrichment — not layout
---

# Operator Domain Pass

The single brain for one decision: **given a decide-one operator cockpit, what operator MEANING must
survive a blank-canvas redesign — who the operator is, what they may decide, and what the system must
SHOW before it ASKS?** It reads the operator-domain profile (never the live UI), names the operator
semantics, and returns a structured appendix that `design-handoff` folds into the brief. It governs
**operator meaning, never layout** — the twin of `finance-domain-pass` for money.

This exists because `design-handoff` already detects a cockpit (`step-01b-decide.md §5a`), applies the
`operational-cockpit` M1–M6 floor, and captures the *interaction model* at §3d (how the operator
DRIVES the surface). Nothing captures **who the operator is and what they must know**, so M6 ("surface
the evidence the decision requires") ships domain-blind — the surface asks the operator for input the
system could have resolved and shown first (the clerk-works-blind defect). This pass makes operator
semantics an explicit, auditable brief input.

## When to invoke

Fires at `design-handoff` `step-01-gather §3e` when **`{is_processing_cockpit}` = true** (already set
at §3d: `page_mode: operational` AND an expert / high-frequency / keyboard-first operator clearing one
item at a time). Skip otherwise — return `operator_detected: none` and stop.

The clerk (warehouse-receive/grade) is the first concrete case, but the pass is **operator-neutral**:
a grading bench, a claim-filing station, a VAT filer, a mapping/triage queue each carry their own
`docs/<operator>-operational-profile.md`. The pass logic, the output keys, the validation gate, and
the Enforcement halts are identical across all of them; only the profile changes.

## Inputs

- The **operator-domain profile** for this surface's operator: project-local
  `docs/<operator>-operational-profile.md`. The authoritative source the pass **selects from** — it
  never invents operator facts.
- Brief context already gathered: `{data_shape}` (§3), `{linked_records_inventory}` (§3a),
  `{must_support_capabilities}` (§4), `{interaction_model_contract}` (§3d), and read-only awareness of
  `docs/design-policy.md`.
- The surface's route + the per-item decision(s) the operator commits on it.

## Trust hierarchy (resolve conflicts strictly in this order — four levels)

1. **`docs/design-policy.md` — the top constraint.** Authoritative for anything it hard-constrains.
   NEVER soften, carve out, or override it. Where operator meaning could collide with a policy rule,
   emit a `policy_collision` **open question** — never auto-resolve it (see Enforcement).
2. **`docs/<operator>-operational-profile.md` — the single source of operator vocabulary.** Role,
   trust boundary, knowledge state, evidence expectations, and forbidden asks all come from here.
   SELECT and APPLY; do not redefine or supplement operator facts from memory.
3. **`operational-cockpit` (M1–M6) — the owner of cockpit STRUCTURE.** This pass does NOT restate the
   floor; it fills only M6's **"which evidence"** content for this operator.
4. **The live UI — explicitly non-authoritative.** An *observation* of what currently ships, never a
   source of truth. "It currently asks for the LPN first" is a defect to fix, not a semantic to preserve.

## Enforcement (two hard rules; neither is auto-resolved)

- **HALT-on-missing-profile (hard stop for any operator cockpit redesign).** If
  `{is_processing_cockpit}` = true and `docs/<operator>-operational-profile.md` does **not** resolve,
  §3e **must NOT emit an operator appendix** and **must surface a blocking question to the project** —
  the handoff does not proceed on generic cockpit doctrine. Diagnostic:

  ```
  design-handoff — missing operator-domain profile for cockpit handoff

  This surface is a decide-one operator cockpit (is_processing_cockpit = true),
  but no operator-domain profile resolved for its operator.

  Why this blocks: without it the brief cannot derive operator role, trust
  boundary, knowledge-before-ask ordering, or evidence-before-input
  requirements — so the redesign would substitute generic cockpit doctrine
  for the operator's real job semantics and ship domain-blind.

  Next step: supply or select docs/<operator>-operational-profile.md
  (e.g. docs/clerk-operational-profile.md), then rerun design-handoff.
  ```

  `semantically_incomplete` (instead of a hard halt) is permitted **only** if a safe downstream
  consumer behavior is named that (a) keeps the warning visible and (b) provably prevents silent
  best-effort use. Absent that named behavior, HALT.

- **Policy-collision is an explicit open item, never auto-resolved.** Any `policy_collision` between
  `docs/design-policy.md` and the operator profile is raised as an explicit open question in the brief.
  Proceeding requires a **human decision recorded in the brief** (which side wins and why). The pass
  never silently bends policy to fit the profile, or vice versa.

## Procedure (run in order)

1. **Resolve the operator profile.** Identify this surface's operator; load
   `docs/<operator>-operational-profile.md`. **If none resolves → HALT (Enforcement: HALT-on-missing-profile).**
2. **Identify the per-item decision(s)** this surface commits (from `{must_support_capabilities}` + the
   route), as outcomes.
3. **For each decision, extract from the profile** (never from the live UI): what the operator must
   decide · what the system already knows before that ask · the evidence that must be on-screen for it ·
   the asks forbidden at that point.
4. **Lift the operator header** from the profile: `operator_role` + `trust_boundary` (surface-independent).
5. **Assemble `must_not_infer`** — operator-truth constraints (don't guess identity the operator can't
   confirm; don't ask the operator to decide outside the trust boundary).
6. **Lift `ordering_invariants`** from the profile (expected-contents-first →
   identity-before-identifier → evidence-before-input, plus any operator-specific ones).
7. **Detect `policy_collision`s** against `docs/design-policy.md`; emit each as an open question — never
   resolve (Enforcement: policy-collision).
8. **Run the internal-consistency check (validation gate).** Verify ALL three:
   - **Decision completeness:** every entry in `operator_decides` has matching non-empty
     `known_before_each_ask`, `evidence_required`, and `forbidden_asks` for that decision.
   - **Ordering respected:** every `ordering_invariant` holds across the decision definitions — in
     particular **no decision requires operator input before the evidence/knowledge it depends on** is
     resolvable and surfaced (evidence-before-input; identity-before-identifier).
   - **No boundary contradiction:** no `forbidden_asks` entry contradicts the `trust_boundary` or
     `must_not_infer` — and, conversely, no *required* ask would force the operator to decide outside
     their `may_decide` set (an ask implying a `may_not_decide` outcome is itself a defect).
   - Any failure ⇒ the handoff is **unverified** and must be revised; name the specific failing check.
     **This gate runs on BOTH the skill-driven and the manual/fallback path** — a brownfield project
     cannot bypass it by skipping the skill.
9. **Return the appendix** using the exact keys below.

## Output contract (consumed by §3e capture + brief §4f without reshaping)

```
operator_detected:        "<e.g. warehouse-clerk>"        # signal; does NOT set page_mode/composition
operator_role:            "<one paragraph: identity · trust relationship · expertise · frequency>"
trust_boundary:
  may_decide:             [ "<outcome>", ... ]
  may_not_decide:         [ "<outcome — owner-gated / verification-required>", ... ]
  write_trust:            "<which operator writes are verifiable vs. taken on trust>"
decision_points:                                          # one entry per per-item decision the surface commits
  - operator_decides:     "<what the operator must decide, one outcome>"
    known_before_each_ask:[ "<fact the system resolves + surfaces first>", ... ]
    evidence_required:    [ "<must be on-screen for this decision>", ... ]
    forbidden_asks:       [ "<ask the surface must NOT make here>", ... ]
must_not_infer:           [ "<operator-truth constraint>", ... ]     # top-level; 1:1 with profile
ordering_invariants:      [ "expected-contents-first", "identity-before-identifier", "evidence-before-input", ... ]
policy_collisions:        [ "<open question — human must decide + record in brief>" ] | none
```

`operator_decides` / `known_before_each_ask` / `evidence_required` / `forbidden_asks` are carried
**per decision** inside `decision_points` (they align by decision, which the validation gate depends
on). `must_not_infer` and `ordering_invariants` are **top-level**, never per-decision, and never mixed
into `forbidden_asks`. If the surface is not an operator cockpit, return `operator_detected: none` and
stop. If it is but a required input is missing, name what's needed and stop rather than guessing.

## Forbidden (hard)

No layout / composition / component / hierarchy / token guidance; no restating the M1–M6 floor (that is
the `operational-cockpit` skill); no inventing operator facts absent from the profile; no resolving a
`policy_collision`; no deciding a `may_not_decide` boundary on the operator's behalf; no reading
operator meaning from the live UI.

## Fallback (skill not synced) — manual checklist, same gate

If `operator-domain-pass` is absent on an older sync, `step-01-gather §3e` produces the operator
appendix **by hand** from `docs/<operator>-operational-profile.md`. The manual path is NOT lighter — it
must satisfy this checklist before `{is_processing_cockpit}` may be marked fully captured:

- [ ] `operator_role` — present, non-empty.
- [ ] `trust_boundary` — present, with `may_decide` / `may_not_decide` / `write_trust` (or explicit `none`).
- [ ] `operator_decides` — present, non-empty (or explicit `none` with justification).
- [ ] `known_before_each_ask` — present per decision (or explicit `none`).
- [ ] `evidence_required` — present per decision (or explicit `none`).
- [ ] `forbidden_asks` — present per decision (or explicit `none`).
- [ ] `must_not_infer` — present top-level (or explicit `none`).
- [ ] `ordering_invariants` — present top-level (or explicit `none`).
- [ ] **The internal-consistency validation gate (Procedure step 8) has been run and passed.**

`step-01-gather` **cannot mark `{is_processing_cockpit}` as fully captured unless this checklist
passes** — the **same validation gate runs on the manual path as on the skill path**, so skipping the
skill does not skip the gate. HALT-on-missing-profile still applies (the profile, not the skill, is the
load-bearing input).

## Provenance

Design-only spec ratified stable-for-wiring 2026-07-18; wired into `design-handoff §3e` + brief §4f
under owner approval 2026-07-18. Full contract: `docs/specs/operator-domain-pass-spec.md` (v0.2) +
`docs/specs/operator-operational-profile-schema.md`. Fork-gap: `docs/fork-gaps.md § Open` (2026-07-18).
