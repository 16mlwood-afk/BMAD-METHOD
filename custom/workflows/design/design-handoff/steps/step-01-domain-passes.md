---
name: 'step-01-domain-passes'
description: 'Full capture procedures for the six conditional domain passes (§3b–§3g) referenced from step-01-gather.md — loaded on demand, only when a pass actually fires'
---

# Step 1 domain passes — full procedures (loaded on demand)

**This file exists for context budget, not for a new job.** `step-01-gather.md` §3b–§3g each state a short FIRES/SKIP test inline (needed to decide whether to open this file at all) and then point here for the full capture procedure. Content is unchanged from the prior single-file version — this is a structural split, not a rewrite (`context-budget.md` §5 "Pointer over inline"; fork-gaps 2026-08-05, cash-recovery step-01-gather.md exceeded a consuming agent's per-read token cap on the very first step of a 7-step chain).

**How to use this file:** step-01-gather.md tells you when a given §3X fires. Once it does, read that section below in full and follow it exactly — do not paraphrase from memory, and do not skip back to check the trigger test again (you already passed it). If a section doesn't fire, don't open this file at all for that pass; the trigger test in step-01-gather.md is self-contained.

---

## Domain passes

### 3b. Finance-domain pass — semantics a blank-canvas redesign must preserve (conditional)

Fires **only when finance presentation is material** to the surface — money is a primary data type
(not an incidental field); the operator reviews/reconciles quantities, values, balances, costs, taxes,
landed costs, or variances; the data is inventory/ledger/payout/statement/VAT/reconciliation/accounting
export; or mispresenting missing/estimated/anomalous/duplicate-grouped values could distort financial
truth. **Skip** (`{is_finance_surface}` = `false`) when money is a minor field on a general CRUD page,
the task is pure styling/layout, or another domain owns the semantics; if uncertain, fire only when bad
presentation could distort operational or financial truth, else proceed without it and note the
ambiguity. (Full gate: `finance-domain-pass` "When to invoke".) Finance surfaces hide load-bearing semantics inside the layout this
brief withholds (lifecycle states, quantity/value separation, reconciliation, exceptions); without this
pass a blank-canvas redesign silently drops them or guesses them as taste. This pass captures the
finance **meaning** — never the layout.

**Invoke the skill (mode: extract).** Load `finance-domain-pass` via the Skill tool and pass it:
- the **source artifact** (the data file / page / export the handoff is about),
- the **`{data_shape}`** and **`{linked_records_inventory}`** just derived (§3, §3a),
- read-only awareness of `docs/design-policy.md` (so it surfaces collisions as open questions, never overrides).

The skill runs its procedure (detect type → column semantics → capabilities-as-outcomes → shed-capability
flags → exception expectations → implied surfaces → unresolved assumptions → terminology → must-not-infer)
and returns its **appendix object**. It governs finance meaning, NOT layout — it never names a bar, card,
drawer, or composition. Capture it and route each field into the existing machinery:

| Appendix field | Captured / routed into |
| --- | --- |
| `report_type_detected` | `{finance_report_type}` — a §1 context signal; does **not** set `{page_mode}` or composition |
| `source_column_semantics` | `{finance_column_semantics}` — enriches `{data_shape}` (Domain Data); never blends qty + value |
| `must_preserve_capabilities` | **merge into** `{must_support_capabilities}` (§4) — as outcomes |
| `dropped_capability_flags` | **cross-check into** `{dropped_capabilities}` (§3 mutation audit) — confirm each, don't auto-drop |
| `exception_expectations` | `{finance_exception_expectations}` — representability requirements (NOT a panel design) |
| `implied_surfaces` | **feed §5f** `{spawned_surfaces}` as candidates (frame-name keyed, depth-1; §5f reconciles + owns the final inventory) |
| `unresolved_assumptions` | `{finance_unresolved_assumptions}` — rendered as brief Open Questions; **never resolved here** |
| `terminology` | `{finance_terminology}` — canonical terms for brief labeling |
| `must_not_infer` | `{finance_must_not_infer}` — acceptance constraints preserving accounting truth |
| `policy_collisions` | surface to the user as `modify-design-policy` candidates — do **not** patch the brief around policy |

**Outcomes, never mechanics.** If any captured capability or surface can't be stated without naming a
component, it was a layout leak — drop it. **Never resolve an unknown:** a flagged `unresolved_assumption`
(status source-of-truth, valuation/costing basis, block/line semantics, FX basis) goes to the brief's
Open Questions verbatim; the pass never decides it and the brief never invents it.

**Fallback (skill not synced).** If `finance-domain-pass` is absent (older sync), apply the same
procedure inline using `{project-root}/_bmad/bmm/workflows/shared/` finance conventions + the
`finance-presentation` standard, and populate the same capture fields by hand. The skill is preferred
(it makes the must-not-infer and capability outputs mandatory rather than skippable prose), but handoff
must not hard-fail when it is absent.

---

### 3c. Live-process pass — runtime behavior a blank-canvas redesign must preserve (conditional)

Fires **only when the surface's primary job is watching or controlling a long-running in-flight process** — a scrape/download run, an import/ingestion job, a sweep, a sync, a batch reconciliation: the page's content changes over time while the operator watches, and the process can partially fail mid-flight. Set `{is_live_process_surface}` = `true` and run the capture below. **Skip** (`false`) for request/response CRUD surfaces where data changes only on user action, and for surfaces that merely *display* a job's finished output; if uncertain, fire only when the operator's core anxiety is "is it still working, and what went wrong?" — else proceed without it and note the ambiguity. A live-process surface hides its load-bearing semantics in *time*, which a brief's static data tables cannot carry: without this pass a blank-canvas redesign depicts one moment of a process whose whole job is change, and the temporal contract (states, staleness, control) never reaches the designer. This pass captures the runtime **meaning** — never widgets, never layout.

**Capture `{runtime_behavior_contract}` — derive from the code that drives the process (its status enums, message types, storage writes), never from memory and never invented.** Greenfield (`{is_greenfield}`): derive from the PRD/architecture's process description per §1c, degrading unknown fields to Open Questions rather than guessing. Five facts:

1. **Run lifecycle** — the state machine of one run: every state, every transition, and what triggers it (operator action, item completion, throttle, fatal error). Read it from the actual state enum/handling; a state the code doesn't have may not be invented, and a state it has may not be dropped.
2. **Per-item states** — the states one work item passes through, **including every failure/partial lane** (throttled, held, load-error, retrying, skipped, missing-at-source). Partial failure is the normal case on a live process, not an edge case.
3. **Update transport & staleness** — how this surface learns the process changed (pushed message, storage listener, poll — and at what cadence), and how stale the display can legitimately be. Staleness is a **designed property** the brief must state, not an accident the designer discovers; if the current transport makes honest liveness impossible (e.g. slow polling), record that as a constraint/open question — do NOT silently spec a liveness the plumbing can't deliver.
4. **Control verbs** — what the operator can do to a run in flight (pause / resume / cancel / retry / reprioritize) with their **real** semantics: immediate or drains in-flight items, resumable or restart-from-zero, per-item or whole-run. As outcomes ("stop the run without losing completed work"), never as buttons.
5. **Progress signals available** — the raw signals the design may derive progress from: counts by state, per-item/per-marketplace telemetry, timing data usable for pacing reads, run-report/history data. Signals only — never prescribe a progress bar, spinner, or log panel; the derivation is the designer's.

**Route into the existing machinery:** each lifecycle state that changes what the operator sees or can do becomes a **state-variant frame candidate** for the primary surface, fed to §5f (which owns the final inventory) — the film-strip is how a static brief communicates a dynamic mechanism. Control verbs that invoke server/extension actions also cross-check against the §3 mutation-derivation audit (a pause/cancel/retry action is a mutation — it must land in `{must_support_capabilities}` or `{dropped_capabilities}` like any other). Unresolvable semantics (what "cancel" really does to in-flight items, whether a run is resumable) go to the brief's Open Questions verbatim — never resolved here. Actual motion/transition/animation verification stays ceded downstream (`design-review` / `verify`); the brief carries states and cadence, not animations.

---

### 3d. Interaction-model pass — how the operator DRIVES a processing cockpit (conditional)

Fires **only when the surface is a processing cockpit**: `{page_mode}` = `operational` AND the §2 user context is **expert, high-frequency, and driven by a fast per-item input device — keyboard-first on a bench, SCANNER-FIRST on a handheld** — a queue/worklist the operator clears one item at a time at speed (mapping-queue, a reconciliation lane, a review queue). Set `{is_processing_cockpit}` = `true` and run the capture below. **Skip** (`false`) for occasional/low-frequency operational surfaces, read-mostly dashboards, chrome, and any surface where the operator is not repeatedly committing per-item decisions. If uncertain, fire only when §2 already says keyboard-first **or scanner-first** / high-frequency AND §1's success metrics reward *speed* (time-to-decision, fewer stuck defers) — else proceed without it and note the ambiguity.

> **"keyboard-first" is a BENCH-ERA PROXY and must not be read literally (fix 2026-08-04, cash-recovery SR-85).** It was written when every cockpit was a desktop workstation, and it stands for *"a fast, expert, per-item input device"* — not for a keyboard. A handheld cockpit fails the literal reading **by design**: the cash-recovery handheld grading brief states *"Scanner-first, not keyboard-first — a phone has no keyboard."* So `{is_processing_cockpit}` evaluated **false**, §3d and §3e both skipped, the brief carried **zero** operator-domain fields, and the shipped station asked for a condition grade before the condition photos were captured — an ask the clerk's own operational profile had forbidden since v1. **Nothing was wrong with the doctrine; the trigger simply could not see a phone.** A scanner-driven, one-item-at-a-time handheld surface IS a processing cockpit. So is a voice- or foot-pedal-driven one. The test is *fast expert per-item commitment*, never the input hardware.

**Why this pass exists (the gap it closes):** a static brief captures *what to show* (composition, data, evidence, contracts) but never *how the surface is operated* — keyboard flow, per-item commit→advance momentum, seeing a consequence before an irreversible commit. Those requirements are derivable from signals the brief ALREADY carries (§2 keyboard-first/high-frequency user, §1 speed metrics), but without this pass nothing converts them into requirements, so a blank-canvas redesign ships a beautiful click-only form and the speed goals fail silently — discovered only when a human drives a prototype. This pass captures the interaction **meaning** — never key maps, never widgets.

**Capture `{interaction_model_contract}` — derive from §1 (`{must_support_capabilities}` verbs), §2 (user context), the §3 mutation audit, and §2b basis where a figure is written; never invented.** Five facts:

1. **Operation surface** — keyboard-first vs pointer-first. For an expert high-frequency cockpit it is keyboard-first: every per-item verb reachable + committable without the mouse, plus a persistent shortcut affordance. State as an outcome, not a key map.
2. **Per-item action set & commit weight** — each per-item verb from `{must_support_capabilities}`, classed **reversible** (skip / defer / claim) vs **irreversible / high-stakes** (immutable key, money, partner write). The irreversible set is what requires a consequence-preview (fact 4).
3. **Momentum after commit** — what happens on decide: auto-advance vs manual, to the next *actionable* item (skip claimed-by-other / read-only), with an undo/safety window. Derived from §1 speed metrics.
4. **Consequence-preview** — which irreversible verbs must show WHAT the commit writes (resulting record + derived figure per §2b basis) BEFORE committing. The correctness lever for hard-to-undo writes.
5. **Confidence-scaled effort** — where the machine is confident/unambiguous → a one-action fast path; where ambiguous/detectors disagree → the full decision is FORCED (no rubber-stamp). Derived from §1 "fewer stuck defers".

**Route into the existing machinery:** the per-item verbs cross-check the §3 mutation-derivation audit exactly like §3c control verbs (a commit that invokes a server action must be in `{must_support_capabilities}` / `{dropped_capabilities}`). A consequence-preview that shows a cost/KPI figure inherits the §2b/§4d **DERIVED-vs-PERSISTED** basis rule (never present a derived number as stored). This pass produces **no new frames** — it is a cross-cutting behavior contract rendered into brief §4f (like §2c), NOT a Surface-Inventory entry. Unresolved semantics go to the brief's Open Questions verbatim. Actual keyboard-focus/animation verification stays ceded downstream (`design-review` / `verify`); the brief carries the operation model, not the bindings.

---

### 3e. Operator-domain pass — who the operator is and what the surface must SHOW before it ASKS (conditional)

Fires when **`{is_processing_cockpit}` = true** (the same flag §3d sets — §3d and §3e **co-fire** on a decide-one operator cockpit). §3d captures how the operator DRIVES the surface; §3e captures **who the operator is and what they must know**. **Skip** (`{operator_domain_present}` = `false`) whenever §3d skipped.

**Why this pass exists (the gap it closes):** `design-handoff` already detects the cockpit, applies the `operational-cockpit` M1–M6 floor (into §4f), and captures the interaction model (§3d) — but nothing injects the operator's ROLE semantics (who they are, the trust boundary, what the system already knows before each ask, what they must decide, the evidence required BEFORE input, the forbidden asks). So M6 ("surface the evidence the decision requires") ships **domain-blind** — the surface asks the operator for input the system could have resolved and shown first (the clerk-works-blind defect). This pass captures operator **meaning** — never layout. It is the twin of §3b `finance-domain-pass` for MONEY, applied to OPERATOR ROLE.

**Invoke the skill (mode: extract).** Load `operator-domain-pass` via the Skill tool and pass it:
- the resolved **operator-domain profile** — `docs/<operator>-operational-profile.md` (e.g. `docs/clerk-operational-profile.md`); resolving this is §3e's first action,
- read-only extraction context: `{is_processing_cockpit}`, `{page_mode}`, `{must_support_capabilities}` (§4), `{interaction_model_contract}` (§3d), the §3 mutation/ask audit, and §2 user context — never layout,
- read-only awareness of `docs/design-policy.md` (so a policy collision is surfaced as an open question, never overridden).

**HALT-on-missing-profile (hard stop).** If `{is_processing_cockpit}` = true and no `docs/<operator>-operational-profile.md` resolves, **do NOT emit an operator appendix and do NOT proceed on generic cockpit doctrine** — surface the blocking diagnostic (see the `operator-domain-pass` skill § Enforcement: "missing operator-domain profile for cockpit handoff / why this blocks … / next step: supply or select `docs/<operator>-operational-profile.md`, then rerun design-handoff"). `semantically_incomplete` is permitted only if a safe downstream consumer behavior is named that keeps the warning visible and prevents silent best-effort use; absent that, HALT.

The skill runs its procedure (resolve profile → per-decision extract → operator header → must-not-infer → ordering-invariants → policy-collision detect → **internal-consistency validation gate**) and returns its **appendix object**. Capture each field into the `{operator_*}` state variables:

| Appendix field | Captured into |
| --- | --- |
| `operator_detected` | `{operator_detected}` — a §1 context signal; does **not** set `{page_mode}`/composition |
| `operator_role` | `{operator_role}` |
| `trust_boundary` | `{operator_trust_boundary}` (`may_decide` / `may_not_decide` / `write_trust`) |
| `decision_points[].operator_decides` | `{operator_decides}` (per decision) |
| `decision_points[].known_before_each_ask` | `{operator_known_before_ask}` (per decision) |
| `decision_points[].evidence_required` | `{operator_evidence_required}` (per decision) |
| `decision_points[].forbidden_asks` | `{operator_forbidden_asks}` (per decision) |
| `must_not_infer` | `{operator_must_not_infer}` — top-level operator-truth constraints |
| `ordering_invariants` | `{operator_ordering_invariants}` — top-level |
| `policy_collisions` | `{operator_policy_collisions}` — open questions to the brief; **never resolved here** |

Set `{operator_domain_present}` = `true` once the profile resolved AND the validation gate passed. The per-item verbs cross-check the §3 mutation audit exactly like §3d (a commit that invokes a server action must be in `{must_support_capabilities}` / `{dropped_capabilities}`). This pass produces **no new frames** — it is a cross-cutting operator-meaning contract rendered into brief §4f alongside the interaction model, NOT a Surface-Inventory entry. A `{operator_policy_collision}` is an open question a human must resolve in the brief; the pass never bends policy to fit the profile or vice versa.

**Fallback (skill not synced).** If `operator-domain-pass` is absent (older sync), produce the same appendix **by hand** from `docs/<operator>-operational-profile.md` against the skill's manual checklist — **the same internal-consistency validation gate runs on this path**, so skipping the skill does not skip the gate, and HALT-on-missing-profile still applies (the profile, not the skill, is the load-bearing input). `{is_processing_cockpit}` may not be marked fully captured until the checklist passes.

---

### 3f. Viewport & responsive pass — the per-surface viewport CONTRACT (every page)

Fires on **every `{surface_class} == page` run** (skip for `chrome` — step-01 §0 already captures `nav-desktop` vs `nav-mobile-drawer` breakpoints; `{viewport_present}` stays unset there). Unlike §3d/§3e (cockpit-only), this is UNIVERSAL for content pages: a page brief that never states its viewport posture ships desktop-blind, and the non-interpretive downstream pipeline then guesses one.

**Why this pass exists (the gap it closes):** owner content surfaces had no responsive doctrine and the gather ran no structured viewport pass — the only mobile signal was the freeform §5 `constraints — responsive breakpoints` field, routinely left empty. This pass makes viewport a first-class, policy-sourced contract. It captures viewport MEANING from policy — never invents a posture. Twin of §3b `finance-domain-pass` (money) / §3e `operator-domain-pass` (operator role), for VIEWPORT.

**Source of truth: the project `docs/design-policy.md §8` (surface-class → viewport policy). Never invent a breakpoint, tap target, or phone-support decision.** (If the project has no §8 viewport policy, record an Open Question — "no viewport policy in docs/design-policy.md; author §8 first" — and do not fabricate one.)

1. **Resolve `{viewport_surface_class}`** — match `{route}` against policy §8.1's class→route table (e.g. `clerk_bench` | `owner_dashboards_worklists` | `owner_approvals_recovery_reimbursements` | `owner_listings_catalog`). Unmappable ⇒ record an Open Question ("route not mapped to a viewport surface-class in policy §8.1"), do NOT guess a class.

   **Membership is QUOTED, never asserted (added 2026-07-29 — `FG-2026-07-29-01`).** Resolving a class means finding `{route}` **literally present** in that class's Members cell, and **copying the matched member text verbatim** into `{viewport_class_evidence}`, which §4g renders beside the class name. A class name with no quoted member string is **not a resolution** — it is an assertion, and gate (a) cannot tell the two apart: (a) fails an *unresolved* class, never a *wrongly resolved* one. **A near-miss is a MISS.** A sibling route in the class (`/foo` present, `/foo/[id]` absent), a route that "obviously belongs", a predecessor brief that already carried the class, or a changelog entry that mapped a *different* route — none of these is membership. Each resolves to **unmappable** ⇒ the step-1 Open Question, exactly as if no class existed. **Do not repair the policy from inside this workflow:** adding the missing member is a policy edit with its own owner-ruling discipline (posture is decided per class, on each class's own job), and doing it here launders a guess into a citation.

   *Observed 2026-07-28: a brief recorded `viewport_surface_class: owner_dashboards_worklists` "resolved from §8.1 (mapped in policy v17)". v17 mapped a different route and nothing else — neither ingestion route had ever been in §8.1. Gate (a) passed (a class WAS named), the brief shipped `pending-policy` — which reads as correctly-following-policy, not as unverified — and every downstream consumer inherited a guessed posture. The route was later mapped by a genuine owner ruling, which is what makes the original citation checkable at all.*
2. **Decided class → AUTO-FILL from policy §8.2 (whatever posture it decided — do NOT assume desktop-only).** If the resolved class is DECIDED in policy §8.2, fill all six fields from THAT class's §8.2 block **verbatim**. A decided class can be any posture, e.g.:
   - a **desktop-only** bench class (e.g. grading/scanning/reconciliation): `{primary_viewport_class}` = `desktop-only`, `{viewport_breakpoints}` = `desktop-only ≥1280px, landscape`, keyboard + hardware scanner, `{viewport_min_tap_target}` = n/a, `{viewport_device_exclusions}` = `phone, tablet — a mobile/faux-mobile UI here is a policy VIOLATION` (cite the project's clerk-web-mode hard-failure);
   - a **handheld-first / mobile-primary** class (e.g. a roaming receiving clerk): `{primary_viewport_class}` = `mobile-first`, phone viewport / portrait / one-handed, mobile scanner, offline-capable if the policy says so, desktop **additive-only** (a desktop-only mouse-dependent layout is the VIOLATION here), `{viewport_min_tap_target}` from policy.
   **Never hardcode desktop-only — read the class's actual §8.2 decision** (a class can be decided desktop-only OR decided mobile-first). Then run the validation gate (step 5).
3. **Owner class + ambition OPEN → WARN-ONLY (do not freeze owner work).** If the resolved class is an owner class and policy §8.3's mobile ambition is still OPEN (the ⚠ OPEN ITEM marker present, ambition unset): **render §4g with the six owner fields marked `pending — awaiting the owner's §8.3 mobile-ambition decision`, set `{viewport_pending_policy}` = true, mark the brief `unverified` / `pending-policy`, and LET THE HANDOFF CONTINUE.** Never invent breakpoints, tap targets, or phone support. Surface the loud diagnostic verbatim:
   > **Viewport policy not set for this owner surface-class. Mason must choose the mobile ambition (tablet-down desktop-primary · mobile-first · desktop-only) in `docs/design-policy.md §8.3`. This brief is marked pending-policy and unverified until that decision — proceeding without freezing owner work.**
   This is **warn-then-gate**: a small follow-up flips this to a hard HALT once the ambition is set. (PROBABILISTIC workflow warn — see § Enforcement tier below; the deterministic companion is the per-project brief-artifact validator.)
4. **Owner class + ambition SET → read from policy §8.3.** Once the owner has set the ambition, populate all six fields from policy per class; never soften or reinterpret. (A missing/partial field HERE — ambition set but a field blank — is a HARD fail, not a warn; see step 5.)
4b. **DECIDED class → derive `{canonical_viewport}` + `{additive_viewports}` (the ARTIFACT-LABELING half).** Steps 1–4 capture which viewport the surface is DESIGNED FOR; they do NOT control how the rendered artifact MARKS it. An unlabelled phone/tablet/desktop comp set contradicts **none** of the six fields, so the gate below passed it while the artifact read desktop-first to every cold reader — and the §7 deliverable line then told the designer "desktop width" regardless of posture. Close that here. **DERIVE, never choose** — if the project policy carries a canonical-vs-additive subsection (e.g. cash-recovery `docs/design-policy.md` §8.2c), read its values verbatim instead:
   - `{canonical_viewport}` — the ONE viewport the interaction model is designed at and judged against, read off `{primary_viewport_class}`: `mobile-first`/handheld-first ⇒ **phone portrait, 375×812 reference**; `desktop-only`/`desktop-primary` ⇒ **desktop ≥1280 landscape, 1440×900 reference**; `tablet-down` ⇒ the policy's named tablet reference. Exactly one — a surface with two canonical viewports has none.
   - `{additive_viewports}` — every other `{viewport_breakpoints}` entry, each an **additive verification render**: a CHECK that the canonical model survives a different container, never a second design. Anything in `{viewport_device_exclusions}` is in NEITHER list and is **not rendered at all**.
   - **Owner class with an OPEN ambition ⇒ leave both unset, skip this derivation, and gate class (e) does not apply.** There is no decided posture to mark; do not invent one.
4c. **Handheld-first DECIDED class → assemble `{handheld_declaration}` (the ARTIFACT-COMPOSITION half).** (e) makes the deliverable be *drawn at* the right viewport; it does not stop the artifact being a **review board** — co-equal comps, rationale competing with the surface, state variants as peer mini-products. Contract + failure shape + golden cases: **`shared/operator-artifact-contract.md`** (rules B1–B7) — read it, do not restate it. **On a table-first surface, also carry rule B7 into §7** — the canonical render must be specified as a **compressed operational stack** (compact header reading as the top of the list; count + primary action loud but inline in the worklist header; secondary counts/filters collapsed at label weight, no chip wall; ≥1 real data row visible at rest), because the artifact-level rules alone will pass a **DASHBOARD OPENER**. Assemble the five declaration fields it requires: surface class · canonical viewport · additive viewports (`none` legal) · **scan/next-step loop** (stated as a loop: trigger → feedback → next, from `{core_job}` / the §3c contract — never a feature list) · **offline/degraded state treatment** (which degraded states are first-class + the B3 statement that they are drawn as states OF this surface, sourced from the class's offline policy and the §5f state-variant frames). `TBD`/`responsive`/`see policy` are non-answers. **Skip entirely on a desktop-only class and on any OPEN owner ambition.**
5. **Validation gate (runs on both paths) — three classes, don't conflate them:** **HARD FAIL** (set `{viewport_present}` = false, brief NOT deliverable, revise naming the failing check): (a) `{viewport_surface_class}` unresolved; (b) **missing/partial** — a field blank on a clerk surface, or on an owner surface whose ambition is SET; (c) **policy contradiction** — a field contradicts the class's OWN declared §8.2 posture (not a blanket "clerk = desktop"): a **desktop-only-decided** class marked mobile/tablet-supported FAILS, **and** a **mobile-first/handheld-first-decided** class forced into a desktop-only, mouse-dependent layout (dropping the mobile/offline premise) FAILS. Contradiction is measured against the class's declared posture, never a hardcoded assumption; it fails, it never warns. **WARN-ONLY** (set `{viewport_present}` = false + `{viewport_pending_policy}` = true, brief `unverified` / `pending-policy` but STILL DELIVERABLE and the handoff CONTINUES): (d) owner ambition OPEN (step 3). **HARD FAIL, cont. — (e) canonical viewport undeclared (DECIDED classes only).** A DECIDED-class `page` run fails when `{canonical_viewport}` is unset, when more than one viewport is marked canonical, or when the brief's §7 "Per-frame outputs" does not name the canonical viewport as the render target with the others explicitly marked additive. This is the artifact-labeling half of the contract: (b) asks *"is the posture recorded?"*, (e) asks *"will the deliverable actually be DRAWN and READ at that posture?"* — a brief can pass (b) with a perfect §4g table and still instruct the designer to render desktop-first, which is exactly what a hardcoded §7 line used to do. **(e) never fires on an owner class with an OPEN ambition** (no decided posture ⇒ nothing to declare) — it is not a back door around the warn-only (d) treatment. **HARD FAIL, cont. — (f) handheld-first declaration incomplete (handheld-first DECIDED classes only).** A `mobile-first`/handheld-first `page` run fails when any of the five §4c declaration fields is missing, blank, or hand-waved (`TBD` · `responsive` · `see policy`), or when §7 does not carry the B1–B4 composition instruction, **or — on a table-first surface (primary content is a list/table/queue/worklist) — when §7 does not carry the B7 IN-SURFACE composition spec** (compact header block reading as the top of the list · count + primary action loud but **inline in the worklist header**, no hero/banner/billboard-CTA/large-empty-half/separate-summary-card · secondary counts, caveats, filters and sorts collapsed into the same vertical rhythm at label weight, no chip wall · **at least one real data row visible at rest**). **The B7 clause is a distinct failure, not a restatement:** a brief can carry a flawless artifact-composition sequence and still commission a **DASHBOARD OPENER**, because every artifact-level rule is satisfied and B5 is satisfied *by construction* by a billboard CTA — the action really is the loudest element. Loudness was never the question; shape is. **B7 binds by CONTENT SHAPE, not viewport class** — it does not fire on a single-record cockpit with no list. **(e) asks *will the deliverable be drawn at the canonical viewport?*; (f) asks *does the brief specify the SHAPE of the artifact at that viewport, and of the surface inside it?*** A brief passes (e) with a flawless canonical label and still commissions a review board. **"Responsive" is not a canonical viewport** — it names a technique, and it is the phrasing that lets a generator pick desktop as the design. **(f) never fires on a desktop-only class or an OPEN owner ambition** (same false-positive guard as (e)). Contract: `shared/operator-artifact-contract.md` § Layer A. A `page` run is *fully captured* only when the gate passes clean (none of a–f); it is deliverable on (d)-only, but never on a/b/c/e/f.

This pass produces **no new frames** — it is a cross-cutting page-shell viewport contract rendered into brief §4g (like §2c / §4f), NOT a Surface-Inventory entry. Set `{viewport_present}` = true once the class resolved, the contract is complete, AND the gate passed.

**§ Enforcement tier (honest — do not overclaim).** Mechanisms 1–5 here are **PROBABILISTIC** (workflow prose the model executes; they ship via the fork sync). The **DETERMINISTIC** companion is a per-project CI/pre-commit validator on the emitted brief artifact (surface_class present · six fields complete · consistent with `design-policy.md §8` · bench-class not mobile-marked) — it is code, distributed on the separate per-project hooks/CI track, and does NOT ship via the workflow sync. Authoring this pass does not deploy a hard gate; the validator is the hard gate.

---

### 3g. Ledger-archetype pass — is this a LEDGER, and which view (conditional pre-filter, every page)

**Ask on any surface where `{is_finance_surface}` is true, OR whose rows are quantity/stock MOVEMENTS
(inventory in/out, receipts/issues, adjustments) even with no money on the page.** Finance-shaped is the
PRE-FILTER for asking the question — it is **not** the answer: a ledger need not carry money (quantity
movements accumulate the same way), and most finance surfaces are plain worklists. Skip entirely on a
surface with neither.

**The archetype test (the ONLY test — apply it to what the rows ARE, never to the route's name):** a
surface is a ledger when its rows are **movements over time on an account** AND a column is **meant to be
summed or accumulated**. A table that merely sorts by a date is a worklist. A route called `/lineage`,
`/ledger` or `/register` is *naming*, not evidence — cash-recovery's `/lineage` is called a ledger in its
own code header and in its policy class name, and is not one (identity links, nothing accumulates).

**1. Set `{is_ledger_surface}` and `{ledger_view}` as a STRUCTURED VALUE, never a yes/no.** Emit exactly
one of three:

| `{ledger_view}` | When | Sort |
|---|---|---|
| `not-a-ledger` | rows are not movements, or no column accumulates | per the project's default (§F most-recent-first) |
| `register` | movements over time, **no** running balance shown | most-recent-first — the default; no exception applies |
| `running-balance` | movements over time **with** a cumulative column | **oldest-first (date-ascending)** — the cumulative only builds correctly reading DOWN |

`not-a-ledger` is a **first-class, legal, common answer** — it is the expected value on most finance
surfaces and is never a failure. Do NOT phrase this to yourself as *"is this a ledger?"* and answer yes/no:
a challenge-shaped self-question produces capitulation rather than judgement. Apply the test, emit the value.

**2. Resolve whether a ledger ARCHETYPE exists in this project's policy chain — two reads, no project list.**
Set `{ledger_archetype_policy_source}` to the file that defines it, or empty:

```
# i. the project policy itself (you have already read it at §1)
grep -nE '^(##+ )?.*(Ledger (&|and) register|Ledger surfaces)' {project-root}/docs/design-policy.md
# ii. the overlay it NAMES as its parent — read the `Inherits`/`inherits:` line, follow it, and check
#     that file's frontmatter for `declares_archetypes:` (authoritative) or its own ledger section
grep -nE 'declares_archetypes|^## §M\.' <the-overlay-path-the-policy-names>
```

**Key on what the policy DECLARES, never on a hardcoded family or project list** — a third project that
starts inheriting the overlay is then picked up the day it does, with no edit here. Prefer the frontmatter
`declares_archetypes:` marker over heading-text matching; heading text drifts and a project's own section
name is project-specific (cash-recovery's is `§3a`, not `§M`).

**3. Branch on what resolved:**
- **An archetype resolved AND `{ledger_view}` ≠ `not-a-ledger`** → the view declaration is **REQUIRED** in
  the brief (rendered at §2d; gate class **(g)** in step-03). Read that policy section and carry its
  concrete rules into §2d verbatim — do not paraphrase them from memory.
- **An archetype resolved AND `{ledger_view}` = `not-a-ledger`** → render §2d with the classification only.
  One line. This is the common case and it is cheap on purpose.
- **NO archetype resolved** → set `{ledger_view}` anyway (the classification is true regardless of which
  policy a project inherits) and **record an Open Question** — *"no ledger archetype in this project's
  design-policy chain; the view is classified but no archetype rules exist to apply"* — then proceed. **Do
  NOT fabricate ledger rules, and do NOT import another project's §M text.** Same discipline as the missing
  §8 viewport policy at §3f: record it, never invent it. A brief field whose rules no consumer defines is a
  reader with no writer — the exact shape the invisibility policy exists to catch.

**§ Enforcement tier (honest — do not overclaim).** This pass is **PROBABILISTIC**: it is workflow prose
the model executes, and it ships via the fork sync. Gate class (g) in step-03 is a workflow halt (tier 3),
the same tier as classes (e)/(f). **What cannot be enforced at all: whether the rendered comp obeys the
archetype's rules — a comp is not a tool call, so no hook can block one**, the identical ceiling to the
canonical-viewport passes. The strongest additional tier is the `design-review-pr` brief check, which reads
TEXT and can only ever confirm the brief SAID the right thing. A commit-time validator on the emitted brief
is **deliberately NOT proposed here** — the existing brief gate documents its own blindness to NEW briefs
in a repo whose artifacts dir is gitignored, and duplicating that placement would ship a check that reports
green from seeing nothing.

