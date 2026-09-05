---
name: 'step-01-load-settled-state'
description: 'Load the settled surface and its artifacts of record, run brief intake checks, and derive the one-sentence core-job statement that every candidate is judged against'
---

# Step 1: Load Settled State

**Progress: Step 1 of 4**

## RULES:

- AUTONOMOUS. No user interaction in this step (the only exception: if the surface cannot be resolved to real code, halt and ask which surface — you cannot elevate what you cannot ground).
- Load the design policy DIRECTLY from `docs/design-policy.md`. Do not inherit it transitively through the brief.
- If a brief exists, it is a consumed artifact — run the intake checks before trusting any field from it.
- The output of this step is `{core_job}`. Everything downstream depends on it being right. Spend the effort to get one true sentence.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## SEQUENCE OF INSTRUCTIONS

### 1. Resolve the surface to real code

From the user's input, locate the actual implementation:

- Resolve `{surface_route}` and the component/route files that render it → `{built_surface_refs}`.
- Read them. You need to know what the surface actually does today — its primary action, its inputs, its commit/save point, its current affordances. Candidates will reference these by name, so read enough to be specific ("the Save button triggers the duplicate check", "the source panel links field→source one-way").
- If the surface cannot be resolved (no matching route/component), **halt** and ask the user which surface they mean. Do not guess and elevate the wrong thing.

### 2. Load the design policy directly

Read `{project-root}/docs/design-policy.md` → `{policy_constraints}`. Capture especially its **named anti-defaults** — the patterns the policy explicitly forbids. These are hard rejects in step-02 regardless of how much leverage a candidate appears to have.

**If `docs/design-policy.md` is absent on main, sweep sibling worktrees before proceeding without it** — a policy authored via `create-design-policy`/`onboard-design-system` is commonly worktree-resident and unmerged: `ls {project-root}/.claude/worktrees/*/docs/design-policy.md 2>/dev/null`. If found, read it and note it is worktree-resident (not yet on main). Elevating without the policy's named anti-defaults loaded means the step-02 reject gate runs blind.

### 3. Find and intake the artifacts of record

Locate the surface's brief and screen-review (explicit if the user named them, else most-recent matching the surface):

```bash
ls -t {implementation_artifacts}/design-brief-*.md 2>/dev/null | head -5
ls -t {implementation_artifacts}/**/screen-review-*.md 2>/dev/null | head -5
# if the main tree is empty, the brief/screen-review may be worktree-resident (authored via design-handoff, unmerged):
ls -t {project-root}/.claude/worktrees/*/_bmad-output/implementation-artifacts/design-brief-*.md 2>/dev/null | head -5
ls -t {project-root}/.claude/worktrees/*/_bmad-output/implementation-artifacts/**/screen-review-*.md 2>/dev/null | head -5
```

When a worktree-resident brief/screen-review is used, record a `worktree-resident, not yet merged to main` caveat alongside `{brief_path}`. The 6 intake checks below still apply unchanged.

If a brief is found → set `{brief_path}` and run the **6 intake checks** from `brief-revision-policy.md` §5 before using any field. Specifically:

1. The brief exists and is readable.
2. Its `target_slug` matches the surface being elevated (not a different feature's brief).
3. It is not in `superseded` state (if it is, find the active successor or halt).
4. Provenance fields are internally consistent (`revision_mode`, `change_class`, `last_modified_by`/`_date`).
5. No forbidden material-change-as-hand-edit (the §3 forbidden combination).
6. The brief's content is consistent with the built surface — if the brief describes a surface materially different from what the code shows, the brief is stale; note it and prefer the code (precedence rule 2 > 3).

On any check failure, **halt** with the prescribed diagnostic (what failed, which check, what would satisfy it). Read the 10-field provenance block into `{brief_provenance}` for carry-forward.

If no brief exists, that is allowed — many surfaces are elevated from code + screen-review alone. Set `{brief_provenance}` empty and derive `{core_job}` from the code and screen-review.

### 4. Load prior elevation state

If `{state_file_path}` exists, load `{prior_candidates}` plus prior selections and explicit declines, and increment `{iteration_number}`. A re-run must not re-propose what was already accepted or declined unless the user asks for it.

### 5. Derive the core-job statement — the deliverable of this step

Write `{core_job}`: one sentence naming the **primary decision or action this surface exists to enable** — the thing the user is here to do, the moment that matters. Ground it in the brief's stated purpose and what the built surface is actually optimized around.

Good core-job statements name a decision or an action and its stakes:

- "Decide, before committing, whether this imported invoice is a duplicate and whether it will go live or be held."
- "Verify the few AI-extracted fields that are low-confidence, without re-reading the ones the model got right."
- "Reconcile a CDS line against its matching invoice and confirm the duty figure before filing."

Bad core-job statements are feature inventories ("a form with fields and a save button") — those describe the surface, not its job, and they invite additive candidates. If your draft reads like a feature list, you have not found the job yet.

If the user supplied a focus ("the pre-commit decision"), narrow `{core_job}` to that facet for this pass and note the narrowing.

### 6. Persist and proceed

Write `{surface_name}`, `{surface_route}`, `{core_job}`, `{brief_path}`, `{brief_provenance}`, `{screen_review_path}`, `{built_surface_refs}`, `{policy_constraints}`, `{iteration_number}`, and `{prior_candidates}` to the state file.

**NEXT:** Read fully and follow `{project-root}/_bmad/bmm/workflows/design/design-elevation/steps/step-02-generate-candidates.md`.
