<!--
  DRAFT working note — greenfield policy→schema-requirements derivation.
  Status: v0.1, unproven. Authored 2026-06-16 to close the schema-rework loop
  the greenfield dry-run surfaced: the design-policy first enters at design-handoff
  (step 7), but the data-bearing rules need to reach create-architecture (step 5),
  so a greenfield schema gets built blind and the design lane catches the violation
  late. This step carries the data-bearing constraints FORWARD to architecture.
  Companion to GREENFIELD-BRIEF-DERIVATION.md and GREENFIELD-BOOTSTRAP-RUNBOOK.md.
  House style mirrors the brief-derivation note. NOT synced.
-->

# Greenfield: Policy → Schema-Requirements Contract

**What this is.** A thin step that runs **before `create-architecture`** in the
greenfield spine. It reads the project's `docs/design-policy.md`, extracts the
**data-bearing** rules (the ones that imply *persisted columns*, not just visual
treatment), and emits a small **Schema Requirements** doc that `create-architecture`
consumes as an input alongside the PRD.

**Why it exists.** The greenfield dry-run showed the failure precisely: the policy
first actually enters at `design-handoff` (step 7), but the data-bearing rules
needed to land at `create-architecture` (step 5). Without this step you build the
schema blind, then the design lane discovers at handoff that the schema *structurally
cannot satisfy the policy* (e.g. a money figure with no VAT-basis column, an
API value with no raw-exchange storage) — and you redo architecture + stories. This
step collapses that loop by carrying the constraints forward two steps.

**The key property — `create-architecture` stays UNFORKED.** This does not modify
the upstream canonical workflow. It produces an *input doc* that `create-architecture`
reads the same way it reads the PRD. The policy-reading logic lives here, in one
fork-owned step, so the fork's upstream-reconciliation surface does not grow.

---

## Single source of truth

The data-bearing rules live **only** in the design policy (they are in no PRD or
requirements template). This step reads them from that one home and hands them to
architecture — it does **not** ask the PRD author to re-derive them as NFRs, which
would duplicate the rules and let policy and PRD drift apart. (That drift is the
same class of problem as the cross-project policy divergence; don't recreate it here.)

---

## Preconditions

1. `docs/design-policy.md` exists (greenfield runbook INSERTION 1 ran).
2. `create-ux-design` has produced the page/entity inventory (tells you *which*
   entities the data-bearing rules apply to).
3. `create-architecture` has **not** run yet.

---

## What counts as a "data-bearing" rule

Project policies differ (each project owns its own — do NOT import another project's
section numbers). So identify by **rule class, not section number**: any policy rule
that mandates a value be *displayed with a property that can only come from stored
data*. The recurring classes:

| Rule class | Signal in the policy | Schema columns it implies |
|---|---|---|
| **Provenance / external exchange** | "show `via <API>` / `Snapshot today` + raw request/response disclosure" | `source_tag`, `fetched_at`, `raw_request`, `raw_response`, `exchange_status` |
| **Relational coherence (linked records)** | "an on-screen value that IS a foreign record must expand in context" | the foreign-key column + the related lookup fields reachable through it |
| **Money basis-completeness** | "every figure declares VAT basis; foreign currency framed against the reporting currency; link to the canonical order" | `vat_basis`, `amount_native`, `currency`, `exchange_rate`, `sourcing_lane`, `<source>_order_id` (FK) |

Where the policy has been **altitude-tagged** (the `architecture-bearing` marker, if
that tagging exists), use the tags directly. Until then, scan by the classes above
plus any rule cross-referenced as a `§12`-style contract-critical assertion that
implies persisted data.

---

## Procedure

1. Check preconditions; HALT to INSERTION 1 if no policy.
2. Read `docs/design-policy.md`. For each rule matching a data-bearing class,
   record: the rule, the entities it touches (from the §-text + the UX entity
   inventory), and the columns it implies.
3. Emit a **Schema Requirements (policy-derived)** doc — per entity, the required
   columns + the policy rule each one satisfies (traceability). Keep it to fields;
   no types/migrations (that's `create-architecture`'s job).
4. Pass it to `create-architecture` as an explicit input alongside the PRD.

### Output shape

```markdown
# Schema Requirements (policy-derived) — <project>
Source: docs/design-policy.md vNN · derived <date>

## <Entity> (e.g. RefundClaim)
- vat_basis            ← §15 money basis-completeness
- amount_native, currency, exchange_rate, sourcing_lane ← §15 foreign-currency framing
- source_order_id (FK) ← §13 linked record + §15 link-to-canonical-order
- source_tag, fetched_at, raw_request, raw_response ← §7 provenance/raw-exchange
```

---

## Self-check (Mode 1 on this note)

- ✅ Keeps `create-architecture` unforked — emits an input, not a patch.
- ✅ Single-source-of-truth — reads constraints from the policy, no PRD duplication.
- ✅ Project-agnostic — classifies by rule class, never hardcodes one project's §-numbers.
- ⚠️ Until the policy carries altitude tags, rule-class detection is heuristic; the
  altitude-tagging task (deferred — it edits the project policy and must coordinate
  with live policy sessions) would make this deterministic.

## Codification target

If a real greenfield run proves this out, fold it into the `design-handoff`
greenfield branch as a pre-architecture sub-step, or keep it as a standalone
runbook step. Don't build a synced workflow until a real project validates it.
