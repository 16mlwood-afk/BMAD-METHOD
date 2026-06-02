---
name: 'step-04-route'
description: 'Emit a per-finding disposition table and route each finding to its fix lane: render gaps to design/wire, data rot to the producer-fix lane (quick-spec/quick-dev) framed under the data-quality root-cause rule. Detection ends here; no fixes applied.'
---

# Step 4: Route

**Goal:** Turn `{classified}` into an actionable report. Every finding gets an explicit disposition and a route. Nothing is silently dropped. This workflow ends at the routing boundary — it does not apply fixes.

---

## AVAILABLE STATE

- `{dimension}`, `{classified}`, `{autonomous_mode}`

## STATE VARIABLES (set in this step)

- `{dispositions}` — the per-finding disposition table

---

## ROUTING RULES

| Verdict | Route | Framing |
|---|---|---|
| **Render gap** | `design-review` / a focused Claude Design paste prompt, **or** `wire-check` if it's purely a dropped field on an existing wire | "The data is correct; surface `{distinguishing attribute}` in `{component}`." A one-line/UI change — do not touch the data. |
| **Data hole / fall-through / source rot** | `maintenance-triage` (if a cluster) or `quick-spec` (to find the producer) → `quick-dev` | Frame the spec around the **producing pipeline** (extractor/importer/sync/normalizer). A backfill is an adjunct, never the whole fix — per the `data-quality` root-cause rule. |
| **Cross-field mismatch** | Same producer-fix lane; if the normalizer *should* have caught it, the fix is in the normalizer. | Name whether the producer or the normalizer is the root. |
| **No canonical normalizer (P1)** | `quick-spec` | "Introduce a canonical normalizer for `{dimension}`; cleaning values once without it just defers recurrence." |

For **render gaps**, prefer the design lane when the fix is a layout/IA question ("how should the marketplace be surfaced") and `wire-check` when it's a mechanically-missing field on a working wire. When in doubt, design-review (audit) over guessing.

## EMIT THE DISPOSITION TABLE

Every classified finding becomes one row — **including benign ones** (disposition: `accepted`, with the reason). This is the silent-partial-implementation guard: a reader can tell, without asking, that nothing was quietly skipped.

```markdown
## Data Quality Audit — {dimension}

**Scanned:** {N} values, {server_live ? "live" : "static"} | **Normalizer:** {normalizer}

| # | Finding | Shape | Verdict | Severity | Route | Disposition |
|---|---------|-------|---------|----------|-------|-------------|
| 1 | {label} spans {attrs} on {entity} | ambiguous | RENDER GAP | P2 | design / wire-check | route → surface {attr} in {component} |
| 2 | {value} unresolved ({n} rows) | fall-through | DATA ROT | P1 | quick-spec → producer | route → fix {producer} |
| … |

### Summary
- Render gaps (UI fix): {n}
- Data rot (producer fix): {n}
- Cross-field mismatches: {n}
- Structural (no normalizer): {n}
- Accepted/benign: {n}

### Top priority
1. {one-line highest-severity finding + its route}
```

Write the report to `{implementation_artifacts}/data-quality-audit-{dimension}-{date}.md`.

## HAND-OFF

- **Autonomous mode:** do not halt. Present the report and, for each non-benign finding, state the exact next workflow to run (copy-paste-ready), e.g. *"Run `/bmad:bmm:workflows:quick-spec` framed on the `{producer}` producer fix."* Do not invoke them — routing is the boundary.
- **Interactive mode:** present the report, then offer to kick off the top-priority route. Let the user choose.

In both cases the routed lane owns the actual change (in its own worktree, under its own rules). This workflow has delivered its value — the verdict and the route — and stops.

---

## SUCCESS METRICS

- Every finding (including benign) has a disposition row — nothing silently dropped
- Render gaps route to UI/design; data rot routes to the producer-fix lane framed under the root-cause rule
- Report written to `{implementation_artifacts}`
- No fixes applied by this workflow; no production data written

## FAILURE MODES

- Dropping benign findings from the table (reader can't tell what was skipped)
- Routing data rot as a data-only backfill instead of a producer fix (violates the `data-quality` root-cause rule)
- Invoking the routed workflow instead of handing off (this workflow detects + routes; it does not fix)
- Routing a render gap into the producer-fix lane (wasted producer work on correct data)
