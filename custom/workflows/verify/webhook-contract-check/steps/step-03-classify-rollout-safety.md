---
name: 'step-03-classify-rollout-safety'
description: 'The load-bearing step. For each field, layer a rollout-safety class on top of the match verdict under the sender-strict / receiver-lenient discipline. Output a per-field verdict carrying BOTH dimensions.'
nextStepFile: './step-04-report-and-route.md'
---

# Step 3: Classify Rollout-Safety

**Goal:** This is the dimension `wire-check` doesn't have, and it's why this workflow exists. A field can match perfectly across the boundary and still be unsafe to ship, because the sender and receiver deploy on different clocks. For each field, layer a **rollout-safety class** on top of the step-2 match verdict, applying the team's **sender-strict / receiver-lenient** discipline. The output is a per-field verdict carrying both the match/mismatch and the rollout-safety class.

---

## AVAILABLE STATE

From previous steps:

- `{sender}`, `{receiver}` — both ends, including the receiver's **unknown-field posture** (reject / ignore / coerce)
- `{contract}` — union field set
- `{findings}` — match-layer verdicts from step 2 (Matched / Mismatched / Sender-only / Receiver-only)

---

## THE DISCIPLINE (read before classifying)

**Sender-strict / receiver-lenient during the rollout window.** The two deploys land at different times, so every schema change has to be safe no matter which side ships first inside that window. Two invariants:

1. **Receiver-lenient-first for additions.** Before the sender starts emitting a new field, the receiver must already tolerate it — ignore unknown fields, or treat the new field as optional. If the sender ships first while the receiver still rejects unknown fields, every payload 4xx's the moment the sender deploys. The receiver's leniency lands **first**.
2. **Sender-strict-last for removals.** The sender keeps emitting a field for as long as the receiver still requires it. If the sender stops first while the receiver still requires the field, every payload fails validation. The receiver drops the requirement **first**; only then may the sender stop emitting.

Everything turns on the receiver's unknown-field posture from step 1. A receiver that ignores unknowns is already lenient, so additions are safe. A receiver that rejects unknowns (`.strict()`) is the dangerous case: additions are unsafe until it's made lenient.

---

## EXECUTION SEQUENCE

Assign exactly one rollout-safety class to each field in `{contract}`. Decision procedure:

### A. Additions (a field the SENDER emits that's new relative to the receiver)

Covers **Sender-only** fields and any field newly added on the sender side.

- Receiver **ignores / passthrough-tolerates** unknown fields → **rollout-safe**. It already swallows the field; the sender may ship.
- Receiver **rejects** unknown fields (strict validation) and has no slot for it yet → **rollout-unsafe-addition**. Ship the sender first and the receiver rejects the payload. **The receiver must be made lenient FIRST.** Flag it.
- Receiver **coerces** (e.g. silently casts) → treat it as rollout-safe for acceptance, but record a step-2 type-mismatch if the coercion changes meaning.

### B. Removals (a field the RECEIVER still requires that the SENDER no longer emits)

Covers **Receiver-only** fields the receiver marks **required**.

- Receiver **requires** the field, sender no longer emits it → **rollout-unsafe-removal**. The sender ship will fail receiver validation. **The receiver must drop the requirement (or make it optional) FIRST**; then the sender may stop emitting. Flag it.
- Receiver treats the field as **optional**, sender no longer emits it → **rollout-safe**. The receiver tolerates its absence, so the sender may stop.

### C. Steady-state matches & mismatches

- **Matched** field, no change in flight → **rollout-safe**. It's the current contract.
- **Mismatched** field (name/type/shape/enum disagreement from step 2) → the mismatch is a present break, ordering aside. Class it by what the fix needs: if the fix adds tolerance on the receiver → **rollout-unsafe-addition** (receiver-first); if the fix changes what the sender emits to match a still-strict receiver → record it as a present break to route, and apply the addition rule to whichever side moves.
- **Enum addition** on the sender (a new member the receiver's validator doesn't accept) → if the receiver rejects unknown enum values → **rollout-unsafe-addition** (receiver accepts the new value first). If the receiver passes unknown enum values through → **rollout-safe**.

---

## PER-FIELD VERDICT (BOTH dimensions — mandatory)

Every field now carries a two-part verdict. Don't omit either part.

| Rollout-safety class | Meaning | Owning side to fix |
| --- | --- | --- |
| **rollout-safe** | Change can ship in any order within the window — receiver already tolerant, or no change in flight | — (pass) |
| **rollout-unsafe-addition** | Sender emits (or will emit) a field the receiver does not yet tolerate; receiver would reject | **Receiver** — add leniency FIRST |
| **rollout-unsafe-removal** | Receiver still requires a field the sender no longer emits; receiver would reject | **Receiver** — drop/relax requirement FIRST |

Record for each field:

```
Field: {field_name}  ({envelope|data})
Match verdict: {Matched | Mismatched | Sender-only | Receiver-only}      ← from step 2
Rollout-safety: {rollout-safe | rollout-unsafe-addition | rollout-unsafe-removal}
Owning side: {sender repo | receiver repo | — }
Ordering constraint: {e.g. "receiver must ship leniency before sender emits"; "—" if safe}
Evidence: {live payload + observed receiver response | inferred}
```

Update `{findings}` so every entry carries both dimensions. A field that reaches step 4 with only a match verdict and no rollout-safety class is an incomplete finding. The second dimension is what this workflow is for.

---

## DISPOSITION CHECK (silent-partial-implementation guard)

Before leaving this step, confirm **every field in `{contract}` has an explicit two-part verdict.** Count it: `fields in contract == fields with a (match, rollout-safety) pair`. If any field lacks a verdict, it got silently dropped — go back and classify it. No field reaches the report unaccounted for.

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-04-report-and-route.md`.

---

## SUCCESS METRICS

- Every field carries BOTH a match verdict and a rollout-safety class
- Rollout-safety derived from the receiver's actual unknown-field posture, not assumed
- Additions classified receiver-first; removals classified receiver-first; the ordering constraint stated per unsafe field
- The disposition check passed: contract field count == verdict count
- Envelope-field additions (new `version`/`schemaVersion`) classified, not skipped

## FAILURE MODES

- Classifying rollout-safety from the schema's claimed strictness when a live POST showed the receiver actually ignores unknowns (or the reverse). The observed posture wins.
- Treating a perfectly-matched field as "nothing to flag" when an in-flight addition makes it unsafe. Match and rollout-safety are independent dimensions.
- Calling a sender-side addition safe without confirming the receiver tolerates unknowns
- Forgetting removals. A sender that stops emitting a still-required field is just as unsafe as an unsupported addition.
- Leaving any field with only a match verdict and no rollout-safety class (silent-partial-implementation)
