---
name: 'step-03-walk-edges'
description: 'Walk each candidate edge against the live surface — the "actual" side of the contract. First decide displayed? (source/DOM); a value never shown is out-of-scope, not a failure. For every displayed foreign record, run the six §13 checks: linked-not-inert, expand-in-context + quiet styling, lookups resolved, bidirectional round-trip, canonical identifier. Each edge ends with one verdict.'
nextStepFile: './step-04-classify-and-route.md'
---

# Step 3: Walk the Edges Against the Live Surface

**Goal:** For every candidate edge in `{expected_graph}`, look at the actual surface and produce one verdict. This is the "actual" half of the two-evidence contract — the schema said the edge *could* exist; now the page says whether it's *displayed*, and if so, whether it's a §13-compliant link.

**Live beats inferred at every check.** Render the surface with real data and read the DOM — the same machinery `design-review-pr` step-02 (source scan) and step-03 (DOM render) use. A static source read tells you a value is printed; only a real render tells you whether it's a working link, whether the drawer opens, whether the lookups resolve. Where the project forbids running the app, fall back to source scan and mark the edge's evidence `inferred` (carried to the report so the reader knows which verdicts are live vs static).

---

## AVAILABLE STATE

- `{expected_graph}` (candidate edges), `{ownership_map}`, `{surface_set}`
- `{db_access}`, `{server_live}`

## STATE VARIABLES (set in this step)

- `{walked}` — every edge with its verdict + evidence

---

## THE GATING CHECK — is the foreign record displayed?

Run this first for each candidate edge. It decides scope, and it's the check that keeps the report honest.

- **Check 0 — Displayed?** Does the surface actually put this foreign record on screen — its id, or a field borrowed from it? Read the rendered row/detail, not the schema.
  - **No** → verdict `out-of-scope-candidate`. The schema relates these records, but this surface never shows the foreign one, so §13 imposes no link. Record it (with the reason "not displayed on {surface}") and move on. **This is not a failure** — it's the conscious exclusion that stops the false-positive flood.
  - **Yes** → in scope. Run Checks 1–5 below.

A nullable-FK edge whose foreign record is simply absent on a given row is an **empty-state**, not "not displayed" and not a missing link — the surface shows the slot, the row has nothing to link. Don't confuse a legitimately empty relationship with a torn one.

---

## THE §13 CHECKS (run for every displayed edge)

### Check 1 — Linked, not inert (the primary §13 failure)

- [ ] The displayed foreign record is a **navigable link**, not inert text. Clicking the id (or its row) does something.
- [ ] If it's plain text with no affordance → verdict `inert-reference`. This is §13 hard-failure #1, the one the section exists to kill.

### Check 2 — Expand-in-context, quiet (the mechanism, per policy v6)

- [ ] Acting on the reference opens the foreign record in the project's §7 **right-side drawer over the current surface** — the expand-in-context mechanism — carrying its own fields. Navigating *straight away* to the sibling page as the primary action is the wrong mechanism (the full page is a demoted "Open full {sibling} →" secondary action).
- [ ] The affordance is **quiet** — the demoted blue accent or a hover underline (§4). Styled as a button, CTA, or colored pill → verdict `loud-affordance` (§13 hard-failure #3 — Airtable's function with the wrong form).

### Check 3 — Lookups resolved, not re-keyed

- [ ] Each field the edge's `mandated_lookups` names (a supplier's name, an order's buy-cost, a catalog title/image) is shown inline **resolved from the canonical record**, not re-typed or re-stored on this surface.
- [ ] A mandated lookup that's absent, or shown as only the bare id with no resolved field → verdict `unresolved-lookup`. The link may work; the data pull §13 requires doesn't.
- [ ] A lookup value that's hand-keyed per surface (risks drift from the canonical record) → also `unresolved-lookup`, noted as "re-keyed, not resolved."

### Check 4 — Bidirectional round-trip

- [ ] The relationship is traversable **both ways** through the established pattern: from the borrowing surface to the owned record, and from the owning surface back to the referencing records. A link reachable from A→B but not B→A → verdict `one-directional`.
- [ ] The drill **round-trips** — after expanding/navigating, the operator returns to where they were without losing place. A dead-end drill → also `one-directional` (note: "no round-trip").

### Check 5 — Canonical identifier

- [ ] The record is shown with the **same identifier, same format** (monospace, §4) and the **same label form** as on its owning surface and every other borrowing surface. `UK` on one surface and `Amazon UK` on its sibling for the same marketplace, or a reformatted/re-labelled id → verdict `identifier-drift`.

---

## RECORD EACH EDGE

Give every walked edge one primary verdict (the most severe that applies — `inert-reference` outranks `unresolved-lookup` outranks `identifier-drift`; a compliant edge passes all five). Record secondary verdicts in the detail so nothing is lost.

```
edge: {from} → {to}  ({source}, {direction})
displayed: yes | no(out-of-scope)
verdict: compliant | inert-reference | loud-affordance | unresolved-lookup | one-directional | identifier-drift | out-of-scope-candidate
evidence: live | inferred
on: {surface route}  ({component:line | DOM node})
detail: {what's shown vs what §13 requires; secondary verdicts; mandated lookups present/absent}
```

Store all of it as `{walked}`. Every candidate edge from step-02 must appear in `{walked}` exactly once — in scope with a §13 verdict, or out-of-scope with the not-displayed reason. An edge that vanishes between steps is a silent-partial-implementation defect.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit/steps/step-04-classify-and-route.md`.

---

## SUCCESS METRICS

- Every candidate edge walked; Check 0 (displayed?) run first to set scope
- Every displayed edge carries a §13 verdict backed by surface + component/DOM evidence
- Live-render evidence used wherever the project allows it; static-only edges marked `inferred`
- Out-of-scope (not-displayed) edges recorded with their reason — not dropped
- Nullable-empty relationships distinguished from torn ones

## FAILURE MODES

- Asserting a missing link from the schema without running Check 0 against the page (the false-positive flood)
- Marking an edge `out-of-scope` when the value IS shown but you only read source, not the render — missing the inert-text case static analysis can't see
- Passing Check 1 (it links!) but skipping Check 2 — a CTA-styled link that navigates away "links" yet fails §13's mechanism + form
- Calling a re-keyed lookup "resolved" because the value happens to match today (it will drift)
- Confusing an empty-state (nullable FK, no foreign record on this row) with a missing-required link
- Letting a candidate edge fall out of `{walked}` with no verdict
