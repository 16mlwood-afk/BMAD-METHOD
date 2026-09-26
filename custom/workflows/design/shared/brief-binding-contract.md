---
name: brief-binding-contract
description: 'What a design brief BINDS and what it only ADVISES. The one split every producer and consumer of a design-handoff brief applies: the designer is bound only by the brief''s "what must be true" tests and the five-second answer test; everything else (frames, layout, composition, tokens, component guidance, the style parts of the design policy) is advisory, and departing from it is a note, never a failure.'
standard: STD-BRIEF-BINDING-001
version: 1
ratified: 2026-09-19
---

# Brief binding contract — what binds the designer, and what is advice

> **Governing principle, in the owner's words (2026-09-19), verbatim:**
> *"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"*
>
> And on the brief this replaced: *"like giving an artist a pencil without lead in… close the gap…
> over-constraining… this should be a global fork fix"*.

Evidence and the worked example behind this contract:
`docs/design-brief-notes-evidence-2026-09-19.md` in the fork (the review of the TheFBAPrep staging
brief after it was built twice). Decision record: `docs/decision-design-brief-outcome-first-2026-09-19.md`.

## 1. The split

A design brief says two kinds of thing. They carry different authority, and every workflow that
reads a brief must keep them apart.

| | **BINDING** — can fail a design | **ADVISORY** — the designer's call |
|---|---|---|
| What | The brief's **Part 2 "What must be true" tests** (T1…Tn), plus **T0, the five-second answer test** | Everything else: suggested frames, layout, order, layer, persistence, column lists, composition, page-mode defaults, tokens, pills, colour, component guidance, the style/layout/composition rules of the project design policy, the AI-fingerprint floor, the comfort floor |
| Written as | A pass/fail outcome a finished design either meets or does not — **never the mechanism that meets it** | Suggestions, starting points, and rules kept for consistency (each marked `[tradeable]`) |
| A departure is | A **failure** (the only kind a gate may raise) | A **note**. Reported, never scored as a fail, never blocking |

**T0 — the five-second test (every brief, always binding).** *A reader who has not seen the page
before can state the page's answer — the brief's `page_answer` — within five seconds of it
loading.* This is judged by a reader (human or an isolated reviewer), never by counting frames.

**T0 has a per-surface twin (2026-09-26).** Every detail surface the brief names — a drawer, an
expanded row, a record panel, a side sheet — carries its own five-second test, **TD0**, plus a reading
order (**TD1**) and a once-per-surface rule (**TD2**). They are Part 2 tests like any other and bind the
same way; `controls-and-attention.md` §2a owns them, and this contract does not restate them.

## 2. How the project design policy splits

The project's `docs/design-policy.md` is **not rewritten** by this contract and stays the project's
own document. What changes is how the fork's workflows **treat** it:

- **Truth and data rules stay BINDING** and are carried into the brief as Part 2 tests. Examples:
  money carries its basis (VAT basis, currency framed against GBP — policy §15 where the project has
  it); two authorities are kept distinct and never merged into one figure; no figure is invented,
  imputed or computed where the source has none; a missing value is never shown as zero; a derived
  figure is never presented as a stored one; a stale or partial read is never presentable as current;
  a linked value is the resolved foreign record, never re-keyed text; a fixture surface discloses
  that it is not live data; a role boundary that protects data (a clerk never sees owner money).
- **Styling, layout and composition rules are ADVISORY.** Status colour caps, pill geometry,
  radius, type scale, table-first defaults, band placement, drawer mechanics, density, hard-failure
  lists that are about look rather than truth. They are passed to the designer as advice. Where a
  rule exists only for consistency across the product, it is labelled `[tradeable]` so a better idea
  can be traded against it.

**The classification test (one question):** *if a design broke this rule, could a reader come away
believing something false about the data, the money, the state of the work, or who may see what?*
Yes → truth rule, binding. No → advisory.

When a rule is genuinely ambiguous, classify it advisory and say so in the brief's Part 5 open
questions. Over-binding is the failure this contract exists to fix.

### 2a. The second classification question — `controls-and-attention.md` (STD-CONTROLS-ATTENTION-001)

The one-question test above is about **data**. A second standard, ratified 2026-09-20, adds five
further truth tests and one further question, because a page can tell the truth about every figure
while still asking a person to do work its own design made unnecessary:

> *Does the page ask a person to spend attention or effort that its own design has made unnecessary?*

`controls-and-attention.md` owns that half — whether a control exists, how loud anything is, and what
the page treats as work. Its five tests (**TC1** a control earns its press · **TC2** an instruction
implies a control · **TA1** emphasis follows consequence · **TA2** one fact, one place · **TF1** a
defect is not a workload) are **binding**, carried into every brief's Part 2 phrased for that surface.
Everything else it touches — colour, shape, placement, spacing, wording — is advisory and deliberately
outside it. Read that file; this section does not restate it.

## 3. The brief shape this implies (outcome-first, five parts)

1. **The moment** — who opens the page, after what, to decide what. One paragraph, plus the
   `page_answer`.
2. **What must be true** — the binding tests, pass/fail, never mechanisms.
3. **What must dominate** — ONE thing. Everything else is explicitly available-on-demand, so
   demoting it is legal.
4. **The data, and its defects** — kept as it was: what each feed contains, what it cannot tell
   you, which figures are derived, where the gaps are.
5. **Open questions, unfenced** — named, with an invitation to sketch two options.

Then an **Advisory guidance** appendix carrying everything else, labelled as such. The template is
`design-handoff/brief-template.md`.

**Kept, and not advisory: the anti-anchoring rule.** A redesign brief still lists the current view's
files as DO-NOT-READ. That rule is about bias, not over-constraint, and it binds the designer's
PROCESS (what they read), not the design.

## 4. What a gate may and may not fail on

- **May fail:** a broken Part 2 truth test; a failed T0 five-second test; a brief-provenance defect
  at intake (unchanged — that is about which brief is current, not about the design).
- **Must not fail — report as a note instead:** a suggested frame not drawn; a different layout,
  layer, order or persistence; a different composition from the page-mode default; a token, pill or
  colour choice; a column set; any style/layout/composition rule from the design policy; the
  AI-fingerprint composite; the comfort floor.
- **Implementation fidelity is a different question.** Whether the CODE matches the DESIGN the
  designer actually drew (`design-implement`'s grid) is not a judgement on the design and is not
  changed by this contract. A frame the designer drew and the build omitted is still a build gap.

**Legacy briefs** (no `brief_shape: outcome-first`): consumers apply the same split. Their
"MUST PRESERVE" list is read as their truth tests; their `frames` list, §4, §5 and §7 are advisory.

## 5. Enforcement, honestly

PROBABILISTIC throughout. Whether a rule was classified correctly, whether a test is phrased as an
outcome rather than a mechanism, and whether a reader really got the answer in five seconds are
judgements. The deterministic slice is narrow: `tools/check-brief-readiness.py` probe P6 warns when
an outcome-first brief is missing its moment, its binding tests, its single dominant, or its open
questions; and `tools/validate-prose-consumers.mjs` fails the fork's own test suite if a consumer
listed below stops referencing this file.

## Prose consumers

| Consumer | Bound how |
|---|---|
| `design-handoff` | Produces the five-part brief; classifies policy rules binding vs advisory |
| `design-review-pr` | Fails only on a Part 2 test or T0; every other finding is an advisory note |
| `design-implement` | Bundle→brief conformance gate halts only on a truth test or T0; frame/shell/composition diffs are notes |
| `design-synthesize` | Suggested frames are the synthesizer's call; self-critique fails only on a truth test or T0 |
| `design-artifact-loop` | Parses the five parts; treats advisory sections as advice; verdict `FAIL` only on a truth issue (the dissent pass may demote to `FAIL` only for one); `PASS WITH NOTES` (formerly `PASS WITH ISSUES`) carries advisory notes |
| `design-review` | Live-page audit: T0 and truth tests are the only `hard failure` / blocking findings; frame coverage, shell chrome, composition shape, the Anti-AI checklist and policy style rules are advisory (`Binding:` on every violation) |
| `design-tuning` | Iteration critic: FAIL only on a broken truth test or T0; fingerprint, treatment, craft, visual-reference and undrawn-frame findings are advisory notes (PASS-WITH-NOTES); coverage blocks approval only for a state a truth test needs |
| `shared/design-standards.md` | AI-fingerprint taxonomy, composite test and scrub checklist are advisory notes; only the undisclosed-fixture-data half of the placeholder row is truth |
| `shared/claude-design-prompt.md` | Paste prompt splits policy constraints into TRUTH (can fail) and ADVISORY (designer's call); artifact shape and in-surface composition are advisory |
| `design-elevation` | Candidate filter: hard-rejects only a candidate that breaks a truth test, T0 or a truth-class rule; a style-rule departure survives with an advisory note; changing advisory guidance is not an intent change |
| `shared/controls-and-attention.md` | Supplies five further truth tests and the second classification question (§2a), and the per-detail-surface TD0/TD1/TD2 (its own §2a); its own advisory half stays advisory |
