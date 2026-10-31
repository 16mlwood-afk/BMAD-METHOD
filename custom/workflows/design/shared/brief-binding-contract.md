---
name: brief-binding-contract
description: 'What a design brief BINDS and what it only ADVISES. The one split every producer and consumer of a design-handoff brief applies: the designer is bound by the brief''s "what must be true" tests, the five-second answer test, and (since v2, 2026-09-27) the Part 2b presentation floor — type scale, spacing, colours, attention plan, item layout, banned patterns; everything else (frames, composition, component guidance, the remaining style parts of the design policy) is advisory, and departing from it is a note, never a failure.'
standard: STD-BRIEF-BINDING-001
version: 3
ratified: 2026-09-19
amended: 2026-09-27; 2026-10-04 (v3 — §1b the opening)
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
| What | The brief's **Part 2 "What must be true" tests** (T1…Tn), plus **T0, the five-second answer test**, plus **the Part 2b presentation floor** (§1a) — the type scale, spacing tokens, colour set, attention plan, item layout and banned patterns, with the concrete values the brief states | Everything else: suggested frames, order, layer, persistence, column lists, composition, page-mode defaults, pills, component guidance, the style/layout/composition rules of the project design policy that Part 2b does not name, the rest of the AI-fingerprint floor and the comfort floor |
| Written as | A pass/fail outcome a finished design either meets or does not — **never the mechanism that meets it** | Suggestions, starting points, and rules kept for consistency (each marked `[tradeable]`) |
| A departure is | A **failure** (the only kind a gate may raise) | A **note**. Reported, never scored as a fail, never blocking |

**T0 — the five-second test (every brief, always binding).** *A reader who has not seen the page
before can state the page's answer — the brief's `page_answer` — within five seconds of it
loading.* This is judged by a reader (human or an isolated reviewer), never by counting frames.

**T0 has a per-surface twin (2026-09-26).** Every detail surface the brief names — a drawer, an
expanded row, a record panel, a side sheet — carries its own five-second test, **TD0**, plus a reading
order (**TD1**) and a once-per-surface rule (**TD2**). They are Part 2 tests like any other and bind the
same way; `controls-and-attention.md` §2a owns them, and this contract does not restate them.

### 1a. The presentation floor — the second binding class (v2, 2026-09-27)

> **Owner, 2026-09-27, verbatim:** *"we need to go back to the drawing board with the UI... treat Claude
> Design like an idiot... we've left basic gaps to Claude Design... it's reading like a ledger printed on
> a screen... no font size enforcement... that yellow thing at the top, the most AI pattern I've ever
> seen, which hasn't been caught by our anti-AI patterns... audit text at the top... a complete violation
> of our user attention policy."*

Version 1 of this contract put tokens, colour, the AI-fingerprint floor and the comfort floor in the
advisory column, *"a note, never a failure"*. The price-list page audit of 2026-09-27 traced a rejected
page straight to that line: the brief told the designer *"What IS yours: typography and scale, spacing
and rhythm… and the weight system"*, only the five-second tests bound, and a tinted notice box is the
cheapest way to pass a five-second test. So v2 moves seven things into the binding column, **specified
in the brief rather than delegated**, and checked on the rendered page:

1. a type scale, one typeface and four sizes set by position (the page's lead line, a block's lead line, inside an item or row, secondary) — five roles until 2026-10-04, when the by-datum `figure` role was removed (§1b);
2. spacing tokens; 3. a colour set, each colour with one meaning; 4. the attention plan — the answer at
the top, the first actionable item above the fold at 1440×900, a word budget above it, provenance and
audit text in the footer or behind a disclosure; 5. the layout — a summary, then items as cards or
groups, detail on open; 6. the banned patterns — tinted callouts, coloured edge stripes, stacked badges,
all-caps labels, the same fact twice; 7. the answer visually heavier than the evidence.

**Brief completeness (2026-09-28, presentation-floor.md §8).** The same binding class covers what a
designer would otherwise have to guess: the order of a ranked list (evidence tier first), what survives
a truncation, a layout for every state in every view, the widths (1440, 1280, narrow), feedback after an
action, headroom under the word budget, and the brief's notation. They bind the BRIEF (Gate 1, B12–B20; and B21, every section's form below the fold, §9; and B22, label/value row groups, §10)
so the designer is never left to invent them; each came from a designer's pre-build review and is
recorded in `brief-gap-ledger.md`.

`presentation-floor.md` (STD-PRESENTATION-FLOOR-001) owns the detail, the fork default values, the ten
policy citations and the checks; this section does not restate them. **The v1 governing principle still
holds for everything else** — Claude Design does the heavy lifting on composition and wording — and the
v1 text is recoverable verbatim at `git -C ~/bmad-method-v6 show c2951122:custom/workflows/design/shared/brief-binding-contract.md`.

### 1b. The opening — what good looks like, ahead of what is forbidden (v3, 2026-10-04)

> **Owner, 2026-10-04, verbatim:** *"we've narrowed it down to the brief being the problem. Take this
> feedback and solve the gap."*

Versions 1 and 2 said what binds and what is advice. Neither said what good looks like, and a designer
given only tests and a floor aims at passing them. So a brief now **opens** with the job, a picture of
good (one accepted reference screen and a short component vocabulary), five rules (use the product's
vocabulary · claims word for word, chrome the designer's · one value leads · type by position · absence
is quiet), the words on screen, and a required self-review that ends on *would this ship at a good
product company?* The five rules and the frozen words bind with the floor; the reference is a bar and a
vocabulary, never a layout to copy.

Two things follow for every consumer. **Claims and chrome are different classes of text**: a claim
(a field's value and qualifier, a figure, a caveat, a state word) is frozen, a basis sentence must appear in
the opened record but is placed by the designer, and a structural label (a section heading, a column
header, a row label, a group name) is the designer's to add, word or drop, so a design is never failed for
adding or rewording chrome. **The checker's matter is not the designer's copy**: how a test is checked,
the markers, the policy citations, the machine copy and every count sit in the brief's checker appendix.
A count is applied to the built page and is never a reason to reword a claim.

`presentation-floor.md` §12 and §13 own the detail and the Gate 1 checks (B25–B35);
`on-screen-copy-screen.md` §1a owns claims and chrome. The prior text of everything this replaced is in
`docs/decision-design-brief-picture-of-good-2026-10-04.md`.

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
- **Styling, layout and composition rules are ADVISORY — except what the presentation floor (§1a)
  names.** The policy's type scale, spacing and colours are the SOURCE the brief's Part 2b is filled
  from, and once there they bind. The rest stays advisory: status colour caps, pill geometry,
  radius, table-first defaults, band placement, drawer mechanics, density, hard-failure
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

0. **The opening** (§1b) — the job (the moment and the `page_answer`, said once), the picture of
   good, the five rules, the words on screen, the self-review. Then a `# Reference` divider.
1. **The moment** — who opens the page, after what, to decide what. Stated in the opening; Part 1
   keeps the purpose and the user.
2. **What must be true** — the binding tests, pass/fail, never mechanisms.
3. **What must dominate** — ONE thing. Everything else is explicitly available-on-demand, so
   demoting it is legal.
4. **The data, and its defects** — kept as it was: what each feed contains, what it cannot tell
   you, which figures are derived, where the gaps are.
5. **Open questions, unfenced** — named, with an invitation to sketch two options.

Then an **Advisory guidance** appendix carrying everything else, labelled as such, and last a
**Checker appendix** holding what only our gate reads. The template is
`design-handoff/brief-template.md`.

**Kept, and not advisory: the anti-anchoring rule.** A redesign brief still lists the current view's
files as DO-NOT-READ. That rule is about bias, not over-constraint, and it binds the designer's
PROCESS (what they read), not the design.

## 4. What a gate may and may not fail on

- **May fail:** a broken Part 2 truth test; a failed T0 five-second test; a broken Part 2b
  presentation-floor item (§1a — a size off the scale, the answer not the heaviest text, a tinted
  callout, an edge stripe, stacked badges, capitals, a fact twice, provenance at the top, the first
  item below the fold, a contrast failure); a brief-provenance defect at intake (unchanged — that is
  about which brief is current, not about the design).
- **Must not fail — report as a note instead:** a suggested frame not drawn; a different layer, order
  or persistence; a different composition from the page-mode default; a pill choice; a column set;
  any style/layout/composition rule from the design policy that Part 2b does not name; the rest of the
  AI-fingerprint composite; the rest of the comfort floor.
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
listed below stops referencing this file. **Since v2 the presentation floor is DETERMINISTIC on both
ends:** `tools/check-rendered-page.js --validate-brief` fails a brief whose Part 2b is incomplete
(Gate 1), and the same tool's rendered-page checks fail a page that breaks it (design-implement
step-04b). Their ceiling: they prove counts and presence, never that the page reads well.

## Prose consumers

| Consumer | Bound how |
|---|---|
| `design-handoff` | Produces the five-part brief; classifies policy rules binding vs advisory |
| `design-review-pr` | Fails only on a Part 2 test or T0; every other finding is an advisory note |
| `design-implement` | Bundle→brief conformance gate halts only on a truth test, T0 or a presentation-floor failure (step-04b rendered-page checks); frame/shell/composition diffs are notes |
| `shared/presentation-floor.md` | Owns the second binding class (§1a): the seven floor parts, the fork default values, the policy citations and the checks |
| `design-synthesize` | Suggested frames are the synthesizer's call; self-critique fails only on a truth test or T0 |
| `design-artifact-loop` | Parses the five parts; treats advisory sections as advice; verdict `FAIL` only on a truth issue (the dissent pass may demote to `FAIL` only for one); `PASS WITH NOTES` (formerly `PASS WITH ISSUES`) carries advisory notes |
| `design-review` | Live-page audit: T0 and truth tests are the only `hard failure` / blocking findings; frame coverage, shell chrome, composition shape, the Anti-AI checklist and policy style rules are advisory (`Binding:` on every violation) |
| `design-tuning` | Iteration critic: FAIL only on a broken truth test or T0; fingerprint, treatment, craft, visual-reference and undrawn-frame findings are advisory notes (PASS-WITH-NOTES); coverage blocks approval only for a state a truth test needs |
| `shared/design-standards.md` | AI-fingerprint taxonomy, composite test and scrub checklist are advisory notes; only the undisclosed-fixture-data half of the placeholder row is truth |
| `shared/claude-design-prompt.md` | Paste prompt splits policy constraints into TRUTH (can fail) and ADVISORY (designer's call); artifact shape and in-surface composition are advisory |
| `design-elevation` | Candidate filter: hard-rejects only a candidate that breaks a truth test, T0 or a truth-class rule; a style-rule departure survives with an advisory note; changing advisory guidance is not an intent change |
| `design-handoff` (opening, v3) | Renders the opening of §1b ahead of the five parts, and the checker appendix after them; Gate 1 checks B25–B35 |
| `shared/controls-and-attention.md` | Supplies five further truth tests and the second classification question (§2a), and the per-detail-surface TD0/TD1/TD2 (its own §2a); its own advisory half stays advisory |
