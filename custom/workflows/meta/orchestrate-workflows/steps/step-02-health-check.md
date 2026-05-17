---
name: 'step-02-health-check'
description: 'Check each workflow individually for structural issues — broken step chains, missing state variables, stale pointers, frontmatter errors'
---

# Step 2: Health Check

**Progress: Step 2 of 4** — Next: Contract Analysis (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Check every workflow — don't sample. The audit is only valuable if it's exhaustive.
- Every finding must include the specific file and what's wrong. No vague "some workflows have issues."

## AVAILABLE STATE

From Step 1:

- `{workflow_inventory}` — structural map of all workflows
- `{handoff_map}` — which workflows suggest which follow-ups

## STATE VARIABLES (set in this step)

- `{health_checks}` — list of findings per workflow, each with category, severity, file, and fix

## SEQUENCE OF INSTRUCTIONS

### 1. Step Chain Integrity

For each workflow in `{workflow_inventory}`:

- **Verify the chain is complete.** Starting from step-01, follow `nextStepFile` pointers. Every step except the last must have a `nextStepFile`. The last step must NOT have one (or must be null).
- **Verify pointers resolve.** Each `nextStepFile` value (e.g., `./step-02-foo.md`) must correspond to an actual file in the steps directory.
- **Verify numbering is sequential.** step-01 → step-02 → step-03, no gaps, no duplicates.
- **Verify the workflow.md references step-01.** The workflow entry point must point to the first step file.

**Finding categories:**
- `broken-chain` (critical) — nextStepFile points to a file that doesn't exist
- `orphaned-step` (moderate) — step file exists but no other step points to it
- `numbering-gap` (low) — step numbers skip (step-01, step-03) or are out of order
- `missing-entry-point` (critical) — workflow.md doesn't reference step-01

### 2. State Variable Flow

For each workflow:

- **Verify producers before consumers.** If step-03 consumes `{gaps}`, verify that step-01 or step-02 produces it.
- **Verify the workflow.md state list is accurate.** The state variables listed in workflow.md should be the union of all variables produced across all steps.
- **Check for orphaned variables.** Variables produced by one step but never consumed by any subsequent step.
- **Check for unproduced variables.** Variables consumed by a step but never produced by any prior step.

**Finding categories:**
- `unproduced-var` (critical) — step consumes a variable no prior step produces
- `orphaned-var` (low) — step produces a variable no subsequent step or output uses
- `stale-var-list` (low) — workflow.md state list doesn't match actual step production

### 3. Frontmatter Consistency

For each step file:

- **name field present and matches filename convention** (e.g., `step-03-render-pipeline`)
- **description field present** and is a meaningful sentence (not empty or placeholder)
- **nextStepFile uses relative path** (`./step-02-foo.md`, not absolute)

**Finding categories:**
- `missing-frontmatter` (moderate) — required field missing
- `name-mismatch` (low) — name field doesn't match filename

### 4. Workflow.md Consistency

For each workflow.md:

- **Phase count matches step count.** If it says "5 phases" but has 6 step files, flag it.
- **Phase list matches step names.** If it says "map → snapshot → render" but step names are different, flag it.
- **Config references resolve.** If it references `{main_config}`, verify `config.yaml` exists.

**Finding categories:**
- `phase-count-mismatch` (moderate) — documented phase count doesn't match actual step count
- `stale-phase-list` (low) — phase names don't match step descriptions

### 5. Compile Health Report

For each finding:

```
{
  workflow: string,
  file: string,
  category: string,
  severity: "critical" | "moderate" | "low",
  description: string,
  fix: string
}
```

Store as `{health_checks}`.

### 6. Proceed to Contract Analysis

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-03-contract-analysis.md`

---

## SUCCESS METRICS

- Every workflow checked for step chain integrity
- Every state variable flow verified (producer before consumer)
- Frontmatter consistency checked across all step files
- Workflow.md phase counts and lists verified
- All findings stored with specific file references and fixes
- `{health_checks}` populated

## FAILURE MODES

- Checking only a subset of workflows ("the main ones")
- Reporting "step chain looks fine" without actually tracing nextStepFile pointers
- Not distinguishing severity levels (a broken chain is critical; a naming mismatch is low)
- Vague findings without file paths
