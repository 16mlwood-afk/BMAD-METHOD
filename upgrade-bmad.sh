#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-bmad-workflows.sh"
UPSTREAM_BRANCH="origin/main"
FORK_REMOTE="myfork"
LOCAL_BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD)"

echo "=== Upgrade BMAD ==="
echo "Local branch: $LOCAL_BRANCH → upstream: $UPSTREAM_BRANCH"
echo ""

# Guard: abort if fork has uncommitted changes
if ! git -C "$SCRIPT_DIR" diff --quiet || ! git -C "$SCRIPT_DIR" diff --cached --quiet; then
  echo "ERROR: ~/bmad-method-v6 has uncommitted changes."
  echo "Commit or stash them first, then re-run."
  echo ""
  git -C "$SCRIPT_DIR" status --short
  exit 1
fi

# Step 1: Fetch upstream
echo "Fetching upstream (bmad-code-org/BMAD-METHOD)..."
git -C "$SCRIPT_DIR" fetch origin

# Step 2: Check for new commits
BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count "HEAD..$UPSTREAM_BRANCH")

if [[ "$BEHIND" -eq 0 ]]; then
  echo "Already up to date with upstream."
  echo ""
  echo "Run sync-bmad-workflows.sh to push current workflows to projects."
  exit 0
fi

echo "$BEHIND new commit(s) from upstream."
echo ""

# Step 3: Rebase custom commits onto upstream
echo "Rebasing local commits onto $UPSTREAM_BRANCH..."
if ! git -C "$SCRIPT_DIR" rebase "$UPSTREAM_BRANCH"; then
  echo ""
  echo "CONFLICT: Rebase conflicts detected."
  echo "Resolve them in ~/bmad-method-v6/, then run:"
  echo "  cd ~/bmad-method-v6 && git add -A && git rebase --continue"
  echo "  git push $FORK_REMOTE $LOCAL_BRANCH --force-with-lease"
  echo "  ./sync-bmad-workflows.sh"
  exit 1
fi

echo ""

# Step 4: Push to fork
echo "Pushing to fork ($FORK_REMOTE)..."
git -C "$SCRIPT_DIR" push "$FORK_REMOTE" "$LOCAL_BRANCH" --force-with-lease

echo ""

# Step 5: Sync to all projects
echo "Syncing workflows to all projects..."
bash "$SYNC_SCRIPT"

echo ""
echo "=== Upgrade complete ==="
