---
name: persona-placement
contract_version: 1
description: 'The placement gate that decides WHETHER a flow earns a named persona at all — the upstream half of the persona contract, before workflow-personas (which voices the three families that pass) and before persona-content-contract / create-agent (which build an invocable agent once placement says yes). Rule: personas are for human-facing judgment, not plumbing. A named character is added only when the flow acts as a router, owner, or advisor AND a reader benefits from knowing who is speaking; mechanical/sub-step/machine-to-machine flows stay anonymous. Reconciles with STD-ESCALATE-001 (act-don''t-menu): a persona changes who speaks, never whether the flow acts. Referenced by workflow-personas (STD-PERSONA-001) and create-agent / persona-content-contract.'
---

# Persona Placement — Personas Are for Human-Facing Judgment, Not Plumbing

**Why this exists.** The fork has two persona surfaces — presentation-only *workflow voices* (Rhea/Sol/Mara, `workflow-personas.md`) and invocable *agents* (`custom/agents/` — Vera/Wren, built by `create-agent`). Both surfaces answer *how* a persona reads or *what* it contains. Neither answers the question that comes first: **should this flow have a persona at all?** Without a reusable test, two failures creep in — a name gets bolted onto plumbing (a sync, a formatter, an internal sub-step) where it adds noise, not legibility; or a mechanical tail dressed up with a voice starts *adjudicating* (the `pick 1–4` terminal-step smell) when it should just execute its contract. This standard is the single placement gate both surfaces consult before any persona is created.

---

## 1. The canonical rule (load-bearing)

> **Personas are for human-facing judgment, not plumbing.** Use a named character only when judgment, role-clarity, or human friction make a "who is speaking?" worth the reader's attention. Keep low-level, mechanical, or purely internal flows anonymous.

A persona changes *who speaks*, never *what the flow does or whether it acts*. It is presentation; the behavior and shape are owned by `answer-shape-and-autonomy` and `escalation-on-class-change` (STD-ESCALATE-001). On any conflict, those win and the persona yields.

---

## 2. SHOULD get a persona — all three must hold

Add a persona only when **every** one of these is true:

1. **It is human-facing** — the flow asks the user something, explains a trade-off, or delivers narrative output a human reads. *(Necessary, not sufficient: a sync that prints results is human-facing too. The weight is carried by the AND with #2.)*
2. **It exercises distinct judgment** — the flow acts as a **router**, **owner**, or **advisor** (the kinds named in `persona-content-contract.md`), and that judgment differs in kind from its siblings (spec vs implementation vs review vs escalation).
3. **A named identity reduces confusion or human friction** — and *only* when multiple distinct judgment-bearing flows coexist and a reader would otherwise confuse who is speaking. "Role clarity" alone is not a licence; bound it to genuine ambiguity between speakers, or it justifies a persona for everything.

**Typical passes:** `design-handoff` (Rhea), `quick-spec` / `quick-dev` (Sol), `escalation-on-class-change` (Mara); invocable advisors and routers (Vera, Wren); future strategy/architecture/critique advisor flows.

---

## 3. SHOULD NOT get a persona — any one disqualifies

Stay anonymous when **any** of these holds:

- **Purely mechanical** — sync, formatting, file moves, rails, hooks, CI/pre-commit, scaffolding. No judgment, just a deterministic contract.
- **Internal sub-step** — a `steps/` file inside a larger workflow. The *parent* owns the voice; naming each step fragments it.
- **Output is consumed by another workflow or agent, not a human** — machine-to-machine handoffs carry an artifact, not a personality.
- **No judgment differentiation from an already-anonymous sibling** — if a sister flow does the same *kind* of work without a name, this one hasn't earned one either (anti-proliferation).
- **A name would imply a decision-maker where the flow only executes** — false agency. This is the same smell as the menu (see §4).

---

## 4. Reconciliation with act-don't-menu (STD-ESCALATE-001)

Placement and act-don't-menu are orthogonal axes that share one failure mode, so they must be read together:

- **Placement** decides whether there is a *who*. **Act-don't-menu** decides how that *who* behaves.
- Four quadrants, **two legal**: *judgment-bearing → named + proposes-and-acts*; *mechanical → anonymous + executes its contract*. The two illegal corners are **named-but-menus** (a voice that hands back `1–4` instead of routing) and **plumbing-that-adjudicates** (a mechanical tail pretending to decide).
- The open `pick 1–4` terminal-step fork-gap lives in exactly that illegal region — it fails **both** axes at once: it is a menu (violates STD-ESCALATE-001) *and* it is usually plumbing dressed up to adjudicate (violates this gate).
- **The bridge clause:** a persona is never permission to menu, and no-persona is never permission to silently continue. A persona'd flow still does *state → name the gateway → propose → proceed-unless-vetoed*; a mechanical flow still executes its contract without adjudicating.

---

## 5. Default and closing rule

> **Default anonymous.** Add a persona only to make a *human-facing judgment* legible — when the flow acts as a router, owner, or advisor and a reader benefits from knowing who is speaking. Never to decorate plumbing; never as a stand-in for a decision the flow should make itself. A persona changes *who speaks*, never *whether the flow acts* (STD-ESCALATE-001). When in doubt, stay anonymous — a missing persona is invisible, a gratuitous one is friction the user must parse.

---

## 6. Enforcement honesty

This is **PROBABILISTIC** — prose the authoring lane chooses to follow. That is the correct tier: persona placement is an authoring-time judgment, not a safety/money/irreversibility concern, so a deterministic gate would false-fire and get disabled. The value is a single canonical test so `workflow-personas` and `create-agent` stop each re-deriving "is this human-facing enough" and drifting. The act-don't-menu *behavior* this pairs with has its own deferred deterministic backstop registered in `docs/fork-gaps.md`; this placement gate does not add one.

---

## 7. Where this binds

- **workflow-personas.md** (STD-PERSONA-001) — consults §2/§3 to decide *which* families earn a named voice before defining one. The three current voices (Rhea/Sol/Mara) are the families that pass this gate.
- **create-agent** — `steps/step-01-brainstorm.md` runs this gate *before* classifying kind: if the candidate is plumbing or an internal sub-step, it is not an agent — stop and say so rather than building a persona for it. `persona-content-contract.md` (the content shape) assumes this gate already said yes.
- **create-workflow** — the inverse pointer: authoring a mechanical/rails/sync/sub-step workflow does **not** spawn a persona; a human-facing judgment workflow may, via the gate above.
- **Out of scope (named, not missed):** the *content* of a persona once placement says yes (`persona-content-contract.md`), and the *behavior/shape* a persona must never violate (`answer-shape-and-autonomy`, `escalation-on-class-change`). This file only decides the yes/no.

Pairs with `workflow-personas` (the voice surface this gates), `persona-content-contract` (the content shape downstream of a yes), and `escalation-on-class-change` / `answer-shape-and-autonomy` (the act-don't-menu behavior §4 reconciles with).
