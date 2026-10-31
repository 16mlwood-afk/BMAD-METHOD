---
name: design-gate-artifacts
description: 'Canonical schemas for the two durable artifacts the three-gate design route emits — brief-adversary-*.md (Gate 1) and design-critique-*.md (Gate 3) — plus the review-binding SHA lifecycle, the Phase-1 warn-only contract and its one narrow exception, the Gate 2 hand-off, and the two entry points. Referenced by design-handoff step-03c (producer of the adversary artifact), design-tuning step-04 (producer of the critique artifact), and brief-revision-policy §9 (Gate 2 intake).'
---

# Design-gate artifacts — schemas, SHA lifecycle, and the Phase-1 contract

**Home of the route:** the design route has exactly three user-visible gates. The machinery
goes INSIDE the gates, not beside them — a mechanical checker, a cold adversary reviewer, a
disposition record and a re-check are internal mechanics of Gate 1, never five separate
steps a person has to remember. This file is the contract for what those gates leave behind.

| Gate | Question | Where it runs | Artifact |
|---|---|---|---|
| **1 · Brief-ready** | Does this exact brief contain unresolved material brief-visible defects? | `design-handoff` step-03c — after the brief is written, BEFORE step-04 delivers it | `brief-adversary-{target_slug}-{date}.md` |
| **2 · Revision-route** | Is the correction editorial or material? | `brief-revision-policy.md` §9 | (no new artifact — the policy's own supersession/amendment record) |
| **3 · Design-closure** | Is this finding a brief gap, an explicit-brief design violation, an implementation/data concern, or a visual concern? | `design-tuning` step-04 — after the first generated design | `design-critique-{target_slug}-{date}.md` |

---

## 1. Two entry points — and Gate 1 is for DRAFTS only

**New work** runs the whole route with no instruction beyond the original task:

```
draft brief → [Gate 1] → Claude Design / design-synthesize → [Gate 3] → close
```

**Backlog work** does NOT go through Gate 1:

```
existing design → [Gate 3] → classify each finding
                       ↓ any ACCEPTED brief-gap finding
                 [Gate 2] → editorial amendment OR material supersession
                       ↓
                 one corrected generation → close
```

**Why backlog briefs are never forced through Gate 1.** A delivered brief already carries a
capability contract that was expensive to establish and is usually correct. Re-running the
full route recreates it from scratch and risks losing it. Enter at closure and classify what
was actually found.

**And a draft brief has no supersession problem.** It has not been delivered, so a Gate 1
defect is edited in place. **Gate 2 is not consulted at Gate 1, ever** — invoking it on an
undelivered draft is what turns a two-minute text fix into a supersession chain.

---

## 2. Phase 1 is WARN-ONLY — and warn-only is NOT uniform

Two different things can come out of a gate, and they are handled differently. Both halves
must be stated on every artifact and in every consumer-facing message.

### 2a. Technical / instrument results — warn-only, never blocking

A fired probe, an adversary finding, a checker result, a classification, a disposition: these
are **observations**. They are recorded in the artifact, surfaced in the close-out, and the
ordinary handoff continues. **No instrument result blocks delivery in Phase 1.** A gate that
blocks on findings before its precision is measured is a gate that gets switched off.

### 2b. A genuine missing OWNER product/design decision — PAUSES the affected handoff

This is the one narrow, deliberate exception, and it must be named as such wherever it fires:

> **This is not the gate blocking on findings. It is the route refusing to guess a decision
> that is the owner's to make.**

When the gate finds a defect whose correction requires a value **nobody has decided** — a row
budget with no authority source, a placement rule that does not exist, a policy question the
brief cannot answer from anything in hand — then:

- **do NOT invent the value**, in the brief or anywhere else;
- **do NOT hand the contract to Claude Design with the decision silently unresolved**;
- **PAUSE the affected brief / design handoff**, surface exactly that decision to the owner,
  and resume when it is answered.

Everything else about the run still completes: the artifact is written, the technical
warnings are recorded, and other surfaces in flight are unaffected. The pause is scoped to
the brief or design whose contract is incomplete.

**Mason sees exactly one thing from a gate: a genuine missing product or design decision.**
Not a findings list, not a score, not a dispositions table. If there is no such decision, the
gate passes silently and the work goes forward.

### 2c. Phase 2 is a separate owner decision

Promoting Gate 1 or Gate 3 from warn-only to blocking-on-findings is **an owner decision that
has not been made**, and no agent may make it by editing a step file. The evidence it needs:

1. a corrected, **pre-registered** fixture run for `check-brief-readiness.py` (F1 run 2 — the
   two ported fixes are candidate fixes, not measured improvements);
2. an adjudicated precision figure for the adversary reviewer over real briefs, with the
   adjudicator independent of the reviewer;
3. a run of gates that produced **zero** false owner-pauses — because a false pause is far
   more expensive than a false warning.

---

## 3. The review-binding SHA — lifecycle

A review is only about the text it read. So every gate artifact records the SHA-256 of the
**brief body with the YAML frontmatter EXCLUDED**.

**One implementation, never a hand-rolled recipe:**

```bash
python3 ~/bmad-method-v6/tools/check-brief-readiness.py <brief.md> --body-sha
```

The same value appears in the checker's `--json` report as `body_sha256`. Two copies of a
hashing recipe is two hashing recipes; there is exactly one here.

**Frontmatter is excluded on purpose.** `last_modified_date`, `brief_status` and
`superseded_by` legitimately move without changing a single requirement — binding the review
to them would invalidate a valid review on a bookkeeping edit.

**Lifecycle rules:**

| Event | Consequence |
|---|---|
| Gate 1 runs | `brief_body_sha256` recorded in the artifact, both pre-repair and post-repair |
| Brief body edited after the review | **the review is INVALIDATED — the gate re-runs.** A recorded SHA that no longer matches the file is not a warning, it is a stale review |
| Frontmatter-only edit | review stays valid (SHA unchanged by construction) |
| Gate 3 runs | records the SHA of the brief the design was critiqued against, so a later reader can tell whether the critique was written against the brief that is now active |

**Ceiling, stated plainly:** the SHA proves WHICH TEXT was reviewed. It proves nothing about
the quality of the review.

---

## 4. Artifact schema — `brief-adversary-{target_slug}-{date}.md` (Gate 1)

Written by `design-handoff/steps/step-03c-gate1-brief-ready.md` into
`{implementation_artifacts}`, delivered in the same commit as the brief by step-04.

```yaml
---
type: brief-adversary
gate: gate-1-brief-ready
phase: 'Phase 1 — WARN-ONLY: no finding in this artifact blocked delivery'
target_slug: my-feature
brief: design-brief-my-feature-2026-08-10.md
brief_body_sha256: <64 hex>          # the text that was reviewed (frontmatter excluded)
brief_body_sha256_after_repair:      # empty when no auto-repair was applied
reviewed_by: isolated-adversary      # an agent that did NOT author the brief
review_date: 2026-08-10
checker_run_1: { fired: 7 }          # tools/check-brief-readiness.py, pre-repair
checker_run_2: { fired: 4 }          # post-repair; empty when no repair was applied
findings_total: 9
dispositions: { open: 1, auto_repaired: 4, routed_to_owner: 1, declined: 3 }
owner_decision_pending: true         # true ⇒ the brief handoff is PAUSED (§2b)
---
```

Body sections, in this order:

1. **Phase-1 status, in plain words** — one sentence stating that instrument findings did not
   block delivery, and whether an owner decision is pending. Never omitted, never a footnote.
2. **What was reviewed** — brief path, body SHA, checker version/run, and the explicit
   statement that the reviewer did not author the brief.
3. **Deterministic probe results** — the checker's fired probes, verbatim, with the standing
   caveat that **a fired probe is a QUESTION, not a defect**.
4. **Findings** — one block each: `class` (1 · brief-only | 2 · cross-artifact) · the probe or
   read that produced it · the **citation** (quoted brief line + line number, or the section
   where the requirement should be and is not) · what a generator will do with the gap · the
   sentence the brief should contain.
5. **Dispositions** — one row per finding, from the closed set below.
6. **Precision statement** — how many probes fired, how many were dismissed on inspection and
   why. A run that reports every probe as a defect has not been checked.

**Disposition enum (closed):**

| Disposition | Meaning |
|---|---|
| `auto-repaired` | Local, draft-only, and the correction's source was already in hand. Records the source. |
| `routed-to-owner` | A genuine missing product/design decision. Triggers the §2b pause. |
| `open` | Real, not repairable here, not an owner decision — carried forward as a named residue. |
| `declined-with-reason` | Not a defect. The reason is mandatory and specific — never "low severity". |

---

## 5. Auto-repair is bounded by EVIDENCE, not by confidence

A Gate 1 finding may be repaired in place **only** when its correction has a source already
in hand — a policy clause, the domain model, or the brief's own text elsewhere. The artifact
records that source for every `auto-repaired` row.

**A defect whose correction needs a value nobody has decided is NEVER auto-filled.** That
distinction is the whole safety property of the gate: the failure mode being guarded is not a
missed defect, it is an **invented number entering a durable contract** — which is exactly
what happened in the pilot when a row count nobody had decided was written into a brief.

Confidence is not evidence. "I am fairly sure the budget should be 50 rows" is the forbidden
move; it routes to the owner (§2b) instead.

---

## 6. Artifact schema — `design-critique-{target_slug}-{date}.md` (Gate 3)

Written by `design-tuning/steps/step-04-emit-critique.md` into `{implementation_artifacts}`.

```yaml
---
type: design-critique
gate: gate-3-design-closure
phase: 'Phase 1 — WARN-ONLY: no finding in this artifact blocked the correction pass'
target_slug: my-feature
brief: design-brief-my-feature-2026-08-10.md
brief_body_sha256: <64 hex>          # the brief the design was critiqued AGAINST
brief_status_at_critique: active     # active | superseded — read, never assumed
rendered_from: artifact-bundle       # artifact-bundle | screenshot | live-screen
treatment_evidence_mode: bundle-exact  # bundle-exact | screenshot-degraded
iteration: 1
correction_passes: 1                 # 1 = the bounded pass; >1 ⇒ classification REOPENED
lanes: { brief_gap: 2, brief_violation: 3, implementation_data: 1, visual: 4 }
routed_to_gate_2: [F1, F5]           # accepted brief-gap findings entering brief-revision-policy §9
owner_decision_pending: false        # true ⇒ the affected design handoff is PAUSED (§2b)
---
```

Body sections:

1. **Phase-1 status, in plain words** (same rule as §4.1).
2. **Provenance** — what was critiqued, against which brief, that brief's body SHA, and HOW it
   was rendered (bundle / screenshot / live screen) with the evidence mode. A treatment claim
   made in `screenshot-degraded` mode is marked `unverified-treatment` and cannot be certified
   resolved.
3. **Findings, each with exactly one lane** (closed set):

   | Lane | Means | Routes to |
   |---|---|---|
   | `brief-gap` | The brief did not determine this; the design filled the vacuum | **Gate 2** — `brief-revision-policy.md` §9 |
   | `brief-violation` | The brief stated it explicitly and the design broke it | `design-tuning` correction pass |
   | `implementation-data` | About data, wiring, or feasibility, not the design | the verification / spec route |
   | `visual` | Density, hierarchy, cramping, treatment | bounded `design-tuning`, or a recorded decline |

4. **Dispositions** — the same closed enum as §4, plus the lane.
5. **The bounded correction pass** — what it covered, and what it deliberately did not.

---

## 7. One bounded correction pass — and what a second pass means

Gate 3 routes each finding **once**, then runs **one bounded correction pass**. Not a loop.

An unexpected second correction pass **REOPENS Gate 3 classification**. Every new finding is
routed by evidence, in the same four lanes. **Do NOT presume the brief is wrong** — a second
pass is not evidence of a brief gap, and treating it as one is how a correct capability
contract gets rewritten to explain a rendering defect.

---

## 8. Gate 2 wiring — materiality is the OUTPUT, never the entry condition

An **accepted** `brief-gap` finding from Gate 3 enters the existing revision route at
`brief-revision-policy.md` §9. That route — and only that route — then decides between an
editorial amendment and a material supersession.

**Deciding materiality before the gate that decides materiality is the circularity this
replaces.** No workflow may filter findings by "is this material enough for Gate 2?".
Acceptance is the entry condition; materiality is the verdict.

Gate 2's status is honest: it is a **defined** route, not a proven one — the policy is written
and consumers carry intake checks against it, but it has not been exercised end-to-end through
this route.
