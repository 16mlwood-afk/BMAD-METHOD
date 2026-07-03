---
name: 'step-03-portal-fill'
description: 'Fill the AVASK portal — navigate, enter form data, upload artifacts — everything short of submission'
---

# Step 3: Portal Fill

**Progress: Step 3 of 5** — Next: HALT — Human Review (interactive)

## RULES

- **NEVER call `mcp__avask-filing__avask_submit` in this step.** This step ends with a filled, unsubmitted return. Submission belongs to step-05 and only after the step-04 HALT.
- Every portal action is narrated as a single status line (`→ uploaded invoice pack (3 PDFs)`) — visible progress, no wall of tool noise.
- A portal error is a BLOCKED box (format in workflow.md), not a silent retry loop. Retry once on transient failures; twice-failed → BLOCKED.

## SEQUENCE OF INSTRUCTIONS

### 1. Announce

Emit `▶ PHASE 4/7 — Portal fill: entering {period} return into the AVASK portal (no submission this phase)`.

### 2. Navigate and fill

Using `{return_data}`:

1. `mcp__avask-filing__avask_navigate` — reach the `{period}` filing form. Wrong page / login failure → one retry, then BLOCKED.
2. `mcp__avask-filing__avask_fill_form` — enter the return figures exactly as validated in step-02. No rounding, no adjustment, no "fixing" at the portal — a discrepancy discovered here goes back to a BLOCKED box, not an inline edit.
3. `mcp__avask-filing__avask_upload_pdf` — upload each required artifact; one status line per upload.
4. `mcp__avask-filing__avask_file_invoices` — attach/register the invoice set if the portal flow requires it pre-submission. If this action is itself the submission trigger in the portal's flow, do NOT call it: set `{pending_submit_action} = avask_file_invoices` and leave it for step-05 after the step-04 HALT. When unsure which side of the boundary an action is on, it is on the submit side. Otherwise `{pending_submit_action} = avask_submit`.

### 3. Build the fill manifest

Store `{fill_manifest}`: what was entered (field → value), what was uploaded (file → portal ref), and any deltas between `{return_data}` and what the portal accepted (expected: none; any delta is prominently flagged).

### 4. Close the phase

Emit `✔ PHASE 4/7 — Portal fill complete: form filled, {n} uploads, 0 unexplained deltas — nothing submitted yet`.

## NEXT STEP

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-04-review-halt.md`

## SUCCESS METRICS

- Portal reflects `{return_data}` exactly; `{fill_manifest}` captured
- Zero submission-side actions taken
- Every portal interaction visible as a status line; every failure surfaced as BLOCKED

## FAILURE MODES

- Calling avask_submit "while I'm here" — the single worst action this workflow can take
- Adjusting a figure at the portal to make the form validate
- Retrying a failing portal action in a silent loop instead of blocking
