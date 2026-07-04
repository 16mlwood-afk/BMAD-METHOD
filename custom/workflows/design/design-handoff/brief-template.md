<!--
  Canonical design-brief template — rendered by steps/step-03-generate-brief.md §2.
  Extracted from the inline step on 2026-06-10 to shrink the step to its procedural
  shell (the digestibility fix from orchestration-tuning-2026-06-10-design-lane).
  Behaviour is unchanged: this is the same template text, verbatim.

  How to render:
  - Substitute every {variable}; honour the conditional {if …} / {for …} blocks.
  - Section order is intentional (purpose → data → user → visual → constraints → ask).
  - Block A/B provenance fields are decided in step-03 §1/§1a/§1b and
    shared/brief-revision-policy.md §2.
  - Quoted policy/brand-identity text is VERBATIM — no carve-outs, softenings, or
    parentheticals the policy lacks (SOURCE-OF-TRUTH PRECEDENCE, workflow.md).
  The brief's own YAML frontmatter begins at the first --- below.
  (The template is wrapped in a ````markdown fence — it is a literal to render,
  exactly as it was inside step-03 before extraction.)
-->

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
surface_class: {surface_class}           # page | chrome (absent ⇒ page). chrome = app-shell (nav/top-bar/sidebar/shell): page_mode is n/a and the composition/band lines below are OMITTED ENTIRELY — see brief-revision-policy.md Block B surface_class row
page_mode: {page_mode}                   # operational | analytical | detail — or n/a iff surface_class: chrome
route: {route}                           # primary route this brief targets (chrome: the shell's scope anchor, normally "/")
surface_part: {surface_part}             # sub-surface within route — a tab/section/panel inside the page (kebab, e.g. raw-records); "" when this brief IS the route's whole primary surface. With route (normalised) + mode it forms the surface identity that keys the active-uniqueness invariant (brief-revision-policy.md §2.6). §13 lookup drawers are NOT surfaces — never give them a surface_part.
{# When surface_class == chrome: OMIT the composition_provenance, composition, and band_provenance lines entirely (absent by design — policy invariant 1a). #}
composition_provenance: {composition_provenance}   # policy-default | recommended-alt (decided in §5a; recommended-alt names a job-fit composition in §4a and was veto-surfaced)
composition: {composition}               # machine-readable composition key the design-implement bundle→implement conformance gate (step-01 §SHARED.1b) diffs against. Default = the page_mode default (operational→worklist | analytical→chart-led | detail→record-view). When composition_provenance is recommended-alt, set the named job-fit composition from §4a as a kebab key (e.g. scanner-terminal, single-item-stream, source-co-present). A NON-default composition (e.g. a clerk scan station) is the signal that the gate must verify the bundle expresses the JOB LOOP (scan→feedback→tally→close), not a centered hero card.
band_provenance: {band_provenance}       # inherited | recommended-new | recommended-drop | none
{# analytics_archetype is REQUIRED iff band_provenance ∈ {inherited, recommended-new}; omit the line entirely otherwise. #}
{if has_analytics_band}
analytics_archetype: {analytics_archetype}   # trend | distribution | composition | ranking | coverage | flow | waterfall | single-metric | correlation
{endif}
{# shell_role is the page-shell & role contract. REQUIRED whenever the app has more than one role/shell (e.g. clerk vs owner); OMIT the whole block for a single-role app where every surface shares one shell. forbidden_chrome is the load-bearing field — design-implement enforces it (step-01 §SHARED.1b refuses; step-02 §1a / step-03 §2d emit the Tier-1 row). #}
{if has_shell_role}
shell_role:
  required_shell: {required_shell}       # the layout / route-group the surface MUST render under (e.g. clerk | owner | authenticated). Verbatim where the design draws it.
  required_chrome: {required_chrome}     # the chrome this surface MUST carry (e.g. "clerk header — 'Bison Management / Receiving — receive station' + role chip 'Clerk'"). Reproduce verbatim on the rendered frame.
  forbidden_chrome: {forbidden_chrome}   # chrome that MUST NOT appear on this surface (e.g. owner global nav, financial/approvals views). An ancestor layout injecting any of these OVER this surface is a Tier-1 shell violation — the owner-nav-on-a-clerk-station case.
{endif}
frames: {frames_list}                    # machine-readable list of the §7 Surface Inventory contract-key ids (e.g. [receive-station, active-session-workspace, resume-rail, close-reconcile-summary, resolved-unit-expand, matched-shipment-lookup]). The bundle→implement conformance gate diffs the bundle's DRAWN frames against THIS list; the §7 table stays the human-readable detail. Keep the two in sync — identical ids. NEVER empty: at minimum the primary frame.
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

> **Repository:** **{github_repo_url}** (branch: `main`). Connect to THIS repository: Claude Design reads THIS brief from the repo **by the path below** (do NOT paste the brief body into a chat) and reads the files it references. Terminal-native alternative: `design-synthesize` reads this brief locally with no Claude Design round-trip.
>
> **This brief:** `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
>
> **Revision provenance** follows `brief-revision-policy.md` in the shared design workflow docs. Consumers (design-artifact-loop, design-synthesize) validate the provenance frontmatter at intake; do not hand-edit this brief into a scope or intent change — re-run `design-handoff` instead.
>
> **Repo read protocol (the bias filter — obey exactly):** this brief deliberately omits the current layout; **the repo does NOT** — it contains the current UI's implementation. {If feature_scope == "redesign": Read ONLY the files named in §8. The current view's markup/component files are listed there as **DO-NOT-READ** — opening one to "understand the feature" anchors you to the exact layout this brief withholds, and the failure mode is invisible (a re-skin renders as confidently as a fresh design). Everything the design needs is in this brief; if something is missing, that is a brief defect — say so rather than reading the view.}{If feature_scope == "new": there is no existing screen for this surface, so repo reading cannot anchor you — read the brief and the files it names, then design fresh.} This is distinct from Claude Design **system setup** (`onboard-design-system`), where the live repo / current screens must NEVER be the seed.

This brief was generated from the codebase after implementation. It intentionally omits the current layout — you have full creative freedom to design from the data, purpose, and constraints below.

**Scope:** {feature_scope — "new" = design from scratch, "redesign" = rethink existing}

---

## Design Contract for Claude — compile and obey

> This is the machine-readable spine. §§1–8 below are the *why* (rich context); this block is the *what you must produce and preserve*. If a design contradicts any field here it is wrong — revise before you consider it done.
>
> These constraints are enforced downstream by `design-review-pr` (a hard gate) and the `design-implement` bundle→implement conformance gate — not by good intentions.

```
  page_mode:   {page_mode}                 # operational | analytical | detail — n/a iff surface_class: chrome (then the composition line is omitted)
  composition: {composition}               # {if composition_provenance == "recommended-alt"}job-fit composition — NOT the page_mode default{else}page_mode default composition{endif}
  shell:       {if has_shell_role}{required_shell} — render under this shell; the forbidden chrome in §5 MUST NOT appear over this surface{else}single shell — every surface shares one app shell{endif}
  route:       {route}
  frames:      {frames_list}               # every id is a REQUIRED rendered frame (§7)
  mutations:   {mutation_posture}          # none (read-only) | the server actions this surface MUST keep
  money:       {money_posture}             # none | the money figures this surface carries (basis-complete per policy §15)
  list_rendering: {list_rendering_verdict} # single-render | paginate | virtualize | load-more (§5g). NOT single-render ⇒ the mechanism is REQUIRED on the primary list frame (design-implement step-03 List-rendering row enforces it)
  width:       1280px desktop
```

**MUST PRESERVE — the object (changing any of these fails review):**
- Every id in `frames` is a rendered frame. An un-drawn frame is inferred downstream and ships thin.
{if has_shell_role}- Render under the `{required_shell}` shell; the chrome named in `forbidden_chrome` (§5) MUST NOT appear over this surface.
{endif}{if linked_records_inventory is non-empty}- §2a expand-in-context (§13): acting on a linked reference opens the foreign record's OWN fields in a drawer *over* this surface — never inert duplicated text, never a navigate-away, never a loud button/CTA/pill/chip. "Open full {sibling} →" is a quiet secondary action only.
{endif}{if is_live_process_surface}- §2c runtime contract: every lifecycle state has its state-variant frame drawn (`{primary}--{state}` ids in `frames`); the design's liveness claims stay inside the §2c staleness budget; every §2c control verb is reachable in the states where it is legal.
{endif}- The §5 hard-failure list holds — a design tripping any §5 item is rejected — and status stays inside the §4 colour system (the product accent is interaction-only, never a status).
{for inv in {contract_must_preserve}}- {inv}
{endfor}

**FREE TO CHANGE — the design freedom (yours):**
- Information architecture, layout, grouping, and visual hierarchy.
- How summaries, roll-ups, durations, and derived figures are computed and presented.
- Table vs grouped presentation; column order; sort defaults beyond any required default order.
- Drawer field grouping and the record-header composition.
{for free in {contract_free_to_change}}- {free}
{endfor}

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

**List rendering (§5g):** {if list_rendering_verdict and list_rendering_verdict != "single-render"}**{list_rendering_verdict}** is REQUIRED on the primary list frame — {list_rendering_rationale}. The design MUST include it (page controls + count / windowed rows / load-more); a single un-paginated render of a growing list is a gap, not a simplification.{else}{if list_rendering_verdict == "single-render"}single-render — {list_rendering_rationale} (a hard ceiling justifies rendering all rows).{else}n/a — not a list surface.{endif}{endif}

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

## 2a. Linked records & lookups

{Render this section ONLY when `{linked_records_inventory}` is non-empty. Omit entirely — no heading, no placeholder — for a true leaf surface that references no record owned by another surface.}

Project design-policy **§13 (linked records & lookups) is a functional mandate, not a suggestion** — and `design-review-pr` enforces it as a hard failure. Every value below IS a record owned by another surface; on this design it must **resolve and expand that foreign record in context**, not inert duplicated text and **not a link that navigates away**. The §13 function is **expand-in-context, not navigate-away**: acting on the reference opens the foreign record in the §7 right-side drawer *over* this surface — showing that record's own fields and its own linked references (recursive) — with related fields surfaced as lookups read *through* the relation. The operator never loses their place; closing the drawer returns them where they were. "Open full {sibling} page →" is a **secondary** action inside the expanded record, never the click's default. **Form stays ours, not Airtable's:** the affordance is the quiet §4 link + the §7 drawer — never a button, CTA, colored pill, chip, grid, or Airtable modal chrome. "Airtable-style" means the **relation** (expand the foreign record in place; carry its fields as lookups), never Airtable's *form*.

| Foreign reference | Owns it (surface · route) | Expand-in-context target (§7 drawer, NOT navigate-away) | Inline lookups (read-only, read through the relation) |
|---|---|---|---|
| {identifier as shown} | {sibling surface · `/route`} | {acting on it → the {foreign record} expands in the §7 drawer over this surface, its own fields shown; "Open full {sibling} →" secondary inside it} | {related fields pulled through the relation, or "—"} |

{One row per entry in `{linked_records_inventory}`.}

**Richness floor — the lookup drawer is a designed surface, not a stub.** Each reference above opens its foreign record as a **frame in the §7 Surface Inventory** (a `{record}-lookup` drawer). That frame must show the fields the relation actually needs — a `warehouse` opened from an order shows code/type/status/location AND what is routed through it for this order; a `catalog` record opened from an order line shows its image/title AND the market/economics the line depends on. The "Inline lookups" column above is that field set; `—` is permitted **only** when the foreign record genuinely carries nothing past identity. A lookup drawer that renders identity alone (code/type/status) when the record has decision-relevant fields is the silent thinness this floor exists to kill — and `design-implement` §2f will flag the frame if it was never drawn at all.

**Required behavior (review-test, §13):** for each reference above — same identifier / same format as on the owning surface; **it expands the foreign record in context** — acting on it opens that record in the §7 drawer *over this surface* (its own fields and its own links shown, not a re-keyed summary and not a navigation away), with a round-trip back; any inline field shown is a *resolved lookup* read through the relation, **never re-keyed** per surface. Inert duplicated text for a record that exists elsewhere — and a link whose only behavior is to navigate to the sibling page — are the anti-patterns this section exists to kill. Expand-in-context via the §7 drawer is the default; the design may choose a different quiet affordance, but acting on the value must **resolve and surface the foreign record's own fields in place**, with the full sibling page only ever a secondary action.

---

{if {is_finance_surface}}
## 2b. Finance semantics & accounting truth

*This surface is finance-shaped ({finance_report_type}). The semantics below MUST survive the
blank-canvas redesign — they describe meaning the design must preserve, never how to lay it out.*

**Column semantics (what each value means):**
{for s in {finance_column_semantics}}
- `{s.column}` — {s.group} · {s.meaning}
{endfor}
Quantities and monetary values are distinct concepts — never present them blended in one field.

**Exception states the design must be able to represent** (somewhere in the journey — these are
outcomes, not a prescribed panel):
{for e in {finance_exception_expectations}}
- {e}
{endfor}

**Accounting-truth constraints (must NOT be inferred):**
{for m in {finance_must_not_infer}}
- {m}
{endfor}

**Open questions — unresolved definitions (do NOT guess these; surface them in the user's journey
or as workflow questions):**
{for u in {finance_unresolved_assumptions}}
- {u}
{endfor}

**Terminology — use consistently:** {finance_terminology}

---
{endif}

{if {is_live_process_surface}}
## 2c. Runtime behavior contract

*This surface's primary job is watching/controlling a **long-running in-flight process**. The temporal
semantics below MUST survive the blank-canvas redesign — they describe what changes over time and what
the operator can do about it, never how to lay it out. Each lifecycle state below is a required
state-variant frame in §7 (the film-strip): a state this brief names but the design never draws ships
un-designed.*

**Run lifecycle (from the implementation's own state machine — design every state):**

| State | What is true in it | Operator's question | Legal control verbs |
|---|---|---|---|
| {state} | {what the process is doing / has done} | {e.g. "is it still working?", "what failed?"} | {pause / resume / cancel / retry / none} |

{One row per lifecycle state in `{runtime_behavior_contract}`. Transitions and triggers as a short plain-English list below the table.}

**Per-item states (including every failure/partial lane):** {per-item states — throttled, held, load-error, retrying, skipped, missing-at-source, … Partial failure is the normal case, not an edge case; the design must make "done with exceptions" distinguishable from "done clean" at a glance.}

**Update transport & staleness (honesty constraint):** {how the surface learns of change — pushed message / storage listener / poll — and its cadence. The design may only promise the liveness this transport delivers: if the display can be N seconds stale, the design must not present itself as real-time. State the staleness budget explicitly.}

**Control verbs (outcomes, with real semantics):** {each verb the operator has over a run in flight, with what it actually does — e.g. "stop the run without losing completed work (cancel drains in-flight items)", "resume a paused run from where it stopped". Never buttons — jobs.}

**Progress signals available (derive from these — presentation is the design's):** {the raw signals — counts by state, per-item/per-marketplace telemetry, timing data, run-report/history data. No progress-bar, spinner, or log-panel prescription here.}

**Open questions — unresolved runtime semantics (do NOT guess these):**
{the unresolved entries from `{runtime_behavior_contract}` — e.g. what cancel does to in-flight items, whether a run is resumable. Omit the block when none.}

---
{endif}

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

- **Lead pass — the form that answers the question fastest:** {the archetype's form, made concrete for this feature. For `coverage`: a completeness strip where the gaps are the content. For `ranking`: a sorted top-N bar list capped and labelled. For `composition`: a single 100%-bar. For `flow`: a funnel/stage strip with drop deltas. For `waterfall`: an anchored opening bar, signed labelled steps, an anchored closing bar — deltas reconcile to the close, reasons live in the step's drill (not a duplicate chip). For `single-metric`: one value + sparkline + threshold. For `trend`: small-multiples with a stated Y-axis rule — **and for a two-magnitude trend (a realised primary like committed/actual/spent plus a subordinate projection like provisional/forecast/pipeline/budget), a solid primary line/area + a ghosted/dashed subordinate reference band, never stacked and never two co-equal lines, with rounded axis ticks and exact figures in the drill (not per-bar labels).** State dimensions, ordering, and what is emphasised.}
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
- {from `{archetype_prohibited}` — archetype-specific, e.g. for trend: "no single multi-series line chart; each series its own small multiple; **no stacked columns — absolute for a trend, including a committed+provisional stack (do NOT soften this to 'unless it is the composition'); no per-bar value labels standing in for an axis; a two-magnitude actuals-vs-forecast trend stays distinct (solid primary + ghosted subordinate), never collapsed to one series nor inflated to two co-equal lines.**" For composition: "no pie/donut; no time-stacked bars." For coverage: "'all good' must not look identical to 'gaps present' at a glance." For ranking: "do not render all N — cap and label the cut."}

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

### Surface Inventory — render every frame below (required, not optional)

This page spawns secondary surfaces at runtime — the detail drawer the operator drills into, and the §13 expand-in-context lookup drawers (§2a) that open over it. **Every row below is a REQUIRED rendered frame, not an optional extra.** This pipeline is non-interpretive: `design-implement` pixel-matches only the frames you draw — a drawer you leave un-rendered is *inferred* downstream, which ships it thin and unformalised (bare `€60` money with no GBP/VAT basis — a `docs/design-policy.md` §15 violation; a lookup drawer showing only code/type/status). **If you want it built well, draw it.** The **Frame** name is the contract key — keep it verbatim on the rendered frame so `design-implement` matches by name with zero inference.

| Frame | Opens from / trigger | Render as | Must contain | Figures (§4d) | Lookups (§2a, depth-1) |
|---|---|---|---|---|---|
| {frame_name} | {trigger} | {full-bleed \| drawer-over-{parent}} | {must_contain} | {the §4d decision numbers this frame carries, basis-complete per policy §15 — or "—"} | {depth-1 §2a fields — or "—"} |

{One row per entry in `{spawned_surfaces}`. The primary surface is always row 1; the drilled detail drawer is a row when the §5a composition spawns one; each `{linked_records_inventory}` entry is one lookup-drawer row.}

**Rules for the inventory:**
- **No bare stubs.** A lookup-drawer frame's "Must contain" must name the fields the relation actually needs (a `warehouse-lookup` opened from an order shows code/type/status/location AND what's routed through it for this order), never identity alone. If the record genuinely carries nothing past identity, state that explicitly.
- **Depth-1 only.** A lookup drawer lists its own immediate lookups; the foreign record's own §2a owns the next level. Do not inline the recursive order→catalog→supplier graph.
- **Money is basis-complete.** Every figure in a "Figures" cell follows `docs/design-policy.md` §15 — VAT basis, native currency framed against GBP, no decontextualised fragment; rendered as the detail surface, not a bare-number dump.
- **Entry point — how the operator REACHES this surface (the primary frame's "Opens from / trigger" is a contract, not a note).** The first row's "Opens from / trigger" cell must state how the operator gets to THIS surface from the rest of the app — a global-nav entry, a link from a *named* parent surface, or a row-drill from a *named* worklist — so `design-implement` can VERIFY the ingress was actually wired (its step-04 flags an "unlinked island" when a built surface is reachable only by URL — the §L recovery-cross-check miss). **A sub-surface is NOT a nav peer:** a detail / drawer / record-view / §13 sub-surface is reached by a link or row-drill from its parent, **never** a global-nav entry (that is nav-bloat and misrepresents it as a sibling page). A top-level operational/analytical *page* is the only kind that earns a global-nav entry.

### Per-frame outputs

For **every** frame in the Surface Inventory above, deliver:

1. **Visual designs** at desktop width (1280px) — including each drawer rendered **open over its parent frame**, not as a standalone page.
2. **Component specs** for new UI patterns
3. **Interaction notes** — hover states, transitions, empty states, loading states; for drawers, the open/close/return-up-the-stack behaviour (§13 round-trip)
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

{If feature_scope == "redesign", add this block after the file table (and after the token-values warning when present) — it is the enforcement half of the "Repo read protocol" in the preamble:

🚫 **DO-NOT-READ — current view implementation.** The files below render the CURRENT layout of this surface. Reading any of them defeats this brief's blank-canvas premise (structure, grouping, and control order will anchor you even if you only meant to check a detail). They are listed so the boundary is explicit, not discoverable by accident:
{For each entry in `{do_not_read_files}` (gathered in step-01 §3), one line:}
- `{file path}` — {what it renders, e.g. "the current view markup" / "current state→DOM rendering"}

If a fact you need lives only in a DO-NOT-READ file, STOP and report the gap as a brief defect — the fix is a brief revision, never reading the view.}

---

## Changelog

Minor revisions (clarifications only — see `brief-revision-policy.md` §1) append one line here. Material revisions re-run `design-handoff` instead; they do NOT append to this changelog — they live in a new brief file.

{If change_class is "material_revision", the first changelog entry below records the supersession; otherwise this section starts empty and is populated by future hand-edits.}

- {date} — {if change_class == "material_revision": "Material revision; supersedes `{supersedes_filename}`. Author: design-handoff workflow."; if change_class == "original": leave the bullet OUT entirely and the section will be empty until a clarification is added.}
````
