---
name: design-review-pr
description: 'Checklist-driven enforcement of the project design policy at PR time. Ingests review-checklist.md, classifies rules into source-grep / dom-render / human-judgment lanes, executes each lane, and produces a structured findings report ready to post as a PR comment.'
---

# Design Review (PR) Workflow

**Goal:** Enforce the project's design policy at PR time by evaluating the diff (and optionally a rendered preview of the affected pages) against `docs/review-checklist.md`. Produce a structured findings report that maps cleanly onto inline PR comments.

**Your Role:** You are the mechanical enforcer of the project's design policy at PR time. You don't replace the human `design-review` workflow (which is a senior-designer Chrome audit) — you catch the rules that don't require taste: forbidden classes, missing tokens, banned patterns. The human reviewer handles information architecture and aesthetic judgment; you make sure the easy violations never reach them.

**Key Insight — Mechanical rules don't deserve a senior reviewer's attention.** A senior designer spending PR review time pointing out `rounded-full` on a `<Button>` is a senior designer being wasted. design-review-pr exists because mechanical rules are deterministic, and deterministic checks should run before human review — not after. The structured findings let the human reviewer trust the floor (everything mechanical is caught) and spend their attention on the ceiling (taste, hierarchy, the questions only a person can answer).

This workflow is **NOT** the same as `design-review`:

| | `design-review` | `design-review-pr` |
|---|---|---|
| Trigger | On-demand, live page in Chrome | PR opened / updated |
| Input | One Chrome tab | A diff (PR or local branch) |
| Output | Freeform senior-designer audit prose | Structured findings keyed to checklist IDs |
| Lanes | All judgment, all the time | source-grep → dom-render → human-judgment |
| Implementation | Single-step Chrome audit | Multi-step: scope → grep → render → deliver |

---

## WORKFLOW ARCHITECTURE

Steps execute in order. Each step's output feeds the next.

- `steps/step-01-scope.md` — Determine target (PR or local diff). Identify which routes / pages the changeset touches. Load the checklist.
- `steps/step-02-source-scan.md` — Run all `source-grep` lane rules against the diff. Emit findings.
- `steps/step-03-dom-render.md` — For each affected page (if Chrome is available), render and run `dom-render` lane rules. Emit findings.
- `steps/step-04-deliver.md` — Aggregate findings, evaluate `C-COMPOSITE-01` and `C-ARCHETYPE-01`, and produce the structured report.

### State Variables

- `{pr_number}` — GitHub PR number (optional; if absent, workflow falls back to `git diff main...HEAD`)
- `{diff_files}` — List of files changed in the diff
- `{affected_routes}` — SvelteKit route paths whose `+page.svelte` (or sibling components) appear in `{diff_files}`
- `{checklist}` — Parsed contents of `docs/review-checklist.md`
- `{findings}` — Accumulating list of rule violations, each with: `rule_id`, `severity`, `file`, `line`, `evidence`, `suggested_fix`
- `{chrome_available}` — Boolean. True if `mcp__claude-in-chrome__*` tools are loadable AND a base URL is reachable.
- `{brief_archetype_map}` — Map of `{route → {archetype, band_provenance, brief_filename, rationale}}` for affected routes whose active brief declares an analytics band. Built in step-01 §7. The `rationale` sub-field (the companion `design-rationale-*` artifact, or `none`) carries the *reasoning* evidence — declared archetype + whether the choice was grounded — and lets `C-ARCHETYPE-01` check the decision was sound, not just the rendered form. Empty when no affected route has a brief-declared band. Drives the `C-ARCHETYPE-01` intrinsic check.

### Workflow-intrinsic checks

Two checks are NOT in `docs/review-checklist.md` — the workflow evaluates them itself:

- **`C-COMPOSITE-01`** — fires when ≥3 distinct P1 fingerprints hit one route (evaluated in step-04 §1).
- **`C-ARCHETYPE-01`** — fires when an analytics band's rendered *form* contradicts the `analytics_archetype` its active brief declared (e.g. brief says `coverage`, the page ships a multi-series trend chart with no gap affordance; brief says `ranking`, the list is unsorted; any band element has no drill target). This is the PR-time counterpart to `design-handoff` step-01 §5c + `shared/analytics-archetypes.md`: the brief picks a shape (via the `analytics-surface-architect` skill), this check verifies the implementation kept it. Brief-aware — it reads the declared contract, not just project policy. **Rationale-aware too:** when the companion `design-rationale-*` artifact exists, it additionally verifies the *decision* was sound — the rationale's archetype matches the brief (P1 on divergence) and the choice was grounded (a `[note]` when reasoning is thin) — so a band that renders as declared but was chosen on an ungrounded guess is still surfaced. Reasoning verification is disclosed, never assumed: a declared band with no rationale is reported as "rendered-form checked, reasoning not verifiable." Evaluated in step-04 §1b.

---

## INITIALIZATION

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/design/design-review-pr`
- `checklist_path` = `{project-root}/docs/review-checklist.md`
- `policy_path` = `{project-root}/docs/design-policy.md`
- `design_standards_path` = `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`
- `archetypes_path` = `{project-root}/_bmad/bmm/workflows/design/shared/analytics-archetypes.md`
- `implementation_artifacts` = config-resolved `_bmad-output/implementation-artifacts/` (where active briefs live)

### Prerequisites (hard)

- `docs/review-checklist.md` exists in the project. If absent, the workflow exits with a clear error: "No `docs/review-checklist.md` found. Run `design-policy` workflows to seed one, or copy from another project."

### Prerequisites (soft — degrade gracefully)

- `gh` CLI present and authenticated → enables PR mode. Absent → fall back to local diff mode.
- Chrome MCP tools loadable AND project's dev server reachable → enables `dom-render` lane. Absent → skip that lane and surface in the report.
- Human-judgment rules → always surfaced as "manual reviewer prompts" in the report. Never executed automatically.

---

## EXECUTION

1. Load `steps/step-01-scope.md` and execute.
2. Load `steps/step-02-source-scan.md` and execute.
3. If `{chrome_available}` and `{affected_routes}` is non-empty, load `steps/step-03-dom-render.md` and execute. Otherwise skip with a note in `{findings}` flagging which rules were not checked.
4. Load `steps/step-04-deliver.md` and execute.

---

## DELIVERABLE FORMAT

The report is a single markdown document with these sections, in order:

### 1. Summary

A one-paragraph verdict, plus a counts table:

| Severity | Count |
|---|---|
| P0 (blockers) | N |
| P1 (change-requested) | N |
| P2 (suggestions) | N |
| P3 (nits) | N |
| Manual prompts | N |

### 2. Blockers (P0)

Each blocker rendered as:

```
**[blocker] {rule_id}** — {one-line statement}
- File: `{path}:{line}`
- Evidence: `{class or value found}`
- Fix: {concrete swap or action}
- Source: {policy section}
```

### 3. Changes requested (P1)

Same shape as blockers. If `C-COMPOSITE-01` fires, surface it FIRST with a recommendation for a redesign pass rather than per-rule fixes.

### 4. Suggestions (P2) and nits (P3)

Same shape but tagged `[suggestion]` or `[nit]`.

### 5. Manual reviewer prompts (human-judgment lane)

Each prompt is a question the human reviewer must answer:

```
**[manual] {rule_id}** — {question}
- Affected pages: `{routes}`
- What to check: {detection guidance from checklist}
```

### 6. Coverage notes

- Which lanes ran, which were skipped, and why.
- Which checklist rules have no matching diff context (i.e., the diff doesn't touch any code subject to that rule).

### 7. Optional: PR comment payload

If `--comment` flag is passed and `{pr_number}` is set: emit a `gh pr comment` invocation as the final action. Otherwise the report is returned as-is.

---

## RULES (workflow-level)

- **Cite checklist IDs, not paraphrases.** Every finding must reference a rule ID from `docs/review-checklist.md`. If a rule doesn't exist for what you want to flag, add it to the checklist in a follow-up PR — don't invent ad-hoc rules in the report.
- **Cite real file paths and line numbers.** `src/routes/.../+page.svelte:L143`, not "somewhere in the layout".
- **Cite real Tailwind classes or computed values.** `rounded-full` on `<Button>`, not "the button looks pill-shaped".
- **Never propose new tokens.** Reference the project's defined tokens or the checklist's `Exception` column.
- **Never implement fixes.** This workflow produces findings; the dev (or a separate `design-implement` workflow) fixes.
- **Do not flag dark-mode issues.** Project is light-mode only.
- **Do not flag accessibility issues beyond what the checklist covers.** Accessibility has its own workflow.
- **Established-pattern exception:** if a flagged pattern appears in `≥3` distinct pages of the existing codebase (i.e., it's part of the project's design language), downgrade to `[note]` and surface as: "Flagged by rule X, but appears established in this project — recommend either updating the rule or refactoring the established usage."

---

## FAILURE MODES

- **Treating the checklist as a wishlist.** Rules are pass/fail. If detection finds the pattern, the rule fails — don't argue with it in the report.
- **Inventing new severity levels or new categories.** Use what's in the checklist.
- **Producing a long prose audit instead of structured findings.** That's `design-review`. This workflow's output is a triage report keyed to rule IDs.
- **Running dom-render before source-grep.** Source is faster, deterministic, and finds most issues. Always run grep first.
- **Skipping the established-pattern check.** Flagging a pattern that the project already uses everywhere creates churn, not value.
