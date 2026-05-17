---
name: 'step-06-suggest-ui'
description: 'Evaluate whether the traced pipeline would benefit from a user-facing pipeline visualization component, and offer to build it'
---

# Step 6: Suggest Pipeline UI

**Goal:** Evaluate whether the traced data flow is something end users would benefit from *seeing* — not just developers. If so, offer to build a pipeline visualization component that surfaces the flow as a live, interactive UI element.

---

## AVAILABLE STATE

From previous steps:

- `{anchor}` — The anchor point
- `{stages}` — Ordered pipeline stages with shape in/out
- `{live_data}` — Captured data values
- `{stack}` — Project stack
- `{gaps}` — Audit findings

---

## EVALUATION CRITERIA

Score the traced pipeline against these signals. Each signal is +1. A score of 3+ triggers the suggestion.

### Positive signals (suggest UI)

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

- **Score 3+:** Strong candidate → suggest building the UI
- **Score 1-2:** Possible candidate → mention it as an option but don't push
- **Score 0 or below:** Not a candidate → skip suggestion, end workflow

---

## AUTONOMOUS MODE GATE

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true` in config:
> - **Score 3+:** Auto-accept. Proceed directly to "BUILD THE COMPONENT" without asking.
> - **Score 1-2:** Note the opportunity in the final summary but do NOT build. The signal is too weak for autonomous action.
> - **Score 0 or below:** Skip suggestion entirely.

---

## WHEN TO SUGGEST

If score >= 1, present the suggestion. Tailor the enthusiasm to the score:

### Score 3+ (strong candidate)

```
**Pipeline UI opportunity detected.**

This flow has {n} stages with trackable status — it's a strong candidate for
a user-facing pipeline visualization. Right now the user sees the end result
but not the journey:

**Stages that would be visible:**
{For each stage:}
  {icon} **{stage_name}** — {one-line description}
    Status: {what determines success/failure/pending}
    Data shown: {key fields the user would see at this stage}

**User value:**
- {Why seeing the pipeline helps — e.g., "Users can see where an import stalled instead of just seeing 'failed'"}
- {What question this answers — e.g., "Is my ASIN verified? Is the listing active? What's the current price?"}

**Want me to build this?** I have all the stage definitions, data shapes, and
status logic from this trace — I can generate the component now.
```

In non-autonomous mode, wait for user response. In autonomous mode with score 3+, proceed immediately.

### Score 1-2 (possible candidate)

```
**Note:** This flow has some pipeline characteristics ({n} stages, status tracking)
that could work as a visualization. It's not as clear-cut as a full pipeline —
{reason for lower score}. Let me know if you'd like to explore it.
```

### Score 0 or below

No suggestion. End workflow.

---

## IF THE USER ACCEPTS: BUILD THE COMPONENT

When the user says yes (or in autonomous mode with score 3+), build the pipeline visualization component.

### Component Design Principles

Model after the project's existing pipeline-style UI patterns. The component should render as a **vertical stage timeline** where each stage is a card showing:

1. **Status indicator** — icon/color based on the stage's state (complete, in-progress, pending, failed)
2. **Stage name** — bold heading describing what happens at this stage
3. **Description** — one sentence explaining what this stage does
4. **Data card** — key-value table showing the actual data at this stage (field name → live value)
5. **Timestamp** — when this stage was last updated (relative time, e.g., "9d ago")

### Architecture

```
PipelineVisualization (container)
├── PipelineHeader (title, summary stats)
├── PipelineStage[] (one per stage)
│   ├── StatusIndicator (icon + color)
│   ├── StageTitle + Description
│   └── DataCard (key-value pairs from the stage's data)
└── PipelineActions (optional: refresh, archive, etc.)
```

### Data Contract

The component receives a **pipeline definition** that maps directly from the trace-flow output:

```typescript
interface PipelineStage {
  name: string
  description: string
  status: 'complete' | 'in_progress' | 'pending' | 'failed' | 'skipped'
  layer: string
  data: Record<string, string | number | boolean | null>
  file?: string
  updatedAt?: string
}

interface PipelineVisualizationProps {
  title: string
  description: string
  stages: PipelineStage[]
  anchor: string
}
```

### Implementation Steps

1. **Create the component** — Place in the project's component directory following existing conventions (e.g., `frontend/src/components/` or `app/components/` depending on the stack)
2. **Style it** — Match the project's existing design patterns (check for Tailwind, CSS modules, styled-components, or inline styles)
3. **Wire it up** — Connect to the API endpoint or data source that feeds the stages
4. **Add status logic** — Map the backend state to stage status (complete/in_progress/pending/failed)
5. **Add data cards** — Render the key-value pairs from each stage's data
6. **Handle loading/error/empty** — Follow the project's existing patterns for these states

### What NOT to build

- Don't build a generic "pipeline framework" — build a specific component for THIS flow
- Don't add routing or navigation — this is a component that gets embedded in an existing page
- Don't add edit/mutation functionality — this is read-only visualization
- Don't over-abstract — if there are 5 stages, it's fine to have the stage definitions inline rather than in a config file

### Handoff to quick-dev

If the component build is substantial (more than ~50 lines of changes), the agent should:

1. Generate a quick tech-spec describing the component, its data sources, and where it gets embedded
2. Offer to execute it via the quick-dev workflow: `→ /bmad:bmm:workflows:quick-dev {spec_path}`

If it's small (a single component file + embedding it in an existing page), build it directly in this step.

---

## PRESENT FINAL SUMMARY

After evaluation (whether or not a UI was suggested/built):

```
**Trace-flow workflow complete.**

**Pipeline:** {source} → ... → {render} ({stage_count} stages)
**Audit:** {n} issues found
**Pipeline UI:** {suggested + accepted | suggested + declined | not suggested — {reason}}

**Deliverable:** {report_file_path}
{If component built: **Component:** {component_file_path}}
```

---

## WORKFLOW COMPLETE

The trace-flow workflow ends here. Deliverables:

1. Pipeline document at `{implementation_artifacts}/flow-trace-{slug}-{date}.md`
2. Pipeline visualization component (if built) in the project's component directory

---

## SUCCESS METRICS

- Pipeline evaluated against all positive and negative signals
- Score calculated and appropriate suggestion level chosen
- If suggested: stages, status logic, and user value clearly articulated
- If accepted: component built following project patterns, wired to real data
- If not suggested: clear reason noted in final summary
- Final summary presented

## FAILURE MODES

- Suggesting a pipeline UI for every trace (most flows are simple CRUD — not everything needs visualization)
- Building a generic framework instead of a specific component for this flow
- Not checking for existing visualizations (suggesting a duplicate)
- Building the component without wiring it to real data (static mockup is useless)
- Over-engineering: adding edit/mutation/routing to what should be a read-only status view
- Suggesting a pipeline UI for internal/developer-only flows that end users never see
