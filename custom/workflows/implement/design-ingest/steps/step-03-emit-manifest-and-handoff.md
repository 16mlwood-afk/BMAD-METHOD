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

- **Frontmatter receipt** — `ingest:` block (workflow/version/input_kind/source/target/baseline_commit), the **supersede stamp** (`supersede_status: {handoff_supersede_status}`, `superseded_by: {superseded_by | empty}`, `source_brief: {source_brief.filename | none}`), `layout_constraints` (from `{design_layout_constraints}`), `completeness` counts, `tokens`. The supersede stamp is REQUIRED — it travels with the manifest so `design-implement` can explain a no-op and guard against re-applying stale design (`manifest-schema.md` → "Supersede stamp").
- **Frame inventory** table — `{design_frame_inventory}` verbatim.
- **Section inventory** — for every `drawn: true` frame, its complete ordered `{frame_sections}[frame]` list with headings/copy. This is the gated, reviewable core.
- **Grid scaffold** — one row per (frame, section): the verbatim design copy/structure, the data fields read, the component×property rows from `{section_catalog}`, status `UNVERIFIED`. This is what `design-implement` consumes AS its grid skeleton.
- **Data-availability notes** — any section whose fields are not known to exist on the impl view-model (so `design-implement` flags rather than fabricates). Where the impl is not in scope to confirm, record "verify against view-model at map step."

Write to `{implementation_artifacts}/design-ingest-<target_slug>.md`. Store `{manifest_path}`.

**Force-add the manifest — it IS this workflow's primary deliverable and must reach `main`.** Most projects gitignore `/_bmad-output/`, so a plain `git add {manifest_path}` is silently rejected as ignored: it stages nothing, the commit reports "nothing to commit," and the push ships an EMPTY branch that still reads as a successful emit (observed: PR #2640, inbound-flow). Use `git add -f`, then ASSERT the file is tracked before declaring done — a silent ignored-path no-op must never pass as a successful emit:

```bash
git add -f {manifest_path}
git ls-files --error-unmatch {manifest_path} >/dev/null || { echo "manifest not tracked — force-add failed; deliver would ship an empty branch"; exit 1; }
```

## 1a. Assert the path invariant — no scratchpad paths in a durable artifact

Before the completeness checks, verify every path the manifest records that a downstream workflow will DEREFERENCE (`ingest.source` when local; any evidence pointer such as an optional `ingest.frame_catalogs_dir`). The rule is `manifest-schema.md` → "Path invariant": **repo-relative, tracked, and named as it actually is on disk.** A session-scoped path in a durable artifact is always a bug — the emitting session's scratchpad is reaped when that session ends, so the manifest ships a dangling pointer to its own evidence that nobody can distinguish from a good path.

For each such field:

```bash
case "{path}" in
  /*|*/scratchpad/*|/tmp/*|/private/tmp/*)
    echo "manifest path '{path}' is absolute or session-scoped — must be repo-relative and durable"; exit 1;;
esac
git ls-files --error-unmatch "{path}" >/dev/null 2>&1 || \
  git ls-files --error-unmatch "{path}"/* >/dev/null 2>&1 || \
  { echo "manifest references '{path}' but it is not tracked — force-add it (git add -f) or drop the field"; exit 1; }
```

If the evidence genuinely lives only in a scratchpad and you do not intend to persist it, **omit the field entirely** — an absent pointer is honest, a dangling one is not. Do not "fix" this by rewriting the path string to a location the files were never copied to; move the files, force-add them, then record the tracked path.

## 2. Re-assert the completeness invariant

Before declaring done, verify and stamp:

- `completeness.frames_with_empty_section_list` is **empty**. If not, step-02's gate was bypassed — halt, do not emit a malformed manifest.
- `completeness.sections_total` == the number of grid-scaffold rows. A mismatch means a section was enumerated but not scaffolded (or vice versa) — reconcile before emitting.
- Every `drawn: true` frame appears in BOTH the section inventory and the grid scaffold.

Stamp `ingest.date` and `completeness.*` now (the orchestrator has the clock; scripts do not).

## 3. PAUSE — hand back to the user as a conversation, then STOP

This is the moment the whole workflow exists for, so don't end it with a status box — **talk to the user.** Write the manifest, then have a real handoff conversation. Do NOT proceed to any implementation.

Cover these, in your own words and in this spirit:

- **If the handoff is superseded (`{handoff_supersede_status} == superseded`), LEAD with it — before the walkthrough.** Tell them plainly: this handoff is superseded by `{superseded_by}` — that newer brief is the current truth. You built the manifest anyway so they can review/audit/diff it, but if they want the *current* design they should re-run `design-ingest` against `{superseded_by}`. And note the work may already be applied, so `design-implement` would likely find no deltas. Don't bury this under the section list — it's the first thing they need to know. (If `ambiguous`, say two briefs claim `active` for this slug and the predecessor chain needs fixing — point at `brief-revision-policy.md` §2.6 — but the manifest itself is fine. If `no_brief`, a one-liner that there's no brief on disk for this slug, so supersede couldn't be checked — you're not asserting it's current, you just can't tell.)
- **Where things stand:** you've gone through the design and listed everything out, and nothing has been changed yet — this is a checkpoint, not a result.
- **Walk them through what you found:** screen by screen, the sections each one has — in plain language, with the heavy/important screen (usually the detail drawer) spelled out in full so they can actually eyeball it. This is the part they're meant to read, so make it readable, not a dump.
- **Call out anything you're unsure about:** a screen that came back thin, a section whose data the implementation might not have, anything that made you hesitate.
- **Invite the check, directly:** ask them to look the list over — does each screen's sections look complete, or is something missing? This is exactly the review that catches a whole section being dropped, so make the ask real, not a footnote.
- **Tell them what happens next, plainly:** when they're happy, you (or they) run design-implement on the manifest and it'll work straight off this list — it won't re-read the bundle, and every section is already a row so nothing gets skipped. If a screen looks short, they point you at it and you re-check that one.

The concrete facts to hand them (weave these in naturally, don't print a form):

- the manifest's saved at `{manifest_path}`
- it covers `{frames_drawn}` drawn screens (`{frames_total}` declared) and `{sections_total}` sections, one grid row each
- supersede status: `{handoff_supersede_status}` (and, if `superseded`, that the stamp is on the manifest and the current design is `{superseded_by}`)
- the next command is `/bmad:bmm:workflows:design-implement {manifest_path}` — and if `superseded`, the alternative is to re-run ingest against the current brief: `/bmad:bmm:workflows:design-ingest <source of {superseded_by}>`

Then stop and wait. If something has genuinely failed (an empty manifest, a broken invariant — §2 above), that's the one case where a short, plain failure note is the right call instead of the friendly walkthrough.

---

## SUCCESS METRICS

- `{manifest_path}` written to `{implementation_artifacts}`, readable on `main`.
- Every dereferenced path recorded in the manifest is repo-relative, tracked, and matches the name on disk (§1a) — no absolute or scratchpad path shipped in a durable artifact.
- `completeness.frames_with_empty_section_list` empty; `sections_total` == grid-scaffold row count.
- Every drawn frame present in both the section inventory and the grid scaffold.
- The `ingest.supersede_status` stamp is present on the manifest (one of `active | superseded | no_brief | ambiguous`), with `superseded_by` set iff `superseded`. If `superseded`, the pause LED with the heads-up — it was not buried under the section list.
- The workflow PAUSED at the handoff — it did not chain into apply.

## FAILURE MODES

- **Auto-chaining into design-implement** — defeats the reviewable handoff. Step-03 stops.
- **Emitting a manifest with an empty section list on a drawn frame** — a malformed manifest `design-implement` must refuse; the invariant check exists to prevent it.
- **Grid scaffold missing a row that the section inventory lists** — the scaffold is the grid skeleton; a missing row is a section design-implement will be blind to.
- **Recording a scratchpad path as a durable evidence pointer** — the referent is reaped with the session, so the manifest dereferences to nothing while looking complete. §1a exists to stop this; omitting the field is always better than a dangling one.
- **Discovering a concurrent session at THIS step** — by the time the manifest is written, the fan-out is already spent and the other session's staged work is one clobbering write away. The collision check belongs in step-01 §5a, before the spend; reaching step-03 and finding a duplicate means §5a did not run.
