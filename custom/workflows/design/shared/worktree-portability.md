---
name: worktree-portability
description: 'Rules for workflow path resolution inside git worktrees. Every BMAD workflow that writes artifacts to {implementation_artifacts} or {planning_artifacts} resolves those paths against the worktree root, not the main checkout. Referenced by design-review (step-01 §7), design-handoff (step-03 §1), design-synthesize, design-artifact-loop, design-tuning.'
---

# Worktree Portability — Path Resolution Policy

**Why this exists.** A BMAD workflow run inside a git worktree must write its artifacts into the worktree's tree — not the main repo's tree. Two failure modes this policy prevents:

1. **Silent main-checkout writes.** A step computes `{artifact_path}` as `/Users/foo/project/_bmad-output/...` (the main repo's absolute path) and writes there directly. The artifact lands in the main repo's working tree as an untracked file. The worktree's branch never sees it. When the worktree's PR is merged, the artifact is missing from the merge — it lives only in the main repo's untracked state and never reaches `origin/main`. Consumer workflows that read the artifact from `origin/main` (Claude Design, downstream synthesize) cannot find it.

2. **Worktree-enforcement hook bypass.** Projects with `PreToolUse(Edit|Write)` hard-blocks for "edits outside a worktree when parallel sessions are detected" expect file writes to happen inside the active worktree. When a workflow uses absolute paths to the main checkout, the hook may not fire (depending on hook scope) — the protective mechanism is bypassed.

This policy is the resolution rule every artifact-emitting workflow must apply.

---

## 1. The resolution rule

`{project-root}` in any workflow MUST resolve to the **session's current working directory's repo root**, not to the main checkout's root.

Concretely, when a workflow needs to compute `{project-root}` (and therefore `{implementation_artifacts}`, `{planning_artifacts}`, or any other `{project-root}/...` path):

```bash
# Resolve project-root to the CURRENT working-tree root, whether that's the
# main checkout or a worktree. `git rev-parse --show-toplevel` returns the
# worktree root when inside a worktree, the main checkout root otherwise.
project_root=$(git rev-parse --show-toplevel 2>/dev/null)

# Detect whether we are inside a worktree (as opposed to the main checkout):
git_dir=$(git rev-parse --git-dir 2>/dev/null)
# In a worktree, $git_dir looks like /path/to/main/.git/worktrees/<name>/
# In the main checkout, $git_dir is /path/to/main/.git
case "$git_dir" in
  */.git/worktrees/*) is_worktree=true ;;
  *)                  is_worktree=false ;;
esac
```

`{implementation_artifacts}` resolves to `${project_root}/_bmad-output/implementation-artifacts/`. `{planning_artifacts}` resolves to `${project_root}/_bmad-output/planning-artifacts/`.

**Never** hard-code an absolute path to the main checkout (e.g., `/Users/foo/project/_bmad-output/...`) when the session is inside a worktree. If the workflow reads such a path from a prior session's state, re-resolve via `git rev-parse --show-toplevel` before using it.

---

## 2. Producer rules

Any workflow that writes an artifact to `{implementation_artifacts}` or `{planning_artifacts}` MUST:

1. **Resolve `{project-root}` via `git rev-parse --show-toplevel`** at write-time. Do not cache a resolution from an earlier session or from the workflow's frontmatter.
2. **Refuse to write outside the current worktree.** If `is_worktree == true` and the computed `{artifact_path}` is not a descendant of `${project_root}`, halt with the diagnostic in §4.
3. **Surface the resolution in the artifact's frontmatter or log.** When writing an artifact, include the resolved `{project-root}` so downstream consumers know which tree the producer was working in. A worktree-produced artifact whose `project_root` is the main checkout is a bug.

---

## 3. Affected workflows

These workflows write artifacts and therefore must apply §1 + §2:

- `design-review` — step-01 §7 emits `screen-review-*.md` to `{implementation_artifacts}`.
- `design-handoff` — step-03 §1 emits `design-brief-*.md` to `{implementation_artifacts}`.
- `design-synthesize` — emits bundles (`bundles/<feature>-<date>/`) under `{implementation_artifacts}`.
- `design-artifact-loop` — emits handoff / response / screen-review artifacts under `{implementation_artifacts}`.
- `design-tuning` — emits design-response state files under `{implementation_artifacts}`.
- `maintenance-triage` — emits tech-specs under `{planning_artifacts}`.

Read-only workflows (workflows that consume but never write artifacts) do not need to apply §2 but DO need to apply §1 — they still need to find the artifact in the right tree.

---

## 4. Halt diagnostics

When a workflow detects an out-of-worktree write attempt, halt with this exact diagnostic shape:

```
Worktree path violation: workflow attempted to write outside the active worktree.

  Active worktree:        <result of `git rev-parse --show-toplevel`>
  Computed artifact path: <{artifact_path}>
  Resolution rule:        shared/worktree-portability.md §1

This usually means a stale {project-root} resolution was cached from an
earlier session. Re-resolve via `git rev-parse --show-toplevel` from the
session's current working directory and retry.
```

Halt is non-overridable for artifact writes. The integrity of the worktree-to-PR pipeline depends on it.

---

## 5. Migration

Workflows that predate this policy may resolve `{project-root}` via a config field, a fork-installer constant, or an absolute path from `{main_config}`. They must be updated to use the `git rev-parse --show-toplevel` rule. Patch order:

1. Read this policy in the affected workflow's `INITIALIZATION` block.
2. In any step file that computes `{artifact_path}`, insert the resolution and the out-of-worktree refusal per §1 + §2.
3. Test the workflow in both a main-checkout run AND a worktree run before considering the migration complete.

---

## 6. Why not just fix the worktree-enforcement hook

Projects can install `PreToolUse(Edit|Write)` hooks that block absolute-path writes outside the active worktree. Those hooks are belt-and-suspenders — they catch the failure mode but don't prevent the workflow from trying. The workflow-side resolution rule prevents the attempt in the first place AND degrades cleanly when invoked from the main checkout (no worktree to refer to → `git rev-parse --show-toplevel` returns the main checkout's root → workflow writes to main, exactly as expected). The hook and the policy compose: the policy makes the right thing happen by default, the hook catches violations from workflows that haven't been migrated.
