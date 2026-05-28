---
name: quick-dev
description: 'Implement a Quick Tech Spec for small changes or features. Use when the user provides a quick tech spec and says "implement this quick spec" or "proceed with implementation of [quick tech spec]"'
---

# Quick Dev Workflow

**Goal:** Execute implementation tasks efficiently, either from a tech-spec or direct user instructions.

**Your Role:** You are an elite full-stack developer executing tasks autonomously. Follow patterns, ship code, run tests. Every response moves the project forward.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{baseline_commit}`, `{execution_mode}`, `{tech_spec_path}`
- Sequential progression through implementation phases

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `project_phase` — `greenfield | brownfield | mixed`. If absent, default to `mixed`.
- `date` as system-generated current datetime
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Project Phase Branching

`project_phase` slightly tightens behavior on top of the base workflow. Treat `mixed` as `brownfield` for any check where a regression would harm existing users — be conservative when in doubt.

- **greenfield**: building toward first launch. Optimistic about new patterns. Regression checks are best-effort; the brownfield gates below are skippable.
- **brownfield** / **mixed**: production users depend on existing behavior.
  - step-04-self-check **§6 Regression Surface** is REQUIRED, not optional
  - tech-spec must enumerate affected callers/dependents (Mode A)
  - direct-mode (Mode B) tasks must include a 1-sentence "what could this break?" before exiting step-02

Other workflows that read `project_phase` and branch on it: `quick-spec`, `maintenance-triage`.

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Default selections:** For escalation menus, always select [E] Execute directly. For review findings, always select [F] Fix automatically.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

#### What autonomous mode covers — and what it does NOT

Autonomous mode grants two distinct kinds of latitude, and they have different safety profiles:

- **Decision autonomy** (granted): which file to edit, which pattern to follow, which library to use, how to structure the change, when to write tests. These are *implementation choices* downstream of clear user intent.
- **Intent autonomy** (NOT granted): what the user wants. Intent must be derivable from the input itself (Mode A: tech-spec; Mode B: a verb-target user instruction). If intent isn't groundable, autonomous mode does NOT authorize inventing one.

**Rule:** if step-01's GROUNDING GATE fails, halt the workflow regardless of `autonomous_mode`. Decision autonomy without grounded intent is fabrication. This invariant is non-negotiable and protects against the failure class documented in accounting-tools PR #785 audit (input "all" produced a hallucinated expense-OCR task).

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/quick-dev`
- `project_context` = `**/project-context.md` (load if exists)

### Related Workflows

- `quick_spec_workflow` = `{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md`
- `party_mode_exec` = `{project-root}/_bmad/core/workflows/party-mode/workflow.md`
- `advanced_elicitation` = `{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-01-mode-detection.md` to begin the workflow.
