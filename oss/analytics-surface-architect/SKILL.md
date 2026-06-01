---
name: analytics-surface-architect
description: Decide HOW a dataset should be presented as an analytics surface — which shape (trend, distribution, composition, ranking, coverage, flow, single-metric, correlation) fits the user's question, why, and what was rejected. Use when choosing or auditing the shape of an analytics band, microchart row, dashboard tile, or evidence layer; when you need a grounded archetype + rationale for a design brief; or when someone asks "what shape should this data be?". Returns a structured decision (archetype + grounding + candidates-weighed + drill map). Do NOT use for visual treatment (color, type, spacing, tokens — that's your design system), for whether a screen needs analytics at all (that's an upstream product decision), or for backend/schema/data-pipeline work.
metadata:
  short-description: Pick the analytics shape for a dataset and explain why
  license: MIT
---

# Analytics Surface Architect

A skill for one decision, made well: **given a dataset and the question a user is trying to answer, what *shape* should the analytics surface take — and why?** It selects an archetype, grounds the choice in both the data and the question, records what it rejected, and maps every element to a drill target. It governs **shape and reasoning, not visual treatment.**

This is the decision that, left to reflex, makes every analytics surface come back looking the same — a coverage strip, a row of sparklines, a few KPI tiles — regardless of what the user actually needed to learn. The skill exists to make the choice deliberate and auditable: it starts from the question, not the data; it refuses to default to a time-series chart just because the data has dates; and it produces a written rationale you can challenge.

## Source of truth

- **The user's question selects the shape.** Not the data's availability, not the prettiest chart, not what the last screen used. "Which weeks are we missing statements for?" is a *coverage* question; "who are the top spenders?" is a *ranking* question; "where is the money concentrated?" is a *composition* question. The same dataset answers different questions in different shapes.
- **The eight archetypes below are the vocabulary.** Pick the dominant one. Visual treatment — color, density, chrome — is out of scope here; that belongs to your design system. Pick the shape with this skill; render it with your component library and style rules.

## The archetypes

Each: the **question** it answers · the **form** that answers it fastest · the **drill** path · what to **avoid**.

- **`trend` — movement over time.** *Q:* How is X moving over time; which series changed, when? *Form:* small-multiple sparklines or one compact line/column strip; shared Y-axis for absolute comparison, per-series only when just the pattern matters (say which). *Drill:* a point opens that period × segment. *Avoid:* one multi-series line that hides individual movement; stacked columns that bury small series.
- **`distribution` — spread and outliers.** *Q:* How are values spread; where do they cluster; what's in the tail? *Form:* histogram, strip/box plot, or value-banded strip (counts per band). *Drill:* a band opens the records in that range. *Avoid:* reporting only a mean/median — the shape is the point, not the center.
- **`composition` — part-to-whole.** *Q:* What's the mix; what share does each part hold? *Form:* a single stacked or 100% bar, or a small ranked breakdown; treemap only when parts span orders of magnitude. *Drill:* a segment opens its records. *Avoid:* pie/donut charts; stacking a time series (that's two archetypes fighting — split them).
- **`ranking` — order and rank movement.** *Q:* Who's on top / at the bottom; who moved? *Form:* a sorted horizontal bar list (top-N) with optional rank-delta arrows. *Drill:* a ranked row opens that entity. *Avoid:* showing all N when the user acts only on the extremes — cap and label the cut ("top 8 of 142").
- **`coverage` — completeness and exceptions.** *Q:* What's missing, late, unreconciled, or off; what needs attention now? *Form:* a coverage strip with explicit gap marks, an exception counter, or a threshold-breach list — the gaps are the content. *Drill:* a gap opens the offending record or the action to resolve it. *Avoid:* burying exceptions in a pretty trend chart; making "all good" look identical to "3 gaps" at a glance.
- **`flow` — movement between stages.** *Q:* Where do items drop or stall between stages? *Form:* a funnel or stage strip with counts per stage and the drop delta. *Drill:* a stage opens the items sitting at it. *Avoid:* implying a funnel when the stages aren't actually sequential.
- **`single-metric` — one number, in context.** *Q:* What's the one number, and is it OK? *Form:* a large value + sparkline + target/threshold marker + delta vs prior. *Drill:* the number opens the period/records behind it. *Avoid:* a row of stat cards (the dashboard-tile fingerprint) — one metric, or promote to `ranking`/`composition` if there are really several.
- **`correlation` — relationship between two measures.** *Q:* Do X and Y move together? *Form:* a small scatter or paired bars. *Drill:* a point opens the underlying record. *Avoid:* reaching for this in an operational worklist — it's almost always an analytical-page tool.

### Cross-cutting rules (every archetype)

- **Every element drills.** No ornamental charts. If an element has no drill target, it doesn't belong.
- **On operational pages, the analytics stays subordinate** to the primary table/worklist. The archetype governs the surface's internal shape; it does not promote analytics over the work.
- **Encode movement/category with position, glyph, and typographic weight before reaching for hue.** Reserve a status palette for genuine status.
- **No dashboard fingerprints** — no KPI-card walls, bento/magazine grids, or animated counters, regardless of archetype.

## The selection procedure

Run these in order. Do not skip to naming an archetype.

1. **State the user's question in their words.** "Which weeks are we missing statements for?" not "show completeness." If you cannot state a single concrete question, the surface has no job — say so rather than inventing one.
2. **Name the data dimension(s) available** — time, segment, category, stage, completeness, magnitude, pairs. List them; do not yet pick.
3. **Ground or flag.** Name BOTH the data dimension AND the user question that select the archetype. If you cannot name both, set `archetype: unclear` and **ask** — never default. This pair is the whole discipline; an archetype without it is a guess wearing a label.
4. **Weigh candidates — the road not taken is mandatory.** List every archetype you genuinely considered with a verdict (`chosen | secondary | rejected`) and a one-line reason. **If the data carries a time dimension, you MUST explicitly rule on `trend`** — record why it won or lost. Defaulting to `trend` because dates exist is the single failure this skill exists to prevent.
5. **Pick one dominant archetype.** A second may co-occur as a *subordinate* pass, but it never doubles the surface's footprint. More than one co-equal archetype means the surface is doing two jobs — split it.
6. **Map every element to a drill target.** For each thing the surface will show, state where interaction goes. An element with no drill target is ornamental — remove it.
7. **Time-in-data check.** If time is present, write one line stating why this is or isn't a `trend` job. This line is the proof the default was resisted.

## Output contract

Return the decision in this shape — a compact, machine-readable record you can paste into a design brief, hand to an implementer, or keep as a decision log:

```
archetype:        <trend|distribution|composition|ranking|coverage|flow|single-metric|correlation|unclear>
user_question:    "<the one question, in the user's words>"
grounding:
  data_dimension: "<the dimension that selected it>"
  user_question:  "<the question that selected it>"   # both required, or archetype=unclear
candidates:                                            # ≥ chosen + the most tempting rejected
  - { archetype: <name>, verdict: chosen,    why: "<one line>" }
  - { archetype: <name>, verdict: secondary, why: "<subordinate, why kept>" }
  - { archetype: <name>, verdict: rejected,  why: "<why it loses to the winner>" }
winner_reason:    "<why the winner won — names the data dimension AND the user question>"
secondary:        <archetype|none>
time_present_check: "<why this is/ isn't a trend job>"  | null   # required iff time in data
drill_map:
  - { element: "<gap mark | bar | value | stage>", drill_target: "<where interaction goes>" }
prohibited:       [ "<surface-specific shape ban, e.g. 'no pie', 'no multi-series line'>" ]
```

If `archetype: unclear`, return only `user_question` (as far as known) plus the single question you need answered to resolve it — and stop. A guessed archetype is worse than an asked one.

## Modes

Lock one mode per invocation.

- **select** (default) — given a data shape + user question, run the procedure and return the output contract.
- **critique** — given a proposed or existing surface (its declared archetype, or its rendered form), check the shape against the question. Flag mismatches: a `trend` strip answering a coverage question; an element with no drill; two co-equal archetypes; a KPI-card wall. Return the corrected archetype + the specific reason, in the output contract.
- **explain** — teach which archetype fits and why, for onboarding or a reviewer. Lead with the user's question, then the archetype, then one concrete example and the most tempting wrong choice.

## Refusals (and what to offer instead)

1. **Refuse** to emit an archetype without the ground-or-flag pair. **Offer:** `archetype: unclear` + the one question that would resolve it.
2. **Refuse** to default to `trend` because the data has dates. **Offer:** the procedure's candidate weighing, with `trend` explicitly ruled on.
3. **Refuse** any element with no drill target. **Offer:** drop it, or replace it with a metric or sentence that does drill.
4. **Refuse** a row of summary stat-cards (the dashboard fingerprint) and any two co-equal archetypes that double the footprint. **Offer:** one dominant archetype's lead form, with the second demoted to a subordinate pass or cut.

## Scope boundary

This skill answers *what shape and why*. It does not decide **whether** a screen needs analytics at all (an upstream product call — if no archetype honestly fits the data and question, say so; that's a signal the surface may not belong), and it does not set **visual treatment** (color, type, spacing, component chrome — that's your design system). Pick the shape here; gate it and style it elsewhere.
