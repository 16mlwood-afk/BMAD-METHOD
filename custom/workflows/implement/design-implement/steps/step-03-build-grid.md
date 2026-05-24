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

For EVERY component, compare EVERY CSS property side by side. Use this column structure:

| Component | Property | Design | Implementation | Delta |
|-----------|----------|--------|----------------|-------|
| {name} | {property} | {exact value} | {exact resolved value} | {difference or ✓} |

**Delta column rules:**
- If values match exactly → `✓`
- If values differ → state the difference (e.g., `+6px`, `-4px`, `different content`)
- If property exists in design but not implementation → `MISSING in impl`
- If property exists in implementation but not design → `EXTRA in impl`

**Properties to compare for EVERY component** (minimum — add more if the component uses them):

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
12. **Background** — color tokens, opacity.
13. **Color** — text color tokens.
14. **Grid template** — `grid-template-columns` definitions, `grid-cols-*` classes.
15. **Text transform** — `uppercase`, `capitalize`, etc.
16. **SVG dimensions** — `width` and `height` on SVG icons.
17. **Content text** — label text, placeholder text, sub-text that differs.

### 3. Count Deltas

Count the number of rows where the Delta column is NOT `✓`:

```
{delta_count} = number of rows with a non-✓ delta
```

### 4. Classify Deltas by Severity

Group deltas into three tiers:

**Tier 1 — Structural (must fix):**
- Missing components
- Wrong grid column counts or definitions
- Content text differences that change meaning

**Tier 2 — Visual (must fix):**
- Border radius mismatches
- Font size mismatches ≥ 2px
- Padding/margin mismatches ≥ 4px
- Width/height mismatches ≥ 8px on containers
- SVG dimension mismatches
- Color token mismatches

**Tier 3 — Micro (fix if feasible):**
- Font weight differences (500 vs 600)
- Letter spacing differences < 0.02em
- Padding mismatches < 4px
- Opacity differences < 20%

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
Properties checked: {total rows}
Deltas found: {delta_count}
  Tier 1 (structural): {count}
  Tier 2 (visual): {count}
  Tier 3 (micro): {count}
```

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-04-apply-and-deliver.md`

---

## SUCCESS METRICS

- Every component has been compared property-by-property
- Every row has exact values in both columns (no vague descriptions)
- Delta column uses consistent notation
- Deltas classified by severity tier
- Grid artifact written to disk
- `{delta_count}` is accurate

## FAILURE MODES

- Comparing at the component level instead of the property level ("QualityVerdict looks right" — no, compare each property)
- Using vague delta descriptions ("slightly different" — quantify it)
- Forgetting to resolve Tailwind classes through the config before comparing
- Missing properties that exist in the design but weren't cataloged in Step 1
- Claiming `✓` when values are "close enough" — 10px ≠ 4px even if both are "rounded"
