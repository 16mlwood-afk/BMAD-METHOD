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
- `{design_system}`, `{brand_identity}`, `{brand_identity_path}`
- `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, `{hard_failures}`, `{constraints}`

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

## 4. Visual Identity & Design Constraints

{Use ONE of the following THREE variants based on `{design_system}`:}

**--- VARIANT A: If `{design_system}` = "branded" (brand identity document exists) ---**

> **CRITICAL — This project has an established visual identity.** The sections below define what this app looks and feels like. These are not suggestions — they are the visual language you must work within. Your creative freedom is in information architecture, layout, and interaction design. The visual system (colors, typography, component patterns, spacing) is fixed.

### Visual Personality

{Copy section 1 from the brand identity document verbatim — the personality statement, register, density, and "what it's NOT"}

### Typography

{Copy section 2 from the brand identity — font families, type scale table, typography rules}

### Color System

{Copy section 3 from the brand identity — core palette table, semantic colors table, badge pattern, domain colors if relevant to this feature}

### Component Patterns

{Copy section 4 from the brand identity — how cards, tables, badges, buttons, status indicators, and navigation actually look in this app. Include exact Tailwind classes.}

### Spacing & Layout

{Copy section 5 from the brand identity — container, padding, gaps, border radius}

### Reference Pages

{Copy section 6 from the brand identity — internal pages that represent the gold standard, with routes and why they're good}

### External Influences

{Copy section 7 from the brand identity — named products and what to borrow/avoid from each}

### Hard Failures — Non-Negotiable

A design that includes ANY of these fails review. These are specific to this project:

{Copy section 8 from the brand identity — the numbered hard failure list}

### AI Fingerprint Sensitivity

These are patterns this project is specifically sensitive to:

{Copy section 9 from the brand identity — the sensitivity table}

**Additionally, avoid ALL standard AI design tool fingerprints:**
- Bento grid layouts — use uniform grids, tables, or lists
- Hero sections on internal pages — content starts immediately
- Dashboard metric card grids as page openers
- Purple/violet as primary accent (unless the brand identity assigns it to a specific domain concept)
- Gradient text, gradient backgrounds, glassmorphism — flat solid colors only
- Oversized border-radius (>10px on containers)
- Heavy card shadows — `shadow-sm` maximum
- Animated number counters — render data immediately
- Chatty empty states with illustrations — plain text only
- Icons on every label and heading — icons only where they add recognition speed

**Self-test:** Show this design to someone who doesn't know AI was involved. If they would suspect it, the design fails.

**--- VARIANT B: If `{design_system}` = "external" ---**

> **This page should use the {design_system_name} design system.** Do NOT use the CSS tokens currently in the codebase — those are developer placeholders and are not this product's intended design language. Apply {design_system_name}'s tokens, typography, spacing, component patterns, and visual language.

**Structural constraints from the codebase (still apply regardless of design system):**
- App shell structure: {describe the fixed shell elements}
- Navigation position: {where this page lives in the app shell}

**--- VARIANT C: If `{design_system}` = "existing" (no brand identity, no external system) ---**

### Tokens (from `{path to tokens file}`)

**Colors:**
{List the key CSS variables with their values}

**Typography:**
{Font families, key sizes}

**Spacing & Borders:**
{Spacing scale, border radius, border colors}

### Existing Patterns in Other Pages

{existing_patterns — patterns from OTHER pages in the app, NOT the target feature}

### Reference Pages

{reference_pages — pages to look at for visual language consistency}

### Design Guardrails

This is a professional tool. The design MUST follow these rules:

**Aesthetic:**
- Pure white or cool neutral gray backgrounds — never cream, off-white, or warm tints
- One neutral sans-serif family — no personality typography
- Monospace fonts for data only (IDs, codes, tabular numbers) — never decorative
- Color used sparingly and functionally

**Anti-patterns (hard failures):**
1. Bento grid layouts — use uniform grids, tables, or lists
2. Hero sections on internal pages — content starts immediately
3. Dashboard metric card grids as page openers
4. Purple/violet as primary accent
5. Gradient text, gradient backgrounds, glassmorphism
6. Oversized border-radius (16px+)
7. Heavy card shadows
8. Colored card fills for status (green card = good, red card = bad) — use badges or left-border accents
9. Chatty empty states with illustrations
10. Marketing copy or enthusiastic language
11. Animated number counters
12. More than 4 distinct badge/status colors

**Self-test:** If someone would guess the design is AI-generated, it fails.

---

## 5. Constraints

{constraints — responsive, data density, accessibility, performance, navigation position}

---

## 6. Design Ask

{Based on feature_scope and design_system, write the specific ask:}

**If "new" + branded:**
> Design the UI for {feature_name} at route {route}. You have the full data model and user context above. Create the best possible design for this user's workflow — decide what information to foreground, how to group data, what interactions to prioritize, and what layout pattern to use. Section 4 defines this app's visual identity — use its exact typography, colors, component patterns, and spacing. The identity and constraints are fixed; information architecture and interaction design are yours.

**If "redesign" + branded:**
> Redesign {feature_name} at route {route}. The current implementation was built by a developer and has not been through a design process. Approach this as a fresh design problem: decide the optimal information architecture, visual hierarchy, and interaction patterns from scratch. Support all data fields in the model (see section 2) but you decide how to present them. Section 4 defines this app's visual identity — your design must be indistinguishable from the reference pages listed there. Match their register, density, and component language exactly.

**If "new" + existing:**
> Design the UI for {feature_name} at route {route}. You have the full data model and user context above. Create the best possible design for this user's workflow — decide what information to foreground, how to group data, what interactions to prioritize, and what layout pattern to use. The design tokens and app patterns above establish the visual language; the constraints are the only hard limits. Everything else is yours to decide.

**If "redesign" + existing:**
> Redesign {feature_name} at route {route}. The current implementation was built by a developer and has not been through a design process. Approach this as a fresh design problem: you have the data model and user context above — decide the optimal information architecture, visual hierarchy, and interaction patterns from scratch. Support all data fields in the model (see section 2) but you decide how to present them. Reference the design tokens and app patterns above for visual consistency with the rest of the app.

**If "new" + external:**
> Design the UI for {feature_name} at route {route}. Apply the {design_system_name} design system — use its tokens, typography, component patterns, and visual language. Create the best possible design for this user's workflow. The structural constraints in section 4 and the hard constraints in section 5 are the only limits. Everything else is yours to decide.

**If "redesign" + external:**
> Redesign {feature_name} at route {route}. Apply the {design_system_name} design system and decide the optimal information architecture and interaction patterns from scratch. Support all data fields in the model (see section 2) but you decide how to present them. Ignore the existing CSS tokens in the codebase — {design_system_name} is the intended design language.

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
- [ ] **Design system check:**
  - If `{design_system}` = "branded": section 4 uses Variant A with FULL brand identity content (personality, typography with exact scale, colors with exact values, component patterns with Tailwind classes, hard failures list, AI sensitivity table). The brand identity content must be comprehensive — not summarized or abbreviated.
  - If `{design_system}` = "external": section 4 uses Variant B (no inline tokens, names the external system)
  - If `{design_system}` = "existing": section 4 uses Variant C with real token values from the codebase
- [ ] **Positive before negative** — in Variant A, the visual personality and component patterns (positive anchors) come BEFORE the hard failures and anti-patterns (negative constraints). This order is critical — Claude Design's priors are strong, and positive references override them more effectively than prohibitions.
- [ ] Reference pages are real routes that exist in the app (and are NOT the target feature's page)
- [ ] The "Design Ask" explicitly grants creative freedom over information architecture while requiring adherence to the visual identity
- [ ] **Hard failures list is present** — if brand identity exists, its hard failures are included verbatim
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
- Claude Design can start working without asking clarifying questions about data shape, constraints, or visual direction
- **Brief does NOT describe the current page structure** — no component names, section headings, or layout descriptions from the existing implementation
- **Data fields are presented neutrally** — no importance ranking that would bias the designer's hierarchy choices
- Brief references file paths instead of inlining entire files
- **If branded:** section 4 contains the FULL brand identity content — personality, typography with exact scale, colors with values, component patterns with classes, reference pages, hard failures, and AI sensitivity. The designer has everything needed to produce work indistinguishable from the reference pages.
- **If existing:** tokens are real values extracted from the codebase; existing patterns are described from OTHER pages; generic anti-pattern list is included
- **If external:** NO inline tokens from the codebase; brief names the external system; CSS/style files excluded from implementation files table
- **Positive anchors precede negative constraints** — the brief establishes what good looks like BEFORE listing what to avoid
