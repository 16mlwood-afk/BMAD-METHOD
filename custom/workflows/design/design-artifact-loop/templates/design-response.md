<!--
Template: design-response-{target_slug}-{date}.md
Used by: design-artifact-loop in mode `design-from-brief` when the brief asks for concept direction rather than immediate implementation (e.g., the brief contains open design questions, asks the agent to "explore", or explicitly defers the implementation handoff).

A design-response is upstream of a design-handoff. After the user reviews the response and accepts a direction, design-artifact-loop is rerun against the response as the canonical artifact, producing an implementation-ready design-handoff on the second pass.

Placeholder → state variable mapping:
- {{target_label}}, {{target_route}}, {{target_slug}}     → state
- {{generated_at}}                                        → ISO 8601 datetime
- {{source_artifact_path}}                                → state.artifact_path (the brief)
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → context
- {{sources_consulted_line}}, {{evidence_gaps}}           → consulted skills, gaps
- {{brief_summary_block}}                                 → 3–5 bullet recap of the brief, in this workflow's words
- {{proposed_screen_structure_block}}                     → free-text + optional ASCII / labeled-region sketch describing the proposed layout
- {{open_questions_answered_block}}                       → numbered list mapping each brief Section-6 question to an answer + rationale-citation
- {{rationale_block}}                                     → connects proposed structure back to brief sections (purpose, data, user context, visual direction, constraints)
- {{implementation_handoff_note}}                         → instruction for the next design-artifact-loop pass (one paragraph): what to ask of the second run, what to treat as locked vs still-open
-->

---
type: design-response
target: {{target_label}}
target_route: {{target_route}}
target_slug: {{target_slug}}
mode: design-from-brief
generated_at: {{generated_at}}
source_artifact: {{source_artifact_path}}
status: ready-for-review
---

# Design Response: {{target_label}}

## Context Block

- **Mode:** design-from-brief (concept direction)
- **Target:** {{target_label}} ({{target_route}} / slug `{{target_slug}}`)
- **Source artifact (brief):** `{{source_artifact_path}}`
- **User / role:** {{user_role}}
- **Frequency:** {{frequency}}
- **Stakes:** {{stakes}}
- **Out of scope:** {{out_of_scope}}
- **Sources consulted:** {{sources_consulted_line}}
- **Evidence gaps:** {{evidence_gaps}}

## Brief Summary

<!-- 3–5 bullets restating the brief in this workflow's own words. If this summary conflicts with the brief, the brief wins — surface the gap in Evidence Gaps. -->

{{brief_summary_block}}

## Proposed Screen Structure

<!--
Describe the proposed layout in domain terms. Name the regions, the data each region surfaces, and the primary action each region affords.
Avoid template-default language ("hero / cards / cta"). Avoid speculative components ("a card row of KPIs") unless the brief asks for them.
Optional: an ASCII or labeled-region sketch where it adds clarity. A sketch is not required.
-->

{{proposed_screen_structure_block}}

## Open Design Questions — Answered

<!--
For each open question in the brief's Section 6 (Design Ask), give an answer + rationale tied back to:
- the brief's domain data (Section 2),
- the brief's user context (Section 3),
- the brief's visual direction (Section 4),
- the brief's hard constraints (Section 5),
- or a sister-skill rule (cited explicitly).

If a question cannot be answered without further user input, mark it OPEN and explain what input is needed.
-->

{{open_questions_answered_block}}

## Rationale

<!--
Explain why the proposed structure follows from the brief. The implementation pass (next design-artifact-loop run) will read this section to understand which constraints are load-bearing.
-->

{{rationale_block}}

## Implementation Handoff Note

<!--
Tell the user (and the next run) what's locked, what's still open, and how to invoke the implementation pass.

Default text (edit per run):
"Rerun design-artifact-loop in design-from-brief mode against this response as the source artifact. Treat the Proposed Screen Structure and Answered Questions as locked; the next run produces a design-handoff with exact changes. If any Open Question above remains unresolved, address it before the implementation run."
-->

{{implementation_handoff_note}}
