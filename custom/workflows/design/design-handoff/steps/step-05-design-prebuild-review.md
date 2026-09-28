---
name: 'step-05-design-prebuild-review'
description: 'The first paste to Claude Design asks it to REVIEW the delivered brief against the brief''s own tests before it builds anything. Findings are folded back into the brief; each finding that shows a gap in the TEMPLATE is appended to shared/brief-gap-ledger.md with the rule and the check added for it, so the template learns from every review.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-handoff'
thisStepFile: './step-05-design-prebuild-review.md'
---

# Step 5: Design pre-build review — the designer reads the brief before it draws

**Goal:** Catch what the brief left out while it is still a document. The designer is the best
reader a brief will ever have, because it is the one who has to act on every sentence. A gap found
before the build costs one revision of the brief; the same gap found after costs a design round and
a rebuild.

> **Owner, 2026-09-28, verbatim:** *"ensure this is systematic brief workflow fix not a one time brief
> patch."* The price-list v4 brief passed every Gate 1 check and Claude Design still found nine gaps
> in it when asked to review it first. Those nine are `shared/brief-gap-ledger.md` G1–G9, and each
> is now a template rule and a Gate 1 check. This step is how the next ones are found.

**Runs when** step-04 has delivered the brief and the next consumer is Claude Design. It does not
run for `design-synthesize` (the fork's own renderer reads the brief mechanically and Gate 1 already
checked it). It does not run for a `--no-deliver` brief: Claude Design reads the brief on `main`.

---

## 1. The first paste is a review, never a build

Hand the owner (or the Claude Design session) this paste, filled in. It is the whole of the first
message; the build prompt waits for §3.

```
Connect to {github_repo_url} and read `{output_path_relative_to_repo_root}` on main. Do NOT design
anything yet.

Review this brief against its own tests, as the person who has to build from it:
- Part 2 (T0, T1…Tn, TD0–TD2, TC1, TC2, TA1, TA2, TF1) and Part 2b (P1–P8, §9 completeness and §10 sections below the first item).
- For each frame the brief asks for: could you draw it from this document alone?

List every place you would have to GUESS, one numbered line each, saying what is missing and where:
a state with no layout, a view referred to but not described, a string not in the Copy deck, a list
whose order is not stated, a truncation with no rule for what survives, a width with no layout,
feedback after an action with no position or duration, a word budget with no room left, a mark in
the brief you are unsure whether to print, a sentence the Copy deck says twice, or anything else.

If you find nothing, say "No gaps." Do not start the design until the brief has been revised.
```

## 2. Fold every finding back into the brief

For each numbered finding:

1. **Classify it in one sentence.** *This brief* (the template asked for it and this brief got it
   wrong) or *the template* (nothing in `brief-template.md` asked for it, so every brief would miss
   it). A finding you cannot classify in a sentence is *this brief*.
2. **Fix the brief.** A revision under `shared/brief-revision-policy.md` (a `material_revision` only
   if the designer's answer changes what the surface is for; otherwise a correction to the same
   brief). Re-run Gate 1 (step-03c) — both `check-copy-screen.js --deck --strict` and
   `check-rendered-page.js --validate-brief` must exit 0 — and re-deliver (step-04).
3. **For a template finding, close the class in the same change, in the fork:**
   - add the rule to `shared/presentation-floor.md` §8 and the matching item to Part 2b §9 of
     `brief-template.md`;
   - where a machine can see the gap, add a Gate 1 check to `tools/check-rendered-page.js` with a
     failing and a passing golden in `test/test-rendered-page-check.js`;
   - append one row to `shared/brief-gap-ledger.md`: date, the gap as the designer said it, the brief
     it was found in, the rule added, the check added (or `none — <why a machine cannot judge it>`).
   - release it through the fork's normal release path, so the next brief in every project gets it.

   A template finding is never closed by fixing only the brief in hand. That is the failure this step
   exists to stop: the next brief for another page repeats the gap.

## 3. Then the build paste

When the revised brief is on `main` and Gate 1 is green, hand over the ordinary build prompt
(`step-04-deliver.md` §10, *For {consumer}*). Tell Claude Design which of its findings were fixed and
where, in one line each, so it builds from the revised brief rather than from its notes.

**A second review round is not the default.** Run one only when a finding changed what the surface is
for, or when more than a third of the findings were template gaps (the template was badly behind).

## RULES

- The review paste never asks for a design, and the build paste never goes first.
- Every template finding reaches the ledger with a rule. A ledger row without a rule is not written.
- Findings are not scored and not shown to the owner as a count. The owner hears what changed in
  the brief, in one line, and whether a decision is theirs.

## Enforcement, honestly

**PROBABILISTIC:** that this step runs, that a finding is classified correctly, and that a template
finding is closed rather than patched in one brief. No hook can see a Claude Design conversation.
**DETERMINISTIC:** once a gap is in the ledger with a check, Gate 1 fails every later brief that has
it (`tools/check-rendered-page.js --validate-brief`), and `npm run test:rendered-page` fails if a
seeded ledger row stops naming its check.
