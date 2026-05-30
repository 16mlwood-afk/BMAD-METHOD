---
name: bmad-fork-status
description: Volatile state of the Mason-BMAD fork. Read by mason-bmad-workflow-expert skill on every invocation.
---

# Mason-BMAD Fork — STATUS

> Update whenever you ship a change to the fork, absorb upstream, or change the shipped/designed status of a feature.

**Last updated:** 2026-05-30 by Claude session (design-tuning two-lane evidence model — artifact-source treatment checks vs screenshot composition; driven by accounting-tools Amazon iter-4 V18 sub-visible-ring miss)

---

## Versioning

- **Upstream BMAD version tracked:** v6.8.0
- **Fork base snapshot:** v6.7.x branch point (commit predating origin/main HEAD by 25)
- **Commits behind origin/main:** 25
- **Commits ahead of origin/main:** 120
- **Last upstream sync attempted:** never since current `custom` branch was established — drift has been growing
- **Last upstream commit:** 3bcd6c3c `chore(release): v6.8.0 [skip ci]` (2026-05-25)
- **Last fork commit:** 0fb21cb8 `feat(modify-design-policy): symmetric six-category coverage guard in step-02` (2026-05-29)

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
- [x] **design-tuning two-lane evidence model (treatment-source vs composition-screenshot)** — step-01 §1c ingests the Claude Design artifact bundle (reuses design-implement URL PATH: `curl` → tar → JSX/`tokens.css`), §1d resolves the canonical codebase component as the §13 reference; step-02 §0a routes checks into a treatment lane (ring/opacity, radius, spacing, color, dot — settled by exact `{artifact_css_catalog}` vs `{canonical_components}`, new `source-exact` evidence class) vs a composition lane (screenshot-authoritative); §2a cross-surface compare. `{treatment_evidence_mode}: bundle-exact | screenshot-degraded` mirrors the design-review degraded switch and blocks APPROVAL on `treatment_unverified` (step-02 §7 / step-03 §1+§5a). workflow.md SOURCE-OF-TRUTH PRECEDENCE gains the self-contained-bundle carve-out (source==render, no override surface). (2026-05-30). Driven by accounting-tools Amazon transactions design-tuning iter-4: V18 status pill scored "resolved" off a PNG when a `ring-rose-500/20` inset ring is sub-visible; user had to step in.
- [x] **Source-vs-deployed drift gate** — design-review step-01 §1.5 pre-flight checks `git status` / recent local commits / local-vs-origin/main delta before reading the page; surfaces source_state_caveat in autonomous mode (2026-05-28).
- [x] **Refine-screen Collapse allowance** — design-handoff workflow.md "Refine-screen rule" now allows one mechanical Vx+Vy collapse to free a slot for a design-requiring hard failure when strict top-3 severity ordering fills slots with token/class swaps. Capped at one collapse per brief; promoted violation must be hard failure (2026-05-28).
- [x] **Brief frontmatter Block A + Block B contract** — `brief-revision-policy.md` §2 split into Block A (Provenance, 11 fields) + Block B (Content, 3-6 fields mode-dependent). Block B fields: `mode`, `page_mode`, `route` always; `screen_review_ref`, `targeted_changes`, `unchanged_regions`, `deferred_violations` for refine-screen; `collapse_note` conditional. Producer (design-handoff step-03) updated; consumers reference by policy name so no inline updates needed. Check 1 expanded to validate both blocks (2026-05-28).
- [x] **shared/worktree-portability.md** — codified rule: every producer resolves `{project-root}` via `git rev-parse --show-toplevel` at write-time, refuses writes outside the active worktree, halts with named diagnostic. Applied in design-review step-01 §7 and design-handoff step-03 §1. Closes silent main-checkout-write bug (2026-05-28).
- [x] **shared/delivery-to-main.md + design-handoff step-04-deliver.md** — producer-side delivery sequence (commit → push → PR → merge → verify → fast-forward → exit-worktree). Closes the "file written to disk but not on origin/main" gap that caused Claude Design to fail-find a brief on 2026-05-28. Skippable via `--no-deliver` or `delivery.design-handoff: skip` config. Pattern is reusable for design-synthesize / maintenance-triage / artifact-loop — they should adopt step-N-deliver next (2026-05-28).
- [x] **Canonical implementation-artifacts path consolidation** — workflow text was referencing legacy `_bmad/bmm/implementation-artifacts/` literal in 11 places across 6 design workflows; config resolves `{implementation_artifacts}` to `_bmad-output/implementation-artifacts/`. Diagnosed in accounting-tools (27 orphaned artifacts), fixed at fork-level (commit `ae4bb805`, 2026-05-28). Audit of all 13 projects: only accounting-tools materially affected. Re-sync needed for the other 12 to refresh workflow text (no artifact moves needed there).
- [x] **design-implement state-axis (component × state × property grid)** — `design-implement/workflow.md`, `steps/step-01-ingest-design.md`, `steps/step-03-build-grid.md` + `design-synthesize/steps/step-07-emit-manifest.md`. The grid contract was Component × Property; the design's intent is Component × **State** × Property. Step-01 now catalogs state-conditional rules from three sources (inline `style=`, `<style>` blocks, `data-state` sibling variants); step-03's grid has a State column with per-state property sweeps and Tier-1 surfacing of state-coverage gaps; manifest schema gains mandatory `components_emitted[*].states_emitted`. Diagnosed in accounting-tools PR #827 retro (failed-row tint at 0.06 vs 0.10, failed-row hover regression, null-supplier rendered bold, null-total rendered bold — all four were state-conditional rules with no grid row). Driven by mason-bmad-workflow-expert Mode 3 diagnosis 2026-05-28; proposed new root cause class `contract-dimension-gap`. Re-sync needed for all 13 projects to pick up the new step text. (2026-05-28)
- [x] **onboard-design-system workflow** — `custom/workflows/design/onboard-design-system/` (workflow.md + 6 steps + claude-design-intake-template.md). The "set up a new design system" front door: orchestrates `create-design-policy` (strategic) → brand-identity population (tactical) → a code-shaped token bundle (`tokens.css` + `sample.html`), runs `delivery-to-main` so the bundle is on `origin/main`, then emits a `claude-design-intake.md` card mapped 1:1 to the claude.ai/design "Set up your design system" form fields. Motivated by the form being code+GitHub-first (markdown underfeeds it) and ingesting from `origin/main` (the 2026-05-28 fail-find gap). Explicitly scopes OUT the brief-revision-policy 6 intake checks (produces design-system artifacts, not briefs) via a PROVENANCE SCOPE section. Authored 2026-05-29; synced to taylor_work for first run; broad re-sync to other 12 projects pending. Open nit: step-06 commit type `feat(...)` vs delivery-to-main §3 bundle-type `design(...)`. (2026-05-29) **Revised same day:** added a `mode` axis — **`led` (default)** = Claude makes all decision-autonomy calls (palette/type/tokens) from an evidence-grounded internal brainstorm, commits to one direction, and surfaces a single end-of-run review (chosen direction + rationale + runners-up + confidence) for veto; `--collaborative` restores propose-and-confirm. Intent honesty rule keeps `led` inside the autonomy boundary (ground-or-flag, never fabricate positioning silently). Per-step behavior marked `[led]`/`[collaborative]`. (2026-05-29)
- [x] **Workflow humanization wave — verify + implement + design-policy families** — three commits (`cb0e0567`, `b19d1b7e`, `f03aef39`, 2026-05-28..29). Rewrote role / Key Insight / Critical Rules prose for the 9 fork-owned workflows that still read like upstream BMAD spec-language: `wire-check`, `trace-flow`, `quick-dev`, `quick-spec`, `create-design-policy`, `modify-design-policy`, `apply-design-policy-change`, `design-review-pr`, `design-agent`. House style now consistent across all 21 fork-owned workflows. Every safety/gate/state-variable/step-file pointer preserved byte-identical — pure prose changes. Skill `mason-bmad-workflow-expert` Mode 1 self-review run on each batch before push. Sync to 13 projects: see distribution step pending below.
- [x] **mason-bmad-workflow-expert skill 1.3 — Closing Out a Wave (Delivery Audit)** — new section inserted between Durable Principles and "What This Skill Does NOT Do". Codifies the post-wave audit (distribution + record-keeping + follow-up triage) that fires after Mode 1/2/4 work. Companion global feedback memory `feedback-delivery-audit-before-done.md` created. Driven by 2026-05-29 retro: after the humanization wave, the skill declared "done" without surfacing the sync / STATUS update / onboard-design-system triage — Mason had to ask "next steps?". The new section + memory close that gap. `last_verified_against_fork_commit` bumped to `f03aef39`.
- [x] **design-implement implementation-multiplicity + numeric-colour axes** — `custom/workflows/implement/design-implement/` step-02/03/04 + workflow.md (2026-05-30). Adds a 4th comparison axis beyond component × state × property: a design primitive can map to MANY implementations, so step-02 §3 enumerates every render site (`{impl_render_sites}`) and step-03 §2a cross-checks them — sibling-implementation divergence is Tier-1 *even if one copy matches the design*; step-04 mandates consolidation (not per-copy patching) as the fix. Secondary: step-02 §2 resolves every colour incl. default Tailwind palette to hex (`{impl_colors}`), step-03 §2b makes colour comparison numeric (ΔE) and bans "both green → ✓". Driven by accounting-tools invoices status pill shipping forked 3 ways (table emerald `#ecfdf5` vs drawer/detail sage `hsl(150 26%/40% …)`) — each per-page design-implement audit passed because the workflow mapped the primitive to one same-page file and never compared the copies. Same severity-tier treatment the state axis got after PR #827. Synced to accounting-tools; broad re-sync to other 12 projects pending.
- [x] **bmad-deploy.sh Cloudflare auth pre-flight (exit 18)** — `custom/scripts/bmad-deploy.sh` §4b + `deployment-to-prod.md` §6 (commit `aa23aa1c`, 2026-05-30). When `deploy.deploy_command` contains `wrangler`, runs `wrangler whoami` before the build and fails fast with a new named exit code **18** + actionable re-mint message if `CLOUDFLARE_API_TOKEN` is invalid/expired/revoked (API 9109/10000). Non-wrangler deploy targets skip it. Driven by accounting-tools: a token expired mid-session, so a merged PR failed to deploy only AFTER a full build, as an opaque post-build wrangler stack trace. Synced to accounting-tools (PR #882); broad re-sync to other 12 projects pending.
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
