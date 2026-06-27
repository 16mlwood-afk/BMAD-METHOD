---
name: 'step-03-execute'
description: 'Execute implementation - iterate through tasks, write code, run tests'

nextStepFile: './step-04-self-check.md'
---

# Step 3: Execute Implementation

**Goal:** Implement all tasks, write tests, follow patterns, handle errors.

**Critical:** Continue through ALL tasks without stopping for milestones.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)
- `{project_context}` - Project patterns (if exists)

From context:

- Mode A: Tasks and AC extracted from tech-spec
- Mode B: Tasks and AC from step-02 mental plan

---

## §0. BLAST-RADIUS ELIGIBILITY — classify BEFORE any edit (both modes)

**This is the one funnel both modes pass through** (Mode A: step-01→03; Mode B: step-01→02→03), so the scope ceiling lives here — it covers the tech-spec path that previously skipped step-01's Mode-B-only escalation check entirely.

Read fully and follow `{project-root}/_bmad/bmm/workflows/shared/blast-radius-eligibility.md`. Classify the intended change surface into `tiny-patch` / `contained-feature` / `not-quick-dev`. On `not-quick-dev` (any HARD trigger — schema/migration, auth, payments, shared-infra, or over the project's file/diff threshold), **halt and reroute regardless of `autonomous_mode`** (mirrors the grounding gate), then **EXIT quick-dev**. Otherwise record the band + one-line reason — step-07 echoes it as the eligibility line, and step-07's deterministic `quick-dev-blast-radius-check` re-checks the *observed* diff as the backstop.

Do this **before** opening a worktree — no point isolating work you're about to reroute.

---

## OPEN: ENTER A WORKTREE BEFORE EDITING `src/`

**Before writing or editing any file under `src/` (or any tracked, non-`_bmad-output` path), enter an isolated git worktree** — do NOT edit `src/` on the main checkout. Follow `shared/parallel-sessions.md` §A1:

- Base the worktree on **local `main`** (parallel sessions merge locally, so `origin` is usually behind and a fresh-from-origin worktree would lack the foundation your work depends on), on a descriptive branch (`<type>/<short-description>`), then `EnterWorktree` into it.
- From inside the worktree, resolve `{project-root}` via `git rev-parse --show-toplevel` (`shared/worktree-portability.md` §1) — every path is worktree-relative from here.

Skip ONLY if the user explicitly said "you're the only session, skip the worktree," or this run writes nothing under `src/` (an `_bmad-output`-only change — that dir is hook-allowlisted and needs no worktree). When in doubt, open one: a worktree of one is free; a collision is not.

---

## PRE-FLIGHT: PRODUCTION DATA REALITY CHECK

**Trigger:** Run this check when the task involves displaying, mapping, or building UI for database fields — especially fields a spec claims "already exist" or "are populated."

Before implementing UI for data fields:

### 1. Identify Data Claims

- List every field the spec or instructions say the UI should display
- Note which fields the spec claims are populated vs. which are new/empty

### 2. Verify Against Production

Query the production database to check actual population rates:

```sql
-- Count non-null values for each field under consideration
SELECT
  COUNT(*) FILTER (WHERE field_a IS NOT NULL) AS has_field_a,
  COUNT(*) FILTER (WHERE field_b IS NOT NULL) AS has_field_b,
  COUNT(*) AS total
FROM target_table;
```

### 3. Build a Reality Table

Present findings before writing UI code:

```
| Field              | Spec says populated | Actually populated | Count |
|--------------------|---------------------|--------------------|-------|
| carrierName        | yes                 | yes                | 20    |
| transportationType | yes                 | NO — all null      | 0     |
```

### 4. Adjust Plan

- **Fields with data:** Implement UI as planned
- **Fields with zero data:** Flag to user. Options:
  - (a) Still add UI with graceful dash/empty handling (future-proofing)
  - (b) Skip UI for empty fields and focus on fields with real data
  - (c) Investigate the import pipeline to understand why data is missing
- In autonomous mode: choose (a) but explicitly log which fields are empty and why, so the user sees the gap immediately rather than discovering it later in production

**Skip condition:** If the task does not involve displaying database fields (e.g., refactoring, infra changes, pure logic), skip this section entirely.

---

## PRE-FLIGHT: NEW COLUMN / ENRICHMENT-OUTPUT BACKFILL METHOD

**Trigger:** Run this check when the task adds a new column whose value is produced by an enrichment job, scraper, or other automated pipeline (i.e. the column needs to land on existing rows, not just new writes).

### 1. Prefer the schema-version sweep

The recommended way to propagate a new enrichment column to existing rows is the **schema-version sweep**: a single backstop cron compares each row's recorded enrichment version against the code's expected version and re-enqueues full enrichment for rows that are behind. The default plan should be: add the column, populate it in the enrichment job, bump the version constant — let the sweep handle the rest.

### 2. Do not propose tacky production UI

Do **NOT** propose adding operator-facing UI buttons in the production app to trigger backfills (e.g. "Enrich X", "Backfill Y", "Refresh Z" buttons). The user has explicitly rejected these. Production UI is for end-user workflows, not operator-triggered pipelines.

Admin endpoints, rearm-style scripts, ad-hoc backfill scripts, and SQL fixes are **not** banned — they are legitimate engineering tools for re-running failed enrichments, one-time data corrections, or paths the sweep doesn't cover. Use judgment; just don't surface them as production UI.

### 3. Recommended deliverables when adding a new enrichment column

- The new column on the schema (with appropriate nullability)
- The enrichment job populates the new field
- The version constant is bumped (one number, in code) so the sweep picks up existing rows
- PR description notes how existing rows will be backfilled (sweep, or another mechanism if the sweep doesn't cover this path)

### 4. Skip condition

Skip this section if the task is not adding an enrichment-output column — e.g. UI-only work, pure refactor, schema changes for fields populated only at write time, infra changes, etc.

---

## PRE-FLIGHT: DESIGN BRIEF SCOPE AUDIT

**Trigger:** Run this check when the task originates from a **design brief** (from Claude Design, a design handoff workflow, or any design artifact that describes UI changes for specific pages/views).

Design briefs only cover **specific pages, views, or components**. They are NOT a mandate to rewrite the entire UI. Treating a design brief as a full replacement is a known failure mode — it causes features outside the design scope to be silently deprecated or broken.

### 1. Identify Design Scope

Read the design brief and list exactly which pages/views/components are covered:

```
| Page/View       | In Design Scope? |
|-----------------|------------------|
| Invoice tab     | YES              |
| Transaction tab | NO               |
| CSV Lookup tab  | NO               |
| Settings panel  | NO               |
```

### 2. Audit Existing Features

Before touching any code, enumerate **all** existing features, controls, and UI elements across the app (not just the in-scope area). For each, mark whether it's in-scope for the design brief:

- In-scope features: implement the design brief's vision
- Out-of-scope features: **must remain functionally identical** — do not restructure their HTML, remove their CSS classes, or change their JS wiring

### 3. Shared Resource Check

Identify CSS classes, JS modules, and HTML patterns used by **both** in-scope and out-of-scope views. These are shared resources:

- **Never delete or rename a shared CSS class** without verifying all consumers still work
- **Never remove HTML elements** that out-of-scope JS references (even if the design brief doesn't show them)
- If the design introduces new classes/patterns, **add** them — don't replace shared ones

### 4. Present Scope Summary

Before writing any code, present:

```
**Design scope:** {which pages/views the brief covers}
**Out of scope (will not be modified):** {list of pages/views/features that must remain untouched}
**Shared resources identified:** {CSS classes, JS modules used across scopes}
**Features at risk:** {any feature that could be accidentally broken by the design changes}
```

In autonomous mode: log this summary but proceed. In non-autonomous mode: wait for user confirmation before executing.

### 5. Skip Condition

Skip this section if the task does not originate from a design brief — e.g. bug fixes, refactors, feature additions from a tech-spec, direct user instructions not tied to a design artifact.

---

## PRE-FLIGHT: EXISTING-CODE PROVENANCE CHECK

**Trigger:** Run this check whenever the task **modifies or removes existing code** — a condition, guard, branch, default, constant, or any line that is already there. It does NOT apply to pure additions.

A line that looks redundant, over-cautious, or "obviously simplifiable" is the single most dangerous thing to delete: it may be a deliberate guard added to fix a specific past bug, and removing it silently re-opens that bug. The author's reason is rarely in the line itself — it lives in the commit that introduced it.

### 1. Trace the provenance of the lines you intend to change

Before editing, for each non-trivial line you plan to modify or delete:

```bash
git log -S '<exact code fragment>' --oneline -- <path>   # commits that added/removed this exact text
git log -L '<start>,<end>:<path>' --oneline               # or line-range history
git blame -L '<start>,<end>' <path>                        # who/when → find the commit
```

Then **read the originating commit message and diff** (`git show <sha>`).

### 2. Classify: deliberate vs incidental

- **Incidental** — the line arrived with a bulk move, scaffold, or unrelated change; the commit says nothing about *why this line exists*. Lower risk to change.
- **Deliberate** — the commit message or its PR explains the line as a guard/fix/workaround for a specific case ("fix:", "guard against…", a linked issue, a regression test added alongside it). **Treat it as load-bearing until proven otherwise.**

### 3. For deliberate code, understand the intent before you implement

- Read the commit (and any test it added) until you can state, in one sentence, **what case the code protects**.
- Confirm your change **extends** that intent rather than regressing it: *does the case the original commit protected still hold under my change?*
- If the original guard relied on an assumption that is now wrong, state the **corrected invariant** explicitly and verify your change still covers the original's protected case (via the existing test, or a new one).

### 4. If your change would undo a deliberate guard

- **Non-autonomous mode:** halt and surface — name the originating commit, what it protected, and why your change is still safe (or ask).
- **Autonomous mode:** proceed only if you can show the protected case is still covered (a passing test that exercises it), and log the originating commit + the preserved invariant in your summary so it lands in the PR description. If you cannot show coverage, halt.

### 5. Skip condition

Skip if the task touches no existing lines (pure addition), or if `project_phase: greenfield` and the touched code has no production consumers.

---

## EXECUTION LOOP

For each task:

### 1. Load Context

- Read files relevant to this task
- Review patterns from project-context or observed code
- Understand dependencies

### 2. Implement

- Write code following existing patterns
- Handle errors appropriately
- Follow conventions observed in codebase
- Add appropriate comments where non-obvious

### 3. Test

- Write tests if appropriate for the change
- Run existing tests to catch regressions
- Verify the specific AC for this task

### 4. Mark Complete

- Check off task: `- [x] Task N`
- Continue to next task immediately

---

## HALT CONDITIONS

**HALT and request guidance if:**

- 3 consecutive failures on same task
- Tests fail and fix is not obvious
- Blocking dependency discovered
- Ambiguity that requires user decision

**Do NOT halt for:**

- Minor issues that can be noted and continued
- Warnings that don't block functionality
- Style preferences (follow existing patterns)

---

## CONTINUOUS EXECUTION

**Critical:** Do not stop between tasks for approval.

- Execute all tasks in sequence
- Only halt for blocking issues
- Tests failing = fix before continuing
- Track all completed work for self-check

---

## NEXT STEP

When ALL tasks are complete (or halted on blocker), read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-04-self-check.md`.

**CRITICAL — DO NOT IMPROVISE DELIVERY.** Even in autonomous mode, you MUST proceed through ALL remaining steps (04 → 05 → 06 → 07 → 08) by reading each step file. Steps 07 (deliver) and 08 (handoff) contain worktree-safety rules that prevent the parallel-sessions hook from blocking file writes. Skipping these steps and running your own ad-hoc commit/merge/exit sequence is a known failure mode — the handoff file write gets blocked because `ExitWorktree` was called too early.

---

## SUCCESS METRICS

- All tasks attempted
- Code follows existing patterns
- Error handling appropriate
- Tests written where appropriate
- Tests passing
- No unnecessary halts
- Production data reality check performed when task involves displaying DB fields
- New enrichment columns default to the schema-version sweep for backfill, with a deliberate alternative noted in the PR if the sweep doesn't cover the path

## FAILURE MODES

- Stopping for approval between tasks
- Ignoring existing patterns
- Not running tests after changes
- Giving up after first failure
- Not following project-context rules (if exists)
- Building UI for fields assumed populated without verifying production data
- Not presenting the reality table before implementing data-display UI
- Proposing tacky operator-facing UI buttons in the production app to trigger backfills/re-enrichment
- Implementing a design brief as a full UI replacement instead of scoped changes
- Removing or breaking features/pages/views that are outside the design brief's scope
- Deleting shared CSS classes or HTML elements used by out-of-scope views
