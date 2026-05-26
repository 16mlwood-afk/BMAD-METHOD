---
name: 'step-04-deliver'
description: 'Aggregate findings, evaluate the composite test, render the structured report, and optionally post it as a PR comment.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review-pr'
thisStepFile: './step-04-deliver.md'
---

# Step 4: Deliver

**Goal:** Take the accumulated `{findings}` from steps 02 and 03, evaluate the composite test, render the report in the format defined in `workflow.md`, and (optionally) post as a PR comment.

---

## AVAILABLE STATE

- `{findings}` — all findings from source-grep and dom-render lanes
- `{checklist.human_judgment}` — rules that require manual review
- `{affected_routes}` — surface scope
- `{chrome_available}` — for coverage-notes section
- `{pr_number}` — for optional `gh pr comment` invocation

---

## EXECUTION SEQUENCE

### 1. Evaluate C-COMPOSITE-01

Group `{findings}` by `route` (for dom-render lane) or by file (for source-grep lane). For each group:

- Count P1 findings.
- If ≥3 distinct P1 rule IDs hit the same route/file, fire `C-COMPOSITE-01` with severity P1 and a recommendation:

> Composite fail on `{route}` — {N} structural fingerprints detected: {rule_id_list}. Prefer a redesign pass over per-rule fixes; the compound effect won't be resolved by individual swaps. See `docs/design-policy.md` §5 Anti-default compositions.

Suppress the individual P1 findings on that route (they're rolled into the composite). Keep P0 / P2 / P3 findings on that route as-is.

### 2. Build manual-prompt section

For each rule in `{checklist.human_judgment}` whose `affected_routes` intersects `{affected_routes}`, emit a manual prompt:

```
**[manual] {rule_id}** — {statement}
- Affected pages: {routes}
- What to check: {detection guidance from checklist}
```

### 3. Render the report

Use the format from `workflow.md` §DELIVERABLE FORMAT. The report has these sections, in order, with empty sections OMITTED entirely:

1. **Summary** (always present) — verdict + counts table.
2. **Blockers (P0)** — only if `P0` findings exist.
3. **Changes requested (P1)** — only if `P1` findings or composite fails exist. Composite fails go FIRST.
4. **Suggestions (P2)** — only if `P2` findings exist.
5. **Nits (P3)** — only if `P3` findings exist.
6. **Manual reviewer prompts** — only if `{checklist.human_judgment}` intersects scope.
7. **Coverage notes** (always present) — list lanes that ran, lanes that were skipped (with reasons), and rules with no diff context.

### 4. Verdict line (in Summary)

Pick one:

- **No findings:** "✓ Design review clean — no checklist violations detected."
- **Only P2/P3:** "Design review surfaced suggestions only — no blockers."
- **P1 present:** "Design review found N change-requested findings."
- **P0 present:** "Design review found N blocker(s). Merge should not proceed until resolved."
- **Composite fail:** "Composite design fail — {route_count} route(s) carry ≥3 structural fingerprints. Recommend a redesign pass."

### 5. Coverage notes

Always emit a coverage section:

```
- source-grep: ran against {N} files, executed {M} rules, surfaced {K} findings.
- dom-render: {ran against {R} routes / skipped — Chrome not available}.
- human-judgment: {Q} rules surfaced as manual prompts.
- Rules with no diff context: {list of rule IDs that had nothing to check this PR}.
```

This section is critical for trust — it tells the reader exactly what the workflow did and didn't evaluate.

### 6. Optional: post as PR comment

If `--comment` flag was passed AND `{pr_number}` is set:

```bash
# Write report to a tempfile so the heredoc doesn't fight markdown
gh pr comment "$PR_NUMBER" --body-file /tmp/design-review-report.md
```

Otherwise, return the report as the workflow's final output.

---

## OUTPUT FORMAT — sample

```markdown
# Design Review (PR #1234)

## Summary

Design review found 4 change-requested findings and 2 suggestions.

| Severity | Count |
|---|---|
| P0 | 0 |
| P1 | 4 |
| P2 | 2 |
| P3 | 0 |
| Manual | 3 |

## Changes requested (P1)

**[change-requested] S-STATUS-01** — Status pills are `rounded-md`, not `rounded-full`.
- File: `src/routes/(authed)/queries/[id]/+page.svelte:142`
- Evidence: `<Badge class="... rounded-full ...">`
- Fix: Replace `rounded-full` with `rounded-md`.
- Source: policy §3

**[change-requested] G-TYPO-03** — No `uppercase tracking-wide` labels.
- File: `src/lib/components/QueryHeader.svelte:24`
- Evidence: `class="uppercase tracking-wide ..."`
- Fix: Remove `uppercase tracking-wide`; use sentence case with `text-sm font-medium text-muted-foreground`.
- Source: policy §4; standards Cat.2

...

## Manual reviewer prompts

**[manual] T-TABLE-01** — Operational pages are table-first and full-width.
- Affected pages: `src/routes/(authed)/queries`
- What to check: Is the table the largest surface on the page? Do filters/summaries support it rather than competing?

...

## Coverage notes

- source-grep: ran against 12 files, executed 24 rules, surfaced 4 findings.
- dom-render: skipped — Chrome MCP not loadable in this session.
- human-judgment: 3 rules surfaced as manual prompts.
- Rules with no diff context: G-VISUAL-02, E-EXEMPLAR-01, E-EXEMPLAR-02 (no exemplar files in diff).
```

---

## FAILURE MODES

- **Reporting one finding per matched line when the same rule fires many times.** Group findings by `rule_id + file`. Show the first 3 occurrences with a "+N more" footer if there are more.
- **Hiding the composite fail.** If `C-COMPOSITE-01` fires, it MUST appear first in the P1 section. The individual fingerprints are secondary.
- **Reporting "everything's fine" when dom-render was skipped.** If dom-render didn't run, the report can't claim the page is clean — only that source-grep found nothing. The coverage-notes section must make this explicit.
- **Posting a PR comment without `--comment`.** This workflow defaults to printing the report; it only mutates GitHub state when the user explicitly opts in.
