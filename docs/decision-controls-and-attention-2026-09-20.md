---
title: 'Decision — controls, attention and faults (2026-09-20)'
description: "Why a design policy now governs whether a control exists, how loud anything is, and what the page treats as work; the five binding tests; where each is wired; and the worked example that produced them."
---

# Decision — controls, attention and faults

**Date:** 2026-09-20 · **Standard:** STD-CONTROLS-ATTENTION-001 · **Scope:** FORK CANON (distributed to every registered project)

Policy file: `custom/workflows/design/shared/controls-and-attention.md`. It sits inside
[STD-BRIEF-BINDING-001](./decision-design-brief-outcome-first-2026-09-19.md) and does not loosen it.

## The owner's words

> _"drift between us thinking there's a live offer versus Amazon not receiving the offer is just a back end bug. Why is it classified as a common operational problem?"_

> _"it's unbelievably text heavy."_

> _"If you can basically get all of these down onto paper, we can hopefully prevent them all using policy preventions."_

Both readings were of the same artefact — the Claude Design output for inbound-flow's listings queue,
20 September 2026.

## The problem this closes

The brief contract ratified the day before made the designer free and kept the fork honest about
**data**: money carries its basis, two authorities stay apart, a stale read never reads as current. It
has no opinion about **what the page asks a person to do**. A page can satisfy every truth test it
carries and still put a filled black button on nine rows where pressing it tells the system nothing,
instruct an action it offers no control for, make the least consequential thing the loudest, say one
fact four times, and present a back-end bug as the largest category of the operator's work.

Every one of those was on one page, and none of them was catchable by anything the fork had.

## What was decided

1. **A new standard, STD-CONTROLS-ATTENTION-001**, governing three things and nothing else: whether a
   control exists, how loud anything is, and what the page treats as work.
2. **Five binding tests**, carried into every outcome-first brief's Part 2 and phrased with that
   surface's own controls, instructions, facts and fault categories:

   | Id | A finished design passes if… |
   | --- | --- |
   | **TC1** | Every action control can name what its press tells the system that the system does not already know — a decision only a person can make, a fact only a person holds, an authorisation for something irreversible, or the operator's knowledge that the world has just changed. |
   | **TC2** | No sentence tells the operator to do something the surface gives them no way to do. |
   | **TA1** | The most emphasised thing is the most consequential thing, and no consequential control is dressed as an inconsequential one. |
   | **TA2** | No fact is stated twice on the surface at rest. |
   | **TF1** | No system fault is presented as a category of the operator's work, and no control exists only to compensate for one. |

3. **A second classification question**, added to the binding contract §2a, because the existing
   one-question test is about data and would not obviously admit TC1, TC2 or TA2: _does the page ask a
   person to spend attention or effort that its own design has made unnecessary?_ TF1 and the second
   half of TA1 pass the original question as written; the other three are admitted by this one, and
   the standard says so rather than pretending otherwise.
4. **Everything else stays advisory and is deliberately absent from the policy** — colour values,
   button shape, placement, spacing, exact wording. The file says so in §4, and three consumers repeat
   the exclusion at the point where a reviewer would be most tempted to widen it. Growing this into a
   style guide would reintroduce the over-constraint STD-BRIEF-BINDING-001 was written against.
5. **Scope: action controls only.** Navigation, filtering, sorting, expanding and opening a record are
   view controls — they move attention rather than instruct the system, and TC1 is not about them.
   Without this the test fires on ordinary work and gets switched off.

## What changed, file by file

| Surface | Change |
| --- | --- |
| `shared/controls-and-attention.md` (new) | The standard: three parts, five binding tests with their reviewer checks, the advisory half, the second classification question, the worked example, and a Prose-consumers table the fork's validator checks |
| `shared/brief-binding-contract.md` | New §2a naming the standard, the second question and the five tests; Prose-consumers row added |
| `design-handoff` step-01 §3j (new) + step-01-gather §3j trigger | Controls pass on every run: `{expected_controls}`, `{background_work}`, `{fault_categories}`, and the five tests phrased for the surface |
| `design-handoff/state-variables.md` | The new pass's four variables documented |
| `design-handoff/brief-template.md` | TC1/TC2/TA1/TA2/TF1 rendered in Part 2 with per-surface placeholders; new advisory §4f-c carrying the expected controls, the background work and the fault table; the binding block names the five |
| `design-handoff` step-03 | Renders the five and §4f-c; HARD FAIL on a missing or generic one; two new self-review checks (the five are surface-specific; no control dropped in silence, no fault left as workload) |
| `design-handoff` step-03c | Adversary probe 9 — boilerplate tests, a control that should have been background work, a fault owned by the operator, a silently dropped capability, and the over-binding inverse (§4f-c prescribing placement) |
| `design-review-pr` step-04 | New §1f with five truth-class checks — `C-CONTROL-01`, `C-CONTROL-02`, `C-ATTENTION-01`, `C-ATTENTION-02`, `C-FAULT-01` — reported exactly like `C-TRUTH-01`; added to the fixed-class list, the manual-prompt order and the anti-pattern list |
| `design-implement` step-01 §SHARED.1b | Binding check 3: the five halt the run like any other truth test, judged against what the bundle draws |
| `design-synthesize` step-01 | Intake loads the five and the §4f-c evidence, and lets them shape step 4 before drawing |
| `design-synthesize` step-06 §4t | Sub-check (t) item 3 — the synthesizer judges the five against its own render |
| `design-artifact-loop` step-02 | The five parsed as `Binding: truth`; §4f-c parsed as advisory evidence |
| `design-review` step-01 §1.6 | New 0c — the five judged on the live page as `hard failure`s |
| `design-tuning` step-01 §2a, step-02 §2c | Captured at load; judged at analyse, including on a legacy or brief-less run |
| `design-elevation` step-02 | A candidate that breaks one is hard-rejected; **removing** a control that fails TC1, deleting a repeated fact, demoting something loud, or routing a fault out of the queue is a first-class elevation candidate |
| `shared/claude-design-prompt.md` | The five go in the prompt's TRUTH half, with the instruction to name this surface's own subjects |

## Proof the tests can fail a real page — the listings queue, 2026-09-20

A test that cannot fail the design that produced it is badly phrased. All five fail it.

| Test | What the design did | Verdict |
| --- | --- | --- |
| TC1 | A filled black **Re-check** button on nine rows where Amazon had already been asked three times and answered no. The press tells the system nothing it does not have. | **FAIL** |
| TC2 | _"Below the price floor: the floor is £71.40 and the price is £62.00. Raise the price, or take it live below the floor."_ Neither control is on the row. | **FAIL** |
| TA1 | The loudest control was the least consequential, nine times over — which is why a **Re-check all 9** link had to be invented beside it. The two decisions that cost money sat behind a grey **Open**. The word **Terminal** sat in the action slot. The auto-approve switch, which decides whether listings go live with nobody looking, sat in the filter row styled as a view filter. | **FAIL** |
| TA2 | The group header's blocking reason repeated in every row; two columns carrying one fact in two voices; per-row provenance stamps; the headline and its three counts stating the same numbers twice. About forty words per row to learn one thing. | **FAIL** |
| TF1 | Back-end drift rendered as the largest category of the operator's work, with a control beside it that existed only to compensate. A recommended price below our own price floor reaching the queue as operator work. | **FAIL** |

**And the same page designed well passes all five** — the worked "after" is in the standard's §5.
Two quite different layouts can pass each test, which is the check that each is an outcome rather
than a mechanism in disguise.

## What this does NOT do

- It does not rewrite any project's `docs/design-policy.md`.
- It does not touch inbound-flow, and the listings-queue brief is **not** rewritten. What that brief
  would need is a §4f-c naming its own controls (the two price decisions, the auto-approve switch),
  its background work (the marketplace re-check), and its fault categories (offer drift owned by
  engineering; recommended-price-below-floor owned by the pricing rule) — then the five tests phrased
  against those. Re-running `design-handoff` produces that; hand-editing the brief would be a
  material change as a hand-edit, which `brief-revision-policy.md` forbids.
- It adds no colour, shape, placement, spacing or wording rule, and must not grow one.

## Enforcement, honestly

**PROBABILISTIC throughout.** Whether emphasis matches consequence, whether a category of work is
really a defect, and whether a fact was said twice or decomposed into two different facts are reader
judgements, and no check makes them. A detector keyed on button styling or word counts would fire on
ordinary work and be switched off within a week.

**The deterministic slice is narrow and real:** `tools/validate-prose-consumers.mjs` fails the fork's
suite if any listed consumer stops referencing the standard, and `design-handoff` renders the five
into every brief's Part 2, so a designer and a reviewer are handed them rather than having to remember
them. The verdicts remain a reader's.

## Recovering the previous state

The fork is git-tracked. The last commit before this change is `3448bc8f`:

    git -C ~/bmad-method-v6 show 3448bc8f:custom/workflows/design/design-handoff/brief-template.md

Every changed file is recoverable the same way from that commit.
