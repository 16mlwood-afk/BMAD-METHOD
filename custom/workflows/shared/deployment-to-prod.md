---
name: deployment-to-prod
contract_version: 3
description: 'Universal post-merge deployment contract for BMAD-managed projects. Defines the deploy-method modes + fallback ladder an agent resolves before shipping (§1A), the cross-service-payload round-trip "done" clause (§1B), when admin-merge on code PRs is acceptable, what dirty paths block a deploy, how dependency state preconditions are auto-healed, and the exit-code grammar that the bmad-deploy.sh executable uses to signal outcomes. Each project encodes its specifics in `_bmad/bmm/config.yaml` → `deploy:`.'
---

# Deployment-to-Prod Contract

**Why this exists.** Every BMAD-managed project shares the same deploy choreography — merge → fast-forward → build → ship — but the friction points (CI quota exhaustion, dirty BMAD-managed paths, missing `node_modules`) are universal. Codifying the contract once and pushing the executable + the rules into every targeted project removes per-project rule-restating, per-session permission prompts, and the silent divergence that happens when one project's CLAUDE.md learns a lesson and the others don't.

This contract is the sibling of `shared/delivery-to-main.md`: that document covers artifact delivery (markdown to `main`); this one covers code deployment (`main` to production). Both live in top-level `workflows/shared/` because both are universal in scope.

---

## 1. Scope

This contract applies to any project that:

- Has `_bmad/bmm/config.yaml` with a populated `deploy:` block (§5 defines the schema).
- Ships `scripts/bmad-deploy.sh` (synced from the fork via `sync-bmad-workflows.sh`).

A project can opt out by setting `deploy.bmad_contract: skip` in its config. The agent then defers entirely to that project's own CLAUDE.md for deploy rules (see §4 for the skip-mode posture — state-and-stop, never ask).

**Delivery is single-track regardless of deploy mode.** Whether the contract applies or is skipped, code reaches the default branch ONE way: commit → push → **PR** → merge. Never `git merge` a feature branch into a local `main` you don't push — that forks local `main` from `origin/<default-branch>` and the two diverge silently (domain work piling up on an unpushed local `main` while other work ships via PR). Local `main` only moves by fast-forwarding from `origin/<default-branch>`. This is enforced by the `bmad-single-track-guard` hook and owned in prose by CLAUDE.md "ALWAYS Deliver Your Work"; the deploy contract assumes it.

This contract does NOT cover:

- The PR-creation step (CLAUDE.md "ALWAYS Deliver Your Work" still owns commit → push → PR).
- The post-deploy verification step beyond the script's own exit code (smoke tests, sentry checks, etc. — project-level concern).
- Blue/green, canary, or staged-rollout deploys. Those projects opt out and run their own choreography.

---

## 1A. Resolve the deploy METHOD first — modes & fallback ladder

Before any deploy action, resolve **how this project ships** from `deploy.method`. **Do not guess a platform CLI** (`railway up`, `wrangler deploy`) — guessing is exactly what put production *ahead of* `main` with a stranded, unmerged commit (inbound-flow, 2026-06-26: the project auto-deploys on push, yet the agent reached for `railway up`). The deploy MODE decides whether there is even a deploy command to run.

### The three modes (`deploy.method`)

| `deploy.method` | What "deploy" means | Agent action after merge | NEVER |
|---|---|---|---|
| `push_auto` | The platform auto-deploys on push to the default branch. **Merge IS the deploy.** | Confirm the merge pushed and the platform build fired (platform/build dashboard, or the project's status endpoint). Nothing else. | Run a platform CLI deploy — it ships *local* state and diverges prod from `main`. |
| `contract_script` | Run the §3 choreography. | `./scripts/bmad-deploy.sh` from an `origin/<default-branch>`-tip checkout (§3a-stale). | Hand-run the platform CLI in place of the script. |
| `manual_cli` | A platform CLI from a **verified** main-tip checkout (e.g. cash-recovery's `railway up`). | Per §4 posture (owner-gated by default; agent-owned iff `deploy.autonomous: true`), from a fresh `origin/<default-branch>` checkout, after verifying the deploy target (§4 autonomous guard). | `railway up` from a worktree / unlinked / home dir — it can resolve to a *different* prod app. |

If `deploy.method` is **unset**, infer conservatively: `bmad_contract` active → `contract_script`; `bmad_contract: skip` with no documented method → **HALT and state** (*"deploy method undeclared — set `deploy.method` or follow the project's deployment doc"*), never default to a CLI. Setting `deploy.method` explicitly removes the inference.

### The fallback ladder — when the primary method is blocked

The ladder is **method-bounded**: a blocked primary never falls back to a method that diverges prod from `main`.

1. **Primary** = the `deploy.method` action above.
2. **If the primary is unavailable** (auto-deploy webhook didn't fire / script errors / CLI broken): use only the project's *documented* manual trigger **for that same mode** — e.g. a `push_auto` project whose webhook is down is re-triggered via the platform's redeploy, **not** an ad-hoc local `railway up`.
3. **No rung ships un-merged local state.** Production is always downstream of `origin/<default-branch>`, never ahead of it.

### Auth-failure branch — the durable target is `origin/<default-branch>`, always

If GitHub auth breaks mid-deliver (push / PR / merge fails), the commit has **not** reached its durable target. Do **not** substitute a side-channel deploy (`railway up` / `wrangler deploy`) of local state for the missing merge:

- A side-channel deploy makes prod ahead of `main`; the next push-based deploy — or anyone's main-tip deploy — **silently reverts your fix**, and prod now diverges from the source of truth.
- Instead: **fix auth and land the commit on `origin/<default-branch>` first** (re-mint the token / `gh auth login` — surface to the owner if it needs an interactive login), then deploy by the resolved method.
- Order is non-negotiable: **merge to the durable target → then deploy.** Never deploy to cover a merge you couldn't land.

---

## 1B. Cross-service payload changes — "done" includes one verified round-trip

**Why this exists.** §1 scopes general post-deploy verification OUT (smoke tests, sentry checks — project-level concern). This is the one narrow, named exception: a change that crosses a SERVICE boundary via a webhook/event payload. For that class, "deployed on both sides" is NOT "done" — both the sender's and the receiver's unit suites can be green while no real payload ever crossed the boundary correctly (bison-ops `Held` incident, 2026-06-28: sender emitted `pipelineStatus:"Held"`, receiver mapped it to `internalStatus`, both sides deployed, no fresh webhook ever sent; the owner caught it).

**The class.** A change is a *cross-service payload change* when, within one feature, the diff touches a payload BUILDER on the sender repo AND the receiver repo's INGEST of the same field/value. (One side alone changing a shared payload field still qualifies — the unverified side is exactly the rollout-unsafe shape.)

**The added "done" clause.** For a cross-service payload change, the work is not done at deploy-on-both-sides; it is done when, in addition, ONE representative payload has been observed crossing sender→receiver and landing correctly — via `webhook-contract-check` step-05 (a live round-trip, or a synthetic replay of the real field shapes against the receiver's ingest). A handoff or PR that calls the change "verified" without a recorded round-trip is wrong; the disposition is **UNVERIFIED — round-trip owed** until step-05 runs.

**Enforcement (honest ceiling).** Harm here is RECOVERABLE (a mis-emitted value can be re-sent once the receiver tolerates it) and a true live round-trip needs prod-like data the sender repo's CI can't reach — so this is GUIDANCE-grade, not a hard CI gate ("fail CI unless you talk to prod" is un-automatable and over-strong, the indiscriminate-gate anti-pattern). Realistic enforcement is two tiers:

- **Probabilistic halt (ships via this sync):** `webhook-contract-check` step-05 computes the `verified` disposition from evidence and refuses it on `inferred` — real for honesty (you can't hand-wave "verified"), but it only fires if an agent runs the workflow.
- **Deterministic awareness trigger (separate track — NOT shipped by this doc):** a conservative, warn-only signal on the sender repo's payload-builder paths injecting "cross-service payload change → receiver round-trip owed before done." It rides the hook-activation rail (`STD-HOOKACTIVATE-001`), not this contract's sync — authoring this clause does NOT ship the hook. Named here so the invocation gap is on the record, not silently assumed closed.

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

### 3a-stale. Stale-checkout guard (deploy from `origin/<default-branch>` HEAD)

A deploy ships **the build of the current checkout**. If that checkout is behind `origin/<default-branch>`, the build is missing whatever commits landed on the branch since the checkout was taken — and deploying it **silently reverts those commits in production**. This is the parallel-session hazard: a feature worktree branched before another session's PR merged, built, and deployed, rolls back the other PR. (Observed in accounting-tools on 2026-05-30: a deploy from a stale feature worktree rolled back a just-merged worklist redesign; the repo was fine, production served stale code until a redeploy from the branch tip.)

The guard fetches `origin/<default-branch>` (resolved from `deploy.default_branch`, default `main`) and compares **deploy-relevant content** against it. The comparison is a commit-to-commit **tree diff**, not commit ancestry — this is deliberate:

- A freshly **squash-merged** worktree has a HEAD that diverges from `main` *by commit* (the squash is a new commit; the feature commit is orphaned) but is **identical by tree**. An ancestry/`rev-list` check would false-positive and refuse this legitimate deploy; the tree diff passes it.
- A **stale** worktree, missing a merged PR's file changes, differs by tree → refused.

The `deploy.deploy_irrelevant_paths` globs are reused as diff excludes, so a docs-only or `_bmad/`-only delta on `main` does not trip the guard. On a content difference the script exits **19** with the branch-tip redeploy recipe. If `origin/<default-branch>` can't be fetched (offline), the guard is skipped with a warning rather than blocking the deploy.

**Operator rule:** deploy from a checkout at the current `origin/<default-branch>` tip — never from a feature worktree that may be behind it. The cheapest safe path with parallel sessions is a throwaway worktree: `git worktree add /tmp/deploy-head origin/<default-branch> && cd /tmp/deploy-head && ./scripts/bmad-deploy.sh`. Intentional off-`main` deploys go through `deploy-hotfix.sh` or `deploy.bmad_contract: skip`.

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

**Posture under skip — NO per-session deploy question.** A skipped contract means deploy is the project owner's **deliberate, manual step**, not the agent's — so a session must NOT turn it into a recurring end-of-implementation question. After merging a PR to the default branch, **state the deploy status as a fact and STOP**: e.g. *"Merged to `origin/<default-branch>`; undeployed — deploy is the owner's manual step (see the project's CLAUDE.md / deployment doc)."* Deploy ONLY when the owner explicitly asks. The merge is the agent's delivery boundary; the deploy is the owner's. "Want me to deploy?" at the end of every implementation is exactly the friction this posture removes. (When the contract is ACTIVE, the agent runs `./scripts/bmad-deploy.sh` after merge — also no question.)

**Opt-in: agent-owned deploy (`deploy.autonomous: true`).** A project can flip the owner-only posture above by setting `deploy.autonomous: true` in its config. When set, the agent **OWNS the deploy end-to-end and never routes deploy choices/questions back to the owner** — it runs the deploy itself (via its tools, not by asking the owner to run it) and makes the in-flight calls autonomously:

- Deploy from a **fresh `origin/<default-branch>` checkout** (never local `main` — which may be ahead/behind or carry uncommitted cruft).
- **Verify the deploy target before shipping** — the one non-negotiable guard even under full autonomy. (E.g. on Railway, confirm the linked project/service is *this* app before `railway up`; a mis-linked/home-dir checkout can resolve to a *different* production app — the catastrophic footgun.)
- Apply pending **additive** migrations (`CREATE TABLE` / `ADD COLUMN` / `ADD CONSTRAINT` / `CREATE INDEX`) as a separate, idempotent step against the confirmed prod DB.
- **Still gate ONE thing for the owner:** a **destructive** migration (`DROP` / column-narrowing / data backfill / `TRUNCATE`) stops even under autonomy — it can lose data, and the global "never run a destructive migration without asking" rule is not erased by this flag.

This is the explicit override for projects that want hands-off shipping; absent the flag (or with `autonomous: false`), the state-and-stop posture above is the default. The two postures share one DNA — *don't ask the owner* — they differ only on *don't deploy* (default) vs *do deploy* (autonomous).

---

## 5. Config schema — `_bmad/bmm/config.yaml` → `deploy:`

```yaml
deploy:
  # Opt-out switch. When true, bmad-deploy.sh exits 99 and the contract does not apply.
  bmad_contract: skip            # optional; default: contract applies

  # Deploy METHOD (§1A) — how this project ships. Agent-read doctrine; the script does
  # not require it (push_auto / manual_cli are skip-mode for the script — the AGENT acts).
  method: push_auto              # push_auto | contract_script | manual_cli
                                 # unset → inferred per §1A; set explicitly to avoid the inference.

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
19  stale checkout — deploy-relevant content differs from origin/<default-branch> (§3a-stale)
99  skip (bmad_contract: skip)
1   bash error (unexpected)
```

The agent reads the exit code and routes accordingly. 10/14/15/16/17/18/19 are user-fixable (18 = re-mint CLOUDFLARE_API_TOKEN and update ~/.secrets; 19 = redeploy from the current origin/<default-branch> tip). 11/12/13 require investigation. 99 is silent success. 0 is success.

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
- **Resolve `deploy.method` first (§1A)** — `push_auto` (merge IS the deploy; run no CLI), `contract_script` (`./scripts/bmad-deploy.sh` from the project root), or `manual_cli` (platform CLI from a verified `origin/<default-branch>` checkout). Never guess a CLI; production is never ahead of `main`.
- Configuration in `_bmad/bmm/config.yaml` → `deploy:`.
- Project-specific exceptions go above this section as named overrides.
```

---

## 9. Contract evolution

Changes to this document propagate to every targeted project on the next `sync-bmad-workflows.sh` run. Same for `scripts/bmad-deploy.sh`. The per-project `_bmad/bmm/config.yaml` is project-owned and not synced — it accumulates per-project values over time.

Breaking changes (e.g., renaming a config field, removing an exit code) require a migration note appended to this document and a one-line entry in each project's CLAUDE.md memory changelog at sync time. The sync script's `--check` mode surfaces config blocks that would fail validation against the current contract version.

**v2 (2026-06-27) — additive, backward-compatible; no config migration required.** Adds §1A (deploy-method modes + fallback ladder + auth-failure branch) and the optional `deploy.method` field. Existing v1 configs without `method` stay valid — the agent infers the mode per §1A (`bmad_contract` active → `contract_script`; `skip` with no documented method → halt-and-state, never a guessed CLI). The change is **doc/doctrine only**: `bmad-deploy.sh` is unchanged (`push_auto` / `manual_cli` remain skip-mode for the script; the AGENT owns those paths). Recommended (not required): each project sets `deploy.method` explicitly so the mode is legible from config rather than inferred. This closes the "deploy method under-specified for agents" fork-gap — production going *ahead of* `main` via a guessed `railway up` on a push-auto project.

**v3 (2026-06-28) — additive, backward-compatible; no config migration required.** Adds §1B (cross-service payload changes — "done" includes one round-trip verified via `webhook-contract-check` step-05). Doc/doctrine only: `bmad-deploy.sh` is unchanged, no config field added, existing configs stay valid. Closes the "cross-service payload fixes have no mandatory end-to-end round-trip gate" fork-gap on its probabilistic tier (the in-workflow halt + this done-clause); the deterministic sender-side awareness trigger is a separate hook-activation-rail follow-up, named in §1B and the fork-gap, not shipped here.
