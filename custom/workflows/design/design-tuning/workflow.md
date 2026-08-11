---
name: design-tuning
description: 'Iterate on Claude Design output by comparing screenshots against the design brief, visual references, and corporate guardrails. Generates structured correction messages ready to paste back. Tracks violations across iterations.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Design Tuning Workflow

**Goal:** After Claude Design produces mockups from a design-handoff brief, iterate toward a design that meets all constraints. Compare each iteration's screenshots against the original brief, visual product references, and corporate guardrails — then generate a structured correction message the user can paste back into Claude Design.

**Your Role:** You are a design critic who evaluates AI-generated mockups against explicit written constraints. You catch constraint violations that Claude Design's visual priors override, track what's been fixed across iterations, and produce correction messages that are specific enough to get compliance on the next pass.

**Key Insight:** AI design tools have strong visual priors from training data (SaaS templates, Dribbble shots) that override written constraints. Negative constraints ("don't use bento grids") are weaker signals than positive references ("match the table density of {named reference product from project policy}"). This workflow combines both — it flags violations AND points to named product references from the project's `docs/design-policy.md` as positive anchors. The specific reference products vary by project; this workflow does not assume any particular ones.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All steps are autonomous — no user interaction after the screenshot(s) and (optionally) the design artifact URL are provided
- State persists via variables (see below)
- Sequential progression: load context (brief + policy + artifact source + canonical components) → analyze (artifact source for treatment, screenshot for composition) → generate correction
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
- `{artifact_url}` — The Claude Design artifact/share URL (or local design-synthesize bundle dir) under review, if provided. The source-of-truth for treatment-level checks (ring/opacity, radius, spacing, color, dot presence). Read directly — never inferred from the screenshot.
- `{artifact_source_dir}` — Local directory the artifact bundle was extracted to (step-01 §1c). Empty if no artifact source was provided.
- `{artifact_css_catalog}` — Per-component CSS property catalog extracted from the artifact source for the components under review (the treatment values: `border-radius`, `box-shadow`/ring, `padding`, `font-*`, `letter-spacing`, exact color, presence of a leading dot). The exact-value baseline step-02's treatment lane compares against.
- `{canonical_components}` — Map of treatment-class (status-pill, badge, filter-chip, drawer, button) → the canonical component in THIS project's codebase plus its extracted classes/values. The §13 cross-surface reference, read from code, NOT from policy prose. This is what the iter-4 V18 miss lacked.
- `{treatment_evidence_mode}` — `bundle-exact` (artifact source ingested; treatment checks read exact values) or `screenshot-degraded` (no artifact source; treatment checks are downgraded to `unverified-treatment` and cannot be certified resolved). Mirrors design-review's `measurement_method` degraded-mode switch.

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

**The carve-out: a self-contained artifact bundle IS its own render — and pixels can't resolve sub-visible treatment.** The "rendered beats source" rule above guards against ONE specific danger: **untraced stylesheet override** in a live app, where the CSS you read may not be the CSS that wins at runtime. A Claude Design artifact bundle (or a design-synthesize bundle) has **no override surface** — it is self-contained; the JSX/`tokens.css`/inline styles you read ARE what renders, nothing overrides them. So the rule's premise does not hold for a bundle, and its conclusion does not apply. This splits the **evidence model** into two sources — and the two lanes below are named for them. (Step-02 §0a adds a third *check family*, the **content lane**, for the literal rendered values — casing, label form, identifier consistency. It sits on the *rendered* side alongside composition and uses the screenshot as its source, so it does not add a third evidence source and does not touch this carve-out; it exists so value-formatting defects stop falling between treatment and composition.)

- **Treatment lane → artifact source is authoritative.** Ring presence and opacity (`ring-{c}/20` vs `/30` vs none), `border-radius`, `padding`, `font-size`/`font-weight`, `letter-spacing`, exact color tokens, presence of a leading status dot. These are *sub-visible or sub-pixel* — a 20%-opacity 1px inset ring is invisible in a screenshot, so eyeballing it is a guess. Read the value from the bundle and compare it to the canonical codebase component (`{canonical_components}`). **This is the lane the iter-4 Amazon V18 miss lived in:** the pill was scored "resolved" off a PNG when a `ring-rose-500/20` divergence was sub-visible; reading the bundle source would have caught it as an exact-value mismatch.
- **Composition lane → screenshot is authoritative.** Layout, hierarchy, density, "is this a stat-card grid / bento / hero," whether an analytics band reads as subordinate. These are gestalt judgments the rendered image is genuinely the right input for, and the exact CSS would not tell you. The "rendered beats source" rule above governs this lane in full.

When no artifact source is available (`{treatment_evidence_mode} == screenshot-degraded`), the treatment lane has no exact-value evidence — its checks are downgraded to `unverified-treatment` and CANNOT be certified resolved (same honesty posture as the coverage gate). Do not silently fall back to pixel-guessing a treatment and call it resolved — that is the exact failure this carve-out exists to prevent.

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

- **Screenshot(s)** — dropped into the conversation (images from Claude Design's output). Authoritative for **composition** (layout, hierarchy, density, card-grid/bento/hero gestalt, band subordination).
- **Design artifact source** — *optional but strongly preferred*: the Claude Design artifact/share URL, or a local design-synthesize bundle directory. When present, treatment-level checks (ring opacity, border-radius, padding, font, color, dot presence) read the **actual CSS** from the artifact instead of guessing from pixels. Sub-visible details — a `ring-rose-500/20` inset ring is one pixel at 20% opacity, invisible in a PNG — are exactly what the screenshot cannot resolve and the source can. If the user pasted only a screenshot, ask once for the artifact URL; if unavailable, proceed in `screenshot-degraded` mode (treatment checks flagged unverifiable, per step-01 §1c).
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

## OUTPUT CONTRACT & VOICE SLOT

Emit the close-out per `shared/close-out-contract.md` (audience-first; process narration forbidden
by default; shape-feedback routes to a workflow patch). **The two-block shape in §2a binds here:**
block 1 is the plain answer; block 2 is at most one fenced `FOR YOUR LLM ADVISER` block, emitted
only when actionable technical detail exists, neutral and machine-shaped, never carrying a voice.

**The voice slot (`persona_slot`).** The agent executing this workflow MAY speak in its own voice
at exactly the three human-facing moments in `shared/workflow-personas.md` §2a — opening, a genuine
owner decision or pause, and close-out block 1. Here that is: the opening re-orientation, the
PARTIAL-STATUS status-for-the-user, and the close-out.

**Never in:** `steps/step-01-load-context.md` (declared `FULLY AUTONOMOUS`), `steps/step-02-analyze.md`,
the violation table, or the correction message's imperatives to Claude Design — those are directives
to a downstream consumer, not conversation. If no voice is bound these render plain and anonymous —
**today's behavior, unchanged.** This workflow names no persona; the binding is the project's.

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-01-load-context.md` to begin.
