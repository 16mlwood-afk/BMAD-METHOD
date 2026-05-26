---
name: create-design-policy
description: 'Create a project visual policy when none exists or the user is unsure about visual direction. Use when the user says "create a design policy" or "I need a design policy" or "make it more corporate" or "clean this up"'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_tuning_workflow: '{project-root}/_bmad/bmm/workflows/design/design-tuning/workflow.md'
design_standards: '{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md'
brand_identity_template: '{project-root}/_bmad/bmm/workflows/design/brand-identity-template.md'
---

# Create Design Policy Workflow

**Goal:** Create a project-level `design-policy.md` that codifies the visual identity and design language for a project. This is the "visual constitution" — a stable document that downstream workflows (`design-handoff`, `design-tuning`, `design-implement`) consume to stay consistent.

**Your Role:** You are a design strategist helping a product owner articulate their visual intent. You don't impose a style — you discover what the product should feel like through structured questions and, when the owner is unsure, a brainstorming mode that presents plausible directions with tradeoffs.

**Key Insight:** Most Brownfield projects have an implicit visual language (the UI already looks like *something*) but no explicit policy. The workflow extracts the implicit, makes it explicit, and fills gaps where the implicit is inconsistent or absent.

**Relationship to brand-identity.md:** The design policy is the strategic "what we want to be" document. The brand identity is the tactical "what we actually are" document (extracted tokens, hex values, Tailwind classes). A project may have one or both. When both exist, the design policy is the north star that guides brand identity updates. Downstream workflows check for brand identity first (concrete), then design policy (directional), then fall back to generic design standards.

**Project-agnostic:** This workflow contains no hardcoded visual preferences. Every aesthetic decision comes from the user or the brainstorming process.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables (see below)
- Sequential progression: check existing → gather intent → (optional) brainstorm → write policy
- The brainstorming step is entered only when the user expresses uncertainty or requests it

### State Variables

- `{has_existing_policy}` - Whether a design policy already exists ("yes" or "no")
- `{existing_policy_path}` - Path to existing design policy (if found)
- `{has_brand_identity}` - Whether a brand identity document exists ("yes" or "no")
- `{brand_identity_path}` - Path to existing brand identity (if found)
- `{product_type}` - What kind of product this is (e.g., "B2B operations tool", "consumer analytics dashboard")
- `{user_role}` - Who the primary users are and what they do
- `{tone}` - Desired emotional register (e.g., "dense, precise, restrained")
- `{reference_products}` - External products whose visual approach to borrow from
- `{anti_references}` - Products or styles to explicitly avoid
- `{operational_bias}` - "operational" (process rows, take actions) or "analytical" (understand patterns, compare data) or "hybrid"
- `{visual_direction}` - The chosen direction (from brainstorming or direct input)
- `{brainstorm_needed}` - Whether to enter brainstorming mode ("yes" or "no")
- `{output_path}` - Where to write the design policy document

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
- **Auto-detect product type and user role** from existing code, docs, and project structure.
- **If visual direction is ambiguous, run brainstorming internally** — pick the strongest direction based on product type and user context, document the reasoning.

### Output Path

- `{output_path}` = `{project_knowledge}/design-policy.md`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/create-design-policy/steps/step-01-check-existing.md` to begin the workflow.
