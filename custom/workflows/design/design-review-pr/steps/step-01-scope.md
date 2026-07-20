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

**Resolve the companion rationale (reasoning evidence).** For each route now in `{brief_archetype_map}`, also look for the analytics presentation rationale that records *why* the archetype was chosen (produced by `design-handoff` step-03b; spec `shared/analytics-rationale.md`):

```bash
# Active rationale whose accompanies_brief points at this brief
grep -l "rationale_status: active" {implementation_artifacts}/design-rationale-*.md 2>/dev/null
```

Match the one whose frontmatter `accompanies_brief == {brief_filename}`. Record into the map entry a `rationale` sub-field:

- **Found:** capture `{rationale_filename}`, its `analytics_archetype`, and whether its body carries the grounding pair (a data dimension AND a user question) and — when the data has a time dimension — the time-in-data check. This is what `C-ARCHETYPE-01` uses to verify the *reasoning* held, not just the rendered form.
- **Not found:** set `rationale: none`. This is NOT a failure — the brief may predate the rationale feature, or the band may be `inherited` without a fresh run. Note it in `{findings.coverage_notes}` ("route X has a declared band but no rationale artifact — archetype *reasoning* not verifiable, only rendered form"). Never imply the reasoning was checked when no rationale exists. Same honesty posture as the no-brief case above.

**Capture the rigor spec (depth evidence).** Read it from the **active brief's §4d (Analytic depth)**, NOT the rationale — §4d is the design contract the implementation must honour, and it is present on any decision surface (including a bandless `detail`/`analytical` page whose decision numbers are in the record/hero, which has no rationale at all). For **every affected route** (not only those with a band), check the brief for a §4d section; when present, build `{brief_rigor_map}[route]` for `C-RIGOR-01`: the `read_sentence`, the `decision_numbers` table (metric · uncertainty · base_rate), the `deciding_field` checks, the `data_gaps`, and the `rigor_verdict`.

- **§4d present:** capture the spec. This is what `C-RIGOR-01` checks the rendered surface against.
- **Also capture `rigor_source`** (`skill` | `inline-fallback` | `not-applicable`; `design-handoff` step-01b §5c-2) into `{brief_rigor_map}[route].rigor_source`. **Why this matters here:** `C-RIGOR-01` checks the *rendered surface against §4d*, taking §4d as ground truth — so it can never audit §4d itself. A §4d written by the by-hand fallback is indistinguishable from a skill-produced one unless the brief says so, which means an under-done spec yields a weak-but-*passing* check. Escalate accordingly:
  - `rigor_source: inline-fallback` → **escalate the human-judgment prompt**: state in the finding prompt that this spec was hand-derived, and ask the reviewer to sanity-check the *spec itself* (is the base rate the right denominator? is the named deciding field genuinely the deciding one, or the handy proxy?) — not only the surface's conformance to it.
  - `rigor_source` **absent** → note it in `{findings.coverage_notes}`: "route X has a §4d with no declared provenance — cannot tell whether the rigor pass ran." Do NOT treat an undeclared §4d as skill-produced.
  - `rigor_source: skill` → normal conformance check. Honest ceiling: this is **self-reported**, so it is evidence, not proof; only the tier-7 invocation marker makes it unfakeable, and even that proves invocation, never quality.
  Apply the identical treatment to `decision_source` on §4e for `C-DECISION-01`.
- **§4d absent:** the brief declares no decision-bearing figures (pure data-entry / passive-review / CRUD) — do not add a `{brief_rigor_map}` entry; rigor does not apply. NOT a failure. (Exception: if the brief's §4a/§4b clearly presents decision figures — a verdict, ROI, KPI — yet has no §4d, that is a handoff defect; note it in `{findings.coverage_notes}`: "route X presents decision figures but the brief has no §4d — analytic depth was not specified.")

**Capture the decision spec (capital-commitment surfaces only).** From the active brief's **§4e (Decision analysis)** — present only when the surface commits a scarce resource under uncertainty (a buy / reorder / sizing) — build `{brief_decision_map}[route]` for `C-DECISION-01`: the `frame`, the `outcome` (method · P(success) · EV · P10 · P90), the `sizing` (quantity · basis), the `sensitivity` (breakeven driver), and the `decision_verdict`.

- **§4e present:** capture the spec. This is what `C-DECISION-01` checks the rendered surface against.
- **§4e absent:** the route is not a capital decision (most routes) — do not add a `{brief_decision_map}` entry; decision analysis does not apply. NOT a failure, and NOT noted (its absence is the norm, unlike §4d).

**Capture the finance contract (finance-shaped surfaces only).** When the active brief is `is_finance_surface: true` (its frontmatter) / carries a **§2b (Finance semantics)** block, build `{brief_finance_map}[route]` for `C-FINANCE-01`: the `column_semantics` (which columns are quantity vs money), the `exception_expectations` (states that must be representable), the `must_not_infer` list (accounting-truth constraints), and the `terminology`. Read from the **brief**, not re-derived.

- **§2b present:** capture it — this is what `C-FINANCE-01` checks the rendered surface against.
- **§2b absent on a finance-shaped route:** if the route clearly handles ledger/inventory/statement/reconciliation data yet the brief has no §2b, that is a possible handoff defect (`finance-domain-pass` may not have run); note it in `{findings.coverage_notes}` ("route X is finance-shaped but the brief has no §2b — finance semantics not specified"). Otherwise (non-finance route) do not add an entry; not a failure, not noted (the norm).

If `{brief_archetype_map}` is empty, `C-ARCHETYPE-01` is a no-op this run; note it in coverage. Likewise if `{brief_rigor_map}` is empty, `C-RIGOR-01` is a no-op; note it. `{brief_decision_map}` empty → `C-DECISION-01` is a no-op (expected on non-decision routes; no note needed). `{brief_finance_map}` empty → `C-FINANCE-01` is a no-op (expected on non-finance routes; no note needed).

---

## OUTPUT

The workflow now has:

- `{diff_files}` — non-empty, design-relevant file list
- `{affected_routes}` — routes whose rendered output may have changed
- `{checklist}` — parsed rule list, grouped by lane, with `established_exception` flags populated
- `{chrome_available}` — boolean
- `{brief_archetype_map}` — declared analytics archetype per affected route that has a brief-declared band (may be empty)
- `{brief_rigor_map}` — declared rigor spec (read sentence, decision numbers + uncertainty/base-rate, deciding fields, data gaps) per affected route whose active brief carries a §4d Analytic depth section (may be empty)
- `{brief_decision_map}` — declared decision spec (framed bet, modelled outcome, sizing, breakeven driver, verdict) per affected route whose active brief carries a §4e Decision analysis section (empty on every non-capital-decision route — the norm)
- `{brief_finance_map}` — declared finance contract (column semantics, exception expectations, must-not-infer, terminology) per affected route whose active brief is `is_finance_surface` / carries a §2b Finance-semantics section (empty on non-finance routes)

Proceed to step-02.

---

## FAILURE MODES

- **Diff includes generated files** (e.g., `.svelte-kit/`). Filter these out — they don't represent author intent.
- **Diff includes only docs.** If the only design change is `docs/design-policy.md` → still proceed, but flag in coverage notes that there are no implementation changes to grep against.
- **Branch is behind origin/main.** `git diff origin/main...HEAD` will show a confusing diff. Surface a warning: "Branch may be behind origin/main — consider rebasing before review."
