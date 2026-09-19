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
- {{verdict}}                 → FAIL | PASS WITH NOTES | PASS  (or INDETERMINATE for review-only with no visual evidence)
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → context block
- {{source_of_truth}}         → state.artifact_path
- {{five_second_answer}}      → pass | fail | "no declared answer" — reader test against the brief's page_answer (T0)
- {{top_issues_block}}        → V1, V2, V3 entries (template form below)
- {{edge_states_block}}       → bullet list
- {{what_to_keep_block}}      → bullet list
- {{out_of_scope_reminder}}   → bullet list of boundaries that survive into refinement
- {{sources_consulted_block}} → bullet list of skill names invoked (added in footer)
- {{evidence_gaps}}           → comma-separated list or "none"
- {{dissent_pass_outcome}}    → "completed; no re-ranking" | "completed; verdict demoted from X to Y because Z"

Fixed vocabulary:
- Verdict: FAIL | PASS WITH NOTES | PASS | INDETERMINATE
- Severity: hard failure | issue | polish
- Binding: truth | advisory — `truth` = breaks a brief truth test, the five-second answer test, or a truth-class policy rule; `advisory` = departs from a style/layout/composition rule. Only a `truth` issue may carry severity `hard failure` or drive a FAIL verdict (shared/brief-binding-contract.md §4). A five-second check ("can a reader state the page's answer within five seconds?") is recorded in Context as `Five-second answer: pass | fail | no declared answer`.

Issue cap rule: emit the top issues only (typically 1–3). V1 is the most damaging. Do not pad; do not invent issues to fill a slot. If only one issue warrants action, ship one V-block. If more than three warrant action, raise the additional ones in the design-handoff phase (per the workflow's Gate 3) rather than expanding this list.

Dissent rule: the dissent pass may DEMOTE a verdict (PASS → PASS WITH NOTES → FAIL; FAIL only for a truth issue) but may not upgrade. `PASS WITH ISSUES` in an artifact written before 2026-09-19 reads as `PASS WITH NOTES`. Record the outcome in the footer.
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
- Five-second answer: {{five_second_answer}}   ← pass | fail | no declared answer (legacy brief)

## Top issues

<!--
Ordered V1 → V3 (V1 = most damaging). V-IDs are stable across iterations of the same target — never re-number. Severity in parentheses: hard failure | issue | polish.

Required fields per block:
- Binding: truth | advisory (see vocabulary above — an advisory issue is never a hard failure)
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
