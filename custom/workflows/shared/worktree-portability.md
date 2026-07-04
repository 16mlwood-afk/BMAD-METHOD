---
name: worktree-portability
contract_version: 1
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

---

## 7. Fallback: obtaining a worktree from a cwd-pinned session

A project may mandate "always work in a worktree," but the `EnterWorktree` tool can refuse when the session's cwd is **pinned to the repo root** (it errors both on create — "cannot create a worktree from a subagent with a cwd override" — and on enter-by-path — "switching is only available to sessions whose working directory is inside a worktree"). The tool's own escape hatch is gated on already being in a worktree, which a repo-root session cannot break. The sanctioned manual fallback:

```bash
# 1. Create the worktree by hand from the remote tip
git worktree add -b <type>/<desc> .claude/worktrees/<desc> origin/main
# 2. Edit every file via its ABSOLUTE worktree path — Write/Edit accept absolute paths,
#    and the `/.claude/worktrees/` segment makes the PreToolUse edit-guard treat it as in-worktree.
# 3. Drive git against the worktree dir
git -C .claude/worktrees/<desc> add -A && git -C .claude/worktrees/<desc> commit -m "…"
```

This satisfies both the worktree mandate and the edit-guard (which keys on the path string, not the process cwd). Clean up with `git worktree remove` after the PR merges. (Recorded in `docs/fork-gaps.md` — the "ALWAYS EnterWorktree" cwd-pinned gap.)

## 8. Per-worktree `_bmad/` refresh is OPT-IN (default off)

A new worktree inherits **`main`'s `_bmad/`** — there is no automatic per-worktree refresh from the fork. This is deliberate. In old-layout projects `_bmad/bmm/workflows/` is **tracked**, so freshening it inside a worktree leaves it dirty, and with a tracked path you cannot have all three of: per-worktree freshness, a friction-free `ExitWorktree` teardown (dirty `_bmad/` makes the teardown demand `discard_changes`, conflating throwaway churn with real work), and a working §A3 `git merge main` integrate step (hiding the churn via `git update-index --skip-worktree` makes the merge abort — "local changes would be overwritten"). The default resolves the trilemma toward **merge + teardown safety**.

- **Default:** worktrees run with `main`'s `_bmad/`. The cure for staleness is to **sync `main`** (the SessionStart drift banner flags when it's behind), not to refresh every worktree.
- **Escape hatch:** when a per-worktree refresh is genuinely needed, set `BMAD_WORKTREE_SYNC=1` before the worktree's `EnterWorktree` (or run `BMAD_WORKTREE_SYNC=1 sync-bmad-workflows.sh --worktree <path>`), accepting the local `_bmad/` churn consciously.
- **Why this default:** routed through `enforcement-expert` — a deterministic mechanism change (don't write the churn) beats a prose "remember not to tear down before merge." The per-worktree sync is a convenience, not a safety primitive; A3 discipline (commit → push → PR → merge before teardown) + a synced `main` are the real safety. (`docs/fork-gaps.md` 2026-06-30.)

## 9. Verifying inside a worktree (framework generated-types + sub-package installs)

A fresh worktree shares the repo's tracked files but **not** generated or installed state — so the editor's own signal (LSP diagnostics, `tsc`) can read as wall-to-wall broken until you bootstrap it. Two recurring cases, both costing real verification quality on exactly the high-stakes changes worktrees are mandated for (`docs/fork-gaps.md` 2026-07-04):

- **Framework ambient types are absent.** SvelteKit's `.svelte-kit/` (the `$app`/`$lib`/`$types` ambient types + the `.svelte-kit/tsconfig.json` the root tsconfig `extends`) is generated, gitignored, and NOT present in a new worktree. Until you run **`npx svelte-kit sync`**, the LSP emits HUNDREDS of phantom diagnostics — `Cannot find module '$lib/...'`, `Cannot find name 'Set'/'Map'`, missing-Promise — i.e. the whole stdlib + every internal import reads as broken, and vitest 404s on the missing tsconfig. Run the framework's sync FIRST, before trusting a single red squiggle. (Other frameworks have the analogous generated-types step — Next `.next/types` via `next dev`/`build`, etc.)
- **Sub-packages have their own `node_modules`.** A sub-package with its own `package.json`/`tsconfig` (e.g. `mcp-avask/`, any MCP-server dir) has **no `node_modules` in the worktree**, so `tsc` / `npm run build` there fails wall-to-wall on `@types/node`/SDK resolution. Until you `npm ci` in that dir, the only available check is vitest (esbuild transform — no full typecheck). Do NOT misread that wall of module-resolution errors as your own change breaking; name it, and verify via the transform-level test.

**The trap this closes:** in a worktree the fastest correct instinct — trust the editor's red — is the WRONG move until bootstrap, and an agent either chases phantoms or learns to ignore ALL diagnostics (defeating the point on exactly the change where they matter). Bootstrap the worktree's verifiability before verifying. The deterministic companion — a PostToolUse `EnterWorktree` framework-detect that runs the sync automatically — is the still-open hook-track half of this gap.
