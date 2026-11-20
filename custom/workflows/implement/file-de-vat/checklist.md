# file-de-vat — Session Validation Checklist

## Pre-flight (step-01)

- [ ] Session header shown with period + full phase plan before any other work
- [ ] Defaulted period explicitly CONFIRMED by the user before any check ran (user-named periods exempt)
- [ ] All 6 checks reported PASS / FAIL / n/a in a table (window, period, invoices, reconciliation, credentials, prior-filing-reconcile)
- [ ] Credentials checked presence-only — `~/.secrets` never read into context, no value echoed
- [ ] Every FAIL cured, explicitly user-overridden, or the session stopped in a BLOCKED box
- [ ] Pre-flight marker written only on a genuine proceed decision

## Data & validation (step-02)

- [ ] Every figure in the return traces to a tool result or read-only query — zero invented values
- [ ] Missing values rendered as `n/a` and listed under Missing data
- [ ] Validation verdict stated explicitly; defects that change the filing blocked, not carried

## Portal fill (step-03)

- [ ] Zero submission-side actions taken in this phase
- [ ] Every portal action visible as a status line; failures rendered as BLOCKED boxes
- [ ] Fill manifest captures field→value and upload→ref with no unexplained deltas

## Review halt (step-04)

- [ ] Submission summary (table incl. submission action + Missing data + Notes) displayed BEFORE the approval question
- [ ] Box table (expected vs Avask per Kz) in the summary; approval question asked only after box check PASS, or COULD NOT CHECK with the owner's own typed override logged; a FAIL named its Kz and refused
- [ ] Approval obtained fresh, in-conversation, after the summary — autonomous_mode not treated as approval
- [ ] Approval marker written only at real approval, with approver + timestamp + action
- [ ] Phase-5 completion banner emitted on BOTH branches (approved-by on yes; declined + pre-flight marker deleted on no)
- [ ] Any change to the return triggered a re-render + fresh approval

## Submit & receipt (step-05)

- [ ] The approved submission action ({pending_submit_action}) called exactly once, after approval; ambiguous outcomes blocked, never retried
- [ ] Confirmation reference captured (or an honest BLOCKED state — no guessed success)
- [ ] Post-submit box check run against the transmission protocol (PASS, FAIL named in a BLOCKED box, or "owed" under Open items — never silently skipped)
- [ ] Receipt artifact written to {implementation_artifacts}/filing-receipts/ with no blank sections
- [ ] BOTH markers (pre-flight + approval) deleted at session close

## Contract-wide

- [ ] All 7 phase banners emitted (entry + completion or a BLOCKED terminal)
- [ ] Every blocker rendered in the BLOCKED box format — none buried in prose
- [ ] Amendability-unconfirmed warning present in the step-04 review and receipt Notes
