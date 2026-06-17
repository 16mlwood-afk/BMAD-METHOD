# Design Implementation Checklist

## Ingestion (Step 1)

- [ ] Design bundle downloaded and extracted successfully
- [ ] README read — target design file identified
- [ ] Chat transcripts read (if referenced in README)
- [ ] All `<script src="...">` imports from the HTML file traced and read
- [ ] Design tokens extracted with resolved values (not just token names)
- [ ] Every component's CSS properties cataloged with exact pixel/em/hex values
- [ ] Asymmetric padding/margin recorded as separate values (not collapsed)
- [ ] `{design_layout_constraints}` captured — from `docs/design-policy.md` (AUTHORITATIVE; the bundle README is generated from it), corroborated by the README + bundle wrapper width (both ingest paths populate it; `authoritative` flag set per source)
- [ ] (URL path) `{design_frame_inventory}` captured (URL.3a) — the primary frame + the drilled detail drawer + each §13 lookup ("link to records (lookups)"), from `<script src>` modules + comments, per-frame banners, lookup→target maps, and sibling standalone `<frame>.html`; each linked standalone frame opened and its components folded into `{design_components}`. This is §2f's frame-coverage denominator on a no-brief run.

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

## Comparison Grid (Step 3)

- [ ] Every design component matched to its implementation counterpart
- [ ] Every CSS property compared with exact values in both columns
- [ ] No vague descriptions in the Delta column — quantified differences only
- [ ] Delta column uses consistent notation: `✓`, `+Npx`, `-Npx`, `MISSING`, `EXTRA`
- [ ] Deltas classified into Tier 1 (structural), Tier 2 (visual), Tier 3 (micro)
- [ ] Page-shell rows emitted (§2d) — container width/centering compared against the policy-authoritative value (mismatch = Tier-1), AND an **injected-chrome** row: any hero/banner/masthead an ancestor layout renders above the page content that the design frame doesn't contain is Tier-1 (a §5 hero-strip hard failure visible in the layout files — an add, not a §2e cede). Never omitted because "no component owns it" or "the bundle didn't draw it."
- [ ] Ceded-dimensions note emitted (§2e) — policy-conformance (prohibitions/tone/motion) + behavior ceded to design-review / verify, not faked as a bundle-diff check
- [ ] Frame-coverage rows emitted (§2f) — **the frame contract was loaded and one row emitted per frame.** Source in precedence order: brief §7 Surface Inventory; OR (raw-URL run, no brief) the bundle's declared `{design_frame_inventory}` (step-01 URL.3a — the drilled drawer + each §13 lookup); OR the manifest. Always emit the block; only if NO source yields a frame set, say so and mark it `needs human confirmation`. A frame drawn-but-unbuilt is Tier-1 (`FRAME MISSING in impl` — the verdict for the §13 lookup drawers on a no-brief URL run); a frame the bundle never drew is routed (`FRAME NOT DRAWN`, counted in `{frame_uncovered_count}`), not inferred. A grid that ran the component sweep only over frames that already exist in impl — never enumerating the contract — is non-conformant; "no brief" is not "no contract."
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

## Delivery

- [ ] Changes committed with descriptive message referencing delta count
- [ ] Branch pushed and PR created
- [ ] PR merged
- [ ] Production deploy triggered
- [ ] Grid artifact preserved for regression reference
