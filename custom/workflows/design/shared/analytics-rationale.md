# Analytics Presentation Rationale

Single source of truth for the **record-of-decision** that accompanies a `design-handoff` brief whenever that brief carries an analytics band. Referenced by `design-handoff` (step-03b emits it; step-01 §5/§5b/§5c capture the reasoning it records).

## Why this file exists

The brief records the *conclusions* of the analytics presentation decision — `page_mode`, `band_provenance`, `analytics_archetype` in frontmatter, plus a one-line grounding in §4b·A. It deliberately records nothing more, because the brief is a **bias filter**: it withholds the current layout so Claude Design starts from a blank canvas, and dumping "we considered `trend` but rejected it" into the brief would hand the designer a shape and break that mandate.

But the deliberation behind those conclusions is the most valuable thing to audit and the thing most likely to be wrong — especially the **road not taken** (time existed in the data and we still didn't pick `trend` — why?). That reasoning has no home in a creative brief. This artifact is that home: a companion file that travels beside the brief, captures the full deliberation, and lets a human read, diff (across re-runs), and challenge how the model decided to present the dataset.

**Consumer model:** Claude Design reads the *brief*, never this file. This is a human-facing and reviewer-facing record. It is emitted only when `{has_analytics_band}` is `true` — a plain operational worklist with no band produces no rationale file. **The brief MUST NOT reference this file** — a pointer from inside the brief would tempt the designer to read it and re-introduce the anchoring the brief exists to prevent. Linkage is one-way: this artifact's `accompanies_brief` names the brief.

## PROVENANCE SCOPE — this is NOT a brief

This artifact is explicitly **out of scope** for `brief-revision-policy.md`. It is not a brief, it is not consumed by `design-synthesize` / `design-artifact-loop` / `design-implement`, and the **6 intake checks do not run on it** (same posture as `onboard-design-system`'s design-system artifacts). It carries its own minimal lineage — `rationale_status: active | superseded`, `supersedes`, `superseded_by` — solely so re-runs don't pile up duplicate active records for the same surface. Do not add the 11-field Block A provenance contract to it; do not have any consumer validate it at intake.

Its lineage is **derived from the brief's**, never invented independently:
- The rationale is named `design-rationale-{target_slug}-{date}.md`, beside the brief in `{implementation_artifacts}`.
- When the brief is a `material_revision` (step-03 §1a found exactly one active predecessor brief), step-03b finds the predecessor *rationale* by its `accompanies_brief == {supersedes_filename}` link — the precise 1:1 tie, no second glob-invariant — and flips it to `superseded`. If no such rationale exists (the predecessor brief predates this feature), there is simply nothing to supersede; proceed.
- It is delivered in the **same commit/PR** as the brief (step-04 stages both), so a brief on `main` always has its rationale beside it.

## The template

Write the file with this exact structure. Fill every `{variable}` from step-01/step-03 state; leave no placeholder behind. Keep it tight — this is a decision log, not an essay.

````markdown
---
type: design-rationale
accompanies_brief: {output_filename}          # the design-brief this rationale explains
feature: {feature_name}
target_slug: {target_slug}
date: {date}
author: {user_name} via design-handoff workflow
rationale_status: active                       # active | superseded (own lineage; NOT brief Block A)
supersedes: {rationale_supersedes_filename}    # empty on an original
superseded_by:                                 # always empty on a freshly written rationale
source_workflow: design-handoff
source_run_date: {source_run_date}
# --- decision summary (conclusions, for quick scan; full reasoning is in the body) ---
page_mode: {page_mode}
band_provenance: {band_provenance}
analytics_archetype: {analytics_archetype}
---

# Analytics Presentation Rationale: {feature_name}

> This records **how** the analytics presentation decisions were reached during
> `design-handoff` — the deliberation behind the conclusions in the companion brief
> `{output_filename}`. It is a record-of-decision, **not** a design input: Claude Design
> reads the brief, not this file. Read this to audit or challenge the reasoning, or to see
> what was considered and rejected.

## 1. Page mode → `{page_mode}`

- **Dominant user task:** {one sentence — what the user is primarily doing on this page}
- **Signal that selected it:** {page_mode_rationale — the concrete signal from step-01 §5, e.g. "user goal is 'spot which week slipped' → pattern discovery, not row processing"}
- **Composition consequence:** {operational → table-first; analytical → chart-led}
- **Note on the other axis:** Page mode (here `operational` or `analytical` — a `detail` view carries no band, so it never reaches this artifact) decides *composition only*, not whether analytics appear at all. That is the separate band decision in §2.
  {If `page_mode == operational` AND a band exists, ADD: "This is the hybrid case — an operational worklist that still carries a supporting analytics band. The band axis (§2), not the mode, carries the analytical weight; the band stays subordinate to the worklist."}

## 2. Does an analytics band belong? → `{band_provenance}`

The three blank-canvas questions (step-01 §5b), answered for THIS feature — decided by **data + job**, not by what the legacy page renders:

1. **Aggregate dimension** — does the data carry a dimension the rows don't expose (time, segment, category, stage, completeness)? → {yes/no + name the dimension}
2. **Pattern job** — is part of the user's job pattern / comparison / anomaly / coverage work, rather than pure row-by-row processing? → {yes/no + which}
3. **Changes next action** — would seeing an aggregate layer change what the user does next (which rows they open, which exception they chase)? → {yes/no + how}

**Verdict:** `{band_provenance}` — {justification in one or two sentences}.
{If `recommended-new` or `recommended-drop`, ADD: "This is a net-new scope {recommendation / removal}, not inherited from the legacy render. Surfaced to the user for veto on {date}: {accepted / declined / pending}."}

## 3. Which shape? Archetype selection → `{analytics_archetype}`

- **The one question this band answers, in the user's words:** "{the question — e.g. 'which weeks are we missing statements for, and in which region?'}"

**Candidates weighed** (against `shared/analytics-archetypes.md`). Include the winner, any genuine secondary, and at minimum the most tempting rejected alternative:

| Archetype | Verdict | Why |
|---|---|---|
| {archetype} | chosen | {one line} |
| {archetype} | secondary | {one line — why kept but subordinate} |
| {archetype} | rejected | {one line — why it loses to the winner} |

**Why `{analytics_archetype}` won:** {archetype_winner_reason — name the data dimension AND the user question that selected it}

{If a time dimension exists in the data, ADD this block — it is the single most important guardrail:}
- **Time-in-data check:** The data contains a time dimension. Defaulting to `trend` because time exists is the exact failure the archetype taxonomy exists to prevent. This selection {avoided it: time is present but the job is `{winner}`, not movement-reading / OR: is a genuine `trend` job because the user's question is literally "how is X moving over time"}.

- **Secondary archetype:** {`{archetype_secondary}` + why it stays subordinate and does not double the band's footprint / OR "none — single-archetype band"}.

## 3b. Which depth? Rigor specification (from the `analytics-rigor` skill)

The archetype (§3) is the *shape*; this is the *depth* that keeps the shape from rendering as a schoolboy data-dump (correct figures, no read). Captured in step-01 §5c-2 by the `analytics-rigor` skill; consumed by `C-RIGOR-01` at review.

- **The read the surface leads with:** "{rigor_read_sentence}" {or "— none: this surface carries no single decision to read"}
- **Decision-bearing numbers — each must carry uncertainty AND a base rate:**

| Metric | Uncertainty it carries | Base rate it's shown against |
|---|---|---|
| {metric} | {range / confidence / assumption it rides on — or "none (data gap)"} | {portfolio median / category norm / own history — or "none (data gap)"} |

- **Deciding field per series (vs the handy proxy):** {rigor_deciding_fields — each visualised series tagged "answers the question" or "proxy → should chart {field}"}
- **Data gaps (surfaced, NEVER fabricated):** {rigor_data_gaps — metrics the enrichment/model must supply before a rigor move can be honestly satisfied; until then the figure ships as an honest bare number, not a faked interval / OR "none — every rigor move is satisfiable from current data"}
- **Rigor verdict at handoff:** `{rigor_verdict}` (analyst-grade | schoolboy | mixed)

## 4. What this band will NOT be

The rejected shapes, stated so reviewers and implementers can see the boundary the brief's §4b encodes:

- {e.g. "Not a trend strip of small multiples — time exists, but the job is coverage; the gaps are the content."}
- {e.g. "Not a KPI / stat-card row — dashboard fingerprint, banned regardless of archetype."}
- {archetype-specific rejected forms — pull from the 'Avoid' line of the chosen and rejected archetypes}

## Provenance

Generated by `design-handoff` on {date}. Companion to brief `{output_filename}`. Reasoning sourced from step-01 §5 / §5b / §5c evaluated against `shared/analytics-archetypes.md`.
{If the brief's `change_class == material_revision`, ADD: "Supersedes `{rationale_supersedes_filename}`."}
````

## Self-check (run before writing)

- [ ] Emitted **only** when `{has_analytics_band}` is `true`. No rationale file for a plain operational worklist.
- [ ] Every `{variable}` is filled — no template placeholder survives. The candidates table has ≥1 chosen row plus at least the most tempting rejected alternative.
- [ ] §1 records the mode *signal*, not just the label. If operational + band, the hybrid note is present.
- [ ] §2 answers all three questions with the feature's actual data/job — not a restated generic "show trends."
- [ ] §3 names the user's question in their words, and the winner's reason names BOTH a data dimension and a user question. If time is in the data, the time-in-data check block is present.
- [ ] §3b records the rigor spec: a read sentence (or an explicit "none"), every decision number with its uncertainty + base rate (or a named data gap), and the deciding-field check per series. No fabricated interval stands in for a data gap.
- [ ] Frontmatter `rationale_status` is `active`; on a brief `material_revision` the predecessor rationale (found via `accompanies_brief == {supersedes_filename}`) was flipped to `superseded`.
- [ ] `accompanies_brief` matches the brief's `{output_filename}` exactly. The brief does NOT reference this file in return.
- [ ] No Block A 11-field provenance block added — this artifact is out of scope for `brief-revision-policy.md`.
