---
name: 'step-01c-ingest-manifest'
description: 'MANIFEST PATH of step-01 ingest: read a gated design-ingest manifest instead of re-ingesting. Reads the GRAIN first (value-exact | partial | summary) to decide whether the scaffold is a sufficient value source, demotes the manifest restated source facts, then builds the catalog from the reviewed grid scaffold. Entered only when input_kind == ingest_manifest; converges on step-01 §SHARED.'
---

# Step 1c: Ingest — MANIFEST PATH

**Entered from `step-01-ingest-design.md` §INPUT-KIND BRANCH when `{input_kind} == "ingest_manifest"`.** Do not run this file on any other input kind. The completeness-invariant gate (no drawn frame with an empty section list) has already cleared in workflow.md Input Resolution. On completion, return to **`step-01-ingest-design.md` §SHARED**.

**Read MANIFEST.1a BEFORE MANIFEST.2.** The grain decides whether the scaffold may serve as a value source at all; skipping it is how a prose-only manifest gets treated as value-exact (`FG-2026-07-25-14`).

**Section ids here are `MANIFEST.*`**, cited from step-01 by that name (see the router's citation legend).

---

## MANIFEST PATH (`{input_kind} == "ingest_manifest"`)

No download, no extract, no per-component re-catalog. `design-ingest` already did the exhaustive, fanned-out enumeration and persisted it. This path READS the manifest into the same downstream state the other two paths produce.

### MANIFEST.1. Read the manifest

`{ingest_manifest}` is already parsed (workflow Input Resolution). It conforms to `design-ingest/manifest-schema.md`. Read, do not re-derive:

- `{design_layout_constraints}` ← `{ingest_manifest}.ingest.layout_constraints` (skip URL.2 / BUNDLE layout derivation entirely).
- `{design_tokens}` ← `{ingest_manifest}.ingest.tokens`.
- `{design_frame_inventory}` ← the manifest's **Frame inventory** table verbatim (skip URL.3a re-derivation). Each `drawn: false` frame carries into §2f as FRAME NOT DRAWN, exactly as on the URL path.
- `{design_file}` ← `{ingest_manifest}.ingest.target_file`.

### MANIFEST.1a. Read `ingest.manifest_grain` FIRST — it decides whether MANIFEST.2 is sufficient

**Do not enter MANIFEST.2 without reading the grain.** MANIFEST.2 builds the CSS catalog from the scaffold's `component×property rows`, which is sound ONLY when those cells hold resolved values — and a manifest can be fully compliant and completeness-passing with prose in them. Contract + rationale: `manifest-schema.md` → "Grain invariant" (fork-gap `FG-2026-07-25-14`). Set `{manifest_grain}`; **absent ⇒ `summary`**, never inferred value-exact.

- `value-exact` → build from the scaffold; the "no re-ingest" promise holds.
- `partial` → scaffold where exact; **re-read the source** for every section in `completeness.sections_missing_property_rows`.
- `summary` → manifest is the **section denominator only** (frames/sections/copy/fields/resume); **re-read the source for values.**

**On `partial`/`summary` the re-read is a REQUIRED step of this path, not a fallback** — resolve the source and read values as URL.5 does, mirroring to `{design_dir}`. A `summary` manifest still saves the expensive half (the gated section enumeration), not the value read. Report grain + re-read in SHARED.2. A `summary` manifest is **not** a defect; proceeding to a treatment verdict on prose is.

### MANIFEST.1b. Do not trust the manifest's restated source facts

`tokens:`, section-copy prose and `## Findings` are **derived copies** that drift (`manifest-schema.md` → "Restated source facts"). Authority for *structure*, never for a *value* or an exhaustive negative.

- **Source vs manifest disagreement → THE SOURCE WINS**, and the correction is written back into the manifest (append-only pass record) so the next pass cannot re-inherit it.
- An exhaustive negative ("no `<img>` exists anywhere", "never drawn") is a **hypothesis to verify** — never a licence to skip or infer. A disproved premise is a manifest **defect**: correct it explicitly.

Instance (`FG-2026-07-25-14`): a passing manifest claimed no `<img>` existed and the resolved thumbnail was never drawn (source drew it in three places), said `30px` for a `26px` numeral, and labelled a chip "Can't vouch" where the source said `Gaps` — caught only by re-reading the source against this path's own shortcut.

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

