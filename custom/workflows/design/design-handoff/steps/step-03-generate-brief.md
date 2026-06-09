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
composition_provenance: {composition_provenance}   # policy-default | recommended-alt (decided in §5a; recommended-alt names a job-fit composition in §4a and was veto-surfaced)
band_provenance: {band_provenance}       # inherited | recommended-new | recommended-drop | none
{# analytics_archetype is REQUIRED iff band_provenance ∈ {inherited, recommended-new}; omit the line entirely otherwise. #}
{if has_analytics_band}
analytics_archetype: {analytics_archetype}   # trend | distribution | composition | ranking | coverage | flow | waterfall | single-metric | correlation
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

**Capabilities the design must support:**
{must_support_capabilities — jobs the operator must be able to accomplish, as outcomes. Each is a requirement the design must satisfy even though this brief deliberately withholds the current layout. If the design cannot express one of these, that is a gap to flag — not to drop silently. Omit this subsection only when the surface genuinely has no capabilities beyond the primary goals above.}

**Deliberately not carried forward (logged drops):**
{Render this subsection ONLY when `{dropped_capabilities}` is non-empty (a redesign that consciously sheds or relocates a capability the current surface had). One bullet per entry: the capability (outcome phrasing) · why (`relocated` to which sibling surface / `obsolete` / `out-of-scope-by-design`). This makes every drop an explicit, on-the-record decision the designer and the user can see — the design need NOT build these, but they are documented, not silently absent. Omit the subsection entirely when `{dropped_capabilities}` is empty.}

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

### Feature State → Color Mapping

{After copying the Color System, generate a compact **Feature State → Color Mapping table** that names every meaningful state on THIS feature and maps it to exactly one of the four status tokens. This is the anti-rainbow contract — it makes explicit that no state gets a unique color outside the four-tone system.

Prefix the table with this constraint block:
> ⚠️ **Strict 4-color cap — every state on this feature maps to exactly one of these four rows.** The categorical tag palette (`--tag-*`) is banned here. Funnel drop-off reason chips do NOT each get a unique color — they map to yellow (expected drop-off) or red (genuine failure).

Then generate the table from the feature's actual states (replace the examples with this feature's real states):

| State | Color | Token |
|---|---|---|
| {error/failure states, e.g. "enrichment error", "processing failed", "blocked"} | Red | `--status-danger` / `--status-danger-muted` |
| {attention/unresolved states, e.g. "unmatched", "needs review", "no buy-box", "unprofitable", "pricing stale"} | Yellow | `--status-warning` / `--status-warning-muted` |
| {success/complete states, e.g. "matched", "reconciled", "enriched", "ranked winner", "received"} | Green (muted) | `--status-success-muted` |
| {resting/neutral states, e.g. "pending", "queued", "in-flight", "not started"} | Gray | `--status-neutral` / `--status-neutral-muted` |

Move any feature-specific color-mapping guidance HERE rather than burying it inside the policy copy block above. This table is the primary color-constraint signal Claude Design receives and must be impossible to miss.}

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

{First, if `{composition_provenance}` = "recommended-alt", emit the composition-override block below — it leads §4a and supersedes the "Composition:" line of the page-mode block that follows. If `{composition_provenance}` = "policy-default", OMIT the override block entirely and emit only the page-mode block.}

**--- Composition override (include ONLY if `{composition_provenance}` = "recommended-alt") ---**

> **Primary composition for this surface: {named job-fit composition from `{composition_rationale}`} — NOT the `{page_mode}` default.**
>
> This surface is `{page_mode}` (it {one-line work description}), but its job is {dispensed / comparison-first / single-item / verification-against-a-source — from the §5a answers}, so the policy's default {table-first worklist / chart-led / record-view} composition is the wrong *primary* shape. Design the primary surface as **{named composition}**. {One or two sentences making it concrete for this feature — e.g. for an operational override: "a full-width single-item decision surface the operator streams through, with the worklist demoted to a deliberate triage/backlog view, not the home screen." For a `detail` verify-against-source override: "a source-co-present verification layout — the extracted record and its source document (receipt / email / PDF) rendered together with the source sticky, so the operator's eye moves value ↔ source; the source must NOT collapse once extraction completes."} The visual system in section 4 still governs all treatment; this overrides only the *composition*, decided from the job per design-handoff §5a (confirmed with the user on {date}). Where the page-mode block below states a default "Composition:", THIS block wins.

{Then include ONE of the following based on `{page_mode}`:}

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

**--- If `{page_mode}` = "detail" ---**

This is a detail page — a drawer or full-page view of **one record**. The design should optimize for reading and editing a single record's fields, not for processing a queue or analyzing a dataset. The user arrived here by drilling from a worklist; this view is the extension of that list, never a re-skin of it.

**Design principles:**
- Group fields by the user's mental model of the record, not by database table order. Make the record's identity and current state legible at the top.
- Inline edit and per-record actions are first-class — surface them where the field lives, not in a distant toolbar.
- Density is moderate (between a dense worklist row and a relaxed analytical page) — the user is reading one record carefully, not scanning hundreds.
- Usually no analytics band: most single records have no aggregate dimension, and child collections (line items, history) are supporting tables, not an analytics surface. **Exception:** an analytics-rich detail page — a research or monitoring view whose one entity carries genuine aggregates (price/rank over time, competitor share, ownership history) — does have analytics surfaces, often several. When two or more are present, §5e ranks them (hero / supporting / drill) instead of stacking them flat; do not suppress them just because the page is `detail`.

**Composition:** Record-view composition — neither table-first nor chart-led. The visual treatment (typography, badges, spacing) follows the visual system in section 4; this section governs mode. Per project policy §6/§7, a detail view is an extension of its operational list, not a standalone redesign.

---

## 4b. Analytics Structure (if present)

{Include this section ONLY if `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). Skip entirely for `none` and `recommended-drop`. This section defines what the analytics layer is FOR and what *shape* it takes, so the designer does not improvise — and does not default every band to the same trend-strip-of-small-multiples. The shape is governed by `{analytics_archetype}`, selected in step-01 §5c by the `analytics-surface-architect` skill (its taxonomy SoT is `shared/analytics-archetypes.md`). The fields below are rendered from that skill's captured decision object — do NOT re-derive them here.}

### 0. Analytics hierarchy (only when the page has ≥2 analytics surfaces — from §5e)

{Include this sub-section ONLY when `{analytics_hierarchy}` is non-empty (the §5e gate fired — the page carries two or more distinct analytics surfaces). Skip entirely for single-surface pages. It ranks the surfaces so the designer assigns visual weight deliberately instead of stacking them flat — policy §6 (one or two lead charts + supporting), §5 (no card-grid-as-structure). Rendered from the captured §5e decision; do NOT re-rank here.}

- **Primary question of the page:** {from `{hierarchy_rationale}` — the one job that decides the ranking}
- **Hero (full-weight, 1–2):** {the surface(s) tagged `hero` + archetype — the chart that answers the primary question}
- **Supporting (compact — sparkline / strip / mini):** {each `supporting` surface + archetype, demoted to a compact form, NOT a full panel}
- **Drill (collapsed behind expand):** {each `drill` surface + archetype, available on demand, not in the default scan}
- **Why this ranking (demoted, not deleted):** {from `{hierarchy_rationale}` — why the hero leads and why each other surface is kept but subordinated; a research/detail page keeps all of it, ranked}

When this sub-section is present, the A–E spec below is written **per surface**, in hero → supporting → drill order, each at the visual weight its tier dictates (the hero gets the full A–E treatment; supporting/drill surfaces get a compact form + drill path, not a full-panel spec).

### A. Archetype & job

- **Archetype:** {analytics_archetype} — {one of: trend | distribution | composition | ranking | coverage | flow | waterfall | single-metric | correlation}
- **Band provenance:** {band_provenance} — {if recommended-new: "net-new — confirmed with user on {date}"}
- **The one question this band answers (1 sentence):** {state it in the user's words — e.g. "which weeks are we missing statements for, and in which region?" Do NOT restate as a generic "show trends."}
- **Why this archetype (grounding):** {from `{archetype_winner_reason}` — names the data dimension AND the user question that selected it, e.g. "coverage: data has per-week × per-region completeness; the job is finding gaps, not reading a trend."}

### B. Reading passes (derived from the archetype)

Do not impose a fixed headline → trend-strip → table sequence. Read `shared/analytics-archetypes.md` for the selected archetype and let its **form** drive the passes. Specify each pass the band actually needs:

- **Lead pass — the form that answers the question fastest:** {the archetype's form, made concrete for this feature. For `coverage`: a completeness strip where the gaps are the content. For `ranking`: a sorted top-N bar list capped and labelled. For `composition`: a single 100%-bar. For `flow`: a funnel/stage strip with drop deltas. For `waterfall`: an anchored opening bar, signed labelled steps, an anchored closing bar — deltas reconcile to the close, reasons live in the step's drill (not a duplicate chip). For `single-metric`: one value + sparkline + threshold. For `trend`: small-multiples with a stated Y-axis rule. State dimensions, ordering, and what is emphasised.}
- **Secondary pass (only if a second archetype genuinely co-occurs):** {from `{archetype_secondary}` — name it and keep it subordinate, e.g. "coverage is dominant; a faint per-region trend is secondary, not co-equal." Omit if `{archetype_secondary}` is `none`.}
- **Evidence pass — path to the rows:** {what the underlying records show that the lead pass cannot — exact values, states, drill affordances. Every band must preserve a path to evidence; a band that can't show its working is a dashboard.}

### C. Drill behaviour

Every analytics element must have a defined drill target — no ornamental elements (the cross-cutting rule from the archetypes file). Render this from `{archetype_drill_map}` (the skill's element → drill-target map); for each element the band contains, state exactly where interaction goes:

- **Lead element(s):** {from `{archetype_drill_map}` — e.g. for coverage: "a gap mark opens the missing record's import action at `/route?week=…&region=…`"; for ranking: "a bar opens that entity at `/route?entity=…`"}
- **Value / label / delta affordances:** {what each click does, in this feature's routes}
- **Empty / inactive / gap state:** {what a no-data or gap cell does — open the resolving action, not a dead tooltip}

### D. Palette & status rules

Specify whether the operational status palette extends into the analytics surface:

- **Can the band use status colors?**
  - No — status palette is reserved for operational states only.
  - Yes, but only for: {describe scope — e.g. "gap marks in the coverage strip may use the warning color, since a gap IS an actionable exception state."}
- **How are movement / category encoded?** {prefer position, glyph, and typographic weight over hue — e.g. "direction by arrow glyph + typographic color; categories by label and position, never by fill hue. No colored pills, no tinted delta backgrounds."}

### E. Prohibited analytics patterns (page-specific)

Render the page-specific bans from `{archetype_prohibited}` (the skill's `prohibited` list), plus the cross-cutting bans from `shared/analytics-archetypes.md`, beyond the global hard constraints in section 5:

- No KPI / stat-card row above the table (dashboard fingerprint).
- {from `{archetype_prohibited}` — archetype-specific, e.g. for trend: "no single multi-series line chart; each series its own small multiple; no stacked columns." For composition: "no pie/donut; no time-stacked bars." For coverage: "'all good' must not look identical to 'gaps present' at a glance." For ranking: "do not render all N — cap and label the cut."}

---

## 4c. Surface Topology

{Include this section ONLY when `{surface_topology_verdict}` is NOT `single-page-appropriate`. Omit entirely — no heading, no placeholder — when the verdict is `single-page-appropriate`.}

{`{surface_topology_notes}` — the recommended topology for this feature, as assessed in step-01 §5d. This section informs the designer that the feature they are designing is one surface in a multi-surface feature — not the whole story. The surrounding context shapes composition, navigation affordances, and what belongs on THIS surface vs. another.}

**This brief covers:** `{route}` — {one-line job description for the primary route only}.

{Render only the applicable conditional block below; omit the others:}

{If `needs-detail-route`:}
**Recommended: detail route (separate brief):** `{feature_prefix}/[id]` — the per-item deep-dive; full evaluation evidence, record-level actions, field-depth content that does not fit a drawer or list row. This brief does not cover that surface. {Note whether a second brief was generated in this session or is pending.}

{If `needs-tab-views`:}
**View structure within this route:** {List the tab names and the operator job each one owns. The designer must accommodate this view structure in the IA. Tab names should describe the operator job, not just the content category.}

{If `needs-sibling-route`:}
**Recommended: sibling route (separate brief):** `{sibling_route}` — {the operator job it owns, distinct from the primary route}. This brief does not cover that surface. {Note whether a second brief was generated in this session or is pending.}

---

## 4d. Analytic depth (decision-bearing figures — render like an analyst, not a schoolboy)

{Include this section ONLY if `{has_decision_numbers}` is `true` (the surface presents figures the user acts on — verdict, score, ROI / margin / profit, KPI). Omit entirely for pure data-entry / passive-review / list-only surfaces. This is **surface-level, not band-only**: it governs the depth of every decision-bearing figure WHEREVER it sits — the §4b band's values AND the §4a record / hero / verdict numbers (a `detail` buy page's `ROI 42%` / `+£840` hero figures are exactly the case a band-only check misses). A correctly-shaped surface still fails if its figures are naked point estimates with no baseline and no read — *correct and useless*. Rendered from the `analytics-rigor` skill's captured decision (step-01 §5c-2; one block **per surface** on multi-surface pages) — do NOT re-derive.}

- **Lead with this read:** {rigor_read_sentence — the one-line conclusion the surface states BEFORE the evidence, e.g. "Buy: 47% ROI, top quartile — but the buy-box is a coin-flip, so size small." / OR "— none: this surface carries no single decision."}
- **Decision-bearing numbers — each carries uncertainty AND a base rate:** {render `{rigor_decision_numbers}` — per metric (a §4b band value OR a §4a hero/verdict figure), the range / confidence / assumption it must show AND the baseline it's shown against (portfolio median / category norm / own history). A bare point estimate on any of these is a defect, not a style choice.}
- **Deciding field per chart (not the handy proxy):** {render `{rigor_deciding_fields}` — for each series, the field that actually answers the question, e.g. "share of *sales* (sold-30d), NOT share of on-hand stock." A proxy substituted for the deciding field is a defect.}
- **Data gaps (surface, NEVER fabricate):** {render `{rigor_data_gaps}` — metrics not yet in the data; until enrichment supplies them the figure ships as an honest bare number with the gap noted, never a faked interval or invented baseline. / OR "none — every figure is satisfiable from current data."}

---

## 4e. Decision analysis (capital-commitment surfaces — render like a quant desk, not a report)

{Include this section ONLY if `{is_capital_decision}` is `true` (the surface's job is to commit a scarce resource — capital / inventory slots / time — under uncertainty with a real downside: a buy / reorder / sizing / go-no-go-with-stake). Omit entirely for every other surface — a dashboard, coverage strip, status worklist, or report carries decision *numbers* (handled by §4d) but commits nothing, so it stops at §4d. §4d made the figures honest (senior-analyst grade); this models and sizes the *decision* (executive grade). Rendered from the `decision-analysis` skill (step-01 §5c-3; one block **per decision surface**) — do NOT re-derive. The visual system in §4 still governs all treatment: a modelled outcome distribution and a sizing read render flat and dense, never as a chrome-y "risk dashboard."}

- **Frame the bet:** {render `{decision_frame}` — action · capital at risk · horizon · payoff (what is won, what is lost and for how long). e.g. "Commit £620 / 8 units, ~45-day hold; win = net margin, lose = capital tied up + return costs." The surface must state the stake and downside, not just an ROI.}
- **Modelled outcome (distribution, not a point):** {render `{decision_outcome}` — method (Monte-Carlo / scenario / closed-form / single-scenario) + P(success) · expected value · P10 · P90, with the model's assumptions named. e.g. "P(profit) 62%, E[ROI] 24%, P10 −£1.10, P90 +£4.30 — 4,000 GBM paths off the current price regime." If un-modellable, an honest `single-scenario` read + the VOI gap, NEVER a fabricated distribution.}
- **Sizing (to the loss tail, not the mean):** {render `{decision_sizing}` — the recommended quantity and the basis (loss-distribution / capital-cap / fractional-Kelly) and the downside it survives. e.g. "Buy 8, not 24 — at 24 the P10 outcome breaches the per-lead capital cap." A binary BUY/PASS or an unjustified quantity is a defect.}
- **Breakeven driver (the threshold that flips the call):** {render `{decision_sensitivity}` — the single most decision-sensitive input and its tipping point. e.g. "Breakeven buy-box-win rate is 22%; below that this loses money." This is the highest-value single read.}
- **Outside view + regime + asymmetry:** {render `{decision_context}` — the computed reference class (an owned-history base rate, the outside view beside the modelled inside view); the decision-relevant time window (regime-weighted, stale window excluded); and the payoff asymmetry that tilts the recommendation (cost of a wrong commitment vs a missed one). Compute reference classes from owned data; do not declare them gaps.}
- **Value-of-information & gaps (surface, NEVER fabricate):** {render `{decision_gaps}` + the VOI ranking — the missing input that would most move the decision (so the operator knows whether to act or wait), and any probabilistic input absent today. An un-modellable decision ships as an honest `single-scenario` read with the gap named — never a confident P(success) off an invented input. / OR "none — the decision is fully modellable from current data."}
- **Decision verdict at handoff:** `{decision_verdict}` (decision-grade | risk-modelled | single-scenario)

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

If `{page_mode}` = **detail:**
> Design this page for a user whose main job is to read and act on one record — understand its current state, edit its fields, and take the next action on it — having arrived here from a worklist.

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
- Detail questions should be about single-record legibility, field grouping, inline edit/action affordances, and how state and next-action are surfaced on one record.
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

{If `{design_system}` = "branded" AND `docs/design-policy.md` contains migration notes flagging non-compliant components, add this block immediately after the file table:

⚠️ **Token values only — do NOT anchor to existing component styling.** The policy flags these implementations as currently non-compliant; reading their code will bias Claude Design toward the wrong patterns:
{For each non-compliance named in the policy migration notes, e.g.:}
- `StatusBadge` — currently `rounded-full` with a leading Lucide icon; policy §3 requires `rounded-md`, no icon, no dot
- Categorical `--tag-*` palette in `tokens.css` — exceeds the 4-color operational status cap; status communication uses only `--status-danger/warning/success/neutral`

Read token VALUES (colors, `--radius-md`) from `tokens.css` — anchor to those. Do NOT anchor to the shape, size, icon, or decoration pattern of any component whose compliance is a migration target.}

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
- [ ] **Page mode is correct.** `{page_mode}` is one of the three contract values (`operational | analytical | detail`) — never a fourth. Section 4a (Page Mode) contains exactly the block for the resolved mode and no other (the operational, analytical, OR detail block). Frontmatter `page_mode` matches the 4a block. A `detail` page is *usually* `band_provenance: none` (a lone record has no aggregate dimension) — but the **analytics-rich detail exception** (a research / monitoring view whose one record carries genuine aggregates — price/rank over time, competitor share, ownership history) DOES carry analytics surfaces, ranked by §5e and specified in §4b.0; do not assert §4b is always absent on `detail`. What a detail page must never carry is a *dashboard* — KPI-card grid, bento, or mini-charts as a stat wall (§5/§7).
- [ ] **Section 4b is correct.** Section 4b (Analytics Structure) is present iff `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). When present, all five subsections (A archetype & job, B reading passes, C drill behaviour, D palette & status rules, E prohibited patterns) are filled with feature-specific values — no template placeholders remain. The archetype is named and matches `{analytics_archetype}` from step-01; subsection A grounds it (data dimension + user question); B's reading passes follow that archetype's form rather than a defaulted trend strip; every analytics element named in B or C has a stated drill target in C (no ornamental elements). When `{has_analytics_band}` is `false`, section 4b is omitted entirely. (Analytic *depth* is no longer a §4b subsection — it is the surface-level §4d, checked below.)
- [ ] **Section 4d is correct.** Section 4d (Analytic depth) is present iff `{has_decision_numbers}` is `true` (the surface carries figures the user acts on — verdict / score / ROI / KPI; broader than `{has_analytics_band}`, so it is present on a bandless `detail`/`analytical` decision surface and absent on pure data-entry/passive-review/CRUD). When present, it renders the §5c-2 rigor spec for **every** decision-bearing figure WHEREVER it sits (§4b band values AND §4a record/hero/verdict numbers): a lead read sentence (or explicit "none"), each decision number's uncertainty + base rate (or a named data gap), and the deciding field per chart. No fabricated interval stands in for a data gap (honesty gate). On multi-surface pages there is one §4d block per surface.
- [ ] **Section 4e is correct.** Section 4e (Decision analysis) is present iff `{is_capital_decision}` is `true` (the surface commits a scarce resource under uncertainty with a downside — buy / reorder / sizing; narrower than `{has_decision_numbers}`, so a dashboard/coverage/status surface has NO §4e). When present, it renders the §5c-3 decision spec: a framed bet (stake · horizon · downside), a modelled outcome distribution (P(success)/EV/P10/P90, or an honest `single-scenario` + VOI gap), a sizing read tied to the loss tail (a quantity with a basis, not BUY/PASS), the breakeven driver with its threshold, and the outside-view/regime/asymmetry context. No fabricated outcome distribution stands in for an un-modellable decision (model-honesty gate). When `{is_capital_decision}` is `false`, section 4e is omitted entirely.
- [ ] **band_provenance is honest.** Frontmatter `band_provenance` is set. If `recommended-new` or `recommended-drop`, the recommendation was surfaced to the user for veto (not silently injected/removed). `analytics_archetype` is present in frontmatter iff `{has_analytics_band}` is `true`.
- [ ] **composition_provenance is honest.** Frontmatter `composition_provenance` is set (`policy-default` or `recommended-alt`). If `recommended-alt`: §4a leads with the composition-override block naming the job-fit composition (no template placeholders remain), the override was veto-surfaced to the user (not silently imposed), and `{page_mode}` still honestly names the *work type* (the override changed composition, not mode — the page can be `operational` with a non-table composition). If `policy-default`: no override block appears and §4a is the plain page-mode block. The composition was decided from the §5a job questions, NOT inherited from the policy default or the legacy render.
- [ ] **Must-support capabilities are captured, not dropped.** §1 lists every job from `{must_support_capabilities}` as an outcome (not a UI mechanic), OR the subsection is omitted because the surface genuinely has none beyond the primary goals. A redesign-scope brief especially must not silently shed a capability the current screen has — the blank-canvas mandate strips the *arrangement*, never the *job* (step-01 §4). If a capability could not be expressed without naming current UI, it is still listed as an outcome, not discarded.
- [ ] **Ingest / entry-point not dropped.** Cross-check the step-01 ingest audit: for each entity type the feature displays, was the source of new records captured? If a production page-level affordance seeds the pipeline (upload, import, manual-create), it appears as a capability in §1 (outcome, not mechanic) AND as a mutation in §2 API Surface. A brief that enables browsing records but omits their creation path is incomplete — and this gap survives "capabilities not dropped" scans because the capability was never added to `{must_support_capabilities}`, not removed from it.
- [ ] **Every current-surface action is accounted for (mutation-derivation audit).** For a redesign, cross-check step-01 §3's mutation-derivation audit: every server action the current surface's components invoke resolves to EITHER a `{must_support_capabilities}` / primary-goal entry (carried forward) OR a `{dropped_capabilities}` entry with a reason. No action is unaccounted for. This is the audit that catches mutations on *existing* records (resolve / remap / override / re-run / reprice) — the subclass the ingest audit and the recall-based capability list both miss (the EOS batch-detail EAN→ASIN remap loss). When `{dropped_capabilities}` is non-empty, the brief's §1 "Deliberately not carried forward" subsection renders it, and step-03 §5 surfaces it to the user as a vetoable decision.
- [ ] **Surface topology captured.** `{surface_topology_verdict}` is set from step-01 §5d. When not `single-page-appropriate`, §4c is present in the brief and describes the recommended topology correctly — which job each surface owns, whether related routes already exist, and whether a sub-brief is pending. When `single-page-appropriate`, §4c is omitted entirely — no heading, no placeholder text. In non-autonomous mode, the topology recommendation was surfaced to the user before the brief was written.
- [ ] **Detail composition fit was checked (not assumed).** For `page_mode: detail`, `composition_provenance` reflects the §5a interaction-verb question: `policy-default` for data-entry / passive-review surfaces, `recommended-alt` (source-co-present verification layout) when the verb is verification-against-a-source. A verify-against-source detail surface left at `policy-default` is the miss this check exists to catch.
- [ ] **File paths are correct** and relative to repo root.

### 4. Write the Brief

Write the file to `{output_path}`.

### 5. Present to User

Show:
1. Where the file was written
2. A 3-line summary
3. **Dropped-capabilities disclosure (MANDATORY when `{dropped_capabilities}` is non-empty).** If this redesign deliberately drops or relocates any capability the current surface had, you MUST enumerate them here at the end of the run — never let a drop be silent. Emit:

   ```
   ⚠️ Capabilities NOT carried into this brief ({N}) — confirm these should be dropped, or re-run to include them:
     - {capability} — {reason: relocated to <sibling surface> | obsolete | out-of-scope-by-design}
     ...
   ```

   If `{dropped_capabilities}` is empty, state one line: "All capabilities the current surface exposes are carried forward — no drops." This disclosure is the *output* half of the anti-silent-drop contract (the *log* half is `{dropped_capabilities}` + the brief's §1 subsection); the drop must reach the user's eyes at hand-off, not just sit in a state variable.
4. Copy-paste prompt for Claude Design:

> **To hand off to Claude Design:**
>
> "Connect to **{github_repo_url}** and read `{output_path_relative_to_repo_root}` on `main`. This is a design brief for {feature_name}. Design the UI following the brief exactly."
>
> {If external, append: "Apply the {design_system_name} design system — ignore CSS tokens in the repo's style files."}

If `{has_analytics_band}` is `true`, add one line: "An analytics presentation rationale (the reasoning behind the page-mode, band, and archetype choices) will be written alongside this brief and delivered with it." Do NOT inline that reasoning into the brief or this summary — it lives in the rationale artifact.

### 6. Next Step

- **If `{has_analytics_band}` is `true`:** load and follow `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03b-emit-rationale.md` to write the analytics presentation rationale, THEN proceed to step-04.
- **If `{has_analytics_band}` is `false`:** skip step-03b entirely and proceed directly to step-04 (deliver).

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
