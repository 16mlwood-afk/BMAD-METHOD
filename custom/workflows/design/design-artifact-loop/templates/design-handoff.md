<!--
Template: design-handoff-{target_slug}-{date}.md (or design-handoff-refine-{target_slug}-{date}.md in refine-screen mode)
Used by: design-artifact-loop in modes `refine-screen`, `policy-lift`, and `design-from-brief` (when brief asks for immediate implementation).
This artifact is implementation-ready. Downstream consumers: `quick-dev`, `dev-story`.

Placeholder → state variable mapping:
- {{mode}}                       → state.mode
- {{target_label}}               → state.target_label
- {{target_route}}               → state.target_route
- {{target_slug}}                → state.target_slug
- {{generated_at}}               → ISO 8601 datetime
- {{source_artifact_path}}       → state.artifact_path (canonical input)
- {{source_artifacts_consulted}} → bullet list: source artifact + screen-review (if synthesized) + policy excerpts referenced
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → from context block
- {{sources_consulted_line}}     → sister-skill invocations summary
- {{evidence_gaps}}              → comma-separated or "none"
- {{design_objective}}           → 1–2 sentence statement bounded to {{mode}}
- {{exact_changes_block}}        → numbered list of concrete changes; each item names component / region / token and cites a source from the evidence set
- {{what_not_to_change_block}}   → bullet list of explicit "do not touch" items, lifted from keepers in the screen-review (if any) and out-of-scope boundaries
- {{component_route_targets}}    → bullet list: file paths or route paths the implementer will touch
- {{edge_states_block}}          → bullet list of states whose design must be preserved or added
- {{implementation_notes_block}} → free-text notes (token names, sister-skill caveats, sequencing); empty if none

Mode rules:
- refine-screen: no Route Changes, no Multi-step Flow, no wholesale primary-surface swaps. Component-level changes only, each tied to a V-ID from the screen-review or a violation block in this file.
- policy-lift: every entry in Exact Changes MUST cite a line in the policy delta. Nothing else is in scope.
- design-from-brief: the brief's Section 6 (Design Ask) drives Exact Changes. Open questions from the brief are answered here; new questions opened during this run are surfaced in Implementation Notes for the next pass.

If the implementer should re-review after applying changes, say so explicitly in Implementation Notes. Otherwise default to no re-review.
-->

---
type: design-handoff
target: {{target_label}}
target_route: {{target_route}}
target_slug: {{target_slug}}
mode: {{mode}}
generated_at: {{generated_at}}
source_artifact: {{source_artifact_path}}
status: ready-for-implementation
---

# Design Handoff: {{target_label}}

## Context Block

- **Mode:** {{mode}}
- **Target:** {{target_label}} ({{target_route}} / slug `{{target_slug}}`)
- **Source artifact:** `{{source_artifact_path}}`
- **User / role:** {{user_role}}
- **Frequency:** {{frequency}}
- **Stakes:** {{stakes}}
- **Out of scope:** {{out_of_scope}}
- **Sources consulted:** {{sources_consulted_line}}
- **Evidence gaps:** {{evidence_gaps}}

## Source Artifacts Consulted

{{source_artifacts_consulted}}

## Design Objective

{{design_objective}}

## Exact Changes to Make

<!--
Numbered list. Each item is concrete enough for an implementer to execute without reinterpretation.
Required fields per item: which component / region / token, the change, the citation (rule + source path), and the V-ID if tied to a screen-review violation.

Example item:
1. **Header height (CountryHeader.tsx, line ~42).**
   - Change: `py-8` → `py-4`.
   - Rule: docs/design-policy.md §3 (Density) — "Detail page headers default to 16px vertical padding."
   - V-ID: V2 (screen-review-reclaim-avask-2026-05-26.md).
-->

{{exact_changes_block}}

## What NOT to Change

<!-- Page-wide protections. Lifted from screen-review Keepers and explicit out-of-scope items in the brief. -->

{{what_not_to_change_block}}

## Component / Route Targets

<!-- Files and routes the implementer will touch. Be specific; relative paths from the repo root. -->

{{component_route_targets}}

## Edge States to Preserve or Add

<!-- The implementer must verify these states render correctly after the change. -->

{{edge_states_block}}

## Implementation Notes

{{implementation_notes_block}}

## Mode Reminder

This handoff is locked to `{{mode}}`. The implementer should not expand scope on encountering related-but-unscoped issues; surface them via a follow-up `design-artifact-loop` run instead. Re-review path: hand the post-implementation screenshot back to `design-artifact-loop` in `review-only` or `refine-screen` mode.
