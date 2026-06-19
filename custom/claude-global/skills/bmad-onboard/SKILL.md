---
name: bmad-onboard
description: >
  Onboard a new project/directory to the Mason-BMAD fork. Load when the user says any of:
  "install the BMAD fork", "onboard this project to BMAD", "set up BMAD here", "this is a new
  project, install the fork", "wire this directory to the fork", "bootstrap BMAD for this project".
  Runs the deterministic onboarding script — do NOT hand-roll the steps or run `bmad-cli install`.
---

# BMAD fork onboarding

The user wants a new directory wired to the Mason-BMAD fork (`~/bmad-method-v6/`) so it matches all
their other projects — full custom workflow layer, hardened quick-dev, design-* workflows, custom
skills, worktree hooks, slash commands. There is **one command** that does this with no hurdles:

```
~/bmad-method-v6/onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed]
```

## How to run it

1. **Project dir** = the current directory unless the user names another. If they say "we're in a
   new directory now," that directory IS the target — pass nothing (defaults to `$PWD`) or pass it
   explicitly.
2. **Name** defaults to the directory basename; **phase** defaults to `greenfield` (a brand-new
   build). Only override if the user indicates otherwise (e.g. an existing codebase → `brownfield`).
   These are sensible defaults — don't interrogate the user; just state what you're using and run.
3. Run the script. It is idempotent and self-verifying. On success it reports the synced custom
   workflows, skills, hooks, and commands.
4. After it finishes, **the BMAD layer is done.** Then help scaffold the *application* itself
   (framework, deps, env) as a separate step — that is project-specific and not BMAD's job.

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

## If something looks off

- "reference project has no _bmad" → check `~/.bmad-reference` points at a healthy project.
- The script refuses if `_bmad/` already exists (re-run with `--force` only if re-seeding is intended;
  otherwise the project is already onboarded — just run `sync-bmad-workflows.sh`).
- The fork being a few commits behind upstream does NOT matter here — onboarding sources the base
  from the reference project, not from a fresh installer run.
