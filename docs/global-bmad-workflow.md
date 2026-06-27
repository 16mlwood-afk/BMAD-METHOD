---
title: Global BMAD Workflow Management
description: Sync, upgrade, onboarding, and autonomous-maintenance procedures for the Mason-BMAD fork.
---

# Global BMAD Workflow Management

> Factored out of `~/.claude/CLAUDE.md` (Executive-summary / pointer-style refactor). The global
> CLAUDE.md keeps a short What/Why/Where pointer to this file; the full procedures live here.

The user maintains a fork of BMAD-METHOD at `~/bmad-method-v6/` (remote: `16mlwood-afk/BMAD-METHOD`, branch: `custom`). Custom workflows live in `custom/workflows/` and are distributed to all projects via a sync script. The `custom` branch tracks `origin/main` (upstream) and rebases custom commits on top.

**The standards canon → `custom/workflows/shared/STANDARDS.md`.** Single index of every shared standard a project follows — deploy, delivery, webhook boundaries, diagnostics, worktree/parallel-session safety, prod-readiness, AND memory discipline. When you need "the canonical way to do X," start there: it names each standard, what it governs, its Home doc, and its `contract_version`. Standards are referenced BY PATH, never restated; a project CLAUDE.md that disagrees with the Home doc is drift (log it in `docs/fork-gaps.md`).

## Workflow routing — route from intent, don't make the user the dispatcher

When a user's natural-language intent clearly maps to a named BMAD workflow and project state makes
the route unambiguous, **select and invoke that workflow** — don't ask the user to name it. BMAD's
workflows are an explicit, named routing surface; the friction to remove is being forced to act as a
dispatcher when the next step is obvious. This **complements, does not override, the grounding gate**:
auto-route when verb + target are clear from the input; halt when they aren't.

Default routes:

| Intent | Route |
| --- | --- |
| "carry on implementing the stories" / "do the next story" | `create-story` (if no valid story exists) → `dev-story` |
| "create the next story" | `create-story` |
| "review this code" | `code-review` |
| "check sprint status" | `sprint-status` |
| "run sprint planning" | `sprint-planning` |
| "run a retrospective" | `retrospective` |

**Approval boundaries — stop and confirm, do not auto-proceed:** deploy, push, commit, DB migration,
promoting an epic / expanding scope, any live external-state write, or genuine ambiguity (two+ valid
routes with materially different consequences, or intent not groundable to a verb + target). At a
boundary, state the recommended route and ask one scoped question — never a multi-item menu.

Full cross-project policy → the `workflow-routing` global memory; this is its BMAD-specific mapping.

## "sync bmad" — Push custom workflows + hooks to projects

1. If this project's `_bmad/bmm/workflows` path isn't in `~/.bmad-targets`, append it first
2. Run `~/bmad-method-v6/sync-bmad-workflows.sh` — syncs workflows and merges worktree enforcement hooks into `.claude/settings.local.json` (preserves existing permissions)
3. If the sync **blocks** a project (local-only content detected), pull changes first: `sync-bmad-workflows.sh --pull <path>`, review, commit to the fork, then re-sync
4. Diff this project's `CLAUDE.md` against `~/bmad-method-v6/src/modules/bmm/_module-installer/assets/CLAUDE.md.template`
5. Propose updates for any missing sections — preserve project-specific values (structure, deploy command, conventions)

**Never modify workflows directly in `_bmad/bmm/workflows/`.** Changes made in projects will be overwritten on next sync. Instead, modify `~/bmad-method-v6/custom/workflows/` and re-sync, or use `--pull` to bring project changes back to the source first.

## Parallel work does NOT isolate BMAD state

**Guardrail.** Worktrees isolate the source tree only. They do **not** isolate BMAD planning state
(stories / sprint-status / epics are untracked and live on the main checkout), shared infra (one
database, object store, and external API account across every worktree), or build artifacts
(`node_modules` / build caches symlink back to main). So parallel sessions collide on planning,
data, and builds even when their code edits never touch the same files.

**Until** BMAD planning state is committed (worktree-self-sufficient) **and** a parallel-work
protocol is defined (story-level ownership + "no migrations in parallel"), **treat story ownership
as single-threaded.** Don't run two sessions against the same story, and never run a migration while
another session is live.

Full reasoning (the four structural reasons + what a real fix looks like) → `parallel-work-and-bmad-state.md`.

## "upgrade bmad" — Pull upstream BMAD updates into the fork

1. Run `~/bmad-method-v6/upgrade-bmad.sh`
2. If merge conflicts occur, resolve them in `~/bmad-method-v6/`, commit, then re-run

## New project bootstrap

To onboard a new project to the fork, run **one command** — it is idempotent and self-verifying:

```
~/bmad-method-v6/onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed]
```

Defaults: `<project-dir>` = cwd, `--name` = dir basename, `--phase` = greenfield. The script does
git init, clones the reference project's `_bmad/` base (per `~/.bmad-reference`), sanitizes
project-specific config, creates `CLAUDE.md` from the template, registers the project in
`~/.bmad-targets`, and runs the sync (custom workflows, skills, hooks, commands). The `bmad-onboard`
skill wraps this for natural-language invocation ("install the BMAD fork", "set up BMAD here").

**Do NOT run `bmad-cli install` / `npx bmad-method install`.** The installer now produces the
upstream v6.8.0 skills layout (`.claude/skills/bmad-*`), which the fork's custom layer and
`sync-bmad-workflows.sh` do not support — a fresh install yields vanilla BMAD with none of the fork's
safety layer. All projects run the 6.0.4 base + custom overlay layout, which `onboard-project.sh`
reproduces. (Migrating the fork to the v6.8.0 skills layout is planned in
`~/bmad-method-v6/custom/MIGRATION-v6.8-skills-plan.md`.)

### New-project gold-standard checklist

`onboard-project.sh` wires the architecture; this is the content checklist so a new repo comes up matching the gold standard (the `cash-recovery` reference shape). After bootstrap, confirm:

1. **Standards synced in** — `_bmad/bmm/workflows/shared/STANDARDS.md` (or `_bmad/bmad-shared/STANDARDS.md` for skills-layout) is present. `check-standards-drift.sh` reads clean.
2. **Project CLAUDE.md follows STD-CLAUDE-001** — thin, pointer-based, in the canonical shape (`# Overview / # Dev / # Deploy / # Memory / # Notes`). It points at shared standards by ID rather than restating them:
   - Deploy → **STD-DEPLOY-001** (`shared/deployment-to-prod.md`)
   - Memory → **STD-MEMORY-001** (the global memory docs) + this repo's `MEMORY.md`
   - CLAUDE.md discipline itself → **STD-CLAUDE-001** (`shared/claude-md-standard.md`)
3. **Memory seed (optional)** — an initial `MEMORY.md` index (+ a placeholder fact) if you want a starter; otherwise it's created on first save.

A new repo is never missing the architecture — bootstrap guarantees the wiring; this checklist guarantees the CLAUDE.md is thin and pointer-correct rather than a fat copy of doctrine. If the bootstrap template ever drifts from STD-CLAUDE-001, fix the template, not each repo.

## Autonomous maintenance — make these calls yourself, don't ask

You are responsible for keeping the BMAD fork and project workflows in a healthy state. The following decisions do NOT require asking the user — when you hit them, just resolve.

**Log structural method/infra gaps yourself → `docs/fork-gaps.md`.** When the fork/infra/method *fights* an agent — not a one-off bug, but the wiring making normal work painful (a deploy path that isn't legible, a hook with nowhere to redirect, sync drift, a workflow step that overruns) — record it in the fork-gaps backlog proactively, pointing at the specific target file. You are the noticer; don't wait for the user to ask "why is this so awkward?". This is the global `workflow-friction-and-process-issues` policy made concrete with a write target. The backlog is the fork-driven sibling of the `maintenance-triage` (production-driven) front door.

**BMAD-managed paths.** These directories are owned by the BMAD fork sync. Treat their contents as derivable, not authored locally in projects:

- `_bmad/` (entire tree)
- `.claude/commands/bmad/`
- `.claude/settings.local.json` (BMAD-injected hooks/permissions only — preserve other entries)

**`git pull` blocked by untracked files in BMAD-managed paths.** This is the standard "stale local sync vs newly-committed sync" race. Resolution:

1. Confirm every blocking path is inside a BMAD-managed directory above. If any blocking path is outside (real local work), stop and surface to the user.
2. Move the local untracked copies to `.claude/orphaned-main-commits/<YYYYMMDD-HHMMSS>/` (preserving directory structure). Do not `rm` — preserve for inspection.
3. `git pull --ff-only`.
4. If `~/.bmad-targets` includes this project, run `~/bmad-method-v6/sync-bmad-workflows.sh` afterward to confirm fork-of-truth state.

Never block a pull on these files; they are either stale duplicates of fork content or will be re-emitted by the next sync.

## Fork hygiene

- **Docs frontmatter is mandatory.** Any `docs/*.md` file in the BMAD fork must include `title:` and `description:` frontmatter; otherwise the Starlight docs build in the pre-commit hook fails and strands the commit (the file stays staged-but-uncommitted with no obvious cause). `docs/` is symlinked into `website/src/content/docs`, so every doc is a Starlight content entry and must satisfy its schema.

**Session-start drift warnings.** Do NOT run upgrade/sync scripts unprompted at session start — they are slow and affect shared resources (the fork's git state, every targeted project). But:

- The moment the user invokes a `/bmad:` workflow that depends on the fork being current, OR you hit a pull conflict caused by drift, OR the user asks anything about BMAD state — resolve the drift first by running the appropriate script (`upgrade-bmad.sh` for fork-behind-upstream, `sync-bmad-workflows.sh` for projects-behind-fork). Don't ask first.
- If `upgrade-bmad.sh` hits merge conflicts in `~/bmad-method-v6/`, surface them — that's the one case where you need the user.

**Editing files inside `_bmad/bmm/workflows/`.** Never edit in place — these are sync targets and your edits get overwritten on next sync. Edit `~/bmad-method-v6/custom/workflows/` instead and re-sync. If the user asks for a workflow change, do this without asking which copy to edit.

**Memory changelog when cross-syncing.** Sync operations that touch `.claude/settings.local.json` or memory-relevant files in other projects must be logged per the Memory Hygiene → Breadcrumb trail rules (see `~/.claude/projects/-Users-masonwood/memory/docs/memory-hygiene.md`). The sync script itself is silent; you must write the entry.
