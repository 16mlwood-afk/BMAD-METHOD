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

The honest edge case, mirroring the content-lane cede: when a `loud-affordance` is the *only* defect, it's mechanical (restyle the existing link); but when the link is *absent entirely* and adding it raises "where does the drawer come from, what does it show," that's re-design. Decide by asking *is there a link affordance to fix, or a relationship to design?* — the first is `quick-dev`, the second is `design-handoff`.

## ROUTING RULES

| Verdict / class | Route | Framing |
|---|---|---|
| **Missing-required link** (`inert-reference`; displayed-but-unlinkable) | `design-handoff` (material revision for that surface) | "Surface `{S}` shows `{foreign record}` but doesn't link to it. Re-design the linked-records affordance (§7 drawer expand-in-context + 'Open full {owner} →'), §13 quiet styling." Carries §13 provenance so the brief isn't silent on it. |
| **Unresolved lookup** | `quick-spec` → `quick-dev` | "Link to `{record}` exists; resolve its mandated lookups `{fields}` from the canonical record (add the join), render as quiet read-only text — not re-keyed." Mechanical; no re-design. |
| **Loud affordance** (only defect) | `quick-dev` | "Demote the `{record}` link from button/CTA/pill to the §4 quiet link affordance." |
| **One-directional / dead-end** | reverse link absent → `design-handoff` for the surface missing it; broken round-trip on an existing link → `quick-dev` | "Make `{A}↔{B}` traversable both ways with a round-trip back." |
| **Identifier drift** | `quick-dev` | "Align `{record}`'s identifier/format/label on `{S}` to the canonical form on `{owner}` (`{canonical}`). Content-lane formatter fix." |
| **Edge-map gap** (P1) | extend `relational-edges.yaml` (template beside this workflow) → re-run | "Derived relationships were not audited. Declare `{edge(s)}` and re-run for full coverage." |
| **Ownerless record** | `design-handoff` / design decision | "Shared record `{R}` is displayed but owned by no surface — designate or stand up an owner before linking can resolve." |

When the choice between re-design and mechanical is genuinely ambiguous, prefer routing to `design-review` (audit) over guessing — a wrong mechanical fix bolts a link onto a page that needed rethinking.

## EMIT THE DISPOSITION TABLE

Every walked edge becomes one row — **including `compliant` and `out-of-scope-candidate`**. This is the silent-partial-implementation guard: a reader can tell, without asking, that the whole graph was covered and exactly what was excluded and why.

```markdown
## Relational Coherence Audit — {surface set}

**Surfaces:** {N routes}  |  **Edges:** {M expected} ({fk}/{declared})  |  **Evidence:** {live | partial-static}  |  **Edge map:** {present | ABSENT (P1)}

| # | Edge ({from} → {to}) | Src | Displayed | Verdict | Class | Route |
|---|----------------------|-----|-----------|---------|-------|-------|
| 1 | listing_queue → warehouse | declared | yes | inert-reference | missing-required-link | design-handoff (/listings/queue) |
| 2 | listing_queue → supply_order | fk | yes | unresolved-lookup | mechanical | quick-dev (resolve supplier, buy-cost) |
| 3 | listing_queue → catalog_item | fk | yes | compliant | — | — |
| 4 | order → customs_entry | fk | no | out-of-scope-candidate | — | not displayed on /orders |
| … |

### Coverage
- Expected edges: {M}  ({in-scope: x} / {out-of-scope: y})
- Compliant: {n}
- Missing-required link (→ re-design): {n}
- Unresolved lookup / drift / loud / round-trip (→ quick-dev): {n}
- One-directional: {n}
- Edge-map gaps (→ declare + re-run): {n}
- Evidence: {live: a} / {inferred-static: b}

### Top priority
1. {highest-severity torn edge + its route}
```

Write the report to `{implementation_artifacts}/relational-coherence-audit-{scope-slug}-{date}.md`.

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
