# Synthetic Paperwork Image Generation — fork default

**Status:** ratified 2026-07-20 (origin: cash-recovery clerk photo-guide work).
**Scope:** any time a project (or a fork workflow) generates an IMAGE of a shipping label, return label,
RMA / vendor-return slip, packing slip, or similar carrier/marketplace paperwork — for instructional guides,
placeholders, mockups, or design fixtures.

**Reference standard, not a sync-distributed workflow.** Point generation prompts and design briefs here
rather than restating it. Lives in `docs/` deliberately so `sync-bmad-workflows.sh` does NOT fan it into the
13 projects; a cross-project rollout is a separate, explicit decision.

**Before generating anything under this standard, clear the spend gates in
`ai-media-spend-controls.md`** — that file governs WHETHER optional AI media should be produced at
all; this one governs HOW paperwork imagery must look once it is.

## The four-point gate (reject an output containing ANY of these)

1. real names, addresses, ASINs, FNSKUs, or tracking numbers;
2. barcodes / QR / DataMatrix that could resolve to a real parcel or account (must encode synthetic,
   non-resolving data);
3. recognizable carrier or marketplace logos (UPS, Amazon, etc.);
4. carrier- or marketplace-specific **trade dress** — header blocks, colours, or layout motifs that match
   a real vendor.

The target is a **realistic GENERIC label**, never a "genericized UPS/Amazon label."

## The default pattern

- **Fake identity:** obviously-placeholder names/addresses (`J. DOE`, `SAMPLE CUSTOMER`, `123 FAKE STREET`,
  `ANYTOWN`, `DEMO ADDRESS`).
- **Synthetic codes:** IDs and tracking in a clearly synthetic form — **never a `1Z…` or any real live
  format**. Use a neutral prefix (`XZ…`) or all-zeros. All barcodes/2D codes are decorative/non-resolving.
- **No branding:** blank logo box; generic headers (`STANDARD RETURN`, `VENDOR RETURN — DAMAGED`).
- **Realism via craft, not data:** deliver believability through **layout density (multi-barcode +
  DataMatrix), monospace machine print, substrate (worn box / kraft), and a casual handheld camera angle** —
  not through real-looking live data.
- **Structural echoes allowed:** fields like `ASIN`, `UPC`, `RMA#`, `Remit To`, `Order Summary` are fine
  (generic identifiers/labels); brand marks and trade dress are not.

## Canonical exemplars (reference outputs)

- **Return shipping label (label-face):** dense tri-panel thermal label on a worn box.
- **Vendor-return backing slip:** dense RMA slip on kraft, blank logo box, ASIN/UPC columns.

Both live in cash-recovery `_bmad-output/implementation-artifacts/higgsfield-angle-guide-prompt-pack-2026-07-19.md`
(B1 / B2), with full prompts and the model used (`nano_banana_2`).

## Boundary

These are instructional / fixture assets only. They must **never** populate an identity-bearing slot
(e.g. a real product-image field). Identity data comes from the real source system, or an honest neutral
placeholder — never a generated label.
