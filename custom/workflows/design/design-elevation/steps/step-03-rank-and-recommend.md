---
name: 'step-03-rank-and-recommend'
description: 'Rank surviving candidates by leverage, recommend a focused subset with a pairing rationale, present the ranked list plus the disclosed rejects, then halt for the user to select what to build'
---

# Step 3: Rank and Recommend

**Progress: Step 3 of 4** — ends in the selection halt

## RULES:

- This step is autonomous UNTIL the halt. Generate the ranking and the recommendation, present them, then STOP and wait for the user's selection. Do not proceed to step-04 until the user has chosen.
- Lead with the recommendation, not the full list. The headline is "build these N"; the full ranked list and the rejects are the supporting detail beneath it.
- Do NOT auto-select and route. Expanding scope is the user's decision (see the workflow's Autonomy Model). Recommending hard is fine; deciding is not.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From steps 01–02: `{surface_name}`, `{core_job}`, `{candidates}` (with rationale), `{rejected_candidates}` (with reasons), `{iteration_number}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Score each candidate against the leverage rubric

For each candidate in `{candidates}`, score the four leverage dimensions from `checklist.md`:

- **Core-job proximity** — does it touch the primary decision/action, or something adjacent? (Closer = higher.)
- **Loop closure / earliness** — does it close a one-way loop or move a signal before the commit point? (Yes = higher — these are the highest-leverage moves on most surfaces.)
- **Effort reduction on what matters** — does it cut operator effort on the high-stakes step specifically?
- **Cost/risk to build** — lower build cost and lower risk to the settled surface rank a candidate up among equals (a cheap deepening beats an expensive one of equal job-impact).

Order `{candidates}` by leverage into `{ranked_candidates}`. Leverage on the core job dominates; build-cost breaks ties.

### 2. Choose the recommended subset

Pick the **1–3 candidates** that, taken together, most elevate the core job — `{recommended_subset}`. Favor a pairing that covers the core job's critical path (e.g. the pre-commit decision AND the verify path) over three variations on one facet. Write a one-line rationale for the *pairing*, not just the individual items: why these together are the highest-leverage scope expansion.

If `{candidates}` is empty, there is no recommendation — report that the surface is settled and nothing cleared the leverage bar this pass, show what was considered and rejected (it proves the pass ran), and end without a halt-for-selection (there is nothing to select). Persist state and stop.

### 3. Present — recommendation first

Emit to the user, in this order:

1. **The recommendation.** "Of the candidates, I'd build **[N]** — [the pairing], because [one-line pairing rationale tied to `{core_job}`]." This is the headline.
2. **The ranked list.** Each surviving candidate, highest leverage first, numbered, with its one-line "why it deepens the job." Keep each to a sentence or two — this is a decision aid, not a spec.
3. **What was rejected (disclosed).** A compact list of `{rejected_candidates}` with reasons. This proves the additive ideas were considered and dropped on purpose — the filter's receipt.
4. **The selection prompt.** "Build [the recommended subset], a different subset (name the numbers), or none?"

Match the project's communication conventions: the recommendation is stated as a recommendation and acted on; the full list is the appendix, not a menu the user must adjudicate option-by-option.

### 4. HALT for selection

Stop here. Persist `{ranked_candidates}`, `{recommended_subset}`, and the presented state to the state file. Wait for the user's reply.

- If the user names a subset (the recommendation, specific numbers, or "all") → set `{selected_enhancements}` and proceed to step-04.
- If the user says "none" / "not now" → record the decline in the state file (so a future pass does not re-propose) and end the workflow cleanly. Nothing is routed.
- If the user adds or reshapes an idea → fold it in, re-ground it against the surface, and confirm the final `{selected_enhancements}` before proceeding.

**NEXT (only after a non-empty selection):** Read fully and follow `{project-root}/_bmad/bmm/workflows/design/design-elevation/steps/step-04-classify-and-route.md`.
