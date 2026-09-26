# SENDBACK artefact contract — `design-implement` → Claude Design

**Home of the rule:** `workflow.md` Critical Rule *"Claude Design is the source of truth for
design — an implementer may not cherry-pick"*, and `steps/step-04-apply-and-deliver.md` §5c.
**Machine check:** `node ~/bmad-method-v6/tools/check-design-sendback.js --sendback <file>`.

---

## Why this artefact exists

**Owner ruling, 2026-09-26, verbatim:**

> *"u cherry picked from the design... this is very bad practice... claude design is the source of
> truth for design never do this again... if you wish to perform a SENDBACK/debate/ask any design
> Q's make this kind of SENDBACK formal okay?? so the iterative loop is between u two."*

An implementer that departs from the design on its own authority has taken a design decision. The
failure it names was **not concealment** — the two mapping-queue ledgers recorded every departure
honestly, in detail, with reasons. What was wrong is that a well-documented unilateral decision was
treated as a legitimate outcome. So a fix that only demands disclosure changes nothing; those runs
already disclosed. What this artefact adds is the **return leg**: the departure becomes a question
put to the designer, and the loop runs between implementer and designer until the design resolves
it.

**The artefact is PASTEABLE, and that is structural.** Claude Design cannot read this repository
(it is an external surface), so a sendback is delivered only when the owner has a self-contained
copy in front of him. Never write a sendback that references a repo path the designer cannot open
without quoting the material it depends on.

---

## Where it lives, and what it is named

`{implementation_artifacts}/SENDBACK-<target_slug>-v<next>.md`

`<next>` is the design revision this sendback is *requesting* — not the one it responds to. A
sendback against `v2` asking for changes is `…-v3.md`, because the artefact's job is to specify the
next design version. Two sendbacks against the same version in one day take a `-b` suffix rather
than overwriting: a sendback is a snapshot of what was asked and when, and a second one sits beside
the first.

---

## Frontmatter — required, and the checker reads it

```yaml
---
type: design-sendback
target_slug: <kebab-case surface id>
route: <the app route, or n/a>
responds_to: "<the design source this answers — artefact dir / .dc.html file, or the URL>"
ledger: <path to the design-implement apply ledger or grid artifact that raised these departures>
verdict_record: <path to the step-02b preflight artefact, or n/a — no halt>
brief: <brief filename (brief_status: <state>), or no_brief>
baseline_commit: <SHA the departures were measured against>
date: <YYYY-MM-DD>
departures: <integer — how many ledger rows this sendback answers for>
asks: <integer — §4 numbered asks>
owner_questions: <integer — §5 items>
---
```

`departures` must equal the number of ledger rows disposed `⊘ departure(…)` / `⊘ interim(…)` that
cite this file. A sendback that answers for fewer rows than the ledger raised leaves a departure
standing on the implementer's own authority, which is the whole thing being stopped.

---

## The opening line — tell the reader what is in it before they read it

Two or three sentences, before any section, stating **(a)** what the implementation did and did not
ship, and **(b)** which sections exist so the designer does not spend the round re-deciding settled
material. The worked example's opening is the shape:

> *"v2 was not implemented. Nothing on the live page changed, and no test moved. … Read this as
> three asks and one question. Sections 1 and 6 exist so you do not spend any of v3 re-deciding
> things that are already settled."*

---

## The seven sections — all required, in this order

A section with nothing in it says so in one line (`None — …`). It is never omitted: an absent
section and an empty one read identically and mean opposite things, and §6 in particular is the
section a designer most needs when it is empty.

### 1. What the design got right, and the next version keeps

**This is scope, not politeness.** Everything carried forward unchanged, named, so no part of the
next round is spent re-deciding it. Be specific enough that the designer can recognise each item in
their own file.

### 2. Why it did not fully ship

The departures, as facts about the rendered output. For each: what the design specifies, what the
implementation renders instead, and **what a reader of the shipped surface then wrongly concludes**
— the consequence column, not the diff. A table is usually right here.

Where a brief carries preserved claims or truth tests, assert against the **rendered output**, never
against phrase presence: *"the phrase returns nought hits"* is evidence; *"the claim is covered
somewhere"* is not.

### 3. Why it happened, and where the gap was OURS

**The section an implementer is most tempted to skip, and the one that stops the loop repeating.**
If the design could not have known — a state it was never shown, a field that does not exist, a
policy rule that was not in the brief — say that plainly and say it is a defect in what we handed
over. Give the evidence that it was invisible rather than chosen.

Where the gap was genuinely the design's, say that too. This is not a section for absorbing blame;
it is a section for locating the cause so the next brief is better.

### 4. The asks — numbered, each naming what must be TRUE

One numbered ask per thing the next design version must resolve. Each ask says what must be **true**
and **names at least two acceptable shapes**, explicitly leaving the choice with the designer:

> *"**Two shapes that would work, and the choice is yours:** a fourth card class under Needs you, or
> a counted line under All good that names them. … If you see a third shape, take it — the test is
> whether the three facts can be read, not where they sit."*

**Dictating one shape is this artefact failing in the other direction.** The implementer's authority
is over what must be true, never over how it is drawn. An ask with exactly one acceptable shape is a
specification wearing a question mark, and the checker flags it.

Each ask carries the ledger rows it answers for, so the two records reconcile:
`answers: <row-id>, <row-id>`.

### 5. Questions that are the OWNER's, not the designer's

A question that turns on a commercial commitment, a product decision, an authority, or a fact no
system holds does not belong to the designer and must not be sent as an ask. Name it here, say
plainly that nothing in this round turns on the answer (or, if something does, say what), and route
it to the owner.

### 6. Already settled — do not spend this round on these

Departures and questions from earlier rounds that are **closed**, with their verdict: kept · accepted
· ruled against · superseded. This is the section that stops a designer re-arguing a decision the
owner already made, and it is the reason a sendback loop converges instead of oscillating.

Where a previous round's instinct was right but aimed one column over, say so — a ruling that
explains itself is one the designer can generalise.

### 7. Not for this round — for the next brief

What belongs in the handoff template or the brief rather than in this design revision, raised
separately, with *no action for the designer*. Keeps process improvement out of the design loop
while still recording it.

---

## What a sendback is NOT

- **Not a deferral record.** A design item simply not built yet is NOT YET BUILT and stays in the
  apply ledger as an honest deferral. Nothing goes to the designer, because nothing of ours is
  standing in the design's place. See step-04 §5c's test.
- **Not a bug report against the implementation.** A delta the implementer can and will fix is a
  grid row, applied. Only a place where we put our own judgement in the design's place is a
  departure.
- **Not a re-composition.** A sendback never ships the departure as the answer and asks for
  ratification afterwards. Where an interim behaviour is unavoidable — a policy hard failure, a
  field that does not exist — it is labelled **interim** in the ledger and in §2, so the design's
  version is still live as the thing to converge on.
