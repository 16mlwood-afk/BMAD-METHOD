---
name: 'step-06-handoff'
description: 'Developer handoff — document wire fixes, observations, and worktree cleanup. Mirrors quick-dev step-08.'
---

# Step 6: Developer Handoff

**Goal:** Document what was found, what was fixed, and any remaining observations. Then clean up the worktree.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` — Git HEAD at workflow start
- `{handoff_path}` — Source handoff artifact
- `{wires}` — Complete wire inventory
- `{findings}` — Wire issues that were fixed
- Implementation delivered and merged

---

## WHAT TO CAPTURE

### 1. Wires Fixed

List each non-connected wire that was resolved:

- Wire name
- What was wrong (loose/mismatched/dead)
- What was changed (file:line, before → after)

### 2. Known Gaps Remaining

Things you noticed but intentionally left alone — either out of scope for a wire-check fix, blocked, or requiring a product decision.

### 3. Code Observations

Patterns, duplication, or structural issues encountered during the trace that aren't wire issues but create friction or risk.

### 4. Recommended Follow-ups

Specific follow-up work beyond wire fixes. Each should be actionable enough to hand to another dev.

**DO NOT include post-deploy commands the user is expected to run.** Run them yourself in-session, or describe the follow-up in prose.

### 5. Strategic & Operational Insights

Step back from the wires you just traced and think about the system holistically. Ask:

- Are there patterns that will produce more loose wires in the future?
- Are there missing abstractions that cause field names to drift between layers?
- Are there transport mechanisms that silently drop fields?

---

## OUTPUT FORMAT

Write the handoff file to `{implementation_artifacts}/` using this structure:

```markdown
---
title: 'Handoff: Wire-check fixes for {slug}'
created: '{date}'
source_pr: '{pr_url}'
type: handoff
---

# Handoff: Wire-check fixes for {slug}

**PR:** {pr_url}
**Wire check report:** {report_file_path}
**Date:** {date}

## Wires Fixed

{List each wire fixed with before/after description}

## Known Gaps

{Remaining issues not addressed, or "None identified."}

## Code Observations

{Patterns or structural issues noticed, or "None."}

## Recommended Follow-ups

{Numbered list of concrete next actions, or "None — all wires resolved."}

## Strategic & Operational Insights

{Numbered observations with impact and suggested action, or "None — fixes were self-contained."}
```

**File naming:** `handoff-wire-check-fixes-{slug}-{date}.md`

---

## PRESENT TO USER

After writing the handoff file:

```
**Wire check + fix complete:** {report_file_path}
**Handoff filed:** {handoff_file_path}

**{total} wires traced, {fixed} issues fixed:**
{One-line summary of each fix}

{If follow-ups: "**Follow-ups identified:** {count}"}
{If no follow-ups: "All wires connected — no follow-ups."}
```

---

## WORKTREE CLEANUP — DO THIS LAST

**Only after** the handoff file is written and the summary has been presented.

### 1. Copy handoff to the main repo BEFORE removing the worktree

The handoff file is untracked. Removing the worktree deletes all untracked files inside it.

```bash
cp <worktree-path>/_bmad-output/implementation-artifacts/handoff-wire-check-fixes-*.md \
   <main-repo-root>/_bmad-output/implementation-artifacts/
```

Also copy the wire-check report if it was written inside the worktree:

```bash
cp <worktree-path>/_bmad-output/implementation-artifacts/wire-check-*.md \
   <main-repo-root>/_bmad-output/implementation-artifacts/
```

Verify the copies landed.

### 2. Remove the worktree

Call `ExitWorktree` with `action: "remove"`:

- All commits have been pushed and merged — the branch is no longer needed.
- If `ExitWorktree` refuses, use `discard_changes: true` only after confirming the handoff was copied.

### 3. Sync local main

```bash
git pull --rebase origin main
```

**Critical ordering:** (1) write handoff → (2) present summary → (3) copy to main repo → (4) `ExitWorktree`. Reversing trips the parallel-sessions hook.

---

## SUCCESS METRICS

- Handoff file written to implementation artifacts directory
- All fixed wires documented with before/after
- Summary presented to user
- Worktree cleaned up via `ExitWorktree`
- Local main synced with remote

## FAILURE MODES

- Skipping the handoff because "it was just a wire fix"
- Not copying the handoff file before removing the worktree
- Calling `ExitWorktree` before the handoff file is written
- Writing vague observations without concrete references
- Not syncing local main after merge
