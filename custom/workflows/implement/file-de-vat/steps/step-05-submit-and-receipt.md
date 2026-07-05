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

- **Success:** emit `✔ PHASE 6/7 — Submit complete: confirmation {confirmation_ref}`. Then mark the case FILED — this is the `sent` write, done only now that a real confirmation is captured (a PostToolUse reminder, `scripts/hooks/avask-submit-sent-reminder.sh`, re-prompts this write right after the submit tool runs so it is never skipped; it never auto-marks, because an ambiguous or failed submit must never show as sent):

  ```bash
  bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} \
    --status sent --submitted-now --confirmation-ref "{confirmation_ref}" \
    --last-action "filed {period} — confirmation {confirmation_ref}"
  ```
- **Failure or ambiguous outcome:** BLOCKED box. State plainly whether the submission may have gone through ("portal errored AFTER the submit action — the return may be filed; do not re-submit until we verify"). An ambiguous submit is NEVER retried automatically — double-filing is the failure mode.

> **Owner filed manually (outside this workflow)?** When the owner reports a period already filed on the AVASK portal ("i officially filed q2") — so phases 1–6 here never ran — do NOT hand-assemble the close-out. Closing out is TWO writes with TWO different status words for the same event (portal-truth marker `filed` + PA case `sent`; `vat-filing-case-update.sh --status filed` silently 400s because the case enum has no `filed`). Run the single wrapper that owns the mapping and fails loudly instead: `bash {project-root}/scripts/close-out-filing.sh --period {period} [--by "…"] [--note "…"] [--confirmation-ref "…"]`. It sets the human-owned portal-truth marker to `filed` (locks the submit gate — safe direction, never opens it) then advances the case to `sent`. The marker stays owner-driven — this records a portal reading the owner has already done; it does not decide filing status.

### 2. Phase 7 — Confirmation receipt (canonical ledger artifact)

Emit `▶ PHASE 7/7 — Confirmation receipt`.

1. **Produce the CANONICAL filing artifact from portal-truth — not from session assumptions.** Run `mcp__avask-filing__avask_generate_ledger` (period as the portal quarter, e.g. `"Q2 2026"`; country `DE`). It reads what the AVASK portal ACTUALLY holds (Active + Rejected sets), renders a **versioned HTML + PDF ledger to R2**, and records it with provenance (input VAT, reconcile timestamp/hash, generator version). This reconciled artifact is the receipt of record — it **supersedes** the old free-text template receipt, which drifted from portal-truth on 2026-Q2 (it claimed €1,053.03; the portal held €769.83, the rest being rejected duplicates).
   - **Fallback:** if the tool is unavailable (MCP tool not yet deployed, or migration `0173` not applied → the route 500s), fall back to populating the legacy template receipt (§2a) and list the missing canonical artifact under Missing data. **Never skip the artifact silently.**
2. **Stub the legacy receipt.** Write `{implementation_artifacts}/filing-receipts/de-vat-{period}-receipt.md` as a THIN stub that points at the canonical artifact (period, country, version, input-VAT total, view URL) — **not** a re-derived figure table. One period must not have two competing "truths."
   - **§2a (fallback only):** if step 1 fell back, populate `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/template.md` into that path instead — every `{{variable}}` from real session data, unobtainable values `n/a` under Missing data.
3. Delete BOTH markers — `{preflight_marker}` and `{project-root}/.claude/filing-session/approval-{period}.json` — the session is over; the gate must re-arm for any future portal access.
4. Emit `✔ PHASE 7/7 — Confirmation receipt complete: {canonical artifact URL, or fallback receipt path}`.

### 3. Close the session

Before the final summary, validate the session against `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/checklist.md` — report any unchecked item plainly; never silently pass it.

Final summary — one short block, no diary:

```text
Filed: German VAT {period} — confirmation {confirmation_ref}
Ledger: {canonical artifact URL, or fallback receipt path}
Open items: {Missing data / follow-ups, or "none"}
```

Recommend (one line) committing the fallback receipt stub to main per the delivery contract (the canonical HTML/PDF artifact already lives in R2 — nothing to commit for it). Do not commit production-data artifacts silently.

## SUCCESS METRICS

- Submission executed exactly once, only after step-04 approval + the harness prompt
- `{confirmation_ref}` captured, or an honest BLOCKED box on ambiguity — never a guessed outcome
- Receipt artifact written with zero invented values; pre-flight marker cleaned up

## FAILURE MODES

- Auto-retrying an ambiguous submit (risk: double filing)
- Declaring success without a captured confirmation reference
- Skipping the receipt because "the filing is the point" — the receipt IS the audit trail
