---
name: 'step-01-identify-sides'
description: 'Identify the SENDER (payload emission site) and RECEIVER (endpoint validation/parse) and assemble the contract field set from both ends'
nextStepFile: './step-02-walk-contract.md'
---

# Step 1: Identify Sender and Receiver

**Goal:** Pin down the two ends of the contract — the SENDER that puts fields on the wire and the RECEIVER that validates/parses them — and build a field inventory drawn from BOTH ends. Each field becomes a contract entry to walk in step 2.

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

You should already be able to state SENDER and RECEIVER in plain English from INITIALIZATION. If you cannot, do not proceed — return to the HALT in `workflow.md`. You cannot verify a contract from one end.

### 2. Characterize the SENDER

Locate the emission site. This is the code that **serializes a domain model (or a subset of it) into the outbound payload and POSTs it** — the same "outbound payload builder" pattern `wire-check`'s step-01 flags, but here it is the primary subject, not a side check.

Common emission-site shapes:

- A `build_payload()` / `buildWebhookPayload()` / `*_webhook*` function that cherry-picks fields from a domain model
- `model_dump()` / `model_dump_json()` on a Pydantic subset model, or `JSON.stringify` of a hand-built object
- An envelope wrapper (e.g., `{ event, version, sentAt, data: {...} }`) around a domain object — note the **envelope fields** separately from the **data fields**; envelope drift (a new `version` or `schemaVersion`) is a classic rollout-window hazard
- A Chrome-extension / scraper content-script that assembles a payload and POSTs to a receiver endpoint

For the sender, extract per field: **name (exact casing), type, shape, whether it is always emitted vs conditionally emitted, and enum values** if applicable. Conditionally-emitted fields matter — a field the sender emits only on one branch behaves, from the receiver's view, like an optional field.

### 3. Characterize the RECEIVER

Locate the validation/parse site — the endpoint handler and the schema it enforces.

Common receiver shapes:

- A Zod / Pydantic / JSON-schema validator on the request body (does it `.strict()` reject unknown keys, or `.passthrough()` / ignore them?)
- A hand-rolled parser that reads specific keys and ignores the rest (implicitly lenient)
- A framework route with a typed body (the type is a *hypothesis* about what's required — confirm against the actual validation, not the type alone)

For the receiver, extract per field: **name it expects (exact casing), type it requires, shape, required vs optional, enum values it accepts**, and crucially the receiver's **unknown-field posture** — does it **reject**, **ignore**, or **coerce** a field it doesn't recognize? This posture is the hinge of the entire rollout-safety analysis in step 3.

### 4. Live the Payload (preferred over inference)

Inference is a fallback. When you can:

- **Capture a real emitted payload** — trigger the sender, log/intercept the POST body, or pull a recent payload from logs/a webhook-inspection tool. Store as `{live_payload}`.
- **Observe the receiver's real behavior** — POST a payload with an extra unknown field and a payload missing an optional field; record whether the receiver returns 2xx, 4xx, or silently drops. This empirically settles the unknown-field posture that the schema *claims*.

A real payload + a real response beats two schemas that each describe what their author *believed* the wire carries. If you cannot live it (no running services, no captured payload), proceed with inferred contract but **mark the contract `inferred` in the report** so the reader knows it wasn't observed on the wire.

### 5. Assemble the Contract Field Set

Build `{contract}` as the **union of fields from both ends** — every field the sender emits AND every field the receiver expects. The union is deliberate: fields present on only one side are exactly the drift this workflow exists to catch.

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

- Characterizing only the sender ("here's what we emit") without reading the receiver's validation — you cannot verify a contract from one end
- Trusting the receiver's body *type* as its validation when the actual validator is stricter or looser than the type
- Missing envelope fields (`version`, `schemaVersion`, `sentAt`) by only diffing the `data` object — envelope drift is a top rollout-window hazard
- Inferring the contract when a live payload was obtainable, and not marking it `inferred`
- Treating a conditionally-emitted sender field as "always present"
