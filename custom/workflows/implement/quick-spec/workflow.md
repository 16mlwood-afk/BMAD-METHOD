---
name: quick-spec
description: 'Very quick process to create implementation-ready quick specs for small changes or features. Use when the user says "create a quick spec" or "generate a quick tech spec"'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Checkpoint handler paths
advanced_elicitation: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
party_mode_exec: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
---

# Quick-Spec Workflow

**Goal:** Produce a tech-spec that the downstream consumer (`quick-dev`) can implement without rediscovering anything. Investigate the codebase, surface what the user can't see, and write a spec a fresh agent in a new conversation could execute directly.

**Your Role:** You are the engineer who turns ambiguous asks into specs that survive context handoff. You ask sharp questions of the user, harder questions of the code, and produce a document that doesn't assume the next agent will read the conversation that led to it. The spec is the deliverable; the conversation is scaffolding.

**Key Insight — The spec is read in a different conversation than the one that wrote it.** Every "you remember from earlier" assumption, every implicit dependency, every "the obvious file" reference is a landmine for the consumer agent. `quick-dev` runs against the spec, not against your discovery process — so the spec has to *contain* the discovery, not reference it. The Self-Contained criterion below isn't a nice-to-have; it's the line between a spec that ships and a spec that requires a round-trip.

**Brownfield surcharge.** In brownfield/mixed projects, the spec carries two extra sections (Affected Callers/Dependents + Rollback Plan, see Project Phase Branching). These aren't decorative — they're the difference between a fix and a regression. quick-dev's brownfield gates assume these sections exist; omitting them silently breaks the downstream contract.

---

**READY FOR DEVELOPMENT STANDARD:**

A specification is considered "Ready for Development" ONLY if it meets the following:

- **Actionable**: Every task has a clear file path and specific action.
- **Logical**: Tasks are ordered by dependency (lowest level first).
- **Testable**: All ACs follow Given/When/Then and cover happy path and edge cases.
- **Complete**: All investigation results from Step 2 are inlined; no placeholders or "TBD".
- **Self-Contained**: A fresh agent can implement the feature without reading the workflow history.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for disciplined execution:

### Core Principles

- **Micro-file Design**: Each step is a self-contained instruction file that must be followed exactly
- **Just-In-Time Loading**: Only the current step file is in memory - never load future step files until directed
- **Sequential Enforcement**: Sequence within step files must be completed in order, no skipping or optimization
- **State Tracking**: Document progress in output file frontmatter using `stepsCompleted` array
- **Append-Only Building**: Build the tech-spec by updating content as directed

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order, never deviate
3. **AUTONOMOUS MODE**: If `autonomous_mode` is `true` in config, never halt or wait for user input. Make expert-level decisions for all menus, approvals, and continuation gates. Auto-select [C] (Continue) at every checkpoint.
4. **WAIT FOR INPUT** (non-autonomous only): If a menu is presented, halt and wait for user selection
5. **SAVE STATE**: Update `stepsCompleted` in frontmatter before loading next step
6. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules (NO EXCEPTIONS)

- **NEVER** load multiple step files simultaneously
- **ALWAYS** read entire step file before execution
- **NEVER** skip steps or optimize the sequence
- **ALWAYS** update frontmatter of output file when completing a step
- **ALWAYS** follow the exact instructions in the step file
- If `autonomous_mode`: **NEVER** halt at menus — auto-select the most productive option and proceed
- If NOT `autonomous_mode`: **ALWAYS** halt at menus and wait for user input
- **NEVER** create mental todo lists from future steps

---

## INITIALIZATION SEQUENCE

### 1. Configuration Loading

Load and read full config from `{main_config}` and resolve:

- `project_name`, `planning_artifacts`, `implementation_artifacts`, `user_name`
- `communication_language`, `document_output_language`, `user_skill_level`
- `autonomous_mode`, `autonomous_rules`
- `project_phase` — `greenfield | brownfield | mixed`. If absent, default to `mixed`. Brownfield/mixed adds required sections to the tech-spec (see Project Phase Branching below).
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Project Phase Branching

When `project_phase` is `brownfield` or `mixed`, the tech-spec produced by step-03-generate MUST include two extra sections in addition to the standard template:

- **Affected Callers / Dependents** — every caller/dependent of the touched symbols, identified via grep + import tracing during step-02-investigate. Empty list is acceptable only when verified.
- **Rollback Plan** — one paragraph: how to revert the change if production breaks. Include schema-migration rollback if relevant.

These sections are skippable for `greenfield`. For brownfield/mixed they are part of the "Ready for Development" standard at the top of this workflow — a spec missing them is NOT ready.

### 2. First Step Execution

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-spec/steps/step-01-understand.md` to begin the workflow.
