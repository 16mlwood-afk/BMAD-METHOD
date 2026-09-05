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

Lane line: *submitting the approved {period} return now.* The `▶ PHASE 6/7 — Submit … via {pending_submit_action}` banner is its **trace-tier** twin. If the submission tool is **denied by the PreToolUse gate**, do NOT surface the raw `permissionDecisionReason` — render it as a **decision-line BLOCKED box** in owner terms (workflow.md → OUTPUT, decision-line contract + worked example), raw reason to trace. The deny stands exactly as the gate made it; the voice never restates a path around it.

Call the approved submission action — `mcp__avask-filing__avask_submit`, or `mcp__avask-filing__avask_file_invoices` where step-03 determined it is the portal's trigger (`{pending_submit_action}`). The anti-retry and ambiguity rules below apply identically to either. Then capture the portal's confirmation state (reference number, timestamp, status page content) as `{confirmation_ref}`.

**Portal-truth verification — MANDATORY before ANY `filed`/`sent` write.** A captured `{confirmation_ref}` is the submit tool's *own* return, NOT proof the portal received the filing. The tool can return OK and mark the DB `FILED` while the portal row never left `Provide Data` (a `waitForLoadState`/networkidle flake — 2026-Q2 hit exactly this: 54 invoices marked FILED, receipt said "63/63 filed", portal row still `Provide Data`, discovered only because the owner had eyes on the portal). So before declaring anything filed, RE-READ portal-truth with a read-only reconcile (`mcp__avask-filing__avask_reconcile_filing`, or `avask_reconcile_portal` — both ungated), independent of the submit tool's return, and branch on THAT — never on `{confirmation_ref}` alone:

- **CONFIRMED** — the reconcile shows the `{period}` row left `Provide Data` (or per-document portal confirmations now exist). Only now: emit `✔ PHASE 6/7 — Submit complete: confirmation {confirmation_ref}`. Then mark the case FILED — the `sent` write, done only on portal-confirmed truth (a PostToolUse reminder, `scripts/hooks/avask-submit-sent-reminder.sh`, re-prompts this write right after the submit tool runs so it is never skipped; it never auto-marks, because an ambiguous or unconfirmed submit must never show as sent):

  ```bash
  bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} \
    --status sent --submitted-now --confirmation-ref "{confirmation_ref}" \
    --last-action "filed {period} — confirmation {confirmation_ref}"
  ```
- **CONTRADICTED** — the reconcile shows the `{period}` row still reads `Provide Data`: the submit did NOT land, whatever it returned. BLOCKED box in owner terms ("submit returned OK but the DE {period} row still reads Provide Data — the return is NOT filed"). Do NOT mark `sent`, do NOT mint a `filed` receipt, do NOT auto-re-submit (an ambiguous submit is NEVER retried — double-filing is the failure mode). The next move is the owner's: re-file deliberately, or eyeball the portal row.
- **UNCONFIRMED** — the reconcile is unavailable or ambiguous, so portal-truth can't be seen. Do NOT mark the case `sent`. The receipt is minted `status: unconfirmed`, never `filed` (phase 7). Surface a decision-line: portal-truth of {period} is unconfirmed; the canonical "did it file?" is the human-set marker (`scripts/set-filing-status.sh`) — ask the owner to confirm at the portal rather than inferring filed from the tool's OK.

Never mark `sent` or write a `filed` receipt on the submit tool's return alone — only on a portal-truth reconcile that returns CONFIRMED.

> **Owner filed manually (outside this workflow)?** When the owner reports a period already filed on the AVASK portal ("i officially filed q2") — so phases 1–6 here never ran — do NOT hand-assemble the close-out. Closing out is TWO writes with TWO different status words for the same event (portal-truth marker `filed` + PA case `sent`; `vat-filing-case-update.sh --status filed` silently 400s because the case enum has no `filed`). Run the single wrapper that owns the mapping and fails loudly instead: `bash {project-root}/scripts/close-out-filing.sh --period {period} [--by "…"] [--note "…"] [--confirmation-ref "…"]`. It sets the human-owned portal-truth marker to `filed` (locks the submit gate — safe direction, never opens it) then advances the case to `sent`. The marker stays owner-driven — this records a portal reading the owner has already done; it does not decide filing status.

### 2. Phase 7 — Confirmation receipt (canonical ledger artifact)

Emit `▶ PHASE 7/7 — Confirmation receipt`.

**Carry the phase-6 portal-truth verdict into the receipt — never upgrade it here.** Only a **CONFIRMED** phase 6 mints a `filed` receipt. On **UNCONFIRMED**, the receipt is `status: unconfirmed` (portal-truth not seen; confirmation fields render `—`/Awaiting, which is the honest state) and the case is NOT `sent`. **CONTRADICTED** does not reach a normal phase 7 at all — it stayed in the phase-6 BLOCKED box; there is no filed return to receipt. Phase 7 records portal-truth; it must not manufacture a `filed` status the reconcile never returned.

1. **Produce the CANONICAL filing artifact from portal-truth — not from session assumptions.** Run `mcp__avask-filing__avask_generate_ledger` (period as the portal quarter, e.g. `"Q2 2026"`; country `DE`). It reads what the AVASK portal ACTUALLY holds (Active + Rejected sets), renders a **versioned HTML + PDF ledger to R2**, and records it with provenance (input VAT, reconcile timestamp/hash, generator version). This reconciled artifact is the receipt of record — it **supersedes** the old free-text template receipt, which drifted from portal-truth on 2026-Q2 (it claimed €1,053.03; the portal held €769.83, the rest being rejected duplicates).
   - **Forward the confirmation facts you actually captured** so the record's confirmation summary shows them instead of `—`: pass `confirmationRef: "{confirmation_ref}"` (the phase-6 reference — **omit it** if the submit was ambiguous and no reference was captured), `confirmedVia: "file-de-vat"`, and `confirmedBy: "AVASK portal"`. Pass `filedAt` only if you captured the portal's submit timestamp as an ISO string; otherwise omit it (the record falls back to the portal-truth read time). Do **not** pass `authorityRef` — the ELSTER/ERiC receipt is a later, separate event; leave it absent (the record shows it as Awaiting) until the authority has actually receipted. Never invent a reference you don't hold; an omitted field renders as `—` + an Awaiting note, which is the correct, honest state.
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
