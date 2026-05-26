<!--
Template: screen-review-{target_slug}-{date}.md
Used by: design-artifact-loop in modes `review-only` and `refine-screen` (when a screen-review must be synthesized before a refinement handoff).
File-format-compatible with the artifact emitted by the `design-review --artifact` workflow, so downstream `design-handoff` and `design-tuning` runs can consume either source interchangeably.

Placeholder → state variable mapping:
- {{target_label}}            → state.target_label
- {{target_url}}              → optional; empty string if not in handoff
- {{target_route}}            → state.target_route
- {{target_slug}}             → state.target_slug
- {{component_path}}          → optional; from artifact frontmatter or empty
- {{peer_paths}}              → optional list; one path per line, indented `  - `
- {{generated_at}}            → ISO 8601 datetime
- {{policy_path_or_empty}}    → resolved policy path, or empty string
- {{mode}}                    → "review-only" or "refine-screen"
- {{source_artifact_path}}    → state.artifact_path (the handoff source, NOT this output)
- {{user_role}}, {{frequency}}, {{stakes}}, {{out_of_scope}} → from context block
- {{sources_consulted_line}}  → built in step 3 from sister-skill invocations
- {{evidence_gaps}}           → comma-separated or "none"
- {{verdict}}                 → FAIL | PASS WITH ISSUES | PASS | INDETERMINATE
- {{verdict_rationale}}       → one sentence
- {{severity_summary.*}}      → integer counts
- {{violations_block}}        → repeated V-blocks; one per issue (template below the frontmatter)
- {{keepers_block}}           → bullet list
- {{edge_states_block}}       → bullet list with rationale
- {{peer_steals_block}}       → bullet list
- {{measurements_block}}      → YAML-ish or empty
- {{anti_ai_checklist_block}} → three checkbox lines with rationale

Violations rule: do not cap, do not pad. Emit every issue you'd act on. Order by severity (hard failure → major → minor); within a severity, by impact on comprehension, trust, and task flow. V1, V2, … are STABLE IDs — never re-number across iterations of the same target.
-->

---
type: screen-review
target: {{target_label}}
target_url: {{target_url}}
target_route: {{target_route}}
target_slug: {{target_slug}}
component_path: {{component_path}}
peer_paths:
{{peer_paths}}
generated_at: {{generated_at}}
policy_path: {{policy_path_or_empty}}
mode: {{mode}}
source_artifact: {{source_artifact_path}}
severity_summary:
  hard_failure: {{severity_summary.hard_failure}}
  major: {{severity_summary.major}}
  minor: {{severity_summary.minor}}
verdict: {{verdict}}
---

# Screen Review: {{target_label}}

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

## Verdict

**{{verdict}}** — {{verdict_rationale}}

## Violations

<!--
One block per issue, ordered hard failure → major → minor. V-IDs are stable; downstream refinement briefs cite them by ID.
For INDETERMINATE verdicts (no visual evidence), this section may be empty; surface the gap in Evidence Gaps above instead of inventing violations.
-->

{{violations_block}}

## Keepers

<!-- Page-wide protections. Things refinement must NOT break. Distinct from per-violation "Do not change". -->

{{keepers_block}}

## Edge States to Test

<!-- States the design must produce variants for. Pull from real data conditions, not generic loading/error states. -->

{{edge_states_block}}

## Peer Steals

<!-- Patterns from peer pages worth porting. Empty if no peers identified. -->

{{peer_steals_block}}

## Measurement Evidence

<!-- Raw numbers when available (font sizes, scroll widths, cell counts). YAML-ish for parseability. Empty when no visual evidence loaded. -->

```yaml
{{measurements_block}}
```

## Anti-AI Checklist

<!--
Three binary checks the page must pass on top of the violation list.
If any item is [ ] (failed), there MUST be a matching `hard failure` violation block above. The checklist is a cross-check, not a parallel track.
Wording is fixed across projects; only the per-line rationale changes.
-->

{{anti_ai_checklist_block}}

## Out-of-Scope Reminder

This review is bounded to `{{mode}}`. Changes beyond that scope (route changes, new flows, wholesale component swaps, IA redesign) are NOT in scope for the follow-on refinement and should be raised as a separate design-from-brief run.
