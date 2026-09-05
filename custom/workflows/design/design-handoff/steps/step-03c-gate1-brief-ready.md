---
name: 'step-03c-gate1-brief-ready'
description: 'Gate 1 — brief-ready. Runs the deterministic brief probes, spawns an ISOLATED adversary reviewer bound to the exact brief body by SHA-256, auto-repairs only evidence-backed draft-only defects, re-checks, and emits brief-adversary-{target_slug}-{date}.md. WARN-ONLY in Phase 1 for every instrument result; the ONE exception is a genuine missing owner product/design decision, which pauses this brief.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-handoff'
thisStepFile: './step-03c-gate1-brief-ready.md'
---

# Step 3c: Gate 1 — brief-ready

**Goal:** answer ONE question about the brief step-03 just wrote —

> **Does this exact brief contain unresolved material brief-visible defects?**

— then either resolve them here, or surface the single thing that is genuinely the owner's to
decide. Everything in this step is an INTERNAL MECHANIC of that one gate: the checker, the
cold reviewer, the SHA binding, the repair, the re-check and the dispositions are never
presented as separate steps or separate approvals.

**Runs after step-03 (brief written) and BEFORE step-04 (deliver).** The brief has not been
delivered yet, which is exactly why this is the cheap place to fix it.

Contract for the artifact this emits, the SHA lifecycle, the disposition enum and the
Phase-1 rules: **`shared/design-gate-artifacts.md`** — do not restate them here.

---

## SCOPE — DRAFTS ONLY. Never run this on a backlog brief.

Gate 1 applies to a brief **this run produced** and has not yet delivered.

- **New work** → the full route: draft brief → Gate 1 → Claude Design → Gate 3 → close.
- **Backlog work** → enters at **Gate 3** (`design-tuning` step-04), is classified there, and
  only an accepted brief-gap finding reaches Gate 2. **Do NOT force an existing delivered
  brief through this step.** A delivered brief already carries a capability contract that was
  expensive to establish and is usually correct; re-deriving it risks losing it.
- **Gate 2 is NOT consulted here.** A draft has no supersession problem — defects are edited
  in place. Invoking the revision route on an undelivered draft is what turns a two-minute
  text fix into a supersession chain.

**Skip conditions** (record which one fired, then go straight to step-04):

- the run is `--no-deliver` **and** the operator asked for no gate (the gate is still useful
  on an undelivered brief, so `--no-deliver` alone does NOT skip it);
- `--no-gate1` in the invocation;
- `gates.design-handoff-gate-1: skip` in `_bmad/bmm/config.yaml`.

---

## AVAILABLE STATE

From step-03: `{output_path}` · `{output_filename}` · `{target_slug}` · `{feature_name}` ·
`{route}` · `{page_mode}` · `{change_class}` · `{handoff_mode}`.
From config: `{implementation_artifacts}` · `{date}` · `{autonomous_mode}`.

Set by this step: `{gate1_artifact_path}` · `{brief_body_sha}` · `{brief_body_sha_after_repair}` ·
`{gate1_owner_decisions}` (list; empty is the normal case) · `{gate1_paused}` (boolean).

---

## EXECUTION SEQUENCE

### 1. Run the deterministic checker and bind the review to the text

```bash
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{output_path}" --json > /tmp/gate1-run1.json
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{output_path}" --body-sha
```

Record the SHA as `{brief_body_sha}`. **Use `--body-sha`; never hand-roll a hashing recipe** —
the checker's report carries the identical `body_sha256`, and two recipes drift.

If the checker is not present in this project (it lives in the fork's `tools/`, which not
every project syncs), record `checker: unavailable` in the artifact and continue with the
reviewer alone. **Do not silently skip and report a clean run** — an absent instrument is an
absent instrument, not a pass.

**A fired probe is a QUESTION, not a defect.** Do not put the fired count in front of the
owner, do not treat it as a score, and do not repair a probe simply because it fired.

### 2. Spawn an ISOLATED adversary reviewer

**This separation is the single strongest finding of the pilot, and it is not optional:** a
self-graded brief misses its own contradictions. The agent that wrote the brief cannot be the
agent that reviews it, and the reviewer must not be handed the author's reasoning.

Spawn ONE isolated agent (`Agent` tool, fresh context) with:

- the brief **file path only** — it reads the file itself, so the review is bound to the text
  on disk rather than to a summary;
- the checker's JSON report, framed explicitly as *questions to resolve, not defects*;
- the project design policy path (`docs/design-policy.md`) and
  `shared/design-standards.md` — the reviewer must be able to CHECK an inherited rule rather
  than assert one. In the pilot the adjudicator resolved a contested finding by opening the
  policy and reading the clause the reviewer had only asserted;
- **no** step-01/step-02 gather state, no authoring rationale, no draft history.

**Reviewer contract** — restate these to it verbatim:

1. **Every finding cites brief text** — the conflicting line quoted with its line number, or
   the section where the requirement should be and is not. A finding with no citation is
   deleted, not softened. *(Pilot: one finding cited a blank line; another cited a line that
   supported a different intent. Both survived only because the finding did not rest on them.)*
2. **A brief that got it right is not a defect.** If the brief states a requirement clearly
   and a design violated it, that is a finding against the DESIGN (Gate 3, lane
   `brief-violation`) — never a finding against the brief. Confusing these inflates recall and
   destroys precision.
3. **Absence must be CHECKED, not assumed.** Search the whole brief for the concept under its
   likely synonyms before reporting it missing. "Not in the section I expected" is not
   "missing".
4. **Do not invent a requirement the surface does not need.** A missing requirement is a
   defect only when the brief's own stated job needs it.
5. **Class 1 only** (answerable from the brief text alone), plus class 2 (brief + rendered
   frames) when frames exist. **Class 3 — cramping, density, hierarchy, anything that needs
   pixels — is OUT OF SCOPE BY CONSTRUCTION.** Claiming a class-3 finding from a brief is a
   manufactured defect and is the primary failure mode of this instrument.
6. **Report internal contradictions first.** A brief that argues a thesis in one section and
   specifies a control contradicting it in another is the highest-value catch, because a
   generator follows the specification and ignores the thesis.
7. **End with a precision statement** — probes fired, how many were dismissed on inspection,
   and why. A run that reports every probe as a defect has not been checked.

Record the reviewer's output verbatim in the artifact. **Do not edit its findings into
agreement with the brief.**

### 3. Disposition every finding

Assign exactly one disposition per finding from the closed enum in
`shared/design-gate-artifacts.md` §4: `auto-repaired` · `routed-to-owner` · `open` ·
`declined-with-reason`. Every `declined-with-reason` carries a specific reason — "low
severity" is not a reason.

#### 3a. Auto-repair is bounded by EVIDENCE, not by confidence

Repair a finding in place **only** when ALL of these hold:

- it is **local** — one sentence, one row, one clause; not a re-composition;
- it is **draft-only** — this brief has not been delivered, so nothing downstream has consumed
  the text being changed;
- the correction's **source is already in hand**: a policy clause, the domain model, or the
  brief's own text elsewhere. Name that source in the artifact row.

**A defect whose correction needs a value nobody has decided is NEVER auto-filled.** Not with
a plausible default, not with a "typical" figure, not with a value inferred from a sibling
surface. In the pilot exactly this failure put an **invented row count into a durable
contract**. Confidence is not evidence; if the source cannot be named, the disposition is
`routed-to-owner`, not `auto-repaired`.

Structural fields are never auto-repaired: `frames`, `route`, `composition`, `page_mode`,
`shell_role`, `surface_part`. A change to any of those is a scope decision, not a correction.

#### 3b. Re-run the checker on the repaired text

```bash
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{output_path}" --json > /tmp/gate1-run2.json
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{output_path}" --body-sha
```

Record BOTH results in the artifact, and the post-repair SHA as
`{brief_body_sha_after_repair}`. A repair that fires a new probe is a real signal — do not
suppress it, and do not repair the new probe reflexively.

**If no repair was applied, run 2 is empty — not a copy of run 1.** An identical pair of runs
reads as corroboration of something that never happened.

### 4. Emit `brief-adversary-{target_slug}-{date}.md`

Write it to `{implementation_artifacts}` using the schema in
`shared/design-gate-artifacts.md` §4 (frontmatter + the six body sections, in order). Set
`{gate1_artifact_path}`.

**The Phase-1 status is section 1 of the body and a frontmatter field — both, in plain
words.** Nobody reading this artifact may mistake observation for enforcement.

### 5. Route ONLY a genuine missing product/design decision to the owner

**Mason sees exactly one thing from this gate: a genuine missing product or design decision.**
Not a findings list. Not a score. Not a dispositions table. Not the artifact.

A finding is owner-routed when its correction requires a value **nobody has decided** and no
authority source exists for it — a row budget with no basis, a placement rule that does not
exist, a policy question the brief cannot answer from anything in hand. The archetype is a
bounded-density rule with no value and no authority source: that is **one owner decision**,
and it is exactly what this gate is allowed to interrupt for. It is **not** a reason to add a
gate.

For each, surface: the decision in one sentence · why the brief cannot answer it · what a
generator will do if it is left unanswered · and (where they exist) the concrete options.
**Never a recommendation dressed as a default.**

If `{gate1_owner_decisions}` is empty, **the gate passes silently.** Say nothing beyond the
artifact path in the close-out. A gate that announces itself on every clean run is a gate
people learn to skip.

### 6. Phase-1 disposition — what blocks and what does not

> **WARN-ONLY IS NOT UNIFORM. Split it, and say which half you are in.**

**6a. Instrument results NEVER block.** A fired probe, an adversary finding, an `open`
disposition, a checker that could not run: all of these are recorded and **step-04 delivery
proceeds normally**. There is no finding count, no severity, and no combination of findings
that stops delivery in Phase 1.

**6b. A `routed-to-owner` decision PAUSES this brief.** Set `{gate1_paused}` = true, and:

- do **not** run step-04 for this brief;
- do **not** invent the value;
- do **not** hand the contract to Claude Design with the decision silently unresolved;
- surface the decision (§5), and resume at step-04 when it is answered.

State plainly, wherever this fires: **this is not the gate blocking on findings — it is the
route refusing to guess a decision that is the owner's to make.** The pause is scoped to this
brief; other surfaces in flight are unaffected, and the artifact is written either way.

**In `autonomous_mode`, 6b still pauses.** Autonomy covers method decisions, not the owner's
product decisions — inventing the value is the exact failure the pause exists to prevent.

**6c. Promotion to Phase 2 (blocking on findings) is a separate owner decision** and no agent
may make it by editing this step. The evidence it needs is listed in
`shared/design-gate-artifacts.md` §2c.

### 7. Invalidation — an edited brief invalidates its review

The review is about the text it read.

- Before step-04 stages the brief, **recompute `--body-sha`**. If it differs from
  `{brief_body_sha_after_repair}` (or `{brief_body_sha}` when no repair ran), **the review is
  INVALID and this gate re-runs.** A recorded SHA that no longer matches the file is not a
  warning; it is a stale review presented as a current one.
- Frontmatter-only edits do not invalidate anything — the digest excludes frontmatter by
  construction, so `last_modified_date` and supersede bookkeeping move freely.

### 8. Hand to step-04

Pass `{gate1_artifact_path}` forward. Step-04 stages the adversary artifact **in the same
commit as the brief** (`git add -f`, same as the analytics rationale) so a brief on `main`
always has its gate record beside it.

The close-out mentions Gate 1 in at most one line, and only when it has something to say:
the artifact path, plus any owner decision that is pending. **Claude Design never reads this
artifact** — it reads the brief.

---

## RULES

- **This step is an internal mechanic of ONE gate.** Never present the checker, the reviewer,
  the repair and the re-check as four things a person has to track. The goal of the whole
  route is gate REDUCTION.
- **The reviewer must not be the author.** A self-graded brief misses its own contradictions;
  that is the finding this step exists to institutionalise.
- **Auto-repair is bounded by evidence, not confidence** (§3a). The failure mode being guarded
  is not a missed defect — it is an invented value entering a durable contract.
- **A fired probe is a QUESTION, not a defect**, everywhere it is surfaced.
- **Warn-only, with one named exception** (§6). Do not widen the exception to "important"
  findings; the exception is *missing owner decision*, not *serious defect*.
- **Never run on a backlog brief.** Backlog enters at Gate 3.

---

## FAILURE MODES

- **Reviewing your own brief.** The one thing this step is for, undone.
- **Auto-filling a value nobody decided.** Observed in the pilot: an invented row count
  entering a durable contract. Route it to the owner instead — always.
- **Putting the findings list in front of the owner.** The owner gets decisions, not evidence
  of work. A dispositions table handed over is a gate that has failed at its own purpose.
- **Blocking delivery on a finding in Phase 1.** Promotion is an owner decision; a step file
  is not where it happens.
- **Proceeding past a missing owner decision because the run is autonomous.** The pause is
  narrow precisely so it can be absolute.
- **Copying run 1 into run 2 when nothing was repaired.** Two identical runs read as
  corroboration of a repair that never happened.
- **Recording a review against a brief that has since been edited.** Recompute the SHA at
  step-04; a stale review is worse than no review, because it looks like coverage.
