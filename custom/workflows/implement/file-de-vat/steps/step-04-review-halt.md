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

The submission summary (§2) and the approval question (§3) ARE the **conversational lane** here — the HALT is already human by design. The `▶ PHASE 5/7 — HALT — human review` banner is its **trace-tier** twin; emit it to the trace, then lead the lane with one plain line: *nothing will be submitted until you approve below*. The `persona_slot` **"I" recommendation** spot applies to §3 — a bound voice may own the recommendation in first person ("I'd file this" / "I'd hold — the reconciliation flag isn't resolved"), but the yes/no decision and the gate are the user's and the workflow's, never the voice's.

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
| Box check (§2a) | {PASS / FAIL — Kz … / COULD NOT CHECK} |

{box table from §2a: Kz, expected, Avask, difference, status}

**Missing data:** {list, or "none"}

**Notes:**
- {validation caveats, overrides taken, anything flagged in steps 1–3}
- Amendability of a submitted filing is UNCONFIRMED — treat this submission as irreversible.
```

### 2a. Box check — approval gate (MANDATORY, runs before §3)

Why: Avask's Q3 2026 filing (9 Oct 2026) put the intra-EU acquisitions in no acquisition box (Kz 89/93/61 at 0) and the credit notes in Kz 43 as -1,032, and nothing compared the boxes to our invoices. This check is that comparison.

1. Establish `{avask_boxes_cents}` (Kz → cents) and `{avask_boxes_source}`, in this order, first one that yields figures:
   - **Portal summary, pre-submit** — only if step-03 captured the portal's own box summary as `{portal_box_summary}` without any click that could submit. As of 20 Nov 2026 no tool reads one, and the owner's fact is that Avask shows its filing summary only during submission, so this is normally absent. Never press a submit or final-confirm control to reveal it.
   - **A transmission protocol already on record for `{period}`** (re-run after a submission, or a correction): read with `mcp__elster__elster_submission_protocol` and take its declared boxes (the ERiC parser's `declaredBoxes`, cents).
   - **Neither** → `{avask_boxes_cents} = null`. Say so in the summary; do not guess and do not read zero.
2. Call `mcp__de-vat-audit__audit_check_boxes` with `period`, `{acquisition_docs}` (step-02), `avask_boxes_cents`, `avask_source`. Put the returned box table (expected vs Avask, per box) in the §2 summary under the main table, verbatim, with its verdict line.
3. Gate on the verdict:
   - **PASS** — continue to §3.
   - **FAIL** (any box outside tolerance: ±1.00 EUR on Kz 89/93/43, ±0.10 EUR on Kz 61) — **approval is REFUSED, naming the box(es).** Do not ask the §3 question. State which Kz disagrees, expected vs Avask, and the next move (have Avask correct the figures, or correct `{acquisition_docs}` if the invoices were mis-scoped), then re-run §2a. No typed override lifts a FAIL.
   - **COULD NOT CHECK** (figures not read, or a document could not be placed) — **approval is REFUSED** unless the owner types an override in their own words after seeing the table. Pass those words (verbatim, never invented, never reused from earlier in the session) as `override_words` in a second call; the tool logs them to `.claude/filing-session/box-check-overrides.jsonl`. Say plainly that the box check could not run and that step-05 will run it after submission.
4. Boxes the check does not derive (Kz 81, 86, 66, 83) are shown as not checked, never as matching.

### 2b. Advance the case (best-effort — see step-01 §6)

The portal form is filled and awaiting your decision — reflect that so the PA banner shows the case as ready-to-send if this session ends here. This records state only; it is NOT approval and does not gate §3:

```bash
bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} \
  --status ready_to_send \
  --last-action "portal filled — awaiting your review before submit" \
  --next-actions "review the summary|approve to submit"
```

### 3. Ask for fresh approval

**Only if §2a allowed it** (PASS, or COULD NOT CHECK with the owner's logged override). On a refusal, end the turn with the refusal from §2a instead of this question.

Ask exactly one question: **"Submit this {period} German VAT return to the AVASK portal via `{pending_submit_action}`? (yes to submit / no to stop — I'll hold the filled form either way)"**

Then STOP. End the turn. Wait.

### 4. Interpret the response

- **Clear affirmative** ("yes", "submit", "go") given after the summary → record `{approval_given} = true`, `{approver} = user_name`, `{approval_time}` = current datetime. Write the approval marker `${CLAUDE_PROJECT_DIR}/.claude/filing-session/approval-{period}.json` (anchor to `CLAUDE_PROJECT_DIR`, the MAIN checkout — the gate reads it there, not from a worktree's `.claude/`; see workflow.md "Where this session runs") (`{"period","approver","approved_at","action":"{pending_submit_action}"}`) — step-05's gate reads it and it must be minutes-fresh, so write it only now, at real approval. Emit `✔ PHASE 5/7 — HALT — human review complete: approved by {approver} at {approval_time}` and proceed to step-05. Where the settings track is installed, the harness will additionally prompt on the submission call itself (permission `ask`) — expected, not an error.
- **Anything else** — a question, a correction, a partial approval ("yes but exclude invoice X") → answer/apply it, re-render the summary with the change, and ask again. A modified return needs a fresh yes against the new summary.
- **No / stop** → emit `✔ PHASE 5/7 — review complete: submission declined; form held unsubmitted`, DELETE the pre-flight marker `{preflight_marker}` (the gate must re-arm — see workflow.md marker-lifecycle rule), and END the workflow cleanly with a one-line state summary (what exists in the portal, how to resume: re-run the workflow; pre-flight is cheap). Record the decline so the PA banner is honest (best-effort — see step-01 §6): `bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} --last-action "submission declined; form held unsubmitted" --next-actions "re-run file-de-vat to resume"`.

## NEXT STEP

Only with `{approval_given} = true`: read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-05-submit-and-receipt.md`

## SUCCESS METRICS

- Summary displayed BEFORE the approval question, in the exact table+Notes shape, with the §2a box table
- Approval question asked only when the box check passed or the owner's typed override is logged
- Approval obtained fresh, in-conversation, post-summary — or the workflow ended cleanly
- Zero submissions from this step

## FAILURE MODES

- Treating autonomous_mode / an earlier "proceed" / the original "file my VAT" request as approval — all three are the same violation
- Re-using an approval after the return changed
- Asking the §3 question over a box-check FAIL, or after COULD NOT CHECK with no owner-typed override (a missing figure is not a zero, and "I couldn't read it" is not a pass)
- Ending the turn without the explicit question (the user cannot approve what wasn't asked)
