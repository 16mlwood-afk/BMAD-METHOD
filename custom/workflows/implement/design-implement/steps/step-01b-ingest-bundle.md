---
name: 'step-01b-ingest-bundle'
description: 'BUNDLE PATH of step-01 ingest: read a local design-synthesize bundle (manifest.yaml + tokens.css + screen HTML), parse tokens, build the component map, and catalog every CSS property across inline styles, <style> blocks and data-state variants. Entered only when input_kind == synthesize_bundle; converges on step-01 §SHARED.'
---

# Step 1b: Ingest — BUNDLE PATH

**Entered from `step-01-ingest-design.md` §INPUT-KIND BRANCH when `{input_kind} == "synthesize_bundle"`.** Do not run this file on any other input kind. The bundle refusal gates (`dev_no_render`, `needs_human_review`) have already cleared in workflow.md Input Resolution. On completion, return to **`step-01-ingest-design.md` §SHARED**.

**Section ids here are `BUNDLE.*`**, cited from step-01 by that name (see the router's citation legend).

---

## BUNDLE PATH (`{input_kind} == "synthesize_bundle"`)

A design-synthesize bundle is self-contained and structurally different from a Claude Design URL bundle:

- No README — `manifest.yaml` serves that role.
- No `<script src="…">` imports — every `<screen>.html` is self-contained per the bundle self-containment invariant.
- Tokens live in `tokens.css` as CSS custom properties (`--name: value;`), not in JSX.
- Components are tracked via `data-component="…"` attributes in HTML and listed in `{bundle_manifest}.components_emitted`.

### BUNDLE.1. Resolve `{design_dir}` and verify expected files

```
{design_dir} = {bundle_dir}
```

Verify the expected files exist before proceeding. Halt if any required file is missing — these are workflow invariants from design-synthesize step 7 and should always be present in a valid bundle, but verify defensively:

```bash
ls {design_dir}/manifest.yaml      # required — already parsed as {bundle_manifest} in workflow Input Resolution
ls {design_dir}/tokens.css         # required — every var(--*) referenced in HTML resolves here
ls {design_dir}/*.html              # required — at least one screen
```

If any required file is missing, halt with:

```
BUNDLE INGEST FAILURE: required file missing from {bundle_dir}.

Expected: manifest.yaml, tokens.css, and at least one <screen>.html.
Missing:  {list of missing files}

This bundle is malformed — re-run design-synthesize to regenerate it.
```

### BUNDLE.2. Read the manifest (already parsed) and select the target screen

`{bundle_manifest}` was parsed during workflow Input Resolution. From it, extract:

- `{bundle_manifest}.screens` — ordered list of screen names (e.g., `["list", "detail", "drawer"]`).
- `{bundle_manifest}.target_route` / `routes` — the route(s) the bundle represents.
- `{bundle_manifest}.page_mode` — `operational | analytical | detail` — or `n/a` when the brief/bundle carries `surface_class: chrome` (app-shell nav/top-bar/shell). page_mode is a framing hint here (never authoritative); for chrome, do NOT enforce page-mode composition expectations — the frames list + design system carry the whole contract, and `composition` is absent by design (degrade gracefully per brief-revision-policy invariant 1a).
- `{bundle_manifest}.components_emitted` — list of components the bundle declares it emitted.
- `{bundle_manifest}.tokens.used` and `tokens.proposed` — token attribution (not values; values are in `tokens.css`).
- `{bundle_manifest}.policy_sections_cited` — for traceability when comparing implementation choices.
- `{bundle_manifest}.visual_review` — already known to be acceptable (refusal gates cleared); surface `visual_quality` and `exemplar_alignment` to the user for context.
- `{bundle_manifest}.exemplars.selected` — the exemplars the synthesizer anchored to; useful when interpreting structural choices in the HTML.

Resolve `{design_file}`:

- If the user provided a `{design_file}` value explicitly, verify it appears in `{bundle_manifest}.screens` and that `{design_dir}/{design_file}.html` exists. Use it.
- Otherwise, default to the FIRST entry in `{bundle_manifest}.screens` and resolve to `{design_file} = <screen>.html`. For multi-screen bundles, steps 2-4 will iterate over the full `screens` list; the "target file" semantic is preserved for single-screen audits.

### BUNDLE.3. Parse `tokens.css` into `{design_tokens}`

Read `{design_dir}/tokens.css` and extract every `--name: value;` declaration. Use the Read tool, not `cat`.

Parsing rules:

- Scan every CSS block — `:root`, `[data-theme="dark"]`, `.dark`, scoped selectors. Default-scope values (`:root`) become the primary value; other scopes are recorded as `{dark: <value>}` etc. for dark-mode-aware comparison if the implementation supports it.
- Token names use the design-synthesize convention (`--status-warning`, `--row-height-compact`, etc.). Preserve them verbatim — these are the names step 3 will diff against the project's tokens.
- For each token, record: `name`, `value`, `scope` (default | dark | other), `line` (source line in `tokens.css`).

Populate `{design_tokens}` as a flat list grouped by category. Inference rules for category from the token name:

| Name prefix | Category |
|---|---|
| `--status-*`, `--state-*` | Status |
| `--color-*`, `--bg-*`, `--text-*`, `--border-*` | Color |
| `--font-*`, `--text-size-*`, `--leading-*`, `--tracking-*` | Type |
| `--space-*`, `--gap-*`, `--p-*`, `--m-*` | Spacing |
| `--radius-*`, `--rounded-*` | Radius |
| `--shadow-*`, `--elevation-*` | Shadow |
| `--row-height-*`, `--row-*` | Density |
| anything else | Other |

The category aids comparison in step 3 (deltas grouped by category read better than alphabetic).

### BUNDLE.4. Build `{design_components}` from manifest + HTML

For a bundle, "components" come from two sources that should agree:

1. **`{bundle_manifest}.components_emitted`** — the synthesizer's declared list, each with a `name`, optional `screen` or `screens`, and `region_span`.
2. **`data-component="…"` attributes in `<screen>.html`** — every interactive/named region in the HTML carries one of these per the policy's positive-assertion contract.

For each screen file `{design_dir}/<screen>.html`:

- Read the file fully (use the Read tool).
- Scan for `data-component="ComponentName"` attributes. Each match defines one component instance in this screen.
- Cross-reference against `components_emitted`. Any HTML `data-component` not in `components_emitted` is a manifest/HTML mismatch — log it as `{component_drift}` but do NOT halt (the HTML wins per design-synthesize's tie-breaker rule). Any `components_emitted` entry not found in HTML is also drift — log it.
- Cross-reference `components_emitted[*].states_emitted` (manifest field added 2026-05-28) against the states observed in HTML (`<style>`-block selectors, `data-state` variants). Manifest declares states the synthesizer claims to have rendered; HTML is the actual evidence. Discrepancies surface in `{state_drift}` — do NOT halt:
  - **States in manifest but absent from HTML** → synthesizer over-claimed; surface as `state_drift.over_claimed` so the user knows the bundle's state coverage is shallower than the manifest advertises.
  - **States in HTML but absent from manifest** → manifest under-reported; surface as `state_drift.under_reported`. HTML wins per the existing tie-breaker; populate `{design_states}` from HTML.
  - **`components_emitted` entry with `states_emitted: [default]` for a component the heuristics flag as interactive** (row, button, input, action cell, anything with `data-bind`/`data-action`/role="button") → surface as `state_drift.interactive_default_only`. This is the explicit signal that the bundle is the kind that historically leaked state-conditional rules — the user sees it before step-03 builds the (likely incomplete) grid.

Build `{design_components}` as:

```
{
  "WorkSurface": {
    file: "list.html",                  # screen file where the component appears
    region: "main-table-wrapper",       # data-region or selector if present
    instances: 1,
    inline_style_blocks: 3,             # count of style="..." attributes inside the component's DOM region
  },
  "StatusBadge": {
    file: "list.html, detail.html, drawer.html",   # multi-screen component
    region: "status-cell",
    instances: 24,                      # one per row in list; one each in detail/drawer
    inline_style_blocks: 24,
  },
  ...
}
```

The `instances` and `inline_style_blocks` counts feed step 3's exhaustiveness gate — every instance and every style block needs a delta row.

### BUNDLE.5. Catalog every CSS property — three sources (inline `style="…"`, `<style>` blocks, `data-state` variants)

The bundle's invariant is "every visual value is explicit at parse time" — but "explicit" includes state-conditional rules, which only fire on hover/focus/data-state changes. The catalog is built from THREE sources, and skipping any one is silent failure (the previous design caught inline styles only and shipped state-conditional rules as deltas — see fork retro 2026-05-28: PR #827 failed-row tint, hover, null-data).

**Source 1 — Inline `style="…"` attributes.** For each `style="..."` attribute:

- Split into individual `property: value;` declarations.
- Identify the row's `state` by walking up to the nearest ancestor carrying `data-state="…"`. If none, `state: default`.
- For each declaration, record one property row in TWO places (canonical embedded + flat catalog; same data, different shapes).

**Source 2 — `<style>` blocks inside `<screen>.html`.** Scan every `<style>` block in the screen file. Parse each rule. For each rule whose selector targets a state pseudo-class or attribute (`:hover`, `:focus`, `:focus-visible`, `:active`, `[data-state="…"]`, `.failed`-style state classes, descendant combinators that name a state):

- Identify the target component by matching the selector against `data-component` roots in the HTML body.
- Identify the `state` from the selector itself (`:hover` → `hover`; `[data-state="failed"]` → `failed`; `.row-empty` → `empty`).
- For each `property: value;` in the rule body, emit one property row per matching (component, state, property) triple. A rule like `[data-component="ExpenseRow"][data-state="failed"]:hover { background: var(--row-failed-hover-bg); }` produces a row with `state: "failed:hover"` — compound states are explicit, not flattened.

**Source 3 — Sibling `data-state` variants.** A bundle that demonstrates state coverage by rendering multiple instances (e.g., one `<tr data-state="default">`, one `<tr data-state="failed">`, one `<tr data-state="empty">`) supplies state rows via inline `style="…"` on the variant element. Catalog each variant's styles per Source 1, distinguishing them via the `state` field. Populate `{design_states}[component]` with the deduplicated set of states observed across all three sources.

Row shape (used for all three sources):

```
{
  component: "ExpenseRow",             # from the nearest ancestor data-component
  state: "failed",                     # default | hover | focus | selected | failed | empty | disabled | <other> | <compound like "failed:hover">
  screen: "list.html",                 # source screen
  element: "<tr>" or selector path,    # the DOM element or CSS selector the rule applies to
  property: "background-color",        # CSS property name (kebab-case as in CSS, not camelCase)
  raw_value: "var(--row-failed-bg)",   # exact source value
  resolved_value: "#fee2e2",           # resolved through tokens.css (var(--*) → value)
  token_ref: "--row-failed-bg",        # populated when raw_value is a var(--*) reference
  source: "inline" | "style_block" | "data_state_variant",
  source_file: "list.html",
  source_line: 47,
}
```

If a `var(--*)` reference cannot be resolved against `{design_tokens}`, that is an invariant-1 violation that design-synthesize step 7 should already have caught. Log as `{unresolved_var_refs}` and surface in the ingestion summary — do not halt, but flag prominently (this bundle should not have been emitted).

**Be exhaustive along all three axes — component, state, property.** Every property on every (element, state) pair. This table is the reference for the comparison grid in Step 3. Every (component, state, property) triple missed here is a delta that leaks through. State-conditional rules are the dominant leak mode — prioritize Source 2 (`<style>` blocks) audit before declaring this step complete.

Pay special attention to:
- `border-radius` — the #1 source of design drift
- `font-size` — design tokens vs Tailwind scale
- `padding` / `margin` — especially asymmetric values
- `width` / `min-width` on grid columns and fixed-size containers
- `letter-spacing` / `font-weight` / `text-transform` — typography details
- `gap` — flex/grid gap values
- `border` / `border-left` — width, color, opacity

Note: bundles MUST NOT contain config-dependent Tailwind classes (per design-synthesize workflow invariant 2), so the catalog is built from `style="…"` and `var(--*)` only. If you encounter Tailwind utility classes whose values are config-dependent (e.g., `text-primary`, `rounded-lg`), log them as `{config_class_violations}` and surface in the summary — design-synthesize step 7 should have caught this.

### BUNDLE.6. Skip to §SHARED

Continue at §SHARED — Property catalog and ingestion summary.

---

