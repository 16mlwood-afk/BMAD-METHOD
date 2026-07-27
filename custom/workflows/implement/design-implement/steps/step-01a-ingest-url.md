---
name: 'step-01a-ingest-url'
description: 'URL PATH of step-01 ingest: acquire a Claude Design bundle (legacy tar or DesignSync project), resolve its SHAPE (legacy_jsx vs dc_html), then catalog the frame inventory, tokens, states and editor-prop variants. Entered only when input_kind == claude_design_url; converges on step-01 §SHARED.'
---

# Step 1a: Ingest — URL PATH

**Entered from `step-01-ingest-design.md` §INPUT-KIND BRANCH when `{input_kind} == "claude_design_url"`.** Do not run this file on any other input kind. On completion, return to **`step-01-ingest-design.md` §SHARED** — that is where the catalog is verified and the summary is emitted.

**Section ids here are `URL.*`, and step-01's `SHARED` / SUCCESS METRICS / FAILURE MODES cite them by that name** (see the router's citation legend). Renaming one means updating those citations.

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
> **HONEST LIMIT — this is opportunistic, NOT a guarantee (verified negative 2026-07-27).** The step above only helps when the harness *chooses* to persist the tool result, and that threshold sits **above normal frame-module size**. On a real run (cash-recovery, project `f93d6a81`) it fired for **zero of eleven files** — every `get_file` returned inline, including a ~26KB JSX module and an ~18KB data module — so mirroring cost the **full 2× context round-trip per file** (read inline, then re-emit through `Write`) for ~112KB of source. Do not plan a run on the assumption that mirroring is free, and do not report it as O(1) when it wasn't: on the URL path, content entering the orchestrator context is **unavoidable today**, because the MCP is only reachable from the agent's own tool interface — no script can fetch it on your behalf.
>
> **What DOES reduce the cost, and is prescribed:**
> - **Mirror only what the fan-out must READ as files** — the target frame and its traced modules. Frame agents need those on disk because the MCP is unreachable from a sub-agent context (gap 510).
> - **For token and design-system files, mirror a RESOLVED DIGEST instead of the raw files.** Read `tokens/*.css` and the component sources once, then write ONE reference file (resolved `var(--…)` → concrete values, plus each shared component's resolved property rows) and point every frame agent at that. It is far smaller than the sources, it removes per-agent token-resolution work, and it is what the agents actually need. Verified effective on the 2026-07-27 run: eight design-system components collapsed into one compact reference.
> - **Budget for the mirror explicitly** before starting: if the target + its modules will not fit comfortably, that is a reason to reconsider scope, not something the workaround absorbs.
>
> It remains a **fork-side workaround**, formalized here so it isn't rediscovered per session — the clean upstream fix is the follow-up noted under step 4, and it is the only thing that would make this genuinely O(1).
>
> **Knock-on to be aware of:** because the mirror may put the whole bundle in the orchestrator context anyway, `design-ingest` step-02's fan-out can lose its context rationale before it even starts — which is exactly what made orchestrator-inline enumeration look acceptable when that fan-out later collapsed. Do not let a spent context budget silently license abandoning the fan-out; that decision is owner-gated (`FG-2026-07-27-05`).
4. `{design_file}` is the decoded path from step 0. If it was unset, default to the project's primary HTML frame per `readme.md`.

> **Upstream follow-up (the clean fix — not for this workflow to build).** The persist-to-disk dance in step 3 exists only because DesignSync `get_file` returns content into context. The proper fix is in the MCP itself: give `get_file` a `localPath` sink symmetric with `write_files` (read straight to disk, content never returned to the caller). That would retire the tool-results workaround above. Tracked as a DesignSync gap.

The fetch mechanism is mechanism-agnostic from here — URL.2 (README) through URL.7 run identically once `{design_dir}` holds the files. What is NOT agnostic is the bundle's **shape**; resolve that next (URL.1c) before anything reads a path.

### URL.1b-i. Early supersede probe — refuse a dead design BEFORE spending the catalog

**The supersede gate at §SHARED.1a is correct but, on the URL path, it fires LAST — after URL.2–URL.5 have mirrored, shape-branched, size-checked and re-catalogued the entire bundle.** So the run pays its most expensive phase to learn something the target file states in its first few hundred bytes, and the second-order cost is worse: URL.1d can advise a full `design-ingest` run on a design that is about to be refused. Probe here instead. It costs **zero extra calls** — the target fetch already happened.

Applies to both fetch mechanisms (URL.1a tar and URL.1b DesignSync) as soon as the target file exists under `{design_dir}`, and runs BEFORE URL.1c shape detection and URL.1d size preflight.

1. **Scan the target's first ~4KB for a `design-brief-*` token** (the handoff filename Claude Design carries into the bundle header/README front-matter):

   ```bash
   head -c 4096 "{design_dir}/{design_file}" | grep -o 'design-brief-[a-z0-9-]*' | head -1
   ```

2. **Token found** → resolve `{target_slug}` from it and run the §SHARED.1a supersede branch **right here**, with its exact semantics and its exact halt wording (`active` → continue · `superseded` → surface `{superseded_by}` and HALT before any catalog work · `no_brief` / `ambiguous` → warn and continue). Record that the resolution happened early so §SHARED.1a does not redo it.
3. **No token** → **behaviour is unchanged.** Legacy JSX bundles and hand-authored designs carry no brief token; fall through and let §SHARED.1a resolve from `{design_frame_inventory}` exactly as today.

**This probe is an early exit, never a new refusal path.** It can only halt a run that §SHARED.1a would have halted anyway — it just halts it before the spend instead of after. A probe that finds nothing must never escalate to a refusal; absence of a token is `no_brief`, not a failure. (Sibling checked 2026-07-25: `design-ingest` step-01 already resolves `{handoff_supersede_status}` in step-01, before its per-frame fan-out, so it does not have this inversion.)

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

