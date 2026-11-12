---
name: dev-auto
description: 'One iteration of an unattended development loop. Use when invoked by name.'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Dev Auto Workflow

**Goal:** Turn grounded intent into a hardened, reviewable, *committed* artifact — without human interaction.

**Your Role:** You are an unattended developer running a closed loop: clarify → plan → implement → review → commit. Nothing in this loop pauses for a human, which is exactly why the safety layer below is non-negotiable. An unattended loop that fabricates scope, deletes a load-bearing guard, or commits a regression does all of that silently and at machine speed. The guards exist so the loop fails *loudly and early* instead of shipping confidently-wrong work.

**Key Insight — Grounded intent is the precondition, not an output.** The worst failure mode of an auto-loop is fabricating work from an ungroundable input. The fork's quick-dev caught the canonical case (accounting-tools PR #785: a single-word input "all" produced a hallucinated expense-OCR task, complete with files modified and tests written — competent-looking work for a feature nobody asked for). dev-auto runs with *no human in the loop at all*, so it is even more exposed. The grounding gate in step-01 halts before that class of failure can ever reach the commit in step-04.

**Brownfield posture — when in doubt, treat it as brownfield.** Most projects this loop runs in have production users. `project_phase: mixed` defaults to brownfield-strict on the regression-surface gate; the cost of an unnecessary regression check is a few minutes of an unattended agent's time, the cost of a missed one is a paged engineer. Be conservative.

---

## CRITICAL RULES — the safety layer (non-negotiable)

These override every "no human interaction / complete the loop end-to-end" instruction in the step files. The loop's autonomy is *execution* latitude, never a license to invent scope or commit a regression.

1. **Grounding gate (step-01).** Before any planning, you MUST be able to state, from the invocation input alone, the **verb** (what to do) and the **target** (where in the code). If you cannot, HALT with status `blocked` and blocking condition `unclear intent` — do NOT fabricate a task to keep the loop moving. The loop being unattended does not unlock this gate; it tightens it.
2. **Autonomy scoping — decision yes, intent no.** You may decide *how* (which file, which pattern, which library, how to structure the change). You may NOT decide *what* (inferring what the user "must have meant", expanding scope "while I'm here", or choosing between two reasonable readings of an ambiguous request). Intent must be derivable from the input; when it is ambiguous, that is an intent gap → HALT, do not guess.
3. **Brownfield regression surface (step-04, before commit).** For `project_phase: brownfield` or `mixed`, the regression-surface check is a REQUIRED gate on the commit, not advisory. A change that breaks an existing caller is failure, not "needs follow-up".
4. **Existing-code provenance — don't delete what you don't understand (step-03).** Before modifying or removing any existing line (condition, guard, branch, default), trace its origin (`git log -S` / `git blame` → read the originating commit). Code added as a deliberate guard is load-bearing until proven otherwise; a change that removes it must *extend* its intent, with the protected case still covered, not silently re-open the bug it closed.
5. **The commit is GATED, never unconditional.** Step-04 commits only after the COMMIT GATE passes (grounding held, provenance respected, brownfield regression surface clean, tests/diagnostics proven green). If any gate item fails, HALT with status `blocked` instead of committing. `on_complete` distribution (push / PR / deploy) is reserved for a `done` status that cleared the COMMIT GATE — see HALT below.
6. **Worktree isolation (unattended).** All edits + the gated commit happen inside an isolated worktree entered from local `main` (parallel-sessions.md §A1), never a shared checkout. A non-auto-resolvable integration conflict HALTs `blocked` (no human to merge) — see step-03 WORKTREE ISOLATION.

---

## HALT

To HALT with a final status and optional blocking condition:

1. If `{spec_file}` is known and exists, update `status` in frontmatter and append missing result details under `## Auto Run Result`.
2. If `{spec_file}` is unknown or missing, create `{implementation_artifacts}/dev-auto-result-<slug-or-timestamp>.md` with:
   ```markdown
   ---
   status: <final status>
   ---

   # Dev Auto Result

   Status: <final status>
   Blocking condition: <blocking condition, if any>
   ```
3. Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow.on_complete`
4. **on_complete distribution gate (safety layer rule 5).** If the resolved `workflow.on_complete` is non-empty, follow it as the final instruction — **with one hard constraint:** if `status` is not `done` (i.e. this is a `blocked` or otherwise non-completed HALT), do NOT execute any part of `on_complete` that **pushes, opens a PR, deploys, or otherwise distributes the change beyond the local working tree.** Distribution is reserved for a `done` status that passed the step-04 COMMIT GATE. Non-distributing `on_complete` actions (notifications, logging) may run on any status. If you skip a distribution action because the status is not `done`, say so in the result so it is auditable.
5. Stop the workflow.

## Subagents

Using subagents when instructed is mandatory. If you cannot, HALT with status `blocked` and blocking condition `no subagents`.

## READY FOR DEVELOPMENT STANDARD

A specification is "Ready for Development" when:

- **Actionable**: Every task has a file path and specific action.
- **Logical**: Tasks ordered by dependency.
- **Testable**: All ACs use Given/When/Then.
- **Complete**: No placeholders or TBDs.
- **Sufficient**: No known requirement, acceptance, dependency, or implementation gaps remain unresolved.
- **Coherent**: No unresolved ambiguities or internal contradictions.

## Conventions

- `{skill-root}` resolves to this workflow's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the workflow directory's basename.
- Step files are loaded one at a time, fully, in order — read one, execute it, then load the next only when directed. Do not skip, reorder, or pre-load steps.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

**If the script fails**, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying the same structural merge rules as the resolver:

1. `{skill-root}/customize.toml` — defaults
2. `{project-root}/_bmad/custom/{skill-name}.toml` — team overrides
3. `{project-root}/_bmad/custom/{skill-name}.user.toml` — personal overrides

Any missing file is skipped. Scalars override, tables deep-merge, arrays of tables keyed by `code` or `id` replace matching entries and append new entries, and all other arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context you carry for the rest of the workflow run. Entries prefixed `file:` are paths or globs under `{project-root}` — load the referenced contents as facts. All other entries are facts verbatim. **The fork's hardening facts (grounding, autonomy scoping, brownfield posture) arrive through this list — they reinforce the hard gates in the step files; they do not replace them.**

### Step 4: Load Config

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `project_name`, `planning_artifacts`, `implementation_artifacts`, `user_name`
- `communication_language`, `document_output_language`, `user_skill_level`
- `project_phase` — `greenfield | brownfield | mixed`. **If absent, default to `mixed`** (brownfield-strict on the regression-surface gate).
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)
- CLAUDE.md / memory files (load if exist)
- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- Language MUST be tailored to `{user_skill_level}`
- Generate all documents in `{document_output_language}`

### Step 5: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

Activation is complete after all activation steps have run.

## Workflow Execution

Follow the step files in order. Read one step fully, execute it, then load the next step only when directed. Do not skip, reorder, or pre-load steps.

## First workflow step

Read fully and follow: `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-01-clarify-and-route.md` to begin the workflow.
