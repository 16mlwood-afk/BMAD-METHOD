---
name: design-implement
description: 'Implement a Claude Design artifact with pixel-level precision. Fetches the design bundle, reads every CSS value, builds a component-by-component comparison grid against the existing implementation, then fixes all deltas.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Design Implement Workflow

**Goal:** Take a Claude Design artifact URL and bring the codebase into pixel-perfect alignment with the design — measured by an exhaustive **component × state × property** comparison grid plus an **implementation-multiplicity** cross-check, not by eyeballing. The state axis (default, hover, focus, selected, failed, empty, disabled, …) is part of the contract: a state-conditional rule in the design that has no matching grid row leaks to production. The multiplicity axis is the other half: a primitive (status pill, chip, money cell) is often implemented more than once, and the drift that ships is usually *between two implementations of the same primitive* — so every render site is enumerated and the implementations are checked against each other (step-03 §2a), not just against the design.

**Your Role:** You are a pixel-precision engineer. You do not design — you enforce. The Claude Design artifact is the authoritative specification. Your job is to extract every CSS value from the design source — **inline styles, `<style>`-block rules, and `data-state` variants alike** — compare it against the implementation, enumerate every delta, and fix all of them. A delta that slips through is a failure, including state-conditional rules (failed-row tint, hover behavior, null-data styling) that don't appear in the default rendering.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All 4 steps are FULLY AUTONOMOUS — no user interaction after invocation
- State persists via variables (see below)
- Sequential progression: ingest design → map implementation → **capability-delta preflight (step-02b: handoff vs production, BOTH ways — DROPPED → strategy halt, ADDED/DEEPENED → build plan; §4e commit-boundary pass on a consequential surface)** → build grid → apply and deliver

### State Variables

- `{input_kind}` — `claude_design_url` | `synthesize_bundle` | `ingest_manifest`. Determines whether step 1 fetches a URL, reads a local bundle directory, or reads a pre-built `design-ingest` manifest (and skips re-ingest entirely).
- `{design_url}` — Claude Design artifact URL (when `{input_kind} == "claude_design_url"`)
- `{bundle_dir}` — Absolute path to a local design-synthesize bundle directory (when `{input_kind} == "synthesize_bundle"`)
- `{bundle_manifest}` — Parsed `bundle/manifest.yaml` contents (when `{input_kind} == "synthesize_bundle"`)
- `{ingest_manifest_path}` — Absolute path to a `design-ingest-*.md` manifest (when `{input_kind} == "ingest_manifest"`). Produced by the `design-ingest` workflow; carries the frame inventory + the gated per-frame section inventory + a pre-seeded grid scaffold (every (frame, section) already a row), so step 1 reads it instead of downloading/extracting and re-cataloging a large bundle in one context.
- `{ingest_manifest}` — Parsed contents of `{ingest_manifest_path}` (when `{input_kind} == "ingest_manifest"`): the `ingest:` receipt, frame inventory, section inventory, and grid scaffold rows.
- `{section_rows_source}` — `ingest_manifest` | `in_context`. Records whether the per-frame **section-coverage** rows (step-03 §2f-bis) came from a gated, reviewed `design-ingest` scaffold or were enumerated in-context on a URL/bundle run. Set in step-01 (MANIFEST.3 → `ingest_manifest`; URL/BUNDLE paths → `in_context`).
- `{frame_scope}` — OPTIONAL (ingest_manifest runs only). A comma-separated frame-id list (or single frame id) restricting THIS pass to those frames; rows in other frames are pre-disposed `⊘ deferred(out-of-scope: not in {frame_scope})`. Absent ⇒ all not-yet-applied in-scope rows. Parsed from a trailing input token in Input Resolution. This is the EXPLICIT slice lever; the self-checkpoint below is the automatic one — you do not need `{frame_scope}` for safe large-manifest runs, only when you want to target a specific frame.
- `{resume_prior_dispositions}` — (ingest_manifest runs only) the map of (frame, section) → disposition read from the manifest's grid scaffold at run start. Rows already `✓ applied` in the manifest are carried forward as `✓ applied (prior pass)` and NOT re-applied — this is what makes re-invoking the SAME command in a fresh session auto-resume. Computed in Input Resolution (manifest gating); honored by step-04 §5.
- `{target_slug}` — Kebab-case identifier for the target surface. On the manifest path it is `{ingest_manifest}.ingest.target_slug`; on the URL/bundle paths it is derived in step-01 §SHARED.1a from the primary frame (same slug semantics as `brief-revision-policy.md` Block A). Keys the supersede resolution.
- `{prior_ingest_manifest}` — (URL/bundle runs) the path of an EXISTING `design-ingest-*{target_slug}*.md` manifest for this same surface, or `none`. Resolved in step-01 §SHARED.1a-iii by globbing `{implementation_artifacts}` on the slug already computed for the supersede check. A hit means earlier passes have an apply ledger this run would otherwise be blind to — including items flagged **"NOT applied (intent, not treatment)"**, which are prior DECISIONS, not unfinished work. Warn/disclose only, never a gate; when set, step-04 §5 appends this run's pass to THAT manifest under `docs/manifest-contract.md` instead of minting a parallel grid artifact.
- `{handoff_supersede_status}` — `active` | `superseded` | `no_brief` | `ambiguous`. Resolved on EVERY path: the manifest path reads `{ingest_manifest}.ingest.supersede_status` at intake (stamped by `design-ingest`; absent ⇒ `no_brief`); the URL/bundle paths resolve it INDEPENDENTLY in step-01 §SHARED.1a by matching `{target_slug}` against briefs in `{implementation_artifacts}`, mirroring `design-ingest` step-01 §5 — so a handoff handed straight to `design-implement` (no ingest in front) still copes. Symmetric tolerance — never a hard refuse. `brief-revision-policy.md` §8.
- `{prior_halt}` — `null` when no earlier run halted on this design source, else `{ artifact, date, session, outcome, blocked_on, baseline_commit, commits_since_on_blocking_paths }` read from a matching `design-implement-preflight-*.md`. Resolved in Input Resolution's **Prior-halt recall** — the cheapest intake check, so it runs FIRST (it keys on the raw input string, needing no `{target_slug}`, fetch, or bundle). **SURFACED, never gated on**; carried into the §SHARED.2 summary and the §9 report so the run states whether it re-derived a verdict that already existed. A missing/malformed artifact is a silent no-op.
- `{prior_applied}` — `none`, or `{ verdict, commit, subject, deployed: bool|unknown, evidence }` — whether this design has ALREADY been applied to the implementation. Resolved in step-02b **§3b Already-shipped recall** (post-map / pre-grid, because it needs step-02's impl paths + §3's delta; it cannot be a cheap intake probe). Two signals already in hand: **git provenance** on the impl paths, and whether §3's capability delta is all-empty. Three verdicts — `already-shipped` (both) · `prior-pass-residual-deltas` (provenance, delta remains — the valuable case, the run continues as a RESIDUAL-DELTA pass) · `matches-no-provenance` (delta empty, no traceable commit). **SURFACED, never gated on** — a verification re-run is legitimate, and blocking one is the failure mode to avoid. Drives the §9 report's framing: on either provenance verdict the report must open by naming the prior commit and calling this a verification pass, never claim authorship of already-shipped work. An all-empty *capability* delta is NOT a green *grid* — never phrase it as "the implementation matches the design."
- `{superseded_by}` — the active successor brief filename, set when `{handoff_supersede_status} == superseded` (manifest: `ingest.superseded_by`; URL/bundle: the matched brief's `superseded_by`). Named to the user in the supersede surface/halt.
- `{bundle_conformance}` — `pass` | `UNVERIFIED(<reason>)` | `halted(<reasons>)` | `warn(composition)`. The bundle→brief structural conformance verdict set in step-01 §SHARED.1b: does the design PROPOSAL cover the brief CONTRACT (every `frames` id drawn / `shell_role` honored / a non-default `composition` job-loop expressed, not a hero). A `halted(...)` exits BEFORE the apply pipeline ("proposal only; needs revision"); `UNVERIFIED` (no brief, or a brief predating the field) and `warn(composition)` proceed but are disclosed in the SHARED.2 summary and carried to the §9 report. The brief-side conformance gate; complements step-03 §2f's impl-side frame coverage and §2d's impl-side shell check.
- `{run_completion_mode}` — `complete` (every in-scope row reached a terminal disposition this pass) | `checkpointed` (the pass stopped at a frame boundary with in-scope rows still UNVERIFIED, to stay inside the context budget — see the resumable-apply Critical Rule). Set in step-04; drives the §9 report's done-vs-resume framing.
- `{design_file}` — Target design file name (e.g., `Data Quality Dashboard.html`)
- `{design_dir}` — Extracted bundle directory on disk
- `{design_components}` — Map of component name → file path within the extracted bundle
- `{design_tokens}` — Design system tokens (radii, type scale, colors, spacing)
- `{impl_page}` — Path to the SvelteKit/React/Vue page component in the codebase
- `{impl_components}` — Map of component name → file path in the project
- `{impl_config}` — Tailwind/CSS config path and key overrides (border-radius, colors, etc.)
- `{design_layout_constraints}` — Page-shell / container assertions the bundle cannot express as a component CSS value: the README's layout prose ("full-width within the content container", "never a centered max-width card", "no sidebar shell") PLUS the bundle wrapper's own width treatment (`.app` / `<body>` full-bleed vs. an explicit `max-width` + centering). Cataloged in step-01 (URL.2 README prose + the wrapper element). This is the evidence the page-shell grid row (step-03 §2d) compares against — the one structural property that lives in prose + the wrapper, not in any cataloged component.
- `{impl_page_shell}` — The implementation's EFFECTIVE container treatment for `{impl_page}`: the chain of width caps from the page wrapper UP THROUGH every ancestor layout (route layout, app shell) — each `max-width` / `mx-auto` / `padding` resolved to a concrete px value, and the tightest effective width computed (e.g. layout `max-w-[1440px]` + page `max-width:1280px` → effective 1280, centered). Also carries `injected_chrome` — any hero/banner/masthead/promo band an ancestor layout renders ABOVE `{children}` that the design's standalone frame doesn't contain (the `/settings/sku-format` hero-banner miss), each flagged `in_design_frame: bool`. Cataloged in step-02 §1a; both the width and the injected-chrome rows are emitted by step-03 §2d.
- `{frame_composition_deltas}` — List of DRILLED frames (detail/create/§13-lookup) that are materially **recomposed** between design and impl — sections renamed, regrouped, reordered, or header/footer chrome changed — even when capabilities are unchanged. Each `{ frame, renamed_groups[], reordered, regrouped[], chrome_delta }`. Computed in step-02b §3 (compared from the manifest section inventory / frame source vs the impl frame map); each entry MUST become a Frame-composition grid row in step-03 §2d-bis. This is the drawer analog of `{impl_page_shell}` — the arrangement axis no single component owns.
- `{design_states}` — Map of component name → list of states cataloged (e.g., `ExpenseRow → [default, hover, selected, failed, empty]`). A component with only `[default]` is the implicit baseline; any other state must be explicitly populated from the design source.
- `{bundle_shape}` — `legacy_jsx` | `dc_html`. Which SHAPE of Claude Design bundle the URL path is reading, resolved in step-01 **URL.1c** before any path is read (target ends `.dc.html`, or `support.js` present, or an `<x-dc>` root ⇒ `dc_html`). The legacy shape has a root `README.md`, `<script type="text/babel">` module imports and `theme/tokens.jsx`; the `.dc.html` shape has none of those — it is one self-contained frame document plus `_ds/<ds-id>/`. Misdetecting it makes URL.2–URL.5 silently find nothing and yield a near-empty-but-plausible catalog (URL.6's guard is the backstop). Reported in the SHARED.2 summary. URL path only; unset on the bundle/manifest paths.
- `{design_variants}` — (`dc_html` only) The **editor-prop variant axis** — whole-frame alternative renderings selected by a design-time prop, orthogonal to `{design_states}`. Each `{ prop, flag, default_value, is_default_branch, section_label, hides_capability, frames_affected[] }`. Cataloged in step-01 **URL.5a** by parsing the `data-props` JSON on `<script type="text/x-dc" data-dc-script>` and enumerating EVERY `<sc-if>` branch — not only the ones the defaults select. Every property row carries a `variant` field alongside `state`. A branch whose prop defaults to false/non-selected but contains structure the default branch lacks is flagged `hides_capability: true`; because all branches' components and frames are folded into `{design_components}` / `{design_frame_inventory}` regardless of default, **step-02b §2 inventories them as `{handoff_capabilities}` with no change to its own logic** — the regression-surface check stays independent of the grid and is simply no longer starved of input. A `section_label` reading "proposal"/"unbriefed" is design-tool provenance carried to the §9 report as annotation, never actioned as a deletion signal.
- `{design_frame_inventory}` — **URL path**: the frames the target surface declares it delivers or consumes — the primary frame, the drilled detail drawer, and each **§13 expand-in-context lookup** (the "link to records (lookups)" the design viewer lists). Derived in step-01 **URL.3a** from the traced `<script src>` modules + their "… frames/lookups consumed" comments, the per-frame banners inside those modules (`/* ==== warehouse-lookup ==== */`), the lookup→target maps in the bundle data (`app.jsx` `catalog: [… "Catalog Items.html"]`), and sibling standalone `<frame>.html` the target links to. This is step-03 §2f's frame-coverage **denominator on a raw-URL run**, where no brief §7 and no manifest exist. (Brief-driven and synthesize-bundle runs use the brief §7 / manifest instead.) Each entry: `{ frame, role: primary|drilled-detail|§13-lookup, parent, declared_in, drawn }`.
- `{design_linked_record_rows}` — The **authoritative §13-lookup denominator**: the rows the detail drawer renders in its "Linked records" / "link to records" section (each `RecordLink` — e.g. `Catalog item`, `Route warehouse`, `Shipping lane`, `Supply source`, `Inbound batch`, `Import run`). Each `{ label, drills_to_frame, order }`. Cataloged in step-01 URL.3a (source 5) by opening the detail drawer and counting its rendered linked-record rows — NOT from a comment/banner/map, which can under-enumerate. step-03 §2f reconciles `{design_frame_inventory}`'s §13-lookup frames against this list: every row must have a frame (else `LOOKUP UNDER-ENUMERATED`), and the §13-lookup count must equal-or-exceed the row count. This is the fix for "design-implement often misses the link-to-record drawers."
- `{impl_identifier_cells}` — Sub-list of `{impl_render_sites}` whose displayed text is `value_source: formatter | enum-map` AND a canonical-identifier class (marketplace, supplier, ASIN/SKU, order/batch number, currency, date, status label). Cataloged in step-02 §3d; these are the cells the grid cannot certify from a mock-data bundle and routes to the content lane (step-03 §2c).
- `{comparison_grid}` — The full component × state × property delta table
- `{delta_count}` — Number of (component, state, property) triples with non-zero deltas
- `{content_unverified_count}` — Number of `content-lane: CONTENT-LANE-UNVERIFIED` rows (step-03 §2c) — formatter-driven identifier cells routed to design-review / design-tuning, counted separately from `{delta_count}` (they are routed items, not deltas applied here).
- `{impl_token_provenance}` — List of every design-mapped CSS custom property with its resolved value AND provenance: `{ token, resolved_value, source_file, scope: canonical | per-screen, semantic_class: shared-semantic | local-constant }`. Cataloged in step-02 §5. `canonical` = defined in `tokens.css` / `globals.css @theme` (the `docs/design-policy.md` §8 ground-truth surface); `per-screen` = resolvable only from a per-screen stylesheet (migration debt, not a system token).
- `{token_noncanonical_count}` — Number of `token-provenance: NON-CANONICAL TOKEN` rows (step-03 §2g) — shared-semantic tokens (status / colour / type) that resolve only from a per-screen stylesheet, disclosed and ceded to design-review (promote-or-leave is token architecture), counted separately from `{delta_count}` and never gated.
- `{design_foundation_tokens}` — The design SYSTEM's foundational token values resolved to px/hex: the **type scale** (`--font-size-base/-sm/-xs/-md`), **control heights** (`--control-h/-sm`), the **radius scale** (`--radius/-md/-lg`), and the **status-colour set** (`--status-*`). On the URL path these live in the bundle's `tokens/*.css` CSS custom properties — step-01 URL.4 reads them, NOT just the JSX theme object; on the bundle path they are the foundational subset of the parsed `tokens.css`. The design-side denominator for the §2i foundation-token reconciliation — absent it, the type-scale comparison silently no-ops on the URL path (the same missing-source-on-one-path failure §2f closes for frame inventory).
- `{app_canonical_scale}` — The app's foundational tokens AND the values the policy declares for them: a list of `{ token, app_value, policy_declared_value, policy_ref, dead_fallback_sites[] }`. Cataloged in step-02 §5a from the canonical surface (`src/styles/tokens.css` + `globals.css @theme`, `docs/design-policy.md` §8) and the policy's declared scale (`docs/design-policy.md` §4). The impl + spec side of §2i.
- `{foundation_token_drift}` — Foundational tokens where the design-system value, the policy-declared value, and the app's canonical value do not all agree. Each `{ token, design_value, policy_value, app_value, source_file, kind: app-violates-policy | design-vs-app }`. Computed in step-03 §2i; ROUTED to `apply-design-policy-change` (a single-source token migration), never patched in-component.
- `{foundation_token_drift_count}` — Number of `{foundation_token_drift}` rows (step-03 §2i) — disclosure items routed to the token-migration owner, counted separately from `{delta_count}` and never patched here or encoded as a dead `var(--token, <literal>)` fallback.
- `{production_capabilities}` — Feature-level inventory of what the CURRENT built page does/shows (routing & sub-surfaces, §13 linked-record lookups, economics/cost-recon, composite status/header, activity/audit, bulk actions/filters, action-wired mutations) — distinct from CSS. Cataloged in step-02b §1 from step-02's outputs.
- `{handoff_capabilities}` — The same feature-level inventory for what the HANDOFF delivers (`{design_components}` + `{design_frame_inventory}` + brief §7). Cataloged in step-02b §2.
- `{dropped_capabilities}` — The regression surface: capabilities in `{production_capabilities}` with no match in `{handoff_capabilities}` — what the redesign would remove. Each `{ capability, class, prod_evidence, why_it_matters, handoff_status: absent|unclear }`. Computed in step-02b §3; a non-empty set HALTS for a strategy choice.
- `{added_capabilities}` — The net-new half of the uplift surface: capabilities in `{handoff_capabilities}` with no production match (a new analytics/disposition band, lane-by-handler segmentation, an action column, co-view tabs, a drawer the live page never had). Computed in step-02b §3; NOT "informational" — each is a build task.
- `{deepened_capabilities}` — Capabilities present in BOTH but materially richer in the handoff (a country-filter → handler-lane segmentation with counts; a flat status column → a disposition band with a verdict vocabulary + per-row action). Each `{ capability, class, prod_evidence, evidence, why_it_matters }`. Computed in step-02b §3; a build task, never "same component, restyle."
- `{uplift_capabilities}` — `{added_capabilities}` ∪ `{deepened_capabilities}` — the net-new construction surface; the symmetric twin of `{dropped_capabilities}`. A non-empty set means the job is substantially a BUILD (strategy ≥ `additive`), regardless of how clean the token mapping looks. Carried into step-03 §2h (`capability-build` tags) and step-04 (constructed; §9 enumerates each `built:`). Computed in step-02b §3–§4b.
- `{commit_boundary_trigger}` — `n/a` | the list of signal classes that fired (`outward-write` · `durable-mutation` · `approval` · `binding-merge` · `retry` · `pre-commit-evidence-review`). Set in step-02b §4e. A surface with no consequential interaction records `n/a` and the pass skips — that is the common case, and the skip is stated rather than silent. `pre-commit-evidence-review` alone never fires the pass (a read-only review surface).
- `{commit_boundary_contract}` — (only when `{commit_boundary_trigger}` ≠ `n/a`) the nine lifecycle determinations behind the surface's irreversible write: `durable_object` · `states` · `transitions` · `evidence_snapshot` · `freshness` · `preconditions` · `outcomes` (success / failure / **unknown-external**) · `idempotency` · `commit_control` (exactly one). Persisted as a `commit_boundary:` block in the §4d preflight artifact on a halt, else in the grid artifact header — no new artifact. Field presence is checkable: `node ~/bmad-method-v6/tools/check-commit-boundary.js --check <artifact>`.
- `{commit_boundary_gaps}` — the determinations that could NOT be resolved from the design + brief + implementation, plus any second control that reaches the same irreversible write. Non-empty ⇒ step-02b §4e HALTS (autonomous mode included) and its remedy — the smallest stateful flow, mapped to named frames/sections — enters `{added_capabilities}` as build tasks. Empty ⇒ the design already models the boundary; record and proceed.
- `{implementation_strategy}` — How the handoff is applied: `restyle-only` (treatment only, keep all capabilities) | `additive` (new structure + retain dropped capabilities) | `partial` (per-capability keep/drop) | `replacement` (handoff wholesale, dropped capabilities removed). Chosen by the user at step-02b §4 (autonomous mode defaults to the non-destructive `restyle-only` and discloses — intent autonomy is out of scope).
- `{capability_dispositions}` — Per-capability `keep | drop` map derived from `{implementation_strategy}` (restyle-only/additive ⇒ all keep; replacement ⇒ all drop; partial ⇒ the user's per-item choice). Constrains step-03 (kept capabilities flagged protected) and step-04 (apply honors keep/drop; §9 states the strategy + every kept/dropped capability).
- `{baseline_commit}` — Git SHA before any changes

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order — no skipping, no optimizing
3. **ALL STEPS ARE AUTONOMOUS**: Never halt, never present menus, never wait for input
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **The design artifact is the single source of truth.** If the design says `border-radius: 4px` and the implementation says `rounded-lg` (which maps to `10px`), the implementation is wrong — full stop.
- **You are TRANSCRIBING, not designing — and that covers COPY and CHROME, not just CSS.** Every literal string the design renders (group titles, button/link labels, sub-captions, breadcrumb and footer copy, FX/units phrasing) and every structural element of the frame wrapper (the drawer/page header, the `‹ Back to …` breadcrumb, the footer, the close affordance) is reproduced **verbatim**. The failures that ship are small "I'll improve this" substitutions — each individually defensible, collectively a worse product: relabeling "Open full cost record" → "Open full order", paraphrasing "deferred import" → "import", swapping "EUR → GBP" → "€ → £", or dropping the breadcrumb because the sibling drawers use a plainer header. You have **no license** to do any of these. A deviation is allowed ONLY when it is *forced* (e.g. the design links to a record route that does not exist) AND it is written into the apply ledger as a logged deviation with its reason (step-04 §5b). Forced-and-logged is fine; silent relabel / paraphrase / omit / "tidy up" is the prohibited move — the copy-and-chrome twin of the holistic-rebuild shortcut the apply ledger already forbids.
- **The grid certifies CSS treatment — it is necessary, NOT sufficient. A green grid is not "done."** The component × state × property grid measures radius / colour / spacing / type on cataloged components. It is structurally blind to copy and to frame chrome — neither is a CSS-property cell — so "every cell matches" manufactures false confidence while the header, breadcrumb, footer, and wording silently drift. **The honest done-check was never the green grid; it is your rendered surface placed beside the design render** (the bundle is runnable HTML; a synthesize bundle ships a screenshot; a handoff run has the design image). Do that comparison before declaring done (step-04 §5b). This does not contradict "read source, not screenshots" below: that rule governs *reading exact values during ingest* (a screenshot can't give you `4px`); it does NOT govern *verification*, where rendering to compare is required, not forbidden.
- **Read the design source code, not screenshots — for VALUES, during ingest.** JSX inline styles and token files contain exact values; screenshots lose precision, so never measure pixels off an image. (Verification at the END is the exception — per the rule above, there you DO render the built surface and compare it against the design render.)
- **Check Tailwind config overrides.** A class like `rounded-sm` doesn't mean 2px — it means whatever the project's `tailwind.config.js` maps it to. Always resolve through the config.
- **Enumerate exhaustively along all three axes — component, state, property.** Every CSS property on every (component, state) pair. The value of this workflow is that nothing slips through. Sampling is failure. Cataloging only the default-state rendering is silent failure: hover, focus, selected, failed, empty, and disabled rules in the design that have no grid row will ship as deltas.
- **The page shell is a mandatory grid row, even though no component owns it.** The single property the component × state × property grid structurally cannot see is the **page container's own width / centering / padding** — because (a) it belongs to the page wrapper and its ancestor layout, not to any cataloged *component*, and (b) the design bundle renders its root `.app` / `<body>` **full-bleed and standalone**, so there is no outer container in the bundle to diff against. The design's intent lives instead in the project's `docs/design-policy.md` ("Operational pages are table-first and full-width within the content container"), echoed by the generated README and the full-bleed wrapper — none of which the component sweep reads. This is the inbound-flow `/orders` miss (PR #2017): the page nested an inner `max-width:1280px` centered cap inside the layout's `max-w-[1440px]`, rendering narrow + centered while the policy said full-width — and every component CSS value matched, so the grid was all-green. The fix is structural, not vigilance: step-01 captures `{design_layout_constraints}` (policy-authoritative; README/wrapper corroborate), step-02 §1a resolves the impl's `{impl_page_shell}` (the EFFECTIVE width after every nested cap), and step-03 §2d emits ONE always-present "Page shell" row comparing them. A width/centering mismatch is Tier-1 structural — it reframes the entire composition.
- **A drilled frame's COMPOSITION is a mandatory grid row — the drawer analog of the page shell.** §2d catches the page container's composition; a drawer/detail/lookup frame has the same blind spot one level deeper. The component sweep compares each section's inner pixels and §2f-bis certifies each section exists, but NEITHER compares how the frame is arranged: section order, how sections are grouped under named headings, and the frame's own header/footer chrome. This is precisely what a user reads as "the drawer looks completely different" — the same data, renamed/regrouped/reordered, with every inner component still "matching." The real inbound-flow supply-order miss: the design's `Cost & sourcing` / standalone `Lifecycle` / `Related records` groups shipped as the impl's `Economics` / a status row folded into the header / a combined `Routing & source`, plus a black-vs-blue footer button — an all-green component grid over a wholly recomposed drawer. So step-02b §3 flags every materially-recomposed present frame into `{frame_composition_deltas}` (surfaced in the preflight so a scope halt shows the visual magnitude, never a one-line "treatment" footnote), and step-03 §2d-bis emits a Frame-composition row per drilled frame comparing section order + group naming + header/footer chrome — Tier-1 on divergence. The frame's footer especially: if it is not a cataloged section it would otherwise have no grid row at all, so its button treatment/labels slip silently.
- **A whole frame the bundle delivers is a mandatory grid row, even on a raw-URL run with no brief.** The component sweep is structurally blind to a frame the impl never built — it catalogs the frame's *inner* primitives (which are usually shared and DO exist elsewhere in the impl), matches them, and greens out while the whole **detail drawer** or **§13 expand-in-context lookup** ("link to records (lookups)") ships unbuilt or inferred-thin. The §7 Surface Inventory is the denominator when a brief exists — but a user who pastes a raw Claude Design URL has no brief AND no manifest, and that is the path where the lookup drawers silently vanish. The bundle declares its own frames regardless: the target HTML's `<script src>` modules + their "… lookups consumed" comments, the per-frame banners inside them, the lookup→target maps in the data, and sibling standalone `<frame>.html`. Step-01 **URL.3a** lifts these into `{design_frame_inventory}`; step-03 §2f uses it as the URL-path frame-coverage denominator (precedence: brief §7 → bundle frame inventory (URL) → manifest (bundle) → needs-human-confirm). On the URL path the frames ARE drawn, so an impl lacking the drawer is `FRAME MISSING in impl` (Tier-1). **"No brief" is not "no contract."** And because every one of those denominator sources is a *declaration* that can under-enumerate, step-01 URL.3a source 5 also captures the **authoritative** lookup denominator — the detail drawer's rendered "Linked records" list (`{design_linked_record_rows}`) — and step-03 §2f reconciles the harvested §13-lookup frames against it (every rendered row → a frame, else `LOOKUP UNDER-ENUMERATED`; §13-lookup count ≥ row count; a present-but-thin drawer is swept for depth, not greened on "it opens"). The rendered linked-record list, not a comment, is what stops the "link to record" drawers from being silently missed.
- **The bundle is a generated PROPOSAL; the spec is `docs/design-policy.md`.** The Claude Design bundle AND its README are generated *from* the project's design policy (the README says so: "policy-first; foundations derived from the policy") — so the bundle is the authoritative source for **treatment** (match its proposed pixels, that is the workflow's job) but NOT for **policy conformance**, and it can itself violate the policy (a real bundle shipped a banned colored-glow `@keyframes` + no `prefers-reduced-motion`). Therefore: read the one statically-checkable policy rule — **page-shell / layout intent — from `docs/design-policy.md`** (not the generated README), and **CEDE the rest of the policy contract — prohibitions / tone / motion / iconography — plus all interaction behavior** to the workflows that own the live evidence (`design-review`, `design-review-pr`, `verify`), via the step-03 §2e cede + step-04 §9 disclosure. Never invent a half-check (a grep for `rounded-full`, an `@keyframes` scan) and present it as conformance — a bundle-anchored check against a generated, self-violating proposal lies; an honest cede does not.
- **N/A is a valid cell.** If a property exists in the design but the implementation doesn't have that component, or vice versa — mark it, don't skip it.
- **A handoff is a proposal about treatment, NOT an authorization to delete what production does — check the regression surface BEFORE building the grid.** A redesign frequently omits a capability the live page has (a §13 linked record, a cost-recon path, an activity timeline, a dual-status header, a wired mutation) — and the component sweep greens out on the omission because the dropped capability's inner primitives exist elsewhere in the impl. Whether a drop is an intended simplification or an accidental regression is **intent**, which this workflow cannot infer. So step-02b (between map and grid) inventories `{production_capabilities}` vs `{handoff_capabilities}`, and when the handoff drops something, **HALTS and ADVISES** — a per-capability keep/drop verdict (with reasons) plus one recommended plan (`restyle-only` keep-all · `additive` · `partial` advised-mix · `replacement`) the user approves or adjusts — rather than silently reproducing the omission OR offloading the keep/drop list to the user to assemble. This is the proactive front end to step-04 §9's orphaned-action backstop. Autonomous mode defaults to the non-destructive keep-all and discloses; it never silently replaces.
- **The capability delta is SYMMETRIC — a redesign that ADDS capability is as load-bearing as one that drops it, and the workflow must BUILD the add, not read it as a reskin.** The regression rule above guards the DROP direction; this guards the ADD direction, the equal-and-opposite failure. When the handoff adds (a new analytics/disposition band, lane-by-handler segmentation, an action column, a co-view, a drawer) or materially DEEPENS (a country-filter → handler-lane segmentation; a flat status → a disposition band) a capability the live page lacks, the component sweep is structurally blind to it the same way it is blind to a drop — it greens the shared shell and at most flags the new sub-components `MISSING`, so the run reads a substantial uplift as "treatment alignment." step-02b §3–§4b therefore inventories the delta BOTH ways, names the uplift (`{uplift_capabilities}`), sets strategy ≥ `additive`, and carries every added/deepened item to step-03 §2h / step-04 as a `capability-build` task. An uplift that ships unbuilt is the exact mirror of a kept capability that ships removed. Autonomous mode BUILDS the uplift (implementing the handoff is decision autonomy); it never defaults an uplift to `restyle-only`.
- **Scope is an OUTPUT of the capability delta, never a prior — do not run blind.** "This is restyle-only / treatment-only / token alignment / a structural superset / no net-new capability" is a *capability-scope* verdict and may be asserted ONLY after step-02b §3 has computed the bidirectional delta and found DROPPED **and** `{uplift_capabilities}` both empty. A clean token mapping (raw-hex → canonical-token debt, a resolvable `var(--*)`) is *treatment* evidence — a step-03 grid signal — and it can never license a scope conclusion. Forming "just tokens / production is a superset" from treatment evidence, *especially while step-02 is still resolving production*, is the running-blind failure: it read the inbound-flow supply-orders uplift (lanes + analytics/disposition band + action column + co-views, all net-new) as a reskin. Inventory both capability surfaces first; let the verdict fall out of §3.
- **Apply is grid-driven and fully accounted.** Step-04 walks the grid row by row; every row ends with an explicit disposition (`applied` / `deferred(reason)` / `dropped(reason)`), and the completion report ALWAYS enumerates what was not applied (or states "all N applied"). A holistic "rebuild until it looks like the design" pass that silently drops enumerated rows is the failure the step-04 apply ledger exists to prevent — exhaustive cataloging (above) is worthless if the apply isn't equally accountable.
- **Resumable apply on an ingest manifest — CHECKPOINT at a frame boundary; never push one giant pass through the compaction trap.** A large `design-ingest` manifest (many frames × many sections) cannot be reliably APPLIED in one context: a single-window run hits the harness's auto-summarization boundary and silently drops exactly the high-value/low-redundancy detail — the exact CSS values and the per-row dispositions — so rows get marked done that were never really verified. This is the `context-budget-overflow` failure the manifest exists to make recoverable. The manifest IS the durable progress ledger (its grid scaffold carries a per-row status). So step-04, on an `ingest_manifest` run, MUST: (1) **apply frame by frame** and **persist each row's disposition back into the manifest file the moment that frame is done** — durable state lands BEFORE any compaction, not at the end; (2) **resume automatically** — at run start it reads `{resume_prior_dispositions}` and skips rows already `✓ applied`, so re-invoking the *same command* in a fresh session continues where the last one stopped; (3) **self-checkpoint** — after each completed frame, judge whether another full frame can be applied-and-re-verified without the run's recall degrading; when in doubt, STOP at that frame boundary, set `{run_completion_mode} = checkpointed`, deliver the slice already built (commit → PR → merge as usual), and report the exact resume command. Stopping early with a durable, delivered slice is CORRECT, not a failure — a fresh session resuming from the manifest is cheap; a compacted single pass that drops rows is the expensive miss. The checkpoint is a clean terminal exit of the pass, **not** a wait-for-input halt — it does not violate the autonomous-execution rule. Soft default (thresholds, not cliffs, per the context-budget principle): a pass should not attempt more than roughly **one heavy frame (a drawer with many sections) or ~10–12 sections total**, whichever comes first, before checkpointing — adjust down the moment recall of earlier frames' exact values feels lossy. Never checkpoint mid-frame: a frame's sections share components and must cohere.
- **The DURABILITY half generalizes to the URL/bundle path; the AUTO-RESUME half does not.** The rule above is scoped to the manifest, but the compaction trap it defends against is not manifest-specific — a `claude_design_url` / `synthesize_bundle` run can specify an arbitrarily large *apply* from a small-to-ingest bundle (a phone-first recomposition is cheap to read, expensive to write), and its only durable artifact — the grid step-03 already wrote to disk — is committed just once, at the very end (step-04 §6). So a mid-apply compaction on the URL path silently loses exactly the per-row dispositions this rule exists to protect, and no size preflight catches it (the preflight measures *ingest* bytes; the un-recoverable cost is *apply*, and the two are uncorrelated). Therefore step-04 MUST, on **every** path, treat the on-disk grid artifact as the durable ledger: **persist each section's disposition into it the moment that section is applied, and commit it early (force-add), BEFORE any compaction boundary** — the `URL-path apply ledger` (step-04 §5). What the URL/bundle path does NOT inherit is *auto-resume + frame checkpointing*: a raw URL run carries no reviewed section scaffold and a fresh worktree may not see an uncommitted artifact, so a re-run re-ingests. The durable-write half is what stops the loss; the resume half is a manifest-only optimization. Persist-as-you-go everywhere; checkpoint-and-resume on the manifest.
- **The grid certifies treatment, structure, state, and multiplicity — NOT the content lane.** design-implement compares the implementation against the design *bundle*, and the bundle renders **seeded mock data**, not real production data. So any defect that lives in *what a value-formatter renders* — a canonical-identifier class (marketplace, supplier, ASIN/SKU, order/batch number, currency, date, status label) shown in the wrong form, a raw enum leaking where a human label belongs (`amazon_us` instead of `US` / `Amazon US`), or inconsistent casing/label-form across sibling surfaces — is **invisible to this workflow by construction**: the formatter is wrong only on a real-data variant the mock bundle never contained, so there is no grid delta to find, and a bundle string-match (mock `UK → UK` vs impl `UK → UK`) "passes" while the real render (`US → amazon_us`) is broken. This is the **content lane** (project design policy §13 "Canonical identifier" / §13a) — owned by `design-review` (live Chrome audit, §13(a) check) and `design-tuning` (step-02 §2b, run against the LIVE page). design-implement does **not** certify it and must not pretend to from a mock-data bundle; instead it **flags formatter-driven identifier cells as `content-lane-unverified` (step-03 §2c) and routes them to those workflows through the apply ledger (step-04 §5/§9)** rather than silently passing them. This is the same treatment / composition / content three-lane model `design-tuning` and `design-review` use: design-implement owns treatment + structure and explicitly **cedes** the content lane to the live-page workflows.
- **A faithful port onto a DIVERGENT FOUNDATION token is a silent failure — reconcile the foundation before trusting any component match (step-03 §2i).** The grid compares a *component's* type/radius and §2g checks a token's *placement*, but NEITHER catches the app's *canonical* token VALUE disagreeing with the design system's foundational scale and with `docs/design-policy.md`'s declared value. A button `font-size: var(--font-size-base)` greens against an identical design declaration while one resolves to the bundle's 13px and the other to the app's 16px — no component owns the type scale, so the component sweep is blind to it (the §2d page-shell blind spot at the token layer). This is the inbound-flow held-orders miss (PR #2412): the app ships `--font-size-base: 1rem` against a policy that declares 13px, every ported surface renders ~23% large, and the implementer encoded the design's 13px as `var(--font-size-base, 0.8125rem)` — a **dead fallback** the defined global silently overrides. So step-01 URL.4 reads the bundle's foundational `tokens/*.css`, step-02 §5a catalogs the app's canonical scale + the policy-declared scale, and step-03 §2i emits a routed Foundation-token row on any drift. The fix is a **single-source token migration** owned by `apply-design-policy-change`, NEVER a per-component patch and NEVER a `var(--token, <literal>)` dead fallback — design-implement DISCLOSES + ROUTES; it does not fix the foundation per-surface, and it states in §9 that green component type/radius rows compared at the app's (possibly divergent) foundation, not as proven parity.
- **Bundle gating is non-negotiable when consuming a design-synthesize bundle.** When `{input_kind} == "synthesize_bundle"`, step 1 MUST parse `bundle/manifest.yaml` and refuse the bundle (halt with the diagnostic in §"Input Resolution") if EITHER of the following is true:
  - `synthesis.dev_no_render: true` — the bundle was emitted without a screenshot (development mode) and is explicitly not production-ready.
  - `visual_review.needs_human_review: true` — `design-synthesize`'s self-critique (step 6 d/e/f) flagged the bundle as needing human design review before implementation. Reasons can include `visual_quality: weak`, `visual_lift_over_baseline: false`, or `exemplar_alignment: deviated_unauthorized`. Implementing a flagged bundle would pixel-lock a design that the synthesizer itself doesn't trust.

  These are bounce-back refusals, not soft warnings. The workflow halts BEFORE step 2 and prints the next-step command (re-run `design-synthesize` or route through `design-review`). This preserves the contract: bundles that `design-synthesize` doesn't trust never become implementations.

- **A consequential control needs an interaction MODEL, and a bundle can supply the control while omitting it — step-02b §4e.** Every check ahead of the grid is blind to this by construction: the capability delta sees the capability present on both sides, the copy is not misworded, and the grid is CSS-only. So a surface can ship two controls pointing at the same irreversible external write with no durable attempt record behind either. On cash-recovery `/listings`, "Preview what will be sent" and "Re-attempt publish" shared a target around an eBay publish — no attempt object, no states, no snapshot of the payload the operator reviewed, no staleness rule, no idempotency, no single owner of the write. **UI-copy review could not have found it.** §4e therefore fires — narrowly — when the surface carries an outward write, durable mutation, approval, binding/merge, retry, or a pre-commit evidence review, and requires the nine lifecycle facts (`{commit_boundary_contract}`) before the grid is built. Controls without the lifecycle are an **interaction-model gap**, not a copy/layout issue: the remedy is the *smallest* stateful flow mapped onto named frames/sections and built as an uplift capability, never a relabel or an extra confirm dialog. Everything read-only or reversible skips, and says so in one line. **Autonomous mode does not auto-proceed past a gap** — inventing a lifecycle around someone else's irreversible write is intent, not decision autonomy.
- **Shipping a fixture-backed surface to a PRODUCTION route is an AUTHORIZATION decision, not a side-effect of faithful transcription — step-02b §4c halts for it.** design-implement transcribes whatever the handoff specifies; when the surface has no live read path, the unflagged default is to wire it to a mock module (a `DATA_STATE = "fixture"`-style marker, no live read-model/DB path) and ship it — mock data reaching a production route as an unremarked consequence of "just implementing the design." Whether that is acceptable is the owner's call, not the transcription's. So step-02b §4c **HALTS-and-ADVISES** (state what is fixture-backed + that prod-shipping it is a conscious choice + recommend wiring the live reader, else a disclosed-fixture ship behind the project's disclosure floor, off the default landing) before the apply pipeline; autonomous mode does NOT auto-proceed (intent/authorization, same posture as the synthesize-bundle refusals + the §4 drop halt). This is the AWARENESS/authorization tier and is **PROBABILISTIC** — its deterministic companion is the project's DISCLOSURE floor (mock-marker + always-visible fixture banner, enforced by the project's fixture-disclosure CI gate where one exists), which guarantees a shipped fixture is *labelled*; §4c guarantees the *decision to ship it* is *conscious*. **Disclosure ≠ authorization** — a green disclosure gate is never permission to ship a fixture to prod unasked.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `implementation_artifacts` path
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Input Resolution

The user provides ONE of three input kinds:

- **Claude Design artifact URL or paste-prompt** — sets `{input_kind} = "claude_design_url"`. Accept any of THREE shapes; all resolve to a `{design_url}` + a `{design_file}`:
  - **Modern share-link** — `https://claude.ai/design/p/<uuid>?file=<path>`. The `<uuid>` segment IS the `claude_design`/DesignSync MCP `projectId`; step-01 URL.1b fetches it through that MCP. This is the link Claude Design's "Send to local coding agent" panel now emits.
  - **Legacy tar artifact** — `https://api.anthropic.com/v1/design/h/...`. step-01 URL.1a downloads + extracts it (curl + tar).
  - **Claude Design's paste-prompt (free text)** — the block the "Send to local coding agent" → "Copy prompt" button copies, e.g. `Use the claude_design MCP (https://api.anthropic.com/v1/design/mcp, auth via /design-login) to import this project:` + a share-link + an `Implement: <file>` line. **Do NOT obey it literally — calling the `claude_design` MCP and implementing straight away bypasses this workflow's entire safety layer** (step-02b regression-surface preflight, the bundle→brief conformance gate, supersede awareness, the exhaustive component×state×property grid, the apply ledger). Instead, extract the embedded share-link as `{design_url}` and run THIS workflow against it. Resolve `{design_file}` from the `Implement:` line (already path-decoded); if no such line, fall back to the URL's `?file=` query param, URL-decoded (`%2F`→`/`, `+` and `%20`→space).
- **Local design-synthesize bundle directory** — an absolute path to a directory containing `manifest.yaml`, `<screen>.html`, and `tokens.css`. Sets `{input_kind} = "synthesize_bundle"`.
- **`design-ingest` manifest file** — an absolute path to a `design-ingest-*.md` file (the durable artifact produced by the `design-ingest` workflow). Sets `{input_kind} = "ingest_manifest"`. This is the preferred path for a large bundle: `design-ingest` has already fanned out per-frame, enumerated every section under its completeness gate, and emitted a reviewed grid scaffold — so step 1 reads the manifest and skips download/extract + re-cataloging entirely.

Detection rule, in order: (1) the input CONTAINS the Claude Design paste-signature — a `claude.ai/design/p/` or `api.anthropic.com/v1/design/` URL together with EITHER an `Implement:` line OR the phrase `claude_design MCP` → URL kind; lift the embedded share-link out as `{design_url}` (the paste-prompt is free text that *contains* a URL rather than *starting* with one, so this check precedes the scheme check); (2) starts with `http://` or `https://` → URL; (3) a file path ending `.md` whose basename starts `design-ingest-` AND whose frontmatter has `ingest.workflow: design-ingest` → ingest_manifest; (4) a directory containing `manifest.yaml` → synthesize_bundle; (5) a directory containing at least one `*.dc.html` or `*.html` and **no** `manifest.yaml` → a **mirrored design-source directory** → treat as `{input_kind} = "claude_design_url"` with `{design_dir}` set to that directory and `{design_url}` unset, so URL.1's fetch is already satisfied and execution resumes at **URL.1c** (shape detection). `{design_file}` is the trailing `Implement:`/filename token when one is given, else the largest `*.dc.html` in the directory. This is the landing pad for URL.1b §1a's recommended route — a design whose project DesignSync cannot reach, exported by hand into `design-source-<slug>-<date>/`. It is a **first-class input, not a workaround**, and rule 4 is evaluated first so a genuine synthesize bundle is never captured by it. If none matches, halt with: `"input must be a Claude Design URL/paste-prompt (https://...), a design-ingest-*.md manifest, a directory containing manifest.yaml, or a mirrored design-source directory containing the design's .dc.html. Got: <input>"`.

On the `ingest_manifest` path only, an OPTIONAL trailing token after the manifest path sets `{frame_scope}` (a comma-separated frame-id list or single id, e.g. `frames=order-detail-drawer` or just the bare id list). Absent ⇒ `{frame_scope}` is unset (apply all not-yet-applied in-scope rows). It is ignored on the URL and bundle paths.

#### When `{input_kind} == "synthesize_bundle"`: Bundle gating

Before any other work, parse `{bundle_dir}/manifest.yaml` into `{bundle_manifest}`. Then check the two refusal gates:

**Refusal 1 — dev-only bundle.** If `{bundle_manifest}.synthesis.dev_no_render == true`:

```
══════════════════════════════════════════════════════════════════
✗ design-implement refused this bundle.

Reason: bundle was emitted with --no-render and has no screenshot.
        synthesis.dev_no_render: true

A bundle without a screenshot has not been visually verified by a human
and is explicitly a development-mode artifact, not a production bundle.

Re-run design-synthesize WITHOUT --no-render and re-invoke:

  /bmad:bmm:workflows:design-synthesize {bundle_manifest.synthesis.brief_path}
══════════════════════════════════════════════════════════════════
```

Halt — do NOT proceed to step 1.

**Refusal 2 — needs human review.** If `{bundle_manifest}.visual_review.needs_human_review == true`:

```
══════════════════════════════════════════════════════════════════
✗ design-implement refused this bundle.

Reason: design-synthesize flagged this bundle for human review.
        visual_review.needs_human_review: true
        visual_review.visual_quality: {bundle_manifest.visual_review.visual_quality}
        visual_review.visual_lift_over_baseline: {bundle_manifest.visual_review.visual_lift_over_baseline}
        visual_review.exemplar_alignment: {bundle_manifest.visual_review.exemplar_alignment}
        synthesis.compliance_state: {bundle_manifest.synthesis.compliance_state}

This bundle satisfies the policy contract but failed one or more of
design-synthesize's visual sub-checks (step 6 d/e/f — visual quality,
lift over baseline, exemplar alignment). Implementing it would pixel-lock
a design that the synthesizer itself does not trust.

Next step — route through human design review BEFORE implementation:

  /bmad:bmm:workflows:design-review {bundle_dir}

Then either re-run design-synthesize with corrections, or — if the human
review explicitly approves the bundle as-is — re-emit the manifest with
visual_review.needs_human_review: false (this requires editing the
manifest manually or re-running design-synthesize until the visual half
passes).
══════════════════════════════════════════════════════════════════
```

Halt — do NOT proceed to step 1.

If neither refusal fires, set `{design_dir} = {bundle_dir}` and `{design_file}` defaults to the first entry in `{bundle_manifest}.screens` (use `<screen>.html` resolution within `{bundle_dir}`). Continue to step 1, which will skip the URL download path and read directly from `{bundle_dir}`. **Supersede awareness for this path is resolved in step-01 §SHARED.1a** (the slug isn't known until the frame inventory is built), same as the URL path — a bundle handed straight to `design-implement` still copes with a superseded handoff.

#### Prior-halt recall (ALL input kinds) — read back what a previous run already decided

**A step-02b halt is an expensive verdict that, before this pair of changes, had nowhere durable to live.** The halt presented its regression report *in chat* and the session ended; nothing persisted it and nothing read it back. So re-pasting the SAME Claude Design prompt re-derived the same halt from zero, after a full ingest + map. Step-02b now PERSISTS the verdict to `{implementation_artifacts}/design-implement-preflight-<slug>-<date>.md` (§4d) and this check READS it — the two ship together, because a reader with no writer is inert and a writer with no reader is write-only. That re-paste is **not operator error**: the "Send to local coding agent" panel emits a *stable* prompt per file, and any project `design-handoff-detect` hook routes every such paste straight here — so the identical input arrives again each time the owner revisits the design. When the blocker is slow to clear (a read model, an owner-gated model change), the window in which re-pastes are wasted is days wide, not a same-hour edge.

**This check runs FIRST, before every other intake check, because it is the cheapest** — it keys on the raw input string, so it needs no `{target_slug}`, no frame inventory, no fetch, no bundle on disk.

1. Enumerate `design-implement-preflight-*.md` in `{implementation_artifacts}` — **from `origin/main` as well as the working tree, never the working tree alone.**

   ```bash
   git fetch -q origin
   { ls "{implementation_artifacts}"/design-implement-preflight-*.md 2>/dev/null
     git ls-tree -r --name-only origin/main -- "{implementation_artifacts}" 2>/dev/null \
       | grep 'design-implement-preflight-.*\.md$'
   } | sort -u
   ```

   Read a hit that exists only on `origin/main` with `git show origin/main:<path>`.

   **Why this is not belt-and-braces.** A checkout that is behind produces a false **ABSENCE**, and absence is this check's only SILENT outcome — it prints nothing, so a stale tree does not look like a failed lookup, it looks like *"no prior halt."* That is the one answer that costs a full re-derivation, and it is indistinguishable from the true negative. The **net-new preflight below already states this rule for itself** (*"`ls`-class, against `origin/main` (a stale checkout reports a false absence, which is the direction that fires it)"*); two intake checks in one file must not disagree about where truth lives.

   **Observed 2026-08-04 (cash-recovery `/held`, FG-2026-08-04-02).** The working-tree glob returned nothing and the run reported "no prior halt" while a matching preflight sat on `origin/main` — the checkout was **159 commits behind**. The prior halt's three blockers (a dropped write-off eligibility disclosure, a doctrine-forbidden class label, and an added action with no destination) were all still live in the redesign, so the run did not merely re-spend the ingest: it proceeded believing no prior verdict existed, and the artifact that would have told it otherwise was one `git show` away.
2. Match each artifact's frontmatter `design_source` against the incoming `{design_url}` / `{bundle_dir}` / `{ingest_manifest_path}` — **normalized**: compare scheme + host + path and the URL-decoded `file=` value, ignoring query-param ORDER and unrelated params. Fall back to a `design_file` match when `design_source` is absent (a pre-contract artifact).
3. On a hit, compute a **still-valid?** signal — `git log <baseline_commit>..origin/main -- <the paths the halt named as blocking>`. **Empty ⇒ nothing has moved on the blocking paths, so the prior halt almost certainly still holds.** Non-empty ⇒ the blocker may have cleared; name the intervening commits so the operator can judge.

Set `{prior_halt}` and SURFACE it:

```
────────────────────────────────────────────────────────────────
◇ A previous design-implement run against this SAME design source halted.

  artifact:   {filename}
  ran:        {date}   (session {session})
  outcome:    {outcome}
  blocked on: {blocked_on, verbatim from the artifact}
  baseline:   {baseline_commit}
  since then: {n} commit(s) touching the blocking paths{, or "none — the blocker has not moved"}

Read that artifact before re-spending the ingest: it already carries the
capability delta, the per-capability KEEP/DROP verdicts, and the recommended
unblock path. Re-deriving them costs a full ingest + map and lands on the
same verdict.
────────────────────────────────────────────────────────────────
```

**SURFACE, never GATE.** This check does not halt, refuse, or skip a step — including when the still-valid signal says nothing has moved. A prior halt is *evidence*, not a verdict about this run: the blocker may have cleared in a way `git log` cannot see (an owner decision, a strategy change, a deliberate re-run to refresh the artifact), and a re-run that re-confirms a stale halt is cheap next to a gate that blocks a legitimate one. **Whether this should ever become a gate is an OPEN OWNER DECISION and is deliberately not taken here** — promoting it would define a new halt threshold (halt when the baseline is unchanged? warn otherwise?) and would promote the preflight artifact from a *report* into a *machine-consumed contract*, implying a schema and a staleness policy. Both are rule changes, not maintenance. Until that call is made, the artifact is read opportunistically and treated as advisory: a missing, malformed, or unparseable preflight artifact is a **silent no-op**, never an error.

**Enforcement honesty:** PROBABILISTIC and deliberately so. The glob + match is mechanical, but nothing forces the operator to act on what it surfaces, and nothing verifies the artifact's `blocked_on` is still true. Its whole job is to put a verdict that already exists in front of the next session instead of leaving it write-only on disk. Note the asymmetry it closes: a **checkpointed** pass already announces itself on the next session (the pending-checkpoint detector); a **halted** pass announced itself to nobody.

> **Twin at the OTHER end of the lifecycle — the already-shipped recall — lives in step-02b §3b, not here.** *"Is there anything LEFT to diff?"* is the mirror of the preflight below, but it cannot be answered cheaply at intake: it needs step-02's resolved impl paths and step-02b §3's computed capability delta. So it runs post-map / pre-grid, and its saving is bounded to the grid + apply rather than the ingest. See `{prior_applied}`.

#### Net-new / no-target preflight (ALL input kinds)

**The existence gate — is there anything to implement against at all?** `design-implement`'s entire model is *diff a design against an EXISTING implementation and fix the deltas*. A design handed off for a **net-new surface whose route, page component, and backing object do not exist yet** has nothing to diff: the grid comes back all `FRAME MISSING in impl` and the run aborts itself at the §2b/§4c fixture-ship halt AFTER a full, non-trivial ingest. This bites hardest on exactly the normal case — a paste straight from Claude Design's "Send to local coding agent" panel for a surface you just designed but have not built. The strong, DETERMINISTIC routing layer (the paste-prompt handling above, and any project `design-handoff-detect` hook) points every paste here; this preflight is the deterministic guard that stops a net-new paste *before* the spend, so the catch no longer depends on the operator probabilistically recalling onboarding doctrine.

Run this check **as soon as `{target_slug}` + the target route are resolved** (step-01 §SHARED.1a — the earliest cheap point, before ingest and the grid). Cheaply probe whether the target surface exists in the implementation. **Probes 1–2 ARE the surface and they alone decide the flavour: both absent ⇒ net-new, whatever probe 3 says — `backing object alone is NOT a surface`.** Probe 3 scopes the *recommendation* (a present table means the backend step is partly done); it is never a veto on the *verdict*. It has to read that way because this preflight's own onboarding path — *"build the minimal backend first"* — deliberately CREATES the schema-present / route-absent state, so an all-three-absent trigger disarms the gate for precisely the operator who followed the advice. Observed 2026-07-27 (cash-recovery `/units/[id]`, a 12-frame ingest manifest): `units` table present, no route and no page component — the old trigger said "not net-new" while the Verdict below said "not brownfield", leaving the real case with no verdict at all.

1. **Route** — no route / nav entry matches the surface (`{target_slug}` or its route) in the app's router or nav config.
2. **Page component** — no page / screen component file exists for the surface.
3. **Backing object** — no schema table and no shared type exists for the surface's primary object (grep the schema + shared types for the object name).

**Capability-granularity probe (the overlay case).** Surface existence is necessary but not sufficient. A common handoff is a **net-new capability layered on an EXISTING surface** — a new lifecycle/persistence dimension (drafts, versions, approvals, autosave/park/resume) overlaid on an already-shipped page. Probes 1–2 hit (route + page exist), so the surface reads brownfield — yet the *capability's own* backing object is unbuilt, and a fixture-only run would pass this cheap gate and only stop at the §2b/§4c fixture-ship halt, after a full ingest is already spent (the exact wasted-spend this preflight exists to prevent). So ALSO probe, at capability granularity — **any one firing ⇒ capability-net-new**:

4. **Paired not-ready backend/arch-spec** — a paired backend or architecture-spec artifact for the same `{target_slug}` exists AND self-marks not-ready (e.g. `Status: NOT ready to implement`) or is uncommitted/unlocked.
5. **Capability's backing object** — the handoff's README/brief declares a net-new capability ("net-new … capability overlaid on …"; a new store such as `order_drafts`), and grepping the schema + shared types for the *capability's* object (the draft/version/approval store — NOT the surface's primary object) finds nothing.
6. **Assumed read/save path** — the save/park/resume/reload path this design assumes has no implementation (no action/mutation/service for the capability).

**Verdict.** If **both surface probes (1–2) are absent ⇒ net-new surface** (early-exit below) — record what probe 3 found, because a present backing object changes what you *recommend* (the schema step may already be done, so the onboarding path starts further along) but never *whether* this is net-new. If the surface exists (1–2 present) BUT any capability probe (4–6) fires **⇒ capability-net-new** — early-exit with the SAME soft recommendation, because the read/save path the design assumes does not exist yet, so the run would still ingest fully and stall at §4c. Only when probes 1–2 find an existing surface AND probes 4–6 are all clear is this a true brownfield diff — **proceed normally**. When surfacing a `capability-net-new` exit, name the missing capability object + spec so the override is informed. **EARLY-EXIT (soft — recommendation, not a hard refuse; the operator may override):**

```
══════════════════════════════════════════════════════════════════
◇ design-implement: this looks like a NET-NEW surface — nothing to diff against.

Target:  {target_slug} ({design_file})
Checked: no route, no page component, and no backing schema/type for
         this surface exist in the repo.

design-implement diffs a design against an EXISTING implementation. A
net-new surface has no implementation yet, so this run would produce an
all-"FRAME MISSING in impl" grid and abort at the fixture-ship halt after
a full ingest — wasted spend, wrong workflow.

Onboarding path for a net-new surface (project doctrine where present —
`project-net-new-design-onboarding`):
  1. Build the minimal backend first (schema + service + types).
  2. Run brownfield design-handoff (it reads the real schema).
  3. design-synthesize → THEN re-invoke design-implement.

To proceed anyway (e.g. the backend is landing in this same session, or
you are knowingly implementing ahead of it), re-invoke with an explicit
"proceed anyway" / override.
══════════════════════════════════════════════════════════════════
```

This is a **soft** early-exit (recommend + override), NOT a hard refuse like the two bundle gates above — it stops a mis-route by default while leaving the owner the wheel. Distinct from a *size* preflight (a large but EXISTING surface): this is about **existence** — whether there is anything to implement against at all. The determination has two flavours — `net-new-surface` (surface probes 1–2 both absent; the backing object may or may not exist, and if it does, say so) and `capability-net-new` (surface exists but a capability probe 4–6 fires: a new persistence/lifecycle dimension whose backing object + read/save path are unbuilt). Surface which flavour in the run's opening summary (§SHARED.2) so the override is scoped to the real gap, not a blanket "surface missing."

#### When `{input_kind} == "claude_design_url"`: existing flow

Store the share-link as `{design_url}` and the resolved target as `{design_file}` (per the URL-kind resolution above: `Implement:` line first, else URL-decoded `?file=`). Continue to step 1 — step-01 URL.1b is the authoritative `{design_file}` resolver (it has the project file tree from `list_files`), so an unresolved `{design_file}` here is fine; it defaults to the project's primary frame there. **Supersede awareness is resolved in step-01 §SHARED.1a** (the slug isn't known until the frame inventory is built), not here — a direct URL run still copes with a superseded handoff.

#### When `{input_kind} == "ingest_manifest"`: manifest gating

Parse `{ingest_manifest_path}` into `{ingest_manifest}`. Then check one refusal gate — the completeness invariant the `design-ingest` workflow is required to uphold:

**Trust check — run the manifest verifier, do not eyeball it.** Before consuming the manifest, run
`node ~/bmad-method-v6/tools/check-ingest-manifest.js --manifest {ingest_manifest_path}` and read the
findings. Two codes change what this run is allowed to assume:

- **`C10-GRAIN-PROSE-ONLY` / `C10-GRAIN-CONFLICT`** — the manifest's body claims a grain its
  frontmatter does not. **The frontmatter wins, and an absent `manifest_grain` means `summary`**
  (manifest-schema "Grain invariant") — so a manifest that *reads* value-exact is one you must
  re-read the design source for. Do not take the prose. Say in the run summary which you used.
- **`C11-UNRESOLVED-VOCAB`** — a vocabulary is dereferenced but never resolved, so the literals it
  names are **not in this manifest**. You may not transcribe what is not there and you may not
  invent it. Resolve it from the design source in THIS context and record what you resolved, or
  defer every row that depends on it with the reference named in its disposition. **Never delegate a
  row carrying an unresolved reference to a sub-agent** — the design MCP is session-bound
  (`FG-2026-07-26-01` / `-06`), so the agent can neither read it nor legally guess, and the failure
  surfaces as invented copy rather than as an error. `C11-DECLARED` is the disclosed-deferral form:
  same handling, already acknowledged by the producer.

Neither is a refusal — a manifest is still consumable with a known gap. What is forbidden is
consuming it as if the gap were not there.

**Refusal — incomplete manifest.** If `{ingest_manifest}.ingest.completeness.frames_with_empty_section_list` is non-empty (a `drawn: true` frame with no enumerated sections), refuse:

```
══════════════════════════════════════════════════════════════════
✗ design-implement refused this ingest manifest.

Reason: a drawn frame has an empty section list —
        completeness.frames_with_empty_section_list: {list}

design-ingest's frame-completeness gate should have halted on this. A manifest
with an unenumerated drawn frame would reintroduce the exact blind spot the
manifest exists to close (a section dropped inside a present frame). Re-run:

  /bmad:bmm:workflows:design-ingest {ingest.source}
══════════════════════════════════════════════════════════════════
```

Halt — do NOT proceed to step 1. If the invariant holds, set `{design_file} = {ingest_manifest}.ingest.target_file`, carry `{ingest_manifest}` forward, and continue to step 1, which reads the manifest directly and skips the URL/bundle ingest paths.

**Resume read (every ingest_manifest run).** Before step 1, read the grid scaffold's existing per-row dispositions into `{resume_prior_dispositions}`. Any row already marked `✓ applied` (or `✓ applied (prior pass)`) from an earlier checkpointed pass is carried forward as-is and is NOT re-applied or re-verified — step-04 §5 pre-disposes it and walks only the remaining UNVERIFIED rows (further narrowed by `{frame_scope}` if set). This is the auto-resume contract: re-invoking `design-implement <same-manifest-path>` in a fresh session continues from the last checkpoint with no extra flags. If EVERY in-scope row is already `✓ applied`, there is nothing to do — report "manifest already fully applied (N/N)" and exit without a no-op PR (but read the supersede branch below first — a fully-applied superseded manifest explains its no-op).

**Supersede awareness (every ingest_manifest run).** Read `{ingest_manifest}.ingest.supersede_status` into `{handoff_supersede_status}` and `ingest.superseded_by` into `{superseded_by}` (stamped by `design-ingest`; `brief-revision-policy.md` §8, `design-ingest` manifest-schema "Supersede stamp"). `design-implement` is symmetric with `design-ingest` — it does NOT hard-refuse a superseded manifest, but it never applies one silently:

- **`active` / `no_brief`** → normal flow. (`no_brief` = supersede could not be determined at ingest, not an assertion that it's current.)
- **`superseded`** → surface it BEFORE step 1 ("this manifest is built from a handoff superseded by `{superseded_by}`; that newer brief is the current truth"), then branch on the resume read above:
  - **No deltas** (every in-scope row already `✓ applied`): the no-op report becomes *self-explaining* — "manifest already fully applied (N/N) — and this handoff is superseded by `{superseded_by}`, so there is nothing to do and nothing current to do it against." Exit without a PR. This is the graceful no-op the supersede stamp exists to produce.
  - **Deltas exist** (UNVERIFIED rows remain): applying them would push the surface toward the SUPERSEDED design — the stale-work hazard. Do NOT auto-apply, even in autonomous mode (this is intent, not decision autonomy). HALT and require explicit confirmation: state the deltas come from a superseded handoff, name `{superseded_by}` as the current design, and ask the user to either re-run against `{superseded_by}` or confirm they really want to apply the older design.
- **`ambiguous`** → warn (two briefs claim `active` for this slug; `brief-revision-policy.md` §2.6) but proceed — the manifest itself is well-formed.
- **Absent stamp** (a manifest emitted before this contract) → treat as `no_brief` and proceed (backward-compatible default, same posture as the policy's absent-field defaults).

**Freshness reconciliation (every ingest_manifest run) — a manifest can be STALE even when its supersede stamp reads `active`.** Supersede (above) catches a DIFFERENT brief replacing this one; freshness catches the SAME active brief being *materially revised AFTER the manifest was built*, so the manifest now encodes an older design version of a still-current brief. At intake, compare the manifest's provenance — `{ingest_manifest}.ingest.source`, `ingest.target_file`, and the brief `source_run_date` the manifest recorded at build time — against the CURRENT brief matched for `{target_slug}` (`brief-revision-policy.md` Block A / `source_run_date`). If the current brief carries an active material revision NEWER than the manifest's recorded `source_run_date` (same slug, same target_file, later revision), WARN before consuming it:

```
⚠ MANIFEST STALE (built from a superseded design version)
  manifest built from:  {ingest.source}  (source_run_date {manifest_source_run_date})
  current brief:        {matched brief}  (source_run_date {brief_source_run_date}, materially revised since)
  → the section inventory / grid scaffold may not reflect the current design.
    Re-run design-ingest against the current brief to refresh, or confirm you
    intend to apply the older captured version.
```

This is a **soft warn, not a halt** (symmetric with the `ambiguous` case) — the manifest is still well-formed and may be applied deliberately; it just must never be consumed *silently* as if current. If provenance can't be compared (no `source_run_date` on the manifest or the brief — a pre-contract artifact), record `freshness: unverified` and proceed, same backward-compatible posture as the absent-stamp default.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/design-implement`

---

## OUTPUT CONTRACT & VOICE SLOT

Emit the close-out per `shared/close-out-contract.md` (audience-first; process narration forbidden
by default; shape-feedback routes to a workflow patch). **The two-block shape in §2a binds here:**
block 1 is the plain answer; block 2 is at most one fenced `FOR YOUR LLM ADVISER` block, emitted
only when actionable technical detail exists, neutral and machine-shaped, never carrying a voice.
Row dispositions, unrouted-component findings, the commit SHA and the manifest path belong in
block 2. **A CHECKPOINTED or HALTED run still states that fact in block 1, in plain language** —
disposition is not a detail to be paged past.

**The voice slot (`persona_slot`).** The agent executing this workflow MAY speak in its own voice
at exactly the three human-facing moments in `shared/workflow-personas.md` §2a — opening, a genuine
owner decision or pause, and close-out block 1.

**Never in:** `steps/step-01a-ingest-url.md` / `step-01b-ingest-bundle.md` / `step-01c-ingest-manifest.md`,
`steps/step-03-build-grid.md` (checker output — a grid row is a verdict, not a sentence),
`template.md`, `unrouted-golden-matrix.md`, or any grid cell or manifest record. If no voice is
bound these render plain and anonymous — **today's behavior, unchanged.** This workflow names no
persona; the binding is the project's.

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-01-ingest-design.md` to begin.

**Step 01 is a ROUTER — read it, then ONE path file, then return to it.** The three ingestion paths live in their own files so a run loads only the one it executes: `step-01a-ingest-url.md` (`URL.*`) · `step-01b-ingest-bundle.md` (`BUNDLE.*`) · `step-01c-ingest-manifest.md` (`MANIFEST.*`). `§SHARED` and the success/failure criteria stay in `step-01-ingest-design.md`, which is where every path converges and where the gates run. **Citations above are unchanged by the split** — the section ids were not renamed, so `step-01 §SHARED.1a` is still in step-01, and `step-01 URL.1b` / `URL.3a` / `URL.4` now resolve inside `step-01a`; step-01 carries a citation legend mapping each prefix to its file.
