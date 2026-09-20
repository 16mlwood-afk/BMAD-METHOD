---
name: controls-and-attention
description: 'Whether a control exists, how loud anything is, and what the page treats as work. Five binding tests a finished design passes or fails: a control earns its press; an instruction implies a control; emphasis follows consequence; one fact, one place; a defect is not a workload. Everything else — colour, shape, placement, spacing, wording — stays advisory.'
standard: STD-CONTROLS-ATTENTION-001
version: 1
ratified: 2026-09-20
---

# Controls and attention

> **The owner, 2026-09-20, on the listings queue:**
> *"drift between us thinking there's a live offer versus Amazon not receiving the offer is just a
> back end bug. Why is it classified as a common operational problem?"*
>
> And, on the same page a second time: *"it's unbelievably text heavy."*
>
> *"If you can basically get all of these down onto paper, we can hopefully prevent them all using
> policy preventions."*

This policy governs three things: **whether a control exists**, **how loud anything is**, and **what
the page treats as work**. It sits inside `brief-binding-contract.md` (STD-BRIEF-BINDING-001) and does
not loosen it — the designer still does the heavy lifting, and everything here that is not one of the
five tests in §4 is advice.

---

## 1 · What earns a control

A control exists only if pressing it does one of three things:

- **DECIDES** something only a person can decide;
- **SUPPLIES** a fact only a person holds;
- **AUTHORISES** something irreversible.

**The test is not "could a machine do this". It is "does the press carry information the system does
not already have."** A press that merely re-runs a step the system can run on its own is the page
borrowing the operator's attention to do its own job. That work goes to the background, and the page
says what it is doing and when it last ran.

Where a *do it now* is genuinely useful — the operator knows the world changed, brand approval has
just been granted, the supplier has just confirmed — the press does carry information: the operator's
knowledge that a re-run is worth making now. That is a legitimate control.

**And an instruction implies a control.** If a sentence on the page tells the operator to do
something, the page gives them a way to do it. An instruction with no mechanism is a chore handed to
the operator to carry somewhere else. Either the control is there, or the sentence states the fact and
stops telling anyone to act.

**Scope — action controls only.** Navigation, filtering, sorting, expanding a row and opening a record
are view controls: they move the operator's attention rather than instruct the system, and §1 is not
about them. It is about a control that makes the system do work or change a record.

## 2 · What earns attention

**Emphasis follows consequence, not frequency.** One focal point per page, and it is the answer, not
an action.

**Every control spends from a fixed attention budget, and so does every word.** A group of
near-identical rows spends once. A status word never occupies an action slot. A page that is already
working says so, because a button where a progress indicator belongs implies that nothing is
happening.

**The rule runs both ways, and the second half is the one that gets missed.** Nothing may be louder
than the most consequential thing on the page — *and* nothing consequential may be dressed as
something inconsequential. A switch that decides whether records go live with nobody looking is the
most consequential control on its page; styled and placed like a view filter, it reads as the least,
and a reader comes away believing it does less than it does.

**One fact, one place.** A fact is stated once on the surface at rest. Three ways a page breaks this,
all seen on one design:

- the group header already states the one thing stopping the group, and every row inside repeats it in
  a paragraph;
- two columns carry the same fact in two voices — *"Our record says live. Amazon has no published
  offer, and has said so for three checks running"* beside *"No live offer, confirmed 4 min ago"*.
  Keeping our word and theirs apart is right; saying it twice is not;
- provenance stamped on every row — *"incl. VAT, inferred"*, *"≈£247"* — which is the per-figure
  annotation the 2026-09-18 evidence notes already rejected. The caveat belongs to the page.

**The repair is not shorter sentences. It is depth.** The row carries the shortest phrase that
distinguishes it from its neighbours; the reasoning, the dates and the other side's exact words live
one layer down. As drawn, the listings queue took about forty words per row to teach the reader one
thing.

## 3 · A defect is not a workload

**A page must not render a system fault as a standing category of the operator's work, and must not
offer the operator a control whose only purpose is to compensate for that fault.**

A fault is **named as a fault**, carries an **owner who is not the operator**, and is **counted
separately from real work**. Where a category of "work" is in truth a recurring defect, the design says
so rather than normalising it into the queue.

Two worked instances, both the owner's own, both from one page:

- **Drift.** We think there is a live offer; the marketplace never received it. That is a back-end bug.
  It was rendered as the largest category of the operator's work, with a control beside it whose only
  job was to ask the marketplace again.
- **A recommended price below our own price floor.** Two of our own numbers disagree. No human
  judgement resolves that; the pricing rule is what needs fixing. A record in that state should never
  reach an operator's queue at all.

---

## 4 · What binds, and what does not

**Five BINDING tests.** They are binding because they are about **what the page asks of a person**, and
about **whether it tells the truth about whose fault something is** — not about how anything looks.
Each is an outcome a finished design passes or fails, and each is carried into a brief's Part 2 with
the surface's own controls and facts named in it.

| Id | A finished design passes if… | How a reviewer checks it |
|---|---|---|
| **TC1** | Every action control on the surface can name what its press tells the system that the system does not already know — a decision only a person can make, a fact only a person holds, an authorisation for something irreversible, or the operator's knowledge that the world has just changed. | List every action control. For each, say what the press tells the system. A control whose answer is "nothing — the system could run this itself" fails. |
| **TC2** | No sentence on the surface tells the operator to do something the surface gives them no way to do. | Read every instruction in the prose. For each, find the control that performs it on the same surface. No control, and the sentence still instructs → fail. |
| **TA1** | The most emphasised thing on the surface is the most consequential thing on it, and no consequential control is dressed as an inconsequential one. | Rank what the eye reaches first. Rank what costs most if pressed or missed. Compare the two orders. Then find the single most consequential control and check it does not read as chrome. |
| **TA2** | No fact is stated twice on the surface at rest. | Pick the page's three loudest facts. Count where each is said before anything is opened. Twice is a fail; a decomposition that carries a *different* fact is a pass. |
| **TF1** | No system fault is presented as a category of the operator's work, and no control exists only to compensate for one. | For each category the page counts as work, ask who must act to make it stop recurring. If the answer is an engineer, it is a fault: it must be named as one, owned by someone other than the operator, and counted separately. |

**Everything else stays ADVISORY and is deliberately not in this policy** — colour values, button
shape, placement, spacing, exact wording, how many pixels a header is, which component renders a
count. This policy is about whether a control exists, how loud anything is, and what the page treats
as work. It must not grow into a style guide; growing it into one would reintroduce exactly the
over-constraint STD-BRIEF-BINDING-001 was written against.

**Advisory guidance that belongs beside these tests, and can be traded:**

- Where a *do it now* is legitimate, prefer a **quiet line, once per group** — never a filled button
  repeated per row. `[tradeable]`
- Prefer depth over compression for text weight: the distinguishing phrase on the row, the reasoning
  and the other side's exact words one layer down. `[tradeable]`
- Prefer saying when background work last ran, in words, over a control that re-runs it. `[tradeable]`

**Why these bind when the contract's one-question test is about data.** `brief-binding-contract.md` §2
asks: *could a reader come away believing something false about the data, the money, the state of the
work, or who may see what?* TF1 and the second half of TA1 pass that test as written — a fault shown
as workload is a false statement about whose work it is, and a consequential control dressed as chrome
is a false statement about what it does. TC1, TC2 and TA2 are admitted by a **second question, added
by this standard**: *does the page ask a person to spend attention or effort that its own design has
made unnecessary?* That is not a look-and-feel question, and it is the one the five tests exist to
answer. Where a finding answers neither question, it is advisory — classify it that way and say so.

---

## 5 · The worked example — the listings queue, 2026-09-20

The design that produced this policy **fails all five tests**. It is kept here in full because a test
that cannot fail a real page is badly phrased.

| Test | What the design did | Verdict |
|---|---|---|
| TC1 | A filled black **Re-check** button on nine rows where the marketplace had already been asked three times and answered no. The press tells the system nothing it does not have; the system can re-ask on its own. | **FAIL** |
| TC2 | The *What is stopping it* column reads *"Below the price floor: the floor is £71.40 and the price is £62.00. Raise the price, or take it live below the floor."* Neither control is on the row. | **FAIL** |
| TA1 | The loudest control was the least consequential, nine times over — which is why a **Re-check all 9** link had to be invented beside it. The two decisions that cost money (raising a price above the floor, taking a listing live below it) sat behind a grey **Open**. The auto-approve switch, which decides whether listings go live with nobody looking, sat in the filter row styled as a view filter. The word **Terminal** sat in the action slot. | **FAIL** |
| TA2 | The group header stated the one thing stopping the group and every row repeated it in a paragraph; two columns carried the same fact in two voices; every row carried its own provenance stamp; the headline sentence and the three counts beside it stated the same numbers twice. About forty words per row to learn one thing. | **FAIL** |
| TF1 | A back-end drift defect — our record says live, the marketplace never received the offer — was rendered as the largest category of the operator's work, with a control beside it that existed only to compensate. A recommended price below our own price floor reached the queue as operator work; it is two of our numbers disagreeing. | **FAIL** |

**And the same page, designed well, passes all five.** The focal point is *two listings need a price
decision* — the answer, not an action, and the loudest thing on the page. Each of those two rows
carries the control that makes the decision, beside the sentence that names it, so nothing instructs
without a mechanism. Re-checking runs in the background; the page says *last checked 09:14* and offers
one quiet *check now* line for the group, because the operator sometimes knows the world changed. The
nine drifted listings are named as *a back-end fault — our records and the marketplace disagree*, owned
by engineering, counted apart from the operator's work, with no control offered against them. The
price-below-floor listing does not appear at all; it is a pricing-rule defect and it is routed as one.
Each row carries the short phrase that distinguishes it; the reasoning, the dates and the marketplace's
exact words are one layer down. The auto-approve switch is the second-loudest thing on the page.

---

## 6 · Enforcement, honestly

**PROBABILISTIC throughout.** Whether emphasis matches consequence, whether a category of work is
really a defect, and whether a fact was said twice or decomposed are reader judgements, and no check
makes them. A detector keyed on button styling or word counts would fire on ordinary work and be
switched off within a week — the failure `brief-binding-contract.md` §5 already names about its own
gates.

**The deterministic slice is narrow and real:** `tools/validate-prose-consumers.mjs` fails the fork's
suite if a consumer listed below stops referencing this file, and the five tests are rendered into
every outcome-first brief's Part 2 by `design-handoff`, so a reviewer is handed them rather than having
to remember them. The reviewer's verdict is still a reader's.

## Prose consumers

| Consumer | Bound how |
|---|---|
| `design-handoff` | §3j controls pass captures the expected controls and the fault split; Part 2 carries TC1, TC2, TA1, TA2, TF1 phrased for this surface; §4f-c renders the expected-controls table as advisory |
| `design-review-pr` | Truth-class checks `C-CONTROL-01`, `C-CONTROL-02`, `C-ATTENTION-01`, `C-ATTENTION-02`, `C-FAULT-01`; reported like the other truth checks |
| `design-implement` | Bundle→brief conformance gate halts on a broken one, same as the other truth tests |
| `design-synthesize` | Intake loads the five tests; step-06 self-critique judges them as failing-class sub-checks |
| `design-artifact-loop` | Intake parses them; screen-review violations carry `Binding: truth` when they break one |
| `design-review` | Live-page audit: a broken test is a `hard failure`, judged before the advisory passes |
| `design-tuning` | Iteration critic: FAIL only on a broken test; the advisory guidance in §4 is a note |
| `design-elevation` | A candidate that breaks one is hard-rejected; a candidate that removes a control failing TC1 is a legitimate elevation |
| `shared/claude-design-prompt.md` | The five tests go in the prompt's TRUTH half |
| `shared/brief-binding-contract.md` | Names this standard as the source of five further truth tests and of the second classification question |
