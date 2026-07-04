---
name: 'step-04-review-halt'
description: 'Mandatory HALT: present the exact submission context and obtain fresh user approval — overrides autonomous_mode'
---

# Step 4: HALT — Human Review

**Progress: Step 4 of 5** — Next: Submit & Receipt (only after fresh approval)

## RULES

- **This HALT overrides `autonomous_mode`. No exceptions.** Do not simulate approval, do not treat an earlier "go ahead" as approval, do not proceed on silence. The precedents are quick-dev's grounding gate and design-implement's fixture-to-prod checkpoint: intent autonomy is never granted for an irreversible partner-facing action.
- Approval is valid ONLY if it is given by the user, in this conversation, AFTER the summary below is displayed. Anything else — including a prior affirmative earlier in the session — is not approval.
- Figures in the table; interpretation in Notes. Never blend them (finance-presentation standard).

## SEQUENCE OF INSTRUCTIONS

### 1. Announce

Emit `▶ PHASE 5/7 — HALT — human review: nothing will be submitted until you approve below`.

### 2. Present the submission summary

Render from `{return_data}` + `{fill_manifest}`:

```markdown
## Submission review — German VAT {period}

| Item | Value |
|------|-------|
| Period | {period} |
| Invoices included | {count} |
| {per-rate totals, one row each} | {amount} |
| Uploads | {n} files ({names}) |
| Portal form state | filled, unsubmitted |
| Submission action | {pending_submit_action} |

**Missing data:** {list, or "none"}

**Notes:**
- {validation caveats, overrides taken, anything flagged in steps 1–3}
- Amendability of a submitted filing is UNCONFIRMED — treat this submission as irreversible.
```

### 2b. Advance the case (best-effort — see step-01 §6)

The portal form is filled and awaiting your decision — reflect that so the PA banner shows the case as ready-to-send if this session ends here. This records state only; it is NOT approval and does not gate §3:

```bash
bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} \
  --status ready_to_send \
  --last-action "portal filled — awaiting your review before submit" \
  --next-actions "review the summary|approve to submit"
```

### 3. Ask for fresh approval

Ask exactly one question: **"Submit this {period} German VAT return to the AVASK portal via `{pending_submit_action}`? (yes to submit / no to stop — I'll hold the filled form either way)"**

Then STOP. End the turn. Wait.

### 4. Interpret the response

- **Clear affirmative** ("yes", "submit", "go") given after the summary → record `{approval_given} = true`, `{approver} = user_name`, `{approval_time}` = current datetime. Write the approval marker `{project-root}/.claude/filing-session/approval-{period}.json` (`{"period","approver","approved_at","action":"{pending_submit_action}"}`) — step-05's gate reads it and it must be minutes-fresh, so write it only now, at real approval. Emit `✔ PHASE 5/7 — HALT — human review complete: approved by {approver} at {approval_time}` and proceed to step-05. Where the settings track is installed, the harness will additionally prompt on the submission call itself (permission `ask`) — expected, not an error.
- **Anything else** — a question, a correction, a partial approval ("yes but exclude invoice X") → answer/apply it, re-render the summary with the change, and ask again. A modified return needs a fresh yes against the new summary.
- **No / stop** → emit `✔ PHASE 5/7 — review complete: submission declined; form held unsubmitted`, DELETE the pre-flight marker `{preflight_marker}` (the gate must re-arm — see workflow.md marker-lifecycle rule), and END the workflow cleanly with a one-line state summary (what exists in the portal, how to resume: re-run the workflow; pre-flight is cheap). Record the decline so the PA banner is honest (best-effort — see step-01 §6): `bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} --last-action "submission declined; form held unsubmitted" --next-actions "re-run file-de-vat to resume"`.

## NEXT STEP

Only with `{approval_given} = true`: read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-05-submit-and-receipt.md`

## SUCCESS METRICS

- Summary displayed BEFORE the approval question, in the exact table+Notes shape
- Approval obtained fresh, in-conversation, post-summary — or the workflow ended cleanly
- Zero submissions from this step

## FAILURE MODES

- Treating autonomous_mode / an earlier "proceed" / the original "file my VAT" request as approval — all three are the same violation
- Re-using an approval after the return changed
- Ending the turn without the explicit question (the user cannot approve what wasn't asked)
