---
name: 'step-02-run-audit'
description: 'Find or generate the read-only audit engine for the dimension, run it against live production values through the app''s canonical normalizer, and capture raw findings.'
nextStepFile: './step-03-classify.md'
---

# Step 2: Run the Audit

**Goal:** Produce raw findings by running the dimension's live production values through the app's canonical normalizer — read-only. Reuse a vetted engine if one exists; otherwise generate one inline.

---

## AVAILABLE STATE

- `{dimension}`, `{storage}`, `{normalizer}`, `{source_fields}`, `{cross_field_rule}`, `{db_access}`

## STATE VARIABLES (set in this step)

- `{engine}` — how the audit was run (existing script path, or "inline-generated")
- `{raw_findings}` — the categorized raw output, pre-classification

---

## FIND OR GENERATE THE ENGINE

### Prefer a vetted engine

Search the project for an existing read-only audit for this dimension — e.g. `scripts/audit-*.{ts,py,…}` that imports `{normalizer}`. If one exists and is read-only, **use it**: it has already been reviewed and it imports the real normalizer (the discipline this workflow demands).

Run it via the project's documented read-only access (`{db_access}`). Capture stdout as `{raw_findings}`.

> Example shape (inbound-flow, `supplier` dimension):
> `DATABASE_URL="$INVENTORY_DATABASE_URL" npx tsx scripts/audit-supply-source-quality.ts`
> This is illustrative — discover the project's actual engine + access from its `CLAUDE.md`; never hardcode credentials.

### Otherwise generate inline

If no engine exists, generate a **read-only** audit that:

1. Imports `{normalizer}` directly (NOT a re-implementation in SQL).
2. Pulls the distinct stored values of `{storage}` (+ counts, + the distinguishing attribute, + `{cross_field_rule}` operands).
3. Pulls the distinct raw `{source_fields}` triples from the producer side.
4. Runs each through `{normalizer}` and records the result.

Keep it `SELECT`-only. If the project has a scripts directory and a normalizer importable from it, write the engine there (it becomes the reusable engine for next time) — but do NOT commit it as part of this read-only workflow; leave that to the routed lane or a follow-up. Run it, capture `{raw_findings}`.

If `{normalizer} = NONE`, there is nothing to run values *through* — instead pull the distinct stored values + counts and a normalized-key approximation (lowercased/trimmed) purely to surface near-duplicates. Mark `{raw_findings}` as **degraded** (no canonical normalizer) so step-03 weights it accordingly.

---

## CAPTURE THE FOUR RAW SHAPES

However the engine runs, `{raw_findings}` must distinguish these shapes (the engine may already label them):

- **Fall-throughs** — values the normalizer could not resolve to a canonical identity (e.g. `marketplace_buy = UNKNOWN`, supplier passed verbatim with no match).
- **Ambiguous groups** — one display label spanning >1 distinguishing attribute on the same entity (the "looks like a duplicate in the UI" shape).
- **Cross-field mismatches** — `{cross_field_rule}` violated (e.g. currency that contradicts the marketplace country).
- **Source rot** — raw `{source_fields}` triples the normalizer still cannot classify (the upstream of the fall-throughs).

Record counts and representative samples for each. Note whether values were captured live or via static fallback (`{server_live}`).

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/data-quality-audit/steps/step-03-classify.md`.

---

## SUCCESS METRICS

- The audit ran read-only against live values (or static fallback, explicitly noted)
- It ran through the real `{normalizer}` — no SQL re-implementation of normalization
- `{raw_findings}` carries counts + samples for all four shapes
- An existing vetted engine was reused if present; an inline one was read-only

## FAILURE MODES

- Re-implementing the normalizer in SQL because it was "easier than importing it" — the cardinal sin; verdicts then drift from app behavior
- Any write to production data
- Running a generated engine but forgetting it imported nothing (silently approximating)
- Reporting only the stored side and never re-running the normalizer on `{source_fields}` (source rot goes undetected)
