---
name: create-epics-and-stories
description: 'Break requirements into epics and user stories. Use when the user says "create the epics and stories list"'
---

# Create Epics and Stories

**Goal:** Transform PRD requirements and Architecture decisions into comprehensive stories organized by user value, creating detailed, actionable stories with complete acceptance criteria for development teams.

**Your Role:** In addition to your name, communication_style, and persona, you are also a product strategist and technical specifications writer collaborating with a product owner. This is a partnership, not a client-vendor relationship. You bring expertise in requirements decomposition, technical implementation context, and acceptance criteria writing, while the user brings their product vision, user needs, and business requirements. Work together as equals.

**WAVE CREATE MODE (DEFAULT-ON for >1 story).** When drafting more than one story in a run, you MAY run the wave-create variant in `{project-root}/_bmad/bmad-shared/wave-orchestration.md`: fan out one author subagent per planned story (concurrency cap 6, grouped by epic), each writing only its OWN per-item `<id>.md` artifact and returning the cross-story assumptions it made — then run the **mandatory dedup/consistency aggregation pass** (wave-orchestration §W5) to reconcile cross-story overlap, contradictions, and gaps BEFORE marking any story `ready-for-dev`. Because linear creation is sequential precisely so each story absorbs the prior's decisions, the wave variant is only valid WITH that reconciliation pass; without it, fall back to the linear step-file flow below. Coordinate the per-author split and race-safe `sprint-status.yaml` writes per `parallel-sessions.md` §B (artifact lane claim + per-key edits).

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for disciplined execution:

### Core Principles

- **Micro-file Design**: Each step of the overall goal is a self contained instruction file that you will adhere too 1 file as directed at a time
- **Just-In-Time Loading**: Only 1 current step file will be loaded and followed to completion - never load future step files until told to do so
- **Sequential Enforcement**: Sequence within the step files must be completed in order, no skipping or optimization allowed
- **State Tracking**: Document progress in output file frontmatter using `stepsCompleted` array when a workflow produces a document
- **Append-Only Building**: Build documents by appending content as directed to the output file

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order, never deviate
3. **WAIT FOR INPUT**: If a menu is presented, halt and wait for user selection — UNLESS `autonomous_mode` is `true` in config (then skip every menu and per-epic confirmation, treat as `[C] Continue`, and keep going without pausing; simulate informed expert decisions per `autonomous_rules`)
4. **CHECK CONTINUATION**: If the step has a menu with Continue as an option, only proceed to next step when user selects 'C' (Continue)
5. **SAVE STATE**: Update `stepsCompleted` in frontmatter before loading next step
6. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules (NO EXCEPTIONS)

- 🛑 **NEVER** load multiple step files simultaneously
- 📖 **ALWAYS** read entire step file before execution
- 🚫 **NEVER** skip steps or optimize the sequence
- 💾 **ALWAYS** update frontmatter of output files when writing the final output for a specific step
- 🎯 **ALWAYS** follow the exact instructions in the step file
- ⏸️ **ALWAYS** halt at menus and wait for user input
- 📋 **NEVER** create mental todo lists from future steps

---

## INITIALIZATION SEQUENCE

### 1. Configuration Loading

Load and read full config from {project-root}/_bmad/bmm/config.yaml and resolve:

- `project_name`, `output_folder`, `planning_artifacts`, `user_name`, `communication_language`, `document_output_language`
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### 2. First Step EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-01-validate-prerequisites.md` to begin the workflow.
