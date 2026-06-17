---
name: design-implement
description: 'Implement a Claude Design artifact with pixel-level precision. Fetches the design bundle, reads every CSS value, builds a component-by-component comparison grid against the existing implementation, then fixes all deltas.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Design Implement Workflow

**Goal:** Take a Claude Design artifact URL and bring the codebase into pixel-perfect alignment with the design — measured by an exhaustive **component × state × property** comparison grid plus an **implementation-multiplicity** cross-check, not by eyeballing. The state axis (default, hover, focus, selected, failed, empty, disabled, …) is part of the contract: a state-conditional rule in the design that has no matching grid row leaks to production. The multiplicity axis is the other half: a primitive (status pill, chip, money cell) is often implemented more than once, and the drift that ships is usually *between two implementations of the same primitive* — so every render site is enumerated and the implementations are checked against each other (step-03 §2a), not just against the design.

**Your Role:** You are a pixel-precision engineer. You do not design — you enforce. The Claude Design artifact is the authoritative specification. Your job is to extract every CSS value from the design source — **inline styles, `<style>`-block rules, and `data-state` variants alike** — compare it against the implementation, enumerate every delta, and fix all of them. A delta that slips through is a failure, including state-conditional rules (failed-row tint, hover behavior, null-data styling) that don't appear in the default rendering.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All 4 steps are FULLY AUTONOMOUS — no user interaction after invocation
- State persists via variables (see below)
- Sequential progression: ingest design → map implementation → **capability-delta preflight (step-02b: handoff vs production, BOTH ways — DROPPED → strategy halt, ADDED/DEEPENED → build plan)** → build grid → apply and deliver

### State Variables

- `{input_kind}` — `claude_design_url` | `synthesize_bundle` | `ingest_manifest`. Determines whether step 1 fetches a URL, reads a local bundle directory, or reads a pre-built `design-ingest` manifest (and skips re-ingest entirely).
- `{design_url}` — Claude Design artifact URL (when `{input_kind} == "claude_design_url"`)
- `{bundle_dir}` — Absolute path to a local design-synthesize bundle directory (when `{input_kind} == "synthesize_bundle"`)
- `{bundle_manifest}` — Parsed `bundle/manifest.yaml` contents (when `{input_kind} == "synthesize_bundle"`)
- `{ingest_manifest_path}` — Absolute path to a `design-ingest-*.md` manifest (when `{input_kind} == "ingest_manifest"`). Produced by the `design-ingest` workflow; carries the frame inventory + the gated per-frame section inventory + a pre-seeded grid scaffold (every (frame, section) already a row), so step 1 reads it instead of downloading/extracting and re-cataloging a large bundle in one context.
- `{ingest_manifest}` — Parsed contents of `{ingest_manifest_path}` (when `{input_kind} == "ingest_manifest"`): the `ingest:` receipt, frame inventory, section inventory, and grid scaffold rows.
- `{section_rows_source}` — `ingest_manifest` | `in_context`. Records whether the per-frame **section-coverage** rows (step-03 §2f-bis) came from a gated, reviewed `design-ingest` scaffold or were enumerated in-context on a URL/bundle run. Set in step-01 (MANIFEST.3 → `ingest_manifest`; URL/BUNDLE paths → `in_context`).
- `{design_file}` — Target design file name (e.g., `Data Quality Dashboard.html`)
- `{design_dir}` — Extracted bundle directory on disk
- `{design_components}` — Map of component name → file path within the extracted bundle
- `{design_tokens}` — Design system tokens (radii, type scale, colors, spacing)
- `{impl_page}` — Path to the SvelteKit/React/Vue page component in the codebase
- `{impl_components}` — Map of component name → file path in the project
- `{impl_config}` — Tailwind/CSS config path and key overrides (border-radius, colors, etc.)
- `{design_layout_constraints}` — Page-shell / container assertions the bundle cannot express as a component CSS value: the README's layout prose ("full-width within the content container", "never a centered max-width card", "no sidebar shell") PLUS the bundle wrapper's own width treatment (`.app` / `<body>` full-bleed vs. an explicit `max-width` + centering). Cataloged in step-01 (URL.2 README prose + the wrapper element). This is the evidence the page-shell grid row (step-03 §2d) compares against — the one structural property that lives in prose + the wrapper, not in any cataloged component.
- `{impl_page_shell}` — The implementation's EFFECTIVE container treatment for `{impl_page}`: the chain of width caps from the page wrapper UP THROUGH every ancestor layout (route layout, app shell) — each `max-width` / `mx-auto` / `padding` resolved to a concrete px value, and the tightest effective width computed (e.g. layout `max-w-[1440px]` + page `max-width:1280px` → effective 1280, centered). Also carries `injected_chrome` — any hero/banner/masthead/promo band an ancestor layout renders ABOVE `{children}` that the design's standalone frame doesn't contain (the `/settings/sku-format` hero-banner miss), each flagged `in_design_frame: bool`. Cataloged in step-02 §1a; both the width and the injected-chrome rows are emitted by step-03 §2d.
- `{design_states}` — Map of component name → list of states cataloged (e.g., `ExpenseRow → [default, hover, selected, failed, empty]`). A component with only `[default]` is the implicit baseline; any other state must be explicitly populated from the design source.
- `{design_frame_inventory}` — **URL path**: the frames the target surface declares it delivers or consumes — the primary frame, the drilled detail drawer, and each **§13 expand-in-context lookup** (the "link to records (lookups)" the design viewer lists). Derived in step-01 **URL.3a** from the traced `<script src>` modules + their "… frames/lookups consumed" comments, the per-frame banners inside those modules (`/* ==== warehouse-lookup ==== */`), the lookup→target maps in the bundle data (`app.jsx` `catalog: [… "Catalog Items.html"]`), and sibling standalone `<frame>.html` the target links to. This is step-03 §2f's frame-coverage **denominator on a raw-URL run**, where no brief §7 and no manifest exist. (Brief-driven and synthesize-bundle runs use the brief §7 / manifest instead.) Each entry: `{ frame, role: primary|drilled-detail|§13-lookup, parent, declared_in, drawn }`.
- `{design_linked_record_rows}` — The **authoritative §13-lookup denominator**: the rows the detail drawer renders in its "Linked records" / "link to records" section (each `RecordLink` — e.g. `Catalog item`, `Route warehouse`, `Shipping lane`, `Supply source`, `Inbound batch`, `Import run`). Each `{ label, drills_to_frame, order }`. Cataloged in step-01 URL.3a (source 5) by opening the detail drawer and counting its rendered linked-record rows — NOT from a comment/banner/map, which can under-enumerate. step-03 §2f reconciles `{design_frame_inventory}`'s §13-lookup frames against this list: every row must have a frame (else `LOOKUP UNDER-ENUMERATED`), and the §13-lookup count must equal-or-exceed the row count. This is the fix for "design-implement often misses the link-to-record drawers."
- `{impl_identifier_cells}` — Sub-list of `{impl_render_sites}` whose displayed text is `value_source: formatter | enum-map` AND a canonical-identifier class (marketplace, supplier, ASIN/SKU, order/batch number, currency, date, status label). Cataloged in step-02 §3d; these are the cells the grid cannot certify from a mock-data bundle and routes to the content lane (step-03 §2c).
- `{comparison_grid}` — The full component × state × property delta table
- `{delta_count}` — Number of (component, state, property) triples with non-zero deltas
- `{content_unverified_count}` — Number of `content-lane: CONTENT-LANE-UNVERIFIED` rows (step-03 §2c) — formatter-driven identifier cells routed to design-review / design-tuning, counted separately from `{delta_count}` (they are routed items, not deltas applied here).
- `{impl_token_provenance}` — List of every design-mapped CSS custom property with its resolved value AND provenance: `{ token, resolved_value, source_file, scope: canonical | per-screen, semantic_class: shared-semantic | local-constant }`. Cataloged in step-02 §5. `canonical` = defined in `tokens.css` / `globals.css @theme` (the `docs/design-policy.md` §8 ground-truth surface); `per-screen` = resolvable only from a per-screen stylesheet (migration debt, not a system token).
- `{token_noncanonical_count}` — Number of `token-provenance: NON-CANONICAL TOKEN` rows (step-03 §2g) — shared-semantic tokens (status / colour / type) that resolve only from a per-screen stylesheet, disclosed and ceded to design-review (promote-or-leave is token architecture), counted separately from `{delta_count}` and never gated.
- `{production_capabilities}` — Feature-level inventory of what the CURRENT built page does/shows (routing & sub-surfaces, §13 linked-record lookups, economics/cost-recon, composite status/header, activity/audit, bulk actions/filters, action-wired mutations) — distinct from CSS. Cataloged in step-02b §1 from step-02's outputs.
- `{handoff_capabilities}` — The same feature-level inventory for what the HANDOFF delivers (`{design_components}` + `{design_frame_inventory}` + brief §7). Cataloged in step-02b §2.
- `{dropped_capabilities}` — The regression surface: capabilities in `{production_capabilities}` with no match in `{handoff_capabilities}` — what the redesign would remove. Each `{ capability, class, prod_evidence, why_it_matters, handoff_status: absent|unclear }`. Computed in step-02b §3; a non-empty set HALTS for a strategy choice.
- `{added_capabilities}` — The net-new half of the uplift surface: capabilities in `{handoff_capabilities}` with no production match (a new analytics/disposition band, lane-by-handler segmentation, an action column, co-view tabs, a drawer the live page never had). Computed in step-02b §3; NOT "informational" — each is a build task.
- `{deepened_capabilities}` — Capabilities present in BOTH but materially richer in the handoff (a country-filter → handler-lane segmentation with counts; a flat status column → a disposition band with a verdict vocabulary + per-row action). Each `{ capability, class, prod_evidence, evidence, why_it_matters }`. Computed in step-02b §3; a build task, never "same component, restyle."
- `{uplift_capabilities}` — `{added_capabilities}` ∪ `{deepened_capabilities}` — the net-new construction surface; the symmetric twin of `{dropped_capabilities}`. A non-empty set means the job is substantially a BUILD (strategy ≥ `additive`), regardless of how clean the token mapping looks. Carried into step-03 §2h (`capability-build` tags) and step-04 (constructed; §9 enumerates each `built:`). Computed in step-02b §3–§4b.
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
- **A whole frame the bundle delivers is a mandatory grid row, even on a raw-URL run with no brief.** The component sweep is structurally blind to a frame the impl never built — it catalogs the frame's *inner* primitives (which are usually shared and DO exist elsewhere in the impl), matches them, and greens out while the whole **detail drawer** or **§13 expand-in-context lookup** ("link to records (lookups)") ships unbuilt or inferred-thin. The §7 Surface Inventory is the denominator when a brief exists — but a user who pastes a raw Claude Design URL has no brief AND no manifest, and that is the path where the lookup drawers silently vanish. The bundle declares its own frames regardless: the target HTML's `<script src>` modules + their "… lookups consumed" comments, the per-frame banners inside them, the lookup→target maps in the data, and sibling standalone `<frame>.html`. Step-01 **URL.3a** lifts these into `{design_frame_inventory}`; step-03 §2f uses it as the URL-path frame-coverage denominator (precedence: brief §7 → bundle frame inventory (URL) → manifest (bundle) → needs-human-confirm). On the URL path the frames ARE drawn, so an impl lacking the drawer is `FRAME MISSING in impl` (Tier-1). **"No brief" is not "no contract."** And because every one of those denominator sources is a *declaration* that can under-enumerate, step-01 URL.3a source 5 also captures the **authoritative** lookup denominator — the detail drawer's rendered "Linked records" list (`{design_linked_record_rows}`) — and step-03 §2f reconciles the harvested §13-lookup frames against it (every rendered row → a frame, else `LOOKUP UNDER-ENUMERATED`; §13-lookup count ≥ row count; a present-but-thin drawer is swept for depth, not greened on "it opens"). The rendered linked-record list, not a comment, is what stops the "link to record" drawers from being silently missed.
- **The bundle is a generated PROPOSAL; the spec is `docs/design-policy.md`.** The Claude Design bundle AND its README are generated *from* the project's design policy (the README says so: "policy-first; foundations derived from the policy") — so the bundle is the authoritative source for **treatment** (match its proposed pixels, that is the workflow's job) but NOT for **policy conformance**, and it can itself violate the policy (a real bundle shipped a banned colored-glow `@keyframes` + no `prefers-reduced-motion`). Therefore: read the one statically-checkable policy rule — **page-shell / layout intent — from `docs/design-policy.md`** (not the generated README), and **CEDE the rest of the policy contract — prohibitions / tone / motion / iconography — plus all interaction behavior** to the workflows that own the live evidence (`design-review`, `design-review-pr`, `verify`), via the step-03 §2e cede + step-04 §9 disclosure. Never invent a half-check (a grep for `rounded-full`, an `@keyframes` scan) and present it as conformance — a bundle-anchored check against a generated, self-violating proposal lies; an honest cede does not.
- **N/A is a valid cell.** If a property exists in the design but the implementation doesn't have that component, or vice versa — mark it, don't skip it.
- **A handoff is a proposal about treatment, NOT an authorization to delete what production does — check the regression surface BEFORE building the grid.** A redesign frequently omits a capability the live page has (a §13 linked record, a cost-recon path, an activity timeline, a dual-status header, a wired mutation) — and the component sweep greens out on the omission because the dropped capability's inner primitives exist elsewhere in the impl. Whether a drop is an intended simplification or an accidental regression is **intent**, which this workflow cannot infer. So step-02b (between map and grid) inventories `{production_capabilities}` vs `{handoff_capabilities}`, and when the handoff drops something, **HALTS and ADVISES** — a per-capability keep/drop verdict (with reasons) plus one recommended plan (`restyle-only` keep-all · `additive` · `partial` advised-mix · `replacement`) the user approves or adjusts — rather than silently reproducing the omission OR offloading the keep/drop list to the user to assemble. This is the proactive front end to step-04 §9's orphaned-action backstop. Autonomous mode defaults to the non-destructive keep-all and discloses; it never silently replaces.
- **The capability delta is SYMMETRIC — a redesign that ADDS capability is as load-bearing as one that drops it, and the workflow must BUILD the add, not read it as a reskin.** The regression rule above guards the DROP direction; this guards the ADD direction, the equal-and-opposite failure. When the handoff adds (a new analytics/disposition band, lane-by-handler segmentation, an action column, a co-view, a drawer) or materially DEEPENS (a country-filter → handler-lane segmentation; a flat status → a disposition band) a capability the live page lacks, the component sweep is structurally blind to it the same way it is blind to a drop — it greens the shared shell and at most flags the new sub-components `MISSING`, so the run reads a substantial uplift as "treatment alignment." step-02b §3–§4b therefore inventories the delta BOTH ways, names the uplift (`{uplift_capabilities}`), sets strategy ≥ `additive`, and carries every added/deepened item to step-03 §2h / step-04 as a `capability-build` task. An uplift that ships unbuilt is the exact mirror of a kept capability that ships removed. Autonomous mode BUILDS the uplift (implementing the handoff is decision autonomy); it never defaults an uplift to `restyle-only`.
- **Scope is an OUTPUT of the capability delta, never a prior — do not run blind.** "This is restyle-only / treatment-only / token alignment / a structural superset / no net-new capability" is a *capability-scope* verdict and may be asserted ONLY after step-02b §3 has computed the bidirectional delta and found DROPPED **and** `{uplift_capabilities}` both empty. A clean token mapping (raw-hex → canonical-token debt, a resolvable `var(--*)`) is *treatment* evidence — a step-03 grid signal — and it can never license a scope conclusion. Forming "just tokens / production is a superset" from treatment evidence, *especially while step-02 is still resolving production*, is the running-blind failure: it read the inbound-flow supply-orders uplift (lanes + analytics/disposition band + action column + co-views, all net-new) as a reskin. Inventory both capability surfaces first; let the verdict fall out of §3.
- **Apply is grid-driven and fully accounted.** Step-04 walks the grid row by row; every row ends with an explicit disposition (`applied` / `deferred(reason)` / `dropped(reason)`), and the completion report ALWAYS enumerates what was not applied (or states "all N applied"). A holistic "rebuild until it looks like the design" pass that silently drops enumerated rows is the failure the step-04 apply ledger exists to prevent — exhaustive cataloging (above) is worthless if the apply isn't equally accountable.
- **The grid certifies treatment, structure, state, and multiplicity — NOT the content lane.** design-implement compares the implementation against the design *bundle*, and the bundle renders **seeded mock data**, not real production data. So any defect that lives in *what a value-formatter renders* — a canonical-identifier class (marketplace, supplier, ASIN/SKU, order/batch number, currency, date, status label) shown in the wrong form, a raw enum leaking where a human label belongs (`amazon_us` instead of `US` / `Amazon US`), or inconsistent casing/label-form across sibling surfaces — is **invisible to this workflow by construction**: the formatter is wrong only on a real-data variant the mock bundle never contained, so there is no grid delta to find, and a bundle string-match (mock `UK → UK` vs impl `UK → UK`) "passes" while the real render (`US → amazon_us`) is broken. This is the **content lane** (project design policy §13 "Canonical identifier" / §13a) — owned by `design-review` (live Chrome audit, §13(a) check) and `design-tuning` (step-02 §2b, run against the LIVE page). design-implement does **not** certify it and must not pretend to from a mock-data bundle; instead it **flags formatter-driven identifier cells as `content-lane-unverified` (step-03 §2c) and routes them to those workflows through the apply ledger (step-04 §5/§9)** rather than silently passing them. This is the same treatment / composition / content three-lane model `design-tuning` and `design-review` use: design-implement owns treatment + structure and explicitly **cedes** the content lane to the live-page workflows.
- **Bundle gating is non-negotiable when consuming a design-synthesize bundle.** When `{input_kind} == "synthesize_bundle"`, step 1 MUST parse `bundle/manifest.yaml` and refuse the bundle (halt with the diagnostic in §"Input Resolution") if EITHER of the following is true:
  - `synthesis.dev_no_render: true` — the bundle was emitted without a screenshot (development mode) and is explicitly not production-ready.
  - `visual_review.needs_human_review: true` — `design-synthesize`'s self-critique (step 6 d/e/f) flagged the bundle as needing human design review before implementation. Reasons can include `visual_quality: weak`, `visual_lift_over_baseline: false`, or `exemplar_alignment: deviated_unauthorized`. Implementing a flagged bundle would pixel-lock a design that the synthesizer itself doesn't trust.

  These are bounce-back refusals, not soft warnings. The workflow halts BEFORE step 2 and prints the next-step command (re-run `design-synthesize` or route through `design-review`). This preserves the contract: bundles that `design-synthesize` doesn't trust never become implementations.

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

- **Claude Design artifact URL** — `https://api.anthropic.com/v1/design/h/...`. Sets `{input_kind} = "claude_design_url"`.
- **Local design-synthesize bundle directory** — an absolute path to a directory containing `manifest.yaml`, `<screen>.html`, and `tokens.css`. Sets `{input_kind} = "synthesize_bundle"`.
- **`design-ingest` manifest file** — an absolute path to a `design-ingest-*.md` file (the durable artifact produced by the `design-ingest` workflow). Sets `{input_kind} = "ingest_manifest"`. This is the preferred path for a large bundle: `design-ingest` has already fanned out per-frame, enumerated every section under its completeness gate, and emitted a reviewed grid scaffold — so step 1 reads the manifest and skips download/extract + re-cataloging entirely.

Detection rule, in order: (1) starts with `http://` or `https://` → URL; (2) a file path ending `.md` whose basename starts `design-ingest-` AND whose frontmatter has `ingest.workflow: design-ingest` → ingest_manifest; (3) a directory containing `manifest.yaml` → synthesize_bundle. If none matches, halt with: `"input must be a Claude Design URL (https://...), a design-ingest-*.md manifest, or a directory containing manifest.yaml. Got: <input>"`.

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

If neither refusal fires, set `{design_dir} = {bundle_dir}` and `{design_file}` defaults to the first entry in `{bundle_manifest}.screens` (use `<screen>.html` resolution within `{bundle_dir}`). Continue to step 1, which will skip the URL download path and read directly from `{bundle_dir}`.

#### When `{input_kind} == "claude_design_url"`: existing flow

Store as `{design_url}` and `{design_file}`. Continue to step 1.

#### When `{input_kind} == "ingest_manifest"`: manifest gating

Parse `{ingest_manifest_path}` into `{ingest_manifest}`. Then check one refusal gate — the completeness invariant the `design-ingest` workflow is required to uphold:

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

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/design-implement`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-01-ingest-design.md` to begin.
