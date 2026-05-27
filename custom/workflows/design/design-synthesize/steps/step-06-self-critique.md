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

Evaluate each screen along five axes. For each axis, classify the screen as `strong | adequate | weak`:

| Axis | What "strong" looks like | What "weak" looks like |
|---|---|---|
| **Visual hierarchy** | Titles, sections, table framing are immediately legible; the eye knows where to start; the screen has a clear "story" before the table | Flat type ramp, no section breaks, table dropped onto the page with no surrounding context |
| **Whitespace & density** | Comfortable for the page mode — dense where the brief says dense, calm where the brief says calm; consistent rhythm between sections | Either gasping for air (too much padding everywhere) or suffocating (uniform tightness without breathing room around headers/separators) |
| **Typography use** | Type scale used purposefully — body, secondary, labels, numbers all distinguishable; weight variation deliberate; tabular numbers in numeric columns | Uniformly small text everywhere, all-bold or all-thin, no weight contrast, non-tabular numbers misaligning columns |
| **Table ergonomics** | Rows scan easily; row states (hover, selected, alert) are clear; column widths fit the data; numeric columns right-aligned; status column is the visual anchor for state | Wall of identical-looking rows, no row-state treatment, columns sized arbitrarily, numbers left-aligned in numeric columns |
| **AI/generic template look** | Reads as a high-trust UK VAT finance operations tool — calm fintech with real operational story; specific to this product | Flat, spreadsheet-y, no operational narrative; would look at home in any generic admin panel; placeholder-feeling even with real data |

Compose `{visual_quality}` from the per-axis ratings using the following rule:

```
strong_count   = count of axes rated "strong" across all screens (averaged)
adequate_count = count of axes rated "adequate"
weak_count     = count of axes rated "weak"

if weak_count >= 2:            {visual_quality} = "weak"
elif weak_count == 1:          {visual_quality} = "acceptable"   # one weak axis, refine targeted at it
elif strong_count >= 3:        {visual_quality} = "excellent"
else:                          {visual_quality} = "acceptable"
```

Record per-axis ratings in `{visual_quality_axes}` for the manifest's audit trail. Multi-screen bundles aggregate by averaging axes across screens; one weak screen in a multi-screen flow forces at least `acceptable` overall.

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

**Negative half** (already partially covered by §3 lift-test detectors — placeholder data, generic SaaS chrome, CRM-shaped composition, wrong currency/locale, page-mode mismatch). Re-use those detectors here; any hit is a `{negative_lift_violations}` entry.

**Positive half** — verify all four requirements:

| # | Requirement | Detector |
|---|---|---|
| 1 | Answers the screen's core operational question at a glance | For `operational` page mode: is there a top band (`operational-analytics-band`) or summary header that states current state (counts, totals, anomalies) BEFORE the user has to read the table? For `analytical`: chart-led summary above drill-down? For `detail`: the entity's status/summary above its sections? Missing = failure. |
| 2 | Surfaces the screen's key states above or beside the worklist | Are pending/failed/anomalies/overdue/awaiting-response visible at the top band or filter strip, not only inside individual rows? Look for explicit state counters or state-grouped filters. Missing = failure. |
| 3 | Visually distinguishes primary actions and alerts from background noise | Does the primary action have a distinct treatment from secondary actions (size, weight, position, or color escalation per policy §3)? Are alert/error states visually escalated above routine row treatment? Failure if primary action is indistinguishable from secondary, or alert rows blend into routine rows. |
| 4 | Aligned with loaded exemplars | Deferred to sub-check (f) below. |

Collect `{positive_lift_violations}` for each failed requirement:

```
[
  { requirement: "1 - core operational question answered at a glance",
    screen: "bundle/list.html",
    detail: "table starts at top of page with no summary band; user must scan rows to learn current state" },
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
```

### 8. Sub-check (f) — Exemplar alignment

Skip if `{exemplars}` is empty (brief had `exemplar_anchoring: waived`); record `{exemplar_alignment} = "aligned"` (vacuously) and move on.

For each screen, compare against the most relevant 1–2 exemplars in `{exemplars}` along these dimensions:

| Dimension | What to compare |
|---|---|
| Page-level hierarchy | Does the screen open with the same KIND of element as the exemplars (summary band, header, chart, etc.)? Does section ordering follow the same pattern? |
| Density | Does the screen feel as tight/loose as the exemplars? Row heights, gutter widths, header weight should be in the same family. |
| Top-band patterns | If exemplars use a top band, does the screen? If exemplars don't, the screen shouldn't either (unless the brief explicitly authorizes). |
| Table framing | Are tables introduced the same way — section heading + summary line, or summary band + filter strip, or direct (no framing)? |
| State presentation | Are status/state treatments consistent (badge style, alert escalation, empty/loading/error states)? |

Classify alignment per screen as `aligned | deviated_with_brief_authorization | deviated_unauthorized`:

- **aligned** — all dimensions match the exemplars.
- **deviated_with_brief_authorization** — at least one dimension departs from exemplars AND the brief explicitly calls for the departure (e.g., brief §"visual direction" says "depart from the dense table pattern — use a card-grid because the page mode is `analytical`"). The departure quotes the brief language in `{exemplar_alignment_rationale}`.
- **deviated_unauthorized** — at least one dimension departs AND the brief does not authorize it.

Aggregate across screens: any `deviated_unauthorized` makes the bundle's `{exemplar_alignment} = "deviated_unauthorized"`. All `aligned` makes it `"aligned"`. Mix of `aligned` and `deviated_with_brief_authorization` (but no unauthorized) makes it `"deviated_with_brief_authorization"`.

Decision:

```
if {exemplar_alignment} == "deviated_unauthorized":
    {exemplar_violations} = [
      { screen: <path>, dimension: <name>, exemplar: <path>,
        detail: "<which exemplar dimension was departed from, what the bundle did instead>" },
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
- `{visual_quality_axes}` populated with per-axis ratings for the manifest audit trail.
- `{visual_lift_passed}` is a boolean.
- `{exemplar_alignment}` ∈ `{aligned, deviated_with_brief_authorization, deviated_unauthorized}`.
- `{needs_human_review}` is a boolean. True whenever `{visual_quality} == "weak"`, `{visual_lift_passed} == false`, or `{exemplar_alignment} == "deviated_unauthorized"` at the final iteration.
- `{hard_failure_violations}`, `{positive_assertion_violations}`, `{drift_violations}`, `{negative_lift_violations}`, `{positive_lift_violations}`, `{exemplar_violations}` are populated (may be empty lists). These feed the manifest's failure-mode disclosure.

Any unset required variable is a workflow bug — halt before step 7.
