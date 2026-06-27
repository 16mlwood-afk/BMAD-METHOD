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

#### 2a. Lookup-drawer target redirect — route, never bounce (destination vs relationship)

A §13 expand-in-context **lookup drawer** (the small drawer that opens *over* a surface when you act on a foreign reference — a `catalog-lookup` over an order, a `warehouse-lookup`, a `supply-source-lookup`) is **owned by the relation, not by a page** (Deliverable-Completeness Principle; brief-template §2a). It is drawn as a **frame in its parent surface's §7 Surface Inventory**, never as its own brief — a separate brief for it would be a duplicate of an already-owned frame and trip the brief-revision-policy multiple-active-brief invariant. So **`design-handoff` does not accept a lookup drawer as a standalone target** — but it must **route**, not reject opaquely (the user targeted it because the drawer is shipping thin; bouncing them with no path is the friction this gate kills).

**Detect.** The resolved target is a lookup drawer when it is a §13 expand-in-context drawer over another surface — signals: the component is a `*-record-drawer` / `*-lookup` that renders a foreign record keyed by an FK/derived edge (an ASIN, warehouse, supply source, batch) opened from a parent surface; the user describes it as "the X drawer/link when I click Y on Z"; it has no route of its own. (When ambiguous between a lookup drawer and a real drilled detail drawer that owns a page/route, treat it as a normal target — only the relation-owned lookup redirects.)

**Redirect (do NOT produce a standalone brief).** Identify the parent surface (the one the drawer opens *over*) and emit:

```
design-handoff — lookup-drawer target redirected (not rejected).

"{target}" is a §13 expand-in-context lookup drawer. It is owned by the
RELATION, so it is drawn as a frame in its parent surface's §7 Surface
Inventory — never its own brief (that would duplicate an owned frame and
break the multiple-active-brief invariant). Destination vs relationship:
a destination (a real page / deep /[id] route) gets a handoff; a
relationship (a lookup over a parent) rides its parent's brief.

It is shipping thin because of WHERE in the pipeline it was missed — pick
the matching fix:

  • Its parent brief's §7 already lists it as a frame, but it was never
    DRAWN → re-run design-synthesize on the PARENT brief (now §7-aware:
    every Surface Inventory frame becomes a rendered screen), then
    design-implement to build the drawn frame. ← most common; this is the
    render gap, not a design gap.

  • Its parent brief has NO §7 frame for it (older brief) → re-run
    design-handoff on the PARENT surface "{parent}" (material revision) so
    step-01 §5f enumerates the lookup drawer into §7, then synthesize +
    implement.

  • You want the foreign RECORD itself redesigned everywhere it expands →
    run design-handoff on that record's OWNING surface "{owner_route}"
    (material revision), not on this one drawer instance.

Parent surface: {parent}   ·   Foreign record / owner: {record} / {owner_route}
```

Then **halt this run** (no brief produced). This is a routing redirect, not a failure — state the chosen next command so the user can run it directly. (Autonomous mode does not override this: producing the duplicate brief is an *intent* violation, not a decision the flag licenses.)

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

Project design-policy **§13 (Cross-surface relational coherence — linked records & lookups)** is a **contract-critical §12 assertion that `design-review-pr` enforces as a hard failure**: any on-screen value that IS a record *owned by another surface* (ASIN, SKU, order number, batch, shipment, supplier, customs entry, listing, …) must **resolve and expand that foreign record in context** — never inert duplicated text, and **never a link that merely navigates away** to the sibling page. The §13 function is **expand-in-context, not navigate-away**: acting on the reference opens the foreign record in the project's §7 right-side drawer *over* the current surface, showing that record's own fields and its own linked references (recursively), with related fields surfaced as lookups read through the relation. Because this brief withholds the current layout (blank canvas), the one place that linking was visible is gone; if the brief is silent on it, the redesign defaults to inert text and **fails review on the way back in**. So derive the inventory here — mechanically, the same anti-recall way as the data surface (§3) and the mutation audit — never leave it for the designer to rediscover.

**Seed from the maintained linkage map first (don't rediscover).** The project keeps a maintained relational-coherence home at `docs/relational-coherence/` — `relational-edges.yaml` (the hand-maintained edge + co-view map: which on-screen value IS a record another surface owns, including the *derived* relationships the schema can't express, like the SellerSmart warehouse push) and `reports/relational-coherence-audit-*.md` (the latest §13 graph audit, already walked against the live surface by Wren / the relational-coherence-audit). **Read both for this surface before deriving anything.** They are the authoritative, already-resolved source — every edge whose `to` is owned by another surface and whose `from` is this surface seeds a `{linked_records_inventory}` entry with its `owner_route`, expand-in-context target, and `mandated_lookups` carried straight through. If a relational-coherence-audit routed this handoff (a missing-required link or a co-view seam), its §2a seed is already attached — use it verbatim, don't re-derive. If the map exists but omits a foreign reference you find below, that's a gap — note it and route "declare it" back to the audit (no-guessed-edges), never invent the edge in the brief. The derivation below is the cross-check (and the fallback when the home is absent), not the primary source.

**Derive (don't recall).** From the `{data_shape}` and route just mapped — cross-checked against the maintained edge map above — for **each** field that resolves to a record another surface owns (start from the foreign keys / natural keys flattened in §3 step 4 — `supplier`, `asin`, `order_number`, `batch_id`, …):
1. **Foreign reference** — the field/identifier as it appears on this surface.
2. **Owning surface** — which surface owns that record, and its route (`/suppliers/[id]`, `/catalog/[asin]`, …). If no surface owns it yet, say so — it is a plain value, not a link, and does not belong in the inventory.
3. **Expand-in-context target (§7 drawer, NOT navigate-away)** — acting on the reference opens **the foreign record** in the right-side **detail drawer** (§7) *over the current surface*, showing that record's own fields and its own linked references (recursive). Name the foreign record that expands and the §7 drawer as the expand surface. Crossing to the sibling's full page ("Open full {sibling} →") is a **secondary** action *inside* the expanded record — note it as secondary, never as the primary drill. A reference whose only behavior is to navigate to the sibling page is a §13 hard failure.
4. **Inline lookups** — any *related field* this surface needs from that foreign record to make its decision (a supplier's lead-time, a catalog product's image/title on an order line, an order's marketplace/currency on a batch). These render as **read-only** lookups read *through the relation* from the canonical record — never re-keyed per surface.

Set `{linked_records_inventory}` — one entry per foreign reference, each with the four facts above. **Empty only when nothing on the surface resolves to a foreign record** (a true leaf surface); empty-by-omission is the silent failure this step exists to prevent — the §13 mandate is invisible to the designer unless this inventory carries it into the brief. The §13 *form* guardrail (the affordance is the quiet demoted-blue §4 link + the §7 drawer, **never** a button, CTA, colored pill, chip, or Airtable modal chrome) travels with the inventory into brief §2a — Airtable's **relation** imported (expand-in-context + lookups), Airtable's **form** rejected.

### 3b. Finance-domain pass — semantics a blank-canvas redesign must preserve (conditional)

Fires **only when finance presentation is material** to the surface — money is a primary data type
(not an incidental field); the operator reviews/reconciles quantities, values, balances, costs, taxes,
landed costs, or variances; the data is inventory/ledger/payout/statement/VAT/reconciliation/accounting
export; or mispresenting missing/estimated/anomalous/duplicate-grouped values could distort financial
truth. **Skip** (`{is_finance_surface}` = `false`) when money is a minor field on a general CRUD page,
the task is pure styling/layout, or another domain owns the semantics; if uncertain, fire only when bad
presentation could distort operational or financial truth, else proceed without it and note the
ambiguity. (Full gate: `finance-domain-pass` "When to invoke".) Finance surfaces hide load-bearing semantics inside the layout this
brief withholds (lifecycle states, quantity/value separation, reconciliation, exceptions); without this
pass a blank-canvas redesign silently drops them or guesses them as taste. This pass captures the
finance **meaning** — never the layout.

**Invoke the skill (mode: extract).** Load `finance-domain-pass` via the Skill tool and pass it:
- the **source artifact** (the data file / page / export the handoff is about),
- the **`{data_shape}`** and **`{linked_records_inventory}`** just derived (§3, §3a),
- read-only awareness of `docs/design-policy.md` (so it surfaces collisions as open questions, never overrides).

The skill runs its procedure (detect type → column semantics → capabilities-as-outcomes → shed-capability
flags → exception expectations → implied surfaces → unresolved assumptions → terminology → must-not-infer)
and returns its **appendix object**. It governs finance meaning, NOT layout — it never names a bar, card,
drawer, or composition. Capture it and route each field into the existing machinery:

| Appendix field | Captured / routed into |
| --- | --- |
| `report_type_detected` | `{finance_report_type}` — a §1 context signal; does **not** set `{page_mode}` or composition |
| `source_column_semantics` | `{finance_column_semantics}` — enriches `{data_shape}` (Domain Data); never blends qty + value |
| `must_preserve_capabilities` | **merge into** `{must_support_capabilities}` (§4) — as outcomes |
| `dropped_capability_flags` | **cross-check into** `{dropped_capabilities}` (§3 mutation audit) — confirm each, don't auto-drop |
| `exception_expectations` | `{finance_exception_expectations}` — representability requirements (NOT a panel design) |
| `implied_surfaces` | **feed §5f** `{spawned_surfaces}` as candidates (frame-name keyed, depth-1; §5f reconciles + owns the final inventory) |
| `unresolved_assumptions` | `{finance_unresolved_assumptions}` — rendered as brief Open Questions; **never resolved here** |
| `terminology` | `{finance_terminology}` — canonical terms for brief labeling |
| `must_not_infer` | `{finance_must_not_infer}` — acceptance constraints preserving accounting truth |
| `policy_collisions` | surface to the user as `modify-design-policy` candidates — do **not** patch the brief around policy |

**Outcomes, never mechanics.** If any captured capability or surface can't be stated without naming a
component, it was a layout leak — drop it. **Never resolve an unknown:** a flagged `unresolved_assumption`
(status source-of-truth, valuation/costing basis, block/line semantics, FX basis) goes to the brief's
Open Questions verbatim; the pass never decides it and the brief never invents it.

**Fallback (skill not synced).** If `finance-domain-pass` is absent (older sync), apply the same
procedure inline using `{project-root}/_bmad/bmm/workflows/shared/` finance conventions + the
`finance-presentation` standard, and populate the same capture fields by hand. The skill is preferred
(it makes the must-not-infer and capability outputs mandatory rather than skippable prose), but handoff
must not hard-fail when it is absent.

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


---

**Next — the gather continues in two focused sub-steps (split out of this file for context budget; same content, no behaviour change):**

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01b-decide.md` (§5 page mode → §5a composition → the §5b–§5c-3 analytics decision stack), then it chains to `step-01c-topology.md` (§5d topology → §6 user context → COMPLETION) and on to step-02.
