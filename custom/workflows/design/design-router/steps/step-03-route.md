---
name: 'step-03-route'
description: 'Emit the exact next command with injected decisions, write the routing artifact, surface net-new scope / straddle / deferred axes — without auto-invoking the specialist'
---

# Step 3: Emit the Route

**Progress: Step 3 of 3** — Final step

## RULES — read before acting

- **DO NOT auto-invoke the specialist.** This router emits the decision + the exact next command; the user (or a separate invocation) runs it. Mirrors `maintenance-triage` — one routing run must not cascade into unattended design work.
- **Carry injected decisions so the route is consumable.** A placement verdict from the leaf travels as `--placement`; a refine route names its `screen-review` artifact; a scoped restyle names the surface. A route that emits a bare workflow name with no target/decision is the implicit-routing problem this gateway exists to kill.
- The route comes from the axis that fired in step-02 — do not re-classify here.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## AVAILABLE STATE

From step-02: `{lane}`, `{altitude}`, `{depth}`, `{placement_dispatch}`, `{route_target}`, `{straddle_parts}`, and (if dispatched) the `analytics-placement-triage` verdict + its emitted command. From step-01: `{request_surface}`, `{felt_want}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Build the exact next command

Set `{handoff_command}` from the fired axis:

- **placement-dispatch** (`{placement_dispatch}` = true) → use the `design-handoff … --placement <verdict>` command the leaf already emitted, verbatim (or "no handoff" if the leaf returned `no-surface`).
- **fresh** → `/bmad:bmm:workflows:design-handoff {request_surface}`
- **refine** → if a `screen-review`/`design-brief` artifact already exists for `{request_surface}`: `/bmad:bmm:workflows:design-artifact-loop` (refine / review-only — name the artifact); else `/bmad:bmm:workflows:design-handoff {request_surface} --refine` (refine-screen, auto-runs `design-review` first). *(Same fork as step-02's depth table — keep them in lockstep.)*
- **restyle** → `/bmad:bmm:workflows:apply-design-policy-change` scoped to `{request_surface}` **only if a policy version changed**; otherwise (restyle to the current policy) `/bmad:bmm:workflows:design-artifact-loop` (refine)
- **elevate** → `/bmad:bmm:workflows:design-elevation {request_surface}`
- **audit** → `/bmad:bmm:workflows:design-review {request_surface}` (add `--artifact` if a downstream refine will consume it)
- **policy** → `/bmad:bmm:workflows:create-design-policy` or `/bmad:bmm:workflows:modify-design-policy`, then note `apply-design-policy-change` to propagate
- **non-visual** → `/bmad:bmm:workflows:quick-spec` (or `maintenance-triage` for a mixed backlog)

For a **straddle**, emit one command per part in `{straddle_parts}`.

### 2. Write the routing-decision artifact

Render `../template.md` to `{routing_artifact_dir}/design-route-{surface_slug}-{date}.md` (derive `{surface_slug}` from `{request_surface}`; use `system-wide` for policy). Substitute every `{{variable}}`. Store the path as `{routing_artifact_path}`. This is a triage record — NOT a brief; no provenance block, not consumed by the provenance contract.

### 3. Hand off (do not auto-invoke)

Display:

```
**Route: {route_target}** for "{felt_want}" on {request_surface}.
Fired axis: {lane / altitude / depth / placement}.

{If a downstream specialist surfaced net-new scope (e.g. sibling page): "⚠️ Net-new scope — {what}. Veto if undesired."}

Next: run
  {handoff_command}
{If straddle: list both part commands.}

Routing artifact: {routing_artifact_path}
```

Then surface any **deferred axis** touched (a request that needed a finer classification this router doesn't yet wire) as a one-line note — never silently swallow it.

Do not run `{handoff_command}` yourself. This workflow ends at the recommendation.

### 4. Done

No further steps. The routing artifact + the surfaced route are the handoff.

---

## SUCCESS METRICS

- `{handoff_command}` is a runnable, target-correct command carrying its injected decision (`--placement`, `--refine`, scoped surface) — never a bare workflow name
- A placement-dispatch route used the leaf's emitted command verbatim
- Net-new scope, straddle splits, and any deferred axis were each surfaced — not swallowed
- Routing artifact written; the specialist NOT auto-invoked

## FAILURE MODES

- Auto-invoking the specialist (cascade boundary violation)
- Emitting a bare workflow name with no target/injected decision (reproduces implicit routing one level up)
- Re-deciding placement instead of using the leaf's verdict
- Swallowing a deferred axis or a straddle instead of surfacing it
- Writing a brief-style provenance block into the routing artifact (it is a triage record)
