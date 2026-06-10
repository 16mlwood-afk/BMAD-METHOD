---
name: 'step-02-derive-expected-graph'
description: 'Derive the EXPECTED edge set from the two authoritative sources — Drizzle schema FKs (literal relations) and the declared relational-edges.yaml (derived/correlated relations the schema can''t encode). Every edge is a CANDIDATE §13 obligation until step-03 confirms the foreign record is actually displayed. A missing edge map is itself a P1 finding.'
nextStepFile: './step-03-walk-edges.md'
---

# Step 2: Derive the Expected Graph

**Goal:** Produce `{expected_graph}` — the set of relational edges that *could* require a §13 link, each tagged by source (`fk` | `declared`) and direction. This is the "expected" half of the two-evidence contract. It is built only from the app's own sources; you never invent an edge.

**Why two sources.** A literal FK (`listing_queue.source_order_id → orders.id`) is authoritative and machine-derivable. But this product's most decision-relevant relationships are *derived* — a correlated `EXISTS`, a join through a link table, a status fold. The Listing Queue's tie to a **warehouse** is exactly this: the SellerSmart push correlates `listing_queue.generated_sku` → `warehouse_order_items` → `warehouse_orders` → a warehouse, with **no literal FK** from the queue row to the warehouse. The schema cannot see that edge. It must be **declared**, or it can't be audited — and silently missing it is how the audit would bless a surface that's actually torn.

---

## AVAILABLE STATE

- `{surface_set}`, `{ownership_map}` (step-01)
- `{project_knowledge}` (the project `docs/`), `{db_access}`

## STATE VARIABLES (set in this step)

- `{schema_edges}` — directed edges from Drizzle FKs
- `{declared_edges}` — directed edges from `relational-edges.yaml` `edges:`
- `{co_view_edges}` — co-view candidates from `relational-edges.yaml` `co_views:` (same-record sibling pairs)
- `{expected_graph}` — the merged candidate set (foreign-record edges + co-view siblings)

---

## EXECUTION SEQUENCE

### 1. Extract schema (FK) edges

Read the Drizzle schema (`{project-root}/src/server/db/schema/*.schema.ts` or the project's schema location). For every foreign key whose **referenced** table is an owned record in `{ownership_map}` and whose **referencing** table is displayed by a surface in `{surface_set}`, emit a directed edge:

```
{from_record}.{fk_column} → {to_record}   (source: fk, owner: {to_record's route})
```

Capture both directions of interest: the forward reference (the surface shows a foreign id) and, where the owning surface lists the referencing records, the reverse (the §13 bidirectional obligation). Note FK columns that are **nullable** — a nullable FK means the foreign record is *sometimes* absent, which step-03 must treat as an empty-state, not a missing link.

### 2. Load declared (derived) edges

Read `{project_knowledge}/relational-edges.yaml`. Each entry is a relationship the schema can't fully express — a correlated existence, a link-table join, a fold, or a literal FK that needs `mandated_lookups` attached. Validate each against the template schema (`relational-edges.template.yaml`): it must name `from`, `to`, `owner_route`, `relation_kind` (`derived` for a non-FK relationship, or `fk-with-lookups` when restating a literal FK only to carry its mandated lookups), the `correlation` (how the edge is computed — the join/EXISTS path, in the app's own terms), and the `mandated_lookups` (the inline fields §13 says the borrowing surface should resolve). Emit a directed edge per entry, `source: declared`.

**If the file is absent:** raise a **P1 finding — `no-declared-edge-map`** and proceed with FK-only edges. State loudly in the eventual report that derived relationships (the SellerSmart push and any link-table join) were **not audited**, and route "create `relational-edges.yaml` from the template" as the first fix. An FK-only audit is a partial audit; it must announce its own blind spot rather than read as complete. (silent-partial-implementation guard.)

**If the file exists but a known derived relationship is missing from it:** you cannot conjure the edge (no-guessed-edges rule). Record `undeclared-derived-edge` as a finding — "the schema shows a link table `X` joining `A` and `B` with no declared edge; if this is an operator-facing relationship, declare it" — and route it to "extend the edge map." Naming the gap is the honest move; inventing the edge is not.

### 2b. Load declared co-views (same-record siblings)

Read the `co_views:` section of `{project_knowledge}/relational-edges.yaml` (separate from `edges:`). Each entry declares a record type rendered by 2+ surfaces in the set — a `master` (all rows) and one or more `partition` views (a status/predicate-filtered slice of the same rows). Validate each against the template (`relational-edges.template.yaml` → CO-VIEWS): it must name `record`, `partition_by`, `surfaces` (each with `route`, `role` ∈ `master`|`partition`, `scope`), and the `shared_contract` booleans (`bidirectional_row_link`, `reconciling_counts`, `consistent_ia`, `shared_vocabulary`, `no_orphaned_partition`). Emit one **co-view candidate** per entry into `{co_view_edges}`, `source: co-view`.

**Scope gate.** A co-view is in scope only when **≥2 of its declared surfaces are in `{surface_set}`** — communication is a property *between* surfaces, unobservable from one. If only the master (or only a partition) is in the set, record the co-view `out-of-scope-candidate` with reason "sibling surface not in the audited set" and name the sibling — don't drop it.

**If `co_views:` is absent but you saw 2+ surfaces render the same record type as a primary subject:** this is the same-record analogue of the missing-derived-edge case. Do not invent it — carry the `undeclared-co-view` finding from step-01 and route it to "declare a `co_view`." (no-guessed-edges rule.)

### 3. Merge into the expected graph

Union `{schema_edges}`, `{declared_edges}`, and `{co_view_edges}` into `{expected_graph}`. De-duplicate the foreign-record edges (a declared edge that restates an FK keeps the richer declared entry, since it carries `mandated_lookups`). Co-view candidates are a distinct kind — they carry a `shared_contract`, not `mandated_lookups`, and step-03 walks them with the CO-VIEW CHECKS, not the §13 lookup checks. For each foreign-record edge:

```
edge:
  from: listing_queue          # referencing record / surface
  to:   warehouse              # owned foreign record
  owner_route: /warehouse
  source: declared             # fk | declared
  relation_kind: derived       # fk | derived
  nullable: true               # foreign record sometimes absent → empty-state, not a gap
  correlation: "generated_sku → warehouse_order_items → warehouse_orders (pushBatchId not null) → warehouse"
  mandated_lookups: [warehouse name, dispatch state]
  direction: forward           # forward | reverse | both
  status: candidate            # every edge starts as a CANDIDATE; step-03 confirms displayed? → in-scope | out-of-scope
```

And for each co-view candidate:

```
co_view:
  record: listing_queue                  # the shared record type
  partition_by: status
  master: /listings/queue                # owns the record
  partition: /listings/queue/triage      # the filtered sibling
  partition_scope: "status IN (CHECK_FAILED, CHECK_ERROR, REJECTED)"
  shared_contract: {bidirectional_row_link, reconciling_counts, consistent_ia, shared_vocabulary, no_orphaned_partition}
  source: co-view
  status: candidate                      # step-03 confirms both surfaces in-set, then runs CV1–CV5
```

Every edge AND every co-view leaves this step as `status: candidate`. Nothing is yet a pass or a fail — step-03 looks at the live surfaces: for an edge, whether the foreign record is *displayed* (→ §13 checks) or *never shown* (→ out-of-scope-candidate); for a co-view, whether ≥2 of its surfaces are in the set (→ CO-VIEW CHECKS) or not (→ out-of-scope-candidate, sibling not audited). Resist the urge to pre-judge from the schema/edge-map; the schema can't see the screen.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit/steps/step-03-walk-edges.md`.

---

## SUCCESS METRICS

- Every FK whose referenced table is an owned record and whose referencing table is in the surface set produced an edge
- The declared edge map was loaded and validated against the template — or its absence raised a P1 with FK-only scope announced
- Derived relationships visible in the schema (link tables) but undeclared are named, not silently skipped
- Every edge carries source, relation_kind, nullable, direction, and starts as `candidate` — none pre-judged

## FAILURE MODES

- Treating the schema as the whole truth and missing every derived relationship (the warehouse case) because no edge map was loaded
- Inventing a derived edge to fill a gap instead of routing "declare it" (no-guessed-edges rule)
- Pre-marking a candidate as a failure from the schema before step-03 confirms the value is even on screen (the false-positive flood)
- Forgetting nullable FKs are empty-states, not missing links — flagging "no link" on a row that legitimately has no foreign record
