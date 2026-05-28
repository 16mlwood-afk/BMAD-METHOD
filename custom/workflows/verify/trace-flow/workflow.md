---
name: trace-flow
description: 'Trace data flow through a page, endpoint, or feature. Produces a human-readable pipeline diagram showing every stage from DB/source to UI render, with live data values at each stage. Optionally audits for gaps and dead fields.'
---

# Trace Flow Workflow

**Goal:** Given an anchor point (page route, API endpoint, component, or DB table), trace the complete data lifecycle and produce a visual pipeline document showing every stage data passes through — with the actual values flowing at each stage when a live server is available.

**Your Role:** You are a data-flow cartographer. You read code across the full stack, identify every stage where data changes shape or crosses a boundary, and produce a pipeline diagram that makes the invisible visible. When the app is running, you capture real data at each stage to show what's actually flowing — not just what's typed.

**Key Principle — The map matters more than the conclusion.** The gap between an engineer's mental model ("the leads page shows lead score") and what actually happens (six stages, two transforms, one silent drop) is rarely zero. Trace-flow's value is in surfacing that gap honestly — the stages, the transforms, the data the backend hands the frontend but the frontend never renders. The user decides what to do about it. Don't pre-empt that decision; produce the map.

**Sibling workflow — what trace-flow is NOT.** Wire-check fixes broken connections. Trace-flow describes the full topology, including connections that are intentionally absent. If you find a loose wire while tracing, *note it as a gap* — don't fix it. The user (or a follow-up `wire-check` run) handles repair. Trace-flow's discipline is in the cartography, not the surgery.

---

## CRITICAL RULES

- **Map the full stack, not just the layer you think matters.** The bug always hides in the layer you didn't bother to read. Walk every stage, even the ones that look trivial.
- **Live values beat static types.** When the server is running, capture the actual data at each stage. Types lie — they describe what the developer intended, not what the wire carries. Live data is the ground truth.
- **Name every gap explicitly.** "Available at API, not rendered in UI" is a category — it's not necessarily a bug, but it's never trivial. Surface it. Let the user decide whether to surface the field or document the suppression.
- **Don't propose fixes.** Repair belongs to wire-check (broken wires) or design-handoff (UX questions about what to surface). Trace-flow stops at "here's the map" — that's the value.
- **The audit (step-04) is honest, not defensive.** Identify dead fields, missing data, and shape mismatches without softening. The user can disagree with a clear claim; they can't disagree with a vague report.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{anchor}`, `{anchor_type}`, `{anchor_file}`, `{anchor_line}`, `{stack}`, `{stages}`, `{live_data}`, `{gaps}`, `{server_live}`, `{page_purpose}`, `{user_decisions}`, `{available_not_shown}`, `{recommendations}`, `{decisions_file}`
- Sequential progression through 6 phases: map → snapshot → render → audit → evaluate-purpose → suggest UI

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

### Input

The user provides an **anchor point** — the starting location for the trace. This can be:

- **Page route:** `/leads`, `/leads/:id`, `/pipeline` — traces from the page component back to its data sources
- **API endpoint:** `GET /api/leads`, `POST /api/runs/{id}/start` — traces from the endpoint handler to DB and forward to consumers
- **Component:** `LeadCard.tsx`, `PipelinePanel.tsx` — traces from the component to its data sources (props, hooks, API calls)
- **DB table/model:** `leads`, `sources`, `RunState` — traces from the schema forward through API to UI
- **Feature name:** "lead scoring", "pipeline progress" — agent identifies the relevant anchor from the codebase

If no anchor is provided, ask the user. If the anchor is ambiguous (e.g., a feature name that touches multiple pages), present the options and let the user choose — or in autonomous mode, trace the primary page.

### Worktree Requirement

This workflow is entirely read-only — it produces diagnostic artifacts but never edits source code. No worktree is needed. The discipline matters: a trace-flow run that "just fixed the obvious wire while I was there" is not trace-flow; it's wire-check wearing a mantle. If the pipeline UI evaluation (step 6) identifies a design opportunity, it writes a handoff artifact and routes the user to the design pipeline — it never edits implementation code directly.


### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/trace-flow`

### Live Server Detection

Check whether the backend is running:

```bash
lsof -iTCP:8000 -sTCP:LISTEN -P 2>/dev/null | grep -q LISTEN
```

Store as `{server_live}` (true/false). If live, the workflow will capture real data at each stage. If not, static analysis only — note this in the output.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/trace-flow/steps/step-01-map-stages.md` to begin the workflow.
