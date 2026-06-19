---
name: 'step-03b-review'
description: 'Adversarially review the just-built workflow against the durable principles — including the context budget and (when it owns policy or routes between skills) the policy-skill/router quality rules — and fix every blocking issue before wiring'
---

# Step 3b: Adversarial Review

**Progress: Step 3b of 4** — Next: Wire & Verify (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction, no menus. But this step DOES gate the pipeline: a blocking issue is fixed here and re-reviewed — you do NOT proceed to wiring with a known blocking issue.
- **ADVERSARIAL POSTURE.** Your job is to BREAK the workflow you just built, not to confirm it. Assume it is flawed and hunt for the flaw. A freshly generated workflow that produces zero findings on the first pass means you did not look hard enough — look again.
- **REVIEW THE ARTIFACT, NOT YOUR INTENTIONS.** Re-read every file from disk as if a different author wrote it. Do not give yourself credit for what you "meant" to do.
- **Prefer a fresh, isolated reviewer.** If sub-agents are available, delegate the review to one with the rubric below: a clean context is genuinely independent AND keeps the heavy re-read out of the builder's context — the same context-budget discipline this workflow now enforces. If sub-agents are not available, re-read the files yourself under the adversarial posture above.

## AVAILABLE STATE

From Step 3:

- `{wf_target_dir}` — the workflow directory and all files written
- `{wf_step_design}`, `{wf_autonomous}`, and whether the workflow consumes/produces briefs

## STATE VARIABLES (set in this step)

- `{wf_review_verdict}` — the structured review result (Blocking [resolved] / Concerns / Nits), surfaced in Step 4's completion report

## SEQUENCE OF INSTRUCTIONS

### 1. Re-read every file from disk

List and read every file under `{wf_target_dir}` — `workflow.md`, every `steps/*.md`, `template.md`, `checklist.md`. Read them fresh; do not rely on memory of what you wrote in Step 3.

### 2. Attack against the durable principles

For `workflow.md` and each step file, try to find a concrete failure on each axis. **Cite the specific file + section for every finding.**

- **Context budget** (the axis this workflow now enforces): count the hard must-dos per step — more than ~10 is `overdense-step` (the step is doing more than one job; split it). Find any inlined corpus that should be a pointer (`inlined-corpus`). Find load-bearing constraints buried mid-step instead of at the top + restated at their point of use (`buried-constraint`). Find a read-heavy / multi-file / research step that inlines its corpus instead of delegating to a sub-agent that returns a distilled artifact (`undelegated-read`). Confirm every step is one job.
- **Grounding** — if the workflow accepts user input, can Step 1 state verb + target from the input alone? If not, does it halt rather than guess?
- **Autonomy scoping** — does any step infer what the user "meant" (intent autonomy) rather than making implementation decisions (decision autonomy)? Inferring intent on a missing or ambiguous input is a blocking flaw.
- **Provenance** — if the workflow consumes briefs, are the 6 intake checks present before any consumption? If it produces briefs, is the full provenance emission present?
- **Greenfield-in-brownfield** — does any step assume PRD/epic/story artifacts that may not exist in maintenance work?
- **Structural** — a `nextStepFile` pointer that doesn't resolve, a state variable consumed before any step produces it, a phase-count/name mismatch in `workflow.md`, or leftover placeholder/TODO text.
- **Policy-skill / router** — applies ONLY when the new flow **owns policy** (it encodes necessity, materiality, domain ownership, or safety/correctness — i.e. *when it should engage at all* and *who owns a decision*) OR acts as a **router** that dispatches between skills/sub-flows. Skip this axis for a plain mechanical-transform workflow. When it applies, require the workflow to declare, near the top of `workflow.md`: its **purpose / ownership / "do not use when"** (a plain-language materiality gate — use / don't-use / if-uncertain — not domain jargon), any **skill dependencies** (`uses_skills:` — the skills it leans on, by name), and an **abstain behavior** ("if uncertain, abstain by …" — it must never guess a policy call). Then, for any NEW skill this workflow introduces or requires, confirm it follows the policy-skill creation rules: a plain-language invoke block (`missing-invoke-block`), every declared mode wired to a real caller (`dormant-mode`), sister-skill symmetry within its domain family (`asymmetric-sibling`), and routing documented both ways — the skill names its callers and each caller defers by name (`undocumented-routing`). A missing declaration or an unwired mode is a finding. For a full read-only sweep of the affected skills, **call the `policy-skills-healthcheck` skill** (it runs exactly these four checks and returns findings + proposed fixes — it does not modify anything).

### 3. Classify findings

Group exactly as a Mode 1 review does:

- **Blocking** — a durable-principle violation or a structural break that will make the workflow misbehave or ship wrong output.
- **Concerns** — likely problems, not violations (e.g. a step sitting at 9–10 must-dos, near the budget ceiling).
- **Nits** — style/consistency.

A context-budget overrun is a **Concern** by default, escalating to **Blocking** only when a step is so dense or so long that the workflow cannot reliably execute its own contract.

A policy-skill/router finding follows the doctrine's severity split: a **contract-breaker** (a new/changed policy-skill with no invoke block, a declared mode with no caller that consumers depend on, a caller re-deriving policy logic the skill owns, or a missing ownership/abstain declaration on a policy-owning flow) is **Blocking**; **structural debt** (a dormant mode, one-way routing, near-symmetry with a sister skill) is a **Concern** that must be named with a follow-up, never dropped silently.

### 4. Fix every blocking issue, then re-review

For each Blocking finding, edit the offending file to resolve it — split an overdense step into one-job-per-step, add the missing intake checks, re-anchor a buried constraint to the top + point of use, convert an inlined corpus to a pointer, add a sub-agent delegation, repair the step chain. After editing, **return to section 1 and re-review the changed files** (a fix can break the step chain or state-variable flow). Loop until zero Blocking findings remain. Concerns and Nits are recorded, not necessarily fixed.

### 5. Record the verdict

Store `{wf_review_verdict}` as the structured result (Blocking [now resolved] · Concerns · Nits). If you have gone more than 3 fix-and-re-review loops without converging, STOP looping and record the unresolved findings as Concerns with a recommendation to redesign the offending step by hand — a split that won't converge is itself a smell, not something to grind on.

### 6. Proceed to Wiring

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-workflow/steps/step-04-wire.md`

---

## SUCCESS METRICS

- Every file re-read from disk under an adversarial posture (ideally by an isolated sub-agent)
- Every durable-principle axis checked, every finding citing a specific file + section
- Zero Blocking findings remain — all fixed and re-reviewed
- `{wf_review_verdict}` recorded for the completion report

## FAILURE MODES

- A confirmatory review ("looks good") instead of an adversarial one — a fresh workflow with zero first-pass findings means you did not look
- Grading your Step 3 intentions instead of the artifact actually on disk
- Proceeding to wire with a known Blocking finding
- Looping forever on a split that won't converge instead of flagging it for manual redesign
- Fixing one finding without re-checking that the fix didn't break the step chain or state-variable flow
