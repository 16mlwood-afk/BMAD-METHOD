---
name: 'step-02-generate-candidates'
description: 'Generate enhancement candidates that deepen the core job, then run the anti-chrome filter — rejecting additive/decorative ideas and disclosing each rejection with a reason'
---

# Step 2: Generate Candidates

**Progress: Step 2 of 4**

## RULES:

- AUTONOMOUS. No user interaction.
- Generate WIDE, then filter HARD. The point is not a short list of safe ideas; it is a deliberately wide sweep narrowed by an explicit anti-chrome filter, so the survivors are defensible and the rejects are visible.
- Every candidate must be grounded in the real surface (`{built_surface_refs}`) and aimed at `{core_job}`. No invented affordances.
- The rejected set is part of the deliverable. Never silently drop an additive idea — record it with a one-line reason.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From step-01: `{surface_name}`, `{core_job}`, `{built_surface_refs}`, `{policy_constraints}`, `{brief_path}`, `{screen_review_path}`, `{prior_candidates}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Generate a wide candidate sweep

Brainstorm enhancement ideas for the surface — wide, before any filtering. Pull from these generative lenses, all pointed at `{core_job}`:

- **Earlier signals.** What does the surface currently reveal only *after* the user commits (on Save, on submit, on navigate away) that it could reveal *before*? Moving a signal earlier — duplicate detection, validation, what-will-happen status — is the single most reliable way to deepen a commit-type core job.
- **Open loops.** What relationships on the surface are one-way that could be two-way? (field→source links but not source→field; a list that filters but doesn't jump-to.) Closing a loop deepens the job without adding surface area.
- **Effort on what matters.** Where does the operator spend effort on the high-stakes step vs. the trivial one? A path that walks only the few fields that matter (a verify stepper) deepens the job; a path that re-presents everything does not.
- **Trust and reversibility.** Is the "done/verified" signal trustworthy, or inferred? Can an override be seen and undone? Making the core decision a deliberate, visible, reversible act deepens it.
- **Coherence with sibling surfaces.** Does a sibling surface in this product already solve a piece of this job in a way this surface could adopt? (Borrowing an existing pattern is deepening; inventing a new one is risk.)
- **Burst / repeat use.** If the job is done back-to-back, what carries over between runs and what should reset? Reducing repeat friction deepens a high-frequency job.

Aim for breadth here — 8–15 raw ideas is normal. Do not self-censor at this stage; the filter is next.

### 2. Run the anti-chrome filter

For each raw idea, apply the filter in `checklist.md` (the leverage rubric + the reject gates). Keep an idea only if it **deepens `{core_job}`**. Reject — and record with a one-line reason — anything that:

- **Adds a capability unrelated to the core job.** A new view, a new report, a settings panel, an export the job doesn't need. Scope creep. → `{rejected_candidates}`.
- **Is pure decoration or "delight."** Animation, illustration, a hero, a metric-card grid, color-for-personality. No leverage on the decision. → `{rejected_candidates}`.
- **Is a default/expected affordance with no leverage on THIS surface's job.** "Add dark mode", "add keyboard shortcuts" in the abstract, "add a help tooltip" — generic completeness, not depth. → `{rejected_candidates}` (note: a *specific* keyboard path that walks the verify fields IS leverage; "add keyboard shortcuts" in general is not — be precise about which you mean).
- **Violates a named anti-default in `{policy_constraints}`.** Hard reject regardless of apparent leverage. → `{rejected_candidates}` with the policy rule cited.
- **Competes with the primary surface for attention.** On operational/hybrid pages, an addition that pulls focus from the worklist/primary action is subtraction, not addition. → `{rejected_candidates}`.
- **Was already proposed and declined in a prior pass** (`{prior_candidates}`). Drop silently unless the user re-opened it.

Survivors → `{candidates}`. Each survivor must carry a one-line **why it deepens the job** grounded in the real surface ("the duplicate check fires only on Save; surfacing it live answers the brief's reach-the-user-before-they-commit goal continuously").

### 3. Sanity-check the balance

If `{candidates}` is empty, that is a legitimate and valuable result: the surface is settled and nothing clears the leverage bar. Say so plainly in step-03 rather than manufacturing weak candidates. If `{rejected_candidates}` is empty, you did not sweep wide enough — go back to §1; a real wide sweep always produces additive ideas worth rejecting.

### 4. Persist and proceed

Write `{candidates}` (with per-item rationale) and `{rejected_candidates}` (with per-item reason) to the state file.

**NEXT:** Read fully and follow `{project-root}/_bmad/bmm/workflows/design/design-elevation/steps/step-03-rank-and-recommend.md`.
