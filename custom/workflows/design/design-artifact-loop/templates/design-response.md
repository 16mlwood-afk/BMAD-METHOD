<!--
Template: design-response-{target_slug}-{date}.md
Used by: design-artifact-loop in mode `design-from-brief` when the brief asks for concept direction rather than immediate implementation.
A design-response is upstream of a design-handoff. After the user reviews the response and accepts a direction, design-artifact-loop is rerun against the response as the canonical artifact, producing an implementation-ready design-handoff on the second pass.
This is the canonical, locked schema for this workflow.

Placeholder → state variable mapping:
- {{target_label}}, {{target_route}}, {{target_slug}} → state
- {{date}}                                           → YYYY-MM-DD
- {{brief_summary_paragraph}}                        → one-paragraph faithful recap of the brief
- {{proposed_screen_structure_block}}                → bullet list naming regions, data, and primary action per region; no template-default vocabulary (no "hero / cards / cta")
- {{answers_to_design_ask_block}}                    → numbered list answering each question from the brief's Design Ask
- {{constraints_honored_block}}                      → bullet list calling out which brief constraints and policy rules the proposal respects
- {{handoff_note_paragraph}}                         → implementation-facing instruction for the next design-artifact-loop pass: what to treat as locked, what's still open, how to invoke the implementation run
- {{sources_consulted_block}}                        → footer; bullet list of skill names invoked during step 3

The workflow's frontend skill routing rule (workflow.md → "Frontend skill routing") REQUIRES design-policy-canonical, operational-finance-ui, and a frontend/webapp skill to be invoked in design-from-brief mode before this file is emitted. Conditional: operational-analytics-band if the proposed structure includes a KPI strip / analytics row / trend band.
-->

# Design Response — {{target_label}}

- Mode: design-from-brief
- Route: `{{target_route}}`
- Slug: `{{target_slug}}`
- Date: {{date}}

## Brief summary

{{brief_summary_paragraph}}

## Proposed screen structure

<!--
Bullet list. Each bullet names a region, the data it surfaces, and the primary action it affords. Avoid template-default vocabulary ("hero / cards / cta"). Avoid speculative components unless the brief asks for them.
-->

{{proposed_screen_structure_block}}

## Answers to design ask

<!--
Numbered list. One answer per open question from the brief's Design Ask section. If a question cannot be answered without further user input, mark it OPEN and explain what input is needed.
-->

{{answers_to_design_ask_block}}

## Constraints honored

<!--
Bullet list. Explicitly map proposal choices back to brief constraints and policy rules. This is the load-bearing section the next pass reads to decide what's locked vs still flexible.
-->

{{constraints_honored_block}}

## Handoff note

{{handoff_note_paragraph}}

---

**Sources consulted:** {{sources_consulted_block}}
