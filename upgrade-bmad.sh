#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-bmad-workflows.sh"

echo "=== Upgrade BMAD ==="
echo ""

# Step 1: Fetch upstream
echo "Fetching upstream (bmad-code-org/BMAD-METHOD)..."
git -C "$SCRIPT_DIR" fetch origin

# Step 2: Check for new commits
LOCAL=$(git -C "$SCRIPT_DIR" rev-parse HEAD)
REMOTE=$(git -C "$SCRIPT_DIR" rev-parse origin/v6-alpha)

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "Already up to date with upstream."
  echo ""
  echo "Run sync-bmad-workflows.sh to push current workflows to projects."
  exit 0
fi

BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count HEAD..origin/v6-alpha)
echo "$BEHIND new commit(s) from upstream."
echo ""

# Step 3: Merge upstream
echo "Merging upstream into local branch..."
if ! git -C "$SCRIPT_DIR" merge origin/v6-alpha; then
  echo ""
  echo "CONFLICT: Merge conflicts detected in the files above."
  echo "Resolve them in ~/bmad-method-v6/, then run:"
  echo "  cd ~/bmad-method-v6 && git add -A && git commit"
  echo "  git push myfork v6-alpha"
  echo "  ./sync-bmad-workflows.sh"
  exit 1
fi

echo ""

# Step 4: Push to fork
echo "Pushing to fork (myfork)..."
git -C "$SCRIPT_DIR" push myfork v6-alpha

echo ""

# Step 5: Sync to all projects
echo "Syncing workflows to all projects..."
bash "$SYNC_SCRIPT"

echo ""
echo "=== Upgrade complete ==="
