# Analytics Archetypes

Single source of truth for the *shape* of an analytics surface. Referenced by `design-handoff` (step-01 §5c selects the archetype; step-03 §4b specifies the band against it) and by any reviewer checking that an analytics band earns its space.

## Why this file exists

Before this taxonomy, the handoff brief described exactly one analytics shape — a time-series trend strip of small-multiples with a drill table — and dressed it up as the generic structure of "an analytics band." Every feature handed off came back looking the same: a row of column microcharts, coverage strips, a gap callout. That is one archetype out of many, and it is the wrong one for most jobs.

An analytics surface has a *shape* the way a sentence has a verb. The shape is chosen by **the question the user is trying to answer**, not by what data happens to be available and not by what the legacy page already rendered. Time existing in the data does not make the job a trend job.

## The selection rule (read this before picking)

1. **Start from the user's question, not the data.** "Which client slipped this quarter?" is a *ranking + drift* question. "Are we missing any statements?" is a *coverage/exception* question. "Where is the money concentrated?" is a *composition* question. The same dataset answers different questions in different shapes.
2. **Pick the dominant archetype.** Surfaces often touch two (e.g. coverage + drift). Name the dominant one — it governs the composition — and treat the second as a secondary pass, not a co-equal that doubles the band's footprint.
3. **Ground or flag.** State the data dimension *and* the user question that selected the archetype. If you cannot name both, set `analytics_archetype: unclear` and halt/flag per the workflow's grounding gate. Do **not** default to `trend` — defaulting to trend is the exact failure this file exists to kill.

> **This file is the taxonomy; the `analytics-surface-architect` skill is the selector.** That skill runs the selection rule above against these archetypes and returns a structured decision (archetype + grounding + candidates-weighed + drill map + prohibited). `design-handoff` step-01 §5c invokes it; the nine definitions live here so the skill (and any reader) has one source of truth for *what the shapes are*, while the skill owns *how to choose*.
>
> **The selection is recorded, not just made.** The skill's decision — candidates weighed, why the winner won, what was rejected, and the explicit time≠trend check — is captured in step-01 §5c and written to a companion **rationale artifact** (`design-rationale-{slug}-{date}.md`, spec in `shared/analytics-rationale.md`). The brief carries only the conclusion; the rationale carries the reasoning so a human can audit how the dataset's presentation was chosen. A reviewer checking that a band earns its space can read the rationale to see whether the ground-or-flag rule was actually honored.
>
> **Shape is not depth — `analytics-rigor` governs the second axis.** This taxonomy and its selector answer *what shape*. They do **not** answer whether that shape is rendered with an expert analyst's depth: a correctly-chosen `coverage` strip can still ship every figure as a naked point estimate, with no base rate, no magnitude on the trend, and no one-line read — *correct and useless*. That axis is owned by `design-handoff` §5c-2, which specifies the lead read sentence, the uncertainty each decision number carries, the base rate it's shown against, and the deciding field (vs the handy proxy). Archetype = shape; rigor = depth; they compose, neither replaces the other. The cross-cutting rules below are shape rules; rigor is checked separately (`C-RIGOR-01` at review).
>
> **⚠️ Status of the `analytics-rigor` skill — read before citing it.** §5c-2 names an `analytics-rigor` skill as its preferred producer, **but that skill is not authored in any resolution root** (global / workspace / project / fork) — verified by a corpus-wide sweep, 2026-07-20. The same is true of `decision-analysis` (§5c-3, `C-DECISION-01`). So in practice §5c-2/§5c-3 run via their **sanctioned inline fallback** on every project today. This section previously called rigor a *mandatory pass* "enforced" by `C-RIGOR-01`; that wording overclaimed in two ways and is corrected here:
>
> 1. **`C-RIGOR-01` is real, but it is not a rigor audit.** It checks the *rendered surface against the brief's §4d spec* and takes §4d as ground truth. It cannot detect a thin or fabricated §4d — it measures against one.
> 2. **Rigor quality is irreducibly PROBABILISTIC.** Whether a base rate is the apt denominator, or a named deciding field is the real one, has no machine-decidable form. No gate will ever settle it; a competent reader is the only oracle.
>
> What IS deterministic — and is now enforced at tier 6 — is **provenance disclosure**: §4d must carry a `rigor_source` (`skill | inline-fallback | not-applicable`), §4e a `decision_source`, warned at commit time by `.githooks/check-design-brief-completeness.sh`. That closes the *hiding* problem (an undeclared fallback silently producing the evidence that enforcement succeeded, so that the only §4d the gate can fail is an honest one). It does not make rigor genuine. **Accurate label: "rigor provenance disclosed" — never "rigor enforced."**
>
> **And depth is not decision — capital-commitment surfaces get a third layer.** Rigor makes the figures honest (senior-analyst grade). A surface whose job is to *commit a scarce resource under uncertainty* — a buy / reorder / sizing decision, not a dashboard — needs one more rung: the **`decision-analysis` skill** (`design-handoff` §5c-3), which models the outcome distribution, sizes the commitment to the loss tail, and names the breakeven driver (executive / quant-desk grade). The stack is **shape → depth → decision**: archetype picks the shape, rigor makes every figure honest, decision-analysis turns the honest figures into a modelled, sized bet. Decision-analysis is the narrowest layer (capital decisions only) and is enforced separately (`C-DECISION-01` at review).

## The archetypes

Each entry: the **question** it answers · the **form** that answers it fastest · the **drill** path · what to **avoid**.

### `trend` — movement over time
- **Question:** How is X moving over time? Which series changed, and when?
- **Form:** Small-multiple sparklines or a single compact line/column strip. Shared Y-axis for absolute comparison; per-series Y-axis when only the *pattern* matters (state which, and why).
- **Two-magnitude sub-case (actuals vs forecast):** when the series carries ONE primary *realised* magnitude (committed / actual / spent) and a SUBORDINATE *projected* magnitude (provisional / forecast / pipeline / budget), these are **not two comparable series** — render the primary as a solid line/area and the subordinate as a **ghosted/dashed reference band**, visually distinct but never co-equal. **Never stack the two** (a committed+provisional stack is the naive-chart failure) and never draw them as two equal lines. Rounded axis ticks carry the scale; the exact per-point figure lives in the drill, **not** as a per-bar label. Optional baseline/average reference. (committed-vs-provisional, plan-vs-realised, budget-vs-spend, actual-vs-forecast are all this one shape.)
- **Drill:** A point/panel opens that period × segment in the worklist.
- **Avoid:** One multi-series line chart that hides individual movement; **stacked columns — full stop, including a committed+provisional stack** (no "unless it's the composition" carve-out applies to a trend); per-bar value labels standing in for an axis; the two-magnitude case collapsed to a single series (it cannot keep the two magnitudes distinct) or inflated to two co-equal lines.

### `distribution` — spread and outliers
- **Question:** How are values spread? Where do they cluster, and what's in the tail?
- **Form:** Histogram, strip/box plot, or a value-banded strip (counts per band).
- **Drill:** A band/bar opens the records inside that range.
- **Avoid:** Reporting only a mean/median — the point of a distribution is the shape, not the center.

### `composition` — part-to-whole
- **Question:** What's the mix? What share does each part hold of the total?
- **Form:** A single stacked bar, a 100%-bar, or a small ranked breakdown. Treemap only when parts span orders of magnitude (sparingly).
- **Drill:** A segment opens the records in that part.
- **Avoid:** Pie/donut charts; stacking a time-series (that's two archetypes fighting — split them).

### `ranking` — order and rank movement
- **Question:** Who's on top / at the bottom? Who moved up or down?
- **Form:** A sorted horizontal bar list (top-N) with optional rank-delta arrows; a leaderboard row.
- **Drill:** A ranked row opens that entity.
- **Avoid:** Showing all N when the user only acts on the extremes — cap and label the cut ("top 8 of 142").

### `coverage` — completeness and exceptions *(this is what most "ops band" attempts are reaching for)*
- **Question:** What's missing, late, unreconciled, or off? What needs attention right now?
- **Form:** A coverage strip with explicit gap marks, an exception counter, or a threshold-breach list. The gaps are the content — not decoration on a trend strip.
- **Drill:** A gap/exception opens the offending record(s) or the action to resolve them.
- **Avoid:** Burying the exceptions inside a pretty trend chart; making "all good" look identical to "3 gaps" at a glance.

### `flow` — movement between stages
- **Question:** Where do items drop or stall between stages of a process?
- **Form:** A funnel or stage strip showing counts per stage and the drop delta between them.
- **Drill:** A stage opens the items currently sitting at it.
- **Avoid:** Implying a funnel when stages aren't actually sequential. And do **not** use `flow` for a *reconciliation* — one population whose signed deltas sum back to a closing total. That is `waterfall`. `flow` is for independent sequential gates where the story is *survival rate per gate and why items fall out*.

### `waterfall` — reconciliation of a total
- **Question:** How did the opening total become the closing total — what was added or subtracted along the way, and why?
- **Form:** A bridge chart: an anchored opening bar, one signed step per contributing delta (each labelled with its cause), and an anchored closing bar. The deltas reconcile — they sum back to the closing total.
- **Drill:** A step opens the records that make up that delta.
- **Avoid:** A funnel. A funnel implies independent sequential *gates* and reads survival-rate-per-stage; a waterfall is *one population* reconciled to a single headline number by signed deltas. The tell: if you would naturally write `opening − Δ − Δ = closing`, it is a bridge, not a funnel. Also avoid double-encoding a delta as both a bar segment *and* a separate reason chip — the signed step *is* the delta; reasons live in its drill/label.
- **When `flow` and `waterfall` both seem to fit** — sequential attrition that *also* reconciles to one outcome (e.g. a conversion run that ends in a single profit or winner figure) — let the **user's question** decide, per the selection rule. If the headline is a single reconciled closing number that is *the point of the surface*, lead `waterfall` and demote the per-gate reasons to drill. If the point is *which gate leaks and why*, lead `flow`.

### `single-metric` — one number, in context
- **Question:** What's the one number, and is it OK?
- **Form:** A large value + its sparkline + a target/threshold marker + delta vs prior. One headline, not a wall of KPI cards.
- **Drill:** The number opens the period/records behind it.
- **Avoid:** A row of stat cards (the classic dashboard-tile fingerprint). One metric, or promote to `ranking`/`composition` if there are really several.

### `correlation` — relationship between two measures *(rare in operational UI)*
- **Question:** Do X and Y move together?
- **Form:** A small scatter or paired bars.
- **Drill:** A point opens the underlying record.
- **Avoid:** Reaching for this in a worklist context — it's almost always an analytical-page tool, not an operational band.

## Cross-cutting rules (apply to every archetype)

- **Every element drills.** No ornamental charts. If an element has no drill target, it doesn't belong in the band.
- **The band stays subordinate to the worklist** on operational pages. The archetype governs the band's internal shape; it does not promote the band over the table.
- **Status palette discipline.** Operational status colors stay reserved for operational states unless the brief explicitly extends them. Encode movement/category with position, glyph, and typographic weight before reaching for hue.
- **No dashboard fingerprints.** No KPI-card walls, no bento/magazine grids, no animated counters — regardless of archetype.

## `band_provenance` (set alongside the archetype)

The archetype answers *what shape*. `band_provenance` answers *why this band exists at all* — and keeps `design-handoff`'s blank-canvas mandate honest:

- **`inherited`** — the legacy page already had an analytics surface, and the data + job still justify it.
- **`recommended-new`** — the legacy page had no band, but the data shape + user job warrant one. This is a *net-new scope recommendation* and MUST be surfaced for explicit user veto before it lands in the brief. Handoff recommends; it does not silently invent scope.
- **`recommended-drop`** — the legacy page has a band, but the job is pure row-processing and the band is ornamental. Recommend removing it (also veto-surfaced).
- **`none`** — no analytics surface; §4b is omitted from the brief.

A band's presence is a *design judgment about the data and the job*, never an inheritance from the legacy render. See `design-handoff/steps/step-01-gather.md` §5b.
