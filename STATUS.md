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

- **Latest wave:** design-handoff — **spawned drawers scoped in as required deliverable frames** (§7 Surface Inventory). 5th `contract-dimension-gap` instance: handoff enumerated the scoped PAGE but never the detail/lookup drawers it spawns, so the non-interpretive pipeline never drew them and design-implement inferred them → thin, unformalised drawers (bare €60, code/type/status stubs). Fix adds real rows (verifiable): workflow Deliverable-Completeness Principle + `{spawned_surfaces}`; step-01 §5f derivation; brief §7 Surface Inventory (frame-name keyed) + §2a richness floor; design-implement §2f Frame-coverage. Fork `3a88eee3`; synced 13/13.
- **Fork vs upstream:** see `## Versioning`.
- **Owed / in-flight:** see `## In-Flight Work`. Skill `last_verified_against_fork_commit` = `3a88eee3`.

## Changelog

Newest first. **One discrete entry per wave** — `### YYYY-MM-DD — title (commit)` + a bounded paragraph (what · why · scope · delivery). NEVER a single run-on line. Keep ~12 entries here; when it grows past that, move the oldest (in newest-first order) into [`STATUS-archive.md`](./STATUS-archive.md).

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
- **Commits ahead of upstream:** 251
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
