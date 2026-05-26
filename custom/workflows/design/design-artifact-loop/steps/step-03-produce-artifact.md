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

### 2. Invoke Sister Skills On Demand

For each entry in `{evidence_set}.sister_skills`, invoke the named skill via the Skill tool at the moment its scope is needed:

- `design-policy-canonical` — invoke whenever choosing or proposing a component, color, typographic size, or layout primitive. Pass the local question (e.g., "Is a card row appropriate for the analytics surface on /reclaim/avask given the policy?"). The skill returns the policy-canonical answer; quote its rule reference in the output, not its prose.
- `operational-analytics-band` — invoke before writing or critiquing any analytics-row / trend-band content. The skill enforces anti-card rules; consult it before proposing strips, microcharts, or counters.
- `operational-finance-ui` — invoke before proposing any change to a table, control row, or status treatment on an operational finance surface. Pass the artifact's current proposal and the local question.

Record each invocation in the output's "Sources consulted" line (skill name + one-line summary of what was decided). If a sister skill's answer contradicts the brief, the policy wins (workflow.md → Source-of-truth precedence) — surface the contradiction in the output's `out_of_scope` block and recommend `modify-design-policy` if appropriate.

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

### 5. Add the Context Block to Every Output

Every output file MUST contain a `## Context Block` section near the top, restated from the evidence set. Format:

```markdown
## Context Block

- **Mode:** {mode}
- **Target:** {target_label} ({target_route} / slug `{target_slug}`)
- **Source artifact:** [`{artifact_path}`]({github_blob_url})
- **User / role:** {user_role}
- **Frequency:** {frequency}
- **Stakes:** {stakes}
- **Out of scope:** {out_of_scope}
- **Sources consulted:** docs/design-policy.md{ if loaded }, sister skills: {comma-separated names}{ if any }, screenshots: {N} file(s){ if any }
- **Evidence gaps:** {comma-separated list, or "none"}
```

Where `{github_blob_url}` = `{repo_url}/blob/main/{artifact_path}` if `{repo_url}` was provided in the handoff, otherwise the bare repo-relative path.

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
