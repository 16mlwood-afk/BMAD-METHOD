---
name: 'step-06-suggest-ui'
description: 'Evaluate whether the traced pipeline would benefit from a user-facing visualization. If so, produce a structured handoff for the design pipeline — never build UI directly.'
---

# Step 6: Evaluate Pipeline UI Opportunity

**Goal:** Evaluate whether the traced data flow is something end users would benefit from *seeing* — not just developers. If so, produce a structured handoff artifact that feeds into the design pipeline (design-handoff → Claude Design → design-review). This workflow does NOT build UI components.

**Boundary:** This is the final step of a diagnostic workflow. It evaluates and hands off — it does not design or implement. The design-handoff workflow exists precisely to prevent developer implementation choices from masquerading as design decisions.

---

## AVAILABLE STATE

From previous steps:

- `{anchor}` — The anchor point
- `{stages}` — Ordered pipeline stages with shape in/out
- `{live_data}` — Captured data values
- `{stack}` — Project stack
- `{gaps}` — Audit findings
- `{page_purpose}` — What the page is for
- `{user_decisions}` — What users decide here
- `{available_not_shown}` — Unsurfaced data with value scores
- `{recommendations}` — Value assessments from step 5

---

## EVALUATION CRITERIA

Score the traced pipeline against these signals. Each signal is +1. A score of 3+ means a strong candidate.

### Positive signals (suggest visualization)

| Signal | What to check |
|--------|--------------|
| **Multi-stage progression** | Pipeline has 3+ sequential stages where a record moves through distinct states |
| **User-visible status** | Each stage has a clear success/failure/pending state that a user would care about |
| **Temporal progression** | Stages happen over time (not all at once) — the user benefits from seeing where things are in the process |
| **Live data enrichment** | Each stage adds or transforms data that's meaningful to the user (not just internal reshaping) |
| **No existing visualization** | The page currently shows the *result* of the pipeline but not the *journey* — the user can't see which stages completed or where something stalled |
| **Debugging value** | When something goes wrong, the user currently has no way to see *where* it broke — they just see the final error or missing data |

### Negative signals (don't suggest)

| Signal | What to check |
|--------|--------------|
| **Simple CRUD** | Data goes from form → DB → list. No pipeline to visualize |
| **Internal plumbing** | The stages are infrastructure (cache → queue → worker) that the user shouldn't see |
| **Already visualized** | The page already has a progress indicator, timeline, or pipeline view for this flow |
| **Single-stage** | Data is fetched and displayed in one step — no progression to show |
| **Batch/background** | The pipeline runs in the background with no user watching it in real time |

### Score calculation

```
score = (positive signals present) - (negative signals present)
```

- **Score 3+:** Strong candidate → produce design handoff
- **Score 1-2:** Possible candidate → mention in summary, don't produce handoff
- **Score 0 or below:** Not a candidate → skip, end workflow

---

## WHEN SCORE >= 3: PRODUCE DESIGN HANDOFF

Write a structured handoff artifact to `{implementation_artifacts}/pipeline-ui-handoff-{slug}-{date}.md`. This artifact is input for the design-handoff workflow — it provides the data contracts and user value, NOT the visual design.

### Handoff Artifact Format

```markdown
---
title: 'Pipeline UI Opportunity: {anchor description}'
created: '{date}'
source: 'trace-flow workflow'
type: pipeline-ui-handoff
score: {score}
---

# Pipeline UI Opportunity: {anchor description}

**Source:** trace-flow analysis of `{anchor}`
**Score:** {score}/6 positive signals
**Date:** {date}

## User Context

**Page purpose:** {page_purpose}
**User decisions:** {user_decisions}
**Current gap:** {What the user can't see today — e.g., "The user sees the final result but not which processing stages completed or where something stalled"}

## Pipeline Stages

{For each stage — factual data only, no layout suggestions:}

### Stage {n}: {stage_name}

- **What happens:** {one-sentence description}
- **Status states:** {what determines complete/in-progress/pending/failed}
- **Key data at this stage:** {field names and example values from live capture}
- **Layer:** {source | model | service | transport | state | render}
- **File:** `{file_path}:{line_number}`

## Data Contracts

{For each stage, the input/output shape — TypeScript interfaces or field lists:}

### Stage {n} → Stage {n+1}

**In:** {fields entering this stage}
**Out:** {fields leaving this stage}
**Transform:** {what changed — renames, computations, drops}

## User Value Proposition

- {Why seeing the pipeline helps the user}
- {What question this answers for them}
- {What they currently have to do instead — workarounds, asking support, etc.}

## Unsurfaced Data (from step 5)

{Include the high/medium value fields from the purpose evaluation — the designer should know what data is available}

| Field | Value Score | Data Source | Why Valuable |
|-------|-----------|-------------|-------------|
{from step 5 inventory}

## What This Handoff Does NOT Include

This artifact deliberately excludes:
- Visual layout or component structure
- Color schemes, icons, or styling
- Specific UI patterns (cards, timelines, progress bars)
- Implementation technology choices

These decisions belong to the design pipeline. Run `/bmad:bmm:workflows:design-handoff {this_file_path}` to produce an unbiased Claude Design brief.
```

---

## AUTONOMOUS MODE BEHAVIOR

In autonomous mode:
- **Score 3+:** Write the handoff artifact. Do NOT auto-build any component.
- **Score 1-2:** Note the opportunity in the final summary but do NOT produce a handoff.
- **Score 0 or below:** Skip entirely.

---

## PRESENT FINAL SUMMARY

After evaluation:

```
**Trace-flow workflow complete.**

**Pipeline:** {source} → ... → {render} ({stage_count} stages)
**Audit:** {n} issues found
**Purpose evaluation:** {n} high-value unsurfaced fields identified
**Pipeline UI:** {score >= 3: "opportunity detected — handoff written" | score 1-2: "possible candidate, noted" | score <= 0: "not suggested — {reason}"}

**Deliverables:**
1. Pipeline trace: {report_file_path}
{If score >= 3:}
2. Pipeline UI handoff: {handoff_file_path}
   → Run `/bmad:bmm:workflows:design-handoff {handoff_file_path}` to produce the Claude Design brief.

{If high-value unsurfaced fields exist:}
**Data opportunities:** {count} field(s) with product value not currently shown.
   → Include in design brief when the page is next redesigned.
```

---

## WORKFLOW COMPLETE

The trace-flow workflow ends here. Deliverables:

1. Pipeline document at `{implementation_artifacts}/flow-trace-{slug}-{date}.md`
2. Decisions file at `{implementation_artifacts}/flow-trace-decisions-{slug}.yaml`
3. Pipeline UI handoff at `{implementation_artifacts}/pipeline-ui-handoff-{slug}-{date}.md` (if score >= 3)

No code is written by this workflow. UI implementation goes through the design pipeline.

---

## SUCCESS METRICS

- Pipeline evaluated against all positive and negative signals
- Score calculated correctly
- If score >= 3: structured handoff artifact written with data contracts and user value
- Handoff artifact contains NO design decisions (no layout, no components, no styling)
- Clear next-step prompt pointing to design-handoff workflow
- Final summary presented with all deliverable paths

## TERMINAL — Behavior Update Digest (STD-DIGEST-001)

Audit-lane terminal: alongside the diagnostic handoff artifact, emit the **Behavior Update Digest** per `shared/behavior-update-digest.md` — the handoff IS the `handoff_delta`, any unsurfaced-data finding is a `story_candidate`, plus `doctrine_delta` / `owner_gated` / `completion_disposition` (STD-COMPLETION-001 `advisory`). The diagnostic-not-implementation boundary above is unchanged — the digest never builds UI or auto-runs design-handoff.

## FAILURE MODES

- Building a UI component directly (this workflow is diagnostic, not implementation)
- Including layout suggestions in the handoff ("use a vertical timeline", "render as cards")
- Auto-executing design-handoff (that's a separate workflow the user or dispatch-followups should trigger)
- Suggesting a pipeline UI for every trace (most flows are simple CRUD)
- Not including the step-5 unsurfaced data inventory in the handoff (the designer needs this)
- Suggesting a pipeline UI for internal/developer-only flows that end users never see
