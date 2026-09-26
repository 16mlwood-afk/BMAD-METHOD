---
---

# Step 3: Implement

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- No human interaction: do not ask questions or wait for approval in this step.
- Content inside `<intent-contract>` in `{spec_file}` is read-only. Do not modify.

## WORKTREE ISOLATION (safety layer rule 6 — do this FIRST, before PRECONDITION)

dev-auto edits tracked files and commits, **unattended**, on a repo other sessions may be editing concurrently. Per `{project-root}/_bmad/bmad-shared/parallel-sessions.md` §A1, **enter an isolated worktree from local `main` BEFORE any edit**, then resolve `{project-root}` via `git rev-parse --show-toplevel` (`worktree-portability.md` §1) so every path is worktree-relative. Everything below (BASELINE, edits, and the step-04 gated commit) happens INSIDE this worktree — never on a shared checkout.

**Unattended variant of §A:** §A tells an interactive workflow to integrate the advancing `main` before delivery and RESOLVE the named collision classes. dev-auto has no human to resolve a genuine conflict, so: attempt the §A integrate/resolve; if a collision is NOT one of the auto-resolvable classes (barrel re-exports · additive schema tables · dual-`0001` migrations · sprint-status per-key), HALT with status `blocked`, blocking condition `worktree integration conflict (needs human)` — never force or guess a merge. If `EnterWorktree`/worktrees are unavailable, HALT `blocked` with `no worktree isolation` rather than edit a shared checkout.

## PRECONDITION

Verify `{spec_file}` resolves to a non-empty path and the file exists on disk. If empty or missing, HALT with status `blocked` and blocking condition `missing spec_file before implementation`.

## BASELINE

Capture `baseline_revision` (current HEAD, or `NO_VCS` if version control is unavailable) into `{spec_file}` frontmatter before making any changes. This is the anchor for the step-04 diff, the regression-surface gate, and the rollback path.

---

## PRE-FLIGHT: EXISTING-CODE PROVENANCE CHECK (safety layer rule 4)

**Trigger:** Run this whenever the planned tasks **modify or remove existing code** — a condition, guard, branch, default, constant, or any line already in the tree. It does NOT apply to pure additions.

A line that looks redundant, over-cautious, or "obviously simplifiable" is the single most dangerous thing to delete: it may be a deliberate guard added to fix a specific past bug, and removing it silently re-opens that bug. The author's reason is rarely in the line itself — it lives in the commit that introduced it. An unattended loop has no human to notice the regression before it commits, so this check is mandatory here, not advisory.

### 1. Trace the provenance of the lines you intend to change

Before editing, for each non-trivial line you plan to modify or delete:

```bash
git log -S '<exact code fragment>' --oneline -- <path>   # commits that added/removed this exact text
git log -L '<start>,<end>:<path>' --oneline               # or line-range history
git blame -L '<start>,<end>' <path>                        # who/when -> find the commit
```

Then **read the originating commit message and diff** (`git show <sha>`).

### 2. Classify: deliberate vs incidental

- **Incidental** — the line arrived with a bulk move, scaffold, or unrelated change; the commit says nothing about *why this line exists*. Lower risk to change.
- **Deliberate** — the commit message or its PR explains the line as a guard/fix/workaround for a specific case ("fix:", "guard against…", a linked issue, a regression test added alongside it). **Treat it as load-bearing until proven otherwise.**

### 3. For deliberate code, understand the intent before you implement

- Read the commit (and any test it added) until you can state, in one sentence, **what case the code protects**.
- Confirm your change **extends** that intent rather than regressing it: *does the case the original commit protected still hold under my change?*
- If the original guard relied on an assumption that is now wrong, state the **corrected invariant** explicitly and verify your change still covers the original's protected case (via the existing test, or a new one).

### 4. If your change would undo a deliberate guard (unattended rule)

Because there is no human to confirm: **proceed only if you can show the protected case is still covered** — a passing test that exercises it, or a new test you add in this change. Record the originating commit SHA + the preserved invariant in the spec's `## Design Notes` (and carry it into the step-04 commit message), so it lands in the audit trail. **If you cannot show coverage, HALT with status `blocked` and blocking condition `would undo a deliberate guard without coverage`.** Never silently delete it to keep the loop moving.

### 5. Skip condition

Skip if the tasks touch no existing lines (pure addition), or if `project_phase: greenfield` and the touched code has no production consumers.

---

## IMPLEMENT

Change `{spec_file}` status to `in-progress` in the frontmatter before starting implementation.

If `{spec_file}` has a non-empty `context:` list in its frontmatter, load those files before implementation begins. When handing to a subagent, include them in the subagent prompt so it has access to the referenced context.

Hand `{spec_file}` to an implementation subagent. **The subagent prompt MUST carry the existing-code provenance discipline above** — instruct it to trace the originating commit for any existing line it modifies or removes, to treat deliberate guards as load-bearing, and to report (back to you) the originating SHA + preserved invariant for any guard it touched. A subagent that cannot show the protected case is still covered must report that rather than delete the guard.

**Path formatting rule:** Any markdown links written into `{spec_file}` must use paths relative to `{spec_file}`'s directory so they are clickable in VS Code. Any file paths displayed in terminal/conversation output must use CWD-relative format with `:line` notation (e.g., `src/path/file.ts:42`) for terminal clickability. No leading `/` in either case.

## Tasks & Acceptance Verification

After the implementation subagent returns, verify every task in the `## Tasks & Acceptance` section of `{spec_file}` is complete and every acceptance criterion is satisfied. Mark each finished task `[x]`. If any task is not done or any acceptance criterion is not satisfied, finish the missing work before proceeding. If the missing work cannot be completed, HALT with status `blocked`, blocking condition `implementation verification failed`, and include the unfinished task or failing acceptance criterion and reason.

## NEXT

Read fully and follow `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-04-review.md`
