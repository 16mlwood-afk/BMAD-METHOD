#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/src/modules/bmm/workflows"

TARGETS=(
  "/Users/masonwood/code/comms_dashboard/_bmad/bmm/workflows"
  "/Users/masonwood/brand-source-finder/_bmad/bmm/workflows"
  "/Users/masonwood/code/inbound-flow/_bmad/bmm/workflows"
  "/Users/masonwood/code/accounting-tools/_bmad/bmm/workflows"
)

SYNC_DIRS=(
  "bmad-quick-flow"
  "shared"
  "4-implementation/code-review"
)

synced=0
skipped=0
errors=0

for target in "${TARGETS[@]}"; do
  if [[ ! -d "$target" ]]; then
    echo "SKIP  $target (not found)"
    skipped=$((skipped + 1))
    continue
  fi

  project="$(basename "$(dirname "$(dirname "$(dirname "$target")")")")"
  echo "SYNC  $project"

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

  synced=$((synced + 1))
done

echo ""
echo "Done: $synced synced, $skipped skipped"
