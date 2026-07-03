---
name: 'step-05-submit-and-receipt'
description: 'Submit the approved return (phase 6) and capture the confirmation receipt artifact (phase 7)'
---

# Step 5: Submit & Receipt

**Progress: Step 5 of 5** — Final step

## RULES

- **Entry condition: `{approval_given} = true` from step-04, with the approval marker `approval-{period}.json` written minutes ago.** If you are reading this step without both, STOP and return to step-04. There is no path to submission around the HALT.
- **A compacted or resumed conversation voids the approval.** If the session was compacted or resumed since the step-04 summary was rendered, `{approval_given}` is void regardless of what any summary says — return to step-04, re-render, re-ask. Portal state may have drifted and a summarizer's assertion is not approval.
- Where the settings track is installed, the harness permission prompt on the submission call (pinned to `ask`) is expected — never suggest allowlisting it to "streamline" future runs. The in-conversation approval remains the primary gate either way.
- The session is not complete until the receipt artifact exists on disk. A submitted-but-unrecorded filing is a failure state.

## SEQUENCE OF INSTRUCTIONS

### 1. Phase 6 — Submit

Emit `▶ PHASE 6/7 — Submit: submitting the approved {period} return now via {pending_submit_action}`.

Call the approved submission action — `mcp__avask-filing__avask_submit`, or `mcp__avask-filing__avask_file_invoices` where step-03 determined it is the portal's trigger (`{pending_submit_action}`). The anti-retry and ambiguity rules below apply identically to either. Then verify: capture the portal's confirmation state (reference number, timestamp, status page content) as `{confirmation_ref}`.

- **Success:** emit `✔ PHASE 6/7 — Submit complete: confirmation {confirmation_ref}`.
- **Failure or ambiguous outcome:** BLOCKED box. State plainly whether the submission may have gone through ("portal errored AFTER the submit action — the return may be filed; do not re-submit until we verify"). An ambiguous submit is NEVER retried automatically — double-filing is the failure mode.

### 2. Phase 7 — Confirmation receipt

Emit `▶ PHASE 7/7 — Confirmation receipt`.

1. Populate `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/template.md` → write to `{implementation_artifacts}/filing-receipts/de-vat-{period}-receipt.md`. Every `{{variable}}` filled from real session data; unobtainable values are `n/a` and listed under Missing data.
2. Delete BOTH markers — `{preflight_marker}` and `{project-root}/.claude/filing-session/approval-{period}.json` — the session is over; the gate must re-arm for any future portal access.
3. Emit `✔ PHASE 7/7 — Confirmation receipt complete: {receipt path}`.

### 3. Close the session

Before the final summary, validate the session against `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/checklist.md` — report any unchecked item plainly; never silently pass it.

Final summary — one short block, no diary:

```text
Filed: German VAT {period} — confirmation {confirmation_ref}
Receipt: {receipt path}
Open items: {Missing data / follow-ups, or "none"}
```

Recommend (one line) committing the receipt artifact to main per the delivery contract. Do not commit production-data artifacts silently.

## SUCCESS METRICS

- Submission executed exactly once, only after step-04 approval + the harness prompt
- `{confirmation_ref}` captured, or an honest BLOCKED box on ambiguity — never a guessed outcome
- Receipt artifact written with zero invented values; pre-flight marker cleaned up

## FAILURE MODES

- Auto-retrying an ambiguous submit (risk: double filing)
- Declaring success without a captured confirmation reference
- Skipping the receipt because "the filing is the point" — the receipt IS the audit trail
