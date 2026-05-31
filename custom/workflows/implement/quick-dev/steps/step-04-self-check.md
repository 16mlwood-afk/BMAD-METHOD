---
name: 'step-04-self-check'
description: 'Self-audit implementation against tasks, tests, AC, and patterns'

nextStepFile: './step-05-adversarial-review.md'
---

# Step 4: Self-Check

**Goal:** Audit completed work against tasks, tests, AC, and patterns before external review.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)
- `{project_context}` - Project patterns (if exists)

---

## SELF-CHECK AUDIT

### 1. Tasks Complete

Verify all tasks are marked complete:

- [ ] All tasks from tech-spec or mental plan marked `[x]`
- [ ] No tasks skipped without documented reason
- [ ] Any blocked tasks have clear explanation

### 2. Tests Passing

Verify test status:

- [ ] All existing tests still pass
- [ ] New tests written for new functionality
- [ ] No test warnings or skipped tests without reason

### 3. Acceptance Criteria Satisfied

For each AC:

- [ ] AC is demonstrably met
- [ ] Can explain how implementation satisfies AC
- [ ] Edge cases considered

### 4. Patterns Followed

Verify code quality:

- [ ] Follows existing code patterns in codebase
- [ ] Follows project-context rules (if exists)
- [ ] Error handling consistent with codebase
- [ ] No obvious code smells introduced

### 5. Production Data Reality Check (if applicable)

**Run this check when UI was built for database fields.** Query production to verify the data the UI depends on actually exists:

- [ ] Every field displayed in the UI has been verified against the production database
- [ ] Fields with zero population are documented with an explanation (e.g., "API doesn't return this field")
- [ ] No UI element relies solely on data that is 100% null in production without the user being informed
- [ ] If the pre-flight check (step-03) was run, verify results still hold after implementation

If gaps are found post-implementation, report them clearly:

```
**Data Gap Report:**
| Field | Expected | Actual | Explanation |
|-------|----------|--------|-------------|
| transportationType | populated | all null | SP-API does not return shippingSolution for these shipments |
```

**Root cause for data fixes (REQUIRED when this change wrote to, corrected, or backfilled stored data).** Amending production data without fixing the code that produced the bad data is a failed quick-dev for a data-quality defect — the next write re-introduces it. Tick all three or the fix is incomplete:

- [ ] **Producer identified.** The code that wrote the bad data (extractor, ingest, importer, sync, migration) was located — not just the rows it left behind.
- [ ] **Producer fixed.** New writes are now correct at the source — OR it is documented in one sentence why the data can only be wrong historically and cannot recur (e.g., an upstream format that has since changed). "It's just old data" without that sentence does not qualify.
- [ ] **Backfill is an adjunct, not the fix.** Any one-time correction of existing rows ran *after* the producer fix shipped, and was previewed before it mutated production.

If you backfilled but did not touch the producing code, state explicitly why the defect cannot recur. If you cannot, return to step-03 — a data-only patch is not done.

### 6. Regression Surface (REQUIRED for brownfield/mixed; optional for greenfield)

> **Skip this section ONLY if `project_phase: greenfield`.** For brownfield and mixed, this is a hard gate: production users depend on the existing behavior of any code you touched.

For each function, component, or schema field you modified:

- [ ] **Callers identified.** Listed every caller/dependent that consumed the old behavior (grep for the symbol; trace imports).
- [ ] **No callers broken.** Type-checked or compiled — no errors introduced. If the project has tests for the affected files, they pass. If not, the absence of tests is itself noted.
- [ ] **Behavior contract documented.** If the change is non-trivial, a one-sentence "before → after" of the contract is recorded (in the tech-spec for Mode A; in your summary for Mode B).
- [ ] **Rollback path known.** You can state in one sentence how to revert this change if production breaks.

If you can't tick all four boxes, the change is not done — return to step-03 and address the gap. Do NOT proceed to adversarial review until the regression surface is clean.

```
**Regression Surface Report (brownfield/mixed):**
| Symbol Touched | Callers | Tests Pass? | Rollback |
|---|---|---|---|
| matchSupplier() | invoices.svelte, queries.svelte, admin/match-batch | yes (3 unit, 0 integration) | revert PR + redeploy; no schema change |
```

---

## UPDATE TECH-SPEC (Mode A only)

If `{execution_mode}` is "tech-spec":

1. Load `{tech_spec_path}`
2. Mark all tasks as `[x]` complete
3. Update status to "Implementation Complete"
4. Save changes

---

## IMPLEMENTATION SUMMARY

Present summary to transition to review:

```
**Implementation Complete!**

**Summary:** {what was implemented}
**Files Modified:** {list of files}
**Tests:** {test summary - passed/added/etc}
**AC Status:** {all satisfied / issues noted}

Proceeding to adversarial code review...
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-05-adversarial-review.md`.

---

## SUCCESS METRICS

- All tasks verified complete
- All tests passing
- All AC satisfied
- Patterns followed
- Tech-spec updated (if Mode A)
- Summary presented
- Production data gaps documented (if data-display task)

## FAILURE MODES

- Claiming tasks complete when they're not
- Not running tests before proceeding
- Missing AC verification
- Ignoring pattern violations
- Not updating tech-spec status (Mode A)
- Shipping UI for fields that are 100% null in production without documenting the gap
- Skipping §6 Regression Surface on a brownfield/mixed project
