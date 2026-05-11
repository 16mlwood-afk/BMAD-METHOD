#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/src/modules/bmm/workflows"
HOOKS_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/hooks.json"
TARGETS_FILE="$HOME/.bmad-targets"

if [[ ! -f "$TARGETS_FILE" ]]; then
  echo "ERROR: $TARGETS_FILE not found"
  echo "Create it with one workflow path per line, e.g.:"
  echo "  /Users/you/project/_bmad/bmm/workflows"
  exit 1
fi

SYNC_DIRS=(
  "bmad-quick-flow"
  "shared"
  "4-implementation/code-review"
)

synced=0
skipped=0

while IFS= read -r target || [[ -n "$target" ]]; do
  [[ -z "$target" || "$target" == \#* ]] && continue

  if [[ ! -d "$target" ]]; then
    echo "SKIP  $target (not found)"
    skipped=$((skipped + 1))
    continue
  fi

  project_root="$(dirname "$(dirname "$(dirname "$target")")")"
  project="$(basename "$project_root")"
  echo "SYNC  $project"

  # Sync workflow directories
  for dir in "${SYNC_DIRS[@]}"; do
    src_path="$SOURCE/$dir"
    dst_path="$target/$dir"

    if [[ ! -d "$src_path" ]]; then
      echo "  WARN  source missing: $dir"
      continue
    fi

    mkdir -p "$dst_path"
    rsync -a --delete "$src_path/" "$dst_path/"
    echo "  OK    $dir"
  done

  # Sync hooks into .claude/settings.local.json
  settings_dir="$project_root/.claude"
  settings_file="$settings_dir/settings.local.json"

  if [[ -f "$HOOKS_SRC" ]] && command -v jq &>/dev/null; then
    mkdir -p "$settings_dir"
    if [[ -f "$settings_file" ]]; then
      # Merge hooks into existing settings, preserving permissions and other keys
      jq -s '.[0] * {hooks: .[1].hooks}' "$settings_file" "$HOOKS_SRC" > "$settings_file.tmp"
      mv "$settings_file.tmp" "$settings_file"
      echo "  OK    hooks (merged)"
    else
      # No existing settings — create with just hooks
      cp "$HOOKS_SRC" "$settings_file"
      echo "  OK    hooks (created)"
    fi
  fi

  synced=$((synced + 1))
done < "$TARGETS_FILE"

echo ""
echo "Done: $synced synced, $skipped skipped"
