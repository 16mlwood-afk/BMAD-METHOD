---
type: design-routing-decision
request_surface: {{request_surface}}
surface_slug: {{surface_slug}}
felt_want: "{{felt_want}}"
fired_axis: {{fired_axis}}        # lane | altitude | depth | placement
lane: {{lane}}                    # visual | non-visual
altitude: {{altitude}}            # policy | surface
depth: {{depth}}                  # fresh | refine | restyle | elevate | audit | (empty for policy)
placement_dispatch: {{placement_dispatch}}
route_target: {{route_target}}    # specialist workflow + target
decided_at: {{date}}
# NOTE: a TRIAGE record, not a brief. No provenance block; not consumed by the provenance contract.
---

# Design Routing Decision: {{request_surface}}

**Route: {{route_target}}**  ·  fired axis: **{{fired_axis}}**

## The request
"{{felt_want}}" on `{{request_surface}}`.

## How it was classified (axes walked in order)

| Axis | Outcome |
|---|---|
| 1 · lane | {{lane}} |
| 2 · altitude | {{altitude}} |
| 3 · depth | {{depth}} |
| 4 · target + placement | {{placement_summary}} |

## Placement (only when analytics-placement was dispatched)
{{If placement_dispatch: the analytics-placement-triage verdict (band | tab | sibling-page |
remove-band | no-surface) + its rationale, consumed verbatim. Else: "n/a — not an analytics
placement request."}}

## Next action (NOT auto-run)
```
{{handoff_command}}
```
{{For a straddle: both part commands. For policy: include the apply-design-policy-change propagation step.}}

## Surfaced notes
{{Net-new scope a downstream specialist flagged; any straddle split; any deferred axis this
router does not yet wire. One bullet each — never swallowed.}}
