---
title: Parallel Work and BMAD State
description: Why git worktrees don't isolate BMAD planning state, infra, or builds — and what a real fix looks like.
---

# Parallel Work and BMAD State

> Method/design note. Worktrees isolate the source tree; BMAD does not isolate the state that
> actually governs parallel work. This explains why parallel sessions feel bad in a BMAD project,
> and what a real fix looks like. The short guardrail lives in `global-bmad-workflow.md`; this is
> the manual behind it.

## Short version

Git worktrees isolate **code**, but BMAD does not isolate **state**. In a BMAD project, almost
everything that matters for parallel work is shared state — planning files, the database, build
artifacts — not the source tree. So two sessions can safely edit code in parallel, but they collide
immediately on planning, data, and builds. That is the friction.

## Why this happens — four structural reasons

1. **Planning state is untracked and main-only.** BMAD's stories, sprint status, epics, and
   deferred-work live as *untracked* files on the main checkout. They are not committed, so a fresh
   worktree sees an empty BMAD state. This forces a split: planning workflows (`create-story`,
   `sprint-status`, `dev-story`) must run on main, while code edits happen in worktrees. Parallel
   sessions cannot each "own" a story cleanly because there is only one shared, uncommitted source
   of truth. **This is the biggest constraint.**

2. **Infra is shared across worktrees.** All worktrees share the same database, object storage, and
   external API accounts. A migration or write in one session changes reality for all others.
   Parallelism is real only for source files; anything stateful is a shared resource with no
   locking.

3. **Build artifacts are symlinked back to main.** `node_modules` and framework build caches in
   worktrees point back to the main checkout. If a parallel session reinstalls dependencies or
   rebuilds on main, it mutates the very files the worktree relies on. Build state is not isolated
   either.

4. **Single delivery track.** BMAD uses one `origin/main` without per-story branches-of-record.
   Parallel branches drift and reconciling them is manual — a cost that has already been paid once
   in practice (a large local-vs-remote commit divergence).

## Net effect

Worktrees solve the one problem BMAD does not really have here (merge collisions on source files)
and solve none of the three that dominate day-to-day friction (planning state, shared infra, shared
build artifacts).

## What would actually fix it

The real fix is at the method level, not in any single project:

- **Make BMAD's planning state shareable** — commit sprint-status / stories so a worktree can be
  self-sufficient, and
- **Define a parallel-work protocol** — story-level ownership plus a "no migrations in parallel"
  rule.

Because this is a fork-level change, it would propagate to all targeted projects, so it belongs in
the fork — not as a per-project local hack. Until both halves exist, treat story ownership as
single-threaded.
