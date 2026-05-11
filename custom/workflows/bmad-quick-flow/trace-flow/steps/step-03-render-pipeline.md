---
name: 'step-03-render-pipeline'
description: 'Produce the human-readable pipeline diagram with stage cards, status indicators, and live data values'

nextStepFile: './step-04-audit.md'
---

# Step 3: Render Pipeline

**Goal:** Produce the artifact — a human-readable pipeline document that shows every stage of the data flow as a vertical chain of stage cards, each with status, description, and live data values. This is the deliverable.

---

## AVAILABLE STATE

From previous steps:

- `{anchor}` — The anchor point being traced
- `{anchor_type}` — Classification
- `{stack}` — Project stack
- `{stages}` — Ordered pipeline stages with shape in/out
- `{live_data}` — Captured data values at each stage (or static analysis results)
- `{server_live}` — Whether live data was captured

---

## OUTPUT FORMAT

Write the pipeline document to `{implementation_artifacts}/flow-trace-{slug}-{date}.md` where `{slug}` is derived from the anchor (e.g., `leads-detail`, `pipeline-progress`, `run-start-endpoint`).

### Document Structure

```markdown
---
title: 'Data Flow: {anchor description}'
created: '{date}'
anchor: '{anchor}'
anchor_type: '{anchor_type}'
stack: '{stack}'
live_data: { true|false }
type: flow-trace
---

# Data Flow: {anchor description}

**Anchor:** `{anchor}` ({anchor_type})
**Stack:** {stack}
**Traced:** {date}
**Live data:** {yes — captured from running server | no — static analysis only}
**Stages:** {count}

---

## Pipeline Overview

{Brief one-sentence description of what this pipeline does — e.g., "Loads a lead record from SQLite, enriches it via the agent pipeline, streams progress via SSE, and renders the lead detail card."}
```

{source_name} → {transform_name} → {transport_name} → {state_name} → {render_name}

```

---

## Stages

{For each stage, render a stage card:}

### ✅ Stage 1: {Stage Name}

{One-sentence description of what happens at this stage.}

| Field | Value |
|-------|-------|
| {field_1} | `{actual_value}` |
| {field_2} | `{actual_value}` |
| {field_3} | `{actual_value}` |

> **File:** `{file_path}:{line_number}`
> **Layer:** {source | model | service | transport | state | render}

---

### ✅ Stage 2: {Stage Name}

{description}

| Field | Value |
|-------|-------|
| {field_1} | `{value — possibly transformed from previous stage}` |

> **File:** `{file_path}:{line_number}`
> **Layer:** {layer}
> **Transform:** {if fields were renamed, computed, or filtered — describe the change}

---

{Continue for all stages...}

## Data Shape Evolution

{Show how the data shape changes across stages — field-level diff view:}

| Field | {Stage 1} | {Stage 2} | {Stage 3} | ... | {Stage N} |
|-------|-----------|-----------|-----------|-----|-----------|
| {field_a} | ✅ `{val}` | ✅ `{val}` | ✅ `{val}` | | ✅ `{val}` |
| {field_b} | ✅ `{val}` | ✅ `{val}` | ❌ dropped | | — |
| {field_c} | — | — | ✅ computed | | ✅ `{val}` |
| {field_d} | ✅ `{val}` | 🔄 renamed → {new_name} | ✅ `{val}` | | ✅ `{val}` |

```

---

## STAGE CARD RULES

### Status Indicators

Each stage card gets a status icon:

| Icon | Meaning                                                                            |
| ---- | ---------------------------------------------------------------------------------- |
| ✅   | Stage confirmed — data flows through and all fields accounted for                  |
| ⚠️   | Stage has gaps — some fields present but others are null, missing, or not rendered |
| ❌   | Stage broken — data doesn't reach this stage or critical fields missing            |
| 🔍   | Stage unverified — could not capture live data, static analysis only               |

### Data Values in Stage Cards

- Show **actual captured values** when available, not types
- Format values for readability: truncate long strings to 80 chars with `...`, format dates as relative ("9d ago"), format currencies with symbols
- For arrays/objects, show the count and first item: `[3 items] { "name": "Exa Search", ... }`
- For null/undefined, show explicitly: `null` or `—` (and note if this is expected or a gap)
- For sensitive values: `[REDACTED]`

### Transform Annotations

When a stage transforms data, annotate what changed:

- **Renamed:** `backend_field` → `frontendField`
- **Computed:** `= price * quantity` → `£184.41`
- **Filtered:** `{field} dropped (not in API response)`
- **Formatted:** `1647302400` → `"2022-03-15"` (Unix timestamp → ISO date)
- **Aggregated:** `sources[].price` → `min: £12.00, max: £45.00`

---

## BRANCHES AND JOINS

If the pipeline has branches or joins (identified in step 1):

### Branch Rendering

Show the branch point, then indent the branches:

```markdown
### Stage 3: API Response (branches)

{Data splits here — consumed by multiple components}

#### Branch A: LeadCard component

| Field  | Value        |
| ------ | ------------ |
| name   | `Widget Pro` |
| status | `active`     |

#### Branch B: PricingPanel component

| Field         | Value    |
| ------------- | -------- |
| buy_box_price | `£61.47` |
| lowest_price  | `£61.47` |
```

### Join Rendering

Show the join point with its sources:

```markdown
### Stage 4: LeadDetail component (joins)

{Combines data from two sources}

**From:** GET /api/leads/{id} + SSE /api/runs/{id}/stream

| Field    | Source | Value        |
| -------- | ------ | ------------ |
| name     | REST   | `Widget Pro` |
| progress | SSE    | `85%`        |
```

---

## PRESENT TO USER

After writing the pipeline document, present a summary:

```
**Flow trace complete:** {report_file_path}

**{anchor}** — {stage_count} stages traced

{source} → {transform} → ... → {render}

**Data captured:** {live | static only}
**Status:** {all_green | n gaps found | n stages broken}

{If gaps/broken stages exist:}
**Issues found — proceeding to audit.**

{If all green:}
**All stages confirmed — pipeline is fully connected.**
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/trace-flow/steps/step-04-audit.md` — even if all stages are green, the audit checks for subtler issues (unused fields, redundant fetches, type drift).

---

## SUCCESS METRICS

- Pipeline document written to implementation artifacts
- Every stage has a card with status indicator
- Live data values shown at every stage where capture was possible
- Data shape evolution table tracks every field across all stages
- Transforms explicitly annotated (renames, computations, filters)
- Branches and joins rendered clearly
- Summary presented to user

## FAILURE MODES

- Showing types instead of values ("string" instead of "Widget Pro")
- Omitting the data shape evolution table (this is the most valuable view for spotting where fields appear/disappear)
- Not truncating large values (full JSON blobs make the doc unreadable)
- Marking all stages ✅ without verifying live data
- Missing branch/join rendering for multi-consumer or multi-source stages
