---
name: delivery-to-main
contract_version: 2
description: 'Shared policy for producer workflows that emit artifacts intended to be readable on the repository default branch. Closes the gap between "file written to disk" and "file accessible to external consumers (Claude Design, downstream synthesize, design-implement) via origin/<default-branch>". Referenced by design-handoff (step-04-deliver), design-synthesize, design-artifact-loop, design-tuning.'
---

# Delivery-to-Main — Producer Policy

**Why this exists.** A producer workflow (design-handoff, design-synthesize, …) emits an artifact intended for an external consumer that fetches from GitHub. Today the producer ends at "file written to `{output_path}`". The consumer's instructions say "read this file from `main`". Without an explicit commit/push/PR step, the file lives only on the operator's local disk — the consumer cannot find it.

Observed failure mode (2026-05-28, `design-brief-refine-amazon-transactions-2026-05-28.md`): Claude Design was handed the brief URL, read `origin/main`, did not find the file, and produced a hallucinated "196 files in project root" complaint instead of failing cleanly. The brief itself was correct; the producer had simply not delivered it to the location the consumer reads from.

This policy closes that gap. Every producer workflow that emits an artifact whose hand-off prompt references `main` MUST run delivery-to-main before declaring success.

---

## 1. Scope

Delivery-to-main applies when ALL of:

- The producer emits a file to `{implementation_artifacts}` or `{planning_artifacts}` (artifact, brief, handoff, bundle, screen-review, design-response).
- The producer surfaces a hand-off prompt that names a `main`-branch URL, OR the file is intended to be consumed by a downstream workflow that reads `main`.

If both are true, the producer must run the delivery sequence in §3 before its final "Present to User" step.

Delivery-to-main does NOT apply when:

- The artifact is purely local (debugging state, scratch output, exploratory).
- The producer is in a project explicitly configured `delivery: skip` in `{main_config}` (some teams ship via a different mechanism — manual review, internal mirror, etc.).
- The user has passed `--no-deliver` to the workflow invocation.

---

## 2. Constraints

- **Never push directly to `main`.** Even for doc-only artifacts. The PR is the audit trail; the operator can self-approve and merge but must NOT bypass the PR shape.
- **Respect the project's branch-naming convention.** Most synced projects use `<type>/<short-description>` (`docs/`, `feat/`, `fix/`, `refactor/`, `chore/`). When inside a worktree with an auto-generated branch name (`worktree-*`), rename before pushing per `worktree-portability.md`. For brief/screen-review/bundle deliveries, `docs/` is the conventional type.
- **Doc-only PRs may bypass branch-protection checks when CI is structurally broken.** A delivery PR for an artifact in `_bmad-output/` does not change runtime behaviour. If branch protection requires a check that is structurally unavailable (GH Actions quota exhausted, zero-step CI run), `gh pr merge --admin` is acceptable — the project's `CLAUDE.md` should document this escape; the delivery policy permits it.
- **Co-author the commit honestly.** Producer-generated commits cite the workflow that ran them.

---

## 3. Delivery sequence

When a producer reaches its "write artifact" step in a worktree session:

1. **Verify the artifact is inside the active worktree** (per `worktree-portability.md` §2). If not, halt — the artifact must land inside the worktree before delivery, otherwise the merge will not include it.

2. **Stage and commit the artifact** to the worktree's branch.

   **Stage with `git add -f`, then assert it staged.** Most consuming projects gitignore `/_bmad-output/` (the `bmad-artifacts-untracked-main-only` posture), so a plain `git add <artifact>` is silently rejected as ignored — nothing stages, the commit reports "no changes", and the push ships an **empty branch that looks delivered**. The force flag is required precisely because the artifact is delivery-bound but lives under a gitignored path. After staging, verify and halt loudly if it didn't take:

   ```bash
   git add -f <artifact>           # -f is mandatory: the path is gitignored
   git diff --cached --name-only | grep -qF "$(basename <artifact>)" || {
     echo "HALT: artifact not staged — path is gitignored, re-run with: git add -f <artifact>"; exit 1;
   }
   ```

   Then commit. Commit message format:

   ```
   <type>(<workflow-name>): <one-line description>

   <2-4 line body explaining what the artifact represents and how it fits
   into the chain. Cite the consumer that will read it.>

   Co-Authored-By: <workflow-name> via Claude Code
   ```

   Where `<type>` matches the artifact class:
   - briefs / screen-reviews / handoffs / design-responses → `docs(<workflow-name>)`
   - bundles (design-synthesize outputs) → `design(<feature-slug>)`
   - tech-specs (maintenance-triage) → `feat(<workflow-name>)`

3. **Rename the worktree branch** if it carries an auto-generated `worktree-*` name. Use `<type>/<short-description>` matching the commit type.

4. **Push the branch** with upstream tracking: `git push -u origin <branch-name>`.

5. **Open a PR** to the default branch (`main` for most projects). PR title matches the commit subject; PR body summarises what the artifact is, what consumer reads it, and any test-plan items the operator should verify after merge.

6. **Attempt to merge.** Prefer `gh pr merge <num> --squash --delete-branch`. If branch protection blocks AND the artifact is doc-only (no files under `src/`, `migrations/`, `wrangler.toml`, `package.json`, etc.), retry with `--admin` per the project's quota-exhausted escape clause.

7. **Verify remote merge state.** `gh pr merge` may report a local error after a successful remote merge (when the parent worktree has `main` checked out — see `worktree-portability.md` §1). Confirm via `gh pr view <num> --json state,mergedAt,mergeCommit`. `"state": "MERGED"` is authoritative.

8. **Fast-forward main from the parent worktree.** This brings the artifact under tracked state in the main checkout so subsequent sessions can see it. Per the project's `CLAUDE.md`, untracked-files-block-pull recipe applies if needed.

9. **Surface the merged URL to the user.** The hand-off prompt now references a file that exists on `main` — the consumer (Claude Design, downstream workflow) can read it.

10. **Exit the worktree** with `action: "remove"` once the PR is merged. Per project `CLAUDE.md`, `discard_changes: true` is required when squash-merges leave the worktree's source commit orphaned (different hash on `main`) — this is the normal case for squash, not a sign of unmerged work.

---

## 4. Failure modes

- **Pushed but did not merge.** The branch is on origin but the PR is open. Consumer reading `main` does not see the artifact. Either merge the PR or update the hand-off prompt to reference the branch URL (`/blob/<branch>/...` instead of `/blob/main/...`) so the consumer can find it.
- **Merged but did not fast-forward.** The artifact is on `origin/main` but the local main checkout is one commit behind. Subsequent local-session work that lists `{implementation_artifacts}` will not see the artifact until pull. Always run step 8.
- **Bypassed delivery entirely.** Workflow ended at "file written to disk" without running this sequence. Consumer fails to find the file on `main`. This is the gap this policy exists to close — any producer that ends without delivery has not completed its job.

---

## 5. Skipping delivery

For workflow invocations that genuinely do not need delivery (local exploration, scratch outputs, the user knows the artifact won't be consumed externally), pass `--no-deliver` to the workflow OR set `delivery: skip` in `{main_config}`. When skipped, the producer must surface a warning at the end of its run:

```
⚠️  Delivery skipped (--no-deliver). The artifact at <path> exists only
   in this worktree. External consumers reading origin/main will not
   find it. To deliver later, run: <workflow-name> --deliver-only --path <path>
```

This makes the skip auditable — the user opted out, not the workflow.

---

## 6. Configuration in projects

Projects synced from the fork inherit this policy. They may opt out per workflow by adding to `_bmad/bmm/config.yaml`:

```yaml
delivery:
  design-handoff: skip      # do not auto-deliver design-handoff artifacts
  design-synthesize: skip   # do not auto-deliver synthesize bundles
  # ... etc
```

Default for all workflows is `auto` (run the §3 sequence). Opt-out is per workflow, not project-wide, so a project can deliver briefs but not synthesize bundles, etc.

If the user has not configured `delivery:` at all, treat as fully `auto` for every producer workflow.
