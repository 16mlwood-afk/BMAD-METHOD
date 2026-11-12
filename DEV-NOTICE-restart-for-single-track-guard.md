# DEV NOTICE — restart your Claude Code sessions (single-track delivery guard)

**Posted 2026-06-21. One-time action for anyone with a Claude Code session that started before today.**

A **single-track delivery guard** shipped to all BMAD projects today — a PreToolUse hook
(`bmad-single-track-guard`) that blocks `git merge <branch>` into a local `main` you don't push
(it allows the legitimate `git merge --ff-only origin/main`). This kills the recurring
`origin/main` divergence at the source.

**But hooks only load at session start.** A session you started earlier today (or yesterday)
does NOT have the guard loaded and is still running on the old "no remote yet → local-merge"
model from its cached context — which is why local-merging still seems blessed in that session.
No current file says to local-merge; the corrected CLAUDE.md is single-track everywhere.

## What to do (each dev, once)

1. **`git fetch origin`** before trusting any "N commits ahead" number. If your session hasn't
   fetched, your `origin/main` pointer is stale and your "ahead" count is inflated — it will
   shrink (often to ~0) after a fetch. Recent merges (incl. the domain-track reconciliation,
   PR #20) are already on `origin/main`.
2. **Restart your Claude Code session.** This loads the guard hook and re-reads the corrected
   CLAUDE.md. There is no way to hot-reload a hook mid-session.
3. **Stop local-merging. Deliver via PR:** `push → gh pr create → gh pr merge --squash`.
   Local `main` only ever moves by fast-forwarding from `origin/main`
   (`git merge --ff-only origin/main`) — never by merging a feature branch into it.

## If, after fetching, you are genuinely several commits ahead

That's a real reconcile, not a stale reading. Flag it (with the repo + the ahead count) and
we'll run the union-PR play: branch from `origin/main`, merge your local `main`, verify
(typecheck + tests + build), PR with `--merge`, then fast-forward local `main`.

## Why this is the last time

The guard + the single-track template default + the shared deploy-contract posture are now in
place across all 15 projects and every future onboard. Once every session has cycled, local `main`
can only fast-forward — divergence can't silently accumulate again.
