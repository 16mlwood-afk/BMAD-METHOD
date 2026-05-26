---
name: 'step-03-generate-brief'
description: 'Generate a bias-free Claude Design brief — domain data in entity-table form, visual direction as theme not layout, design ask as open questions'
---

# Step 3: Generate Design Brief

**Goal:** Write the final brief to disk. The brief gives Claude Design the business problem, domain data, visual direction, and hard constraints — nothing about the current page structure. It is a creative brief, not a reconstruction spec.

---

## RULES

1. **Self-contained.** Claude Design must be able to start without clarifying questions.
2. **No current UI.** No layout descriptions, component names, section headings, tab lists, or grouping structures from the existing page — in any section.
3. **Section 2 = domain-entity tables** walked up from the DB schema. Not a TypeScript interface. Not the page server's return type. No derived fields, rendering hints, grouped collections, or UI-control enums.
4. **Section 4 = visual direction as theme.** Describe the desired aesthetic and constraints, not the current UI structure. Reference products and visual anchors should come from the project's design policy (variant A) or, if absent, be omitted in favor of principles (variant C). Do not invent reference products.
5. **Section 6 = questions and outcomes.** Frame user problems the design must solve. Never prescribe UI primitives ("must group by X", "must contain a Y picker").
6. **Reconstructability test.** Read the finished brief. If a developer could rebuild the current page from it, it's leaking.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From steps 01–02:
- `{github_repo_url}`, `{feature_name}`, `{feature_scope}`, `{feature_purpose}`
- `{data_shape}`, `{api_surface}`, `{implementation_files}`, `{user_context}`
- `{design_system}`, `{brand_identity}`, `{brand_identity_path}`
- `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, `{hard_failures}`, `{constraints}`
- `{page_mode}`, `{has_analytics_band}`
- `{handoff_mode}` — `"fresh-design"` or `"refine-screen"`
- If refine-screen: `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}`

---

## EXECUTION SEQUENCE

### 1. Determine Output Path

```
{output_path} = {implementation_artifacts}/design-brief-{feature-slug}-{date}.md
{output_path_relative_to_repo_root} = path relative to git repo root
```

If `{handoff_mode}` = `"refine-screen"`, use the slug `refine-{feature-slug}` instead of `{feature-slug}` so the refinement brief is visually distinct from any fresh-design brief on the same feature:

```
{output_path} = {implementation_artifacts}/design-brief-refine-{feature-slug}-{date}.md
```

### 2. Generate the Brief

Write the file using this template. The section order is intentional — Claude Design should understand the business problem first, then the visual system, then the non-negotiables.

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

Fields are in domain language. Grouping, derivation, and presentation are design decisions — not prescribed here.

### {EntityName}
{one-line purpose}

| Field | Type | Nullable | Notes |
|---|---|---|---|
| ... | ... | ... | {only genuine notes: units, value domains, FK targets} |

{Repeat per entity. Minimal set — only entities this feature touches.}

**Volumes:** {real-world counts in domain terms}

**Relationships:** {plain-English facts about how entities relate — NOT grouping structures}

**Derivation inputs:** {raw fields the designer can derive from — NOT pre-computed outputs}
- {e.g., "deadline date per country — the design can derive urgency however it sees fit"}
- {e.g., "row-level status enum — the design can derive progress rollups however it sees fit"}
- {e.g., "row-level net + vat amounts in a currency — the design can derive totals however it sees fit"}

**Nullable fields needing empty-state treatment:** {list}

### API Surface

{api_surface — endpoints, methods, brief response descriptions. Implementation reference only.}

---

## 3. Who Uses This

{user_context — role, job-to-be-done, frequency, emotional state}

**Design implication:** {one sentence connecting user context to design priority}

---

## 4. Visual Direction

{Use ONE of the following variants based on `{design_system}`:}

**--- VARIANT A: `{design_system}` = "branded" (brand identity document exists) ---**

> This project has an established visual identity. The sections below define its visual language. Your creative freedom is in information architecture, layout, and interaction design. The visual system is fixed.

### Visual Personality

{Copy section 1 from brand identity verbatim — personality statement, register, density, "what it's NOT"}

### Typography

{Copy section 2 from brand identity — font families, type scale, rules}

### Color System

{Copy section 3 from brand identity — core palette, semantic colors, badge pattern, domain colors}

### Component Patterns

{Copy section 4 from brand identity — tables, badges, buttons, status indicators with exact class names or token references as written in the policy}

### Spacing & Layout

{Copy section 5 from brand identity — container, padding, gaps, border radius}

### Reference Pages

{Copy section 6 from brand identity — internal gold-standard pages with routes and why}

### External Influences

{Copy section 7 from brand identity — named products and what to borrow/avoid}

**--- VARIANT B: `{design_system}` = "external" ---**

> This page uses the **{design_system_name}** design system. Apply its tokens, typography, spacing, and component patterns. Do NOT use the CSS tokens in the codebase — those are developer placeholders.

**Structural constraints (still apply):**
- App shell: {fixed shell elements}
- Navigation: {where this page lives}

**--- VARIANT C: `{design_system}` = "existing" (no brand identity, no external system) ---**

> No project design policy was found. Derive the visual system from the tokens below and the patterns observed in other pages of this app. The goal is **visual continuity with the existing product**, not the introduction of a new aesthetic. Where the existing system has gaps, default to restraint: neutral surfaces, sparing color use, status communicated through small consistent badges, type and density appropriate to the data.
>
> **Note for the project team:** Creating a `docs/design-policy.md` will replace this generic fallback with the project's actual visual language. Without one, the designer must reverse-engineer intent from raw CSS values.

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

This is an operational page. The design should optimize for row-level work, exception handling, and workflow progress. Prioritize dense scanning, explicit state visibility, and fast narrowing of large record sets.

**Composition:** Use table-first composition for workflow, review, and exception handling pages. Visual treatment of tables, badges, filters, and density follows the visual system defined in section 4 — this section governs mode, not aesthetic.

**--- If `{page_mode}` = "analytical" ---**

This is an analytical page. The design should help the user understand patterns, compare segments, detect anomalies, and move from summary insight to supporting evidence.

**Design principles:**
- Maintain visual consistency with the rest of the product — the visual system is defined in section 4.
- Charts and summary metrics exist to support understanding, not to decorate. Avoid promotional or BI-template-driven treatments.
- Filters should remain compact and persistent so the user can understand the scope of the analysis at all times.
- Charts may lead the page when they genuinely help the user see patterns faster, but there must always be a clear path to underlying records or evidence.
- Tables are supporting evidence on analytical pages unless row-level processing is the dominant task.

**Composition:** Use chart-led composition for analytical pages. Even on analytical pages, avoid KPI-card walls, decorative dashboards, and disconnected widgets.

**Evidence rule:** Analytics pages may be chart-led, but they must still preserve a clear path to underlying records or evidence. Every chart, metric, or summary should let the user drill into the rows behind it. An analytical page that cannot show its working is a dashboard.

---

## 4b. Analytics Structure (if present)

{Include this section ONLY if the feature has an analytics band, summary strip, or supporting chart layer above/beside the primary worklist. Skip entirely for pure data-entry, list-only, or detail pages with no analytics surface. Defines what each analytics layer is FOR so the designer does not improvise.}

### A. Reading passes

The analytics surface should be designed as a sequence of three reading passes, each with a stated job:

**Pass 1 — headline**

- **Job (1 sentence):** {e.g., "Tell the user total VAT at stake for this period and movement vs prior period in one inline sentence."}
- **Metrics allowed:** {e.g., "total VAT at stake, delta vs prior period (absolute + percentage)."}

**Pass 2 — trend strip**

- **Job (1 sentence):** {e.g., "Show within-source drift over the last 4 completed quarters; detect which source moved."}
- **Primary question this strip answers:** {e.g., "Which sources changed meaningfully this period?"}
- **Comparison type (pick one):**
  - absolute magnitude across sources
  - within-series pattern / drift only
- **Small-multiples axis rule:**
  - shared Y-axis across panels
  - per-source Y-axis (pattern-only; absolute comparison deferred to table)
- **Panel ordering rule:** {e.g., "Order panels by current-period total descending," or "fixed domain order: DE, FR, ES, …"}

**Pass 3 — evidence table**

- **Job (1 sentence):** {e.g., "Let the user compare sources by amount and drill into underlying records."}
- **What must be visible in the table that is not in the strip:** {e.g., "exact amounts per source × period, filing states, drill affordances."}

### B. Drill behaviour

Define exactly what each interactive element does. Every analytics element must have a defined drill target — no ornamental elements.

- **Headline summary:** {e.g., "click opens the current period in `/route` with all sources."}
- **Trend strip tile (sparkline card):**
  - Tile click: {e.g., `/route?country=DE&period=Q1 2026`}
  - Value click: {e.g., same as tile click}
  - Delta click: {e.g., side-by-side view of current vs prior period for that source}
- **Table cells:**
  - Value cell (amount): {e.g., drill to `/route` filtered to that source × period}
  - Label cell (source name): {e.g., `/route` filtered to that source across all periods}
  - Delta cell: {e.g., comparison view of the two periods being compared}
  - "No activity" / inactive cell: {e.g., open onboarding doc or show one-line tooltip}

### C. Palette & status rules

Specify whether the operational status palette extends into the analytics surface:

- **Can the analytics strip use status colors?**
  - No — status palette is reserved for operational states only.
  - Yes, but only for: {describe scope}.
- **How are movement directions encoded?** {e.g., "Arrow glyph + typographic color (red = higher spend, green = lower spend). No colored pills, no tinted backgrounds for deltas."}
- **Category encoding:** {e.g., "Sources are differentiated by label and panel position, never by hue."}

### D. Prohibited analytics patterns (page-specific)

Re-state or add any analytics-specific bans for this page beyond the global hard constraints in section 5:

- {e.g., "No stat-card row above the table."}
- {e.g., "No single multi-series line chart; each source must have its own small multiple."}
- {e.g., "No stacked columns; they hide small sources behind large ones."}
- {e.g., "No KPI cards or dashboard tiles in the analytics band."}

---

## 5. Hard Constraints

{Use ONE of the following variants based on `{design_system}`:}

**--- If `{design_system}` = "branded" ---**

A design containing ANY of these fails review:

{Copy section 8 from brand identity — numbered hard failure list, verbatim}

**AI fingerprint sensitivity:**

{Copy section 9 from brand identity — sensitivity table, verbatim}

Additionally, avoid all standard AI design tool fingerprints:
- Bento grid layouts
- Hero sections on internal pages
- Dashboard metric card grids as page openers
- Purple/violet as primary accent (unless brand identity assigns it)
- Gradient text, gradient backgrounds, glassmorphism
- Oversized border-radius (>10px on containers)
- Heavy card shadows — `shadow-sm` maximum
- Animated number counters
- Chatty empty states with illustrations
- Icons on every label and heading

**Self-test:** If someone would guess AI was involved, the design fails.

**--- If `{design_system}` = "external" ---**

{constraints — responsive, data density, accessibility, performance, navigation position}

**--- If `{design_system}` = "existing" ---**

> No project design policy exists, so only **universal anti-AI-slop guardrails** apply. Aesthetic-specific rules (status color count, sidebar policy, status fill treatment, accent color, type family, etc.) are project decisions and should be added to `docs/design-policy.md` rather than asserted here.

**Universal anti-AI-slop guardrails (a design failing any of these is rejected):**

1. No bento or asymmetric "magazine" grid layouts
2. No hero strips, banner panels, or marketing-style intros above working content
3. No dashboard stat-card grids as page openers (classic AI fingerprint)
4. No 3-feature icon rows or colored-icon-circle clusters (classic AI fingerprint)
5. No gradient text, gradient backgrounds, or glassmorphism
6. No oversized container border-radius (>12px on panels/cards)
7. No animated number counters, hover lift/scale transforms, or other decoration effects
8. No purple/violet as default primary accent (`indigo-600` / `violet-500` are the AI default — pick a deliberate brand accent instead)
9. No icon on every label or heading — icons earn their place by adding information
10. No chatty empty states with illustrations
11. No invented branding (logos, taglines, product names) the project has not specified
12. No marketing copy or enthusiastic language in operational UI

{constraints — responsive breakpoints, data density, accessibility, performance, navigation position}

**Self-test:** If someone would guess AI-generated, it fails. Anything beyond the universal guardrails above (color counts, sidebar vs full-width, status treatment, type family, etc.) is the **project's** decision — when those decisions are made, capture them in `docs/design-policy.md` so future briefs include them as branded constraints rather than re-deriving them per feature.

---

## 6. Design Ask

{Use ONE of the following based on `{handoff_mode}`.}

**--- VARIANT REFINE: `{handoff_mode}` = "refine-screen" ---**

> This is a refinement, not a redesign. The information architecture and task model are stable. Address exactly the three issues below and produce variants for the listed edge states. Do not propose new IA, new components, or alternate layouts unless required to land one of the three fixes. The page should remain recognizable.

**Source diagnostic:** `{review_artifact_path}` — generated by `design-review --artifact` on `{date}`. This is the ground truth; do not invent additional issues.

### Fixes (address all three; in priority order)

{For each item in `{refine_focus}`:}

**{N}. {short-name}** *(severity: {high|medium|low})*

- Location: `{file:line}`
- Question this fix unblocks: {question_blocked from artifact}
- Direction: {before_class} → {after_class}
- {why this is the top fix — one sentence from artifact}

### Required edge-state variants

{For each item in `{required_variants}`:}

- **{state}** — design implication: {why this needs explicit treatment}

### Peer patterns to port

{For each item in `{peer_steals}`:}

- From `{peer_path}`: {pattern} — port by {action}.

### Do NOT break

The audit found these aspects already work. The refinement must preserve them:

{Bullet list from `{already_fine}`}

### Scope guardrails (refine-screen)

- Do NOT redesign the IA, the task model, or the navigation. Those are out of scope for this round.
- Do NOT propose new components unless one of the three fixes genuinely requires it.
- Do NOT add a "get radical" alternative — see step-01 of `design-review` for that conversation; refine-screen is bounded by design.
- DO produce the edge-state variants — they are required, not optional.

**--- VARIANT FRESH: `{handoff_mode}` = "fresh-design" (or unset) ---**

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
- **redesign + branded:** "The current implementation was developer-built without a design process. Start fresh from the data model and user context. Your design must be indistinguishable from the reference pages in section 4."
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
- "How does the page maintain visual consistency with the rest of the product while still feeling analytical?"

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
4. **Information architecture rationale** — why you grouped and prioritized information this way

---

## 8. Implementation Files (Reference Only)

Technical context only — NOT layout or design references.

{If `{design_system}` = "external": omit CSS/style files.}

| File | What it contains |
|------|-----------------|
| {3-5 key files} | {type definitions, API handlers, CSS tokens if applicable} |
````

---

### 3. Self-Review

Before writing, verify:

- [ ] **No current UI anywhere.** The brief does not describe what sections, components, tabs, or groupings currently exist on the page. No phrases like "the current page has", "the left panel shows", "the table is currently placed under", "this section is a card grid." *(Refine-screen exception: section 6 cites the artifact's specific `file:line` references — that's expected, because the artifact IS the diagnostic.)*
- [ ] **Section 2 is entity tables from the DB schema.** No `interface PageData {...}`, no ```typescript blocks, no nested/grouped collections, no derived fields, no rendering hints, no UI-control enums.
- [ ] **Section 1 goals are outcomes, not UI actions.** No "click X" or "switch the Y tab."
- [ ] **Section 4 describes the desired aesthetic, not the current layout.** Reference products (where named by the project policy) describe a *direction*, not the existing implementation.
- [ ] **Section 6 variant is correct.** If `{handoff_mode}` = "refine-screen", section 6 uses the REFINE variant — fixes from `{refine_focus}`, variants from `{required_variants}`, peer steals from `{peer_steals}`, "do not break" from `{already_fine}`. If `{handoff_mode}` = "fresh-design", section 6 uses the FRESH variant — framing + scope directive + open questions, no diagnostic fixes.
- [ ] **Refine-screen scope is bounded.** The brief addresses exactly 3 fixes (not 4, not 2). It lists at least 2 edge-state variants. It does NOT instruct the designer to redesign the IA, replace components wholesale, or "get radical."
- [ ] **Fresh-design section 6 is questions, not primitives.** No "must group by", "must contain", "must have." Questions emerge from user goals + data shape, not from the current UI's solutions.
- [ ] **Reconstructability test (fresh-design only).** A developer could NOT rebuild the current page from this brief. Does not apply in refine-screen mode — that mode intentionally references the current page.
- [ ] **Design system variant is correct and complete:**
  - branded = full brand identity content (personality, typography, colors, components, spacing, reference pages, hard failures, AI sensitivity)
  - existing = visual direction statement + real tokens + anti-pattern list
  - external = names the system, no repo tokens
- [ ] **Positive before negative** — visual direction and reference products come BEFORE hard failures and anti-patterns.
- [ ] **Page mode is correct.** If `{page_mode}` = "analytical", section 4a (Analytics View Addendum) is present. If "operational", section 4a is omitted entirely.
- [ ] **Section 4b is correct.** Section 4b (Analytics Structure) is present iff the feature has an analytics band / summary strip / supporting chart layer above or beside the primary worklist. When present, all four subsections (A reading passes, B drill behaviour, C palette & status rules, D prohibited patterns) are filled with feature-specific values — no template placeholders remain. Every analytics element named in A or B has a stated drill target in B (no ornamental elements). When the feature has no analytics surface, section 4b is omitted entirely.
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
- Claude Design can start without clarifying questions
- **Zero implementation echoes** — no layout, component, section, or tab references from the current page
- **Section 2** is domain-entity tables from the schema — not TS interfaces, not page server shapes
- **Section 4** describes the desired aesthetic (theme, reference products, tokens) — not the current structure
- **Section 6** poses open design problems as questions — not UI-primitive instructions
- **Reconstructability test passes** — the brief constrains the designer to solving the user's problem, not reproducing this specific UI
- Visual identity is complete for the variant (branded/existing/external)
- Positive anchors precede negative constraints
- **Analytics structure (section 4b) is filled when an analytics band exists** — reading passes have stated jobs, every interactive element has a defined drill target, palette rules and prohibited patterns are explicit. The designer cannot improvise the analytics layer.
