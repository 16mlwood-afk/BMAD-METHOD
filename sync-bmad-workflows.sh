#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/custom/workflows"
COMMANDS_SOURCE="$SCRIPT_DIR/custom/commands"
HOOKS_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/hooks.json"
WORKTREE_INCLUDE_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/worktreeinclude.template"
TARGETS_FILE="$HOME/.bmad-targets"
CHECK_ONLY=false
FORCE=false
PULL_TARGET=""

usage() {
  echo "Usage: $0 [--check] [--force] [--pull <project-workflows-path>]"
  echo ""
  echo "  (no args)   Sync source → all targets (aborts if targets have local-only content)"
  echo "  --check     Report drift without modifying anything"
  echo "  --force     Sync even if targets have local-only content (DESTRUCTIVE)"
  echo "  --pull PATH Pull changes from a project back to the source of truth"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_ONLY=true; shift ;;
    --force) FORCE=true; shift ;;
    --pull)
      [[ -z "${2:-}" ]] && { echo "ERROR: --pull requires a path argument"; usage; }
      PULL_TARGET="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "ERROR: Unknown argument: $1"; usage ;;
  esac
done

# Dependency checks
for cmd in rsync jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not installed."
    exit 1
  fi
done

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
  | .["$schema"] = "https://json.schemastore.org/claude-code-settings.json"
'

# --- PULL MODE ---
if [[ -n "$PULL_TARGET" ]]; then
  if [[ ! -d "$PULL_TARGET" ]]; then
    echo "ERROR: $PULL_TARGET not found"
    exit 1
  fi

  project_root="${PULL_TARGET%/_bmad/bmm/workflows}"
  if [[ "$project_root" == "$PULL_TARGET" ]]; then
    echo "ERROR: path doesn't end in /_bmad/bmm/workflows"
    exit 1
  fi
  project="$(basename "$project_root")"

  echo "PULL  $project → source"
  pulled=0

  for dir in "${SYNC_DIRS[@]}"; do
    src_path="$SOURCE/$dir"
    dst_path="$PULL_TARGET/$dir"

    if [[ ! -d "$dst_path" ]]; then
      echo "  SKIP  $dir (not in project)"
      continue
    fi

    if [[ ! -d "$src_path" ]] || ! diff -rq --exclude='.DS_Store' "$src_path" "$dst_path" &>/dev/null; then
      mkdir -p "$src_path"
      rsync -a --delete --exclude='.DS_Store' "$dst_path/" "$src_path/"
      echo "  OK    $dir"
      pulled=$((pulled + 1))
    else
      echo "  ----  $dir (no changes)"
    fi
  done

  # Pull command files
  commands_target="${project_root}/.claude/commands/bmad"
  if [[ -d "$commands_target" ]]; then
    for cmd_dir in "$COMMANDS_SOURCE"/*/; do
      [[ ! -d "$cmd_dir" ]] && continue
      module="$(basename "$cmd_dir")"
      src_cmd_path="$COMMANDS_SOURCE/$module"
      dst_cmd_path="$commands_target/$module/workflows"

      if [[ ! -d "$dst_cmd_path" ]]; then
        echo "  SKIP  commands/$module (not in project)"
        continue
      fi

      # Only pull files that exist in the target but not in source
      for f in "$dst_cmd_path"/*.md; do
        [[ ! -f "$f" ]] && continue
        fname="$(basename "$f")"
        if [[ ! -f "$src_cmd_path/workflows/$fname" ]]; then
          mkdir -p "$src_cmd_path/workflows"
          cp "$f" "$src_cmd_path/workflows/$fname"
          echo "  OK    commands/$module/workflows/$fname (pulled)"
          pulled=$((pulled + 1))
        fi
      done
    done
  fi

  echo ""
  if [[ $pulled -gt 0 ]]; then
    echo "Pulled $pulled dir(s) from $project. Review changes in $SOURCE, then commit and re-sync."
  else
    echo "Nothing to pull — source already matches $project."
  fi
  exit 0
fi

# --- CHECK / SYNC MODE ---
if [[ ! -f "$TARGETS_FILE" ]]; then
  echo "ERROR: $TARGETS_FILE not found"
  echo "Create it with one workflow path per line, e.g.:"
  echo "  /Users/you/project/_bmad/bmm/workflows"
  exit 1
fi

synced=0
skipped=0
stale=0
blocked=0
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

  # Derive project root: strip _bmad/bmm/workflows suffix
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

      # Check for local-only content in target that would be deleted
      if [[ -d "$dst_path" ]]; then
        local_only=$(diff -rq --exclude='.DS_Store' "$dst_path" "$src_path" 2>/dev/null | grep "^Only in $dst_path" || true)
        if [[ -n "$local_only" ]]; then
          if ! $dirty; then
            echo "STALE $project"
            dirty=true
          fi
          echo "  ⚠  LOCAL-ONLY content in $dir (would be DELETED on sync):"
          echo "$local_only" | sed 's/^/     /'
        fi
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

    # Check command files
    if [[ -d "$COMMANDS_SOURCE" ]]; then
      commands_target="$project_root/.claude/commands/bmad"
      while IFS= read -r -d '' src_file; do
        rel="${src_file#"$COMMANDS_SOURCE/"}"
        # rel is like bmm/workflows/trace-flow.md
        dst_file="$commands_target/$rel"
        if [[ ! -f "$dst_file" ]] || ! diff -q "$src_file" "$dst_file" &>/dev/null; then
          if ! $dirty; then
            echo "STALE $project"
            dirty=true
          fi
          echo "  ↳  commands/$rel"
        fi
      done < <(find "$COMMANDS_SOURCE" -type f -name '*.md' -not -name '.DS_Store' -print0)
    fi

    if $dirty; then
      stale=$((stale + 1))
    else
      echo "OK    $project"
    fi
  else
    # --- Pre-sync safety check: detect local-only content ---
    has_local_only=false
    for dir in "${SYNC_DIRS[@]}"; do
      src_path="$SOURCE/$dir"
      dst_path="$target/$dir"
      [[ ! -d "$dst_path" ]] && continue
      [[ ! -d "$src_path" ]] && { has_local_only=true; continue; }

      local_only=$(diff -rq --exclude='.DS_Store' "$dst_path" "$src_path" 2>/dev/null | grep "^Only in $dst_path" || true)
      if [[ -n "$local_only" ]]; then
        has_local_only=true
      fi
    done

    if $has_local_only && ! $FORCE; then
      echo "BLOCK $project — has local-only workflow content that would be deleted"
      echo "  Options:"
      echo "    1. Pull changes first:  $0 --pull $target"
      echo "    2. Force overwrite:     $0 --force"
      blocked=$((blocked + 1))
      continue
    fi

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

    # Copy .worktreeinclude if missing
    worktree_include="$project_root/.worktreeinclude"
    if [[ -f "$WORKTREE_INCLUDE_SRC" ]] && [[ ! -f "$worktree_include" ]]; then
      cp "$WORKTREE_INCLUDE_SRC" "$worktree_include"
      echo "  OK    .worktreeinclude (created)"
    fi

    # Sync command files from custom/commands/ to .claude/commands/bmad/
    if [[ -d "$COMMANDS_SOURCE" ]]; then
      commands_target="$project_root/.claude/commands/bmad"
      cmd_count=0
      for cmd_dir in "$COMMANDS_SOURCE"/*/; do
        [[ ! -d "$cmd_dir" ]] && continue
        module="$(basename "$cmd_dir")"
        src_cmd_path="$COMMANDS_SOURCE/$module"
        dst_cmd_path="$commands_target/$module"

        # Walk subdirectories (e.g., workflows/)
        while IFS= read -r -d '' src_file; do
          rel="${src_file#"$src_cmd_path/"}"
          dst_file="$dst_cmd_path/$rel"
          mkdir -p "$(dirname "$dst_file")"
          if [[ ! -f "$dst_file" ]] || ! diff -q "$src_file" "$dst_file" &>/dev/null; then
            cp "$src_file" "$dst_file"
            cmd_count=$((cmd_count + 1))
          fi
        done < <(find "$src_cmd_path" -type f -name '*.md' -not -name '.DS_Store' -print0)
      done
      if [[ $cmd_count -gt 0 ]]; then
        echo "  OK    commands ($cmd_count file(s) synced)"
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
  echo "Done: $synced synced, $skipped skipped, $blocked blocked"
  if [[ $blocked -gt 0 ]]; then
    echo ""
    echo "⚠  $blocked project(s) blocked due to local-only content."
    echo "   Pull changes first, or use --force to overwrite."
  fi
fi
