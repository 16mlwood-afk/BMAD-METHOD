---
name: 'step-01-ingest-design'
description: 'Fetch the Claude Design bundle, extract it, read the README, trace all imports, and catalog every component with its CSS values'
---

# Step 1: Ingest Design

**Progress: Step 1 of 4** — Next: Map Implementation (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- If download fails, retry once. If it fails again, report the error and stop.
- Read every file in the bundle that the target design file imports — do not skip any.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## SEQUENCE OF INSTRUCTIONS

### 1. Download the Design Bundle

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

### 2. Read the README

```bash
cat {design_dir}/README.md 2>/dev/null || cat {design_dir}/../README.md 2>/dev/null
```

The README contains:
- Which design file to implement (if `{design_file}` wasn't specified by the user)
- Chat transcript references that explain design decisions
- Import structure

If the README references chat transcripts, read them — they contain rationale that disambiguates edge cases.

### 3. Read the Target Design File

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

### 4. Extract Design Tokens

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

### 5. Catalog Every Component's CSS Properties

For each component in `{design_components}`, extract **every inline style property**:

Read the JSX source. For every `style={{ ... }}` block, record:

| Component | Element | Property | Design Value |
|-----------|---------|----------|-------------|
| QualityVerdict | card wrapper | borderRadius | 4px (tokens.radius.lg) |
| QualityVerdict | icon container | width | 32px |
| QualityVerdict | icon container | height | 32px |
| QualityVerdict | SVG icon | width | 24px |
| QualityVerdict | SVG icon | height | 24px |
| HeatGrid | cell | minWidth | 54px |
| HeatGrid | cell | borderRadius | 2px (tokens.radius.sm) |
| ... | ... | ... | ... |

**Be exhaustive.** This table is the reference for the comparison grid in Step 3. Every property you miss here is a delta that leaks through.

Pay special attention to:
- `borderRadius` — the #1 source of design drift
- `fontSize` — design tokens vs Tailwind scale
- `padding` / `margin` — especially asymmetric values
- `width` / `minWidth` on grid columns and fixed-size containers
- `letterSpacing` / `fontWeight` / `textTransform` — typography details
- `gap` — flex/grid gap values
- `border` / `borderLeft` — width, color, opacity

### 6. Report Ingestion Summary

Output a brief summary:

```
Design ingested: {design_file}
Components found: {count}
Token categories: {list}
CSS properties cataloged: {count}
```

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-02-map-implementation.md`

---

## SUCCESS METRICS

- Design bundle downloaded and extracted successfully
- README read and chat transcripts consulted (if referenced)
- All imported files traced and read
- Design tokens extracted as a structured table
- Every component's CSS properties cataloged exhaustively
- `{design_components}` and `{design_tokens}` populated

## FAILURE MODES

- Skipping imported files ("I'll check those later" — no, read them now)
- Recording token names without resolving their values (e.g., `tokens.radius.lg` without noting it equals `4px`)
- Treating the HTML wrapper as the design spec (the components and theme files are the spec)
- Missing asymmetric padding (`padding: '8px 12px'` is two properties, not one)
