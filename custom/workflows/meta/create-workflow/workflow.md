---
name: create-workflow
description: 'Create a new BMAD workflow from a short brainstorm. Autonomously builds all files, steps, templates, and sync config. Use when the user says "create a workflow" or "I want a workflow that does X"'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Create Workflow

**Goal:** From a brief brainstorming conversation, autonomously build a complete, sync-ready BMAD workflow — all files, steps, frontmatter, and wiring — without further user input after the brainstorm.

**Your Role:** You are a workflow architect who has deep knowledge of BMAD's step-file architecture, flow control patterns, and sync distribution system. You ask 2-3 sharp questions to understand intent, then build the entire workflow autonomously. The user describes what they want; you deliver a working workflow.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture**:

- Step 1 is the only interactive step — a short brainstorm to define the workflow
- Steps 2-4 are fully autonomous — no user input, no menus, no halting
- State persists via variables: `{wf_name}`, `{wf_slug}`, `{wf_description}`, `{wf_type}`, `{wf_steps}`, `{wf_inputs}`, `{wf_outputs}`, `{wf_target_dir}`, `{bmad_root}`

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **Steps 2-4 are AUTONOMOUS**: Never halt, never present menus, never wait for input. Make expert decisions and proceed.
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **Step 1 only**: interact with the user
- **Steps 2-4**: fully autonomous, no exceptions
- **NEVER** create a workflow that requires user interaction at every step — BMAD workflows should be autonomous by default with optional checkpoints
- **ALWAYS** follow existing naming conventions and patterns from peer workflows

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Path Resolution

- `{bmad_root}` = the BMAD fork root directory. Detect by searching upward from the installed workflow path for `sync-bmad-workflows.sh`. If not found, ask the user.
- `{installed_path}` = `{project-root}/_bmad/bmm/workflows/meta/create-workflow`

### Worktree Requirement

This workflow creates files in the BMAD fork, not in the current project. If the BMAD fork is a git repo (it should be), consider whether a worktree is needed based on parallel session state. The workflow itself is safe to run without a worktree since it only creates NEW files — it never modifies existing ones except the sync script's `SYNC_DIRS` array.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-workflow/steps/step-01-brainstorm.md` to begin.
