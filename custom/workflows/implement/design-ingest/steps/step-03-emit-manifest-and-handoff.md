---
name: 'step-03-emit-manifest-and-handoff'
description: 'Assemble the durable ingest manifest per manifest-schema.md (frame inventory + section inventory + pre-seeded grid scaffold), re-assert the completeness invariant, write it to implementation_artifacts on main, and PAUSE with the design-implement handoff command. This is the one deliberate halt.'
---

# Step 3: Emit Manifest + Handoff

**Progress: Step 3 of 3** — terminal. Emits the manifest and STOPS.

## RULES

- This step PAUSES. It does NOT chain into `design-implement`. The reviewable section inventory between ingest and apply is the whole point.
- The manifest is the durable artifact; everything step-01/02 built is serialized here so the apply phase needs no re-ingest.

---

## 1. Assemble the manifest

Build `design-ingest-<target_slug>.md` per `{installed_path}/manifest-schema.md`:

- **Frontmatter receipt** — `ingest:` block (workflow/version/input_kind/source/target/baseline_commit), `layout_constraints` (from `{design_layout_constraints}`), `completeness` counts, `tokens`.
- **Frame inventory** table — `{design_frame_inventory}` verbatim.
- **Section inventory** — for every `drawn: true` frame, its complete ordered `{frame_sections}[frame]` list with headings/copy. This is the gated, reviewable core.
- **Grid scaffold** — one row per (frame, section): the verbatim design copy/structure, the data fields read, the component×property rows from `{section_catalog}`, status `UNVERIFIED`. This is what `design-implement` consumes AS its grid skeleton.
- **Data-availability notes** — any section whose fields are not known to exist on the impl view-model (so `design-implement` flags rather than fabricates). Where the impl is not in scope to confirm, record "verify against view-model at map step."

Write to `{implementation_artifacts}/design-ingest-<target_slug>.md`. Store `{manifest_path}`.

## 2. Re-assert the completeness invariant

Before declaring done, verify and stamp:

- `completeness.frames_with_empty_section_list` is **empty**. If not, step-02's gate was bypassed — halt, do not emit a malformed manifest.
- `completeness.sections_total` == the number of grid-scaffold rows. A mismatch means a section was enumerated but not scaffolded (or vice versa) — reconcile before emitting.
- Every `drawn: true` frame appears in BOTH the section inventory and the grid scaffold.

Stamp `ingest.date` and `completeness.*` now (the orchestrator has the clock; scripts do not).

## 3. PAUSE — handoff

Emit the handoff and STOP. Do not proceed to any implementation.

```
══════════════════════════════════════════════════════════════════
✓ design-ingest complete — manifest emitted, NOT yet applied.

  manifest:        {manifest_path}
  frames:          {frames_drawn} drawn / {frames_total} declared
  sections:        {sections_total} across {frames_drawn} frames
  grid scaffold:   {sections_total} rows (status UNVERIFIED)
  thin-frame warns:{list or none}

REVIEW the section inventory in the manifest before applying — confirm every
frame's sections look complete (this is the gate that catches a section
dropped inside a present frame). Then implement from the manifest:

  /bmad:bmm:workflows:design-implement {manifest_path}

design-implement will consume input_kind: ingest_manifest, skip re-ingest,
and go straight to map → regression-surface → grid → apply. The grid is
already seeded with every (frame, section) row, so no section can be
silently skipped.
══════════════════════════════════════════════════════════════════
```

---

## SUCCESS METRICS

- `{manifest_path}` written to `{implementation_artifacts}`, readable on `main`.
- `completeness.frames_with_empty_section_list` empty; `sections_total` == grid-scaffold row count.
- Every drawn frame present in both the section inventory and the grid scaffold.
- The workflow PAUSED at the handoff — it did not chain into apply.

## FAILURE MODES

- **Auto-chaining into design-implement** — defeats the reviewable handoff. Step-03 stops.
- **Emitting a manifest with an empty section list on a drawn frame** — a malformed manifest `design-implement` must refuse; the invariant check exists to prevent it.
- **Grid scaffold missing a row that the section inventory lists** — the scaffold is the grid skeleton; a missing row is a section design-implement will be blind to.
