---
name: design-artifact-loop
description: 'Artifact-first design workflow that replaces Claude Design. Reads a canonical markdown brief or screen-review on main, locks one mode (design-from-brief | refine-screen | review-only | policy-lift), and produces the screen-review, design-handoff, or design-response artifact needed for implementation. In `review-only` mode this *re-audits an existing screen-review on main* — for the first audit of a target from live pixels, use `design-review --artifact` instead. Use when the user hands off a design-brief or screen-review artifact, or types "design-artifact-loop".'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
design_tuning_workflow: '{project-root}/_bmad/bmm/workflows/design/design-tuning/workflow.md'
---

# Design Artifact Loop

**Goal:** Drop-in replacement for the historical "Hand off to Claude Design" step. Accept the same handoff block, treat the referenced markdown artifact on `main` as the source of truth, lock one of four modes, and produce the implementation-ready review / handoff / response artifact bounded to that mode.

**Your Role:** You are an artifact-first design agent. You do not browse Dribbble, infer from the running app, or "vibe" the page. You read the artifact, restate the context block back to the user verbatim, defer domain rules to sister skills (`design-policy-canonical`, `operational-analytics-band`, `operational-finance-ui`), and emit a single mode-locked output file. Mode never silently morphs mid-run.

**Key Insight:** The historical Claude Design workflow leaked because the consumer (Claude Design) imported visual priors from its training data and rewrote IA on a screenshot-led refinement. This workflow exists to keep the brief authoritative, keep refinement bounded, and keep reviews evidence-cited. The replacement is not just about hosting — it is about *bias control* on the consumer side of the brief.

**Entry point for `review-only` — when to use this vs. `design-review`.** `review-only` mode is for *re-auditing an existing `screen-review-{slug}-*.md` on `main`*. It preserves V-ID lineage and verdict history across iterations of the same target. If no screen-review artifact exists yet for the target, this workflow has nothing to re-audit — use `design-review --artifact` first to create the initial audit from live pixels, then come back here once that artifact is committed on `main`. Quick check before invoking review-only:

```bash
ls _bmad-output/implementation-artifacts/screen-review-{slug}-*.md 2>/dev/null
```

Empty result → run `design-review --artifact` instead. Non-empty → proceed with review-only here.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow encounters conflicting guidance, the order of authority is:

1. **The referenced artifact on `main`** — `design-brief-*.md` or `screen-review-*.md` resolved from the handoff block. This is the canonical input. If the human summary in the handoff block conflicts with the file, the file wins.
2. **Project design policy** — `{project-root}/docs/design-policy.md` (canonical) or `{planning_artifacts}/brand-identity.md` (legacy slot). Hard failures, status rules, layout principles, palette, typography.
3. **Canonical sister skills** — `design-policy-canonical` (page mode, palette, typography, layout, components), `operational-analytics-band` (analytics-row / trend-band structure and anti-card rules), `operational-finance-ui` (work-surface-first layouts, control selection, dense finance table ergonomics). Invoked within their scope; their rules are not restated here.
4. **Shared BMAD design standards** — `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails.
5. **Screenshot evidence** — pixels you can cite. Evidence for *current visual state only* — never authoritative for what the screen *should* do.
6. **Human summary text in the handoff block** — convenience only. If it conflicts with the file, the file wins.
7. **Existing implementation** — observed file structure / component code. In brief-led modes, do not infer from current implementation unless the brief explicitly asks for comparison.

**Brief revision provenance** is governed by `{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md`. When the input artifact is a `design-brief`, step-01 validates the provenance frontmatter (revision_mode / change_class / supersedes / active-uniqueness) before any other processing and halts on any failure. A brief that fails validation is not consumed — there is no fallback to a stale or superseded brief. The validation rules are mechanical; they exist to catch silent drift (hand-edited scope changes, multiple "active" briefs on the same surface, consumption of a superseded brief without explicit opt-in).

**Not contract — never cite as authority:**

- **Agent run-time thinking notes / "other observed issues" / mental scratch.** Only what is committed to a markdown artifact on `main` is contract. If the agent noticed a problem during a screen-review run but did NOT enumerate it as V1/V2/V3 (or as a separate `## Edge states` / `## What to keep` / `## Out-of-scope reminder` entry), that observation is not part of the artifact and a downstream PR cannot cite "the screen-review's deferred items" to justify shipping it. The remedy is below in §POLISH ITEMS BELOW V3.
- **Prior conversation context / chat history** between the user and the agent. Only the committed artifact on `main` survives across runs.
- **The PR description of any in-flight PR.** PR descriptions are convenience metadata; the artifact on `main` (or the diff itself once merged) is the durable record.

**Implication:** A screen-review violation's `Rule violated:` field must cite (1) or (2), never (5) or (6). A design-handoff's exact-change list must come from the brief or from a violation tied back to (2); never from the agent's own preferences. Briefs may narrow the policy for a feature but may not loosen or carve out exceptions.

---

## POLISH ITEMS BELOW V3

A screen-review caps at V1–V3 by the "issue cap rule" in `templates/screen-review.md`. That cap is intentional — it forces ranking discipline. But it creates a real-world tension: the screen often has additional violations the agent noticed but didn't rank, and the user later wants those fixed too.

**The rule:** any code change for a polish item that is NOT covered by V1/V2/V3 of the current screen-review must do ONE of the following:

1. **Cite the original handoff section** in the PR description (e.g. "implements `design-handoff-{slug}-{date}.md` §1.3 verbatim"). This is appropriate when the polish item is simply an as-yet-unbuilt piece of the original design contract — the contract was always there, the screen-review just didn't elevate it to top-3.
2. **Run a second `design-artifact-loop` pass in `review-only` mode** that adds V4–Vn to the screen-review (V-IDs are stable; new findings get new IDs). Ship the polish PR citing the new V-ID. This is appropriate when the polish item is a new finding not in the original handoff (e.g. a regression discovered post-implementation, or a UX papercut the brief didn't anticipate).

Phrases like "deferred items from the screen-review's Other observed issues list" are **not allowed in PR descriptions** when the screen-review does not contain such a list. If the agent's run-time thinking surfaced items beyond V1–V3, those items are not commitments — they are either (1) re-castable as handoff-section citations or (2) require a second review pass to become contract.

Cross-check at PR-creation time: if a PR claims to implement a "deferred screen-review item" but the cited screen-review file on `main` does not contain that item by V-ID or by explicit list, the PR description is mis-citing and must be rewritten under one of the two paths above.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture**:

- Step 1 is conditionally interactive — only halts if the mode is genuinely ambiguous from the handoff block. Otherwise autonomous.
- Steps 2–4 are fully autonomous — no menus, no halting.
- State persists via variables (see below).
- The mode is **locked** after step 1 and may not silently change. If the user authorizes scope expansion mid-run, the current run terminates and a new run is restated under the new mode.

### State Variables

- `{repo_url}` — GitHub HTTPS URL from the handoff block (no trailing `.git`)
- `{artifact_path}` — Repo-relative path to the canonical artifact on `main` (e.g., `_bmad-output/implementation-artifacts/design-brief-foo-2026-05-26.md`)
- `{artifact_abs_path}` — Absolute path on the local filesystem
- `{artifact_type}` — `design-brief` | `screen-review` | `policy-delta` | `unknown` (parsed from artifact frontmatter or filename prefix)
- `{artifact_content}` — Full contents of the canonical artifact
- `{user_summary}` — 1–3 line human summary from the handoff block (convenience only; non-authoritative)
- `{user_instruction}` — Direct instruction text from the handoff block ("Design the UI following the brief exactly", "Iterate on AVASK", etc.)
- `{screenshot_paths}` — Optional screenshot paths from the handoff block
- `{mode}` — `design-from-brief` | `refine-screen` | `review-only` | `policy-lift` (locked after step 1)
- `{target_label}` — Free-text human label (e.g., "AVASK VAT reclaim", "Invoice review queue")
- `{target_route}` — Pathname (e.g., `/reclaim/avask`)
- `{target_slug}` — Kebab-case slug derived from the route (e.g., `reclaim-avask`)
- `{user_role}` — Who uses this surface (from artifact or context block)
- `{frequency}` — How often (e.g., "quarterly, 4–8 days per quarter")
- `{stakes}` — Consequence of error (e.g., "€233k at stake this quarter")
- `{out_of_scope}` — Explicit boundaries lifted from the artifact or stated by the user
- `{policy_path}` — Resolved path to `docs/design-policy.md` or `{planning_artifacts}/brand-identity.md`
- `{policy_content}` — Loaded policy contents (load once in step 2; never re-state inline)
- `{sister_skills_invoked}` — List of sister skills consulted during the run (logged in the output for audit)
- `{output_kind}` — `screen-review` | `design-handoff` | `design-response` (decided in step 3 from `{mode}` + artifact type)
- `{output_paths}` — Absolute paths of files written (one or more)
- `{tuning_state_path}` — Absolute path to `design-tuning-state-{target_slug}.md` if iteration chain is active

### Step Processing Rules

1. **READ COMPLETELY** — read each step file before taking action
2. **FOLLOW SEQUENCE** — execute numbered sections in order
3. **STEP 1 IS CONDITIONALLY INTERACTIVE** — halt ONLY to disambiguate mode; never to "check in" or present menus
4. **STEPS 2–4 ARE AUTONOMOUS** — never halt, never present menus, never wait for input
5. **MODE LOCK IS NON-NEGOTIABLE** — once `{mode}` is set in step 1, every later step rejects work that would violate the mode's scope rules (see §"Definitions and refinement boundaries" below)
6. **SAVE STATE** — carry variables between steps

### Critical Rules

- **No IA redesign in `refine-screen`.** No route changes, no new multi-step flows, no wholesale replacement of a major component (primary work surface / primary action area / main filter row). Component-level swaps are permitted only when a top screen-review issue requires them.
- **No invented hidden flows.** A screenshot suggests problems; it does not prove them. Possible issues are labeled as such, not promoted to confirmed failures.
- **Verbatim policy copy.** When quoting `docs/design-policy.md`, reproduce text byte-for-byte. No editorializing parentheticals, no softenings, no "the codebase already does X so the designer may too." If you believe the policy is wrong, surface it as a `modify-design-policy` candidate; do NOT patch the output to route around it.
- **No restating sister-skill rules inline.** Defer to `design-policy-canonical` / `operational-analytics-band` / `operational-finance-ui`. Log which were invoked in the output's "Sources consulted" line.
- **YOU MUST ALWAYS SPEAK OUTPUT** in your agent communication style with the config `{communication_language}`.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `planning_artifacts` and `implementation_artifacts` paths
- `date` as system-generated current datetime

### Paths

- `{installed_path}` = `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop`
- `{output_dir}` = `{implementation_artifacts}` — all output artifacts are written here, alongside briefs and screen-reviews from peer workflows
- `{policy_canonical}` = `{project-root}/docs/design-policy.md`
- `{policy_legacy}` = `{planning_artifacts}/brand-identity.md`

### Policy Loading

Check both possible locations, in order. `docs/design-policy.md` is canonical; `{planning_artifacts}/brand-identity.md` is the legacy slot. Prefer the first if both exist:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

Store the resolved path as `{policy_path}` and the contents as `{policy_content}`. Step 2 references both.

**If the canonical path should exist for this project but the check returned nothing, STOP and report the path you tried.** Silent fallback to "no policy" mode is a loader-drift bug — surface it instead of swallowing it.

### Input

The handoff block accepted by this workflow has this canonical shape:

```text
Brief written, PR opened (#NNN), squash-merged to main (HASH), worktree cleaned.

File: _bmad-output/implementation-artifacts/design-brief-{slug}-{date}.md
(on GitHub https://github.com/ORG/REPO/blob/main/_bmad-output/implementation-artifacts/design-brief-{slug}-{date}.md)

Summary (3 lines):
- ...
- ...
- ...

Hand off to design-artifact-loop:
Connect to https://github.com/ORG/REPO and read
_bmad-output/implementation-artifacts/design-brief-{slug}-{date}.md on main.
This is a design brief for {target}. Design the UI following the brief exactly.
```

The block may also reference a `screen-review-*.md` artifact for refinement flows, or carry an optional screenshot. The referenced markdown file on `main` is canonical; the summary lines are convenience.

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- Step 1 must not halt for mode disambiguation. Apply the mode-detection rules deterministically; on a tie, prefer in order: `design-from-brief` → `refine-screen` → `review-only` → `policy-lift`.
- Never ask "do you want X or Y?" — pick the higher-priority mode and proceed. The first sentence of the output's context block must state the chosen mode and why it was chosen.

---

## DEFINITIONS AND REFINEMENT BOUNDARIES

### IA vs visual hierarchy

**IA** = navigation, route hierarchy, page-to-page flow, and the conceptual model of how content is divided across screens.

**Visual hierarchy** = which element draws the eye, density, prominence, spacing, ordering, and emphasis within a single page. Visual hierarchy is NOT IA.

### Major component

A **major component** is the primary work surface (table / worklist), the primary action area, or the main filter row. A swap is "major" if it changes what data or actions the area exposes.

### Mode scope (enforced by step 3)

| Action | `design-from-brief` | `refine-screen` | `review-only` | `policy-lift` |
|---|---|---|---|---|
| Propose new screen structure | yes | no | no | no |
| Hierarchy / spacing / density fixes | yes | yes | no (label as issue) | yes |
| Control swaps at component level | yes | yes (only if a top issue requires it) | no | yes (only if policy requires) |
| Wholesale swap of a major component | yes (if brief asks) | **no** | no | no |
| Route changes | yes (if brief asks) | **no** | no | no |
| New multi-step flows | yes (if brief asks) | **no** | no | no |
| Speculative redesign beyond evidence | **no** | **no** | **no** | **no** |
| Cite visible evidence only | n/a | required | required | n/a |
| Compare against named policy delta | optional | optional | optional | **required** |

Step 3 enforces this matrix. If the work product crosses a "no" cell, step 3 rejects the output and returns to step 2 with a scoping diagnostic.

---

## OUTPUT ARTIFACTS

This workflow produces ONE of the following per run (plus an optional tuning state file):

### A. `screen-review-{target_slug}-{date}.md`
Modes: `review-only`, `refine-screen` (when no recent review exists).
Template: `templates/screen-review.md`.
Required sections: header (mode, target, date), context block, verdict (`FAIL` / `PASS WITH ISSUES` / `PASS`), top issues (ranked V1, V2, … with severity + rule-cited evidence), edge states, what to keep, out-of-scope reminder, sources consulted.
Filename convention matches the existing `design-review` artifact contract so downstream `design-handoff` (refine-screen mode) can read it without modification.

### B. `design-handoff-{target_slug}-{date}.md`
Modes: `refine-screen` (after a screen-review exists), `policy-lift`, `design-from-brief` (when the brief asks for immediate implementation rather than concept direction).
Template: `templates/design-handoff.md`.
Required sections: header (mode, target, date), context block, source artifacts consulted, design objective, exact changes to make, what NOT to change, component / route targets, edge states to preserve or add, implementation notes, sources consulted.

### C. `design-response-{target_slug}-{date}.md`
Modes: `design-from-brief` (when output is concept direction rather than immediate implementation).
Template: `templates/design-response.md`.
Required sections: brief summary, proposed screen structure, answers to the brief's open design questions, rationale tied back to brief sections, implementation handoff note.

### D. `design-tuning-state-{target_slug}.md` (optional, persistent)
Tracks: previous failures, fixed issues, current open issues, final accepted direction. Created on first iteration; appended on each subsequent run against the same `{target_slug}`. Compatible with the existing `design-tuning` workflow's state-file conventions.

---

## FRONTEND SKILL ROUTING

When this workflow produces any UI proposal, refinement plan, layout recommendation, or implementation-facing design handoff, it must invoke the relevant frontend/design skills BEFORE generating output. Artifact orchestration alone is not sufficient — improvising visual decisions from workflow prose is the failure mode this section exists to prevent.

### Routing rules

#### In `design-from-brief`
Always invoke:
- `design-policy-canonical`
- `operational-finance-ui` for dense worklists, tables, filters, status hierarchies, and operational screen structure
- frontend / webapp design skill (`website-building` or project-equivalent) for page composition, spacing, hierarchy, component treatment, and web UI conventions

Conditionally invoke:
- `operational-analytics-band` when the screen includes KPI strips, analytics rows, trend bands, or quarter-by-quarter summary bands

#### In `refine-screen`
Always invoke:
- `design-policy-canonical`
- `operational-finance-ui` when the screen is a table-, queue-, or operations-led finance UI

Conditionally invoke:
- `operational-analytics-band` when reviewing or changing an analytics band / KPI row
- frontend / webapp design skill (`website-building` or project-equivalent) when concrete visual, layout, spacing, control, or component changes are being proposed

#### In `review-only`
Frontend / webapp design skill is optional unless the review includes concrete correction guidance. If the output contains specific UI fix directions, load the relevant frontend skill first.

#### In `policy-lift`
Always invoke:
- `design-policy-canonical` (the policy is the source of the lift)
- Whichever surface skill matches the target (`operational-finance-ui`, `operational-analytics-band`) so the lift is interpreted against the right component vocabulary

### Routing rule

If the workflow is producing UI-facing guidance, it MUST route through the relevant frontend / design skills rather than improvise design decisions from workflow prose alone. A run that emits a `design-handoff` or `design-response` with no entries under "Skill routing used" is a failed routing pass and step 3 must rewind to load the missing skills before continuing.

---

## APPROVAL GATES

The workflow must pass these gates in order. Each gate is a hard checkpoint; failure halts the run and surfaces a specific diagnostic to the user. Step 1 owns gate 0 and gates 1–2; step 2 owns gate 3 setup; step 3 owns gates 3 and 4; gate 5 is for the next agent in the chain (post-implementation review).

### Gate 0 — required skills available (step 1)

For modes that emit UI-facing guidance (`design-from-brief`, `refine-screen` when concrete visual changes are proposed, `policy-lift`), the relevant skills declared in FRONTEND SKILL ROUTING must be present in the session's available-skills list before the workflow proceeds. Resolution order for the project frontend skill: (i) `frontend_skill:` in the input artifact's frontmatter; (ii) `frontend_skill:` in `{project-root}/_bmad/bmm/config.yaml`; (iii) the first available skill matching `frontend`, `website-building`, or `webapp`.

If any required skill cannot be resolved, halt with: `"Required skill <name> not available in this project. Skills are distributed by ~/bmad-method-v6/sync-bmad-workflows.sh — run it from any session, then re-invoke this workflow. (Project-local skills must already exist under .claude/skills/; portable skills are seeded from ~/bmad-method-v6/custom/skills/.)"`

This gate does not fire in `review-only` mode unless the review will emit concrete correction guidance (see FRONTEND SKILL ROUTING → `review-only`). It is the first gate to evaluate because every downstream gate's diagnostics depend on the skills being loaded — running gates 1–4 without the skill produces lower-quality halts and degrades the user's trust in the workflow.

### Gate 1 — input validity (step 1)
Confirm:
- referenced artifact exists on `main`
- target route / slug is known or explicitly unknown
- mode is explicit or can be unambiguously inferred (otherwise halt per the step-1 disambiguation rule)
- screenshots are present if the task is screenshot-led refinement

If this gate fails, stop and request the missing input. Do NOT guess paths or fall back to "the most recent brief."

### Gate 2 — context sufficiency (step 1)
Confirm the context block includes:
- user / role
- frequency of use
- stakes / consequence of failure
- source-of-truth artifact
- explicit out-of-scope boundary

If any of these are missing, ask once before proceeding, UNLESS a workflow default already defines them (e.g., out-of-scope is implicit in `refine-screen`'s mode-scope matrix). Missing context is recorded as an evidence gap in the output, never silently invented.

### Gate 3 — review sufficiency (step 3, for `review-only` and `refine-screen`)
Confirm:
- top issues are ranked
- edge states are named
- each confirmed issue is tied to visible evidence or a cited brief / policy rule
- "What to keep" is present if the screen has acceptable solved areas

Do NOT emit `design-handoff-*` until `screen-review-*` passes this gate. In the synthesized-review-then-handoff case, the synthesized review is gated before the handoff section is built.

### Gate 4 — handoff readiness (step 3, before emitting `design-handoff-*`)
Confirm:
- exact changes are specific enough to implement (file / region / token + change + citation)
- out-of-scope boundaries are explicit
- sister-skill ownership is respected (per Source-of-Truth Precedence)
- route / component targets are named where possible
- no IA redesign has leaked into refine mode (cross-checked against the Mode Scope matrix)

### Gate 5 — post-implementation acceptance (next agent in the chain)
After implementation, the next screenshot review (via `design-artifact-loop` in `review-only` or `refine-screen` mode, or via `design-review`) must end with one of the fixed verdicts: `FAIL` | `PASS WITH ISSUES` | `PASS`. No implementation is considered accepted without a post-implementation screenshot review or equivalent visual verification artifact.

The handoff summary in step 4 names this gate explicitly so the next agent knows it is expected.

---

## OUTPUT SCHEMAS

The templates in `templates/` are the canonical, locked schemas for this workflow. They are intentionally simpler than the richer `screen-review --artifact` schema emitted by `design-review` — this workflow trades machine-parseability for cross-run consistency. **Verdict vocabulary is fixed. Severity vocabulary is fixed. Do not invent alternative labels.**

### Schema: `screen-review-{slug}-{date}.md`

```md
# Screen Review — {screen name}

- Mode: {mode}
- Route: `{route}`
- Slug: `{slug}`
- Date: {date}
- Verdict: {FAIL | PASS WITH ISSUES | PASS}

## Context
- User:
- Frequency:
- Stakes:
- Source of truth:
- Out of scope:

## Top issues
### V1. {short issue name} ({hard failure | issue | polish})
- Evidence:
- Why it matters:
- Required correction:

### V2. ...

### V3. ...

## Edge states
- {state}
- {state}
- {state}

## What to keep
- {approved element}
- {approved element}

## Out-of-scope reminder
- {explicit boundary}
```

### Schema: `design-handoff-{slug}-{date}.md`

```md
# Design Handoff — {screen name}

- Mode: {mode}
- Route: `{route}`
- Slug: `{slug}`
- Date: {date}

## Context
- User:
- Frequency:
- Stakes:
- Source artifacts:
- Out of scope:

## Objective
{one paragraph}

## Changes to make
1. ...
2. ...
3. ...

## What not to change
- ...
- ...

## Edge states
- ...
- ...

## Component / route targets
- Route:
- Components:

## Skill routing used
- design-policy-canonical
- operational-finance-ui
- operational-analytics-band (if applicable)
- frontend / webapp skill (if applicable)

## Implementation notes
- ...
```

### Schema: `design-response-{slug}-{date}.md`

```md
# Design Response — {screen name}

- Mode: design-from-brief
- Route: `{route}`
- Slug: `{slug}`
- Date: {date}

## Brief summary
{one paragraph}

## Proposed screen structure
- ...
- ...
- ...

## Answers to design ask
1. ...
2. ...
3. ...

## Constraints honored
- ...
- ...

## Handoff note
{implementation-facing note}
```

**Fixed vocabulary:**
- Verdict: `FAIL` | `PASS WITH ISSUES` | `PASS` (and `INDETERMINATE` for `review-only` runs with no visual evidence — used sparingly, never as a default).
- Severity (per V-numbered issue): `hard failure` | `issue` | `polish`. No `major`/`minor`/`p0`/`p1` or other parallel vocabularies.

---

## DISSENT / SANITY-CHECK PASS

Before finalizing any `screen-review-*`, run one explicit challenge pass. This exists to catch false-positive `PASS` outcomes caused by improvement bias — when a screen looks directionally better than the previous iteration, reviewers tend to under-weight remaining problems.

### Challenge questions

- Is the top-ranked issue truly the most damaging issue for trust, comprehension, or next-action clarity?
- Is there a visible legibility or credibility problem that is easier to miss because the broader layout improved?
- Am I passing a screen because it feels directionally better, rather than because the visible issues are actually resolved?
- Did a decorative asymmetry, weak label, or low-contrast micro-element escape review because it seemed "small"?
- Would a skeptical reviewer disagree with this `PASS` verdict based on the screenshot alone?

### Rule

If the challenge pass surfaces a more serious missed issue, re-rank the findings BEFORE issuing the final verdict. The dissent pass may demote a `PASS` to `PASS WITH ISSUES`, or `PASS WITH ISSUES` to `FAIL`. It may not upgrade a verdict — the only direction of travel is toward more skepticism. Record that the dissent pass ran (`dissent_pass: completed` in the output footer, even when the pass changed nothing).

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/steps/step-01-receive-and-lock-mode.md` to begin.

---

## SUCCESS CRITERIA

This workflow succeeds when:

- The mode is explicit, stated in the output's context block, and does not drift across the run.
- The canonical markdown artifact on `main` remained the source of truth — no rule was sourced from the screenshot or the human summary alone.
- Screen reviews cite visible evidence with file path or class name; possible issues are labeled as such, not promoted to confirmed failures.
- Handoff files are implementation-ready — every "exact change" item is concrete enough to execute without reinterpretation.
- Refinement did not expand into IA redesign, route changes, or wholesale major-component swaps.
- The next agent in the chain (a design-tuning iteration, a quick-dev implementation, or a re-review) can work from the artifact alone without re-prompting the user.
