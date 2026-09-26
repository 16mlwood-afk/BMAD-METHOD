---
deferred_work_file: '{implementation_artifacts}/deferred-work.md'
spec_file: '' # set at runtime for both routes before leaving this step
---

# Step 1: Clarify and Route

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- Treat the invocation intent as workflow input, not as a substitute for step-02 investigation and spec generation.
- **EARLY EXIT** means: stop this step immediately, then read and follow the target file. Return here only if a later step explicitly says to loop back.

## GROUNDING GATE (do this FIRST — overrides autonomous behavior)

> This gate is the safety layer's rule 1. It is NOT subject to the loop's "no human interaction / complete end-to-end" posture. The loop grants **decision autonomy** (which file, which pattern, which library — *how* to execute). It does NOT grant **intent autonomy** (deciding *what* the user wants). dev-auto runs with no human in the loop, so an ungroundable input has nothing downstream to catch a fabricated scope before it commits. Ground intent here or HALT.

Use the invocation prompt as the intent. Before doing anything else, you MUST be able to state both of the following **from the invocation input alone** (plus, for a supplied spec, the spec's own contents):

1. **The verb** — the specific action requested, in one sentence (add, remove, refactor, rename, fix, implement…). Not a feeling, not a direction.
2. **The target** — where in this codebase: a file path, a symbol/function/component name, a story/ticket ID that resolves to planning artifacts, or a string a quick `grep` locates uniquely.

### Ungroundable inputs → HALT

You **cannot** derive both verb and target when the input is:

- A single word that is not a verb-target ("all", "go", "do", "yes", "this", "next").
- A pure sentinel / leftover ("ok", ".", "—", a stray flag like `--check`).
- A reference to a thing that does not exist after one quick grep (no file, symbol, or UI surface matches).
- A task description with no nameable target ("clean things up", "make it better", "fix the issues").
- An empty argument list when one was expected.

A short input is not automatically ungroundable — "fix the typo in the queries header" is short but groundable (verb + target). The test is groundability, not length.

**If the input is ungroundable: HALT with status `blocked` and blocking condition `unclear intent`.** In the result, show the literal input you received and which piece (verb or target) is missing. Do NOT invent a task to keep the loop moving. The loop being unattended is the reason this halts, not a reason to push through.

## Intent check (spec routing)

If the invocation prompt explicitly points to an existing spec file with recognized `status` frontmatter, set `spec_file`, then **EARLY EXIT** to the appropriate step:
- `draft` → `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-02-plan.md`
- `ready-for-dev` or `in-progress` → `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-03-implement.md`
- `in-review` → `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-04-review.md`
- `blocked` → HALT with status `blocked` and blocking condition `blocked spec supplied`.
- `done` → set `review_loop_iteration` to `0` in the frontmatter, then **EARLY EXIT** to `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-04-review.md` for a fresh review pass. (A `done` spec is a completed run, so this starts a follow-up review, not a resumption.)

Otherwise, treat the invocation prompt as starting intent (a story ID, ticket ID, file path, short description, or longer free-form intent). Do not infer workflow state from non-spec files.

## INSTRUCTIONS

1. Load context.
   - List files in `{planning_artifacts}` and `{implementation_artifacts}`.
   - If the invocation prompt points to an unformatted spec or intent file, ingest that file. Do not scan for unrelated intent files.
   - **Determine context strategy.** Using the intent and the artifact listing, infer whether the current work is a story from an epic. Do not rely on filename patterns or regex — reason about the intent, the listing, and any epics file content together.

     **A) Epic story path** — if the intent is clearly an epic story:

     1. Identify the epic number `{epic_num}` and (if present) the story number `{story_num}`. If you can't identify an epic number, use path B.

     2. **Check for a valid cached epic context.** Look for `{implementation_artifacts}/epic-<N>-context.md` (where `<N>` is the epic number). A file is **valid** when it exists, is non-empty, starts with `# Epic <N> Context:` (with the correct epic number), and no file in `{planning_artifacts}` is newer.
        - **If valid:** load it as the primary planning context. Do not load raw planning docs (PRD, architecture, UX, etc.).
        - **If missing, empty, or invalid:** compile it in the next bullet.

     3. **Compile epic context if needed.** If no valid cached epic context was loaded, produce `{implementation_artifacts}/epic-<N>-context.md` by spawning a subagent with `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/compile-epic-context.md` as its prompt. Pass it the epic number, the epics file path, the `{planning_artifacts}` directory, and the output path `{implementation_artifacts}/epic-<N>-context.md`.

     4. **Verify if compiled.** If epic context was compiled, verify the output file exists, is non-empty, and starts with `# Epic <N> Context:`. If valid, load it. If verification fails, HALT with status `blocked` and blocking condition `context compilation verification failed`.

     5. **Previous story continuity.** Regardless of which context source succeeded above, scan `{implementation_artifacts}` for specs from the same epic with `status: done` and a lower story number. Load the most recent one (highest story number below current). Extract its **Code Map**, **Design Notes**, **Spec Change Log**, and **task list** as continuity context for step-02 planning. If no `done` spec is found but an `in-review` spec exists for the same epic with a lower story number, HALT with status `blocked` and blocking condition `missing previous-story continuity decision`.

     **B) Freeform path** — if the intent is not an epic story:
     - Planning artifacts are the output of BMAD phases 1-3. Typical files include:
       - **PRD** (`*prd*`) — product requirements and success criteria
       - **Architecture** (`*architecture*`) — technical design decisions and constraints
       - **UX/Design** (`*ux*`) — user experience and interaction design
       - **Epics** (`*epic*`) — feature breakdown into implementable stories
       - **Product Brief** (`*brief*`) — project vision and scope
     - Scan the listing for files matching these patterns. If any look relevant to the current intent, load them selectively — you don't need all of them, but you need the right constraints and requirements rather than guessing from code alone.
2. Resolve intent from the invocation prompt and loaded artifacts. **Stay inside decision autonomy** (safety layer rule 2): you may resolve *how* to implement a grounded intent, but you may NOT resolve an ambiguous *what* by picking the reading you prefer. If, after loading artifacts, the intent admits two genuinely different shippable interpretations, that is an intent gap — do not fantasize and do not leave open questions: HALT with status `blocked` and the unresolved questions as blocking condition.
3. Version control sanity check. Is the working tree clean? Does the current branch make sense for this intent — considering its name and recent history? If the tree is dirty or the branch is an obvious mismatch, HALT with status `blocked` and that condition as blocking condition. If version control is unavailable, skip this check.
4. Multi-goal warning. If the intent appears to contain multiple independently shippable goals, carry `multiple-goals` forward so step-02 can add it to `{spec_file}` frontmatter `warnings`. Do not split or block.
5. Route:

   Derive a valid kebab-case slug from the clarified intent. If the intent references a tracking identifier (story number, issue number, ticket ID), lead the slug with it (e.g. `3-2-digest-delivery`, `gh-47-fix-auth`). If `{implementation_artifacts}/spec-{slug}.md` already exists: if its status is `draft`, treat it as the same work and resume it (set `spec_file` to that path, **EARLY EXIT** → step-02); otherwise append `-2`, `-3`, etc. Set `spec_file` = `{implementation_artifacts}/spec-{slug}.md`.

## NEXT

Read fully and follow `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-02-plan.md`
