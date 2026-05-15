#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM_BRANCH="origin/main"
FORK_REMOTE="myfork"
LOCAL_BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD)"

# Quiet fetch — just update refs
git -C "$SCRIPT_DIR" fetch origin --quiet 2>/dev/null || {
  echo "BMAD drift check: could not reach upstream (offline?)"
  exit 0
}

BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count "HEAD..$UPSTREAM_BRANCH" 2>/dev/null || echo 0)

# Check if fork remote is up to date
FORK_BEHIND=0
if git -C "$SCRIPT_DIR" rev-parse "$FORK_REMOTE/$LOCAL_BRANCH" &>/dev/null; then
  FORK_BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count "$FORK_REMOTE/$LOCAL_BRANCH..HEAD" 2>/dev/null || echo 0)
fi

if [[ "$BEHIND" -eq 0 && "$FORK_BEHIND" -eq 0 ]]; then
  exit 0
fi

echo "──────────────────────────────────────────"
echo "⚠ BMAD fork drift detected (~/bmad-method-v6)"
if [[ "$BEHIND" -gt 0 ]]; then
  echo "  $BEHIND commit(s) behind upstream main"
fi
if [[ "$FORK_BEHIND" -gt 0 ]]; then
  echo "  $FORK_BEHIND unpushed commit(s) to GitHub fork"
fi
echo "  Run: ~/bmad-method-v6/upgrade-bmad.sh"
echo "──────────────────────────────────────────"
