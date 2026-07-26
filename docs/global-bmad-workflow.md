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

### The core lane (`_bmad/core/workflows/`) is UNMANAGED — shadow, don't patch

The sync maps `custom/workflows/` → `_bmad/bmm/workflows/` only. Core workflows (`_bmad/core/workflows/*` — e.g. `brainstorming`, `party-mode`) are frozen at whatever the original install shipped: they are NOT in the fork lane, the sync never touches them, and the managed-path edit guard blocks in-place edits with nowhere to redirect. That is by design, not an oversight — but it means a core workflow can drift from fork doctrine with no in-place fix.

**The blessed fix is a custom-lane SHADOW:** author a fork-managed replacement in `custom/workflows/` and point routing/docs/skills at it, leaving the core original as the upstream specialist (precedent: `quick-brainstorm` shadows core `brainstorming` — the shadow is the front door, core remains the deep-divergence specialist). Do NOT hand-edit `_bmad/core/`, and do NOT build sync machinery for it: a structural `custom/core-overrides/` sync lane is deliberately DEFERRED until a second core workflow actually needs fork management — one shadow is a pattern, one override lane for one file is machinery (fork-gaps `2026-07-03 — _bmad/core/workflows/ has no fork lane`).

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

**The decision boundary is blast radius, not difficulty.** Project-local + reversible + a clear best option → **execute the default, then report** (e.g. a scoped `sync-bmad-workflows.sh --only <project>` to clear that project's standards drift, pruning a stale worktree, re-running a stale tracker). Fork-wide OR irreversible OR outward-facing → present options and get approval (the no-arg fan-out sync across all targets, `upgrade-bmad.sh`, promoting an agent into `custom/agents/`, anything that propagates to the 13 projects). A multiple-choice menu for a safe local default is the failure mode — it hands a decided question back to the user. Report shape for the auto-execute lane: *"I did X; if you want Y (the bigger/fan-out thing), say so."* Full test → the global `feedback-lead-dont-ask` memory (blast-radius autonomy). When the user has *already named* the action in their request, it is authorized — do it; don't re-ask permission for it under the banner of caution.

**Log structural method/infra gaps yourself → `docs/fork-gaps.md`.** When the fork/infra/method *fights* an agent — not a one-off bug, but the wiring making normal work painful (a deploy path that isn't legible, a hook with nowhere to redirect, sync drift, a workflow step that overruns) — record it in the fork-gaps backlog proactively, pointing at the specific target file. You are the noticer; don't wait for the user to ask "why is this so awkward?". This is the global `workflow-friction-and-process-issues` policy made concrete with a write target. The backlog is the fork-driven sibling of the `maintenance-triage` (production-driven) front door.

**Logging a gap is NOT authorisation to implement it — an FG entry is a backlog item, never a work order.** The rule above makes you the *noticer*; it does not make you the *implementer*. The two are separate decisions and only the first is autonomous.

- **A maintenance session may NOT treat "fix the recent fork gaps" (or any equivalently vague standing prompt) as carte blanche to implement unrouted FG entries.** That phrasing names a *file*, not a piece of work — it fails the grounding gate for exactly the reason `quick-dev`'s does: you cannot state verb + target from the input alone. Halt and ask for one.
- **The grounding bar for implementing an FG entry is a concrete id AND a target.** Acceptable: *"Implement FG-2026-07-25-11 in design-implement for inbound-flow."* Not acceptable: *"fix the recent fork gaps"*, *"action the backlog"*, *"clear the register."*
- **You may always PROPOSE.** Reading the register, diagnosing an entry, drafting the fix direction, sharpening a target file, and reporting *"FG-N is ready to route, here is the patch I would write"* are all in-scope and encouraged. **Writing the fork code is not**, until the entry is routed.
- **Routing is Mason's call** (or a delegate he names in-thread). Once an entry is routed, implementation may be delegated freely — the gate is on the *decision to start*, not on the work itself.
- **State machine on each entry:** `recorded` → `routed` → `in-progress` → `shipped`. An entry sitting at `recorded` is inert by construction. Only `routed` (or later) may be implemented. `fork-fixed-distribution-owed` remains a valid terminal-ish state for authored-but-undistributed work — authoring is not deployment.

**Why this exists (2026-07-25).** A session started with the single prompt *"fix an action, the recent fork gaps."* migrated the register to schema v1, armed a write-time gate, added an archive step, and implemented `FG-2026-07-25-11` **seven minutes after another session logged it** — while that entry's own header said the investment decision was Mason's. Nothing was lost (the session correctly marked it `fork-fixed-distribution-owed` and did not distribute), but the register had silently become an autonomous work queue instead of a backlog, and no one chose that. The failure is not the session's diligence — it is that a vague prompt over a file full of actionable items reads as a mandate unless something says otherwise. This is that something. [Scope: FORK CANON — fork-local doc, does not sync to the 13 projects]

**Code wins over narrative docs — verify before any destructive action (fork-gap #7).** The fork's hand-maintained narrative docs (`STATUS.md`, this file, the `~/.bmad-reference` header, migration plans, project memories) **lag the sync code** — they are decision aids, not ground truth. When such a doc says a capability is *unsupported / orphaned / cut-off / complete* and you're about to act on it — **especially before anything destructive or irreversible (a revert, a `--delete`, dropping a pilot, "rolling back X")** — first confirm the claim against the actual code (`sync-bmad-workflows.sh`, the installer, the relevant script) and the live state. If the doc and the code disagree, **the code wins**: act on the code, then fix the stale doc in the same pass. This rule exists because stale "skills-layout is unsupported / cash-recovery is orphaned" guidance once nearly drove a revert of a *working* pilot that the sync code already supported. Treat a capability claim as CHECKED (does the code path exist?), never merely asserted (see the STATUS `built: <commit|NO>` integrity rule).

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
