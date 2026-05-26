<!--
Template: screen-review-{target_slug}-{date}.md
Used by: design-artifact-loop in modes `review-only` and `refine-screen` (when a screen-review must be synthesized before a refinement handoff).
This is the canonical, locked schema for this workflow. Simpler than the richer artifact emitted by `design-review --artifact` — this workflow trades machine-parseability for cross-run consistency.

Placeholder → state variable mapping:
- {{target_label}}            → state.target_label
- {{target_route}}            → state.target_route
- {{target_slug}}             → state.target_slug
- {{mode}}                    → "review-only" or "refine-screen"
- {{date}}                    → YYYY-MM-DD
- {{verdict}}                 → FAIL | PASS WITH ISSUES | PASS  (or INDETERMINATE for review-only with no visual evidence)
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → context block
- {{source_of_truth}}         → state.artifact_path
- {{top_issues_block}}        → V1, V2, V3 entries (template form below)
- {{edge_states_block}}       → bullet list
- {{what_to_keep_block}}      → bullet list
- {{out_of_scope_reminder}}   → bullet list of boundaries that survive into refinement
- {{sources_consulted_block}} → bullet list of skill names invoked (added in footer)
- {{evidence_gaps}}           → comma-separated list or "none"
- {{dissent_pass_outcome}}    → "completed; no re-ranking" | "completed; verdict demoted from X to Y because Z"

Fixed vocabulary:
- Verdict: FAIL | PASS WITH ISSUES | PASS | INDETERMINATE
- Severity: hard failure | issue | polish

Issue cap rule: emit the top issues only (typically 1–3). V1 is the most damaging. Do not pad; do not invent issues to fill a slot. If only one issue warrants action, ship one V-block. If more than three warrant action, raise the additional ones in the design-handoff phase (per the workflow's Gate 3) rather than expanding this list.

Dissent rule: the dissent pass may DEMOTE a verdict (PASS → PASS WITH ISSUES → FAIL) but may not upgrade. Record the outcome in the footer.
-->

# Screen Review — {{target_label}}

- Mode: {{mode}}
- Route: `{{target_route}}`
- Slug: `{{target_slug}}`
- Date: {{date}}
- Verdict: {{verdict}}

## Context

- User: {{user_role}}
- Frequency: {{frequency}}
- Stakes: {{stakes}}
- Source of truth: `{{source_of_truth}}`
- Out of scope: {{out_of_scope}}

## Top issues

<!--
Ordered V1 → V3 (V1 = most damaging). V-IDs are stable across iterations of the same target — never re-number. Severity in parentheses: hard failure | issue | polish.

Required fields per block:
- Evidence: visible thing or cited brief/policy section. No "feels off" without a pointer.
- Why it matters: one sentence connecting the issue to trust, comprehension, or next-action clarity.
- Required correction: concrete enough that the refinement pass can act on it without reinterpreting.
-->

{{top_issues_block}}

## Edge states

<!-- States the design must produce variants for. Pull from real data conditions, not generic loading/error states. -->

{{edge_states_block}}

## What to keep

<!-- Elements that work — the refinement must NOT break these. -->

{{what_to_keep_block}}

## Out-of-scope reminder

<!-- Boundaries that survive into refinement: route changes, new flows, wholesale major-component swaps are not in scope unless the next run is explicitly restated under design-from-brief. -->

{{out_of_scope_reminder}}

---

**Sources consulted:** {{sources_consulted_block}}
**Evidence gaps:** {{evidence_gaps}}
**Dissent pass:** {{dissent_pass_outcome}}
