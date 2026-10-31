---
name: 'step-01-identify-dimension'
description: 'Resolve the input (a dimension name or a live-UI symptom) to a concrete dimension: its storage column(s), the app''s canonical normalizer, the source fields, and any cross-field constraint. Enforces the grounding gate.'
nextStepFile: './step-02-run-audit.md'
---

# Step 1: Identify the Dimension

**Goal:** Turn the input into a precisely-scoped audit target. By the end of this step you can state *"audit the **{dimension}** dimension"* and you know exactly where its values live, which function canonicalizes them, and what cross-field rule (if any) constrains them.

---

## STATE VARIABLES (set in this step)

- `{symptom}` — the raw input (dimension name, or the UI symptom described/screenshotted)
- `{dimension}` — the resolved controlled-vocabulary field (e.g. `supplier`)
- `{storage}` — table + column(s) where the dimension is stored (e.g. `supply_sources.supplier`, `supply_sources.marketplace_buy`)
- `{normalizer}` — the app's canonical normalizer for this dimension (file:export), or `NONE`
- `{source_fields}` — the upstream raw columns the normalizer consumes (e.g. `orders.supplier`, `orders.marketplace`, `orders.source_country`)
- `{cross_field_rule}` — any invariant linking this dimension to another (e.g. "currency must match marketplace country"), or `NONE`

---

## THE GROUNDING GATE (fires first, even in autonomous mode)

State **verb + target** from the input alone: the verb is always *audit*; the target is the dimension. If the input is a dimension name, the target is explicit — proceed. If the input is a UI symptom, you must resolve it to a single dimension:

1. Identify the surface/component the symptom appears on.
2. Trace the symptomatic field back to its storage column(s) — read the component, the action/query that feeds it, the schema.
3. Name the dimension.

If the symptom cannot be pinned to a specific field/dimension — it's too vague, or it implicates several fields with no clear primary — **HALT** with:

```
Cannot ground this audit. The symptom "{symptom}" doesn't resolve to a single
dimension. Which field should I audit? (e.g. supplier, marketplace, currency)
```

Do not guess which field the user meant. Choosing the target for them is intent autonomy, which this workflow does not take — and auditing the wrong field produces confident nonsense.

---

## RESOLVE THE DIMENSION'S MACHINERY

Once the dimension is named:

### 1. Storage

Locate the table + column(s). A dimension is often a *pair*: a display label plus a distinguishing attribute the label is normalized against (e.g. `supplier` + `marketplace_buy`). Capture both — the pair is exactly what render-gap vs data-rot turns on.

### 2. Canonical normalizer

Find the function the app uses to canonicalize this dimension on write. Search for `normalize*`, `canonical*`, alias/mapping tables, the importer/ingest path. Record it as `file:export` in `{normalizer}`.

- If a normalizer exists → note its input signature (the `{source_fields}` it consumes) — step-02 will run real values through it.
- If **no** normalizer exists → set `{normalizer} = NONE`. This is itself a finding: an uncanonicalized controlled vocabulary. Carry it forward; step-03 records it as P1.

### 3. Source fields

The raw columns the normalizer reads (the producer side). These are where source rot is detected in step-02.

### 4. Cross-field rule

Note any invariant tying this dimension to another field — currency↔marketplace-country, status↔timestamp presence, warehouse↔region. Capture as `{cross_field_rule}`; step-03 checks it. If none applies, `NONE`.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/data-quality-audit/steps/step-02-run-audit.md`.

---

## SUCCESS METRICS

- `{dimension}` named and grounded (verb + target stated from input)
- `{storage}`, `{source_fields}`, `{cross_field_rule}` resolved
- `{normalizer}` is either a concrete `file:export` or an explicit `NONE` (carried as a finding)

## FAILURE MODES

- Guessing the dimension from a vague symptom instead of halting (intent-autonomy violation)
- Capturing only the display label and missing its distinguishing attribute — render-gap detection then can't work
- Approximating the normalizer's logic instead of locating the real function
- Treating "no normalizer found" as "no problem" instead of as a P1 finding
