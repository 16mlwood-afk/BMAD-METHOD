---
name: 'step-07-deliver'
description: 'Commit, push, create PR, and land changes on main. Ensures agent work is never left stranded on an unmerged branch.'

nextStepFile: './step-08-handoff.md'
---

# Step 7: Deliver

**Goal:** Land the implementation on `main`. Code that isn't merged is code that doesn't exist.

**Why this step exists:** Without explicit delivery, autonomous agents finish the review, say "done," and leave code stranded on worktree branches — never committed, never pushed, never merged. This step closes that gap.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)
- Implementation complete, reviewed, and findings resolved

---

## DETECT ENVIRONMENT

Before starting delivery, determine the git environment:

```bash
git rev-parse --show-toplevel
```

- **Worktree:** If the path contains `.claude/worktrees/`, you are in an isolated worktree. The original repo has `main` checked out — you cannot `git checkout main` from here.
- **Standard repo:** Normal git workflow applies.

Store as `{is_worktree}` for use in later steps.

---

## PRE-FLIGHT CHECKS

Before committing, verify the work is ready to ship:

### 1. Run Tests

```bash
npm test
```

- If tests fail: fix failures before proceeding. Do NOT skip this.
- If `tsc` is configured as a pre-push hook, run `npx tsc --noEmit` now to catch type errors early.

### 2. Verify No Unintended Changes

```bash
git status
git diff --stat
```

- Confirm only expected files are modified
- Ensure no secrets, `.env` files, or build artifacts are staged
- Ensure no unrelated changes crept in

---

## DELIVERY SEQUENCE

### 1. Check Branch Name

Worktrees auto-generate branch names that may not be descriptive. If the current branch name is generic (e.g., a random worktree name), rename it before pushing:

```bash
git branch -m <descriptive-branch-name>
```

Use the naming convention: `feat/description`, `fix/description`, `refactor/description`.

### 2. Stage and Commit

Stage all implementation files (be explicit — never use `git add .` or `git add -A`):

```bash
git add <file1> <file2> ...
git commit -m "<type>: <description>"
```

- Use Conventional Commits format: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`
- Message should describe **what** and **why**, not just list files
- If the commit is based on a tech-spec, reference it: `feat: implement <spec-name>`

### 3. Push Branch

Push the feature branch to the remote:

```bash
git push -u origin <branch-name>
```

- The pre-push hook will run `tsc` + `vitest`. If it fails, fix the issue and retry.
- Never use `--no-verify` to skip hooks.

### 4. Create Pull Request

Create a PR targeting `main`:

```bash
gh pr create --title "<title>" --body "<body>"
```

- Keep the PR title under 70 characters
- Body should include:
  - **Summary:** 1-3 bullet points of what changed
  - **Test plan:** How to verify the changes work
- If the workflow was triggered by a tech-spec, link it in the PR body

### 5. Merge to Main

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true` in config, merge the PR immediately after creation. Do not wait for external review.

> **NON-AUTONOMOUS MODE:** Present the PR URL to the user and halt. The user decides when to merge.

**Autonomous merge sequence:**

```bash
gh pr merge <pr-number> --squash
```

- Use `--squash` to keep main history clean
- Do NOT use `--delete-branch` if in a worktree — the local branch is still the worktree's checkout and deleting it causes errors. The remote branch will be cleaned up by `ExitWorktree` or manually.
- If NOT in a worktree, add `--delete-branch` to clean up the feature branch.
- If merge fails (e.g., merge conflict with main), report the error and halt — do not force-push or force-merge

### 6. Verify Merge

Confirm the change landed on main:

**If in a worktree (`{is_worktree}` = true):**

You cannot `git checkout main` from a worktree (main is checked out in the original repo). Instead verify via the GitHub API:

```bash
gh pr view <pr-number> --json state,mergeCommit
```

- Confirm `state` is `MERGED`
- Note the `mergeCommit` hash

**If in a standard repo:**

```bash
git checkout main && git pull
git log --oneline -3
```

- Verify your commit appears in main's history

In both cases: if the project auto-deploys from main (e.g., Railway), note that deployment is triggered.

---

## DO NOT EXIT THE WORKTREE YET — CRITICAL

**Stay in the worktree.** `ExitWorktree` is deferred to the **end of step-08**, after the handoff file is written.

Why: when parallel sessions are detected, the `PreToolUse` hook on `Edit|Write` hard-blocks file writes whenever `$PWD` does not contain `/.claude/worktrees/`. If you exit the worktree here, you land back in the main repo and step-08's handoff file write gets blocked — the agent then either stalls or wastes time re-entering a fresh worktree. Both are timing bugs the workflow has hit before. Avoid them by leaving cleanup until after the handoff file is on disk.

There is **no** "WORKTREE CLEANUP" in this step. Do not call `ExitWorktree` here under any circumstances. The cleanup section lives at the bottom of step-08.

---

## COMPLETION OUTPUT

```
**Delivered!**

**Branch:** {branch-name}
**PR:** {pr-url}
**Merged:** {yes/no — pending user review}
**Commit on main:** {merge-commit-hash}

{If auto-deploy: "Railway deployment triggered from main."}
{If worktree: "Worktree still active — will be removed after step-08 handoff."}
```

---

## NO POST-MERGE USER HANDOFFS — CRITICAL

**Never end the workflow by queuing the user with commands to run after deployment.** No "Next step (you run, after Railway deploys): ..." sections. No `source ~/.secrets && npx tsx scripts/...` blocks for the user to execute. No verification scripts the user is expected to kick off.

If a script needs to run after deploy (a backfill, a rearm, a dry-run + apply, a sanity query), there are exactly two acceptable options:

1. **Run it yourself in this session.** Wait for the deploy if needed (poll `railway logs` or the relevant endpoint), then execute the dry-run, then the apply. Report what happened. This is the default.
2. **Don't mention it.** If running it yourself isn't possible (missing credentials, requires a human decision, the script doesn't exist yet), simply don't list it. Capture it in the step-08 handoff under "Recommended Follow-ups" as a written description (not a copy-pasteable command block) so it lands in the artifact, not the chat.

Why: the user does not want a queue of post-deploy chores at the end of every shipping session. Either the work is done in-session, or it goes in the handoff file. Never in the completion output.

**Examples of what this rule forbids:**

```
# FORBIDDEN
Next step (you run, after Railway deploys):
  source ~/.secrets
  npx tsx scripts/rearm-stuck-listing-check-403.ts --dry-run
  npx tsx scripts/rearm-stuck-listing-check-403.ts
```

**What to do instead:**

```
# CORRECT — run it yourself
[Claude runs `railway logs` until new deploy is live, then executes the dry-run, then the apply, then reports counts.]

# CORRECT — record in handoff if you can't run it
[Claude writes it as a follow-up in handoff-*.md with rationale and rough size, no command block.]
```

---

## DEPLOY — via BMAD contract

After merge, run `./scripts/bmad-deploy.sh` per the BMAD deploy contract (see `_bmad/bmm/workflows/shared/deployment-to-prod.md`). The script reads the project's `_bmad/bmm/config.yaml` → `deploy:` block and decides whether to deploy, skip (`bmad_contract: skip`), or halt. This workflow does NOT carry deploy logic — the contract owns deploy. If the script exits 99 (skip), the project has opted out and follows its own CLAUDE.md deploy choreography.

---

## NEXT STEP

Delivery is done but the workflow is not complete. Proceed immediately to the developer handoff:

**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-08-handoff.md`

**CRITICAL:** Do NOT skip the handoff. Observations from implementation are perishable — if you don't capture them now, they're lost.

---

## SUCCESS METRICS

- All changes committed with meaningful message
- Branch has a descriptive name (not a random worktree ID)
- Branch pushed to remote
- PR created with summary and test plan
- PR merged to main (autonomous) or URL presented (non-autonomous)
- Merge verified via `gh pr view` (worktree) or `git log` (standard)
- Worktree still active (cleanup happens at end of step-08, not here)

## FAILURE MODES

- Leaving changes uncommitted after step-06
- Committing with `git add .` (may include secrets or junk)
- Not pushing the branch (commit exists locally only)
- Not creating a PR (branch pushed but no merge path)
- Not merging in autonomous mode (PR created but abandoned)
- Force-pushing or skipping hooks to work around failures
- Running `git checkout main` inside a worktree (will fail)
- Using `--delete-branch` inside a worktree (breaks the checkout)
- **Calling `ExitWorktree` at the end of step-07.** The `PreToolUse` hook will then block the step-08 handoff file write because `$PWD` is no longer inside `/.claude/worktrees/`. Cleanup belongs at the end of step-08, not here.
- Not verifying the merge landed on main
- Declaring workflow complete without producing a handoff (step-08)
- **Outputting a "Next step (you run, after Railway deploys): ..." block or any other post-deploy command queue for the user.** Run it yourself, or put it in the handoff file — never in the completion output.
