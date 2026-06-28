---
name: 'step-04-classify-and-route'
description: 'Turn the walked edges into a graph report: every edge a row, every non-compliant edge classified (missing-required-link / unresolved-lookup / one-directional / identifier-drift / edge-map gap) and routed to its lane — re-design via design-handoff, mechanical via quick-spec/quick-dev, or "extend the edge map". Detection ends here; no fixes applied.'
---

# Step 4: Classify & Route

**Goal:** Turn `{walked}` into an actionable graph report. Every edge gets a row; every non-compliant edge gets a disposition and a route. Nothing is silently dropped — including compliant and out-of-scope edges. This workflow ends at the routing boundary; it applies no fixes.

---

## AVAILABLE STATE

- `{walked}`, `{expected_graph}`, `{surface_set}`, `{ownership_map}`, `{server_live}`, `{autonomous_mode}`

## STATE VARIABLES (set in this step)

- `{dispositions}` — the per-edge disposition table

---

## THE LOAD-BEARING SPLIT

Before routing, resolve every non-compliant edge to one class. The split decides the lane, and getting it wrong wastes the wrong team's time:

- **Missing-required link** (`inert-reference`, or a displayed foreign record the surface gives no drawer/lane for) → the surface needs to *express* a relationship it currently doesn't. That's an **information-architecture** decision — how should this link look and sit. Routes to **re-design**.
- **Mechanical** (`unresolved-lookup`, `identifier-drift`, `loud-affordance`, a broken round-trip on an otherwise-present link) → the relationship is expressed; a join, a formatter, a styling fix, or a return-path is missing. Routes to **`quick-spec`/`quick-dev`**.
- **Edge-map gap** (`no-declared-edge-map`, `undeclared-derived-edge`) → the audit's own input is incomplete. Routes to **"extend `relational-edges.yaml`"** — and a re-run.
- **Structural** (`ownerless-record` from step-01) → a shared record with no owning surface. Routes to a design decision about where it should live.
- **Co-view seam** (the CV verdicts) → splits the same way the foreign-record edges do, by *relationship-vs-mechanism*. **Seam-as-IA** (`no-row-link`, `ia-divergence`, and a missing-direction `one-directional-coview`) → the two pages don't express the relationship at all, or express it with structurally different IA; *how the master and partition communicate* is an information-architecture question → **re-design**. **Seam-as-mechanism** (`count-drift`, `vocabulary-drift`, `orphaned-partition` wiring, a broken return on an existing cross-link) → the relationship is expressed; a count derivation, a status→label mapping, or an exception-chip route is off → **`quick-spec`/`quick-dev`**. **Undeclared co-view** (from step-01/02) → **"declare a `co_view` + re-run."**

The honest edge case, mirroring the content-lane cede: when a `loud-affordance` is the *only* defect, it's mechanical (restyle the existing link); but when the link is *absent entirely* and adding it raises "where does the drawer come from, what does it show," that's re-design. Decide by asking *is there a link affordance to fix, or a relationship to design?* — the first is `quick-dev`, the second is `design-handoff`. **For a co-view seam the design lane is special: it cannot be designed from one page in isolation — the seam is a property *between* the two surfaces, so its `design-handoff` is a material revision spanning both (and, where the partition view post-dates the master's redesign, it inherits the master's settled patterns rather than re-inventing them).**

## ROUTING RULES

| Verdict / class | Route | Framing |
|---|---|---|
| **Missing-required link** (`inert-reference`; displayed-but-unlinkable) | `design-handoff` (material revision for that surface) | "Surface `{S}` shows `{foreign record}` but doesn't link to it. Re-design the linked-records affordance (§7 drawer expand-in-context + 'Open full {owner} →'), §13 quiet styling." Carries §13 provenance so the brief isn't silent on it. |
| **Unresolved lookup** | `quick-spec` → `quick-dev` | "Link to `{record}` exists; resolve its mandated lookups `{fields}` from the canonical record (add the join), render as quiet read-only text — not re-keyed." Mechanical; no re-design. |
| **Loud affordance** (only defect) | `quick-dev` | "Demote the `{record}` link from button/CTA/pill to the §4 quiet link affordance." |
| **One-directional / dead-end** | reverse link absent → `design-handoff` for the surface missing it; broken round-trip on an existing link → `quick-dev` | "Make `{A}↔{B}` traversable both ways with a round-trip back." |
| **Identifier drift** | `quick-dev` | "Align `{record}`'s identifier/format/label on `{S}` to the canonical form on `{owner}` (`{canonical}`). Content-lane formatter fix." |
| **Edge-map gap** (P1) | extend `{relational_coherence_home}/relational-edges.yaml` (template beside this workflow) → re-run | "Derived relationships were not audited. Declare `{edge(s)}` in the maintained edge map and re-run for full coverage." |
| **Ownerless record** | `design-handoff` / design decision | "Shared record `{R}` is displayed but owned by no surface — designate or stand up an owner before linking can resolve." |
| **Co-view: `no-row-link` / `ia-divergence`** | `design-handoff` (material revision spanning **both** surfaces) | "`{master}` and `{partition}` are two views of `{record}` that don't communicate: no per-row link between an entry's two views / divergent IA (`{detail}`, e.g. v7 handler-split on one, flat on the other). Design the seam — per-row in-context cross-link both ways + a shared partition IA — across both pages." |
| **Co-view: `count-drift` / `vocabulary-drift` / `orphaned-partition`** | `quick-spec` → `quick-dev` | "The `{master}`↔`{partition}` relationship is expressed; reconcile the `{count}` against the shared scope / align the `{state}` label across both / route the master's exception chip into the partition view. Mechanical." |
| **Co-view: `one-directional-coview`** | missing direction → `design-handoff` (the surface lacking the link); broken return on an existing cross-link → `quick-dev` | "Make `{master}`⇄`{partition}` traversable both ways with a round-trip back." |
| **Undeclared co-view** | declare a `co_view` in `relational-edges.yaml` → re-run | "Two surfaces render `{record}` as a primary subject with no `co_views:` entry — the seam was not audited. Declare it and re-run." |

When the choice between re-design and mechanical is genuinely ambiguous, prefer routing to `design-review` (audit) over guessing — a wrong mechanical fix bolts a link onto a page that needed rethinking.

## EMIT THE DISPOSITION TABLE

Every walked edge becomes one row — **including `compliant` and `out-of-scope-candidate`**. This is the silent-partial-implementation guard: a reader can tell, without asking, that the whole graph was covered and exactly what was excluded and why.

```markdown
## Relational Coherence Audit — {surface set}

{if not server_live, emit this banner as the FIRST line — loud, unmissable:}
> ⚠ **ACTUAL SIDE NOT RUN — STRUCTURAL-ONLY AUDIT.** The live surface/DB was unreachable ({reason — e.g. `DATABASE_URL` is an internal `*.railway.internal` host and no `docs/deployment.md` read-only proxy was found}). Every edge verdict below is derived from schema + source, **NOT confirmed against a live render**, and any *count* the request asked for is **NOT a verdict here** — it ships as a hand-off query to run once a read-only actual-side path exists. Re-run this audit then for decision-grade findings.

**Surfaces:** {N routes}  |  **Edges:** {M expected} ({fk}/{declared})  |  **Evidence:** {live | partial-static (structural-only)}  |  **Edge map:** {present | ABSENT (P1)}

| # | Edge ({from} → {to}) | Src | Displayed | Verdict | Class | Route |
|---|----------------------|-----|-----------|---------|-------|-------|
| 1 | listing_queue → warehouse | declared | yes | inert-reference | missing-required-link | design-handoff (/listings/queue) |
| 2 | listing_queue → supply_order | fk | yes | unresolved-lookup | mechanical | quick-dev (resolve supplier, buy-cost) |
| 3 | listing_queue → catalog_item | fk | yes | compliant | — | — |
| 4 | order → customs_entry | fk | no | out-of-scope-candidate | — | not displayed on /orders |
| … |

**Co-views** (same-record siblings — a row per co-view, **every** CV check accounted for):

| # | Co-view ({master} ⇄ {partition}) | In-scope | Failing CV checks | Class | Route |
|---|----------------------------------|----------|-------------------|-------|-------|
| C1 | /listings/queue ⇄ /listings/queue/triage | yes | no-row-link, count-drift, ia-divergence, vocabulary-drift | seam (IA + mechanical) | design-handoff (seam, both surfaces) + quick-dev (counts, vocab) |
| … |

### Coverage
- Expected edges: {M}  ({in-scope: x} / {out-of-scope: y})  ·  Co-views: {K}  ({in-scope: k} / {out-of-scope: j})
- Compliant: {n edges} / {n co-views}
- Missing-required link (→ re-design): {n}
- Unresolved lookup / drift / loud / round-trip (→ quick-dev): {n}
- One-directional: {n}
- Co-view seam-as-IA (→ design-handoff, spans both surfaces): {n}
- Co-view seam-as-mechanism (→ quick-dev): {n}
- Edge-map / co-view-map gaps (→ declare + re-run): {n}
- Evidence: {live: a} / {inferred-static: b}

### Top priority
1. {highest-severity torn edge or co-view seam + its route}
```

Write the report to `{implementation_artifacts}/relational-coherence-audit-{scope-slug}-{date}.md` — the same read-only-audit output convention as `webhook-contract-check`. Do NOT write it into a git-tracked `docs/` path: this is a no-worktree run, and the parallel-session edit-guard hook hard-blocks Edit/Write outside a worktree, so a `docs/relational-coherence/reports/` write would be **refused mid-run**. (To retain a report beside the edge map, promote it into `docs/relational-coherence/reports/` afterward as a deliberate committed step under worktree → PR delivery — not part of this audit. See `workflow.md` → "Declared edge map (read-only input) — and where the report goes".)

## HAND-OFF

- **Autonomous mode:** do not halt. Present the report, and for each non-compliant edge state the exact next workflow, copy-paste-ready — e.g. *"Run `/bmad:bmm:workflows:design-handoff` for `/listings/queue` to add the warehouse linked-record"* or *"Run `/bmad:bmm:workflows:quick-spec` to resolve the supply-order lookups."* Do not invoke them — routing is the boundary.
- **Interactive mode:** present the report, then offer to kick off the top-priority route. Let the user choose.

In both cases the routed lane owns the change, in its own worktree, under its own rules. A `design-handoff` routed from here should be flagged **material revision** so it supersedes the surface's prior brief rather than spawning a second active one (brief-revision-policy). This workflow has delivered its value — the graph verdict and the routes — and stops.

---

## SUCCESS METRICS

- Every edge (compliant, torn, and out-of-scope) has a disposition row — the whole graph is visible, nothing dropped
- Missing-required links route to re-design; mechanical defects route to quick-dev; edge-map gaps route to "declare + re-run"
- The report names which verdicts are live-render vs static-inferred
- A routed design-handoff is marked material-revision (supersedes, not duplicates)
- No fixes applied; no code or data written

## FAILURE MODES

- Dropping compliant or out-of-scope edges from the table (reader can't tell the graph was fully covered)
- Routing a missing-required link to `quick-dev` (bolts a link onto a surface that needed re-design)
- Routing an unresolved lookup to `design-handoff` (a whole re-design for a one-line join)
- Spawning a fresh design-handoff brief instead of a material revision (two active briefs for one surface — brief-revision-policy violation)
- Invoking the routed workflow instead of handing off (this workflow detects + routes; it does not fix)
- Reporting an FK-only run as complete when the edge map was absent (announce the blind spot — P1)
