---
name: 'step-01-ingest-design'
description: 'Ingest the design source — either fetch and extract a Claude Design URL bundle, or read a local design-synthesize bundle directory — then catalog every component with its CSS values. Both paths normalize to the same downstream state.'
---

# Step 1: Ingest Design

**Progress: Step 1 of 4** — Next: Map Implementation (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- **Branch on `{input_kind}` at the top.** Two ingestion paths converge on the same downstream state. Never mix them: a `synthesize_bundle` path never calls curl; a `claude_design_url` path never reads `manifest.yaml`.
- If download fails (URL path only), retry once. If it fails again, report the error and stop.
- Read every file in the bundle that the target design file references — do not skip any.
- **Catalog the state axis explicitly.** Inline `style="…"` attributes only describe a single rendering. State-conditional rules live in (a) `<style>` blocks inside `<screen>.html` with `:hover`, `:focus`, `[data-state="…"]`, `.failed`-style selectors, (b) sibling element instances carrying `data-state="…"` variants, and (c) — for URL-path bundles — JSX conditional styling keyed on a prop or row.status. **Skipping any of these three is silent failure**: the default-state grid will rate `✓` while the state-conditional rule ships as a delta. Every property row records a `state` field; if no state is detectable for an element, record `state: default`.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## INPUT-KIND BRANCH

This step has two parallel ingestion paths. Both populate the same downstream state — `{design_dir}`, `{design_file}`, `{design_components}`, `{design_tokens}`, and the CSS-property catalog — so steps 2-4 are agnostic to which path ran.

```
if {input_kind} == "claude_design_url":  → execute §URL PATH below
if {input_kind} == "synthesize_bundle":  → execute §BUNDLE PATH below
```

Workflow.md's Input Resolution has already populated `{input_kind}`, `{design_url}` (URL path), or `{bundle_dir}` + `{bundle_manifest}` (bundle path). For the bundle path, the refusal gates (`dev_no_render`, `needs_human_review`) have already cleared — if execution reached this step with `{input_kind} == "synthesize_bundle"`, the manifest is good.

---

## URL PATH (`{input_kind} == "claude_design_url"`)

### URL.1. Download the Design Bundle

Claude Design artifact URLs return a gzip-compressed tar archive. Download and extract:

```bash
curl -sL "{design_url}" -o /tmp/design-bundle.tar.gz
mkdir -p /tmp/design-bundle
cd /tmp/design-bundle
file ../design-bundle.tar.gz
```

The file may be:
- **gzip compressed** → `gunzip -f ../design-bundle.tar.gz && tar xf ../design-bundle.tar`
- **tar archive directly** → `tar xf ../design-bundle.tar.gz`
- **HTML file** → copy directly to working directory

After extraction, find the project directory:
```bash
find /tmp/design-bundle -name "*.html" -type f | head -10
```

Store the directory containing the HTML files as `{design_dir}`.

### URL.2. Read the README

```bash
cat {design_dir}/README.md 2>/dev/null || cat {design_dir}/../README.md 2>/dev/null
```

The README contains:
- Which design file to implement (if `{design_file}` wasn't specified by the user)
- Chat transcript references that explain design decisions
- Import structure
- **Layout / page-shell assertions** (see below) — capture these into `{design_layout_constraints}`

If the README references chat transcripts, read them — they contain rationale that disambiguates edge cases.

**Capture `{design_layout_constraints}` — the page-shell intent the component sweep can't see.** The README almost always states how a feature page is framed in prose, and that prose is the ONLY authoritative source for the page container's width — because the bundle renders its root standalone and full-bleed (there is no app-shell or content-container in the bundle to measure). Scan the README (and the design policy it cites, if present) for layout assertions and record each verbatim with its constraint:

- Width / framing: "full-width within the content container", "centered max-width card", "max-width 1280", "edge-to-edge".
- Shell: "never inside a sidebar shell", "no hero strip above the table".
- Centering / gutters: "centered", "left-aligned", explicit horizontal padding.

Then read the **bundle wrapper element** for the target screen — the outermost layout element (`.app`, `<body>`, the root `<div>`) in `{design_file}` and its theme/layout CSS — and record ITS width treatment: `max-width` (or none → full-bleed), `margin: 0 auto` (centered) vs none, and root padding. The wrapper being full-bleed with no `max-width` is itself a positive assertion of "full-width", and it corroborates (or contradicts) the README prose.

Store both into `{design_layout_constraints}` as `{ source: "README" | "bundle-wrapper" | "policy", assertion: "<verbatim>", resolved: { width: "full-bleed" | "<px>", centered: bool, padding: "<value>" } }`. This is what step-03 §2d's mandatory page-shell row compares against. If the README is silent AND the wrapper is full-bleed, record `width: "full-bleed", centered: false` — silence + a full-bleed wrapper still means "fill the container", and the page-shell row is still emitted (a nested `max-width` cap in the impl is still a delta against it).

### URL.3. Read the Target Design File

Open `{design_dir}/{design_file}` and trace every `<script>` import:

```html
<script type="text/babel" src="components/data-quality-page.jsx"></script>
<script type="text/babel" src="theme/tokens.jsx"></script>
```

Read each imported file. Build `{design_components}` — a map of:

```
ComponentName → {
  file: relative path in bundle,
  props: [list of props],
  sections: [logical sections within the component]
}
```

### URL.4. Extract Design Tokens

Read the token/theme file (typically `theme/tokens.jsx` or similar). Extract and store `{design_tokens}`:

| Category | Token | Value |
|----------|-------|-------|
| Radius | sm | 2px |
| Radius | md | 3px |
| Radius | lg | 4px |
| Radius | xl | 6px |
| Type | h1 | 22px |
| Type | h2 | 18px |
| Type | body | 13px |
| ... | ... | ... |

### URL.5. Catalog Every Component's CSS Properties (JSX inline styles + state-conditional branches)

For each component in `{design_components}`, extract **every inline style property** from the JSX source. For every `style={{ ... }}` block, record one property row.

**State detection on the URL path.** JSX bundles encode states three ways — catalog ALL of them, not just the default branch:

1. **Conditional style objects.** `style={{ ...base, ...(row.status === 'failed' && failedStyles) }}` → emit rows for BOTH branches: one with `state: default` containing the base styles, one with `state: failed` containing the merged base + override styles.
2. **Template-literal class joins.** `` className={`row ${hovered ? 'row-hover' : ''} ${selected ? 'row-selected' : ''}`} `` → look up the referenced class rules in the same component file or imported stylesheets; emit a row per (component, state, property) triple.
3. **Multiple JSX siblings demonstrating variants.** A component file that renders `<Row state="default" />`, `<Row state="failed" />`, `<Row state="empty" />` for documentation → catalog the styling each variant resolves to.

Add `{design_states}[ComponentName]` populated with every state observed (deduplicated). If only the default branch exists, record `[default]` and move on.

Property rows live in TWO places (write to both — they're the same data, different shapes):

1. **Embedded in `{design_components}`** — append to `{design_components}[name].properties` (a list of rows). This is the canonical store that step-03 reads from when iterating component-by-component for the comparison grid.
2. **Flat list in `{css_property_catalog}`** — append to the flat catalog for SHARED.1's non-empty verification and SHARED.2's count display.

Both writes use the same row shape (see §SHARED below). Every row includes a `state` field — `default` for the unconditional branch, `hover | focus | selected | failed | empty | disabled | <other>` for state-conditional rules.

Token references like `tokens.radius.lg` resolve to their numeric value (`4px`) via `{design_tokens}` and the resolved value is what gets recorded; preserve the token name in parentheses for traceability.

### URL.6. Skip to §SHARED

Continue at §SHARED — Property catalog and ingestion summary.

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
- `{bundle_manifest}.page_mode` — `operational | analytical | detail`.
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

## SHARED — Property catalog and ingestion summary

Both paths converge here. `{design_components}` (with embedded `.properties` per component), `{css_property_catalog}` (flat view of the same rows), and `{design_tokens}` are populated; downstream steps don't need to know which path produced them.

**`{design_layout_constraints}` must be populated on BOTH paths.** The URL path fills it from README prose + the bundle wrapper (URL.2). The **bundle path has no README**, so for `{input_kind} == "synthesize_bundle"` derive it from the evidence the bundle does carry: read the screen HTML's outermost layout element (the root `<div data-region>` / `<body>`) for its width treatment (`max-width` present → capped; absent → full-bleed; `margin:auto` → centered) and fold in `{bundle_manifest}.page_mode` (`operational`/`analytical`/`detail`) as the framing hint. Record it in the same `{ source: "bundle-wrapper" | "manifest", assertion, resolved: {width, centered, padding} }` shape. Either path MUST leave `{design_layout_constraints}` non-empty (at minimum a `full-bleed` default from a wrapper with no `max-width`) so step-03 §2d's Page-shell row has a Design column to compare against.

**The two stores must agree.** The same property rows appear in BOTH `{design_components}[name].properties` AND `{css_property_catalog}` — they are different shapes of the same data, not parallel writes that could drift. Step-03 reads via `{design_components}[name].properties` (component-by-component for the comparison grid); the flat catalog exists for SHARED's counts and as a defensive sanity store. If the two ever disagree, the per-component embedding is canonical.

### SHARED.1. Verify the catalog is non-empty

If `{css_property_catalog}` is empty, that is a step-1 failure regardless of input kind. Halt with:

```
INGEST FAILURE: no CSS properties cataloged.

input_kind:    {input_kind}
design_dir:    {design_dir}
design_file:   {design_file}
components:    {len(design_components)}
tokens:        {len(design_tokens)}

A non-empty design source produced no styled elements. This is either a malformed
source (URL path: design file has no JSX style blocks; bundle path: HTML has no
inline style attributes) or a parsing bug. Investigate before proceeding.
```

### SHARED.2. Report ingestion summary

Output a brief summary:

```
Design ingested ({input_kind}):
  source:                 {design_url or design_dir}
  primary file:           {design_file}
{if input_kind == "synthesize_bundle":}
  page_mode:              {bundle_manifest.page_mode}
  screens:                {comma-separated bundle_manifest.screens}
  visual_quality:         {bundle_manifest.visual_review.visual_quality}
  exemplar_alignment:     {bundle_manifest.visual_review.exemplar_alignment}
  exemplars anchored:     {len(bundle_manifest.exemplars.selected)}
  policy sections cited:  {comma-separated bundle_manifest.policy_sections_cited}
{end if}
  components found:       {len(design_components)}
  token categories:       {comma-separated unique categories}
  tokens cataloged:       {len(design_tokens)}
  CSS properties:         {len(css_property_catalog)}
  states cataloged:       {sum(len(states) for states in design_states.values())} across {len(design_states)} components
  state breakdown:        {comma-separated unique states observed, e.g., "default(12), hover(4), focus(2), failed(3), empty(1)"}
{if any(states == ["default"] for component, states in design_states.items() if component in interactive_components):}
  ⚠ interactive-only-default: {list of interactive components with default-only states} — state-conditional rules may have been missed; re-audit <style> blocks before proceeding
{end if}
{if input_kind == "synthesize_bundle" and len(unresolved_var_refs) > 0:}
  ⚠ unresolved var(--*):  {len(unresolved_var_refs)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(config_class_violations) > 0:}
  ⚠ config-class violations: {len(config_class_violations)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(component_drift) > 0:}
  ⚠ manifest/HTML component drift: {len(component_drift)} — HTML wins per tie-breaker, but flag for audit
{end if}
{if input_kind == "synthesize_bundle" and len(state_drift) > 0:}
  ⚠ manifest/HTML state drift:
    over-claimed (in manifest, missing from HTML):   {len(state_drift.over_claimed)}
    under-reported (in HTML, missing from manifest): {len(state_drift.under_reported)}
    interactive-default-only (likely leak case):     {len(state_drift.interactive_default_only)} — re-audit <style> blocks before step-02
{end if}
```

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-02-map-implementation.md`

---

## SUCCESS METRICS

Both paths must populate the same normalized state:

- `{design_dir}` resolves to a directory containing the design source files.
- `{design_file}` resolves to a primary file inside `{design_dir}` that exists and is readable.
- `{design_components}` is a non-empty map of component name → metadata. Each component entry includes a non-empty `.properties` list of property rows (this is what step-03 iterates over).
- `{design_tokens}` is a non-empty list of tokens with resolved values.
- `{css_property_catalog}` is non-empty and every entry has `component`, `state`, `property`, `resolved_value`, `source`, and `source_file`. Its rows are identical to the rows embedded across `{design_components}[*].properties` — same data, different shape.
- `{design_states}` is populated for every component. Components with only `[default]` are flagged in the summary if they match interactive-component heuristics (rows, buttons, inputs, cells with `data-bind` / `data-action` / role="button") — interactivity without state-conditional rules is the dominant leak mode and warrants a re-audit of `<style>` blocks before step-02.

URL-path-only:
- Design bundle downloaded and extracted successfully.
- README read and chat transcripts consulted (if referenced).
- All imported files traced and read.

Bundle-path-only:
- No curl invocation occurred.
- `manifest.yaml`, `tokens.css`, and at least one `<screen>.html` verified to exist on disk.
- `{bundle_manifest}` fields surfaced in the summary so the user sees what design-synthesize recorded about visual quality, exemplar alignment, and policy sections.

## FAILURE MODES

- **Cross-path contamination.** Calling curl on a bundle path, or trying to parse `manifest.yaml` from a URL bundle. The §INPUT-KIND BRANCH check is a hard branch — never mix.
- Skipping imported files (URL path) ("I'll check those later" — no, read them now).
- Recording token names without resolving their values (e.g., `tokens.radius.lg` without noting it equals `4px`, or `var(--status-warning)` without resolving through `tokens.css`).
- Treating the HTML wrapper as the design spec on the URL path (the components and theme files are the spec; the HTML is just the wrapper).
- Missing asymmetric padding (`padding: '8px 12px'` is two properties, not one).
- Silently ignoring `{unresolved_var_refs}` or `{config_class_violations}` on the bundle path. These indicate a bundle that should not have been emitted; surface them in the summary even though they don't halt step 1.
- **State-axis blindness — the dominant leak mode.** Cataloging only inline `style="…"` and ignoring `<style>` blocks, `data-state` sibling variants, or JSX conditional style branches. The default-state catalog will look complete; the bundle's hover/focus/failed/empty/disabled rules will silently bypass the grid and ship as deltas in production. The 2026-05-28 fork retro (PR #827) was caused by exactly this — failed-row tint, failed-row hover, null-supplier styling, and null-total styling were all state-conditional and absent from the cataloged rows. If you finish ingestion with `{design_states}` showing only `[default]` for an interactive component (row, button, input, action cell), that is the signal that this failure mode is in play — re-audit `<style>` blocks before proceeding to step-02.
