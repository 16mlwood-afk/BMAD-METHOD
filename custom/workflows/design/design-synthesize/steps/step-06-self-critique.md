---
name: 'step-06-self-critique'
description: 'Run three sub-checks (hard failures, positive allowlist, drift). Loop back to step 4 with correction notes on failure. Max 3 iterations.'
---

# Step 6: Self-Critique

**Goal:** Verify the synthesized bundle complies with the policy's hard failures (a), the policy's contract-critical positive-assertion allowlist (b), and — in refine-screen mode only — the drift contract against the prior implementation (c). On failure, return to step 4 with a precise correction note. Max 3 iterations across all sub-checks; on the 3rd failure, record the failure mode and proceed to step 7.

**Loop control:** This step is the ONLY step that loops. The loop target is step 4. The loop terminates at iteration 3 regardless of result.

---

## RULES

- **Policy-derived only.** Sub-checks (a) and (b) verify the bundle against `{hard_failures}` and `{positive_allowlist}` loaded in step 2 — NOT against workflow invariants. Workflow invariants (e.g., "every `var(--*)` resolves in tokens.css", "no config-dependent Tailwind classes", "manifest never disagrees with HTML on a visual fact", "bundle is self-contained") are checked unconditionally in step 7's manifest-validation pass. Conflating these two categories was an earlier draft error — keep them separate.
- **`design-synthesize` does NOT invent allowlist items.** Sub-check (b) iterates `{positive_allowlist}` only. New positive assertions enter the system via `modify-design-policy`, not this workflow.
- **Drift in refine-screen is failure, not noise.** Any non-empty diff in an `unchanged_region` against the prior implementation is a synthesis bug. Either eliminate the drift in step 4, or move the region into `targeted_changes` in the brief (which requires the user's involvement — this workflow does not edit briefs).
- **One correction per loop.** When multiple sub-checks fail in the same iteration, emit ONE consolidated correction note covering all failures, return to step 4 once, and re-check everything on the next iteration. Do not loop step 4 once per failure.
- **At iteration 3, do not loop.** Set `{compliance_state}` to the failure mode, emit the bundle anyway in step 7, surface the failure to the user. The bundle is shipped with `compliance_state: hard_failed | positive_failed | drift_failed` so the user sees the gap before invoking `design-implement`.
- **Skill-routing check is binary.** If `{skills_invoked}` is empty, that's a routing failure regardless of iteration count — return to step 4 with: `step 6: skills_invoked is empty. Route per workflow.md §SKILL ROUTING before re-emitting.`
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
    correction = "step 6 routing: {skills_invoked} is empty. Per workflow.md §SKILL ROUTING, design-policy-canonical and the project frontend skill MUST be invoked in step 4 before emitting. Re-enter step 4 with the skill routing applied."
    GOTO step 4 with {correction_note} = correction
```

This check is unconditional and not subject to the iteration cap — it represents a workflow bug, not a synthesis quality issue.

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

### 6. Aggregate failures and decide

```python
total_violations = (
    len(hard_failure_violations) +
    len(positive_assertion_violations) +
    len(drift_violations)
)

if total_violations == 0:
    {compliance_state} = "pass"
    GOTO step 7
elif iteration_count < 3:
    correction_note = compose_correction(
        hard_failure_violations,
        positive_assertion_violations,
        drift_violations
    )
    GOTO step 4 with {correction_note}
else:  # iteration_count == 3
    if hard_failure_violations: {compliance_state} = "hard_failed"
    elif positive_assertion_violations: {compliance_state} = "positive_failed"
    elif drift_violations: {compliance_state} = "drift_failed"
    print warning to user (see §7)
    GOTO step 7  # emit anyway, with failure mode flagged
```

### 7. Compose the correction note (when looping)

When returning to step 4, the correction note must be:

- **Specific:** file + line + snippet for every violation.
- **Bounded:** instruct step 4 to fix only the listed regions; do not redesign unrelated regions.
- **Cite the policy:** every hard-failure or positive-assertion violation cites the policy line that ratifies the rule, so step 4's correction matches the policy's intent.

Template:

```
Step 6 correction (iteration {iteration_count}/3):

Hard failures ({N}):
  - bundle/main.html:47 violates "No colored pill badges" (policy:89)
    snippet: <span style="border-radius: 9999px; background: #f59e0b;">Warning</span>
    fix: replace with <span data-component="StatusBadge" style="...; background: var(--status-warning); ...">
  - ...

Positive assertions ({M}):
  - bundle/main.html:102 fails "Status indicators use status tokens" (policy:134)
    snippet: ...
    fix: replace raw color with var(--status-warning).
  - ...

Drift ({K}):
  - bundle/list.html:412-440 region "footer" diverged from prior (src/routes/.../+page.svelte:412-440) but is in unchanged_regions
    diff:
      - <prior line>
      + <bundle line>
    fix: restore the prior implementation's footer region byte-for-byte (token substitution allowed).
  - ...

Do not modify regions not listed above. Re-emit only the affected files.
```

### 8. Print the critique summary

On `pass`:

```
✓ Self-critique passed (iteration {iteration_count}/3):
  hard failures:        0/{len(hard_failures)} rules violated
  positive assertions:  0/{len(positive_allowlist)} assertions failed
  drift:                0 regions (refine-screen) or n/a (fresh-design)
  compliance_state:     pass

Proceeding to step 7: emit manifest.
```

On loop (iteration < 3):

```
✗ Self-critique failures (iteration {iteration_count}/3):
  hard failures:        {len(hard_failure_violations)}/{len(hard_failures)}
  positive assertions:  {len(positive_assertion_violations)}/{len(positive_allowlist)}
  drift:                {len(drift_violations)}

Returning to step 4 with correction note.
```

On final-iteration failure (iteration == 3):

```
⚠ Self-critique failed at iteration 3 — emitting bundle anyway with compliance_state={compliance_state}:
  hard failures:        {len(hard_failure_violations)}
  positive assertions:  {len(positive_assertion_violations)}
  drift:                {len(drift_violations)}

The bundle is being emitted so you can inspect it. design-implement WILL still consume bundles in this state, but the manifest's compliance_state field documents the failure mode. Address the violations before running design-implement OR before treating this bundle as production-ready.

Proceeding to step 7: emit manifest.
```

Then load `step-07-emit-manifest.md`.

---

## STATE CHECKPOINT

After this step (when proceeding to step 7):

- `{iteration_count}` is 1, 2, or 3.
- `{compliance_state}` ∈ `{pass, hard_failed, positive_failed, drift_failed}`.
- `{hard_failure_violations}`, `{positive_assertion_violations}`, `{drift_violations}` are populated (may be empty lists). These feed the manifest's failure-mode disclosure.

Any unset required variable is a workflow bug — halt before step 7.
