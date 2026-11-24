---
name: 'step-04-tune'
description: 'Produce the tuning report — prioritized fixes, coverage gaps, and concrete recommendations to improve the workflow ecosystem'
---

# Step 4: Tune

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Every recommendation must be concrete — name the file, the line, and the change.
- Group by effort (quick fix vs structural improvement) so the user can act incrementally.
- Write the report to implementation artifacts, then present a summary.

## AVAILABLE STATE

From previous steps:

- `{workflow_inventory}` — structural map of all workflows
- `{handoff_map}` — workflow connection graph
- `{health_checks}` — individual workflow health findings
- `{contract_map}` — cross-workflow contract verification
- `{coverage_analysis}` — scenario coverage map

## SEQUENCE OF INSTRUCTIONS

### 1. Prioritize All Findings

Merge findings from `{health_checks}`, `{contract_map}`, and `{coverage_analysis}` into a single prioritized list:

**Priority tiers:**

| Tier | Criteria | Examples |
|------|----------|---------|
| **P0 — Broken** | Workflow will fail at runtime | Broken step chain, unproduced state variable, missing step file |
| **P1 — Misaligned** | Workflow runs but produces wrong results or misleading output | Contract mismatch, stale nextStepFile pointer, phase count wrong |
| **P2 — Incomplete** | Workflow works but misses opportunities | Missing coverage for a scenario, orphaned variable, no handoff suggestion |
| **P3 — Cosmetic** | Workflow works fine, just untidy | Naming mismatch, stale phase list, numbering gap |

### 2. Generate Fix Recommendations

For each finding, produce a concrete fix:

```
### {n}. {finding title} — P{priority}

**Workflow:** {workflow_name}
**File:** {file_path}
**Issue:** {specific description}
**Fix:** {exactly what to change — "In step-04-audit.md line 5, change nextStepFile from './step-05-suggest-ui.md' to './step-05-evaluate-purpose.md'"}
**Effort:** {trivial | small | medium | structural}
**Where to edit:** {fork path — ~/bmad-method-v6/custom/workflows/...}
```

### 3. Coverage Recommendations

For each gap in `{coverage_analysis}`:

```
### Gap: {scenario with no coverage}

**What happens today:** {what the user has to do manually}
**Recommendation:** {which existing workflow should add a handoff prompt, OR suggest a new workflow}
**Effort:** {small — add a copy-paste prompt to an existing handoff | medium — modify a workflow step | large — new workflow needed}
```

### 4. Ecosystem Health Score

Compute a simple health score:

```
total_checks = {number of checks performed across all steps}
passed = {checks with no findings}
health_score = passed / total_checks * 100

Breakdown:
- Step chains: {n}/{total} intact
- State variables: {n}/{total} properly flowing
- Contracts: {n}/{total} aligned
- Coverage: {n}/{total} scenarios covered
- Overall: {health_score}%
```

### 5. Write Tuning Report

Write to `{implementation_artifacts}/orchestration-tuning-{date}.md`:

```markdown
---
title: 'Workflow Ecosystem Tuning Report'
created: '{date}'
type: orchestration-tuning
---

# Workflow Ecosystem Tuning Report

**Date:** {date}
**Workflows audited:** {count}
**Total steps:** {count}
**Health score:** {score}%

## Ecosystem Overview

| Workflow | Category | Steps | Health | Connections |
|----------|----------|-------|--------|-------------|
{for each workflow: name, category, step count, pass/fail, outbound connection count}

## Findings by Priority

### P0 — Broken (must fix)
{findings or "None"}

### P1 — Misaligned (should fix)
{findings or "None"}

### P2 — Incomplete (nice to fix)
{findings or "None"}

### P3 — Cosmetic (when convenient)
{findings or "None"}

## Coverage Map

| Scenario | Coverage | Gaps |
|----------|----------|------|
{for each scenario from coverage analysis}

## Quick Fixes (under 5 min each)

{List of trivial/small effort fixes — the user can action these immediately}

## Structural Improvements

{List of medium/structural effort recommendations}

## Workflow Connection Graph

{ASCII representation of the workflow connection graph:}

```
quick-dev ──handoff──> wire-check ──handoff──> trace-flow
    │                                              │
    └──prompt──> design-handoff              prompt──> design-review
```
```

### 6. Present Summary

Display to the user:

```
## Workflow Ecosystem Tuning Complete

**{workflow_count} workflows audited** | **{step_count} steps** | **Health: {score}%**

### Findings

- **P0 (broken):** {count}
- **P1 (misaligned):** {count}
- **P2 (incomplete):** {count}
- **P3 (cosmetic):** {count}

{If P0 findings exist:}
**Critical issues found — fix these first:**
{numbered list of P0 findings with one-line descriptions}

### Quick Fixes Available

{numbered list of trivial fixes the user can action now}

### Coverage Gaps

{list of uncovered scenarios}

**Full report:** {report_file_path}
```

---

## SUCCESS METRICS

- All findings merged and prioritized (P0-P3)
- Every fix recommendation names specific files and changes
- Coverage gaps identified with actionable recommendations
- Health score computed with per-category breakdown
- Report written to implementation artifacts
- Summary presented directly to user
- Quick fixes separated from structural improvements

## FAILURE MODES

- Vague recommendations ("improve error handling in workflows")
- Not specifying WHERE to make changes (fork path vs project path)
- Treating all findings as equal priority
- Producing a report but no summary (user has to go read the file)
- Missing the coverage analysis entirely (only checking individual health, not the system)
