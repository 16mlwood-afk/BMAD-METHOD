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
- [ ] Page-shell row emitted (§2d) — container width/centering compared against the policy-authoritative value; a mismatch surfaced as Tier-1, never omitted because "no component owns it"
- [ ] Ceded-dimensions note emitted (§2e) — policy-conformance (prohibitions/tone/motion) + behavior ceded to design-review / verify, not faked as a bundle-diff check
- [ ] Frame-coverage rows emitted (§2f) — **the brief §7 Surface Inventory was loaded and one row emitted per promised frame** (always emit the block; if the brief was unavailable, say so and mark the block `needs human confirmation`). A frame drawn-but-unbuilt is Tier-1 (`FRAME MISSING in impl`); a frame the bundle never drew is routed (`FRAME NOT DRAWN`, counted in `{frame_uncovered_count}`), not inferred. A grid that ran the component sweep only over frames that already exist in impl — never enumerating the §7 list — is non-conformant: "all green" then means "we never looked," not "every promised frame was built and matched."
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
