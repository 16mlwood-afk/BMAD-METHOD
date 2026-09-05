---
type: schema-spec
status: draft-stable-for-wiring
name: operator-operational-profile
target-file: "docs/<operator>-operational-profile.md (project-local, one per operator)"
consumed-by: operator-domain-pass
created: 2026-07-18
version: 0.2
source: "ratified owner paste-backs 2026-07-18; clerk vocabulary from clerk-receive-grade workflow audit (2026-06-29) + clerk-web-mode doctrine"
---

# docs/<operator>-operational-profile.md — Schema + Example (stable-for-wiring)

**What this is:** the project-local, human-maintained source of truth `operator-domain-pass` selects
from — the operator analogue of `finance-presentation` for finance vocabulary. One file per operator.
This document is **schema + partial example**, not a fully-populated profile (the complete clerk
profile is authored in Step 4 validation).

The authored sections map **1:1** onto the pass's output keys. `operator_role` and `trust_boundary`
are top-level and match the outputs verbatim; `must_not_infer` and `ordering_invariants` are
explicit top-level lists that map 1:1 to the corresponding output fields and are **never mixed into
`forbidden_asks`**. The per-decision fields are authored under `decision_points` and the skill
derives the named per-decision output keys from them (mapping table below).

## Frontmatter (required)
```yaml
---
type: operator-operational-profile
operator_id: warehouse-clerk            # matches the <operator> the pass resolves
domain: cash-recovery
role_summary: "Paid third-party warehouse clerk who receives, grades, and photographs FBA-return units at a bench terminal with a hardware scanner."
trust_class: third-party-non-owner      # third-party-non-owner | owner | internal-staff
last_updated: 2026-07-18
version: 1
source: "clerk-receive-grade workflow audit (2026-06-29) + clerk-web-mode doctrine"
---
```

## Profile → output mapping (how the skill derives its keys)
| Profile (authored) | Skill output key | Derivation |
|---|---|---|
| `operator_role` (section) | `operator_role` | verbatim |
| `trust_boundary.may_decide/may_not_decide/write_trust` | `trust_boundary` | verbatim object |
| `decision_points[].decision` | `operator_decides` | the `decision` string of each entry |
| `decision_points[].known_before_ask` | `known_before_each_ask` | per decision |
| `decision_points[].evidence_required` | `evidence_required` | per decision |
| `decision_points[].forbidden_asks` | `forbidden_asks` | per decision |
| `must_not_infer` (top-level list) | `must_not_infer` | 1:1, top-level (never folded into forbidden_asks) |
| `ordering_invariants` (top-level list) | `ordering_invariants` | 1:1, top-level |

## Required sections

### 1. `operator_role` → output `operator_role`
Prose: who the operator is, employment/trust relationship, expertise, frequency, operating environment.
> *Example:* "A paid third party, never the business owner. Expert at physical handling and scanning;
> **not** assumed to know the data model, ASINs, or recovery economics. High-frequency, keyboard-first,
> at a shared bench terminal + hardware scanner (desktop browser)."

### 2. `trust_boundary` → output `trust_boundary`
```yaml
trust_boundary:
  may_decide:
    - "confirm the physical condition/grade of a unit against a rubric"
    - "capture required condition photos"
    - "bind a scanned unit to the shipment/session the system already matched"
  may_not_decide:
    - "approve a recovery route (resale vs reimbursement) — owner-gated"
    - "file a reimbursement claim — owner-gated"
    - "assign product identity to an unresolved unit without explicit provenance"
  write_trust: "Clerk writes are physical observations, verifiable against expected shipment contents; they are not authoritative identity or economic decisions."
```

### 3. `decision_points` → outputs `operator_decides` / `known_before_each_ask` / `evidence_required` / `forbidden_asks`
One entry per per-item decision the operator owns. Authored key `decision` becomes `operator_decides`;
the three lists are carried per decision (alignment the validation gate depends on).
```yaml
decision_points:
  - decision: "confirm this unit's identity matches an expected item"
    known_before_ask:
      - "the matched shipment/session and its expected contents (from ingestion)"
      - "any prior enrichment for the scanned LPN/FNSKU (ASIN, product name, image)"
    evidence_required:
      - "expected-vs-scanned reconciliation panel (what the system expected here)"
      - "product thumbnail + title resolved from the identifier"
    forbidden_asks:
      - "do NOT ask the clerk to type an ASIN/identifier the scan already resolves"
      - "do NOT ask for identity before showing expected contents"
  - decision: "grade the unit's condition"
    known_before_ask:
      - "the confirmed product identity + its grading rubric/presets"
    evidence_required:
      - "condition rubric/presets on-screen; the captured photos"
    forbidden_asks:
      - "do NOT ask for a grade before identity is confirmed and photos are captured"
```

### 4. `must_not_infer` (top-level list) → output `must_not_infer`
Explicit top-level list; **not** nested inside any decision and **not** mixed into `forbidden_asks`.
```yaml
must_not_infer:
  - "never guess product identity from an LPN alone — flag unresolved, don't fabricate"
  - "never assume the clerk knows the ASIN, recovery value, or claim eligibility"
  - "never treat a clerk observation as an owner approval"
```

### 5. `ordering_invariants` (top-level list) → output `ordering_invariants`
Explicit top-level list; the invariants the validation gate checks the decision definitions against.
```yaml
ordering_invariants:
  - "expected-contents-first: show what the system expects before asking anything"
  - "identity-before-identifier: resolve/confirm identity before requesting any identifier the operator would type"
  - "evidence-before-input: every decision's evidence is on-screen before its commit control is reachable"
```

## Authoring notes
- Keep this file **schema + example** at spec stage; the complete clerk profile is authored in Step 4
  (validation), when the clerk cockpit is rebuilt through `design-router → design-handoff` and the
  brief is confirmed to preserve the three ordering invariants.
- `forbidden_asks` (per decision) and `must_not_infer` (global) are **distinct**: the first bans a
  UI ask at a decision point; the second bans a fact the design/pass may not infer anywhere. Do not
  collapse them.
- One profile per operator; a second operator (grading-bench, claim-filer, VAT-filer) gets its own
  `docs/<operator>-operational-profile.md` with the same section structure.
