---
name: webhook-contract-check
description: 'Verify a webhook payload contract across a service boundary, field-by-field, sender to receiver. Catches contract drift and rollout-unsafe schema changes BEFORE they ship — under the sender-strict / receiver-lenient rollout discipline. Detect-and-report-and-route; never auto-edits across two deploys.'
---

# Webhook Contract Check Workflow

**Goal:** Given a sender emission site and a receiver endpoint (or a contract artifact that describes both), check that every field on the webhook payload survives the trip across the service boundary: name and casing, type, shape, required-vs-optional, enum values. Then do the thing a single-app trace can't. Classify each field for **rollout-safety** under the sender-strict / receiver-lenient discipline, so a change that's fine in steady-state but unsafe mid-rollout gets caught before either side ships. The output is an honest per-field report, and then you route each finding to the side that owns it. You never auto-edit across the boundary.

**Your Role:** Treat both deploys as suspect. The sender's tests pass against the sender's idea of the payload; the receiver's tests pass against the receiver's idea of it. Both suites can be green while the wire between them is already broken, or about to break on the next deploy. What you're actually verifying is the contract across the boundary and the order in which the two sides are allowed to change — not either side on its own.

**Key Insight — a webhook is two deploys joined by an envelope, on different clocks.** Sender and receiver live in different repos, services, and release cadences. So a field mismatch isn't the only way to fail. Even a perfectly correct new field fails if it lands on the wire before the receiver can tolerate it. The rule the team runs is **sender-strict / receiver-lenient during the rollout window**: make the receiver lenient (ignore unknown fields, treat new ones as optional) before the sender starts emitting them, and keep the sender emitting a field for as long as the receiver still requires it. You catch the ordering violation here, on paper, or you catch it in production as a rejected payload right after the sender deploys.

---

## Sibling workflow — what webhook-contract-check is NOT

This is the cross-service analogue of `wire-check`. It adds one dimension and is deliberately more conservative about fixing. Keep the distinction sharp:

| | `wire-check` | `webhook-contract-check` |
| --- | --- | --- |
| **Boundary** | Intra-app: producer → transport → sink, all inside **one deploy** | Cross-service: sender deploy → envelope → receiver deploy, **two deploys on different clocks** |
| **What "correct" means** | The chain of layers holds within the app | The contract holds across the boundary, and the two sides change in a safe order |
| **Added dimension** | — | Schema evolution under a rollout window (sender-strict / receiver-lenient). Each field gets a match/mismatch verdict AND a rollout-safety class. That second verdict is the point of this workflow. |
| **Fix posture** | Auto-fixes every issue — it owns all the code | Detect, report, route. Auto-editing two repos across a deploy boundary is unsafe, so each finding goes to the owning side (sender repo / receiver repo) via `quick-spec`. It never edits both deploys. |
| **Output** | Fixed code on `main` | A contract report plus per-side routing slips. This workflow changes no code. |

Wiring fields between layers of a single app is `wire-check` — use it, it will fix things. Verifying the envelope between two services, and whether a change is safe to ship given the rollout order, is this workflow — and it hands you routed findings, not edits.

---

## CRITICAL RULES

- **The contract of record is the charter.** The standard you verify against is `{project-root}/_bmad/bmm/workflows/shared/webhook-contract-charter.md` — the sender/receiver duties, the sender-strict / receiver-lenient rollout-order rule, and the breaking-change taxonomy all live there, declaratively. A per-boundary contract (if one exists) *refines* the charter for this specific pair and may override a named clause with rationale; the charter governs wherever the boundary contract is silent. Name the clause you're applying in each finding (e.g. "receiver duty R3: fail loud, no silent fallback" or "rollout-unsafe-removal: sender-last not honored").
- **Correctness lives across the boundary, not on either side alone.** A green sender suite and a green receiver suite tell you nothing if they encode two different envelopes, or if both are right but the sender ships first. Check sender-output against receiver-input at the boundary, and check the order in which they're allowed to change.
- **Be exact about format and shape.** `camelCase` vs `snake_case`, `string` vs `number`, `Date` vs ISO string, `[]` vs `null`, required vs optional, enum-value drift — these are the contract bugs. "Looks similar" is not the same as equal. Be precise about casing and shape on both sides.
- **Live the payload; don't infer it.** When you can, capture an actual emitted payload from the sender and watch the receiver's real validation behavior — does it reject, ignore, or coerce an unknown field? Static analysis guesses; a real payload and a real 200/4xx don't. Each side's schema is a hypothesis until a live payload carries it across.
- **A payload-CHANGE run cannot be "verified" on inferred evidence — it MUST round-trip.** When this run is verifying a *change* to the payload contract (the diff touches a payload BUILDER on the sender AND the receiver's INGEST of the same field/value), a static "looks right" is not done: both unit suites can be green while no real payload ever crossed the boundary correctly (the bison-ops `Held` incident). Step-05 requires ONE representative payload to travel sender→receiver — live, or a synthetic replay of the real field shapes against the receiver's ingest directly — observed landing correctly, and COMPUTES the `verified` disposition from that evidence. No round-trip ⇒ disposition is **UNVERIFIED — round-trip owed**, blocking. A steady-state audit (no contract change) skips step-05. This is the awareness/halt tier; the deterministic sender-side trigger that makes the agent KNOW a round-trip is owed rides the hook rail on a separate track (see `deployment-to-prod.md` §1B).
- **Rollout-safety is the classification that matters.** Every field carries two verdicts: the match/mismatch verdict, and the rollout-safety class (**rollout-safe** / **rollout-unsafe-addition** / **rollout-unsafe-removal**). A field can match perfectly and still be rollout-unsafe. Under sender-strict / receiver-lenient: make the receiver lenient first, and keep the sender emitting a field while the receiver still requires it.
- **Every field gets an explicit disposition.** No field on either side gets silently dropped from the report. Account for each one — matched, mismatched, sender-only, receiver-only — with a verdict and a rollout-safety class. A field reported on neither side is a silent-partial-implementation defect.
- **Detect and report across the boundary; never auto-edit two deploys.** This workflow enters no worktree and changes no code. Editing two repos on different release clocks is exactly the unsafe move this workflow exists to prevent — so it reports and routes instead.
- **Route per side.** Each finding belongs to exactly one side, the sender repo or the receiver repo, and the fix is routed there via `quick-spec` with the rollout-safety constraint spelled out (for example, "receiver must ship leniency BEFORE the sender ships the new field"). Routing makes the ordering explicit so the two deploys land in the safe sequence.
- **Finance values: validate against the live site, never internal expectation.** When a finding concerns the interpretation of scraped MONEY values (order totals, fees, taxes, refunds) and routes to a producer-defect report, the producer's proposed rule MUST be validated against the live external site as the source of truth — on a 3–10 order sample — before the defect can be considered resolved, and the result recorded in the report's **§7 Site verification** (see `shared/producer-defect-template.md`). Tool: **Claude in Chrome** (`shared/tool-registry.md` → "Claude in Chrome"). Do NOT settle a money-rule on "max vs min" reasoning alone: the canonical `max()` defect (`producer-defect-bison-ops-2026-06-28`) shipped an over-statement precisely because the rule was never checked against the site, where the settled (lower) total was the truth. This is the awareness tier; the deterministic gate that blocks resolution without §7 lives on the receiver repo's CI track.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{sender}`, `{receiver}`, `{contract}`, `{findings}`, `{baseline_commit}`
- Sequential progression: identify sender/receiver → walk the contract field-by-field → classify rollout-safety → report + route per side → (for a payload-CHANGE run) round-trip verify before any "verified" disposition (step-05)

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

> **Scope — two things `autonomous_mode` does NOT cover:** the **grounding gate** below and the no-auto-edit-across-the-boundary rule. Autonomous mode gives you decision autonomy (which field, which artifact, which phrasing). It does not give you intent autonomy — guessing what the user means when you can't identify the sender or receiver — and it does not let you auto-edit two deploys. If the input isn't groundable, halt regardless of the flag. If a fix spans the boundary, route it; don't apply it. Inventing intent or editing across the boundary under `autonomous_mode` is the exact failure class this workflow is built to avoid.

### No Worktree — Read-Only Across the Boundary

**This workflow enters no worktree and edits no code.** Unlike `wire-check`, it's a read-and-report audit across two deploys: it captures payloads, reads validation, classifies, reports, and routes. The fixes themselves happen later, per side, when `quick-spec` → `quick-dev` runs in the owning repo's own worktree. The deliverable is routing, not editing.

### Input & Grounding Gate

The input is the sender emission site plus the receiver endpoint, or a contract artifact that names both — an OpenAPI/JSON-schema doc, a webhook spec, a prior contract report. If no per-boundary contract artifact exists, the charter (`{project-root}/_bmad/bmm/workflows/shared/webhook-contract-charter.md`) is the default contract of record: verify against its rules and note in the report that no boundary-specific contract was found (and that minting one — via the charter's per-boundary template — is the recommended follow-up).

**Before exiting INITIALIZATION you MUST be able to state both of these in plain English. If you can't, the input isn't groundable — HALT.**

- **SENDER:** what code emits the payload (file/function, or the named service plus the endpoint it POSTs to).
- **RECEIVER:** what code validates/parses the payload (the endpoint handler and its validation, or the named service plus route that receives it).

**Ungroundable inputs (HALT):**

- A request that names only one side ("check our webhook") with no way to find the other. You can't verify a contract from one end.
- A bare verb with no target ("verify the contract", "check it") where neither sender nor receiver is identifiable from the input or `{implementation_artifacts}`.

**HALT response** (same shape as the quick-dev / wire-check halt — say what's wrong, which gate, and what would clear it):

1. State plainly: "I can't identify both sides of the contract. webhook-contract-check needs a SENDER (what emits the payload) and a RECEIVER (what validates it) — they may live in different repos."
2. Name what you *can* see (e.g., "I can see the sender emission site at `X`, but no receiver endpoint or contract artifact").
3. Ask for the missing side: the receiver endpoint/handler, or a contract artifact (OpenAPI/JSON-schema/webhook spec) that describes both.

This halt fires regardless of `autonomous_mode`. The mode buys you execution latitude, not the right to fabricate the missing side of a contract.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check`

### Baseline Commit

Capture `{baseline_commit}` = `git rev-parse HEAD` at workflow start — for reference in the report only. Nothing in this workflow commits.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-01-identify-sides.md` to begin the workflow.
