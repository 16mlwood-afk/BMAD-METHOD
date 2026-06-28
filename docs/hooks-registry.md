---
title: Hooks & Gates Registry
description: The single registry of every Claude Code hook in the Mason-BMAD setup — name, event type, purpose, source-of-truth path, enforcement level, and owner. Hooks may only be introduced here; ad-hoc per-project hooks outside this registry are drift.
---

# Hooks & Gates Registry

The single place hooks are catalogued and governed — the hook-layer equivalent of `STANDARDS.md`.

## The one rule

**Hooks live in exactly two homes:** `~/.claude/hooks/` + `~/.claude/settings.json` (machine-local, global) and the synced hook templates / scripts in `~/bmad-method-v6/` (distributed by `sync-bmad-workflows.sh`). **Do not introduce ad-hoc hooks elsewhere** — a per-project `_bmad/`-local hook or an inline one-off not listed here is drift. Add the hook here first, then wire it.

Hooks are machine-local (they live in `settings.json`, which does NOT sync through the fork) — authoring a hook script in the fork does not ship the wiring; the `settings.json` entry does.

## Registry

| Hook | Event | Purpose | Source of truth | Level | Owner |
|---|---|---|---|---|---|
| secrets-loader | SessionStart | Source `~/.secrets` into the session env | inline (settings.json) | n/a | fork maintainer |
| check-upstream-drift | SessionStart | Warn when the fork is behind upstream BMAD | `~/bmad-method-v6/check-upstream-drift.sh` | warn | fork maintainer |
| check-fork-gaps | SessionStart | Surface open entries from `docs/fork-gaps.md` | `~/bmad-method-v6/check-fork-gaps.sh` | warn | `mason-bmad-workflow-expert` |
| check-standards-drift | SessionStart | Warn when a project's synced STANDARDS.md is behind canon | `~/bmad-method-v6/check-standards-drift.sh` | warn | STANDARDS canon |
| check-claude-md-drift | SessionStart | Soft-warn on a missing or thick/restating project CLAUDE.md | `~/bmad-method-v6/check-claude-md-drift.sh` | warn | STD-CLAUDE-001 |
| prod-readiness-probe | SessionStart | Warn on a live project missing a deploy/memory contract | `~/.claude/hooks/prod-readiness-probe.sh` | warn | `prod-readiness-charter` |
| session-epoch | SessionStart | Record session start time for other hooks | inline | n/a | fork maintainer |
| chrome-cache-health | SessionStart | Warn on oversized Chrome cache (freeze bug) | inline | warn | fork maintainer |
| bmad-sync-warn | UserPromptSubmit | Warn when synced workflows are stale vs the fork | inline | warn | fork maintainer |
| auto-format | PostToolUse | Format files after edit/write | `~/.claude/hooks/auto-format.sh` | enforce | fork maintainer |
| bmad-auto-sync | PostToolUse(EnterWorktree) | Sync BMAD workflows into a new worktree | inline | enforce | fork maintainer |
| enforcement-expert-nudge | PreToolUse(Edit\|Write) | Nudge to consult `enforcement-expert` when editing an enforcement surface | `~/.claude/hooks/enforcement-expert-nudge.sh` | warn (nudge) | `enforcement-expert` |
| check-claude-md-lint | PreToolUse(Edit\|Write) | Nudge to use a pointer when a CLAUDE.md edit restates a shared standard | `~/bmad-method-v6/check-claude-md-lint.sh` | warn (nudge) | STD-CLAUDE-001 |
| check-fork-authoring-collision | PreToolUse(Edit\|Write) | Nudge when authoring in `custom/workflows/shared/` while ANOTHER session has uncommitted changes there (per-session ledger avoids self-flagging) | `~/bmad-method-v6/check-fork-authoring-collision.sh` | warn (nudge) | `parallel-sessions` |
| prod-readiness-deploy-gate | PreToolUse(Bash) | Gate deploy-class commands on a prod-readiness contract | `~/.claude/hooks/prod-readiness-deploy-gate.sh` | enforce (gate) | `prod-readiness-charter` |
| sprint-apply-gate | PreToolUse(Edit\|Write\|Bash) | Freeze a pending correct-course proposal's `files_to_change` set until an APPROVE token clears it; ships DRY-RUN (`~/.claude/sprint-apply-gate.mode`=`enforce` to gate) | `~/.claude/hooks/sprint-apply-gate.sh` | warn→gate | `bmad-correct-course` |
| sprint-apply-approve | UserPromptSubmit | Clear the sprint-apply gate on an exact `APPROVE: APPLY_SPRINT_PROPOSAL::<id>` token | `~/.claude/hooks/sprint-apply-approve.sh` | enforce (clears gate) | `bmad-correct-course` |
| friction-reflect | Stop | Fire-once end-of-session prompt to log structural friction | `~/bmad-method-v6/check-friction-reflect.sh` | warn (nudge) | `workflow-friction-and-process-issues` |

**Project-level enforcement hooks** (in each project's `.claude/settings.local.json`, not global): the worktree Edit/Write hard-block and the `bmad-single-track-guard` (blocks `git merge` into local main). These are per-project by design; they follow the same "no ad-hoc additions" rule.

## Adding a hook

1. Decide the enforcement class first (consult `enforcement-expert`): DETERMINISTIC gate vs PROBABILISTIC nudge. A non-negotiable rule needs a deterministic tier; guidance can be a nudge.
2. Write the script in a home above (fork script for synced/global, `~/.claude/hooks/` for machine-local).
3. Wire it in `~/.claude/settings.json` (or the synced template).
4. **Add a row to this registry** — name / event / purpose / source / level / owner.
5. **Add a smoke-test case** to `check-hooks-smoke.sh` — a representative stdin fixture asserting it exits 0 and honours its output contract (empty / valid JSON / plain text for SessionStart). For a stdin-consuming hook (Stop / PreToolUse), add a BEHAVIORAL case that pins the stdin contract (e.g. a fixture that must be silent), so the "hook ignores its stdin and emits valid-but-wrong output" bug class is caught.

## Governance

- **Function is validated, not just existence.** `check-hooks-smoke.sh` runs in the fork's `.husky/pre-commit` — a hook that crashes, emits malformed JSON, or breaks its stdin contract can't be committed. (This exists because a broken hook fails *silently*: the friction-reflect Stop hook once shipped emitting valid-but-wrong output because it ignored stdin — see fork-gaps "Hooks ship unvalidated".)
- Reviewed alongside `STANDARDS.md` by the quarterly Standards Governance Review (which verifies each in-repo hook's source file exists). Catching *unregistered* hooks is future work.
