---
name: bmad-onboard
description: >
  Onboard a new project/directory to the Mason-BMAD fork. Load when the user says any of:
  "install the BMAD fork", "onboard this project to BMAD", "set up BMAD here", "this is a new
  project, install the fork", "wire this directory to the fork", "bootstrap BMAD for this project",
  "this is my fork of <upstream>", "re-stamp onboarding", "is this repo onboarded?".
  Handles standalone repos and personal forks of an external upstream, stamps a completion marker,
  and offers a teach-by-doing tutorial. Runs the deterministic onboarding script — do NOT hand-roll
  the steps or run `bmad-cli install`.

provenance:
  id: bmad-onboard
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://github.com/bmad-code-org/BMAD-METHOD  # upstream project this fork descends from; its own installer is the adaptation source
    - https://docs.bmad-method.org/how-to/install-bmad/  # upstream's `npx bmad-method install` onboarding flow, which this skill deliberately replaces with a custom script for a different (6.0.4 base + custom overlay) layout
  origin_type: adapted
  exemption_reason: ""
  predecessor_id:
  superseded_by:
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. Core job (bootstrap a project onto BMAD) matches upstream bmad-code-org's own installer, but this skill runs a materially different local script to preserve the fork's custom layout/safety layer instead of upstream's v6.8.0 skills layout."
---

# BMAD fork onboarding

## External research checked
- Date: 2026-07-24 · Queries: "BMAD-METHOD onboard-project script install workflow skill" · "bmad-code-org BMAD-METHOD GitHub install.js onboarding CLI"
- Sources: <https://github.com/bmad-code-org/BMAD-METHOD> · <https://docs.bmad-method.org/how-to/install-bmad/>
- Verdict: ADAPTED — upstream BMAD-METHOD ships its own installer/onboarding CLI (`npx bmad-method install`); this skill deliberately does NOT use it, instead running a custom `onboard-project.sh` to reproduce the fork's older, custom-layer-compatible layout and add fork-specific topology/marker/tutorial handling.

The user wants a new directory wired to the Mason-BMAD fork (`~/bmad-method-v6/`) so it matches all
their other projects — full custom workflow layer, hardened quick-dev, design-* workflows, custom
skills, worktree hooks, slash commands. There is **one command** that does this with no hurdles:

```
~/bmad-method-v6/onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed] \
                                    [--topology standalone|fork-of-upstream] [--upstream <url>]
```

## How to run it

1. **Project dir** = the current directory unless the user names another. If they say "we're in a
   new directory now," that directory IS the target — pass nothing (defaults to `$PWD`) or pass it
   explicitly.
2. **Name** defaults to the directory basename; **phase** defaults to `greenfield` (a brand-new
   build). Only override if the user indicates otherwise (e.g. an existing codebase → `brownfield`).
   These are sensible defaults — don't interrogate the user; just state what you're using and run.
3. **Topology** — is this a standalone repo, or a *personal fork of an external upstream*? The script
   **auto-detects** a fork when an `upstream` git remote already exists, so usually you pass nothing.
   Only when the repo has no `upstream` remote yet but the user describes it as their fork of someone
   else's project, confirm the upstream URL and pass `--upstream <url>` (which implies
   `--topology fork-of-upstream` and adds the remote). This is the one genuine fork in onboarding —
   ask only if the signal is ambiguous; otherwise state what you detected and proceed.
4. Run the script. It is idempotent and self-verifying. On success it reports the synced custom
   workflows, skills, hooks, and commands, **and stamps a completion marker** (see below).
5. After it finishes, **the BMAD layer is done.** Offer to run the **`bmad-onboard-tutorial`** skill —
   it walks the safety gates once by doing (a safe sync dry-run, then a first feature branch + tests +
   commit). Then help scaffold the *application* itself (framework, deps, env) — that is
   project-specific and not BMAD's job.

## Re-stamping an already-onboarded repo

If the repo is already onboarded but predates the completion marker (most existing projects do), or the
fork has bumped the onboarding playbook version, run `onboard-project.sh --restamp [<dir>]`. It rewrites
the marker **only** — no re-clone, no sync. The SessionStart detector (`check-onboarding-version.sh`)
surfaces a line when a stamped repo is behind the current playbook; a missing stamp is deliberately
silent (no false alarms on the ~14 repos onboarded before the marker existed).

## Why a script, not `bmad-cli install`

CRITICAL: do **not** run `bmad-cli install` / `npx bmad-method install`. The fork's installer now
produces the upstream **v6.8.0 skills layout** (`.claude/skills/bmad-*`), which the fork's custom
layer and `sync-bmad-workflows.sh` do **not** support — a fresh install yields vanilla upstream BMAD
with none of the fork's safety layer. All 14+ existing projects run the **6.0.4 base + custom
overlay** layout instead. `onboard-project.sh` reproduces that layout by cloning the reference
project's `_bmad/` base (`~/.bmad-reference` → the fork's source-of-truth install), sanitizing the
project-specific bits, registering the project in `~/.bmad-targets`, and running the sync.

(The long-term fix — migrating the custom corpus to the v6.8.0 skills layout — is planned separately
in `~/bmad-method-v6/custom/MIGRATION-v6.8-skills-plan.md`. Until that lands, old layout is correct.)

## What the script handles (so you don't have to)

- `git init` (default branch `main`) if the dir isn't a repo yet
- Clones the reference `_bmad/` base; sanitizes `project_name`/`project_phase`; clears the
  reference's sidecar memory + stale sync stamp
- Creates `CLAUDE.md` from the fork template (the sync needs it to exist before it manages sections)
- Adds the project to `~/.bmad-targets` and runs `sync-bmad-workflows.sh`
- **Topology**: detects/records `standalone` vs `fork-of-upstream`; for a fork it records the
  `upstream` remote and adds an "Upstream fork — sync safety" section to `CLAUDE.md`. The destructive
  upstream guard (`bmad-upstream-guard.sh`, a global PreToolUse hook) self-gates on the topology stamp —
  it blocks `git push upstream` / force-push / hard-reset-onto-upstream only in fork repos.
- **Completion marker**: an `onboarding:` stamp in `_bmad/bmm/config.yaml`
  (`playbook_version`/`onboarded_at`/`topology`/`guarantees`), a human-facing `ONBOARDING.md`, and a
  `project-onboarding-done` project memory. The stamp is the machine-checkable source of truth the
  SessionStart detector reads.

## If something looks off

- "reference project has no _bmad" → check `~/.bmad-reference` points at a healthy project.
- The script refuses if `_bmad/` already exists (re-run with `--force` only if re-seeding is intended;
  otherwise the project is already onboarded — just run `sync-bmad-workflows.sh`).
- The fork being a few commits behind upstream does NOT matter here — onboarding sources the base
  from the reference project, not from a fresh installer run.
