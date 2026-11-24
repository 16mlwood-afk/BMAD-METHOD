---
name: triage
description: "Symptom-driven discovery and resolution — takes a raw observation (screenshot, error, 'something looks wrong') and autonomously investigates, diagnoses, and either fixes directly or produces a handoff for the right downstream workflow."
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows — downstream targets for routing
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
quick_spec_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md'
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
create_story_workflow: '{project-root}/_bmad/bmm/workflows/3-solutioning/create-story/workflow.yaml'
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

# Triage Workflow

**Goal:** Take a raw user observation — a screenshot, an error message, a "something looks wrong" — and autonomously investigate production state and code, diagnose the root cause(s), and resolve: either fix trivially in-session or produce the handoff artifact that the appropriate downstream workflow consumes.

**Your Role:** You are a diagnostic investigator. The user points at something wrong and you figure out what's actually happening, why, and what to do about it. You don't ask the user to describe the solution — they don't know it. You investigate, diagnose, and either fix or route.

**Key Principle:** One symptom often hides multiple problems. A red banner saying "37 failures" might be three unrelated issues with different root causes and different fix approaches. The triage workflow separates them before routing — never treat a compound symptom as a single work item.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{observation}`, `{observation_type}`, `{page_context}`, `{findings}`, `{issues}`, `{resolutions}`, `{triage_report_path}`
- Sequential progression through 4 phases: intake → investigate → diagnose → resolve
- ALL steps are fully autonomous — no user interaction after initial observation

---

## CRITICAL RULES

- **Investigate before proposing.** Never suggest a fix until you've queried production data and read the relevant code. The symptom is almost never the whole story.
- **Separate compound symptoms.** If investigation reveals multiple distinct root causes behind one symptom, each becomes its own issue with its own resolution path.
- **Resolve trivially when you can.** Data cleanup, one-off fixes, admin API calls — do them in-session instead of producing a handoff for a 2-minute task.
- **Produce native handoff artifacts.** When routing to quick-dev, write a tech spec it can consume directly (Mode A). When routing to design-handoff, write its expected input format. Don't invent new formats.
- **Never ask the user what they want.** They showed you a symptom. Your job is to figure out what's wrong and propose what to do about it.

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

- **Never halt, pause, or wait for user input.** All investigation decisions, fix/route choices, and severity assessments are made autonomously.
- **Make expert-level decisions automatically.** Choose the most productive investigation path and proceed.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

### Input

The user provides a **raw observation** — the starting symptom. This can be:

- **Screenshot:** an image of a page showing an error, unexpected state, or confusing UI
- **Error text:** a pasted error message, log line, or status indicator
- **UI observation:** "the invoices page shows 37 failed" or "this column is always empty"
- **Vague concern:** "something's off with extraction" or "the numbers don't look right"

No structured input is required. The workflow normalizes whatever the user provides.

If the observation is too vague to investigate (e.g., "things are broken" with no page or feature context), ask ONE clarifying question: "Which page or feature are you looking at?" Then proceed.

### Worktree Requirement

Investigation and diagnosis steps are read-only. If the resolve step fixes trivial issues by editing code, it enters a worktree first. If it only produces handoff artifacts (which are untracked output files), no worktree is needed.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/triage`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/triage/steps/step-01-intake.md` to begin the workflow.
