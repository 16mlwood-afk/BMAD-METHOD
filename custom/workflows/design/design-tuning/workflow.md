---
name: design-tuning
description: 'Iterate on Claude Design output by comparing screenshots against the design brief, visual references, and corporate guardrails. Generates structured correction messages ready to paste back. Tracks violations across iterations.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
---

# Design Tuning Workflow

**Goal:** After Claude Design produces mockups from a design-handoff brief, iterate toward a design that meets all constraints. Compare each iteration's screenshots against the original brief, visual product references, and corporate guardrails — then generate a structured correction message the user can paste back into Claude Design.

**Your Role:** You are a design critic who evaluates AI-generated mockups against explicit written constraints. You catch constraint violations that Claude Design's visual priors override, track what's been fixed across iterations, and produce correction messages that are specific enough to get compliance on the next pass.

**Key Insight:** AI design tools have strong visual priors from training data (SaaS templates, Dribbble shots) that override written constraints. Negative constraints ("don't use bento grids") are weaker signals than positive references ("match the table density of {named reference product from project policy}"). This workflow combines both — it flags violations AND points to named product references from the project's `docs/design-policy.md` as positive anchors. The specific reference products vary by project; this workflow does not assume any particular ones.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All steps are autonomous — no user interaction after the screenshot is provided
- State persists via variables (see below)
- Sequential progression: load context → analyze screenshot → generate correction
- Iteration state persists across invocations via a state file on disk

### State Variables

- `{feature_name}` — Feature being designed (from the brief)
- `{brief_path}` — Path to the design-handoff brief being iterated on
- `{iteration_number}` — Current iteration count (1-based, incremented each invocation)
- `{state_file_path}` — Path to the persistent iteration state file
- `{brand_identity}` — Contents of the project's brand identity document (if it exists). When present, this is the PRIMARY reference for evaluating design alignment — supersedes generic corporate guardrails.
- `{brand_identity_path}` — Path to the brand identity document
- `{brief_constraints}` — Hard constraints extracted from the brief (section 4 identity + section 5 constraints)
- `{hard_failures}` — Non-negotiable anti-patterns from the brand identity (section 8) or from the brief's guardrails
- `{visual_references}` — Named product references and what to borrow from each (from brand identity section 7, or user-provided)
- `{corporate_guardrails}` — Anti-patterns and hard failure conditions (from brand identity or brief section 4a — legacy compatibility)
- `{previous_violations}` — Violations from the previous iteration (empty on first run)
- `{current_violations}` — Violations found in the current screenshot
- `{fixed_violations}` — Violations that were present before but are now resolved
- `{kept_elements}` — Elements that work well and should be preserved
- `{correction_message}` — The paste-ready output for Claude Design

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **ALL STEPS ARE AUTONOMOUS**: Never halt, never present menus, never wait for input
4. **SAVE STATE**: Carry variables between steps and persist to state file
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **NEVER suggest layout or design ideas of your own.** You are a constraint enforcer, not a designer. Flag what violates the brief — don't propose alternatives unless the brief or visual references provide them.
- **Be specific.** "Badge colors exceed the 4-color limit" not "the colors feel wrong."
- **Track across iterations.** The value of this workflow is knowing what got fixed and what persists — without that, it's just a review.
- **Policy is authoritative; the brief is derivative.** If the brief explicitly allows something but the project design policy prohibits it, the policy wins — flag the violation. If the brief explicitly prohibits something the policy permits, the brief wins for this feature (the brief may narrow but not loosen). When in doubt, cite the policy.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow encounters conflicting guidance, the order of authority is:

1. **Project design policy** — `{project-root}/docs/design-policy.md` (canonical) or `{planning_artifacts}/brand-identity.md` (legacy slot). Loaded directly in step-01, NOT inherited transitively through the brief.
2. **Shared BMAD design standards** — `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails the policy can override but not contradict.
3. **Generated design brief** — `{brief_path}`. Derivative of (1) and (2). May restate, focus, or narrow the policy for one feature. May NOT introduce exceptions, softenings, or carve-outs the policy does not contain.
4. **Previous iteration state** — `{state_file_path}`. Derivative of (3). Cannot contradict higher levels.

**Brief drift is real.** Generated briefs sometimes insert editorializing parentheticals into hard rules ("Use Lucide icons or no icon at all. (But the codebase uses flag emoji so the designer may …)"). If design-tuning treats the brief as authoritative, that false exception propagates into correction messages and is then "fixed" in the wrong direction. Step-01 loads the policy directly to break that chain. Step-02 runs a contradiction scan between brief-derived constraints and policy-derived constraints; on conflict, policy wins and the drift is recorded.

**Rendered output beats source on rendering-level checks.** When the reviewer is evaluating a screenshot — and the source HTML/CSS (or a CSS comment claiming a behavior) disagrees with what the rendered pixels show — **the rendered pixels are authoritative**. A CSS rule like `.tile { border-left: 3px solid; background: transparent; }` may claim a single-shared-band rendering, but if the screenshot shows full-border rounded-corner cards, the rendering is the truth. The source disagreement is itself evidence — it signals a stylesheet override the reviewer hasn't traced, a markup mismatch, or a comment that no longer matches the code — and that disagreement is flagged as a sub-finding, not used to absolve the rendering. Reviewers reading the source instead of the rendering is the single most common failure mode this workflow exists to prevent. See step-02 §2's evidence-required rule and §1b's per-surface render inspection for the procedural enforcement.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `implementation_artifacts` path
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Input

The user provides:

- **Screenshot(s)** — dropped into the conversation (images from Claude Design's output)
- **Design brief reference** — either explicit ("tune against design-brief-foo.md") or implicit (workflow finds the most recent design brief)
- **Visual references** — either from a `visual-references-{feature}.md` file on disk, pasted inline from research (e.g., Perplexity output), or already stored in the state file from a previous iteration

If no brief is specified, find the most recent design brief:
```bash
ls -t {implementation_artifacts}/design-brief-*.md | head -1
```

### State File Resolution

The iteration state file lives at:
```
{implementation_artifacts}/design-tuning-state-{feature-slug}.md
```

- If the file exists → load previous state, increment `{iteration_number}`
- If the file doesn't exist → first iteration, `{iteration_number}` = 1

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-01-load-context.md` to begin.
