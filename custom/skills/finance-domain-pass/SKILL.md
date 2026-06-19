---
name: finance-domain-pass
description: >
  Extract the finance SEMANTICS a blank-canvas redesign must preserve, from a finance-shaped source
  artifact (ledger, transactions, inventory movement, reconciliation, P&L / balance sheet / cash flow,
  FP&A). Returns a structured finance-domain appendix — capabilities-as-outcomes, exception
  expectations, unresolved assumptions, implied runtime surfaces, terminology, source-column
  semantics, and a must-not-infer list — for design-handoff step-01 to capture and step-03 to render
  into a brief. Use when a workflow needs the finance MEANING of a surface for brief authoring. Do NOT
  use for visual treatment, layout, composition, summary bars, cards, drawers, tokens, or chart style
  (that is the project design policy + the blank-canvas design process). Never invents figures,
  account mappings, or valuation methods; never resolves an unknown — it flags it.
metadata:
  short-description: Finance semantics of a surface for brief enrichment — not layout
---

# Finance Domain Pass

The single brain for one decision: **given a finance-shaped source artifact, what finance MEANING
must survive a blank-canvas redesign — and what must stay explicit instead of being inferred?** It
reads the source (data + workflow), names the finance semantics, and returns a structured appendix
that `design-handoff` folds into the brief. It governs **meaning and accounting truth, not layout.**

This exists because `design-handoff` withholds the current UI on purpose (the bias filter). Finance
surfaces hide load-bearing semantics inside that withheld UI — lifecycle states, quantity/value
separation, reconciliation, exceptions — and a designer starting blank will silently drop them or
guess them as taste. This pass makes those semantics an explicit, auditable input so the redesign
preserves accounting truth without the brief leaking layout.

## Trust hierarchy

1. **The project design policy wins, verbatim.** `docs/design-policy.md` is authoritative for anything
   it hard-constrains. This pass NEVER softens, carves out, or overrides it. Where finance meaning and
   policy could collide, emit an **open question** — do not assert a finance rule that bends the policy.
2. **`finance-presentation` is the source of truth for finance vocabulary, column semantics, and
   anomaly definitions.** This pass SELECTS and APPLIES from it (what a ledger column means, what an
   anomaly is, how units/value separate) — it does not redefine them.
3. **`brief-revision-policy` owns provenance and capability bookkeeping.** This pass FEEDS
   `must_support_capabilities` / `dropped_capabilities` / the Surface Inventory; it never bypasses the
   intake checks or the supersede machinery.
4. **The live product UI is not a source of truth.** Read meaning from the data and the workflow,
   never from how the legacy screen renders it. "It's currently three tabs" is not a finance semantic.

## Cardinal rules

- **Outcomes, never mechanics.** Every capability and surface is phrased as a job/outcome
  ("segment by lifecycle state", "reconcile expected vs received"), never as UI ("use tabs", "a
  summary bar"). If you cannot phrase it without naming a component, it does not belong here.
- **Never invent; never resolve.** No figures, account mappings, or valuation methods. An unknown
  (status source-of-truth, costing basis, FX basis) is FLAGGED as an unresolved assumption — never
  decided. Missing data is named, never imputed.
- **Numbers vs. commentary stay separated** in anything you describe.
- **Depth-1 on implied surfaces.** Propose a runtime surface and its own immediate lookups only; the
  foreign record owns its next level. You propose candidates — `design-handoff` §5f/§7 owns the final
  inventory.

## Procedure (run in order)

1. **Detect the report/data type** from columns + workflow purpose (ledger / inventory movement /
   reconciliation / P&L / balance sheet / cash flow / transaction export). State it; this is a signal
   only — it does NOT set page-mode or composition.
2. **Map source columns to semantic groups** — each column → `quantity | money | status | identity |
   date | meta` + its meaning. Keep quantity and value distinct; note any money stored with an
   embedded currency glyph or as text (a parse/data-quality fact, not a display choice).
3. **Name finance-critical capabilities to preserve**, as outcomes. Lifecycle segmentation, qty/value
   separation, reconciliation (expected vs received/delivered/held/returned), cost/landed-value
   breakdown, etc. — only those grounded in the source.
4. **Audit deliberately-shed capabilities** the source exposes but that may not carry forward — each
   `{ capability (outcome) · backing field/action · reason: relocated|obsolete|out-of-scope }`. A
   flag for the brief author to confirm, not a decision.
5. **Name the exception expectations** the design must be able to REPRESENT somewhere: missing cost,
   negative stock/value, reconciliation break, pending receipt, duplicate/exploded references,
   estimated-vs-actual cost. Outcomes the journey must accommodate — not a panel.
6. **Identify implied runtime surfaces** finance workflows spawn (row-level detail, exception review,
   grouped-reference inspection when one reference spans multiple rows) — as §7 Surface-Inventory
   CANDIDATES, frame-name keyed, depth-1.
7. **List unresolved assumptions** that must stay explicit and never be inferred (status SoT,
   valuation/costing basis, block/line semantics, FX/currency basis).
8. **Fix the terminology** to use consistently in the brief (canonical finance terms per
   `finance-presentation`).
9. **Write the must-not-infer list** — accounting-truth constraints (no invented figures, mappings, or
   valuation; missing → mark not impute).

## Output contract

Return the appendix in this exact shape (consumed by design-handoff step-01 §3b and step-03 without reshaping):

```
report_type_detected:   "<e.g. inbound inventory reconciliation>"   # signal only; does NOT set page_mode
source_column_semantics:
  - { column: "<src column>", group: <quantity|money|status|identity|date|meta>, meaning: "<one line>" }
must_preserve_capabilities:                 # outcomes; fold into {must_support_capabilities}
  - "<capability as an outcome>"
dropped_capability_flags:                   # candidates for {dropped_capabilities}; brief author confirms
  - { capability: "<outcome>", backing: "<field/action>", reason: <relocated|obsolete|out-of-scope> }
exception_expectations:                     # outcomes the design must be able to represent
  - "<e.g. missing cost must be representable as a flagged state>"
implied_surfaces:                           # §7 candidates, frame-name keyed, depth-1
  - { frame_name: "<name>", purpose: "<what it lets the operator do>", depth1_lookups: [ "<field>" ] }
unresolved_assumptions:                     # must stay explicit; NEVER resolved here
  - "<e.g. status source-of-truth (Status vs Delivery Status) unconfirmed>"
terminology:                               # canonical terms for the brief
  - "<term>"
must_not_infer:                            # accounting-truth constraints
  - "<e.g. no valuation method assumed; missing cost marked, never imputed>"
policy_collisions:                         # where finance meaning may meet a policy hard-constraint
  - "<surface as open question; do NOT override policy>"   | none
```

If the source is **not** finance-shaped, return `report_type_detected: none` and stop — the caller
skips the pass. If finance-shaped but a required input is missing, name what you need and stop rather
than guessing.

## Forbidden (hard)

No layout / composition / component / visual-hierarchy / token / spacing / chart-style guidance; no
summary-bar / cards / drawer / table-first prescriptions; no policy carve-outs; no invented figures,
mappings, or valuation; no resolving an `unresolved_assumption`.
