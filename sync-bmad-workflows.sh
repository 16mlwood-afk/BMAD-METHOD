#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/custom/workflows"
SKILLS_SOURCE="$SCRIPT_DIR/custom/skills"
SCRIPTS_SOURCE="$SCRIPT_DIR/custom/scripts"
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
WORKTREE_TARGET=""
REAP_ONLY=false
REAP_PATH=""

usage() {
  echo "Usage: $0 [--check] [--force] [--pull <path> | --worktree <path> | --reap [<path>]]"
  echo ""
  echo "  (no args)       Sync source → all targets (aborts if targets have local-only content)"
  echo "                  Includes automatic stale-worktree reap on each target."
  echo "  --check         Report drift without modifying anything"
  echo "  --force         Sync even if targets have local-only content (DESTRUCTIVE)"
  echo "  --pull PATH     Pull changes from a project back to the source of truth"
  echo "  --worktree PATH Sync custom workflow dirs + skills into a single worktree path"
  echo "                  (minimal — no hooks/commands/CLAUDE.md; git-tracked files propagate via checkout)"
  echo "  --reap [PATH]   Remove stale worktrees (merged on origin/main + clean working tree)."
  echo "                  Without PATH: reaps all targets. With PATH: reaps that project only."
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_ONLY=true; shift ;;
    --force) FORCE=true; shift ;;
    --pull)
      [[ -z "${2:-}" ]] && { echo "ERROR: --pull requires a path argument"; usage; }
      PULL_TARGET="$2"; shift 2 ;;
    --worktree)
      [[ -z "${2:-}" ]] && { echo "ERROR: --worktree requires a path argument"; usage; }
      WORKTREE_TARGET="$2"; shift 2 ;;
    --reap)
      REAP_ONLY=true
      # Optional path argument
      if [[ -n "${2:-}" && "${2:0:1}" != "-" ]]; then
        REAP_PATH="$2"; shift 2
      else
        shift
      fi ;;
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

# Legacy subpaths that have been moved or removed in the canonical source.
# Listed as <sync-dir>/<leaf-name>. The sync workflow:
#   1. Treats these as already-migrated for the local-only block check
#      (otherwise every project that still has the legacy copy would block).
#   2. Removes them from each target during the migration step before rsync
#      writes the new canonical location.
LEGACY_SUBPATHS_TO_REMOVE=(
  "design/apply-design-policy-change"  # moved to meta/apply-design-policy-change
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
  | .permissions = ($template.permissions // .permissions // {})
  | .enableAllProjectMcpServers = ($template.enableAllProjectMcpServers // .enableAllProjectMcpServers // false)
  | .["$schema"] = "https://json.schemastore.org/claude-code-settings.json"
'

# Auto-generate a .claude/commands/ file from a workflow.md's YAML frontmatter.
# Args: $1 = workflow.md path, $2 = relative path from _bmad/bmm/workflows/ (e.g. verify/trace-flow),
#        $3 = filename (e.g. workflow.md or workflow-technical-research.md)
generate_command_content() {
  local workflow_md="$1" rel_dir="$2" filename="${3:-workflow.md}"
  local description
  description=$(sed -n '/^---$/,/^---$/{ /^---$/d; /^description:/{ s/^description:[[:space:]]*//; s/^['\''"]//; s/['\''"][[:space:]]*$//; p; }; }' "$workflow_md")
  [[ -z "$description" ]] && return 1
  printf '%s\n' \
    '---' \
    "description: '${description}'" \
    '---' \
    '' \
    "IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL @_bmad/bmm/workflows/${rel_dir}/${filename}, READ its entire contents and follow its directions exactly!"
}

# Sync auto-generated command files for all workflows under a synced directory.
# Handles both standard workflow.md files (command name = parent dir) and
# variant workflow-*.md files (command name = variant slug, e.g. workflow-technical-research.md → technical-research).
# Args: $1 = target workflows dir (e.g. /path/project/_bmad/bmm/workflows),
#        $2 = synced dir name (e.g. verify),
#        $3 = commands target dir (e.g. /path/project/.claude/commands/bmad/bmm/workflows),
#        $4 = mode ("check" or "sync")
# Prints status lines. Returns count of stale/synced files via stdout last line "COUNT:<n>".
sync_commands_for_dir() {
  local workflows_dir="$1" sync_dir="$2" commands_dir="$3" mode="$4"
  local count=0

  # Standard workflow.md files — command name from parent directory
  while IFS= read -r -d '' workflow_md; do
    local dir_name
    dir_name="$(dirname "$workflow_md")"
    dir_name="${dir_name#"$workflows_dir/"}"
    local wf_name
    wf_name="$(basename "$dir_name")"
    local cmd_file="$commands_dir/${wf_name}.md"

    local expected
    expected="$(generate_command_content "$workflow_md" "$dir_name" "workflow.md")" || continue

    if [[ ! -f "$cmd_file" ]] || [[ "$(cat "$cmd_file")" != "$expected" ]]; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$commands_dir"
        printf '%s\n' "$expected" > "$cmd_file"
      fi
      count=$((count + 1))
    fi
  done < <(find "$workflows_dir/$sync_dir" -name 'workflow.md' -print0 2>/dev/null)

  # Variant workflow-*.md files — command name from filename slug
  while IFS= read -r -d '' variant_md; do
    local dir_name filename slug
    dir_name="$(dirname "$variant_md")"
    dir_name="${dir_name#"$workflows_dir/"}"
    filename="$(basename "$variant_md")"
    slug="${filename#workflow-}"
    slug="${slug%.md}"
    local cmd_file="$commands_dir/${slug}.md"

    local expected
    expected="$(generate_command_content "$variant_md" "$dir_name" "$filename")" || continue

    if [[ ! -f "$cmd_file" ]] || [[ "$(cat "$cmd_file")" != "$expected" ]]; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$commands_dir"
        printf '%s\n' "$expected" > "$cmd_file"
      fi
      count=$((count + 1))
    fi
  done < <(find "$workflows_dir/$sync_dir" -name 'workflow-*.md' -print0 2>/dev/null)

  echo "$count"
}

# Remove orphaned command pointers whose target workflow files don't exist.
# Args: $1 = project root, $2 = commands dir, $3 = mode ("check" or "sync")
# Returns count of orphaned files via stdout.
cleanup_orphaned_commands() {
  local project_root="$1" commands_dir="$2" mode="$3"
  local count=0

  [[ ! -d "$commands_dir" ]] && { echo "0"; return; }

  for cmd_file in "$commands_dir"/*.md; do
    [[ ! -f "$cmd_file" ]] && continue
    local target
    target=$(grep -oE '@_bmad/[^ ,]+' "$cmd_file" 2>/dev/null | head -1)
    [[ -z "$target" ]] && continue
    target="${target#@}"
    local resolved="$project_root/$target"
    if [[ ! -f "$resolved" ]]; then
      if [[ "$mode" == "sync" ]]; then
        rm -f "$cmd_file"
      fi
      count=$((count + 1))
    fi
  done

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

# Sync portable skills from custom/skills/ to a project's .claude/skills/.
# Each top-level dir under SKILLS_SOURCE is mirrored to a same-named dir in the
# target. In check mode, returns count of skills that differ from source.
# Args: $1 = project root, $2 = mode ("check" or "sync")
# Returns count via stdout.
sync_skills_for_project() {
  local project_root="$1" mode="$2"
  local count=0

  [[ ! -d "$SKILLS_SOURCE" ]] && { echo "0"; return; }

  local skills_target="$project_root/.claude/skills"
  for skill_dir in "$SKILLS_SOURCE"/*/; do
    [[ ! -d "$skill_dir" ]] && continue
    local skill_name skill_dst
    skill_name="$(basename "$skill_dir")"
    skill_dst="$skills_target/$skill_name"

    if [[ ! -d "$skill_dst" ]] || ! diff -rq --exclude='.DS_Store' "$skill_dir" "$skill_dst" &>/dev/null; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$skill_dst"
        rsync -a --delete --exclude='.DS_Store' "$skill_dir" "$skill_dst/"
      fi
      count=$((count + 1))
    fi
  done

  echo "$count"
}

# Sync portable scripts from custom/scripts/ to a project's ./scripts/.
# Each file under SCRIPTS_SOURCE is copied to scripts/<name> in the target,
# preserving execute permissions. Per-file sync (not directory rsync) so the
# project's existing scripts/ entries (e.g., deploy-prod.sh) are untouched.
# In check mode, returns count of scripts that differ from source.
# Args: $1 = project root, $2 = mode ("check" or "sync")
# Returns count via stdout.
sync_scripts_for_project() {
  local project_root="$1" mode="$2"
  local count=0

  [[ ! -d "$SCRIPTS_SOURCE" ]] && { echo "0"; return; }

  local scripts_target="$project_root/scripts"
  for script_file in "$SCRIPTS_SOURCE"/*; do
    [[ ! -f "$script_file" ]] && continue
    local script_name script_dst
    script_name="$(basename "$script_file")"
    script_dst="$scripts_target/$script_name"

    if [[ ! -f "$script_dst" ]] || ! cmp -s "$script_file" "$script_dst"; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$scripts_target"
        cp -p "$script_file" "$script_dst"
        chmod +x "$script_dst"
      fi
      count=$((count + 1))
    fi
  done

  echo "$count"
}


# ============================================================================
# Stale-worktree reaper. Removes worktrees in <project>/.claude/worktrees/*
# where (a) the branch is fully merged into origin/main AND (b) git status is
# clean. Untracked-but-merged is also OK — those are usually sync artifacts.
#
# Args: $1 = project root, $2 = mode ("check" or "sync")
# Returns count of reaped (or reapable, in check mode) worktrees via stdout.
# ============================================================================
reap_stale_worktrees_for_project() {
  local project_root="$1" mode="$2"
  local count=0
  local worktrees_dir="$project_root/.claude/worktrees"
  [[ ! -d "$worktrees_dir" ]] && { echo "0"; return; }

  # Need git to inspect branches/status. Skip silently if not a repo.
  git -C "$project_root" rev-parse --git-dir >/dev/null 2>&1 || { echo "0"; return; }

  # Fetch origin/main once so the merged-check is accurate.
  if [[ "$mode" == "sync" ]]; then
    git -C "$project_root" fetch origin main --quiet >/dev/null 2>&1 || true
  fi

  # Resolve origin/main as a ref to compare against.
  local main_sha
  main_sha=$(git -C "$project_root" rev-parse origin/main 2>/dev/null ||              git -C "$project_root" rev-parse main 2>/dev/null || echo "")
  [[ -z "$main_sha" ]] && { echo "0"; return; }

  for wt_path in "$worktrees_dir"/*/; do
    [[ ! -d "$wt_path" ]] && continue
    wt_path="${wt_path%/}"
    local wt_name
    wt_name="$(basename "$wt_path")"

    # Check that this is actually a registered worktree of the project.
    git -C "$project_root" worktree list --porcelain 2>/dev/null |       grep -q "^worktree $wt_path$" || continue

    # Get the branch the worktree is on.
    local branch
    branch=$(git -C "$wt_path" rev-parse --abbrev-ref HEAD 2>/dev/null)
    [[ -z "$branch" || "$branch" == "HEAD" || "$branch" == "main" ]] && continue

    # Branch must be effectively merged into origin/main. Use git cherry
    # which detects patch-equivalent commits (handles squash-merges, where
    # main's commit has a different SHA than the branch's tip). cherry
    # outputs "+ <sha>" for commits in branch NOT equivalent to any in main,
    # and "- <sha>" for commits with equivalents in main. If no "+" lines,
    # the branch is fully reflected in main.
    local branch_sha
    branch_sha=$(git -C "$wt_path" rev-parse HEAD 2>/dev/null)
    [[ -z "$branch_sha" ]] && continue

    local unmerged_count
    unmerged_count=$(git -C "$project_root" cherry origin/main "$branch" 2>/dev/null | grep -c "^+" || true)
    [[ "$unmerged_count" -gt 0 ]] && continue

    # Working tree must be reap-clean: no uncommitted modifications to
    # tracked files EXCEPT those under BMAD-managed / artifact paths
    # (_bmad/, .claude/, _bmad-output/, docs/) — those are almost always
    # sync artifacts and shouldn't block reaping. Untracked-anywhere is OK.
    local dirty
    dirty=$(git -C "$wt_path" status --porcelain 2>/dev/null | \
            grep -E "^[ MARC]" | \
            grep -vE "^[ MARC]+ (_bmad/|\.claude/|_bmad-output/|docs/)" | \
            head -1)
    [[ -n "$dirty" ]] && continue

    if [[ "$mode" == "sync" ]]; then
      # Remove worktree (git's own cleanup; handles branch deletion separately).
      if git -C "$project_root" worktree remove --force "$wt_path" >/dev/null 2>&1; then
        # Optionally delete the branch too (it's merged + worktree gone).
        git -C "$project_root" branch -d "$branch" >/dev/null 2>&1 || true
      fi
    fi
    count=$((count + 1))
  done

  echo "$count"
}

# Pull a project's .claude/skills/<name>/ contents back to custom/skills/<name>/
# for any skill that already exists at the source. New project-local skills are
# NOT auto-promoted to the fork — that requires an explicit user action.
# Args: $1 = project root
# Returns count via stdout.
pull_skills_from_project() {
  local project_root="$1"
  local count=0

  [[ ! -d "$SKILLS_SOURCE" ]] && { echo "0"; return; }

  for skill_dir in "$SKILLS_SOURCE"/*/; do
    [[ ! -d "$skill_dir" ]] && continue
    local skill_name skill_src
    skill_name="$(basename "$skill_dir")"
    skill_src="$project_root/.claude/skills/$skill_name"
    [[ ! -d "$skill_src" ]] && continue

    if ! diff -rq --exclude='.DS_Store' "$skill_dir" "$skill_src" &>/dev/null; then
      rsync -a --delete --exclude='.DS_Store' "$skill_src/" "$skill_dir/"
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

  # Pull custom skills back to custom/skills/
  skills_pulled=$(pull_skills_from_project "$project_root")
  if [[ "$skills_pulled" -gt 0 ]]; then
    echo "  OK    skills ($skills_pulled updated from project)"
    pulled=$((pulled + skills_pulled))
  fi

  echo ""
  if [[ $pulled -gt 0 ]]; then
    echo "Pulled $pulled dir(s) from $project. Review changes, then commit and re-sync."
  else
    echo "Nothing to pull — sources already match $project."
  fi
  exit 0
fi

# --- WORKTREE MODE ---
# Minimal sync into a single worktree. Skips hooks, slash-commands, and CLAUDE.md
# because those are git-tracked and propagate via the worktree's normal checkout.
# Writes the custom workflow dirs (SYNC_DIRS) and portable skills, which are
# NOT tracked in project repos and would otherwise be missing in worktrees
# branched from origin.
if [[ -n "$WORKTREE_TARGET" ]]; then
  WORKTREE_TARGET="${WORKTREE_TARGET%/}"
  # Accept either a project root or a _bmad/bmm/workflows path
  wt_project_root="${WORKTREE_TARGET%/_bmad/bmm/workflows}"
  if [[ "$WORKTREE_TARGET" != */_bmad/bmm/workflows ]]; then
    WORKTREE_TARGET="$WORKTREE_TARGET/_bmad/bmm/workflows"
  fi

  mkdir -p "$WORKTREE_TARGET"

  copied=0
  for dir in "${SYNC_DIRS[@]}"; do
    src="$SOURCE/$dir"
    dst="$WORKTREE_TARGET/$dir"
    [[ ! -d "$src" ]] && continue
    mkdir -p "$dst"
    rsync -a --delete --exclude='.DS_Store' "$src/" "$dst/"
    copied=$((copied + 1))
  done

  skills_copied=$(sync_skills_for_project "$wt_project_root" "sync")
  scripts_copied=$(sync_scripts_for_project "$wt_project_root" "sync")

  msg="OK    Worktree synced: $WORKTREE_TARGET ($copied dirs"
  [[ "$skills_copied" -gt 0 ]] && msg="$msg, $skills_copied skill(s)"
  [[ "$scripts_copied" -gt 0 ]] && msg="$msg, $scripts_copied script(s)"
  echo "$msg)"
  exit 0
fi

# --- REAP MODE ---
if [[ "$REAP_ONLY" == "true" ]]; then
  if [[ -n "$REAP_PATH" ]]; then
    # Single-project reap
    if [[ ! -d "$REAP_PATH" ]]; then
      echo "ERROR: $REAP_PATH not found"
      exit 1
    fi
    project_root="$REAP_PATH"
    [[ "$project_root" == */_bmad/bmm/workflows ]] && project_root="${project_root%/_bmad/bmm/workflows}"
    count=$(reap_stale_worktrees_for_project "$project_root" "sync")
    if [[ "$count" -gt 0 ]]; then
      echo "OK    reaped $count stale worktree(s) from $(basename "$project_root")"
    else
      echo "OK    no stale worktrees in $(basename "$project_root")"
    fi
    exit 0
  fi
  # All-targets reap
  if [[ ! -f "$TARGETS_FILE" ]]; then
    echo "ERROR: $TARGETS_FILE not found"; exit 1
  fi
  total_reaped=0
  while IFS= read -r target; do
    [[ -z "$target" || "${target:0:1}" == "#" ]] && continue
    project_root="$target"
    [[ "$project_root" == */_bmad/bmm/workflows ]] && project_root="${project_root%/_bmad/bmm/workflows}"
    [[ ! -d "$project_root" ]] && continue
    count=$(reap_stale_worktrees_for_project "$project_root" "sync")
    if [[ "$count" -gt 0 ]]; then
      echo "OK    $(basename "$project_root"): reaped $count stale worktree(s)"
      total_reaped=$((total_reaped + count))
    fi
  done < "$TARGETS_FILE"
  echo ""
  echo "Done: reaped $total_reaped stale worktree(s) across all targets."
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
    cmd_orphaned=$(cleanup_orphaned_commands "$project_root" "$commands_target" "check")
    cmd_stale_total=$((cmd_stale_total + cmd_orphaned))
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

    # Check portable skills sync
    skills_drift=$(sync_skills_for_project "$project_root" "check")
    if [[ "$skills_drift" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  skills ($skills_drift skill(s) missing/outdated)"
    fi

    # Check portable scripts sync
    scripts_drift=$(sync_scripts_for_project "$project_root" "check")
    if [[ "$scripts_drift" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  scripts ($scripts_drift script(s) missing/outdated)"
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

      # Strip lines for known-legacy subpaths — the migration step will clean them up.
      for legacy in "${LEGACY_SUBPATHS_TO_REMOVE[@]}"; do
        legacy_parent="${legacy%%/*}"
        legacy_leaf="${legacy##*/}"
        if [[ "$dir" == "$legacy_parent" ]]; then
          local_only=$(echo "$local_only" | grep -v ": $legacy_leaf\$" || true)
        fi
      done

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

    # Migration: remove legacy subpaths (workflows moved between subdirs in the source)
    for legacy_path in "${LEGACY_SUBPATHS_TO_REMOVE[@]}"; do
      old_path="$target/$legacy_path"
      if [[ -d "$old_path" ]]; then
        rm -rf "$old_path"
        echo "  OK    removed legacy $legacy_path/ (moved in source — sync will write the canonical copy)"
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

    # Sync portable skills from custom/skills/
    skills_synced=$(sync_skills_for_project "$project_root" "sync")
    if [[ "$skills_synced" -gt 0 ]]; then
      echo "  OK    skills ($skills_synced skill(s) synced)"
    fi

    # Sync portable scripts from custom/scripts/ (bmad-deploy.sh, etc.)
    scripts_synced=$(sync_scripts_for_project "$project_root" "sync")
    if [[ "$scripts_synced" -gt 0 ]]; then
      echo "  OK    scripts ($scripts_synced script(s) synced)"
    fi

    # Reap stale worktrees (merged on origin/main + clean working tree).
    reaped=$(reap_stale_worktrees_for_project "$project_root" "sync")
    if [[ "$reaped" -gt 0 ]]; then
      echo "  OK    reaped $reaped stale worktree(s)"
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
    cmd_cleaned=$(cleanup_orphaned_commands "$project_root" "$commands_target" "sync")
    cmd_total=$((cmd_total + cmd_cleaned))
    if [[ $cmd_total -gt 0 ]]; then
      cmd_msg="$cmd_total file(s) generated"
      [[ "$cmd_cleaned" -gt 0 ]] && cmd_msg="$cmd_msg, $cmd_cleaned orphaned removed"
      echo "  OK    commands ($cmd_msg)"
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
