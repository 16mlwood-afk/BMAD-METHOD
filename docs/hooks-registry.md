---
title: Hooks & Gates Registry
description: The single registry of every Claude Code hook in the Mason-BMAD setup — name, event type, purpose, source-of-truth path, enforcement level, and owner. Hooks may only be introduced here; ad-hoc per-project hooks outside this registry are drift.
---

# Hooks & Gates Registry

The single place hooks are catalogued and governed — the hook-layer equivalent of `STANDARDS.md`.

## The one rule

**Hooks live in exactly two homes:** `~/.claude/hooks/` + `~/.claude/settings.json` (machine-local, global) and the synced hook templates / scripts in `~/bmad-method-v6/` (distributed by `sync-bmad-workflows.sh`). **Do not introduce ad-hoc hooks elsewhere** — a per-project `_bmad/`-local hook or an inline one-off not listed here is drift. Add the hook here first, then wire it.

## Where the fork wires a PROJECT hook — changed 2026-09-21

**The fork's project hooks are wired by SCRIPT REFERENCE into each project's tracked
`.claude/settings.json`.** The script itself is delivered from `custom/hooks/` into
`<project>/.claude/hooks/`, and the settings entry only locates and runs it.

Until this change every hook the fork shipped was written as **inline shell into
`.claude/settings.local.json`**, which is gitignored in every target. Three costs, all
measured on 2026-09-21 across the registered projects:

- **A guard existed only on the machine that synced it.** A fresh clone, a new device or
  another contributor got a repository that looked guarded and was not. Four targets
  (`comms_dashboard`, `bison-ops`, `bison-website`, `inbound-flow`) were each holding six
  fork hook FILES with none of them tracked, because those repositories also ignore
  `.claude/hooks/`.
- **Nothing was reviewable.** A 3,164-character inline blob appears in no diff, has no
  unit test, and a hook could claim in its own header to be wired while the settings said
  otherwise.
- **The channel ran one way.** A project could not see the fork's guards as files, so 32
  hooks were authored locally in one repository with no route back into the fork.

**Permissions do NOT follow the hooks.** `permissions.defaultMode: bypassPermissions` and
`enableAllProjectMcpServers: true` are per-machine TRUST decisions; committing them into
fourteen tracked repositories would be a security-posture change wearing the clothes of a
refactor. They stay in `settings.local.json`, which keeps its proper job.

**A hook left in BOTH files fires TWICE.** Claude Code merges list keys across settings
files rather than overriding them, so the sync demotes every fork-owned hook out of
`settings.local.json` in the same act as it writes the tracked file. The two jq programs
that do it (`JQ_MERGE`, `JQ_LOCAL` in `sync-bmad-workflows.sh`) share one ownership
definition, and `tools/verify-settings-merge.sh` pins that they stay identical.

**A repository whose `.gitignore` would swallow the tracked file is repaired or refused,
never written into silently.** The sync appends the narrowest negations under a marked
block, then RE-VERIFIES with `git check-ignore` — an append is not a result. If it cannot
prove the paths are now trackable, or the `.gitignore` is mid-edit, it falls back to the
old local-file behaviour and prints the exact lines to add. A guard nobody can commit is
the defect, not the fix.

**Ownership is declared, not inferred.** `bmadTrackedHookScripts` in the template lists the
script basenames the fork claims; the merge reclaims a hand-wired copy of one of those so
it ends up wired exactly once. It is an explicit list rather than a regex over the template
because `bash_edit_guard.py` must stay OUT of it — `cash-recovery` wires that one its own
way, and a wider key would silently delete a working guard.

Adding a hook script to `custom/hooks/` still does not ship the wiring; the entry in
`src/modules/bmm/_module-installer/assets/hooks.json` does. Two of the golden suites
(`test_stash_untracked_guard.py`, `test_main_thread_open_pointer.py`) now read that
template when they run inside the fork, so a script added without a wiring entry fails a
test rather than shipping dormant.

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
| sprint-apply-gate | PreToolUse(Edit\|Write\|Bash) | Risk-classifier over a pending correct-course proposal's `files_to_change`. OWNER-GATE lane freezes until an APPROVE token (`~/.claude/sprint-apply-gate.mode` dry-run→enforce). AUTOPILOT lane (`~/.claude/sprint-apply-autopilot.mode` off→classify-log→on) auto-applies deterministically-classified low-risk single-repo sprint-execution edits (`_bmad-output/implementation-artifacts/` + `epics.md` only; planning-artifacts PRD/architecture/specs → owner-gate; ≤`AUTOPILOT_MAX_FILES`, no governance/doctrine path) after a pre-edit snapshot to `_bmad/.sprint-apply-backups/`. Gate DERIVES the class (never the planner's label); fail-closed; kill-switch `_bmad/.sprint-apply-autopilot.disable` | `~/.claude/hooks/sprint-apply-gate.sh` | warn→gate (+autopilot opt-in) | `bmad-correct-course` |
| sprint-apply-approve | UserPromptSubmit | Clear the sprint-apply gate on an exact `APPROVE: APPLY_SPRINT_PROPOSAL::<id>` token | `~/.claude/hooks/sprint-apply-approve.sh` | enforce (clears gate) | `bmad-correct-course` |
| manifest-contract-gate | PreToolUse(Edit\|Write\|Bash) | Multi-writer contract for the shared `design-ingest-*` / `design-implement-grid-*` write-back ledgers: un-ID'd pass record, in-place renumbering, concurrent/stale/malformed current-editor marker, and sweep-shaped commands that would scoop another session's dirty manifest. Also a CLI (`--acquire`/`--release`/`--status`/`--check`) — `--release` refuses to clear another session's marker. Deterministic detection, WARN-only action; override `MANIFEST_CONTRACT_OFF=1` (logged to `~/.claude/logs/manifest-contract-gate.jsonl`) | `~/.claude/hooks/manifest-contract-gate.py` | warn (promotion criteria in the contract) | `docs/manifest-contract.md` |
| hook-resolve-check | SessionStart | Two findings, one family — a guard that is configured and cannot run. (1) a hook the settings WIRE whose script is absent; (2) a hook script that is PRESENT and that the repository is set to ignore, so a fresh clone, a second machine or CI gets a project that looks guarded and is not. Keys on IGNORED, never on merely untracked — a guard you just wrote is ordinary work and is never reported. Silent when clean; never blocks | `~/bmad-method-v6/custom/hooks/hook-resolve-check.py` | warn | fork maintainer |
| friction-reflect | Stop | Fire-once end-of-session prompt to log structural friction | `~/bmad-method-v6/check-friction-reflect.sh` | warn (nudge) | `workflow-friction-and-process-issues` |

**Project-level enforcement hooks** (in each project's tracked `.claude/settings.json` since
2026-09-21 — see *Where the fork wires a PROJECT hook* above; previously
`settings.local.json`): the worktree Edit/Write hard-block and the `bmad-single-track-guard`
(blocks `git merge` into local main). These are per-project by design; they follow the same
"no ad-hoc additions" rule.

### The nine generic agent-discipline guards — moved into the fork 2026-09-21

Authored in `amazon-removal-assistant`, where they were tracked and wired but reachable by
exactly one project. Each carries its `test_*.py` golden suite; all nine suites run green
from `custom/hooks/`. Source of truth for every row: `~/bmad-method-v6/custom/hooks/<name>.py`.

| Hook | Event | Purpose | Level |
|---|---|---|---|
| agent-isolation-gate | PreToolUse(Agent\|Task\|EnterWorktree) | Deny an implementation-authority spawn with no worktree isolation | enforce (gate) |
| branch-switch-removal-guard | PreToolUse(Bash) | Ask before a branch switch or hard reset takes recognisable files off the disk | ask |
| claude-md-admission-gate | PreToolUse(Edit\|Write\|MultiEdit\|Bash) | A new section in an always-loaded CLAUDE.md must earn its slot | enforce (gate) |
| claude-md-drift | UserPromptSubmit | Say when CLAUDE.md moved under the session | warn |
| main-thread-open-pointer | UserPromptSubmit | Hand long work to a background agent; keep the main thread open | warn (nudge) |
| orphaned-chrome-sweep | SessionStart | Surface leaked browser processes from past sessions | warn |
| owned-decision-guard | Stop | Never hand back a decision already settled in writing | enforce (gate) |
| owner-step-handback-warn | Stop | A step handed to the owner must name why it needs him | warn |
| stash-untracked-guard | PreToolUse(Bash) | The stash stack is shared across worktrees — refuse `stash -u` | enforce (gate) |

**Two were deliberately NOT moved** and stay project-local until their partner names and
persona come from configuration rather than being hard-coded: `working-week-pointer.py` and
`transcript-attribution-pointer.py`. Nineteen others in that project name pallets, Leipzig,
TheFBAPrep, claims against Amazon, the Wren persona or its own MCP server, and are correctly
project-local.

### A guard the VCS does not carry is not a guard — measured 2026-09-21

`hook-resolve-check` gained its second finding on 2026-09-21, and the fork template gained a
`bmad-hook-resolve-check` SessionStart entry so it fires in every project rather than in the
two that happened to wire it by hand.

Running it against all fourteen registered targets that day, it fires on **five**. Four —
`comms_dashboard`, `bison-ops`, `bison-website`, `inbound-flow` — ignore `.claude/hooks/`
wholesale and each already held six or more fork-delivered hook files with **zero tracked**;
three of those four also ignore `.claude/settings.json`, the registration itself. A fifth,
`amazon-lead-generator`, carries its guards and ignores only the wiring. Seven are clean and
the check says nothing about them.

The sync already narrows a swallowing `.gitignore` when it runs in such a project (see *Where
the fork wires a PROJECT hook* above), so the gap was never the repair. It was that **nothing
said a repository was in that state until somebody happened to run a sync.**

**Still open, named rather than fixed (2026-09-21).** `guard-wiring-check.sh` opens with
*"WIRED HERE on SessionStart via the tracked `.claude/settings.json`"*. That is true in two of
the fourteen projects it is distributed to and false in the other twelve, where the fork
template wires it nowhere — a file asserting its own enforcement status in twelve repositories
where the assertion does not hold. It is the same family as the two findings above and is a
separate decision, because unlike `hook-resolve-check` it also runs live probes. Counted with
it: of the 15 guard scripts the fork ships, the template wires 11; `audit-override-log.py` is
wired nowhere at all, `deploy_lane_guard.py` in one project, and `guard-health-check.sh` is
honestly declared manual in its own header and is therefore NOT an instance.

## Adding a hook

1. Decide the enforcement class first (consult `enforcement-expert`): DETERMINISTIC gate vs PROBABILISTIC nudge. A non-negotiable rule needs a deterministic tier; guidance can be a nudge.
2. Write the script in a home above (fork script for synced/global, `~/.claude/hooks/` for machine-local).
3. Wire it in `~/.claude/settings.json` (or the synced template).
4. **Add a row to this registry** — name / event / purpose / source / level / owner.
5. **Add a smoke-test case** to `check-hooks-smoke.sh` — a representative stdin fixture asserting it exits 0 and honours its output contract (empty / valid JSON / plain text for SessionStart). For a stdin-consuming hook (Stop / PreToolUse), add a BEHAVIORAL case that pins the stdin contract (e.g. a fixture that must be silent), so the "hook ignores its stdin and emits valid-but-wrong output" bug class is caught.

## Governance

- **Function is validated, not just existence.** `check-hooks-smoke.sh` runs in the fork's `.husky/pre-commit` — a hook that crashes, emits malformed JSON, or breaks its stdin contract can't be committed. (This exists because a broken hook fails *silently*: the friction-reflect Stop hook once shipped emitting valid-but-wrong output because it ignored stdin — see fork-gaps "Hooks ship unvalidated".)
- Reviewed alongside `STANDARDS.md` by the quarterly Standards Governance Review (which verifies each in-repo hook's source file exists). Catching *unregistered* hooks is future work.
