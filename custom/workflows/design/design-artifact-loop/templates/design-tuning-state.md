<!--
Template: design-tuning-state-{target_slug}.md
Used by: design-artifact-loop in `refine-screen` mode to track iteration chains against a single target.
Created on first refine-screen run against {target_slug}; appended on each subsequent run.
This file complements (not replaces) the existing `design-tuning` workflow's state file — they share filename conventions so a single tuning chain can be driven by either workflow without losing history.

Top-of-file fields are stable across iterations; iterations are appended as blocks below the divider.

Placeholder → state variable mapping:
- {{target_label}}, {{target_route}}, {{target_slug}} → state
- {{first_iteration_at}}                              → ISO 8601 datetime of iteration 1
- {{final_accepted_direction}}                        → empty until the user marks the chain "accepted"; set once and never overwritten

Per-iteration block placeholders (filled in step 4):
- {{iteration_number}}        → 1-based, incremented each run
- {{iteration_at}}             → ISO 8601 datetime
- {{iteration_artifact_path}} → absolute path to the handoff or screen-review produced this iteration
- {{previous_failures_block}} → bullet list of V-IDs from the prior iteration that were targeted
- {{fixed_issues_block}}      → V-IDs resolved in this iteration (per the post-implementation re-review)
- {{current_open_issues_block}} → V-IDs still open after this iteration
- {{iteration_notes}}         → free text; sequencing decisions, sister-skill caveats, evidence gaps
-->

---
type: design-tuning-state
target: {{target_label}}
target_route: {{target_route}}
target_slug: {{target_slug}}
first_iteration_at: {{first_iteration_at}}
final_accepted_direction: {{final_accepted_direction}}
---

# Tuning State: {{target_label}}

Iteration chain for the {{target_route}} surface. Each iteration block below is appended by `design-artifact-loop` (mode: refine-screen) and corresponds to one round of refinement + re-review.

The `final_accepted_direction` frontmatter field is empty until the user explicitly accepts a direction. Once set, it is NEVER overwritten — subsequent iterations are layered on top of an accepted baseline, not replacing it.

---

## Iteration block

<!--
Appended per run. New iterations land below this divider; older iterations stay in place (append-only). Do not edit prior blocks.
-->

### Iteration {{iteration_number}} — {{iteration_at}}

- **Artifact produced:** `{{iteration_artifact_path}}`
- **Previous failures targeted:**

{{previous_failures_block}}

- **Fixed in this iteration:**

{{fixed_issues_block}}

- **Still open after this iteration:**

{{current_open_issues_block}}

**Notes:** {{iteration_notes}}

---
