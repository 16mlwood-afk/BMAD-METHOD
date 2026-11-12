---
name: webhook-contract-charter
contract_version: 1
description: 'Contract of record for every webhook boundary across BMAD-managed projects. Codifies sender/receiver duties, the sender-strict / receiver-lenient rollout-order rule, the breaking-change taxonomy, fail-loud / no-silent-fallback at the boundary, ambiguity ownership, and a per-boundary contract template. `webhook-contract-check` verifies against it; `quick-spec` / `quick-dev` consult it before changing emission or validation code.'
---

# Webhook Contract Charter

**Why this exists.** A webhook is the one place where "my tests pass" proves nothing. The sender's suite is green against the sender's idea of the payload; the receiver's suite is green against the receiver's idea of it; and the wire between them can already be broken, or one deploy away from breaking. The discipline that keeps two services honest across that gap was, until now, tribal knowledge spread across one workflow's enforcement rules, a project memory, and a schema registry. This document writes it down once, declaratively, so every boundary is held to the same standard everywhere.

This charter is the declarative sibling of `verify/webhook-contract-check`: that workflow *enforces* the contract field-by-field across a live boundary; this document *is* the contract it judges against. Both live in top-level `workflows/shared/` because webhook boundaries are universal in scope — the same way `deployment-to-prod` and `delivery-to-main` are.

**Status — contract of record.** This is the standard `webhook-contract-check` verifies against, and the document `quick-spec` / `quick-dev` must consult **before** writing code that emits, changes, or consumes a webhook payload. When a per-boundary contract and this charter disagree, the charter wins unless the boundary contract explicitly overrides a named clause (see Per-boundary contract → Overrides).

---

## The model — what a webhook actually is

**A webhook is two deploys joined by an envelope, on different clocks.** Sender and receiver live in different repos, ship on different cadences, and neither can assume the other has deployed. Every rule below falls out of that one fact. A field mismatch is the obvious failure. The subtler failure is a *perfectly correct* change that lands on the wire before the other side can tolerate it — correct in steady state, broken during the rollout window.

Two roles, named explicitly in every boundary:

- **SENDER** — the code that emits the payload (a function, a job, a service POSTing to an endpoint).
- **RECEIVER** — the code that validates and consumes the payload (the endpoint handler and its schema/validator).

A boundary is the ordered pair `(sender → receiver)`. Contracts are per-pair, never per-app: the same app can be a strict sender on one boundary and a lenient receiver on another.

---

## Sender duties

1. **Emit the canonical shape, exactly.** Name, casing, type, and shape match the contract. `camelCase` ≠ `snake_case`; `number` ≠ numeric string; ISO-8601 string ≠ `Date`; `[]` ≠ `null` ≠ omitted. "Looks similar" is a contract bug.
2. **Keep emitting a field for as long as any receiver still requires it.** You do not get to stop sending a required field because *your* code no longer needs it. Removal is a receiver-led, multi-deploy dance (see Rollout order).
3. **Add new fields as additive only.** A new field is optional on arrival. Never make a freshly-added field required in the same change that introduces it.
4. **Never weaken a value silently.** Don't start sending `null`, `""`, a sentinel, or a coerced default where a real value was promised. If the real value is genuinely unavailable, that is a sender-side defect to fix or a contract change to negotiate — not a quiet downgrade.
5. **Own your enum.** Adding an enum value is a breaking change for a strict receiver. Widen the receiver first (see Rollout order).

## Receiver duties

1. **Be lenient about what you don't know.** Ignore unknown fields; never reject a payload for carrying a field you haven't met. Leniency is what lets the sender evolve without coordinating a synchronized deploy.
2. **Be strict about what you require — and require as little as possible.** Validate the fields you actually consume. Every field you mark *required* is a chain you've welded to the sender's release schedule.
3. **Fail loud at the boundary on a broken canonical field — never silently fall back.** If a field the contract calls canonical arrives missing, malformed, or wrongly typed, reject or alert at the edge. Do **not** paper over it with a default, a guess, or a downstream coalesce. A silent fallback turns a loud, fixable contract violation into quiet data rot that surfaces weeks later three systems away. (This is the boundary form of the project-wide no-silent-fallbacks rule.)
4. **Tolerate before the sender emits.** Ship leniency for a new field *before* the sender starts sending it, so the change is safe in either deploy order.
5. **Treat absence and emptiness as distinct.** A missing field, an explicit `null`, and an empty collection mean different things. Decide which the contract allows and validate accordingly; don't conflate them.

---

## Rollout order — the rule that makes two clocks safe

The window between the two deploys is where correct changes go wrong. The invariant is **sender-strict / receiver-lenient**: at every instant of a rollout, the payload on the wire is one the *currently deployed* receiver can accept.

- **Adding a field** → **receiver first.** Ship the receiver's leniency/optional-acceptance, deploy it, *then* let the sender emit. (Sender-first is only safe if the receiver was already lenient to unknowns — which duty R1 requires, so additive fields are usually safe either way. Tightening the new field to required is a *separate, later* change.)
- **Removing a field** → **sender last.** Drop the receiver's requirement, deploy it, *then* stop emitting. A sender that removes a field the live receiver still requires breaks production the moment it deploys.
- **Renaming a field** = add-new + remove-old. Emit both names through the window; migrate the receiver to the new name; then drop the old. Never an atomic rename across the boundary.
- **Changing a type or an enum domain** → widen the receiver first (accept old ∪ new), migrate the sender, then narrow the receiver. Never narrow before the sender has stopped producing the old form.

The test for any change: *"If exactly one side deploys this and the other is still on the old code — in either order — does the live payload still validate?"* If no, the change is **rollout-unsafe** and must be split into ordered steps.

## Breaking-change taxonomy

| Change | Class | Safe if… |
| --- | --- | --- |
| Add optional field | rollout-safe | receiver is lenient to unknowns (R1) |
| Make existing field required (receiver) | rollout-unsafe-addition | sender already emits it for 100% of payloads |
| Remove field | rollout-unsafe-removal | receiver dropped the requirement first |
| Rename field | unsafe | run as add-then-remove through a dual-emit window |
| Tighten type / narrow enum (receiver) | unsafe | sender already constrained to the narrower domain |
| Widen type / add enum value (sender) | unsafe for a strict receiver | receiver widened to accept it first |
| Change casing/format of an existing field | unsafe | treat as rename |

"Breaking" is judged **against the currently-deployed other side**, not against the other side's `main`. Two green branches can still encode a breaking change.

---

## Ambiguity ownership

When the contract is silent or unclear, **the receiver does not get to invent a meaning and proceed.** Underspecified input is a contract gap to close, not a default to fabricate. The sender owns producing a well-formed value; the receiver owns rejecting a malformed one loudly. Neither side owns "quietly making it work." Ambiguity is resolved by amending the contract, not by either side guessing.

## Versioning & deprecation etiquette

- **The canonical schema is the source of truth, and it has one home.** Where the codebase has a schema registry (e.g. an MCP schema server), the canonical payload schema lives there and both sides validate against it. A change to the canonical schema and the two sides' copies land together or not at all.
- **Deprecate with a window, not a cliff.** Announce a field's removal, keep emitting through the agreed window, then remove sender-last. No silent removals.
- **Version the envelope, not every field.** Bump a payload/version discriminator only for changes that can't be made rollout-safe by the ordering rules above. Most field additions need no version bump — that's what leniency is for.

---

## Per-boundary contract — the template

Each live boundary records its own contract inheriting this charter. Keep it short; the charter carries the rules, the contract carries the *specifics*. Store it where the boundary's enforcement runs (next to the receiver, or in the schema registry).

```markdown
# Webhook Contract: <sender> → <receiver>

**Inherits:** webhook-contract-charter.md (all clauses unless overridden below)
**Canonical schema:** <path / schema-registry key>   **Envelope version:** <vN>
**Sender:** <repo · emission site>   **Receiver:** <repo · endpoint + validator>

## Fields
| field | type | required | notes / enum domain |
| --- | --- | --- | --- |
| ... | ... | sender-always / receiver-requires / optional | ... |

## Overrides (charter clauses this boundary changes, with rationale)
- <none, or e.g. "R3: malformed `x` is tolerated and logged, not rejected — because …">

## Open contract gaps
- <ambiguities awaiting resolution — never resolved by a silent default>
```

---

## How this is enforced

- **`verify/webhook-contract-check`** is the enforcer. It walks the live payload field-by-field against the per-boundary contract (or, absent one, against this charter's rules), assigns each field a match verdict **and** a rollout-safety class, and routes every finding to the owning side via `quick-spec`. It never edits across the boundary. This charter is the standard it judges against.
- **`implement/quick-spec` / `implement/quick-dev`** consult the relevant per-boundary contract and this charter *before* changing emission or validation code, and split any rollout-unsafe change into the ordered steps above.
- **A field reported on neither side is a defect, not a default.** Every field on either side gets an explicit disposition — matched, mismatched, sender-only, receiver-only — with a rollout-safety class. Silence is never a pass.
