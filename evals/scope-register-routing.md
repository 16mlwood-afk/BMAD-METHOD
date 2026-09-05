---
name: eval-scope-register-routing
description: Golden suite for STD-SCOPEREG-001. Measures the axis the linter deliberately cedes — whether a scope item is routed to the CORRECT route, with the route-appropriate next artifact. Replay on any change to scope-register-routing.md §3.
---

# Golden suite — scope-register routing (STD-SCOPEREG-001)

**What this measures, and why it exists.** `tools/check-scope-register.js` can prove a row *has* a
route and a shape-appropriate `next_artifact`. It cannot prove the route is **right** — a row
claiming `R2-bounded-local` with a quick-spec path passes the linter even if the item was really
`R1-capability`. Faking that check inside the linter would be the indiscriminate-detector
anti-pattern, so §8 cedes the axis here and measures it instead.

**Method.** Present the case's item text + evidence ONLY (never the expected route). Score three
things independently:

| Axis | Pass condition |
|---|---|
| **route** | exact match on the expected route |
| **next_artifact** | names the route-appropriate SHAPED artifact (§4) — not a workflow name, not an epic, not the proposal |
| **actionability** | does not describe a REGISTERED / PROPOSED / DESCRIBED artifact as actionable |

A case is **true** only if all three pass. Record the run as `N/9` per axis and overall.

**Provenance.** All nine cases are real rows from the cash-recovery register
(`_bmad-output/planning-artifacts/scope-register.md`) as they stood on 2026-07-25, chosen because
they route *differently* under §3 and because five of them are the exact shapes that were previously
mis-routed or left unrouted. Cases 6–9 are the hard ones: each is a near-miss for a route it must
NOT take.

---

## Case 1 — R1-capability (the clean capability)

**Item.** Ingest a ~6–7 photo BUNDLE per unit through the backend to clear a ~300-unit standing
backlog. Owner shoots on a phone; bundles must be resolved to Units, mapped to manifest slots, and
coverage-checked. Requires a new persisted bundle/import-batch grouping and a new intake entry
point. R2 photo storage is already live; the unit population comes from reports already ingested.

- **Expected route:** `R1-capability`
- **Expected next_artifact:** the first STORY FILE at `ready-for-dev` (e.g. the coverage-report
  slice), NOT `epics.md ## Epic 10` and NOT the sprint-change-proposal
- **Trap:** PREMISE-CHECK is satisfiable in the *wrong* direction — "R2 + SP-API already ingested"
  tempts a downgrade to R3. It is still R1 because of the **new persisted grouping + new intake
  entry point**, which is a structural model change.
- *(Real row: SR-23.)*

## Case 2 — R2-bounded-local (materiality clause)

**Item.** Receive-station scan tokens are routed **by position** (tracking → lpn → fnsku) rather
than by token type. Add a pure, offline `classifyScanToken` + a `ScanTokenType` enum so routing is
by type; ASIN vs FNSKU (shape-identical) is never guessed on shape alone. No network lookup, no new
table, no schema change.

- **Expected route:** `R2-bounded-local`
- **Expected next_artifact:** the quick-spec / tech-spec file path
- **Trap:** "a new enum" reads like a persisted-model change. MATERIALITY (§3 R1 guardrail) sends a
  new enum value / bounded classifier to R2, not the capability lane.
- *(Real row: SR-15.)*

## Case 3 — R3-design (already-ingested data, presentation depth)

**Item.** Show the Amazon catalog product image to the clerk during receive, and combine it with
clerk condition photos on the eBay listing. Verified in code: SP-API Catalog Items already returns
`images`, the parser reads them, and the enrichment step already **persists** them.

- **Expected route:** `R3-design`
- **Expected next_artifact:** the ACTIVE design brief path (material revision produced by
  `design-handoff`)
- **Trap:** "add Amazon product images" sounds like a new source. PREMISE-CHECK (§3) proves we
  already ingest AND persist it → design lane, not capability lane. A `next_artifact` of "hand-edit
  the brief" must FAIL — invalid by construction (§3 R3).
- *(Real row: SR-16.)*

## Case 4 — R4-operational-milestone (the one that must not become stories)

**Item.** Prove the EXISTING per-unit pipeline once, end-to-end, on one real unit: front-door →
receive → grade → route → stage → price → offer → approve → publish to a live buyable listing.
Traced against live code and live prod data. Blocking preconditions: confirm prod object storage
accepts a real photo write; confirm marketplace credentials are set in prod; owner go for the one
irreversible partner-facing publish. Known loose hops are accepted as manual workarounds, not fixes.

- **Expected route:** `R4-operational-milestone`
- **Expected next_artifact:** the milestone-block key, e.g. `sprint-status.yaml#proving-run-resale`
- **Expected owners:** the two config confirmations `owner: operator`; the drive-to-approved-offer
  step `owner: agent`; the publish go `owner: operator`
- **Trap (the expensive one):** the three preconditions and the loose hops read like a backlog of
  build work. Converting any of them into stories is a **mis-route** — it manufactures code for a
  problem that is a config check or a physical action. Also: an answer that downgrades this to
  "not ready / backlog" because it has no story file **fails the actionability axis** (§4 — "not a
  build" is not "not ready").
- *(Real row: SR-24.)*

## Case 5 — R5-parked (complete activation)

**Item.** Flipping the dashboard to per-unit detail tables is blocked by a grain conflict: live
reimbursement recovery is aggregate-only per-claim and never attributed to a unit, whereas the
fixture's table is per-unit. Resale and inbound detail *can* go per-unit; reimbursement cannot
without a re-grain. Two forks exist: re-grain reimbursement detail to per-claim rows, or accept
mixed grain. Nothing is lost by deferring.

- **Expected route:** `R5-parked`
- **Expected next_artifact:** `—` (legal here and ONLY here)
- **Expected activation:** `owner:` the product owner · `trigger:` **an observable condition** — the
  owner wants per-item detail on the dashboard AND picks fork (a) or (b) · `why-not-now:` the
  rollups-only surface ships the live aggregate and is complete without per-item detail
- **Trap:** an answer giving a route but omitting any of the three activation parts **fails** — a
  parked row missing owner, trigger, or why-not-now is not legally parked (§3 R5).
- *(Real row: SR-04.)*

## Case 6 — R0 gateway, NOT a route (the "correct-course is a terminal" trap)

**Item.** Owner confirms the physical reality: clerks roam between pallets across multiple locations
with handheld phones, often several in parallel — they are NOT fixed at a bench. The existing
desktop-only clerk premise is **wrong on premise, not merely incomplete**, and the doctrine built on
it must be superseded.

- **Expected handling:** R0 fires first — this changes an accepted decision, so `correct-course`
  **LEADS** and supersedes the prior doctrine on the record. It is a **gateway, not a terminal**.
  The item is then re-entered into the procedure and routes `R1-capability` (it forks a new PRD FR
  and forces a new architecture decision for an offline-capable roaming shell).
- **Expected next_artifact:** the first STORY FILE — **NOT** the sprint-change-proposal
- **Trap:** the single most common failure. An answer whose `next_artifact` is the
  sprint-change-proposal **fails**: a proposal is PROPOSED, actionable for an owner *decision* only
  (§4). A row whose only artifact is the proposal is not routed — it is awaiting routing.
- *(Real row: SR-10.)*

## Case 7 — pending, `route: TBD` (the only legal absence)

**Item.** If the clerk roams with a phone, the clerk-facing expected-inbound feed is a likely fourth
mobile surface — but it is gated on an unresolved question about whether that route belongs to the
clerk shell or the owner shell. Nobody has decided the shell ownership.

- **Expected route:** `TBD` (the row is `disposition: pending`)
- **Expected next_artifact:** none required while pending
- **Expected accompanying field:** the **named decision that unblocks it** — the shell-ownership
  call
- **Trap:** defaulting an unclassified item to `R5-parked` **fails**. Parking is a positive decision
  that owes an owner, an observable trigger, and a why-not-now; it is not a place to put items
  nobody classified (§ Step 4.5 check).
- *(Real row: SR-12.)*

## Case 8 — mixed, name the LEAD

**Item.** Richer carrier data is fetched on every poll but **dropped before persistence**, so it
never reaches display, prioritisation, or claims. Two of the parsed fields are empty because they
are a paid add-on. Separately, one field introduces a new parcel *disposition* — a parcel going back
to the sender that will never arrive — which is a state-model change.

- **Expected handling:** mixed, and the answer must say so. The field-depth work is `R2-bounded-local`
  (an existing, already-ingested source gaining persisted depth — PREMISE-CHECK forbids calling it a
  new source) and it **LEADS**. The return-to-sender disposition is a **separate row** routed
  `R1-capability` (a new state-model concept), explicitly carved out so it cannot ride in on a
  field-reading change.
- **Expected next_artifact (lead row):** the quick-spec path
- **Trap:** folding both into one row **fails** — a row with two routes has no checkable next
  artifact (§3 Mixed).
- *(Real row: SR-22.)*

## Case 9 — accepted-and-shipped, but with owed reconciliation

**Item.** A coach video shipped on one photo slot under an explicit owner override of a
spend-control precondition. The controls that were held are machine-enforced by a contract test. But
the active design brief still reads "video is out of scope for THIS revision" — so the artifact now
contradicts what shipped.

- **Expected handling:** the delivered work is `done`; the **owed reconciliation is its own row**,
  routed `R3-design`.
- **Expected next_artifact:** the re-issued ACTIVE design brief (via `design-handoff`) — a
  `next_artifact` of "hand-edit the brief to remove the out-of-scope line" **fails** (material
  change; §3 R3).
- **Trap:** treating "it shipped" as closing the item. Artifact/reality drift is unrouted scope
  wearing a `done`.
- *(Real row: SR-21.)*

---

## Replay log

| Date | Runner | route | next_artifact | actionability | Overall | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | not yet replayed; suite authored 2026-07-25 alongside STD-SCOPEREG-001 v1 |

**Replay trigger:** any edit to `custom/workflows/shared/scope-register-routing.md` §3 or §4, or to
`bmad-correct-course` Step 4.5. A change to §3's ordering (R0-first) invalidates cases 6 and 8 in
particular — re-score them before claiming the change is safe.
