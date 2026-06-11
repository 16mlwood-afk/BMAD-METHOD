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
- **A fourth axis — implementation multiplicity — applies wherever `{impl_render_sites}` lists more than one implementation of a primitive.** Each implementation gets its own grid rows AND the implementations are cross-checked against each other (§2a). Two implementations of one primitive that resolve to different values is a Tier-1 delta even if one of them matches the design — a row and its drawer must not disagree on the same pill.
- **Colours are compared as resolved values, numerically — never by class name or family.** Use `{impl_colors}`. "Both green," "both emerald-ish," "close enough" are banned verdicts (see §2 colour rule).
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## CONTEXT

From Steps 1–2 you have:
- `{design_components}` with every CSS property and value from the design
- `{impl_components}` with every CSS property and resolved value from the implementation
- `{impl_render_sites}` — every implementation of every primitive, keyed by primitive (the multiplicity input for §2a)
- `{impl_colors}` — every colour (incl. default Tailwind palette) resolved to a concrete hex/oklch value
- `{design_tokens}` — the design system's token values
- `{impl_config}` — the Tailwind class resolution table

## SEQUENCE OF INSTRUCTIONS

### 1. Align Components

Match each design primitive to its implementation counterpart**s** — plural. Using `{impl_render_sites}`, a primitive may map to more than one implementation. Build a mapping:

| Design Primitive | Implementation File(s) | Match Type |
|-----------------|------------------------|------------|
| QualityVerdict | QualityVerdict.svelte | exact |
| status-pill | InvoiceStatusPill.svelte **+** InvoiceDrawer.svelte (inline `.pill`) **+** invoices/[id] header pill | exact (×3) |
| SupplierHeatGrid | SupplierHeatGrid.svelte | exact |
| ... | ... | ... |

Flag any `MISSING` or `EXTRA` from Step 2. **Flag any primitive with ≥2 implementations** — those carry a mandatory §2a consistency pass.

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

### 2a. Implementation-consistency pass (shared primitives)

For every primitive that `{impl_render_sites}` lists with **two or more implementations**, do NOT just compare each to the design independently. Compare the implementations **to each other**, property by property:

| Primitive | Property | Impl A (file) | Impl B (file) | Impl C (file) | Consistent? |
|-----------|----------|---------------|---------------|---------------|-------------|
| status-pill | green bg | `#ecfdf5` (InvoiceStatusPill) | `#eef5f1` (drawer `.pill`) | `#e3efe9` (id header) | ✗ three greens |
| status-pill | approved label | "Awaiting sync" | "Approved" | "Approved" | ✗ label split |
| status-pill | radius | 6px | 5px | 6px | ✗ |

**Any property where the implementations disagree is a Tier-1 delta (§4), even if one of them matches the design.** A shared primitive that renders differently across surfaces is broken by definition — the row and its detail drawer disagreeing on the same status is the exact failure this axis exists to catch. The fix is consolidation to one implementation, not patching each copy toward the design separately (which leaves the next copy to drift again).

### 2b. Colour comparison is numeric — never nominal

Every colour delta in the grid compares **resolved values from `{impl_colors}`**, not class names. For each colour pair:

1. Resolve both sides to the same space (hex or oklch). A design `hsl(150 26% 95.5%)` and an impl `bg-emerald-50` become `#eef5f1` vs `#ecfdf5`.
2. Compute a perceptual distance (ΔE, or a simple per-channel delta if ΔE is impractical). Treat **ΔE ≳ 3 (or any channel off by ≳ 5%)** as a real delta → Tier-2.
3. **Banned verdicts:** "both green", "same family", "emerald ≈ sage", "close enough". Same hue family is not a match; only resolved-value proximity is. The invoices status-pill shipped emerald-where-the-design-said-sage precisely because the comparison stopped at "both pale green."

### 2c. Content-lane flag — formatter-driven identifier cells (do NOT pixel-match against the mock bundle)

This grid certifies **treatment** (CSS) — it is blind to the **content lane** (what a value-formatter renders), and that blindness is structural, not an oversight: design-implement compares against the design *bundle*, which carries **seeded mock data**. A canonical-identifier cell whose text comes from a formatter or enum→label map is wrong only on a *real-data variant the bundle never contained* — so the bundle string-match (`UK → UK` mock vs `UK → UK` impl) returns `✓` while the live render (`US → amazon_us`, a leaked raw enum) is broken. Treating that `✓` as conformance is the exact miss this section exists to prevent (inbound-flow `/orders`: the live `marketplaceCode` fell through to the raw `amazon_us` enum; the bundle's mock `UK → UK` made the cell "pass").

For every cell in `{impl_identifier_cells}` (step-02 §3d — `value_source: formatter | enum-map` AND a canonical-identifier class):

1. **Do NOT assign the cell's *value* a treatment `✓` or a value-delta.** Its CSS still gets normal grid rows (radius, font, colour — those ARE bundle-verifiable); only the rendered *string* is exempt from the bundle comparison.
2. **Add one content-lane row** to the grid instead, with this fixed shape — it is NOT a Tier-1/2/3 delta (those are fixable here; this is not):

   | Component | State | Property | Design | Implementation | Delta |
   |-----------|-------|----------|--------|----------------|-------|
   | {cell} | — | `content-lane: identifier value ({class})` | mock `{bundle value}` — NOT authoritative | `{formatter_ref}` (real-data variants not in bundle) | `CONTENT-LANE-UNVERIFIED → route to design-review / design-tuning (live)` |

3. **Never "verify" it by reading the bundle harder.** A mock bundle physically cannot contain the production enum forms; the only authoritative evidence is the LIVE page with real data. That evidence is `design-review`'s §13(a) check and `design-tuning` step-02 §2b — not this workflow. Reading the bundle and declaring the identifier "matches" is the failure, not the verification.

Count these as `{content_unverified_count}` (separate from `{delta_count}` — they are routed items, not deltas applied here). They carry into the step-04 apply ledger as `deferred(content-lane)` and into the §9 completion report's mandatory disclosure, so the run announces "these identifier cells were NOT content-verified — run design-review / design-tuning against the live page" rather than implying the grid covered them.

### 2d. Page-shell row — ALWAYS emit one, even when no component maps to it

The grid MUST contain exactly one **Page shell** row, regardless of how many components matched. It is the only row whose Design column comes from `{design_layout_constraints}` (step-01) instead of a cataloged component, and whose Implementation column comes from `{impl_page_shell}` (step-02 §1a) instead of a component file — because the page container's width is owned by the wrapper + ancestor layout, not by any component, and the bundle renders full-bleed so there is no component-level value to diff. Omitting it is the structural blind spot that shipped the inbound-flow `/orders` narrow-and-centered page (PR #2017) with an all-green component grid.

Emit it with this fixed shape:

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| Page shell | default | container width | `{design_layout_constraints.resolved.width}` (e.g. `full-bleed` — README "full-width within the content container") | `{impl_page_shell.effective_width}` (e.g. `1280px`, the tightest cap in the chain `layout max-w-[1440px] → page max-width:1280px`) | e.g. `capped 1280 vs full-bleed → Tier-1` or `✓` |
| Page shell | default | centering | `centered: {design…centered}` | `centered: {impl…centered}` | difference or `✓` |
| Page shell | default | horizontal padding | `{design…padding}` | `{impl…padding}` | difference or `✓` |

Rules:
- **A width or centering mismatch is Tier-1 structural** (§4) — it reframes the entire composition, not one component. A `max-width` cap the design doesn't call for (or a missing one the design does) is the headline, not a nit.
- **Silence is not a pass.** If the README was silent but the bundle wrapper is full-bleed (`{design_layout_constraints}` resolved `full-bleed`), an impl `max-width` cap is STILL a delta — the row is emitted and scored, never skipped for "the design didn't say."
- **Surface a house-convention divergence, don't auto-spread it.** If step-02 §1a noted that sibling pages share the impl's cap, say so in the Delta cell (`divergence: design wants full-width, but catalog/supply-sources/… also cap at 1280 — confirm scope`). The apply (step-04) fixes THIS page to the design; widening every sibling is a separate, deliberate decision, not a silent sweep.

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
- **Sibling-implementation divergence** (§2a) — two or more implementations of one primitive resolving to different values (colour, label, radius, size). Tier-1 **even if one of them matches the design**; the fix is consolidation to a single shared implementation, not patching each copy independently. This is the axis the invoices status-pill drift (3 forked pills) exposed.
- Wrong grid column counts or definitions
- **Page-shell width / centering mismatch** (§2d) — the impl caps or centers the page where the design wants full-width within the content container (or vice versa). The whole composition is reframed; this is a headline Tier-1, not a per-component nit. Padding-only differences on an otherwise-matching shell are Tier-2.
- Content text differences that change meaning

**Tier 2 — Visual (must fix):**
- Border radius mismatches
- Font size mismatches ≥ 2px
- Padding/margin mismatches ≥ 4px
- Width/height mismatches ≥ 8px on containers
- SVG dimension mismatches
- Color token mismatches — compared as **resolved values** (§2b), ΔE ≳ 3 or any channel off ≳ 5%. A Tailwind-palette colour and a raw-HSL design colour that resolve apart count here (e.g. `emerald-50` `#ecfdf5` vs design sage `#eef5f1`). "Same colour family" is not a defence.
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
Components compared:  {count}
Primitives w/ ≥2 impls: {count}   ← each ran the §2a consistency pass
States compared:      {total (component, state) pairs}
Properties checked:   {total rows}
Deltas found:         {delta_count}
  Tier 1 (structural): {count}
    of which state-axis:    {count of missing-state + state-collision + hover-fall-through}
    of which sibling-divergence: {count of §2a cross-implementation deltas}
  Tier 2 (visual):     {count}
    of which state-conditional: {count of state-tint + state-text-weight deltas}
    of which colour (resolved ΔE): {count}
  Tier 3 (micro):      {count}
Content-lane unverified (routed, NOT deltas): {content_unverified_count}
  → formatter/enum-driven identifier cells; route to design-review / design-tuning (live page)
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
- **Every primitive with ≥2 implementations ran the §2a consistency pass; sibling-divergence Tier-1 deltas surfaced explicitly in the summary**
- **Every colour delta compared resolved values numerically (§2b), never by class name or family**
- **Every formatter/enum-driven canonical-identifier cell (`{impl_identifier_cells}`) carries a `content-lane: CONTENT-LANE-UNVERIFIED` row (§2c) — its value was NOT pixel-matched against the mock bundle, and `{content_unverified_count}` is surfaced separately in the summary**
- **Exactly one Page-shell row exists (§2d), comparing `{design_layout_constraints}` against `{impl_page_shell}`'s effective container width — a width/centering mismatch is surfaced as Tier-1 in the summary, never omitted because "no component owns it"**

## FAILURE MODES

- Comparing at the component level instead of the property level ("QualityVerdict looks right" — no, compare each property)
- **Comparing a shared primitive against the design but not against its own other implementations.** A primitive built once as a shared component and again inline elsewhere can have one copy match the design while the copies disagree with each other — the §2a pass exists because that is the exact shape that shipped the invoices status-pill drift (table emerald vs drawer sage vs detail-header sage). One matching copy is not a pass.
- **Nominal colour comparison** — calling `emerald-50` vs `hsl(150 26% 95.5%)` a match because "both are green." Resolve both and compute distance (§2b); same hue family is not a match.
- **Comparing only the default state and assuming hover/focus/failed/empty inherit correctly.** This is the dominant historic leak (PR #827). Every state cataloged in step-01 gets its own grid rows. "The default matches" is not evidence the failed-state matches.
- **Treating `:hover` and `[data-state]` as independent rather than compound.** A row that's both `failed` AND being hovered needs an explicit `[data-state="failed"]:hover` row in the grid — not an inference that "failed background" + "generic hover background" will combine correctly. They won't: generic hover usually wins the cascade and the state tint vanishes.
- Using vague delta descriptions ("slightly different" — quantify it)
- Forgetting to resolve Tailwind classes through the config before comparing
- Missing properties that exist in the design but weren't cataloged in Step 1
- Claiming `✓` when values are "close enough" — 10px ≠ 4px even if both are "rounded"
- **Pixel-matching a formatter-driven identifier cell against the mock bundle and calling it `✓`.** The bundle's mock `UK → UK` matching the impl's `UK → UK` is NOT evidence the formatter handles the real `amazon_us` / `amazon.de` / stray-`GB` variants — those never appear in a mock bundle. Such a cell is `content-lane: CONTENT-LANE-UNVERIFIED` (§2c) and routed to the live-page workflows, never certified here. This is the inbound-flow `/orders` raw-enum leak the content lane exists to catch.
- **An all-green component grid with no Page-shell row (§2d).** Every component's CSS can match byte-for-byte while the page renders narrow + centered because a wrapper `max-width` cap nested inside the layout reframed the whole composition — and no per-component row can see it (the cap belongs to the wrapper + ancestor layout, and the bundle is full-bleed so there's nothing to diff at component level). The page-shell row is mandatory precisely because the component sweep is structurally blind to it. This is the inbound-flow `/orders` narrow-page miss (PR #2017).
