---
name: 'step-02-prepare-return'
description: 'Pull the period return data (phase 2) and validate it (phase 3) into a submission-ready dataset'
---

# Step 2: Prepare Return (Data Pull + Validation)

**Progress: Step 2 of 5** — Next: Portal Fill (autonomous)

## RULES

- **Never invent figures.** Every number in `{return_data}` traces to a tool result or admin-API query. A value you could not obtain is `n/a` and goes on the Missing data list — it never becomes a guess.
- **No `mcp__avask-filing__*` call in this step.** This step reads accounting data only.
- This step carries phases 2 AND 3 — announce both banners separately.

## SEQUENCE OF INSTRUCTIONS

### 1. Phase 2 — Data pull

Emit `▶ PHASE 2/7 — Data pull`.

- Preferred path: `mcp__de-vat-audit__audit_pull_invoices` for `{period}` (the sanctioned German VAT primitive), plus `mcp__de-vat-audit__audit_build_pack` if a filing pack is expected by the portal.
- Fallback (de-vat-audit not connected): read-only admin API (`sql-query`) for the period's German-VAT-relevant invoices. Read-only means read-only: SELECT queries exclusively.
- Store `{return_data}`: invoice list (count, ids), per-rate totals, any PDFs/artifacts the portal upload needs.

Emit `✔ PHASE 2/7 — Data pull complete: {invoice count} invoices, totals gathered` (or a BLOCKED box if the source is unreachable).

### 2. Phase 3 — Validation

Emit `▶ PHASE 3/7 — Validation`.

Run the checks and print a compact validation report:

- `mcp__de-vat-audit__audit_validate_invoices` on the pulled set (preferred), plus:
- Internal consistency: totals sum, no duplicated invoice ids, no negative counts.
- Completeness: every field the portal form will need is present; anything absent → `n/a` + Missing data list.
- Known project traps: Mifarma GBP/English invoices mis-parse amounts (never auto-accept those figures); AVASK B2B requires buyer VAT number — missing buyer VAT → NOT_RECLAIMABLE, flag it.

Store `{validation_report}`. Verdict rules:

- **Clean or clean-with-disclosed-n/a:** emit `✔ PHASE 3/7 — Validation complete` with the one-line verdict.
- **Defects that change what gets filed** (wrong totals, unresolvable invoices): BLOCKED box. Filing on known-bad data is never the autonomous choice.

## NEXT STEP

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-03-portal-fill.md`

## SUCCESS METRICS

- `{return_data}` fully sourced from tools/queries — zero invented values
- Validation report shown with an explicit verdict
- Missing data list present whenever anything is `n/a`

## FAILURE MODES

- Silently "correcting" a figure that looks wrong instead of flagging it
- Proceeding to portal fill with a validation defect because autonomous_mode felt like permission
