---
name: dispatch-followups
description: 'Post-workflow dispatcher — reads handoff artifacts, identifies follow-up workflows to run, auto-executes critical ones and presents optional ones as copy-paste prompts.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Dispatch Followups Workflow

**Goal:** After any workflow completes (or on demand), analyze what was done, identify likely gaps and follow-up needs, and **auto-execute** the critical and recommended follow-up workflows. Optional follow-ups are presented as copy-pasteable prompts for the user to run if desired.

**Your Role:** You are a workflow execution dispatcher. You understand every workflow in the BMAD ecosystem — what it does, what it catches, what inputs it needs. You read the artifacts of completed work, cross-reference against available workflows, and **execute** the high-priority follow-ups directly — eliminating the manual copy-paste-into-clean-terminal loop entirely.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{trigger_context}`, `{changed_files}`, `{file_categories}`, `{workflow_index}`, `{gap_analysis}`, `{execution_results}`
- Sequential progression through 4 phases: gather → index → analyze → execute
- ALL steps are fully autonomous — no user interaction after initialization

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **FULLY AUTONOMOUS**: Never halt, never present menus, never wait for input. Make expert decisions and proceed.
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **NEVER ask the user which workflow to run next** — that's the whole point of this workflow. Assess, then execute.
- **Auto-execute critical and recommended workflows** — spawn each as an Agent sub-agent. Chain-dependent workflows run sequentially; independent workflows run in parallel.
- **Present optional workflows as copy-paste prompts** — include the slash command, all necessary context (file paths, routes, handoff paths), and a one-sentence rationale.
- **NEVER recommend workflows that don't match the work done** — a CSS-only change doesn't need a wire-check.
- **Agent prompts must be self-contained** — the sub-agent has no memory of this session. Bake in every path, context variable, and rationale the target workflow needs.

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

The dispatch phase (steps 1-3) is read-only. Step 4 spawns Agent sub-agents that may edit files — those agents use `isolation: "worktree"` when their target workflow edits code (wire-check, quick-dev, etc.). The dispatch session itself does not need a worktree beyond what it entered at session start.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/meta/dispatch-followups`
- `workflow_registry` = `{project-root}/_bmad/bmm/workflows/` — scan all category subdirectories (`implement/`, `verify/`, `design/`, `meta/`) for peer workflows.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/dispatch-followups/steps/step-01-gather-context.md` to begin.
