---
name: 'step-04-emit-critique'
description: 'Gate 3 — design-closure. Emits the durable design-critique-{target_slug}-{date}.md: provenance (what was critiqued, against which brief, that brief body SHA, how it was rendered), per-finding lane classification, dispositions, and the routing of accepted brief-gap findings into Gate 2. Extends design-tuning; it does not move or replace the correction-pass capability that already lives in steps 01-03.'
---

# Step 4: Gate 3 — design-closure

**Progress: Step 4 of 4** — Final step. Runs after step-03 has produced its correction /
approval / partial-status message.

**Goal:** answer ONE question about every finding this run produced —

> **Is this finding a brief gap, an explicit-brief design violation, an implementation/data
> concern, or a visual concern?**

— route each finding **once**, and leave the classification and its routing behind as a
durable artifact instead of as a conversation.

**This EXTENDS `design-tuning`; it does not move or replace it.** The correction-pass
capability already lives in steps 01–03 and is untouched. What is added is that the findings,
their lane, their disposition and their routing **survive as an artifact**. Before this step,
Gate 3's analytical capability existed but was manually driven and emitted nothing durable —
the one critique that survives from the pilot does so only because a person hand-wrote it into
the repo afterwards.

Artifact schema, lane enum, disposition enum, SHA lifecycle and the Phase-1 rules:
**`shared/design-gate-artifacts.md`** — do not restate them here.

---

## THIS IS ALSO THE BACKLOG ENTRY POINT

Two routes arrive here, and they are treated identically once they do:

- **New work** — draft brief → Gate 1 (`design-handoff` step-03c) → generated design → **here**.
- **Backlog work** — an existing design and an already-delivered brief enter the route **at
  this gate**. They are classified here, and only an **accepted `brief-gap` finding** reaches
  Gate 2. **A backlog brief is never forced through Gate 1** — it already carries a capability
  contract that was expensive to establish and is usually correct.

---

## AVAILABLE STATE

From steps 01–03: `{feature_name}` · `{brief_path}` · `{iteration_number}` ·
`{current_violations}` · `{fixed_violations}` · `{kept_elements}` · `{brief_drift}` ·
`{policy_overrides_brief}` · `{artifact_url}` / `{artifact_source_dir}` ·
`{treatment_evidence_mode}` · `{has_unresolved_issues}` · the step-02 §7 assessment.

Set by this step: `{critique_artifact_path}` · `{critiqued_brief_sha}` ·
`{gate3_lanes}` (counts per lane) · `{gate3_routed_to_gate_2}` (finding ids) ·
`{gate3_owner_decisions}` (list; empty is the normal case) · `{gate3_paused}` (boolean).

---

## SEQUENCE OF INSTRUCTIONS

### 1. Bind the critique to the brief it was written against

```bash
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{brief_path}" --body-sha
```

Record it as `{critiqued_brief_sha}`. **Use `--body-sha`; do not hand-roll a hashing recipe** —
Gate 1 records the same digest for the same brief, which is the only reason a later reader can
line the two artifacts up.

Also read the brief's `brief_status` from its frontmatter and record it verbatim
(`active` | `superseded`). **Read it; never assume it.** A critique written against a brief
that was superseded mid-flight is still a useful record — but only if it says so.

If the checker is unavailable in this project, record `brief_body_sha256: unavailable` and say
why. Do not substitute a different hash of a different span of text.

### 2. Record the render provenance — HOW the design was seen

The critique's authority depends entirely on what was actually looked at:

- `rendered_from`: `artifact-bundle` (a Claude Design artifact / `design-synthesize` bundle) |
  `screenshot` | `live-screen`;
- `treatment_evidence_mode`: carry `{treatment_evidence_mode}` forward verbatim.

**In `screenshot-degraded` mode every treatment-lane finding is marked
`unverified-treatment` and CANNOT be certified resolved.** This is the same honesty posture
step-01 §1c and step-02's treatment lane already take; the artifact makes it durable rather
than leaving it in a message that scrolls away.

### 3. Classify every finding into EXACTLY ONE lane

Route each finding **once**. The lanes are closed (`shared/design-gate-artifacts.md` §6):

| Lane | The finding says | Routes to |
|---|---|---|
| `brief-gap` | The brief did not determine this, and the design filled the vacuum | **Gate 2** — `brief-revision-policy.md` §9 |
| `brief-violation` | The brief stated it **explicitly** and the design broke it | the `design-tuning` correction pass (steps 01–03) |
| `implementation-data` | It is about data, wiring or feasibility, not the design | the verification / spec route |
| `visual` | Density, hierarchy, cramping, treatment | bounded `design-tuning`, or a recorded decline |

**The `brief-gap` / `brief-violation` distinction is the one that matters, and it is the one
most often got wrong.** A brief that stated a requirement clearly and was ignored is a finding
against the DESIGN. Filing it as a brief gap inflates the apparent defect rate of the brief and
sends a correct capability contract into a revision route it did not need.

**Every finding carries a citation.** For `brief-gap`: the section where the requirement should
be and is not. For `brief-violation`: the brief line, quoted, with its line number. A finding
with no citation is deleted, not softened — and **check the citation resolves**: in the pilot,
one cited line was blank and another supported a different intent entirely.

Assign one disposition per finding from the same closed enum Gate 1 uses:
`auto-repaired` · `routed-to-owner` · `open` · `declined-with-reason`.

### 4. Emit `design-critique-{target_slug}-{date}.md`

Write it to `{implementation_artifacts}` per `shared/design-gate-artifacts.md` §6 —
frontmatter plus the five body sections in order. Set `{critique_artifact_path}`.

**The Phase-1 status is body section 1 AND a frontmatter field, in plain words.** Nobody
reading this artifact may mistake observation for enforcement.

### 5. Route accepted brief-gap findings into Gate 2

For every **accepted** `brief-gap` finding, hand it to `brief-revision-policy.md` §9 and list
its id in `routed_to_gate_2`.

> **Materiality is the OUTPUT of Gate 2, never a precondition for entering it.**

Do NOT pre-filter by "is this material enough to be worth a revision?" — that is the
circularity this route replaces. Acceptance is the entry condition; Gate 2 decides editorial
amendment versus material supersession, and it is the only thing that decides it.

Nothing in this step edits a delivered brief. Gate 2 owns that edit, under its own rules.

### 6. ONE bounded correction pass

After routing, run **one bounded correction pass** — the existing steps 01–03 machinery, over
the findings routed to `design-tuning`. **Not a loop.** Record in the artifact what the pass
covered and what it deliberately did not.

**An unexpected second correction pass REOPENS Gate 3 classification.** Set
`correction_passes` accordingly, re-run §3 for every NEW finding, and route each by evidence.

> **Do NOT presume the brief is wrong.** A second pass is not evidence of a brief gap. Treating
> it as one is how a correct, expensively-established capability contract gets rewritten to
> explain what is actually a rendering defect.

### 7. Phase-1 disposition — what blocks and what does not

> **WARN-ONLY IS NOT UNIFORM. Split it, and say which half you are in.**

**7a. Instrument results NEVER block.** Findings, lanes, dispositions, `open` residue, an
unavailable checker: recorded, surfaced, and the ordinary flow continues. No finding count and
no severity stops the correction pass or the close-out in Phase 1.

**7b. A genuine missing OWNER product/design decision PAUSES the affected design handoff.**
Set `{gate3_paused}` = true and surface exactly that decision — one sentence, why the brief and
the design cannot answer it, what a generator will do if it stays unanswered, and the concrete
options where they exist. Do **not** invent the value, and do **not** send a correction to
Claude Design with the decision silently unresolved.

State plainly wherever this fires: **this is not the gate blocking on findings — it is the
route refusing to guess a decision that is the owner's to make.** In `autonomous_mode` it still
pauses; autonomy covers method decisions, not the owner's product decisions.

**7c. Promotion to Phase 2 (blocking on findings) is a separate owner decision.** No agent may
make it by editing this step; the evidence it needs is in `shared/design-gate-artifacts.md` §2c.

### 8. Surface — one line, plus any owner decision

Append to step-03's existing presentation, at most:

- the critique artifact path;
- the lane counts, one line;
- `routed_to_gate_2` ids, if any;
- **any pending owner decision** (§7b), which leads.

**If there is no owner decision, the gate is quiet.** The owner gets decisions, not evidence of
work — a dispositions table handed over is a gate that has failed at its own purpose.

---

## SUCCESS METRICS

- Every finding carries exactly one lane, one disposition, and a citation that resolves.
- The artifact records what was critiqued, against which brief, at which body SHA, and how it
  was rendered — so a later reader can tell whether it still applies.
- Accepted brief-gap findings reach Gate 2 **unfiltered by materiality**.
- Exactly one bounded correction pass, or an explicit record of why classification reopened.
- Phase-1 status is unmissable in both the frontmatter and the body.

## FAILURE MODES

- **Filing a `brief-violation` as a `brief-gap`.** Sends a correct brief into a revision route
  it did not need and inflates its apparent defect rate.
- **Pre-filtering brief gaps by materiality before Gate 2.** Deciding materiality before the
  gate that decides materiality is the exact circularity this route replaces.
- **Letting the correction pass become a loop.** One bounded pass; a second one reopens
  classification rather than continuing.
- **Presuming the brief is wrong on a second pass.** The most expensive failure available here.
- **Certifying a treatment finding resolved in `screenshot-degraded` mode.** A sub-visible ring
  or radius cannot be read from a PNG; it is `unverified-treatment`, not resolved.
- **Handing the owner the findings list.** They get the one decision that is theirs, or silence.
- **Emitting nothing durable.** The whole reason this step exists: before it, the classification
  survived only as a conversation.
