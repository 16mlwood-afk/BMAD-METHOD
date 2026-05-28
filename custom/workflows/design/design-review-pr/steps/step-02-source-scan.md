---
name: 'step-02-source-scan'
description: 'Run every source-grep lane rule against the diff. Collect findings keyed to rule IDs.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review-pr'
thisStepFile: './step-02-source-scan.md'
---

# Step 2: Source Scan

**Goal:** Run the `source-grep` lane of `{checklist}` against `{diff_files}`. Emit one finding per rule violation. Cheap, deterministic, no rendering required.

---

## AVAILABLE STATE

- `{diff_files}` — filtered list of design-relevant changed files
- `{checklist.source_grep}` — rules to check, with detection patterns

---

## EXECUTION SEQUENCE

### 1. For each rule in `{checklist.source_grep}`

Translate the rule's **Detection** column into one or more concrete ripgrep / AST queries. Run each against `{diff_files}` (NOT against the whole codebase — we're reviewing this PR's contribution, not auditing the project).

```bash
# Generic pattern: rg ONLY the changed files
rg --line-number --column --no-heading --pcre2 "<pattern>" $(cat /tmp/diff-files)
```

For each hit, record:

- `rule_id` — e.g., `G-COLOR-01`
- `severity` — from the rule
- `file` — absolute or repo-relative path
- `line` — line number from ripgrep
- `column` — column from ripgrep
- `evidence` — the matched substring (truncate to 120 chars)
- `suggested_fix` — derived from the rule's **Detection** + **Exception** columns; for simple swaps, render as a before/after one-liner

### 2. Apply exceptions

For each candidate finding:

- If the file's enclosing block matches an **Exception** clause (e.g., a `rounded-full` button inside an `<Avatar>` component), suppress the finding.
- If the rule is marked `established_exception` from step-01, downgrade severity by one tier and tag the finding as `established` in the report.

### 3. Reference patterns for common rules

These are starting points — refine per rule. The exact patterns belong in the checklist's Detection column over time.

| Rule | Pattern (PCRE2) |
|---|---|
| G-COLOR-01 | `\b(indigo\|violet\|purple)-(500\|600\|700)\b` |
| G-COLOR-02 | `\bbg-gradient-to-` |
| G-COLOR-03 | `\bbackdrop-blur\b` |
| G-COLOR-04 | `\bshadow-(lg\|xl\|2xl)\b` |
| G-COLOR-05 | `\bborder-(amber\|blue\|emerald\|green\|red\|rose\|indigo\|violet\|purple\|orange\|sky\|teal\|cyan)-\d` |
| G-TYPO-03 | `uppercase\b.*\btracking-(wide\|widest)\b\|\btracking-(wide\|widest)\b.*\buppercase\b` |
| G-TYPO-04 | `\bfont-mono\b` (then check enclosing element semantics) |
| G-TYPO-05 | Unicode emoji ranges in JSX/Svelte template text (excluding string literals inside `data-*` or test fixtures) |
| G-VISUAL-01 | `\bhover:(scale-\|-translate-y-)` |
| G-VISUAL-03 | `bg-(blue\|emerald\|amber\|red\|indigo\|violet\|purple)-(50\|100\|200)\b.*\brounded-full\b` on icon wrappers |
| S-STATUS-01 | `<(Badge\|Pill\|StatusBadge\|StatusPill)[^>]*\brounded-full\b` |
| S-STATUS-04 | `status[A-Za-z]*\s*=\s*['"](purple\|blue\|indigo\|violet\|orange\|sky\|teal\|cyan\|rose\|pink)` |
| B-BUTTON-01 | `<Button[^>]*variant=["']default["'][^>]*\brounded-full\b` |
| B-BUTTON-02 | `<Button[^>]*\b(h-12\|h-14\|text-lg\|text-xl)\b` |
| L-LAYOUT-06 | `grid-cols-(2\|3)\b.*\n.*<Card.*\n.*<(?:Lucide\|Icon)` (multi-line heuristic) |
| D-DETAIL-04 | `<Drawer.*footer.*<Button.*rounded-full` |

### 4. Special handling

- **`G-TYPO-04` (font-mono on prose):** A simple regex finds `font-mono` everywhere. To distinguish prose from numeric/ID content, inspect the matched element's text or class context — if the enclosing element renders dynamic numeric data (e.g., a table cell bound to a `price` field) or has class names like `tabular-nums`, `numeric`, `id-cell`, suppress the finding.
- **`G-TYPO-05` (emoji as icon):** Match Unicode emoji ranges (e.g., `[\u{1F300}-\u{1FAFF}]`). Suppress matches inside `*.test.ts`, `*.fixture.*`, `mocks/**`.
- **`E-EXEMPLAR-*`:** Run only if `{diff_files}` includes anything under `_bmad-output/` or a path matching `*exemplar*`.

---

## OUTPUT

Append all findings to `{findings}`. Each finding looks like:

```yaml
- rule_id: G-COLOR-01
  severity: P1
  file: src/routes/(authed)/expenses/+page.svelte
  line: 142
  column: 24
  evidence: "class=\"... bg-indigo-600 ...\""
  suggested_fix: "Replace `bg-indigo-600` with `bg-primary` (project accent token)."
  source: "policy §5; standards Cat.3"
  lane: source-grep
  established: false
```

Proceed to step-03.

---

## FAILURE MODES

- **Over-broad regex.** A pattern like `\bpurple\b` will match comments and strings. Restrict to class-attribute contexts (`class="..."`, `className="..."`, `class={`) where possible.
- **Missing the diff filter.** Never scan the entire repo — only `{diff_files}`. Otherwise the workflow churns on established patterns and produces noise.
- **Treating every `rounded-full` as a violation.** Avatars, indicator dots, icon-only buttons, and circular badge containers legitimately use `rounded-full`. The rule fires only on status pills, primary CTAs, and badges.
- **Reporting findings without `suggested_fix`.** A finding without a fix is just a complaint. Every finding must propose a concrete swap or action.
