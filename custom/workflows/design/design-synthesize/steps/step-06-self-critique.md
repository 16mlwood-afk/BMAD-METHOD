---
name: 'step-06-self-critique'
description: 'Run three sub-checks (hard failures, positive allowlist, drift). Loop back to step 4 with correction notes on failure. Max 3 iterations.'
---

# Step 6: Self-Critique

**Goal:** Verify the synthesized bundle clears two distinct bars:

- **Policy half (a/b/c) — compliance.** Hard failures from the policy (a), the policy's contract-critical positive-assertion allowlist (b), and — in refine-screen mode only — the drift contract against the prior implementation (c).
- **Visual half (d/e/f) — lift & taste.** Self-rated visual quality across hierarchy/density/typography/ergonomics (d), the two-sided lift test (e), and exemplar alignment (f). Passing the policy half is necessary but not sufficient — a bundle that satisfies every hard-failure rule and still reads as a generic spreadsheet has not done the work this step exists to enforce.

On failure of any sub-check, return to step 4 with a precise correction note. Max 3 iterations across ALL sub-checks combined; on the 3rd failure, record the failure mode and proceed to step 7. Visual failures additionally set `{needs_human_review} = true` so step 7's hand-off line routes the user to human design review instead of `design-implement`.

**Loop control:** This step is the ONLY step that loops. The loop target is step 4. The loop terminates at iteration 3 regardless of result. `{review_iterations}` separately tracks how many of those iterations were driven by visual sub-checks (d/e/f) — distinct from `{iteration_count}` which covers all loop returns.

---

## RULES

- **Policy half is policy-derived only.** Sub-checks (a) and (b) verify the bundle against `{hard_failures}` and `{positive_allowlist}` loaded in step 2 — NOT against workflow invariants. Workflow invariants (e.g., "every `var(--*)` resolves in tokens.css", "no config-dependent Tailwind classes", "manifest never disagrees with HTML on a visual fact", "bundle is self-contained") are checked unconditionally in step 7's manifest-validation pass. Conflating these two categories was an earlier draft error — keep them separate.
- **Visual half is taste-derived, not policy-derived.** Sub-checks (d), (e), (f) evaluate the bundle against principles policy can't easily enumerate: hierarchy quality, density calibration, lift over a baseline operational screen, alignment with the project's own gold-standard work. A bundle can satisfy every hard-failure rule in (a) and still fail (d/e/f) — that is the failure mode this half exists to catch.
- **`design-synthesize` does NOT invent allowlist items.** Sub-check (b) iterates `{positive_allowlist}` only. New positive assertions enter the system via `modify-design-policy`, not this workflow.
- **Drift in refine-screen is failure, not noise.** Any non-empty diff in an `unchanged_region` against the prior implementation is a synthesis bug. Either eliminate the drift in step 4, or move the region into `targeted_changes` in the brief (which requires the user's involvement — this workflow does not edit briefs).
- **One correction per loop.** When multiple sub-checks fail in the same iteration, emit ONE consolidated correction note covering all failures (policy and visual together), return to step 4 once, and re-check everything on the next iteration. Do not loop step 4 once per failure.
- **At iteration 3, do not loop.** Set `{compliance_state}` to the failure mode, emit the bundle anyway in step 7, surface the failure to the user. The bundle is shipped with `compliance_state: hard_failed | positive_failed | drift_failed | lift_failed | exemplar_failed` so the user sees the gap before invoking `design-implement`. Visual failures additionally set `{needs_human_review} = true`.
- **`acceptable` triggers one refine pass; `weak` does not.** Sub-check (d) rates `{visual_quality}` as `excellent | acceptable | weak`. `excellent` proceeds with no loop. `acceptable` triggers exactly ONE refine pass (incrementing `{review_iterations}`) targeted at hierarchy, density, and operational framing; if the second pass still rates `acceptable`, accept the rating and proceed. `weak` does NOT trigger a refine pass — it proceeds to step 7 with `needs_human_review: true` because the synthesizer's own judgment is that the bundle is below the bar a single refine pass can correct.
- **Skill-routing check is binary AND now checks for `{frontend_skill}`.** If `{skills_invoked}` is empty OR is missing the resolved `{frontend_skill}` entry, that's a routing failure regardless of iteration count — return to step 4 with: `step 6: skills_invoked is empty or missing {frontend_skill}. Route per workflow.md §SKILL ROUTING before re-emitting.`
- **Violation arrays are mandatory outputs.** All six arrays — `{hard_failure_violations}`, `{positive_assertion_violations}`, `{drift_violations}`, `{negative_lift_violations}`, `{positive_lift_violations}`, `{exemplar_violations}` — MUST be initialized and emitted in the manifest, even when empty `[]`. An empty array is a falsifiable "no violations" claim that downstream consumers can audit; an omitted array is opaque and forbidden. Same rule for `{visual_quality_axes}` (per-axis rating + evidence string) and `{exemplar_comparisons}` (per-exemplar consulted flag + per-dimension diffs): always present, never omitted. A run that finishes step 7 without these structures is a workflow bug, not a passing run.
- **Macro-hierarchy is a falsifiable claim, not a vibe.** Every screen MUST emit `{macro_hierarchy}[screen]` with `eye_lands_first` (a single named element) and `above_fold_allocation` (integer percentages summing to exactly 100). A sum ≠ 100, an unresolvable `eye_lands_first`, or a vague evidence string is a workflow bug — Axis 1 is forced to `weak` and the synthesizer must re-rate.
- **Exemplars must be consulted, not just listed.** Every entry in `{exemplars}` MUST have `consulted: true` in `{exemplar_comparisons}` by the end of this step, with per-dimension diff strings (aligned or not — both are valid) for every screen. A `consulted: false` entry is a routing failure (not iteration-counted, same precedent as the skill-routing check) — return to step 4 to Read the unconsulted exemplars before re-emitting.
- **Anti-spreadsheet hard floor.** Per §6 Axis 5 T4: a screen whose only differences from a plain styled `<table>` are pills and a summary line CANNOT earn `generic_look: strong`, and the bundle CANNOT earn `visual_quality: excellent`. This floor is the failure mode the rubric exists to catch — "policy-compliant spreadsheet" is the named failure, and it caps at `acceptable`.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Increment the iteration counter

```
{iteration_count} = {iteration_count} + 1   # initialized to 0 in step 1
```

If `{iteration_count} == 1`, this is the first critique pass. If `==3`, it's the last — failures here are not re-looped; they're recorded.

### 2. Skill-routing check (binary, runs every iteration)

```
if len({skills_invoked}) == 0:
    correction = "step 6 routing: {skills_invoked} is empty. Per workflow.md §SKILL ROUTING, design-policy-canonical and the project frontend skill ({frontend_skill}) MUST be invoked in step 4 before emitting. Re-enter step 4 with the skill routing applied."
    GOTO step 4 with {correction_note} = correction

if {frontend_skill} not in {skills_invoked}:
    correction = "step 6 routing: {frontend_skill} (resolved in step 3) is not present in {skills_invoked}. Per workflow.md §SKILL ROUTING → 'Always invoke', the resolved frontend skill is MANDATORY — synthesis without it produces a policy-compliant wireframe rather than a designed screen. Re-enter step 4 and invoke {frontend_skill} before composing."
    GOTO step 4 with {correction_note} = correction
```

These checks are unconditional and not subject to the iteration cap — they represent a workflow bug (skill never invoked), not a synthesis quality issue.

### 3. Sub-check (a) — Hard-failure pass

For each rule in `{hard_failures}`:

1. Translate the rule into a verifiable check against the bundle. Most policy hard-failure rules are stated as anti-patterns — translate to a pattern detector.
2. Run the detector against every `<screen>.html` in the bundle.

Common hard-failure detectors (extend per project):

| Policy rule pattern | Detector |
|---|---|
| "No colored pill / lozenge badges" | Scan for elements with `border-radius: 9999px` (or `border-radius: 100px+`) AND a colored background that isn't a status token. |
| "No raw color values for status" | Scan for `color:` / `background:` declarations using `#hex` or `rgb()` literals on elements whose `data-component` matches `*Badge*`, `*Status*`, `*Indicator*`. |
| "No decorative drop shadows" | Scan for `box-shadow:` declarations with non-zero offset+blur on non-modal elements. |
| "Components have stable identifiers" | Scan every interactive/named component for a `data-component=` attribute. |
| "Status indicators use status tokens" | Scan status-related elements for `var(--status-*)` references; reject raw colors. |

For project-specific rules without a generic detector, fall back to AI-judgment review of the rule text against the bundle HTML. Be conservative — false negatives (missed violations) are safer than false positives (correction loops on phantom issues).

**Lift test (always runs as a hard-failure check item, per workflow.md §Critical Rules / policy §10):**

If the synthesized bundle would render acceptably as a different SaaS product (a generic CRM, an HR dashboard, a marketing tool, a generic admin panel) without modification, it has failed the lift test. The bundle must read as a high-trust UK VAT finance operations tool — calm fintech, never marketing or playful SaaS (policy §1).

Lift-test detectors:

- **Placeholder data:** `lorem ipsum`, `John Doe`, generic `Item 1 / Item 2`, `acme@example.com`, `$1,234.56` (USD when the project is UK-GBP), placeholder usernames. The brief's `{data_shape}` provides real domain content — invoices, VAT periods, suppliers, CDS records, GBP amounts. Failure to use it is a lift-test failure.
- **Generic SaaS chrome:** colored gradient hero, animated illustrations, marketing copy ("Welcome back!", "Get started"), pricing tables, testimonials.
- **CRM-shaped composition:** card-grid openers on landing screens (policy §5 anti-default), pipeline-stage Kanban without finance-specific data, generic "Activity feed" sidebars unrelated to the brief.
- **Wrong currency / locale:** `$` instead of `£`, US date formats (`MM/DD/YYYY`) when policy/brief specifies UK formats, `state` instead of `country`.
- **Page-mode mismatch:** an `operational` page that opens with a KPI grid (policy §5 / §6). An `analytical` page that opens with a generic card grid instead of a chart-led summary. A `detail` view that introduces KPI cards or charts (policy §7).

Treat any lift-test violation as a hard-failure rule entry (synthetic `source_line: "policy §1/§10 (lift test)"`) and collect into `{hard_failure_violations}` alongside the explicit policy rules.

Collect violations into `{hard_failure_violations}`:

```
[
  { rule: "No colored pill badges", source_line: 89, file: "bundle/main.html", line: 47, snippet: "<span style='border-radius: 9999px; background: #f59e0b;'>Warning</span>" },
  ...
]
```

### 4. Sub-check (b) — Positive-allowlist pass

Skip if `{positive_allowlist}` is empty (step 2 logged this).

For each assertion in `{positive_allowlist}`:

1. Translate to a positive detector (the bundle MUST contain X).
2. Run against every `<screen>.html` in the bundle.

Common positive-assertion detectors:

| Policy assertion pattern | Detector |
|---|---|
| "Components have stable identifiers" | Every region with a named role (header, table, card, drawer) has a `data-component=` attribute. |
| "Status indicators use status tokens, not raw colors" | Every status-related element uses `var(--status-*)` references — no raw color literals. |
| "Tables are flat — no card-wrapped rows" | Table rows are direct children of `<tbody>` (or the equivalent CSS grid contract), not wrapped in `<div>` "cards" inside the row. |
| "Filter rows render as a single horizontal band" | The filter region is a single flex container with `flex-direction: row`, not stacked into multiple bands. |

Collect violations into `{positive_assertion_violations}`:

```
[
  { assertion: "Status indicators use status tokens", source_line: 134, file: "bundle/main.html", line: 102, snippet: "..." },
  ...
]
```

### 5. Sub-check (c) — Drift pass (refine-screen only)

Skip if `{mode} != "refine-screen"`.

For each screen in `{screens}`:

1. Compare the bundle's HTML region-by-region against `{prior_impl_content[route]}` for that screen.
2. Region identity comes from `data-region=` attributes in both the prior implementation and the bundle.
3. For each region in `{unchanged_regions}`: the bundle's region must match the prior implementation modulo token substitution (e.g., `#f59e0b` in prior vs `var(--status-warning)` in bundle is acceptable IF the token resolves to `#f59e0b`). Structural changes (different tag, different children, different inline-style topology) are NOT acceptable.
4. For each region in `{targeted_changes}`: the bundle's region SHOULD differ from the prior — that's the point. No check needed.

Collect violations into `{drift_violations}`:

```
[
  { region: "footer", file: "bundle/list.html", lines: "412-440", prior_file: "src/routes/.../+page.svelte", prior_lines: "412-440", diff: "<unified diff of the region>" },
  ...
]
```

A region that doesn't appear in either `targeted_changes` or `unchanged_regions` is an UNDECLARED region — surface as a drift violation: `region 'X' appears in bundle but is not declared in either targeted_changes or unchanged_regions. Declare it.`

### 6. Sub-check (d) — Visual-quality review

Read each `bundle/<screen>.html` and each `bundle/screenshot-<screen>.png` (if `--no-render` was not used; otherwise read only the HTML and note `screenshot_skipped: dev_no_render`).

Evaluate each screen along five axes against the explicit test cases below. Every rating MUST cite at least one test case in `{visual_quality_axes}[axis].evidence` — a rating without a cited test case is a workflow bug, not a judgment call. "Excellent" is a falsifiable claim only when the evidence string names the passing tests; an unevidenced rating is treated as `weak` for aggregation purposes.

#### Axis rubric — test cases per level

For each axis, classify the screen as `strong | adequate | weak`. The test cases below are the rubric — Step-06 evidence strings reference them by ID (T1, T2, …).

**Axis 1 — Visual hierarchy**
- *Strong* — passes ALL of:
  - **T1**: Above-the-fold contains a dominant primary element (band, summary header, or section-titled summary) that states current state BEFORE the table — the eye lands on the primary question, not on row data.
  - **T2**: Table is framed by a section heading + summary line, OR sits beneath a summary band; never dropped onto the page raw.
  - **T3**: Clear focal region — alert/anomaly rows or counters break out of the routine treatment with visible escalation (weight, color, or position).
- *Adequate* — passes T1 OR T2 (not both); T3 may be marginal.
- *Weak* — fails T1 AND T2: the table is the first thing on the page with no framing, no summary band, and no section heading; the user must scan rows to know what's happening.

**Axis 2 — Whitespace & density**
- *Strong* — passes ALL of:
  - **T1**: Rhythm varies between sections — header padding > summary padding > row padding > inline-detail padding. Not uniform.
  - **T2**: Density matches the brief's `{page_mode}` declaration: `operational` = tight rows (24–32px), `analytical` = relaxed (40px+), `detail` = moderate (32–40px).
  - **T3**: Headers and separators have explicit air around them — at least 1.5× the row gap above any section break.
- *Adequate* — passes T2 (density matches mode); T1 OR T3 may be uniform/marginal.
- *Weak* — uniform padding everywhere (suffocating), OR all gasping (no rhythm), OR density mismatches page mode (e.g., operational page with 50px rows).

**Axis 3 — Typography use**
- *Strong* — passes ALL of:
  - **T1**: Type scale used purposefully — body, secondary, labels, numbers all distinguishable by size AND weight (not just one).
  - **T2**: Tabular numbers (`font-variant-numeric: tabular-nums`) in EVERY numeric column; numbers align on the decimal.
  - **T3**: Weight variation is deliberate and tied to information role (label vs value vs hint), not decorative.
- *Adequate* — passes T1 AND T2; T3 may be marginal.
- *Weak* — uniformly small text everywhere, OR all-bold/all-thin, OR non-tabular numbers misaligning numeric columns.

**Axis 4 — Table ergonomics**
- *Strong* — passes ALL of:
  - **T1**: Row states are visually distinct — hover, selected, alert, disabled — and each treatment escalates above the routine row.
  - **T2**: Column widths fit the data (currency columns sized for the longest expected value; status column has explicit width to act as visual anchor).
  - **T3**: Numeric columns are right-aligned; the status column is the visual anchor for state (not just colored text).
- *Adequate* — passes T1 AND (T2 OR T3); the missing item is marginal, not absent.
- *Weak* — wall of identical-looking rows (no row states), OR columns sized arbitrarily, OR numbers left-aligned in numeric columns.

**Axis 5 — AI/generic template look**
- *Strong* — passes ALL of:
  - **T1**: Real domain content from the brief's `{data_shape}` — invoices, VAT periods, suppliers, CDS records, GBP amounts. No placeholder data, no `John Doe`, no `$1,234.56`.
  - **T2**: Specific to this product — UK VAT finance-operations vocabulary in section titles, column headers, and empty-state copy. Could NOT be mistaken for a generic CRM/HR/admin tool.
  - **T3**: Operational narrative is present — the screen tells a story about what is happening (e.g., "12 invoices pending OCR · 3 anomalies · 1 overdue") — not just a list.
  - **T4 (anti-spreadsheet)**: The screen contains at least one composition element that is NOT a styled `<table>`, a summary line, or status pills. Counter-examples that FAIL T4: a screen whose entire composition is a single `<table>` with status pills and a one-line totals row above; the operational analytics band is just a stack of counters with no chart/sparkline/state-grouped filter strip.
- *Adequate* — passes T1 AND T2; T3 may be marginal; **T4 must still pass**.
- *Weak* — placeholder data, OR could be a different product, OR no operational narrative, OR fails T4.

**Anti-spreadsheet hard floor.** If a screen fails T4 (its only differences from a plain styled `<table>` are pills and a summary line), then:

- `generic_look` CANNOT be rated `strong`. Cap at `adequate` at most; `weak` if T4 is the dominant failure.
- The bundle's overall `{visual_quality}` CANNOT be `excellent`. Cap at `acceptable` regardless of other axis ratings.

This floor is the failure mode the rubric exists to enforce. A bundle that satisfies every other axis but reads as a single styled table with pills has not done the work — it cannot be labeled "excellent".

#### Macro-hierarchy judgment (mandatory, every screen)

In addition to per-axis ratings, record an explicit macro-hierarchy judgment per screen in `{macro_hierarchy}` — a falsifiable claim about where attention lands above the fold:

```
{macro_hierarchy} = {
  <screen_path>: {
    eye_lands_first: <element name>,           # one of: "summary band" | "filter strip" | "table header" | "primary heading" | "chart" | "detail header" | "drawer"
    above_fold_allocation: {                    # integer percentages of the top 900px viewport (DPR=2), MUST sum to 100
      band: <int 0-100>,                        # operational-analytics-band or summary band
      table: <int 0-100>,                       # table including header
      controls: <int 0-100>,                    # filter strip + action bar
      header: <int 0-100>,                      # page title + breadcrumb + meta
      other: <int 0-100>                        # sidebars, drawers, empty space, anything else
    },
    evidence: <one-line string>,                # e.g., "screenshot top 900px: summary band 35%, filter strip 12%, table header + first 4 rows 45%, page header 8%"
  },
  ...
}
```

Rules:

- `above_fold_allocation` percentages MUST sum to exactly 100. A sum ≠ 100 is a workflow bug — halt the critique pass and resolve before continuing.
- `eye_lands_first` MUST be a single element name. If the synthesizer cannot identify one ("everything competes equally"), the screen has no hierarchy and Axis 1 MUST be rated `weak`.
- `evidence` MUST quote allocation percentages and at least one screen element by name — a generic "looks fine" evidence string is treated as missing.

#### Composing {visual_quality}

```
strong_count   = count of axes rated "strong" across all screens (averaged)
adequate_count = count of axes rated "adequate"
weak_count     = count of axes rated "weak"

if weak_count >= 2:            {visual_quality} = "weak"
elif weak_count == 1:          {visual_quality} = "acceptable"   # one weak axis, refine targeted at it
elif strong_count >= 3:        {visual_quality} = "excellent"
else:                          {visual_quality} = "acceptable"
```

Then apply the **anti-spreadsheet floor**:

```
if any screen failed Axis 5 T4:
    if {visual_quality_axes}[generic_look].rating == "strong":
        downgrade {visual_quality_axes}[generic_look].rating to "adequate"  # T4 failure forbids strong
    if {visual_quality} == "excellent":
        {visual_quality} = "acceptable"                                      # T4 failure forbids excellent
    # the weak-count rule already prevents "excellent" when generic_look is weak; this floor adds the cap when T4 is the only generic_look problem
```

Then apply the **macro-hierarchy cap**:

```
if any screen's macro_hierarchy.eye_lands_first is unresolvable (no dominant element):
    Axis 1 (visual hierarchy) MUST be "weak" for that screen — re-rate before composing
```

Record per-axis ratings AND evidence strings in `{visual_quality_axes}` for the manifest's audit trail. Every axis must have both fields; missing evidence is a workflow bug:

```
{visual_quality_axes} = {
  hierarchy:        { rating: "strong",   evidence: "passes T1 (summary band above table on bundle/list.html), T2 (table framed by section heading 'In progress')" },
  density:          { rating: "adequate", evidence: "passes T2 (28px rows match operational mode); T1 marginal — rhythm between summary and table is similar to between table rows" },
  typography:       { rating: "strong",   evidence: "passes T1, T2, T3 — type scale 18/14/13/12, tabular-nums on amount columns, weight tied to role (label 500, value 600, hint 400)" },
  table_ergonomics: { rating: "strong",   evidence: "passes T1 (hover/selected/alert escalated via border-l-2 + bg-status-*), T2 (status column 100px), T3 (amount columns right-aligned tabular)" },
  generic_look:     { rating: "strong",   evidence: "passes T1 (real GBP/VAT data from data_shape), T2 (UK VAT vocabulary in headers), T3 ('12 pending OCR · 3 anomalies' narrative line), T4 (top band is a state-grouped filter strip with sparkline, not a styled table)" },
}
```

Multi-screen bundles aggregate by averaging axes across screens; one weak screen in a multi-screen flow forces at least `acceptable` overall. Anti-spreadsheet T4 failure on ANY screen forces the bundle below `excellent`.

If `{visual_quality} == "weak"`:
- Set `{needs_human_review} = true`.
- Do NOT loop — `weak` is a synthesizer's-own-judgment signal that one refine pass cannot close the gap. Proceed to (e)/(f) for the rest of the visual-half assessment; on aggregation in §10, this will emit the bundle with `needs_human_review: true`.

If `{visual_quality} == "acceptable"` AND `{review_iterations} == 0`:
- Collect `{visual_quality_correction}` — a targeted note naming the weak/adequate axes and the screens they appeared on (e.g., `"step 6(d) acceptable: visual hierarchy weak on bundle/list.html — table is dropped onto page without a summary band or section heading; lift by adding an operational summary above the table. Density adequate but uniform — vary rhythm between header, summary, and table."`).
- This contributes to the loop decision in §10.

If `{visual_quality} == "acceptable"` AND `{review_iterations} >= 1`:
- One refine pass already consumed — accept the rating and proceed.

If `{visual_quality} == "excellent"`:
- No loop contribution from (d).

### 7. Sub-check (e) — Lift-over-baseline check

Per workflow.md §Critical Rules → "Lift test (policy §10) — two-sided contract", BOTH halves must pass.

**Mandatory output.** `{negative_lift_violations}` and `{positive_lift_violations}` MUST always be written — even when empty `[]`. An empty array is a falsifiable "no violations" claim that downstream consumers can audit; an omitted array is opaque and forbidden. A run that finishes step 7 without both arrays present in the manifest's `violations.lift` section is a workflow bug.

**Negative half** (already partially covered by §3 lift-test detectors — placeholder data, generic SaaS chrome, CRM-shaped composition, wrong currency/locale, page-mode mismatch). Re-run each detector for this sub-check and append a `{negative_lift_violations}` entry for every hit:

```
{negative_lift_violations} = [
  { screen: <path>,
    detector: "placeholder_data" | "generic_chrome" | "crm_composition" | "wrong_locale" | "page_mode_mismatch",
    detail: <one-line evidence string, naming the offending element / text / class>,
    line: <int or null> },
  ...
]
```

Even on pass, initialize `{negative_lift_violations} = []` explicitly.

**Positive half** — verify all four requirements:

| # | Requirement | Detector |
|---|---|---|
| 1 | Answers the screen's core operational question at a glance | For `operational` page mode: is there a top band (`operational-analytics-band`) or summary header that states current state (counts, totals, anomalies) BEFORE the user has to read the table? For `analytical`: chart-led summary above drill-down? For `detail`: the entity's status/summary above its sections? Missing = failure. |
| 2 | Surfaces the screen's key states above or beside the worklist | Are pending/failed/anomalies/overdue/awaiting-response visible at the top band or filter strip, not only inside individual rows? Look for explicit state counters or state-grouped filters. Missing = failure. |
| 3 | Visually distinguishes primary actions and alerts from background noise | Does the primary action have a distinct treatment from secondary actions (size, weight, position, or color escalation per policy §3)? Are alert/error states visually escalated above routine row treatment? Failure if primary action is indistinguishable from secondary, or alert rows blend into routine rows. |
| 4 | Aligned with loaded exemplars | Deferred to sub-check (f) below. |

Collect `{positive_lift_violations}` for each failed requirement (initialize `[]` explicitly when nothing fails):

```
{positive_lift_violations} = [
  { requirement: 1 | 2 | 3,
    requirement_label: "core operational question answered at a glance" | "key states surfaced above the worklist" | "primary actions and alerts visually escalated",
    screen: <path>,
    detail: <one-line evidence string>,
    fix: <one-line correction directive, ties to brief / exemplar / policy> },
  ...
]
```

Decision:

```
if len({negative_lift_violations}) > 0 OR len({positive_lift_violations}) > 0:
    {visual_lift_passed} = false
    if {iteration_count} == 3:
        {compliance_state} candidate = "lift_failed"
        {needs_human_review} = true
else:
    {visual_lift_passed} = true

# Arrays are written either way — empty [] is the affirmative no-violations claim.
```

### 8. Sub-check (f) — Exemplar alignment

Skip if `{exemplars}` is empty (brief had `exemplar_anchoring: waived`); record `{exemplar_alignment} = "aligned"` (vacuously), set `{exemplar_comparisons} = {}` (vacuously — none to consult), `{exemplar_violations} = []`, and move on.

**Per-exemplar audit trail — mandatory.** For every entry in `{exemplars}`:

1. **Open the file with the Read tool during this critique pass.** Not "trust step 4 read it"; this sub-check verifies the synthesizer actually consulted the exemplar against the bundle output. Record `consulted: true` only after a successful Read.
2. **Emit a per-dimension diff string for every (exemplar × screen) pair** — even when the dimension is aligned. "matches: both open with summary band above table" is a valid diff string and is equally falsifiable as a misalignment string. An empty / missing diff for any (exemplar, screen, dimension) tuple is a workflow bug.

For each screen, compare against EVERY exemplar in `{exemplars}` along these dimensions:

| Dimension | What to compare |
|---|---|
| `hierarchy` | Does the screen open with the same KIND of element as the exemplar (summary band, header, chart, etc.)? Does section ordering follow the same pattern? |
| `density` | Does the screen feel as tight/loose as the exemplar? Row heights, gutter widths, header weight should be in the same family. |
| `top_band` | If the exemplar uses a top band, does the screen? If the exemplar doesn't, the screen shouldn't either (unless the brief explicitly authorizes). |
| `table_framing` | Are tables introduced the same way — section heading + summary line, summary band + filter strip, or direct (no framing)? |
| `state_presentation` | Are status/state treatments consistent (badge style, alert escalation, empty/loading/error states)? |

Record a structured comparison per exemplar in `{exemplar_comparisons}`:

```
{exemplar_comparisons} = {
  <exemplar_path>: {
    consulted: true | false,                        # true only after Read of <exemplar_path> in this critique pass
    consulted_at_step: <iteration_count>,           # which loop iteration did the consult happen on
    diffs: {
      <screen_path>: {
        hierarchy:          { aligned: true|false, diff: <one-line, e.g., "matches: both open with state-grouped filter strip above table" OR "differs: exemplar opens with summary band; screen opens with bare table heading"> },
        density:            { aligned: true|false, diff: <one-line> },
        top_band:           { aligned: true|false, diff: <one-line> },
        table_framing:      { aligned: true|false, diff: <one-line> },
        state_presentation: { aligned: true|false, diff: <one-line> },
      },
      ...                                          # one entry per screen in {screens}
    },
  },
  ...                                              # one entry per exemplar in {exemplars}
}
```

**Consulted-flag enforcement.** Before classifying alignment, scan `{exemplar_comparisons}` for any entry with `consulted: false`:

```
unconsulted = [path for path, entry in {exemplar_comparisons}.items() if not entry.consulted]
if unconsulted:
    correction = (
        f"step 6(f) routing: the following exemplars were never opened during synthesis "
        f"or this critique pass: {unconsulted}. "
        f"Per workflow.md §Exemplar alignment (anchoring rule), every entry in "
        f"{{exemplars}} MUST be opened and compared. Re-enter step 4 and Read each "
        f"unconsulted exemplar before re-emitting; on re-entry to step 6, populate "
        f"diffs for every (exemplar × screen × dimension) tuple."
    )
    GOTO step 4 with {correction_note} = correction
    # This routing failure is NOT counted against {iteration_count} — it is a workflow bug, not a synthesis quality issue (same precedent as the skill-routing check in §2).
```

Classify alignment per screen as `aligned | deviated_with_brief_authorization | deviated_unauthorized` based on the diffs:

- **aligned** — every dimension in every (exemplar × screen) pair has `aligned: true`.
- **deviated_with_brief_authorization** — at least one dimension has `aligned: false` AND the brief explicitly calls for the departure (e.g., brief §"visual direction" says "depart from the dense table pattern — use a card-grid because the page mode is `analytical`"). The departure quotes the brief language in `{exemplar_alignment_rationale}`.
- **deviated_unauthorized** — at least one dimension has `aligned: false` AND the brief does not authorize it.

Aggregate across screens: any `deviated_unauthorized` makes the bundle's `{exemplar_alignment} = "deviated_unauthorized"`. All `aligned` makes it `"aligned"`. Mix of `aligned` and `deviated_with_brief_authorization` (but no unauthorized) makes it `"deviated_with_brief_authorization"`.

Decision:

```
{exemplar_violations} = []   # initialize explicitly, even on pass
if {exemplar_alignment} == "deviated_unauthorized":
    {exemplar_violations} = [
      { screen: <path>,
        dimension: "hierarchy" | "density" | "top_band" | "table_framing" | "state_presentation",
        exemplar: <path>,
        diff: <the diff string from {exemplar_comparisons}[exemplar].diffs[screen][dimension].diff>,
        detail: <one-line: what departed, why it isn't brief-authorized>,
        fix: <one-line: match the exemplar OR get brief authorization (cite section)> },
      ...
    ]
    if {iteration_count} == 3:
        {compliance_state} candidate = "exemplar_failed"
        {needs_human_review} = true
```

### 9. Compose the combined correction note (when looping)

When returning to step 4, the correction note combines all sub-check failures into ONE consolidated message. Add the visual-half violations to the existing policy-half template:

```
Step 6 correction (iteration {iteration_count}/3, review iteration {review_iterations}):

[POLICY HALF]
Hard failures ({N}): ...
Positive assertions ({M}): ...
Drift ({K}): ...

[VISUAL HALF]
Visual quality ({visual_quality}): {visual_quality_correction or "n/a"}
  - per-axis ratings: hierarchy={rating}, density={rating}, typography={rating}, table={rating}, generic-look={rating}
  - weak axes: {list}

Lift over baseline ({visual_lift_passed ? "passed" : "failed"}):
  Negative half violations ({L}):
    - {screen}: placeholder data / generic chrome / CRM composition / wrong locale / page-mode mismatch
      detail: {one-line}
  Positive half violations ({P}):
    - bundle/{screen}: requirement {N} ({description})
      detail: {one-line, ties to exemplar or policy}
      fix: {what to add or change}

Exemplar alignment ({exemplar_alignment}):
  Deviations ({Q}):
    - bundle/{screen}, dimension={name}, exemplar={path}
      detail: {what departed}
      fix: either match the exemplar OR get brief authorization in {brief_path} (then re-invoke)

Do not modify regions not listed above. Re-emit only the affected files.
```

### 10. Aggregate failures and decide

```python
policy_violations = (
    len(hard_failure_violations) +
    len(positive_assertion_violations) +
    len(drift_violations)
)
visual_violations = (
    (1 if {visual_quality} in ("acceptable", "weak") and {review_iterations} == 0 else 0) +
    (1 if not {visual_lift_passed} else 0) +
    (1 if {exemplar_alignment} == "deviated_unauthorized" else 0)
)
total_violations = policy_violations + visual_violations

if total_violations == 0:
    {compliance_state} = "pass"
    GOTO step 7
elif iteration_count < 3:
    # Track which loop iterations were driven by visual sub-checks (d/e/f only).
    if visual_violations > 0 and policy_violations == 0:
        {review_iterations} += 1
    elif visual_violations > 0:
        {review_iterations} += 1   # visual contributed even if mixed
    correction_note = compose_combined_correction(
        hard_failure_violations,
        positive_assertion_violations,
        drift_violations,
        visual_quality_correction,
        positive_lift_violations,
        negative_lift_violations,
        exemplar_violations,
    )
    GOTO step 4 with {correction_note}
else:  # iteration_count == 3
    # Policy failures win priority for compliance_state; visual failures additionally set needs_human_review.
    if hard_failure_violations:           {compliance_state} = "hard_failed"
    elif positive_assertion_violations:   {compliance_state} = "positive_failed"
    elif drift_violations:                {compliance_state} = "drift_failed"
    elif not {visual_lift_passed}:        {compliance_state} = "lift_failed"
    elif {exemplar_alignment} == "deviated_unauthorized":
                                          {compliance_state} = "exemplar_failed"
    else:                                 {compliance_state} = "pass"   # only visual_quality=="weak" remained; no compliance_state change, but needs_human_review is set
    # needs_human_review is set whenever any visual sub-check signals it (weak quality, lift failure, exemplar deviation)
    if ({visual_quality} == "weak" or
        not {visual_lift_passed} or
        {exemplar_alignment} == "deviated_unauthorized"):
        {needs_human_review} = true
    print warning to user (see §11)
    GOTO step 7  # emit anyway, with failure mode flagged
```

### 11. Print the critique summary

On `pass`:

```
✓ Self-critique passed (iteration {iteration_count}/3, review iterations {review_iterations}):
  [POLICY HALF]
  hard failures:        0/{len(hard_failures)} rules violated
  positive assertions:  0/{len(positive_allowlist)} assertions failed
  drift:                0 regions (refine-screen) or n/a (fresh-design)

  [VISUAL HALF]
  visual quality:       {visual_quality}
  lift over baseline:   passed (negative + positive halves)
  exemplar alignment:   {exemplar_alignment}

  compliance_state:     pass
  needs_human_review:   false

Proceeding to step 7: emit manifest.
```

On loop (iteration < 3):

```
✗ Self-critique failures (iteration {iteration_count}/3, review iterations {review_iterations}):
  [POLICY HALF]
  hard failures:        {len(hard_failure_violations)}/{len(hard_failures)}
  positive assertions:  {len(positive_assertion_violations)}/{len(positive_allowlist)}
  drift:                {len(drift_violations)}

  [VISUAL HALF]
  visual quality:       {visual_quality} ({"refine pass triggered" if acceptable and review_iterations==0 else "no refine"})
  lift over baseline:   {"passed" if visual_lift_passed else "failed (" + str(len(negative_lift_violations)) + " neg / " + str(len(positive_lift_violations)) + " pos)"}
  exemplar alignment:   {exemplar_alignment} ({len(exemplar_violations)} deviations)

Returning to step 4 with combined correction note.
```

On final-iteration failure (iteration == 3):

```
⚠ Self-critique failed at iteration 3 — emitting bundle anyway with compliance_state={compliance_state}:
  [POLICY HALF]
  hard failures:        {len(hard_failure_violations)}
  positive assertions:  {len(positive_assertion_violations)}
  drift:                {len(drift_violations)}

  [VISUAL HALF]
  visual quality:       {visual_quality}
  lift over baseline:   {"passed" if visual_lift_passed else "failed"}
  exemplar alignment:   {exemplar_alignment}

  needs_human_review:   {needs_human_review}

The bundle is being emitted so you can inspect it. When needs_human_review is true,
design-implement WILL REFUSE this bundle (per the manifest gating contract) and
the handoff line in step 7 will route you to design-review instead. Address the
violations before running design-implement OR route through design-review first.

Proceeding to step 7: emit manifest.
```

Then load `step-07-emit-manifest.md`.

---

## STATE CHECKPOINT

After this step (when proceeding to step 7):

- `{iteration_count}` is 1, 2, or 3.
- `{review_iterations}` is 0, 1, or 2 (visual-half loops only; subset of `{iteration_count}`).
- `{compliance_state}` ∈ `{pass, hard_failed, positive_failed, drift_failed, lift_failed, exemplar_failed}`.
- `{visual_quality}` ∈ `{excellent, acceptable, weak}`.
- `{visual_quality_axes}` populated for ALL 5 axes (hierarchy, density, typography, table_ergonomics, generic_look). Each entry has both `rating` ∈ `{strong, adequate, weak}` AND a non-empty `evidence` string citing the passing test-case IDs (T1, T2, …). Missing rating or missing/generic evidence string ("looks fine", "good") is a workflow bug.
- `{macro_hierarchy}` populated for every screen in `{screens}`. Each entry has `eye_lands_first` (a single element name), `above_fold_allocation` (integer percentages summing to exactly 100), and `evidence` (one-line string quoting allocation percentages and at least one screen element by name). Missing entry, sum ≠ 100, or unresolvable `eye_lands_first` is a workflow bug.
- `{visual_lift_passed}` is a boolean.
- `{exemplar_alignment}` ∈ `{aligned, deviated_with_brief_authorization, deviated_unauthorized}`.
- `{exemplar_comparisons}` populated for EVERY entry in `{exemplars}` (or `{}` when `exemplar_anchoring: waived`). Each entry has `consulted: true | false`, `consulted_at_step` (iteration number), and `diffs` keyed by `<screen_path>` with sub-entries for ALL FIVE dimensions (`hierarchy`, `density`, `top_band`, `table_framing`, `state_presentation`) each carrying `aligned: bool` and a non-empty `diff` string. A `consulted: false` entry that survived past step 6 is a workflow bug (routing failure should have looped step 4).
- `{needs_human_review}` is a boolean. True whenever `{visual_quality} == "weak"`, `{visual_lift_passed} == false`, or `{exemplar_alignment} == "deviated_unauthorized"` at the final iteration.
- All six violation arrays are present (may be empty `[]` — empty is the affirmative no-violations claim, omission is forbidden): `{hard_failure_violations}`, `{positive_assertion_violations}`, `{drift_violations}`, `{negative_lift_violations}`, `{positive_lift_violations}`, `{exemplar_violations}`. These feed the manifest's `violations:` section unconditionally.

Any unset required variable is a workflow bug — halt before step 7.
