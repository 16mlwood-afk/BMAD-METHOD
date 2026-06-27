---
title: Fork Gaps — method & infra backlog
description: A running, Claude-noticed backlog of structural gaps in the Mason-BMAD fork and surrounding infra — method-level friction (deploy, hooks, sync, workflow steps, shared state) logged proactively for later investigation.
---

# Fork Gaps — method & infra backlog

A running, **Claude-noticed** backlog of STRUCTURAL gaps in the Mason-BMAD fork and the infra around it — places where the way things are wired makes normal agent work painful. This is *not* a bug tracker: it's for method-level friction (deploy, hooks, sync, workflow steps, shared state), not one-off task bugs.

This doc is **fork-local** (like `global-bmad-workflow.md` / `parallel-work-and-bmad-state.md`): it is not synced into the 13 projects. It is consumed by the fork-maintenance lane — `maintenance-triage` (sibling, production-driven), `orchestrate-workflows`, and the `mason-bmad-workflow-expert` skill.

## How this works
- **Claude logs here proactively** when the method / fork / infra fights an agent — per the global `workflow-friction-and-process-issues` policy. The user shouldn't have to notice the gap or drag it out; catching yourself working *around* the method is the signal to log.
- **No fixed schema.** Each entry is free-form prose: *what fought us · the specific target file/workflow it points at · why it's structural · proposed investigation · rough priority in words.* No severity/category enums — infer the flavour and urgency in prose.
- **Point at a specific target**, never "the fork is awkward." Name the file/workflow/hook that should change.
- Newest at top. Close an entry by marking it `[resolved: <how>]` in place — don't delete it (the history of what got rediscovered is the point).

---

## Open

### `onboard-project.sh --restamp` run from a worktree derives the wrong project identity → `onboard-project.sh`  `[resolved: 2026-06-27 — onboarding playbook v2. The script now resolves a CANON_ROOT (via git --git-common-dir → the MAIN checkout when PROJECT_DIR is a …/.claude/worktrees/<branch>/ worktree) and bases the project name default + the memory slug on it, while in-repo writes still target PROJECT_DIR so they remain committable from the worktree. Restamp-from-a-worktree now derives the canonical name + slug with no --name and no memory relocation. Verified with a REAL git worktree: name=canonical (not the branch), memory at the canonical slug, no worktree-slug leak. onboarding-playbook.version bumped 1→2.]`
**Noticed:** 2026-06-27 (cash-recovery onboarding-marker demo). **Priority: medium** — every `--restamp` on an existing repo is naturally run from a worktree (BMAD artifacts live on main + the parallel-session worktree discipline), which is exactly where the script misbehaves.

**What fought us:** restamping cash-recovery, I ran `onboard-project.sh --restamp` from a fresh worktree (correct per the worktree discipline + because the marker files are tracked and need a PR). The script defaults `PROJECT_NAME` to `basename(PROJECT_DIR)` and derives the memory slug from `PROJECT_DIR` — so it produced `ONBOARDING.md` Project = `chore+onboarding-marker-cash-recovery` and wrote the `project-onboarding-done` memory to a worktree-slug dir (`…-.claude-worktrees-chore+…`) instead of the canonical `-Users-masonwood-code-cash-recovery`. I had to pass `--name cash-recovery` and hand-relocate the memory to the canonical slug + delete the junk dir.

**Why structural:** the script assumes `PROJECT_DIR` IS the canonical repo root, but the fork's own rules push `--restamp` to run from a worktree (`.claude/worktrees/<branch>/`), whose basename and path are not the project's identity. The two outputs that must be canonical — the human-facing project name and the global memory slug — both silently take the worktree's identity. It's the same family as `bmad-artifacts-untracked-main-only`: a BMAD op that must resolve "the real project," not "wherever PWD happens to be."

**Proposed investigation:** in `onboard-project.sh`, resolve the canonical repo root before defaulting `--name`/computing the memory slug — e.g. if `PROJECT_DIR` is under `*/.claude/worktrees/`, walk up to the main checkout (or use `git rev-parse --path-format=absolute --git-common-dir` → the main worktree), and base the slug + name on that. Cheap, and makes restamp-from-a-worktree (the common case) produce canonical output with no `--name` + hand-relocation dance.

### Removing/renaming a shared standard deadlocks the whole sync on "local-only content" → `sync-bmad-workflows.sh`  `[resolved: 2026-06-27 — per-project content-hashed sync manifest (_bmad/_config/sync-manifest.txt, "sha256 TAB relpath"). A target file absent from source is PURGEABLE only if it is in the manifest AND its current bytes match the recorded hash; any divergence (locally edited, absent entry, invalid hash, no manifest, or whole source dir missing) → BLOCKING. Closes the deadlock (a removed standard now propagates as a purge instead of blocking all targets) AND the edited-and-removed fail-open caught in an enforcement-expert review (a delivered-then-locally-edited-then-source-removed file is now protected, not silently deleted). Blocked projects now print the offending file(s) + the --pull/--force remediation. Commits 4a5f590b (base manifest fix) + 92cb6762 (hash hardening); verified 11/11 isolated classifier tests + --check clean across all 15 targets. Bootstrap is fail-closed: no manifest → block (old behavior) until the first sync writes one.]`
**Noticed:** 2026-06-27 (bmad-method-v6, CLAUDE.md-charter session). **Priority: high** — one removed shared file blocks standards delivery to ALL projects until manually cleaned in each.

**What fought us:** the parallel-session charter (`claude-md-charter.md`) synced into 13 projects, then was deleted from the fork source. The next sync did NOT purge the orphaned copies — its anti-clobber safety flagged them as "local-only content" and BLOCKED all 13 projects (`Done: 1 synced, 13 blocked`). The pipeline was dead until I hand-`rm`'d the orphan from every project + the skills mirror.

**Why structural:** the sync can't distinguish "a file that USED to be synced and should now be purged" from "genuine local work to protect." So deleting or renaming any `shared/` standard doesn't propagate the deletion — it deadlocks delivery for every project. Removal/rename is a first-class canon operation (it WILL happen) with no safe path.

**Proposed investigation:** give the sync a memory of what it last delivered (a per-project manifest) so a file in the manifest but absent from source is a *deletion to propagate*, not local content to protect; or a `--purge-removed` mode; or at minimum a per-project "blocked because of `<file>`" message + a one-command remediation instead of a silent 13-blocked.

### Hooks ship unvalidated — a broken hook misfires silently until caught by luck → `docs/hooks-registry.md` + a hook smoke-test  `[resolved: 2026-06-27 — check-hooks-smoke.sh (exit-0 + stdin-contract assertions, incl. a regression case for the friction-reflect stdin bug), wired into .husky/pre-commit]`
**Noticed:** 2026-06-27 (bmad-method-v6). **Priority: medium** — a non-functional safety/awareness hook fails *silent*, which is worse than no hook (false confidence).

**What fought us:** `check-friction-reflect.sh` (Stop hook) was shipped earlier this session with a `python3 - <<PY` pattern that makes the heredoc itself become stdin — so `session_id`/`stop_hook_active` never parsed and it would have fired once GLOBALLY instead of once per session. A manual test "passed" only because its marker masked the bug; it was caught later only because a sibling hook (built next) had the same latent flaw.

**Why structural:** nothing validates a hook before it's wired. A hook that emits invalid JSON, mishandles stdin, or always-no-ops runs (or fails to run) silently every session. The hooks-registry catalogues hooks but never checks they FUNCTION.

**Proposed investigation:** a tiny hook smoke-test — feed each registered hook a representative stdin fixture and assert it exits 0 and emits parseable JSON (or empty). Wire it into the registry / pre-push so a broken hook can't ship. Cheap, and would have caught the friction-reflect bug immediately.

### No collision protection for fork-DIRECT authoring of shared standards/workflows → `parallel-sessions.md` (+ the fork edit-guard allowlist)  `[resolved: 2026-06-27 — awareness tier: check-fork-authoring-collision.sh (PreToolUse nudge when another session has uncommitted shared/ work, per-session ledger avoids self-flagging) + parallel-sessions.md §D (claim-before-authoring protocol + defer-to-most-integrated dedupe convention). A hard reserved-ID/claim ledger remains a heavier future option if the nudge proves insufficient.]`
**Noticed:** 2026-06-27 (bmad-method-v6, during the CLAUDE.md-charter session). **Priority: high** — silent duplication of shared infra is exactly the failure worktrees exist to prevent, and it's currently unguarded for the fork itself.

**What fought us:** two parallel sessions independently authored *the same new standard* into `custom/workflows/shared/` — one as `claude-md-charter.md` / `STD-CLAUDEMD-001`, the other as `claude-md-standard.md` / `STD-CLAUDE-001` (plus duplicate hooks, a `hooks-registry.md`, and STANDARDS.md index edits). Neither knew the other existed until one session happened to re-read STANDARDS.md mid-edit and saw the foreign block. Both were uncommitted, so it was recoverable — but only by luck of a re-read, not by any mechanism.

**Why structural:** fork-direct edits are deliberately **hook-allowlisted** (the project edit-guard skips `~/bmad-method-v6/`, so no `EnterWorktree` is required to edit the fork — by design, per the global rules). That convenience removes the *only* collision protection. And `parallel-sessions.md` covers project `src/` (§A worktree-before-edit) and sprint-status (§C claim ledger), but has **no section for authoring a new shared standard/workflow in the fork** — there is no claim, no "does this standard already exist / is another session writing it" check, no reserved-ID registry. So two cold sessions pointed at the same gap will both build it, duplicate the ID space, and collide in STANDARDS.md.

**Proposed investigation:**
- Add a **fork-authoring coordination** section to `custom/workflows/shared/parallel-sessions.md` (or a fork-local sibling, since this doc syncs): before authoring a new standard/workflow, grep STANDARDS.md + `git status`/recent commits for an in-flight same-topic artifact; claim the intended ID/Home up front. Mirror §C's claim-ledger idea for the `shared/` namespace.
- Consider a lightweight **reserved-ID / in-flight ledger** (even a top-of-STANDARDS.md "being authored" line, or a `SessionStart` note that another session has uncommitted `shared/` changes) so a second session sees the work before duplicating it.
- Revisit whether the fork edit-guard allowlist should at least *warn* (not block) when a second session has uncommitted `custom/workflows/shared/` changes — awareness-tier, consistent with the conservative-hook posture.
- Decide the dedupe convention when it *does* happen (defer-to-most-integrated + fold-in, as recommended this session) so reconciliation isn't re-litigated each time.

**Proposed design (minimal spec — NOT built; build is one coordinated session, hook routes through `enforcement-expert`):**

*Placement:* the procedure does NOT belong in `parallel-sessions.md` — that doc syncs to the 13 and is about project `src/` + sprint-status. Authoring a new shared standard is a **fork-only** act, so the rule lives in the fork-local `docs/global-bmad-workflow.md`, cross-referenced from STANDARDS.md's "author a NEW standard" recipe. Only the hook lives in `~/.claude` (not synced).

- **A — the rule (procedure tier; agent must run it).** Before authoring anything in `custom/workflows/shared/`, a 3-line claim-check: `grep -ri "<topic>" custom/workflows/shared/STANDARDS.md` (already exists?) · `git -C ~/bmad-method-v6 status --porcelain custom/workflows/shared/` + `git log --oneline -10` (in-flight?) · if clear, reserve the ID/Home in the ledger (B) *before writing a line*.
- **B — the in-flight ledger (minimal shape).** A transient claim line at the top of STANDARDS.md under an `<!-- in-flight -->` block, removed when the real index block is committed: `<!-- in-flight: STD-<AREA>-NNN · <topic> · session=<branch-slug|pid> · at=<iso8601> -->`. Co-located in the file everyone greps; visible in `git status` while uncommitted; racing the claim itself still surfaces the other session's line on re-read (deliberate, not lucky). A separate `.in-flight.yaml` is the cleaner-but-nobody-reads-it alternative — start with the in-file comment.
- **C — awareness warning (deterministic-awareness tier; NO gate).** A SessionStart hook in `~/.claude` that, when the session is in/near the fork, runs `git -C ~/bmad-method-v6 status --porcelain custom/workflows/shared/` and on any uncommitted `shared/` change (or a stale in-flight claim) injects one line: *"⚠ another session has uncommitted changes under custom/workflows/shared/ (<files>) — check for in-flight standard authoring before adding one."* Warn-only — a duplicate standard is recoverable, so no PreToolUse deny. **Limit:** SessionStart fires once, so mid-session changes won't re-warn — which is exactly why A's at-author-time check exists (belt = hook at start, suspenders = procedure at the dangerous moment).

*Enforcement honesty:* A is probabilistic (procedure), C is deterministic-awareness (injected, can't be missed at start) but deliberately not a gate. No hard gate — same low-stakes-recoverable call as the CLAUDE.md standard's awareness ceiling.

### Deploy method is under-specified for agents → `deployment-to-prod.md` + project CLAUDE.md deploy notes
**Noticed:** 2026-06-26 (inbound-flow). **Priority: high** — deploy is the last mile of *every* task, so this friction recurs constantly and every agent pays it.

**What fought us:** an agent deployed with `railway up` directly, leaving prod *ahead of `main`* with the commit stranded on an unmerged local branch; it never considered the git-push-auto-deploy path, weighed no fallback ladder, and followed a CLAUDE.md note ("run `railway up` from `inventory-manager/`") that was wrong and cost failed deploys to rediscover. It also didn't connect that this is a *fork* gap — it treated a structural deploy-legibility problem as a one-off session annoyance.

**Why structural:** there is no canonical, agent-legible deploy method + **fallback ladder**, and no "what to do when GitHub auth breaks mid-deliver" branch. So agents reinvent the deploy path each session and sometimes pick a method that diverges prod from `main`.

**Proposed investigation:**
- Define the canonical deploy path per project and a fallback ladder (e.g. git-push auto-deploy → `railway up` from the correct dir → manual), encoded so an agent picks the right one without guessing. Note: inbound-flow is `deploy.bmad_contract: skip` (Railway auto-deploys on push) — yet the agent reached for `railway up`, which is the tell that the method isn't legible from where the agent looks.
- Add an **auth-failure branch**: if GitHub auth breaks, the commit must still reach `main` (the durable target), not just prod via a side-channel `railway up` — otherwise the next git-based deploy reverts the fix.
- Correct the wrong "run `railway up` from `inventory-manager/`" guidance wherever it's copied (likely several project CLAUDE.mds seeded from the fork template).
- Decide whether the deploy method belongs codified **once** in `deployment-to-prod.md` (so it syncs to all ~13 projects) rather than restated — and drifting — per project CLAUDE.md.

### Decision-guiding docs drifted from the sync code → `docs/global-bmad-workflow.md` + `~/.bmad-reference` header + `STATUS.md` migration line + `custom/MIGRATION-v6.8-skills-plan.md`
**Noticed:** 2026-06-27 (cash-recovery session, the v6.8 fleet rollout). **Priority: high** — this drift nearly drove a *destructive* action (reverting the cash-recovery skills pilot).

**What fought us:** the docs an agent reads to decide *what to do* said skills-layout was unsupported and cash-recovery was "cut off from sync / orphaned" (`global-bmad-workflow.md`, `~/.bmad-reference`, and a project memory) — while the sync **code** had already shipped dual-layout delivery (`deliver_skills_layout_project`, commits `c589223c`+). Acting on the docs, the plan-of-record became "revert cash-recovery to commands layout" — i.e. destroy the working pilot. It was caught only by reading the sync source mid-task and noticing the contradiction. Separately, `STATUS.md` + `MIGRATION-v6.8-skills-plan.md` claimed the migration "MACHINERY COMPLETE" while the old-layout-alongside-overlay delivery path for the *other 13* was in fact **unbuilt** (had to build it this session) — "complete" overstated what the code did.

**Why structural:** the fork's narrative docs (reference guard, global workflow, STATUS migration status) are hand-maintained and lag the code, but they are exactly what an agent trusts to choose between *safe* and *destructive* options. Stale "X is unsupported/orphaned/complete" guidance is worse than no guidance — it actively points at the wrong action. There is no check that STATUS's "shipped vs designed" claims match the code, and no signal that a capability doc is behind the sync script.

**Proposed investigation:**
- Make migration/capability status **derivable or checked**, not asserted: e.g. STATUS's "machinery complete" should be gated on the code path actually existing (a smoke test), or phrased as "designed; built: <commit|NO>".
- When the sync code gains a capability (skills-layout delivery), the same commit should update the guard docs (`~/.bmad-reference` header, `global-bmad-workflow.md`) that say it's unsupported — treat them as part of the code's contract surface.
- Add a "verify against code before acting on a destructive recommendation" note where these docs live, since the failure mode is doc-says-revert / code-says-fine.

### Cross-repo project-config edits have no sanctioned path; the edit-guard blocks with nowhere to redirect → edit-guard hook allowlist + `cross-repo-edits` guidance
**Noticed:** 2026-06-27 (cash-recovery session, fleet rollout). **Priority: medium.**

**What fought us:** the fleet rollout legitimately had to edit *other* projects' `_bmad/bmm/config.yaml` (the opt-in key) from a cash-recovery session. The PreToolUse Edit hook hard-blocked it ("not in a worktree") — but there is no worktree of *that other repo* to be in, and the fork's own guidance sanctions bash-driven cross-repo edits. The only way through was routing the edit through `python3`/`rsync` in Bash, which slips past the edit-equivalent guard — i.e. the sanctioned pattern works only by *evading* the guard, which feels like circumvention rather than a blessed path.

**Why structural:** the edit-guard's redirect ("call EnterWorktree") is meaningless for a cross-repo edit — a worktree of the current project doesn't isolate a *different* project. The Edit tool is fully blocked while the Bash path is allowed, so the guard's effect is just to force every cross-repo config touch through bash, with no positive sanctioned route. `cross-repo-edits` describes bash-driven rollouts in prose but the hook offers no Edit-tool affordance for them.

**Proposed investigation:**
- Give the edit-guard a cross-repo affordance: allow (or warn-not-block) Edits whose target resolves *outside the current project root* (it's not the local repo the worktree rule protects), consistent with the bash guard's existing cross-repo carve-out.
- Or document the bash-driven cross-repo edit as the *explicitly blessed* path in `cross-repo-edits` so it doesn't read as guard-evasion.

### Full upstream test suite on every fork push (~5 min/commit) → `.husky/pre-push` + package.json `test`
**Noticed:** 2026-06-27 (cash-recovery session — 4 small fork pushes this session). **Priority: low.**

**What fought us:** each fork `git push myfork custom` runs `npm run test` (test:refs/install/urls/channels + lint + lint:md + format:check + validate:budget) — the entire upstream suite — turning every small `custom/`-only commit into a ~5-minute wait, even when the change touches only fork tooling the suite doesn't cover.

**Why structural:** the fork is a high-iteration shared-infra repo, but the pre-push gate is the full upstream product suite with no fast path for `custom/`-scoped changes. Recurs on every fork delivery.

**Proposed investigation:**
- Consider a scoped pre-push for `custom/`-only diffs (run the budget/ref validators + a lint subset, skip the installer/website/url suites), falling back to the full suite when non-`custom/` paths change. Keep the full suite for upstream-touching commits.

### SessionStart auto-register keys on path, not repo identity → duplicate sync targets for two checkouts of one repo → `src/modules/bmm/_module-installer/assets/hooks.json` (SessionStart auto-register) + `~/.bmad-targets`
**Noticed:** 2026-06-27 (inbound-flow session). **Priority: medium.**

**What fought us:** session start auto-registered `/Users/masonwood/inbound-flow/_bmad/bmm/workflows` to `~/.bmad-targets`, which already contained `/Users/masonwood/code/inbound-flow/_bmad/bmm/workflows` — two **separate working copies of the same git remote** (`16mlwood-afk/inbound-flow`), sitting at different HEADs (`e7c5c1a` vs `b08a2a6`). Both are now first-class sync targets. This is precisely why the session's standards-drift fired: the freshly-registered checkout had never been synced. A no-arg fan-out sync would write the same workflows into both checkouts, which then drift independently and could overwrite uncommitted work in whichever copy isn't active.

**Why structural:** the auto-register dedupe key is the literal filesystem path, not repo identity. Any project a user clones twice (a `/code/` copy + a top-level copy, a worktree-style second checkout) silently becomes two sync destinations — guaranteed recurring drift warnings and a fan-out that double-writes. The registration step has no notion of "this remote is already a target under a different path," so the targets list accretes near-duplicates that no one prunes.

**Proposed investigation:**
- Dedupe at registration on **repo identity** (e.g. `git -C <dir> remote get-url origin` normalized), not the path string: if a target with the same origin already exists, skip-and-note rather than append a second line.
- Or surface a one-line warning at SessionStart when two targets resolve to the same remote, with the prune command — so the user decides which checkout is canonical instead of silently syncing both.
- Decide the intended model for multiple checkouts of one repo: is a second checkout ever a legitimate independent sync target, or always an accident? If always accidental, the auto-register should refuse it; if sometimes intended, the drift check should treat same-remote targets as a set, not independently.
