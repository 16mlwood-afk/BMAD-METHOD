---
name: deployment-to-prod
description: 'Universal post-merge deployment contract for BMAD-managed projects. Defines when admin-merge on code PRs is acceptable, what dirty paths block a deploy, how dependency state preconditions are auto-healed, and the exit-code grammar that the bmad-deploy.sh executable uses to signal outcomes. Each project encodes its specifics in `_bmad/bmm/config.yaml` → `deploy:`.'
---

# Deployment-to-Prod Contract

**Why this exists.** Every BMAD-managed project shares the same deploy choreography — merge → fast-forward → build → ship — but the friction points (CI quota exhaustion, dirty BMAD-managed paths, missing `node_modules`) are universal. Codifying the contract once and pushing the executable + the rules into every targeted project removes per-project rule-restating, per-session permission prompts, and the silent divergence that happens when one project's CLAUDE.md learns a lesson and the others don't.

This contract is the sibling of `shared/delivery-to-main.md`: that document covers artifact delivery (markdown to `main`); this one covers code deployment (`main` to production). Both live in top-level `workflows/shared/` because both are universal in scope.

---

## 1. Scope

This contract applies to any project that:

- Has `_bmad/bmm/config.yaml` with a populated `deploy:` block (§5 defines the schema).
- Ships `scripts/bmad-deploy.sh` (synced from the fork via `sync-bmad-workflows.sh`).

A project can opt out by setting `deploy.bmad_contract: skip` in its config. The agent then defers entirely to that project's own CLAUDE.md for deploy rules.

This contract does NOT cover:

- The PR-creation step (CLAUDE.md "ALWAYS Deliver Your Work" still owns commit → push → PR).
- The post-deploy verification step beyond the script's own exit code (smoke tests, sentry checks, etc. — project-level concern).
- Blue/green, canary, or staged-rollout deploys. Those projects opt out and run their own choreography.

---

## 2. The merge-phase rule (admin-merge on code PRs)

`gh pr merge --admin` is acceptable on a **code-change** PR iff ALL of the following hold:

1. The failing required check is **structurally unavailable** — the documented zero-step quota-exhausted signal: a CI run that completed with `conclusion: failure` and `steps: 0` in under 15 seconds.
2. The agent has run the project's build command locally and it completed clean (no new errors introduced; pre-existing errors documented in `_bmad/bmm/config.yaml` → `deploy.build_baseline_errors` if they need to be allowlisted).
3. The PR's diff has been reviewed by the agent at minimum (no automated `--admin` of unreviewed code).
4. The user has not explicitly disabled the carve-out via `deploy.allow_admin_merge_on_structural_ci_failure: false`.

When the failing check is **substantive** (CI ran steps and failed inside one), `--admin` is **never** acceptable. The rule's intent is to bypass missing CI signal, not real CI signal.

### CI failure classification

| Signal | Class | `--admin` allowed? |
|---|---|---|
| `conclusion: failure`, `steps: 0`, `elapsed < 15s` | Structural (quota exhausted, runner unavailable) | Yes |
| `conclusion: failure`, `steps >= 1` | Substantive (a build/test step actually ran and failed) | No |
| `conclusion: cancelled`, `steps == 0` | Structural (queue cancellation) | Yes |
| `conclusion: timed_out` | Substantive | No |
| `conclusion: skipped` | Inapplicable (no signal either way) | Defer to project config |

The classification logic is encoded in `bmad-deploy.sh` so the agent doesn't have to re-derive it per session.

---

## 3. The deploy-phase rule (dirty tree, deps, build, ship)

`bmad-deploy.sh` runs the following in order. Each step has a defined named exit code (§6) so the agent can route failure deterministically.

### 3a. Dirty-tree filter (deploy-irrelevant paths)

A dirty working tree is rejected by default for safety — running a build with mid-edit files would ship code the author hasn't committed. BUT some dirty paths are universally deploy-irrelevant:

- BMAD-managed paths: `_bmad/`, `.claude/`, `_bmad-output/`
- Local documentation paths: `docs/` (configurable per project)
- Local note paths: `notes/`, `scratch/` (configurable)

A project declares its irrelevant globs in `deploy.deploy_irrelevant_paths`. The script computes the dirty set, subtracts the irrelevant globs, and proceeds iff the remaining set is empty. If non-empty, it exits with code 10 listing the offending paths.

This is the rule that lets `bmad-deploy.sh` run successfully even when the BMAD sync has left the parent checkout dirty — those paths are universally irrelevant to the build.

### 3b. Dep-state precondition

The script checks for a tool that proves dependencies are installed (`deploy.dep_state_check`, defaulting to `node_modules/.bin/<build_tool>`). If missing, it runs `deploy.dep_install_command` automatically. The install command must be **lockfile-clean** (npm: `npm ci`; pnpm: `pnpm install --frozen-lockfile`; yarn: `yarn install --immutable`). The contract pre-authorizes these specific commands because they cannot mutate the lockfile or the package manifest — they only realize the locked state.

Mutating installs (`npm install`, `pnpm install`, `yarn install` without lockfile flags) are NOT pre-authorized and the script will reject them if configured.

If the install fails, the script exits with code 11.

### 3c. Build

The script runs `deploy.build_command`. On non-zero exit, the script exits with code 12.

### 3d. Deploy

The script runs `deploy.deploy_command`. On non-zero exit, the script exits with code 13.

### 3e. Verification

The script captures the deploy command's stdout. If `deploy.success_pattern` is set (a regex), the script asserts the pattern matches stdout. If absent, the script accepts any zero-exit deploy command as success.

---

## 4. Skip path

When the project's deploy is too custom for the contract, set:

```yaml
deploy:
  bmad_contract: skip
```

`bmad-deploy.sh` then exits with code 99 (skip-no-op) and the agent defers to that project's own CLAUDE.md for deploy choreography. The skip is permanent for that project until the config is changed.

---

## 5. Config schema — `_bmad/bmm/config.yaml` → `deploy:`

```yaml
deploy:
  # Opt-out switch. When true, bmad-deploy.sh exits 99 and the contract does not apply.
  bmad_contract: skip            # optional; default: contract applies

  # Platform identifier — informational, used by the script for error messages.
  platform: cloudflare_pages     # vercel | railway | fly | aws_amplify | custom

  # Build phase.
  build_command: npm run build
  build_baseline_errors: 0       # optional; number of pre-existing svelte-check/tsc errors
                                 # that should NOT block deploy. Above this, build fails.

  # Dep-install phase. Both fields are required if the dep-state check might fail.
  dep_state_check: node_modules/.bin/vite   # path relative to project root
  dep_install_command: npm ci               # MUST be lockfile-clean

  # Deploy phase.
  deploy_command: npx wrangler pages deploy .svelte-kit/cloudflare --project-name=my-app
  success_pattern: '✨ Deployment complete'  # optional regex

  # Dirty-tree filter — paths that are dirty-but-deploy-irrelevant.
  deploy_irrelevant_paths:
    - _bmad/
    - .claude/
    - _bmad-output/
    - docs/

  # Merge-phase rule overrides.
  allow_admin_merge_on_structural_ci_failure: true  # default true; set false to disable
  structural_ci_failure_signals:
    - { conclusion: failure, max_steps: 0, max_elapsed_ms: 15000 }
    - { conclusion: cancelled, max_steps: 0 }
```

A project's `deploy:` block is the entire BMAD contract surface. If a field is missing, the script halts with code 14 naming the missing key. If a field is present but malformed, code 15.

---

## 6. Named exit codes

```
0   success — deploy completed
10  dirty tree had real (non-irrelevant) changes
11  dep_install_command failed
12  build_command failed
13  deploy_command failed (non-zero exit OR success_pattern mismatch)
14  required config field missing in _bmad/bmm/config.yaml deploy block
15  config field malformed
16  not a git repo
17  no _bmad/bmm/config.yaml in project root
18  Cloudflare auth pre-flight failed (wrangler deploy targets only; token invalid/expired)
99  skip (bmad_contract: skip)
1   bash error (unexpected)
```

The agent reads the exit code and routes accordingly. 10/14/15/16/17/18 are user-fixable (18 = re-mint CLOUDFLARE_API_TOKEN and update ~/.secrets). 11/12/13 require investigation. 99 is silent success. 0 is success.

The auth pre-flight (§4b in the script) runs only when `deploy.deploy_command` contains `wrangler`, before the build, so an expired token fails in seconds with an actionable message instead of after a full build as a raw wrangler stack trace.

---

## 7. Pre-authorizations

The contract pre-authorizes these operations without per-invocation permission prompts:

- `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable` (lockfile-clean installs only)
- `git diff --quiet` and `git status --porcelain` (read-only working-tree introspection)
- The project's declared `build_command` and `deploy_command`
- `gh pr merge <num> --squash --delete-branch --admin` when AND ONLY WHEN the CI failure classification is structural per §2 (the script does NOT run the admin-merge — the agent does, after the script has run successfully on a local verify pass)

The contract does NOT pre-authorize:

- `npm install`, `pnpm install`, `yarn install` without lockfile flags (those can mutate the manifest)
- `git push`, `git reset --hard`, or anything that mutates remote state beyond the explicit merge step
- Modifying `package.json`, `package-lock.json`, or any non-deploy infrastructure config

---

## 8. Where this lives in each project

After `sync-bmad-workflows.sh` runs:

- `_bmad/bmm/workflows/shared/deployment-to-prod.md` — this document (read-only mirror; agent reads but does not edit).
- `scripts/bmad-deploy.sh` — the executable (read-only mirror; agent runs but does not edit). The script reads `_bmad/bmm/config.yaml` to get project-specific values.
- `_bmad/bmm/config.yaml` → `deploy:` block — the per-project configuration (each project owns its values).

Project CLAUDE.md collapses the deploy-related sections into one pointer block:

```markdown
### Deployment
Deploys follow the BMAD deploy-to-prod contract. See `_bmad/bmm/workflows/shared/deployment-to-prod.md`.
- Run `./scripts/bmad-deploy.sh` from the project root.
- Configuration in `_bmad/bmm/config.yaml` → `deploy:`.
- Project-specific exceptions go above this section as named overrides.
```

---

## 9. Contract evolution

Changes to this document propagate to every targeted project on the next `sync-bmad-workflows.sh` run. Same for `scripts/bmad-deploy.sh`. The per-project `_bmad/bmm/config.yaml` is project-owned and not synced — it accumulates per-project values over time.

Breaking changes (e.g., renaming a config field, removing an exit code) require a migration note appended to this document and a one-line entry in each project's CLAUDE.md memory changelog at sync time. The sync script's `--check` mode surfaces config blocks that would fail validation against the current contract version.
