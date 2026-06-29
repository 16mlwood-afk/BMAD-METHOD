---
name: 'step-04-report-and-route'
description: 'Produce the honest contract report (both dimensions per field), then route each finding to the side that owns it via quick-spec — never auto-edit across the deploy boundary'
---

# Step 4: Report and Route

**Goal:** Write a structured, honest contract report — every field with both its match verdict and its rollout-safety class — then route each finding to the side that owns the fix (sender repo or receiver repo) via `quick-spec`. This workflow changes no code. The deliverable is a report plus per-side routing slips that make the safe deploy ordering explicit.

---

## AVAILABLE STATE

From previous steps:

- `{sender}`, `{receiver}` — both ends
- `{contract}` — union field set
- `{findings}` — every field with a (match verdict, rollout-safety class) pair
- `{baseline_commit}` — reference commit (nothing is committed)

---

## REPORT FIRST, ROUTING SECOND — house rule

Write the honest report before you generate any routing slip — same as `wire-check`'s "honest report first, fixes second." The report is the record of what the contract actually is right now. Don't soften or rewrite it after routing. Routing is a separate, additive act.

---

## REPORT FORMAT

Write the report to `{implementation_artifacts}/webhook-contract-check-{slug}-{date}.md` where `{slug}` names the sender→receiver pair.

```markdown
---
title: 'Webhook Contract Check: {sender} → {receiver}'
created: '{date}'
sender: '{emission site}'
receiver: '{validation site}'
payload_evidence: '{live | synthetic-replay | inferred}'
type: webhook-contract-check
---

# Webhook Contract Check: {sender} → {receiver}

**Sender:** {emission site — file:function or service+endpoint}
**Receiver:** {validation site — handler+validator or service+route}
**Receiver unknown-field posture:** {reject | ignore | coerce}
**Payload evidence:** {live — captured payload | synthetic-replay — representative payload replayed to receiver ingest | inferred — no payload observed}
**Fields in contract:** {total_count}

## Summary

| Rollout-safety class      | Count |
| ------------------------- | ----- |
| rollout-safe              | {n}   |
| rollout-unsafe-addition   | {n}   |
| rollout-unsafe-removal    | {n}   |

| Match verdict | Count |
| ------------- | ----- |
| Matched       | {n}   |
| Mismatched    | {n}   |
| Sender-only   | {n}   |
| Receiver-only | {n}   |

{If all rollout-safe and all matched: "Contract intact and rollout-safe — no findings."}
{Else: "**{n} findings** — {u} rollout-unsafe. Routed below."}

## Field Ledger (every field, both dimensions)

| Field | Layer | Match verdict | Rollout-safety | Owning side | Ordering constraint |
| ----- | ----- | ------------- | -------------- | ----------- | ------------------- |
| {field} | {envelope/data} | {matched/...} | {safe/unsafe-add/unsafe-remove} | {sender/receiver/—} | {constraint or —} |

_Every field in the contract appears in this ledger. A field absent from the ledger is a defect._

## Findings (in priority order: rollout-unsafe > mismatched > one-sided)

### {n}. {field_name} — {rollout-safety class} / {match verdict}

- **Sender:** {file:line} — {what is emitted: name/type/shape/when}
- **Receiver:** {file:line} — {what is expected: name/type/shape/required}
- **Evidence:** {live payload value + observed receiver response | inferred}
- **Why unsafe / mismatched:** {specific explanation}
- **Owning side:** {sender repo | receiver repo}
- **Ordering constraint:** {e.g. "receiver must ship leniency BEFORE sender emits this field"}
- **Routed to:** {quick-spec slip filename, filled in below}

## Pattern Notes

{Optional. Recurring shape across findings — e.g. "receiver uses .strict() Zod across all endpoints, so every additive sender change is rollout-unsafe until leniency is added globally."}
```

---

## ROUTE PER SIDE — the fix posture

**This workflow detects and reports; it does not edit across the boundary.** Editing two repos on different deploy clocks is the unsafe move this workflow is built to prevent. For each finding, generate a routing slip addressed to the single owning side, to be run by that repo's own `quick-spec` → `quick-dev` in its own worktree.

### Per-side routing rules

| Finding | Owning side | Routing slip says |
| --- | --- | --- |
| **rollout-unsafe-addition** | **Receiver** | "Make the receiver lenient to `{field}` (ignore-unknown or treat-optional) and deploy this BEFORE the sender ships the field." |
| **rollout-unsafe-removal** | **Receiver** | "Relax the receiver's requirement on `{field}` (make optional) and deploy this BEFORE the sender stops emitting it." |
| **Mismatched (name/casing)** | The side that deviates from the agreed contract | "Rename `{field}` to `{agreed}` to match the contract; if receiver is strict, sequence per the rollout rule." |
| **Mismatched (type/shape)** | Usually **sender** (emit the shape the receiver requires), unless the receiver should broaden | "Emit `{field}` as `{type/shape}`; if it widens what the receiver must accept, the receiver broadens FIRST." |
| **Receiver-only (required, never emitted)** | **Sender** (start emitting) or **Receiver** (drop requirement) — state which, and the ordering | per the chosen direction |

### Routing-slip shape

For each finding, emit a copy-pasteable slip the owning repo's session can run as-is:

```
**Route → {owning side} repo**

quick-spec: {one-line intent — verb + target on the owning side}
Context: webhook contract `{sender} → {receiver}`, field `{field}`.
Finding: {match verdict} / {rollout-safety class}.
Constraint: {ordering constraint — which side deploys first}.
Source report: {report_file_path}
```

If `autonomous_mode` is on and the owning side is the same project this workflow is running in, you may invoke `quick-spec` directly for that side. If the owning side is a different repo or deploy, emit the slip for a human or that repo's session to run — you do not reach across and edit it.

### Per-finding disposition (silent-partial-implementation guard)

Every finding ends with an explicit disposition: **routed-to-sender**, **routed-to-receiver**, **acknowledged-no-action** (intentional, or not relevant to the consumer), or **needs-product-decision** (unclear whether the consumer needs the field). No finding drops out of the routing pass silently. State the count: `findings == dispositions`.

**When the owning side is an EXTERNAL repo you don't control** — the sender is another team's scraper extension or upstream service (resolve against the registry in `shared/producer-defect-template.md`) — a `quick-spec` slip is unactionable: there's no in-repo code to spec. Disposition that finding **routed-to-sender (`external:<producer_id>`)** and emit the producer-defect report per `shared/producer-defect-template.md` instead — it carries the violated charter clause, the evidence, and the proposed contract change to file upstream. The receiver-side hardening (fail-loud leniency/rejection per charter Receiver §3) stays an in-repo `quick-spec`. Report and harden are both required — neither substitutes for the other.

---

## WORKED EXAMPLE (sender-strict / receiver-lenient catch)

> **Context.** Mid-rollout, the sender (a scraper/extension emitting order payloads) starts wrapping its payload in a new envelope field, `schemaVersion: 2`, to flag a forthcoming data-shape change. The receiver validates the body with a `.strict()` Zod schema that lists the known envelope keys (`event`, `sentAt`, `data`) and **rejects** unknown keys. It hasn't been updated to tolerate `schemaVersion` yet.
>
> **Step 1** captures a live payload carrying `schemaVersion: 2`, and a test POST with an extra key returns `400`. Receiver unknown-field posture = **reject**.
>
> **Step 2** match verdict: `schemaVersion` is **Sender-only** — the receiver has no slot for it.
>
> **Step 3** rollout-safety: addition plus a receiver that rejects unknowns → **rollout-unsafe-addition**. Ship `schemaVersion` from the sender first and every webhook 400's. Owning side = **receiver**. Ordering constraint = "receiver must ship leniency (accept-and-ignore `schemaVersion`) BEFORE the sender emits it."
>
> **Step 4** routes:
>
> ```
> **Route → receiver repo**
>
> quick-spec: relax the webhook body validator to ignore unknown envelope keys (or explicitly accept `schemaVersion`)
> Context: webhook contract `order-scraper → /webhooks/orders`, field `schemaVersion`.
> Finding: Sender-only / rollout-unsafe-addition.
> Constraint: receiver MUST deploy leniency BEFORE the sender ships `schemaVersion: 2`.
> Source report: _bmad-output/implementation-artifacts/webhook-contract-check-order-scraper-receiver-2026-06-06.md
> ```
>
> The workflow doesn't edit the sender to stop emitting, and it doesn't reach into the receiver repo to add leniency itself. It reports the unsafe ordering and routes the fix to the receiver with the deploy-order constraint stated. That's exactly the catch sender-strict / receiver-lenient is meant to produce before anything ships.

---

## NEXT — round-trip if this is a payload-change

Classify the run before presenting:

- **Payload-change run** — the diff being verified touches a payload BUILDER on the sender AND the receiver's INGEST of the same field/value. The contract report above is necessary but NOT sufficient: a static check cannot certify a real payload crosses the boundary correctly (the bison-ops `Held` incident — both suites green, nothing round-tripped). **Proceed to `step-05-round-trip-verify.md`**; it requires one observed round-trip (live or synthetic-replay) and computes the `verified` disposition from that evidence. Do NOT present this run as verified until step-05 runs — step-05 owns PRESENT for this class.
- **Steady-state contract audit** — no change to what the sender emits or the receiver ingests. This report is terminal; present below.

Read fully and follow `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-05-round-trip-verify.md` when the run is a payload-change.

## PRESENT TO USER

```
**Webhook contract check complete:** {report_file_path}

**Sender → Receiver:** {sender} → {receiver}  ({live | inferred})
**{total} fields in contract:**
- {safe} rollout-safe
- {unsafe_add} rollout-unsafe-addition
- {unsafe_remove} rollout-unsafe-removal

{If findings:}
**Routed:**
1. {field} → {owning side} ({rollout-safety class}) — {ordering constraint}
2. ...

{If clean:}
Contract intact and rollout-safe — nothing to route.
```

---

## SUCCESS METRICS

- Report written to implementation artifacts directory, with the full field ledger (every field, both dimensions)
- Findings ordered by priority (rollout-unsafe first)
- Each finding routed to exactly one owning side, with the deploy-ordering constraint stated
- Every finding carries an explicit disposition (findings == dispositions)
- No code edited across the boundary by this workflow
- Report written before any routing slip (honest record first)

## TERMINAL — Behavior Update Digest (STD-DIGEST-001)

Audit-lane terminal: emit the **Behavior Update Digest** per `shared/behavior-update-digest.md` — the per-side routes become `story_candidate` / `handoff_delta` (each `quick-spec` with its deploy-ordering constraint as an acceptance criterion), record any `doctrine_delta`, name `owner_gated`, and declare the `completion_disposition` (STD-COMPLETION-001 `advisory`). The never-auto-edit-across-the-boundary rule above is unchanged — the digest standardizes the close-out, it never edits either side or invokes the routed lane.

## FAILURE MODES

- Auto-editing the sender or receiver instead of routing — the boundary-crossing edit this workflow exists to prevent
- Routing a finding to both sides, or to neither. Each finding has exactly one owning side.
- Omitting the ordering constraint on a rollout-unsafe finding. The constraint is the value of the finding.
- Dropping a field from the ledger or a finding from the disposition count (silent-partial-implementation)
- Rewriting the report to look cleaner after routing. The original verdict is the record.
- Reporting only mismatches and forgetting the rollout-unsafe-but-matched fields
