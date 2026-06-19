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

### 5. Standing check: C-IDENTFMT-01 — canonical-identifier formatting (source arm, advisory)

This is the cheap source-side arm of the §13(a) "Canonical identifier" check (policy §13: a record *"reads, formats … the same way everywhere … do not relabel, reformat, or re-key the same record per surface."*). The authoritative arm is dom-render §3c; this arm exists so the check is not silently skipped when Chrome is unavailable. It is **advisory** — it surfaces *candidates* to confirm in dom-render or via the step-04 human-judgment prompt, not P0/P1 findings on its own (raw regex cannot prove a cross-surface inconsistency).

Run against `{diff_files}` only:

| Signal | Pattern (PCRE2) | Why it's a candidate |
|---|---|---|
| Raw enum/code in template text | SCREAMING_SNAKE token (`\b[A-Z][A-Z0-9]+_[A-Z0-9_]+\b`) inside a JSX/Svelte text node or `>{ … }<` interpolation, NOT inside a `class=`/`className=`/`data-*`/import/`const X =` enum *definition* | a stored enum (`AMAZON_ES`) rendered verbatim where a human label is expected |
| Unformatted identifier interpolation | an identifier-class field (`\b(supplier\|marketplace\w*\|asin\|sku\|orderNumber\|externalOrderId)\b`) interpolated directly (`{…}`) into rendered text **without** passing through a known display formatter (`format`, `titleCase`, `prettify`, `label`, `display`) | inconsistency risk — one surface formats, another renders raw |

For each candidate, emit an **advisory** finding: `rule_id: C-IDENTFMT-01`, `severity: P2`, `lane: source-grep`, `advisory: true`, with `suggested_fix: "Render <field> through the project's display-format helper and confirm it matches how the same record renders on sibling surfaces; confirm in dom-render §3c or the C-IDENTFMT-01 human prompt."` Suppress matches inside `*.test.*`, `*.fixture.*`, `mocks/**`, enum/const *definitions*, and `data-*` attributes (per the over-broad-regex failure mode). If `{diff_files}` touches no rendered identifier text, record C-IDENTFMT-01 source-arm as "no diff context" for step-04 coverage.

### 6. Standing check: F-FOUNDTOKEN-01 — dead foundation-token fallback + tokens-vs-policy drift

This is the source-side backstop for the design-implement §2i foundation-token reconciliation — it catches a wrong-foundation render at PR time even when `design-implement` was bypassed (a hand-written stylesheet, a direct edit). It closes the inbound-flow held-orders miss (PR #2412): a foundation token written as `var(--font-size-base, 0.8125rem)` is an **inert no-op** — the fallback fires only when the variable is *undefined*, and the canonical surface (`src/styles/tokens.css`) *defines* it — so the literal is silently overridden and the surface renders at the global scale, not the design scale.

Run against `{diff_files}` only:

| Signal | Pattern (PCRE2) | Verdict |
|---|---|---|
| Dead foundation-token fallback | `var\(\s*--(font-size\|control-h\|radius)[\w-]*\s*,\s*[\d.]+(rem\|px)\s*\)` inside a CSS / `style=` / template-literal context | **P1, deterministic.** The named globals ARE defined on the canonical surface, so the literal never applies. Emit `rule_id: F-FOUNDTOKEN-01`, `severity: P1`, `lane: source-grep`, `suggested_fix: "Remove the inert fallback. If the design intends a different value, that is a foundation-token divergence — reconcile src/styles/tokens.css to docs/design-policy.md via /bmad:bmm:workflows:apply-design-policy-change; never encode the intended value as a var() fallback or a per-component literal."` |
| Canonical type-scale touched | `{diff_files}` includes `src/styles/tokens.css` OR `globals.css` AND the hunk changes a `--font-size-*` / `--control-h*` / `--radius*` value | **P2, advisory.** Emit `rule_id: F-FOUNDTOKEN-01`, `severity: P2`, `advisory: true`, `suggested_fix: "Confirm the changed foundation token still matches the scale docs/design-policy.md declares (§4). A canonical-token change is app-wide; if it is the policy migration, say so in the PR and confirm every ported surface was re-verified."` |

Suppress matches inside `*.test.*`, `*.fixture.*`, `mocks/**`. If `{diff_files}` touches no stylesheet/style context, record F-FOUNDTOKEN-01 as "no diff context" for step-04 coverage.

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
