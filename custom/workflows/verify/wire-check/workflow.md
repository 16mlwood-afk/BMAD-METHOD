---
name: wire-check
description: 'Trace data flow end-to-end from a quick-dev handoff artifact. Catches loose wires, format mismatches, and dead counters between backend and frontend. Autonomously fixes all issues found.'
---

# Wire Check Workflow

**Goal:** Take a quick-dev handoff artifact and verify that every data field the implementation touches flows correctly from backend generation through SSE/API transport to frontend state and UI rendering. Report loose wires — places where the chain breaks — then **autonomously fix all issues**, regardless of severity.

**Your Role:** You are a meticulous integration auditor AND fixer. You read code across the full stack, trace data flows, report what's connected and what's not, then fix every issue you find.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{handoff_path}`, `{wires}`, `{findings}`, `{baseline_commit}`
- Sequential progression through 6 phases: map → trace → report → fix → deliver → handoff

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
- **Fix ALL issues found** — including low-severity ones. Every loose, mismatched, or dead wire gets resolved.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

### Worktree Requirement

**Before editing any files**, enter a worktree via `EnterWorktree`. The wire-check workflow now writes code (step 04) and must not collide with parallel sessions. Follow the project's worktree rules from CLAUDE.md:

- Enter worktree before any file edits
- Use descriptive branch names: `fix/wire-check-{slug}`
- Deliver work to main before ending the session

### Input

The user provides a handoff artifact path (e.g., `_bmad-output/implementation-artifacts/handoff-screenshot-pipeline-2026-05-06.md`). If no path is provided, check `{implementation_artifacts}` for the most recent `handoff-*.md` file and confirm with the user.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/wire-check`

### Baseline Commit

Capture `{baseline_commit}` = `git rev-parse HEAD` at workflow start.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/wire-check/steps/step-01-map-wires.md` to begin the workflow.
