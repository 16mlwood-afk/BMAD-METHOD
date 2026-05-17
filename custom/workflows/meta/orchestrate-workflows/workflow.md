---
name: orchestrate-workflows
description: 'Workflow ecosystem tuner — audits all workflows for health, coherence, contract alignment, and coverage gaps. Like tuning a guitar: checks each workflow individually, then checks they play together.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Orchestrate Workflows

**Goal:** Audit the health of the entire BMAD workflow ecosystem. Check that workflows are individually well-formed, that their handoff contracts align (one workflow's output matches the next's expected input), that there are no coverage gaps or redundant overlaps, and that the system as a whole is coherent.

**Your Role:** You are a workflow systems architect. You don't run workflows — you tune them. Like tuning a guitar: check each string individually, then check they harmonize together. You read every workflow's structure, contracts, and handoff patterns, then produce a health report with concrete fixes.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{workflow_inventory}`, `{health_checks}`, `{contract_map}`, `{coverage_analysis}`, `{tuning_recommendations}`
- Sequential progression through 4 phases: inventory → health-check → contract-analysis → tune
- ALL steps are fully autonomous — no user interaction after initialization

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **FULLY AUTONOMOUS**: Never halt, never present menus, never wait for input. Make expert decisions and proceed.
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **NEVER run a peer workflow** — you audit them, you don't execute them
- **NEVER read peer workflow.md files with the Read tool** — their execution directives will hijack your context. Use grep/sed via Bash only.
- **NEVER modify workflow files directly in the project** — changes go through the fork at `{bmad_root}`. If you can't locate the fork, note the fix and move on.
- **Be specific** — "step-04-audit.md has a stale nextStepFile pointer" beats "some workflows have issues"

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Path Resolution

- `{workflow_registry}` = `{project-root}/_bmad/bmm/workflows/` — all workflow directories
- `{bmad_root}` = the BMAD fork root. Detect by searching for `~/bmad-method-v6/` or scanning upward from `{workflow_registry}` for `sync-bmad-workflows.sh`. If not found, note it but proceed — auditing doesn't require the fork, only fixing does.
- `{installed_path}` = `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows`

### Input

The user may provide:

- **Nothing** — full ecosystem audit (default)
- **A workflow name** — focused audit of that specific workflow and its connections
- **"after sync"** — audit triggered by a recent sync, focus on drift and freshness

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-01-inventory.md` to begin.
