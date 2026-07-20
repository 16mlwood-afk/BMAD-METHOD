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

> **Sub-agent delegation caveat (the DesignSync MCP is session-bound — gap 510).** The DesignSync / `claude_design` MCP is **session-authenticated and absent from sub-agent contexts** (the documented "interactively-authenticated MCP servers may be absent in headless/sub-agent runs" caveat). So when a later step delegates a read-heavy comparison to a sub-agent to stay inside the context budget (step-04 §5a), **the orchestrator MUST pass the resolved source INTO the agent** — the mirrored `{design_dir}` files written here, or an `ingest_manifest` whose grid scaffold already carries value-exact per-property rows — and must **never tell the agent to fetch via the MCP** (it will come back blocked, and a good agent will refuse to invent design values). On a large surface where the delegated diff needs live source the sub-agent cannot reach, either **ingest first** (the manifest path bakes resolved values into the artifact, so a manifest-driven sub-agent diff needs no MCP) or **run the diff in the session that holds the source**. Mirroring to `{design_dir}` here is what makes the source travel as files; keep it complete for exactly this reason.

0. **Resolve `{design_file}` BEFORE fetching — and URL-decode it.** The `<uuid>` in `claude.ai/design/p/<uuid>` is the DesignSync `projectId`. The target file comes from one of two places, in this order: (a) the `Implement: <file>` line if the input was Claude Design's paste-prompt — it is **already path-decoded** (e.g. `orders-spend/Spend Analysis.html`), use it verbatim; (b) otherwise the URL's `?file=<path>` query param, which is **percent/`+`-encoded** and MUST be decoded — `%2F`→`/`, `+`→space, `%20`→space (e.g. `?file=orders-spend%2FSpend+Analysis.html` → `orders-spend/Spend Analysis.html`). The decoded value is the project-relative key `get_file` and the `list_files` tree match against; an undecoded `%2F`/`+` key will miss every file. If neither source is present, leave `{design_file}` unset and default it at step 4.
1. `get_project` with `projectId = <uuid>`; verify `type: PROJECT_TYPE_DESIGN_SYSTEM`. (If auth is missing, run `/design-login` first, per the command surface.)
2. `list_files` to enumerate the project tree (HTML/JSX frames, `tokens/*.css`, `readme.md`, data/app modules).
3. `mkdir -p /tmp/design-bundle` → `{design_dir}`. For the target frame (the decoded `{design_file}` from step 0), its `<script src>` module dependencies, the `tokens/*.css` files, and `readme.md`, mirror each file to `{design_dir}/<path>` via the **context-free persist mechanism below** — NOT by pasting `get_file`'s return value back out — **preserving the project-relative path** (so URL.2's README read, URL.3's target-file read, URL.3a's `<script src>`/sibling-`.html` enumeration, and URL.4's token-file reads all resolve against `{design_dir}` unchanged).

> **Mirror `get_file` to disk WITHOUT pulling the bytes through context (fork-side workaround — DesignSync `get_file` has no to-disk sink).** `claude_design`'s only read verb, `get_file`, RETURNS file content into the caller's context — unlike `write_files`, which has a `localPath` sink. So the naive "call `get_file`, then write the returned string to disk" pulls every byte of every mirrored file through the orchestrator context first; a large bundle blows the budget in exactly the case the ingest fan-out exists to protect (the bigger the bundle, the worse it fails). Sidestep it by staging each `get_file` through the harness's tool-results file, so the content lands on disk and NEVER re-enters your context:
> 1. Call `get_file <path>`. When the result is large the harness auto-persists the raw tool output to a `tool-results/*.txt` JSON file and hands you back only that PATH — treat that file as the mirror source; do NOT echo or re-read its contents into context. (If you must force the raw JSON to a file yourself, write it to a temp path first — same downstream extract.)
> 2. Extract the file body straight from that JSON to the target path, so the content goes file→file and is never returned to you:
>
>    ```bash
>    python3 -c "import json;print(json.load(open('$TOOL_RESULT_PATH'))['content'])" > "{design_dir}/<path>"
>    ```
>
>    (`content` is the `get_file` payload key; adjust if the MCP nests it, e.g. `['result']['content']`.) A small `get_file` that returned inline rather than via a `tool-results/*.txt` file can be written directly — the O(1)-context win is for the LARGE files that would otherwise dominate the budget.
>
> This keeps mirroring **O(1) context regardless of bundle size**. It is a **fork-side workaround**, formalized here so it isn't rediscovered per session — the clean upstream fix is the follow-up noted under step 4.
4. `{design_file}` is the decoded path from step 0. If it was unset, default to the project's primary HTML frame per `readme.md`.

> **Upstream follow-up (the clean fix — not for this workflow to build).** The persist-to-disk dance in step 3 exists only because DesignSync `get_file` returns content into context. The proper fix is in the MCP itself: give `get_file` a `localPath` sink symmetric with `write_files` (read straight to disk, content never returned to the caller). That would retire the tool-results workaround above. Tracked as a DesignSync gap.

The fetch mechanism is mechanism-agnostic from here — URL.2 (README) through URL.7 run identically once `{design_dir}` holds the files. What is NOT agnostic is the bundle's **shape**; resolve that next (URL.1c) before anything reads a path.

### URL.1c. Bundle SHAPE branch — legacy JSX vs `.dc.html` (`{bundle_shape}`)

**The fetch mechanism is not the only difference — the bundle SHAPE is, and getting it wrong makes every downstream ingest instruction silently no-op.** URL.2–URL.5 were written against the legacy Claude Design bundle: a root `README.md`, `<script type="text/babel" src="components/*.jsx">` module imports, `theme/tokens.jsx`, and `/* ==== frame ==== */` banners inside those modules. Claude Design's current "Send to local coding agent" panel emits a **different, self-contained shape** — a `<name>.dc.html` frame document plus a `_ds/<design-system-id>/` directory — in which **none of those paths exist**. Run the legacy instructions against it and each one finds nothing: no README, no traced modules, no `tokens.jsx`, no banners. The catalog comes back near-empty but *plausible*, and the grid then proceeds against a denominator missing whole frames and whole variants. Detect the shape FIRST — before the size preflight, which counts `<script src>` groups and would read zero on a `.dc.html` bundle of any size.

Set `{bundle_shape}`:

- **`dc_html`** — the target file ends `.dc.html`, OR `{design_dir}` contains `support.js`, OR the target's body contains an `<x-dc>` root element. Any ONE of these is sufficient.
- **`legacy_jsx`** — otherwise. A root `README.md` plus `<script type="text/babel">` imports is the positive confirmation.

Where the two shapes diverge, each of URL.2–URL.5 carries an explicit **`.dc.html` sub-branch**. **Legacy bundles are untouched** — the existing instructions remain the `legacy_jsx` branch verbatim; nothing about the legacy path changes. Carry `{bundle_shape}` into the SHARED.2 summary so the run states which shape it ingested (a run that reports `legacy_jsx` on a `.dc.html` target is the misdetection to catch).

### URL.1d. Size preflight — recommend `design-ingest` for a large surface

**Estimate the surface's scale NOW — after `list_files` + the target `get_file`, BEFORE the inline re-catalog (URL.3–URL.5) spends orchestrator context.** The URL path pulls the whole design into THIS context and re-enumerates every component; a large multi-frame bundle can burn the context budget before the run can even tell the surface was too big — the exact `context-budget-overflow` failure the `design-ingest` manifest path exists to avoid (durable manifest → resumable, checkpointed apply; see the resumable-apply Critical Rule in workflow.md). So gate on a CHEAP, pre-catalog estimate:

- **Frame count** — count the frame-inventory *sources* without tracing them. **Shape-dependent (`{bundle_shape}` from URL.1c) — using the wrong counter reads zero and defeats the preflight:**
  - `legacy_jsx` → the `<script src>` module groups the target imports plus the sibling standalone `<frame>.html` files from URL.1's `find` / `list_files`.
  - `dc_html` → the `<!-- ==== FRAME n · <id> ==== -->` banner comments plus the `data-screen-label` / `id` attributes on frame roots inside the single `.dc.html`, plus sibling `*.dc.html` files in the project tree. A `.dc.html` bundle carries its frames INSIDE one document, so a `<script src>` count is structurally zero no matter how many frames it holds.

  (Either way this is the same evidence URL.3a lifts into `{design_frame_inventory}`, counted here, not yet cataloged.)
- **Target byte size** — `wc -c {design_dir}/{design_file}` (or the `get_file` payload size on the MCP path). Shape-independent.

**Above a SOFT threshold — ≈5 frames OR ≈60KB target (thresholds, not cliffs, per the context-budget principle) — SURFACE this recommendation before continuing:**

```
────────────────────────────────────────────────────────────────
◇ Large surface — recommend routing through design-ingest first.

  frames (est):  {n}   ·   target size:  {kb}KB
  soft threshold: ≥5 frames OR ≥60KB

This URL run would pull the whole design into THIS context and re-catalog it
inline — a large surface can exhaust the context budget before the grid is even
built. design-ingest fans out per-frame, enumerates every section under its
completeness gate into a DURABLE manifest, and hands design-implement a
resumable, checkpointed apply — the reason that path exists.

  Recommended:  /bmad:bmm:workflows:design-ingest {design_url}
  then:         /bmad:bmm:workflows:design-implement <the design-ingest-*.md it emits>
────────────────────────────────────────────────────────────────
```

This is a **recommendation, not a hard refuse** — a clean, low-cost early exit offered while almost no context has been spent, NOT a halt. In interactive mode, prefer the exit (re-route through `design-ingest`) unless the user says to continue inline; in autonomous mode, DISCLOSE the recommendation and proceed with the inline URL ingest (same posture as the other autonomous-mode disclosures). Below the threshold, record nothing and continue silently to URL.2.

### URL.2. Read the README

**`legacy_jsx`:**

```bash
cat {design_dir}/README.md 2>/dev/null || cat {design_dir}/../README.md 2>/dev/null
```

**`dc_html` — the README lives INSIDE the design-system directory, not at bundle root.** Neither path above exists, so the legacy read silently yields nothing and `{design_layout_constraints}` comes back empty on a path where the policy read is the only authoritative layout source. Resolve it from the design-system dir instead:

```bash
ls -d {design_dir}/_ds/*/ 2>/dev/null                    # → the <ds-id> dir (usually exactly one)
cat {design_dir}/_ds/<ds-id>/readme.md 2>/dev/null       # note: lowercase readme.md
```

Take `<ds-id>` from the `<helmet>` block's stylesheet hrefs (URL.4 resolves the same prefix) rather than guessing — the id is a long slug and must match exactly. If more than one `_ds/*/` exists, use the one the target's `<helmet>` actually links. **Do NOT fall back to a root `README.md` for a `.dc.html` bundle** — there isn't one, and treating its absence as "no layout constraint" is the silent failure.

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

**`legacy_jsx`** — open `{design_dir}/{design_file}` and trace every `<script>` import:

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

**`dc_html` — there are no module imports to trace; the frame document IS the source.** A `.dc.html` file is self-contained: markup, inline styles, and its logic script all live in the one file. Tracing `<script src>` returns only `./support.js` and the design-system `_ds/<ds-id>/_ds_bundle.js` — neither is a component module, and concluding "no components" from that is the silent no-op this branch exists to prevent. Read the target file fully (Read tool, not `cat` — it is typically 40–80KB) and build `{design_components}` from its own structure:

- **Frame roots** — elements carrying `data-screen-label` / `id`, each introduced by a `<!-- ==== FRAME n · <id> ==== -->` banner. These are the top-level units (URL.3a catalogs them as frames).
- **Named sections within a frame** — `<header>`, semantic groups, and any element whose banner comment or heading names it. Component key is `"{frame} / {section}"`, the same granularity the manifest path uses (MANIFEST.2), so step-03 grids section-by-section.
- **Imported design-system components** — `<x-import component-from-global-scope="…Button" variant="secondary" size="sm">`. Record the imported name + the variant/size attributes; the resolved styling lives in `_ds/<ds-id>/styles.css` + the token files (URL.4), not inline.

Record `file:` as the `.dc.html` path for every entry (they all come from the one document), and `sections:` from the frame's own structure.

### URL.3a. Catalog the declared frame inventory (`{design_frame_inventory}`)

The target file is rarely one frame. A worklist surface declares the **drilled detail drawer** and the **§13 expand-in-context lookups** it consumes — and those are the deliverables most often silently dropped: the "link to records (lookups)" the design viewer lists. On a brief-driven run, step-03 §2f gets this list from the brief's §7 Surface Inventory — but a raw Claude Design URL run has **no brief and no manifest**, so §2f would have no frame-coverage denominator and the lookup drawers would vanish (a worklist's lookups' inner primitives are shared and exist elsewhere in the impl, so the component sweep greens out over them). Capture the frame set NOW, from the evidence URL.3 already traced, so §2f has a URL-path denominator.

Build `{design_frame_inventory}` — one entry per frame the target surface delivers or consumes:

1. **`<script src>` frame modules + their comments.** Each module group the target imports is usually one frame; the HTML comment above it names what it carries — e.g. `<!-- Supply Order Detail Drawer modules (order frame + warehouse/batch/import/accounting lookups consumed) -->` declares the detail drawer PLUS four §13 lookups; `<!-- Catalog Record Drawer modules (catalog + supply-source frames consumed) -->` declares two more.
2. **Per-frame banners inside the traced modules.** Module files delimit frames with banner comments — `/* ===== warehouse-lookup ===== */`, `/* ===== inbound-batch-lookup ===== */`, `/* ===== import-run-lookup ===== */`, `/* ===== accounting-outcome-lookup ===== */`. Each banner is one frame.
3. **Lookup→target maps in the bundle data.** Data/app modules often carry an explicit map (e.g. `catalog: ["read-only §13 lookup", "Open full catalog item", "Catalog Items.html"]`) naming each lookup and the standalone frame it drills to.
4. **Sibling standalone `<frame>.html` the target links to.** The `find … -name "*.html"` from URL.1 lists them (e.g. `Catalog Record Drawer.html`, `Supply Order Detail Drawer.html`). A target that links to one declares that frame.

**`dc_html` — sources 1–4 above have `.dc.html` equivalents; substitute them one-for-one.** The harvest *sources* change; nothing else in URL.3a does — the reconciliation against source 5 below is unchanged and still mandatory.

- **1′ (replaces the `<script src>` comment).** `<!-- ==== FRAME n · <id> ==== -->` banner comments inside the target document. Each banner opens one frame; `<id>` is the frame name.
- **2′ (replaces the per-module JSX banner).** `data-screen-label` and `id` attributes on each frame root element. These agree with the banner comment and are the machine-readable form — prefer them when the two disagree.
- **3′ (replaces the lookup→target map).** Cross-frame anchors: `<a href="Other Frame.dc.html#anchor">`. Each distinct `href` target is a lookup edge — the `#anchor` names the frame within that document, the filename names the document. An `href` into the SAME document (`#some-frame`) is an intra-document edge to a frame already harvested by 1′/2′.
- **4′ (replaces the sibling standalone `<frame>.html`).** Sibling `*.dc.html` files in the project tree (`list_files` / `find`). A target that anchors into one declares that frame; open it and fold its components into `{design_components}` exactly as the legacy branch does.

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

**`legacy_jsx`** — read the token/theme file (typically `theme/tokens.jsx` or similar). Extract and store `{design_tokens}`:

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

**`dc_html` — there is no `theme/tokens.jsx`; the tokens are CSS custom properties under `_ds/<ds-id>/tokens/`, and they are the ONLY token source.** Do not treat the absent JSX theme as "no tokens." Resolve the `<helmet>` block's stylesheet hrefs rather than globbing a root `tokens/` dir:

```html
<helmet>
  <link rel="stylesheet" href="_ds/<ds-id>/tokens/fonts.css">
  <link rel="stylesheet" href="_ds/<ds-id>/tokens/colors.css">
  <link rel="stylesheet" href="_ds/<ds-id>/tokens/typography.css">
  <link rel="stylesheet" href="_ds/<ds-id>/tokens/spacing.css">
  <link rel="stylesheet" href="_ds/<ds-id>/styles.css">
</helmet>
```

Read each linked `tokens/*.css` with the Read tool and parse every `--name: value;` into `{design_tokens}` (same categorization table the BUNDLE path uses in BUNDLE.3). Also read the linked `styles.css` — on this shape it carries the resolved styling for `<x-import>` design-system components (Button and friends), which have no inline styles of their own; without it those components have no design-side values and their grid rows would compare against nothing. The `<helmet>` link set is authoritative for which files matter — a token file present on disk but not linked is not in play.

**ALSO read the bundle's FOUNDATIONAL token files — the `tokens/*.css` CSS custom properties — into `{design_foundation_tokens}`.** A Claude Design bundle keeps its *foundation* in CSS custom properties (`tokens/typography.css` → `--font-size-base: 0.8125rem`, `tokens/spacing.css` → `--control-h`, `--radius*`, `tokens/colors.css` → `--status-*`), NOT in the JSX theme object — so a JSX-theme-only read SILENTLY MISSES the type scale, and step-03 §2i / §2 property #2 then have no resolved design value for `var(--font-size-base)` and no-op (greening a 13px-vs-16px drift). `ls {design_dir}/tokens/*.css` (or `{design_dir}/../tokens/*.css`) on `legacy_jsx`; on `dc_html` these are the same `_ds/<ds-id>/tokens/*.css` files the `<helmet>` block links (resolved just above) — one read serves both `{design_tokens}` and `{design_foundation_tokens}`. Read each with the Read tool (not `cat`); extract the foundational subset — the **type scale** (`--font-size-base/-sm/-xs/-md`), **control heights** (`--control-h/-sm`), the **radius scale** (`--radius/-md/-lg`), and the **status-colour set** (`--status-*`) — resolving each `rem` to px. Store as `{design_foundation_tokens}` (a list of `{ token, value_px_or_hex, source_file }`). This is the design-side denominator for the §2i foundation-token reconciliation. If no `tokens/*.css` exists in the bundle, set `{design_foundation_tokens}` empty and note it — §2i will mark the foundation comparison `needs human confirmation` rather than silently skipping.

### URL.5. Catalog Every Component's CSS Properties (JSX inline styles + state-conditional branches)

For each component in `{design_components}`, extract **every inline style property** from the JSX source. For every `style={{ ... }}` block, record one property row.

**State detection on the URL path.** JSX bundles encode states three ways — catalog ALL of them, not just the default branch:

1. **Conditional style objects.** `style={{ ...base, ...(row.status === 'failed' && failedStyles) }}` → emit rows for BOTH branches: one with `state: default` containing the base styles, one with `state: failed` containing the merged base + override styles.
2. **Template-literal class joins.** `` className={`row ${hovered ? 'row-hover' : ''} ${selected ? 'row-selected' : ''}`} `` → look up the referenced class rules in the same component file or imported stylesheets; emit a row per (component, state, property) triple.
3. **Multiple JSX siblings demonstrating variants.** A component file that renders `<Row state="default" />`, `<Row state="failed" />`, `<Row state="empty" />` for documentation → catalog the styling each variant resolves to.

Add `{design_states}[ComponentName]` populated with every state observed (deduplicated). If only the default branch exists, record `[default]` and move on.

#### URL.5a. The editor-prop VARIANT axis (`dc_html`) — MANDATORY, and it is not the state axis

**A `.dc.html` bundle can carry more than one COMPLETE rendering of the same frame, selected by an editor prop with a default — and the state axis above does not reach them.** States are per-component and conditional on interaction (`hover`, `failed`, `empty`). A **variant** is per-*frame* and conditional on a design-time prop: two whole renderings of the surface, one of which is what you see by default and the other of which is invisible unless you go looking. Catalog only the default and the grid's design-side denominator silently loses everything the other variant contains — entire columns, summary strips, provenance lines, footnotes.

**This is not hypothetical.** A real bundle (`Inbound Feed.dc.html`, cash-recovery, 2026-07-20) declared:

```html
<script type="text/x-dc" data-dc-script data-props="{
  &quot;trackingEnrichment&quot;: {&quot;editor&quot;: &quot;boolean&quot;, &quot;default&quot;: false,
    &quot;section&quot;: &quot;Tracking enrichment (proposal, unbriefed)&quot;}
}">
```

driving `<sc-if value="{{ trackingOn }}">` / `<sc-if value="{{ trackingOff }}">` around a 7-column Arrival version of the feed and a 6-column version without it. **The default rendering was the one WITHOUT the capability — which was already shipped in production.** A default-only catalog would have handed step-03 a denominator missing a live column, licensing its deletion.

**Do this:**

1. **Parse the prop schema.** Read the `data-props` attribute on `<script type="text/x-dc" data-dc-script>` and HTML-unescape it (`&quot;` → `"`) into JSON. Each key is one variant dimension: `{ editor: "boolean" | "enum" | …, default: <value>, options: [...], section: "<label>" }`. Also read the script body's `renderVals()` — it maps raw props to the flag names `<sc-if>` actually tests (`trackingOn: tracking`, `trackingOff: !tracking`, `feeUnresolved: fee === "unresolved"`), which is how a single prop becomes two or more branches.
2. **Enumerate every `<sc-if>` branch — not just the ones the defaults select.** For each `<sc-if value="{{ flag }}">`, resolve `flag` back through `renderVals()` to the prop and the prop value that makes it true. A boolean prop yields 2 branches; an enum yields one per option (the real bundle's `feeResolution` had three: `unresolved` / `owner-facing` / `clerk-facing`).
3. **Catalog EVERY branch, not the default alone.** Every property row inside an `<sc-if>` gets a `variant` field alongside its `state` field — `variant: "trackingOn"` / `"trackingOff"` / `"feeOwner"`. Rows outside any `<sc-if>` are `variant: default` (unconditional, present in all renderings). The two axes are independent and compose: a row can be `state: hover, variant: trackingOn`. Populate `{design_variants}` as `[{ prop, flag, default_value, is_default_branch: bool, section_label, hides_capability: bool, frames_affected: [...] }]`.
4. **Flag a variant that HIDES a capability — this is the step-02b hand-off.** When a branch whose prop `default` is `false`/non-selected contains structure the default branch does not (an extra column, a summary/tally strip, an action, a provenance line, a whole section), set `hides_capability: true`. Because every branch's components and frames are folded into `{design_components}` / `{design_frame_inventory}` regardless of default, step-02b §2 inventories them as part of `{handoff_capabilities}` with no change to its own logic — **the regression-surface check stays independent of the grid, exactly as designed; this branch just stops starving it of input.** A capability that exists only in a non-default variant must never be silently excluded from the denominator.
5. **Carry `section` labels through as ANNOTATION, never as a deletion signal.** A `section` reading `"Tracking enrichment (proposal, unbriefed)"` is the design tool honestly flagging its own addition as outside the brief. That is provenance worth surfacing in the SHARED.2 summary and the step-04 §9 report — it is **not** licence to drop the variant, and it is **not** evidence the capability is unwanted. Treat "unbriefed" as "the brief needs revising," never as "the code should lose this."

`legacy_jsx` bundles have no `data-props` / `<sc-if>` machinery — record `{design_variants}` empty and skip this sub-step.

Property rows live in TWO places (write to both — they're the same data, different shapes):

1. **Embedded in `{design_components}`** — append to `{design_components}[name].properties` (a list of rows). This is the canonical store that step-03 reads from when iterating component-by-component for the comparison grid.
2. **Flat list in `{css_property_catalog}`** — append to the flat catalog for SHARED.1's non-empty verification and SHARED.2's count display.

Both writes use the same row shape (see §SHARED below). Every row includes a `state` field — `default` for the unconditional branch, `hover | focus | selected | failed | empty | disabled | <other>` for state-conditional rules — and, on `dc_html`, a `variant` field per URL.5a (`default` when the row sits outside every `<sc-if>`). The axes are orthogonal: `state` is interaction-conditional and per-component, `variant` is prop-conditional and per-frame.

Token references like `tokens.radius.lg` resolve to their numeric value (`4px`) via `{design_tokens}` and the resolved value is what gets recorded; preserve the token name in parentheses for traceability.

### URL.6. Near-empty-catalog guard — HALT rather than proceed on a plausible nothing

**A URL-path ingest that found essentially nothing is a shape misdetection, not a small design.** This is the failure mode the `.dc.html` branch exists to close, and it is dangerous precisely because it is *quiet*: every instruction "ran," none errored, and the resulting catalog looks like a clean read of a simple surface. SHARED.1 only catches a **completely** empty `{css_property_catalog}`; a partial no-op — say the inline styles parsed but no modules, no README, no tokens — sails past it and reaches step-03 as a denominator missing whole frames and variants.

Before continuing, check all three of:

- **zero traced component modules** (`legacy_jsx`: no `<script src>` module resolved; `dc_html`: no frame root / named section found in the target document), AND
- **zero README** (neither the root `README.md` nor `_ds/<ds-id>/readme.md` was read), AND
- **zero token files** (`{design_tokens}` empty — no `theme/tokens.jsx`, no `tokens/*.css`).

If **all three** hold, HALT — do NOT continue to §SHARED:

```
══════════════════════════════════════════════════════════════════
✗ design-implement halted — near-empty catalog after URL-path ingest.

  bundle_shape (URL.1c):  {bundle_shape}
  design_dir:             {design_dir}
  design_file:            {design_file}
  traced modules/frames:  0
  README:                 not found
  token files:            0

Ingest ran without error but resolved almost nothing. That is far more
likely a BUNDLE-SHAPE MISDETECTION than a genuinely empty design — most
often a `.dc.html` bundle ingested down the `legacy_jsx` branch (no root
README, no <script src> modules, no theme/tokens.jsx exist in that shape,
so every legacy read returns nothing).

Proceeding would hand step-03 a plausible-looking but structurally
incomplete denominator — missing frames, missing variants — which can
license DELETING shipped capability.

Next: re-check URL.1c shape detection against the actual bundle contents
(`ls {design_dir}` and the target file's root element), then re-run.
══════════════════════════════════════════════════════════════════
```

The conjunction is deliberate — requiring **all three** keeps the guard quiet for a genuinely minimal-but-valid bundle (e.g. one that legitimately has no README but does resolve components and tokens). Two of three is a warn worth stating in SHARED.2, not a halt.

### URL.7. Skip to §SHARED

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
  bundle shape:           {bundle_shape}   ← URL.1c: legacy_jsx | dc_html. Misdetection is the silent-no-op failure; a dc_html target reported as legacy_jsx is wrong.
  frames declared:        {len(design_frame_inventory)} — {comma-separated frame names, e.g. "Orders(primary), supply-order-detail-drawer, warehouse-lookup, inbound-batch-lookup, import-run-lookup, accounting-outcome-lookup, catalog-record-drawer, supply-source-lookup"}
  of which §13 lookups:   {count of role == "§13-lookup"} ← step-03 §2f checks each is built in the impl (no brief, so the bundle IS the frame contract)
  linked-records rows:    {len(design_linked_record_rows)} drawn in the detail drawer — {comma-separated labels} (the AUTHORITATIVE lookup denominator; §13-lookup frames must equal-or-exceed this){if any row has no matching §13-lookup frame: " ⚠ {n} UNDER-ENUMERATED → re-traced / flagged for §2f"}
{end if}
  token categories:       {comma-separated unique categories}
  tokens cataloged:       {len(design_tokens)}
  CSS properties:         {len(css_property_catalog)}
  states cataloged:       {sum(len(states) for states in design_states.values())} across {len(design_states)} components
  state breakdown:        {comma-separated unique states observed, e.g., "default(12), hover(4), focus(2), failed(3), empty(1)"}
{if bundle_shape == "dc_html":}
  variants cataloged:     {len(design_variants)} across {count of distinct props} editor prop(s) — {e.g. "trackingOn/trackingOff (trackingEnrichment), feeUnresolved/feeOwner/feeClerk (feeResolution)"}
  default-branch:         {the variant(s) the prop defaults select, e.g. "trackingOff, feeUnresolved"}
{if any(v.hides_capability for v in design_variants):}
  ⚠ capability-hiding variant: {list} — a NON-default branch contains structure the default lacks. Folded into {design_components}/{design_frame_inventory} so step-02b §2 inventories it as handoff capability; NEVER excluded from the denominator. (URL.5a step 4)
{end if}
{if any(v.section_label matches /proposal|unbriefed/i for v in design_variants):}
  ⓘ variant provenance:   {list with section labels} — the design tool flagged these as outside the brief. ANNOTATION carried to the §9 report; NOT a deletion signal. Read as "the brief needs revising," never "the code should lose this." (URL.5a step 5)
{end if}
{end if}
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
- `{bundle_shape}` resolved (URL.1c) and reported in the SHARED.2 summary. A `.dc.html` target was NOT ingested down the `legacy_jsx` branch.
- README read and chat transcripts consulted (if referenced) — from the root `README.md` (`legacy_jsx`) or `_ds/<ds-id>/readme.md` (`dc_html`); its absence was never treated as "no layout constraint."
- All imported files traced and read (`legacy_jsx`), or the self-contained frame document read in full and its frame roots / named sections / `<x-import>` components cataloged (`dc_html`).
- **`{design_variants}` populated on a `dc_html` run (URL.5a)** — the `data-props` schema parsed, EVERY `<sc-if>` branch enumerated (not only the ones the defaults select), and every property row tagged with a `variant` alongside its `state`. Any non-default branch containing structure the default lacks is flagged `hides_capability: true` and its components/frames folded into `{design_components}` / `{design_frame_inventory}` so step-02b §2 inventories it — never excluded from the denominator. `section` labels reading "proposal"/"unbriefed" carried through as annotation, never actioned as deletion.
- The near-empty-catalog guard (URL.6) either passed or HALTED — the run never continued past a zero-modules AND zero-README AND zero-tokens ingest.
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
- **Bundle-SHAPE blindness — the silent-no-op leak (URL.1c).** Ingesting a `.dc.html` bundle down the `legacy_jsx` branch. Nothing errors: `cat README.md` finds nothing, the `<script src>` trace finds nothing (only `support.js` and the design-system bundle), `theme/tokens.jsx` does not exist, and there are no `/* ==== frame ==== */` banners. Every instruction "ran" and the catalog comes back near-empty but *plausible* — which is worse than a crash, because step-03 then grids against a denominator missing whole frames and whole variants. The tell is a run reporting `bundle shape: legacy_jsx` on a target whose name ends `.dc.html`, or a suspiciously tiny component/token count on a visibly rich design. URL.6's guard is the backstop, but detection at URL.1c is the fix.
- **Variant-axis blindness — the capability-deleting leak (URL.5a).** Cataloging only the rendering the editor-prop defaults select. This is the state-axis failure one level up: states are per-component and interaction-conditional; **variants are per-frame and prop-conditional**, and a `default: false` prop can hide an entire alternative rendering — extra columns, a tally strip, a provenance line, whole sections. The real instance (`Inbound Feed.dc.html`, 2026-07-20) defaulted `trackingEnrichment` to `false`, so the default rendering was the 6-column feed WITHOUT the Arrival axis that was already shipped in production; a default-only catalog would have handed step-03 a denominator missing a live column and licensed deleting it. step-02b's regression check is the safety net that catches this — but it can only catch what the ingest gives it, so starving it by cataloging one branch is how the net gets bypassed. Enumerate every `<sc-if>` branch; never let the prop default decide what enters the denominator.
- **Reading an "unbriefed"/"proposal" variant label as permission to drop the capability.** A `section` label like `"Tracking enrichment (proposal, unbriefed)"` is the design tool being *honest* that its addition is not yet in the brief. It is provenance, not a verdict. Treating it as "the design says this isn't wanted" inverts it — the correct reading is "the brief needs revising to catch up with what shipped." Carry it to the §9 report as annotation; never let it justify removing structure the implementation already has.
- **State-axis blindness — the dominant leak mode.** Cataloging only inline `style="…"` and ignoring `<style>` blocks, `data-state` sibling variants, or JSX conditional style branches. The default-state catalog will look complete; the bundle's hover/focus/failed/empty/disabled rules will silently bypass the grid and ship as deltas in production. The 2026-05-28 fork retro (PR #827) was caused by exactly this — failed-row tint, failed-row hover, null-supplier styling, and null-total styling were all state-conditional and absent from the cataloged rows. If you finish ingestion with `{design_states}` showing only `[default]` for an interactive component (row, button, input, action cell), that is the signal that this failure mode is in play — re-audit `<style>` blocks before proceeding to step-02.
