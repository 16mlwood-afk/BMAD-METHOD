---
name: 'step-05-round-trip-verify'
description: 'For a cross-service PAYLOAD-CHANGE run only: require one observed sender→receiver round-trip (live or synthetic-replay) and COMPUTE the verified disposition from the evidence — refuse "verified" on inferred evidence. A steady-state contract audit skips this step.'
---

# Step 5: Round-Trip Verify (payload-change class only)

**Goal:** Close the gap a static contract check structurally cannot: a green sender suite + a green receiver suite + an "inferred" contract report can ALL pass while a real payload never crossed the boundary correctly. For a run that is verifying a **change to the payload contract**, require one representative payload to actually travel sender→receiver and be observed landing correctly — and compute the report's `verified` disposition from that evidence rather than asserting it. No round-trip observed ⇒ the disposition is **UNVERIFIED — round-trip owed**, a blocking condition in the verify lane.

This step is the fix for the fork-gap "cross-service payload fixes have NO mandatory end-to-end round-trip gate" (the bison-ops `Held` status incident: sender emitted `pipelineStatus:"Held"`, receiver mapped to `internalStatus`, both suites green, both deployed, no fresh webhook ever sent — the owner caught it).

---

## AVAILABLE STATE

From previous steps:

- `{sender}`, `{receiver}` — both ends
- `{contract}`, `{findings}` — the field ledger + per-field verdicts
- `{baseline_commit}` — reference commit
- `{report_file_path}` — the report written in step-04

---

## WHEN THIS STEP APPLIES — the CHANGE class

This step runs ONLY when the workflow is verifying a **payload-change**, not a steady-state contract audit. A steady-state audit (no change to what the sender emits or the receiver ingests) is complete at step-04 — do not gate it on a round-trip it has no change to exercise.

**The deterministic CHANGE-class signal** — this run is a payload-change iff BOTH hold within one feature:

1. the diff touches a **payload BUILDER on the sender** (the code that assembles the emitted field/value), AND
2. the diff touches the **receiver's INGEST of that same field/value** (read, map, validate, or store).

If only one side changed, it is still a change but the other side's behavior is unverified by construction — treat it as the CHANGE class and round-trip it; a one-sided change to a shared contract is exactly the rollout-unsafe shape this workflow exists to catch. If neither side's payload logic changed, skip to PRESENT (step-04 was terminal).

> Enforcement honesty: this in-workflow gate is **probabilistic for invocation** — it only fires if an agent runs webhook-contract-check at all. The deterministic backbone that makes the agent KNOW a round-trip is owed (a conservative awareness trigger on the sender repo's payload-builder paths, warn-only, on the hook-activation rail) is a SEPARATE distribution track, named in `deployment-to-prod.md` §1B and the fork-gap as a follow-up. What this step DOES make deterministic-once-run: the `verified` disposition is computed from evidence, so it cannot be hand-waved.

---

## THE ROUND-TRIP — two arms, pick what the change allows

One representative payload must cross the boundary and be observed landing correctly. Either arm is valid; pick by what's reachable.

> **Safety — never round-trip into production data.** The round-trip WRITES a record on the receiver (an ingest/upsert). Target the receiver's TEST/staging surface or its integration-test harness (a test DB), never a live replay into the prod datastore. If the receiver has only a prod datastore, the round-trip is **owner-gated**: use a clearly-marked disposable record and remove it after, or defer to a receiver-side integration test. This step verifies a contract; it must not leave a phantom test record in production. (This is the one write this otherwise read-only, no-worktree workflow performs — and it is a test write against a test surface, not a code edit across the boundary.)

### Arm A — live round-trip (preferred when a real source event is reachable)
Capture an actual emitted payload from the sender against a real triggering event, let it hit the receiver, and observe the result (the stored record / the 2xx-with-effect, not just a 2xx). Use when the sender can be driven to emit on demand (e.g. reload the extension and scrape a real qualifying page).

### Arm B — synthetic replay (when the live source event isn't on hand)
When the change can't be triggered live cheaply (the real source event — e.g. a live Undeliverable page, a specific upstream state — isn't available), build ONE representative payload from the **real field shapes** (the sender's actual builder output — never an invented schema) and deliver it to the receiver's ingest **service/handler directly** (bypassing transport auth/signing — this is an integration test, not a curl), then observe landing. Mark synthetic values as synthetic; the status/contract fields under test carry the real names and the values the change is about.

> Reference fixture (the shape Arm B takes): a representative payload + a sender-field→receiver-assertion table + a happy-path test + (where the change adds a guard) a guard test. The bison-ops `Held` fixture is the worked example.

### If the change carries a state-machine / guard
Add the adversarial case to the round-trip: drive the receiver to the state the guard protects, replay the changed payload, and assert the guard behaves (e.g. a terminal-state transition is DROPPED, status held, logged) — end-to-end, not only as the receiver's unit fixtures.

---

## RECORD THE RESULT — append a round-trip block to the report

Append to `{report_file_path}`:

```markdown
## Round-trip verification (payload-change class)

**Change class:** payload-change — sender builder `{sender_builder file:fn}` + receiver ingest `{receiver_ingest file:fn}` both touched.
**Arm:** {live | synthetic-replay}
**Payload:** {the representative payload, or a pointer to the fixture file}
**Assertion:** {expected landed value — e.g. order X / SKU Y lands internalStatus=held, no duplicate row}
**Observed:** {landed-correct | landed-wrong | dropped} — {receiver response / stored value observed}
**Guard case (if any):** {state seeded → payload replayed → guard verdict observed}
**Result:** {ROUND-TRIP VERIFIED | ROUND-TRIP FAILED — <what dropped>}
```

---

## DISPOSITION — computed from evidence, never asserted

Update the report's `payload_evidence` and the overall disposition by RULE, not by claim:

- `payload_evidence` ∈ `{ live, synthetic-replay }` AND **Observed = landed-correct** (and the guard case, if any, passed) → disposition **VERIFIED**.
- `payload_evidence: inferred`, OR no round-trip block, OR **Observed ≠ landed-correct** → disposition **UNVERIFIED — round-trip owed**. This is a **blocking** condition: the workflow MUST NOT present this payload-change as verified, and any "done"/handoff that claims verification is wrong until the round-trip is run (see `deployment-to-prod.md` §1B).

For the CHANGE class, **`inferred` is not a complete check.** A report that ends at `payload_evidence: inferred` for a payload-change is the exact silent hole this step closes — fail it loudly rather than letting it read as done.

---

## PRESENT TO USER (replaces step-04's PRESENT for the CHANGE class)

```
**Webhook contract check + round-trip:** {report_file_path}

**Sender → Receiver:** {sender} → {receiver}
**Change class:** payload-change (builder + ingest both touched)
**Round-trip:** {VERIFIED via live | VERIFIED via synthetic-replay | UNVERIFIED — round-trip owed}
{if verified}: {assertion} observed landing correctly{; guard case passed}.
{if unverified}: inferred evidence only — a representative payload has NOT been observed crossing the boundary. This change is NOT verified; run Arm A or Arm B before declaring done.
```

---

## SUCCESS METRICS

- For a payload-change run, a round-trip block is present and the disposition is computed from its `Observed` result, not asserted.
- `verified` is emitted ONLY on `live`/`synthetic-replay` evidence with an observed-correct landing.
- A guard-bearing change exercises the guard end-to-end, not only via the receiver's unit fixtures.
- A steady-state audit is NOT forced through this step.

## FAILURE MODES

- Presenting a payload-change as verified on `inferred` evidence (the silent hole this step exists to close).
- Inventing a payload schema instead of using the sender's real builder output (Arm B must replay real field shapes).
- Treating a 2xx as landing — assert the stored effect / mapped value, not just the response code.
- Forcing a steady-state contract audit through a round-trip it has no change to exercise (false-positive tax).
- Claiming this gate makes invocation deterministic — it does not; the deterministic backbone is the separate sender-side awareness trigger on the hook rail.
