---
name: 'step-03-produce-artifact'
description: 'Dispatch on {mode} to produce exactly one mode-locked output artifact; enforce the scope matrix; cite only from the evidence set'
---

# Step 3: Produce the Output Artifact

**Progress: Step 3 of 4** — Next: Save & Hand Off (autonomous)

## RULES:

- FULLY AUTONOMOUS. No menus, no halting (except for the mode-scope rejection path defined below).
- The artifact you produce here is the deliverable. It must be implementation-ready, citation-tight, and bounded to `{mode}`'s scope.
- Cite ONLY from `{evidence_set}`. If a claim has no backing in the evidence set, drop it.
- Mode lock is enforced HERE. If the work product would cross a "no" cell of the scope matrix (workflow.md → Mode Scope), reject the work and emit the scoping diagnostic instead.

---

## AVAILABLE STATE FROM STEPS 1–2

- `{mode}`, `{target_label}`, `{target_route}`, `{target_slug}`
- `{evidence_set}` — primary artifact parsed sections, policy section index, sister skills, screenshot observations, context block, evidence gaps
- `{user_summary}`, `{user_instruction}` (convenience only; non-authoritative)

---

## SEQUENCE OF INSTRUCTIONS

### 1. Dispatch on Mode

Set `{output_kind}` per the mode dispatch table:

| `{mode}` | `{output_kind}` | Template |
|---|---|---|
| `design-from-brief` AND brief asks for concept direction (open questions, "explore", "answer") | `design-response` | `templates/design-response.md` |
| `design-from-brief` AND brief asks for immediate implementation ("design the UI", "produce a handoff for dev") | `design-handoff` | `templates/design-handoff.md` |
| `refine-screen` AND `{evidence_set}.primary.artifact_type` = `screen-review` | `design-handoff` | `templates/design-handoff.md` |
| `refine-screen` AND no recent screen-review (screenshot only) | `screen-review` first, then internally pivot to a `design-handoff` bounded to the synthesized review's top 3 violations (produce BOTH files this run) | both templates |
| `review-only` | `screen-review` | `templates/screen-review.md` |
| `policy-lift` | `design-handoff` (bounded to policy delta) | `templates/design-handoff.md` |

If `{evidence_set}.evidence_gaps` contains "no visual evidence" AND `{mode}` = `review-only`, the output is still a `screen-review` but the verdict is `INDETERMINATE` and only directional issues may be raised (no per-pixel corrections).

### 2. Invoke the Routing Plan (Required Skills First)

The routing plan was built in step 2 per workflow.md → "Frontend skill routing". Invoke required skills for `{mode}` BEFORE generating any output. A run that emits a `design-handoff` or `design-response` with an empty "Skill routing used" block while having produced UI-facing guidance is a Gate-4 failure and must rewind.

For each entry in `{evidence_set}.sister_skills`, invoke the named skill via the Skill tool at the moment its scope is needed:

- `design-policy-canonical` — invoke whenever choosing or proposing a component, color, typographic size, or layout primitive. Pass the local question (e.g., "Is a card row appropriate for the analytics surface on /reclaim/avask given the policy?"). The skill returns the policy-canonical answer; quote its rule reference in the output, not its prose.
- `operational-finance-ui` — invoke before proposing any change to a table, control row, or status treatment on an operational finance surface. Pass the artifact's current proposal and the local question.
- `operational-analytics-band` — invoke before writing or critiquing any analytics-row / trend-band content. The skill enforces anti-card rules; consult it before proposing strips, microcharts, or counters.
- `operational-cockpit` — invoke before proposing or critiquing the composition/interaction of a decide-one triage + single-item decision workspace (`composition: operational-cockpit`). The skill is the single source of truth for the cockpit archetype: queue↔workspace co-presence, per-item momentum, keyboard-first commit, consequence-visibility before an irreversible commit, no working blind.
- Frontend / webapp skill (`website-building` or project-equivalent) — invoke for page composition, spacing, hierarchy, component treatment, and web UI conventions when the output will carry concrete UI fix guidance.

Record each invocation in `{skill_routing_used}` — a bullet list that populates both the "Sources consulted" footer (screen-review, design-response) and the dedicated "Skill routing used" block (design-handoff). If a sister skill's answer contradicts the brief, the policy wins (workflow.md → Source-of-truth precedence) — surface the contradiction in the output's `out_of_scope` block and recommend `modify-design-policy` if appropriate.

### 3. Generate the Output

Open the resolved template (from step 1 of this step) and populate it from state. The templates are at:

- `{installed_path}/templates/screen-review.md`
- `{installed_path}/templates/design-handoff.md`
- `{installed_path}/templates/design-response.md`

Each template has `{{double_brace_placeholders}}` that map to state variables. The mapping is documented in each template's preamble comment.

**Citation discipline:** every `Rule violated:` field cites either:

- `docs/design-policy.md §N (Title)` — for policy-sourced rules
- `{artifact_path} §X (Section Title)` — for brief-sourced or screen-review-sourced rules
- `design-standards.md — {category}` — only when no policy or brief covers the rule

Never cite `{user_summary}` or `{user_instruction}` as authority. They are conversational scaffolding.

### 3a. Gate 3 — Review Sufficiency (`review-only` and `refine-screen`)

Before finalizing a `screen-review` output, confirm all four:

- Top issues are ranked (V1 = most damaging by trust/comprehension/next-action impact).
- Edge states are named (at least one, even if just "all-zero state" or "all-action-required state").
- Each confirmed issue cites visible evidence (a class name, file:line, screenshot region) OR a cited brief / policy rule.
- "What to keep" is present if the screen has any acceptable solved areas.

If any of these is missing, do NOT emit the file — return to evidence assembly. In the synthesized-review-then-handoff case (`refine-screen` mode without a pre-existing review), this gate applies to the synthesized review BEFORE the handoff section is built.

### 3b. Dissent / Sanity-Check Pass (every `screen-review`)

Before issuing the final verdict, walk the five challenge questions from workflow.md → "Dissent / sanity-check pass":

1. Is the top-ranked issue truly the most damaging issue for trust, comprehension, or next-action clarity?
2. Is there a visible legibility or credibility problem that is easier to miss because the broader layout improved?
3. Am I passing a screen because it feels directionally better, rather than because the visible issues are actually resolved?
4. Did a decorative asymmetry, weak label, or low-contrast micro-element escape review because it seemed "small"?
5. Would a skeptical reviewer disagree with this `PASS` verdict based on the screenshot alone?

If the challenge pass surfaces a more serious missed issue, re-rank the V-list (renumbering only NEW additions; existing V-IDs are stable across iterations) and DEMOTE the verdict as needed. The dissent pass may demote `PASS` → `PASS WITH ISSUES` → `FAIL`. It may NOT upgrade a verdict.

Record the outcome in the output footer as `Dissent pass: completed; no re-ranking` or `Dissent pass: completed; verdict demoted from {X} to {Y} because {one-sentence reason}`.

### 4. Enforce the Mode-Scope Matrix

Before finalizing the output, walk the work product against the mode scope matrix (workflow.md → "Mode scope"). For `refine-screen` in particular:

- No `## New Route` or `## Multi-step Flow` section may appear.
- No bullet under "Exact changes to make" may rewrite the primary work surface, primary action area, or main filter row wholesale. Component-level swaps are allowed only when tied to a specific V-numbered violation from the screen-review.
- No "Get radical (optional)" or "Alternative layout" section may appear.

For `review-only`:

- No "Exact changes to make" section may appear. Issues are stated; corrections are NOT prescribed. Required corrections move to `refine-screen` in a later run.

For `policy-lift`:

- Only policy-driven changes may appear. Any change not traceable to a line in the policy delta is rejected.

**If the work product crosses a "no" cell:** halt this step, rewind to step 2's evidence set, and try again with the offending sections removed. If after rewriting the work product is empty, emit:

```
Mode-scope rejection: the proposed changes for {target_label} cannot fit inside {mode}. The minimum useful change set requires {forbidden-action}, which {mode} does not permit. Two paths:

1. Restate the handoff under {target_mode} (likely {recommended_mode}) and rerun. This is the right call if the change really is needed.
2. Re-scope the brief to ask for less. Run modify-design-policy or design-handoff to produce a narrower input.

This run produced no artifact.
```

Do NOT silently emit a partial artifact that breaks the mode contract.

### 4a. Gate 4 — Handoff Readiness (before any `design-handoff` is emitted)

Before staging a `design-handoff` output, confirm all five:

- Every "Changes to make" item is specific enough to implement (file or component + region or token + exact change + citation). Vague items ("tighten this area", "improve hierarchy") are rejected.
- Out-of-scope boundaries are explicit in the "What not to change" block.
- Sister-skill ownership is respected — palette/typography/layout decisions cite `design-policy-canonical` (or the policy it interprets); analytics-band decisions cite `operational-analytics-band`; finance-UI control/table/status decisions cite `operational-finance-ui`.
- Route / component targets are named where possible — at least one component file path or route path.
- No IA redesign leaked into `refine-screen` (cross-check against the Mode Scope matrix in step 4).
- The "Skill routing used" block is non-empty if the output carries any UI-facing guidance.

If any check fails, rewind to step 2 evidence assembly OR to section 2 of this step (re-invoke missing skills). Do NOT emit a partial handoff.

### 5. Populate the Output From the Locked Schema

The output structure is the locked schema in workflow.md → "Output schemas" and `templates/{kind}.md`. Do NOT add free-form sections; do NOT rename fields; do NOT invent new headings. Fixed vocabulary applies:

- Verdict: `FAIL` | `PASS WITH ISSUES` | `PASS` (or `INDETERMINATE` for review-only with no visual evidence)
- Severity per V-block: `hard failure` | `issue` | `polish` — no `major`/`minor`/`p0`/`p1`/etc.

Each template carries its own `## Context` block — populate it from the evidence set's `context_block`. Where the template's footer expects "Sources consulted", "Evidence gaps", or "Dissent pass" lines, populate those from `{skill_routing_used}`, `{evidence_set}.evidence_gaps`, and the result of the dissent pass (section 3b above) respectively.

**Brief provenance pass-through.** When `{evidence_set}.primary.artifact_type == "design-brief"`, append a "Brief provenance" line under the Context block's `Source of truth:` / `Source artifacts:` entry. Format:

```
- Source of truth: <artifact_path>
- Brief provenance: revision_mode={brief_revision_mode}, change_class={brief_change_class}, last_modified_by={brief_last_modified_by} on {brief_last_modified_date}{; supersedes <brief_supersedes> if non-empty}
```

This carries the brief's lineage forward one hop so the next consumer of THIS output (e.g. `design-implement` reading a `design-handoff-*.md`) sees provenance without re-reading the original brief. Skip the line when the primary artifact was a `screen-review` or `policy-delta` — those have their own lineage models.

For `design-handoff` outputs, the dedicated `## Skill routing used` block is REQUIRED non-empty whenever the run produced UI-facing guidance — this is the Gate 4 cross-check.

### 6. Stage the Output for Step 4

Write the populated output(s) to memory as `{output_artifact_content}` (a map of `output_kind` → file content). Do NOT write to disk yet — step 4 owns disk writes, filename resolution, and the user-facing summary.

If the run produced two artifacts (the `refine-screen` + synthesized screen-review case), stage both:

```yaml
output_artifact_content:
  screen-review: "<full content of screen-review-{slug}-{date}.md>"
  design-handoff: "<full content of design-handoff-{slug}-{date}.md>"
```

Also set `{output_paths}` as a placeholder list — step 4 fills in absolute paths.

### 7. Proceed to Step 4

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/steps/step-04-save-and-handoff.md`

---

## SUCCESS METRICS

- Exactly one `{output_kind}` was selected per the dispatch table (or both, for the `refine-screen` + synthesized review case).
- Every `Rule violated:` / "Required correction" entry cites a real, addressable source (policy section, artifact section, or design-standards.md category).
- No "Exact changes to make" item ever cites `{user_summary}` or `{user_instruction}` as authority.
- The mode-scope matrix was walked and either passed or rejected — never silently bent.
- Sister skills were invoked at decision points, not paraphrased from memory.

## FAILURE MODES

- Mixing `design-response` (concept direction) and `design-handoff` (implementation-ready) in the same file. Pick one per run; the dispatch table says which.
- Adding a "Get radical" or "Alternative layout" section to a `refine-screen` handoff. The mode forbids it.
- Citing the screenshot as authority for a rule. Screenshots are evidence of state, not authority for the rule.
- Inlining sister-skill prose. Quote the rule reference; don't paraphrase the skill's body.
- Emitting a partial artifact when the mode-scope matrix rejects part of the work. All-or-nothing: either rewrite to fit the mode, or emit the scoping diagnostic and produce no artifact.
