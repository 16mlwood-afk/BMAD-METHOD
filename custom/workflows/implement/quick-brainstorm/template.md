---
type: quick-brainstorm-session
target: '{{ask_target}}'
date: '{{date}}'
triage_verdict: divergent
techniques: '{{selected_techniques}}'
grounding_sources: '{{grounding_sources}}'
status: converged
---

# Quick Brainstorm — {{ask_target}}

## Ask

{{ask}}

## Grounding

_What the ideas had to respect — constraints and materials read from the repo before ideation._

{{grounding_summary}}

**Sources read:** {{grounding_sources}}

## Ideas ({{idea_count}})

_Numbered, grouped by theme. User riffs attributed inline._

{{ideas_by_theme}}

## Ranked Shortlist

_Top 3-5, scored against the grounded constraints (impact / feasibility / effort). One-line rationale each._

{{shortlist}}

## Recommendation

_The ONE biased pick and why. A null recommendation ("none clear the bar") is valid._

{{recommendation}}

## Handoff

_Consumer of this artifact, if the recommendation implies action: quick-spec (code change) or design-router (new/redesigned surface — design-router picks the specialist). `n/a` if none._

{{handoff}}
