---
name: 'step-03-generate-brief'
description: 'Generate a bias-free Claude Design brief — three-layer structure: compact main brief, data summary, technical appendix'
---

# Step 3: Generate Design Brief

**Goal:** Write the final brief to disk. The brief gives Claude Design the business problem, domain data, visual direction, and hard constraints — nothing about the current page structure. It is a creative brief, not a reconstruction spec.

**Structure:** The brief uses three layers to reduce cognitive load while preserving reference depth:
1. **Main brief (sections 1–7)** — decision-shaping material: purpose, compact data summary, user context, visual direction, constraints, design ask, deliverables
2. **Appendix A** — full field-level schema tables, API surface, implementation files

The main brief must be self-sufficient for design decisions. The appendix is opt-in reference for precise field types and endpoint details.

---

## RULES

1. **Self-contained.** Claude Design must be able to start from sections 1–7 without clarifying questions or reading the appendix.
2. **No current UI.** No layout descriptions, component names, section headings, tab lists, or grouping structures from the existing page — in any section.
3. **Section 2 = compact domain summary** in prose and bullet form. Describe each entity in 2–3 sentences, list relationships, key dimensions for design decisions, and empty states. Full field-level tables go in Appendix A — NOT in section 2.
4. **Section 4 = visual direction as theme.** Describe the desired aesthetic and constraints, not the current UI structure. Name reference products (Stripe, Ramp, Linear, Mercury, etc.) and state what to borrow from each. Consolidate — don't repeat the same anchors in multiple sub-sections.
5. **Section 5 = one consolidated constraint list.** Merge brand identity hard failures and AI fingerprint rules into a single numbered list. No "Additionally" block that repeats items from the main list.
6. **Section 6 = questions and outcomes.** Frame user problems the design must solve. Never prescribe UI primitives ("must group by X", "must contain a Y picker").
7. **Reconstructability test.** Read the finished brief. If a developer could rebuild the current page from it, it's leaking.
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
{output_path_relative_to_repo_root} = path relative to git repo root
```

### 2. Generate the Brief

Write the file using this template. The section order is intentional — Claude Design should understand the business problem first, then the visual system, then the non-negotiables. Technical reference is last.

---

````markdown
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

> **Repository:** **{github_repo_url}** (branch: `main`). Connect to THIS repository to read referenced files.
>
> **This brief:** `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`

This brief was generated from the codebase after implementation. It intentionally omits the current layout — you have full creative freedom to design from the data, purpose, and constraints below.

**Scope:** {feature_scope — "new" = design from scratch, "redesign" = rethink existing}

---

## 1. Feature Purpose

**What this feature does:** {feature_purpose — the problem it solves, NOT what the page looks like}

**Route:** `{route path}`

**What the user needs to accomplish:**
{user_goals — domain outcomes, NOT UI actions. "Spot invoices near deadline" not "click the overdue tab."}

**Typical data volume:** {counts in domain terms}

---

## 2. Domain Data

Grouping, derivation, and presentation are design decisions — not prescribed here. Full field-level schema is in **Appendix A** for reference; this section covers what matters for design.

### Entities

{For each entity, write 2–3 sentences: what it represents, what its key fields are (in domain language), and how many records typically exist. Do NOT use field tables here.}

**{EntityName}** — {one-line purpose}. {Key fields described in prose: "Carries X, Y, and Z." or "Each record has a date, amounts in native currency plus GBP equivalents, a status, and an optional link to..."} {Typical count.}

{Repeat per entity. Minimal set — only entities this feature touches.}

### Relationships

{plain-English facts about how entities relate — NOT grouping structures}

### Key dimensions for design decisions

{Bullet list of the raw fields/dimensions the designer can use to organise information. Frame as design inputs, not as prescribed groupings.}
- {e.g., "Location (UK | DE) — two warehouses, two currencies, two VAT regimes"}
- {e.g., "Charge date — time-based grouping, trend detection, coverage analysis"}
- {e.g., "Workflow status per record — the design can derive progress views however it sees fit"}
- {e.g., "Dual currency — native amounts plus GBP-converted equivalents for UK reporting. GBP fields are nullable for legacy rows."}

### Empty states to consider

{Compact list of nullable fields that need empty-state treatment, grouped by entity}

---

## 3. Who Uses This

{user_context — role, job-to-be-done, frequency, emotional state. Keep this concise — 4–5 lines max.}

**Design implication:** {one sentence connecting user context to design priority}

---

## 4. Visual Direction

{Use ONE of the following variants based on `{design_system}`:}

**--- VARIANT A: `{design_system}` = "branded" (brand identity / design policy exists) ---**

> This project has an established visual identity defined in `{brand_identity_path}`. Your creative freedom is in information architecture, layout, and interaction design. The visual system is fixed.

### Personality & Influences

{Consolidate the brand identity's personality statement AND external influences into one sub-section. State the tone, then list the reference products and what to borrow from each. Do NOT create a separate "External Influences" sub-section that repeats the same anchors.}

### Visual System

{Consolidate typography, color, status, and layout rules into a dense sub-section. Use bullet groups:}
- **Surfaces:** {palette, accent rules, when color is used}
- **Type:** {body size, font stack, monospace rules, max sizes per component, casing}
- **Status:** {badge component description, shape, the 4 color meanings}
- **Layout:** {table-first, filter placement, badge placement, chrome rules}

{If the brand identity has reference pages, include:}

### Reference Pages

{Internal gold-standard pages with routes and why — from brand identity}

**--- VARIANT B: `{design_system}` = "external" ---**

> This page uses the **{design_system_name}** design system. Apply its tokens, typography, spacing, and component patterns. Do NOT use the CSS tokens in the codebase — those are developer placeholders.

**Structural constraints (still apply):**
- App shell: {fixed shell elements}
- Navigation: {where this page lives}

**--- VARIANT C: `{design_system}` = "existing" (no brand identity, no external system) ---**

This product should feel like a high-trust finance operations tool — not a generic SaaS dashboard.

### Personality & Influences

Match the discipline of Stripe's data tables, the status clarity of Ramp's approval states, the filter density of Linear, and the calm restraint of Mercury. Optimize for dense tables, compact filters, and small pill badges. Use a mostly neutral palette, one accent color, and status color only for small badges.

### Tokens (from `{path}`)

**Colors:** {CSS variables with values}
**Typography:** {font families, key sizes}
**Spacing & Borders:** {spacing scale, border radius, border colors}

### Patterns from Other Pages

{existing_patterns — from OTHER pages in the app, NOT the target feature}

### Reference Pages

{reference_pages — internal pages to reference for visual consistency}

---

## 4a. Page Mode

{Include ONE of the following based on `{page_mode}`:}

**--- If `{page_mode}` = "operational" ---**

**Operational.** The user processes work: {brief description of the dominant tasks}. Optimise for dense scanning, explicit state visibility, and fast narrowing of record sets.

{If the page has a secondary analytical dimension, note it in one sentence: "This page has a secondary analytical dimension (X and Y), but analytics exist to support the operational task — not as a standalone workflow."}

**--- If `{page_mode}` = "analytical" ---**

**Analytical.** The user discovers patterns: {brief description of the dominant tasks}. Help the user understand what changed, why, and where to investigate further.

**Principles:**
- Keep the same corporate visual system: high-trust, restrained, precise, data-first.
- Charts may lead when they help the user see patterns faster, but there must always be a clear path to underlying records.
- Filters remain compact and persistent. Tables are supporting evidence unless row-level processing is the dominant task.

---

## 5. Hard Constraints

{Use ONE of the following variants based on `{design_system}`:}

**--- If `{design_system}` = "branded" ---**

A design containing ANY of these fails review:

{Merge the brand identity's hard failure list AND the standard AI fingerprint rules into ONE numbered list. De-duplicate: if the brand identity already lists "no bento layouts" and the AI fingerprint list also has "bento grid layouts", include it once. The merged list should typically have 12–16 items.}

{After the numbered list, add physical constraints:}

**Responsive:** {breakpoints or "desktop-only"}
**Data density:** {typical row counts, virtualization needs}
**Navigation:** {where the page lives in the app shell}
**Interaction model:** {key workflows — upload, filter, export, bulk actions, etc.}

**Self-test:** If someone would guess AI was involved, the design fails.

**--- If `{design_system}` = "external" ---**

{constraints — responsive, data density, accessibility, performance, navigation position}

**--- If `{design_system}` = "existing" ---**

A design containing ANY of these fails review:

{Single numbered list — merge the generic anti-patterns with AI fingerprint rules. Typically 12–16 items. No separate "Additionally" block.}

**Aesthetic rules:**
- Pure white or cool neutral gray backgrounds
- One neutral sans-serif family
- Monospace for data only (IDs, codes, tabular numbers)
- Color used sparingly and functionally

{Physical constraints — same as branded variant above}

**Self-test:** If someone would guess AI-generated, it fails.

---

## 6. Design Ask

{Write the ask using the mode-specific pattern below, then append 3-5 feature-specific questions.}

**Structure:**

> {Mode-specific framing sentence (see below).}
> {Scope directive (see below).}
>
> Questions your design should answer:
> {3-5 feature-specific questions derived from user goals + data shape}

**Mode-specific framing:**

If `{page_mode}` = **operational:**
> Design this page for a user whose main job is to process work accurately and efficiently.

If `{page_mode}` = **analytical:**
> Design this page for a user whose main job is to understand what changed, why it changed, and where to investigate further.

**Scope directives (append after the framing sentence):**

- **new + branded:** "Section 4 defines this app's visual identity — match it exactly. Information architecture and interaction design are yours."
- **redesign + branded:** "The current implementation was developer-built without a design process. Start fresh from the data model and user context. Your design must be indistinguishable from the reference products in section 4."
- **new + existing:** "Match the visual direction in section 4. Respect the hard constraints in section 5. Everything else is yours."
- **redesign + existing:** "Start fresh from the data model and user context. Match the visual direction and constraints above."
- **new + external:** "Apply **{design_system_name}**."
- **redesign + external:** "Apply **{design_system_name}**. Ignore existing CSS tokens in the repo."

---

**Hard rule: questions must be derived from the data model and user goals only — never from current UI sections, labels, or grouping structure.** If a question names the current grouping logic, the current tabs, the current panels, the current summary blocks, or the current page breakdown, it is leaking. If it names the job to be done, it is safe.

**Page-mode rule for questions:**
- Operational questions should be about processing, review, exception handling, and workflow progress.
- Analytical questions should be about trend detection, comparison, anomaly diagnosis, and drill-to-evidence.
- Questions must not mention current tabs, panels, cards, sections, or grouping structures from the existing implementation.

**Good questions for operational pages:**
- "How does the user quickly find items needing action among a dense set of records?"
- "How does the interface make workflow state and exceptions immediately understandable?"
- "How does the design support both precise row-level review and efficient bulk throughput?"
- "How does filtering help the user narrow the work queue without clutter or loss of context?"
- "How does the page remain calm and trustworthy while supporting operational urgency?"

**Good questions for analytical pages:**
- "How does the page help the user spot trends, changes, or anomalies quickly?"
- "How does the interface support comparison across time periods, segments, categories, or entities?"
- "How does the user move from summary insight to underlying evidence without losing context?"
- "How does filtering define the scope of the analysis without turning the page into a control panel?"
- "How does the page stay aligned with the same corporate visual system while still feeling analytical?"

**Bad questions** name the current UI's structure (disguised layout instructions — do NOT use):
- "How should the per-country view work?" ← names the current grouping
- "How should the quarter tabs behave?" ← names the current tab structure
- "Where should the sidebar grouping be arranged?" ← names the current panel layout
- "How should the bulk action toolbar work?" ← presupposes a toolbar

---

## 7. Deliverable Format

1. **Visual designs** at desktop width (1280px)
2. **Component specs** for new UI patterns
3. **Interaction notes** — hover states, transitions, empty states, loading states
4. **Information architecture rationale** — why you grouped and prioritized this way

---

## Appendix A: Technical Reference

Schema fields, API surface, and implementation files for deep context. Not required for design decisions — consult when you need precise field types or endpoint details.

### {EntityName} — full schema

| Field | Type | Nullable | Notes |
|---|---|---|---|
| ... | ... | ... | {only genuine notes: units, value domains, FK targets} |

{Repeat per entity — same entities as section 2, but with complete field tables.}

### API Surface

{api_surface — endpoints, methods, brief response descriptions}

### Implementation Files

{If `{design_system}` = "external": omit CSS/style files.}

| File | Contents |
|------|----------|
| {3-5 key files} | {type definitions, API handlers, CSS tokens if applicable} |
````

---

### 3. Self-Review

Before writing, verify:

- [ ] **No current UI anywhere.** The brief does not describe what sections, components, tabs, or groupings currently exist on the page. No phrases like "the current page has", "the left panel shows", "the table is currently placed under", "this section is a card grid."
- [ ] **Section 2 is a compact prose summary.** No field tables in the main brief. Entity descriptions are 2–3 sentences each. Full tables are in Appendix A only.
- [ ] **Section 1 goals are outcomes, not UI actions.** No "click X" or "switch the Y tab."
- [ ] **Section 4 is consolidated.** No redundant sub-sections repeating the same visual anchors. Branded variant uses "Personality & Influences" + "Visual System" (+ optional "Reference Pages") — not 7 separate sub-sections.
- [ ] **Section 5 is one list.** Hard failures and AI fingerprint rules are merged into a single numbered list with no duplication. No "Additionally" block.
- [ ] **Section 6 is questions, not primitives.** No "must group by", "must contain", "must have." Questions emerge from user goals + data shape, not from the current UI's solutions.
- [ ] **Reconstructability test.** A developer could NOT rebuild the current page from this brief.
- [ ] **Three-layer structure.** Sections 1–7 are self-sufficient for design decisions. Appendix A contains full schema, API, and file references.
- [ ] **Design system variant is correct and complete:**
  - branded = personality + visual system (consolidated) + reference pages + merged constraint list
  - existing = visual direction + real tokens + merged constraint list
  - external = names the system, no repo tokens
- [ ] **Positive before negative** — visual direction and reference products come BEFORE hard failures and anti-patterns.
- [ ] **Page mode is correct and concise.** Operational or analytical, 2–3 lines max. Secondary dimensions noted in one sentence.
- [ ] **File paths are correct** and relative to repo root.

### 4. Write the Brief

Write the file to `{output_path}`.

### 5. Present to User

Show:
1. Where the file was written
2. A 3-line summary
3. Copy-paste prompt for Claude Design:

> **To hand off to Claude Design:**
>
> "Connect to **{github_repo_url}** and read `{output_path_relative_to_repo_root}` on `main`. This is a design brief for {feature_name}. Design the UI following the brief exactly."
>
> {If external, append: "Apply the {design_system_name} design system — ignore CSS tokens in the repo's style files."}

---

## SUCCESS METRICS

- Brief written to `{output_path}`
- Claude Design can start from sections 1–7 without reading the appendix
- **Zero implementation echoes** — no layout, component, section, or tab references from the current page
- **Section 2** is a compact prose summary with dimensions and empty states — not field tables
- **Section 4** is consolidated: personality + visual system (not 7 sub-sections)
- **Section 5** is a single merged constraint list — no duplicates, no "Additionally" block
- **Section 6** poses open design problems as questions — not UI-primitive instructions
- **Appendix A** contains full schema tables, API surface, and implementation files
- **Reconstructability test passes** — the brief constrains the designer to solving the user's problem, not reproducing this specific UI
- Visual identity is complete for the variant (branded/existing/external)
- Positive anchors precede negative constraints
