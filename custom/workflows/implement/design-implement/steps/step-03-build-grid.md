---
name: 'step-03-build-grid'
description: 'Build the exhaustive component × property comparison grid and output the delta table as a structured artifact'
---

# Step 3: Build Comparison Grid

**Progress: Step 3 of 4** — Next: Apply and Deliver (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Every row in the grid must have a concrete value in both the Design and Implementation columns — no "similar" or "approximately" or "matches". Exact values only.
- If a property cannot be determined, mark it as `?` with a note — never leave it blank.
- Output the grid using the template at `{project-root}/_bmad/bmm/workflows/implement/design-implement/template.md`.
- **The grid spans three axes — component × state × property — not two.** Step-01 cataloged states explicitly into `{design_states}`. Every (component, state, property) triple in `{design_components}[*].properties` must produce a grid row. A grid that omits a state declared in `{design_states}` is a step-03 failure, equivalent in severity to "components missing from the design".
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## CONTEXT

From Steps 1–2 you have:
- `{design_components}` with every CSS property and value from the design
- `{impl_components}` with every CSS property and resolved value from the implementation
- `{design_tokens}` — the design system's token values
- `{impl_config}` — the Tailwind class resolution table

## SEQUENCE OF INSTRUCTIONS

### 1. Align Components

Match each design component to its implementation counterpart. Build a mapping:

| Design Component | Implementation File | Match Type |
|-----------------|---------------------|------------|
| QualityVerdict | QualityVerdict.svelte | exact |
| SupplierHeatGrid | SupplierHeatGrid.svelte | exact |
| InvoiceListSection | InvoiceListSection.svelte | exact |
| ... | ... | ... |

Flag any `MISSING` or `EXTRA` from Step 2.

### 2. Build the Comparison Grid

For EVERY component, FOR EVERY STATE in `{design_states}[component]`, compare EVERY CSS property side by side. Use this column structure:

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| {name} | {default \| hover \| focus \| selected \| failed \| empty \| disabled \| <other> \| <compound>} | {property} | {exact value} | {exact resolved value} | {difference or ✓} |

A component cataloged with states `[default, hover, failed]` produces three sub-tables (or three state-groups within one table) — one per state — each with the full per-property sweep. Skipping a state because "the implementation's default works" is exactly the failure mode this axis was added to catch.

**Delta column rules:**
- If values match exactly → `✓`
- If values differ → state the difference (e.g., `+6px`, `-4px`, `different content`)
- If property exists in design but not implementation → `MISSING in impl`
- If property exists in implementation but not design → `EXTRA in impl`
- If a STATE exists in `{design_states}` but the implementation never enters that state (no `:hover` rule, no `data-state="…"` branch, no conditional class) → `STATE MISSING in impl` for every property in that state's design rows. This is Tier-1 structural (see §4).

**Properties to compare for EVERY (component, state) pair** (minimum — add more if the component uses them):

1. **Border radius** — the #1 drift source. Compare `borderRadius` from design against resolved Tailwind class.
2. **Font size** — design `fontSize` vs implementation `text-*` class (resolved).
3. **Font weight** — `fontWeight` vs `font-*` class.
4. **Font family** — mono vs sans. Check if the design uses `sharedStyles.mono` and the implementation matches.
5. **Letter spacing** — `letterSpacing` vs `tracking-*` class (resolved).
6. **Padding** — all four sides. Note asymmetric values.
7. **Margin** — significant margins (section spacing, not micro-adjustments).
8. **Gap** — flex/grid gap values.
9. **Width / min-width / max-width** — especially on grid columns and fixed containers.
10. **Height / min-height** — row heights, icon containers.
11. **Border** — width, style, color, opacity.
12. **Background** — color tokens, opacity (state-conditional tint intensities live here — e.g., `bg-destructive/[0.06]` vs `bg-destructive/[0.10]`).
13. **Color** — text color tokens (state-conditional muted-vs-default text colors live here — e.g., null-data styling).
14. **Grid template** — `grid-template-columns` definitions, `grid-cols-*` classes.
15. **Text transform** — `uppercase`, `capitalize`, etc.
16. **SVG dimensions** — `width` and `height` on SVG icons.
17. **Content text** — label text, placeholder text, sub-text that differs.

**Per-state properties (compare each state explicitly — do NOT inherit from default):**

For every non-default state in `{design_states}[component]`, sweep AT MINIMUM:

- **Background-color + opacity** — state tints (failed rows, selected rows, hover wash).
- **Text color + font-weight** — null-data, disabled, secondary-text-on-state.
- **Border / border-left** — accent strips, focus rings, selected indicators.
- **Hover-on-state cascade** — if both `:hover` and `[data-state="…"]` exist, verify the compound `[data-state]:hover` does NOT fall through to the generic `:hover` rule and lose the state tint. This is the exact regression mode that shipped in PR #827.
- **Box-shadow** — focus rings, selected glow.

If the implementation collapses two states into one (e.g., `hover` and `selected` share the same `bg-muted` class), record one row per state with `Implementation = "bg-muted (shared with <other state>)"` and a delta describing the collision.

### 3. Count Deltas

Count the number of rows where the Delta column is NOT `✓`:

```
{delta_count} = number of rows with a non-✓ delta
```

### 4. Classify Deltas by Severity

Group deltas into three tiers:

**Tier 1 — Structural (must fix):**
- Missing components
- **Missing states** (`STATE MISSING in impl` rows) — the implementation has no path into the design-required state (no `:hover` rule, no `data-state` branch, no conditional class)
- **State collisions** — two distinct design states resolve to the same implementation treatment (e.g., `hover` and `selected` both rendering `bg-muted`)
- **Hover-on-state fall-through** — `[data-state="failed"]:hover` cascading to the generic `:hover` rule and losing the state tint (the PR #827 failed-row-hover regression)
- Wrong grid column counts or definitions
- Content text differences that change meaning

**Tier 2 — Visual (must fix):**
- Border radius mismatches
- Font size mismatches ≥ 2px
- Padding/margin mismatches ≥ 4px
- Width/height mismatches ≥ 8px on containers
- SVG dimension mismatches
- Color token mismatches
- **State-conditional color/opacity mismatches** — e.g., design specifies `bg-destructive/[0.10]` for failed rows; impl renders `bg-destructive/[0.06]`. Opacity-step differences ≥ 0.02 on state tints count as Tier 2 even if absolute opacity is small.
- **State-conditional font-weight mismatches on null/empty data** — design specifies muted normal weight for `(unknown)` / `—` placeholders; impl inherits default font-weight. Counts as Tier 2 because the visual semantic (data presence vs absence) is broken.

**Tier 3 — Micro (fix if feasible):**
- Font weight differences (500 vs 600) **on populated data only — state-conditional weight diffs are Tier 2 above**
- Letter spacing differences < 0.02em
- Padding mismatches < 4px
- Opacity differences < 20% **on default-state rendering only — state-tint opacity diffs are Tier 2 above**

### 5. Output the Grid as a Handoff Artifact

Write the completed grid to disk using the template:

```bash
{implementation_artifacts}/design-implement-grid-{page-slug}-{date}.md
```

This artifact serves two purposes:
1. The user can review exactly what will change before Step 4 applies fixes
2. Future sessions can reference it to prevent regression

### 6. Report Grid Summary

Output:

```
Comparison grid complete.
Components compared: {count}
States compared:     {total (component, state) pairs}
Properties checked:  {total rows}
Deltas found:        {delta_count}
  Tier 1 (structural): {count}
    of which state-axis: {count of missing-state + state-collision + hover-fall-through}
  Tier 2 (visual):     {count}
    of which state-conditional: {count of state-tint + state-text-weight deltas}
  Tier 3 (micro):      {count}
```

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-04-apply-and-deliver.md`

---

## SUCCESS METRICS

- Every component has been compared property-by-property, **state-by-state**
- Every state in `{design_states}[component]` appears as a sub-table or state-group in the grid — no states silently dropped
- Every row has exact values in both columns (no vague descriptions)
- Delta column uses consistent notation
- Deltas classified by severity tier
- Grid artifact written to disk
- `{delta_count}` is accurate
- State-axis Tier-1 deltas (missing state, state collision, hover-on-state fall-through) are surfaced explicitly in the summary, not buried in the per-property rows

## FAILURE MODES

- Comparing at the component level instead of the property level ("QualityVerdict looks right" — no, compare each property)
- **Comparing only the default state and assuming hover/focus/failed/empty inherit correctly.** This is the dominant historic leak (PR #827). Every state cataloged in step-01 gets its own grid rows. "The default matches" is not evidence the failed-state matches.
- **Treating `:hover` and `[data-state]` as independent rather than compound.** A row that's both `failed` AND being hovered needs an explicit `[data-state="failed"]:hover` row in the grid — not an inference that "failed background" + "generic hover background" will combine correctly. They won't: generic hover usually wins the cascade and the state tint vanishes.
- Using vague delta descriptions ("slightly different" — quantify it)
- Forgetting to resolve Tailwind classes through the config before comparing
- Missing properties that exist in the design but weren't cataloged in Step 1
- Claiming `✓` when values are "close enough" — 10px ≠ 4px even if both are "rounded"
