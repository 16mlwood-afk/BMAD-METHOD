---
name: 'step-02-classify'
description: 'Walk the four routing axes in order — lane, altitude, depth, target+placement — the first that fires sets the route; delegate the analytics-placement sub-decision'
---

# Step 2: Classify Across the Axes

**Progress: Step 2 of 3** — Next: Route (autonomous)

## RULES — read before acting

- **CLASSIFY AND DELEGATE — do not do the work, do not re-derive a specialist's logic.** This step picks a lane; it never redesigns, tunes, or decides band/tab/page itself. For the analytics-placement sub-decision it **dispatches to `analytics-placement-triage`** and consumes its result.
- **Walk the axes IN ORDER (1→4). The first axis that fires determines the route.** Don't evaluate depth before ruling out non-visual lane and policy altitude — a policy change misrouted as a surface redesign is the classic miss.
- FULLY AUTONOMOUS for decisions. No menus. Do not emit the command yet — that is step-03.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## AVAILABLE STATE

From step-01: `{request_surface}`, `{felt_want}`. The mode-registration table is in `workflow.md`.

## SEQUENCE OF INSTRUCTIONS

### 1. Axis 1 — lane (visual vs not)

Is the want a *visual/design* change, or a product/flows/data/logic spec? Set `{lane}`:
- `non-visual` (a behavior, a calculation, a data fix, a new endpoint) → route OUT: recommend `quick-spec` (needs investigation) or `maintenance-triage` (a backlog of mixed signals). Record `{route_target}` and skip to step-03.
- **Straddle** (part design, part code — "the drawer is read-only AND the number is wrong"): split into a design part and a code part, record both in `{straddle_parts}`, route each. Don't force one lane.
- `visual` → continue to axis 2.

### 2. Axis 2 — altitude (policy vs surface)

Is the change system-wide design *policy* (tone, density, tokens, component language across the app), or one surface? Set `{altitude}`:
- `policy` → route to `create-design-policy` (no `docs/design-policy.md` exists) or `modify-design-policy` (refine an existing one), then note `apply-design-policy-change` propagates it to affected pages. Record `{route_target}`, leave `{depth}` empty, skip to step-03.
- `surface` (or `{request_surface}` is a concrete route) → continue to axis 3.

### 2a. Axis 2 — altitude value `topology` (cross-surface IA / dashboard-consolidation)

If the want is to **re-group a SET of surfaces** — override the existing information architecture, consolidate distributed surfaces into a partner-/entity-centric dashboard, or otherwise change how multiple routes are grouped (signals: "should these become one dashboard", "partner-centric view", "override the in/out IA", "regroup X across pages") — set `{altitude}` = `topology`. This is an **IA-override / ownership decision**, not a single-surface redesign. Do NOT continue to depth, do NOT route to a specialist, and do NOT begin any consultant/agent divergence. Instead:

1. **Collect the real surface inventory** — the actual routes in scope + what each does + shared entities — from the repo, never guessed.
2. **Build `{ia_override_frame}`**: surfaces-in-scope + the overlap map · the one-sentence governing question · fixed named lenses (no ad-hoc mid-pass expansion) · the fixed output shape each consultant returns (recommended grouping principle · what merges · what stays separate · why · one risk) · a single synthesis rule (compare returns against the governing question, not a vibe-merge).
3. **Name the IA-override out loud** — state plainly that the governing question is an ownership decision (override the existing IA or not), and that consultant fan-out must not smuggle that unmade decision into a "ranked proposal."
4. **HALT for owner confirmation** (step-03 §0). Only on explicit owner confirmation does the bounded consultant pass run — and that pass is the caller's orchestration, downstream of this router.

**Degrade — owner unavailable / `autonomous_mode: true`:** `autonomous_mode` grants *decision* autonomy, NOT *intent* autonomy (see Initialization). An IA-override is an intent/ownership decision → the router **drafts `{ia_override_frame}`, writes it into the routing artifact, surfaces the HALT, and STOPS. It never auto-fans-out.** Draft-and-log, never diverge.

### 3. Axis 3 — depth (intervention type for one surface)

Classify the intervention from `{felt_want}` + cheap signals (does a `screen-review-*`/`design-brief-*` artifact already exist for this surface? is the surface settled/shipped?). Set `{depth}`:

| Signal in `{felt_want}` | `{depth}` | Routes to |
|---|---|---|
| "redesign", "new page", structural change, no prior artifact | `fresh` | `design-handoff` |
| "tighten", "iterate", "second pass", a baseline + a known diagnostic | `refine` | `design-artifact-loop` (refine) if a `screen-review`/`design-brief` artifact exists; else `design-handoff --refine` (refine-screen, which auto-runs `design-review` first) |
| "restyle", "match the policy", mechanical token/treatment swap | `restyle` | `apply-design-policy-change` **only if `docs/design-policy.md` version changed** (it is version-diff-driven); a restyle to the *current* policy with no version bump is a `refine` → `design-artifact-loop` |
| "what would make this better", a settled surface to deepen | `elevate` | `design-elevation` |
| "feels wrong but unclear", needs a diagnosis before any fix | `audit` | `design-review` |

If two depths genuinely tie, prefer the cheaper/investigative one (`audit` over `fresh`; `refine` over `fresh`) — investigation is cheap, a fabricated redesign is expensive.

### 4. Axis 4 — target + placement (delegate analytics-placement)

Confirm the precise `{route_target}` surface/route. **If `{felt_want}` is "add analytics to an operational page"** (a band/dashboard/trend/coverage want on a worklist), set `{placement_dispatch}` = `true` and **dispatch to `analytics-placement-triage`** with `{request_surface}` + the analytics want. Consume its verdict (band | tab | sibling-page | remove-band | no-surface) and its emitted `design-handoff --placement …` command — that becomes `{handoff_command}` in step-03. Do NOT decide band/tab/page here; the leaf owns it. Otherwise `{placement_dispatch}` = `false` and `{route_target}` is the axis-3 specialist against `{request_surface}`.

### 5. Proceed to Route

Record `{fired_axis}` = the axis that determined the route (`lane` | `altitude` | `depth` | `placement`). Set `{placement_summary}`: when `{placement_dispatch}` = `true`, the leaf's verdict + home (e.g. `band — rides /orders`); otherwise `n/a — not an analytics placement request`.

Confirm the fired axis, `{route_target}`, and (if dispatched) the placement leaf's result are captured. Then read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-router/steps/step-03-route.md`

---

## SUCCESS METRICS

- Axes walked in order; the first that fired set the route (lane → altitude → depth → target+placement)
- Analytics-placement was DISPATCHED to `analytics-placement-triage`, not decided inline
- A straddle was split and both parts routed; a non-visual or policy request exited at its axis without forcing a depth

## FAILURE MODES

- Evaluating depth before ruling out non-visual lane / policy altitude (misroutes a policy change as a surface redesign)
- Continuing to depth / routing a topology (IA-override) request to a single-surface specialist, or fanning out consultants before the owner confirmed the frame
- Deciding band/tab/page inline instead of dispatching to the leaf (router invariant break)
- Re-deriving a specialist's logic instead of routing to it
- Forcing a straddle down a single lane
