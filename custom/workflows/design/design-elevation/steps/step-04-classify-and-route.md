---
name: 'step-04-classify-and-route'
description: 'Classify each user-selected enhancement as an intent-change or an in-surface refinement, and route each into the correct downstream build workflow with brief provenance preserved and per-item accountability'
---

# Step 4: Classify and Route

**Progress: Step 4 of 4** — runs only after a non-empty selection

## RULES:

- AUTONOMOUS. The user has already made the intent decision (which enhancements to build) at the step-03 halt. This step does not re-ask — it classifies and routes.
- Per-item accountability is mandatory. Every selected enhancement gets an explicit disposition (routed-to-X / built-here / deferred). Never report success while silently dropping a selected item — that is the silent-partial-implementation failure class.
- Preserve provenance. Routed work carries `{brief_provenance}` forward so the lineage from the original brief to the new work is unbroken.
- Respect brownfield. If `project_phase = brownfield`, routed refinements carry the brownfield obligations (quick-spec §4b, quick-dev §6).
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From steps 01–03: `{surface_name}`, `{surface_route}`, `{core_job}`, `{brief_path}`, `{brief_provenance}`, `{selected_enhancements}`, `{policy_constraints}`, `{iteration_number}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Classify each selected enhancement

For each item in `{selected_enhancements}`, decide its class — this determines its route:

- **Intent-change** — it changes *what the surface is for*: adds or removes a view/screen, changes the layout goal, introduces a new entity or data the surface didn't carry, or reframes the primary action. Signal: the surface's brief would need to *say something different* to describe the result.
- **In-surface refinement** — it deepens an *existing* interaction within the current surface intent: surfacing an existing signal earlier, closing a one-way loop, a verify stepper over fields that already exist, a GBP-equivalent hint beside an existing total. Signal: the brief's stated job is unchanged; the surface just does it better.

When an item straddles the line, classify by the higher bar: if it would make any field of the brief's intent read differently, treat it as an intent-change. Record the classification and the one-line reason in `{routing_plan}`.

### 2. Route intent-changes through design-handoff

For each intent-change, the brief is the artifact of record and it must be **superseded, not silently outgrown** (brief-revision-policy.md — material change cannot be a hand-edit). Route it by re-running design-handoff for the surface:

- Prepare the design-handoff intake: the surface, the new/changed intent the enhancement introduces, and `{brief_provenance}` of the predecessor brief so design-handoff performs the predecessor lookup and flips the old brief to `superseded`.
- State in `{routing_plan}`: "→ design-handoff (intent-change): [what changes about the surface's job]."
- If `autonomous_mode` permits auto-execution, invoke the design-handoff workflow with that intake. Otherwise emit a paste-ready design-handoff invocation the user can run.

### 3. Route in-surface refinements through quick-spec

For each in-surface refinement, the surface intent is unchanged, so it does not need a new brief — it needs an implementation spec. Route it to quick-spec → quick-dev:

- Prepare the quick-spec intake: the specific refinement, grounded in the real surface (the component/route it touches), the `{core_job}` facet it deepens, and a reference to `{brief_path}` + `{brief_provenance}` so the new spec is traceable to the brief it descends from.
- For brownfield projects, flag that quick-spec §4b (grounding) and quick-dev §6 (regression-surface) are required, not optional.
- State in `{routing_plan}`: "→ quick-spec (in-surface refinement): [what gets deepened, which files]."
- If `autonomous_mode` permits, invoke quick-spec with that intake; otherwise emit a paste-ready quick-spec invocation.

### 4. Emit the routing summary — per-item accountability

Produce the closing summary. For EVERY selected enhancement, show its disposition — no item is allowed to vanish:

```
Selected for build: {N items}

| Enhancement | Class | Routed to | Status |
|---|---|---|---|
| Live preflight before save | in-surface refinement | quick-spec | invoked / paste-ready below |
| Verify stepper | in-surface refinement | quick-spec | invoked / paste-ready below |
| ...                         | ...   | ...       | ...    |

Brief provenance carried forward: {brief filename + revision_mode + last_modified_by/_date}
Deferred / not routed: {any selected item that could not be routed this pass, with the reason}
```

If any selected item could not be routed (e.g. it needs a decision outside this workflow), name it explicitly under "Deferred / not routed" with the blocker — never let it disappear from the summary.

### 5. Persist and close

Write `{selected_enhancements}`, `{routing_plan}`, and the dispositions to the state file so a future elevation pass on this surface knows what was already built or routed. The workflow is complete.
