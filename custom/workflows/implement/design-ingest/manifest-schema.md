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
  surface_existence: {brownfield | net-new-surface | unknown}      # resolved in design-ingest step-01 §5b by probing origin/main (NEVER the working tree) for a route + page component for target_slug. `net-new-surface` means there is nothing to diff against — design-implement will soft-exit at its own existence gate. TERMINAL FOR PRESENTATION: a manifest carrying `net-new-surface` is a CATALOGUE and must never be handed off, summarised, or stamped as ready to implement. ABSENT ⇒ a consumer MUST read it as `unknown`, never as `brownfield`. (FG-2026-07-28-07)
  layout_constraints:                   # design-implement step-03 §2d denominator; sourced from docs/design-policy.md (authoritative) per design-implement URL.2
    source: {policy | README-generated | bundle-wrapper}
    assertion: {verbatim framing rule}
    resolved: { width: {full-bleed | <px>}, centered: {bool}, padding: {value} }
    authoritative: {bool}               # true only when read from docs/design-policy.md
  manifest_grain: {value-exact | partial | summary}   # REQUIRED. What this manifest may be TRUSTED FOR. Consumers branch on it — see "Grain invariant". ABSENT ⇒ a consumer MUST read it as `summary` (conservative default), NEVER as value-exact.
  completeness:
    frames_total: {int}
    frames_drawn: {int}
    sections_total: {int}               # sum of frame_sections across all drawn frames
    sections_per_frame:                 # REQUIRED. One entry per drawn frame. A single total is unverifiable by eye; this map makes the arithmetic machine-checkable AND localises which frame is miscounted. Must sum to sections_total. (FG-2026-07-27-06)
      {frame}: {int}
    frames_with_empty_section_list: []  # MUST be empty for a clean manifest — a non-empty list is a frame-completeness defect (step-02 should have halted)
    frames_not_enumerated: []           # OPTIONAL, and an HONEST failure: frames whose enumeration could not be completed (e.g. the step-02 fan-out died and no fallback applied). A named non-empty list is a declarable partial; silently omitting a frame is not. design-implement must refuse a manifest with a non-empty list unless the operator explicitly accepts the partial.
    sections_with_property_rows: {int}      # of sections_total, how many carry a VALUE-EXACT component×property cell
    sections_missing_property_rows: []      # "<frame> / <section>" per section whose property cell is prose-only, elided (`…`), or empty. MUST be empty iff manifest_grain == value-exact.
    resolved_vocabularies: []               # Every ALL-CAPS vocabulary the manifest DEREFERENCES (DECISION, DEFECT, GAPS, LIFECYCLE…) whose members it resolves to literals — inline, or in a `Vocabulary: <NAME>` block. See "Vocabulary resolution" below. (FG-2026-07-27-09)
    unresolved_references: []               # THE LOGGED OVERRIDE. "<NAME>: <why>" per vocabulary that genuinely could not be resolved. A declared deferral is reported and consumable; an UNdeclared one is a defect (C11), because the consumer cannot tell the difference between "deferred" and "forgotten".
  tokens:                               # SUMMARY ONLY, and NOT a substitute for reading the design source — see "Restated source facts".
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

### `status` vocabulary — four values; a scope decision MUST use the third, an unwired build MUST use the fourth

| value | meaning | resume behaviour |
|---|---|---|
| `UNVERIFIED` | not yet dispositioned — the walkable set | selected by the resume walk |
| `✓ applied` | dispositioned by a prior pass **and reachable by an operator** | terminal — never re-applied |
| `⊘ deferred(<reason>)` | deliberately out of scope (owner ruling, policy, missing backend) | **terminal — never auto-selected** |
| `◐ transcribed · UNROUTED` | the code faithfully implements part of the brief but **has no reachable path for an operator yet** | **NON-terminal — an outstanding obligation.** Never counts as applied; blocks "frame fully applied" |

**`◐ transcribed · UNROUTED` — the fourth value, and why `✓ applied` was not enough.**
`applied` conflated two different questions: *do the values match the design?* and *can anyone reach
this?* A transcribed-but-unwired component answers **yes** to the first, so it read as `applied` under
every available reading — the row was not wrong, the state was **inexpressible**. Rules:

- **Never treated as `applied`.** A frame holding any `◐` row is not fully applied, and no pass may
  report it as such.
- **Listed ABOVE the grid as an explicit open item** — never left to be inferred from a table cell, and
  never written only in narrative below the grid. A resume read consults row statuses and the block
  above them; prose further down is not read in time to matter.
- **A resume walk treats `◐` as outstanding work.** It is the one non-terminal disposition:
  `UNVERIFIED` means "not looked at yet", `◐` means "built, and the wiring is owed".
- **Every `◐` carries its follow-up** — who wires it, and into what. `◐` with no named follow-up is the
  same silent-staging failure wearing a new symbol.

**Choosing between `◐` and `⊘ deferred`.** They are not interchangeable, and the difference is whether
code was written. `⊘ deferred` = *we decided not to build it* (nothing exists; terminal). `◐` =
*we built it and it is unreachable* (code exists; obligation outstanding). Downgrading a `◐` to
`⊘ deferred` to close a pass is a **misreport**: it leaves live code in the tree that no operator can
reach and no row is tracking.

**Origin (cash-recovery `/receive`, 2026-07-20 → 2026-07-26).** Two frames were transcribed, their nine
rows marked `✓ applied`, their forced deviations logged correctly, and shipped in two PRs. Both
components had **zero non-test importers for six days.** The authoring pass *did* write "not yet
wired… the largest un-owed piece" — 60 lines below a table of nine green ticks. Three later sessions
read that manifest and none reopened it, because the grid said closed. That is the failure this value
exists to make unrepresentable. Backing entry: `docs/fork-gaps.md` **FG-2026-07-26-05**.

**A scope decision written only as prose in the manifest body does not bind the resume walk.** The one mechanism that decides what to build next reads *row statuses*, not narrative — so an owner ruling or policy deferral recorded in a `### OWNER DECISION` table while the rows stay `UNVERIFIED` leaves a frame that must NOT be built reading as the frame that SHOULD be built next. That is the dangerous direction of failure, and it is discretionary protection: it holds only while every future session re-reads the whole file.

So: **when a frame or section is out of scope, stamp `⊘ deferred(<reason>)` into its status cells at scaffold time**, in the same pass that writes the prose. The prose explains; the cell binds. Keep the reason inline and specific (`⊘ deferred(policy §8.2b: clerk grading stays desktop-only)`, `⊘ deferred(no offline backend)`) — a reason that can lapse needs to say what would un-defer it. Re-enabling a deferred row is then a deliberate edit of the cell, not the default. (fork-gap 2026-07-25)
| frame | section | design copy/structure (verbatim) | data fields read | component×property rows | status |
|---|---|---|---|---|---|
| supply-order-detail-drawer | Reconciliation | recon-lead 3 branches ("Not gathered yet." / "Reconciled clean." / gap); recon-grid 4 fixed tiles | quantity, amazonDeliveredQty, amazonHeldQty, amazonReturnedQty, varianceResolution | .recon-lead{12px,subtle-fg} · .recon-grid{grid 4×1fr,gap8} · .rc-cell{border,radius7,inset-bg} · .rc-n{15px,600} · .rc-l{10px,muted} | UNVERIFIED |
| supply-order-detail-drawer | SellerSmart dispatch | "SellerSmart dispatch" h4 + dispatch pill + §13 link | (dispatch fields — see data-availability note) | `PROPERTY-ROWS-MISSING(no impl view-model fields)` | UNVERIFIED |
| … one row per (frame, section) … | | | | | |

**The `component×property rows` cell is LOAD-BEARING, and an elision in it is a defect, not a
shorthand.** It is the only place a resolved CSS value survives ingest, so a cell reading `…` or
carrying prose (`"46px, white, hairline base"`) instead of value-exact declarations silently
converts a value-exact manifest into a summary one — while every other field still looks complete.
When the values genuinely cannot be resolved, write the explicit sentinel
**`PROPERTY-ROWS-MISSING(<reason>)`** and list that section in
`completeness.sections_missing_property_rows`. Never leave the cell bare, and never let `…` stand in
a delivered manifest: an honest sentinel is greppable and forces `manifest_grain: partial`, whereas
an ellipsis reads as "omitted for brevity" to every future reader.

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

**The stamp is resolved ONCE, for the manifest being written — which leaves one path that defeats it.** A re-ingest that ARCHIVES the prior manifest under a discriminated filename (rather than overwriting it) produces a file whose `supersede_status` says `active` while the brief behind it is superseded, because nothing re-resolves an existing manifest's stamp. A later session that opens the archived file reads `active` and `design-implement` proceeds normally — the exact silent apply this stamp exists to prevent. So the archiving run MUST restamp it: `supersede_status: superseded`, `superseded_by: <successor BRIEF filename>` (per the field table above — a brief, never the successor manifest), plus `successor_manifest:` naming the run that archived it. Procedure and the accompanying inbound-reference report: `steps/step-01-frame-inventory.md` § "Restamp the archived manifest".

**An archived manifest is not inert.** It remains the only provenance for rows already applied from it, so it is retained, not deleted — and its applied rows do **not** transfer to the successor grid when `bundle_shape` differs (`legacy_jsx` vs `dc_html` catalogue different documents). State the transfer verdict on the archived file; rows that look transferable and are not are how a superseded design gets re-applied under a green grid.

### Multi-writer contract — who may write this file, when, and what a second writer must do

**The manifest is a SHARED, multi-writer artifact, and multi-writer is its DESIGNED operating mode** — the resumable-apply rule exists precisely because a large surface needs many passes across many sessions. This schema defines the artifact's *fields*; the authorship rules are in **`docs/manifest-contract.md`** (fork docs) and are binding on every writer. The short form, because the silence here is what let two sessions each believe they were the only writer:

- **A pass is identified by a stamped `pass_id` (`<session_id>-<UTC compact>`), never by reading the file and adding one to the highest `Pass N`.** That derivation is a read-modify-write race; on 2026-07-20 it produced two `Pass 4`s and, an hour later, two `Pass 5`s in this exact artifact. `session_id` is the only field a reader or gate compares — the `claude-session-<timestamp>` header is a display label and is provably non-unique under concurrency.
- **Pass records are append-only.** Never renumber, reorder in place, or re-identify an existing record. A retained pass number is a **derived** `seq` (position when sorted by `started_at`), regenerable, not identity. When file order cannot equal run order, the out-of-order record says so explicitly.
- **The `(frame, section)` grid rows stay mutable** — that is resume state, owned by whichever pass applies the section. Only the pass narrative is append-only. Keeping those two roles apart is what stops a benign concurrent append from becoming data loss.
- **Take the current-editor marker before the first write, release it at handoff.** `<main-checkout>/.claude/manifest-locks/<manifest>.lock.json`, resolved via `git rev-parse --git-common-dir` so it is visible from every worktree immediately with no commit. A live marker held by another session forces **explicit reconciliation, never a silent merge**; no session may clear another's marker.
- **Commit the manifest explicitly by path (`git add -f`) or leave it out.** A broad `git add -A` / `git stash` / sync sweep is how one session's uncommitted manifest work gets scooped into another's commit.

Detection is deterministic (`~/.claude/hooks/manifest-contract-gate.py`, PreToolUse, WARN-only); taking the marker and reconciling a real concurrent edit are probabilistic. See the contract's Enforcement section for the honest split and the WARN→DENY promotion criteria.

### Path invariant — every dereferenced path is repo-relative and durable

**Any path this manifest records that a downstream workflow will DEREFERENCE must be repo-relative and point at a committed, durable location. A session-scoped path in a durable artifact is always a bug.**

This covers `ingest.source` when it is a local directory, and any evidence pointer a run chooses to record — e.g. an optional `ingest.frame_catalogs_dir` naming where step-02's per-frame catalogs were persisted. Such a field is **not required**, but if it is present it is load-bearing, and the rule is absolute:

- **Repo-relative, from the repo root** (`_bmad-output/implementation-artifacts/…`), never absolute, and never a harness scratchpad path (`/private/tmp/…/<session-uuid>/scratchpad/…`, `/tmp/…`).
- **The referent must be tracked** — force-added and verified with `git ls-files --error-unmatch`, exactly as the manifest itself is (step-03 §1). An untracked referent is the same silent-empty-emit failure the force-add rule exists to stop.
- **The name recorded must be the name on disk.** Recording one path while the durable copies land under a different name produces a manifest that *looks* complete and dereferences to nothing.

**Why (2026-07-20, cash-recovery).** A delivered manifest stamped `frame_catalogs_dir` as the emitting session's own `/private/tmp/.../<session-uuid>/scratchpad/...` directory — reaped when that session ended — while the durable catalogs were force-added into the repo under a different name. The manifest shipped a latent dangling pointer to its own evidence, and nothing in the schema or the emit step objected. `design-implement` would have dereferenced it into a void, on a path it had no way to distinguish from a good one.

### Completeness invariant

`ingest.completeness.frames_with_empty_section_list` MUST be empty in a delivered manifest. A non-empty list means step-02's per-frame completeness gate did not halt as it should have — the manifest is malformed and `design-implement` should refuse it (the same bounce-back shape as the synthesize-bundle gates).

**The arithmetic is MACHINE-VERIFIED, not hand-summed — `tools/check-ingest-manifest.js`.** step-03 §2 invokes it with `--strict`, and the emit is blocked on a clean run. It derives the counts independently from the emitted file and asserts them against what the frontmatter declares: grid-scaffold rows == `sections_total` (C1) · per-frame grid rows == each frame's declared `(N sections)` heading (C2) == `sections_per_frame[frame]` (C3) · every `drawn: true` frame present in BOTH the section inventory and the scaffold (C4) · no grid rows for an undeclared frame (C5) · `frames_with_empty_section_list` empty (C6) · `manifest_grain: value-exact` requires an empty `sections_missing_property_rows` (C7) · no duplicate frame-inventory rows (C8) · `sections_per_frame` sums to `sections_total` (C9).

**Why a tool and not an instruction (FG-2026-07-27-06).** Both sides of "verify `sections_total` == grid rows" used to be produced by the same agent, by hand, with no mechanism — so "verify" meant "add it up again and hope". A real 2026-07-27 run declared `sections_total: 66` against a 73-row grid and caught it only by an ad-hoc script. That is this fork's own anti-pattern turned on its own gate: *a field an agent self-reports will eventually be wrong; the harness must stamp anything a gate keys on.* The checker deliberately does **not write** `sections_total` — the agent still declares it and the tool still disagrees, because it is the disagreement between two independent derivations that catches the error.

**What a green run does NOT mean.** It proves the manifest's numbers agree with themselves. It cannot prove the enumeration is COMPLETE — a section nobody wrote down is invisible to a reader of the manifest by construction. That axis is carried by the step-02 fan-out and by the human review at the step-03 handoff pause, and must never be claimed from a green checker run.

### Grain invariant — a manifest must declare what it can be trusted for

**Section coverage and VALUE coverage are two different completeness questions, and this schema used to answer only the first.** `frames_with_empty_section_list` proves every drawn frame was enumerated; it says nothing about whether any section's `component×property rows` cell holds resolved values. So a manifest could pass every gate here, be fully compliant, and still carry prose anchors — while `design-implement` step-01 **MANIFEST.2** is told to build its CSS property catalog from exactly those cells. Producer-compliant and consumer-contract-unmeetable at the same time, with nothing in between to object.

`ingest.manifest_grain` closes that by making the manifest state its own trust level:

| value | means | `design-implement` must |
|---|---|---|
| `value-exact` | EVERY drawn section carries value-exact `component×property rows`. `sections_missing_property_rows` is empty. | Build the property catalog from the scaffold. No source re-read needed. |
| `partial` | Some sections carry values; the rest are sentinelled and listed in `sections_missing_property_rows`. | Use the scaffold where present; **re-read the design source for every listed section.** |
| `summary` | Section inventory + completeness gate only. Property cells are prose/absent throughout. | Treat the manifest as the *section denominator only* and **re-read the design source for values.** |

**`summary` is a legitimate, useful manifest — not a failure.** The section inventory and the frame-completeness gate are most of this artifact's value, and they are exactly what a fresh context cannot cheaply reconstruct. Declaring `summary` costs a source re-read; *undeclared* summary costs correctness. The point of the field is to stop a consumer inferring value-exactness from a manifest that never claimed it.

**Absent field ⇒ `summary`.** Older manifests predate this field; the conservative default keeps them consumable and makes the failure direction safe (an unnecessary re-read, never a wrong value).

### Restated source facts — the manifest must not assert what it cannot keep true

**The manifest is a DERIVED artifact. Every source fact it restates in prose is a copy that can drift from the design, and the manifest is precisely the thing a fresh context trusts *instead of* the source.** An incomplete manifest degrades safely (the consumer notices and re-reads); a **lossy but confident** one is worse than absent, because it is authoritative-by-position for a reader who will never open the design file.

So, for the `tokens:` block, the section-inventory copy column, and any `## Findings` prose:

- **Prefer structure over values.** Record *that* a section exists, *what* it is called, *which* fields it reads. Let the design source own exact px/hex/label values, and let `manifest_grain` say whether the property cells can be trusted for them.
- **A restated value carries a source reference** (`<file>:<line>` or the frame + banner it came from) or it does not go in.
- **A finding must not assert a negative it did not exhaustively check.** "No `<img>` exists anywhere in the component" is an exhaustive-search claim. State the search that was actually run and its scope, or record the observation narrowly ("the row's 40×40 box is a placeholder div in the default branch").
- **Never reason downstream from a restated fact.** A finding that concludes *"…so `design-implement` would have to infer the resolved treatment"* has built an inference-hazard warning on top of a copy. If the premise drifts, the warning becomes the hazard.

**Why (2026-07-25, cash-recovery, `FG-2026-07-25-14`).** A delivered, completeness-passing manifest for the Clerk Inbound Board carried three restated facts that were wrong against its own source: finding **F2** asserted no `<img>` existed anywhere and that the resolved-thumbnail treatment was never drawn (the source draws one in **three** places inside `<sc-if value="{{ r.img }}">`, and F2 then reasoned from that false premise to an inference warning); `tokens.type_scale.primary_numeral` said `30px` where the source said **26px**; and the section-8 prose named a filter chip *"Can't vouch"* where the source's `filters` array said **`Gaps`**. All three were caught only because that run re-read the design source **contrary to** the manifest path's own "no re-ingest" shortcut. A session that honoured MANIFEST.2 as written would have shipped the wrong numeral, the wrong label, and a fabricated thumbnail treatment, with every gate green.

---

## Vocabulary resolution — a reference is not a value (FG-2026-07-27-09)

`manifest_grain: value-exact` promises the consumer it need not re-read the design source. A cell
that records **`DECISION[decision].label`** breaks that promise while looking like it keeps it: the
row is present, ordered, dispositioned and specific — and the string the surface actually renders is
nowhere in the file.

**The rule.** When a section's copy or data cell dereferences an ALL-CAPS vocabulary
(`DECISION[x].label`, `DEFECT[].note`, `GAPS[k].label`), the manifest MUST resolve every member it
can reach — inline, or once in a `### Vocabulary: <NAME>` block that rows dereference the same way
they dereference `→ §6/<id>` — and list `<NAME>` in `completeness.resolved_vocabularies`. A
vocabulary that genuinely cannot be resolved is declared in `completeness.unresolved_references`
with a reason. Silence is the one disallowed option.

**Why this is a hard rule and not a preference.** The consumer's transcription contract says copy is
reproduced VERBATIM and a paraphrase is prohibited. So an unresolved reference leaves exactly two
legal moves — re-read the design source, or halt. And the re-read is precisely what a **delegated
sub-agent cannot do**: the design MCP is session-bound and absent from sub-agent contexts
(`FG-2026-07-26-01` / `-06`), which is the documented way a large surface is meant to be handled.
Compose the two and a delegated run has no legal continuation at all; the only remaining exit is to
invent the string. Every previous fabrication incident in this fork started as a gap that looked
like a detail.

**Not a completeness question — a TRUST question.** `frames_with_empty_section_list` proves every
frame was enumerated; `sections_missing_property_rows` proves every section carries values. Neither
looks INSIDE a cell, so a manifest can satisfy both and still be unimplementable. Machine-checked by
`tools/check-ingest-manifest.js` **C11**, which fires only on the `NAME[...].field` shape (an
ALL-CAPS identifier, indexed, dereferenced) — lowercase accessors and `.length` are invisible to it.

**It is not rare.** On the sweep that introduced the check, **four of eight** delivered manifests in
one project carried at least one unresolved vocabulary — `DECISION`/`DEFECT`, `WINDOW`/`LIFECYCLE`/
`CLAIM_TYPES`/`EVIDENCE`, `ORDER_LINES`. Every one of them declared value-exact grain.
