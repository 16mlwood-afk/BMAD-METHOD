---
name: 'step-03-analyze-gaps'
description: 'Cross-reference completed work against workflow capabilities to identify gaps and prioritize follow-ups'
---

# Step 3: Analyze Gaps

**Progress: Step 3 of 4** — Next: Execute Follow-ups (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Be precise — only recommend workflows where there's a concrete signal, not "maybe this could help."
- Prioritize by impact: data integrity issues first, then user-facing quality, then developer experience.
- Never recommend more than 4 workflows — if you have more candidates, cut the lowest-impact ones.

## AVAILABLE STATE

From previous steps:

- `{trigger_context}` — how this was triggered and raw data
- `{recent_handoffs}` — handoff artifacts from the last 24h
- `{changed_files}` — list of all changed files
- `{file_categories}` — categorized file map with counts
- `{work_scope}` — narrow / medium / wide / full-stack
- `{workflow_index}` — capability index of all available workflows
- `{workflow_chains}` — known workflow sequences

## SEQUENCE OF INSTRUCTIONS

### 1. Match File Categories to Workflow Triggers

For each workflow in `{workflow_index}`, check whether its trigger signals match the current `{file_categories}`:

```
For each workflow W in {workflow_index}:
  score = 0
  matched_signals = []
  
  For each trigger_signal in W.trigger_signals:
    if trigger_signal matches {file_categories} or {work_scope}:
      score += 1
      matched_signals.append(trigger_signal)
  
  if score > 0:
    add to candidates: { workflow: W, score, matched_signals }
```

### 2. Check Handoff Recommendations

If `{recent_handoffs}` contains a handoff artifact, cross-reference its sections:

- **"Gaps Found & NOT Fixed"** — each gap is a potential workflow trigger. Map each gap to the workflow that would address it:
  - Data not surfaced in UI → trace-flow
  - Wiring/format issues mentioned → wire-check
  - UI quality concerns → design-review
  - New feature suggestions → quick-spec

- **"Recommended Follow-ups"** — these are explicit next-step suggestions. Map each to a workflow.

- **"Strategic & Operational Insights"** — system-level observations. These rarely map to a single workflow but may indicate quick-spec territory.

Add handoff-derived recommendations to the candidates list with a bonus score of +2 (handoff gaps are higher-confidence signals than file-pattern matching alone).

### 3. Check for Workflow Chain Continuations

If `{trigger_context}` identifies a source workflow (e.g., "quick-dev just ran"), check `{workflow_chains}` for the natural next step:

- If the source workflow appears in a chain, add the chain's next workflow to candidates with a bonus score of +3 (chain continuation is the highest-confidence signal).

### 4. Deduplicate and Rank

1. Merge candidates by workflow name (sum scores, union matched signals)
2. Sort by total score, descending
3. Apply the **4-recommendation cap** — keep only the top 4
4. For each recommendation, determine priority tier:

| Tier | Score | Label |
|------|-------|-------|
| **Critical** | 5+ | "Run this — high probability of issues" |
| **Recommended** | 3-4 | "Likely valuable based on what changed" |
| **Optional** | 1-2 | "Worth considering if you have time" |

### 5. Validate Recommendations

For each recommendation, sanity-check:

- **Does the workflow actually exist?** Verify it's in `{workflow_index}` (guards against stale chain data).
- **Is the input available?** If the workflow needs a handoff path, is there one? If it needs a route, can you infer one from `{changed_files}`?
- **Was it already run?** Check `{recent_handoffs}` — if a wire-check handoff already exists for this PR, don't recommend wire-check again.
- **Does the scope justify it?** A 2-file CSS change doesn't warrant a wire-check, even if frontend files changed.

Remove recommendations that fail validation. Adjust the reasoning for those that pass.

### 6. Build Gap Analysis

For each validated recommendation, create a structured entry:

```
{
  workflow_name: string,
  slash_command: string,
  priority_tier: "critical" | "recommended" | "optional",
  rationale: string,              // one sentence: why this workflow for this work
  matched_signals: string[],      // what triggered this recommendation
  input_value: string,            // the actual input to pass (handoff path, route, etc.)
  chain_position: number | null,  // if part of a chain, what order (1, 2, 3...)
  chain_predecessor: string | null, // workflow_name this depends on (must complete first)
  estimated_value: string,        // what the user gains by running this
  edits_source_code: boolean      // true if workflow modifies project source files (needs worktree isolation)
}
```

**`edits_source_code` classification:**

| Workflow | edits_source_code | Reason |
|----------|-------------------|--------|
| wire-check | `true` | Fixes wiring issues in code |
| quick-dev | `true` | Implements changes |
| code-review | `false` | Read-only review |
| trace-flow | `false` | Read-only analysis |
| design-review | `false` | Read-only audit |
| design-handoff | `false` | Writes artifact only |
| quick-spec | `false` | Writes artifact only |

For unlisted workflows, infer from the workflow's description in `{workflow_index}`. If unsure, default to `true` (safer to isolate unnecessarily than to collide).

Store the complete analysis as `{gap_analysis}`.

### 7. Proceed to Execution

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/dispatch-followups/steps/step-04-generate-prompts.md`

---

## SUCCESS METRICS

- Every workflow in the index was evaluated against current signals
- Handoff recommendations were cross-referenced (if available)
- Workflow chains were checked for continuations
- No more than 4 recommendations produced
- Each recommendation has a concrete rationale and available input
- Already-run workflows were excluded
- `{gap_analysis}` populated with validated, prioritized entries

## FAILURE MODES

- Recommending every workflow "just in case" — be selective
- Ignoring the handoff's own follow-up suggestions
- Recommending a workflow that was already run in the last 24h for the same PR
- Recommending wire-check for a style-only change
- Recommending design-review for a backend-only change
