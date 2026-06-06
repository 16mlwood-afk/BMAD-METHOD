---
name: 'step-03-classify-rollout-safety'
description: 'The load-bearing step. For each field, layer a rollout-safety class on top of the match verdict under the sender-strict / receiver-lenient discipline. Output a per-field verdict carrying BOTH dimensions.'
nextStepFile: './step-04-report-and-route.md'
---

# Step 3: Classify Rollout-Safety

**Goal:** This is the dimension `wire-check` does not have and the reason this workflow exists. A field can match perfectly across the boundary and STILL be unsafe to ship, because the sender and the receiver deploy on **different clocks**. For each field, layer a **rollout-safety class** on top of the match verdict from step 2, applying the team's **sender-strict / receiver-lenient** discipline. The output is a per-field verdict carrying BOTH the match/mismatch AND the rollout-safety class.

---

## AVAILABLE STATE

From previous steps:

- `{sender}`, `{receiver}` — both ends, including the receiver's **unknown-field posture** (reject / ignore / coerce)
- `{contract}` — union field set
- `{findings}` — match-layer verdicts from step 2 (Matched / Mismatched / Sender-only / Receiver-only)

---

## THE DISCIPLINE (read before classifying)

**Sender-strict / receiver-lenient during the rollout window.** Because the two deploys land at different times, every schema change must be safe regardless of *which side ships first within the rollout window*. The two invariants:

1. **Receiver-lenient-first for additions.** Before the sender starts emitting a new field, the receiver must already **tolerate** it (ignore unknown fields, or treat the new field as optional). If the sender ships first and the receiver still **rejects** unknown fields, every payload 4xx's the moment the sender deploys. The receiver's leniency must land **first**.
2. **Sender-strict-last for removals.** The sender must keep emitting a field for as long as the receiver still **requires** it. If the sender stops emitting first while the receiver still requires the field, every payload fails validation. The receiver must drop the requirement **first**; only then may the sender stop emitting.

The hinge is the **receiver's unknown-field posture** captured in step 1. A receiver that *ignores* unknowns is already lenient — additions are safe. A receiver that *rejects* unknowns (`.strict()`) is the dangerous case — additions are unsafe until it is made lenient.

---

## EXECUTION SEQUENCE

For each field in `{contract}`, assign exactly one rollout-safety class. Decision procedure:

### A. Additions (a field the SENDER emits that is new relative to the receiver)

Applies to **Sender-only** fields and to any field newly added on the sender side.

- If the receiver **ignores / passthrough-tolerates** unknown fields → **rollout-safe**. The receiver already swallows it; the sender may ship.
- If the receiver **rejects** unknown fields (strict validation) and does NOT yet have a slot → **rollout-unsafe-addition**. The sender shipping first will cause the receiver to reject the payload. **The receiver must be made lenient FIRST.** Flag.
- If the receiver **coerces** (e.g., silently casts) → treat as rollout-safe for *acceptance* but record a step-2 type-mismatch if the coercion changes meaning.

### B. Removals (a field the RECEIVER still requires that the SENDER no longer emits)

Applies to **Receiver-only** fields where the receiver marks the field **required**.

- Receiver **requires** the field, sender no longer emits it → **rollout-unsafe-removal**. The sender ship will fail receiver validation. **The receiver must drop the requirement (or make it optional) FIRST**, then the sender may stop emitting. Flag.
- Receiver treats the field as **optional**, sender no longer emits it → **rollout-safe**. The receiver tolerates absence; the sender may stop.

### C. Steady-state matches & mismatches

- **Matched** field, no change in flight → **rollout-safe** (it is the current contract).
- **Mismatched** field (name/type/shape/enum disagreement from step 2) → the mismatch is a present break regardless of ordering. Class it by what fixing it requires: if the fix adds tolerance on the receiver → **rollout-unsafe-addition** (receiver-first); if the fix changes what the sender emits to match a still-strict receiver → note it as a present break to route, and apply the addition rule to whichever side moves.
- **Enum addition** on the sender (new member the receiver's validator doesn't accept) → if receiver rejects unknown enum values → **rollout-unsafe-addition** (receiver must accept the new value first). If receiver passes through unknown enum values → **rollout-safe**.

---

## PER-FIELD VERDICT (BOTH dimensions — mandatory)

Every field now carries a two-part verdict. Neither part may be omitted.

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

Update `{findings}` so every entry carries BOTH dimensions. A field that reaches step 4 with only a match verdict and no rollout-safety class is an incomplete finding — the whole point of this workflow is the second dimension.

---

## DISPOSITION CHECK (silent-partial-implementation guard)

Before leaving this step, confirm **every field in `{contract}` has an explicit two-part verdict.** Count: `fields in contract == fields with a (match, rollout-safety) pair`. If any field lacks a verdict, it was silently dropped — go back and classify it. No field may reach the report unaccounted for.

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

- Classifying rollout-safety from the schema's *claimed* strictness when a live POST showed the receiver actually ignores unknowns (or vice versa) — live posture wins
- Treating a perfectly-matched field as "nothing to flag" when an in-flight addition makes it unsafe (match and rollout-safety are independent dimensions)
- Calling a sender-side addition safe without confirming the receiver tolerates unknowns
- Forgetting removals — a sender that *stops* emitting a still-required field is just as unsafe as an unsupported addition
- Leaving any field with only a match verdict and no rollout-safety class (silent-partial-implementation)
