---
name: 'step-04-classify-and-route'
description: 'Classify each user-selected enhancement on two axes — intent-change vs in-surface refinement, and design-shaped vs code-shaped — then route each to where the work actually happens (design-handoff re-brief, a focused Claude Design paste prompt, or quick-spec/code) with brief provenance preserved and per-item accountability'
---

# Step 4: Classify and Route

**Progress: Step 4 of 4** — runs only after a non-empty selection

## RULES:

- AUTONOMOUS. The user has already made the intent decision (which enhancements to build) at the step-03 halt. This step does not re-ask — it classifies and routes.
- Per-item accountability is mandatory. Every selected enhancement gets an explicit disposition (routed-to-X / built-here / deferred). Never report success while silently dropping a selected item — that is the silent-partial-implementation failure class.
- Preserve provenance. Routed work carries `{brief_provenance}` forward so the lineage from the original brief to the new work is unbroken.
- Respect brownfield. If `project_phase = brownfield`, routed refinements carry the brownfield obligations (quick-spec §4b, quick-dev §6).
- **Route by where the work actually happens, not just by what changes.** Classification has TWO axes (§1): intent vs in-surface, AND design-shaped vs code-shaped. A design-shaped change (a redesigned region, a new commit footer, a verify-against-source layout) is authored in the project's design tool (Claude Design — the design family's iteration loop), delivered as a **paste-ready prompt**; it must NOT be forced into a code spec. A code-shaped change (an inert control needing a handler, a sort/filter predicate, a dead link, a derived value) is wiring/logic and goes to code. Mis-routing a drawer redesign to quick-spec produces a code spec for work the design tool should author — the gap this step exists to close.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From steps 01–03: `{surface_name}`, `{surface_route}`, `{core_job}`, `{brief_path}`, `{brief_provenance}`, `{screen_review_path}`, `{built_surface_refs}`, `{selected_enhancements}`, `{policy_constraints}`, `{iteration_number}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Classify each selected enhancement — TWO axes

For each item in `{selected_enhancements}`, classify on both axes below. Together they pick the route (§2/§3a/§3b). One axis alone mis-routes — a drawer redesign and a dead-button fix are both "in-surface refinements," but they belong in different tools.

**Axis A — scope: intent-change vs in-surface refinement.**

- **Intent-change** — it changes *what the surface is for*: adds or removes a view/screen, changes the layout goal, introduces a new entity or data the surface didn't carry, or reframes the primary action. Signal: the surface's brief would need to *say something different* to describe the result.
- **In-surface refinement** — it deepens an *existing* interaction within the current surface intent: surfacing an existing signal earlier, closing a one-way loop, a verify stepper over fields that already exist, a GBP-equivalent hint beside an existing total. Signal: the brief's stated job is unchanged; the surface just does it better.

When an item straddles the scope line, classify by the higher bar: if it would make any field of the brief's intent read differently, treat it as an intent-change.

**Axis B — shape: design-shaped vs code-shaped.** (Decides the *tool*, not the brief.)

- **Design-shaped** — closing it changes what the surface *looks like or how the user interacts with it*: a new or redesigned region, a new/changed commit footer, a verify-against-source layout, a new band, a restructured cell. The deliverable is a visual + interaction design, so it is authored in the design tool (Claude Design), not a code spec.
- **Code-shaped** — closing it is wiring or logic behind affordances that already exist visually: an inert control that needs a handler, a sort/filter/severity predicate, a dead link that needs a target, a derived value or status mapping. No new pixels — it belongs in code.

Intent-changes are design-shaped by definition (they re-brief the surface) → §2. In-surface refinements split by Axis B: design-shaped → §3a, code-shaped → §3b. When an in-surface item straddles the shape line (e.g. a mostly-wiring change that also needs a small new affordance), split it into a design-shaped part (§3a) and a code-shaped part (§3b) rather than forcing the whole item down one route.

Record both axes and the one-line reason for each in `{routing_plan}`.

### 2. Route intent-changes through design-handoff

For each intent-change, the brief is the artifact of record and it must be **superseded, not silently outgrown** (brief-revision-policy.md — material change cannot be a hand-edit). Route it by re-running design-handoff for the surface:

- Prepare the design-handoff intake: the surface, the new/changed intent the enhancement introduces, and `{brief_provenance}` of the predecessor brief so design-handoff performs the predecessor lookup and flips the old brief to `superseded`.
- State in `{routing_plan}`: "→ design-handoff (intent-change): [what changes about the surface's job]."
- If `autonomous_mode` permits auto-execution, invoke the design-handoff workflow with that intake. Otherwise emit a paste-ready design-handoff invocation the user can run.

### 3a. Route design-shaped in-surface refinements to a focused Claude Design prompt

The surface intent is unchanged, so this MUST NOT supersede the brief (that is the §2 intent-change path) and MUST NOT go to quick-spec (that produces a *code* spec for a *visual* change the design tool should author). Instead, emit a **focused, brief-descended design prompt** — a paste-ready enhancement prompt for Claude Design: the same connect-the-repo prompt design-handoff emits, scoped down to this one enhancement.

The prompt must contain, in this order:

1. The repo + branch connect line (read it from the brief's "For Claude Design" block so the URL is exact).
2. The specific files to read first — the `{built_surface_refs}` component(s)/route the enhancement touches, the relevant derivation/helper, `{brief_path}`, and `docs/design-policy.md`.
3. A **"keep everything else exactly as-is"** guard naming what NOT to redesign.
4. The precise interaction being deepened and the `{core_job}` facet it serves (grounded in the real surface, not an invented affordance).
5. Any **sibling pattern to borrow** (the coherence lens from step-02) — name the sibling surface and the part to mirror — WITH a grounding caveat to copy the *layout/grammar*, not mismatched *data semantics*.
6. The hard constraints from `{policy_constraints}` that apply (pill shape/4-tone, drawer pattern, accent/mono rules, named anti-defaults) so Claude Design stays conformant.

Then:

- **Save it** to `{implementation_artifacts}/claude-design-prompt-{surface-slug}-{enhancement-slug}.md` so it is copy-pasteable, and surface the prompt inline in the summary.
- Reference `{brief_path}` + `{brief_provenance}` inside the artifact so it is traceable to the (unchanged) brief it descends from. This is a brief *descendant*, not a brief revision — no Block A, no supersede, no 6 intake checks.
- State in `{routing_plan}`: "→ Claude Design prompt (in-surface refinement, design-shaped): [what region gets deepened] · artifact: [path]."
- **Always emit + save the prompt** regardless of `autonomous_mode` — Claude Design is a human-in-the-loop external tool; the workflow's deliverable is the prompt, not a running of it. Do not attempt to invoke Claude Design.

### 3b. Route code-shaped in-surface refinements through quick-spec / code

The surface intent is unchanged and no new pixels are needed — this is wiring or logic. It does not need a new brief or a design prompt; it needs an implementation spec (or, when trivial, a direct branch).

- Prepare the quick-spec intake: the specific refinement, grounded in the real surface (the `{built_surface_refs}` component/route and symbol it touches — e.g. the inert handler, the sort predicate, the dead link target), the `{core_job}` facet it deepens, and a reference to `{brief_path}` + `{brief_provenance}` so the new spec is traceable to the brief it descends from.
- **Trivial wiring may skip quick-spec.** A one-line predicate, a handler for an already-rendered control, or a link target is small enough to implement directly on a branch per the project's delivery rules; quick-spec is for refinements with real implementation surface (multiple files, a new mutation, a regression-prone path). Use judgment; state which you chose.
- For brownfield projects, flag that quick-spec §4b (grounding) and quick-dev §6 (regression-surface) are required, not optional.
- State in `{routing_plan}`: "→ quick-spec / direct code (in-surface refinement, code-shaped): [what gets wired, which files]."
- If `autonomous_mode` permits, invoke quick-spec with that intake; otherwise emit a paste-ready quick-spec invocation.

### 4. Emit the routing summary — humanized, per-item accountability

Produce the closing summary. **Lead with the plain-language disposition the user can act on**, not the internal taxonomy — the user wants to know "what do I paste, and what will you build," not "intent-change vs in-surface refinement." For EVERY selected enhancement, show its disposition — no item is allowed to vanish.

The three plain-language dispositions map 1:1 to the routes:

- **"Paste into Claude Design"** ← §2 intent-change (full re-brief) and §3a design-shaped refinement (focused prompt). Show/point to the saved prompt artifact.
- **"Wire in code (branch + PR)"** ← §3b code-shaped refinement. Name the files.
- **"Re-brief first"** ← §2 intent-change specifically, when the brief must be superseded before design.

```
Selected for build: {N items}

| Enhancement | What happens next | (internal: class · shape · route) |
|---|---|---|
| Reconcile-the-gap drawer | Paste into Claude Design → prompt saved at {path} | in-surface · design-shaped · §3a |
| "Raise comms case" button | Wire in code (branch + PR) — {file:line} | in-surface · code-shaped · §3b |
| ...         | ...               | ...    |

Brief provenance carried forward: {brief filename + revision_mode + last_modified_by/_date}
Deferred / not routed: {any selected item that could not be routed this pass, with the reason}
```

The internal column stays (it is the audit trail and feeds a future elevation pass), but it is the *trailing* column — the headline is the human action. If any selected item could not be routed (e.g. it needs a decision outside this workflow), name it explicitly under "Deferred / not routed" with the blocker — never let it disappear from the summary.

### 5. Persist and close

Write `{selected_enhancements}`, `{routing_plan}`, and the dispositions to the state file so a future elevation pass on this surface knows what was already built or routed. The workflow is complete.
