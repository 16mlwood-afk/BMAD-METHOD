---
name: analytics-surface-architect
description: Decide HOW a dataset should be presented as an analytics surface — which archetype (trend, distribution, composition, ranking, coverage, flow, single-metric, correlation) fits the user's question, why, and what was rejected. Use when choosing or auditing the SHAPE of an analytics band, microchart row, or evidence layer; when a workflow needs an archetype + grounded rationale for a brief; or when someone asks "what shape should this data be?". Returns a structured decision (archetype + grounding + candidates-weighed + drill map). Invoke only when the main question is "what analytical shape should answer this user question from this dataset?" — choosing OR auditing (critique mode) an analytics band's archetype; skip a plain operational worklist with no band. Do NOT use for visual treatment / tokens / colors (that is the project design policy and operational-analytics-band), for whether a page needs a band at all (that is the upstream page-mode/band-belongs decision), or for backend/schema/data work.
metadata:
  short-description: Pick the analytics archetype for a dataset and explain why
---

# Analytics Surface Architect

The single brain for one decision: **given a dataset and the question a user is trying to answer, what *shape* should the analytics surface take — and why?** It selects an archetype, grounds the choice, records what it rejected, and maps every element to a drill target. It governs **shape and reasoning, not visual treatment**.

This is the decision that, left to reflex, makes every analytics surface come back looking the same (a coverage strip + microchart + counter row). The skill exists to make the choice deliberate and auditable, and to be the one place that choice is reasoned — so a workflow, a reviewer, and a human all defer to the same logic instead of re-deriving it.

## When to invoke

Use this skill when the main question is **"what analytical SHAPE should answer this user question from this dataset?"** — choosing or auditing the shape of an analytics band / chart / evidence layer.

Invoke when:

- choosing the archetype for a new analytics band/surface (**mode: select**);
- auditing whether an existing or proposed surface uses the right archetype — a trend-strip answering a coverage question, an element with no drill, two co-equal archetypes, a KPI-card wall (**mode: critique**);
- teaching which shape fits and why, for onboarding or a brief reviewer (**mode: explain**).

Do **not** use when:

- the question is "does this page even need analytics / a band at all?" — that's the upstream page-mode / band-belongs decision (design-handoff §5b), not this skill;
- the page is a plain operational worklist with no analytics band;
- the request is visual styling, colours, tokens, density, or front-end implementation detail (the project design policy + `operational-analytics-band` own that).

If uncertain: invoke **only when the main question is "what analytical shape should answer this user question from this dataset?"**; otherwise stay silent and note the ambiguity.

## Trust hierarchy

1. **The archetype taxonomy is the source of truth for *what shapes exist*.** `_bmad/bmm/workflows/design/shared/analytics-archetypes.md` defines the eight archetypes — each with its question / form / drill / avoid — plus the cross-cutting rules (every element drills; band stays subordinate on operational pages; status-palette discipline; no dashboard fingerprints). This skill **selects against** that file; it does not redefine the archetypes. If the taxonomy and this skill ever disagree, the taxonomy wins.
2. **This skill owns the *selection procedure*, the *grounding discipline*, and the *output contract*.** That is the part that is reasoning, not vocabulary.
3. **Visual treatment is out of scope.** How the chosen shape is rendered — color, density, tokens, card chrome — belongs to the project design policy (`docs/design-policy.md`) and, on operational pages, to `operational-analytics-band`. Pick the shape here; render it there.
4. **The live product UI is not a source of truth.** Pick from the data and the question, never from what the legacy page happens to render. Time existing in the data does not make the job a `trend` job.

## The selection procedure

Run these in order. Do not skip to naming an archetype.

1. **State the user's question in their words.** "Which weeks are we missing statements for?" not "show completeness." If you cannot state a single concrete question, the surface has no job — say so rather than inventing one.
2. **Name the data dimension(s) available** — time, segment, category, stage, completeness, magnitude, pairs. List them; do not yet pick.
3. **Ground or flag.** Name BOTH the data dimension AND the user question that select the archetype. If you cannot name both, set `archetype: unclear` and **ask** — never default. This pair is the whole discipline; an archetype without it is a guess wearing a label.
4. **Weigh candidates — the road not taken is mandatory.** List every archetype you genuinely considered with a verdict (`chosen | secondary | rejected`) and a one-line reason. **If the data carries a time dimension, you MUST explicitly rule on `trend`** — record why it won or lost. Defaulting to `trend` because dates exist is the single failure this skill exists to prevent.
5. **Pick one dominant archetype.** A second may co-occur as a *subordinate* pass, but it never doubles the surface's footprint. More than one co-equal archetype means the surface is doing two jobs — split it.
6. **Map every element to a drill target.** For each thing the surface will show (a gap mark, a bar, a value, a stage), state where interaction goes. An element with no drill target is ornamental — remove it.
7. **Time-in-data check.** If time is present, write one line stating why this is or isn't a `trend` job. This line is the proof the default was resisted.

## Output contract

Return the decision in this exact shape. It maps 1:1 onto the `design-rationale-*` artifact (§1–§4) and design-handoff step-01 §5c, so callers consume it without reshaping.

```
archetype:        <trend|distribution|composition|ranking|coverage|flow|single-metric|correlation|unclear>
user_question:    "<the one question, in the user's words>"
grounding:
  data_dimension: "<the dimension that selected it>"
  user_question:  "<the question that selected it>"   # both required, or archetype=unclear
candidates:                                            # ≥ chosen + the most tempting rejected
  - { archetype: <name>, verdict: chosen,   why: "<one line>" }
  - { archetype: <name>, verdict: secondary, why: "<subordinate, why kept>" }
  - { archetype: <name>, verdict: rejected,  why: "<why it loses to the winner>" }
winner_reason:    "<why the winner won — names the data dimension AND the user question>"
secondary:        <archetype|none>
time_present_check: "<why this is/ isn't a trend job>"  | null   # required iff time in data
drill_map:
  - { element: "<gap mark | bar | value | stage>", drill_target: "<where interaction goes>" }
prohibited:       [ "<page-specific shape ban, e.g. 'no pie', 'no multi-series line'>" ]
```

If `archetype: unclear`, return only `user_question` (as far as known) plus the single question you need answered to resolve it — and stop. A guessed archetype is worse than an asked one.

## Modes

Lock one mode per invocation.

- **select** (default) — given a data shape + user question, run the procedure and return the output contract. **Callers:** `design-handoff` step-01 §5c (the producer, at the handoff gate) and `analytics-placement-triage` step-03-shape (the placement-triage gate, which names the shape *before* the analytics home is committed).
- **critique** — given a proposed or existing surface (its declared archetype, or its rendered form), check the shape against the question. Flag mismatches: a `trend` strip answering a coverage question; an element with no drill; two co-equal archetypes; a KPI-card wall. Return the corrected archetype + the specific reason, in the output contract.
- **explain** — teach which archetype fits and why, for onboarding or a brief's reviewer. Lead with the user's question, then the archetype, then one concrete example and the most tempting wrong choice. **Callers:** human onboarding (per "When to invoke"), and `design-review-pr` step-03 §3b when a `C-ARCHETYPE-01` finding fires (so the finding teaches the right shape, not just flags the wrong one).

## Refusals (and what to offer instead)

1. **Refuse** to emit an archetype without the ground-or-flag pair. **Offer:** `archetype: unclear` + the one question that would resolve it.
2. **Refuse** to default to `trend` because the data has dates. **Offer:** the procedure's candidate weighing, with `trend` explicitly ruled on.
3. **Refuse** any element with no drill target. **Offer:** drop it, or replace it with a metric or sentence that does drill.
4. **Refuse** a row of summary stat-cards (the dashboard fingerprint) and any two co-equal archetypes that double the footprint. **Offer:** one dominant archetype's lead form, with the second demoted to a subordinate pass or cut.

## How this composes with the rest of the system

- **`analytics-archetypes.md`** — the taxonomy this skill selects against (item 1 above).
- **`operational-analytics-band`** — once this skill picks the shape, that skill governs how it sits on an operational page (subordination, visual weight, policy citations). Architect picks; band places.
- **`design-policy-canonical` / `docs/design-policy.md`** — visual treatment of the rendered shape. Architect never sets color, density, or chrome.
- **`design-handoff` (step-01 §5c → step-03b)** — the producer caller: selects the archetype here, writes the output contract into the `design-rationale-*` artifact.
- **`analytics-placement-triage` (step-03-shape)** — the placement-triage caller: selects the archetype while deciding *where* the analytics lives (band | tab | sibling page), so the chosen home carries the shape decision into its `design-handoff` invocation rather than re-deriving it.
- **`design-review-pr` (C-ARCHETYPE-01)** — the enforcer: verifies the *rendered* surface matches the *declared* archetype; can read the rationale to check the *reasoning* held, not just the pixels.

The band-belongs question — *should this surface exist at all?* — is upstream (page-mode / `design-handoff` §5b). This skill assumes a surface is warranted and answers *what shape*; if no archetype honestly fits the data and question, say so — that is a signal the band may not belong, and it routes back to that upstream decision.
