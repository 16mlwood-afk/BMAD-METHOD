---
name: bmad-fork-status
description: Volatile state of the Mason-BMAD fork. Read by mason-bmad-workflow-expert skill on every invocation.
---

# Mason-BMAD Fork — STATUS

> Update whenever you ship a change to the fork, absorb upstream, or change the shipped/designed status of a feature.

**Last updated:** 2026-05-28 by Mason (design-synthesize step-06 brief-faithfulness half)

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
