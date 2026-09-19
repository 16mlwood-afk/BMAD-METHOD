---
title: 'Decision — the design brief binds only through its tests (2026-09-19)'
description: 'Why the design-handoff brief became outcome-first in five parts, what binds the designer and what is advice, what changed in each producer and consumer, and how to recover the old template.'
---

# Decision — the design brief binds only through its tests

**Date:** 2026-09-19 · **Standard:** STD-BRIEF-BINDING-001 · **Scope:** FORK CANON (distributed to every registered project)

## The owner's words

> **Governing principle, verbatim:** *"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"*

> On the brief it replaces: *"like giving an artist a pencil without lead in… close the gap… over-constraining… this should be a global fork fix"*

Evidence: [`design-brief-notes-evidence-2026-09-19.md`](./design-brief-notes-evidence-2026-09-19.md) — the review of the TheFBAPrep staging brief after the page was built twice. The second build, made without the brief's formal constraints, was better and kept every substantive commitment. The brief named outputs rather than a decision, wrote its honesty commitments as mechanisms, marked nothing droppable, smuggled placement in as requirement, implied an eleven-column table, fixed status vocabulary at the token level, fenced its open questions, and ran a review gate that rewarded inventory.

## What was decided

1. **The brief is outcome-first, in five parts:** the moment · what must be true · what must dominate · the data and its defects · open questions (unfenced, with an invitation to sketch two options). Everything else sits under an **Advisory guidance** heading.
2. **Only Part 2 binds the designer.** T0 (the five-second answer test) plus T1…Tn truth tests, each written as a pass/fail outcome, never as a mechanism.
3. **The project design policy is not rewritten.** Its truth and data rules bind, as Part 2 tests; its style, layout and composition rules are advice. Rules kept only for consistency are marked `[tradeable]`. The one-question classification test is in `custom/workflows/design/shared/brief-binding-contract.md` §2.
4. **Token, pill and colour detail leaves the brief.** It points to the project's design system.
5. **Downstream gates match.** `design-review-pr` and the `design-implement` conformance gate may fail a design only on a truth test or the five-second answer. Everything else is a note.
6. **Kept:** the anti-anchoring rule (DO-NOT-READ list for the current view). It is about bias, not over-constraint.

## What changed, file by file

| Surface | Change |
|---|---|
| `shared/brief-binding-contract.md` (new) | The single source for the split, the classification test, what a gate may fail on, and a Prose-consumers table the fork's validator checks |
| `design-handoff/brief-template.md` | New Block B fields (`brief_shape`, `page_answer`, `dominant`, `truth_tests`); binding block replaces the "compile and obey" spine; Parts 1–5; §4 points to the design system instead of copying tokens; §4a–§7 labelled advisory; §7 frames are suggestions |
| `design-handoff` step-01 (§3i, new) + `state-variables.md` | Outcome pass captures the moment, answer, dominant, draft truth tests, policy classification, open questions, design-system pointer |
| `design-handoff` step-03 | Assembles Part 2 (T0 + tests), classifies policy rules, new self-review checks for the five parts and for not losing a guarantee |
| `design-handoff` step-03c | The adversary reviewer also flags over-binding (mechanism-shaped tests) and dropped guarantees |
| `design-handoff/workflow.md` | Governing principle at the top; Anti-Bias II and Deliverable-Completeness revised |
| `shared/brief-revision-policy.md` | Block B fields documented; `frames` advisory; Check 1c (outcome-first completeness; legacy briefs never halt) |
| `design-review-pr` | Step-04 §0 classifies every finding truth vs advisory; new `C-TRUTH-01` and `C-ANSWER-01`; report and verdict driven only by truth; frame inventory is not scored |
| `design-implement` | §SHARED.1b halts only on a truth test or T0; frame/shell/composition differences are notes; §2f "suggested frame not drawn" is a note |
| `design-synthesize` | Intake Check 1c; §7 frames loaded as suggestions (Gate 1f now guards the parse only); step-06 sub-check (t) is the only failing class; manifest carries `truth_test_results` and `advisory_notes` |
| `design-artifact-loop` | Intake Check 1c; parses the five parts; screen-review violations carry `Binding: truth | advisory` and a five-second line |
| `tools/check-brief-readiness.py` | Probe P6 (warn-only) for outcome-first briefs; 8 golden cases, mostly silence |
| `shared/operator-artifact-contract.md`, `disclosure-layer-contract.md`, `spawned-surface-completeness.md` | Binding-status banner: their rules are advisory unless carried into Part 2 |

### Follow-on, same day — the three remaining design workflows

| Surface | Change |
|---|---|
| `design-review` | New "What may be a hard failure" section; every violation carries `Binding: truth` or `advisory`; `hard failure` and blocking are reserved for truth. §1.6 checks T0 and the truth tests first (blocking); frame coverage, shell chrome and station-vs-dashboard become advisory (the role-boundary and staleness cases stay truth). An Anti-AI checklist failure is an advisory `major`, not a `hard failure`. Artifact frontmatter gains `five_second_answer` and `brief_binding` |
| `design-tuning` | New BINDING vs ADVISORY section; step-01 §2a captures T0 and the truth tests and classifies policy rules; step-02 §0b tags every finding and §2c judges T0 and the truth tests; fingerprint, treatment, craft, §13 and visual-reference findings are notes. FAIL only on truth; PARTIAL only when a truth test's state was not shown; an unverified treatment no longer blocks; PASS-WITH-ISSUES became PASS-WITH-NOTES; the correction message separates "Must be true" from "Advisory — your call" |
| `design-elevation` | Only a candidate that breaks a truth test, T0 or a truth-class rule is hard-rejected; a style-rule or look-based anti-default departure survives with an advisory note; `{core_job}` anchors on `page_answer` and `dominant`; changing advisory guidance is an in-surface refinement, not a re-brief |

## Proof the guarantees survived — the TheFBAPrep brief regenerated in the new shape

The notes list six commitments that survived the second build. Each is expressible as a Part 2 test, with no layout:

| Id | Test (a finished design passes if…) | Was, in the old brief |
|---|---|---|
| T0 | A first-time reader states *"TheFBAPrep DE Leipzig — the prep's records are missing 14 of your purchases"* within five seconds | (absent — the brief named no answer) |
| T1 | For every figure a reader can tell whether it is ours (what we bought) or theirs (what the prep's documents say), without opening anything | "Both authorities visible on every row" |
| T2 | Where our count and the prep's disagree, both are shown with their sources and no variance is computed between them | "Two authorities, never blended" |
| T3 | With no prep document read, the page shows our purchases only and says it cannot see the prep — no prep-side figure, zero or dash stands in | "The named absences render as named absences" |
| T4 | A price whose VAT basis is unknown says it is unknown and names what would settle it | money basis-complete per policy §15 |
| T5 | A rate with no recorded provenance says so wherever it is used | "Every prep-side figure names its document and date" |
| T6 | A failed or partial read can never be mistaken for a clean result, and nothing else on the page competes with it as an alarm | "The freshness band is permanent and non-dismissible" / only red on the page |

Two layouts pass every one of these — the inline-annotated eleven-column version and the second build's headline-rewrite version — which is the test that each is an outcome, not a mechanism. Dominant: *the purchases the prep is missing*. On demand: the 598 matched rows, the full mirror, document dates, VAT basis, lot ids, raw exchanges.

## Recovering the old template

The fork is git-tracked. The last commit carrying the pre-change template is `85d5a189`:

    git -C ~/bmad-method-v6 show 85d5a189:custom/workflows/design/design-handoff/brief-template.md

Every other changed file is recoverable the same way from that commit.

## Enforcement, honestly

PROBABILISTIC. Classification, test phrasing and the five-second judgement are reader judgements. The deterministic slice: probe P6 (warn-only, Gate 1) and the prose-consumers validator, which fails the fork's suite if a consumer stops referencing the contract. Legacy briefs keep working: their MUST PRESERVE list is read as truth tests and nothing halts on the new fields' absence.
