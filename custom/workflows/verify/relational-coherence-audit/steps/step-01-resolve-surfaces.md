---
name: 'step-01-resolve-surfaces'
description: 'Ground the input to a concrete surface set, then build the record-ownership map — which route owns which record type. This is the spine the expected graph hangs on: an edge is only a §13 obligation if its target record is owned by a surface in (or reachable from) the set.'
nextStepFile: './step-02-derive-expected-graph.md'
---

# Step 1: Resolve the Surface Set & Ownership Map

**Goal:** Turn the input into (a) `{surface_set}` — the concrete routes under audit — and (b) `{ownership_map}` — record type → the surface/route that owns it. Without the ownership map, "link to that record" has no target; without a grounded surface set, there's no graph.

**The grounding gate is hard.** You must be able to say "audit the §13 linkage among {named routes}" before leaving this step. Auditing the wrong surface set produces confident nonsense — a clean report for pages nobody asked about. If the input won't ground, halt per the workflow's HALT response. This gate fires even under `autonomous_mode`.

---

## AVAILABLE STATE

- the raw input (surface list, domain area, single anchor, or full-sweep)
- `{autonomous_mode}`, `{db_access}`

## STATE VARIABLES (set in this step)

- `{surface_set}` — the routes under audit, each with its page component path
- `{ownership_map}` — record type → owning route + the canonical identifier it's shown with

---

## EXECUTION SEQUENCE

### 1. Resolve the surface set

Map the input to concrete routes:

- **Explicit route list** → use it verbatim; resolve each route to its page component (App Router tree).
- **Domain area** ("the Listings surfaces", "inbound supply chain") → resolve via `nav-config` (the grouped nav sections) to the routes in that group, plus any sibling the schema says shares its records.
- **Single anchor** → expand: read the records the anchor surface displays, follow their schema FKs and declared edges to the owning surfaces, and add those. A single page's §13 coherence is only judgeable against the siblings it links to (or should).
- **Full sweep** → every operational route in `nav-config` that the schema marks as owning or referencing a shared record. Leaf surfaces (auth, settings, standalone upload) are excluded and *listed as excluded* — never silently.

Record `{surface_set}` as `route → page component path`. If a route in an explicit list has no resolvable page, halt and name it — auditing a route that doesn't exist is ungrounded.

### 2. Build the record-ownership map

§13's whole premise is that each shared record has **one owning surface**. Derive `{ownership_map}` from the policy's named siblings plus the schema:

- Start from `docs/design-policy.md` §13's named owners (Catalog items `/catalog-items`, Supply orders `/orders`, Inbound batches `/inbound`, Customs `/customs`, Inventory/Listings `/inventory` `/listings`, Sourcing/Buy list `/sourcing` `/buy-list`) — these are policy-ratified.
- Extend with any record type a surface in `{surface_set}` displays whose owner isn't yet mapped: find the route that renders that record as its *primary* table/detail subject (it owns it) vs merely references it (it borrows it).
- For each owned record, note the **canonical identifier** it's shown with (ASIN, SKU, order number, batch id, …) and its format (monospace per §4) — step-03 checks every borrowing surface shows the same id, same format.

```
{ownership_map}:
  catalog_item   → /catalog-items   (id: ASIN, mono)
  supply_order   → /orders          (id: order number, mono)
  warehouse      → /warehouse        (id: warehouse name/id)
  listing        → /listings        (id: SKU, mono)
  ...
```

If a record is displayed across the surface set but **no** surface owns it (nobody renders it as a primary subject), that's a finding in its own right — a shared record with no home surface to link to. Carry it to step-04 as `ownerless-record` (route: stand up an owning surface, or designate one). Don't drop it.

### 3. Confirm the gate, then proceed

State, in plain English: **"Auditing the §13 linkage graph among: {routes}. Record owners: {map}."** If you can say that, the gate is cleared. If you can't — the input named no surface, or every candidate is a leaf with no shared records — HALT with the workflow's HALT response.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit/steps/step-02-derive-expected-graph.md`.

---

## SUCCESS METRICS

- `{surface_set}` is concrete routes, each resolved to a page component
- `{ownership_map}` covers every record type any surface in the set displays, each with one owner and one canonical identifier
- Excluded leaf surfaces are listed, not silently dropped
- The grounding gate is stated in plain English before proceeding

## FAILURE MODES

- Auditing a surface set the user didn't ask for because the input was vague (intent autonomy — halt instead)
- A record displayed on the set with no owner mapped — leaves step-03 with a link target it can't name
- Treating a leaf surface as in-scope and manufacturing edges for it
- Mapping two owners for one record (the §13 single-owner premise is broken — surface it, don't pick one silently)
