---
name: bmad-fork-status
description: Volatile state of the Mason-BMAD fork. Read by mason-bmad-workflow-expert skill on every invocation.
---

# Mason-BMAD Fork — STATUS

> Update whenever you ship a change to the fork, absorb upstream, or change the shipped/designed status of a feature.

**Last updated:** 2026-06-12 by inbound-flow session.

---

## Now

The compact, always-current state. The skill reads THIS block + the top of `## Changelog` on every invocation — it does not need the archive.

- **Latest wave:** create-design-policy — **Bison product-family policy overlay + `inherits:` mechanism** (`3141456f`). New `shared/bison-product-family-policy.md` lifts the reusable "bulk" of inbound-flow's `design-policy.md` v11 (itself ported from accounting-tools v11) in source-agnostic form — register · status system · money/VAT · relational expand-in-context linking · per-source provenance · positive-assertion floor — so a new Bison tool **inherits** it instead of hand-porting and re-diverging. Three tiers deciphered from inbound-flow's own change_log "Propagation (§9)" tags: universal AI-fingerprint substance stays in `design-standards.md`; product-family substance → the new overlay; project-unique residue (exemplar domain · surface topology / multi-handler · product imagery · concrete tokens/routes) stays in each project's policy, **enumerated in the overlay's §Z** so a new project knows exactly what to author. `create-design-policy` stays project-agnostic: template gains an optional `inherits:` frontmatter field + a family-overlay precedence tier, `workflow.md` gains an inherit-don't-re-port CRITICAL RULE + `{family_overlay}` state var, `step-04 §2b` gains a residue-only authoring path. The overlay lives in `shared/` so it distributes to all sync targets but is **inert for non-Bison projects** (consumed only when a project declares `inherits: bison-product-family-policy`). Pre-push full test suite green. **Sync owed (13/13)** to distribute.
- **Prior wave:** design-implement — **§2f frame-coverage gets a URL-path denominator** (`56d44fc9`); on a raw Claude Design URL run §2f's two contract sources (brief §7, manifest) are both absent, so frame coverage no-opped and §13 lookup drawers vanished — fixed with a three-source precedence + URL-path frame inventory.
- **Fork vs upstream:** see `## Versioning`.
- **Owed / in-flight:** see `## In-Flight Work`. Skill `last_verified_against_fork_commit` = `3141456f`. **Sync owed (13/13)** to distribute the overlay + create-design-policy `inherits:` wiring. Open follow-ups: (a) adopt-the-overlay pass for the two Bison projects — convert inbound-flow + accounting-tools policies to `inherits: bison-product-family-policy` + residue-only (separate, deliberate per-project rewrites; NOT auto-done); (b) carried — confirm design-implement §2f treats a `{consumed_frames}` entry as out-of-scope-for-this-bundle, not `FRAME NOT DRAWN`.

## Changelog

Newest first. **One discrete entry per wave** — `### YYYY-MM-DD — title (commit)` + a bounded paragraph (what · why · scope · delivery). NEVER a single run-on line. Keep ~12 entries here; when it grows past that, move the oldest (in newest-first order) into [`STATUS-archive.md`](./STATUS-archive.md).

### 2026-06-17 — create-design-policy: Bison product-family policy overlay + `inherits:` mechanism (`3141456f`)

inbound-flow session: owner asked to "template the bulk of the design policy for a reusable policy for new projects" and explicitly "decipher what's unique to project and what is template." Mode 5/2 (explain → author). The key finding reframed the task: a blank greenfield template already existed (`create-design-policy/design-policy-template.md`, 16 placeholder sections) and `shared/design-standards.md` already held the universal AI-fingerprint substance — so the *missing* layer was the **product-family** tier, the exact "bulk" the owner keeps re-porting by hand (inbound-flow v11 was itself a verbatim port of accounting-tools v11). The decipher is **three** tiers, not two, and inbound-flow's own change_log already authored the answer: every entry tags `Propagation (§9)` as "shared product-family value → propagate to accounting-tools" vs "inbound-flow-only, do NOT propagate." Read off those tags: **universal** (anti-AI fingerprints, table-first, status mechanism) → `design-standards.md`; **product-family** (corporate register, status system + 4-colour hierarchy, monochrome-primary/Inter/13px, money/VAT + 2dp + derived-ROI proof, relational expand-in-context linking, API + comingled per-source provenance, sorting/chronology, positive-assertion floor) → the new overlay; **project-unique** (multi-handler warehouse-handler topology, product imagery, Amazon/FBA exemplar content, concrete tokens/routes) → stays in each project policy. Built `shared/bison-product-family-policy.md` (§A–§L + §Z) by lifting the propagate-tagged prose in source-agnostic form, with §Z enumerating the tier-3 residue so a new project knows exactly what it must still author. Wired inheritance without breaking the workflow's project-agnostic contract: template `inherits:` frontmatter + family-overlay precedence tier; `workflow.md` inherit-don't-re-port CRITICAL RULE + `{family_overlay}` state var; `step-04 §2b` residue-only authoring path. Overlay lives in `shared/` (distributes everywhere) but is inert unless a project declares `inherits: bison-product-family-policy`. Mode 1 self-review of the overlay: 0 blocking; 1 caught + fixed pre-commit (§I positive-assertion YAML carried stale inbound-flow section numbers §L/§M and pointed money's relational link at §K instead of §J — corrected to the overlay's own A–L scheme). Pushed `myfork/custom` → `3141456f`; pre-push full test suite green. Skill bumped → `3141456f`. **Sync owed (13/13).** Follow-up: a deliberate per-project adopt-the-overlay rewrite for inbound-flow + accounting-tools (convert to `inherits:` + residue-only) — not auto-done, since it's a large destructive rewrite of two live policies.

### 2026-06-12 — design-implement: §2f frame-coverage gets a URL-path denominator (the bundle's own declared lookup frames) (`56d44fc9`)

inbound-flow session: owner reported "design-implement is no longer catching all deltas when I hand over a bundle and run the flow — every time it fails to catch the detail pages that are there in the 'link to records (lookups)'", with a live Claude Design URL (`open_file=Orders.html`). Diagnosis (Mode 3), grounded by fetching the actual bundle: `Orders.html` consumes five §13 expand-in-context lookup frames inside the Supply Order Detail Drawer — `warehouse-lookup` / `inbound-batch-lookup` / `import-run-lookup` / `accounting-outcome-lookup` (supply-order/lookups.jsx banners) plus `catalog` + `supply-source` (catalog-record/) — declared in the bundle's own HTML comments ("… lookups consumed"), jsx per-frame banners, and the `app.jsx` lookup→target map. Root class `contract-dimension-gap` (URL-path twin of the §2f axis): §2f's two contract sources are the **brief §7** and the **synthesize-bundle manifest** — and a raw Claude Design URL run has NEITHER. So §2f had no denominator, emitted zero Frame-coverage rows, and the lookup drawers fell out silently: their inner primitives (Pill, Money, RecordLink) are shared and match somewhere in the impl, so the component sweep greened out while the whole drawer shipped unbuilt or inferred-thin. step-04 §9's Frame-coverage disclosure was gated on "whenever the brief enumerated a §7 Surface Inventory" — no brief → section legitimately skipped → false-green. Add-not-cede (the bundle declares its frames; reading them is evidence already in hand, same posture as page-shell §2d): step-01 **URL.3a** captures `{design_frame_inventory}` (primary + drilled drawer + each §13 lookup, from traced modules/comments + per-frame banners + lookup→target maps + sibling standalone `<frame>.html`, opening any linked standalone frame into `{design_components}`); step-03 §2f resolves the contract by **three-source precedence** — brief §7 → bundle frame inventory (URL) → manifest (bundle) → needs-human-confirm — with the URL-path frames `drawn:true` so an impl lacking the drawer is `FRAME MISSING in impl` (Tier-1); step-04 §9 + SUCCESS/FAILURE + checklist generalize the disclosure gate beyond brief §7 ("no brief" is not "no contract"); workflow.md gains the state var + a Critical Rule. Mode 1 self-review: 0 blocking. Pushed `myfork/custom` → `56d44fc9`; synced 13/13 (also distributing the previously-owed `e72c1cb7` gate). Skill bumped → `56d44fc9`. Follow-up (carried): `{consumed_frames}` disposition in §2f.

### 2026-06-12 — design-implement: gate the §7 frame-coverage axis + deliver the stranded design-lane sync (`e72c1cb7`, PR #2071)

inbound-flow session: owner pasted a prior `design-implement` run on the `/orders` bundle that declared "Deltas applied: 0 — green," then pushed back with "brief's §7 Surface Inventory lists 9 frames, each a required deliverable." Per-frame cross-check found 5 of 9 frames built, 4 (inbound-batch / import / shipping-lane / comms-case lookup drawers) designed-in-the-bundle but unbuilt in impl. Diagnosis (Mode 3) had **two layers**. Layer 1 — root cause of *this* run — `worktree-sync-drift`: the §2f Frame-coverage axis (and §2d/§2e, and the §7 render/scoping waves) were synced into inbound-flow's main working tree but **never committed**; `EnterWorktree` branches from HEAD, so the worktreed run loaded the pre-§2f copy (`git show HEAD:…/step-03-build-grid.md | grep -c Frame-coverage` → 0) and was structurally blind to a whole unbuilt frame. Fix: committed the stranded design-lane sync to `main` (PR #2071, doc-only admin-merge) — §2f now in committed HEAD, worktree runs see it. Layer 2 — latent even post-sync — `silent-partial-implementation`: §2f's emission was never *enforced* (no checklist row, no mandatory §9 report section), so an agent could still sweep only the found frames and green out. Fix mirrors the existing content-lane / capabilities-removed gates: checklist gains the §2f row; step-04 §9 gains a mandatory **"Frame coverage (brief §7)"** section enumerating every promised frame as built / missing-in-impl (Tier-1) / not-drawn (routed); SUCCESS METRICS + FAILURE MODES codify "the §7 list, not the found-frame set, is the denominator for a green claim." Mode 1 self-review of the gate: 0 blocking (legitimate *add*, not a faked policy check — §2f is verifiable from evidence the workflow already holds). Pushed `myfork/custom` → `e72c1cb7`. Skill bumped → `e72c1cb7`. **`sync bmad` owed** to distribute the gate to all 13 targets. Follow-up (carried from `22406ca7`): `{consumed_frames}` disposition in §2f.

### 2026-06-12 — design-synthesize + design-handoff: draw §7 lookup-drawer frames; redirect lookup-drawer handoffs (`22406ca7`)

inbound-flow session: owner reported the small §13 "link to record" lookup drawers (a thin catalog record drawer subtitled "Catalog record for ASIN"; a supply-source lookup drawer that shipped as a hand-rolled key/value stub violating §15 — bare `€245.71` no GBP/VAT basis, inert Sell ASIN, inert gate) "getting completely missed by Claude Design," AND "whenever I call for a handoff the handoff purpose gets rejected." Diagnosis (Mode 3): the `3a88eee3` wave shipped the §7 enumeration (handoff) + the §2f verification (design-implement) but left the *render* half and the *redirect* half as explicit follow-ups — and they were never done. Root class `silent-partial-implementation`: the §7 Surface Inventory contract was complete, but **design-synthesize never consumed it** — step-01 §7 derived `{screens}` only from frontmatter `route`/`routes`, never the brief BODY's §7 table, so the enumerated lookup-drawer frames never became screens, never rendered, and design-implement §2f then inferred them thin. Symptom 2 was partly correct-by-design (a lookup drawer is owned by the relation, never its own handoff — destination-vs-relationship) but the rejection routed nowhere. Fix, two halves: **(A) render** — design-synthesize step-01 §7a populates `{screens}` from the §7 Surface Inventory (frame-name-keyed verbatim, the contract key that travels brief→`<frame>.html`→§2f), with Gate 1f halting if any §7 frame would go undrawn (silent-partial guard mirroring §2f at the render step) + `{consumed_frames}` accounting for "consume from sibling brief" rows + a pre-§7-brief announced blind-spot; step-04 composes a `drawer-over-{parent}` frame as the §13 drawer open over its parent (§15 basis-complete, §2a richness floor); workflow.md state vars document it. **(B) redirect** — design-handoff step-01 §2a detects a §13 lookup-drawer target and REDIRECTS it (not a bounce) to the matching next command — re-synthesize the parent brief (now §7-aware), material-revise the parent, or redesign the owning surface — preserving the multiple-active-brief invariant; autonomous mode does not override (intent violation). The infra was already multi-screen (step-04/05/07 loop `{screens}`), so the render fix was one missing wire, not new machinery. Mode 1 self-review: 0 blocking. Pushed `myfork/custom`; synced 13/13. Skill bumped → `22406ca7`. Follow-up: verify design-implement §2f treats a `{consumed_frames}` row as out-of-scope-for-this-bundle, not `FRAME NOT DRAWN`.

### 2026-06-12 — design-handoff: spawned drawers scoped in as required deliverable frames (`3a88eee3`)

User reported poor detail-page drawers (financial data presented sloppily, thin warehouse lookup, an `ROI`-bearing catalog drawer subtitled "Catalog record for ASIN") — "especially when the handoff specified a page and not a specific detail page." Root class `contract-dimension-gap`, 5th instance (after state / multiplicity / content-lane / page-shell): handoff enumerated the scoped PAGE but never the surfaces it spawns at runtime — the drilled **detail drawer** and the §13 expand-in-context **lookup drawers**. The pipeline is non-interpretive (Claude Design draws only §7's frames; design-implement matches only bundle frames), so an un-enumerated drawer is never drawn and then INFERRED downstream → thin, unformalised (bare `€60` with no GBP/VAT basis — a `docs/design-policy.md` §15 violation that ships because the drawer never entered the design pipeline as a frame; lookup drawers stubbed at code/type/status). The taxonomy that settled the scoping: **destination vs relationship** — lookup drawers are owned by the *relation* (§2a, never a separate handoff), the drilled drawer is an inline spawned-surface frame by default, fresh handoff only on graduation to a deep `/[id]` route. Verifiable from evidence the workflows already hold, so the fix adds real rows, not a cede: workflow.md Deliverable-Completeness Principle ("if you want it built well, it must be drawn") + `{spawned_surfaces}`; step-01 §5f derives the frames from page_mode + composition + linked_records (richness floor, depth-1); brief §7 leads with a frame-name-keyed Surface Inventory table; §2a richness floor; step-03 substitution + checklist guard; design-implement §2f Frame-coverage rows (a brief-promised frame absent from the bundle = `FRAME NOT DRAWN` → routed, not inferred). No inbound-flow policy change — §15/§13 already mandate the content quality; the gap was the drawer never being drawn. Mode 1: 0 blocking. Pushed `myfork/custom`; synced 13/13. Skill bumped → `3a88eee3`. Follow-ups: design-synthesize (terminal-native render path) should honor §7 frames; design-implement step-01-ingest could capture the brief §7 frame list explicitly rather than §2f re-reading it.

### 2026-06-12 — design-implement: the bundle is a generated proposal, the spec is the policy (`9a0a1089`)

User pulled a second real sheet (`Accounting Import v2`) and asked "is the README gened by Claude Design?" — yes. The bundle AND its README are generated *from* `docs/design-policy.md` and can violate it (that bundle shipped a banned colored-glow `@keyframes ai-pulse` + no `prefers-reduced-motion`). So the bundle is authoritative for **treatment** only, never policy conformance. **(1)** step-01 re-points `{design_layout_constraints}` to read the layout rule from `docs/design-policy.md` FIRST (authoritative); README + wrapper demoted to corroboration with an `authoritative` flag + a no-policy fallback. **(2)** new step-03 §2e + step-04 §9 + a workflow.md Critical Rule explicitly CEDE policy-conformance (prohibitions/tone/motion/iconography) + behavior wiring to design-review / design-review-pr / verify — not a faked grep. Page-shell stays a check (statically verifiable against policy + impl); the rest is ceded. Mode 1: 0 blocking, 1 nit fixed. Pushed `myfork/custom`; synced 13/13. Skill bumped → `9a0a1089`.

### 2026-06-11 — design-implement gains the page-shell axis (`1febc8ce`)

The comparison grid is component × state × property, but the page CONTAINER's width/centering is owned by the wrapper + ancestor layout (no component) and the bundle renders full-bleed standalone — so a nested `max-width:1280px` cap inside the layout's `max-w-[1440px]` rendered `/orders` narrow + centered (PR #2017) while every component CSS matched (grid all-green). Root class `contract-dimension-gap` — 4th instance after state / multiplicity / content-lane. Fix: `{design_layout_constraints}` + `{impl_page_shell}` state vars; step-01 capture (both ingest paths); step-02 §1a resolves the EFFECTIVE width after every nested cap; step-03 §2d emits one always-present Page-shell row (width/centering mismatch = Tier-1). Pushed `myfork/custom`; synced 13/13.

> Earlier waves (2026-06-10 and before) are preserved verbatim — as the original log — in [`STATUS-archive.md`](./STATUS-archive.md).

---

## Versioning

- **Upstream BMAD tracked:** v6.8.0 (`origin/main`)
- **Fork base snapshot:** v6.7.x branch point
- **Commits behind upstream:** 3 (as of 2026-06-12)
- **Commits ahead of upstream:** 258
- **Last upstream sync:** `upgrade-bmad.sh` 2026-06-01 (clean)
- **Last fork commit:** see `## Changelog` top entry (self-maintaining)

## Shipped Features

Foundational capabilities, shipped. The wave-by-wave feature history (what landed each session) lives in `## Changelog` + [`STATUS-archive.md`](./STATUS-archive.md); this is the durable capability set, not the running log.

**Provenance & safety**

- [x] Brief provenance contract — 11-field frontmatter + 6 intake checks (`401e2d57`)
- [x] design-handoff predecessor + supersession logic (brief-revision-policy)
- [x] Quick-dev grounding gate + autonomy scoping (decision vs intent) (`1979c48f`)
- [x] `project_phase` config — greenfield | brownfield | mixed (`0dd2e1ca`)

**Sync & infra**

- [x] `sync-bmad-workflows.sh` + `--worktree` single-worktree flag (`647c14e7`)
- [x] worktree-portability rule (every producer resolves `{project-root}`)
- [x] `bmad-deploy` stale-checkout guard + source-vs-deployed drift gate

**Design pipeline**

- [x] design-handoff / design-artifact-loop / design-synthesize / design-tuning — intake checks + two-lane evidence model
- [x] design-review + design-review-pr — live + PR-time policy §13 / archetype enforcement
- [x] design-implement — comparison-grid axes: state · multiplicity · content-lane · page-shell · policy-as-spec
- [x] design-elevation (scope-expansion) + maintenance-triage (shape gate)

**Analytics presentation family**

- [x] analytics-surface-architect (shape) · analytics-rigor (depth) · decision-analysis (capital decisions)
- [x] archetype taxonomy incl. `waterfall`; design-handoff §5e surface hierarchy

**Verify lane (detect + route)**

- [x] data-quality-audit · scrape-coverage-audit · webhook-contract-check (+ charter) · relational-coherence-audit

**Agents**

- [x] custom-agents lane + create-agent: Vera (data-integrity) · Wren (relational-coherence)

## Designed but Not Yet Shipped

- [ ] **Quick-dev split into `spec-dev` and `direct-dev` entry points** — current `quick-dev` carries both modes behind one entry; split would make the safety boundary explicit at the entry point
- [ ] **`tech-spec` workflow** — lightweight artifact between `maintenance-triage` and dev, for brownfield work that needs more than direct instructions but less than a full PRD
- [ ] **Full brownfield maintenance pipeline** — `maintenance-triage → tech-spec → spec-dev` (1 of 3 surfaces shipped)

## In-Flight Work

- `worktree-feat+brief-revision-policy` in **accounting-tools** (not the fork) — design-tuning step revisions + new directories under `_bmad/bmm/workflows/design/`. These will need to be lifted back into the fork's `custom/workflows/` once stable. **Important:** edits in the project will be overwritten on next sync; the canonical edit point is `~/bmad-method-v6/custom/workflows/`.

## Known Drift Across the 13 Projects

Audit pending. Run `~/bmad-method-v6/sync-bmad-workflows.sh --check` to populate. Active sync targets:

- comms_dashboard, brand-source-finder, inbound-flow, accounting-tools, bison-ops, image-pipeline, bison-website, amazon-removal-assistant, taylor_work, accounting_api_backend, otp_manager, wera-catalog, amazon-lead-generator

## Upstream Items Under Evaluation

25 upstream commits behind. Per-commit triage not done yet. Reconciliation difficulty likely high in any area the fork has restructured (design pipeline, quick-dev, sync layer). Low-risk absorbs likely in areas the fork has not touched (core agents, party-mode, brainstorming, retro).

- v6.8.0 release → undecided → triage pending

## Recent Decisions Worth Remembering

- 2026-05-28: Shipped `project_phase` config and `maintenance-triage` workflow together. `project_phase` is the gating mechanism for routing brownfield work through `maintenance-triage` instead of greenfield-biased entry points.
- 2026-05-27: Shipped `sync --worktree` flag to resolve worktree-portability P0. Worktree creation no longer requires a full multi-project sync.
- 2026-05-?: Brief provenance contract finalized (11 fields + 6 intake checks). Hand-edits to material_revision briefs are now forbidden by intake check 5; clarifications remain allowed.
- 2026-05-?: Quick-dev grounding gate redefined autonomous_mode — decision autonomy (file choice, pattern selection) allowed; intent autonomy (inferring what user meant) forbidden.
