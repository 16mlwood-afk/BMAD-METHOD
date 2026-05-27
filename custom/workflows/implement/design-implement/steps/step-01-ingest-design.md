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

If the README references chat transcripts, read them — they contain rationale that disambiguates edge cases.

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

### URL.5. Catalog Every Component's CSS Properties (JSX inline styles)

For each component in `{design_components}`, extract **every inline style property** from the JSX source. For every `style={{ ... }}` block, record one property row.

Property rows live in TWO places (write to both — they're the same data, different shapes):

1. **Embedded in `{design_components}`** — append to `{design_components}[name].properties` (a list of rows). This is the canonical store that step-03 reads from when iterating component-by-component for the comparison grid.
2. **Flat list in `{css_property_catalog}`** — append to the flat catalog for SHARED.1's non-empty verification and SHARED.2's count display.

Both writes use the same row shape (see §SHARED below).

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

### BUNDLE.5. Catalog every CSS property (inline `style="…"` + resolved `var(--*)`)

For each `<screen>.html` file, extract **every visual property** declared inline. The bundle's invariant is "every visual value is explicit at parse time" — so the catalog is built by scanning inline `style="…"` attributes and resolving any `var(--*)` references through `{design_tokens}`.

For each `style="..."` attribute:

- Split into individual `property: value;` declarations.
- For each declaration, record one property row in TWO places (same data, different shapes):
  1. **Embedded in `{design_components}`** — append to `{design_components}[component].properties`. This is the canonical store that step-03 reads from when iterating component-by-component for the comparison grid.
  2. **Flat list in `{css_property_catalog}`** — append to the flat catalog for SHARED.1's non-empty verification and SHARED.2's count display.

Row shape (used for both writes):

```
{
  component: "StatusBadge",            # from the nearest ancestor data-component
  screen: "list.html",                 # source screen
  element: "<span>" or selector path,  # the DOM element bearing the style attribute
  property: "background-color",        # CSS property name (kebab-case as in CSS, not camelCase)
  raw_value: "var(--status-warning)",  # exact source value from the attribute
  resolved_value: "#f59e0b",           # resolved through tokens.css (var(--*) → value)
  token_ref: "--status-warning",       # populated when raw_value is a var(--*) reference
  source_file: "list.html",
  source_line: 47,
}
```

If a `var(--*)` reference cannot be resolved against `{design_tokens}`, that is an invariant-1 violation that design-synthesize step 7 should already have caught. Log as `{unresolved_var_refs}` and surface in the ingestion summary — do not halt, but flag prominently (this bundle should not have been emitted).

**Be exhaustive.** Every property on every styled element. This table is the reference for the comparison grid in Step 3. Every property missed here is a delta that leaks through.

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
{if input_kind == "synthesize_bundle" and len(unresolved_var_refs) > 0:}
  ⚠ unresolved var(--*):  {len(unresolved_var_refs)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(config_class_violations) > 0:}
  ⚠ config-class violations: {len(config_class_violations)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(component_drift) > 0:}
  ⚠ manifest/HTML component drift: {len(component_drift)} — HTML wins per tie-breaker, but flag for audit
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
- `{css_property_catalog}` is non-empty and every entry has `component`, `property`, `resolved_value`, and `source_file`. Its rows are identical to the rows embedded across `{design_components}[*].properties` — same data, different shape.

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
