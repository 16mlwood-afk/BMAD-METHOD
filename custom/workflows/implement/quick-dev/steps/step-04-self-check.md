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

### 2. MUST-PASS — automated gates (a red here blocks delivery)

These are binary and machine-checked. Any failure stops the workflow until fixed:

- [ ] All existing tests still pass; new tests written for new functionality
- [ ] No test warnings or skipped tests without reason
- [ ] Type-check / lint / build clean where the project configures them (the pre-push hook enforces these — don't discover a red at push time)
- [ ] **Diagnostics gate — prove, don't assert** (`{project-root}/_bmad/bmm/workflows/shared/diagnostics-gate.md`). If ANY new diagnostic surfaced (type error, "cannot find module", lint/compile failure) — including after a merge or worktree teardown — re-run the relevant check IN THE CURRENT CHECKOUT and confirm zero errors. Quote the result. Do NOT reason a diagnostic away as "stale" — a true-stale diagnostic disappears on re-run, and that disappearance is the proof; the explanation is not.

### 2b. MUST-OBSERVE — surfaces a green test suite does NOT cover

Brownfield regressions usually escape through surfaces no unit test exercises. For each that your change touched, state explicitly what you checked (or "n/a — not touched"). Silence here is the failure mode, not a pass:

- [ ] **Migrations / schema** — does a column/table change need a migration? Is it backward-compatible with rows already in production, and with the currently-running server until deploy? (If schema changed, you likely tripped the step-03 §0 ceiling — confirm this still belongs in quick-dev.)
- [ ] **Background jobs / queues** — did a job payload, enqueue call, or worker registration change? A worker runs out-of-band; a stale or mis-shaped payload fails silently with no request to trace. (Cross-boundary payloads: validate via the schema registry per the project's MCP rule.)
- [ ] **Auth / permission scope** — did the change alter who can see or do something — a route guard, role check, ownership filter, or API-key path? Under-restriction is a security bug a test rarely catches.
- [ ] **Config / env / feature flags** — does this need a new env var, secret, or flag set in production? Code that works locally and 500s on deploy because an env var is unset is the classic miss.

If any box surfaces a gap, resolve it here (or in step-03) — do not defer a must-observe gap to "follow-up."

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
- [ ] **Registry / exhaustiveness sync (only when ADDING a member to a source-of-truth set).** If this change adds a value to an enum / const / union / report-type list / status vocabulary that hand-maintained registries elsewhere mirror, you grepped for the new member's **VALUE string** (e.g. the literal `GET_LEDGER_*`), not only its symbol — stringly-typed mirrors (a catalog like `raw-records/data.ts`, a settings panel, an export-column list) couple by bare string and are invisible to a symbol-only caller trace. Every such mirror either got its new entry or is recorded as deliberately N/A.
- [ ] **No callers broken.** Type-checked or compiled — no errors introduced. If the project has tests for the affected files, they pass. If not, the absence of tests is itself noted.
- [ ] **Behavior contract documented.** If the change is non-trivial, a one-sentence "before → after" of the contract is recorded (in the tech-spec for Mode A; in your summary for Mode B).
- [ ] **Rollback path known.** You can state in one sentence how to revert this change if production breaks.
- [ ] **Provenance of changed/removed lines checked.** For any existing line you modified or deleted, you traced its originating commit (`git log -S` / `git blame`) and confirmed the change *extends*, not regresses, whatever it deliberately protected (step-03 existing-code provenance pre-flight). If it undid a deliberate guard, the protected case is still covered by a passing test.

If you can't tick all six boxes, the change is not done — return to step-03 and address the gap. Do NOT proceed to adversarial review until the regression surface is clean. (The registry/exhaustiveness box is N/A — auto-ticked — for a change that adds no new member to a mirrored source-of-truth set.)

```
**Regression Surface Report (brownfield/mixed):**
| Symbol Touched | Callers | Tests Pass? | Rollback |
|---|---|---|---|
| matchSupplier() | invoices.svelte, queries.svelte, admin/match-batch | yes (3 unit, 0 integration) | revert PR + redeploy; no schema change |
```

---

## UPDATE TECH-SPEC (Mode A only)

If `{execution_mode}` is "tech-spec":

1. Load `{tech_spec_path}` and re-read its frontmatter.
2. **Spec-of-record guard (HALT-if-swapped).** Assert the frontmatter `slug` (or `title`) still matches `{tech_spec_slug}` captured at load in step-01. If it differs, the shared `_bmad-output/` spec path was overwritten by a parallel session mid-run — do NOT stamp status onto a stranger's spec. HALT: *"spec-of-record was replaced at `{tech_spec_path}` — your implementation is intact (committed in the worktree), but the artifact lineage is lost; re-resolve the spec before stamping."* (The shared-`_bmad-output`-filename collision class, `docs/fork-gaps.md`.)
3. Mark all tasks as `[x]` complete.
4. Update status to "Implementation Complete".
5. Save changes.

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
- Deleting or rewriting a deliberate guard without reading its originating commit (step-03 existing-code provenance pre-flight)
