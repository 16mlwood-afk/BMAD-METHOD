---
name: 'step-01-gather'
description: 'Gather feature purpose, data model, API surface, and user context — without capturing current layout or component structure'
---

# Step 1: Gather Feature Context (Bias-Free)

**Goal:** Extract the raw materials a designer needs — data model, user purpose, API surface, constraints — without describing the current UI's layout, information grouping, or visual hierarchy.

---

## RULES

- **NEVER describe the current page layout, component structure, or information grouping.** The current UI was built by a developer. Describing it anchors the designer to implementation choices.
- Read component files ONLY to extract data types, API calls, and route paths — NOT to summarize what sections the page shows.
- Focus on WHAT DATA is available and WHO needs it — not HOW it is currently presented.
- Present all data fields neutrally. Do NOT rank fields as "prominent" or "secondary."
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## EXECUTION SEQUENCE

### 1. Resolve Repository URL

Capture `{github_repo_url}`:

```bash
git remote get-url origin
```

Convert SSH URLs to HTTPS. Strip trailing `.git`.

### 1b. Load Project Design Policy

Check both possible locations for a project-level design system declaration. `docs/design-policy.md` is the canonical location; `planning-artifacts/brand-identity.md` is the legacy slot. Prefer the first if both exist.

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

**If either is found:**
- Read the entire file → `{brand_identity}` (variable name retained for backward compatibility)
- Set `{brand_identity_path}` to the absolute path of whichever file was loaded
- Set `{design_system}` = "branded"
- Parse the frontmatter `version:` field of the loaded file → `{policy_version}` (integer). If no version field exists, default to `1`. This value is stamped into the generated brief's `policy_version_required` field in step-03 so downstream consumers can detect when the policy has moved past the brief's pinned version.

**If neither is found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty
- Set `{design_system}` = "existing" (may be overridden to "external" by user input)
- Set `{policy_version}` = `0` (sentinel meaning "no policy in effect at brief time"; downstream consumers treat this as "no drift check possible — surface to user").

### 2. Identify the Feature

Determine `{feature_name}` and `{feature_scope}` from user input or recent git history:

```bash
git log --oneline -10
git diff --name-only HEAD~3..HEAD
```

Set `{feature_scope}`:
- **"new"** — component file was created (not modified) in recent commits
- **"redesign"** — component exists and user wants it redesigned

### 3. Map the Data Surface

**Route:**
- What URL path does this feature live at?
- Note the route path — NOT the component that renders at it

**Data Model — Procedural Capture (anti-bias):**

Follow these steps in order. The goal is to capture domain entities from the source of truth (DB schema), not from the page server's UI-shaped response.

1. **Open the DB schema** at the project's source of truth. Common locations: `src/lib/server/db/schema.ts` (Drizzle), `prisma/schema.prisma` (Prisma), `app/models/` (Rails), `models.py` (Django), `migrations/*.sql` (raw SQL), or equivalent. Find the tables this feature reads from.
2. **For each entity**, list its columns: name, type, nullability. These are the primitive fields.
3. **Stop. Do NOT open the page-shaped server response file to get the data shape.** Examples: `+page.server.ts` (SvelteKit), `getServerSideProps` or route `loader` (Next.js), controller action (Rails), view function (Django/Flask), GraphQL resolver, etc. These denormalize, group, pre-compute, and add rendering hints — all of which bias the designer. If you need to know which entities the feature uses, check the file's imports or queries, but do NOT copy its return type.
4. **Flatten any nested structures.** If the schema has a foreign key (e.g., `supplier_country` on an invoice), that's a flat field on the row — not a grouping dimension. Record it as a field.
5. **Drop anything not in the schema:**
   - Pre-computed derivations (`daysLeft`, `totalNet`, `filingProgress`, etc.) — keep only the inputs (deadline date, money amount, status enum)
   - Rendering hints (`flag`, `badgeColor`, emoji fields) — keep only the underlying data (`countryCode`, status enum)
   - UI-control enums (`'all' | 'not_filed' | 'ready'`) — "all" is a filter affordance, not data. Keep only the row-level status enum.
   - Precomputed rollups (`domesticCount`, `countryTotal`, `validCount`) — the designer decides which aggregations matter.
6. **Note which primitive fields are nullable** — these need empty-state treatment.

Capture `{data_shape}` in **domain-entity table form** (see step-03 template). If you find yourself copy-pasting `interface PageData { ... }`, you've gone off track.

**API Surface:**
- What endpoints does the frontend call? → `{api_surface}`
- What does each response look like? (reference the data shape)
- What mutations are available? (POST/PUT/DELETE endpoints)
- **Ingest / entry-point audit:** For each entity type the feature displays, ask: *how does a new record enter the system?* Is there an upload, import, manual-create, webhook, or scraper that populates it? A production page-level affordance that seeds the pipeline (e.g. a "Upload wholesale price list" button) is a **capability**, not just a technical endpoint — capture it in `{must_support_capabilities}` (as an outcome) AND in `{api_surface}` (as the mutation). Miss it and the redesign can browse records but never create them. This is the most common single-capability loss in redesign-scope briefs.
- **Mutation-derivation audit (anti-recall — DERIVE capabilities, don't remember them):** The data shape is *derived* from the schema (above), so no field can be silently missed. Capabilities must be derived the **same mechanical way**, not recalled — recall is where they leak. For a **redesign**, `grep` the *current* surface's implementing component files for every server action / mutation they import and call (this reads the **verbs the screen exposes**, NOT its layout — so it stays inside the anti-bias rule; you are cataloguing what the operator can *do*, never how it's arranged). Then account for **every** action found — each must resolve to exactly one of:
  - a **primary user goal** or a **`{must_support_capabilities}`** entry — the capability is carried forward (name it as an outcome), OR
  - a **deliberate drop** — recorded in `{dropped_capabilities}` as `{ capability (outcome phrasing) · backing_action · reason }`, where `reason` is one of: `relocated` (to a named sibling surface), `obsolete`, or `out-of-scope-by-design`.
  No action may be left unaccounted for. The **ingest audit** above catches mutations that *create* records; **this** audit catches mutations on *existing* records — resolve / remap / override / re-run / reprice / reconcile / approve / dismiss — the subclass a blank-canvas redesign sheds most easily because each is neither a primary goal nor an entry-point, and the anti-bias rule discourages the very UI-reading that would surface it. An action that lands in **neither** bucket is the silent capability loss this audit exists to make impossible (the EAN→ASIN remap dropped from the EOS batch-detail redesign — `overrideWholesaleAsinAction` left with zero callers — is the canonical case). For a **new** feature there is no current surface to grep, so this audit reduces to the ingest audit alone.

**Implementation Files:**
- List relevant file paths → `{implementation_files}`
- Include: type definitions, API route handlers, the main page component path, CSS/style files
- These are for technical reference, NOT layout reference

### 3a. Linked-records inventory — every on-screen value that IS a foreign record

Project design-policy **§13 (Cross-surface relational coherence — linked records & lookups)** is a **contract-critical §12 assertion that `design-review-pr` enforces as a hard failure**: any on-screen value that IS a record *owned by another surface* (ASIN, SKU, order number, batch, shipment, supplier, customs entry, listing, …) must be a **navigable lookup/link** to that record — never inert duplicated text. Because this brief withholds the current layout (blank canvas), the one place that linking was visible is gone; if the brief is silent on it, the redesign defaults to inert text and **fails review on the way back in**. So derive the inventory here — mechanically, the same anti-recall way as the data surface (§3) and the mutation audit — never leave it for the designer to rediscover.

**Derive (don't recall).** From the `{data_shape}` and route just mapped, for **each** field that resolves to a record another surface owns (start from the foreign keys / natural keys flattened in §3 step 4 — `supplier`, `asin`, `order_number`, `batch_id`, …):
1. **Foreign reference** — the field/identifier as it appears on this surface.
2. **Owning surface** — which surface owns that record, and its route (`/suppliers/[id]`, `/catalog/[asin]`, …). If no surface owns it yet, say so — it is a plain value, not a link, and does not belong in the inventory.
3. **Drill target** — the §13 default is row/value → right-side **detail drawer** (§7) for the in-context record, **plus** an explicit "Open full {sibling} →" cross-link to the owning surface. Name both.
4. **Inline lookups** — any *related field* this surface needs from that foreign record to make its decision (a supplier's lead-time, a catalog product's image/title on an order line, an order's marketplace/currency on a batch). These render as **read-only** lookups resolved from the canonical record — never re-keyed per surface.

Set `{linked_records_inventory}` — one entry per foreign reference, each with the four facts above. **Empty only when nothing on the surface resolves to a foreign record** (a true leaf surface); empty-by-omission is the silent failure this step exists to prevent — the §13 mandate is invisible to the designer unless this inventory carries it into the brief. The §13 *quiet-styling* guardrail (the link is the demoted blue accent / hover underline, **never** a button, CTA, or colored pill) travels with the inventory into brief §2a — function imported, not Airtable's form.

### 4. Capture Feature Purpose

Write `{feature_purpose}`:

```
Feature: {feature_name}
Route: /path
Scope: new | redesign
Purpose: [1-2 sentences: what problem does this solve for the user?]
Data source: GET /api/endpoint → domain entities (see {data_shape})
User goals: [domain outcomes, NOT UI clicks.
  GOOD: "spot countries near deadline", "answer 'what's blocking filing today?'"
  BAD:  "click bulk-mark filed", "switch the active quarter"]
Must-support capabilities: [the jobs the operator must be able to ACCOMPLISH on this
  surface beyond the primary goals above — as outcomes, NOT UI mechanics. These are
  requirements the design must satisfy even though this brief withholds the current
  layout; name the secondary capabilities a blank-canvas redesign most easily drops.
  Set `{must_support_capabilities}` (empty only if there genuinely are none).
  GOOD: "attach the source receipt to the order", "verify each AI-extracted field
        against the source it came from", "bypass staging review for a trusted record"
  BAD:  "drag-drop zone in the right rail", "a skip-staging checkbox", "a two-pane split"]
Data volume: [typical count — "usually 10-50 items", "1,400+ records per quarter"]
```

Do NOT include "Main component", "Child components", "Current sections", "Current tabs", or "Key interactions." Do NOT phrase user goals or capabilities as UI actions. **The line between a forbidden interaction and a required capability is the arrangement, not the verb:** strip *how the current UI does it* (the control, the layout, the mechanic — "a skip-staging checkbox in the toolbar"), but keep *what the operator must be able to accomplish* (the job — "bypass staging for a trusted record"). The blank-canvas mandate forbids inheriting the *arrangement*; it does not license dropping a *capability*. A capability the brief never names is silently dropped from the redesign — the design tool cannot reinstate what it was never told to support, which is exactly how a redesign comes back "more basic" than the screen it replaced.

### 5. Determine Page Mode

Set `{page_mode}` based on the feature's **dominant user task**:

- **"operational"** — the user processes, reviews, approves, reconciles, files, or resolves records. The page is a worklist. The design should prioritize throughput, scanability, and status visibility. Most pages are operational.
- **"analytical"** — the user discovers trends, compares segments, diagnoses anomalies, explains changes, or moves from summary insight to supporting evidence. The page is an analysis tool.
- **"detail"** — the user reads or edits the fields of **one record**. The page is a drawer or full-page extension of an operational list (the thing you reach by drilling INTO a worklist row), not a queue and not an analysis tool. The design should prioritize legible single-record layout, field grouping, and inline edit/action affordances. Composition is neither table-first nor chart-led — it is a record view. (Per project policy §6/§7: "a drawer or full-page extension of an operational list, never a re-skin.")

**Signals for analytical:** user goals center on "understand", "compare", "spot trends", "review performance", "analyze", "diagnose", or the data has time-series dimensions and the user's job is pattern discovery rather than row processing.

**Signals for detail:** the route is single-entity (ends in `/[id]`, `/[slug]`, a record drawer), the primary surface is ONE record's fields rather than a multi-row table, and the page is reached by drilling from a worklist. A detail page almost never carries an analytics band — a single record has no aggregate dimension (§5b will resolve `band_provenance: none`).

**Hybrid handling:** Some pages mix modes.
- If analysis exists to support immediate row-level action (e.g., a summary chart above a worklist), keep the page in **operational** mode.
- If row-level detail exists mainly to verify or explain summarized behavior (e.g., a trend chart with a drill-down table), keep the page in **analytical** mode.
- A page that contains a worklist AND a per-row detail surface is **operational** — `detail` is for a page whose dominant (often only) job is the single record.
- The dominant user task determines the mode — not the presence of a chart or a table.

If unclear, default to "operational." These three values are the full `page_mode` enum the whole brief contract uses (`brief-revision-policy.md` Block B; consumed by `design-synthesize` / `design-implement`) — emit one of them, never a fourth.

**Capture the reasoning (not just the label).** Set `{page_mode_rationale}` to the concrete signal that selected the mode — the user-goal phrasing or data property that decided it (e.g. "user goal is 'spot which week slipped' → pattern discovery, not row processing"). This is recorded verbatim in the analytics rationale artifact (step-03b) when a band exists; capturing it now means the deliberation is not thrown away once the mode label is set. (Skip the capture only when `{has_analytics_band}` resolves to `false` below — no rationale artifact is emitted then.)

### 5a. Composition Fit Check — does the page-mode's default composition fit THIS surface?

Page mode (§5) names the *kind of work*; the project design policy attaches a **default composition** to each mode (operational → table-first worklist + right-side detail drawer; analytical → chart-led; detail → record-view). That default is a sensible starting point, **not** a certification that this surface's job fits it. Stamping it in unquestioned is the policy-default bias (see workflow.md Anti-Bias Principle II) — as real as inheriting the legacy layout, and harder to see because it feels like "just following the system."

So decide the **primary composition** the same way §5b decides the band: by the **job**, not by the policy default and not by the legacy render. Answer three questions about the feature:

1. **Selection model** — does the operator *choose the next item by scanning* a list (a worklist's core competency), or is the work *dispensed / pull-based* (the system hands them the next item — a queue, an inbox, a "next task")? If the work is dispensed, a table's scan-to-select competency is dead weight.
2. **Per-item cost** — is the dominant cost *scanning many rows* (favours a table), or a *decision / comparison on one item* that needs width — image, candidates, evidence side-by-side (which a ~400px right-side drawer physically cannot hold at legible size)?
3. **Dominant loop** — does the operator live *in the list* (scan → pick → glance → next), or *in one item at a time* (read → decide → advance)? A one-item loop is served by a focused full-surface composition, not list + drawer.

The three questions above decide list-bearing modes. **For `detail` mode there is no list to select from — the operator is already inside one record — so the fit turns on the record's *interaction verb*, not list-vs-item.** Ask one more question:

4. **Interaction verb (`detail` mode)** — is the record surface's job (a) **data entry** (create / fill a new record), (b) **passive review** (read or confirm an existing record's fields), or (c) **verification against a source** (confirm extracted, imported, OCR'd, or scraped field values against the originating document — an order-confirmation email, a receipt image, a customs PDF, a parsed web page)? For (a) and (b) the grouped-fields record view fits. For (c) the operator's eye must move **value ↔ source**, so the source has to be **co-present** with the fields — which a plain grouped-fields record view does not provide. A verify-against-source surface wants a **source-co-present verification layout** (extracted record and source rendered together, the source sticky), and is therefore `recommended-alt`. The in-system exemplar is the **CDS customs page** (extracted record left / source PDF right, per-line values highlighted on the document). The cost of missing this: a "capture form" that discards the source the moment it is consumed, breaking the verify loop the surface exists for.

Set `{composition_provenance}`:

- **`policy-default`** — the page-mode's default composition fits the job. The common case. (Most operational pages really are scan-to-select worklists; most detail pages really are record views.)
- **`recommended-alt`** — the answers point away from the default: the job wants a different *primary* composition than the policy attaches to this mode. This is a **net-scope / IA recommendation** — surface it to the user for veto before it lands in the brief (one line — "this surface is `{page_mode}`, but its job is {dispensed / comparison-heavy / single-item}; the policy's default {table-first / chart-led / …} doesn't fit — recommend {named composition} as the primary surface, with {the table demoted to a triage view / …}. Use it?"). Handoff recommends; it never silently overrides the policy's composition.

**`composition_provenance` does NOT change `{page_mode}`.** A pull-based mapping/resolution queue is still `operational` — it processes records — but its *composition* may be a single-item decision surface, not a worklist table. The two axes are orthogonal: `{page_mode}` = what kind of work; `{composition_provenance}` = whether the mode's default composition is the right shape for it. Keep `{page_mode}` honest (the work type) and let `{composition_provenance}` carry the composition deviation.

**Capture the reasoning.** Set `{composition_rationale}` to the three answers + the named alt composition + (for `recommended-alt`) the veto outcome (`accepted | declined | pending`), so step-03 §4a renders the override with its justification and the deviation stays auditable. If the three questions genuinely don't resolve, do not silently default — ask the user the one composition question above.

This check applies to every mode but bites differently per mode. `operational` is where the table-first default is most over-applied — questions 1 and 3 decide it. `detail` is `policy-default` for data-entry and passive-review surfaces, but `recommended-alt` when the verb is verification-against-a-source (question 4) — the source must be co-present, which the record-view default does not provide. This is the detail-mode analogue of the operational table-vs-resolve miss, and just as easy to wave through, because the bare record view *feels* like correctly following the system. `analytical` is usually chart-led, but a surface whose real job is a single ranked decision can still warrant `recommended-alt`.

### 5b. Decide Whether an Analytics Band Belongs

This is a **design judgment about the data and the user's job — not a detection of what the legacy page renders.** `design-handoff` exists to start the designer from a blank canvas; inheriting band presence/absence from the current layout is the one place that mandate matters most. A bare legacy table sitting on time-series, multi-segment data where the user's real job is "spot which one slipped" *should* get a band even though the current page has none.

So do NOT decide by inspecting the current render. Decide by answering three questions about the feature itself:

1. **Aggregate dimension** — does the data carry a dimension the rows don't expose (time, segment, category, stage, completeness)?
2. **Pattern job** — is part of the user's job pattern / comparison / anomaly / coverage work, rather than pure row-by-row processing?
3. **Changes next action** — would seeing an aggregate layer change what the user does next (which rows they open, which exception they chase)?

If the **pattern job** answer is yes, a band belongs — regardless of whether the legacy page had one.

Set `{band_provenance}` to record *why* the band exists (or doesn't), keeping the blank-canvas reasoning auditable:

- **`inherited`** — the legacy page already had an analytics surface AND the data + job still justify it.
- **`recommended-new`** — the legacy page had no band, but the three questions justify one. This is a **net-new scope recommendation**: surface it explicitly to the user for veto before it lands in the brief (one line — "this feature has no analytics surface today; the data + job warrant one of shape X — include it?"). Handoff recommends; it never silently invents scope.
- **`recommended-drop`** — the legacy page has a band, but the job is pure row-processing and the band is ornamental. Recommend removing it (also veto-surfaced).
- **`none`** — no analytics surface justified. Pure data-entry forms, single-record detail views, settings pages, list-only pages with no aggregate dimension. Section 4b is omitted entirely from the brief.

`{has_analytics_band}` = `true` iff `{band_provenance}` ∈ {`inherited`, `recommended-new`}. When `true`, section 4b (Analytics Structure) MUST be filled in step 3. When `false` (`none` or `recommended-drop`), section 4b is omitted.

`{page_mode}` = "analytical" forces `{has_analytics_band}` = `true` (an analytical page is analytics-led by definition); set `{band_provenance}` to `inherited` or `recommended-new` accordingly.

If the three questions genuinely don't resolve, do not default to a band *or* to none silently — ask the user the one band question above. A guessed band is worse than an asked one.

**Capture the reasoning.** When `{has_analytics_band}` is `true`, set `{band_decision_log}` to the three questions answered for THIS feature — each a one-liner of `yes/no + the specific dimension / job / next-action`, exactly as they'll appear in step-03b §2. If `{band_provenance}` is `recommended-new` or `recommended-drop`, also record the veto outcome (`accepted | declined | pending`) so the rationale can state that the scope recommendation was surfaced, not silently injected.

### 5c. Select the Analytics Archetype

Skip this section entirely if `{has_analytics_band}` is `false` — `{analytics_archetype}` and all the capture fields below stay empty.

When `{has_analytics_band}` is `true`, the archetype selection is delegated to the **`analytics-surface-architect` skill** — the single brain for this decision, so handoff, design-review-pr, and any human all reason the same way instead of re-deriving it. Do not hand-reason the archetype inline when the skill is available.

**Multiple analytics surfaces on one page.** A page can carry more than one distinct analytics surface — e.g. a product view with price-over-time, sales-rank, and competitor-share, which are three surfaces, not one band. When it does, run this selection **once per surface** (each gets its own captured archetype), and **§5e** then ranks them into hero / supporting / drill. For the common single-surface page, run it once exactly as written below.

**Invoke the skill (mode: `select`).** Load `analytics-surface-architect` via the Skill tool and pass it:
- the **data shape** (`{data_shape}` — the domain entities and their dimensions from §3),
- the **user's question** in their words (from `{feature_purpose}` / `{user_context}` — the single thing the band must answer),
- the **page mode** (`{page_mode}`).

The skill runs its selection procedure (start from the question, ground-or-flag, weigh candidates incl. an explicit ruling on `trend` when time is in the data, pick one dominant + at most one subordinate, map every element to a drill target) and returns its **decision object**. Capture it field-for-field — the names already match what step-03b and §4b consume:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `archetype` | `{analytics_archetype}` (one of the nine, or `unclear`) | frontmatter, §4b, rationale |
| `candidates` | `{archetype_candidates}` (chosen / secondary / rejected + why) | rationale §3 table |
| `winner_reason` | `{archetype_winner_reason}` | rationale §3 |
| `secondary` | `{archetype_secondary}` (or `none`) | rationale §3 |
| `time_present_check` | `{time_present_check}` (set iff time in data) | rationale §3 |
| `drill_map` | `{archetype_drill_map}` | §4b C, rationale §3 evidence |
| `prohibited` | `{archetype_prohibited}` | §4b E, rationale §4 |

**Ground-or-flag is preserved through the skill:** if it returns `archetype: unclear` (it could not name BOTH a data dimension and a user question), do NOT default to `trend` — ask the user the one resolving question the skill surfaced, then re-invoke. A guessed archetype is worse than an asked one.

**Fallback (skill not available).** If the `analytics-surface-architect` skill is not present in this project (e.g. an older sync), apply `shared/analytics-archetypes.md`'s selection rule directly — identical logic — and populate the same capture fields by hand: name the dominant archetype from the nine; ground-or-flag (data dimension AND user question, else `unclear` → ask); record the candidates weighed with the most-tempting rejected alternative (for time-bearing data, almost always `trend`); the winner reason; the secondary or `none`; and the time-in-data check. The skill is the preferred path because it makes the road-not-taken and the drill map mandatory outputs rather than easily-skipped prose, but handoff must not hard-fail when it is absent.

Either path populates the same state, so step-03b renders identically. `{analytics_archetype}` empty ⇒ no band.

### 5c-2. Specify the Analytics Rigor — depth, not shape

§5c picked the *shape* of the analytics band; this picks the *depth* of **every decision-bearing figure on the surface** — and depth is **not** confined to the band. A correctly-shaped band can still be schoolboy-grade (every figure a naked point estimate, nothing compared to a baseline, no connective read — *correct and useless*), and so can a **bandless decision surface**: a `detail` buy/verdict page whose hero shows `ROI 42%`, `+£840 est. net profit`, `Headroom 18%` is exactly the case — those are decision numbers in the §4a record/hero, not in any §4b band, and they are the worst schoolboy offenders.

**Gate — `{has_decision_numbers}` (broader than `{has_analytics_band}`).** Set `{has_decision_numbers}` = `true` iff the surface presents one or more figures the user **acts on** — a verdict, recommendation, score, ROI / margin / profit, KPI, or any number that drives the next decision. Concretely:
- `{has_analytics_band}` is `true` → `true` (a band is decision context).
- `{page_mode}` ∈ {`detail`, `analytical`} AND the record/hero/verdict cluster presents figures the user acts on → `true` (this is the lead-detail case the band gate misses).
- A single-item **decision composition** (§5a `recommended-alt`) whose surface is one ranked/scored decision → `true`.
- Pure **data-entry**, **passive-review**, or list-only CRUD with no figure the user acts on → `false`. Rigor does not apply; leave all `{rigor_*}` empty and skip the rest of this section.

**Per surface.** When the page carries multiple analytics/decision surfaces (the §5e gate fired), run this **once per surface**, exactly as §5c does — each surface gets its own rigor spec. For the common single-surface page, run it once.

**Invoke the skill (mode: `spec`).** Load `analytics-rigor` via the Skill tool and pass it:
- the **surface's decision-bearing figures**, wherever they sit (the §4b band's values AND the §4a record/hero/verdict numbers — not just the band),
- the **decision the surface serves**, in the user's words (from `{feature_purpose}` / `{user_context}`),
- the **§5c archetype** if a band exists (the shape it must deepen; omit for a bandless decision surface).

The skill runs its procedure (state the decision; list the decision-bearing numbers; run the eight rigor moves; name the deciding field per series; find the connective read; separate fixes from data gaps; cut ornament) and returns its **rigor decision object**. Capture it field-for-field:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `read_sentence` | `{rigor_read_sentence}` (or `none`) | brief §4d, rationale §3b |
| `decision_numbers` (metric · uncertainty · base_rate) | `{rigor_decision_numbers}` | brief §4d (the design contract `C-RIGOR-01` checks) |
| `deciding_field_check` | `{rigor_deciding_fields}` | brief §4d, `C-RIGOR-01` |
| `data_gaps` | `{rigor_data_gaps}` | brief §4d — surfaced as enrichment requirements |
| `verdict` | `{rigor_verdict}` (analyst-grade / schoolboy / mixed) | brief §4d, rationale §3b |

The rigor spec lands in the **brief §4d** (a surface-level section — it covers decision numbers whether they sit in the band or the record/hero), so it reaches the designer and `C-RIGOR-01` even when there is no band. The rationale §3b additionally records the *reasoning* when a rationale exists (i.e. when `{has_analytics_band}`), parallel to how §3 records the archetype reasoning while the brief carries the conclusion.

**Honesty gate (mirrors §5c's ground-or-flag).** If a required uncertainty or base rate is not computable from the available data, the skill returns it as a `data_gap`, NOT a fabricated figure. Carry the gap into the brief as a data requirement — never instruct the designer to draw a confidence interval the data can't support. **False precision is worse than an honest bare number**; a decorative error bar lies. This is the same honesty posture as the no-silent-fallbacks rule.

**Fallback (skill not available).** Apply the eight rigor moves by hand — lead with the read; no naked decision number; sensitivity to drivers; base rate; deciding field; trend magnitude + dispersion; rank by impact; missing-vs-weak — and populate the same fields. The skill is preferred because it makes the read sentence and per-number uncertainty mandatory outputs rather than skippable prose.

Set `{has_decision_numbers}` and the `{rigor_*}` fields (all empty when `{has_decision_numbers}` is `false`).

### 5c-3. Decision analysis — the executive layer (capital-commitment surfaces only)

Skip unless the surface is a **capital decision** — its primary job is to commit a scarce resource (capital, inventory slots, time) under uncertainty with a real downside (a buy / reorder / sizing / go-no-go-with-stake). This is **narrower than §5c-2**: a coverage strip, a trend dashboard, or a status worklist carries decision *numbers* but commits nothing — it stops at rigor. Set `{is_capital_decision}` accordingly; when `false`, leave all `{decision_*}` empty and skip the rest of this section.

§5c-2 made the figures honest (senior-analyst grade); this models and sizes the *decision* (executive / quant-desk grade). A surface can pass rigor — honest ranges, named gaps — and still leave the operator to decide how much to bet and whether the downside is survivable. Closing that is a distinct discipline.

**Invoke the skill (mode: `spec`).** Load `decision-analysis` via the Skill tool and pass it:
- the **commitment the surface serves** — action · stake (capital at risk) · horizon · downside,
- the **rigor figures** from §5c-2 (the honest inputs it builds the decision on),
- the **data sources** for the uncertain inputs (live data, an owned-history reference class, or absent).

The skill runs its procedure (frame the bet; model the outcome distribution; size to the loss tail; find the breakeven driver; compute the reference class; weight the decision-relevant regime; state the value-of-information gap; decide under asymmetry) and returns its **decision object**. Capture it field-for-field:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `frame` (action · stake · horizon · payoff) | `{decision_frame}` | brief §4e, rationale §3c |
| `outcome` (method · P(success) · EV · P10 · P90) | `{decision_outcome}` | brief §4e (the design contract `C-DECISION-01` checks) |
| `sizing` (quantity · basis · downside_survived) | `{decision_sizing}` | brief §4e, `C-DECISION-01` |
| `sensitivity` (swing driver · breakeven threshold) | `{decision_sensitivity}` | brief §4e, `C-DECISION-01` |
| `reference_class` / `regime` / `value_of_info` / `asymmetry` | `{decision_context}` | brief §4e, rationale §3c |
| `gaps` | `{decision_gaps}` | brief §4e — surfaced as enrichment requirements |
| `verdict` | `{decision_verdict}` (decision-grade / risk-modelled / single-scenario) | brief §4e, rationale §3c |

**Model-honesty gate (paramount — outranks the rest).** If the key probabilistic input is missing AND no reference class is computable, the skill returns `verdict: single-scenario` with the VOI gap — NOT a fabricated outcome distribution. Carry that honestly into the brief: an honest single-scenario read plus the named gap, never a confident P(success) off an invented win-rate. A fake distribution is worse than an honest point estimate. Same honesty posture as §5c-2 and the no-silent-fallbacks rule.

**Per surface.** On a page with more than one capital decision, run once per decision surface.

**Fallback (skill not available).** Apply the eight decision moves by hand — frame the bet; model the outcome distribution; size to the loss tail; breakeven driver; compute the reference class; weight the regime; value of information; asymmetry — and populate the same fields.

Set `{is_capital_decision}` and the `{decision_*}` fields (all empty when `{is_capital_decision}` is `false`).

### 5d. Surface Topology Assessment

**The question:** Given everything gathered above, is this feature's scope correctly bounded at a single route — or does the data depth, capability breadth, or user job structure suggest multiple surfaces?

**Reason from the evidence, not from thresholds.** You have already captured: the data model (entities and their depth), the user goals, the capabilities list, the data volumes, and the existing routes in `{implementation_files}`. Work through these four questions from the gathered evidence:

**1. How many distinct user jobs live on this route?**
Count from `{must_support_capabilities}` and the primary goals. Jobs that operate at fundamentally different depths — a triage queue and a deep-dive evidence panel, a batch management view and the items within it — are structural signals, not just UX variety. If the same route is expected to do two distinct jobs at different depths, ask whether splitting is the better architectural choice.

**2. What is the realistic capacity of the primary surface?**
A right-drawer holds a moderate-depth record view. A full-page detail view holds more — but there is a ceiling. If the per-item evidence layer (fields, charts, sub-tables, provenance panels) would span several full-page scroll-sections, the item record has outgrown a secondary panel and warrants its own route. Check whether `/[feature]/[id]` already exists in `{implementation_files}`.

**3. Are there sub-entities that belong on a sibling route?**
Import batches, audit history, configuration records, and provenance tables are frequently embedded in a primary surface when they'd be better served by an adjacent route — `/[feature]/batches`, `/[feature]/history`, `/[feature]/config`, etc. Check whether such routes already exist or are implied by the implementation. A sibling route serves a distinct operator job and does NOT require a return to the primary surface mid-task.

**4. Would tab/view navigation help — or just add chrome?**
Tab-level views are appropriate when the surface has two or three genuinely distinct slices of the same primary data that users switch between deliberately — not as a workaround for content overflow. The test: can you name the operator job that owns each tab? "Active queue" and "batch history" pass. "Main" and "Other" fail. If tabs would just partition what should be one coherent view, they are chrome. If they represent distinct operator modes, they earn their place.

**Verdict — one of:**

| Verdict | When to use |
|---------|------------|
| `single-page-appropriate` | All jobs are coherently served from one route. Scope, depth, and volume fit the surface. |
| `needs-detail-route` | The per-item depth warrants its own route (`/[feature]/[id]`). The primary route covers the queue/list; the item's full evaluation belongs on a second route. Most common for data-heavy operational surfaces. |
| `needs-tab-views` | Two or three genuinely distinct operator modes on the same primary data justify top-level tab navigation within the current route. The tabs represent mode-switching, not content overflow. |
| `needs-sibling-route` | A distinct sub-feature (batch management, history, configuration) belongs on its own adjacent route rather than embedded in the primary surface. |

**When the verdict is not `single-page-appropriate`:**
Describe the recommended topology in 2-4 sentences: which route covers which job. Note any routes that already exist in `{implementation_files}` for this feature prefix.

Before generating the brief, surface to the user:
> *"The gathered scope suggests this feature spans multiple surfaces. This brief will cover `{route}` ([primary job]). Also recommended: a brief for [other routes + their jobs]. Generate now, or continue with primary only?"*

In autonomous mode, proceed with the primary brief and surface the topology in §4c of the generated brief.

Set `{surface_topology_verdict}` and `{surface_topology_notes}`.

### 5e. Analytics Surface Hierarchy — rank multiple co-resident surfaces

**Gate:** run this section ONLY when the route (after §5d topology) carries **two or more distinct analytics surfaces** — a "surface" being a dataset + question pair that earns its own §5c archetype (a price-over-time chart, a seller-share composition, and a buy-box-ownership ranking are three surfaces, not one band). Zero or one surface → skip; §5b/§5c already handle the singular case. **This gate fires regardless of `{page_mode}`, including `detail`:** an analytics-rich single-entity page (a product research / monitoring view whose record carries time-series and competitive aggregates) is exactly the case §5b's "a single record has no aggregate dimension" misses.

**The problem this prevents:** left unranked, multiple legitimate surfaces render at equal visual weight — the flat panel-stack the policy bans (§6 "the visual lead must be one or two restrained charts… supporting tables"; §5 no card-grid-as-structure). The handoff has named the *shape* of each surface (§5c) but never said which one *leads*. This section carries that decision into the brief so the designer ranks deliberately instead of stacking by default.

**Rank by the page's primary question, not the legacy render.** You have already captured the one job this page exists for (§4 feature purpose / §6 user context). Run §5c once per surface to get each one's archetype, then assign each surface a tier:

| Tier | Test | Form in the brief |
|------|------|-------------------|
| **hero** (1, rarely 2) | Most directly answers the page's primary question | Full-weight chart, top of the analytics region |
| **supporting** | Qualifies or contextualises the hero's answer | Demoted to a compact form — sparkline / strip / mini-chart, not a full panel |
| **drill** | Consulted only on a specific doubt, not in the default scan | Collapsed behind an expand/toggle; available, not displayed |

The anti-bias is the same as §5a/§5b: rank by the **job**, never by the order the legacy page happened to stack them (flat-equal *is* the legacy bias). Demotion is real form, not a smaller title — a supporting surface becomes a sparkline, a drill surface collapses.

**Ground or flag (reuses §5d).** If you **cannot name a single primary question that designates one hero** — two surfaces are genuinely co-equal because the page serves two unrelated jobs — do not flatten them to a tie. That is the §5c "two co-equal archetypes → split it" rule at the page level: **route back to §5d** (`needs-tab-views` if the two jobs are deliberately switched between, `needs-sibling-route` if they are distinct sub-features). If you can't rank it to one hero, it may not be one page.

**Capture the reasoning.**
- `{analytics_surface_inventory}` — the distinct surfaces found, each with its dataset + question + §5c archetype.
- `{analytics_hierarchy}` — each surface tagged `hero | supporting | drill`.
- `{hierarchy_rationale}` — the primary question, why the hero answers it, and why each other surface is **demoted, not deleted** (richness is preserved — a research/detail page wants all of it, ranked).
- `{hierarchy_unresolved}` — set when no single hero emerges; record the §5d verdict it routed to.

In autonomous mode, proceed with the inferred hierarchy and surface it in the brief (§4b); the ground-or-flag still fires — a wrong hero is confident nonsense, so an unresolvable primary question is asked/routed, not guessed.

Set `{analytics_hierarchy}` and `{hierarchy_rationale}` (both empty when the gate doesn't fire — zero or one analytics surface).

### 6. Identify User Context

Set `{user_context}`:

- What role uses this page?
- What's the job-to-be-done?
- How often? (daily tool vs. occasional reference)
- What's the emotional state? (urgent task vs. exploratory browsing)

If undetermined from code, ask the user ONE question:
> "Who uses this and what are they trying to accomplish?"

---

## COMPLETION

Confirm populated:
- `{github_repo_url}` ✓
- `{feature_name}` ✓
- `{feature_scope}` ✓
- `{feature_purpose}` ✓
- `{data_shape}` ✓
- `{api_surface}` ✓ (incl. the §3 **mutation-derivation audit** — every server action the current surface invokes is accounted for: carried into `{must_support_capabilities}` or logged in `{dropped_capabilities}`)
- `{dropped_capabilities}` ✓ (each a deliberate drop with `capability · backing_action · reason`; empty list only when every action the current surface exposes is carried forward — never empty by omission)
- `{implementation_files}` ✓
- `{page_mode}` ✓ ("operational", "analytical", or "detail")
- `{composition_provenance}` ✓ (`policy-default` | `recommended-alt`; decided in §5a from the job, NOT inherited from the policy default; `recommended-alt` veto-surfaced and `{composition_rationale}` captured) — and `{page_mode}` stays the honest work type even when composition deviates
- `{band_provenance}` ✓ (`inherited` | `recommended-new` | `recommended-drop` | `none`; net-new/drop recommendations veto-surfaced)
- `{has_analytics_band}` ✓ (`true` iff band_provenance ∈ {inherited, recommended-new})
- `{analytics_archetype}` ✓ (one of the nine, or `unclear` → asked; empty when no band)
- **Analytics reasoning capture** ✓ (populated iff `{has_analytics_band}` is `true`; all empty otherwise) — `{page_mode_rationale}`, `{band_decision_log}`, and the archetype decision object captured from the `analytics-surface-architect` skill in §5c: `{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`, `{archetype_drill_map}`, `{archetype_prohibited}`. These feed the rationale artifact (step-03b) and §4b; capturing the deliberation here is what makes the presentation decision auditable instead of discarded.
- `{has_decision_numbers}` ✓ (`true` iff the surface presents figures the user acts on — verdict, score, ROI/margin/profit, KPI; broader than `{has_analytics_band}`, so it captures bandless `detail`/`analytical` decision surfaces like a lead buy page; `false` for pure data-entry/passive-review/CRUD — §5c-2)
- **Analytics rigor capture** ✓ (populated iff `{has_decision_numbers}` is `true`; all empty otherwise — run **per surface** on multi-surface pages) — `{rigor_read_sentence}`, `{rigor_decision_numbers}`, `{rigor_deciding_fields}`, `{rigor_data_gaps}`, `{rigor_verdict}` from the `analytics-rigor` skill in §5c-2. These render into **brief §4d** (surface-level — covers decision numbers in the band AND the record/hero) and drive `C-RIGOR-01` at review; rationale §3b records the reasoning when a band exists. The §5c-2 honesty gate holds — data gaps are surfaced as enrichment requirements, never fabricated into figures.
- `{is_capital_decision}` ✓ (`true` iff the surface's job is to commit a scarce resource — capital / inventory slots / time — under uncertainty with a real downside; narrower than `{has_decision_numbers}`, so a buy/reorder/sizing surface is `true` but a dashboard/coverage/status surface is `false` — §5c-3)
- **Decision analysis capture** ✓ (populated iff `{is_capital_decision}` is `true`; all empty otherwise — run **per decision surface**) — `{decision_frame}`, `{decision_outcome}`, `{decision_sizing}`, `{decision_sensitivity}`, `{decision_context}`, `{decision_gaps}`, `{decision_verdict}` from the `decision-analysis` skill in §5c-3. These render into **brief §4e** (the executive layer — modelled outcome + sizing + breakeven driver + reference class) and drive `C-DECISION-01` at review; rationale §3c records the reasoning when a band exists. The §5c-3 model-honesty gate holds — an un-modellable decision is an honest `single-scenario` read + a named VOI gap, never a fabricated outcome distribution.
- `{surface_topology_verdict}` ✓ (one of: `single-page-appropriate` | `needs-detail-route` | `needs-tab-views` | `needs-sibling-route`)
- `{analytics_hierarchy}` ✓ (each surface tagged hero | supporting | drill — §5e; empty when the page has 0–1 analytics surface) — plus `{hierarchy_rationale}` and `{analytics_surface_inventory}`; `{hierarchy_unresolved}` set only when no single hero emerged (→ routed to §5d topology)
- `{surface_topology_notes}` ✓ (recommended topology in 2-4 sentences; empty string when verdict is `single-page-appropriate`)
- `{linked_records_inventory}` ✓ (§3a — one entry per on-screen value that IS a record another surface owns: foreign reference · owning surface+route · drill target (drawer + "Open full {sibling} →") · inline lookups; empty **only** for a true leaf surface that references no foreign record. Renders into brief §2a and is enforced at review by `design-review-pr` §13/§12.)
- `{user_context}` ✓
- `{brand_identity}` ✓ (may be empty)
- `{design_system}` ✓ ("branded", "existing", or "external")
- `{handoff_mode}` ✓ ("fresh-design" or "refine-screen")
- If `{handoff_mode}` = "refine-screen": `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}` ✓ (loaded by workflow.md before this step)

**Refine-screen mode reminder:** Do NOT ask the user "what feels wrong?" or "what are the top issues?" — those came from the artifact loaded in workflow.md. The user-context question (who uses this, how often) is still valid; the diagnostic question is not.

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md`
