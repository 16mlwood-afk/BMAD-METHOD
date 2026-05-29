---
name: operational-analytics-band
description: Design and critique the supporting analytics band / evidence layer on operational or hybrid product pages — the compact row of coverage strips, microcharts, and counters that sits above or beside the primary table/worklist. Use when adding, revising, tightening, or auditing this band so it stays subordinate to the worklist and tied to user actions. Do NOT use for full BI/executive dashboards, any page where analytics is the primary surface, standalone analytical/reporting pages, schema/backend/data work, copy-only edits, or page redesigns that contain no analytics surface.
metadata:
  short-description: Critique the analytics band on operational pages
---

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

## What the skill does

### 1. Decide whether the page needs an analytics band at all

Before designing anything:

- Confirm the page mode (operational, analytical, hybrid). Hybrid defaults to operational — see §6.
- Ask: *what concrete user decision or action does an analytics band enable here?* If none, **recommend removing the band rather than filling space**. Empty real estate is preferable to decorative analytics.
- If the only honest answer is "context" or "overview," that is a signal the page is operational and the band should be minimal or absent.

### 2. Preserve hierarchy

On operational and hybrid-as-operational pages:

- The table/worklist remains visually and interactionally primary (§2, §6).
- The analytics band is **one compact row**, calm, and clearly secondary. Above-the-fold space stays majority table (~60–70% vertical, per §2 *Analytics visual weight*).
- Nothing in the band may compete with the table for attention. If it does, redesign to reduce prominence (§6 *Analytics in operational mode*).

### 3. Design compact evidence surfaces

Prefer, in roughly this order of utility:

- **Coverage strips / timelines / progress tick marks** — a status meter for the underlying table data (per-week completeness, filing readiness across a period). Render as a single narrow strip (§2 *Coverage strip*).
- **Micro bar charts / sparklines** — a single compact row aligned with the coverage strip, restrained heights and colors (§2 *Weekly spend / trend charts*).
- **Focused counters or readiness summaries** — a short inline summary line ("243 invoices / 18 pending review / 3 blocked"), per §5's guidance against stat-card grids.
- **Short, explicit drill hints** — e.g. *"click a week to filter the table"* — so the band's purpose is visible.

Each element must tie to a clear action or drill path. Decorative charts are not allowed.

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
   **Counter-offer:** A single shared evidence band with one coverage/readiness strip, one compact trend chart, and one focused readiness counter — each clearly tied to a table action, not framed as a summary card.

2. **Refusal:** "Three summary cards above table" as the default pattern, even if visually restrained.
   **Why:** Same §5 hard failure; the cardization is the problem, not the count.
   **Counter-offer:** Combine the metrics into a single horizontally structured band that reads left-to-right as a short narrative — **coverage → trend → readiness** — without tile boundaries or card chrome.

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
