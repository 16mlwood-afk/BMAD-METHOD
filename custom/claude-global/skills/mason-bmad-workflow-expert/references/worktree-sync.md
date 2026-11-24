# Worktree-Safe Workflow Sync

The fork uses Git worktrees heavily. Originally, not all BMAD workflows were present in every worktree, which caused "missing workflow" failures that were hard to trace. The current design uses a hook-based auto-sync as a P0 fix (planned/partially implemented — confirm current state via STATUS.md).

## The Architecture

- **Source of truth:** `sync-bmad-workflows.sh` is the single script that decides which workflows get copied into a project. It reads from the fork and writes into the consuming project's `_bmad/` (or equivalent) directory.
- **Worktree hook:** Worktree creation is wired to run the sync script for the new worktree. Every worktree gets the same workflow set without manual intervention.
- **.gitignore:** The synced workflow directories are gitignored in consuming projects so generated files don't clutter `git status` or get committed accidentally.

## Invariants

These must hold across the system:

1. **Fork is the only authoritative source.** No project edits its synced workflow files directly. Edits happen in the fork, then propagate via sync.
2. **Per-worktree isolation.** Each worktree has its own copy. No worktree shares workflow files with another via symlink or mount.
3. **Consistency across 13 projects.** All projects pull from the same fork commit (or close to it). Drift between projects is a smell.
4. **No committed sync output.** Synced workflow files never appear in `git status` as tracked changes in consuming projects.

## Common Failure Modes

### "Workflow not found" in a worktree

Cause: worktree was created without the sync hook firing, or the hook failed silently.
Fix: re-run `sync-bmad-workflows.sh` manually for that worktree. Then check why the hook didn't fire (missing hook, hook script bug, worktree created via tooling that bypasses hooks).

### Workflow behaves differently in two worktrees of the same project

Cause: the two worktrees are synced from different fork commits (one was synced before a fork update, the other after).
Fix: re-sync both. Add a check in the sync script (or STATUS.md) that records which fork commit was used for the last sync.

### Synced files showing up in `git status`

Cause: `.gitignore` is missing the synced directory, or the directory was previously committed and is now being tracked despite the gitignore.
Fix: ensure `.gitignore` covers the synced path; if previously committed, `git rm --cached` the directory.

### Edits to synced files in a consuming project disappear

Cause: working as designed. Synced files are overwritten on every sync. The user edited the wrong layer.
Fix: edit in the fork, not the consuming project. Re-sync to propagate.

## Review Checklist for Sync-Related Changes

When reviewing changes to `sync-bmad-workflows.sh`, the worktree hook, or related plumbing:

- [ ] Script is idempotent — running it twice produces the same result.
- [ ] Script handles the case where the target directory doesn't exist yet (fresh worktree).
- [ ] Script handles the case where the target directory has stale files from a previous sync (clean overwrite, not merge).
- [ ] Hook is wired in a way that survives common worktree-creation paths the team uses.
- [ ] `.gitignore` entries are updated if the synced directory structure changes.
- [ ] No new authoritative-source ambiguity introduced (e.g., a workflow that could be edited in two places).

## Authoring Workflows with Worktree Awareness

When writing a new workflow:

- Assume the workflow lives in the fork and gets copied. Don't write paths that only make sense in a specific consuming project.
- Don't reference files outside the synced directory tree unless they're guaranteed to exist in every consuming project (rare — be explicit when you do).
- If a workflow needs project-specific config, read it from a known location in the consuming project (e.g., `_bmad/bmm/config.yaml`), not from the fork.
