---
name: design-router
description: 'The design-lane front door. Classify a design-shaped request and decide the lane/altitude/depth/target BEFORE any specialist runs, then emit the exact consumable handoff — which design workflow, against which surface, carrying which injected decisions. A thin router: it CLASSIFIES and DELEGATES; it never does the design work or re-derives a specialist''s reasoning. Use when you have a design want ("redesign X", "tighten Y", "add analytics to Z", "this feels wrong", "make it more corporate") and are not sure which workflow or target to point at.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Dispatch targets — this router decides WHICH of these runs against WHICH target.
# It defers to each by name; it never re-implements their logic.
design_handoff: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_artifact_loop: '{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/workflow.md'
design_tuning: '{project-root}/_bmad/bmm/workflows/design/design-tuning/workflow.md'
design_elevation: '{project-root}/_bmad/bmm/workflows/design/design-elevation/workflow.md'
design_review: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
apply_design_policy_change: '{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/workflow.md'
create_design_policy: '{project-root}/_bmad/bmm/workflows/design/create-design-policy/workflow.md'
modify_design_policy: '{project-root}/_bmad/bmm/workflows/design/modify-design-policy/workflow.md'
analytics_placement_triage: '{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage/workflow.md'
---

# Design Router Workflow

**Goal:** Make the design-lane's routing decisions **explicit and upstream**, instead of leaving them implicit inside the specialist workflows (where they only fire *after* you've already picked a target). Given a design-shaped request, decide — in order — its **lane**, **altitude**, **depth**, and **target+placement**, then emit the exact next command (specialist + target + injected decisions). This router decides *where the work goes*; the specialists do the work.

**Your Role:** You are the design triage desk. You do not redesign, tune, restyle, or audit anything yourself — you classify the request and hand it to the workflow that owns that kind of work, against the right surface, carrying any decision that's already been made so the specialist doesn't re-derive it.

---

## OWNERSHIP & MATERIALITY GATE — read first

This is a **router**. It owns the *routing*, nothing downstream.

**This workflow OWNS:** the design-lane routing decision — *which specialist workflow + which target + which injected decisions* a design-shaped request resolves to.

**This workflow does NOT own (it defers, by name):**
- The design work itself → `design-handoff` / `design-artifact-loop` / `design-tuning` / `design-elevation` / `design-review`.
- *Where analytics lives* on an operational page (band | tab | sibling page) → **dispatches to `analytics-placement-triage`** (which itself single-sources §5b/§5d/§5e). The router never decides band/tab/page inline.
- Design-policy content (system-wide tone/density/tokens) → `create-design-policy` / `modify-design-policy` / `apply-design-policy-change`.

**USE this workflow when:** you have a design-shaped want and aren't sure which workflow or target — "redesign the orders page", "tighten the held drawer", "add analytics to /orders", "this screen feels wrong", "make it more corporate".

**Do NOT use when:** (a) you already know the specialist + target → run it directly; (b) the request is code-shaped (a bug, a slow query, a dead handler) → that's `maintenance-triage` / `quick-spec`; (c) it's pure backend/schema/data work with no visual surface.

**Composition:** `maintenance-triage`'s design lane **dispatches design-shaped clusters into this workflow** (it names the surface + the want; design-router does the routing). design-router is the *single source of design-lane routing truth* — so the two front doors give one answer, not two divergent ones.

**If uncertain, ABSTAIN — never guess a route:**
- Cannot ground **either** the **surface** (or "system-wide" for policy) **or** the **felt want** from the input → **HALT** and ask (intent autonomy; see Initialization).
- The request straddles two lanes (part design, part code) → split it and route each part; don't force the whole thing down one lane.
- An axis genuinely won't resolve → surface the fork to the user; do not pick silently.

---

## MODE-REGISTRATION CONTRACT — the axes this router classifies

The router walks four axes **in order**; the first that fires determines the route. Each axis maps to a specialist with a `wired` (has a home today) or `deferred` (named, not yet wired) status. **Deferred axes are surfaced, never silently swallowed.**

| # | Axis | Question | Resolves to | Status |
|---|------|----------|-------------|--------|
| 1 | **lane** | Is this a *visual/design* task, or a product/flows/data spec wearing design clothes? | non-visual → route OUT to `quick-spec` / `maintenance-triage`; visual → continue | `wired` (coarse: visual-vs-not) |
| 2 | **altitude** | Is the change to the *project design policy* (system-wide tone/density/tokens), or to *one surface*? | policy → `create-design-policy` (none exists) / `modify-design-policy` (refine) → then `apply-design-policy-change` to propagate; surface → continue | `wired` |
| 3 | **depth** | For one surface: fresh redesign? refine an existing baseline? mechanical restyle-to-policy? deepen a settled surface? audit only? | fresh → `design-handoff`; refine → `design-artifact-loop` (refine) / `design-tuning`; restyle → `apply-design-policy-change` (scoped); elevate → `design-elevation`; audit → `design-review` | `wired` |
| 4 | **target + placement** | Which surface/route — and if the want is *"add analytics to an operational page"*, where does it live? | surface/route named; analytics-placement → **dispatch to `analytics-placement-triage`** (returns band\|tab\|sibling-page + its own `design-handoff --placement` command) | `wired` |

A genuinely new axis (e.g. a finer design-vs-product-flows-spec classification) is added here as a new row with `deferred` status and surfaced at run end — not bolted onto an existing axis.

---

## WORKFLOW ARCHITECTURE

Three-step linear flow. Autonomous for decisions; only intent grounding can halt (step-01).

1. **step-01-intake** — ground the request: the surface/route (or "system-wide" for policy) and the felt want in the user's words. Halt if neither resolves.
2. **step-02-classify** — walk axes 1→4 in order; the first that fires sets the route. Delegate the analytics-placement sub-decision to `analytics-placement-triage`. Produce a routing decision, not the work.
3. **step-03-route** — emit the exact next command(s) with injected decisions (`--placement`, `--refine`, scoped restyle), write the routing artifact, surface net-new scope and any straddle/deferred axis. Does NOT auto-invoke the specialist.

### State Variables

- `{request_surface}` — the route/surface the request targets, or `system-wide` (policy altitude)
- `{felt_want}` — the user's want in their words ("tighten it", "add analytics", "feels wrong", "more corporate")
- `{lane}` — `visual` | `non-visual` (axis 1)
- `{altitude}` — `policy` | `surface` (axis 2)
- `{depth}` — `fresh` | `refine` | `restyle` | `elevate` | `audit` (axis 3; empty when altitude=policy)
- `{placement_dispatch}` — `true` when the want is "add analytics to an operational page" → analytics-placement-triage is dispatched (axis 4)
- `{fired_axis}` — `lane` | `altitude` | `depth` | `placement` — the axis that determined the route (set in step-02 §5)
- `{placement_summary}` — when `{placement_dispatch}`, the leaf's verdict + home (e.g. `band — rides /orders`); else `n/a — not an analytics placement request` (set in step-02 §5)
- `{route_target}` — the resolved specialist workflow + its target argument
- `{handoff_command}` — the exact next command string, carrying injected decisions
- `{straddle_parts}` — when the request straddles lanes, the split (design part / code part) each routed
- `{routing_artifact_path}` — path to the written routing-decision artifact

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode — decision autonomy only

`autonomous_mode` governs *decision* autonomy (which axis fires, which specialist) — proceed and decide. It does NOT grant *intent* autonomy: if the input names no surface AND no felt want, HALT and ask — do not invent the request. Net-new scope surfaced by a downstream specialist (e.g. a sibling page from `analytics-placement-triage`) is surfaced-and-proceeded under autonomy, not silently committed.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/design/design-router`
- `routing_artifact_dir` = `{implementation_artifacts}`
- `design_policy` = `{project-root}/docs/design-policy.md` (read to tell policy-altitude from surface-altitude)

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-router/steps/step-01-intake.md` to begin.
