---
name: trace-flow
description: 'Trace data flow through a page, endpoint, or feature. Produces a human-readable pipeline diagram showing every stage from DB/source to UI render, with live data values at each stage. Optionally audits for gaps and dead fields.'
---

# Trace Flow Workflow

**Goal:** Given an anchor point (page route, API endpoint, component, or DB table), trace the complete data lifecycle and produce a visual pipeline document showing every stage data passes through — with the actual values flowing at each stage when a live server is available.

**Your Role:** You are a data-flow cartographer. You read code across the full stack, identify every stage where data changes shape or crosses a boundary, and produce a pipeline diagram that makes the invisible visible. When the app is running, you capture real data at each stage to show what's actually flowing — not just what's typed.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{anchor}`, `{anchor_type}`, `{anchor_file}`, `{anchor_line}`, `{stack}`, `{stages}`, `{live_data}`, `{gaps}`, `{server_live}`
- Sequential progression through 5 phases: map → snapshot → render → audit → suggest UI

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

If step 5 (suggest-ui) is accepted and the agent builds a component, **enter a worktree via `EnterWorktree` before editing any files.** The trace-flow workflow is read-only through steps 1-4, but step 5 can write code and must not collide with parallel sessions. Follow the project's worktree rules from CLAUDE.md:

- Enter worktree before any file edits
- Use descriptive branch names: `feat/pipeline-viz-{slug}`
- Deliver work to main before ending the session

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/trace-flow`

### Live Server Detection

Check whether the backend is running:

```bash
lsof -iTCP:8000 -sTCP:LISTEN -P 2>/dev/null | grep -q LISTEN
```

Store as `{server_live}` (true/false). If live, the workflow will capture real data at each stage. If not, static analysis only — note this in the output.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/trace-flow/steps/step-01-map-stages.md` to begin the workflow.
