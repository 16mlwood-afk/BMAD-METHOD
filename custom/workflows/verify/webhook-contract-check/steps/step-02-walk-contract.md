---
name: 'step-02-walk-contract'
description: 'Walk the payload contract field-by-field, sender to receiver — name/casing, type, shape, required-vs-optional, enum values — and classify each field matched or mismatched'
nextStepFile: './step-03-classify-rollout-safety.md'
---

# Step 2: Walk the Contract, Field-by-Field

**Goal:** For every field in the contract inventory, compare what the SENDER puts on the wire against what the RECEIVER expects. Apply the same exactness `wire-check` uses between layers, but across the service boundary. Here you classify each field **matched** or **mismatched**; step 3 layers the rollout-safety verdict on top.

---

## AVAILABLE STATE

From step 1:

- `{sender}` — Emission site characterization (per-field name/type/shape/emitted-when/enum)
- `{receiver}` — Validation characterization (per-field name/type/shape/required/enum + unknown-field posture)
- `{contract}` — Union field set, envelope vs data
- `{live_payload}` — Captured payload (if any)

---

## EXECUTION SEQUENCE

Run these checks against each field in `{contract}` by reading the actual code or observing the live payload, never by assumption. A live value beats an inferred one at every check.

### Check 1: Name & Casing Match

- [ ] The key the sender emits is byte-for-byte the key the receiver reads. Case-sensitive, exact.
- [ ] No `camelCase` vs `snake_case` split across the boundary. Emit `processedCount`, expect `processed_count`, and it's a mismatch: the receiver sees the field as missing and, depending on posture, either ignores or rejects it.
- [ ] Envelope keys match too (`schemaVersion` vs `schema_version`, `sentAt` vs `timestamp`).

### Check 2: Type Match

- [ ] The JSON type the sender serializes is the type the receiver requires: `string` vs `number` (an ID emitted as `123` but validated as `"123"`), `boolean` vs stringified `"true"`, `Date` object vs ISO-8601 string vs epoch number.
- [ ] Numeric precision and format: cents-as-integer vs decimal string, a timestamp as ISO string vs epoch ms.

### Check 3: Shape Match

- [ ] Array vs scalar (`[]` vs single object), nested object vs flat, `[]` vs `null` for "no items" — the canonical empty-collection mismatch.
- [ ] Null-handling: does the sender emit `null`, omit the key, or emit `[]`? And does the receiver tolerate all three, or only one?

### Check 4: Required vs Optional Match

- [ ] Every field the receiver requires is always emitted by the sender, not just on some branches. A receiver-required field the sender emits on only one branch is a latent break.
- [ ] Also note fields the receiver treats as optional but the sender always sends. That's fine for matching, but it feeds step 3's rollout analysis.

### Check 5: Enum / Value-Domain Match

- [ ] Every enum value the sender can emit is one the receiver accepts. A new sender-side member (`status: "partially_received"`) that the receiver's validator doesn't list is a mismatch — and, per step 3, a rollout hazard.
- [ ] Value-domain constraints: string length caps, format regexes (email, UUID), numeric ranges the receiver enforces that the sender doesn't guarantee.

### Check 6: One-Sided Fields

For each field present on only one end:

- [ ] **Sender-only** (sender emits, receiver has no slot): whether this breaks comes down entirely to the receiver's unknown-field posture. Record it here as a one-sided field and let step 3 settle the verdict.
- [ ] **Receiver-only** (receiver expects, sender never emits): if the receiver requires it, that's a break right now; if it's optional, record it for step 3.

---

## CLASSIFICATION (match dimension)

After the walk, give each field a match verdict. Step 3 adds the rollout-safety class, so every field ends up carrying both.

| Match verdict | Meaning |
| --- | --- |
| **Matched** | Name, type, shape, required-ness, and enum domain all agree across the boundary |
| **Mismatched** | Field flows but name/type/shape/enum disagrees between sender and receiver |
| **Sender-only** | Sender emits it; receiver has no slot for it (verdict depends on receiver posture — resolved in step 3) |
| **Receiver-only** | Receiver expects it; sender never emits it (a hard break if receiver requires it) |

For each field, record:

```
Field: {field_name}  ({envelope|data})
Match verdict: {Matched | Mismatched | Sender-only | Receiver-only}
Sender:   {what is emitted — name/type/shape/when}  ({file:line})
Receiver: {what is expected — name/type/shape/required}  ({file:line})
Evidence: {live payload value | inferred from schema}
Details: {specific disagreement, if any}
```

Store all of this as the match layer of `{findings}`.

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-03-classify-rollout-safety.md`.

---

## SUCCESS METRICS

- Every field in the contract walked across all six checks (name, type, shape, required, enum, one-sided)
- Each field carries a match verdict backed by file:line on both ends
- Live payload values used as evidence wherever captured (not inferred)
- Envelope fields walked with the same exactness as data fields
- No field left without a verdict (every contract entry accounted for)

## FAILURE MODES

- Comparing only the fields the sender emits, and never checking what the receiver requires but never receives — the receiver-only break
- Assuming names match without reading both the emission key and the validation key
- Missing the `[]` vs `null` empty-collection mismatch
- Treating a new sender-side enum value as fine without checking the receiver's accepted set
- Marking a field "matched" from two schemas when a live payload would have exposed a coercion or a casing drift
- Settling a sender-only field's verdict here instead of leaving it to the rollout-safety analysis — its safety hinges on the receiver's unknown-field posture
