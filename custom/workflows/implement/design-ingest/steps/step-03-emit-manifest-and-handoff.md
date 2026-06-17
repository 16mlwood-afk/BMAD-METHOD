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

## 3. PAUSE — hand back to the user as a conversation, then STOP

This is the moment the whole workflow exists for, so don't end it with a status box — **talk to the user.** Write the manifest, then have a real handoff conversation. Do NOT proceed to any implementation.

Cover these, in your own words and in this spirit:

- **Where things stand:** you've gone through the design and listed everything out, and nothing has been changed yet — this is a checkpoint, not a result.
- **Walk them through what you found:** screen by screen, the sections each one has — in plain language, with the heavy/important screen (usually the detail drawer) spelled out in full so they can actually eyeball it. This is the part they're meant to read, so make it readable, not a dump.
- **Call out anything you're unsure about:** a screen that came back thin, a section whose data the implementation might not have, anything that made you hesitate.
- **Invite the check, directly:** ask them to look the list over — does each screen's sections look complete, or is something missing? This is exactly the review that catches a whole section being dropped, so make the ask real, not a footnote.
- **Tell them what happens next, plainly:** when they're happy, you (or they) run design-implement on the manifest and it'll work straight off this list — it won't re-read the bundle, and every section is already a row so nothing gets skipped. If a screen looks short, they point you at it and you re-check that one.

The concrete facts to hand them (weave these in naturally, don't print a form):

- the manifest's saved at `{manifest_path}`
- it covers `{frames_drawn}` drawn screens (`{frames_total}` declared) and `{sections_total}` sections, one grid row each
- the next command is `/bmad:bmm:workflows:design-implement {manifest_path}`

Then stop and wait. If something has genuinely failed (an empty manifest, a broken invariant — §2 above), that's the one case where a short, plain failure note is the right call instead of the friendly walkthrough.

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
