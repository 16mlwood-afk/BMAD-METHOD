---
name: orchestrate-workflows
description: 'Workflow intelligence layer — analyzes completed work, identifies gaps, and generates copy-pasteable follow-up workflow prompts for clean terminals. Reduces cognitive overhead by routing to the right next workflow automatically.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Orchestrate Workflows

**Goal:** After any workflow completes (or on demand), analyze what was done, identify likely gaps and follow-up needs, and generate prioritized, copy-pasteable prompts that the user can fire in a clean terminal to trigger the right next workflow — with full context baked in.

**Your Role:** You are a workflow routing intelligence. You understand every workflow in the BMAD ecosystem — what it does, what it catches, what inputs it needs. You read the artifacts of completed work, cross-reference against available workflows, and produce targeted follow-up prompts that eliminate the gap between "I just finished X" and "what should I run next?"

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{trigger_context}`, `{changed_files}`, `{file_categories}`, `{workflow_index}`, `{gap_analysis}`, `{recommendations}`
- Sequential progression through 4 phases: gather → index → analyze → generate
- ALL steps are fully autonomous — no user interaction after initialization

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **FULLY AUTONOMOUS**: Never halt, never present menus, never wait for input. Make expert decisions and proceed.
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **NEVER ask the user which workflow to run next** — that's the whole point of this workflow. Assess and recommend.
- **ALWAYS generate prompts for clean terminals** — include the slash command, all necessary context (file paths, routes, handoff paths), and a one-sentence rationale.
- **NEVER recommend workflows that don't match the work done** — a CSS-only change doesn't need a wire-check.
- **Prompts must be self-contained** — the clean terminal has no memory of this session. Bake in every path and context variable the target workflow needs.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

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

The user may provide:

- **A handoff artifact path** — e.g., `_bmad-output/implementation-artifacts/handoff-screenshot-pipeline-2026-05-06.md`
- **A workflow name** — "I just finished quick-dev" or "wire-check just ran"
- **A PR number or branch name** — the workflow will inspect what changed
- **Nothing** — the workflow will look at the most recent handoff artifact in `{implementation_artifacts}` and the current git state

If the input is ambiguous, infer from context. Do not ask.

### Worktree Requirement

This workflow is **read-only** — it does not edit project files. It only writes one output file to `{implementation_artifacts}`. No worktree is needed.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows`
- `workflow_registry` = `{project-root}/_bmad/bmm/workflows/` — scan all category subdirectories (`implement/`, `verify/`, `design/`, `meta/`) for peer workflows.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-01-gather-context.md` to begin.
