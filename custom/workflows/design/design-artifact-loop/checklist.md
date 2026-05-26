# Design Artifact Loop — Output Validation Checklist

Apply this checklist to every output artifact produced by `design-artifact-loop` before handing off. Step 3 of the workflow walks this list internally; the file is also a paste-ready audit aid for humans reviewing a chain.

Mode-locked sections only apply to their named mode; ignore unrelated sections.

---

## Universal (all modes)

- [ ] **Context block present.** The output's top section is the `## Context Block` with the eight required fields (Mode, Target, Source artifact, User/role, Frequency, Stakes, Out of scope, Sources consulted) and Evidence gaps.
- [ ] **Mode is named explicitly.** The first line under "Context Block" states `Mode: {mode}` matching the workflow's locked value.
- [ ] **Source artifact path resolves.** The `Source artifact:` line points to a real file at `{project-root}/{artifact_path}`.
- [ ] **All citations are real.** Every `Rule violated:`, `Source:`, or "Required correction" entry cites a section that exists in `docs/design-policy.md`, the canonical source artifact, or `design-standards.md`. No citations to `{user_summary}`, `{user_instruction}`, or "the screenshot."
- [ ] **No sister-skill prose inlined.** Sister skills are named in `Sources consulted` only — their bodies are not paraphrased into the output.
- [ ] **No invented hidden flows.** Where a screenshot suggests a problem but does not prove it, the issue is labeled "possible" rather than promoted to a confirmed failure.

## `screen-review` outputs

- [ ] **Verdict is one of:** `FAIL` | `PASS WITH ISSUES` | `PASS` | `INDETERMINATE`. `INDETERMINATE` appears only when Evidence Gaps include "no visual evidence."
- [ ] **Violations are ordered by severity.** hard failure → major → minor; within a severity, ordered by impact on comprehension, trust, and task flow.
- [ ] **V-IDs are stable across iterations.** If a prior screen-review of the same target exists, this output reuses the same V-IDs for unresolved issues; new issues get the next available V-ID.
- [ ] **Each violation block has every required field.** `Severity`, `Rule violated`, `Observed failure`, `Required correction`. `Do not change` is optional.
- [ ] **Anti-AI checklist is filled in.** All three checks have rationale on the same line. If any check is `[ ]`, a matching `hard failure` violation block exists above.
- [ ] **No "Exact changes to make" section.** Reviews state issues; they do not prescribe corrections at the implementation level. That's `refine-screen`'s job.
- [ ] **No "Get radical" or "Alternative layout" section.** Reviews are bounded.

## `design-handoff` outputs

- [ ] **Design Objective is bounded to mode.** One or two sentences; no "and while we're at it" expansions.
- [ ] **Every Exact Change item is concrete.** Names a file / component / region / token AND the change AND the citation. No "tighten this area" or "improve hierarchy" without a specific replacement.
- [ ] **Refine-screen mode only:** every Exact Change item ties back to a V-ID in the source screen-review.
- [ ] **Policy-lift mode only:** every Exact Change item cites a line in the policy delta.
- [ ] **What NOT to Change section present and non-empty.** Lifted from screen-review Keepers (when applicable) and explicit out-of-scope items.
- [ ] **Component / Route Targets section present.** Names the files or routes the implementer will touch.
- [ ] **Edge States section present.** Even if "no edge states required," that fact is stated explicitly.
- [ ] **No Route Changes section.** (Refine-screen mode forbids it.)
- [ ] **No Multi-step Flow section.** (Refine-screen mode forbids it.)
- [ ] **No wholesale primary-component replacement.** In refine-screen mode, no Exact Change rewrites the primary work surface, primary action area, or main filter row in full.

## `design-response` outputs

- [ ] **Brief Summary block restates the brief faithfully.** No new constraints or anti-patterns introduced.
- [ ] **Proposed Screen Structure uses domain language.** No "hero / cards / cta" template-default vocabulary.
- [ ] **Every open question from the brief is answered or marked OPEN.** No silent omissions.
- [ ] **Rationale ties back to brief sections explicitly.** Each major proposal cites Section 1 / 2 / 3 / 4 / 5 of the brief.
- [ ] **Implementation Handoff Note tells the next run what to do.** No vague "design it later" — a specific instruction for the second-pass invocation.

## Mode-scope (final cross-check)

- [ ] The output does not cross any "no" cell of the workflow.md Mode Scope matrix.
- [ ] If the output had to cross a "no" cell to be useful, the workflow emitted the scoping diagnostic in step 3 and produced NO artifact, rather than silently bending the scope.
