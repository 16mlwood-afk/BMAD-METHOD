---
type: design-policy-overlay
family: bison-management
status: approved
version: 1
created: 2026-06-17
last_updated: 2026-06-17
inherited_by:
  - inbound-flow        # Amazon FBA inbound & inventory operations
  - accounting-tools    # VAT / accounting tool
  # future Bison Management operational tools inherit by adding `inherits: bison-product-family-policy` to their docs/design-policy.md
precedence: "project design-policy.md  >  THIS overlay  >  shared/design-standards.md  >  code tokens"
---

# Bison Management — Product-Family Design Policy (overlay)

> **What this is.** This is the **shared visual constitution for Bison Management's operational tools** — the design language that makes every Bison product (inbound-flow, accounting-tools, and future siblings) read as **one product family** operated by one person who handles real money and inventory. It is the *tier between* the universal AI-fingerprint rules (`shared/design-standards.md`, below it) and each project's own `design-policy.md` (above it).
>
> **This is NOT project-agnostic machinery.** It deliberately encodes Bison-specific product values (a GBP/VAT-reporting business, finance-grade restraint, relational records, multi-currency sourcing). It lives in the fork's `shared/` directory so it distributes to every sync target, but it is **inherited only by Bison Management family tools** — a project consumes it *only* if its `docs/design-policy.md` frontmatter declares `inherits: bison-product-family-policy`. Non-Bison sync targets have this file on disk and ignore it.
>
> **How inheritance works.** A Bison project's `docs/design-policy.md` inherits every rule here verbatim, then states **only its project-unique residue** (its own exemplar domain, its own surface topology, its own product imagery, its concrete tokens/routes). It must not re-state these shared rules — it points to this overlay. When a project needs to *diverge* from a shared rule, it overrides explicitly and records the divergence in its own change log (project policy wins per precedence above).
>
> **Provenance.** This overlay was extracted from `inbound-flow/docs/design-policy.md` v11 — itself ported from `accounting-tools` v11 — by lifting every section the change log tagged "shared product-family value → propagate," in source-agnostic form. The Amazon/FBA/inventory exemplars and inbound-flow's warehouse-handler and product-imagery sections were deliberately left in the project policy as tier-3 residue (see §Z).

---

## §A. Register & tone

These are Bison-family operational tools for one owner-operator (plus any ops help working the same queues) running a real, money-handling business. Every product in the family must read as **fast, precise, and dense — a cockpit for processing records, not a presentation surface.**

- **Serious, trustworthy, corporate-restrained.** It handles real money and should feel like an **in-house finance-grade tool**, not a designed SaaS product. Calm and dense, never marketing or playful.
- **Restraint over flourish.** The page communicates through **structure, typography, and data**. Decoration, motion, and glow are *removed*, not minimized.
- **A worklist, not a dashboard.** Data and status are the primary visual affordances. Decoration is not.

Visual anchors the family draws from: **Stripe** (operations-first dense data tables, chip-based filter bars), **Linear** (compact top-bar filters, keyboard-first, calm low-contrast palette), **Mercury** (calm fintech restraint, data as the focus), **Ramp** (explicit operational status badges). Borrow their *operational density and restraint*; never their opinionated marketing surfaces.

Light/dark is a **project choice** (accounting-tools is light-first off-white; inbound-flow keeps dark as root) — but **both themes must read flat and sober; the corporate register is theme-agnostic** and every rule here applies identically in either theme. The palette is always read from the project's tokens.

---

## §B. Layout principles

- Operational pages are **table-first** and full-width within the content container. The table is the page. Filters, summaries, and actions exist to support it.
- Filters live in a **persistent top bar** (chips/pills) immediately above the table.
- Status is shown via small pill badges integrated into table rows — never as colored card fills, hero strips, or banner panels.
- Page chrome is minimal: title, optional one-line description, inline actions. No hero padding, no centered marketing layouts.
- Multiple background colors per section is a smell. Default to one surface color per panel.

**Analytics visual weight.** Analytics bands (coverage strips, trend charts, readiness gauges) must not occupy more than one compact row above the table. Above-the-fold space should be majority table (~60–70% of vertical height). The analytics band **shares the table's surface** — no separate background fill, no card-style framing. The "three summary cards above a table" default is **banned** — it is the generic enterprise-dashboard opener and an AI fingerprint. For headline counts use an inline summary line in the page header (§E). The narrow band is reserved for context that genuinely needs a visualization (coverage, trend, readiness), not summary numbers. See the `operational-analytics-band` skill for the supporting-band pattern.

---

## §C. Status system

All operational state across the family is communicated through a **single pill-badge component** used identically across tables, queues, and detail views.

**Shape:** small rounded pill (`rounded-md`, **not** `rounded-full`), `text-xs`, compact padding. **A desaturated tinted fill with a 1px solid tinted border per tone and neutral text.** No leading colored dot and no leading status icon — the badge's signal is its tinted background, bordered edge, and neutral text.

**Colors (only these four):**

- **Gray** — queued, default, unknown, not-yet-processed.
- **Yellow** — needs review, attention required, manual action pending, unmatched / not-yet-reconciled.
- **Green** — ready, reconciled, received, success. A **true green**, never a teal/turquoise.
- **Red** — failed, blocked, error.

Maximum **4 distinct badge colors** on any page. No purple/blue/orange/teal/pink status variants, no rainbow mappings. Blue is reserved as the product *accent* (§D) for active filter chips, links, active-tab underlines, and focus — **never** for primary buttons and never as a status color.

**Status saturation.** Use the desaturated `--status-*-muted` tints. Badge colors must not dominate table text — "structured annotation," not "traffic-light dashboard." Operational meters/progress bars fill with the **muted** tint, not full saturation.

**Color hierarchy (weight in proportion to operational urgency, not equal weight):**

- **Red** — primary/blocking weight; the only status that should visibly pull the eye on a dense row.
- **Yellow** — mid weight; quieter than red, more present than gray.
- **Green** — restrained weight; success is the *expected* outcome, not a reward. Not celebratory.
- **Gray** — resting weight; should not interrupt scanning.

**Reconciliation / match states map by meaning, not by stage.** A record that is un-reconciled or awaiting a match (`unmatched`, `pending`, `review`, `no match found`, `awaiting receipt`) is an *attention/pending* state and is **yellow**, never red. **Red is reserved for genuine failures** (processing errors, blocked states, failed jobs), not for a missing or not-yet-found match. `matched`/`reconciled`/`received` → green; `archived` → gray. This keeps red rare and guarantees the same match state reads the same tone on every sibling surface (§K).

**Primary vs secondary status.** A row may carry one primary status (workflow state, full pill) and one secondary signal (a derived flag — "needs evidence", "price changed", "duplicate detected") rendered quieter: smaller, neutral text, optional icon, no fill. **Never two equal-weight colored pills on one row.** If two primary statuses seem needed, the model is wrong — collapse to one.

**Anti-pattern (banned):** the pastel `rounded-full` pill with a leading colored dot and pale tinted background (the Linear/Vercel default-template aesthetic AI tools reach for), or any badge whose primary signal is a colored dot or leading icon rather than the background/text.

---

## §D. Color & typography

- **Surfaces are flat solid colors only** — no decorative gradients, no ambient background mesh, no glassmorphism. Read from the project's tokens.
- **Primary actions are monochrome** (near-foreground dark-on-light / light-on-dark — the Stripe treatment), not a saturated fill. The blue accent is a single, sparingly-applied *interaction* color — links, active filter chips, active-tab underlines, focus rings — never the default fill of a primary CTA.
- Color is reserved for: status badges, warnings/errors, success indicators, active filter chips, links, focus. Nothing else.
- **Depth is flat:** `shadow-sm` maximum, neutral shadows only — no colored or glow shadows.
- **Primary font: Inter** (the corporate sans), falling back to the neutral system sans stack.
- Body text is **denser than typical SaaS** (≈13px default inside panels and table rows) — the corporate-finance density.
- **Negative letter-spacing on headings** (-0.01em to -0.025em).
- **Monospace only for tabular numbers, IDs, codes, and currency amounts in tables.** Never for prose, labels, or headers. Pair with `tabular-nums`.
- Maximum 3 distinct font sizes per component. Sentence case for labels. Never `uppercase tracking-wide`.

---

## §E. Hard failures (non-negotiable)

A design containing any of the following fails review and must be revised before merge. This list is the family floor; it sits **on top of** the universal AI-fingerprint taxonomy in `shared/design-standards.md` (which still applies in full).

- **Sidebar layout inside feature pages.** App-shell nav is out of scope; feature pages are full-width.
- **Centered card-on-gray-background layouts.** These are not settings pages.
- **Dashboard stat-card grids as page openers.** Use an inline summary line in the page header instead.
- **Bento or asymmetric "magazine" card layouts.**
- **Hero strips, banner panels, or marketing-style intros** above working tables.
- **More than 4 distinct badge colors on a single page** (categorical tag chips count — a multi-hue tag palette must not defeat the cap).
- **Inconsistent status badge shapes or colors between surfaces.**
- **Temporal tables in non-chronological default order, or orderable columns with no sort affordance** (§G).
- **Gradient backgrounds, ambient mesh, glassmorphism, or playful marketing visuals.** Surfaces are flat.
- **Colored or glow shadows.** Neutral, subtle, `shadow-sm` maximum.
- **Entrance and decorative motion** — fade/slide-in on mount, staggered children, pulse/shimmer/breathing. Only subtle *functional* feedback is allowed (hover background change, `active:scale-[0.98]` press).
- **Marketing or enthusiastic copy** ("Welcome back!", "Great job!", celebratory emoji). Tool chrome is declarative and factual.
- **Chatty or illustrated empty states.** Plain text only: "No results." / "No items match your filters."
- **AI fingerprint tropes:** 3-feature icon rows, colored icon circles, "AI purple" (`indigo-600`/`violet-500`) as primary accent, animated number counters, hover lift/scale transforms.
- **Emoji as UI icons.** Use a single icon set (Lucide) or no icon at all.
- **Pill-shaped (`rounded-full`) buttons as primary CTA.**
- **Typography fingerprints:** uppercase tracking-wide labels in tool chrome, all-caps section headers, mismatched display+body pairings.
- **The money / numeric hard failures in §L** apply family-wide.

### Anti-default compositions (categorical)

- **Rows of identical stat cards** (any count/size) to open a page or summarize a worklist — use an inline summary line.
- **Evenly padded card grids** as primary page structure (the "modular dashboard" shell).
- **Template-y "summary cards + table" layouts.**
- **Compositions that could be lifted into a different SaaS admin product without modification.** If the structure would work unchanged for an HR tool, a CRM, or a generic analytics dashboard, it is wrong for this product.

### Anti-AI layout principles

- **No generic card rows as structure.** Test: if a layout could be dropped unchanged into any generic SaaS admin, it fails.
- **Analytics bands must not masquerade as card grids.** Trend strips read as a single shared band — shared container, minimal per-panel chrome — not a row of interchangeable mini-cards.
- **Hierarchy and grouping must be domain-authored.** Ordering/grouping must encode real domain meaning (most at-stake first, blocked states grouped) — at least one hierarchy decision per page traceable to a domain rationale.
- **Symmetry is the exception, not the default.** Break symmetry through size/emphasis/grouping when it serves the story.
- **Decorative patterns must be justified or removed.** Every decorative element must answer "what job does this do?" — if "looks nice" or "fills space," remove it.
- **AI outputs require a human authorship pass** before they ship.

---

## §F. Page modes

Every page is one of two modes, declared in the design brief, constraining layout.

### Operational mode (default)

The user processes records: source, import, enrich, reconcile, batch, clear, resolve, file, match.

- **Table-first**, filters above, pagination/actions below, status integrated into rows. The table is the primary surface; everything else supports it.

### Data-heavy operational tables

A sub-pattern for tables with many columns/rows. Keep the main grid scannable while preserving access to full detail.

- **Primary unit of work.** Every data-heavy table declares one primary unit (per row, or per batch). Only the primary unit gets strong status pills and primary actions. Secondary units use quieter chips/text and cannot visually compete.
- **Overview vs detail.** The table is an overview, not a dossier: identifiers, one primary status, a limited set of critical metrics. Full detail (multi-line notes, full payloads, audit trail) lives in the right-hand detail drawer (§H) or a separate detail view — never extra inline columns or stacked text.
- **Column hierarchy — three tiers.** Tier 1 (identifiers & status): leftmost, always visible. Tier 2 (key metrics): may collapse on small screens. Tier 3 (ancillary): moves into the drawer or an overflow pattern if it harms scan.
- **Status and actions.** At most one strong status pill per row (the four-color hierarchy of §C applies to this pill only); additional state uses muted text/icons or the drawer. Exactly one primary visible action per row; others go to an overflow menu or the drawer. **Bulk actions live in a transient floating action bar tied to selection** (fixed bottom, neutral card surface, one subtle shadow), visually separated from row actions — not inline per-row controls or a persistent header toolbar.
- **Density & scannability.** One line of primary text, one of secondary at most; no more than two emphasis levels per row. Density presets govern row height but never change the column hierarchy or status rules.
- **Alignment.** Identifiers left; numbers right with consistent decimals (`tabular-nums`); statuses centered/right in their column. Sticky headers required for vertical scroll; key identifier columns stay visible on horizontal scroll.
- **Sorting and default order.** Sort is the **default expectation on every operational table, not an opt-in.** Any orderable column (dates, quantities, costs, names, ordered statuses) exposes click-to-sort with a visible active-sort indicator. A non-sortable column is the exception and needs a reason.
- **Chronology is the default story.** Any table whose rows carry a primary date/time **defaults to a most-recent-first chronological sort** on that date — never insertion/arbitrary/alphabetical order. Sibling surfaces (§K) sort by the same canonical date and direction.
- **Compound-data cells in under-sized columns.** When a cell stacks more than one field (cost + margin, value + unit), the column must be wide enough that the secondary sub-line never wraps; otherwise split into two columns. Column widths are content-aware, not header-length-decided — audit undersized compound columns and oversized header-sized columns together.
- **Filters and modes.** Provide a search scoped to key identifiers, filters for primary statuses, and a way to narrow to the current batch/group. An active filter/mode shows as a small clear label above the table, not an extra column.
- **When to redesign the view.** More than one strong status per row, more than one primary action per row, or more than ~10 visible columns at default density → split into separate views or a secondary tab; never extend the main grid indefinitely.

### Analytical mode

The user discovers patterns: trends, period comparisons, anomaly diagnosis.

- **Chart-first**, filters above, supporting tables below as evidence. Charts are always matched with tabular drill-down — never abstract metrics floating alone.
- The "evenly modular analytics cards with flat hierarchy" default (3–6 identical tiles as the opener) is **banned** — it is the generic BI shell. Lead with one or two restrained charts with clear narrative; KPI numbers go in a header summary line.
- **Hybrid pages default to operational mode** unless the dominant task is pattern discovery.

### Analytics in operational mode

Analytics on operational pages must be visually and structurally **subordinate to the worklist** — no analytics element larger than the primary table or displacing it as the focal point. If they compete, reduce analytics prominence.

---

## §G. Detail views

Detail views (drawers or pages) are extensions of operational lists, not separate experiences.

- **Default pattern:** right-side detail drawer anchored to the selected row. Full-page detail is the exception, used only when the workflow cannot fit comfortably in a drawer.
- **Mode:** operational by default — review/verify/update a single record while staying in context.
- **Structure:** header (primary identifier, summary, status pill); body (key fields in ≤3–4 short logical groups); footer (one primary action + clearly-subordinate secondary actions).
- **Visual rules:** same surface, typography, and status system as the list. No hero sections, banners, or marketing layouts. Compact form spacing; sentence-case labels close to inputs. Primary buttons solid/rectangular with the project accent; secondary are neutral-outline or text.

**Hard failures (detail views):** turning the drawer into a mini-dashboard (KPI cards, charts, bento inside it); different badge shapes/colors in detail vs list; centered card-on-gray detail layouts; over-decorated sections.

### API-sourced data: provenance + raw exchange disclosure

Bison tools talk to external systems (a marketplace's Selling Partner API, an accounting API like Xero, integration partners, scrapers, imports). Wherever a detail drawer shows a value **fetched from or pushed to an external API**, the operator must see *where it came from* and *what crossed the wire* — trust and debuggability, not chrome.

- **Quiet provenance label (required).** Any field group whose data is the result of an external exchange carries a quiet provenance tag in the group header (`via SP-API`, `via Xero`, `via Import`, `Snapshot today`) in the demoted §D text treatment. The operator never guesses whether a number is live, imported, scraped, or cached.
- **Raw request/response is one quiet disclosure away.** Each API-backed group exposes a collapsed `Show raw request / response` disclosure (collapsed by default) revealing the outgoing request, the raw response, and exchange metadata (timestamp, status, latency/attempts where relevant).
- **It stays a disclosure, never a console.** Read-only monospace on the drawer surface — no syntax-rainbow theme, no terminal chrome, never auto-expanded. Subordinate to the human-readable fields above it.
- **Surfaces that *write* to an API show the request, not just the result.** An action pushing to an external system must let the operator inspect the outgoing request before/after it fires — an irreversible external write the operator cannot inspect is a trust failure on a tool handling real money.

---

## §H. Dropdowns

Dropdowns are allowed but discouraged — only for short, bounded sets of mutually-exclusive options where hiding the list improves density without slowing the primary workflow.

- **Visual treatment:** a light, neutral floating menu — not an oversized card, pill, or decorative surface. Soft radius, one subtle shadow, compact row height, restrained border; no gradient fills, heavy chrome, or exaggerated elevation. Keep the scope label visible while open; mark the current selection explicitly (checkmark), not by hover alone.
- **Allowed:** short option sets (~3–7 values), single-select, secondary/occasional controls.
- **Avoid when:** the list is long/scrollable; the control is a frequent operational action or primary nav; or segmented controls, radios, inline lists, or direct manipulation would be clearer.
- **Review test — fails if:** it hides a high-frequency action behind an extra click; contains a long/scroll-heavy list; its title row looks disabled/ambiguous; or its styling reads as a generic component-library artifact rather than quiet product UI.

---

## §I. Positive assertions (contract-critical) — the mechanism

The hard-failure list (§E) is the enforcement *floor* (what synthesis must avoid). The family also maintains a positive *allowlist* — the small set of contract-critical patterns synthesis MUST **produce**, not merely avoid violating — so `design-review-pr` can enforce them. The mechanism:

- Each item is a single verbatim assertion traceable to an originating section, expressed in source-agnostic family terms.
- Items are the *load-bearing implementations* of a section (e.g. the floating bulk-action bar is the only implementation of §F "bulk actions live in a table-level action bar" — dropping it silently breaks §F even though no hard failure fires).
- Specific-value assertions (row heights, exact font sizes, spacing) stay **out** — those belong to `design-review` running against rendered DOM.
- A project inherits this allowlist and **appends its own project-unique assertions** (its surface topology, its imagery rules) in its own policy's §12.

Family-level contract-critical assertions (inherited verbatim):

```yaml
positive_allowlist_family:
  - assertion: "Bulk actions on data-heavy tables use a transient floating action bar tied to selection (fixed bottom, neutral card surface, one subtle shadow) — not inline per-row controls, a persistent header toolbar, or a button row above the table."
    source: "§F Data-heavy operational tables"
  - assertion: "Page-opener counts on operational pages use an inline summary line integrated into the page header — not a row of stat cards, KPI tiles, or summary panels."
    source: "§E / §B"
  - assertion: "Filters on operational pages live in a persistent top bar of chips/pills immediately above the table — not in a sidebar, modal, collapsed drawer, or inline column-header dropdowns."
    source: "§B"
  - assertion: "Detail views default to a right-side drawer anchored to the selected row; full-page detail is the exception."
    source: "§G"
  - assertion: "Status indicators use the rectangular pill (rounded-md) with tinted background, 1px tinted border, and neutral text — not rounded-full capsules, pastel pill-with-leading-dot, leading status icons, or saturated fills with white text."
    source: "§C"
  - assertion: "Operational tables are sortable on their meaningful columns (click-to-sort with a visible active-sort indicator), and any table whose rows carry a primary date/time defaults to a most-recent-first chronological sort on that date — never insertion/arbitrary order or alphabetical-by-id."
    source: "§F Sorting and default order"
  - assertion: "On surfaces that share data, any on-screen value that IS a record owned by another surface resolves and EXPANDS that foreign record IN CONTEXT — it opens in the §G right-side detail drawer over the current surface, showing that record's OWN fields and its own linked references (recursively), with related fields surfaced as read-only lookups read through the relation and a round-trip back. It is NOT inert duplicated text and NOT a link whose primary behavior is to navigate away. The affordance stays quiet (demoted accent / subtle hover underline) and uses the §G drawer — never a button, CTA, colored pill, chip, grid, or modal chrome."
    source: "§K"
  - assertion: "Money is rendered basis-complete: every monetary figure declares its VAT basis (inc/excl) where meaningful, foreign-currency amounts from a sourcing lane are labelled as native currency AND framed against GBP (the reporting currency) where a decision depends on the value, and a record's economics are reached via a §J link to the canonical owning record rather than a decontextualised fragment. Amounts use monospace + tabular-nums and never wrap a value from its currency/VAT label."
    source: "§K"
  - assertion: "Financial figures render to two decimal places — money amounts and the derived figures computed from them (ROI, margin, percentage, rate) alike — never under-precise nor spurious; multiples/small ratios keep their compact form (1.8×). Every number carries its unit correctly (currency symbol adjacent, a rate as a percentage not a raw fraction, measures with their unit, quantities as integers), all tabular monospace."
    source: "§K"
  - assertion: "A derived profit / ROI / margin is computed the proper way — sell price minus the complete fee set minus cost, on the declared VAT basis, never a naive sell−buy that omits fees — reaches its breakdown (fee lines + cost + fee-source provenance) via a §J expand, and carries a quiet verified-economics tag ONLY when the breakdown is complete and from the source's real fees; an estimated/incomplete figure reads as provisional, never as a confident decision-ready number."
    source: "§K"
  - assertion: "A detail drawer whose fields are fed by an external API exchange carries a quiet provenance tag in the group header AND a collapsed 'Show raw request / response' disclosure exposing the outgoing request, raw response, and exchange metadata; an action that WRITES to an external system lets the operator inspect the outgoing request. The disclosure is read-only monospace, collapsed by default — never a decorated console."
    source: "§G API-sourced data"
  - assertion: "A comingled snapshot / cross-check surface (≥2 independently-sourced reads shown together) carries PER-SOURCE provenance on each panel (never one card-level tag) and a FORMAL as-of (relative age paired with the absolute pull timestamp), distinguishes never-pulled / not-fetched / empty as separate states, and is an auditable record (clicking it opens its pull audit in the §G drawer). Records named on the card stay §J-clickable; open-in-external is the §J secondary action."
    source: "§L"
```

---

## §J. Cross-surface relational coherence (linked records & lookups)

Bison products are **relational, not isolated**: records reference one another across surfaces (an item links to its orders; orders feed batches/filings; lines carry a supplier, a marketplace, a currency, a status). The design must make this fabric **coherent and navigable** across every surface that touches a shared record. Per-screen compliance (§A–§H) is necessary but not sufficient: a page passes this section only if it also coheres with, and links to, its sibling records.

**The function is expand-in-context, not navigate-away (Airtable's *relation*, our *form*).** Across **most** pages that share data, any on-screen reference to a record *owned by another surface* is a **link that expands that record in context** — not inert text. This is a **functional** requirement about the *relation*, not a visual treatment.

- **Every foreign reference expands the foreign record in context.** Acting on it opens **that foreign record** in the right-side detail drawer (§G) **over the current surface**, showing the foreign record's own fields and its own linked references. The expansion is **recursive** (open a record from a row → from inside it open its related record → each over the last), with a clean **round-trip** back — closing the drawer returns the operator exactly where they were. "Open full {sibling} page →" is a **secondary** action *inside* the expanded record, never the link's default. Inert duplicated text, and a "link" whose only behavior is to navigate away, are both the anti-pattern this kills.
- **Lookups (related fields pulled inline).** A related field the current surface needs is surfaced inline as a **read-only lookup resolved from the canonical record** — never re-keyed per surface — with the underlying record one click away. A lookup displays as quiet text (§D), not an editable field on the borrowing surface.
- **Canonical identifier.** A record appearing on more than one surface uses **one canonical identifier and one consistent linking affordance** everywhere — same read, same format (monospace, §D), same link behavior. No relabel/reformat/re-key per surface.
- **Shared component language.** Sibling operational surfaces share the same status-pill system (§C), filter-chip grammar (§B/§I), right-side detail-drawer pattern (§G), and link affordance. Inventing a bespoke pill set/filter style/detail layout/link treatment for the same class of work is a violation, even if independently policy-clean.
- **Bidirectional, consistent drill.** Related records round-trip in both directions through the established pattern. No dead-end links; no relationship visible from one side only.
- **Linked-records band.** A detail view surfacing related records uses the established quiet grouped band of drill links — not an ad-hoc embedded table, never a mini-dashboard.

**Form is ours.** The expand affordance is the quiet §D link + the §G drawer — **never** blue link pills, chips, grid, button/CTA chrome, or modal chrome.

**Hard failures (relational):** inert non-navigable text for a record owned elsewhere; a foreign reference whose primary behavior is to navigate away; a fake "expansion" showing a re-keyed summary instead of the foreign record's own fields; the same field re-keyed per surface instead of a lookup; a linked reference styled loud (button/CTA/colored pill/chip); a one-directional or dead-end relationship.

**Review test.** Pick any record reachable from two surfaces. Confirm: (1) same identifier, same format; (2) same status-pill language; (3) it **expands in context** in the §G drawer over the current surface (own fields + own links, round-trip back; full sibling page only as a secondary action); (4) any inline related field is a resolved lookup, not a re-keyed copy. If any fails, the surfaces are incoherent and the page fails review regardless of standalone compliance.

---

## §K. Financial and money data

Bison is a **GBP-reporting business that sources/transacts across currencies and runs on VAT.** Money is the single most decision-critical class of data on every surface and the most often rendered carelessly. A monetary figure is never just a number: it has a **basis** (inc/excl VAT), a **currency** (and, when foreign, a relationship to the GBP the business reports in), and an **owning record**. Every surface showing money respects all three or it misleads the operator. This section is the money-specific application of §J (relational coherence) and §D (formatting); where it overlaps them it is more specific and wins.

- **Prefer the link over the fragment.** A record's economics belong to a canonical record. To show money it does not own, a surface surfaces the canonical record as a §J expand-in-context link — not a hand-picked subset with no path to the full economics.
- **If money is shown inline, show it basis-complete** — never a decontextualised number.
- **Every figure declares its VAT basis.** Inc vs excl is never left to inference — an explicit `inc VAT` / `excl VAT` marker, or a per-group declared basis. On a VAT business a bare amount where both bases are plausible is a defect; the distinction is load-bearing for margin maths.
- **Foreign currency is legitimate, but never bare.** A foreign amount from a real lane is not hidden and not "wrong," but it reads as the **native currency, labelled as such**, and — wherever a decision depends on it — is **framed against GBP** with FX basis/as-of noted. Render `€66.17 (DE lane) · ~£X` , not an unexplained `€66.17 · EUR` floating in a GBP app. "Why is this in euros?" must be answered on the surface.
- **Formatting (defers to §D/§F).** Monospace + `tabular-nums`, consistent decimals, currency symbol/ISO adjacent, right-aligned in tables. A value and its currency/VAT label never wrap apart.
- **Financial figures render to two decimal places** — money amounts **and** derived figures (ROI, margin, markup, percentage, an FX/growth rate shown as context): `£593.28`, `ROI 23.45%`, `margin 31.20%`. Never under-precise (a stray `23.4%`) nor spurious (`23.4187%`). Multiples/small ratios keep their compact form (`1.8×`).
- **Every number carries its unit, correctly** — currency symbol adjacent (`£`/`€`/`$`, never a bare ISO code or naked amount), a rate as a percentage (`23%`, not `0.23`), weights/dimensions with their unit, quantities as integers.
- **A derived profit / ROI is proven by its breakdown, or it is not shown as fact.** Profit/ROI/margin are *derived*, trustworthy only when computed properly: **sell price − the complete fee set (all referral/platform/handling/closing fees) − cost**, on the declared VAT basis. A naive `sell − buy` that omits fees is not an ROI — it overstates every deal — and is banned. The figure must **reach its breakdown** (fee lines + cost + fee-source provenance) via a §J expand.
- **A properly-proven profit / ROI is tagged; a provisional one says so.** Only when backed by a **complete breakdown from the source's real fees** (not estimated, not incomplete) does the figure carry a quiet **verified-economics provenance tag** (the §C/§G quiet-tag treatment — small tinted marker or `via SP-API fees` label, no leading dot, never a loud badge). An estimated or incomplete figure must **not** carry it and reads as **provisional** (`est. ROI`, `fees incomplete`), never as a confident decision-ready number. The honest boundary, made universal: *do not promise a profit figure the data cannot back.*

**Hard failures (financial):** money with no VAT basis where the distinction is meaningful; a bare foreign amount with no GBP frame/lane context; a cherry-picked economics fragment with no §J link to the owning record; money re-keyed per surface instead of a §J lookup; a value wrapping away from its currency/VAT label; a financial figure at other than 2dp (multiples excepted); a number with no unit where the unit is meaningful; a profit/ROI computed by omitting fees; a profit/ROI with no reachable breakdown; a provisional figure presented as proven (or carrying the verified tag it hasn't earned).

---

## §L. Comingled snapshot & cross-check surfaces (sourced data)

A **snapshot / cross-check card** is a point-in-time evidence panel presenting *sourced* data — values fetched from an external system at a moment in time — and very often **comingles two or more independently-sourced reads side by side** (a buy-side read next to a sell-side read; one system's figures next to another's). It is a **distinct surface archetype**: not a §G detail drawer (it sits *on* an operational/detail surface as a subordinate evidence panel) and not a §E/§B dashboard tile. Its trustworthiness rides entirely on *which source each number came from and when it was pulled*, so it earns its own provenance/dating/audit discipline. This is the snapshot-specific application of §G, §J, and §K; where it overlaps, it is more specific and wins.

- **Per-source provenance is mandatory and panel-local.** When a card comingles ≥2 sources, **each panel/figure declares its own source** in the quiet §G provenance treatment. A single card-level tag that papers over which side came from where is the failure this kills.
- **Formal dating.** Each sourced panel carries its **absolute as-of timestamp** as the audit anchor; a relative age (`3d ago`) may lead for scannability but never *replaces* the absolute pull time. A snapshot dated only as "3d ago" fails.
- **Distinguish the freshness states honestly (§K boundary).** *Never-pulled* (`Never checked`), *not-fetched* (deliberately not requested — `… : not fetched`), and *empty* (requested, came back with no value — `—`) are three different facts and must read as distinct. Conflating them misleads the operator about whether the gap is theirs to close or the source's.
- **The pull is an auditable, clickable record.** Acting on the snapshot opens the **pull's audit** in the §G drawer — per-source provenance, each source's formal as-of, result/status, and the §G raw request/response of each exchange. Floor: the last pull's full audit. Surface pull history only where it already exists — the policy does **not** mandate building a pull-history store (keep it simple).
- **Records named on the card stay §J-clickable** (expand-in-context, recursive, round-trip). The external-system link (open in the source) is the §J **secondary** action, never the primary behavior. A re-pull control obeys §G write/exchange inspection.
- **Still subordinate, still quiet.** Obeys §B analytics weight and §E anti-default compositions — an evidence panel, not a dashboard. The comingling is a content structure, not a licence for card-grid chrome.

---

## §Z. What stays project-local (tier-3 residue — do NOT lift into this overlay)

These are the sections each Bison project owns and the overlay deliberately omits. Naming them here *is* the decipher — it tells a new project exactly what it must author for itself:

- **Exemplar domain content.** Real records from the specific product (one tool's ASINs/SKUs/suppliers/batches/shipments vs another's invoices/VAT periods/expenses). Policy-first exemplars are a shared *requirement*; the *content* is project-local.
- **Surface topology unique to one product.** e.g. inbound-flow's **multi-handler surfaces** (split-by-view across warehouse handlers / shipping lanes / fulfilment providers) — driven by that product's physical operations, not a family value.
- **Product imagery.** e.g. inbound-flow's **§14 product-thumbnail / face-pile** rules — inventory-specific; the VAT tool has little product imagery.
- **Product-specific exemplars of a shared principle.** e.g. the comingled-snapshot *principle* (§L) is family-wide, but inbound-flow's buy↔sell / Keepa / buy-box examples are project-local.
- **Concrete tokens, routes, and file paths.** The exact token file, `@theme` block, route names, and component file locations — these are the project's `precedence` #1 and live in each project's policy and code.
- **Project-specific hard failures and positive assertions** beyond the family floor — appended in the project's own §5 / §12.

---

## Precedence & maintenance

**Resolution order** (most specific wins): the project's `docs/design-policy.md` → **this overlay** → `shared/design-standards.md` (universal AI-fingerprint rules) → code tokens. A project may override any rule here explicitly; the override lives in the project policy and is recorded in the project's change log.

**Ownership.** This overlay is owned by the Bison Management product family, maintained in the fork's `shared/`. When a rule that the whole family shares changes, change it **here** and let it propagate to every inheriting project on the next sync — rather than editing each project's policy and re-diverging (the hand-port this overlay exists to replace). When a change is genuinely one-product-only, it belongs in that project's policy (§Z), not here.
