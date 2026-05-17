#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/custom/workflows"
HOOKS_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/hooks.json"
WORKTREE_INCLUDE_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/worktreeinclude.template"
CONFIG_DEFAULTS_SRC="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/config-defaults.yaml"
CLAUDEMD_TEMPLATE="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/CLAUDE.md.template"
CLAUDEMD_SYNC="$SCRIPT_DIR/sync-claudemd-sections.py"
TARGETS_FILE="$HOME/.bmad-targets"
REFERENCE_FILE="$HOME/.bmad-reference"
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
  "implement"
  "verify"
  "design"
  "meta"
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

# Auto-generate a .claude/commands/ file from a workflow.md's YAML frontmatter.
# Args: $1 = workflow.md path, $2 = relative path from _bmad/bmm/workflows/ (e.g. verify/trace-flow)
generate_command_content() {
  local workflow_md="$1" rel_dir="$2"
  local description
  description=$(sed -n '/^---$/,/^---$/{ /^---$/d; /^description:/{ s/^description:[[:space:]]*//; s/^['\''"]//; s/['\''"][[:space:]]*$//; p; }; }' "$workflow_md")
  [[ -z "$description" ]] && return 1
  printf '%s\n' \
    '---' \
    "description: '${description}'" \
    '---' \
    '' \
    "IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL @_bmad/bmm/workflows/${rel_dir}/workflow.md, READ its entire contents and follow its directions exactly!"
}

# Sync auto-generated command files for all workflows under a synced directory.
# Args: $1 = target workflows dir (e.g. /path/project/_bmad/bmm/workflows),
#        $2 = synced dir name (e.g. verify),
#        $3 = commands target dir (e.g. /path/project/.claude/commands/bmad/bmm/workflows),
#        $4 = mode ("check" or "sync")
# Prints status lines. Returns count of stale/synced files via stdout last line "COUNT:<n>".
sync_commands_for_dir() {
  local workflows_dir="$1" sync_dir="$2" commands_dir="$3" mode="$4"
  local count=0

  while IFS= read -r -d '' workflow_md; do
    local dir_name
    dir_name="$(dirname "$workflow_md")"
    dir_name="${dir_name#"$workflows_dir/"}"
    local wf_name
    wf_name="$(basename "$dir_name")"
    local cmd_file="$commands_dir/${wf_name}.md"

    local expected
    expected="$(generate_command_content "$workflow_md" "$dir_name")" || continue

    if [[ ! -f "$cmd_file" ]] || [[ "$(cat "$cmd_file")" != "$expected" ]]; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$commands_dir"
        printf '%s\n' "$expected" > "$cmd_file"
      fi
      count=$((count + 1))
    fi
  done < <(find "$workflows_dir/$sync_dir" -name 'workflow.md' -print0 2>/dev/null)

  echo "$count"
}

# Backfill missing required keys from config-defaults.yaml into a project's config.yaml.
# Args: $1 = project config.yaml path, $2 = mode ("check" or "sync")
# Returns count of missing keys via stdout.
sync_config_defaults() {
  local config_file="$1" mode="$2"
  local count=0

  [[ ! -f "$CONFIG_DEFAULTS_SRC" ]] && { echo "0"; return; }
  [[ ! -f "$config_file" ]] && { echo "0"; return; }

  # Extract top-level keys from defaults (lines matching "^key:" that aren't comments or indented)
  local required_keys
  required_keys=$(grep -E '^[a-zA-Z_][a-zA-Z0-9_]*:' "$CONFIG_DEFAULTS_SRC" | sed 's/:.*//')

  for key in $required_keys; do
    if ! grep -qE "^${key}:" "$config_file"; then
      if [[ "$mode" == "sync" ]]; then
        # Extract the block for this key: from the comment line above it through all indented/continuation lines
        local block=""
        local in_block=false
        local pending_comment=""
        while IFS= read -r line; do
          if [[ "$line" =~ ^#.* ]] && ! $in_block; then
            pending_comment="${pending_comment:+$pending_comment
}$line"
          elif [[ "$line" =~ ^${key}: ]]; then
            in_block=true
            block="${pending_comment:+$pending_comment
}$line"
            pending_comment=""
          elif $in_block && [[ "$line" =~ ^[[:space:]] ]]; then
            block="$block
$line"
          elif $in_block; then
            break
          else
            pending_comment=""
          fi
        done < "$CONFIG_DEFAULTS_SRC"

        if [[ -n "$block" ]]; then
          printf '\n%s\n' "$block" >> "$config_file"
        fi
      fi
      count=$((count + 1))
    fi
  done

  echo "$count"
}

# --- REFERENCE PROJECT SYNC ---
# Upstream-only workflow dirs (installed by BMAD CLI, no custom override).
# These get synced from a reference project to all others so they stay consistent.
UPSTREAM_WORKFLOW_DIRS=(
  "1-analysis"
  "2-plan-workflows"
  "3-solutioning"
  "4-implementation/correct-course"
  "4-implementation/create-story"
  "4-implementation/dev-story"
  "4-implementation/retrospective"
  "4-implementation/sprint-planning"
  "4-implementation/sprint-status"
  "document-project"
  "generate-project-context"
  "qa-generate-e2e-tests"
)

# Non-workflow dirs to sync from the reference project's _bmad/ tree
UPSTREAM_BMAD_DIRS=(
  "core/agents"
  "core/tasks"
  "core/workflows"
  "core/module-help.csv"
  "bmm/agents"
  "bmm/data"
  "bmm/teams"
  "bmm/module-help.csv"
)

# Resolve reference project root from ~/.bmad-reference (first line, stripped).
# Falls back to the first target with a manifest if the file doesn't exist.
resolve_reference_root() {
  if [[ -f "$REFERENCE_FILE" ]]; then
    local ref_path
    ref_path=$(grep -v '^#' "$REFERENCE_FILE" | grep -v '^$' | head -1)
    ref_path="${ref_path%%[[:space:]]}"
    ref_path="${ref_path##[[:space:]]}"
    if [[ -n "$ref_path" ]] && [[ -d "$ref_path/_bmad" ]]; then
      echo "$ref_path"
      return
    fi
  fi

  # Fallback: first target project that has _config/manifest.yaml
  while IFS= read -r target || [[ -n "$target" ]]; do
    target="${target%%[[:space:]]}"
    target="${target##[[:space:]]}"
    [[ -z "$target" || "$target" == \#* ]] && continue
    local proot="${target%/_bmad/bmm/workflows}"
    if [[ -f "$proot/_bmad/_config/manifest.yaml" ]]; then
      echo "$proot"
      return
    fi
  done < "$TARGETS_FILE"

  echo ""
}

# Sync upstream dirs from reference to a target project.
# Args: $1 = reference _bmad root, $2 = target _bmad root, $3 = target workflows dir, $4 = mode ("check"|"sync")
# Prints count of changes.
sync_upstream_from_reference() {
  local ref_bmad="$1" tgt_bmad="$2" tgt_workflows="$3" mode="$4"
  local count=0

  # Sync upstream workflow dirs
  for dir in "${UPSTREAM_WORKFLOW_DIRS[@]}"; do
    local src="$ref_bmad/bmm/workflows/$dir"
    local dst="$tgt_workflows/$dir"
    [[ ! -d "$src" ]] && continue

    if [[ ! -d "$dst" ]] || ! diff -rq --exclude='.DS_Store' "$src" "$dst" &>/dev/null; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$dst"
        rsync -a --delete --exclude='.DS_Store' "$src/" "$dst/"
      fi
      count=$((count + 1))
    fi
  done

  # Sync non-workflow upstream dirs (core, agents, data, teams)
  for item in "${UPSTREAM_BMAD_DIRS[@]}"; do
    local src="$ref_bmad/$item"
    local dst="$tgt_bmad/$item"

    if [[ -f "$src" ]]; then
      # Single file sync
      if [[ ! -f "$dst" ]] || ! diff -q "$src" "$dst" &>/dev/null; then
        if [[ "$mode" == "sync" ]]; then
          mkdir -p "$(dirname "$dst")"
          cp "$src" "$dst"
        fi
        count=$((count + 1))
      fi
    elif [[ -d "$src" ]]; then
      # Directory sync
      if [[ ! -d "$dst" ]] || ! diff -rq --exclude='.DS_Store' "$src" "$dst" &>/dev/null; then
        if [[ "$mode" == "sync" ]]; then
          mkdir -p "$dst"
          rsync -a --delete --exclude='.DS_Store' "$src/" "$dst/"
        fi
        count=$((count + 1))
      fi
    fi
  done

  echo "$count"
}

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

  # Pull custom workflow dirs back to custom/workflows/
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
      echo "  OK    $dir (custom)"
      pulled=$((pulled + 1))
    else
      echo "  ----  $dir (no changes)"
    fi
  done

  # Pull upstream workflow dirs back to the reference project
  REFERENCE_ROOT=$(resolve_reference_root)
  if [[ -n "$REFERENCE_ROOT" ]] && [[ "$project_root" != "$REFERENCE_ROOT" ]]; then
    ref_workflows="$REFERENCE_ROOT/_bmad/bmm/workflows"
    for dir in "${UPSTREAM_WORKFLOW_DIRS[@]}"; do
      src_path="$ref_workflows/$dir"
      dst_path="$PULL_TARGET/$dir"

      [[ ! -d "$dst_path" ]] && continue

      if [[ ! -d "$src_path" ]] || ! diff -rq --exclude='.DS_Store' "$src_path" "$dst_path" &>/dev/null; then
        mkdir -p "$src_path"
        rsync -a --delete --exclude='.DS_Store' "$dst_path/" "$src_path/"
        echo "  OK    $dir (→ reference)"
        pulled=$((pulled + 1))
      fi
    done

    # Pull non-workflow upstream dirs (core, agents, etc.)
    ref_bmad="$REFERENCE_ROOT/_bmad"
    tgt_bmad="$project_root/_bmad"
    for item in "${UPSTREAM_BMAD_DIRS[@]}"; do
      dst="$tgt_bmad/$item"
      src="$ref_bmad/$item"
      [[ ! -e "$dst" ]] && continue

      if [[ -d "$dst" ]]; then
        if [[ ! -d "$src" ]] || ! diff -rq --exclude='.DS_Store' "$src" "$dst" &>/dev/null; then
          mkdir -p "$src"
          rsync -a --delete --exclude='.DS_Store' "$dst/" "$src/"
          echo "  OK    $item (→ reference)"
          pulled=$((pulled + 1))
        fi
      elif [[ -f "$dst" ]]; then
        if [[ ! -f "$src" ]] || ! diff -q "$src" "$dst" &>/dev/null; then
          mkdir -p "$(dirname "$src")"
          cp "$dst" "$src"
          echo "  OK    $item (→ reference)"
          pulled=$((pulled + 1))
        fi
      fi
    done
  fi

  echo ""
  if [[ $pulled -gt 0 ]]; then
    echo "Pulled $pulled dir(s) from $project. Review changes, then commit and re-sync."
  else
    echo "Nothing to pull — sources already match $project."
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

# Resolve reference project for upstream sync
REFERENCE_ROOT=$(resolve_reference_root)
if [[ -n "$REFERENCE_ROOT" ]]; then
  REFERENCE_BMAD="$REFERENCE_ROOT/_bmad"
  ref_project="$(basename "$REFERENCE_ROOT")"
  if ! $CHECK_ONLY; then
    echo "REF   $ref_project (upstream source)"
  fi
else
  REFERENCE_BMAD=""
  if ! $CHECK_ONLY; then
    echo "WARN  No reference project found — skipping upstream sync"
    echo "  Create ~/.bmad-reference with the project root path, e.g.:"
    echo "    /Users/you/project"
  fi
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

    # Check auto-generated command files (custom + upstream workflow dirs)
    commands_target="$project_root/.claude/commands/bmad/bmm/workflows"
    cmd_stale_total=0
    for dir in "${SYNC_DIRS[@]}"; do
      cmd_stale=$(sync_commands_for_dir "$target" "$dir" "$commands_target" "check")
      cmd_stale_total=$((cmd_stale_total + cmd_stale))
    done
    for dir in "${UPSTREAM_WORKFLOW_DIRS[@]}"; do
      cmd_stale=$(sync_commands_for_dir "$target" "$dir" "$commands_target" "check")
      cmd_stale_total=$((cmd_stale_total + cmd_stale))
    done
    if [[ "$cmd_stale_total" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  commands ($cmd_stale_total missing/outdated)"
    fi

    # Check CLAUDE.md sections
    project_claudemd="$project_root/CLAUDE.md"
    if [[ -f "$CLAUDEMD_TEMPLATE" ]] && [[ -f "$CLAUDEMD_SYNC" ]] && [[ -f "$project_claudemd" ]]; then
      missing_sections=$(python3 "$CLAUDEMD_SYNC" --check "$CLAUDEMD_TEMPLATE" "$project_claudemd" 2>/dev/null || true)
      if [[ -n "$missing_sections" ]]; then
        if ! $dirty; then
          echo "STALE $project"
          dirty=true
        fi
        echo "  ↳  CLAUDE.md (missing sections):"
        echo "$missing_sections" | sed 's/^/     /'
      fi
    fi

    # Check config defaults
    project_config="$project_root/_bmad/bmm/config.yaml"
    cfg_missing=$(sync_config_defaults "$project_config" "check")
    if [[ "$cfg_missing" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  config ($cfg_missing required key(s) missing)"
    fi

    # Check upstream sync from reference project
    if [[ -n "$REFERENCE_BMAD" ]] && [[ "$project_root" != "$REFERENCE_ROOT" ]]; then
      upstream_drift=$(sync_upstream_from_reference "$REFERENCE_BMAD" "$project_root/_bmad" "$target" "check")
      if [[ "$upstream_drift" -gt 0 ]]; then
        if ! $dirty; then
          echo "STALE $project"
          dirty=true
        fi
        echo "  ↳  upstream ($upstream_drift dir(s) differ from reference)"
      fi
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

    # Migration: remove legacy directories (reorganized into implement/verify/design/meta)
    for legacy_dir in "bmad-quick-flow" "build"; do
      old_path="$target/$legacy_dir"
      if [[ -d "$old_path" ]]; then
        rm -rf "$old_path"
        echo "  OK    removed legacy $legacy_dir/ (migrated to implement/verify/design/meta)"
      fi
    done

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

    # Backfill missing config defaults
    project_config="$project_root/_bmad/bmm/config.yaml"
    if [[ -f "$project_config" ]]; then
      cfg_added=$(sync_config_defaults "$project_config" "sync")
      if [[ "$cfg_added" -gt 0 ]]; then
        echo "  OK    config ($cfg_added key(s) backfilled)"
      fi
    fi

    # Sync upstream content from reference project
    if [[ -n "$REFERENCE_BMAD" ]] && [[ "$project_root" != "$REFERENCE_ROOT" ]]; then
      upstream_synced=$(sync_upstream_from_reference "$REFERENCE_BMAD" "$project_root/_bmad" "$target" "sync")
      if [[ "$upstream_synced" -gt 0 ]]; then
        echo "  OK    upstream ($upstream_synced dir(s) synced from reference)"
      fi
    fi

    # Auto-generate command files from workflow.md frontmatter (custom + upstream)
    commands_target="$project_root/.claude/commands/bmad/bmm/workflows"
    cmd_total=0
    for dir in "${SYNC_DIRS[@]}"; do
      cmd_count=$(sync_commands_for_dir "$target" "$dir" "$commands_target" "sync")
      cmd_total=$((cmd_total + cmd_count))
    done
    for dir in "${UPSTREAM_WORKFLOW_DIRS[@]}"; do
      cmd_count=$(sync_commands_for_dir "$target" "$dir" "$commands_target" "sync")
      cmd_total=$((cmd_total + cmd_count))
    done
    if [[ $cmd_total -gt 0 ]]; then
      echo "  OK    commands ($cmd_total file(s) generated)"
    fi

    # Sync missing CLAUDE.md sections
    project_claudemd="$project_root/CLAUDE.md"
    if [[ -f "$CLAUDEMD_TEMPLATE" ]] && [[ -f "$CLAUDEMD_SYNC" ]] && [[ -f "$project_claudemd" ]]; then
      added_sections=$(python3 "$CLAUDEMD_SYNC" --sync "$CLAUDEMD_TEMPLATE" "$project_claudemd" 2>/dev/null || true)
      if [[ -n "$added_sections" ]]; then
        count=$(echo "$added_sections" | wc -l | tr -d ' ')
        echo "  OK    CLAUDE.md ($count section(s) added)"
      fi
    fi

    # Write sync stamp for version tracking
    stamp_dir="$project_root/_bmad/_config"
    if [[ -d "$stamp_dir" ]]; then
      ref_version=""
      if [[ -n "$REFERENCE_ROOT" ]] && [[ -f "$REFERENCE_ROOT/_bmad/_config/manifest.yaml" ]]; then
        ref_version=$(grep -m1 'bmad_version:' "$REFERENCE_ROOT/_bmad/_config/manifest.yaml" 2>/dev/null | sed 's/.*: *//' || true)
        [[ -z "$ref_version" ]] && ref_version=$(grep -m1 '  version:' "$REFERENCE_ROOT/_bmad/_config/manifest.yaml" 2>/dev/null | sed 's/.*: *//' | head -1 || true)
      fi
      cat > "$stamp_dir/sync-stamp.yaml" <<STAMP
# Auto-generated by sync-bmad-workflows.sh — do not edit
synced_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
reference_project: "${REFERENCE_ROOT:-(none)}"
reference_version: "${ref_version:-(unknown)}"
STAMP
    fi

    synced=$((synced + 1))
  fi
done < "$TARGETS_FILE"

# --- POST-SYNC VERIFICATION ---
if ! $CHECK_ONLY && [[ $synced -gt 0 ]] && [[ -f "$CLAUDEMD_TEMPLATE" ]] && [[ -f "$CLAUDEMD_SYNC" ]]; then
  verify_failures=0
  for target in "${seen_targets[@]}"; do
    project_root="${target%/_bmad/bmm/workflows}"
    [[ "$project_root" == "$target" ]] && continue
    project_claudemd="$project_root/CLAUDE.md"
    [[ ! -f "$project_claudemd" ]] && continue
    missing=$(python3 "$CLAUDEMD_SYNC" --check "$CLAUDEMD_TEMPLATE" "$project_claudemd" 2>/dev/null || true)
    if [[ -n "$missing" ]]; then
      project="$(basename "$project_root")"
      echo "VERIFY FAIL  $project — still missing CLAUDE.md sections after sync:"
      echo "$missing" | sed 's/^/  ↳  /'
      verify_failures=$((verify_failures + 1))
    fi
  done
  if [[ $verify_failures -gt 0 ]]; then
    echo ""
    echo "⚠  $verify_failures project(s) still missing CLAUDE.md sections after sync."
    echo "   Investigate: Python error, file permissions, or template parse failure."
  fi
fi

echo ""
if $CHECK_ONLY; then
  if [[ $stale -eq 0 ]]; then
    echo "All projects up to date."
  else
    echo "$stale project(s) out of date. Run without --check to sync."
  fi
else
  echo "Done: $synced synced, $skipped skipped, $blocked blocked"

  # Record sync timestamp for stale-session detection
  date +%s > "$HOME/.bmad-last-sync"

  ACTIVE_SESSIONS=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$ACTIVE_SESSIONS" -gt 0 ]]; then
    echo ""
    echo "ℹ  $ACTIVE_SESSIONS active Claude session(s) may be using stale workflows."
    echo "   They will be warned on next prompt. Restart sessions to pick up changes."
  fi

  if [[ $blocked -gt 0 ]]; then
    echo ""
    echo "⚠  $blocked project(s) blocked due to local-only content."
    echo "   Pull changes first, or use --force to overwrite."
  fi
fi
