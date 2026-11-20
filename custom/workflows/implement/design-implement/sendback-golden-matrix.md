# Sendback golden matrix — the four rows that decide the rule

**Rule:** `workflow.md` Critical Rule *"Claude Design is the source of truth for design"* ·
`steps/step-04-apply-and-deliver.md` §5c · artefact contract `sendback-template.md`.
**Checker:** `tools/check-design-sendback.js` · **suite:** `npm run test:design-sendback` (18 cases).

**Why this file exists.** A rule nobody has tested against the case that produced it is not known to
work. These four rows are the real departures and the real deferrals from the two mapping-queue
cockpit apply ledgers (`inbound-flow`, passes of 2026-09-25 and 2026-09-26) that produced the
2026-09-26 owner ruling. Each is asserted in the suite, so the matrix cannot drift away from what
the checker actually does.

**The load-bearing calibration is G1–G3 firing while G4 stays silent.** Three departures must be
caught; four honest deferrals in the same pass must cost nothing. A rule that taxed G4 would be
switched off within a week, and then G1–G3 would go unreported too.

---

## G1 — a policy hard failure resolved by the implementer, and recorded as a win

**What the ledger said** (pass 1 §7, repeated verbatim as pass 2 §9, *"v15 beats the design again,
in the same place"*):

> *"Section labels — v15 wins over the design, and it is logged. … The current implementation uses
> `text-transform` zero times, so transcribing the design faithfully would have introduced a §5 hard
> failure into a compliant surface. **v15 wins, and this is where.**"*

Twelve section labels, `text-transform: uppercase; letter-spacing: 0.04em` in the design;
`docs/design-policy.md` §4 forbids label capitals and §5 lists all-caps section headers as a **hard
failure**. Pass 2 added it to a numbered list headed *"Where v15 beat the design"*.

| | |
|---|---|
| **Classification** | **DEPARTURE** — the surface renders sentence case where the design specifies uppercase. Something of ours is in the design's place. |
| **Why not NOT-YET-BUILT** | The labels shipped. They are just ours rather than the design's. |
| **What was right** | Not shipping the §5 hard failure. That constraint is unchanged (§2e "The boundary", step 1). |
| **What was wrong** | Recording it as a verdict. Two authorities the owner set were in conflict and the implementer resolved it — in the safe-feeling direction, which is still a resolution. |
| **New disposition** | `⊘ interim(policy-conflict: design-policy §4/§5 label case vs design) → sendback:SENDBACK-mapping-queue-cockpit-v16.md#ask-1` |
| **Sendback ask** | §4 Ask 1: *what must be true* — a scanning operator can tell a decisive section from supporting evidence at a glance; **two shapes**, a weight/size step on the label or a rule-and-indent treatment on the section, and a third if the designer sees one. Policy §4 quoted verbatim in the ask. |
| **Also in the sendback** | §2 — what the design specifies, what we render in the interim. §3 — the gap was **OURS**: the brief quoted the policy's type scale but neither §4's label-case prohibition nor §5's hard-failure list, so the design could not have known. |
| **Checker fires** | `D2-VERDICT-VERB` on *"v15 wins over the design"* · `D1-DEPARTURE-NO-SENDBACK` on the unreferenced row |

**The generalisation, because this is the row that recurs:** `policy wins` is never a verdict this
workflow issues. Comply as **interim**, label it, ask.

---

## G2 — a table column dropped because no field records it

**What the ledger said** (pass 2 §3):

> *"**The detector table is new, and it is two columns rather than three.** The design's card carries
> detector name · what it read · count. The middle column does not exist: `PackDetection.detections`
> carries `{ method, quantity }` and nothing else … So a `reads` string would be a design figure
> arriving as data, which is a stop condition. The table renders name and count, and states the
> absence under itself in words."*

| | |
|---|---|
| **Classification** | **DEPARTURE** — and this is the row that most tests the test. The *table shipped*, in a shape we chose. Compare pass 2 §7's *"The `reads` column — § 3. No field records it."*, which reads as a deferral: it is the same fact seen from the other side, and the disposition follows the **rendered surface**. Something of ours (a two-column table) stands in the design's place (a three-column one). |
| **Counter-case** | Had the whole detector table been left unbuilt, that is NOT-YET-BUILT — `⊘ deferred(needs-data: no field records the span)`, no sendback. The distinction is whether we rendered a substitute. |
| **What was right** | Refusing to invent the middle column. A design figure arriving as data is a genuine stop condition, and stating the absence in words on the surface was good work. |
| **What was wrong** | Choosing the two-column shape unilaterally. The designer drew three columns for a reason and may prefer an empty-but-present column with an honest `not recorded`, a merged cell, or a different card entirely. |
| **New disposition** | `⊘ departure(no field records the span; rendered 2 of 3 columns) → sendback:…#ask-2` |
| **Sendback ask** | §4 Ask 2: *what must be true* — a reader can see that each detector resolved to a count and that **what it matched is not recorded anywhere**; **two shapes**, drop the column and state the absence beneath the table (what shipped), or keep the column and render `not recorded` per row. The designer's call, and the field's absence is stated as a fact they cannot change. |
| **Checker fires** | `D1-DEPARTURE-NO-SENDBACK` · `D2` correctly **silent** — this ledger wrote no verdict verb |

---

## G3 — a treatment kept because ours was judged better

**What the ledger said** (pass 1 §9, preserved-claims table):

> *"A zero confidence score must never read as a real score — **held, and the implementation beats
> the design.** `CandidateRow` renders the word `auto` for a machine-found candidate and a number
> **only** when `score > 0`. The design renders `score not ranked` in the **same column** as
> `score 0.91`, which a scanning reader can read as automation having lost a comparison.
> **Keeping ours.**"*

| | |
|---|---|
| **Classification** | **DEPARTURE**, and the purest one — no policy clause, no missing field, no forced constraint. A design treatment was read, judged worse, and replaced by ours. |
| **What was right** | The reasoning. It is a real scanning-legibility risk and worth the designer knowing. |
| **What was wrong** | That it closed. *"Keeping ours"* is a verdict on a design question, and the designer never saw the argument — which is the loop the ruling exists to create. |
| **New disposition** | `⊘ departure(candidate-score treatment: ours retained over the design's) → sendback:…#ask-3` |
| **Sendback ask** | §4 Ask 3: *what must be true* — an unranked candidate can never be misread as having scored badly; **two shapes**, a separate column or row-slot for unranked candidates, or a distinct non-numeric token in the score column. Carry the observation — *"`score not ranked` beside `score 0.91` in one column reads as a lost comparison"* — as the evidence, not as the ruling. |
| **Checker fires** | `D2-VERDICT-VERB` on *"beats the design"* and *"Keeping ours"* · `D1-DEPARTURE-NO-SENDBACK` |

**Note for the sendback's §6 on the NEXT round:** once the designer answers, the answer is settled
and never re-argued. That is what makes the loop converge rather than oscillate.

---

## G4 — four honest deferrals. SILENT, and this is the row that keeps the rule affordable

**What the ledger said** (pass 2 §7, *"What is NOT built, and why — nothing shipped on a guess"*):

| Item | Why it was held | Disposition — unchanged |
|---|---|---|
| The multi-operator header | The design hardcodes one operator and assumes the answer to an open owner question | `⊘ deferred(out-of-scope: owner question open)` |
| The undo panel | Needs `undoAvailability` computed server-side from six refusal conditions; five never reach the cockpit | `⊘ deferred(needs-data: undoAvailability)` |
| The `Proposal reasoning` row | Rests on a requirement the profile marks unratified; rendering it would answer a question for the owner | `⊘ deferred(judgment: requirement unratified)` |
| The detector `reads` column | No field records it — the deferral half of G2 | see G2 |

**None of these is a departure.** Each is the design's item, untouched, with nothing of ours standing
in its place. A deferral asserts nothing, so the designer is owed nothing — the items go into §9's
"Deltas not applied" exactly as they always did, at no extra cost.

**And the pass was RIGHT to hold them**, which is why the row belongs in this matrix rather than in a
failure-mode list. Pass 2's own summary — *"Everything shipped here is either a traced requirement …
or a policy compliance fix"*, with `Shipped this pass: Nothing` under *"Resting on an unratified
profile line"* — is the discipline this rule must not tax.

**Checker:** silent. `checkLedger` returns zero hard findings, asserted.

---

## The fifth row, which is not a case but a calibration

**A faithfully applied row is not a departure**, and neither is:

- **a capability disposition already ruled at step-02b §4** — pass 2 §9 item 4, *"The pull reaches an
  ageing snapshot, not only a never-pulled one — not a policy win but a production capability the
  design drops; retained per pass 1's `additive` strategy."* An `additive` strategy is an owner
  decision already taken. Do not re-ask it, and note the ledger itself already distinguished it from
  the three policy/judgement items — correctly.
- **a §5b FORCED path substitution** — the design links to a route that does not exist. Forced-and-
  logged is already the contract; a sendback is owed only where the force is a *design* question.
- **an ancestor layout injecting chrome a brief's `shell_role.forbidden_chrome` names**
  (`step-03-build-grid.md` §2d) — the design frame is not departed from at all; the repair is outside
  it. An impl-side Tier-1 row, not a sendback item.

---

## What this matrix does NOT prove

It proves the checker fires and stays quiet on four real, known shapes. It does not prove a run will
**classify** a novel departure correctly — that is a judgement, it is PROBABILISTIC, and §5c says so
rather than letting this file imply coverage it does not have. It also cannot see a departure never
recorded as one: a run that quietly matched its own taste and wrote `✓ applied` is invisible to every
tier here.
