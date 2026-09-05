# Design Artifact Loop — Output Validation Checklist

Apply this checklist to every output artifact produced by `design-artifact-loop` before handing off. Step 3 of the workflow walks this list internally; the file is also a paste-ready audit aid for humans reviewing a chain.

Mode-locked sections only apply to their named mode; ignore unrelated sections.

---

## Universal (all modes)

- [ ] **Mode header matches lock.** The output's top metadata line states `Mode: {mode}` matching the workflow's locked value.
- [ ] **Context block present and populated.** The `## Context` section has User, Frequency, Stakes, Source of truth / Source artifacts, Out of scope. Missing fields are rendered as `(not specified)` — never invented.
- [ ] **Source artifact path resolves.** The Source of truth / Source artifacts entry points to a real file at `{project-root}/{artifact_path}`.
- [ ] **All citations are real.** Every "Evidence", "Required correction" rule reference, or "Changes to make" citation points to a section that exists in `docs/design-policy.md`, the canonical source artifact, or `design-standards.md`. No citations to `{user_summary}`, `{user_instruction}`, or "the screenshot" alone.
- [ ] **Fixed vocabulary respected.** Verdict ∈ `{FAIL, PASS WITH ISSUES, PASS, INDETERMINATE}`. Severity ∈ `{hard failure, issue, polish}`. No alternative labels.
- [ ] **No sister-skill prose inlined.** Skills are named (in Skill routing used / Sources consulted); their bodies are not paraphrased.
- [ ] **No invented hidden flows.** Where a screenshot suggests a problem but does not prove it, the issue is labeled "possible" rather than promoted to a confirmed failure.

## `screen-review` outputs (Gate 3 + Dissent pass)

- [ ] **Top issues ranked V1 → V3 (V1 = most damaging).** V-IDs are stable across iterations of the same target; never re-numbered.
- [ ] **Each V-block has Evidence, Why it matters, Required correction.** No block is missing any of the three.
- [ ] **Severity in V-block parens** is `hard failure` | `issue` | `polish`.
- [ ] **Edge states named** (at least one — "all-zero state" / "all-action-required state" / etc.).
- [ ] **What to keep** is present if the screen has acceptable solved areas.
- [ ] **Out-of-scope reminder** present — boundaries that survive into the next refinement run.
- [ ] **Dissent pass footer present.** Format: `Dissent pass: completed; no re-ranking` OR `Dissent pass: completed; verdict demoted from {X} to {Y} because {reason}`. The pass may demote a verdict but may not upgrade.
- [ ] **No "Changes to make" section.** Reviews state issues; they do NOT prescribe corrections at the implementation level.
- [ ] **No "Get radical" or "Alternative layout" section.** Reviews are bounded.

## `design-handoff` outputs (Gate 4)

- [ ] **Objective is one paragraph bounded to mode.** No "and while we're at it" expansions.
- [ ] **Every "Changes to make" item is concrete.** Names a file / component / region / token AND the change AND the citation.
- [ ] **`refine-screen` mode:** every "Changes to make" item ties back to a V-ID in the source screen-review.
- [ ] **`policy-lift` mode:** every "Changes to make" item cites a line in the policy delta.
- [ ] **What not to change is present and non-empty.** Lifted from screen-review "What to keep" and explicit out-of-scope items.
- [ ] **Component / route targets are named** — at least one route AND at least one component path.
- [ ] **Edge states section present.** Even if "no edge states required," state it explicitly.
- [ ] **`## Skill routing used` block present and non-empty** when the output carries UI-facing guidance. Lists the actual skills invoked during step 3 (at minimum: `design-policy-canonical`; plus surface skills per the routing rules).
- [ ] **No route-change section in `refine-screen`.**
- [ ] **No multi-step-flow section in `refine-screen`.**
- [ ] **No wholesale primary-component replacement in `refine-screen`.**

## `design-response` outputs (Gate 4 + frontend routing)

- [ ] **Brief summary restates the brief faithfully** — no new constraints or anti-patterns introduced.
- [ ] **Proposed screen structure uses domain language.** No "hero / cards / cta" template defaults.
- [ ] **Every open question from the brief is answered or marked OPEN.** No silent omissions.
- [ ] **Constraints honored ties proposal choices back to brief / policy.**
- [ ] **Handoff note tells the next run what to do** — specific instruction for the second-pass invocation, not vague "design it later."
- [ ] **Sources consulted footer non-empty** with at least `design-policy-canonical` + `operational-finance-ui` + the frontend / webapp skill (per `design-from-brief` always-invoke rule).

## Approval gates (run order)

- [ ] **Gate 1 — Input validity** cleared (step 1): artifact exists on `main`, mode known, screenshots present if screenshot-led.
- [ ] **Gate 2 — Context sufficiency** cleared (step 1): all five context fields populated or explicitly marked missing.
- [ ] **Gate 3 — Review sufficiency** cleared (step 3, for review-only / refine-screen).
- [ ] **Gate 4 — Handoff readiness** cleared (step 3, before any `design-handoff` is emitted).
- [ ] **Gate 5 — Post-implementation acceptance** named in the step-4 handoff summary as the next agent's responsibility.

## Mode-scope (final cross-check)

- [ ] The output does not cross any "no" cell of the workflow.md Mode Scope matrix.
- [ ] If the output had to cross a "no" cell to be useful, the workflow emitted the scoping diagnostic in step 3 and produced NO artifact, rather than silently bending the scope.
