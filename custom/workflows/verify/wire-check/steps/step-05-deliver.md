---
name: 'step-05-deliver'
description: 'Commit, push, create PR, and land changes on main. Mirrors quick-dev step-07 delivery sequence.'

nextStepFile: './step-06-handoff.md'
---

# Step 5: Deliver

**Goal:** Land the wire fixes on `main`. Code that isn't merged is code that doesn't exist.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` — Git HEAD at workflow start
- `{handoff_path}` — Source handoff artifact
- `{findings}` — Wire issues that were fixed
- Implementation complete from step-04

---

## DETECT ENVIRONMENT

```bash
git rev-parse --show-toplevel
```

- **Worktree:** If the path contains `.claude/worktrees/`, you are in an isolated worktree.
- **Standard repo:** Normal git workflow applies.

Store as `{is_worktree}`.

---

## PRE-FLIGHT CHECKS

### 1. Type Check

```bash
cd frontend && npx tsc --noEmit
```

If it fails, fix before proceeding.

### 2. Verify No Unintended Changes

```bash
git status
git diff --stat
```

- Confirm only expected files are modified
- Ensure no secrets, `.env` files, or build artifacts are staged

---

## DELIVERY SEQUENCE

### 1. Check Branch Name

If the current branch name is generic, rename it:

```bash
git branch -m fix/wire-check-{slug}
```

### 2. Stage and Commit

Stage all implementation files explicitly (never use `git add .` or `git add -A`):

```bash
git add <file1> <file2> ...
git commit -m "fix: resolve wire-check issues for {slug}"
```

- Reference the wire-check report in the commit message
- Use Conventional Commits format

### 3. Rebase onto Latest Main

```bash
git fetch origin && git rebase main
```

If conflicts arise, resolve them before proceeding.

### 4. Push Branch

```bash
git push -u origin <branch-name>
```

Never use `--no-verify` to skip hooks.

### 5. Create Pull Request

```bash
gh pr create --title "<title>" --body "<body>"
```

- Keep the PR title under 70 characters
- Body should include:
  - **Summary:** Which wires were fixed and how
  - **Wire check report:** Link to the report file
  - **Test plan:** How to verify the fixes

### 6. Merge to Main

> **AUTONOMOUS MODE:** Merge the PR immediately after creation.

```bash
gh pr merge <pr-number> --squash
```

- Use `--squash` to keep main history clean
- Do NOT use `--delete-branch` if in a worktree
- If merge fails, use `--admin` flag. If that also fails, report the error and halt.

### 7. Verify Merge

**If in a worktree:**

```bash
gh pr view <pr-number> --json state,mergeCommit
```

Confirm `state` is `MERGED`.

**If in a standard repo:**

```bash
git checkout main && git pull
git log --oneline -3
```

---

## DO NOT EXIT THE WORKTREE YET — CRITICAL

**Stay in the worktree.** `ExitWorktree` is deferred to the **end of step-06**, after the handoff file is written.

Why: the `PreToolUse` hook on `Edit|Write` hard-blocks file writes when `$PWD` does not contain `/.claude/worktrees/`. Exiting the worktree before writing the handoff file will block step-06.

---

## COMPLETION OUTPUT

```
**Delivered!**

**Branch:** {branch-name}
**PR:** {pr-url}
**Merged:** {yes/no}
**Commit on main:** {merge-commit-hash}

{If auto-deploy: "Deploy triggered from main."}
{If worktree: "Worktree still active — will be removed after step-06 handoff."}
```

---

## DEPLOY — via BMAD contract

After merge, run `./scripts/bmad-deploy.sh` per the BMAD deploy contract (see `_bmad/bmm/workflows/shared/deployment-to-prod.md`). The script reads the project's `_bmad/bmm/config.yaml` → `deploy:` block and decides whether to deploy, skip (`bmad_contract: skip`), or halt. This workflow does NOT carry deploy logic — the contract owns deploy. If the script exits 99 (skip), the project has opted out and follows its own CLAUDE.md deploy choreography.

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/wire-check/steps/step-06-handoff.md`.

---

## SUCCESS METRICS

- All changes committed with meaningful message
- Branch has a descriptive name
- Branch pushed to remote
- PR created with summary and test plan
- PR merged to main (autonomous) or URL presented (non-autonomous)
- Merge verified
- Worktree still active (cleanup happens at end of step-06)

## FAILURE MODES

- Leaving changes uncommitted
- Committing with `git add .`
- Not pushing the branch
- Not creating a PR
- Not merging in autonomous mode
- Calling `ExitWorktree` before step-06 handoff is written
- Force-pushing or skipping hooks
