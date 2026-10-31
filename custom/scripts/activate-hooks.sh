#!/usr/bin/env bash
# activate-hooks.sh — idempotent git-hook activation (STD-HOOKACTIVATE-001).
#
# Points this repo's git at the tracked .githooks/ dir and makes the entrypoints
# executable, so a distributed gate script actually fires. Owned by the fork:
# sync-bmad-workflows.sh and onboard-project.sh run this automatically, so a
# synced gate is reliably WIRED instead of silently off. Safe to run anywhere,
# any number of times (a no-op when already activated). Also the manual fix a
# developer runs if the SessionStart liveness probe warns.
#
# Enforcement class: DETERMINISTIC activation (the operator does not choose).
# It does NOT make the gate fail-closed — see custom/githooks/pre-push header.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
GITHOOKS_DIR="$ROOT/.githooks"

if [[ ! -d "$GITHOOKS_DIR" ]]; then
  echo "activate-hooks: no .githooks/ in $ROOT — nothing to activate" >&2
  exit 0
fi

# Make entrypoints executable (tracked perms can be lost across checkouts/copies).
chmod +x "$GITHOOKS_DIR"/* 2>/dev/null || true

# Point git at .githooks/ (repo-local; shared across all worktrees via the common
# git config). Overrides any prior husky core.hooksPath — the canonical mechanism.
current="$(git -C "$ROOT" config --get core.hooksPath || true)"
if [[ "$current" != ".githooks" ]]; then
  git -C "$ROOT" config core.hooksPath .githooks
  echo "activate-hooks: set core.hooksPath=.githooks in $ROOT" >&2
fi

exit 0
