---
name: operational-analytics-band
description: Design and critique the supporting analytics band / evidence layer on operational or hybrid product pages — the compact row of coverage strips, microcharts, and counters that sits above or beside the primary table/worklist. Use when adding, revising, tightening, or auditing this band so it stays subordinate to the worklist and tied to user actions. Do NOT use for full BI/executive dashboards, any page where analytics is the primary surface, standalone analytical/reporting pages, schema/backend/data work, copy-only edits, or page redesigns that contain no analytics surface.
metadata:
  short-description: Critique the analytics band on operational pages
provenance:
  id: operational-analytics-band
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://tessl.io/registry/skills/github/secondsky/claude-skills/kpi-dashboard-design/quality  # general KPI-dashboard-design skill; covers full BI dashboards, not this narrow operational-page-subordinate band
    - https://github.com/nickcrew/claude-cortex/blob/main/skills/dashboard-designer/SKILL.md  # general dashboard-designer skill; spec/critique for whole dashboards, not the specific worklist-subordinate band + archetype-defer pattern
    - https://sstoitsev.medium.com/a-dashboard-design-ai-agent-skill-for-getting-past-pretty-screens-8747d20f09f9  # adjacent "dashboard design AI agent skill" writeup; same problem space (past-pretty-screens critique) but for dashboards-as-primary-surface, not this skill's operational/hybrid-band-as-secondary-surface job
  origin_type: original
  exemption_reason: "Searched for existing dashboard/analytics-band design-critique tools and skills (web + GitHub/npm/marketplace). Found several general-purpose dashboard-design skills (kpi-dashboard-design, dashboard-designer, a Medium-documented 'past pretty screens' agent skill) but all of them treat the dashboard/chart as the primary surface to spec or critique. This skill does the opposite job: it governs a narrow, secondary evidence band on operational/hybrid pages where the worklist stays primary, deferring shape selection to a sibling fork skill (analytics-surface-architect) and visual rules to this fork's own docs/design-policy.md. No external tool addresses that specific subordinate-band-on-operational-page constraint, so this is original to the fork rather than adopted/adapted from an external analog."
  predecessor_id:
  superseded_by:
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. No external analog found for the subordinate-band-on-operational-page job; nearest matches are general dashboard-design skills that treat the dashboard as primary."
---

## External research checked
- Date: 2026-07-24 · Queries: "dashboard analytics band design linter subordinate to worklist table UI pattern tool" · "design critique agent skill \"analytics band\" OR \"evidence layer\" GitHub open source dashboard KPI strip"
- Sources: https://tessl.io/registry/skills/github/secondsky/claude-skills/kpi-dashboard-design/quality · https://github.com/nickcrew/claude-cortex/blob/main/skills/dashboard-designer/SKILL.md · https://sstoitsev.medium.com/a-dashboard-design-ai-agent-skill-for-getting-past-pretty-screens-8747d20f09f9
- Verdict: ORIGINAL — general dashboard-design skills exist but treat the dashboard as primary; none govern a compact evidence band kept subordinate to an operational worklist per this fork's design-policy.md.

# Operational Analytics Band

This skill applies `docs/design-policy.md` to **one specific surface**: the compact analytics/evidence band that may appear above (or beside) the primary table on operational and hybrid pages. It does not govern the page as a whole, and it does not apply to analytical-mode pages (where the chart *is* the primary surface).

## Trust hierarchy

1. **`docs/design-policy.md` is canonical.** This skill defers to, and never overrides, that file. The directly relevant sections are:
   - §2 Layout Principles — *Analytics visual weight*, *Coverage strip*, *Weekly spend / trend charts*.
   - §5 Hard Failures — bullets on dashboard stat-card grids, bento/magazine layouts, hero strips above working tables, and AI-fingerprint tropes.
   - §6 Page Modes — *Operational mode*, *Analytical mode*, and *Analytics in operational mode*.
   - §8 Precedence — tailwind tokens → this policy → shared BMAD design standards.
2. **This skill interprets and applies those rules to the analytics band only.** Cite sections by number when explaining a decision or refusal.
3. **The current product UI is not a source of truth.** Treat any live page as possible drift from policy. Where the live UI conflicts with `docs/design-policy.md`, the policy wins (§8 *Precedence*) — recommend changing the UI, not relaxing the rule.
4. **Band *shape* is selected by the `analytics-surface-architect` skill; the taxonomy is its vocabulary.** `_bmad/bmm/workflows/design/shared/analytics-archetypes.md` (synced from BMAD shared standards — §8's bottom layer) defines the eight forms — `trend`, `distribution`, `composition`, `ranking`, `coverage`, `flow`, `single-metric`, `correlation`. The `analytics-surface-architect` skill is the **selector** that picks the dominant one from the user's question (see §1b — defer to it, don't re-derive). `docs/design-policy.md` still governs visual treatment; the architect governs shape. The three compose: the architect picks the shape (vocabulary from the taxonomy), this skill places it subordinate to the worklist, the policy styles it.

## What the skill does

### 1. Decide whether the page needs an analytics band at all

Before designing anything:

- Confirm the page mode (operational, analytical, hybrid). Hybrid defaults to operational — see §6.
- Ask: *what concrete user decision or action does an analytics band enable here?* If none, **recommend removing the band rather than filling space**. Empty real estate is preferable to decorative analytics.
- If the only honest answer is "context" or "overview," that is a signal the page is operational and the band should be minimal or absent.

### 1b. Choose the archetype — defer to `analytics-surface-architect`

Once a band is justified, pick its **shape** *before* designing anything — this is the step that keeps every band from collapsing into the same coverage-strip + microchart + counter row. **Do not re-derive the selection here; defer to the `analytics-surface-architect` skill** — the single selection brain (the same one `design-handoff` invokes), so this skill, the handoff workflow, and PR-time enforcement all reason identically.

- **Invoke `analytics-surface-architect` (mode: `select`)** with the data shape and the user's question. It returns the dominant archetype (one of the eight), grounded by the user's question, plus any subordinate archetype and the per-element drill map. It enforces ground-or-flag and refuses to default to `trend` because dates exist — so you don't restate that rule, you consume its result. If a `design-rationale-*` artifact already exists for this surface (handoff produced one), read it instead of re-selecting.
- **This skill owns placement, not selection.** Take the architect's archetype and render it as a band that stays subordinate to the worklist (§2 below). A second archetype may appear as a subordinate pass but must not double the band's footprint.
- `coverage → trend → readiness` is **one** composition (a coverage-dominant band with a secondary trend and a counter), legitimate only when the architect actually selects `coverage` for a completeness-over-a-period question. It is not the universal band — never apply it by reflex to a `ranking`, `composition`, `distribution`, `flow`, or `single-metric` selection.

### 2. Preserve hierarchy

On operational and hybrid-as-operational pages:

- The table/worklist remains visually and interactionally primary (§2, §6).
- The analytics band is **one compact row**, calm, and clearly secondary. Above-the-fold space stays majority table (~60–70% vertical, per §2 *Analytics visual weight*).
- Nothing in the band may compete with the table for attention. If it does, redesign to reduce prominence (§6 *Analytics in operational mode*).

### 3. Design compact evidence surfaces

The archetype chosen in §1b dictates the **lead form**; pick from the vocabulary below to render it. These are the available compact surfaces — not a fixed sequence to assemble every time:

- **Coverage strips / timelines / progress tick marks** — lead form for `coverage`: a status meter where the *gaps are the content* (per-week completeness, filing readiness). Render as a single narrow strip (§2 *Coverage strip*). **A single accent marks the gaps — never a multi-colour heatmap:** the strip reads present-vs-missing, so gaps carry one accent against a neutral track; a rainbow/heatmap gradient turns a completeness signal into decorative noise and defeats the at-a-glance read.
- **Micro bar charts / small-multiple sparklines** — lead form for `trend`: a single compact row, restrained heights and colors, one panel per series rather than one multi-series chart (§2 *Weekly spend / trend charts*).
- **Sorted bar lists** — lead form for `ranking`: top-N, capped and labelled ("top 8 of 142"), optional rank-delta arrows.
- **A single stacked / 100% bar** — lead form for `composition`: part-to-whole in one bar, never a pie and never a time-stacked series.
- **One large value + sparkline + threshold marker** — lead form for `single-metric`: one number in context, never a row of stat cards.
- **Focused counters or readiness summaries** — a short inline summary line ("243 invoices / 18 pending review / 3 blocked"), per §5's guidance against stat-card grids. A supporting element, not a lead.
- **Short, explicit drill hints** — e.g. *"click a week to filter the table"* — so the band's purpose is visible.

See `analytics-archetypes.md` for the full question/form/drill/avoid of each archetype. Each element must tie to a clear action or drill path. Decorative charts are not allowed.

### 4. Wire drill-to-evidence behavior

For every element in the band, state explicitly:

- The user question it answers ("which weeks are missing invoices?").
- The action it enables (filter, sort, drill, jump).
- How that action connects back to the main table.

If you cannot answer all three for an element, that element should not exist — replace it with a simpler metric, a sentence, or nothing.

### 5. Align with policy

When designing or critiquing, cite the specific section of `docs/design-policy.md` that drove the decision. Do not duplicate policy content here — point to it. If a rule in the policy appears ambiguous for this surface, raise the ambiguity rather than guessing.

## Refusals (and what to offer instead)

When this skill is active, refuse the following patterns and propose the alternative each time.

1. **Refusal:** A row of 3–6 identical summary tiles/cards above the table (classic KPI row).
   **Why:** §5 — *Dashboard stat-card grids as page openers* is a hard failure and named AI fingerprint.
   **Counter-offer:** A single shared evidence band whose lead form is the §1b archetype (a coverage strip, a sorted ranking list, a single composition bar, one contextualized metric, …) — each element clearly tied to a table action, not framed as a summary card.

2. **Refusal:** "Three summary cards above table" as the default pattern, even if visually restrained.
   **Why:** Same §5 hard failure; the cardization is the problem, not the count.
   **Counter-offer:** Combine into a single horizontally structured band built around the archetype's lead form, without tile boundaries or card chrome. (When the archetype is genuinely `coverage`, that band reads coverage → trend → readiness — but derive the composition from the archetype, don't impose that sequence on a ranking or composition question.)

3. **Refusal:** Evenly modular analytics tiles with flat hierarchy that could appear in any SaaS admin.
   **Why:** §5 — *Bento or asymmetric "magazine" card layouts* and AI-fingerprint tropes; also §2 *Analytics visual weight* (band, not dashboard header).
   **Counter-offer:** Introduce hierarchy and asymmetry — one dominant evidence surface, one secondary, one tertiary. Vary widths, densities, and label emphasis so the band signals what matters most.

4. **Refusal:** Executive-dashboard style headers that visually compete with the main table.
   **Why:** §6 *Analytics in operational mode* — analytics must be subordinate to the worklist; §5 forbids hero strips and banner panels above working tables.
   **Counter-offer:** Keep the band thin and calm. Prioritize legibility and direct tie-in to the worklist over "summary" aesthetics. If it still competes, shrink or remove it.

5. **Refusal:** Decorative or redundant charts that don't inform a concrete action.
   **Why:** §2 *Weekly spend / trend charts* — trend charts must drive a clear filter/drill action; otherwise prefer a simpler summary metric.
   **Counter-offer:** Remove the chart, or replace it with a single metric or a short explanatory sentence that directly supports a user decision.

## Examples

This skill is **only** for analytics bands on operational or hybrid pages where a table/worklist is the primary surface. It is **never** for standalone analytical/reporting pages, and it must never recommend reducing the table's primacy on the pages it does cover.

**Good fit for this skill**
Refining a worklist page's evidence band so a per-period coverage strip, a compact trend microchart, and a focused readiness counter all sit in one compact row, each wired to filter the primary table — and the table still owns the majority of vertical space.

**Out of scope**
Designing a full executive dashboard, building a standalone analytical/reporting page, or producing a general-purpose BI report. Those are §6 *Analytical mode* surfaces and belong to a different skill or workflow — do not invoke this skill on them.
