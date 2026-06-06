---
name: 'step-01-identify-sides'
description: 'Identify the SENDER (payload emission site) and RECEIVER (endpoint validation/parse) and assemble the contract field set from both ends'
nextStepFile: './step-02-walk-contract.md'
---

# Step 1: Identify Sender and Receiver

**Goal:** Nail down both ends of the contract — the SENDER that puts fields on the wire and the RECEIVER that validates and parses them — then build a field inventory drawn from both ends. Each field becomes a contract entry you'll walk in step 2.

---

## STATE VARIABLES (capture now, persist throughout)

- `{sender}` — The emission site: what code builds and POSTs the payload, what fields/types/shapes it puts on the wire
- `{receiver}` — The validation/parse site: what the endpoint requires, tolerates, ignores
- `{contract}` — The union field set, drawn from both ends (built in this step)
- `{live_payload}` — An actual emitted payload captured from the sender (if obtainable)
- `{baseline_commit}` — Git HEAD at workflow start (reference only)

---

## EXECUTION SEQUENCE

### 1. Confirm the Grounding Gate Passed

By now you should be able to state SENDER and RECEIVER in plain English from INITIALIZATION. If you can't, stop and go back to the HALT in `workflow.md`. A contract can't be verified from one end.

### 2. Characterize the SENDER

Find the emission site: the code that serializes a domain model (or a subset of it) into the outbound payload and POSTs it. This is the same "outbound payload builder" pattern `wire-check`'s step-01 flags, except here it's the main subject rather than a side check.

Common emission-site shapes:

- A `build_payload()` / `buildWebhookPayload()` / `*_webhook*` function that cherry-picks fields from a domain model
- `model_dump()` / `model_dump_json()` on a Pydantic subset model, or `JSON.stringify` of a hand-built object
- An envelope wrapper (e.g. `{ event, version, sentAt, data: {...} }`) around a domain object. Note the envelope fields separately from the data fields — envelope drift, like a new `version` or `schemaVersion`, is a classic rollout-window hazard.
- A Chrome-extension or scraper content-script that assembles a payload and POSTs to a receiver endpoint

For each sender field, pull out its name (exact casing), type, shape, whether it's always emitted or only conditionally emitted, and any enum values. Conditionally-emitted fields matter: a field the sender only emits on one branch looks, from the receiver's seat, like an optional field.

### 3. Characterize the RECEIVER

Find the validation/parse site — the endpoint handler and the schema it enforces.

Common receiver shapes:

- A Zod / Pydantic / JSON-schema validator on the request body. Does it `.strict()` and reject unknown keys, or `.passthrough()` and ignore them?
- A hand-rolled parser that reads specific keys and ignores the rest (implicitly lenient)
- A framework route with a typed body. The type is a hypothesis about what's required; confirm it against the actual validation, not the type alone.

For each receiver field, pull out the name it expects (exact casing), the type and shape it requires, required vs optional, and the enum values it accepts. Then get the one that drives everything in step 3: the receiver's unknown-field posture. When a field it doesn't recognize shows up, does it **reject**, **ignore**, or **coerce** it?

### 4. Live the Payload (preferred over inference)

Inference is the fallback. When you can:

- **Capture a real emitted payload.** Trigger the sender, log or intercept the POST body, or pull a recent payload from logs or a webhook-inspection tool. Store it as `{live_payload}`.
- **Watch the receiver's real behavior.** POST one payload with an extra unknown field and another missing an optional field, and record whether the receiver returns 2xx, 4xx, or silently drops. That settles, by observation, the unknown-field posture the schema only claims.

A real payload and a real response beat two schemas that each describe what their author believed the wire carries. If you can't live it — no running services, no captured payload — go ahead with an inferred contract, but **mark it `inferred` in the report** so the reader knows it was never observed on the wire.

### 5. Assemble the Contract Field Set

Build `{contract}` as the union of fields from both ends: every field the sender emits and every field the receiver expects. The union is deliberate. Fields present on only one side are exactly the drift this workflow is here to catch.

```
Contract field: {field_name}
Sender:   {emitted? always|conditional|absent} — {type/shape/enum as emitted}  ({file:line})
Receiver: {expected? required|optional|ignored|rejected} — {type/shape/enum as required}  ({file:line})
Layer:    {envelope | data}
```

### 6. Output the Contract Inventory

Present to the conversation context (intermediate state, not a file):

```
## Webhook Contract Inventory ({count} fields)

**Sender:** {emission site — file:function or service+endpoint}
**Receiver:** {validation site — handler+validator or service+route}
**Payload captured:** {yes — live | no — inferred}
**Receiver unknown-field posture:** {reject | ignore | coerce | unknown}

### Envelope fields
1. {field} — sender: {emitted/type} | receiver: {expected/type}

### Data fields
1. {field} — sender: {emitted/type} | receiver: {expected/type}

### One-sided fields (drift candidates)
1. {field} — present on {sender only | receiver only}
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/webhook-contract-check/steps/step-02-walk-contract.md`.

---

## SUCCESS METRICS

- Both SENDER and RECEIVER located and characterized (not just one end)
- Receiver's unknown-field posture (reject/ignore/coerce) established — by observation if possible
- A real emitted payload captured, or the contract explicitly marked `inferred`
- Contract field set assembled as the UNION of both ends — envelope fields separated from data fields
- Every one-sided field surfaced as a drift candidate (none silently dropped)

## FAILURE MODES

- Characterizing only the sender ("here's what we emit") without reading the receiver's validation. A contract can't be verified from one end.
- Trusting the receiver's body type as its validation when the real validator is stricter or looser than the type
- Missing envelope fields (`version`, `schemaVersion`, `sentAt`) by diffing only the `data` object. Envelope drift is a top rollout-window hazard.
- Inferring the contract when a live payload was there for the taking, and not marking it `inferred`
- Treating a conditionally-emitted sender field as "always present"
