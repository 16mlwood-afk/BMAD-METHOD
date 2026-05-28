---
name: modify-design-policy
description: 'Refine an existing project design policy when the tone, density, or component language needs adjustment. Use when the user says "this feels too casual", "make it more corporate", "tighten the density", or wants the same product to feel different.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
create_design_policy_workflow: '{project-root}/_bmad/bmm/workflows/design/create-design-policy/workflow.md'
apply_design_policy_change_workflow: '{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/workflow.md'
design_standards: '{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md'
---

# Modify Design Policy Workflow

**Goal:** Make targeted edits to an existing `design-policy.md` when the visual direction, tone, density, or component language needs refinement — without rewriting the whole document.

**Your Role:** You are an editor, not a creator. The policy already exists and downstream artifacts depend on it. Your job is to localize the change to the smallest set of sections needed, preserve the rest, bump the version, and surface the downstream impact so the user can decide whether to also run `apply-design-policy-change`.

**Key Insight:** A policy change is rarely a full rewrite. The user usually means one of: (a) the tone is wrong (too casual / too corporate / too playful), (b) the density preference is wrong (cards instead of tables, or vice versa), (c) the component language is misaligned with the product's actual use, or (d) a hard failure needs to be added or removed. Identify which axis is moving before touching the document.

**When to use a different workflow instead:**
- No policy exists yet → `create-design-policy`
- A new page or feature needs design → `design-handoff`
- The policy already changed and now downstream artifacts need to catch up → `apply-design-policy-change`

---

## CRITICAL RULES

- **Localize the change.** Identify the smallest set of sections that move; leave the rest untouched. A "make it more corporate" ask is rarely a full rewrite — pinpoint the axis (tone, density, components) and edit there.
- **Bump the version.** Every policy revision changes the version number. Downstream `apply-design-policy-change` reads version diffs to decide what migrates; an unbumped revision is invisible to it.
- **Surface downstream impact explicitly.** Step-03 produces `{downstream_impact}` — pages and artifacts that may need a follow-up. Don't hide it. The user decides whether to run `apply-design-policy-change`; the workflow's job is to make the choice legible.
- **Confirmation gates the write.** In non-autonomous mode, step-03 proposes deltas and step-04 only writes after the user confirms. Skipping the proposal step burns the user's ability to course-correct before the policy ships.
- **In autonomous mode, close the loop.** When `{downstream_impact}` is non-empty, auto-trigger `apply-design-policy-change` at step-04 §6. Leaving impacted pages flagged-but-unactioned violates the autonomy contract.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Sequential progression: load current → identify deltas → propose changes → write revision
- The proposal step is the gate — nothing is written until the user confirms (unless in autonomous mode)

### State Variables

- `{policy_path}` - Path to the existing design policy
- `{current_policy}` - Full text of the current policy
- `{current_version}` - Current policy version number
- `{change_axes}` - Which axes are moving: tone | density | component-language | status-system | hard-failures | layout | typography | color (one or more)
- `{change_description}` - The user's actual problem statement, verbatim
- `{proposed_deltas}` - Map of section → before/after text
- `{downstream_impact}` - Which existing pages/features/artifacts may be affected by the change
- `{output_path}` - Where to write the revised policy (same as `{policy_path}`)

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `project_name`, `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `project_knowledge`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- **Never halt or wait for user input.** Make expert-level decisions and proceed.
- **Infer change axes** from the user's problem statement — pick the smallest set of sections that need to change.
- **Skip the proposal confirmation** — write the revision directly and report what changed.
- **Auto-trigger `apply-design-policy-change`** at the end of step-04 when `{downstream_impact}` is non-empty. The autonomy contract requires closing the loop within a single run — leaving impacted pages flagged but unactioned violates "make expert-level decisions and proceed." Pass `{policy_path}`, `{from_version}` = pre-revision version, `{to_version}` = new version, and `{downstream_impact}` to the apply-workflow. See step-04 §6 for the full contract.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/modify-design-policy/steps/step-01-load-current-policy.md` to begin the workflow.
