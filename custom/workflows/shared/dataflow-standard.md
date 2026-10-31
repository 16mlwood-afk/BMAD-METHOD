---
name: dataflow-standard
description: Every data flow that crosses a system/repo boundary must be documented as a code-anchored map entry — source, ingress path, payload, direction, authority role — plus the hard "non-flow" separations. The canonical Ingress Map is the single answer to "where does X data come from?". Reference by path; never restate.
contract_version: 1
---

# Data flow standard (STD-DATAFLOW-001)

## The rule

Any data flow that **crosses a system or repo boundary** — a producer→consumer seam, a new
cross-boundary schema/webhook, a pull/push integration — MUST be documented as a
**code-anchored entry in the project's data-flow map** before the seam is relied on. A flow
that isn't on the map is drift: an undocumented seam is invisible, and a silent gap in one is
undetectable until a reconciliation forces it out. (Owner-named after the 2026 mifarma
incident — 9 supplier invoices sat un-ingested for ~2 months in an undocumented
mifarma → accounting-tools → inbound-flow seam.)

This is a **standards-track, code-anchored** doc — the same governance tier as the webhook
contract (`STD-WEBHOOK-001`), not a lightweight ADR. Other docs and specs reference it; they
do not re-derive it.

## When (triggers)

- A new ingress **source**, or a new **cross-boundary schema / webhook route**.
- A **producer→consumer handoff** — one system writes data another system reads.
- A **direction or authority change** on an existing flow (pull↔push, or who is canonical).
- A **"non-flow" boundary** that must be kept separate (document it as a hard rule, below).

## How — the per-flow template (repeatable)

Each flow is one block:

- **Source & domain** — who produces it, which system.
- **Ingress path** — routes, processors, queues, schemas (file-anchored, e.g. `path:line`).
- **Payload** — the entities/fields it carries.
- **Direction** — `pull` (we fetch) vs `push` (they send).
- **Authority** — `canonical source` / `verification authority` / `enrichment-only`.
- **Non-flow constraints** — what it must never cross or drive.

## The Ingress Map (canonical shape)

The single "where does X come from?" table. Worked instance (inbound-flow):

| # | Source | Ingress | Payload | Direction | Authority |
|---|--------|---------|---------|-----------|-----------|
| 1 | **bison-ops** (Chrome scraper) | webhook (`X-API-Key`) → `import-processing.processor.ts` | orders (buying/acquisition) | push | **canonical** (primary order source) |
| 2 | **XLSX upload** | parsers in `infrastructure/importers/` | manual orders | push (operator) | canonical (manual) |
| 3 | **accounting-tools** | `/api/accounting-import/pull` + push (`supplier_purchase.created`) | supplier invoices / costs (mifarma) | both | canonical for cost |
| 4 | **Amazon SP-API** | pull (sweeps + on-demand) / push (listing feeds) | catalog+images, listing status; outbound listings | both | **verification authority** (not primary source) |
| 5 | **SellerSmart / TheFBAPrep** | adapters in `warehouses/adapters/` | prep-centre parcels / tracking | both | enrichment / fulfilment |

## Worked example — Amazon (SP-API), flow #4

Integration lives in `src/infrastructure/sp-api/` (client, LWA auth, rate-limiter, executors).
Amazon is **mostly pull-based**, both directions:

- **Inbound (we pull FROM Amazon):**
  - Catalog / product / images — `src/server/catalog/adapters/sp-api-catalog.adapter.ts`
    (`getCatalogItem` by ASIN), behind `/api/v1/catalog/{lookup,landed-cost,viability}`.
    *(ASIN-keyed — this is why EAN-keyed supplier products, e.g. mifarma, don't get images here.)*
  - Listing existence/status — `getListingsItem` → `offer_published` / `amazon_status`, driven
    by a scheduled sweep: `instrumentation.ts scheduleAmazonVerifySweep()` → `listing-reverify.ts`
    (sp-api-listings queue, ~4h cadence).
- **Outbound (we push TO Amazon):** `listing_queue` → feed submission → `CREATED` on acceptance
  (`listing-queue.service.ts`, `marketplace.config.ts`).

Two labels this example must carry (the non-obvious authority facts):

- **"Acceptance ≠ existence."** `CREATED` = feed accepted, not a live listing; the verify sweep
  is the authority check for `CREATED-but-404` phantoms.
- **"Amazon is a selling-side sink + verification authority, NOT the primary order source."**
  Orders originate from bison-ops/webhooks (#1), not Amazon.

## Non-flow rules (hard separations)

Boundaries that must be documented as **explicit non-flows**, not left implicit:

- **STD-DATAFLOW-001-NF1 — leads ↔ inventory.** The leads pipeline lives in a separate Postgres
  (`postgres-y5ep…`) with incompatible PKs (leads `products.id` integer vs inventory text). Inventory
  must **never join to, read from, or write into** leads tables (and vice-versa). A cross-boundary
  join/write is a defect, not a flow.

## Where these docs live

- A **single-repo ingress map** lives in that repo's `docs/` (e.g. `docs/data-flows.md`).
- A **cross-repo flow** lives in the **hub** repo (the system-of-record) with a **pointer** from
  each participating repo's "Shared knowledge — where to look" section. Reference by path — never
  restate (a restatement that disagrees is drift; log it in `docs/fork-gaps.md`).

## Enforcement tier (classified with enforcement-expert)

Prose is not enforcement — the classification:

- **AWARENESS (PROBABILISTIC):** this standard + each project's data-flow map; the project
  `CLAUDE.md` points at the map. Makes the seam legible; does not guarantee it's kept current.
- **GATE (DETERMINISTIC — the real tier):** a pre-commit/CI check that fails when a **cross-boundary
  schema** (`schema-server/src/schemas/`) or **webhook route** changes **without** a matching
  data-flow-map update — the "seam changed but the map didn't" gap. It guards the *artifact*
  correspondence (change ↔ map), not "an author remembered to document," mirroring the
  `STD-CLOSEOUT-001` template-gate pattern. **Warn-then-gate:** ship warn-only, arm the block only
  after adoption is proven quiet.
- **Runtime authoring** ("did they actually write the block?") stays probabilistic; the deterministic
  tier is what makes an *un-updated* map fail loudly.

Enforcement classification done with `enforcement-expert`; this standard exists precisely to avoid
the *"authored the doc and called it enforced"* anti-pattern. The CI/pre-commit gate is **DEFERRED**
until authored + verified (do not call the standard "enforced" until it lands).
