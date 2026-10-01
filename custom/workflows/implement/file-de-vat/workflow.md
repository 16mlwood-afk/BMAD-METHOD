---
name: file-de-vat
description: 'Single front door for the quarterly German VAT filing session via the avask-filing MCP tools. Fixed announced phase contract: pre-flight PASS/FAIL → data pull → validation → portal fill → HALT human review → submit → confirmation receipt. Use when the user says "file German VAT", "start the German filing", "file de vat", "start a VAT filing session", or wants to begin the quarterly AVASK portal filing.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
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

**Phase banner format** — the *trace-tier* form of a transition (emit on entry and on completion of every phase):

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

## OUTPUT — two tiers and the voice slot

The phase contract above is load-bearing — visibility is the whole point — but its raw form reads as an operator console, and when the gate's agent-facing text leaks straight to the user the session feels like three systems, not one assistant. Surface the contract in two tiers and let the executing agent speak in three sanctioned spots. This is presentation only: it does not weaken, move, or reword a single gate, marker, HALT, or approval rule above. On any conflict, the gate and the answer-shape standard win and the voice yields.

**Two tiers.**

- **Conversational lane (default — what the user reads):** one plain-language line per phase transition, the step-04 HALT summary, and the BLOCKED box. This is all the user sees unless they ask for more. The lane-line and its `▶ PHASE n/7` banner are the SAME transition at two altitudes — emitting the human line already satisfies "every phase announces"; the banner is its trace twin, not a second event.
- **Trace tier (on demand):** the raw `▶ PHASE n/7` / `✔` banners, worktree/sync/hook logs, and any agent-facing gate `permissionDecisionReason`. Surface it only when the user says "show the trace" (or equivalent), or when a raw reason is genuinely needed to act. Never dump it by default — but never withhold it when asked (compression is not concealment; a failed check, skipped step, or unverified state is stated plainly in the lane regardless).

**The voice slot (`persona_slot`).** The agent executing this workflow MAY speak in its own voice in exactly three spots (per `shared/workflow-personas.md` §1 — presentation only, never decision-making):

1. **Opening re-orientation** — one line at session start (step-01 §1) naming what we're about to do.
2. **Risk acknowledgement on a BLOCK** — the `What happened` / `Why I stopped` lines atop a BLOCKED box.
3. **"I" on the approval recommendation** — first person when owning the step-04 recommendation.

If no voice is bound, these render plain and anonymous — **today's behavior, unchanged.** The workflow itself stays voice-agnostic and names no persona; the binding is the project's, per `persona-placement.md`. (In accounting-tools the slot is filled by the executing agent **Anya** (`custom/agents/anya-de-vat.md`), handed off from the session-start **Remy** brief — but this file does not depend on that.) The voice flavors those three lines and nothing else: it never drives a decision, reopens a menu, or changes phase/HALT/gate structure.

**Decision-line contract (the BLOCKED box, tightened).** Every BLOCKED box is written for the OWNER, not the agent. The `What I need from you:` line MUST:

- be in **owner terms** — portal status, the DE Apr–Jun row, "confirm Q2 already filed" — NEVER tool names, script paths, marker filenames, or raw `permissionDecisionReason` text;
- name the **single fact that would unblock it** and the **smallest next move**;
- push the raw gate reason / tool output to the **trace tier** (available on "show the trace").

This is a presentation wrapper only. It MUST NOT soften, restate-away, or invent a path around a deny — the gate's decision stands exactly as the hook made it. A voice that weakens a deny is a `workflow-personas.md` §1 violation (voice driving a decision). Same block, same safety; the owner just reads it in their own terms.

**Worked example — a gate deny becomes a decision-line.** A mutating avask tool denied by the PreToolUse gate returns an agent-facing `permissionDecisionReason` ("…portal-truth = not_checked… scripts/set-filing-status.sh --period … Do NOT write the marker by hand"). Do NOT surface that raw. Render:

```text
■ BLOCKED — need you (phase 6/7 — Submit)
  What happened: I can't confirm whether {period} was already filed.
  Why I stopped: the receipt, the PA banner, and the ledger disagree, and none of them is portal-truth — I won't submit on a guess.
  What I need from you: read the AVASK portal's DE {month-range} row and tell me what it says — filed, or still "Provide Data". (Say "show the trace" for the exact gate reason.)
```

## WORKFLOW ARCHITECTURE

Step-file architecture. Steps 1–3 run autonomously (within the rules above); step 4 is a mandatory interactive HALT; step 5 runs only after fresh approval.

State variables: `{period}` (e.g. `2026-Q1`), `{period_source}` (`user-named` | `defaulted`), `{preflight_marker}`, `{return_data}`, `{validation_report}`, `{fill_manifest}`, `{pending_submit_action}` (`avask_submit` default; `avask_file_invoices` when step-03 defers it as the trigger), `{approval_given}`, `{approver}`, `{approval_time}`, `{approval_marker}`, `{confirmation_ref}`, `{case_slug}` (`de-vat-{period}` lowercased — the PA case key).

## CASE RECORD (PA mode)

Alongside the phase markers, this workflow keeps a durable **filing case** in comms_dashboard so the session-start PA banner can LEAD with an unsent, near-due filing instead of waiting to be asked. The case is keyed by `{case_slug}` = `de-vat-{period}` lowercased (e.g. `de-vat-2026-q2`). Each boundary step advances it via `{project-root}/scripts/vat-filing-case-update.sh` (step-01 §6, step-02 §3, step-04 §2b/§4, step-05 §1). Contract:

- **Best-effort, never blocking.** The helper always exits 0; a comms_dashboard outage degrades PA visibility, never the filing. No phase gates on its result.
- **Lifecycle:** `in_progress` (pre-flight passed) → `ready_to_send` (portal filled, awaiting your review) → `sent` (submitted). `sent` is terminal server-side — a resumed session can advance the case but never un-sends a filed return.
- **The `sent` write is re-prompted deterministically** by a PostToolUse reminder (`scripts/hooks/avask-submit-sent-reminder.sh`) right after the submission tool runs, so step-05's write is never silently skipped. It NEVER auto-marks — an ambiguous or failed submit must not show as sent — it only re-prompts the step-05 write once a real confirmation exists.
- **State reporting only.** It is NEVER a substitute for the step-04 human-approval HALT.

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

Run in a worktree per project policy (the parallel-session edit guard would otherwise block the marker/receipt writes). **Two roots, not one — do not conflate them** (fork-gap 2026-07-04: "consistent by construction" was false in a worktree):

- **Step files** resolve from wherever they are readable. A fresh worktree contains **no `_bmad/`** (it is untracked on `main`, and the EnterWorktree auto-sync is opt-in / off by default), so `{project-root}/_bmad/.../step-NN.md` will 404 in the worktree and you will read the step files from the **MAIN checkout** instead. That is expected — the step content is identical; only the path differs.
- **Filing-session markers and the PreToolUse avask gate** must both anchor to the gate's own root, **`CLAUDE_PROJECT_DIR` (the MAIN checkout)** — NOT the worktree's `.claude/`. The gate reads markers from `CLAUDE_PROJECT_DIR/.claude/filing-session/`; a marker written into the worktree's `.claude/` is invisible to it and the gate will deny a legitimate session. Write every pre-flight / approval / portal-reconcile marker under `CLAUDE_PROJECT_DIR/.claude/filing-session/`.

Init check: if `_bmad/` is absent in the worktree and you have not run `sync-bmad-workflows.sh --worktree "$(pwd)"`, do not treat the missing path as an error — resolve step files from the main checkout and keep marker writes anchored to `CLAUDE_PROJECT_DIR`. The receipt artifact is delivered to main via the normal delivery contract at session close.

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/file-de-vat/steps/step-01-preflight.md` to begin.
