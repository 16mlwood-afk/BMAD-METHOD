---
name: 'step-03-generate-brief'
description: 'Generate an unbiased Claude Design brief — presents data and purpose without describing current layout'
---

# Step 3: Generate Design Brief

**Goal:** Produce the final design brief as a markdown file that Claude Design can read directly from the repo. The brief must present raw materials (data, purpose, constraints) without describing the current UI's structure.

---

## RULES

- The brief must be self-contained enough that Claude Design can start working immediately
- Reference file paths (Claude Design has repo access) but inline the critical context
- **NEVER describe the current page layout, component tree, section organization, or visual hierarchy in the brief.** These are implementation choices that bias the designer.
- Present ALL data fields neutrally — do NOT rank them as "prominent" vs "secondary"
- Use the template below EXACTLY — Claude Design will learn to expect this structure
- Write to `{implementation_artifacts}` path from config (typically `_bmad-output/implementation-artifacts/`)
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From steps 01–02:
- `{github_repo_url}`, `{feature_name}`, `{feature_scope}`, `{feature_purpose}`
- `{data_shape}`, `{api_surface}`, `{implementation_files}`, `{user_context}`
- `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, `{constraints}`

---

## EXECUTION SEQUENCE

### 1. Determine Output Path

```
{output_path} = {implementation_artifacts}/design-brief-{feature-slug}-{date}.md
{output_path_relative_to_repo_root} = path relative to git repo root (e.g., _bmad-output/implementation-artifacts/design-brief-{feature-slug}-{date}.md)
```

Compute the relative path by stripping the repo root from the absolute path. This is used in the brief header and handoff instructions so Claude Design can locate the file via GitHub.

### 2. Generate the Brief

Write the file using this template:

---

```markdown
---
type: design-brief
feature: {feature_name}
scope: {feature_scope}
date: {date}
author: {user_name} via design-handoff workflow
status: ready-for-design
---

# Design Brief: {feature_name}

## For Claude Design

> **IMPORTANT — Repository context.** This brief lives in the GitHub repository **{github_repo_url}** (branch: `main`). You must connect to THIS specific repository to read the referenced files. If you are currently working in a different project, switch to this repo first.
>
> **Direct link to this brief:** `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
>
> All file paths below are relative to this repo's root — you can read any of them directly once connected.

This brief was auto-generated from the codebase after implementation. **Important:** The current UI was built by a developer, not a designer. This brief intentionally does NOT describe the current layout or visual structure — you have full creative freedom to design from scratch based on the data, purpose, and constraints below.

**Scope:** {feature_scope — "new" means design from scratch, "redesign" means rethink the existing UI}

---

## 1. Feature Purpose

**What this feature does:** {feature_purpose — what problem it solves, NOT what the page currently looks like}

**Route:** {route path}

**Available user actions:** {list of mutations/actions from api_surface — e.g., "create", "delete", "filter", "export"}

**Typical data volume:** {how many items, how much data — e.g., "usually 10-50 items", "single detail view with nested collections"}

---

## 2. Available Data

The UI has access to this data shape. All fields are listed neutrally — you decide what deserves prominence, grouping, and hierarchy.

\`\`\`typescript
{data_shape — full TypeScript interface(s), NO annotations about importance}
\`\`\`

**Fields requiring design consideration:**
- Nullable fields (need empty/missing state): {list nullable fields}
- Array fields (need collection/list treatment): {list array fields}
- Computed/derived fields: {list if any}

### API Surface
{api_surface — endpoints, methods, brief response shape descriptions}

---

## 3. Who Uses This

{user_context — role, job-to-be-done, frequency, emotional state}

**Design implication:** {One sentence connecting user context to design priority — e.g., "This is a daily-driver tool so density and keyboard shortcuts matter more than first-impression polish."}

---

## 4. Design System Context

{Use ONE of the following two variants based on `{design_system}`:}

**--- VARIANT A: If `{design_system}` = "external" ---**

> **This page should use the {design_system_name} design system.** Do NOT use the CSS tokens currently in the codebase — those are developer placeholders from a different project and are not this product's intended design language. Apply {design_system_name}'s tokens, typography, spacing, component patterns, and visual language to this feature.

**Structural constraints from the codebase (these still apply regardless of design system):**
- App shell structure: {describe the fixed shell elements — e.g., "56px icon rail + 200px nav panel + fluid content area" — because these are architectural, not stylistic}
- Navigation position: {where this page lives in the app shell}

**--- VARIANT B: If `{design_system}` = "existing" ---**

### Tokens (from `{path to tokens file}`)

**Colors:**
{List the key CSS variables with their values}

**Typography:**
{Font families, key sizes}

**Spacing & Borders:**
{Spacing scale, border radius, border colors}

### Existing Patterns in Other Pages

{existing_patterns — describe patterns from OTHER pages in the app, NOT the target feature. These establish the app's visual language — the designer should harmonize with them but is not bound to copy them.}

### Reference Pages

{reference_pages — "Look at /pipeline for the app's visual language" with description of what's good about it. These are for design language consistency, NOT for layout inspiration for this feature.}

{If `{design_system_style}` = "corporate", include this section. Otherwise skip it entirely.}

## 4a. Corporate Design Guardrails

This is a corporate/enterprise application. The design MUST follow these rules — they are hard constraints, not suggestions.

**Aesthetic:**
- Pure white (#FFFFFF) or cool neutral gray backgrounds — never cream, off-white, or warm tints
- One neutral sans-serif family (Inter, SF Pro, Segoe UI) — no personality typography
- Monospace fonts for data only (IDs, codes, tabular numbers) — never in headings or as a decorative voice
- Color used sparingly and functionally — not as personality or branding
- Dark mode: true dark neutrals (#1A1A1A–#2D2D2D) — not navy, not deep blue

**Voice:**
- Functional, instructional labeling: "Search Results," "Distributor Details" — not "01 — FOUNDATIONS"
- No marketing copy, no aspirational headlines, no agency voice
- Every UI element must be self-explanatory: no unexplained badges, no icons without labels, no truncated text

**Anti-patterns (hard failures — do not produce any of these):**
1. Cream or warm-tinted backgrounds
2. Monospace fonts used decoratively (headings, section labels, navigation)
3. Oversized editorial typography or playful numbering ("01 —")
4. Marketing-style hero sections or aspirational copy
5. Truncated text that isn't explicitly handled with a tooltip or expand pattern
6. Numeric badges without explanatory labels
7. "Indie SaaS" or "startup template" aesthetic of any kind

**AI design tool fingerprints (reject these — they signal auto-generated output, not intentional design):**

*Layout:*
- Bento grid layouts (asymmetric mixed-size card grids) — use uniform grids, tables, or lists
- Hero sections on internal pages — start with content, not a tagline
- Dashboard-as-homepage with metric card grids — route to the primary workflow instead
- Massive padding/whitespace — dense is fine for power-user tools; 16px card padding, 24px section gaps

*Visual:*
- Purple/violet primary color (the #1 AI default) — use brand color or conservative blue
- Gradient text, gradient backgrounds, glassmorphism — flat solid colors only
- Oversized border-radius (16px+) — use 4px–8px max; pill shapes only for tags/badges
- Heavy card shadows as decoration — reserve elevation for overlays and modals
- Gradient/colored dividers — use `1px solid var(--border)`
- Colored sidebar icons (different color per nav item) — monochrome icons, color = state only
- Semantic-colored card fills (green card = good, red card = bad) — use a left-border accent or small badge, never fill an entire card background

*Content/UX:*
- Chatty empty states with illustrations ("No items yet! Get started…") — plain text: "No results."
- Icons on every label, heading, and menu item — icons only where they add recognition speed
- Hover scale transforms on cards — hover = background/border change, no movement
- Animated number counters on metrics — render data immediately
- Excessive status colors (8+ badge colors) — use 4 max: green, yellow, red, gray

**Self-test:** If someone would guess the design is AI-generated, it fails. Corporate tools look like they were built by an in-house team — competent, consistent, invisible.

---

## 5. Constraints

{constraints — responsive, data density, accessibility, performance, navigation position}

---

## 6. Design Ask

{Based on feature_scope, write the specific ask:}

**If "new" + existing design system:**
> Design the UI for {feature_name} at route {route}. You have the full data model and user context above. Create the best possible design for this user's workflow — decide what information to foreground, how to group data, what interactions to prioritize, and what layout pattern to use. The design tokens and app patterns above establish the visual language; the constraints are the only hard limits. Everything else is yours to decide.

**If "new" + external design system:**
> Design the UI for {feature_name} at route {route}. You have the full data model and user context above. Apply the {design_system_name} design system — use its tokens, typography, component patterns, and visual language. Create the best possible design for this user's workflow — decide what information to foreground, how to group data, what interactions to prioritize, and what layout pattern to use. The structural constraints in section 4 and the hard constraints in section 5 are the only limits. Everything else is yours to decide.

**If "redesign" + existing design system:**
> Redesign {feature_name} at route {route}. The current implementation was built by a developer and has not been through a design process. Approach this as a fresh design problem: you have the data model and user context above — decide the optimal information architecture, visual hierarchy, and interaction patterns from scratch. Support all data fields in the model (see section 2) but you decide how to present them. Reference the design tokens and app patterns above for visual consistency with the rest of the app.

**If "redesign" + external design system:**
> Redesign {feature_name} at route {route}. The current implementation was built by a developer using placeholder tokens from a different project — it has not been through a design process. Approach this as a fresh design problem: apply the {design_system_name} design system and decide the optimal information architecture, visual hierarchy, and interaction patterns from scratch. Support all data fields in the model (see section 2) but you decide how to present them. Ignore the existing CSS tokens in the codebase — {design_system_name} is the intended design language.

---

## 7. Deliverable Format

Please produce:
1. **Visual designs** for the page at desktop width (1280px)
2. **Component specs** for any new UI patterns not already in the app
3. **Interaction notes** for hover states, transitions, empty states, loading states
4. **Information architecture rationale** — brief explanation of why you grouped and prioritized information the way you did

---

## 8. Implementation Files (Reference Only)

These files contain the current implementation. Browse them for technical context (data types, API contracts) if needed, but do NOT use them as layout or design references — the current structure is a developer implementation, not a design decision.

{If `{design_system}` = "external": Do NOT list CSS/style files here — they contain tokens from a different design system and will confuse the designer. Only list type definitions and API route handlers.}

| File | What it contains |
|------|-----------------|
{Table of 3-5 key files — e.g., type definitions, API route handlers. If design_system = "existing", include CSS tokens. If "external", OMIT CSS/style files.}
```

---

### 3. Self-Review

Before writing the file, verify:

- [ ] Data shape includes ALL fields the UI could render (check the TypeScript interface)
- [ ] **No field importance ranking** — fields are presented neutrally without "primary" or "secondary" labels
- [ ] **No current layout description** — the brief does not describe what sections, components, or groupings currently exist on the page
- [ ] **Design system check:** If `{design_system}` = "external": section 4 uses Variant A (no inline tokens, names the external system), implementation files in section 8 exclude CSS/style files. If "existing": section 4 uses Variant B with real token values from the codebase.
- [ ] Reference pages are real routes that exist in the app (and are NOT the target feature's page) — or N/A if external design system
- [ ] The "Design Ask" explicitly grants creative freedom over information architecture
- [ ] File paths are correct and relative to repo root
- [ ] Constraints include data density estimate (how many items in a typical list?)

### 4. Write the Brief

Write the file to `{output_path}`.

### 5. Present to User

Show the user:
1. Where the file was written
2. A 3-line summary of what's in the brief
3. The copy-paste prompt for Claude Design (including the full GitHub URL so Claude Design connects to the right repo):

> **To hand off to Claude Design:**
> Copy-paste this prompt into Claude Design:
>
> **If `{design_system}` = "existing":**
> "Connect to the GitHub repository **{github_repo_url}** and read the file `{output_path_relative_to_repo_root}` on the `main` branch. This is a design brief for {feature_name}. Design the UI following the brief exactly."
>
> **If `{design_system}` = "external":**
> "Connect to the GitHub repository **{github_repo_url}** and read the file `{output_path_relative_to_repo_root}` on the `main` branch. This is a design brief for {feature_name}. Apply the {design_system_name} design system you created — use its tokens, typography, and component patterns. Ignore any CSS tokens in the repo's style files (they are developer placeholders from another project). Design the UI following the brief."
>
> **Why the full repo URL matters:** Claude Design may have a different project open. Without the explicit repo URL, it will look for the file in whatever project is currently active — and fail.

---

## SUCCESS METRICS

- Brief is written to `{output_path}`
- Claude Design can start working without asking clarifying questions about data shape or constraints
- **Brief does NOT describe the current page structure** — no component names, section headings, or layout descriptions from the existing implementation
- **Data fields are presented neutrally** — no importance ranking that would bias the designer's hierarchy choices
- Brief references file paths instead of inlining entire files
- **If existing design system:** tokens are real values extracted from the codebase; existing patterns are described from OTHER pages
- **If external design system:** NO inline tokens from the codebase; brief explicitly names the external system and tells the designer to apply it; CSS/style files are excluded from implementation files table
