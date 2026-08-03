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
  - **Any frame or section already known to be OUT OF SCOPE gets `⊘ deferred(<reason>)` in its status cells, not `UNVERIFIED`** — stamped here, in the same pass that writes the scope prose. If this manifest records an owner ruling or a policy boundary (an `### OWNER DECISION` block, a design-policy section that keeps a surface on another route, a frame whose backend does not exist), the machine-readable cell and the narrative must agree. Prose alone does not bind: `design-implement`'s resume walk selects on row status, so an out-of-scope frame left `UNVERIFIED` reads to a later session as the next thing to build. Reason inline and specific — `⊘ deferred(policy §8.2b: clerk grading stays desktop-only)` — and say what would un-defer it if the reason can lapse. Vocabulary + rationale: `manifest-schema.md` → `status` vocabulary. (fork-gap 2026-07-25)
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

## 2. Re-assert the completeness invariant — RUN THE CHECKER, do not hand-sum

Stamp `ingest.date` and `completeness.*` first (the orchestrator has the clock; scripts do not) — including the REQUIRED `completeness.sections_per_frame` map, one entry per drawn frame.

Then **verify by running the tool, not by adding it up again:**

```bash
node ~/bmad-method-v6/tools/check-ingest-manifest.js --manifest {manifest_path} --strict
```

A non-zero exit is a **HALT** — fix the manifest and re-run; do not emit. It asserts, independently of your own arithmetic: grid rows == `sections_total` (C1) · per-frame grid rows == each frame's declared `(N sections)` heading (C2) == `sections_per_frame[frame]` (C3) · every `drawn: true` frame in BOTH the section inventory and the scaffold (C4) · no grid rows for an undeclared frame (C5) · `frames_with_empty_section_list` empty (C6) · the §2a grain pair (C7) · no duplicate frame rows (C8) · `sections_per_frame` sums to `sections_total` (C9).

**Quote the checker's output in the handoff — a claim with no run is UNVERIFIED.** "Invariants satisfied" without the command's result is exactly the assertion this replaced.

**Why this is a tool now (FG-2026-07-27-06).** This step used to say "verify `sections_total` == the number of grid-scaffold rows" and offer no mechanism, so both sides of the equation were the agent's own hand-arithmetic. A 2026-07-27 run declared `sections_total: 66` against a 73-row grid — the five `claim-workspace--*` variants under-counted by one frame's worth — and caught it only via a throwaway script. A gate keyed on a self-reported number is the fork's own named anti-pattern (`actor` / `claimed_by` / `claimed_at`); the fix is a second, independent derivation that can disagree with you. The checker deliberately does NOT write `sections_total` — you still declare it, and the disagreement is the whole mechanism.

**And be clear what green means.** A clean run proves the numbers agree with themselves. It does **not** prove the enumeration is complete — a section nobody wrote down is invisible to a reader of the manifest by construction. Completeness is carried by step-02's fan-out and by the human review at the §3 pause. Never report a green checker run as evidence that nothing was missed.

### 2a. Classify the GRAIN — and never let it default silently

Section coverage (above) and VALUE coverage are different questions. This step used to answer only the first, which let a prose-only manifest satisfy every gate while `design-implement` MANIFEST.2 was told to build its CSS catalog from the property cells (`manifest-schema.md` → "Grain invariant"; fork-gap `FG-2026-07-25-14`).

Walk the grid scaffold and classify each row's `component×property rows` cell:

- **value-exact** — resolved declarations (`.rc-n{15px,600}`), not prose, not `…`.
- **missing** — prose (`"46px, white, hairline base"`), an ellipsis, empty, or an explicit `PROPERTY-ROWS-MISSING(<reason>)` sentinel.

Then stamp, and HALT on the one inconsistency that matters:

- `completeness.sections_with_property_rows` = the value-exact count.
- `completeness.sections_missing_property_rows` = `"<frame> / <section>"` for every missing one.
- `ingest.manifest_grain` = `value-exact` if the missing list is empty · `summary` if NO section carries values · `partial` otherwise.
- **HALT if `manifest_grain: value-exact` and `sections_missing_property_rows` is non-empty** — that combination is the exact lie the field exists to prevent. Fix the grain or fill the cells; never emit both.
- **Replace every bare `…` with the sentinel before emitting.** An ellipsis reads as "omitted for brevity" to every future reader; the sentinel is greppable and forces an honest grain.

**Declaring `summary` is not a failure and must not be treated as one.** The section inventory + frame-completeness gate are most of this manifest's value and are exactly what a fresh context cannot cheaply rebuild. The cost of an honest `summary` is one source re-read downstream; the cost of an *undeclared* summary is a wrong value shipped with every gate green.

### 2b. Strip restated source facts you cannot keep true

Before emitting, re-read your own `## Findings`, `tokens:`, and section-copy prose against the design source and apply `manifest-schema.md` → "Restated source facts":

- A restated value carries a source reference, or it comes out.
- A finding must not assert an exhaustive negative ("no `<img>` exists anywhere") unless that search was actually run — state the scope that WAS checked.
- No finding may reason downstream from a restated fact (an inference-hazard warning built on a copy becomes the hazard when the copy drifts).

This is the half that bit hardest in `FG-2026-07-25-14`: three restated facts in a completeness-passing manifest were wrong against its own source, and only a run that re-read the source *contrary to* the no-re-ingest shortcut caught them.

## 3. PAUSE — hand back to the user as a conversation, then STOP

This is the moment the whole workflow exists for, so don't end it with a status box — **talk to the user.** Write the manifest, then have a real handoff conversation. Do NOT proceed to any implementation.

Cover these, in your own words and in this spirit:

- **If the handoff is superseded (`{handoff_supersede_status} == superseded`), LEAD with it — before the walkthrough.** Tell them plainly: this handoff is superseded by `{superseded_by}` — that newer brief is the current truth. You built the manifest anyway so they can review/audit/diff it, but if they want the *current* design they should re-run `design-ingest` against `{superseded_by}`. And note the work may already be applied, so `design-implement` would likely find no deltas. Don't bury this under the section list — it's the first thing they need to know. (If `ambiguous`, say two briefs claim `active` for this slug and the predecessor chain needs fixing — point at `brief-revision-policy.md` §2.6 — but the manifest itself is fine. If `no_brief`, a one-liner that there's no brief on disk for this slug, so supersede couldn't be checked — you're not asserting it's current, you just can't tell.)
- **If `{surface_existence} == net-new-surface`, LEAD with that too** (alongside supersede, before the walkthrough) — the operator continued past the §5b probe deliberately, so this is a reminder, not news. Say plainly that this surface has no route and no page component on `origin/main`, so what you've built is a **catalogue of the design, not a plan against an implementation**: `design-implement` will soft-exit at its own existence gate until the surface is scaffolded. **Do NOT describe this manifest as ready to implement, and do NOT make `/bmad:bmm:workflows:design-implement {manifest_path}` the headline next command** — name the onboarding path first (build the minimal backend → brownfield `design-handoff` → `design-synthesize` → `design-implement`), say which of those steps the §5b probe found already done, and offer the implement command as the step AFTER that. The 2026-07-31 `intake-pilot-console` handoff recorded the net-new fact in a flag and still closed with "READY FOR IMPLEMENT"; a verdict the artifact carries but the handoff contradicts is not a gate. (If `unknown`, one line that the probe could not resolve, so you can't tell — don't assert brownfield.)
- **If this run ARCHIVED a prior manifest under a new filename, say what you did to it and what the rename broke.** Two things, both plainly: (a) the archived file was restamped `supersede_status: superseded` per step-01 § "Restamp the archived manifest", so a later session opening it cannot read `active` and apply a superseded design — and whether its applied rows transfer to this grid (they do not when `bundle_shape` differs; say so, because the rows LOOK transferable); (b) the inbound references step-01 grepped, listed by path. The un-discriminated filename now resolves to THIS manifest, so every one of those pointers still resolves while silently meaning something else — that is a retarget, not a break, and nothing will error. Name them and say you did not rewrite them.
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
- The `ingest.surface_existence` stamp is present (one of `brownfield | net-new-surface | unknown`). If `net-new-surface`, the pause LED with it, the manifest was described as a CATALOGUE rather than as ready to implement, and the onboarding path — not the `design-implement` command — was the headline next step.
- **If a prior manifest was ARCHIVED under a new filename:** that archived file now carries `supersede_status: superseded` + `superseded_by` (a BRIEF) + `successor_manifest`, and the pause named both the row-transfer verdict and the inbound references the rename retargeted. An archived manifest left reading `active` is a FAILED run — it is the one path that silently defeats `design-implement`'s stale-apply refusal.
- The workflow PAUSED at the handoff — it did not chain into apply.

## FAILURE MODES

- **Auto-chaining into design-implement** — defeats the reviewable handoff. Step-03 stops.
- **Emitting a manifest with an empty section list on a drawn frame** — a malformed manifest `design-implement` must refuse; the invariant check exists to prevent it.
- **Grid scaffold missing a row that the section inventory lists** — the scaffold is the grid skeleton; a missing row is a section design-implement will be blind to.
- **Recording a scratchpad path as a durable evidence pointer** — the referent is reaped with the session, so the manifest dereferences to nothing while looking complete. §1a exists to stop this; omitting the field is always better than a dangling one.
- **Discovering a concurrent session at THIS step** — by the time the manifest is written, the fan-out is already spent and the other session's staged work is one clobbering write away. The collision check belongs in step-01 §5a, before the spend; reaching step-03 and finding a duplicate means §5a did not run.
- **Handing off a `net-new-surface` manifest as ready to implement** — the section list can be flawless and the handoff still wrong, because the next command it names cannot run. Recording the fact in the receipt and contradicting it in the narration is worse than not detecting it: the artifact now certifies a state the prose denies. The probe belongs in step-01 §5b, before the spend; the presentation rule belongs here.
