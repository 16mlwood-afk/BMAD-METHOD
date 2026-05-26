---
name: design-handoff
description: 'Generate an unbiased Claude Design brief from a completed implementation. Gathers data model, user context, design tokens, and constraints — deliberately excludes current layout and component structure so the designer starts from a blank canvas. Use after building a feature when you want Claude Design to design or redesign the UI.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_agent_workflow: '{project-root}/_bmad/bmm/workflows/design/design-agent/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
---

# Design Handoff Workflow

**Goal:** After an implementation is complete (or partially complete), produce a structured design brief that Claude Design can consume directly from the repo. The brief gives Claude Design everything it needs to design (or redesign) the UI without asking clarifying questions about architecture, data shape, or constraints.

**Your Role:** You are a bridge between engineering and design. You understand both the technical implementation and what a designer needs to produce great work. You extract the right context from code — not too much (overwhelming), not too little (ambiguous) — and structure it for a design tool that has repo access.

**Key Insight:** Claude Design can read files from the repo (GitHub is linked). The brief should reference file paths for deep context rather than inlining everything. But it MUST inline enough for Claude Design to start working immediately — don't require it to read 20 files before understanding the ask.

**Anti-Bias Principle — CRITICAL:** The current UI was built by a developer, not a designer. Its layout, information grouping, visual hierarchy, and component structure are *implementation choices*, not design requirements. The brief must **never** describe what the current page looks like or how information is currently organized. Instead, give the designer the raw materials — data model, user purpose, constraints, visual direction — and let them create their own vision. The brief describes the desired aesthetic (theme, reference products, tokens), not the current structure.

**Brief Section Order:** The template follows this sequence for optimal handoff to Claude Design: Feature purpose → Domain data → User context → Visual direction → Hard constraints → Design ask. This order lets the designer understand the business problem before encountering visual constraints.

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
- `{data_shape}` - Domain entities and their primitive fields, in domain language — NOT the page server's return type. Captured by walking up from DB schema, not down from the UI response. See step-01 for procedural capture rules.
- `{api_surface}` - Endpoints and response shapes the frontend can call
- `{implementation_files}` - File paths for implementation reference only (designer may browse for technical context, not for layout inspiration)
- `{brand_identity_path}` - Path to the project's brand identity document (if it exists)
- `{brand_identity}` - Contents of the brand identity document — provides positive visual anchors, design tokens, component patterns, reference pages, and hard failures. When present, this is the PRIMARY source for design system context — it supersedes token extraction and generic guardrails.
- `{design_system}` - "branded" (brand identity exists) or "existing" (extract tokens from code) or "external" (external design system — e.g., created in Claude Design). Controls which variant of section 4 (Visual Direction) and section 5 (Hard Constraints) the brief uses.
- `{design_system_name}` - If external: the name of the design system (e.g., "Meridian"). Empty otherwise.
- `{design_tokens}` - Design tokens — from brand identity (preferred) or extracted from codebase
- `{existing_patterns}` - Component patterns — from brand identity (preferred) or observed in other pages
- `{page_mode}` - "operational" (process rows, review items, take actions) or "analytical" (understand patterns, trends, anomalies across a dataset). Determines whether the brief includes the analytics view addendum.
- `{constraints}` - Hard constraints the designer must respect (responsive breakpoints, data density, accessibility)
- `{user_context}` - Who uses this feature, what they're trying to accomplish, frequency of use
- `{reference_pages}` - Existing pages in the app that have good design to reference — from brand identity (preferred)
- `{hard_failures}` - Non-negotiable anti-patterns from brand identity — designs containing any of these fail review
- `{github_repo_url}` - GitHub HTTPS URL for the repository (no trailing `.git`)
- `{output_path}` - Absolute path where the brief is written on disk
- `{output_path_relative_to_repo_root}` - Brief path relative to the repo root (for GitHub URLs and Claude Design references)
- `{handoff_mode}` - `"fresh-design"` (default) or `"refine-screen"`. Refine-screen mode is triggered by the design-pm prompt-expansion or by the user passing `--refine-screen` / `--refine`. In refine-screen mode the workflow consumes a `screen-review` artifact (auto-running `design-review --artifact` first if none exists) and produces a tightly-scoped refinement brief instead of an open creative brief.
- `{review_artifact_path}` - Absolute path to the consumed `screen-review-*.md` artifact (only set in refine-screen mode)
- `{refine_focus}` - Violations parsed from the artifact (V1, V2, … — used to bound the brief's Design Ask in refine-screen mode; the brief may consume all or just the top N)
- `{required_variants}` - Edge states parsed from the artifact (required design variants in refine-screen mode)
- `{peer_steals}` - Peer-pattern transplants parsed from the artifact (used as visual references in refine-screen mode)
- `{already_fine}` - Keepers parsed from the artifact (things refine-screen must NOT break — folded into hard constraints. State-variable name kept for compatibility with step-03 templates.)

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

### Brand Identity & Design System Detection

**Step 1 — Check for a project design policy (highest priority):**

Projects may declare visual direction, layout principles, status systems, and hard failures in one of two locations. Check both, in order:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

If `{project-root}/docs/design-policy.md` exists, prefer it. Otherwise fall back to `{planning_artifacts}/brand-identity.md`. Both files play the same role — they describe the project's design system. `design-policy.md` is the canonical name; `brand-identity.md` is the legacy slot.

If either file exists:
- Read it and store as `{brand_identity}`
- Set `{brand_identity_path}` to the file path
- Set `{design_system}` = "branded"
- Extract `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, and `{hard_failures}` directly from the document
- **Skip design system questions entirely** — the project policy IS the design system

**Step 2 — If no brand identity, check for external directive:**

- If the user mentions an external design system by name → `{design_system}` = "external", `{design_system_name}` = that name
- If NOT in autonomous mode → ask: **"Should this design use the existing tokens from the codebase, or an external design system?"**
- If in autonomous mode → default to "existing"

**Step 3 — Fallback (no brand identity, no external directive):**

Set `{design_system}` = "existing" — tokens will be extracted from the codebase in step 02.

**Why brand identity first:** A brand identity document captures the project's ACTUAL visual language — not raw CSS tokens, not generic anti-patterns, but the specific decisions that make this app look like this app. When one exists, it provides both positive anchors (what we look like) and negative constraints (what we never do), which are far more effective than generic guardrails. Without it, Claude Design fills the vacuum with its strongest priors (generic SaaS templates).

### Refine-Screen Detection & Artifact Loading

The workflow handles two modes:

- **`fresh-design`** (default) — new page, new feature, structural redesign. The brief is open and creative. The rest of this section does not apply.
- **`refine-screen`** — iteration on an existing baseline screen. The brief is tightly scoped to the diagnostic from a `design-review` artifact. NO USER COMPLAINTS ARE COLLECTED — the diagnostic is automated.

**Detect mode** in this order:

1. If the user's invocation or prompt-expansion contains the literal `--refine-screen`, `--refine`, or starts with "refine"/"iterate"/"tighten"/"polish"/"second pass on" → `{handoff_mode}` = `"refine-screen"`.
2. If `design-pm` set `{handoff_mode}` in state when routing → honor it.
3. Otherwise → `{handoff_mode}` = `"fresh-design"`.

**If `{handoff_mode}` = `"refine-screen"`, run artifact loading BEFORE step-01:**

1. **Resolve target slug.** From the user's input identify the target route or feature slug. Same kebab-case rule as `design-review`: pathname → strip slashes → replace `/` with `-` → lowercase. Examples: `/reclaim/avask` → `reclaim-avask`; "iterate AVASK" + the AVASK page in context → `reclaim-avask`.

2. **Search for an existing artifact:**

   ```bash
   ls -t {implementation_artifacts}/screen-review-{target_slug}-*.md 2>/dev/null | head -1
   ```

   Pick the most recent. Also accept matches where the slug is a prefix (e.g., `reclaim-avask-v2-...md`).

3. **Branch on result:**

   - **Artifact found AND less than 24 hours old:** Load it. Set `{review_artifact_path}` to its absolute path. Parse the YAML frontmatter into state, then parse the body's Violations → `{refine_focus}` (preserve V-IDs, severities, and all per-violation fields), Edge States → `{required_variants}`, Peer Steals → `{peer_steals}`, Keepers → `{already_fine}`. Proceed to step-01.

   - **Artifact found but older than 24 hours:** The screen may have changed. Surface to the user: "Found a screen-review artifact from {age}. Use it as-is, or re-run design-review --artifact?" In autonomous mode, prefer fresh — re-run design-review.

   - **No artifact found AND `autonomous_mode` = true:** Auto-invoke `design-review` with `{output_mode}` = `"artifact"` and the same `{target_url}` / target context. Load the resulting artifact and proceed.

   - **No artifact found AND `autonomous_mode` = false:** Stop. Tell the user: "Refine-screen mode requires a screen-review artifact. Run `/bmad:bmm:workflows:design-review --artifact` on the target page first, then retry this workflow." Do NOT fall back to asking the user for complaints — the whole point of refine-screen mode is that the diagnostic is automated.

4. **Skip the "ask user what's wrong" prompt in step-01.** The artifact replaces it. The user-context question in step-01 still applies (who uses this, how often) since the artifact doesn't cover that.

5. **In step-03, the Design Ask section is rewritten** to the refine-screen variant — see step-03 for the bounded refinement template.

**Refine-screen rule:** The brief produced in this mode must be BOUNDED. It addresses the artifact's top 3 violations (by severity order) and requires variants for the artifact's edge states. It does NOT redesign the IA, does NOT introduce new components unless required to land one of those top 3, and does NOT propose a "get radical" alternative. Open creative freedom belongs in `fresh-design`. Lower-severity violations (V4+) remain in the artifact for visibility but are not in-scope for the brief unless the user explicitly asks.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01-gather.md` to begin the workflow.
