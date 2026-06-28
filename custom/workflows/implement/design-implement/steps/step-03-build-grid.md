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
| Page shell | default | injected chrome (hero/banner/masthead) | none in the design frame (the bundle renders the frame standalone) — OR the design's own header band if it drew one | `{impl_page_shell.injected_chrome}` (e.g. `<InboundHeroBanner> in settings/layout.tsx — hero image + title + subtitle above the worklist`) | difference or `✓` |

Rules:
- **A width or centering mismatch is Tier-1 structural** (§4) — it reframes the entire composition, not one component. A `max-width` cap the design doesn't call for (or a missing one the design does) is the headline, not a nit.
- **An ancestor-injected hero / banner / masthead the design frame doesn't contain is Tier-1 structural.** When `{impl_page_shell.injected_chrome}` lists a band an ancestor layout renders above `{children}` and its `in_design_frame` is false, the impl is shipping prominent chrome the design never drew — emit the injected-chrome row as Tier-1 (it reframes the whole page, exactly like a width cap, and a hero/banner above a working table is independently a `docs/design-policy.md` §5 hard failure). This is *not* the policy cede (§2e): the band is **visible in the layout files the §1a walk already read**, so design-implement can name it directly — an add, not a cede. The fix routes to removing/scoping the ancestor chrome (the layout wrapper), not to any component in the grid. *Direction matters:* the **design frame is authoritative** here — if the design drew a compact header and the impl injects a tall photographic hero, that is the delta; if the design itself drew a band and the impl omits it, that is the (rarer) inverse delta. The bundle rendering standalone (no app shell) is why the band isn't in `{design_components}` — absence from the bundle is NOT license to keep an injected hero the design's composition excludes.
- **An ancestor-injected chrome matching the brief's `shell_role.forbidden_chrome` is Tier-1 — the owner-nav-on-a-clerk-station case.** When the matched brief carries `shell_role` (`brief-revision-policy.md` §2 Block B) and `{impl_page_shell.injected_chrome}` (step-02 §1a) lists a band whose identity matches `forbidden_chrome` — e.g. the owner global nav rendered by a root layout above a `(clerk)` surface — emit it as a Tier-1 injected-chrome row **regardless of whether the design frame drew any header**: the contract explicitly forbids that chrome here, so the named prohibition overrides the usual "design frame is authoritative" direction. The fix routes to scoping the ancestor chrome to its own role (move the nav out of the shared root layout / gate it by route-group), never to a component in the grid. This is the impl-side twin of step-01 §SHARED.1b's bundle shell check: §SHARED.1b catches the *proposal* drawing the wrong chrome; this catches the *runtime* shell injecting it. When the brief has no `shell_role` (or `no_brief`), this degrades to the hero/banner rule above (`docs/design-policy.md` §5) — disclosed as `UNVERIFIED(shell)`, never silent.
- **Silence is not a pass.** If the README was silent but the bundle wrapper is full-bleed (`{design_layout_constraints}` resolved `full-bleed`), an impl `max-width` cap is STILL a delta — the row is emitted and scored, never skipped for "the design didn't say."
- **Surface a house-convention divergence, don't auto-spread it.** If step-02 §1a noted that sibling pages share the impl's cap, say so in the Delta cell (`divergence: design wants full-width, but catalog/supply-sources/… also cap at 1280 — confirm scope`). The apply (step-04) fixes THIS page to the design; widening every sibling is a separate, deliberate decision, not a silent sweep.
- **The Design column is authoritative ONLY from the policy.** Use the `{design_layout_constraints}` entry marked `authoritative: true` (the `docs/design-policy.md` rule) as the binding Design value. If only `README-generated` / `bundle-wrapper` entries exist (no policy found), still emit the row but mark the Delta `needs human confirmation` rather than a hard Tier-1 — the bundle and its generated README are not authoritative on their own (see §2e).

### 2d-list. List-rendering row — emit one when the brief requires pagination / virtualization

The component sweep is blind to whether a growing list actually paginates: it compares row pixels, not whether the table renders **all N rows** or pages them. So a brief that requires `paginate` / `virtualize` / `load-more` (`{brief}.list_rendering`, set by design-handoff §5g from the captured Data volume) can ship as a single un-paginated render with an **all-green component grid** — the page-shell blind spot one level down, at the list level. This is the impl-side enforcement of the §5g derivation: the gather makes pagination a *requirement*, this makes a build that omits it *fail*.

When `{brief}.list_rendering` is **not** `single-render` (skip when `single-render`, empty, or `no_brief`), emit ONE List-rendering row for the primary list frame:

| Component | State | Property | Design (brief) | Implementation | Delta |
|---|---|---|---|---|---|
| Primary list | default | row-rendering mechanism | `{brief.list_rendering}` (e.g. `paginate` — the §5g requirement on the primary list frame) | the impl's actual list rendering (page controls + a count / windowed-virtualized rows / a load-more affordance — or **none: all rows rendered**) | e.g. `required paginate vs renders all rows → Tier-1` or `✓` |

Rules:
- **A required list-rendering mechanism that is ABSENT is Tier-1 structural** — a growing worklist that renders every row is exactly the gap §5g exists to close; it is the headline, not a nit. The fix is a list-rendering change on the primary surface, owned by no single cataloged component (like the page shell).
- **The brief is authoritative.** `list_rendering` comes from design-handoff §5g (volume-derived), NOT from inspecting the bundle. On a `no_brief` / raw-URL run with no `list_rendering`, skip the row and mark `UNVERIFIED(list-rendering)` in the §9 report rather than invent a threshold — the requirement is the brief's to set (same posture as the §2e policy cede).
- `single-render` (or a non-list `detail` surface) ⇒ no row.

### 2d-bis. Frame-composition row — emit one per DRILLED frame (detail / create / lookup drawer), the drawer analog of the page shell

§2d catches the **page** container's composition; this catches a **drilled frame's** composition. The component sweep (§2) compares each section's *inner* pixels and §2f-bis certifies each design section *exists* — but neither compares **how the frame is composed as a whole**: the order its sections appear in, how they are grouped under named headings, and the frame's own chrome (its header and footer). That is exactly the axis a user reads as "the drawer looks completely different" — the same data, renamed/regrouped/reordered. It is structurally invisible to §2 (no single component owns the arrangement) and to §2f-bis (a section can be present, deep, and pixel-matched while sitting in the wrong group, in the wrong order, under a renamed heading). This is the page-shell blind spot (PR #2017) one level deeper, inside the drawer — and the real inbound-flow supply-order miss: the design's **Cost & sourcing** / standalone **Lifecycle** / **Related records** groups ship as the impl's **Economics** / a status row folded into the header / a combined **Routing & source** group, plus a black-vs-blue footer button — every inner component "matching" while the drawer's composition is wrong.

For EACH frame whose `role` is `drilled-detail`, `create`, or `§13-lookup` (the manifest `Frame inventory`, or `{design_frame_inventory}` on a URL run), emit ONE Frame-composition row. The Design column comes from the frame's section list **in render order** + its group headings + its header/footer chrome (the manifest section inventory carries all three; on a URL/bundle run, read them from the frame source). The Implementation column comes from the impl frame component's actual rendered section order + group headings + footer (step-02's frame map):

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| {frame} shell | default | section order | design section sequence (e.g. `Product · Block · Reconciliation · Cost & sourcing · Lifecycle · SellerSmart dispatch · Related records · …`) | impl rendered sequence | reordered/missing → Tier-1 |
| {frame} shell | default | group naming + grouping | design group headings (e.g. `Cost & sourcing`, standalone `Lifecycle`, `Related records`) | impl headings (e.g. `Economics`, status-in-header, `Routing & source`) | renamed/merged/split group → Tier-1 |
| {frame} shell | default | frame chrome (header + footer) | design header (title/dual-status/breadcrumb) + footer (button label/treatment + cross-link, e.g. black `Accept gap` + `Open full order →`) | impl header + footer (e.g. blue `Mark received` + `Cancel`) | difference → Tier-1 |

Rules:
- **A reordered / renamed-group / regrouped composition is Tier-1 structural**, not a per-component nit — it reframes the whole drawer exactly as a width cap reframes the page. Count it in `{delta_count}`. The fix (step-04) is to rebuild the frame's arrangement to the design, not to recolour one component inside it.
- **The frame's footer (and any chrome not owned by a cataloged section) is in scope here.** A drawer footer that isn't a section row would otherwise have NO grid row — its button treatment/labels (black `Accept gap` vs blue `Mark received`) would slip entirely. This row is where it is compared (it dovetails with the step-04 §5b chrome transcription, which owns the literal-copy half).
- **Section EXISTENCE stays §2f-bis; composition is the arrangement of those sections.** Do not duplicate the missing-section finding here — §2d-bis assumes the section set and asks whether it is ordered/grouped/framed like the design. A section that is both missing AND would change grouping is one §2f-bis row + one §2d-bis note, not double-counted.
- **Carries `{frame_composition_deltas}`** (set at step-02b when a present frame is flagged materially recomposed) — every frame named there MUST have a Frame-composition row here; a recompose surfaced at preflight that never became a grid row is the leak this closes.

### 2e. Policy-conformance, prohibitions, and behavior — CEDED, not checked (the bundle is a generated proposal, not the spec)

The bundle and its README are **generated by Claude Design from `docs/design-policy.md`** — they are a *proposal*, not the contract, and they can themselves violate the policy (a real bundle shipped a colored-glow `@keyframes` pulse + no `prefers-reduced-motion`, both banned by the very policy it was scaffolded from). So design-implement, which diffs the impl against that bundle, **cannot certify policy conformance** — matching a bundle that breaks the policy faithfully reproduces the break and scores `✓`. Three dimensions are therefore CEDED here (the same disclosure model as the content lane §2c), never faked into a grid check:

1. **Prohibitions / anti-patterns** — the policy's "never" list (colored/glow shadows, ambient gradient, `rounded-full` pill + leading dot, AI-purple accent, hover-lift, animated counters, emoji-as-icon, …). A bundle-diff structurally cannot catch an *introduced* banned pattern — there is nothing in the bundle to diff against (and if the bundle itself contains the ban, the diff says `✓`). **Owner: `design-review-pr`** (`S-`/`L-`/`C-` DOM+source checks) and `design-review` (live audit) — both already enforce `docs/design-policy.md`.
2. **Tone / motion / iconography contracts** — sentence-case, status-verbs, the error format, "no emoji"; opacity+translate-only / 120–200ms / `prefers-reduced-motion`; Lucide stroke/size, no colored icon halos. These live in policy prose, not in a per-component CSS value the bundle can supply. **Owner: `design-review` / `design-review-pr`.**
3. **Behavior / interaction wiring** — drawer push/pop/return stacks, Esc handling, the pull/mutation flow, live-SSE, sort/filter round-trips. The grid is treatment-only; it never executes a handler, so a pixel-perfect surface that doesn't open the drawer or return up the stack scores `✓`. **Owner: `verify` / `design-review` (live).**

Emit ONE **Ceded-dimensions** note in the grid (not a delta, not counted in `{delta_count}`):

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| Page (whole) | — | `ceded: policy-conformance + behavior` | `docs/design-policy.md` (prohibitions/tone/motion) + JSX handlers | not certifiable from a generated bundle-diff | `CEDED → design-review / design-review-pr (policy) · verify (behavior)` |

It carries into the step-04 §9 report's disclosure so the run says "treatment + structure + page-shell verified; policy-conformance + behavior were NOT — run design-review / verify on the live page," never implying the grid covered them. Do **not** invent a half-check (a grep for `rounded-full`, a scan for `@keyframes`) and present it as conformance — a partial, bundle-anchored check that lies is worse than an honest cede to the workflow that owns the live evidence.

### 2f. Frame-coverage rows — every frame the brief promised must exist in the bundle AND the impl

The component sweep (§2) is structurally blind to a **whole frame** the bundle never contained — exactly the way it was blind to the page-shell (§2d). A brief's **§7 Surface Inventory** enumerates the frames this page must deliver: the primary surface, the drilled **detail drawer**, and one **lookup drawer** per linked record (design-handoff Deliverable-Completeness Principle). If Claude Design drew only the primary frame and skipped a drawer, there is nothing in the bundle to catalog, so `{design_components}` simply omits it and every component row goes green — while the drawer ships *inferred* (the thin, bare-`€60` drawer the inventory exists to prevent). So cross-check the promised frames against what was actually drawn and built — never let an absent frame pass by omission.

**Load the contract — three sources, in precedence order.** The frame-coverage denominator is "every frame this surface must deliver." Resolve it from the most authoritative source available to THIS run — and never conclude "no source" without checking all three:

1. **Brief §7 Surface Inventory — authoritative on what was *promised*.** Read the active brief's §7 for this page (the design-handoff artifact for `{page-slug}`). Enumerate frames by **Frame name** — the contract key. Use this whenever a brief is available (brief-driven and synthesize-bundle runs).
2. **URL path, no brief — the bundle's OWN declared frame inventory (`{design_frame_inventory}`, step-01 URL.3a).** When the user hands a raw Claude Design URL there is no brief AND no manifest — but the bundle declares its frames itself: the target HTML's `<script src>` modules + their "… lookups consumed" comments, the per-frame banners inside them (`/* ==== warehouse-lookup ==== */`), the lookup→target maps in the data, and sibling standalone `<frame>.html`. This is the denominator on the URL path — readable evidence the run already traced in step-01, not an invented list. Emit **real** Frame-coverage rows (the bundle IS authoritative on what it delivers — same add-not-cede posture as page-shell §2d). On this path the frames are `drawn: true`, so the live verdict is `FRAME MISSING in impl` (Tier-1) whenever the impl lacks the drawer/lookup.
3. **Bundle path, no brief — the manifest frame set.** Mark every Frame-coverage Delta `needs human confirmation` rather than Tier-1 (the manifest is the synthesizer's claim, weaker than a brief).

If NONE of the three yields a frame set, say so and mark the block `needs human confirmation` — never silently skip frame coverage. **A run that emits zero Frame-coverage rows because "there was no brief" is the exact URL-path false-green this section closes:** the lookup drawers `Orders.html` consumes (warehouse / inbound-batch / import-run / accounting-outcome / catalog / supply-source — the "link to records (lookups)") are declared in the bundle itself. "No brief" is not "no contract."

**Reconcile the §13-lookup frames against the AUTHORITATIVE denominator — the detail drawer's rendered "Linked records" list (`{design_linked_record_rows}`, step-01 URL.3a source 5).** The three contract sources above are all *declarations* (a brief, script comments, a manifest) and can under-enumerate — which is how a linked-record drawer silently goes unchecked against Claude Design ("the workflow often misses these"). The detail drawer's own **Linked records section is the ground truth**: it renders exactly one row per lookup that must drill to a frame, so its row count is the floor for `§13-lookup` coverage. Before emitting Frame-coverage rows, cross-check:

- **Every row in `{design_linked_record_rows}` MUST have a `role: §13-lookup` Frame-coverage row.** A linked-record row with no matching frame in the contract is `LOOKUP UNDER-ENUMERATED` — the harvest (sources 1–4) missed it. Emit a Frame-coverage row for it anyway, denominated from the rendered row, with Delta `LOOKUP UNDER-ENUMERATED → re-trace bundle for this lookup's frame; if absent, needs human confirmation`. NEVER let a rendered linked-record row produce zero Frame-coverage rows — that is the precise "missed it" failure. (Live example: the Orders detail drawer draws `Catalog item · Route warehouse · Shipping lane · Supply source · Inbound batch · Import run` — six rows; `Shipping lane` is exactly the row a script-comment harvest drops, so it must surface here from the rendered list, not from a comment.)
- **The §13-lookup Frame-coverage count must equal or exceed `len({design_linked_record_rows})`.** If it's lower, a lookup is unaccounted — stop and reconcile, do not proceed to the per-frame sweep with a short denominator.
- This reconciliation is denominator-source-agnostic: it runs on the brief path AND the URL path AND the manifest path. The Linked-records list is authoritative over all three because it is what the surface actually renders, not what a declaration claims.

**Emit one Frame-coverage row per promised frame** (always emit the block, even when only the primary frame exists):

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| Frame: {frame_name} | — | `frame present` | brief §7 (required) | {drawn in bundle? built in impl?} | {✓ \| `FRAME NOT DRAWN in bundle → route to design-handoff / Claude Design re-render` \| `FRAME MISSING in impl → Tier-1`} |

Rules:
- **A promised frame absent from the bundle is NOT a fixable delta — it is routed**, like the content lane (§2c). `design-implement` cannot draw a drawer Claude Design never rendered; matching pixels presupposes pixels. Mark it `FRAME NOT DRAWN → route to design-handoff / Claude Design`, count it in `{frame_uncovered_count}` (separate from `{delta_count}`), and disclose it in §9. Inferring the drawer to "fill the gap" is the exact failure this axis exists to forbid.
- **A frame drawn in the bundle but absent from the impl is Tier-1 structural** (`FRAME MISSING in impl`) — the drawer was designed and not built. This one IS actionable here.
- **A frame present in both** runs the full §2 component × state × property sweep *within that frame* (a drawer's own pills, money cells, lookups get the same per-property rigor as the page) — the Frame-coverage row only certifies the frame exists; the components inside it are still compared normally. **"Present" means the impl drawer is as DEEP as the bundle drew it — not merely that a drawer opens.** A lookup drawer that ships *inferred-thin* (the bundle drew a rich warehouse lookup — address, contact, throughput, lane bindings — and the impl renders a bare `code — name` stub) has a present frame whose interior is missing rows: catalog the bundle frame's full component set and sweep ALL of it against the impl drawer, so the missing interior surfaces as `MISSING in impl` rows, not a false `✓` on "the drawer exists." Frame-present is necessary, not sufficient.
- **A `LOOKUP UNDER-ENUMERATED` row (from the `{design_linked_record_rows}` reconciliation above) is routed, not silently dropped.** It means a rendered linked-record row had no harvested frame — the harvest, not the design, is incomplete. Count it in `{frame_uncovered_count}`, surface it in §9 with the re-trace / needs-human-confirmation routing, and never let "I only found N frames" override "the drawer renders N+1 linked-record rows." The rendered list wins.
- **Drawer money cells inherit the content-lane (§2c) and policy-cede (§2e) rules** — a drawer's `€60`-style figure is bundle-mock data; its basis-completeness (`docs/design-policy.md` §15) is policy-conformance, ceded to design-review, not certified here. The Frame-coverage row certifies the drawer was *drawn and built*; whether its money is basis-complete is design-review's call.

### 2f-bis. Section-coverage rows — every top-level SECTION of every present frame is a mandatory grid row

Frame-coverage (§2f) is **frame-granular**: it certifies "the drawer exists / is built," and §195 already says a present frame must be as DEEP as the bundle drew it. But §2f's *denominator* is the frame list — it has no row per **top-level section** of a present frame, so a whole section dropped *inside* an otherwise-present frame slips through: the section's inner primitives (pills, money cells, tiles) are shared and match elsewhere in the impl, so the component sweep greens out over the absence. This is the exact miss that shipped a present Supply-Order drawer with **no Reconciliation block** and **no SellerSmart-dispatch section** while every component row was ✓. Frame-present is necessary; section-complete is the missing axis.

**The denominator is the frame's top-level section list. Resolve it in precedence order:**

1. **`ingest_manifest` scaffold — authoritative.** When `{section_rows_source} == "ingest_manifest"` (step-01 MANIFEST.3), the `design-ingest` manifest's Grid scaffold already carries one reviewed, completeness-gated row per `(frame, section)`. Use it verbatim — the enumeration was done exhaustively, per-frame, under `design-ingest`'s frame-completeness gate, and reviewed at its handoff. This is the path that structurally cannot under-enumerate. **Resume/scope budget note:** the full row SET is always carried (the contract stays complete), but compute design-vs-impl deltas ONLY for the in-scope UNVERIFIED rows — rows already `✓ applied` in `{resume_prior_dispositions}`, or outside `{frame_scope}` if set, are carried forward with their existing disposition and do NOT get their design/impl files re-read here. This keeps a resume session from spending its budget re-cataloging frames a prior pass already finished (the grid build is itself read-heavy — re-deriving deltas for done frames is the budget leak a checkpoint is meant to avoid).
2. **In-context enumeration — URL / bundle path.** When `{section_rows_source} == "in_context"`, enumerate each `drawn: true` frame's top-level sections HERE, the same way `design-ingest` step-02 does: read the frame source fully, list every section (`<h4>`/`grp`/`data-region` block, conditionally-rendered banner) in render order. An empty section list for a drawn primary or detail frame is the under-enumeration defect — do not proceed with a frame that has zero section rows.

**Emit one Section-coverage row per (present frame, section)** — always, even when the frame is otherwise green:

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| {frame} / {section} | — | `section present` | design renders it ({verbatim heading/copy}) | {present & aligned? present w/ delta? absent?} | {✓ \| `SECTION MISSING in impl → Tier-1 structural` \| `COPY-DELTA` \| `STRUCTURE-DELTA`} |

Rules:
- **A section the design renders that the impl frame lacks is Tier-1 structural** (`SECTION MISSING in impl`), counted in `{delta_count}` — it is actionable here (build the section), unlike a not-drawn *frame* (which is routed). If the section needs view-model fields the impl lacks, flag per the data-availability lane (do not fabricate), same as the content-lane cede.
- **A present section still runs the full §2 component × state × property sweep within it** — the Section-coverage row certifies the section exists; its components are compared normally. "Present" means as deep as the design drew the section, not merely that a heading exists (the §195 inferred-thin rule applies at section granularity too).
- **Never collapse a frame to one row.** A drawer with 10 design sections produces 10 Section-coverage rows. A run that emits one "drawer ✓" row and moves on is the precise false-green this gate closes.
- Section-coverage uncovered items count in `{delta_count}` (missing sections are actionable deltas), distinct from `{frame_uncovered_count}` (routed not-drawn frames).

### 2g. Token-provenance row — a shared-semantic token resolved only from a per-screen stylesheet (DISCLOSE + cede, never gate)

A `var(--*)` that resolves cleanly is **not automatically a clean "1:1" mapping** — *which layer* it resolved from is a distinction the project's token precedence treats as load-bearing. `docs/design-policy.md` §8 names the **canonical token surface** narrowly: `src/styles/tokens.css` + the `@theme inline` block in `globals.css` are "ground truth for what exists in the system," and the v3 note marks the ~25 per-screen stylesheets as migration debt. So a design token (e.g. `--status-success-text`) that the impl resolves **only from a per-screen file** (`supply-orders.css` lines 34–50) is resolvable at runtime but is **not a system token** — and a *status / colour / type* token in that position is the exact cross-surface-drift risk §3/§13 forbid (the same status reads a different colour on a sibling surface that doesn't load that screen's CSS). The miss this section closes is the run that resolves such a token, finds it "defined somewhere," and collapses it into "the mapping is effectively 1:1" — papering over real design debt.

**But promote-or-leave is token *architecture*, which design-implement does NOT own** — the same boundary as the policy cede (§2e). The token works on this screen; whether it should be lifted into `tokens.css` is a refactor call for `design-review` (or the owner), not a gate that blocks this render. So design-implement **discloses and cedes**, it does not gate or thrash:

For every token in `{impl_token_provenance}` (step-02 §5) with `scope: per-screen` **AND** `semantic_class: shared-semantic`:

1. **Do NOT gate the render and do NOT score it a Tier-1/2/3 delta.** Its treatment rows (the resolved colour value, radius, font) are compared normally in §2/§2b — a per-screen token whose *value* differs from the design is still a real colour delta there. §2g is only about the token's *placement*, which is not a pixel the grid can fix.
2. **Emit one Token-provenance row** — fixed shape, not a delta, not counted in `{delta_count}`:

   | Component | State | Property | Design | Implementation | Delta |
   |-----------|-------|----------|--------|----------------|-------|
   | {token} | — | `token-provenance: {semantic_class} resolved per-screen` | canonical surface (`tokens.css` / `@theme`) | resolved only from `{source_file}` (not canonical) | `NON-CANONICAL TOKEN → cede promote-or-leave to design-review (token architecture)` |

3. **A `local-constant` per-screen token is NOT flagged** — a one-off spacing/layout var with no cross-surface contract legitimately lives local; disclosing it would be noise. Only shared-semantic tokens (status / colour / type) earn the row.
4. **Never "resolve" the debt by declaring 1:1.** Finding the token in a per-screen stylesheet is not evidence the mapping is canonical — it is the evidence it is *non*-canonical. The bundle being generated from that same per-screen CSS does not launder it; a generated bundle is a proposal, not the spec (§2e).

Count these as `{token_noncanonical_count}` (separate from `{delta_count}` — disclosure items, not deltas applied here). They carry into the step-04 §9 report under "Token provenance (non-canonical)" with the cede routing, so the run says "these tokens resolve only from per-screen CSS — promotion to the canonical surface is a design-review call" rather than implying the token mapping was clean.

### 2h. Flag protected-capability AND build-capability rows (honor the step-02b strategy)

Before counting, reconcile the grid against `{capability_dispositions}` and `{uplift_capabilities}` (step-02b). The chosen `{implementation_strategy}` governs what the apply removes AND what it builds:

**Protected (the DROP side).** Any grid row whose effect would **delete or strip a capability the user marked `keep`** (a §13 lookup drawer, a cost-recon/economics surface, an activity timeline, a wired action — anything in `{production_capabilities}` disposed `keep`) is tagged **`capability-protected`**. The handoff's treatment is applied *around* the kept capability; the capability itself is not removed just because the new design's frame omits it. Step-04 disposes these `⊘ deferred(capability-protected)`, never `applied`. (For `replacement` / dropped capabilities, no flag — the handoff governs and step-04 §9's orphaned-action check confirms the removal is clean.) If `{implementation_strategy}` is `restyle-only`, treatment rows apply normally but **no** row may remove any capability — the whole point of that strategy.

**Build (the ADD/DEEPEN side).** For every item in `{uplift_capabilities}` (ADDED / DEEPENED), the new structure it requires shows up in the component sweep as `MISSING in impl` rows — a country-filter that became handler-lane segmentation flags its lane chips MISSING; a new analytics/disposition band flags its counters/strips MISSING; a new action column flags its buttons MISSING. **Tag every such row `capability-build`, not a stray treatment nit.** A `capability-build` row is NOT "the impl is missing a class" — it is "a net-new capability must be constructed." Step-04 BUILDS these (not "skip, nothing to align toward"); the §9 report enumerates each as `built:`. A `capability-build` row left unbuilt is a Tier-1 failure, the mirror of a `capability-protected` row that shipped removed. The treatment of any *shared shell* a deepened capability sits in still flows through the grid normally — only the net-new sub-structure is `capability-build`. **Never let a `capability-build` row be silently dropped as "MISSING component → out of scope for a restyle"**: the step-02b uplift inventory is exactly what makes these in-scope.

### 2i. Foundation-token reconciliation row — the design SYSTEM's foundation vs the app's CANONICAL tokens vs the POLICY (the page-shell of the type / radius / control scale)

§2 property #2 compares a *component's* font-size; §2g checks a token's *placement* (canonical vs per-screen). NEITHER catches the defect behind the most pervasive "the whole surface looks different" miss: the impl token resolves cleanly **from the canonical surface**, but that canonical **value** disagrees with the design system's foundational scale and with the value `docs/design-policy.md` declares. A button styled `font-size: var(--font-size-base)` greens against a design button styled `font-size: var(--font-size-base)` — byte-identical declarations — while one resolves to the bundle's 13px and the other to the app's 16px. **No component owns the type scale**, so no component row can see it: this is the page-shell blind spot (§2d) one layer down, at the token foundation. It is the real inbound-flow held-orders miss (PR #2412): the app ships `--font-size-base: 1rem` (16px) against a policy that declares 13px "corporate density," every ported surface renders ~23% large and re-wraps, and the implementer — given no sanctioned way to flag a *wrong canonical token* — encoded the design's 13px as `var(--font-size-base, 0.8125rem)`, a **dead fallback** the defined global silently overrides.

**Reconcile the FOUNDATIONAL tokens three ways** — the tokens no component owns but every component inherits: the **type scale** (`--font-size-base/-sm/-xs/-md`), **control heights** (`--control-h/-sm`), the **radius scale** (`--radius/-md/-lg`), and the **status-colour set** (`--status-*`). For each, compare:

1. **Design system value** — `{design_foundation_tokens}` (step-01 URL.4 / BUNDLE.3), resolved to px/hex. What the bundle's foundation declares. On the raw-URL path this comes from the bundle's `tokens/*.css` CSS custom properties — **not** the JSX theme object — which is why URL.4 was extended to read them; without it the design side of this comparison has no resolved value and the axis silently no-ops (the missing-source-on-one-path failure §2f closes for frame inventory).
2. **App canonical value** — `{app_canonical_scale}.app_value` (step-02 §5a) — what `src/styles/tokens.css` + the `globals.css @theme` block actually define (the §8 canonical surface, "ground truth for what exists").
3. **Policy-declared value** — `{app_canonical_scale}.policy_declared_value` (step-02 §5a) — what `docs/design-policy.md` DECLARES canonical (§4 "Body text is 13px by default"). **The policy is the spec** (§2e: the bundle is a proposal, the policy is the contract); the app token is merely "what exists," and can violate it.

Emit one **Foundation-token row** per foundational token where the three do NOT all agree (skip the ones that agree — no noise):

| Component | State | Property | Design | Implementation | Delta |
|-----------|-------|----------|--------|----------------|-------|
| Foundation: {token} | — | `foundation-token: {scale} value` | design `{design_value}` · policy `{policy_value}` | app canonical `{app_value}` ({source_file}) | `FOUNDATION-TOKEN DRIFT ({kind}) → route to apply-design-policy-change (token migration); do NOT patch in-component` |

`{kind}` is one of:
- **`app-violates-policy`** — the headline. The app's canonical token disagrees with the value `docs/design-policy.md` declares (app `--font-size-base: 16px` vs policy's 13px). EVERY ported surface inherits the defect; the app violates its own policy. The debt is often already written in the policy's own changelog ("flagged, not auto-migrated") — quote it if present, it is the documented origin.
- **`design-vs-app`** — the bundle's foundation value disagrees with the app's canonical value (bundle 13px vs app 16px), independent of policy. The design was built on a denser scale than the app ships.

Rules:
- **A foundation-token drift is NOT a fixable-here delta — it is ROUTED**, like the content lane (§2c), the policy-less page-shell (§2d), and the policy cede (§2e). The ONLY correct resolution is a **single-source token migration** — align `src/styles/tokens.css` to the policy-declared scale, once, for the whole app — which is `apply-design-policy-change`'s job, never a per-surface edit. Count it in `{foundation_token_drift_count}` (separate from `{delta_count}`); surface it in §6 and §9.
- **BAN the per-component "fix" — and ban the dead fallback hardest.** Do NOT resolve a foundation drift by editing each component's `font-size`/`border-radius` to the design literal, and NEVER write the design value as a `var(--token, <literal>)` fallback: a fallback fires ONLY when the variable is undefined, so when the app defines the global it is an **inert no-op** that reads as "the design value is encoded" while rendering the wrong one. This is the #2412 anti-pattern — the *fourth* wrong encoding of the same divergence after hardcoded-px screens, no-fallback screens, and the dead fallback. If step-02 §5a found an existing `var(--*, <rem/px-literal>)` whose global IS defined (`{app_canonical_scale}.dead_fallback_sites`), surface each here as `DEAD-FALLBACK (inert) → the defined global overrides it; remove and reconcile the token`.
- **Treatment rows still apply normally.** A foundation drift does NOT block the rest of the grid — other (component, state, property) deltas are applied as usual. §2i forbids "fixing" the *foundation* per-component and routes that one class of defect to the migration owner; it does not freeze the pass.
- **Foundation drift makes component type/radius matches MOOT — and the run must say so.** When `app-violates-policy` fires on the type scale, every component font-size that "matched" matched at the wrong absolute size. The §9 report must state: "components were compared at the app's foundation scale, which diverges from the design system / policy; the foundation must be reconciled (apply-design-policy-change) before component-level type parity means anything" — never imply the green type rows are real parity.

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
Foundation-token drift (routed, NOT deltas): {foundation_token_drift_count}
  → app canonical tokens (type scale / control heights / radii / status colours) diverge from the
    design system AND/OR docs/design-policy.md; route to apply-design-policy-change (token migration).
    NEVER patched in-component, NEVER encoded as a dead var(--token, <literal>) fallback.
Frames in contract ({brief §7 | bundle frame inventory (URL) | manifest}):  {count}
Linked-records rows (AUTHORITATIVE §13-lookup denominator): {len(design_linked_record_rows)}  ← §13-lookup frames must equal-or-exceed this
  of which UNDER-ENUMERATED (rendered row, no harvested frame → routed): {count}  ← the "often missed" lookups (e.g. Shipping lane)
Frames missing in impl (Tier-1, designed-but-unbuilt): {count}  ← incl. the §13 lookup drawers on a no-brief URL run
Frames present but THIN in impl (Tier-1, drawer opens but interior under-built): {count}
Frames not drawn (routed, NOT deltas): {frame_uncovered_count}
  → the contract names the frame; the bundle never rendered it; route to design-handoff / Claude Design re-render
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
- **Every shared-semantic token that resolved only from a per-screen stylesheet (`{impl_token_provenance}` `scope: per-screen`) carries a `token-provenance: NON-CANONICAL TOKEN` row (§2g) — disclosed and ceded to design-review, never collapsed into "1:1" and never gated; `{token_noncanonical_count}` surfaced separately**
- **Foundation tokens reconciled (§2i) — the design system's foundational scale (type / control-height / radius / status-colour) was compared against the app's CANONICAL token values AND `docs/design-policy.md`'s declared scale; any drift is one routed Foundation-token row (`{foundation_token_drift_count}`), ceded to `apply-design-policy-change`, NEVER patched in-component and NEVER encoded as a dead `var(--token, <literal>)` fallback. The §9 report states that green component type/radius rows compared at the app's (possibly divergent) foundation, not as real parity.**
- **Exactly one Page-shell row exists (§2d), comparing `{design_layout_constraints}` against `{impl_page_shell}`'s effective container width — its Design value is the policy-authoritative entry; a width/centering mismatch is surfaced as Tier-1, never omitted because "no component owns it"**
- **One Ceded-dimensions note exists (§2e) — policy-conformance (prohibitions/tone/motion/iconography) + behavior are explicitly ceded to design-review / design-review-pr / verify, NOT faked into a grid check against the generated bundle**
- **One Frame-coverage row per frame in the resolved contract (§2f) — brief §7, OR (raw-URL, no brief) the bundle's declared `{design_frame_inventory}`, OR the manifest. A frame absent from the bundle is `FRAME NOT DRAWN`, routed (`{frame_uncovered_count}`) not inferred; a drawn-but-unbuilt frame is Tier-1 (this is the verdict for the §13 lookup drawers on a no-brief URL run); frames present in both ran the full per-property sweep inside them. Emitting zero Frame-coverage rows because "there was no brief" is non-conformant — the bundle declares its own lookup frames.**
- **The §13-lookup frames were reconciled against the AUTHORITATIVE denominator (§2f) — the detail drawer's rendered "Linked records" list (`{design_linked_record_rows}`). Every rendered linked-record row has a Frame-coverage row; a row with no harvested frame is `LOOKUP UNDER-ENUMERATED` (routed), never zero rows; the §13-lookup count ≥ the Linked-records row count. A drawer "present" in the impl was swept for DEPTH (a thin `code — name` stub against a rich bundle drawer is `MISSING in impl` rows, not a false `✓`).**

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
- **An all-green grid that silently omits a whole frame (§2f).** The brief §7 promised an `order-drawer` and a `warehouse-lookup` drawer; Claude Design drew only the worklist; the component sweep cataloged the worklist's components, matched them all, and reported success — while the drawers ship *inferred* and thin (bare `€60`, code/type/status stub). A frame the bundle never drew produces zero component rows, so "all green" is "we never looked." The Frame-coverage axis is mandatory because the component sweep, like the page-shell case, is structurally blind to what was never drawn. Never infer the missing frame to close the gap — route it back (`FRAME NOT DRAWN`).
- **Denominating §13-lookup coverage from a declaration instead of the rendered "Linked records" list (§2f).** The harvest sources (brief §7, script comments, banners, lookup→target maps) are all *declarations* that can under-enumerate — so a lookup the comments forgot to list never enters the contract and §2f can't flag a frame it never knew existed. The detail drawer's rendered Linked-records section is the authoritative count (one row per lookup); failing to reconcile against `{design_linked_record_rows}` is the precise "the workflow often misses these" failure. The live Orders drawer draws six rows including `Shipping lane` — exactly the row a script-comment harvest drops; it must surface as a Frame-coverage row from the rendered list, `LOOKUP UNDER-ENUMERATED` if the harvest missed it, never silently absent. The rendered row count is the floor; the harvested frame set never falls below it.
- **Greening a lookup drawer on "it opens" without sweeping its depth (§2f).** A frame present in both bundle and impl is NOT done until the impl drawer is as deep as the bundle drew it — a rich warehouse lookup (address / contact / throughput / lane bindings) shipping as a bare `code — name` stub is a present frame with a missing interior. Catalog the bundle frame's full component set and sweep all of it; the thin stub surfaces as `MISSING in impl` rows. Frame-present is necessary, not sufficient.
- **Greening component type/radius against a divergent FOUNDATION token (§2i).** A button `font-size: var(--font-size-base)` matching a design button `font-size: var(--font-size-base)` is NOT type parity when the app's canonical `--font-size-base` (16px) disagrees with the design system / policy (13px) — the declarations are identical while the rendered sizes differ by ~23%. No component owns the type scale, so the component sweep is structurally blind to it (the §2d page-shell blind spot at the token layer). This is the inbound-flow held-orders miss (PR #2412), where the wrong-foundation render was then "fixed" with a dead `var(--font-size-base, 0.8125rem)` fallback the defined global overrides. The Foundation-token row is mandatory; the fix is a token migration (`apply-design-policy-change`), never a per-component patch or a dead fallback.
- **Skipping Frame-coverage entirely on a raw-URL run because "there is no brief" (§2f source 2).** This is the inverse, no-brief leak — and the one the `Orders.html` "link to records (lookups)" miss came from. With no brief AND no manifest, an agent that only knows the brief §7 source concludes "no contract → nothing to check" and the §13 lookup drawers (warehouse / inbound-batch / import-run / accounting-outcome / catalog / supply-source) silently fall out: their inner primitives (Pill, Money, RecordLink) are shared and match somewhere in the impl, so the component grid is all-green while the whole drawer ships unbuilt or inferred-thin. The bundle declares those frames itself — the `<script src>` comments say "… lookups consumed", the modules carry `/* ==== warehouse-lookup ==== */` banners — so `{design_frame_inventory}` (step-01 URL.3a) IS the denominator. "No brief" is not "no contract."
