---
name: escalation-on-class-change
contract_version: 1
description: 'Propose-and-act reflex for when work changes CLASS mid-flow — scope outgrew the story, a keystone/shared seam is missing, the framing is planning-not-execution, or the request belongs to another lane. On detection the workflow states the class-change, names the BMAD-default gateway (correct-course / design-router / maintenance-triage), proposes it, and proceeds unless vetoed — it does NOT surface a numbered menu and does NOT silently continue in the wrong lane. Referenced by dev-story and quick-spec (class-change tripwire), and conformed-to by correct-course, design-router, maintenance-triage, design-elevation, quick-dev.'
---

# Escalation on Class-Change — Propose and Act, Don't Menu

**Why this exists.** A workflow is scoped for a *unit* — one story, one spec, one surface. Sometimes, mid-flow, the work reveals it is no longer that unit: the change is bigger than the story, a shared seam is missing, the task is really a replan, or it belongs to a different lane entirely. The agent almost always *notices* this. The failure is what it does next:

1. **It hands back a menu.** "I found that this is larger than the story — would you like to (1) continue, (2) run correct-course, (3) re-scope, (4) stop?" The agent has done the hard part (detection) and then offloads the easy part (the obvious route) onto the user, making them the coordinator. This contradicts the global *act-don't-menu* doctrine (`answer-shape-and-autonomy`, `feedback-lead-dont-ask`).
2. **It silently continues in the wrong lane.** Worse — it finishes the story as written, shipping work grounded in a scope that no longer holds. The class-change is detected internally and never surfaced.

This standard is the single reflex both failures violate. Detection is a judgment the agent makes; this standard governs only what it does *once it has detected* — and the answer is never "make the user choose," it is "propose the default route and take it unless stopped."

---

## 1. The class-change tripwire (detection)

A workflow operating on a scoped unit checks, at its natural decision points (mid-flow when new scope surfaces, and again before it declares "done"), whether **any** of these now hold:

- **(a) Scope delta** — the change is materially larger or differently shaped than the story/spec/ask the workflow was handed. (Tell: tasks appear that were never in the unit; the unit's acceptance criteria no longer describe the work.)
- **(b) Missing keystone / seam** — a shared dependency, cross-cutting contract, or foundational piece the unit assumes is absent and must be built first. (Tell: "I can't do this without first changing X that other things depend on.")
- **(c) Planning, not execution** — the work is really a re-plan/re-scope decision, not an implementation task. (Tell: the unit's *framing* would need to change, not just its code.)
- **(d) Wrong lane** — the request belongs to another lane: design (a surface/IA problem), maintenance (a production-driven backlog item), or planning (epics/stories/architecture). (Tell: the right next actor is a different workflow's owner.)

If none hold, the workflow proceeds normally — this standard is silent. The tripwire is conservative: when uncertain, do NOT fire (a missed escalation is recoverable next pass; a false one is friction).

---

## 2. The response contract — state, propose, proceed-unless-vetoed

When the tripwire fires, the workflow does these four things, in order, as a single move — **not** a numbered menu:

1. **State** the detected class-change: which signal (a–d) fired and the concrete evidence (the task that wasn't in scope, the missing seam, the lane mismatch).
2. **Name** the BMAD-default gateway for that class (the map in §3).
3. **Propose** the route in one line — what the gateway will be asked to do — framed as the default action, not a question.
4. **Proceed** to the gateway (invoke it, or emit its exact handoff command) **unless the user vetoes.** Alternatives, if genuinely close, are a single secondary line ("…unless you'd rather X") — never an adjudicated 1–4 list the user must resolve.

The shape is *"I detected [class-change]; per BMAD I'm routing to [gateway] to [do X] — proceeding unless you say otherwise."* It is the act-don't-menu reflex applied to routing. The original lane HALTS while the gateway runs; it does not finish the now-mis-scoped unit in parallel.

---

## 3. Gateway map

| Detected class | BMAD-default gateway |
|---|---|
| Scope delta / replan / sprint-execution change (a, c) | `correct-course` |
| Wrong lane = design / surface / IA (d-design) | `design-router` |
| Wrong lane = production-driven backlog item (d-maintenance) | `maintenance-triage` |
| Missing keystone in a *quick* unit (b, under quick-dev) | reroute to `quick-spec` (quick-dev's existing §0 reroute) |

When two could apply, prefer the gateway that owns the *decision* the user must make, not the one nearest the symptom. When the lane itself is unclear, `correct-course` is the safe default for execution-lane work and `design-router` for anything visual.

---

## 4. Autonomy scoping — this is decision-autonomy, surfaced

Proposing-and-routing is **decision autonomy** (choosing the obvious next workflow and taking it with a veto window) — explicitly permitted. It is NOT **intent autonomy**: the workflow does not *silently re-scope* the work or infer a new goal the user never set. It surfaces the class-change and the route in plain language and yields a veto. The line this standard holds: **act on the routing decision; never act on a changed intent without surfacing it.** (Consistent with the fork's decision-vs-intent autonomy doctrine — see `quick-dev` step-03 reroute, which is the deterministic-flavored sibling of this rule.)

**Unattended / `autonomous_mode`.** A class-change is *intent-adjacent* — whether to re-scope, replan, or switch lanes is exactly the kind of decision autonomous mode does NOT grant (decision autonomy covers *how* to execute the unit, not *whether the unit is still the right unit*). So when the tripwire fires with **no user present to veto** (a `dev-auto`/wave/unattended run), the workflow does NOT auto-route — it **HALTs and records** the detected class-change + the proposed gateway into its handoff/output so the user routes it next session. "Proceed unless vetoed" requires a veto window; with no one to veto, the safe default is halt-and-surface, never silent self-routing into a planning/replan lane.

---

## 5. Enforcement honesty

This standard is **PROBABILISTIC** — it is prose a workflow chooses to follow. It works by (a) removing the menu-shaped sabotage that pulled agents the wrong way, and (b) naming one canonical reflex so workflows reference it instead of each re-deriving (and drifting). It is the right tier here because escalating into the wrong lane is *recoverable next pass* — a hard gate on a judgment call across every project would false-fire and get disabled (the indiscriminate-detector anti-pattern; consult `enforcement-expert`).

The **DETERMINISTIC** backstop — a detect→marker→Stop/pre-push gate that refuses to let the original lane complete until the gateway ran or an override is logged — is deferred. It is registered in `docs/fork-gaps.md` as dependent on the hook-distribution rail (the gate can't ship until hooks have a fork-managed distribution path); it is NOT hand-rolled as a standalone gate. Warn-only first when it does land.

---

## 6. Where this binds

- **dev-story** implements the full standard: it runs the §1 tripwire mid-flow (step 5) and before completion (step 9), and on a fire it executes the §2 contract (the execution-lane default gateway is `correct-course`). This is the workflow the standard was authored to fix — it previously had no class-change reflex at all.
- **quick-spec** runs the §1 tripwire at scope-assessment time (step-01 §2e): if the ask isn't actually a small/quick change, it escalates to the right gateway rather than authoring a quick spec for non-quick work — the spec-time sibling of quick-dev's §0 reroute.
- **correct-course, design-router, maintenance-triage, design-elevation, quick-dev** already embody this behavior; they **conform** by referencing this standard by name (so the reflex is canonical, not re-derived, and a new workflow inherits it). Their routing logic is unchanged — the pointer documents that what they already do IS this standard.
- **Out of scope (named, not missed):** pure status explorers (`sprint-status` — its numbered prompt is a view-picker, not a class-change fork); planning workflows that *produce* the scoped units and are the lanes escalated *into* (`create-story`, `create-epics-and-stories`, `sprint-planning`); fixed-contract implementers that already *cede* unverifiable dimensions rather than re-scope (`design-implement` / `design-ingest`); and read-only audits, doc, and brainstorm generators. None operate on a scoped unit that can itself change class.

Pairs with `answer-shape-and-autonomy` / `feedback-lead-dont-ask` (the global act-don't-menu doctrine this is the workflow-level expression of) and with `quick-dev`'s §0 reroute (the same reflex with a deterministic exit already in place).
