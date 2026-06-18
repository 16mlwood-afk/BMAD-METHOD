<!--
  Canonical design-ingest manifest schema (design-ingest-<surface>.md frontmatter
  + body). Emitted by step-03-emit-manifest-and-handoff.md; read by
  design-implement via input_kind: ingest_manifest. workflow.md keeps the
  one-line pointer here.
-->

## INGEST MANIFEST SCHEMA (`design-ingest-<surface>.md`)

The manifest is the durable, reviewable contract that decouples ingest from apply. It is **authoritative for the frame inventory, the per-frame section inventory, and the grid scaffold** — i.e. for *what must be accounted for*. It is NOT authoritative for whether a section is correctly implemented (that is `design-implement`'s grid + step-02b) nor for treatment correctness beyond recording the design's own values.

It is a markdown file (so it lives readably on `main`) with a YAML frontmatter receipt and a structured body. Path: `{implementation_artifacts}/design-ingest-<target_slug>.md`.

```yaml
# ── Frontmatter: ingest receipt (authoritative) ──
ingest:
  workflow: design-ingest
  version: 1
  date: {iso8601}                       # stamped by the orchestrator after the run (scripts can't read the clock mid-run)
  input_kind: {claude_design_url | synthesize_bundle}
  source: {design_url | bundle_dir}
  target_file: {primary frame filename, e.g., "Supply Orders - Worklist (blocked-stock).html"}
  target_slug: {kebab-case}
  baseline_commit: {git sha at ingest time}
  supersede_status: {active | superseded | no_brief | ambiguous}   # resolved in design-ingest step-01 by matching target_slug against briefs in implementation_artifacts; design-ingest TOLERATES every value (never refuses) — it stamps so design-implement can explain a no-op and guard re-applying stale design. brief-revision-policy.md §8.
  superseded_by: {successor brief filename | empty}                # set iff supersede_status == superseded
  source_brief: {matched brief filename | none}                    # the brief this handoff traces to (none on a no_brief raw-URL run)
  layout_constraints:                   # design-implement step-03 §2d denominator; sourced from docs/design-policy.md (authoritative) per design-implement URL.2
    source: {policy | README-generated | bundle-wrapper}
    assertion: {verbatim framing rule}
    resolved: { width: {full-bleed | <px>}, centered: {bool}, padding: {value} }
    authoritative: {bool}               # true only when read from docs/design-policy.md
  completeness:
    frames_total: {int}
    frames_drawn: {int}
    sections_total: {int}               # sum of frame_sections across all drawn frames
    frames_with_empty_section_list: []  # MUST be empty for a clean manifest — a non-empty list is a frame-completeness defect (step-02 should have halted)
  tokens:
    radii: { ... }
    type_scale: { ... }
    colors: { ... }
```

```markdown
# ── Body ──

## Frame inventory
<!-- one row per frame the target delivers or consumes; same derivation as
     design-implement URL.3a. The primary frame is row 0. -->
| frame | role | parent | declared_in | drawn |
|---|---|---|---|---|
| Orders (primary)              | primary        | —                        | target html      | true  |
| supply-order-detail-drawer    | drilled-detail | Orders                   | script-src comment | true |
| warehouse-lookup              | §13-lookup     | supply-order-detail-drawer | jsx banner       | true  |
| amazonqty-lookup              | §13-lookup     | supply-order-detail-drawer | jsx banner       | false |  <!-- drawn:false → carries to design-implement §2f as FRAME NOT DRAWN (routed, not inferred) -->

## Section inventory  (THE COMPLETENESS GATE)
<!-- For EVERY frame with drawn: true, its COMPLETE ordered list of top-level
     sections, with the heading/copy the design renders. This list is REQUIRED
     and non-empty — an empty list for a drawn frame is a frame-completeness
     defect and step-02 must have halted on it. This is the structural fix for
     "a whole section dropped inside a present frame." -->

### Frame: supply-order-detail-drawer  (10 sections)
1. Co-view banner — "Also in /operations/blocked-stock — …"
2. Header / product identity — crumb + mono id + product KV
3. Block & disposition (the setter)
4. Reconciliation (three-state) — recon-lead + Ordered/Delivered/Held/Returned grid
5. Cost & sourcing — verdict strip + econ rows
6. Lifecycle + Amazon status
7. SellerSmart dispatch
8. Related records (§13 xrefs)
9. Source receipt
10. Decision history (block trail + lifecycle)

## Grid scaffold  (pre-seeded — every section is already a row)
<!-- design-implement consumes this AS its component×section grid skeleton.
     Every (frame, section) is a row with status UNVERIFIED; design-implement
     fills verdict + deltas (ALIGNED / COPY-DELTA / TREATMENT-DELTA /
     STRUCTURE-DELTA / MISSING) in its grid + apply steps. A section with no
     row here is a section design-implement is structurally blind to — which is
     exactly the gap this scaffold closes. -->
| frame | section | design copy/structure (verbatim) | data fields read | component×property rows | status |
|---|---|---|---|---|---|
| supply-order-detail-drawer | Reconciliation | recon-lead 3 branches ("Not gathered yet." / "Reconciled clean." / gap); recon-grid 4 fixed tiles | quantity, amazonDeliveredQty, amazonHeldQty, amazonReturnedQty, varianceResolution | .recon-lead{12px,subtle-fg} · .recon-grid{grid 4×1fr,gap8} · .rc-cell{border,radius7,inset-bg} · .rc-n{15px,600} · .rc-l{10px,muted} | UNVERIFIED |
| supply-order-detail-drawer | SellerSmart dispatch | "SellerSmart dispatch" h4 + dispatch pill + §13 link | (dispatch fields — see data-availability note) | … | UNVERIFIED |
| … one row per (frame, section) … | | | | | |

## Data-availability notes
<!-- For any section whose fields are NOT present on the impl view-model, record
     it here so design-implement flags rather than fabricates. Mirrors the
     design-implement content-lane cede + logged-deviation discipline. -->
- supply-order-detail-drawer / SellerSmart dispatch: needs `dispatch` view-model fields + a backend dispatch read — NOT currently on the SupplyOrder view-model. Implementing requires data plumbing; flag, do not fabricate.
```

### How `design-implement` consumes it

When invoked with `input_kind: ingest_manifest`, `design-implement` step-01:
- Reads `ingest.layout_constraints` into `{design_layout_constraints}` (skips URL.2 re-derivation).
- Reads the Frame inventory into `{design_frame_inventory}` (skips URL.3a re-derivation).
- Reads the Grid scaffold rows into `{design_components}` / `{css_property_catalog}` — every (frame, section) row becomes a grid row carried into step-03.
- Reads `ingest.supersede_status` + `ingest.superseded_by` (Input Resolution) and branches per the Supersede stamp section below — symmetric tolerance: no hard refuse, but no silent apply of a superseded handoff.
- Skips the download/extract + per-component re-catalog entirely. No 140KB re-ingest.

The named gate `design-implement` adds (step-03): **every (frame, section) row in the scaffold is a mandatory grid row** — and on a non-manifest run (URL/bundle ingested in-context), step-03 must itself enumerate each drawn frame's sections so the same denominator exists. The manifest path makes the denominator durable and reviewable; the in-context path must reconstruct it.

### Supersede stamp

`ingest.supersede_status` records whether the handoff this manifest was built from is still the active design. `design-ingest` resolves it (step-01) by matching `target_slug` against the briefs in `{implementation_artifacts}` and **tolerates every value — it never refuses** (ingest is non-destructive; see `brief-revision-policy.md` §8). The stamp exists so the *destructive* downstream half can act on it:

- `active` / `no_brief` → `design-implement` proceeds normally (`no_brief` = a raw-URL run where supersede could not be determined; not asserted active, just unknown).
- `superseded` → `design-implement` does NOT silently apply. With no remaining deltas it emits a *self-explaining* no-op ("already applied, and superseded by `{superseded_by}`"); with deltas it HALTS for explicit confirmation, because applying them would regress the surface toward the superseded design. `superseded_by` names the current brief.
- `ambiguous` → two briefs claim `active` for the slug (active-uniqueness broken, `brief-revision-policy.md` §2.6); `design-implement` warns but the manifest is otherwise well-formed.

This is deliberately weaker than the §5 consumer *refuse* contract: a cataloguer that pauses for review only needs to tell the truth loudly, not block.

### Completeness invariant

`ingest.completeness.frames_with_empty_section_list` MUST be empty in a delivered manifest. A non-empty list means step-02's per-frame completeness gate did not halt as it should have — the manifest is malformed and `design-implement` should refuse it (the same bounce-back shape as the synthesize-bundle gates).
