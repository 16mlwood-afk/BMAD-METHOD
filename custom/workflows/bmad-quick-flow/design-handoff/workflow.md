---
name: design-handoff
description: 'Generate an unbiased Claude Design brief from a completed implementation. Gathers data model, user context, design tokens, and constraints — deliberately excludes current layout and component structure so the designer starts from a blank canvas. Use after building a feature when you want Claude Design to design or redesign the UI.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_agent_workflow: '{project-root}/_bmad/bmm/workflows/bmad-quick-flow/design-agent/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/bmad-quick-flow/quick-dev/workflow.md'
---

# Design Handoff Workflow

**Goal:** After an implementation is complete (or partially complete), produce a structured design brief that Claude Design can consume directly from the repo. The brief gives Claude Design everything it needs to design (or redesign) the UI without asking clarifying questions about architecture, data shape, or constraints.

**Your Role:** You are a bridge between engineering and design. You understand both the technical implementation and what a designer needs to produce great work. You extract the right context from code — not too much (overwhelming), not too little (ambiguous) — and structure it for a design tool that has repo access.

**Key Insight:** Claude Design can read files from the repo (GitHub is linked). The brief should reference file paths for deep context rather than inlining everything. But it MUST inline enough for Claude Design to start working immediately — don't require it to read 20 files before understanding the ask.

**Anti-Bias Principle — CRITICAL:** The current UI was built by a developer, not a designer. Its layout, information grouping, visual hierarchy, and component structure are *implementation choices*, not design requirements. The brief must **never** describe what the current page looks like or how information is currently organized. Instead, give the designer the raw materials — data model, user purpose, constraints, design tokens — and let them create their own vision. Feeding the designer "this page contains sections X, Y, Z" paves the road and kills creative exploration.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables (see below)
- Sequential progression: gather → audit → generate

### State Variables

- `{feature_name}` - Name of the feature being handed off
- `{feature_scope}` - "new" (design from scratch) or "redesign" (improve existing)
- `{feature_purpose}` - What the feature does and why it exists — NOT how it is currently laid out
- `{data_shape}` - TypeScript interfaces or Python models that define what data is available to the UI — presented neutrally without ranking field importance
- `{api_surface}` - Endpoints and response shapes the frontend can call
- `{implementation_files}` - File paths for implementation reference only (designer may browse for technical context, not for layout inspiration)
- `{design_system}` - "existing" (inline tokens from the codebase) or "external" (design system provided separately — e.g., created in Claude Design). When "external", section 4 of the brief is replaced with a note telling the designer to apply their own system.
- `{design_system_name}` - If external: the name of the design system (e.g., "Meridian"). Empty if "existing".
- `{design_system_style}` - "corporate" or "default". When "corporate", the brief includes anti-patterns and guidelines from the corporate design system reference doc. Detect from user input or ask.
- `{design_tokens}` - Existing CSS variables, font stacks, color palette, spacing scale (only populated when design_system = "existing")
- `{existing_patterns}` - Component patterns already in the app (card styles, table patterns, form patterns)
- `{constraints}` - Hard constraints the designer must respect (responsive breakpoints, data density, accessibility)
- `{user_context}` - Who uses this feature, what they're trying to accomplish, frequency of use
- `{reference_pages}` - Existing pages in the app that have good design to reference
- `{github_repo_url}` - GitHub HTTPS URL for the repository (no trailing `.git`)
- `{output_path}` - Absolute path where the brief is written on disk
- `{output_path_relative_to_repo_root}` - Brief path relative to the repo root (for GitHub URLs and Claude Design references)

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- **Never halt or wait for user input.** Make expert-level decisions and proceed.
- **Infer feature scope from git history** — if the feature was just committed, it's "new" unless the user says otherwise.
- **Auto-detect design tokens** from CSS/style files without asking which file.

### Input

The user may provide:

- **A feature name or description** — "the outreach queue I just built"
- **A commit hash or branch** — the workflow will diff to understand what changed
- **A route** — `/outreach`, `/pipeline` — the page to design
- **A design system directive** — "use Meridian", "use the corporate design system", "external design system"
- **Nothing** — the workflow will look at the most recent commit(s) on the current branch

If the input is ambiguous, ask ONE clarifying question maximum, then proceed.

### Design System Detection

Determine `{design_system}`, `{design_system_name}`, and `{design_system_style}`:

- If the user mentions an external design system by name → `{design_system}` = "external", `{design_system_name}` = that name
- If NOT in autonomous mode → ask: **"Should this design use the existing tokens from the codebase, or an external design system (e.g., one created in Claude Design)?"**
- If in autonomous mode and no explicit directive → default to "existing"

Determine `{design_system_style}`:
- If user says "corporate," "enterprise," "B2B," or the project is a business tool → `{design_system_style}` = "corporate"
- Otherwise → `{design_system_style}` = "default"

When `{design_system_style}` = "corporate", the brief includes anti-pattern guardrails from the corporate design guidelines reference doc (`_bmad-output/planning-artifacts/corporate-design-system-guidelines.md` if it exists in the project, otherwise inline the key rules). These prevent Claude Design from producing "indie SaaS" aesthetics instead of corporate.

**Why this matters:** The codebase tokens may be developer placeholders copied from another project — NOT an intentional design system. Inlining them into the brief anchors the designer to dev choices, which is just as biased as describing the current layout. When a proper design system exists externally, the brief should reference it by name and tell the designer to apply it — not compete with inline tokens.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/design-handoff/steps/step-01-gather.md` to begin the workflow.
