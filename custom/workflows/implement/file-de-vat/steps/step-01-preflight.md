---
name: 'step-01-preflight'
description: 'Announce the session, run the PASS/FAIL pre-flight checklist, write the pre-flight marker'
---

# Step 1: Pre-flight

**Progress: Step 1 of 5** — Next: Prepare Return (autonomous)

## RULES

- **No `mcp__avask-filing__*` call in this step.** Pre-flight is read-only against local data and the admin API.
- Every check reports PASS or FAIL — never "probably fine". A FAIL you cannot cure renders as a BLOCKED box (format in workflow.md).
- Do not skip checks; do not reorder them silently.

## SEQUENCE OF INSTRUCTIONS

### 1. Announce the session

Emit the phase banner (`▶ PHASE 1/7 — Pre-flight`), then a short session header:

```text
German VAT filing session — period {period}
Plan: pre-flight → data pull → validation → portal fill → HALT for your review → submit → receipt
I will stop and ask before anything is submitted. Blockers will be flagged loudly, not buried.
```

**If `{period_source} = defaulted`, this header is a CONFIRM gate — it overrides `autonomous_mode`.** Append one question ("I've defaulted to {period} — confirm, or name the period you meant") and WAIT for the answer before running any checks. Phases 2–4 write to a live third-party portal; a defaulted period must be confirmed before the first check runs, not vetoed mid-stream. If `{period_source} = user-named`, proceed without pausing.

### 2. Run the checklist

Evaluate each check and print the table with PASS / FAIL / n/a and a one-line detail per row:

| # | Check | How to evaluate |
|---|-------|-----------------|
| 1 | Filing window open | AVASK portal opens the 4th–8th of the **filing month = the first month after `{period}` ends** (e.g. 2026-Q1 → April 2026; per project memory). Compare `{date}` to that window. Outside → FAIL with the next opening date. If the mapping cannot be confirmed from project memory/docs, report `n/a — mapping unconfirmed` and BLOCK asking the user — never guess a window. |
| 2 | Period chosen | `{period}` resolved; if defaulted, confirmed by the user in §1. |
| 3 | Invoices validated | Prefer `mcp__de-vat-audit__audit_validate_invoices` for `{period}` if the de-vat-audit MCP is connected; otherwise a read-only admin-API check (`system-status` / `sql-query`) that the period's invoices exist and carry no open validation flags. |
| 4 | Reconciliation clean | Prefer `mcp__de-vat-audit__audit_reconcile` for `{period}`; otherwise report `n/a — de-vat-audit not connected` and list it under Missing data (do NOT fabricate a reconciliation verdict). |
| 5 | Portal credentials present | The `mcp__avask-filing__*` tools are listed via ToolSearch, and each env var the avask-filing MCP server declares (its `env` block in the project's MCP config) passes a presence-only `test -n "$VAR"`. NEVER read, `cat`, or grep `~/.secrets` itself, and never echo a value — present/absent is the only permitted output. |
| 6 | No prior filing evidence | ALL of: no receipt at `{implementation_artifacts}/filing-receipts/de-vat-{period}-receipt.md`; no pre-existing `preflight-{period}.json` (evidence of an interrupted session). Any evidence → BLOCKED: a second submission requires the user to explicitly confirm the first one did not go through. |

### 3. Decide the gate

- **All PASS (or n/a with user-visible disclosure):** proceed to §4.
- **Check 1 FAIL (window closed):** BLOCKED box with the next window date. The user may explicitly override ("proceed outside the window") — if they do, note the override in the marker and proceed.
- **Any other FAIL:** BLOCKED box naming the exact cure (e.g. "3 invoices for 2026-Q1 have open validation flags — fix via the queries page or tell me to exclude them"). Stop and wait.

### 4. Write the pre-flight marker

Write `{project-root}/.claude/filing-session/preflight-{period}.json`:

```json
{
  "period": "{period}",
  "created": "{ISO datetime}",
  "checks": { "window": "PASS", "period": "PASS", "invoices": "PASS", "reconciliation": "PASS|n/a", "credentials": "PASS" },
  "overrides": []
}
```

This marker is the PROOF a PreToolUse gate on `mcp__avask-filing__*` reads. Write it ONLY when the gate decision in §3 was proceed — never write it to get past the hook.

### 5. Close the phase

Emit `✔ PHASE 1/7 — Pre-flight complete: {n} PASS, {n} n/a, 0 blocking` and store `{preflight_marker}`.

### 6. Register the case (best-effort — never blocks the filing)

Advance the durable filing case so the session-start PA banner leads with real state (workflow.md → case-record contract). Use the slug `de-vat-{period}` lowercased (e.g. `de-vat-2026-q2`):

```bash
bash {project-root}/scripts/vat-filing-case-update.sh --period de-vat-{period} \
  --status in_progress \
  --last-action "pre-flight passed" \
  --next-actions "prepare & validate return|fill AVASK portal|review & approve|submit"
```

The helper always exits 0 — a comms_dashboard outage degrades PA visibility, never the filing. Do not gate the phase on its result. Set `--filing-due {ISO}` here only if check 1 established a concrete due date; never invent one.

## NEXT STEP

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-02-prepare-return.md`

## SUCCESS METRICS

- Session header + full PASS/FAIL table shown before any other work
- Every FAIL either cured, explicitly overridden by the user, or the workflow is stopped in a BLOCKED box
- Marker file written with real check results

## FAILURE MODES

- Writing the marker despite a FAIL to "keep momentum" — that is forging the proof the gate relies on
- Reporting a reconciliation verdict without having run a real check (fabrication)
- Burying a failed check in prose instead of a BLOCKED box
