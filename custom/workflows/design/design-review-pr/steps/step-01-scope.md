---
name: 'step-01-scope'
description: 'Resolve the target (PR or local diff), enumerate affected files and routes, and load the checklist.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review-pr'
thisStepFile: './step-01-scope.md'
---

# Step 1: Scope

**Goal:** Establish exactly what changeset we're reviewing, what routes it touches, and what rules we're checking it against.

---

## INPUTS

- Optional: `{pr_number}` passed by the user (e.g., `/design-review-pr 1234`).
- Otherwise: the current branch's diff against `origin/main`.

---

## EXECUTION SEQUENCE

### 1. Resolve diff source

```bash
# PR mode
if [ -n "$PR_NUMBER" ]; then
  gh pr diff "$PR_NUMBER" --name-only > /tmp/diff-files
  gh pr view "$PR_NUMBER" --json headRefName,baseRefName -q .headRefName
# Local mode
else
  git diff --name-only origin/main...HEAD > /tmp/diff-files
fi
```

Store the list as `{diff_files}`. If empty, exit early with "No changes to review."

### 2. Verify diff actually touches design surface

Filter `{diff_files}` to design-relevant paths:

- `src/routes/**/*.svelte`
- `src/lib/components/**/*.svelte`
- `src/lib/components/**/*.ts` (for component logic that affects rendering)
- `src/app.css`, `src/app.html`
- `tailwind.config.{ts,js,cjs}`
- `docs/design-policy.md`, `docs/review-checklist.md`

If the filtered list is empty, exit early with: "PR touches no design surface — design-review-pr has nothing to evaluate."

### 3. Resolve affected routes

For each `+page.svelte` or `+layout.svelte` in the filtered list, the route is the directory path under `src/routes/`. Store as `{affected_routes}`.

For component changes (`src/lib/components/**`), find consumers via ripgrep:

```bash
rg -l "from '\\\$lib/components/<ComponentName>'" src/routes/
```

Add the routes of any consuming `+page.svelte` to `{affected_routes}`.

### 4. Load the checklist

```bash
cat {project-root}/docs/review-checklist.md
```

If absent, **exit with a hard error** — the workflow cannot proceed without the checklist. Print:

> No `docs/review-checklist.md` found. This workflow requires the project's mechanical checklist of design rules. Run one of the design-policy workflows to seed one, or copy from a sibling project. Aborting.

Parse the checklist into `{checklist}`:

- For each rule row: `{id, statement, severity, lane, source, detection, exception}`
- Group by lane:
  - `{checklist.source_grep}` — rules to run in step-02
  - `{checklist.dom_render}` — rules to run in step-03
  - `{checklist.human_judgment}` — rules to surface as manual prompts in step-04

### 5. Probe Chrome availability

```bash
# Attempt to load Chrome MCP tools
# (via ToolSearch in the harness — pseudocode)
if chrome_mcp_loadable && project_dev_server_reachable; then
  {chrome_available} = true
else
  {chrome_available} = false
fi
```

If `{chrome_available}` is false, the `dom-render` lane will be skipped in step-03. Note this in `{findings.coverage_notes}`.

### 6. Establish-pattern baseline (cache)

Run a quick pre-scan of the existing codebase to identify which rules will hit "established pattern" exceptions in step-02 and step-04:

```bash
# Example for S-STATUS-04 (no purple/blue/etc status)
rg -c "status.*(?:purple|blue|indigo|violet)" src/routes/ | wc -l
```

If a banned pattern appears in ≥3 distinct routes already, mark the rule as `established_exception` in `{checklist}`. Findings against it will be downgraded to `[note]` in step-04.

### 7. Resolve declared analytics contracts

For each route in `{affected_routes}`, find its active brief and capture the analytics shape it committed to. This is what `C-ARCHETYPE-01` checks the implementation against.

```bash
# Active briefs whose route matches an affected route, that declare a band
grep -l "brief_status: active" {implementation_artifacts}/*brief*.md 2>/dev/null
```

For each matching active brief, read its Block B frontmatter:

- If `band_provenance` ∈ {`inherited`, `recommended-new`} AND `route` matches an affected route, record `{route → {archetype: analytics_archetype, band_provenance, brief_filename}}` into `{brief_archetype_map}`.
- If `band_provenance` is `none`/`recommended-drop`/absent (a pre-contract brief defaults to `none` — see `brief-revision-policy.md` §2 invariant 1a), skip — there is no declared band to enforce.
- If an affected route has no active brief at all, do not invent a contract. Note it in `{findings.coverage_notes}` ("route X has no brief — archetype conformance not checked") so the report does not falsely imply the band was verified.

If `{brief_archetype_map}` is empty, `C-ARCHETYPE-01` is a no-op this run; note it in coverage.

---

## OUTPUT

The workflow now has:

- `{diff_files}` — non-empty, design-relevant file list
- `{affected_routes}` — routes whose rendered output may have changed
- `{checklist}` — parsed rule list, grouped by lane, with `established_exception` flags populated
- `{chrome_available}` — boolean
- `{brief_archetype_map}` — declared analytics archetype per affected route that has a brief-declared band (may be empty)

Proceed to step-02.

---

## FAILURE MODES

- **Diff includes generated files** (e.g., `.svelte-kit/`). Filter these out — they don't represent author intent.
- **Diff includes only docs.** If the only design change is `docs/design-policy.md` → still proceed, but flag in coverage notes that there are no implementation changes to grep against.
- **Branch is behind origin/main.** `git diff origin/main...HEAD` will show a confusing diff. Surface a warning: "Branch may be behind origin/main — consider rebasing before review."
