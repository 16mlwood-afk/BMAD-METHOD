---
name: 'step-03-diagnose'
description: 'Cluster findings into distinct issues, assign root cause, category, severity, and scope to each'

nextStepFile: './step-04-resolve.md'
---

# Step 3: Diagnose

**Goal:** Transform raw findings into diagnosed issues. Each issue gets a root cause, category, severity, and scope. Compound symptoms are separated — one finding per root cause, not one finding per symptom.

**Principle:** The diagnosis must explain WHY, not just WHAT. "26 invoices have EXTRACTION_PDF_NOT_FOUND" is a finding. "These 26 invoices are from a synthetic batch that was created without uploading actual PDF files — the extraction correctly reported them missing" is a diagnosis.

---

## AVAILABLE STATE

From previous steps:

- `{observation}` — the original symptom
- `{observation_type}` — classification
- `{page_context}` — page, route, feature
- `{findings}` — concrete data points from investigation

## STATE VARIABLES (set in this step)

- `{issues}` — list of diagnosed issues, each with root cause, category, severity, scope, and resolution category

---

## EXECUTION SEQUENCE

### 1. Cluster Findings by Root Cause

Group the findings from step 2 into clusters that share a single root cause. 

**Clustering signals:**
- Same error message → likely same cause
- Same batch/source → likely same cause
- Same time window → likely same cause
- Same code path → likely same cause
- Different error messages but same pipeline stage → possibly same cause, investigate further

**Separation signals:**
- Different error messages AND different sources → separate issues
- Same symptom but different code paths → separate issues
- One is a code bug, another is a data issue → always separate

A single finding can be its own issue. Multiple findings can merge into one issue if they share a root cause.

### 2. Diagnose Each Issue

For each cluster, produce a diagnosis:

#### Assign Root Cause

State the actual cause — not the symptom, not the error message, but WHY this happened:

| Surface symptom | Root cause (example) |
|----------------|---------------------|
| "PDF not found in storage" | Synthetic batch created DB records without uploading actual files |
| "ocr_failed with null error" | Post-extraction classification silently fails and marks as ocr_failed without recording the error |
| "FOREIGN KEY constraint failed" | Enrichment step references a record that was deleted or never created |
| "Column is always empty" | Field is populated in the DB but the API loader doesn't include it in the SELECT |
| "Numbers don't add up" | VAT calculation uses net amount but the stored field is gross |

If you can't determine the root cause from the data, say so — "Root cause unclear: {what you know and what you'd need to confirm}" is a valid diagnosis.

#### Assign Category

| Category | Definition | Downstream workflow |
|----------|-----------|-------------------|
| `bug` | Code produces wrong behavior — wrong status, missing error capture, incorrect calculation | Quick-dev (tech spec) |
| `data-cleanup` | Bad data in production — orphaned records, wrong status, missing references. Code is correct. | In-session fix (admin API/script) or quick-dev for a cleanup script |
| `ux-gap` | Data exists and is correct, but the UI doesn't surface it well — missing columns, confusing layout, no drill-down | Design-handoff |
| `missing-feature` | A capability that doesn't exist yet — no error, just absence | Quick-spec (small) or create-story (large) |
| `config-issue` | Wrong threshold, missing env var, stale cron schedule, incorrect mapping | In-session fix |
| `external-dependency` | Caused by an external service (Amazon API, Xero, HMRC) — not fixable in our code | Document and monitor |

#### Assign Severity

| Severity | Definition |
|----------|-----------|
| `critical` | Data loss, incorrect financial calculations, or blocked user workflow |
| `moderate` | Incorrect display, missing information, or degraded but functional workflow |
| `low` | Cosmetic issues, minor inefficiencies, or edge cases that rarely occur |

#### Assess Scope

| Scope | Definition | Resolution path |
|-------|-----------|----------------|
| `trivial` | Fix in under 5 minutes — admin API call, data update, config change | Resolve in-session (step 4) |
| `small` | Single-file code change, clear fix | Quick-dev direct mode |
| `medium` | Multi-file change, needs a tech spec | Quick-dev with tech spec (Mode A) |
| `large` | New feature or significant rework | Create-story or full spec |

### 3. Check for Compound Diagnoses

Before finalizing, verify:

- **Did you separate compound symptoms?** If the original observation was "37 invoices failed" and you found 3 different causes, you should have 3 issues — not 1.
- **Did you check for hidden issues?** Investigation sometimes reveals problems the user didn't ask about (e.g., silent failures with null error messages). Include these as separate issues.
- **Did you check the "working" cases?** Sometimes the "working" records have a subtle problem too (e.g., all "approved" invoices have the same default VAT rate, suggesting the classification isn't actually running).

### 4. Format Issue List

For each issue:

```
### Issue {n}: {descriptive title}

**Root cause:** {why this is happening — one clear sentence}
**Category:** {bug | data-cleanup | ux-gap | missing-feature | config-issue | external-dependency}
**Severity:** {critical | moderate | low}
**Scope:** {trivial | small | medium | large}
**Affected records:** {count and description}
**Evidence:** {key finding(s) from step 2 that support this diagnosis}
**Resolution path:** {in-session | quick-dev | design-handoff | create-story}
```

---

## PRESENT DIAGNOSIS

```
**Diagnosis complete:** {total_issues} issue(s) found behind "{original symptom}"

{For each issue:}
{n}. **{title}** — {category}, {severity} severity, {scope} scope
   {one-line root cause}
   → {resolution path}
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/triage/steps/step-04-resolve.md`.

---

## SUCCESS METRICS

- Every finding from step 2 is accounted for in at least one issue
- Each issue has a genuine root cause explanation — not just restating the error message
- Compound symptoms are separated into distinct issues
- Categories, severities, and scopes are assigned and internally consistent
- Resolution paths match the category and scope (trivial → in-session, bug+medium → quick-dev with spec)
- No issue has "unclear" root cause without explaining what further investigation would be needed

## FAILURE MODES

- Treating all findings as one issue when they have different root causes
- Restating the symptom as the root cause ("root cause: extraction failed" — that's the symptom)
- Over-categorizing as `bug` when the code is correct and the data is bad (`data-cleanup`)
- Under-scoping: marking a multi-file change as `trivial` to avoid producing a handoff
- Over-scoping: marking a one-line fix as `medium` because the area is complex (scope the FIX, not the codebase)
- Not checking for hidden issues beyond what the user reported
