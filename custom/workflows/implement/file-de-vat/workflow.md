---
name: file-de-vat
description: 'Single front door for the quarterly German VAT filing session via the avask-filing MCP tools. Fixed announced phase contract: pre-flight PASS/FAIL → data pull → validation → portal fill → HALT human review → submit → confirmation receipt. Use when the user says "file German VAT", "start the German filing", "file de vat", "start a VAT filing session", or wants to begin the quarterly AVASK portal filing.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# File DE VAT Workflow

**Goal:** Run the quarterly German VAT filing session end-to-end behind a fixed, announced phase contract — so the user always knows which phase is running, what passed, what failed, and exactly when their approval is needed.

**Your Role:** You are the filing operator. You execute a rigid, legible procedure against a real filing portal. You are not paid for creativity here — you are paid for making every state visible and never crossing the submission boundary without a fresh human yes.

**Key Insight — anxiety is a visibility defect.** This workflow exists because "did it start? is it stuck? did it fail?" was unanswerable. Every phase announces entry and completion. Every blocker renders as a `BLOCKED — need you` box. Silence is a bug.

---

## CRITICAL RULES

- **The submission HALT (step-04) overrides `autonomous_mode`.** Like quick-dev's grounding gate and design-implement's fixture-to-prod checkpoint: decision autonomy never extends to an irreversible partner-facing filing. NEVER simulate, infer, or carry over approval for the submission action (`avask_submit`, or `avask_file_invoices` where step-03 determined it is the portal's real trigger). Approval must be given by the user, in the current conversation, AFTER the submission summary is displayed. Where the settings track is installed, `avask_submit` and `avask_file_invoices` are additionally pinned to permission `ask` — but the in-conversation approval rule is the PRIMARY gate and holds regardless; never add either tool to an allowlist.
- **No portal tool call before pre-flight passes.** `mcp__avask-filing__*` tools are untouchable until step-01 writes the pre-flight marker. (A PreToolUse gate enforces this deterministically where the hook is installed; the rule holds regardless.)
- **Marker lifecycle: any session that ends without completing phase 7 deletes the pre-flight marker.** Decline at step-04, a terminal BLOCKED box, or an abandoned session — all delete `.claude/filing-session/preflight-{period}.json` before ending (a dying session that couldn't is why the gate also applies a freshness TTL). A resumed session re-runs step-01; pre-flight is cheap and read-only.
- **Finance non-negotiables apply.** Never invent figures, totals, or VAT treatments. Missing input → `n/a` + a "Missing data" list. Figures in tables; commentary in a separate Notes section.
- **Blockers are boxes, not prose.** Any condition you cannot resolve yourself renders in the BLOCKED format below and stops the phase. Never bury "I couldn't log in" mid-paragraph.
- **Known unknown — amendability.** Whether a submitted filing can be amended after the fact is UNCONFIRMED. Until confirmed, treat every submission as irreversible and say so in the step-04 review.

## OWNERSHIP — use / don't use

- **Use for:** the quarterly German VAT filing session via the AVASK portal. The `mcp__avask-filing__*` tools are sanctioned ONLY inside this workflow — that is policy, not preference.
- **Do NOT use for:** audit/reconciliation-only sessions (call the `mcp__de-vat-audit__*` tools directly — no filing session needed), UK VAT work, or 13th-Directive reclaim questions.
- **If uncertain** whether a request is a filing session: abstain and ask — never start portal work on an inferred intent.

## PHASE CONTRACT (announce every transition)

| # | Phase | Step file |
|---|-------|-----------|
| 1 | Pre-flight | step-01-preflight |
| 2 | Data pull | step-02-prepare-return |
| 3 | Validation | step-02-prepare-return |
| 4 | Portal fill | step-03-portal-fill |
| 5 | HALT — human review | step-04-review-halt |
| 6 | Submit | step-05-submit-and-receipt |
| 7 | Confirmation receipt | step-05-submit-and-receipt |

**Phase banner format** (emit on entry and on completion of every phase):

```text
▶ PHASE n/7 — {phase name}: {one-line what happens now}
✔ PHASE n/7 — {phase name} complete: {one-line outcome}
```

**BLOCKED format** (emit whenever a phase cannot proceed; then stop and wait):

```text
■ BLOCKED — need you (phase n/7 — {phase name})
  What happened: {one line}
  Why I stopped: {one line}
  What I need from you: {one specific action or answer}
```

## WORKFLOW ARCHITECTURE

Step-file architecture. Steps 1–3 run autonomously (within the rules above); step 4 is a mandatory interactive HALT; step 5 runs only after fresh approval.

State variables: `{period}` (e.g. `2026-Q1`), `{period_source}` (`user-named` | `defaulted`), `{preflight_marker}`, `{return_data}`, `{validation_report}`, `{fill_manifest}`, `{pending_submit_action}` (`avask_submit` default; `avask_file_invoices` when step-03 defers it as the trigger), `{approval_given}`, `{approver}`, `{approval_time}`, `{approval_marker}`, `{confirmation_ref}`.

## INITIALIZATION

### Project gate (run FIRST — before config commentary, before any phase banner)

This workflow is only meaningful in **accounting-tools** with the **avask-filing MCP server** connected. Check both:

1. `{main_config}` → `project_name` must be `accounting-tools`.
2. ToolSearch for `avask` must surface the `mcp__avask-filing__*` tools.

If either fails, emit a BLOCKED box ("This workflow files German VAT for accounting-tools via the avask-filing MCP server, which is not available here") and END the workflow. Do not improvise an alternative filing path.

### Configuration loading

Load `{main_config}` and resolve: `user_name`, `communication_language`, `autonomous_mode`, `autonomous_rules`, `implementation_artifacts`, `date` (system datetime).

`autonomous_mode: true` covers phases 1–4's internal decisions (period defaulting, retry choices, formatting). It does NOT cover the step-04 approval — see Critical Rules.

### Input resolution

- `{period}`: if the user named a period, use it (`{period_source} = user-named`). Otherwise default to the **most recent completed quarter** (the user works one quarter behind), set `{period_source} = defaulted`, and note: step-01 §1 turns a defaulted period into a one-question CONFIRM before any further work — a guessed period must never reach a live portal write.

### Where this session runs

Run in a worktree per project policy (the parallel-session edit guard would otherwise block the marker/receipt writes). This is consistent by construction: the workflow's marker writes and the PreToolUse avask gate both resolve against the running session's `{project-root}`, so within one session they always see the same `.claude/filing-session/`. The receipt artifact is delivered to main via the normal delivery contract at session close.

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-01-preflight.md` to begin.
