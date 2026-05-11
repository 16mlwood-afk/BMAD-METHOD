#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/custom/workflows"
HOOKS_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/hooks.json"
TARGETS_FILE="$HOME/.bmad-targets"
CHECK_ONLY=false

if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
fi

# Dependency checks
for cmd in rsync jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not installed."
    exit 1
  fi
done

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

JQ_MERGE='
  input as $base | input as $template |
  ($template.hooks | [.. | .statusMessage? // empty]) as $bmad_msgs |
  reduce ($template.hooks | keys[]) as $event (
    $base;
    .hooks[$event] = (
      [(.hooks[$event] // [])[] | select(
        ((.name // "") | startswith("bmad-") | not) and
        ([.hooks[]?.statusMessage // ""] | map(. as $m | $bmad_msgs | index($m)) | any | not)
      )]
      + $template.hooks[$event]
    )
  )
'

synced=0
skipped=0
stale=0
seen_targets=()

while IFS= read -r target || [[ -n "$target" ]]; do
  target="${target%%[[:space:]]}"
  target="${target##[[:space:]]}"
  [[ -z "$target" || "$target" == \#* ]] && continue

  # Deduplicate
  for seen in "${seen_targets[@]+"${seen_targets[@]}"}"; do
    if [[ "$seen" == "$target" ]]; then
      continue 2
    fi
  done
  seen_targets+=("$target")

  if [[ ! -d "$target" ]]; then
    echo "SKIP  $target (not found)"
    skipped=$((skipped + 1))
    continue
  fi

  # Derive project root: strip _bmad/bmm/workflows suffix instead of counting dirnames
  project_root="${target%/_bmad/bmm/workflows}"
  if [[ "$project_root" == "$target" ]]; then
    echo "SKIP  $target (path doesn't end in /_bmad/bmm/workflows)"
    skipped=$((skipped + 1))
    continue
  fi
  project="$(basename "$project_root")"

  if $CHECK_ONLY; then
    dirty=false
    for dir in "${SYNC_DIRS[@]}"; do
      src_path="$SOURCE/$dir"
      dst_path="$target/$dir"
      [[ ! -d "$src_path" ]] && continue
      if [[ ! -d "$dst_path" ]] || ! diff -rq --exclude='.DS_Store' "$src_path" "$dst_path" &>/dev/null; then
        if ! $dirty; then
          echo "STALE $project"
          dirty=true
        fi
        echo "  ↳  $dir"
      fi
    done

    settings_file="$project_root/.claude/settings.local.json"
    if [[ -f "$HOOKS_SRC" ]]; then
      if [[ ! -f "$settings_file" ]]; then
        if ! $dirty; then
          echo "STALE $project"
          dirty=true
        fi
        echo "  ↳  hooks (missing)"
      else
        merged=$(jq -n "$JQ_MERGE" "$settings_file" "$HOOKS_SRC")
        current=$(cat "$settings_file")
        if [[ "$(echo "$merged" | jq -S .)" != "$(echo "$current" | jq -S .)" ]]; then
          if ! $dirty; then
            echo "STALE $project"
            dirty=true
          fi
          echo "  ↳  hooks (outdated)"
        fi
      fi
    fi

    if $dirty; then
      stale=$((stale + 1))
    else
      echo "OK    $project"
    fi
  else
    echo "SYNC  $project"

    for dir in "${SYNC_DIRS[@]}"; do
      src_path="$SOURCE/$dir"
      dst_path="$target/$dir"

      if [[ ! -d "$src_path" ]]; then
        echo "  WARN  source missing: $dir"
        continue
      fi

      mkdir -p "$dst_path"
      rsync -a --delete --exclude='.DS_Store' "$src_path/" "$dst_path/"
      echo "  OK    $dir"
    done

    settings_dir="$project_root/.claude"
    settings_file="$settings_dir/settings.local.json"

    if [[ -f "$HOOKS_SRC" ]]; then
      mkdir -p "$settings_dir"
      if [[ -f "$settings_file" ]]; then
        jq -n "$JQ_MERGE" "$settings_file" "$HOOKS_SRC" > "$settings_file.tmp"
        mv "$settings_file.tmp" "$settings_file"
        echo "  OK    hooks (upserted)"
      else
        cp "$HOOKS_SRC" "$settings_file"
        echo "  OK    hooks (created)"
      fi
    fi

    synced=$((synced + 1))
  fi
done < "$TARGETS_FILE"

echo ""
if $CHECK_ONLY; then
  if [[ $stale -eq 0 ]]; then
    echo "All projects up to date."
  else
    echo "$stale project(s) out of date. Run without --check to sync."
  fi
else
  echo "Done: $synced synced, $skipped skipped"
fi
