---
name: bmad-fork-status
description: Volatile state of the Mason-BMAD fork. Read by mason-bmad-workflow-expert skill on every invocation.
---

# Mason-BMAD Fork — STATUS

> Update whenever you ship a change to the fork, absorb upstream, or change the shipped/designed status of a feature.

**Last updated:** 2026-05-29 by Mason (new workflow: onboard-design-system — Claude Design design-system onboarding front door)

---

## Versioning

- **Upstream BMAD version tracked:** v6.8.0
- **Fork base snapshot:** v6.7.x branch point (commit predating origin/main HEAD by 25)
- **Commits behind origin/main:** 25
- **Commits ahead of origin/main:** 100
- **Last upstream sync attempted:** never since current `custom` branch was established — drift has been growing
- **Last upstream commit:** 3bcd6c3c `chore(release): v6.8.0 [skip ci]` (2026-05-25)
- **Last fork commit:** 0dd2e1ca `feat(bmad): project_phase config + maintenance-triage workflow` (2026-05-28)

## Shipped Features

- [x] **Brief provenance contract** — 11-field frontmatter, 6 intake checks (commit `401e2d57`)
- [x] **design-handoff predecessor + supersession logic** — part of brief-revision-policy
- [x] **design-artifact-loop, design-synthesize, design-tuning intake checks** — wired to provenance contract
- [x] **design-synthesize synthesis honesty rules + under_grounded label** (commit `6e4cee98`)
- [x] **design-synthesize brief-faithfulness half (g/h/i)** — pre-visual gates for internal consistency, deliverable coverage, brief-question coverage; T4 strengthened to four sub-tests (T4a-T4d) (commit pending today, 2026-05-28). Driven by `amazon-transactions` bundle PR #800 in accounting-tools shipping as `pass / excellent / aligned` while containing 4 contradictions, missing 2 of 4 brief §7 deliverables, and abstractly answering 3 of 7 brief §6 questions.
- [x] **Quick-dev grounding gate (Mode B)** (commit `1979c48f`)
- [x] **Quick-dev autonomy scoping (decision vs intent)** (commit `1979c48f`)
- [x] **sync-bmad-workflows.sh** — base sync script
- [x] **sync `--worktree PATH` flag** — single-worktree minimal sync (commit `647c14e7`)
- [x] **project_phase config flag** — `greenfield | brownfield | mixed` (commit `0dd2e1ca`, shipped today)
- [x] **maintenance-triage workflow** — `custom/workflows/implement/maintenance-triage/` (commit `0dd2e1ca`, shipped today)
- [x] **design-review degraded-mode switch** — `measurement_method: chrome-live | source-derived | screenshot-only` + mandatory `measurement_caveat` (2026-05-28). Closes the gap where step-01 §3 assumed Chrome MCP always available and FAILURE MODES listed screenshot-only as failure with no sanctioned alternative.
- [x] **Source-vs-deployed drift gate** — design-review step-01 §1.5 pre-flight checks `git status` / recent local commits / local-vs-origin/main delta before reading the page; surfaces source_state_caveat in autonomous mode (2026-05-28).
- [x] **Refine-screen Collapse allowance** — design-handoff workflow.md "Refine-screen rule" now allows one mechanical Vx+Vy collapse to free a slot for a design-requiring hard failure when strict top-3 severity ordering fills slots with token/class swaps. Capped at one collapse per brief; promoted violation must be hard failure (2026-05-28).
- [x] **Brief frontmatter Block A + Block B contract** — `brief-revision-policy.md` §2 split into Block A (Provenance, 11 fields) + Block B (Content, 3-6 fields mode-dependent). Block B fields: `mode`, `page_mode`, `route` always; `screen_review_ref`, `targeted_changes`, `unchanged_regions`, `deferred_violations` for refine-screen; `collapse_note` conditional. Producer (design-handoff step-03) updated; consumers reference by policy name so no inline updates needed. Check 1 expanded to validate both blocks (2026-05-28).
- [x] **shared/worktree-portability.md** — codified rule: every producer resolves `{project-root}` via `git rev-parse --show-toplevel` at write-time, refuses writes outside the active worktree, halts with named diagnostic. Applied in design-review step-01 §7 and design-handoff step-03 §1. Closes silent main-checkout-write bug (2026-05-28).
- [x] **shared/delivery-to-main.md + design-handoff step-04-deliver.md** — producer-side delivery sequence (commit → push → PR → merge → verify → fast-forward → exit-worktree). Closes the "file written to disk but not on origin/main" gap that caused Claude Design to fail-find a brief on 2026-05-28. Skippable via `--no-deliver` or `delivery.design-handoff: skip` config. Pattern is reusable for design-synthesize / maintenance-triage / artifact-loop — they should adopt step-N-deliver next (2026-05-28).
- [x] **Canonical implementation-artifacts path consolidation** — workflow text was referencing legacy `_bmad/bmm/implementation-artifacts/` literal in 11 places across 6 design workflows; config resolves `{implementation_artifacts}` to `_bmad-output/implementation-artifacts/`. Diagnosed in accounting-tools (27 orphaned artifacts), fixed at fork-level (commit `ae4bb805`, 2026-05-28). Audit of all 13 projects: only accounting-tools materially affected. Re-sync needed for the other 12 to refresh workflow text (no artifact moves needed there).
- [x] **design-implement state-axis (component × state × property grid)** — `design-implement/workflow.md`, `steps/step-01-ingest-design.md`, `steps/step-03-build-grid.md` + `design-synthesize/steps/step-07-emit-manifest.md`. The grid contract was Component × Property; the design's intent is Component × **State** × Property. Step-01 now catalogs state-conditional rules from three sources (inline `style=`, `<style>` blocks, `data-state` sibling variants); step-03's grid has a State column with per-state property sweeps and Tier-1 surfacing of state-coverage gaps; manifest schema gains mandatory `components_emitted[*].states_emitted`. Diagnosed in accounting-tools PR #827 retro (failed-row tint at 0.06 vs 0.10, failed-row hover regression, null-supplier rendered bold, null-total rendered bold — all four were state-conditional rules with no grid row). Driven by mason-bmad-workflow-expert Mode 3 diagnosis 2026-05-28; proposed new root cause class `contract-dimension-gap`. Re-sync needed for all 13 projects to pick up the new step text. (2026-05-28)
- [x] **onboard-design-system workflow** — `custom/workflows/design/onboard-design-system/` (workflow.md + 6 steps + claude-design-intake-template.md). The "set up a new design system" front door: orchestrates `create-design-policy` (strategic) → brand-identity population (tactical) → a code-shaped token bundle (`tokens.css` + `sample.html`), runs `delivery-to-main` so the bundle is on `origin/main`, then emits a `claude-design-intake.md` card mapped 1:1 to the claude.ai/design "Set up your design system" form fields. Motivated by the form being code+GitHub-first (markdown underfeeds it) and ingesting from `origin/main` (the 2026-05-28 fail-find gap). Explicitly scopes OUT the brief-revision-policy 6 intake checks (produces design-system artifacts, not briefs) via a PROVENANCE SCOPE section. Authored 2026-05-29; synced to taylor_work for first run; broad re-sync to other 12 projects pending. Open nit: step-06 commit type `feat(...)` vs delivery-to-main §3 bundle-type `design(...)`. (2026-05-29) **Revised same day:** added a `mode` axis — **`led` (default)** = Claude makes all decision-autonomy calls (palette/type/tokens) from an evidence-grounded internal brainstorm, commits to one direction, and surfaces a single end-of-run review (chosen direction + rationale + runners-up + confidence) for veto; `--collaborative` restores propose-and-confirm. Intent honesty rule keeps `led` inside the autonomy boundary (ground-or-flag, never fabricate positioning silently). Per-step behavior marked `[led]`/`[collaborative]`. (2026-05-29)
- [?] **Worktree creation hook → auto-sync** — partial: `--worktree` flag exists, automatic hook wiring needs confirmation per-project
- [?] **.gitignore entries for synced directories** — enforced per-project; audit across all 13 projects pending

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
