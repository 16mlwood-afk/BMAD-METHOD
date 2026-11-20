---
name: 'step-04-resolve'
description: 'For each diagnosed issue: fix trivially in-session or produce the native handoff artifact for the downstream workflow. Write triage report.'
---

# Step 4: Resolve

**Goal:** Act on every diagnosed issue. Trivial issues are fixed right now. Non-trivial issues get a handoff artifact written in the format the downstream workflow expects. Nothing is left unaddressed.

**Principle:** The triage workflow is a front door, not a dead end. Every issue either gets resolved or gets a handoff artifact that another workflow can pick up without re-investigating. The user should never have to explain the problem twice.

---

## AVAILABLE STATE

From previous steps:

- `{observation}` — the original symptom
- `{observation_type}` — classification
- `{page_context}` — page, route, feature
- `{findings}` — raw data points
- `{issues}` — diagnosed issues with root cause, category, severity, scope

## STATE VARIABLES (set in this step)

- `{resolutions}` — what was done for each issue
- `{triage_report_path}` — path to the written triage report artifact

---

## EXECUTION SEQUENCE

### 1. Sort Issues by Resolution Path

Order the issues for processing:

1. **Trivial fixes first** — resolve them now, clear the deck
2. **Quick-dev targets** — write tech specs
3. **Design targets** — write design handoff briefs
4. **Story targets** — write story briefs
5. **External/unresolvable** — document and note

### 2. Resolve Trivial Issues In-Session

For each issue with scope `trivial`:

**Data cleanup:**
- Execute the fix via admin API or direct SQL (read-only queries for verification first, then the mutating action)
- Verify the fix took effect — re-query and confirm the count/state changed
- Record what was done: the query executed, the before/after state

**Config fixes:**
- Identify the config file or env var
- State the change needed
- If it requires a code edit: enter a worktree first, make the change, commit, PR, merge
- If it's an env var or external config: tell the user what to change

**One-off admin actions:**
- Execute via admin API
- Verify the result
- Record the action

**For each resolved issue, record:**

```
Resolution: resolved-inline
Action: {what was done}
Verification: {how you confirmed it worked}
```

### 3. Produce Quick Tech Specs (for `quick-dev` targets)

For each issue with resolution path `quick-dev`, write a tech spec that quick-dev Mode A can consume directly.

**Write to:** `{implementation_artifacts}/tech-spec-triage-{slug}-{date}.md`

**Format — follows the project's existing tech-spec template:**

```markdown
---
title: '{issue title}'
slug: 'triage-{issue-slug}'
created: '{date}'
source: 'triage workflow'
status: ready
stepsCompleted: [1, 2, 3, 4]
---

# {issue title}

## Context

**Source:** Triage workflow diagnosis of "{original observation}"
**Root cause:** {root cause from diagnosis}
**Evidence:** {key data points from investigation}

## Current Behavior

{What currently happens — with specific code references and data}

## Expected Behavior

{What should happen after the fix}

## Tasks

{Numbered, ordered list of specific changes:}

1. **{file_path}** — {what to change and why}
2. **{file_path}** — {what to change and why}

## Acceptance Criteria

- Given {precondition}, when {action}, then {expected result}
- {Additional criteria}

## Investigation Already Done

The triage workflow has already completed the investigation that quick-dev step-02 (context gathering) would perform:

- **Production data queried:** {summary of queries run and results}
- **Code paths identified:** {files read and what was found}
- **Root cause confirmed:** {how the root cause was verified}

Quick-dev can skip context gathering and proceed directly to execution.
```

**Record:**

```
Resolution: routed-to-quick-dev
Artifact: {tech spec path}
Next: /bmad:bmm:workflows:quick-dev {tech spec path}
```

### 4. Produce Design Handoff Briefs (for `design-handoff` targets)

For each issue with resolution path `design-handoff`, write an artifact the design-handoff workflow can consume.

**Write to:** `{implementation_artifacts}/triage-design-brief-{slug}-{date}.md`

**Format — provides the raw materials for design-handoff's step 1:**

```markdown
---
title: 'Design Opportunity: {issue title}'
created: '{date}'
source: 'triage workflow'
type: triage-design-brief
---

# Design Opportunity: {issue title}

## User Problem

{What the user observed and why it's a problem — from the user's perspective, not the code's}

## Available Data

{What data exists in the DB and API that could address this problem — field names, types, example values}

## Current State

{What the page currently shows — factual, not prescriptive. Do NOT describe how the redesign should look.}

## Constraints

{Technical constraints the designer must know — data update frequency, performance limits, mobile considerations}

## Next Step

Run `/bmad:bmm:workflows:design-handoff` with this file to produce a Claude Design brief.
```

**Record:**

```
Resolution: routed-to-design
Artifact: {design brief path}
Next: /bmad:bmm:workflows:design-handoff {design brief path}
```

### 5. Produce Story Briefs (for `create-story` targets)

For each issue with resolution path `create-story`, write a brief that provides context for story creation.

**Write to:** `{implementation_artifacts}/triage-story-brief-{slug}-{date}.md`

**Format:**

```markdown
---
title: 'Feature: {issue title}'
created: '{date}'
source: 'triage workflow'
type: triage-story-brief
---

# Feature: {issue title}

## Problem

{What's missing and why it matters — from the user's perspective}

## Investigation Context

{What the triage workflow found — production data, code analysis, scope assessment}

## Scope Assessment

**Estimated size:** {medium | large}
**Why this isn't a quick-dev:** {what makes it too big for a single-session fix}

## Next Step

Run `/bmad:bmm:workflows:create-story` to develop this into a full story with acceptance criteria.
```

**Record:**

```
Resolution: routed-to-story
Artifact: {story brief path}
Next: /bmad:bmm:workflows:create-story
```

### 6. Document External/Unresolvable Issues

For issues with category `external-dependency` or where the root cause is outside the codebase:

**Record:**

```
Resolution: documented
Reason: {why this can't be fixed — external API limitation, third-party bug, etc.}
Workaround: {if any — e.g., "manually re-process via admin API when this occurs"}
Monitor: {what to watch for — e.g., "check error counts weekly for recurrence"}
```

### 7. Write Triage Report

Write the triage report to `{implementation_artifacts}/triage-{slug}-{date}.md` using the template at `{project-root}/_bmad/bmm/workflows/verify/triage/template.md`.

Store the path as `{triage_report_path}`.

### 8. Present Final Summary

```
**Triage complete:** {original observation}

**{total_issues} issue(s) diagnosed:**

{For each issue:}
{n}. **{title}** [{category}] — {resolution summary}
   {If resolved inline:} ✓ Fixed: {what was done}
   {If routed:} → {artifact path}
     Run: {slash command to trigger next workflow}

{If any issues were resolved inline:}
**Resolved in-session:** {count} issue(s) fixed directly

{If any handoff artifacts were produced:}
**Handoff artifacts:** {count} produced — ready for downstream workflows

**Triage report:** {triage_report_path}
```

---

## AUTONOMOUS MODE BEHAVIOR

In autonomous mode:

- Fix all trivial issues without asking — execute and verify
- Write all handoff artifacts without asking — use expert judgment for content
- If a trivial fix requires a code edit: enter worktree, edit, commit, PR, merge — full delivery pipeline
- Present the final summary and end

---

## CHAINING TO DOWNSTREAM WORKFLOWS

The triage workflow does NOT automatically trigger downstream workflows. It produces the artifacts and presents the next-step commands. The user (or dispatch-followups) decides when to execute them.

**Why not auto-chain:** Triage often produces multiple artifacts for different workflows. Auto-chaining into quick-dev for issue #1 while issues #2 and #3 need design-handoff would lose context. The user should see the full picture before deciding execution order.

**Exception:** If there is exactly ONE non-trivial issue and `autonomous_mode` is true, the workflow MAY chain directly into the downstream workflow by loading its workflow.md. This keeps single-issue triage seamless. Present the triage report first, then chain.

---

## SUCCESS METRICS

- Every diagnosed issue has a resolution (fixed, routed, or documented)
- Trivial fixes were executed and verified — not just described
- Handoff artifacts are in the native format of the downstream workflow — quick-dev can consume tech specs directly
- Tech specs include the investigation context so quick-dev can skip its context-gathering step
- The user has clear next-step commands for every routed issue
- Triage report written to implementation artifacts

## FAILURE MODES

- Leaving an issue unresolved — every issue must have a resolution entry
- Writing a handoff artifact that the downstream workflow can't consume (wrong format, missing required fields)
- Fixing a non-trivial issue inline instead of producing a proper handoff (rushing a multi-file change without a spec)
- Producing a handoff for a trivial fix instead of just doing it (unnecessary overhead)
- Not verifying trivial fixes took effect (executing a query without checking the result)
- Auto-chaining into a downstream workflow when multiple issues exist (loses the big picture)
- Writing vague tech specs ("fix the extraction pipeline") instead of specific ones with file paths and code references
