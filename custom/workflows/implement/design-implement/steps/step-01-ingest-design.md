---
name: 'step-01-ingest-design'
description: 'Ingest the design source. Routes on input_kind to ONE of three path files (step-01a URL / step-01b bundle / step-01c manifest), then converges here at §SHARED to verify the catalog, resolve supersede + brief conformance, and emit the ingestion summary.'
---

# Step 1: Ingest Design

**Progress: Step 1 of 4** (+ a step-02b regression-surface preflight between map and grid) — Next: Map Implementation (autonomous)

**Announce the plan up front (one line to the user) before ingesting:** this run will ingest the handoff, map the current implementation, then — *before changing any code* — **run a regression-surface check: what does this handoff DROP relative to what production does today?** If it drops a capability, the run pauses and **advises a per-capability keep/drop plan to approve** — not a blank menu to fill in — rather than silently reproducing the omission (step-02b). State this so the user knows the capability check is coming; then proceed autonomously through ingest + map.

## RULES:

- FULLY AUTONOMOUS through ingest + map. No user interaction in steps 01–02. The first (and usually only) halt is step-02b's strategy choice, and only when the handoff drops a production capability.
- **Branch on `{input_kind}` at the top, and read ONLY that path's file.** The three ingestion paths converge on the same downstream state. Never mix them: a `synthesize_bundle` path never calls curl; a `claude_design_url` path never reads `manifest.yaml`.
- If download fails (URL path only), retry once. If it fails again, report the error and stop.
- Read every file in the bundle that the target design file references — do not skip any.
- **Catalog the state axis explicitly.** Inline `style="…"` attributes only describe a single rendering. State-conditional rules live in (a) `<style>` blocks inside `<screen>.html` with `:hover`, `:focus`, `[data-state="…"]`, `.failed`-style selectors, (b) sibling element instances carrying `data-state="…"` variants, and (c) — for URL-path bundles — JSX conditional styling keyed on a prop or row.status. **Skipping any of these three is silent failure**: the default-state grid will rate `✓` while the state-conditional rule ships as a delta. Every property row records a `state` field; if no state is detectable for an element, record `state: default`.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## INPUT-KIND BRANCH — read ONE path file, then come back here

This step has three parallel ingestion paths, split into their own files so a run loads only the one it executes. All populate the same downstream state — `{design_dir}` (or, on the manifest path, no dir), `{design_file}`, `{design_components}`, `{design_tokens}`, `{design_frame_inventory}`, `{design_layout_constraints}`, and the CSS-property catalog — so steps 2-4 are agnostic to which path ran.

```
if {input_kind} == "claude_design_url":  → read ./step-01a-ingest-url.md      (URL.*)
if {input_kind} == "synthesize_bundle":  → read ./step-01b-ingest-bundle.md   (BUNDLE.*)
if {input_kind} == "ingest_manifest":    → read ./step-01c-ingest-manifest.md (MANIFEST.*)
```

**Then RETURN HERE and continue at §SHARED.** The path files end by handing back; §SHARED is where the catalog is verified, supersede + brief conformance are resolved, and the summary is emitted. A run that stops at the end of its path file has skipped the gates.

**Why these are separate files (one job per step).** A run executes exactly ONE path but used to load all three, plus §SHARED, in a single ~94KB step — against a 95KB hard ceiling, so the next addition would have blocked. Splitting cuts the per-run read to ~77KB (URL), ~50KB (bundle) and ~41KB (manifest); the biggest saving lands on the manifest path, which is the one recommended for large surfaces and therefore the one where budget matters most.

### Citation legend — section ids are FILE-SCOPED, the names are unchanged

`§SHARED`, SUCCESS METRICS and FAILURE MODES below cite path sections by their original ids. Nothing was renamed in the split, so a citation resolves by prefix:

| citation prefix | lives in |
|---|---|
| `URL.1` … `URL.7` | `./step-01a-ingest-url.md` |
| `BUNDLE.1` … `BUNDLE.6` | `./step-01b-ingest-bundle.md` |
| `MANIFEST.1` … `MANIFEST.4` | `./step-01c-ingest-manifest.md` |
| `SHARED.*` | this file |

`workflow.md` also cites `step-01 §SHARED.1a` (still here) and `step-01 URL.1b` (now in `step-01a`).

Workflow.md's Input Resolution has already populated `{input_kind}`, `{design_url}` (URL path), `{bundle_dir}` + `{bundle_manifest}` (bundle path), or `{ingest_manifest}` (manifest path). For the bundle path, the refusal gates (`dev_no_render`, `needs_human_review`) have cleared; for the manifest path, the completeness-invariant gate (no drawn frame with an empty section list) has cleared — if execution reached this step with that `{input_kind}`, the manifest is good.

**The MANIFEST PATH is the context fix.** A large bundle (~140KB JSX) does not fit one ingest context — the failure mode was shortcutting the exhaustive per-component catalog to fit, which let a whole *section* go unenumerated. When `design-ingest` has already fanned out per-frame and emitted a reviewed grid scaffold, that path reads the scaffold instead of re-cataloging; the exhaustive enumeration already happened, durably, in `design-ingest`. **Read its grain first (`MANIFEST.1a`)** — the scaffold is only a value source when it says it is.

---

## SHARED — Property catalog and ingestion summary

Both paths converge here. `{design_components}` (with embedded `.properties` per component), `{css_property_catalog}` (flat view of the same rows), and `{design_tokens}` are populated; downstream steps don't need to know which path produced them.

**`{design_layout_constraints}` must be populated on BOTH paths — and the AUTHORITATIVE source is path-independent.** On either path, the binding layout rule comes from the project `docs/design-policy.md` (URL.2 precedence #1) — both the Claude-Design URL README and a synthesize bundle are generated artifacts downstream of that policy. The paths differ only in their *corroboration*: the URL path has a generated README + the bundle wrapper (URL.2); the **synthesize-bundle path has no README**, so its corroboration is the screen HTML's outermost layout element (root `<div data-region>` / `<body>` — `max-width` present → capped; absent → full-bleed; `margin:auto` → centered) plus `{bundle_manifest}.page_mode` (`operational`/`analytical`/`detail`) as a framing hint, tagged `source: "bundle-wrapper" | "manifest", authoritative: false`. Either path MUST leave `{design_layout_constraints}` non-empty (at minimum a `full-bleed` default from a wrapper with no `max-width`) so step-03 §2d's Page-shell row has a Design column; if the policy was readable, the policy entry is the one marked `authoritative: true`.

**The two stores must agree.** The same property rows appear in BOTH `{design_components}[name].properties` AND `{css_property_catalog}` — they are different shapes of the same data, not parallel writes that could drift. Step-03 reads via `{design_components}[name].properties` (component-by-component for the comparison grid); the flat catalog exists for SHARED's counts and as a defensive sanity store. If the two ever disagree, the per-component embedding is canonical.

### SHARED.1. Verify the catalog is non-empty — necessary, NOT sufficient

**Non-empty is a floor, not a grain check.** A prose-only manifest yields a non-empty `{css_property_catalog}` — every section still produces a row, the rows just carry prose — so this check passes on exactly the input MANIFEST.1a exists to catch. The two are a pair: **SHARED.1 proves rows exist; `{manifest_grain}` proves they carry values.** Never read a green SHARED.1 as "value-exact."

On the manifest path, also assert before leaving this step: `{manifest_grain}` is set (absent ⇒ `summary`); if it claims `value-exact` then `completeness.sections_missing_property_rows` is **empty** — if not, the manifest is internally inconsistent (`design-ingest` step-03 §2a should have halted), so downgrade to `partial`, re-read the listed sections, and disclose it in SHARED.2; and on `partial`/`summary` the required re-read has actually happened *here*, not deferred to step-03 where no source remains in context.

If `{css_property_catalog}` is empty, that is a step-1 failure regardless of input kind. Halt with:

```
INGEST FAILURE: no CSS properties cataloged.

input_kind:    {input_kind}
design_dir:    {design_dir}
design_file:   {design_file}
components:    {len(design_components)}
tokens:        {len(design_tokens)}

A non-empty design source produced no styled elements. This is either a malformed
source (URL path: design file has no JSX style blocks; bundle path: HTML has no
inline style attributes) or a parsing bug. Investigate before proceeding.
```

### SHARED.1a. Supersede awareness (URL / bundle paths) → `{handoff_supersede_status}`

Skip on the manifest path — `{handoff_supersede_status}` is already set from the stamp at intake (Input Resolution). On the URL and bundle paths there is no stamp, so resolve it HERE, now that the frame inventory exists (the slug isn't knowable before it). This is what lets a handoff handed STRAIGHT to `design-implement` cope with supersede, not only one that came through `design-ingest`. `brief-revision-policy.md` §8.

Resolve exactly as `design-ingest` step-01 §5 (same contract — do not duplicate the logic):

1. Derive `{target_slug}` from the primary frame (`{design_frame_inventory}` entry 0). Prefer an exact match to an existing brief's `target_slug`.
2. Match it against the briefs in `{implementation_artifacts}`, read `brief_status`, and set `{handoff_supersede_status}` to `active` | `superseded` | `no_brief` | `ambiguous` (`no_brief` when the surface doesn't confidently correspond to any brief — do NOT force a match or infer `active`; capture `{superseded_by}` when `superseded`).

Then gate — symmetric with the manifest path, but a direct URL/bundle run has no prior dispositions, so it is effectively the "there is work to apply" case:

- **`active` / `no_brief`** → continue normally.
- **`superseded`** → SURFACE it now ("this handoff is superseded by `{superseded_by}`; that newer brief is the current truth") and **HALT before the apply pipeline (steps 2–4) for explicit confirmation** — proceeding would build the surface toward the superseded design, which is intent, not decision autonomy, so autonomous mode does NOT proceed unasked. Halting here (before the grid) also avoids wasting the mapping/grid work. On explicit confirmation — or after the user re-points at `{superseded_by}` — continue. **Never** silently apply a superseded handoff.
- **`ambiguous`** → warn (two briefs claim `active` for this slug; `brief-revision-policy.md` §2.6) and continue — the design source itself is fine.

### SHARED.1a-ii. Concurrent-run check on `{target_slug}` (same key, same moment)

`{target_slug}` was just resolved above, and it is a **canonical collision key** — two sessions working the same surface compute the same slug. Run the same check `design-ingest` step-01 §5a runs, here, for the same reason: the mapping + grid + apply pipeline (steps 02–04) is the expensive part, and it starts immediately after this step.

Follow `design-ingest` step-01 §5a verbatim (do not duplicate the logic — same two probes, same fail-open discipline, same "never hand-write a claim"), with one substitution: the artifact probed is **this run's apply target**, not an ingest manifest. Probe (1) tests whether another session has, *since `{run_started_at}`*, written or staged changes to the implementation files this run is about to touch (`git status --porcelain` on `{impl_files}` plus `git log origin/main --since` on the same paths); probe (2) tests the register for a live `design-implement:{target_slug}` claim held by a different `claimed_by_session_id`.

- **Concurrent session detected** → SURFACE and HALT before step-02, same posture as a `superseded` handoff above: applying now would race another session's in-flight edits to the same surface, and that is intent, not decision autonomy.
- **Anything unreadable or ambiguous** → UNKNOWN, warn in one line, continue. Fails open by construction.

### SHARED.1a-iii. Prior-manifest check on `{target_slug}` (what earlier passes already DECIDED) → `{prior_ingest_manifest}`

**Skip on the manifest path** — an `ingest_manifest` run IS the manifest, and it read its dispositions at intake (`{resume_prior_dispositions}`). On the URL and bundle paths this is the ONLY place the question gets asked, and it is asked with a key already in hand: `{target_slug}`, resolved two sections above. Cost: one glob.

**Why this exists.** The manifest path carries a full provenance apparatus — supersede stamp at intake, `{resume_prior_dispositions}`, an explicit freshness reconciliation. The URL path had none of it: it resolved `{target_slug}` only to match a *brief*, and never asked whether a *manifest* already existed on the same key. It bites hardest on the normal case, which is the tell — a paste from Claude Design's "Send to local coding agent" panel ALWAYS lands on the URL path, and a surface being re-designed is precisely one that has been implemented before, so the run most likely to have prior passes was the run structurally guaranteed not to look for them. The existing safety layer does not cover it either: the supersede gate compares handoff-to-handoff, and the §2b/§4c halts compare handoff-to-production. **Neither compares this run against the prior RUNS' decisions** — which is where "we already thought about that and said no" lives. (Observed 2026-07-25, cash-recovery `/clerk`: a three-pass `design-ingest-clerk-grading-workspace.md` for the same slug was found only by an unrelated `ls`.)

1. **Glob** `{implementation_artifacts}` for `design-ingest-*{target_slug}*.md`. No hit → set `{prior_ingest_manifest} = none` and continue. That is the ordinary first-implementation case and is never a warning.
2. **On a hit, READ its apply ledger BEFORE step-02** — not after the grid is built — and surface all three of:
   - **passes already applied** (`pass_id` / `started_at` / frames, from the identity stamps);
   - **frames still `⊘ deferred`**;
   - **every "Flagged — NOT applied (intent, not treatment)" item.** This is the load-bearing part. Those rows are prior DECISIONS, not unfinished work — items an earlier session examined and deliberately declined, often as an explicit owner call. **This run must not re-open one without saying so.** Silently re-applying one is precisely the harm the apply ledger exists to prevent.
3. **Freshness — disclose, never halt.** Compare the manifest's `ingest.source` and recorded `source_run_date` against the bundle in hand. If the bundle has been REGENERATED since (newer brief, new composition contract), state plainly that the manifest's section inventory is STALE and that this run is **re-ingesting, not resuming**. Symmetric with the manifest path's own freshness warn; soft by construction.
4. **Route this run's ledger write.** When `{prior_ingest_manifest} != none`, step-04 §5 appends this pass to **that manifest** under the multi-writer contract (`docs/manifest-contract.md`: take the marker, stamp the pass identity, append-only, commit by explicit path) instead of minting a parallel `design-implement-grid-*` artifact. Two ledgers for one surface each read as complete — that is the failure mode, not the fix.

**All four are warn/disclose; none is a gate.** The URL path's defect is that it is BLIND, not that it is permissive. Carry this block into the SHARED.2 summary:

```
Prior manifest for {target_slug}: {prior_ingest_manifest}
  passes already applied:    {n} ({pass_ids})
  frames still deferred:     {list | none}
  flagged NOT applied:       {list | none}   ← prior DECISIONS — do not silently re-open
  bundle regenerated since:  {yes → inventory STALE, re-ingesting (not resuming) | no}
  this run's ledger:         appends to the above manifest (multi-writer contract)
```

### SHARED.1b. Bundle → brief conformance gate (the design proposal is not yet a contract)

**The bundle is a PROPOSAL; the brief is the contract. This gate refuses to implement a proposal that silently under-delivers the contract** — the receive-station failure (a strong "station, not dashboard" brief produced a centered hero card with minimal frame coverage, which `design-implement` then faithfully shipped because nothing compared the two). It runs on EVERY path, AFTER SHARED.1a has resolved the brief via `{target_slug}`, and BEFORE step-02/03/04 — a non-conformant proposal is bounced before any mapping or grid work is spent on it.

**Precondition — a brief must exist to gate against.** Use the `{handoff_supersede_status}` resolved in SHARED.1a:

- **`no_brief`** (no brief matched `{target_slug}`) → there is no captured contract, so conformance **cannot be verified** — the SP-API lesson (a surface whose brief was never saved). Do NOT silently treat absence as a pass: record `{bundle_conformance} = UNVERIFIED (no brief)` and surface it in SHARED.2 ("implementing the proposal as-is; no brief to gate against — capture one via `design-handoff` to enable this gate"). Proceed.
- **`active` / `superseded` / `ambiguous`** (a brief matched) → read its machine-readable contract fields — `frames` (the §7 contract-key ids), `shell_role` (`required_shell` / `required_chrome` / `forbidden_chrome`), and `composition` (`brief-revision-policy.md` §2 Block B) — and run the three structural checks below. A brief that PRE-DATES these fields (older brief, field absent) is the same degraded case **per dimension**: mark that dimension `UNVERIFIED (brief lacks <field>)`, disclose it, and gate only the dimensions the brief actually carries.

**The three structural checks (structure, not style):**

1. **Frame coverage** — every id in the brief's `frames` list must appear as a DRAWN frame in `{design_frame_inventory}` (a present module / standalone HTML / manifest scaffold row — `drawn: true`). A brief frame the bundle never drew is a proposal that under-delivered the surface inventory, not a thin-but-acceptable build. (This is the brief-side denominator that complements step-03 §2f's impl-side coverage; here it gates the BUNDLE, there it gates the IMPL.)
2. **Shell / role** — when `shell_role` is present: the bundle's own rendered frame must carry `required_chrome` (verbatim where it draws it) and must NOT render `forbidden_chrome`. A clerk-station bundle that draws the owner global nav — or omits the clerk header — fails here. (The impl-side twin, an ANCESTOR layout injecting `forbidden_chrome` over the surface at runtime, is caught later by step-02 §1a / step-03 §2d against this same `forbidden_chrome`.)
3. **Composition / job-loop** — when `composition` is a NON-default key (a `recommended-alt` such as `scanner-terminal` / `single-item-stream`, i.e. the brief said "this is NOT the page-mode default — it's a station/stream/verify surface"): the bundle must express the JOB LOOP the composition names (e.g. scan → feedback → tally → close), not a single centered hero card in dead space. This check is a **judgment** read (PROBABILISTIC — there is no exact test for "expresses the loop"); checks 1–2 are structural id/string matches (still model-executed, so structured-probabilistic — the fully-deterministic tier is a per-project CI/manifest validator, which does NOT ship via the fork sync).

**On a miss in check 1 or 2 → HALT. Do NOT proceed to step-02.** Print:

```
══════════════════════════════════════════════════════════════════
✗ design-implement halted — the bundle does not conform to its brief.

This is a PROPOSAL that under-delivers the CONTRACT, not a build target.
Implementing it would ship the design's misread (the receive-station failure).

Brief:   {matched brief filename} (target_slug: {target_slug})
{for each frame-coverage miss:}  ✗ frame "{id}" — in brief.frames, NOT drawn in the bundle
{if shell miss:}                 ✗ shell — bundle renders forbidden chrome "{forbidden_chrome}" / omits required "{required_chrome}"
{if composition concern:}        ⚠ composition — brief says "{composition}" (job loop), bundle reads as a hero/dashboard

Next: revise the design so it covers the brief, then re-run. The bundle is
"proposal only; needs revision" — re-run design-synthesize (fork path) or
regenerate in Claude Design against the brief, then re-invoke design-implement.
══════════════════════════════════════════════════════════════════
```

A check-3 composition concern with checks 1–2 passing is a **warn**, not a hard halt (it is a judgment call): surface it loudly in SHARED.2 and carry it to step-03 / the §9 report so design-review can adjudicate the station-vs-dashboard verdict on the live surface — but do not silently bless it. Record the outcome as `{bundle_conformance} = pass | UNVERIFIED(reason) | halted(reasons) | warn(composition)` for the SHARED.2 line.

### SHARED.2. Report ingestion summary

Output a brief summary:

```
Design ingested ({input_kind}):
  source:                 {design_url or design_dir}
  primary file:           {design_file}
  bundle conformance:     {bundle_conformance}   ← SHARED.1b: pass | UNVERIFIED(reason) | warn(composition). A hard HALT (frame/shell miss) exits BEFORE this summary.
{if input_kind == "ingest_manifest":}
  manifest grain:         {manifest_grain}   ← MANIFEST.1a: value-exact | partial | summary (absent field ⇒ summary). Says which half of this path actually ran.
  source re-read:         {none (value-exact) | "REQUIRED + done — N section(s): <list>"}   ← on partial/summary the value read is a required step, not a fallback; a run reporting `summary` with NO re-read has not verified treatment
{if completeness.sections_missing_property_rows and manifest_grain == "value-exact":}
  ⚠ manifest inconsistent: grain claims value-exact but {n} section(s) are listed missing property rows → DOWNGRADED to partial and re-read (design-ingest step-03 §2a should have halted on this)
{end if}
{end if}
{if input_kind == "synthesize_bundle":}
  page_mode:              {bundle_manifest.page_mode}
  screens:                {comma-separated bundle_manifest.screens}
  visual_quality:         {bundle_manifest.visual_review.visual_quality}
  exemplar_alignment:     {bundle_manifest.visual_review.exemplar_alignment}
  exemplars anchored:     {len(bundle_manifest.exemplars.selected)}
  policy sections cited:  {comma-separated bundle_manifest.policy_sections_cited}
{end if}
  components found:       {len(design_components)}
{if input_kind == "claude_design_url":}
  bundle shape:           {bundle_shape}   ← URL.1c: legacy_jsx | dc_html. Misdetection is the silent-no-op failure; a dc_html target reported as legacy_jsx is wrong.
  frames declared:        {len(design_frame_inventory)} — {comma-separated frame names, e.g. "Orders(primary), supply-order-detail-drawer, warehouse-lookup, inbound-batch-lookup, import-run-lookup, accounting-outcome-lookup, catalog-record-drawer, supply-source-lookup"}
  of which §13 lookups:   {count of role == "§13-lookup"} ← step-03 §2f checks each is built in the impl (no brief, so the bundle IS the frame contract)
  linked-records rows:    {len(design_linked_record_rows)} drawn in the detail drawer — {comma-separated labels} (the AUTHORITATIVE lookup denominator; §13-lookup frames must equal-or-exceed this){if any row has no matching §13-lookup frame: " ⚠ {n} UNDER-ENUMERATED → re-traced / flagged for §2f"}
{end if}
  token categories:       {comma-separated unique categories}
  tokens cataloged:       {len(design_tokens)}
  CSS properties:         {len(css_property_catalog)}
  states cataloged:       {sum(len(states) for states in design_states.values())} across {len(design_states)} components
  state breakdown:        {comma-separated unique states observed, e.g., "default(12), hover(4), focus(2), failed(3), empty(1)"}
{if bundle_shape == "dc_html":}
  variants cataloged:     {len(design_variants)} across {count of distinct props} editor prop(s) — {e.g. "trackingOn/trackingOff (trackingEnrichment), feeUnresolved/feeOwner/feeClerk (feeResolution)"}
  default-branch:         {the variant(s) the prop defaults select, e.g. "trackingOff, feeUnresolved"}
{if any(v.hides_capability for v in design_variants):}
  ⚠ capability-hiding variant: {list} — a NON-default branch contains structure the default lacks. Folded into {design_components}/{design_frame_inventory} so step-02b §2 inventories it as handoff capability; NEVER excluded from the denominator. (URL.5a step 4)
{end if}
{if any(v.section_label matches /proposal|unbriefed/i for v in design_variants):}
  ⓘ variant provenance:   {list with section labels} — the design tool flagged these as outside the brief. ANNOTATION carried to the §9 report; NOT a deletion signal. Read as "the brief needs revising," never "the code should lose this." (URL.5a step 5)
{end if}
{end if}
{if any(states == ["default"] for component, states in design_states.items() if component in interactive_components):}
  ⚠ interactive-only-default: {list of interactive components with default-only states} — state-conditional rules may have been missed; re-audit <style> blocks before proceeding
{end if}
{if input_kind == "synthesize_bundle" and len(unresolved_var_refs) > 0:}
  ⚠ unresolved var(--*):  {len(unresolved_var_refs)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(config_class_violations) > 0:}
  ⚠ config-class violations: {len(config_class_violations)} — bundle should not have been emitted
{end if}
{if input_kind == "synthesize_bundle" and len(component_drift) > 0:}
  ⚠ manifest/HTML component drift: {len(component_drift)} — HTML wins per tie-breaker, but flag for audit
{end if}
{if input_kind == "synthesize_bundle" and len(state_drift) > 0:}
  ⚠ manifest/HTML state drift:
    over-claimed (in manifest, missing from HTML):   {len(state_drift.over_claimed)}
    under-reported (in HTML, missing from manifest): {len(state_drift.under_reported)}
    interactive-default-only (likely leak case):     {len(state_drift.interactive_default_only)} — re-audit <style> blocks before step-02
{end if}
```

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-02-map-implementation.md`

---

## SUCCESS METRICS

Both paths must populate the same normalized state:

- `{design_dir}` resolves to a directory containing the design source files.
- `{design_file}` resolves to a primary file inside `{design_dir}` that exists and is readable.
- `{design_components}` is a non-empty map of component name → metadata. Each component entry includes a non-empty `.properties` list of property rows (this is what step-03 iterates over).
- `{design_tokens}` is a non-empty list of tokens with resolved values.
- `{css_property_catalog}` is non-empty and every entry has `component`, `state`, `property`, `resolved_value`, `source`, and `source_file`. Its rows are identical to the rows embedded across `{design_components}[*].properties` — same data, different shape.
- `{design_states}` is populated for every component. Components with only `[default]` are flagged in the summary if they match interactive-component heuristics (rows, buttons, inputs, cells with `data-bind` / `data-action` / role="button") — interactivity without state-conditional rules is the dominant leak mode and warrants a re-audit of `<style>` blocks before step-02.

URL-path-only:
- Design bundle downloaded and extracted successfully.
- **The URL.1b-i early supersede probe RAN before URL.1c/URL.1d** — the target's first ~4KB scanned for a `design-brief-*` token, and a `superseded` handoff HALTED there, before the shape branch, the size preflight, and the whole URL.2–URL.5 catalog. A no-token bundle fell through to §SHARED.1a unchanged (absence of a token is `no_brief`, never a refusal).
- `{bundle_shape}` resolved (URL.1c) and reported in the SHARED.2 summary. A `.dc.html` target was NOT ingested down the `legacy_jsx` branch.
- README read and chat transcripts consulted (if referenced) — from the root `README.md` (`legacy_jsx`) or `_ds/<ds-id>/readme.md` (`dc_html`); its absence was never treated as "no layout constraint."
- All imported files traced and read (`legacy_jsx`), or the self-contained frame document read in full and its frame roots / named sections / `<x-import>` components cataloged (`dc_html`).
- **`{design_variants}` populated on a `dc_html` run (URL.5a)** — the `data-props` schema parsed, EVERY `<sc-if>` branch enumerated (not only the ones the defaults select), and every property row tagged with a `variant` alongside its `state`. Any non-default branch containing structure the default lacks is flagged `hides_capability: true` and its components/frames folded into `{design_components}` / `{design_frame_inventory}` so step-02b §2 inventories it — never excluded from the denominator. `section` labels reading "proposal"/"unbriefed" carried through as annotation, never actioned as deletion.
- The near-empty-catalog guard (URL.6) either passed or HALTED — the run never continued past a zero-modules AND zero-README AND zero-tokens ingest.
- `{design_frame_inventory}` populated (URL.3a) — the primary frame plus every drilled drawer and §13 lookup the target declares (via `<script src>` modules + comments, per-frame banners, lookup→target maps, sibling standalone `<frame>.html`). Each linked standalone frame opened and its components folded into `{design_components}`. This is step-03 §2f's frame-coverage denominator on a no-brief run.
- **`{design_linked_record_rows}` populated AND reconciled (URL.3a source 5)** — the detail drawer's rendered "Linked records" rows enumerated (the AUTHORITATIVE lookup denominator), and every row confirmed to map to a `§13-lookup` frame in `{design_frame_inventory}`. Any row that sources 1–4 failed to declare was re-traced or added as an under-enumerated lookup frame, never silently dropped. The harvested §13-lookup count ≥ the Linked-records row count.
- `{handoff_supersede_status}` resolved on this run (manifest path: from the stamp at intake; URL/bundle paths: independently in §SHARED.1a). A `superseded` URL/bundle run SURFACED and HALTED for explicit confirmation before the apply pipeline — it never silently built the superseded design.
- The §SHARED.1a-ii concurrent-run check RAN on `{target_slug}` before step-02, with a recorded verdict. A detected concurrent session HALTED the run before any mapping/grid spend.
- **The §SHARED.1a-iii prior-manifest check RAN on `{target_slug}` before step-02** and `{prior_ingest_manifest}` is set (`none` is a valid, explicit outcome). On a hit, the manifest's apply ledger was READ and its prior passes, still-deferred frames, and **"Flagged — NOT applied (intent, not treatment)"** items were surfaced before any mapping/grid spend — no prior DECISION was re-opened without saying so, and this run's ledger was routed to that manifest rather than a parallel grid artifact.

Bundle-path-only:
- No curl invocation occurred.
- `manifest.yaml`, `tokens.css`, and at least one `<screen>.html` verified to exist on disk.
- `{bundle_manifest}` fields surfaced in the summary so the user sees what design-synthesize recorded about visual quality, exemplar alignment, and policy sections.

## FAILURE MODES

- **Cross-path contamination.** Calling curl on a bundle path, or trying to parse `manifest.yaml` from a URL bundle. The §INPUT-KIND BRANCH check is a hard branch — never mix.
- Skipping imported files (URL path) ("I'll check those later" — no, read them now).
- Recording token names without resolving their values (e.g., `tokens.radius.lg` without noting it equals `4px`, or `var(--status-warning)` without resolving through `tokens.css`).
- Treating the HTML wrapper as the design spec on the URL path (the components and theme files are the spec; the HTML is just the wrapper).
- Missing asymmetric padding (`padding: '8px 12px'` is two properties, not one).
- Silently ignoring `{unresolved_var_refs}` or `{config_class_violations}` on the bundle path. These indicate a bundle that should not have been emitted; surface them in the summary even though they don't halt step 1.
- **Frame-inventory blindness on the URL path (URL.3a) — the "link to records (lookups)" leak.** Cataloging only the primary file's components and never recording the drilled detail drawer + the §13 lookups it consumes. On a raw-URL run there is no brief and no manifest, so step-03 §2f has no other frame-coverage denominator — skip URL.3a and the lookup drawers (warehouse / inbound-batch / import-run / accounting-outcome / catalog / supply-source for Orders.html) vanish: their inner primitives are shared and match somewhere in the impl, so the component grid greens out while the whole drawer ships unbuilt. The bundle declares these frames itself (the `<script src>` comments literally say "… lookups consumed", the modules carry `/* ==== warehouse-lookup ==== */` banners) — capturing them is reading evidence already in hand, not inventing a contract.
- **Harvesting the lookup set from bundle self-declarations alone — the under-enumeration leak (the "often misses these" failure).** Sources 1–4 (script comments, banners, lookup→target maps) are *declarations* and can be incomplete, imprecise, or describe a different conditional state than the one rendered — so a lookup the comments forgot to list never enters `{design_frame_inventory}`, and §2f cannot flag a frame it never knew existed. The detail drawer's rendered **"Linked records" section** is the authoritative denominator (one row per lookup that must exist — e.g. the live Orders detail drawer draws `Catalog item · Route warehouse · Shipping lane · Supply source · Inbound batch · Import run`, where `Shipping lane` is exactly the kind of row a script-comment harvest misses). Failing to enumerate `{design_linked_record_rows}` and reconcile the harvested §13-lookup frames against it is how a linked-record drawer silently goes unchecked against Claude Design. The row count is the floor; harvest must meet or exceed it.
- **Bundle-SHAPE blindness — the silent-no-op leak (URL.1c).** Ingesting a `.dc.html` bundle down the `legacy_jsx` branch. Nothing errors: `cat README.md` finds nothing, the `<script src>` trace finds nothing (only `support.js` and the design-system bundle), `theme/tokens.jsx` does not exist, and there are no `/* ==== frame ==== */` banners. Every instruction "ran" and the catalog comes back near-empty but *plausible* — which is worse than a crash, because step-03 then grids against a denominator missing whole frames and whole variants. The tell is a run reporting `bundle shape: legacy_jsx` on a target whose name ends `.dc.html`, or a suspiciously tiny component/token count on a visibly rich design. URL.6's guard is the backstop, but detection at URL.1c is the fix.
- **Variant-axis blindness — the capability-deleting leak (URL.5a).** Cataloging only the rendering the editor-prop defaults select. This is the state-axis failure one level up: states are per-component and interaction-conditional; **variants are per-frame and prop-conditional**, and a `default: false` prop can hide an entire alternative rendering — extra columns, a tally strip, a provenance line, whole sections. The real instance (`Inbound Feed.dc.html`, 2026-07-20) defaulted `trackingEnrichment` to `false`, so the default rendering was the 6-column feed WITHOUT the Arrival axis that was already shipped in production; a default-only catalog would have handed step-03 a denominator missing a live column and licensed deleting it. step-02b's regression check is the safety net that catches this — but it can only catch what the ingest gives it, so starving it by cataloging one branch is how the net gets bypassed. Enumerate every `<sc-if>` branch; never let the prop default decide what enters the denominator.
- **Reading an "unbriefed"/"proposal" variant label as permission to drop the capability.** A `section` label like `"Tracking enrichment (proposal, unbriefed)"` is the design tool being *honest* that its addition is not yet in the brief. It is provenance, not a verdict. Treating it as "the design says this isn't wanted" inverts it — the correct reading is "the brief needs revising to catch up with what shipped." Carry it to the §9 report as annotation; never let it justify removing structure the implementation already has.
- **State-axis blindness — the dominant leak mode.** Cataloging only inline `style="…"` and ignoring `<style>` blocks, `data-state` sibling variants, or JSX conditional style branches. The default-state catalog will look complete; the bundle's hover/focus/failed/empty/disabled rules will silently bypass the grid and ship as deltas in production. The 2026-05-28 fork retro (PR #827) was caused by exactly this — failed-row tint, failed-row hover, null-supplier styling, and null-total styling were all state-conditional and absent from the cataloged rows. If you finish ingestion with `{design_states}` showing only `[default]` for an interactive component (row, button, input, action cell), that is the signal that this failure mode is in play — re-audit `<style>` blocks before proceeding to step-02.
