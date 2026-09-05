<!--
Template: design-handoff-{target_slug}-{date}.md (or design-handoff-refine-{target_slug}-{date}.md in refine-screen mode)
Used by: design-artifact-loop in modes `refine-screen`, `policy-lift`, and `design-from-brief` (when brief asks for immediate implementation).
This is the canonical, locked schema for this workflow.
Downstream consumers: `quick-dev`, `dev-story`.

Placeholder → state variable mapping:
- {{target_label}}, {{target_route}}, {{target_slug}}     → state
- {{mode}}                                                → state.mode
- {{date}}                                                → YYYY-MM-DD
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → context block
- {{source_artifacts_block}}                              → bullet list of consulted source artifacts (the brief or screen-review, plus any policy excerpts cited)
- {{objective_paragraph}}                                 → one-paragraph design objective bounded to {{mode}}
- {{changes_to_make_block}}                               → numbered list (1, 2, 3, …) of concrete changes — each names the component/region/token, the change, and the source citation
- {{what_not_to_change_block}}                            → bullet list lifted from the screen-review's "What to keep" plus explicit out-of-scope items
- {{edge_states_block}}                                   → bullet list of states the implementer must preserve or add
- {{route_target}}, {{components_block}}                  → route + bullet list of file/component paths
- {{skill_routing_used_block}}                            → bullet list of skill names actually invoked during step 3 — gate 4 forbids emitting this output with the block empty when the run produced UI-facing guidance
- {{implementation_notes_block}}                          → bullet list; sequencing decisions, token names, sister-skill caveats

Mode rules:
- refine-screen: no route changes, no multi-step flows, no wholesale primary-surface swaps. Every "Changes to make" item ties back to a V-ID from the source screen-review.
- policy-lift: every "Changes to make" item cites a line in the policy delta.
- design-from-brief: the brief's Design Ask drives "Changes to make". Open questions resolved here are noted in "Implementation notes" for the next pass.

Verdict / severity vocabulary inherited from screen-review (when this handoff cites V-IDs): hard failure | issue | polish.
-->

# Design Handoff — {{target_label}}

- Mode: {{mode}}
- Route: `{{target_route}}`
- Slug: `{{target_slug}}`
- Date: {{date}}

## Context

- User: {{user_role}}
- Frequency: {{frequency}}
- Stakes: {{stakes}}
- Source artifacts:

{{source_artifacts_block}}

- Out of scope: {{out_of_scope}}

## Objective

{{objective_paragraph}}

## Changes to make

<!--
Numbered list. Each item is concrete enough for an implementer to execute without reinterpretation.
Required per item: which component / region / token, the change, the citation (rule + source path), and the V-ID if tied to a screen-review violation.

Example:
1. Header height (CountryHeader.tsx, line ~42). Change `py-8` → `py-4`. Cites docs/design-policy.md §3 (Density). V-ID: V2.
-->

{{changes_to_make_block}}

## What not to change

<!-- Page-wide protections. Lifted from screen-review "What to keep" plus explicit out-of-scope items in the brief. -->

{{what_not_to_change_block}}

## Edge states

<!-- The implementer must verify these states render correctly after the change. -->

{{edge_states_block}}

## Component / route targets

- Route: `{{route_target}}`
- Components:

{{components_block}}

## Skill routing used

<!--
Required block. Lists the skills actually invoked during step 3.
Gate 4 forbids emitting this output with the block empty when the run produced UI-facing guidance.
-->

{{skill_routing_used_block}}

## Implementation notes

{{implementation_notes_block}}

---

**Mode reminder:** This handoff is locked to `{{mode}}`. The implementer should not expand scope on encountering related-but-unscoped issues; surface them via a follow-up `design-artifact-loop` run instead. Re-review path (Gate 5): hand the post-implementation screenshot back to `design-artifact-loop` in `review-only` or `refine-screen` mode.
