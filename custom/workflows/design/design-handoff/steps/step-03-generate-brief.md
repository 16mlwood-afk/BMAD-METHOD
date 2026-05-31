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
7. **Verbatim policy copy — no editorializing.** When the template directs you to "Copy section X from brand identity", reproduce the source text **byte-for-byte** within the quoted block. You may add the explicit attribution line ("From `{brand_identity_path}` §X:") preceding the block, and you may add a clearly-outside-the-quote sentence afterward that applies the rule to the current feature. You may NOT insert parentheticals into the rule itself, soften/narrow/broaden it, carve out exceptions the source does not contain, combine multiple policy bullets in a way that elides one, or substitute your own wording because it reads better. The policy's wording is the contract. If the policy needs a change, surface that to the user as a `modify-design-policy` candidate and write the brief against the **current** policy. See workflow.md "Source-of-Truth Precedence".
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

**Resolve `{project-root}` to the current working tree.** Per `shared/worktree-portability.md` §1, `{project-root}` is the output of `git rev-parse --show-toplevel` from the session's current working directory — the worktree root when inside a worktree, the main checkout root otherwise. Do NOT use a cached resolution from earlier session state or an absolute path from `{main_config}` that points outside the current tree.

```
{project-root}            = $(git rev-parse --show-toplevel)
{implementation_artifacts} = {project-root}/_bmad-output/implementation-artifacts/
{output_path}             = {implementation_artifacts}/design-brief-{feature-slug}-{date}.md
{output_path_relative_to_repo_root} = path relative to {project-root}
```

If `{handoff_mode}` = `"refine-screen"`, use the slug `refine-{feature-slug}` instead of `{feature-slug}` so the refinement brief is visually distinct from any fresh-design brief on the same feature:

```
{output_path} = {implementation_artifacts}/design-brief-refine-{feature-slug}-{date}.md
```

Capture `{output_filename}` = basename of `{output_path}` (used in §1a and the frontmatter below). Capture `{target_slug}` = the kebab-case slug component of the filename — i.e., `{feature-slug}` for fresh-design or `refine-{feature-slug}` for refine-screen. This becomes the active-uniqueness key consumers use; the predecessor lookup in §1a globs against this exact slug.

**Worktree refusal.** Before writing, verify `{output_path}` is a descendant of `{project-root}`. If not, halt with the diagnostic in `shared/worktree-portability.md` §4 — this catches the case where a stale absolute path leaked into state from an earlier session and would have caused the brief to land in the main checkout instead of the worktree.

### 1a. Resolve Predecessor & Decide change_class

Per `shared/brief-revision-policy.md` §4, `design-handoff` must decide each new brief's `change_class` by checking for an existing **active** brief on the same surface. The `target_slug` for this lookup is the same kebab-case identifier used to name the file (in refine-screen mode, that includes the `refine-` prefix — refine-screen briefs supersede earlier refine-screen briefs on the same feature, not fresh-design briefs).

```bash
ls -t {implementation_artifacts}/design-brief-{target_slug}-*.md 2>/dev/null
```

For each candidate file returned by the glob, parse its frontmatter and keep only those where `brief_status: active`. Then branch on the count:

| Count | Resolution |
|---|---|
| 0 | `{change_class}` = `"original"`; `{supersedes_filename}` = `""`; `{predecessor_path}` = none. |
| 1 | `{change_class}` = `"material_revision"`; `{supersedes_filename}` = basename of the predecessor; `{predecessor_path}` = absolute path. (Re-running `design-handoff` on a surface IS material by definition — minor edits don't go through this workflow.) |
| 2+ | **HALT.** The active-uniqueness invariant (`brief-revision-policy.md` §2.6) is already broken. Surface the list of conflicting paths and tell the user to fix the predecessor chain (set `brief_status: superseded` and `superseded_by` on the older briefs) before generating a new brief. Do NOT proceed and do NOT auto-pick a predecessor — the existing inconsistency must be resolved deliberately. |

Capture `{source_run_date}` = `{date}` (the workflow's `date` variable; same value used in `last_modified_date`).

### 1b. Flip the Predecessor (only when `change_class == "material_revision"`)

When §1a found exactly one active predecessor, edit that file's frontmatter in-place BEFORE writing the new brief:

- Set `brief_status: superseded`
- Set `superseded_by: {output_filename}`
- Set `last_modified_by: workflow`
- Set `last_modified_date: {date}`

Leave every other field (including `source_workflow`, `source_run_date`, the body, and any prior changelog) untouched. This is the only edit `design-handoff` makes to an existing file.

If the predecessor's frontmatter is missing the provenance block entirely (a pre-policy brief), back-fill the full block at the same time per `brief-revision-policy.md` §7 — `revision_mode: workflow_generated`, `change_class: original`, `source_workflow: design-handoff`, `source_run_date` set to its existing top-level `date:` field if present (else its `last_modified_date`), and then apply the supersede edit above. The point is to leave the predecessor in a consumer-valid state so a later `--allow-superseded` lookup still works.

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

# Block A — Revision Provenance (see shared/brief-revision-policy.md §2)
target_slug: {target_slug}               # kebab-case slug; doubles as the active-uniqueness key. Refine-screen runs use the "refine-{feature-slug}" form.
brief_status: active
revision_mode: workflow_generated
change_class: {change_class}             # original | material_revision (decided in §1a)
supersedes: {supersedes_filename}        # empty when change_class is original
superseded_by:                           # always empty on a freshly generated brief
source_workflow: design-handoff
source_run_date: {source_run_date}
policy_version_required: {policy_version}     # version of docs/design-policy.md this brief was authored against. Downstream (design-synthesize, design-implement) MUST halt or warn if the current policy version exceeds this value, since rules ratified after this brief may invalidate its assumptions. Populate from the frontmatter of the policy file resolved in step-01 (default to `0` if no policy exists — `existing` design_system variant).
last_modified_by: workflow
last_modified_date: {date}

# Block B — Content (see shared/brief-revision-policy.md §2)
mode: {handoff_mode}                     # fresh-design | refine-screen
page_mode: {page_mode}                   # operational | analytical | detail
route: {route}                           # primary route this brief targets
band_provenance: {band_provenance}       # inherited | recommended-new | recommended-drop | none
{# analytics_archetype is REQUIRED iff band_provenance ∈ {inherited, recommended-new}; omit the line entirely otherwise. #}
{if has_analytics_band}
analytics_archetype: {analytics_archetype}   # trend | distribution | composition | ranking | coverage | flow | single-metric | correlation
{endif}
{# In refine-screen mode the following four fields are REQUIRED. In fresh-design mode they MUST be omitted entirely. #}
{if handoff_mode == "refine-screen"}
screen_review_ref: {review_artifact_path_relative_to_repo_root}
targeted_changes:
  {for each entry in {targeted_changes_list}}
  - region: {region_name}
    rationale: "{V-ID} — {one-line summary}"
  {end for}
{if collapse_occurred}collapse_note: "{which V-IDs collapsed and why}"{end if}
unchanged_regions:
  {for each entry in {unchanged_regions_list}}
  - region: {region_name}
    note: "{one-line reason this region is protected}"
  {end for}
deferred_violations:
  {for each V-ID in {deferred_violations_list}}
  - {V-ID}: "{reason deferred — out of scope, mechanical-only, IA decision, etc.}"
  {end for}
{end if}
---

# Design Brief: {feature_name}

## For Claude Design

> **Repository:** **{github_repo_url}** (branch: `main`). Connect to THIS repository to read referenced files.
>
> **This brief:** `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
>
> **Revision provenance** follows `brief-revision-policy.md` in the shared design workflow docs. Consumers (design-artifact-loop, design-synthesize) validate the provenance frontmatter at intake; do not hand-edit this brief into a scope or intent change — re-run `design-handoff` instead.
>
> **Why connecting the repo is safe here:** this brief is the bias filter — it deliberately omits the current layout, so reading the repo for the data model, tokens, and referenced files will not anchor you to the existing screens. This is distinct from Claude Design **system setup** (`onboard-design-system`), where the live repo / current screens must NEVER be the seed. Here, read the brief and the files it names, then design the information architecture fresh.

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

{Include this section ONLY if `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). Skip entirely for `none` and `recommended-drop`. This section defines what the analytics layer is FOR and what *shape* it takes, so the designer does not improvise — and does not default every band to the same trend-strip-of-small-multiples. The shape is governed by `{analytics_archetype}`, selected in step-01 §5c against `shared/analytics-archetypes.md`.}

### A. Archetype & job

- **Archetype:** {analytics_archetype} — {one of: trend | distribution | composition | ranking | coverage | flow | single-metric | correlation}
- **Band provenance:** {band_provenance} — {if recommended-new: "net-new — confirmed with user on {date}"}
- **The one question this band answers (1 sentence):** {state it in the user's words — e.g. "which weeks are we missing statements for, and in which region?" Do NOT restate as a generic "show trends."}
- **Why this archetype (grounding):** {name the data dimension AND the user question that selected it — e.g. "coverage: data has per-week × per-region completeness; the job is finding gaps, not reading a trend."}

### B. Reading passes (derived from the archetype)

Do not impose a fixed headline → trend-strip → table sequence. Read `shared/analytics-archetypes.md` for the selected archetype and let its **form** drive the passes. Specify each pass the band actually needs:

- **Lead pass — the form that answers the question fastest:** {the archetype's form, made concrete for this feature. For `coverage`: a completeness strip where the gaps are the content. For `ranking`: a sorted top-N bar list capped and labelled. For `composition`: a single 100%-bar. For `single-metric`: one value + sparkline + threshold. For `trend`: small-multiples with a stated Y-axis rule. State dimensions, ordering, and what is emphasised.}
- **Secondary pass (only if a second archetype genuinely co-occurs):** {name it and keep it subordinate — e.g. "coverage is dominant; a faint per-region trend is secondary, not co-equal." Omit if the band is single-archetype.}
- **Evidence pass — path to the rows:** {what the underlying records show that the lead pass cannot — exact values, states, drill affordances. Every band must preserve a path to evidence; a band that can't show its working is a dashboard.}

### C. Drill behaviour

Every analytics element must have a defined drill target — no ornamental elements (the cross-cutting rule from the archetypes file). For each element the band contains, state exactly where interaction goes:

- **Lead element(s):** {e.g. for coverage: "a gap mark opens the missing record's import action at `/route?week=…&region=…`"; for ranking: "a bar opens that entity at `/route?entity=…`"}
- **Value / label / delta affordances:** {what each click does, in this feature's routes}
- **Empty / inactive / gap state:** {what a no-data or gap cell does — open the resolving action, not a dead tooltip}

### D. Palette & status rules

Specify whether the operational status palette extends into the analytics surface:

- **Can the band use status colors?**
  - No — status palette is reserved for operational states only.
  - Yes, but only for: {describe scope — e.g. "gap marks in the coverage strip may use the warning color, since a gap IS an actionable exception state."}
- **How are movement / category encoded?** {prefer position, glyph, and typographic weight over hue — e.g. "direction by arrow glyph + typographic color; categories by label and position, never by fill hue. No colored pills, no tinted delta backgrounds."}

### E. Prohibited analytics patterns (page-specific)

Re-state the cross-cutting bans from `shared/analytics-archetypes.md` plus any archetype-specific ones for this page, beyond the global hard constraints in section 5:

- No KPI / stat-card row above the table (dashboard fingerprint).
- {archetype-specific — e.g. for trend: "no single multi-series line chart; each series its own small multiple; no stacked columns." For composition: "no pie/donut; no time-stacked bars." For coverage: "'all good' must not look identical to 'gaps present' at a glance." For ranking: "do not render all N — cap and label the cut."}

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

---

## Changelog

Minor revisions (clarifications only — see `brief-revision-policy.md` §1) append one line here. Material revisions re-run `design-handoff` instead; they do NOT append to this changelog — they live in a new brief file.

{If change_class is "material_revision", the first changelog entry below records the supersession; otherwise this section starts empty and is populated by future hand-edits.}

- {date} — {if change_class == "material_revision": "Material revision; supersedes `{supersedes_filename}`. Author: design-handoff workflow."; if change_class == "original": leave the bullet OUT entirely and the section will be empty until a clarification is added.}
````

---

### 3. Self-Review

Before writing, verify:

- [ ] **Block A (Provenance) is complete and consistent.** All 11 fields from `brief-revision-policy.md` §2 Block A are present. `revision_mode` is `workflow_generated`. `last_modified_by` is `workflow`. `last_modified_date == source_run_date == {date}`. If `change_class == "material_revision"`, `supersedes` names an existing file in `{implementation_artifacts}`; if `change_class == "original"`, `supersedes` is empty. `superseded_by` is empty (it's set retroactively on the predecessor in §1b, never on a freshly generated brief).
- [ ] **Block B (Content) is complete for the run mode.** Always-required fields present: `mode`, `page_mode`, `route`. If `mode: refine-screen`, also present: `screen_review_ref` (resolvable path), `targeted_changes` (≥1 entry, each citing a V-ID), `unchanged_regions` (≥1 entry), `deferred_violations` (may be empty list but key present). If a collapse occurred per the design-handoff "Collapse allowance", `collapse_note` is present and names both collapsed V-IDs + the promoted one. If `mode: fresh-design`, the refine-screen-specific fields MUST be absent (not just empty).
- [ ] **Predecessor flipped (if applicable).** When `change_class == "material_revision"`, the predecessor file's frontmatter was edited in §1b: its `brief_status` is now `superseded`, its `superseded_by` is set to this brief's filename, and its `last_modified_date` is `{date}`. Re-read the predecessor to confirm — the active-uniqueness invariant must hold after this run completes.
- [ ] **No current UI anywhere.** The brief does not describe what sections, components, tabs, or groupings currently exist on the page. No phrases like "the current page has", "the left panel shows", "the table is currently placed under", "this section is a card grid." *(Refine-screen exception: section 6 cites the artifact's specific `file:line` references — that's expected, because the artifact IS the diagnostic.)*
- [ ] **Verbatim policy quotes — no drift.** For every section that quotes the brand identity / design policy (section 4 Visual Identity sub-sections, section 5 Hard Failures, AI Fingerprint Sensitivity), re-open `{brand_identity_path}` and string-match each quoted bullet against the source. Specifically check: (a) no parentheticals appear in your bullet that don't appear in the policy bullet, (b) no qualifying phrase ("usually", "primarily", "except when", "the codebase already uses X so …") softens a hard rule, (c) every bullet in the policy's hard-failure list appears in section 5 — none silently dropped, (d) no merged bullets where two policy items collapsed into one. If any bullet fails the match, replace it with the policy text verbatim. **This catches the single most common drift mode — softening a hard rule with a "but in this case …" parenthetical.**
- [ ] **Section 2 is entity tables from the DB schema.** No `interface PageData {...}`, no ```typescript blocks, no nested/grouped collections, no derived fields, no rendering hints, no UI-control enums.
- [ ] **Section 1 goals are outcomes, not UI actions.** No "click X" or "switch the Y tab."
- [ ] **Section 4 describes the desired aesthetic, not the current layout.** Reference products (where named by the project policy) describe a *direction*, not the existing implementation.
- [ ] **Section 6 variant is correct.** If `{handoff_mode}` = "refine-screen", section 6 uses the REFINE variant — fixes from `{refine_focus}`, variants from `{required_variants}`, peer steals from `{peer_steals}`, "do not break" from `{already_fine}`. If `{handoff_mode}` = "fresh-design", section 6 uses the FRESH variant — framing + scope directive + open questions, no diagnostic fixes.
- [ ] **Refine-screen scope is bounded.** The brief addresses exactly 3 fixes (not 4, not 2). It lists at least 2 edge-state variants. It does NOT instruct the designer to redesign the IA, replace components wholesale, or "get radical." If two top-3 violations are mechanical (token/class swaps with no design decision), the workflow.md "Collapse allowance" applies — one combined Vx+Vy entry plus a promoted design-requiring V-ID, with `collapse_note` in frontmatter. Never collapse twice; never collapse a design-requiring violation.
- [ ] **Fresh-design section 6 is questions, not primitives.** No "must group by", "must contain", "must have." Questions emerge from user goals + data shape, not from the current UI's solutions.
- [ ] **Reconstructability test (fresh-design only).** A developer could NOT rebuild the current page from this brief. Does not apply in refine-screen mode — that mode intentionally references the current page.
- [ ] **Design system variant is correct and complete:**
  - branded = full brand identity content (personality, typography, colors, components, spacing, reference pages, hard failures, AI sensitivity)
  - existing = visual direction statement + real tokens + anti-pattern list
  - external = names the system, no repo tokens
- [ ] **Positive before negative** — visual direction and reference products come BEFORE hard failures and anti-patterns.
- [ ] **Page mode is correct.** If `{page_mode}` = "analytical", section 4a (Analytics View Addendum) is present. If "operational", section 4a is omitted entirely.
- [ ] **Section 4b is correct.** Section 4b (Analytics Structure) is present iff `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). When present, all five subsections (A archetype & job, B reading passes, C drill behaviour, D palette & status rules, E prohibited patterns) are filled with feature-specific values — no template placeholders remain. The archetype is named and matches `{analytics_archetype}` from step-01; subsection A grounds it (data dimension + user question); B's reading passes follow that archetype's form rather than a defaulted trend strip; every analytics element named in B or C has a stated drill target in C (no ornamental elements). When `{has_analytics_band}` is `false`, section 4b is omitted entirely.
- [ ] **band_provenance is honest.** Frontmatter `band_provenance` is set. If `recommended-new` or `recommended-drop`, the recommendation was surfaced to the user for veto (not silently injected/removed). `analytics_archetype` is present in frontmatter iff `{has_analytics_band}` is `true`.
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
- **Analytics structure (section 4b) is filled when an analytics band exists** — the archetype is named and grounded (data dimension + user question), reading passes are derived from that archetype's form (not a defaulted trend strip), every interactive element has a defined drill target, palette rules and prohibited patterns are explicit. The designer cannot improvise the analytics layer.
- **Band presence is a judgment, not an inheritance** — `band_provenance` is set; a `recommended-new` band reflects data + job (not the legacy render) and was veto-surfaced to the user. A bare-table feature whose job is pattern/coverage/ranking work is NOT silently shipped without a band.
