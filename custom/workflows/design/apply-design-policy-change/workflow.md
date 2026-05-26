---
name: apply-design-policy-change
description: 'Detect design policy version changes, classify impact per page, and emit scoped briefs (restyle, component refresh, or full handoff). Use when design-policy.md has been updated and affected pages need migration.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_tuning_workflow: '{project-root}/_bmad/bmm/workflows/design/design-tuning/workflow.md'
create_design_policy_workflow: '{project-root}/_bmad/bmm/workflows/design/create-design-policy/workflow.md'
---

# Apply Design Policy Change Workflow

**Goal:** When `design-policy.md` is updated to a new version, systematically determine what each page in the app needs — a visual restyle, a component refresh, or a full design-handoff rerun — and emit scoped briefs for each. This turns "the policy changed" into a governed migration instead of ad-hoc rework.

**Your Role:** You are a design-system governance agent. You understand both the policy diff and the implementation surface. You classify changes precisely so that pages get exactly the work they need — no more (wasteful full redesigns) and no less (missed compliance gaps).

**Key Insight:** Not all policy changes are equal. A tighter status-color rule affects badge components but not page layout. A new page-mode rule restructures operational pages but leaves analytical ones alone. The workflow classifies impact per page, not globally — because the same policy change can be Level 1 for one page and Level 3 for another.

**When to run this workflow:**
- After `modify-design-policy` bumps the policy version
- After a design-tuning session reveals a pattern that gets codified into the policy
- When a stakeholder requests a visual direction change mid-project
- Proactively during sprint planning to detect drift between policy and shipped pages

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables (see below)
- Sequential progression: detect → diff → classify → decide → emit

### State Variables

- `{policy_path}` - Path to current design-policy.md
- `{policy_current}` - Contents of current policy (version N)
- `{policy_previous}` - Contents of previous policy version (version N-1, from git history)
- `{policy_version_current}` - Current version number from frontmatter
- `{policy_version_previous}` - Previous version number
- `{policy_changelog}` - Changelog entries between versions (from section 10 of the policy)
- `{affected_briefs}` - List of design briefs with their `design_policy_version` frontmatter
- `{affected_pages}` - List of pages/routes whose briefs or implementations reference an older policy version
- `{section_diffs}` - Per-section diff classification: unchanged | minor | major
- `{page_impact_map}` - Map of {page → impact level (1, 2, or 3)}
- `{page_action_map}` - Map of {page → action (restyle | component_refresh | full_handoff)}
- `{output_briefs}` - List of generated brief file paths

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `project_name`, `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`, `project_knowledge`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- **Run end-to-end without pausing.** Classify all changes, decide all actions, emit all briefs.
- **Default to the conservative action** when classification is ambiguous (upgrade Level 1 → Level 2, not downgrade).

### Input

The user may provide:

- **Nothing** — the workflow detects the policy change from git history
- **A specific version range** — "diff v2 to v3"
- **A specific page** — "what does the policy change mean for /invoices?"

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/apply-design-policy-change/steps/step-01-detect-versions.md` to begin the workflow.
