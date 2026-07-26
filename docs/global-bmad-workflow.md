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

### The routing rule — MAINTENANCE vs NEW DESIGN

**The rule, in Mason's words (ratified 2026-07-26):**

> For **NEW DESIGN WORK**, do not implement any FG entry unless it carries a routing marker from Mason (or a named delegate). For **ROUTINE FORK MAINTENANCE** under a clear owner instruction (e.g. *"fix the fork gaps"*, *"do the fork maintenance"*), you may both:
>
> - log gaps in `fork-gaps.md`, **AND**
> - fix safety and coherence issues directly.

**A maintenance instruction IS pointing.** *"Fix the fork gaps"*, *"do the fork maintenance"*, *"action the backlog"*, *"clear the register"* — these are owner-scope instructions and they authorise the maintenance lane. They must **not** be classified as "not routing", and you must not halt to ask which id: pick the ones you can actually finish, and say which you picked.

**Which lane is this?** Ask what the change *is*, not how big it feels.

| Lane | What it covers | Authorisation |
|---|---|---|
| **MAINTENANCE** — fix it now | A defect in how the fork EXECUTES: a broken recipe, a gate that no-ops, a detector nothing invokes, a test polluting the shared index, drifted prose, a missing affordance the standard already mandates. Safety and coherence repairs. | A clear owner maintenance instruction is enough. |
| **NEW DESIGN / DOCTRINE / POLICY** — needs a routing marker | Changing what the rule IS, not whether it works: a new standard, a taxonomy or enum change, a route/lane redefinition, a scope decision, a policy shift, an entry whose own text says *"doctrine-owner call"* / *"not actioned deliberately"*. | Per-entry routing from Mason. Propose it; don't ship it. |

The test that separates them: **am I fixing execution, or deciding policy?** Implementing a doctrine change is deciding *for* him. Repairing a mechanism that already exists and doesn't work is the job.

**Two things still stop you regardless of lane** — these are blast radius, not authorisation:

1. **Distribution.** The 14-project fan-out sync, `upgrade-bmad.sh`, a `port-workflows-to-skills.sh` regeneration in a contended window, promoting an agent into `custom/agents/`. Authoring is not deployment; that split is deliberate and unchanged.
2. **Irreversible or outward-facing.** A prod mutation, a force-push, deleting or overwriting another session's work, running the register archiver while others are editing it.

**FG entries are an AUDIT tool, not a gate.** Maintenance sessions are allowed to both log and fix gaps under Mason's maintenance instructions. FG entries help with audit; **they are not the only way maintenance is authorised.** Concretely:

- **Logging a real gap you discover is good practice** — keep doing it, proactively, per the paragraph above.
- **It is NOT required to freeze all fixes until each FG has a specific routing line.** A missing `routing:` field blocks nothing in the maintenance lane.
- **Never log-only merely because it is a gap.** A gap logged and left creates a second session whose entire job is to re-read it and re-derive the fix — pure overhead, and the register grows faster than it drains.
- **Write the entry as found + fixed, in the same pass.** The audit value lives in the record and the evidence, not in the delay. *"Found this, here is the cause, here is the fix, here is the run that proves it"* is strictly better provenance than a bare backlog line, because a reader can check it.
- **Prove it, don't assert it — this is the real guardrail.** A fix claimed without a run is UNVERIFIED. State what you ran and what it said. Be strict here, not about who authorised the work.
- **`routing:` values:** `recorded` (or absent) · `routed` (Mason named it) · `retro-routed` (done under a standing maintenance instruction, noted in `routing_note`) · `in-progress` · `shipped`. `fork-fixed-distribution-owed` remains a valid `state:` for authored-but-undistributed work.

**History, corrected (2026-07-26).** A 2026-07-25 session wrote a hard rule here that a vague standing prompt was NOT routing and that unrouted entries must never be implemented. **Mason overruled it the next day, twice** — first in substance ("if I tell you to fix the fork gaps, that is absolutely pointing… I really trust you to do the fork maintenance"), then by dictating the maintenance-vs-new-design split quoted above. His reason is the one that matters: the rule manufactured a loop where a session logs a gap, stops, and a new session has to be opened to say "fix that", so the register only ever grew. The old rule also contradicted this section's own opening principle — it gated on TOPIC (is this an FG entry) rather than on blast radius.

What survives from the original incident, narrowed to what is actually right: **do not implement an entry whose own header reserves the decision for the owner**, keep the strict marker requirement for design/doctrine/policy changes, and never confuse authoring with distributing.

**Retro-authorised under this rule (2026-07-26):** `FG-2026-07-25-04`, `-08`, `-10(2)` and `-12` were implemented earlier the same day under the standing *"fix the recent fork gaps"* instruction, before this text existed. Each now carries `routing: retro-routed` plus a `routing_note` recording that. They are **not** to be reverted. `FG-2026-07-25-11` and `-13` already carried routing and were left untouched. [Scope: FORK CANON — fork-local doc, does not sync to the 13 projects]

**WIRING STATUS IS A FIRST-CLASS MAINTENANCE SIGNAL — prove a guard is LIVE, never infer it (2026-07-26).** A passing unit suite proves a mechanism's **LOGIC**. Only invoking it the way the harness does proves its **WIRING**. Those are different claims, and conflating them is how a reviewed edit-guard sat unwired for a day while three artifacts asserted it was live — the file existed, its 43-case suite was green, `CLAUDE.md` said it had replaced the legacy blob, and `settings.local.json` still ran the blob. Four open fork-gap entries stayed open *for that reason alone*. So:

- **After editing any hook/gate, and after fanning one out, run a live probe** — one input that must be ALLOWED and one that must be BLOCKED, through the real stdin/JSON contract. Exemplar: `cash-recovery/.claude/hooks/guard-health-check.sh` (it also asserts the settings point at the reviewed implementation and that the superseded one is gone).
- **Never write "now enforced by X" on the strength of a green test run.** Say which artifact you invoked and what it returned, or label the claim UNVERIFIED.
- **Hooks distribute on a SEPARATE TRACK from workflows** (`settings.local.json` is gitignored and the BMAD sync does not carry it), so authoring a guard never deploys it. State the deployment state explicitly every time — this is the same failure as `FG-2026-07-25-09`.
- **A documented override that no code honours is not an override.** It makes a gate look well-designed while pushing every real use into a tool-swap bypass. If a deny message names an escape hatch, something must implement it, and its use must be logged.

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
