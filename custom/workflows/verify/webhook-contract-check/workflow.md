---
name: webhook-contract-check
description: 'Verify a webhook payload contract across a service boundary, field-by-field, sender to receiver. Catches contract drift and rollout-unsafe schema changes BEFORE they ship — under the sender-strict / receiver-lenient rollout discipline. Detect-and-report-and-route; never auto-edits across two deploys.'
---

# Webhook Contract Check Workflow

**Goal:** Take a sender emission site and a receiver endpoint (or a contract artifact describing them) and verify that every field on the webhook payload flows correctly across the service boundary — name/casing, type, shape, required-vs-optional, enum values. Then add the dimension a single-app trace cannot have: classify each field for **rollout-safety** under the sender-strict / receiver-lenient discipline, so a change that is correct in steady-state but unsafe mid-rollout is caught before either side ships. Produce an honest per-field report, then **route each finding to the side that owns it** — never auto-edit across the boundary.

**Your Role:** You are the cross-service contract specialist. You don't trust either deploy in isolation. The sender's tests are green against the sender's idea of the payload; the receiver's tests are green against the receiver's idea of the payload; both can be green while the wire between them is broken or about to break on the next deploy. The whole job is the contract **across the boundary** and the **order in which the two sides may change** — not either side alone.

**Key Insight — A webhook is two deploys joined by an envelope, and they ship on different clocks.** The sender and the receiver live in different repos / services / release cadences. That means a field mismatch is not the only failure: even a *correct* new field is a failure if it lands on the wire before the receiver is ready to tolerate it. The canonical rule the team runs is **sender-strict / receiver-lenient during the rollout window**: the receiver must be made lenient (ignore unknown fields, treat new ones as optional) *before* the sender starts emitting them; and the sender must keep emitting a field for as long as the receiver still requires it. Catch the ordering violation here, on paper, or catch it in production as a rejected payload after the sender deploys.

---

## Sibling workflow — what webhook-contract-check is NOT

This workflow is the **cross-service analogue of `wire-check`**, with one added dimension and a deliberately more conservative fix posture. Keep the distinction sharp:

| | `wire-check` | `webhook-contract-check` |
| --- | --- | --- |
| **Boundary** | Intra-app: producer → transport → sink, all inside **one deploy** | Cross-service: sender deploy → envelope → receiver deploy, **two deploys on different clocks** |
| **Unit of correctness** | The chain of layers within the app | The contract across the service boundary **plus the order the two sides may change** |
| **Added dimension** | — | **Schema evolution under a rollout window** (sender-strict / receiver-lenient). Per field: a match/mismatch verdict AND a rollout-safety class. This is the load-bearing addition. |
| **Fix posture** | **Auto-fixes** every issue — it owns all the code | **Detect + report + route.** Auto-editing two repos across a deploy boundary is unsafe, so it routes each finding to the owning side (sender repo / receiver repo) via `quick-spec`. It never edits both deploys. |
| **Output** | Fixed code on `main` | A contract report + per-side routing slips. No code changed by this workflow. |

If the work is wiring fields between layers of a single app, that's `wire-check` — use it; it will fix things. If the work is verifying the envelope between two services and whether a change is safe to ship given the rollout order, that's this workflow — and it will hand you routed findings, not edits.

---

## CRITICAL RULES

- **The chain across the service boundary is the unit of correctness, not either side alone.** A green test on the sender and a green test on the receiver prove nothing if they encode two different envelopes — or if they're both right but the sender ships first. Verify sender-output against receiver-input at the boundary, and verify the *order* in which they may change.
- **Format and shape exactness.** `camelCase` vs `snake_case`, `string` vs `number`, `Date` vs ISO string, `[]` vs `null`, required vs optional, enum-value drift — these are the contract bugs. "Looks similar" is not equivalent. Be exact about casing and shape on both sides.
- **Live the payload, don't infer it.** When you can, capture an **actual emitted payload** from the sender and observe the receiver's **real validation behavior** (does it reject, ignore, or coerce an unknown field?). Static analysis hallucinates; a real payload and a real 200/4xx don't. The schema on each side is a hypothesis until a live payload carries it across.
- **Rollout-safety is the load-bearing classification.** Every field carries TWO verdicts: the match/mismatch verdict AND the rollout-safety class (rollout-safe / rollout-unsafe-addition / rollout-unsafe-removal). A field can match perfectly and still be rollout-unsafe. Under the sender-strict / receiver-lenient discipline: the receiver must be made lenient *first*; the sender must keep emitting a field while the receiver still requires it.
- **Every field gets an explicit disposition.** No field on either side may be silently dropped from the report. Each field is accounted for — matched, mismatched, sender-only, receiver-only — with a stated verdict and a rollout-safety class. A field reported on neither side is a silent-partial-implementation defect.
- **Detect and report across the boundary — never auto-edit two deploys.** This workflow does not enter a worktree and does not change code. Auto-editing two repos on different release clocks is the unsafe operation this workflow exists to prevent, not perform. It produces a report and routes findings.
- **Route per side.** Each finding is owned by exactly one side — the sender repo or the receiver repo. The fix is routed there via `quick-spec`, with the rollout-safety constraint stated (e.g., "receiver must ship leniency BEFORE the sender ships the new field"). The routing makes the ordering explicit so the two deploys land in the safe sequence.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{sender}`, `{receiver}`, `{contract}`, `{findings}`, `{baseline_commit}`
- Sequential progression through 4 phases: identify sender/receiver → walk the contract field-by-field → classify rollout-safety → report + route per side

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input** for *decision* questions — which field to inspect first, which artifact is the most recent payload, how to phrase a routing slip. Choose the most productive option and proceed.
- **Complete the full workflow end-to-end** — walk every field, classify every field, report every field, and emit a routing slip for every finding.

> **Scope — this is NOT subject to `autonomous_mode`:** The **grounding gate** below and the **no-auto-edit-across-the-boundary** rule. Autonomous mode grants *decision autonomy* (which field, which artifact, which phrasing). It does NOT grant *intent autonomy* (guessing what the user means when sender/receiver can't be identified) and it does NOT grant the right to auto-edit two deploys. If the input isn't groundable, halt regardless of the flag. If a fix spans the boundary, route it — never apply it. Inventing intent or editing across the boundary under `autonomous_mode` is the documented failure class this workflow is built to avoid.

### No Worktree — Read-Only Across the Boundary

**This workflow does not enter a worktree and does not edit code.** Unlike `wire-check`, it is a read-and-report audit across two deploys. It captures payloads, reads validation, classifies, reports, and routes. The actual fixes are performed later, per-side, by `quick-spec` → `quick-dev` in the owning repo's own worktree. Routing — not editing — is the deliverable.

### Input & Grounding Gate

The input is **the sender emission site + the receiver endpoint**, or a **contract artifact** that names both (an OpenAPI/JSON-schema doc, a webhook spec, a prior contract report).

**Before exiting INITIALIZATION you MUST be able to state both of the following in plain English. If you cannot, the input is not groundable — HALT.**

- **SENDER:** what code emits the payload (file/function, or the named service + endpoint it POSTs to).
- **RECEIVER:** what code validates/parses the payload (the endpoint handler + its validation, or the named service + route that receives it).

**Ungroundable inputs (HALT):**

- A request that names only one side ("check our webhook") with no way to locate the other — you cannot verify a contract from one end.
- A bare verb with no target ("verify the contract", "check it") where neither sender nor receiver is identifiable from the input or `{implementation_artifacts}`.

**HALT response** (mirror the quick-dev / wire-check halt shape — say what's wrong, which gate, and what would satisfy it):

1. State plainly: "I can't identify both sides of the contract. webhook-contract-check needs a SENDER (what emits the payload) and a RECEIVER (what validates it) — they may live in different repos."
2. Name what you *can* see (e.g., "I can see the sender emission site at `X`, but no receiver endpoint or contract artifact").
3. Ask for the missing side: the receiver endpoint/handler, or a contract artifact (OpenAPI/JSON-schema/webhook spec) that describes both.

This halt fires regardless of `autonomous_mode`. The mode grants execution latitude, not the right to fabricate the missing side of a contract.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check`

### Baseline Commit

Capture `{baseline_commit}` = `git rev-parse HEAD` at workflow start — for reference in the report only. Nothing in this workflow commits.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-01-identify-sides.md` to begin the workflow.
