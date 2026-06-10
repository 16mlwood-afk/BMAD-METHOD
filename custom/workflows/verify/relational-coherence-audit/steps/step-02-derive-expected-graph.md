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
- `{declared_edges}` — directed edges from `relational-edges.yaml`
- `{expected_graph}` — the merged candidate edge set

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

### 3. Merge into the expected graph

Union `{schema_edges}` and `{declared_edges}` into `{expected_graph}`. De-duplicate (a declared edge that restates an FK keeps the richer declared entry, since it carries `mandated_lookups`). For each edge record:

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

Every edge leaves this step as `status: candidate`. Nothing is yet a pass or a fail — step-03 looks at the live surface to decide whether the foreign record is *displayed* (→ in scope, walk the §13 checks) or *never shown* (→ out-of-scope-candidate, named not failed). Resist the urge to pre-judge from the schema; the schema can't see the screen.

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
