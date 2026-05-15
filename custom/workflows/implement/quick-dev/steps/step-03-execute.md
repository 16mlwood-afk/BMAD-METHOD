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
