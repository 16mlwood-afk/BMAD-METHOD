---
title: 'Evidence — what the TheFBAPrep brief cost us (2026-09-19)'
description: 'Verbatim copy of the owner-side review notes on design-brief-thefbaprep-staging-dashboard, after the page was built twice. Dated evidence behind STD-BRIEF-BINDING-001 and the outcome-first brief template.'
---

<!--
  EVIDENCE FILE — verbatim, do not edit. Copied 2026-09-19 from the review notes supplied with the
  change request (brief-notes.md, sha256 57ac67015cc015f741b10d3e6d342b7916334d22e9e7471e1cf30a926adddb55).
  Only this comment and the frontmatter above were added (the frontmatter is required by the
  fork's docs build). Decision record: docs/decision-design-brief-outcome-first-2026-09-19.md.
-->

# What the brief cost us, and what to change

Notes on `design-brief-thefbaprep-staging-dashboard`, after building it twice
19 September 2026 · for the team that writes the briefs

---

We built the TheFBAPrep page to the brief, then built it again without the brief's formal constraints. The second one is better, and the interesting part is that it is better while keeping every substantive commitment the brief was written to protect. Nothing true was given up. What was given up was the brief's prescription of *how* those truths appear on screen.

That gap is worth explaining precisely, because the brief is not careless. It is unusually thorough, and the thoroughness is the problem: it spends its authority specifying rendering, and spends almost none establishing what the page is for.

## The flaws

### 1 · The brief names outputs, not a decision

It opens with eight frames, each with a contract key, and closes with a review gate that checks they exist. So the work becomes: produce eight artefacts that pass. Nowhere does it say what the operator is trying to find out when they open this page, or what they do next. Design without a stated decision has nothing to rank against, and the output shows it — three equal bands, eleven columns, no focal point. It is a correct page that does not answer anything.

> **Was:** Deliver eight frames: prep-mirror, prep-mirror--no-prep-feed, prep-mirror--stale-feed, prep-row-drawer…

> **Better:** The operator opens this page because they suspect the prep is holding less than they paid for. The page must answer that in one line, and give them the list to act on. Frames are yours to choose.

### 2 · Principles are written as mechanisms

The honesty commitments are the best thing in the brief. But they arrive as rendering rules rather than as things that must be true: every figure annotated inline with its document and that document's date; both authorities visible on every row; the freshness band permanent and non-dismissible. Each is defensible alone. Together they mandate a form, and the form was the failure.

Stated as a principle instead, the same commitment has better solutions available. In the second version the freshness caveat is not annotated onto each figure — it rewrites the headline. Under a stale, partial read the page's first line stops being "14 purchases are missing" and becomes "this page last saw the prep 15 days ago, and only part of it." That is stronger than an inline annotation, because an annotation can be read past and a headline cannot.

> **Was:** Every prep-side figure names the document it came from and that document's own date, inline, absolute.

> **Better:** A reader must never be able to mistake a stale or partial figure for a current one, including when they screenshot a single row. How you guarantee that is yours.

### 3 · Nothing is marked droppable, so nothing can be subordinate

Every requirement is mandatory and none is ranked. A page where everything must be visible is a page where nothing is emphasised; hierarchy is created by demoting things, and the brief forbade demotion. The second version puts fourteen rows at full weight and moves 288 unmatched rows, the 612-row mirror, and the whole provenance apparatus behind four quiet lines and a drawer. Same content, reachable in one click, no longer competing.

A brief can grant this cheaply: name the one thing that must dominate, and mark the rest as available-on-demand.

### 4 · Placement decisions are smuggled in as requirements

"Layer-1, permanent, non-dismissible" for the freshness band is a layout decision, made in a document that is not a layout. It reads as a requirement because it is phrased as one, and it is the single biggest contributor to the busyness: it hands the top of the page to metadata before the page has said anything. Requirements should constrain outcomes. Layer, order, and persistence are outcomes of design.

### 5 · The column set is implied, then denied

The brief never asks for eleven columns. It asks for both authorities on every row, their spelling, their word, their count, their on-hand figure, the source document, and our reading — which is eleven columns. Implied density is still specified density, and it arrives without anyone having decided it was worth the cost. Requirements framed as field lists should be checked against the table they force.

### 6 · Status vocabulary is fixed at the token level

Four tones, pill geometry to the pixel, fixed strings. This is component-library work appearing inside a product brief, and it pre-empts the option that turned out to be best: mostly not using pills. In the second version most readings are sentences — "five of their reports have been read since it left; none mentions it" — which carry the reasoning a pill can only gesture at. Reserve token-level spec for genuine system constraints, and say when a rule exists for consistency rather than for correctness, so it can be traded.

### 7 · Open questions are listed and simultaneously fenced

Six questions are named, each followed by an instruction not to draw anything for it. The effect is a brief that asks for a complete design while forbidding exploration of the parts that are undecided — and the honest answer to several of them is a sketch, not a sentence. Fencing them costs the reviewer the cheapest way to resolve them. Better: name the question and invite two options.

### 8 · The review gate rewards compliance

Contract keys, screen labels, frame inventory. All checkable, none of it about whether the page works. Whatever the gate measures is what the work optimises for, and a gate made of inventory produces inventory. Add one criterion the gate cannot count: can a reader state the page's answer within five seconds of it loading.

## What the second version did

Four moves, all of which the brief prohibited or crowded out.

**It answers in the first line.** "TheFBAPrep DE Leipzig — the prep's records are missing 14 of your purchases," at the app's own title scale, with three counts beside it. Everything below is either that answer's evidence or a way out to something else.

**It ranks.** Fourteen rows at full weight with a plain-English line each. The other 598 rows are a link.

**It moved disclosure from per-figure to per-page, and made it load-bearing.** One freshness line, and a headline that changes when the read is bad. Document dates, VAT basis, lot ids, raw exchanges all still exist, in drawers, complete.

**It writes sentences.** Most of the work the brief assigned to pills and columns is now done by short lines of prose, which cost less space and say more.

## What survived, unchanged

Worth stating plainly, because the fear behind a brief this prescriptive is that looseness loses the guarantees. It did not.

- The two authorities are still distinct — in language now rather than in a column rule.
- No figure is subtracted from another; the disagreement drawer shows 24 and 18 side by side and refuses to compute a variance.
- No prep-side number is invented where no feed exists; that state shows our purchases only and says so.
- Unknown VAT basis is still stated as unknown, with what would settle it.
- The rate with no recorded provenance still says so.
- A failed read is still the only red on the page.

Those are the commitments. They are all expressible as things that must be true, and none of them needed a layout to enforce it.

## The shape of a better brief

Roughly half the length, in five parts.

**The moment.** Who opens this, after what, to decide what. One paragraph. This is the part the current brief is missing entirely and the part everything else should hang from.

**What must be true.** The honesty commitments, written as tests a finished design either passes or fails — never as the mechanism that achieves them.

**What must dominate.** One thing. Everything else is explicitly available-on-demand, and the brief says so, so demoting it is not a violation.

**The data, and its defects.** This the current brief does well and should keep verbatim: what each feed contains, what it cannot tell you, which figures are derived, where the gaps are. Facts about the world, not instructions about pixels.

**Open questions, unfenced.** Named, with an invitation to answer two of them in sketch form.

Anything left over — pill geometry, colour tokens, layer order, column lists — either belongs in the design system or should be dropped. If a rule exists only for consistency, say so, so it can be traded against a better idea.

---

One line if it's useful in the room: *the brief specified the pencil strokes and forgot to say what to draw.* Everything it protected could have been protected by a page of tests, and the design would have been free to be good.
