---
name: design-elevation-checklist
description: 'The leverage rubric and anti-chrome reject gates — used by step-02 to filter candidates and by step-03 to rank them'
---

# Design Elevation Checklist

The whole workflow turns on one question per candidate: **does this deepen the core job, or does it add surface area?** This checklist makes that judgment repeatable.

## The Leverage Rubric (score every surviving candidate)

A candidate earns its rank on these four dimensions. Leverage on the core job dominates; build-cost only breaks ties between candidates of equal job-impact.

- [ ] **Core-job proximity** — Does it touch the primary decision or action the surface exists for, or something adjacent? Closer to the moment that matters = higher leverage.
- [ ] **Loop closure / earliness** — Does it close a loop that is currently one-way (field→source but not source→field), or move a signal *before* the commit point (duplicate/validation/what-happens-next shown before Save, not after)? These are the highest-leverage moves on most surfaces — score them up.
- [ ] **Effort reduction on what matters** — Does it cut operator effort on the high-stakes step specifically (verify only the low-confidence fields), rather than adding effort or re-presenting what's already trusted?
- [ ] **Build cost / risk to the settled surface** — Among candidates of equal job-impact, the cheaper and lower-risk one ranks higher. A small change that deepens the job beats a large rewrite that deepens it equally.

## The Anti-Chrome Reject Gates (apply before ranking)

Reject — and record in `{rejected_candidates}` with a one-line reason — any candidate that trips a gate. The rejected list is part of the deliverable.

- [ ] **Unrelated capability** — Adds a view, report, panel, or export the core job does not need. Scope creep, reject.
- [ ] **Decoration / "delight"** — Animation, illustration, hero, metric-card grid, color-for-personality, gradients. No leverage on the decision, reject.
- [ ] **Generic completeness** — A default affordance added for its own sake ("add dark mode", "add shortcuts", "add a help tooltip") with no leverage on THIS surface's job. Reject. (Be precise: a *specific* keyboard path that walks the verify fields is leverage and survives; "add keyboard shortcuts" in the abstract is chrome.)
- [ ] **Policy anti-default** — Violates a named anti-default in `docs/design-policy.md`. Hard reject regardless of apparent leverage; cite the rule.
- [ ] **Competes with the primary surface** — On operational/hybrid pages, pulls attention from the worklist/primary action. Addition that subtracts focus, reject.
- [ ] **Already declined** — Proposed in a prior pass and declined by the user. Drop silently unless re-opened.

## Sweep-Balance Self-Test (step-02 §3)

- [ ] If `{candidates}` is empty — that is a valid result. Report "surface is settled, nothing cleared the bar" rather than manufacturing weak candidates.
- [ ] If `{rejected_candidates}` is empty — the sweep was too narrow. A genuine wide sweep always surfaces additive ideas worth rejecting; go wider.

## Grounding Self-Test (every candidate)

- [ ] The candidate references something that actually exists on the surface (read from `{built_surface_refs}`), not an invented affordance.
- [ ] The candidate's "why" names the core-job facet it deepens, in one sentence.

## Autonomy Self-Test (step-03)

- [ ] The workflow recommended a subset and halted for selection — it did NOT auto-select and route.
- [ ] Expanding scope was handed to the user as an explicit decision.
