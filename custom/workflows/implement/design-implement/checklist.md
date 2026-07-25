# Design Implementation Checklist

## Ingestion (Step 1)

- [ ] (ingest_manifest path) `ingest.supersede_status` read — if `superseded`, the supersede surfaced to the user BEFORE apply; a no-delta run self-explained the no-op (named `superseded_by`), a with-deltas run HALTED for explicit confirmation (never auto-applied a superseded handoff). `brief-revision-policy.md` §8
- [ ] (URL / bundle path) `{handoff_supersede_status}` resolved independently in step-01 §SHARED.1a (no stamp on these paths) — if `superseded`, SURFACED and HALTED for explicit confirmation before the apply pipeline; never silently built a superseded handoff. `brief-revision-policy.md` §8
- [ ] (URL / bundle path) `{prior_ingest_manifest}` resolved in step-01 §SHARED.1a-iii — `{implementation_artifacts}` globbed for `design-ingest-*{target_slug}*.md` BEFORE step-02; on a hit the manifest's apply ledger was READ and its prior passes / still-deferred frames / **"Flagged — NOT applied (intent, not treatment)"** items surfaced, no prior DECISION was re-opened without saying so, staleness of the section inventory was disclosed, and this run's ledger was routed to that manifest rather than a parallel grid artifact. `docs/manifest-contract.md`
- [ ] Design bundle downloaded and extracted successfully
- [ ] README read — target design file identified
- [ ] Chat transcripts read (if referenced in README)
- [ ] (URL path) `{bundle_shape}` resolved BEFORE any path is read (URL.1c) — `legacy_jsx` vs `dc_html`; a `.dc.html` target was not ingested down the legacy branch, and the shape is stated in the SHARED.2 summary
- [ ] All `<script src="...">` imports from the HTML file traced and read (`legacy_jsx`) — or, on `dc_html`, the self-contained frame document read in full and its frame roots / named sections / `<x-import>` components cataloged (there are no module imports to trace; concluding "no components" from that is the silent no-op)
- [ ] (`dc_html`) `{design_variants}` captured (URL.5a) — `data-props` parsed, EVERY `<sc-if>` branch enumerated (not just the prop defaults), every property row tagged `variant` alongside `state`; a non-default branch containing structure the default lacks flagged `hides_capability` and folded into `{design_components}`/`{design_frame_inventory}` so step-02b §2 sees it. "proposal"/"unbriefed" section labels carried as annotation, never as a deletion signal
- [ ] (URL path) Near-empty-catalog guard evaluated (URL.6) — the run did NOT continue past a zero-modules AND zero-README AND zero-tokens ingest
- [ ] Design tokens extracted with resolved values (not just token names) — from `theme/tokens.jsx` (`legacy_jsx`) or the `<helmet>`-linked `_ds/<ds-id>/tokens/*.css` + `styles.css` (`dc_html`); on `dc_html` the absent JSX theme was never read as "no tokens"
- [ ] Every component's CSS properties cataloged with exact pixel/em/hex values
- [ ] Asymmetric padding/margin recorded as separate values (not collapsed)
- [ ] `{design_layout_constraints}` captured — from `docs/design-policy.md` (AUTHORITATIVE; the bundle README is generated from it), corroborated by the README + bundle wrapper width (both ingest paths populate it; `authoritative` flag set per source)
- [ ] (URL path) `{design_frame_inventory}` captured (URL.3a) — the primary frame + the drilled detail drawer + each §13 lookup ("link to records (lookups)"), from `<script src>` modules + comments, per-frame banners, lookup→target maps, and sibling standalone `<frame>.html`; each linked standalone frame opened and its components folded into `{design_components}`. This is §2f's frame-coverage denominator on a no-brief run.
- [ ] `{design_linked_record_rows}` captured AND reconciled (URL.3a source 5) — the detail drawer's rendered "Linked records" rows (the **authoritative** §13-lookup denominator — e.g. Catalog item · Route warehouse · Shipping lane · Supply source · Inbound batch · Import run) enumerated, and every row confirmed to map to a `§13-lookup` frame in `{design_frame_inventory}` (a row with no harvested frame → re-traced or flagged `LOOKUP UNDER-ENUMERATED`, never dropped). Harvested §13-lookup count ≥ rendered row count.

## Implementation Mapping (Step 2)

- [ ] Implementation page file located and read
- [ ] All child component imports traced and read
- [ ] `tailwind.config.js` read — all theme overrides extracted
- [ ] Tailwind class resolution table built (class → default → override → actual)
- [ ] Every implementation component's classes/styles cataloged with resolved values
- [ ] CSS custom properties (shadcn tokens, etc.) resolved to computed values
- [ ] Missing/extra components flagged explicitly
- [ ] Page-shell wrapper chain walked (§1a) — `{impl_page_shell}` effective container width resolved after every nested layout cap (+ sibling-page convention note)
- [ ] Baseline commit SHA recorded

## Regression-Surface Preflight (Step 2b)

- [ ] `{production_capabilities}` and `{handoff_capabilities}` inventoried at the FEATURE level (routing/sub-surfaces, §13 linked records, economics/cost-recon, composite status/header, activity/audit, bulk actions/filters, action-wired mutations) — not CSS
- [ ] `{dropped_capabilities}` computed (prod minus handoff); an undrawn-but-promised handoff frame (brief §7 / `{design_frame_inventory}`) NOT mis-scored as dropped
- [ ] If the dropped set is non-empty, the run **HALTED** with the regression report + strategy menu and recorded `{implementation_strategy}` + `{capability_dispositions}` — it did NOT proceed to the grid on an unconfirmed replacement (autonomous mode defaulted to non-destructive keep-all and disclosed)
- [ ] Kept capabilities flagged **protected** for step-03/04; dropped capabilities routed to the step-04 §9 orphaned-action confirmation
- [ ] New surface with no production page → recorded "no regression surface" and proceeded

## Comparison Grid (Step 3)

- [ ] Every design component matched to its implementation counterpart
- [ ] Every CSS property compared with exact values in both columns
- [ ] No vague descriptions in the Delta column — quantified differences only
- [ ] Delta column uses consistent notation: `✓`, `+Npx`, `-Npx`, `MISSING`, `EXTRA`
- [ ] Deltas classified into Tier 1 (structural), Tier 2 (visual), Tier 3 (micro)
- [ ] Page-shell rows emitted (§2d) — container width/centering compared against the policy-authoritative value (mismatch = Tier-1), AND an **injected-chrome** row: any hero/banner/masthead an ancestor layout renders above the page content that the design frame doesn't contain is Tier-1 (a §5 hero-strip hard failure visible in the layout files — an add, not a §2e cede). Never omitted because "no component owns it" or "the bundle didn't draw it."
- [ ] Ceded-dimensions note emitted (§2e) — policy-conformance (prohibitions/tone/motion) + behavior ceded to design-review / verify, not faked as a bundle-diff check
- [ ] Frame-coverage rows emitted (§2f) — **the frame contract was loaded and one row emitted per frame.** Source in precedence order: brief §7 Surface Inventory; OR (raw-URL run, no brief) the bundle's declared `{design_frame_inventory}` (step-01 URL.3a — the drilled drawer + each §13 lookup); OR the manifest. Always emit the block; only if NO source yields a frame set, say so and mark it `needs human confirmation`. A frame drawn-but-unbuilt is Tier-1 (`FRAME MISSING in impl` — the verdict for the §13 lookup drawers on a no-brief URL run); a frame the bundle never drew is routed (`FRAME NOT DRAWN`, counted in `{frame_uncovered_count}`), not inferred. A grid that ran the component sweep only over frames that already exist in impl — never enumerating the contract — is non-conformant; "no brief" is not "no contract."
- [ ] §13-lookup frames reconciled against the authoritative denominator (§2f) — every row in `{design_linked_record_rows}` has a Frame-coverage row; a rendered row with no harvested frame is `LOOKUP UNDER-ENUMERATED` (routed), never silently absent; §13-lookup count ≥ rendered row count. A lookup drawer "present" in impl was swept for **depth** (a thin `code — name` stub vs a rich bundle drawer = `MISSING in impl` rows, not a false ✓). This is the "often missed link-to-record drawers" fix.
- [ ] Token-provenance rows emitted (§2g) — every shared-semantic token (status / colour / type) that resolved only from a per-screen stylesheet (`{impl_token_provenance}` `scope: per-screen`) carries a `NON-CANONICAL TOKEN` disclosure row, ceded to design-review; never collapsed into "tokens map 1:1" and never gated. A `local-constant` per-screen token is NOT flagged. `{token_noncanonical_count}` surfaced separately from `{delta_count}`.
- [ ] Grid artifact written to disk at `{implementation_artifacts}/`
- [ ] `{delta_count}` matches actual count of non-✓ rows

## Minimum Property Coverage Per Component

For each component, confirm these properties were checked (mark N/A if the component doesn't use them):

- [ ] `border-radius` — resolved through Tailwind config, not assumed
- [ ] `font-size` — design token vs Tailwind class (resolved)
- [ ] `font-weight`
- [ ] `font-family` — mono vs sans distinction
- [ ] `letter-spacing` — `tracking-*` class resolved
- [ ] `padding` — all four sides, especially asymmetric
- [ ] `gap` — flex/grid gap
- [ ] `width` / `min-width` / `max-width` — grid columns, fixed containers
- [ ] `height` / `min-height` — row heights, icon containers
- [ ] `border` — width, color, opacity
- [ ] `background` — color token
- [ ] `color` — text color token
- [ ] `grid-template-columns` — if applicable
- [ ] `text-transform` — uppercase, capitalize
- [ ] SVG `width` / `height` — if icons present
- [ ] Content text — labels, sub-text

## Application (Step 4)

- [ ] Every Tier 1 delta fixed
- [ ] Every Tier 2 delta fixed
- [ ] Every Tier 3 delta fixed
- [ ] Each modified file re-read after edit to verify correctness
- [ ] `npm run build` passes
- [ ] Grid artifact updated with `✓ FIXED` for each resolved delta
- [ ] Fix log records the before/after value for each change
- [ ] No files outside the target page's component tree were modified
- [ ] `tailwind.config.js` was NOT modified (arbitrary values used instead)
- [ ] Copy & frame chrome transcribed VERBATIM (§5b) — header, `‹ Back to …` breadcrumb, footer (caption + cross-link label AND target), every group title / label / sub-caption; any deviation logged in the ledger with a *forced* reason (no silent relabel / paraphrase / code↔symbol swap / generic-shell substitution)
- [ ] **Every drilled frame has a Frame-composition row (§2d-bis)** — section order + group naming + header/footer chrome compared against the design; a renamed/regrouped/reordered drawer or a footer button treatment mismatch is Tier-1, and every `{frame_composition_deltas}` entry from step-02b became a row (the drawer analog of the page-shell row)
- [ ] Render-compare done-gate run (§5b) — built surface placed beside the design render and stepped through top-to-bottom — OR explicitly marked owed-and-routed (`verify` / design-review). "Done" was NOT declared off the green grid alone
- [ ] State-render coverage accounted for (§5b.3) whenever the done-check was a live/local render — every non-default state row (domain state-variants + `hover`/`failed`/`empty`) marked `painted` / `no-data-to-paint`; each `no-data-to-paint` state named and ceded `visually-unverified (static/unit-covered only)` into the §9 prod-smoke checklist, or the section states "all declared states painted". A clean default-state screenshot was NOT treated as state-axis coverage (the seed data only exercises the states it contains)
- [ ] **(ingest_manifest runs only) Resumable apply honored (§5a)** — applied frame-by-frame with each frame's dispositions persisted back into the manifest at its boundary; prior-pass `✓ applied` rows skipped (not re-applied); `{frame_scope}` respected if set; if the pass stopped early it set `{run_completion_mode} = checkpointed`, delivered the slice (incl. the updated manifest), and printed the resume command — a large manifest was NOT forced through one single-window pass

## Delivery

- [ ] Changes committed with descriptive message referencing delta count
- [ ] Branch pushed and PR created
- [ ] PR merged
- [ ] Production deploy triggered
- [ ] Grid artifact preserved for regression reference
