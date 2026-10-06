---
type: analytics-placement-decision
target_route: {{target_route}}
target_slug: {{target_slug}}
placement_verdict: {{placement_verdict}}   # band | tab | sibling-page | remove-band | no-surface
is_net_new_scope: {{is_net_new_scope}}
band_belongs: {{band_belongs}}             # §5b: inherited | recommended-new | recommended-drop | none
topology_verdict: {{topology_verdict}}     # §5d: single-page-appropriate | needs-tab-views | needs-sibling-route | unresolved
analytics_shape: {{analytics_shape}}       # analytics-surface-architect archetype, or n/a
surface_hierarchy: {{surface_hierarchy}}   # single | per-surface hero|supporting|drill ranking
decided_at: {{date}}
# NOTE: this is a TRIAGE record, not a brief. No brief provenance block; not consumed by the provenance contract.
---

# Analytics Placement Decision: {{target_route}}

**Verdict: {{placement_verdict}}**

## The question
Add analytics to `{{target_route}}` answering: "{{analytics_question}}".
Dataset: {{analytics_dataset}}. Existing surface on the page: {{existing_band}}.

## How the verdict was reached (borrowed brains, single-sourced)

| Decision | Source (applied verbatim) | Outcome |
|---|---|---|
| Does an analytics surface belong? | design-handoff step-01 §5b (band-belongs) | {{band_belongs}} |
| Is it its own surface? | design-handoff step-01 §5d (topology) | {{topology_verdict}} |
| Ranking (if >1 surface) | design-handoff step-01 §5e (hierarchy) | {{surface_hierarchy}} |
| What shape? | analytics-surface-architect skill | {{analytics_shape}} |

## Placement rationale
{{One short paragraph: why this home and not the others. For net-new scope, why the
band-on-page option was rejected. For `unresolved`, the two co-equal jobs and the
ask/route that followed.}}

## Net-new scope
{{If is_net_new_scope: state that this adds a tab / sibling page and was surfaced for
veto. If false: "Rides the existing operational page — no new surface area."}}

## Next action (NOT auto-run)
```
{{handoff_invocation}}
```
{{For band: note upgrade-vs-add against the existing band. For sibling-page: page_mode
must be analytical. For no-surface: no handoff — the data + job do not justify a surface.}}
