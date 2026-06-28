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
finance_value: <true | false>            # true = changes interpretation of scraped MONEY (totals/fees/tax/refunds) → §7 gate applies
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

## 7. Site verification  (REQUIRED for finance-critical defects)
<For any defect that changes the interpretation of scraped MONEY values (order
totals, fees, taxes, refunds), the producer's new rule MUST be validated against
the live external site as the source of truth — NOT internal expectation
("max vs min") — on a 3–10 order sample, before status moves off `open`.
Tool: Claude in Chrome (see `tool-registry.md` → "Claude in Chrome"). One row per
order; mark unverifiable orders `n/a` with the reason (e.g. marketplace not
logged in). For non-finance defects, write `n/a — not a finance-value defect`.>

| order | site total (source of truth) | producer emitted | match? | note / evidence ref |
|---|---|---|---|---|
| <id> | <amount> | <amount> | yes/no | <DOM/screenshot ref, or `n/a — <reason>`> |

## 8. Linked issues
<Cross-repo discovery without automation — link the tracker tickets on BOTH sides,
so a session living mostly in one repo can find this report from its own tracker
and click through for the full context:
- Producer repo: <issue/PR URL(s) in the producing repo, e.g. bison-ops>
- Receiver repo: <issue/PR URL(s) in this repo>
Write `none yet` rather than omitting — an unlinked report is a visible gap, not a
blank. Start using it even before any bot wiring exists.>
```

> **§7 is the proof-marker, not just documentation.** A finance defect must not be
> marked resolved on internal reasoning alone — `max()` shipped precisely because no
> one checked the site. The honest enforcement (per the `enforcement-expert` gate) is
> a DETERMINISTIC check in the receiver repo (CI / pre-commit on `docs/producer-defects/`)
> that blocks a finance defect from leaving `open` until §7 is populated with ≥3 orders
> each carrying a match verdict. That gate ships on the receiver's CI track, NOT via this
> synced template — authoring §7 here is the awareness tier; it does not deploy the gate.
>
> **Built (first instance):** inbound-flow ships this gate as
> `scripts/check-producer-defect-verification.ts`, wired into `.githooks/pre-push` +
> a PR CI workflow. It keys off the `finance_value: true` frontmatter field above
> (conservative — only explicitly-marked finance defects are gate-eligible; `open`/
> `wontfix` never fire), and a `verification_override: "<reason/PR#>"` frontmatter line
> is the logged escape hatch (passes the gate, surfaced loudly + in the committed diff).
> A defect that *looks* finance-value but has no `finance_value` field gets a soft warn
> to classify it. Other receiver repos replicate the same script + field convention.

**Consumer-side harden is a separate lane.** A producer defect often has a twin in-repo follow-up: the receiver should *fail loud at the boundary* instead of silently coalescing the bad value (charter Receiver §3). That follow-up is real `quick-spec`/`quick-dev` work in THIS repo and is filed as such — it does NOT substitute for the producer report, and the producer report does NOT substitute for it. Both, never one.

---

## Producer registry

The lookup the `external:*` branch resolves `producer_id` against. A producer not listed here cannot be routed `external:*` until it is added (add it, don't guess an owner). Project-specific entries may extend this in the consuming project; these are the shared, known cross-repo producers.

| producer_id | repo / service | role on the boundary | delivery_channel | report_location | owner / how_to_file |
|---|---|---|---|---|---|
| `bison-ops` | bison-ops Chrome extension (separate repo) | SENDER → inventory-manager order webhook | `pull-from-receiver` | `inbound-flow:docs/producer-defects/` | bison.management (sales@bison.management) · pull weekly |
| `accounting-app` | accounting app (separate service) | SENDER → inventory-manager accounting webhook/pull | `pull-from-receiver` | `<receiver>:docs/producer-defects/` | <accounting service owner · pull cadence> |

> Owner/cadence cells are placeholders to fill per environment — the registry's job is to make "where does this get filed and who reads it" a lookup, not a per-defect decision. An unfilled owner is itself a gap to close, not a reason to drop the finding. `delivery_channel` is one of the four in §Delivery seam; `report_location` is the committed path the producer pulls from.

---

## Delivery seam — getting the report to a producer in another repo

The report is filed in the **receiver's** tree (the consuming project's committed `docs/producer-defects/`). The producer lives in **another repo/team**, so "filed" and "delivered" are two different things. This section names the delivery channels and the default.

**Why pull, not push, is the default.** The receiver cannot reliably *push* across a repo boundary without write access to a repo it does not own — that is a cross-team auth grant and an ownership decision, not a mechanical default. Pulling inverts the burden: the producer reads its reports from a stable, documented location using *its own* access. So unless a team has deliberately wired push, the seam is a **pull contract**.

**`delivery_channel` — the four options (registry field):**

- **`pull-from-receiver`** (DEFAULT) — the receiver commits the report to `report_location` (its own `docs/producer-defects/`); the producer team/terminal pulls from that path on its cadence. No receiver→producer auth, no automation. This is the whole seam for most boundaries: a documented location + a named owner + a cadence.
- **`pr-into-producer`** — the receiver opens a PR/issue **in the producer's repo** carrying the report. Delivers actively, but requires a token with write/issue access to that repo (an explicit cross-team grant) and couples the receiver to the producer's repo shape. Any automation here is an enforcement mechanism → design it through the `enforcement-expert` gate (deterministic vs probabilistic) before building.
- **`tracker`** — the report is filed to a shared incident board / issue tracker with an SLA. Good for accountability once volume justifies it; depends on tracker infra + integration auth.
- **`manual`** — a human hand-carries the committed path/link to the producer. The `pull-from-receiver` contract without the producer auto-pulling; fine as a starting point.

**Escalation, not exclusivity.** Start at `pull-from-receiver`. Escalate to `pr-into-producer` or `tracker` only when pull proves too passive (the producer demonstrably isn't reading) — and only with the auth/ownership decision made explicitly. Downgrading is always safe; upgrading carries a cross-team cost.

**What's the USER's call (not mechanical):** who owns each producer and their pull cadence (fills the registry), and whether to ever grant push access / stand up a tracker. The fork supplies the contract and the registry shape; the cross-team process is the owner's to set.

---

## Ownership per layer (fork vs project)

Where a new rule or doc belongs, so another directory knows where to go:

- **The fork owns** the shared, cross-project contracts: the tool registry, THIS
  producer-defect template + registry + delivery seam, the `webhook-contract-charter`,
  and workflow/policy rules. A new tool or a cross-project rule → propose it in the
  fork (`~/bmad-method-v6/custom/workflows/shared/`); it syncs to every project.
- **Each project owns** its domain specifics: the concrete defect briefs
  (`docs/producer-defects/`), domain runbooks and financial invariants
  (`docs/financial-invariants/`), and the IMPLEMENTATION of the per-project
  instances this template only describes as guidelines — the deterministic harvest
  hook, the fail-loud receiver behaviour, the §7 site-verification CI gate. A new
  domain invariant → write a project doc, don't put it in the fork.

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
