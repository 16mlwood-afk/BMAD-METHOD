---
name: 'design-handoff-state-variables'
description: 'Rationale appendix for the design-handoff state variables. The orchestrator (workflow.md § State Variables) carries a one-line definition + allowed values + where-set for each variable; this file carries the WHY — the failure mode each variable closes, the anti-bias reasoning, and the cross-variable contracts. Read this when you need the reasoning behind a variable; the one-liner in workflow.md is enough to execute the flow.'
---

# Design-Handoff State Variables — Rationale Appendix

This file exists for **context budget** (see `mason-bmad-workflow-expert/references/context-budget.md`). The orchestrator `workflow.md` is re-read on every run; its `### State Variables` block is the index (name · allowed values · where set). The *rationale* — why a variable exists, the failure it guards, the cross-variable contract — lives here and is read on demand, so the hot path stays cheap. **Load-bearing semantics also live at point-of-use in the step files** (step-01b/01c decide most of these; step-03 renders them); this appendix is the consolidated "why", not a second source of truth for the contract.

Only the variables whose definition carried multi-sentence rationale are documented here. Pure one-liners (`{feature_name}`, `{api_surface}`, `{implementation_files}`, etc.) need no appendix entry — their workflow.md line is complete.

---

## `{injected_placement}` / `{injected_archetype}` — the consumability contract

These carry an upstream decision (from `analytics-placement-triage`, or a direct `--placement`/`--archetype`) so this workflow **honors** it rather than silently re-deriving it. The point is the consumability contract: a placement/shape verdict made by the single-source brain upstream must not degrade into advisory prose that this workflow re-decides differently. When non-empty, §5b (band-belongs) / §5d (topology) / §5c (archetype) honor the injected value (after a §5b-style sanity gate) and skip re-derivation, threading provenance (`injected-by-triage`). Empty (the default) → fully derive as before — backward-compatible.

## `{must_support_capabilities}` — the anti-silent-drop "keep" list

The jobs the operator must accomplish on this surface beyond the primary goals, as **outcomes not UI mechanics**. These are requirements the blank-canvas redesign must satisfy even though the brief withholds the current layout — the anti-bias strip removes the *arrangement*, never the *capability*. Guards the failure where a redesign returns "more basic" than the screen it replaced because a secondary capability (attach-source-receipt, verify-field-against-source, bypass-staging) was never named and so was silently dropped. Empty only when the surface genuinely has none beyond the primary goals.

## `{dropped_capabilities}` — the anti-silent-drop "shed" log

Capabilities the current surface exposes that are **deliberately NOT carried into this brief**, each `{ capability (outcome phrasing) · backing_action · reason }`, reason ∈ `relocated` (to a named sibling) | `obsolete` | `out-of-scope-by-design`. The *log* half of the anti-silent-drop contract: `{must_support_capabilities}` records what the redesign must keep; this records what it deliberately sheds and WHY — so a drop is a visible, vetoable decision (surfaced at end-of-run by step-03 §5 and in the brief), never a silent omission. Never empty by omission — empty list only when every action the current surface invokes is carried forward. Blind spot it closes: a mutation on an existing record (resolve / remap / override / re-run) that is neither a primary goal nor an ingest endpoint, which recall-based capture misses (the EOS batch-detail remap loss).

## `{composition_provenance}` / `{composition_rationale}` — verify the composition, don't inherit it

`policy-default` | `recommended-alt`. WHETHER the page-mode's default composition (operational→table-first; analytical→chart-led; detail→record-view) fits the job — decided in §5a by the job, NOT inherited from the policy default or the legacy render. `recommended-alt` (veto-surfaced) means §4a names a different *primary* composition; it does NOT change `{page_mode}` (work type and composition are orthogonal). Guards the policy-default bias (Anti-Bias Principle II): stamping the mode's default composition unquestioned is a bias as real as inheriting the legacy layout, and harder to catch because it feels like correctly following the system. `{composition_rationale}` keeps the deviation auditable (the three §5a answers + named alt + veto outcome); empty when `policy-default`.

## `{spawned_surfaces}` — the Deliverable-Completeness contract

The secondary surfaces THIS page spawns at runtime, each a **required deliverable frame** in §7's Surface Inventory: the primary surface; the right-side detail drawer (present for `operational`/`analytical` under the table-first composition — for `page_mode: detail` the primary surface IS the drawer); one frame per `{linked_records_inventory}` entry (the §13 expand-in-context lookup drawers). Derived in §5f from `{page_mode}` + `{composition_provenance}` + `{linked_records_inventory}` — **NOT recalled**. Each entry: `{ frame_name · trigger · render_as (drawer-over-{parent} | full-bleed) · must_contain · figures (the §4d decision numbers) · lookups (depth-1 §2a fields) }`. Rendered by step-03 into §7, **frame-name keyed** so the same name travels brief → rendered frame → `design-implement` grid row with zero inference at any hop (Deliverable-Completeness Principle). **Depth-1:** a lookup drawer lists only its own immediate lookups; the foreign record's own §2a owns the next level (stops the recursive order→catalog→supplier graph from inlining). Empty only for a true leaf surface with no drawer and no linked records.

## `{band_provenance}` / `{has_analytics_band}` — band presence is a judgment, not an inheritance

`inherited` | `recommended-new` | `recommended-drop` | `none`. WHY an analytics band exists (or doesn't) — decided in §5b by data + user job, NOT by inspecting the legacy render. The blank-canvas mandate means a bare-table feature whose job is pattern/coverage/ranking work gets a band recommendation (`recommended-new`, veto-surfaced) even when the current page has none. Drives §4b inclusion: present iff `inherited` or `recommended-new`. `{has_analytics_band}` = `true` iff `band_provenance` ∈ {`inherited`, `recommended-new`} and gates §4b emission.

## `{analytics_archetype}` + the analytics reasoning capture — one selection brain

The *shape* of the band (one of nine archetypes, or `unclear` → ask). **Selected in §5c by invoking the `analytics-surface-architect` skill** — the single selection brain so handoff, design-review-pr, and a human all reason the same way (`shared/analytics-archetypes.md` is its taxonomy SoT). Chosen from the user's question, never the data's availability; prevents every band defaulting to the same trend-strip-of-small-multiples. The companion capture variables (`{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`, `{archetype_drill_map}`, `{archetype_prohibited}`, plus the non-skill `{page_mode_rationale}` / `{band_decision_log}`) are the skill's decision object, captured at decision time and rendered by step-03b into the rationale artifact. Capturing it where the decision is made turns a discarded deliberation into an auditable record. Empty when there is no band.

## `{project_phase}` / `{is_greenfield}` — same brief shape, different input sources

The project lifecycle phase from config (`greenfield` | `brownfield` | `mixed`; absent ⇒ `brownfield`). `{is_greenfield}` = true iff `greenfield`. Governs step-01 §1c source binding: greenfield gathers §2–§4 from PRD + architecture + UX + the design-policy-as-spec (no built code), relaxes the §2-pre grounding gate to a settled-spec/policy basis, and skips step-02. The brief shape is phase-agnostic — only the INPUT SOURCES change (codifies `GREENFIELD-BRIEF-DERIVATION.md`). A greenfield brief is stamped `revision_mode: spec_derived` / `last_modified_by: human` in step-03 (`brief-revision-policy.md` §4).

## `{policy_version}` — drift detection downstream

Integer version of `docs/design-policy.md` at brief-generation time (`1` if no version field; `0` if no policy file). Stamped into the brief's `policy_version_required:` so downstream consumers (design-synthesize, design-implement) can detect when the policy has moved past the brief's pinned version.

## Finance-domain pass (`{is_finance_surface}` + the finance block) — capture meaning, never layout

Set in step-01 §3b only when the surface is finance-shaped; empty/absent otherwise. Produced by the `finance-domain-pass` skill (inline fallback if not synced). Captures finance MEANING for the brief, never layout:

- `{is_finance_surface}` — `true` iff a ledger / transactions / inventory movement / reconciliation / P&L / balance sheet / cash flow / FP&A surface. Gates §3b and the finance render in step-03.
- `{finance_report_type}` — detected finance report/data type. A §1 context signal — does NOT set `{page_mode}` or composition.
- `{finance_column_semantics}` — each source column → semantic group (`quantity|money|status|identity|date|meta`) + meaning; enriches `{data_shape}`. Quantity and value stay distinct.
- `{finance_exception_expectations}` — finance exceptions the design must be able to REPRESENT (missing cost, negative stock/value, reconciliation break, pending receipt, duplicate/exploded references, estimated-vs-actual) — as outcomes, not a panel design.
- `{finance_unresolved_assumptions}` — finance definitions that must stay explicit and NEVER be inferred (status SoT, valuation/costing basis, block/line semantics, FX basis). Rendered as brief Open Questions; the workflow never resolves them.
- `{finance_terminology}` — canonical finance terms to use consistently (per `finance-presentation`).
- `{finance_must_not_infer}` — accounting-truth acceptance constraints (no invented figures, account mappings, or valuation methods; missing → mark, never impute).
- The pass's `must_preserve_capabilities` fold into `{must_support_capabilities}`; `dropped_capability_flags` cross-check into `{dropped_capabilities}`; `implied_surfaces` feed `{spawned_surfaces}` via §5f — capability/surface outputs travel the existing vars, no new ones needed.
