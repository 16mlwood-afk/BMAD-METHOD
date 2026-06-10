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
- `{ownership_map}` — record type → owning route + the canonical identifier it's shown with (the `master` is the owner for a co-viewed record)
- `{co_views}` — declared same-record sibling pairs from `relational-edges.yaml` `co_views:` (record + master/partition surfaces + scopes + shared_contract), for step-02 to merge into the expected graph

---

## EXECUTION SEQUENCE

### 0. Read the ask in plain English

The input is **natural language first** — routes are an optional shorthand, not the expected form. A human asks this workflow the way they'd ask a colleague: *"is the listing queue properly linked to its records?"*, *"check the linking between listings and the warehouse"*, *"audit the inbound supply-chain pages for broken links"*, *"does /orders link everything it should?"*. Pick the **verbs and nouns** out of that sentence and map them to surfaces via `nav-config` (label → route) and the ownership map (record name → owning route). A page label ("listing queue"), a domain area ("inbound supply chain"), a record type ("warehouse"), or a raw route (`/orders`) are all valid handles — resolve whichever the user used. Only fall back to treating the input as a literal route list when the user actually typed routes.

You do **not** need the user to phrase it as a command or hand you two routes. If a friendly sentence names enough to ground a surface set, ground it and proceed. If it's friendly but *under*-specified, go to step 1's offer path — don't make them re-type it as machine input.

### 1. Resolve the surface set

Map whatever you extracted in step 0 to concrete routes:

- **Explicit route list** → use it verbatim; resolve each route to its page component (App Router tree).
- **Domain area / page label** ("the Listings surfaces", "inbound supply chain", "the listing queue") → resolve via `nav-config` (the grouped nav sections / labels) to the routes in that group, plus any sibling the schema says shares its records.
- **Single anchor** (one page or one record named) → expand: read the records the anchor surface displays, follow their schema FKs and declared edges to the owning surfaces, and add those. A single page's §13 coherence is only judgeable against the siblings it links to (or should).
- **Full sweep** → every operational route in `nav-config` that the schema marks as owning or referencing a shared record. Leaf surfaces (auth, settings, standalone upload) are excluded and *listed as excluded* — never silently.

Record `{surface_set}` as `route → page component path`. If a route in an explicit list has no resolvable page, halt and name it — auditing a route that doesn't exist is ungrounded.

#### 1a. When the ask is under-specified — OFFER scopes, don't demand them

If step 0 leaves the surface set ambiguous — the user said "check our linking" or "is this page linked right?" without pinning a clear set — **do not bounce them back to re-type a command.** Derive 2–4 candidate audit scopes and **offer them as a recommendation menu**, most-leverage first. Candidates come from the same two sources the audit already reads, so they're grounded, not invented:

- **the anchor's neighbourhood** — if any page/record was named, its schema-FK + declared-edge neighbours (e.g. *"Listing queue + the records it touches: orders, catalog items, warehouse"*).
- **a nav cluster** — the `nav-config` group the named page sits in (e.g. *"All Listings surfaces"*).
- **a single hot edge** — one specific relationship worth checking alone (e.g. *"Just the listing-queue → warehouse link"*).
- **full sweep** — every shared-record surface (named as the thorough/slow option).

Present each in **plain language with what it covers and why it's worth it**, recommend one, and let the user pick. This is **not** intent autonomy — you're surfacing *derived* candidates for the user to choose among, never guessing which one they meant and running it silently. The pick becomes `{surface_set}`; then continue to step 2.

**Autonomous mode:** don't render a menu — choose the highest-leverage candidate (the named anchor + its schema neighbours, or the obvious nav cluster) and proceed, **stating the scope you chose** in one line so the run is auditable. Reserve the hard halt for genuinely ungroundable input (step 3).

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

#### 2a. Co-viewed records — the single-owner carve-out

The single-owner premise above has one **declared** exception: a record type that a `co_views:` entry in `relational-edges.yaml` says is rendered by **2+ surfaces** on purpose — a `master` view (all rows) plus one or more `partition` views (a status/predicate-filtered slice of the *same* rows). The Listing Queue (master) and the Listing Upload Triage desk (the failure-tail partition) are the canonical pair.

- This is **not** a dual-owner defect and must **not** be flagged as one (it's the legitimate other-relation, audited by the CO-VIEW CHECKS, not the §13 lookup checks). The declared `master` is the record's owner in `{ownership_map}`; the `partition` surfaces are recorded as **co-viewers** of that record, not rival owners.
- If you encounter two surfaces in the set rendering the same record type as a primary subject with **no** `co_views:` declaration, do **not** invent the relationship and do **not** flag a dual-owner break — record it as an **undeclared co-view** finding and route it to "declare a `co_view` in `relational-edges.yaml`," exactly as an undeclared derived edge is routed (no-guessed-edges rule).

Carry the declared co-views forward as `{co_views}` for step-02 to merge into the expected graph.

### 3. Confirm the gate, then proceed

State, in plain English: **"Auditing the §13 linkage graph among: {routes}. Record owners: {map}."** If you can say that — whether the user named the surfaces or picked them from the offer in step 1a — the gate is cleared.

**HALT is the last resort, not the first response to vagueness.** Only hard-halt when the input is genuinely ungroundable *and* the offer path can't help: nothing in the sentence names or implies any surface, the nav tree yields no candidate to even offer, or every candidate is a leaf with no shared records (no graph to audit). A vague-but-anchorable ask ("check our linking") is handled by the step-1a offer, not a halt — halting on it would be the exact "very computer input" friction this workflow's trigger is meant to avoid.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit/steps/step-02-derive-expected-graph.md`.

---

## SUCCESS METRICS

- A natural-language ask was accepted as-is — the user was not required to phrase the input as a command or a route list
- An under-specified ask was met with a derived **offer of candidate scopes** (interactive) or a stated highest-leverage default (autonomous), not a bounce-back halt
- `{surface_set}` is concrete routes, each resolved to a page component
- `{ownership_map}` covers every record type any surface in the set displays, each with one owner and one canonical identifier
- Excluded leaf surfaces are listed, not silently dropped
- The grounding gate is stated in plain English before proceeding

## FAILURE MODES

- Demanding routes / a command form when a plain-English ask named enough to ground (the "very computer input" friction this trigger exists to avoid)
- Hard-halting on a vague-but-anchorable ask instead of offering derived candidate scopes (step 1a)
- The opposite error: *running* a guessed scope silently instead of offering it (intent autonomy — offer and let the user pick, or in autonomous mode state the chosen scope)
- A record displayed on the set with no owner mapped — leaves step-03 with a link target it can't name
- Treating a leaf surface as in-scope and manufacturing edges for it
- Mapping two owners for one record (the §13 single-owner premise is broken — surface it, don't pick one silently) — UNLESS a `co_views:` entry declares the pair, in which case it's the legitimate co-view carve-out (§2a): the `master` owns it, the `partition` views are co-viewers, and it's audited by the CO-VIEW CHECKS, not flagged as dual-owner
- Treating an undeclared same-record sibling as a dual-owner defect, or inventing the co-view yourself — route "declare a `co_view`," don't conjure or mis-flag it
