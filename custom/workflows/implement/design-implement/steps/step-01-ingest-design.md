---
name: 'step-01-ingest-design'
description: 'Ingest the design source — either fetch and extract a Claude Design URL bundle, or read a local design-synthesize bundle directory — then catalog every component with its CSS values. Both paths normalize to the same downstream state.'
---

# Step 1: Ingest Design

**Progress: Step 1 of 4** (+ a step-02b regression-surface preflight between map and grid) — Next: Map Implementation (autonomous)

**Announce the plan up front (one line to the user) before ingesting:** this run will ingest the handoff, map the current implementation, then — *before changing any code* — **run a regression-surface check: what does this handoff DROP relative to what production does today?** If it drops a capability, the run pauses and **advises a per-capability keep/drop plan to approve** — not a blank menu to fill in — rather than silently reproducing the omission (step-02b). State this so the user knows the capability check is coming; then proceed autonomously through ingest + map.

## RULES:

- FULLY AUTONOMOUS through ingest + map. No user interaction in steps 01–02. The first (and usually only) halt is step-02b's strategy choice, and only when the handoff drops a production capability.
- **Branch on `{input_kind}` at the top.** Two ingestion paths converge on the same downstream state. Never mix them: a `synthesize_bundle` path never calls curl; a `claude_design_url` path never reads `manifest.yaml`.
- If download fails (URL path only), retry once. If it fails again, report the error and stop.
- Read every file in the bundle that the target design file references — do not skip any.
- **Catalog the state axis explicitly.** Inline `style="…"` attributes only describe a single rendering. State-conditional rules live in (a) `<style>` blocks inside `<screen>.html` with `:hover`, `:focus`, `[data-state="…"]`, `.failed`-style selectors, (b) sibling element instances carrying `data-state="…"` variants, and (c) — for URL-path bundles — JSX conditional styling keyed on a prop or row.status. **Skipping any of these three is silent failure**: the default-state grid will rate `✓` while the state-conditional rule ships as a delta. Every property row records a `state` field; if no state is detectable for an element, record `state: default`.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## INPUT-KIND BRANCH

This step has three parallel ingestion paths. All populate the same downstream state — `{design_dir}` (or, on the manifest path, no dir), `{design_file}`, `{design_components}`, `{design_tokens}`, `{design_frame_inventory}`, `{design_layout_constraints}`, and the CSS-property catalog — so steps 2-4 are agnostic to which path ran.

```
if {input_kind} == "claude_design_url":  → execute §URL PATH below
if {input_kind} == "synthesize_bundle":  → execute §BUNDLE PATH below
if {input_kind} == "ingest_manifest":    → execute §MANIFEST PATH below
```

Workflow.md's Input Resolution has already populated `{input_kind}`, `{design_url}` (URL path), `{bundle_dir}` + `{bundle_manifest}` (bundle path), or `{ingest_manifest}` (manifest path). For the bundle path, the refusal gates (`dev_no_render`, `needs_human_review`) have cleared; for the manifest path, the completeness-invariant gate (no drawn frame with an empty section list) has cleared — if execution reached this step with that `{input_kind}`, the manifest is good.

**The MANIFEST PATH is the context fix.** A large bundle (~140KB JSX) does not fit one ingest context — the failure mode was shortcutting the exhaustive per-component catalog to fit, which let a whole *section* go unenumerated. When `design-ingest` has already fanned out per-frame and emitted a reviewed grid scaffold, this step reads that scaffold instead of re-cataloging; the exhaustive enumeration already happened, durably, in `design-ingest`.

---

## URL PATH (`{input_kind} == "claude_design_url"`)

### URL.1. Acquire the Design Bundle — two URL sub-kinds

A `{design_url}` is one of **two** sub-kinds, ingested differently. Detect by URL shape, then take the matching branch. Both converge on the same exit state: a local `{design_dir}` populated with the design files (HTML/JSX + `tokens/*.css` + `readme.md`), so URL.2 onward is unchanged.

- **`…api.anthropic.com/.../h/<id>`** (legacy tar artifact) → **URL.1a (curl + tar)**.
- **`claude.ai/design/p/<uuid>`** (a Claude Design *project* served through the **DesignSync** / `claude_design` MCP — the modern share-link the `/bmad:bmm:workflows:design-implement` command surface emits) → **URL.1b (MCP fetch)**. A `curl` of this URL returns HTML/a redirect, not a tar — never run the tar branch on it.

If the shape is ambiguous, attempt URL.1a; if `file` reports HTML/non-tar (not gzip, not tar), fall through to URL.1b rather than proceeding with an empty bundle.

#### URL.1a. Legacy tar artifact (`…/h/<id>`)

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

#### URL.1b. DesignSync project (`claude.ai/design/p/<uuid>`)

This URL is a design-system project read through the **DesignSync** (`claude_design`) MCP, NOT a tar — mirror the project's files to a local `{design_dir}` so the rest of URL PATH reads them exactly as it would an extracted bundle:

0. **Resolve `{design_file}` BEFORE fetching — and URL-decode it.** The `<uuid>` in `claude.ai/design/p/<uuid>` is the DesignSync `projectId`. The target file comes from one of two places, in this order: (a) the `Implement: <file>` line if the input was Claude Design's paste-prompt — it is **already path-decoded** (e.g. `orders-spend/Spend Analysis.html`), use it verbatim; (b) otherwise the URL's `?file=<path>` query param, which is **percent/`+`-encoded** and MUST be decoded — `%2F`→`/`, `+`→space, `%20`→space (e.g. `?file=orders-spend%2FSpend+Analysis.html` → `orders-spend/Spend Analysis.html`). The decoded value is the project-relative key `get_file` and the `list_files` tree match against; an undecoded `%2F`/`+` key will miss every file. If neither source is present, leave `{design_file}` unset and default it at step 4.
1. `get_project` with `projectId = <uuid>`; verify `type: PROJECT_TYPE_DESIGN_SYSTEM`. (If auth is missing, run `/design-login` first, per the command surface.)
2. `list_files` to enumerate the project tree (HTML/JSX frames, `tokens/*.css`, `readme.md`, data/app modules).
3. `mkdir -p /tmp/design-bundle` → `{design_dir}`. For the target frame (the decoded `{design_file}` from step 0), its `<script src>` module dependencies, the `tokens/*.css` files, and `readme.md`, call `get_file <path>` (the decoded path) and write each to `{design_dir}/<path>` **preserving the project-relative path** (so URL.2's README read, URL.3's target-file read, URL.3a's `<script src>`/sibling-`.html` enumeration, and URL.4's token-file reads all resolve against `{design_dir}` unchanged).
4. `{design_file}` is the decoded path from step 0. If it was unset, default to the project's primary HTML frame per `readme.md`.

The fetch mechanism is the ONLY difference — URL.2 (README) through URL.6 are mechanism-agnostic and run identically once `{design_dir}` holds the files.

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

**Capture `{design_layout_constraints}` — the page-shell intent the component sweep can't see, sourced AUTHORITATIVELY from the project design policy.** The bundle README is **generated by Claude Design** (it says so: "Trust hierarchy: `docs/design-policy.md` > … This system is policy-first; foundations are derived from the policy"), so it is NOT an independent spec — it is a lossy, possibly-stale, sometimes self-violated echo of the project's `docs/design-policy.md`. (Bundles routinely ship patterns their own README forbids — a colored-glow animation, a missing `prefers-reduced-motion` — because the generator doesn't enforce the policy on its own output.) So source the layout constraint in **precedence order**, not from the README alone:

1. **Project `docs/design-policy.md` — AUTHORITATIVE.** Read it (root or `inventory-manager/docs/`; it is the trust-hierarchy top the README itself names). Extract the page-framing rule verbatim — e.g. "Operational pages are table-first and **full-width within the content container**", "centered max-width card", "never inside a sidebar shell". This is the binding contract; the bundle was generated *from* it.
2. **Bundle README prose — corroboration only.** Capture the same layout assertions, tagged `source: "README-generated"`. Use to corroborate; if it contradicts the policy, the policy wins and log the drift.
3. **Bundle wrapper element — corroboration only.** Read the outermost layout element (`.app`, `<body>`, root `<div>`) in `{design_file}` + its theme CSS: `max-width` (or none → full-bleed), `margin: 0 auto` (centered) vs none, root padding. A bundle renders its root standalone, so a full-bleed wrapper corroborates "full-width" but is NOT proof — the bundle simply has no app-shell to express a cap.

Store as `{design_layout_constraints} = { source: "policy" | "README-generated" | "bundle-wrapper", assertion: "<verbatim>", resolved: { width: "full-bleed" | "<px>", centered: bool, padding: "<value>" }, authoritative: <true for policy, false for README/wrapper> }`. This is what step-03 §2d's mandatory page-shell row compares against. If `docs/design-policy.md` is absent (not every project has one), fall back to README + wrapper and mark `authoritative: false` so the page-shell delta is surfaced as "needs human confirmation" rather than asserted. If the policy is silent on framing AND the wrapper is full-bleed, record `width: "full-bleed", centered: false` — silence + a full-bleed wrapper still means "fill the container", and the page-shell row is still emitted (a nested `max-width` cap in the impl is still a delta against it).

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

### URL.3a. Catalog the declared frame inventory (`{design_frame_inventory}`)

The target file is rarely one frame. A worklist surface declares the **drilled detail drawer** and the **§13 expand-in-context lookups** it consumes — and those are the deliverables most often silently dropped: the "link to records (lookups)" the design viewer lists. On a brief-driven run, step-03 §2f gets this list from the brief's §7 Surface Inventory — but a raw Claude Design URL run has **no brief and no manifest**, so §2f would have no frame-coverage denominator and the lookup drawers would vanish (a worklist's lookups' inner primitives are shared and exist elsewhere in the impl, so the component sweep greens out over them). Capture the frame set NOW, from the evidence URL.3 already traced, so §2f has a URL-path denominator.

Build `{design_frame_inventory}` — one entry per frame the target surface delivers or consumes:

1. **`<script src>` frame modules + their comments.** Each module group the target imports is usually one frame; the HTML comment above it names what it carries — e.g. `<!-- Supply Order Detail Drawer modules (order frame + warehouse/batch/import/accounting lookups consumed) -->` declares the detail drawer PLUS four §13 lookups; `<!-- Catalog Record Drawer modules (catalog + supply-source frames consumed) -->` declares two more.
2. **Per-frame banners inside the traced modules.** Module files delimit frames with banner comments — `/* ===== warehouse-lookup ===== */`, `/* ===== inbound-batch-lookup ===== */`, `/* ===== import-run-lookup ===== */`, `/* ===== accounting-outcome-lookup ===== */`. Each banner is one frame.
3. **Lookup→target maps in the bundle data.** Data/app modules often carry an explicit map (e.g. `catalog: ["read-only §13 lookup", "Open full catalog item", "Catalog Items.html"]`) naming each lookup and the standalone frame it drills to.
4. **Sibling standalone `<frame>.html` the target links to.** The `find … -name "*.html"` from URL.1 lists them (e.g. `Catalog Record Drawer.html`, `Supply Order Detail Drawer.html`). A target that links to one declares that frame.
5. **THE AUTHORITATIVE SOURCE — the detail drawer's rendered "Linked records" section.** Sources 1–4 are bundle *self-declarations* (a comment, a banner, a map) — each can under-enumerate, be imprecise, or describe a different conditional state than the one drawn. The detail drawer's own **"Linked records" / "link to records" section is the ground truth**: it renders exactly **one row per §13 lookup the surface must drill to**, so the COUNT and IDENTITY of its rows is the canonical lookup denominator. Open the detail drawer frame and enumerate every linked-record row it draws (each `RecordLink` / row in the Linked-records list — e.g. `Catalog item`, `Route warehouse`, `Shipping lane`, `Supply source`, `Inbound batch`, `Import run`). Store this list as **`{design_linked_record_rows}`** — `[{ label, drills_to_frame (the lookup frame name this row opens), order }]`. This is what §2f reconciles the harvested frame set against; it is the fix for "the workflow often misses these," because a lookup that sources 1–4 failed to declare still appears here as a rendered row.

**Reconcile NOW — every Linked-records row MUST have a matching `§13-lookup` frame.** For each row in `{design_linked_record_rows}`, confirm `{design_frame_inventory}` contains a `role: §13-lookup` frame it drills to. A row with **no matching harvested frame** means sources 1–4 under-enumerated — do NOT drop it: re-trace the drawer's modules for the missing lookup, and if it still can't be located, add a frame entry `{ frame: "<label>-lookup", role: "§13-lookup", parent: "<detail-drawer>", declared_in: "linked-records-row (under-enumerated by script/banner/map)", drawn: "unknown" }` and flag it for §2f. The Linked-records row count is the denominator; the harvested frame set must equal or exceed it, never silently fall short.

Record each frame as:

```
{
  frame: "warehouse-lookup",            # frame/lookup name (banner | comment | filename)
  role: "§13-lookup",                   # primary | drilled-detail | §13-lookup
  parent: "supply-order-detail-drawer", # the frame it expands within (null for the primary)
  declared_in: "lookups.jsx banner",    # Orders.html comment | jsx banner | app.jsx map | sibling html
  drawn: true,                          # true when a module OR a standalone <frame>.html exists in the bundle
}
```

The primary frame (`{design_file}` itself) is always entry 0 with `role: primary`. **Open and catalog the components of every frame in the inventory.** A traced module's components are already cataloged in URL.5; a sibling standalone `<frame>.html` the target links to but does NOT `<script src>` import must be opened here (same trace as URL.3) so its components enter `{design_components}` rather than being invisible. A frame declared in a comment/map but with NO module and NO standalone HTML in the bundle is `drawn: false` → it carries into §2f as `FRAME NOT DRAWN` (routed, not inferred).

### URL.4. Extract Design Tokens — incl. the FOUNDATIONAL scale (read the CSS token files, not just the JSX theme)

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

**ALSO read the bundle's FOUNDATIONAL token files — the `tokens/*.css` CSS custom properties — into `{design_foundation_tokens}`.** A Claude Design bundle keeps its *foundation* in CSS custom properties (`tokens/typography.css` → `--font-size-base: 0.8125rem`, `tokens/spacing.css` → `--control-h`, `--radius*`, `tokens/colors.css` → `--status-*`), NOT in the JSX theme object — so a JSX-theme-only read SILENTLY MISSES the type scale, and step-03 §2i / §2 property #2 then have no resolved design value for `var(--font-size-base)` and no-op (greening a 13px-vs-16px drift). `ls {design_dir}/tokens/*.css` (or `{design_dir}/../tokens/*.css`); read each with the Read tool (not `cat`); extract the foundational subset — the **type scale** (`--font-size-base/-sm/-xs/-md`), **control heights** (`--control-h/-sm`), the **radius scale** (`--radius/-md/-lg`), and the **status-colour set** (`--status-*`) — resolving each `rem` to px. Store as `{design_foundation_tokens}` (a list of `{ token, value_px_or_hex, source_file }`). This is the design-side denominator for the §2i foundation-token reconciliation. If no `tokens/*.css` exists in the bundle, set `{design_foundation_tokens}` empty and note it — §2i will mark the foundation comparison `needs human confirmation` rather than silently skipping.

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

## MANIFEST PATH (`{input_kind} == "ingest_manifest"`)

No download, no extract, no per-component re-catalog. `design-ingest` already did the exhaustive, fanned-out enumeration and persisted it. This path READS the manifest into the same downstream state the other two paths produce.

### MANIFEST.1. Read the manifest

`{ingest_manifest}` is already parsed (workflow Input Resolution). It conforms to `design-ingest/manifest-schema.md`. Read, do not re-derive:

- `{design_layout_constraints}` ← `{ingest_manifest}.ingest.layout_constraints` (skip URL.2 / BUNDLE layout derivation entirely).
- `{design_tokens}` ← `{ingest_manifest}.ingest.tokens`.
- `{design_frame_inventory}` ← the manifest's **Frame inventory** table verbatim (skip URL.3a re-derivation). Each `drawn: false` frame carries into §2f as FRAME NOT DRAWN, exactly as on the URL path.
- `{design_file}` ← `{ingest_manifest}.ingest.target_file`.

### MANIFEST.2. Build `{design_components}` + catalog from the grid scaffold

The manifest's **Grid scaffold** has one row per `(frame, section)` — already the unit step-03 grids over. Map each scaffold row into `{design_components}` and the flat `{css_property_catalog}`:

- Component key = `"{frame} / {section}"` (so the grid iterates section-by-section, the granularity that closes the missing-section blind spot).
- `.properties` ← the row's `component×property rows`; `.copy` ← the verbatim design copy/structure; `.data_fields` ← the fields the section reads; carry the row's `status` (UNVERIFIED) so step-03 fills the verdict.
- Carry the manifest's **Data-availability notes** into `{content_unverified_count}` / the apply ledger's flag lane — a section whose fields the impl view-model lacks is flagged, never fabricated (same discipline as the content-lane cede).

### MANIFEST.3. Section-coverage is pre-satisfied — record it

Because the scaffold already enumerates every `(frame, section)`, the §2d-bis section-coverage gate (step-03) is seeded, not reconstructed. Record `{section_rows_source} = "ingest_manifest"` so step-03 knows the rows came from a gated, reviewed inventory rather than an in-context enumeration. (On the URL/bundle paths, `{section_rows_source} = "in_context"` and step-03 must enumerate each drawn frame's sections itself.)

### MANIFEST.4. Skip to §SHARED

Continue at §SHARED — the catalog is already populated from the scaffold; SHARED.1 verifies it is non-empty (a manifest that yielded zero rows is a malformed manifest — halt) and SHARED.2 reports the summary.

---

## SHARED — Property catalog and ingestion summary

Both paths converge here. `{design_components}` (with embedded `.properties` per component), `{css_property_catalog}` (flat view of the same rows), and `{design_tokens}` are populated; downstream steps don't need to know which path produced them.

**`{design_layout_constraints}` must be populated on BOTH paths — and the AUTHORITATIVE source is path-independent.** On either path, the binding layout rule comes from the project `docs/design-policy.md` (URL.2 precedence #1) — both the Claude-Design URL README and a synthesize bundle are generated artifacts downstream of that policy. The paths differ only in their *corroboration*: the URL path has a generated README + the bundle wrapper (URL.2); the **synthesize-bundle path has no README**, so its corroboration is the screen HTML's outermost layout element (root `<div data-region>` / `<body>` — `max-width` present → capped; absent → full-bleed; `margin:auto` → centered) plus `{bundle_manifest}.page_mode` (`operational`/`analytical`/`detail`) as a framing hint, tagged `source: "bundle-wrapper" | "manifest", authoritative: false`. Either path MUST leave `{design_layout_constraints}` non-empty (at minimum a `full-bleed` default from a wrapper with no `max-width`) so step-03 §2d's Page-shell row has a Design column; if the policy was readable, the policy entry is the one marked `authoritative: true`.

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

### SHARED.1a. Supersede awareness (URL / bundle paths) → `{handoff_supersede_status}`

Skip on the manifest path — `{handoff_supersede_status}` is already set from the stamp at intake (Input Resolution). On the URL and bundle paths there is no stamp, so resolve it HERE, now that the frame inventory exists (the slug isn't knowable before it). This is what lets a handoff handed STRAIGHT to `design-implement` cope with supersede, not only one that came through `design-ingest`. `brief-revision-policy.md` §8.

Resolve exactly as `design-ingest` step-01 §5 (same contract — do not duplicate the logic):

1. Derive `{target_slug}` from the primary frame (`{design_frame_inventory}` entry 0). Prefer an exact match to an existing brief's `target_slug`.
2. Match it against the briefs in `{implementation_artifacts}`, read `brief_status`, and set `{handoff_supersede_status}` to `active` | `superseded` | `no_brief` | `ambiguous` (`no_brief` when the surface doesn't confidently correspond to any brief — do NOT force a match or infer `active`; capture `{superseded_by}` when `superseded`).

Then gate — symmetric with the manifest path, but a direct URL/bundle run has no prior dispositions, so it is effectively the "there is work to apply" case:

- **`active` / `no_brief`** → continue normally.
- **`superseded`** → SURFACE it now ("this handoff is superseded by `{superseded_by}`; that newer brief is the current truth") and **HALT before the apply pipeline (steps 2–4) for explicit confirmation** — proceeding would build the surface toward the superseded design, which is intent, not decision autonomy, so autonomous mode does NOT proceed unasked. Halting here (before the grid) also avoids wasting the mapping/grid work. On explicit confirmation — or after the user re-points at `{superseded_by}` — continue. **Never** silently apply a superseded handoff.
- **`ambiguous`** → warn (two briefs claim `active` for this slug; `brief-revision-policy.md` §2.6) and continue — the design source itself is fine.

### SHARED.1b. Bundle → brief conformance gate (the design proposal is not yet a contract)

**The bundle is a PROPOSAL; the brief is the contract. This gate refuses to implement a proposal that silently under-delivers the contract** — the receive-station failure (a strong "station, not dashboard" brief produced a centered hero card with minimal frame coverage, which `design-implement` then faithfully shipped because nothing compared the two). It runs on EVERY path, AFTER SHARED.1a has resolved the brief via `{target_slug}`, and BEFORE step-02/03/04 — a non-conformant proposal is bounced before any mapping or grid work is spent on it.

**Precondition — a brief must exist to gate against.** Use the `{handoff_supersede_status}` resolved in SHARED.1a:

- **`no_brief`** (no brief matched `{target_slug}`) → there is no captured contract, so conformance **cannot be verified** — the SP-API lesson (a surface whose brief was never saved). Do NOT silently treat absence as a pass: record `{bundle_conformance} = UNVERIFIED (no brief)` and surface it in SHARED.2 ("implementing the proposal as-is; no brief to gate against — capture one via `design-handoff` to enable this gate"). Proceed.
- **`active` / `superseded` / `ambiguous`** (a brief matched) → read its machine-readable contract fields — `frames` (the §7 contract-key ids), `shell_role` (`required_shell` / `required_chrome` / `forbidden_chrome`), and `composition` (`brief-revision-policy.md` §2 Block B) — and run the three structural checks below. A brief that PRE-DATES these fields (older brief, field absent) is the same degraded case **per dimension**: mark that dimension `UNVERIFIED (brief lacks <field>)`, disclose it, and gate only the dimensions the brief actually carries.

**The three structural checks (structure, not style):**

1. **Frame coverage** — every id in the brief's `frames` list must appear as a DRAWN frame in `{design_frame_inventory}` (a present module / standalone HTML / manifest scaffold row — `drawn: true`). A brief frame the bundle never drew is a proposal that under-delivered the surface inventory, not a thin-but-acceptable build. (This is the brief-side denominator that complements step-03 §2f's impl-side coverage; here it gates the BUNDLE, there it gates the IMPL.)
2. **Shell / role** — when `shell_role` is present: the bundle's own rendered frame must carry `required_chrome` (verbatim where it draws it) and must NOT render `forbidden_chrome`. A clerk-station bundle that draws the owner global nav — or omits the clerk header — fails here. (The impl-side twin, an ANCESTOR layout injecting `forbidden_chrome` over the surface at runtime, is caught later by step-02 §1a / step-03 §2d against this same `forbidden_chrome`.)
3. **Composition / job-loop** — when `composition` is a NON-default key (a `recommended-alt` such as `scanner-terminal` / `single-item-stream`, i.e. the brief said "this is NOT the page-mode default — it's a station/stream/verify surface"): the bundle must express the JOB LOOP the composition names (e.g. scan → feedback → tally → close), not a single centered hero card in dead space. This check is a **judgment** read (PROBABILISTIC — there is no exact test for "expresses the loop"); checks 1–2 are structural id/string matches (still model-executed, so structured-probabilistic — the fully-deterministic tier is a per-project CI/manifest validator, which does NOT ship via the fork sync).

**On a miss in check 1 or 2 → HALT. Do NOT proceed to step-02.** Print:

```
══════════════════════════════════════════════════════════════════
✗ design-implement halted — the bundle does not conform to its brief.

This is a PROPOSAL that under-delivers the CONTRACT, not a build target.
Implementing it would ship the design's misread (the receive-station failure).

Brief:   {matched brief filename} (target_slug: {target_slug})
{for each frame-coverage miss:}  ✗ frame "{id}" — in brief.frames, NOT drawn in the bundle
{if shell miss:}                 ✗ shell — bundle renders forbidden chrome "{forbidden_chrome}" / omits required "{required_chrome}"
{if composition concern:}        ⚠ composition — brief says "{composition}" (job loop), bundle reads as a hero/dashboard

Next: revise the design so it covers the brief, then re-run. The bundle is
"proposal only; needs revision" — re-run design-synthesize (fork path) or
regenerate in Claude Design against the brief, then re-invoke design-implement.
══════════════════════════════════════════════════════════════════
```

A check-3 composition concern with checks 1–2 passing is a **warn**, not a hard halt (it is a judgment call): surface it loudly in SHARED.2 and carry it to step-03 / the §9 report so design-review can adjudicate the station-vs-dashboard verdict on the live surface — but do not silently bless it. Record the outcome as `{bundle_conformance} = pass | UNVERIFIED(reason) | halted(reasons) | warn(composition)` for the SHARED.2 line.

### SHARED.2. Report ingestion summary

Output a brief summary:

```
Design ingested ({input_kind}):
  source:                 {design_url or design_dir}
  primary file:           {design_file}
  bundle conformance:     {bundle_conformance}   ← SHARED.1b: pass | UNVERIFIED(reason) | warn(composition). A hard HALT (frame/shell miss) exits BEFORE this summary.
{if input_kind == "synthesize_bundle":}
  page_mode:              {bundle_manifest.page_mode}
  screens:                {comma-separated bundle_manifest.screens}
  visual_quality:         {bundle_manifest.visual_review.visual_quality}
  exemplar_alignment:     {bundle_manifest.visual_review.exemplar_alignment}
  exemplars anchored:     {len(bundle_manifest.exemplars.selected)}
  policy sections cited:  {comma-separated bundle_manifest.policy_sections_cited}
{end if}
  components found:       {len(design_components)}
{if input_kind == "claude_design_url":}
  frames declared:        {len(design_frame_inventory)} — {comma-separated frame names, e.g. "Orders(primary), supply-order-detail-drawer, warehouse-lookup, inbound-batch-lookup, import-run-lookup, accounting-outcome-lookup, catalog-record-drawer, supply-source-lookup"}
  of which §13 lookups:   {count of role == "§13-lookup"} ← step-03 §2f checks each is built in the impl (no brief, so the bundle IS the frame contract)
  linked-records rows:    {len(design_linked_record_rows)} drawn in the detail drawer — {comma-separated labels} (the AUTHORITATIVE lookup denominator; §13-lookup frames must equal-or-exceed this){if any row has no matching §13-lookup frame: " ⚠ {n} UNDER-ENUMERATED → re-traced / flagged for §2f"}
{end if}
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
- `{design_frame_inventory}` populated (URL.3a) — the primary frame plus every drilled drawer and §13 lookup the target declares (via `<script src>` modules + comments, per-frame banners, lookup→target maps, sibling standalone `<frame>.html`). Each linked standalone frame opened and its components folded into `{design_components}`. This is step-03 §2f's frame-coverage denominator on a no-brief run.
- **`{design_linked_record_rows}` populated AND reconciled (URL.3a source 5)** — the detail drawer's rendered "Linked records" rows enumerated (the AUTHORITATIVE lookup denominator), and every row confirmed to map to a `§13-lookup` frame in `{design_frame_inventory}`. Any row that sources 1–4 failed to declare was re-traced or added as an under-enumerated lookup frame, never silently dropped. The harvested §13-lookup count ≥ the Linked-records row count.
- `{handoff_supersede_status}` resolved on this run (manifest path: from the stamp at intake; URL/bundle paths: independently in §SHARED.1a). A `superseded` URL/bundle run SURFACED and HALTED for explicit confirmation before the apply pipeline — it never silently built the superseded design.

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
- **Frame-inventory blindness on the URL path (URL.3a) — the "link to records (lookups)" leak.** Cataloging only the primary file's components and never recording the drilled detail drawer + the §13 lookups it consumes. On a raw-URL run there is no brief and no manifest, so step-03 §2f has no other frame-coverage denominator — skip URL.3a and the lookup drawers (warehouse / inbound-batch / import-run / accounting-outcome / catalog / supply-source for Orders.html) vanish: their inner primitives are shared and match somewhere in the impl, so the component grid greens out while the whole drawer ships unbuilt. The bundle declares these frames itself (the `<script src>` comments literally say "… lookups consumed", the modules carry `/* ==== warehouse-lookup ==== */` banners) — capturing them is reading evidence already in hand, not inventing a contract.
- **Harvesting the lookup set from bundle self-declarations alone — the under-enumeration leak (the "often misses these" failure).** Sources 1–4 (script comments, banners, lookup→target maps) are *declarations* and can be incomplete, imprecise, or describe a different conditional state than the one rendered — so a lookup the comments forgot to list never enters `{design_frame_inventory}`, and §2f cannot flag a frame it never knew existed. The detail drawer's rendered **"Linked records" section** is the authoritative denominator (one row per lookup that must exist — e.g. the live Orders detail drawer draws `Catalog item · Route warehouse · Shipping lane · Supply source · Inbound batch · Import run`, where `Shipping lane` is exactly the kind of row a script-comment harvest misses). Failing to enumerate `{design_linked_record_rows}` and reconcile the harvested §13-lookup frames against it is how a linked-record drawer silently goes unchecked against Claude Design. The row count is the floor; harvest must meet or exceed it.
- **State-axis blindness — the dominant leak mode.** Cataloging only inline `style="…"` and ignoring `<style>` blocks, `data-state` sibling variants, or JSX conditional style branches. The default-state catalog will look complete; the bundle's hover/focus/failed/empty/disabled rules will silently bypass the grid and ship as deltas in production. The 2026-05-28 fork retro (PR #827) was caused by exactly this — failed-row tint, failed-row hover, null-supplier styling, and null-total styling were all state-conditional and absent from the cataloged rows. If you finish ingestion with `{design_states}` showing only `[default]` for an interactive component (row, button, input, action cell), that is the signal that this failure mode is in play — re-audit `<style>` blocks before proceeding to step-02.
