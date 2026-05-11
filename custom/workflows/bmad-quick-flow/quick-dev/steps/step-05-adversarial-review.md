---
name: 'step-05-adversarial-review'
description: 'Construct diff and invoke adversarial review + edge-case hunter tasks'

nextStepFile: './step-06-resolve-findings.md'
---

# Step 5: Adversarial Code Review + Edge-Case Hunting

**Goal:** Construct diff of all changes, invoke adversarial review AND edge-case hunter tasks, present unified findings.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start (CRITICAL for diff)
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)

---

### 1. Construct Diff

Build complete diff of all changes since workflow started.

### If `{baseline_commit}` is a Git commit hash:

**Tracked File Changes:**

```bash
git diff {baseline_commit}
```

**New Untracked Files:**
Only include untracked files that YOU created during this workflow (steps 2-4).
Do not include pre-existing untracked files.
For each new file created, include its full content as a "new file" addition.

### If `{baseline_commit}` is "NO_GIT":

Use best-effort diff construction:

- List all files you modified during steps 2-4
- For each file, show the changes you made (before/after if you recall, or just current state)
- Include any new files you created with their full content
- Note: This is less precise than Git diff but still enables meaningful review

### Capture as {diff_output}

Merge all changes into `{diff_output}`.

**Note:** Do NOT `git add` anything - this is read-only inspection.

---

### 2. Invoke Reviews

Run both reviews against `{diff_output}`. These are orthogonal — the adversarial review is attitude-driven (cynical skepticism), while the edge-case hunter is method-driven (exhaustive path enumeration). Both should run.

If possible, run them in parallel using separate subagents with read access to the project but no context except `{diff_output}`.

#### 2a. Adversarial Review

```xml
<invoke-task>Review {diff_output} using {project-root}/_bmad/core/tasks/review-adversarial-general.xml</invoke-task>
```

**Platform fallback:** If task invocation not available, load the task file and follow its instructions inline, passing `{diff_output}` as the content.

The task should: review `{diff_output}` and return a list of findings.

#### 2b. Edge-Case Hunter Review

```xml
<invoke-task>Review {diff_output} using {project-root}/_bmad/core/tasks/review-edge-case-hunter.xml</invoke-task>
```

**Platform fallback:** If task invocation not available, load the task file and follow its instructions inline, passing `{diff_output}` as the content.

The task should: walk every branching path and boundary condition in the diff, returning a JSON array of unhandled edge cases (location, trigger_condition, guard_snippet, potential_consequence).

---

### 3. Process Findings

Merge findings from BOTH reviews into a single unified findings list.

#### 3a. Normalize edge-case findings

The edge-case hunter returns a JSON array. Convert each entry into a finding with:
- **Severity:** Infer from `potential_consequence` — data loss/security → Critical, incorrect behavior → High, degraded UX → Medium, cosmetic → Low
- **Validity:** Default to "real" (the hunter only reports unhandled paths)
- **Source:** "edge-case"
- **Description:** Combine `trigger_condition` + `potential_consequence` + `guard_snippet`

#### 3b. Tag adversarial findings

For each adversarial review finding, add:
- **Source:** "adversarial"

#### 3c. Merge and present

Combine all findings into one list.
**If zero findings from BOTH reviews:** HALT - this is suspicious. Re-analyze or request user guidance.
Evaluate severity (Critical, High, Medium, Low) and validity (real, noise, undecided).
DO NOT exclude findings based on severity or validity unless explicitly asked to do so.
Order findings by severity, then by source (edge-case findings first within same severity, as they represent concrete missing paths).
Number the ordered findings (F1, F2, F3, etc.).
If TodoWrite or similar tool is available, turn each finding into a TODO, include ID, severity, validity, source, and description in the TODO; otherwise present findings as a table with columns: ID, Source, Severity, Validity, Description

---

## NEXT STEP

With findings in hand, read fully and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-06-resolve-findings.md` for user to choose resolution approach.

---

## SUCCESS METRICS

- Diff constructed from baseline_commit
- New files included in diff
- Both review tasks invoked with diff as input
- Findings received from both reviews
- Findings merged, normalized, and presented as unified table/TODOs

## FAILURE MODES

- Missing baseline_commit (can't construct accurate diff)
- Not including new untracked files in diff
- Invoking tasks without providing diff input
- Running only one review and skipping the other
- Accepting zero findings from both reviews without questioning
- Presenting fewer findings than the review tasks returned without explicit instruction to do so
- Not attributing findings to their source (adversarial vs edge-case)
