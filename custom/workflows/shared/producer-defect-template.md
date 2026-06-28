---
name: producer-defect-template
contract_version: 1
description: 'Canonical format for an EXTERNAL-producer defect report — the artifact an audit emits when a detected defect originates in a producer that lives in another repo/service/team (the bison-ops scraper extension, the accounting app), which the consuming project can detect+route but not fix at source. Judged against `webhook-contract-charter.md` (the clause source). Emitted by the `external:<producer_id>` branch of `data-quality-audit`, `scrape-coverage-audit`, and `webhook-contract-check` step-04; harvested deterministically per the §"Deterministic harvest" guideline. This is the cross-repo sibling of the in-repo producer-fix lane: in-repo data rot routes to quick-spec/quick-dev; external producer defects route HERE.'
---

# Producer-Defect Report — Canonical Format

**Why this exists.** A consuming project (inventory-manager, accounting-tools, …) routinely *detects* a data defect whose root cause is in a producer it does not own — the bison-ops Chrome-extension scraper, the accounting app, any sender across a webhook boundary. The existing audits route in-repo data rot to the producer-fix lane (`quick-spec` → `quick-dev`) — but that lane assumes the producing code is *here*. When the producer is **another repo/service/team**, there is nothing to `quick-spec`; the consumer can only file a defect upstream and harden its own boundary. Until now that filing was **probabilistic** (a human noticing a log), **one-off** (each defect got an ad-hoc narrative), and **unenforced**. This format makes the external-producer report a first-class, fixed-shape, never-dropped artifact — the same detect-and-route discipline the audits already apply, extended across the repo boundary.

This document is a **template + registry**, not a workflow. It is judged against `webhook-contract-charter.md`: a producer defect IS a charter violation (a sender weakening a value, emitting a non-canonical shape, or the receiver silently coalescing it). The charter is the clause source; this artifact cites it.

---

## When an audit emits this (the `external:*` branch)

An audit's step-04 classifies each routed finding's `producer_fix_lane`:

- **`internal`** — the producing code (extractor / importer / sync / normalizer) lives in THIS repo → the existing in-repo producer-fix lane (`quick-spec` → `quick-dev`), framed under the data-quality root-cause rule. Unchanged.
- **`external:<producer_id>`** — the root producer lives in another repo/service/team (look it up in the §Producer registry below). This is a **HARD never-drop branch**: it MUST NOT route to in-repo `quick-spec`, and it MUST emit (create-or-update) the producer-defect report defined here. A finding classified `external:*` with no producer-defect artifact is a silent drop — the exact failure the routing boundary exists to prevent.

The audit still **stops at the routing boundary** — it files the report and names the upstream owner; it never edits the producer's repo (it cannot) and never silently coalesces the bad value in the consumer (that would be the charter's silent-fallback violation rebranded as a "fix").

---

## The report — `producer-defect-{producer}-{YYYY-MM-DD}.md`

Written to `{implementation_artifacts}/`. One file per `(producer, day)`; **a same-day re-detection UPDATES the file** (append evidence row, refresh blast radius) rather than spawning a new one — this is what makes the deterministic harvest idempotent. Fixed structure (every section required; mark `n/a` with a reason rather than omit):

```markdown
---
type: producer-defect
producer_id: <e.g. bison-ops>            # MUST match a §Producer registry key
producer_repo: <repo/service URL or path>
boundary: <sender → receiver pair, e.g. bison-ops → inventory-manager/orders-webhook>
detected_by: <audit slug + run date, e.g. data-quality-audit · grand_total · 2026-06-28>
charter_clauses: [<e.g. "Sender §4 never-weaken-silently", "Receiver §3 fail-loud">]
severity: <P1 | P2 | P3>
status: open                              # open | acknowledged | fixed-upstream | wontfix
first_seen: <YYYY-MM-DD>
last_seen: <YYYY-MM-DD>
---

## 1. Producer
<id, repo/service, and the boundary — which sender→receiver pair.>

## 2. Violated charter clause(s)
<Cite webhook-contract-charter.md by clause, verbatim where it bites. The defect is
defined as a charter violation; if no clause fits, the finding is not a producer
defect — re-classify.>

## 3. Evidence
<The signal that triggered this: the exact log line (e.g. detectEconomicsDivergence
"box-rows disagree on grand_total — economics divergence at source"), the offending
records/values, counts, a reproduction. Concrete and copy-pasteable for the upstream
team. Append a dated row on each re-detection.>

## 4. Blast radius / severity
<How many records / which surfaces are affected, what the consumer is forced to do
about it today (e.g. "spend page picks max() of the divergent totals"), and why the
severity. Refresh on update.>

## 5. Proposed contract change or fix
<What the PRODUCER must change to stop violating the charter — stated as a contract
change, not a consumer patch. Name the rollout order if the change is breaking
(charter §Rollout order). If the consumer must also harden its boundary (fail-loud
instead of silent coalesce), name that as a SEPARATE in-repo follow-up — it is not
the producer's fix.>

## 6. Contact / owner
<From the §Producer registry: who owns the producer repo, how this is filed
(issue tracker URL / channel), and the consumer-side owner tracking it.>
```

**Consumer-side harden is a separate lane.** A producer defect often has a twin in-repo follow-up: the receiver should *fail loud at the boundary* instead of silently coalescing the bad value (charter Receiver §3). That follow-up is real `quick-spec`/`quick-dev` work in THIS repo and is filed as such — it does NOT substitute for the producer report, and the producer report does NOT substitute for it. Both, never one.

---

## Producer registry

The lookup the `external:*` branch resolves `producer_id` against. A producer not listed here cannot be routed `external:*` until it is added (add it, don't guess an owner). Project-specific entries may extend this in the consuming project; these are the shared, known cross-repo producers.

| producer_id | repo / service | role on the boundary | owner / how to file |
|---|---|---|---|
| `bison-ops` | bison-ops Chrome extension (separate repo) | SENDER → inventory-manager order webhook | <extension repo owner · issue tracker> |
| `accounting-app` | accounting app (separate service) | SENDER → inventory-manager accounting webhook/pull | <accounting service owner · issue tracker> |

> Owner/tracker cells are placeholders to fill per environment — the registry's job is to make "where does this get filed" a lookup, not a per-defect decision. An unfilled owner is itself a gap to close, not a reason to drop the finding.

---

## Deterministic harvest (guideline — instance is per-project, gated by enforcement-expert)

Filing must not depend on a human noticing a log. The fork carries this **guideline**; each consuming project wires the **instance**, and because it is an enforcement mechanism it is designed through the `enforcement-expert` gate (deterministic tier — the harness/tooling creates the report; the model cannot forget) BEFORE it is authored. The guideline:

- **Source the signal structurally.** A producer defect already surfaces as a structured in-app event — the `detectEconomicsDivergence` warning, a `webhook-contract-check` failure, a normalizer fall-through. The harvest reads those events, not free prose.
- **Always upsert, never notify-and-hope.** On each qualifying event the harvest creates-or-updates `producer-defect-{producer}-{date}.md` (append evidence, refresh blast radius), keyed on `(producer_id, day)`. Idempotent by construction.
- **The deterministic tier is the point.** A guideline that says "the agent should file a report when it sees divergence" is probabilistic and fails the same way the old practice did. The instance must be a job/hook the runtime fires (e.g. a structured-log consumer, a scheduled sweep over the divergence events, or a CI check on the boundary), so the report exists whether or not anyone is watching. `enforcement-expert` picks the primitive and placement per project.

---

## Worked example — bison-ops grand_total divergence

- **Detect:** inventory-manager's import pipeline logs `detectEconomicsDivergence` — order `306-1457926` carries box-rows with two order totals (2497.78 and 3001.44); it logs and stores both, never reconciling.
- **Classify:** the producing code is the bison-ops scraper extension (a separate repo) → `producer_fix_lane = external:bison-ops`.
- **Charter clause:** Sender §4 *"never weaken a value silently … a sender-side defect to fix or a contract change to negotiate, not a quiet downgrade"* — the scraper emits an order-level field with per-box-divergent values. Twin: Receiver §3 *"fail loud … never silently fall back"* — the consumer currently picks `max()`, a silent coalesce.
- **Emit:** `producer-defect-bison-ops-2026-06-28.md` — producer `bison-ops`; clause `Sender §4` + `Receiver §3`; evidence the divergence log + the two totals + the affected-order count; blast radius "ambiguous order total → spend totals pick max()"; proposed fix "scraper must emit one canonical order-level `grandTotal` per order (charter §1 canonical shape), or the boundary contract must define which row is authoritative"; owner the extension repo.
- **Twin in-repo follow-up (separate):** harden the receiver to flag/reject divergent totals at the boundary instead of `max()`-coalescing — filed as `quick-spec` in inventory-manager.
