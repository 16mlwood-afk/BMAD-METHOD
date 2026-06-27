---
name: 'step-04-deliver'
description: 'Deliver the brief to the repository default branch so external consumers (Claude Design, downstream synthesize, design-implement) can read it. Implements shared/delivery-to-main.md for design-handoff.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-handoff'
thisStepFile: './step-04-deliver.md'
---

# Step 4: Deliver

**Goal:** Commit the brief written in step-03, push the worktree branch, open a PR, and merge to `main` so external consumers can read the brief at its hand-off URL. Without this step, the brief lives only on the operator's local disk and the consumer cannot find it.

This step implements `shared/delivery-to-main.md` for `design-handoff`. The shared policy carries the full rationale; this step is the executable form.

---

## AVAILABLE STATE

From step-03:
- `{output_path}` — absolute path to the brief on disk
- `{output_filename}` — basename of the brief
- `{output_path_relative_to_repo_root}` — for PR body / hand-off prompt
- `{github_repo_url}` — for verification
- `{feature_name}`, `{target_slug}`, `{handoff_mode}` — for commit / PR text

From step-03b (only when `{has_analytics_band}` is `true`):
- `{rationale_output_path}` — absolute path to the analytics rationale on disk
- `{rationale_path_relative_to_repo_root}` — for the final surface
- If `{has_analytics_band}` is `false`, no rationale file exists — every "rationale" reference below is a no-op.

From config:
- `{delivery_mode}` — `auto` (default) or `skip` (from `_bmad/bmm/config.yaml`'s `delivery.design-handoff` field, if set)
- `{user_name}`

---

## EXECUTION SEQUENCE

### 1. Delivery Skip Check

Determine whether to run the delivery sequence at all.

```bash
# Read delivery config from _bmad/bmm/config.yaml — look for:
#   delivery:
#     design-handoff: skip
```

Resolve `{delivery_mode}`:
- If the user's invocation contains `--no-deliver` → `{delivery_mode}` = `skip`
- Else if `_bmad/bmm/config.yaml` has `delivery.design-handoff: skip` → `{delivery_mode}` = `skip`
- Else → `{delivery_mode}` = `auto`

If `{delivery_mode}` = `skip`, emit the warning from `shared/delivery-to-main.md` §5 and exit step-04. The brief stays on disk in the worktree; the operator is on the hook for delivery later.

If `{delivery_mode}` = `auto`, proceed to step 2.

### 2. Verify Worktree Containment

Per `shared/worktree-portability.md` §2, the brief must be inside the current worktree before delivery — otherwise the PR will not include it.

```bash
project_root=$(git rev-parse --show-toplevel)
case "{output_path}" in
  "${project_root}"/*) : ;;  # ok — brief is inside the worktree
  *) halt with shared/worktree-portability.md §4 diagnostic ;;
esac
```

### 3. Stage and Commit the Brief

Stage the brief, and the rationale too when one was written (`{has_analytics_band}` is `true`) — both belong in the same commit so a brief on `main` always has its rationale beside it.

**Use `git add -f`.** Most projects gitignore `/_bmad-output/` (the `bmad-artifacts-untracked-main-only` posture), so a plain `git add` of a brief is silently rejected as ignored — it stages nothing, the commit reports "no changes", and the push ships an EMPTY branch that looks delivered. The `-f` flag is mandatory for delivery-bound artifacts under a gitignored path. (See `shared/delivery-to-main.md` §3.)

```bash
git add -f {output_path}
# Only when {has_analytics_band} is true:
git add -f {rationale_output_path}
```

**Assert the stage actually happened** — turn the silent no-op into a loud, self-correcting halt:

```bash
git diff --cached --name-only | grep -qF "$(basename {output_path})" || {
  echo "HALT: brief did not stage. The path is gitignored — re-run with: git add -f {output_path}"; exit 1;
}
```

Do not proceed to commit until the brief is confirmed staged.

Compose the commit message. Use this template (HEREDOC form to preserve formatting):

```bash
git commit -m "$(cat <<'EOF'
docs(design-handoff): {handoff_mode} brief for {feature_name}

{2-3 line description: what the brief is, what consumer will read it, what scope it covers.
For refine-screen briefs: cite the screen-review artifact this brief derives from.
For fresh-design briefs: cite the feature scope and target route.
If {has_analytics_band} is true: add a line noting the commit also includes the analytics presentation rationale (design-rationale-{target_slug}-{date}.md) — the record-of-decision behind the page-mode/band/archetype choices.}

Co-Authored-By: design-handoff workflow via Claude Code
EOF
)"
```

If a pre-commit hook fails on this commit, the brief itself is unlikely to have caused it (markdown in `_bmad-output/`). Read the hook output, fix the underlying issue, re-stage, and create a NEW commit per the project's commit guidance.

### 4. Rename the Worktree Branch (if auto-generated)

Worktrees created via `EnterWorktree` start on an auto-generated name like `worktree-<random>`. Rename before pushing so the PR carries a meaningful identifier.

```bash
current=$(git branch --show-current)
case "$current" in
  worktree-*)
    new_name="docs/design-brief-{target_slug}"
    git branch -m "$new_name"
    ;;
esac
```

If the branch is already conventionally named (`docs/...`, `feat/...`, etc.), skip the rename.

### 5. Push the Branch

```bash
git push -u origin "$(git branch --show-current)"
```

This sets the upstream tracking branch. Per project `CLAUDE.md` pre-push hook conventions: pushes to non-main branches skip the build check; pushes to `main` are blocked entirely (the delivery flow goes through PR).

### 6. Open the PR

Compose the PR body using this template (HEREDOC form):

```bash
gh pr create --title "docs(design-handoff): {handoff_mode} brief for {feature_name}" --body "$(cat <<'EOF'
## Summary

- {1-2 line description of what this brief is}
- {Consumer that will read it (Claude Design, design-synthesize, design-implement)}
- {Scope: refine-screen V1-V3 with edge-state variants, OR fresh-design with N open questions}
- {If {has_analytics_band} is true: "Includes an analytics presentation rationale (design-rationale-…) — a human-facing record of WHY the page-mode/band/archetype were chosen. Not a design input; Claude Design reads the brief only."}

## Why this is doc-only

Brief lives in `_bmad-output/implementation-artifacts/` — BMAD workflow artifact directory, not source, not build input. No code touched, no schema touched, no runtime impact. Safe to merge without deploy.

## Test plan

- [ ] Brief renders as readable Markdown on the PR diff
- [ ] Once merged, the consumer can read `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
- [ ] No deploy needed — doc-only change, no runtime impact. The BMAD deploy contract (`./scripts/bmad-deploy.sh`) would also no-op on this PR

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Capture the PR number from the `gh pr create` output as `{pr_number}`.

### 7. Merge the PR

Prefer the standard squash-merge:

```bash
gh pr merge {pr_number} --squash --delete-branch
```

If branch protection blocks the merge AND the failing check is structurally unavailable (GH Actions quota exhausted, zero-step CI failure — see project `CLAUDE.md` "CI Health Check"), retry with admin override:

```bash
gh pr merge {pr_number} --squash --delete-branch --admin
```

The `--admin` escape is acceptable here because the brief is doc-only — no runtime impact. **Never use `--admin` to bypass real CI signal.** The condition for `--admin` is:
- The brief is in `_bmad-output/` (doc-only), AND
- The failing check is structurally unavailable, not substantively failing.

If both conditions are not met, halt and surface to the user.

### 8. Verify Remote Merge State

`gh pr merge` may report a local error after a successful remote merge (when the parent worktree has `main` checked out). Confirm the merge via remote state:

```bash
gh pr view {pr_number} --json state,mergedAt,mergeCommit
```

If `"state": "MERGED"`, the delivery succeeded. The local error from step 7 (if any) is non-blocking and unrelated to merge success.

If `"state": "OPEN"` and step 7 errored, the merge actually failed — surface the gh output and halt.

### 9. Fast-Forward Main from the Parent Worktree

The artifact is now on `origin/main`, but the local main checkout (outside this worktree) is one commit behind. Pull it forward so subsequent sessions see the artifact under tracked state.

```bash
# Run from the parent worktree (NOT the current worktree, which is on the now-deleted branch)
cd {parent_repo_root}
git fetch origin main
git pull --ff-only origin main
```

If `git pull` blocks on untracked files in `_bmad-output/` matching the brief's path, follow the project `CLAUDE.md` recipe — move blocking files to `.claude/orphaned-main-commits/<stamp>/`, then re-pull.

### 10. Surface Delivery Result to User

Emit the final hand-off block:

```
✓ Brief delivered to main.

  PR:           {pr_number} ({pr_url}) — MERGED
  Brief on main: {github_repo_url}/blob/main/{output_path_relative_to_repo_root}
  {If {has_analytics_band} is true, add:}
  Rationale:    {github_repo_url}/blob/main/{rationale_path_relative_to_repo_root}
                (why the analytics presentation was chosen — read this, don't hand it to Claude Design)

To hand off to {consumer}:
  "Connect to {github_repo_url} and read {output_path_relative_to_repo_root}
   on main. [consumer-specific instructions from step-03 §5...]"
```

### 11. Exit the Worktree

Per project `CLAUDE.md`, exit the worktree once the PR is merged. The squash-merge leaves the worktree's local commit orphaned (different hash from the merged squash on main) — this is normal, not a sign of unmerged work.

```
ExitWorktree action: "remove" discard_changes: true
```

`discard_changes: true` is required because the worktree's local commit is orphaned-by-squash; the content is on `main` under a different hash.

---

## RULES

- Step-04 only runs when `{delivery_mode}` = `auto`. Skip-mode emits the warning and exits at step 1.
- Never push directly to `main`. Always via PR.
- `--admin` merge is allowed only for doc-only artifacts with structurally-unavailable CI. Document the override in the PR thread or session log.
- The merged-URL surfaced in step 10 MUST be the URL the consumer will actually read. If the operator chose `--no-deliver`, the warning says so — do not pretend the file is on main.

---

## FAILURE MODES

- **Skipped step-04 entirely.** Brief on disk, consumer can't find it. The producer has not finished its job.
- **Pushed but did not merge.** Branch on origin, PR open. Consumer fails to find the file on `main`. Either complete the merge or update the hand-off prompt to reference the branch URL.
- **Used `--admin` for a non-doc-only PR.** Bypasses real CI signal. The escape exists for structurally-broken-CI + doc-only — not for "I want to skip review."
- **Forgot to fast-forward main.** Local main checkout is behind origin/main. Subsequent local-session reads of `{implementation_artifacts}` don't see the brief until pull. Always run step 9.
- **Reused a worktree-* branch name in the PR.** Reader of the PR list sees a meaningless identifier. Always rename per step 4.
