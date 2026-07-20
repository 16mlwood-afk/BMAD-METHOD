#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/custom/workflows"
SKILLS_SOURCE="$SCRIPT_DIR/custom/skills"
SCRIPTS_SOURCE="$SCRIPT_DIR/custom/scripts"
GITHOOKS_SOURCE="$SCRIPT_DIR/custom/githooks"
AGENTS_SOURCE="$SCRIPT_DIR/custom/agents"
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
ONLY_TARGET=""
COMMIT_SYNCED=false

usage() {
  echo "Usage: $0 [--check] [--force] [--only <path>] [--pull <path> | --worktree <path> | --reap [<path>]]"
  echo ""
  echo "  (no args)       Sync source → all targets (aborts if targets have local-only content)"
  echo "                  Includes automatic stale-worktree reap on each target."
  echo "  --check         Report drift without modifying anything"
  echo "  --force         Sync even if targets have local-only content (DESTRUCTIVE)"
  echo "  --commit        After writing, scoped-commit the synced BMAD paths in each project"
  echo "                  (_bmad/, .claude/skills/, .claude/commands/bmad/, CLAUDE.md) so the"
  echo "                  sync has a real done-state instead of leaving a dirty tree"
  echo "  --only PATH     Sync just ONE project (its root or _bmad/bmm/workflows path); skip all others"
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
    --commit) COMMIT_SYNCED=true; shift ;;
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
    --only)
      [[ -z "${2:-}" ]] && { echo "ERROR: --only requires a project path argument"; usage; }
      ONLY_TARGET="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "ERROR: Unknown argument: $1"; usage ;;
  esac
done

# Normalize --only to a project root (accept either the root or its workflows path).
if [[ -n "$ONLY_TARGET" ]]; then
  ONLY_TARGET="${ONLY_TARGET%/}"
  ONLY_TARGET="${ONLY_TARGET%/_bmad/bmm/workflows}"
fi

# Dependency checks
for cmd in rsync jq shasum; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not installed."
    exit 1
  fi
done

# Durability guard (fork-gap 2026-07-05 "sync has no delivery contract", part c):
# the sync reads the LOCAL fork working tree, so syncing while the fork is ahead of its
# remote propagates UNPUSHED edits to every target — state that exists nowhere in version
# control if this checkout is lost. Warn (don't block) on the main sync paths.
# Key on the FORK's own remote branch (myfork/<branch>), NOT @{upstream} — the custom
# branch tracks the original bmad-code-org upstream (origin/main), so @{upstream}..HEAD is
# always ~600 (the whole fork divergence) and would fire on every sync = ignore-training noise.
if [[ -z "$PULL_TARGET" && -z "$WORKTREE_TARGET" ]] && ! $REAP_ONLY; then
  fork_branch=$(git -C "$SCRIPT_DIR" branch --show-current 2>/dev/null || echo custom)
  fork_ref="myfork/${fork_branch}"
  if git -C "$SCRIPT_DIR" rev-parse --verify --quiet "$fork_ref" >/dev/null 2>&1; then
    fork_ahead=$(git -C "$SCRIPT_DIR" rev-list --count "${fork_ref}..HEAD" 2>/dev/null || echo 0)
    if [[ "${fork_ahead:-0}" -gt 0 ]]; then
      echo "⚠  Local fork is $fork_ahead commit(s) ahead of ${fork_ref} (unpushed)."
      echo "   Syncing now propagates UNPUSHED fork state to all targets. If this checkout is"
      echo "   lost before you push, those projects carry wiring that exists nowhere in git."
      echo "   Recommend: git push myfork ${fork_branch}   (then re-run sync)."
      echo ""
    fi
  fi
fi

SYNC_DIRS=(
  "implement"
  "verify"
  "design"
  "meta"
  "shared"
  "4-implementation/code-review"
  "4-implementation/sprint-planning"  # fork-customized 2026-07-11: adds an incremental --epic mode (promoted OUT of UPSTREAM_WORKFLOW_DIRS below). workflow.yaml format (no workflow.md) → the skills-native porter skips it by design; it ships via the _bmad/bmm/workflows tree that skills-native projects also read.
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

# BMAD-managed paths the destructive rsync -a --delete fan-out overwrites in each target.
# Used by the deterministic skip-if-dirty guard (fork-gap 2026-07-10): uncommitted TRACKED
# modifications in any of these signal a peer session mid-edit → refuse that target unless
# --force. (Untracked local-only content is handled separately by classify_local_only + the
# manifest; that is why the guard uses --untracked-files=no.)
BMAD_MANAGED_GIT_PATHS=(
  "_bmad/bmm/workflows"
  "_bmad/bmm/agents"
  "_bmad/bmad-shared"
  ".claude/commands/bmad"
  ".claude/skills"
)

# Uncommitted TRACKED modifications in a target's BMAD-managed paths ("" if clean or non-git).
# The single deterministic predicate behind the skip-if-dirty guard (both --check preview and
# the sync-mode refusal call it), so the two paths can never diverge. Regression-locked by
# test/test-sync-skip-if-dirty.sh.
bmad_managed_dirty() {
  local project_root="$1"
  git -C "$project_root" rev-parse --is-inside-work-tree &>/dev/null || return 0
  git -C "$project_root" status --porcelain --untracked-files=no -- "${BMAD_MANAGED_GIT_PATHS[@]}" 2>/dev/null || true
}

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
  local delivered=()
  for script_file in "$SCRIPTS_SOURCE"/*; do
    [[ ! -f "$script_file" ]] && continue
    local script_name script_dst
    script_name="$(basename "$script_file")"
    script_dst="$scripts_target/$script_name"
    delivered+=("$script_name")

    if [[ ! -f "$script_dst" ]] || ! cmp -s "$script_file" "$script_dst"; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$scripts_target"
        cp -p "$script_file" "$script_dst"
        chmod +x "$script_dst"
      fi
      count=$((count + 1))
    fi
  done

  # Manifest of the exact fork-delivered basenames, so bmad-deploy.sh's dirty-tree
  # filter can treat these fork-owned scripts as deploy-irrelevant (they never enter
  # the build output) while a project's OWN uncommitted scripts still block. Written
  # under .claude/ (itself deploy-irrelevant) and refreshed EVERY sync — regardless
  # of whether any script changed — so a fork script removed later drops off the list.
  # This closes the "sync drops a runnable script into scripts/, which then trips the
  # deploy dirty-tree gate until each project happens to commit it" false-block.
  if [[ "$mode" == "sync" && ${#delivered[@]} -gt 0 ]]; then
    mkdir -p "$project_root/.claude"
    printf '%s\n' "${delivered[@]}" > "$project_root/.claude/bmad-synced-scripts.txt"
  fi

  echo "$count"
}

# A repo's .githooks/ is BESPOKE (project-owned, NOT fork-managed) if it holds a
# pre-push/pre-commit entrypoint that does NOT carry the fork marker. The rail must
# never overwrite or auto-activate such a repo — a project's own tsc/build/lint gate
# is theirs to own (a real fleet has them: inbound-flow, accounting-tools, …). The
# liveness probe surfaces these for a deliberate per-repo decision instead. The fork
# only manages truly gate-less repos + ones already carrying its own dispatcher.
_githooks_repo_is_bespoke() {
  local ghd="$1/.githooks"
  local ep
  for ep in "$ghd/pre-push" "$ghd/pre-commit"; do
    [[ -f "$ep" ]] || continue
    grep -q "STD-HOOKACTIVATE-001" "$ep" 2>/dev/null || return 0
  done
  return 1
}

# Sync canonical git-hook entrypoints from custom/githooks/ to a project's
# ./.githooks/ — ONLY for repos the fork manages (gate-less, or already carrying the
# fork dispatcher). A repo with a bespoke entrypoint is skipped wholesale (its gate
# is protected). Marker-gated copy: a fork-delivered file (carries the marker) can be
# updated; a project's own files are never touched. STD-HOOKACTIVATE-001.
# Args: $1 = project root, $2 = mode. Count via stdout.
sync_githooks_for_project() {
  local project_root="$1" mode="$2"
  local count=0

  [[ ! -d "$GITHOOKS_SOURCE" ]] && { echo "0"; return; }
  _githooks_repo_is_bespoke "$project_root" && { echo "0"; return; }

  local gh_target="$project_root/.githooks"
  for gh_file in "$GITHOOKS_SOURCE"/*; do
    [[ ! -f "$gh_file" ]] && continue
    local gh_name gh_dst
    gh_name="$(basename "$gh_file")"
    gh_dst="$gh_target/$gh_name"

    # Never overwrite a pre-existing non-fork file (e.g. a project-customized
    # gates.conf carries no marker → create-only after first delivery).
    if [[ -f "$gh_dst" ]] && ! grep -q "STD-HOOKACTIVATE-001" "$gh_dst" 2>/dev/null; then
      continue
    fi

    if [[ ! -f "$gh_dst" ]] || ! cmp -s "$gh_file" "$gh_dst"; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$gh_target"
        cp -p "$gh_file" "$gh_dst"
        chmod +x "$gh_dst"
      fi
      count=$((count + 1))
    fi
  done

  # Fork-owned gate drop-ins (gap 496). gates.d/*.conf are FORK-managed (projects
  # customize gates.conf, never gates.d) → always distribute, so a new fork gate
  # retrofits the fleet without a per-repo gates.conf edit. The loop above iterates
  # files only and skips the gates.d/ SUBDIR, so it is handled here.
  if [[ -d "$GITHOOKS_SOURCE/gates.d" ]]; then
    for gd_file in "$GITHOOKS_SOURCE"/gates.d/*.conf; do
      [[ ! -f "$gd_file" ]] && continue
      local gd_dst="$gh_target/gates.d/$(basename "$gd_file")"
      if [[ ! -f "$gd_dst" ]] || ! cmp -s "$gd_file" "$gd_dst"; then
        if [[ "$mode" == "sync" ]]; then
          mkdir -p "$gh_target/gates.d"
          cp -p "$gd_file" "$gd_dst"
        fi
        count=$((count + 1))
      fi
    done
  fi

  echo "$count"
}

# Ensure a project's git is wired to its tracked .githooks/ so synced gates actually
# fire (the activation half of STD-HOOKACTIVATE-001 — distribution is
# sync_githooks_for_project above). ONLY auto-activates a FORK-MANAGED .githooks
# (carries the marker) — a repo with a bespoke/dormant gate is left for a deliberate
# per-repo decision, never silently switched on (the probe surfaces it). check: 1 when
# a fork-managed .githooks exists but core.hooksPath != .githooks; sync: set it
# idempotently. Worktrees inherit this (core.hooksPath lives in the shared common git
# config), so the worktree sync path deliberately does NOT call this. Args: $1 root, $2 mode.
activate_hooks_for_project() {
  local project_root="$1" mode="$2"
  local count=0

  [[ ! -d "$project_root/.githooks" ]] && { echo "0"; return; }
  _githooks_repo_is_bespoke "$project_root" && { echo "0"; return; }

  local current
  current="$(git -C "$project_root" config --get core.hooksPath 2>/dev/null || true)"
  if [[ "$current" != ".githooks" ]]; then
    if [[ "$mode" == "sync" ]]; then
      git -C "$project_root" config core.hooksPath .githooks 2>/dev/null || true
      chmod +x "$project_root/.githooks"/* 2>/dev/null || true
    fi
    count=1
  fi

  echo "$count"
}

# Sync custom agent personas from custom/agents/ to a project. Each *.md under
# AGENTS_SOURCE is mirrored to _bmad/bmm/agents/<name>.md AND a thin slash-command
# wrapper is (re)generated at .claude/commands/bmad/bmm/agents/<name>.md so the
# persona is invokable as /bmad:bmm:agents:<name>. The wrapper just loads the
# agent file — same shape the upstream installer emits for built-in agents.
# A custom agent counts as drifted if either the persona file OR its wrapper
# differs from what this run would write. Args: $1 = project root, $2 = mode.
# Returns count via stdout.
sync_agents_for_project() {
  local project_root="$1" mode="$2"
  local count=0

  [[ ! -d "$AGENTS_SOURCE" ]] && { echo "0"; return; }

  local agents_target="$project_root/_bmad/bmm/agents"
  local cmds_target="$project_root/.claude/commands/bmad/bmm/agents"
  for agent_file in "$AGENTS_SOURCE"/*.md; do
    [[ ! -f "$agent_file" ]] && continue
    local agent_name agent_dst wrapper_dst wrapper_content
    agent_name="$(basename "$agent_file" .md)"
    agent_dst="$agents_target/$agent_name.md"
    wrapper_dst="$cmds_target/$agent_name.md"

    wrapper_content="---
name: '$agent_name'
description: '$agent_name agent'
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified. NEVER break character until given an exit command.

<agent-activation CRITICAL=\"TRUE\">
1. LOAD the FULL agent file from @_bmad/bmm/agents/$agent_name.md
2. READ its entire contents - this contains the complete agent persona, menu, and instructions
3. Execute ALL activation steps exactly as written in the agent file
4. Follow the agent's persona and menu system precisely
5. Stay in character throughout the session
</agent-activation>"

    local drifted=0
    { [[ ! -f "$agent_dst" ]] || ! cmp -s "$agent_file" "$agent_dst"; } && drifted=1
    { [[ ! -f "$wrapper_dst" ]] || [[ "$(cat "$wrapper_dst" 2>/dev/null)" != "$wrapper_content" ]]; } && drifted=1

    if [[ "$drifted" -eq 1 ]]; then
      if [[ "$mode" == "sync" ]]; then
        mkdir -p "$agents_target" "$cmds_target"
        cp -p "$agent_file" "$agent_dst"
        printf '%s\n' "$wrapper_content" > "$wrapper_dst"
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

    # Defensive: the branch must have at least one commit ahead of where it
    # split from origin/main. A branch at exactly origin/main HEAD (zero commits
    # of its own) is a fresh worktree with no work yet — reaping it can destroy
    # uncommitted in-progress work whose author hasn't run git add yet.
    local ahead_count
    ahead_count=$(git -C "$project_root" rev-list --count origin/main.."$branch" 2>/dev/null || echo 0)
    [[ "$ahead_count" -eq 0 ]] && continue

    # All commits on the branch must be patch-equivalent to commits on
    # origin/main. cherry outputs "+ <sha>" for unequivalent commits.
    local unmerged_count
    unmerged_count=$(git -C "$project_root" cherry origin/main "$branch" 2>/dev/null | grep -c "^+" || true)
    [[ "$unmerged_count" -gt 0 ]] && continue

    # Working tree must be COMPLETELY clean — no untracked, no modified,
    # no staged, no anything. The previous rule (tolerate BMAD-managed dirty
    # paths) caused an incident: an agent's in-progress new files
    # (InvoiceDrawer.svelte, a new endpoint route) were untracked, and
    # their modified design-tuning state file lived under _bmad-output/
    # which was filtered. The worktree was reaped → uncommitted work
    # destroyed. Strict-clean is the only safe rule.
    local any_dirty
    any_dirty=$(git -C "$wt_path" status --porcelain 2>/dev/null | head -1)
    [[ -n "$any_dirty" ]] && continue

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
  # "4-implementation/sprint-planning" — PROMOTED to fork-customized (SYNC_DIRS) 2026-07-11 for the incremental --epic mode; no longer reference-synced (the reference-sync runs AFTER SYNC_DIRS and would clobber the custom copy).
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
# Writes the custom workflow dirs (SYNC_DIRS) and portable skills.
#
# OPT-IN, DEFAULT OFF (set BMAD_WORKTREE_SYNC=1 to enable). In OLD-LAYOUT projects
# the SYNC_DIRS land under a TRACKED `_bmad/bmm/workflows/`, so writing them here
# dirties every new worktree (~88 files vs the branch's fork-lagging _bmad/). That
# churn (a) makes the harness ExitWorktree teardown demand `discard_changes` —
# conflating throwaway sync churn with real, possibly-unmerged work, training the
# reflex that eventually discards real work — and (b) cannot be hidden via
# `git update-index --skip-worktree` without BREAKING the §A3 `git merge main`
# integrate step (empirically: the merge aborts, "local changes would be
# overwritten"). With `_bmad/` tracked, per-worktree freshness + friction-free
# teardown + a working integrate are mutually exclusive — so the chosen default is
# freshness-off: a worktree inherits MAIN's `_bmad/`, and the cure for staleness is
# to sync MAIN (the SessionStart drift banner flags it), not every worktree. The
# per-worktree refresh stays available behind the flag for the rare case it's
# genuinely needed. (fork-gaps.md 2026-06-30; routed via enforcement-expert — a
# deterministic mechanism change beats a prose "don't tear down before merge".)
if [[ -n "$WORKTREE_TARGET" ]]; then
  if [[ "${BMAD_WORKTREE_SYNC:-}" != "1" ]]; then
    echo "OK    Worktree _bmad/ refresh skipped (opt-in: BMAD_WORKTREE_SYNC=1). Worktree inherits main's _bmad/."
    exit 0
  fi
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
  agents_copied=$(sync_agents_for_project "$wt_project_root" "sync")

  msg="OK    Worktree synced: $WORKTREE_TARGET ($copied dirs"
  [[ "$skills_copied" -gt 0 ]] && msg="$msg, $skills_copied skill(s)"
  [[ "$scripts_copied" -gt 0 ]] && msg="$msg, $scripts_copied script(s)"
  [[ "$agents_copied" -gt 0 ]] && msg="$msg, $agents_copied agent(s)"
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

# --- v6.8 SKILLS-LAYOUT DELIVERY (dual-layout transition) ---
# A skills-layout project (fresh bmad-cli v6.8 install) has NO _bmad/bmm/workflows dir but IS a real
# project (.claude/skills present). Instead of skipping it, deliver the migrated custom layer: the
# skills-native ports (generated by tools/port-workflows-to-skills.sh) + the bmad-shared policy home,
# plus the same hooks/skills/scripts/agents/config/CLAUDE.md the old-layout path delivers.
# Old-layout projects are untouched by this — they take the existing path below.
SKILLS_NATIVE="$SCRIPT_DIR/custom/skills-native"
PORT_ENGINE="$SCRIPT_DIR/tools/port-workflows-to-skills.sh"
_skills_native_built=false
# Success MUST depend on the porter actually succeeding — never on a leftover directory.
# Previously this ran the engine as `>/dev/null 2>&1 || true` and then inferred success from
# `[[ -d "$SKILLS_NATIVE" ]]`, a tree that persists from any PRIOR successful port. So a failed
# port + a stale tree reported OK and shipped stale ports to every skills-layout target
# (fork-gap 2026-07-20, silent-failure). The porter itself is fine (`set -euo pipefail`); the
# swallowing was here. Error-handling only — sync scope, target list, dirty-target guard and
# commit behaviour are untouched.
ensure_skills_native_built() {
  $_skills_native_built && return 0
  if [[ ! -x "$PORT_ENGINE" ]]; then
    echo "  FAIL  skills-native [phase: engine-check] — port engine missing or not executable: $PORT_ENGINE" >&2
    return 1
  fi
  local _port_log _port_rc
  _port_rc=0
  _port_log="$(mktemp -t bmad-skills-native-port 2>/dev/null)" || _port_log=""
  if [[ -n "$_port_log" ]]; then
    "$PORT_ENGINE" "$SKILLS_NATIVE" >"$_port_log" 2>&1 || _port_rc=$?
  else
    "$PORT_ENGINE" "$SKILLS_NATIVE" >/dev/null 2>&1 || _port_rc=$?
  fi
  if (( _port_rc != 0 )); then
    echo "  FAIL  skills-native [phase: generate-ports] — port engine exited $_port_rc; NO fresh ports were produced." >&2
    echo "        A pre-existing $SKILLS_NATIVE tree is NOT accepted as success (stale ports must never ship as OK)." >&2
    if [[ -n "$_port_log" ]]; then
      sed 's/^/        | /' "$_port_log" >&2
      rm -f "$_port_log"
    fi
    return 1
  fi
  if [[ -n "$_port_log" ]]; then
    rm -f "$_port_log"
  fi
  if [[ ! -d "$SKILLS_NATIVE" ]]; then
    echo "  FAIL  skills-native [phase: verify-output] — engine reported success but produced no tree at $SKILLS_NATIVE" >&2
    return 1
  fi
  _skills_native_built=true
  return 0
}

# Colon-command aliases for skills-layout projects. For every delivered bmad-<name>
# skill, emit a thin wrapper so the skill is ALSO invokable in the old command-layout
# slash format — in addition to the native /bmad-<name> skill invocation. Namespacing:
#   bmad-agent-<role>  -> .claude/commands/bmad/bmm/agents/<role>.md  -> /bmad:bmm:agents:<role>
#   bmad-<name> (else) -> .claude/commands/bmad/bmm/workflows/<name>.md -> /bmad:bmm:workflows:<name>
# Agent-persona skills belong in the agents/ namespace, matching sync_agents_for_project's
# /bmad:bmm:agents:<name> wrappers (bmad-create-agent / bmad-design-agent are WORKFLOWS,
# not personas — they stay in workflows/). Skills-layout-only: this runs from
# deliver_skills_layout_project, so it only touches projects on the v6.8 skills layout
# (cash-recovery is the sole one today; future migrated projects inherit it).
#
# These aliases ARE reaped: cleanup_orphaned_commands (the old-layout reaper) keys off an
# @_bmad/... target ref these Skill-invoking wrappers don't carry, and isn't called here.
# Instead we reap against the desired set — any wrapper WE own (carries our marker) that
# we did not (re)write this run, i.e. its backing skill was removed OR relocated namespace.
# The marker check leaves fork-lane agent wrappers (LOAD-from-file form) and any non-alias
# command untouched. Args: $1 = project root. Returns count of changes (writes + reaps).
SKILL_ALIAS_MARKER='invoke the Skill tool with skill name'
sync_skill_command_aliases_for_project() {
  local proot="$1"
  local count=0
  local skills_dir="$proot/.claude/skills"
  local wf_dir="$proot/.claude/commands/bmad/bmm/workflows"
  local ag_dir="$proot/.claude/commands/bmad/bmm/agents"
  [[ ! -d "$skills_dir" ]] && { echo "0"; return; }

  local desired=$'\n'   # newline-delimited, newline-bracketed list of wrappers we own this run
  local d nm slug skillmd desc sub out_slug wrapper_dst wrapper_content
  for d in "$skills_dir"/bmad-*/; do
    [[ -d "$d" ]] || continue
    nm="$(basename "$d")"
    slug="${nm#bmad-}"
    skillmd="$d/SKILL.md"
    [[ -f "$skillmd" ]] || continue
    # Pull the frontmatter description (single- or double-quoted), strip one quote layer.
    desc=$(sed -n '/^description:/{ s/^description:[[:space:]]*//; s/^"//; s/"[[:space:]]*$//; s/^'\''//; s/'\''[[:space:]]*$//; p; q; }' "$skillmd")
    [[ -z "$desc" ]] && desc="$nm skill"
    # Escape single quotes for the YAML single-quoted scalar.
    desc="${desc//\'/\'\'}"
    # Route agent-persona skills (bmad-agent-<role>) to the agents/ namespace.
    if [[ "$slug" == agent-* ]]; then
      sub="$ag_dir"; out_slug="${slug#agent-}"
    else
      sub="$wf_dir"; out_slug="$slug"
    fi
    wrapper_dst="$sub/$out_slug.md"
    desired+="$wrapper_dst"$'\n'
    wrapper_content="---
description: '$desc'
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: invoke the Skill tool with skill name \`$nm\` and follow its instructions exactly. Pass through any arguments supplied after the command."

    if [[ ! -f "$wrapper_dst" ]] || [[ "$(cat "$wrapper_dst" 2>/dev/null)" != "$wrapper_content" ]]; then
      mkdir -p "$sub"
      printf '%s\n' "$wrapper_content" > "$wrapper_dst"
      count=$((count + 1))
    fi
  done

  # Reap stale aliases in both namespaces: a wrapper we own but didn't (re)write means its
  # skill was removed or its alias moved namespace (e.g. workflows/agent-pm -> agents/pm).
  local f
  for f in "$wf_dir"/*.md "$ag_dir"/*.md; do
    [[ -f "$f" ]] || continue
    grep -qF "$SKILL_ALIAS_MARKER" "$f" 2>/dev/null || continue   # not ours — leave it alone
    case "$desired" in
      *$'\n'"$f"$'\n'*) : ;;                       # still desired — keep
      *) rm -f "$f"; count=$((count + 1)) ;;       # stale — reap
    esac
  done

  echo "$count"
}

deliver_skills_layout_project() {
  local proot="$1"
  echo "SYNC  $(basename "$proot") (skills-layout)"
  ensure_skills_native_built || { echo "  WARN  skills-native ports unavailable (engine: $PORT_ENGINE)"; return; }
  # 1. Ported skills (bmad-*) -> .claude/skills/ ; --delete so the fork copy fully replaces any
  #    upstream-installed skill of the same name (the bmad-quick-dev collision wins here).
  local sk_dst="$proot/.claude/skills"; mkdir -p "$sk_dst"; local n=0 d nm
  for d in "$SKILLS_NATIVE"/bmad-*/; do
    [[ -d "$d" ]] || continue
    nm="$(basename "$d")"
    rsync -a --delete --exclude='.DS_Store' "$d" "$sk_dst/$nm/"
    n=$((n + 1))
  done
  echo "  OK    skills-native ($n port(s) delivered)"
  # 2. Shared policy home -> _bmad/bmad-shared/
  if [[ -d "$SKILLS_NATIVE/_shared" ]]; then
    mkdir -p "$proot/_bmad/bmad-shared"
    rsync -a --delete --exclude='.DS_Store' "$SKILLS_NATIVE/_shared/" "$proot/_bmad/bmad-shared/"
    echo "  OK    bmad-shared ($(ls "$SKILLS_NATIVE/_shared" 2>/dev/null | wc -l | xargs) policies)"
  fi
  # 3. Hand-authored custom skills (the 4) + scripts + agents (same as old layout)
  local cs; cs=$(sync_skills_for_project "$proot" "sync"); [[ "$cs" -gt 0 ]] && echo "  OK    custom skills ($cs)"
  sync_scripts_for_project "$proot" "sync" >/dev/null 2>&1 || true
  sync_agents_for_project "$proot" "sync" >/dev/null 2>&1 || true
  sync_githooks_for_project "$proot" "sync" >/dev/null 2>&1 || true
  activate_hooks_for_project "$proot" "sync" >/dev/null 2>&1 || true
  # 3b. Colon-command aliases (/bmad:bmm:workflows:<name>) for every delivered skill.
  local ca; ca=$(sync_skill_command_aliases_for_project "$proot"); [[ "$ca" -gt 0 ]] && echo "  OK    colon-command aliases ($ca change(s): written/reaped)"
  # 4. Hooks
  local sdir="$proot/.claude" sfile="$proot/.claude/settings.local.json"
  if [[ -f "$HOOKS_SRC" ]]; then
    mkdir -p "$sdir"
    if [[ -f "$sfile" ]]; then
      local dropped; dropped=$(jq -rn 'input as $b | input as $t | ([$t.hooks[]?[]?.name]) as $tn | [$b.hooks[]?[]? | (.name // "") | select(startswith("bmad-")) | select(($tn|index(.))|not)] | unique | join(", ")' "$sfile" "$HOOKS_SRC" 2>/dev/null)
      jq -n "$JQ_MERGE" "$sfile" "$HOOKS_SRC" > "$sfile.tmp" && mv "$sfile.tmp" "$sfile" && echo "  OK    hooks (upserted)"
      [[ -n "$dropped" ]] && echo "  WARN  dropped non-template bmad- hook(s): $dropped — add them to $HOOKS_SRC (the template owns the bmad- hook namespace; hand-added project hooks do not survive sync)"
    else
      cp "$HOOKS_SRC" "$sfile" && echo "  OK    hooks (created)"
    fi
  fi
  # 5. .worktreeinclude + config backfill + CLAUDE.md sections
  [[ -f "$WORKTREE_INCLUDE_SRC" && ! -f "$proot/.worktreeinclude" ]] && cp "$WORKTREE_INCLUDE_SRC" "$proot/.worktreeinclude"
  [[ -f "$proot/_bmad/bmm/config.yaml" ]] && sync_config_defaults "$proot/_bmad/bmm/config.yaml" "sync" >/dev/null 2>&1 || true
  if [[ -f "$CLAUDEMD_TEMPLATE" && -f "$CLAUDEMD_SYNC" && -f "$proot/CLAUDE.md" ]]; then
    python3 "$CLAUDEMD_SYNC" --sync "$CLAUDEMD_TEMPLATE" "$proot/CLAUDE.md" >/dev/null 2>&1 || true
  fi
}

# --- v6.8 DUAL-LAYOUT TRANSITION (old-layout project opts in) ---
# An OLD-LAYOUT project (its _bmad/bmm/workflows overlay EXISTS) can opt into ALSO receiving the
# skills-native layer alongside that overlay, so the v6.8 migration is gradual and never breaks a
# project mid-flight (MIGRATION-v6.8-skills-plan.md Phase 5: "keep the old overlay until validated").
# Opt-in is a per-project config key so it is DELIBERATE and travels with the project:
#   skills_native_transition: true   (in _bmad/bmm/config.yaml)
# It delivers ONLY the bits the old-layout path does not already cover — the ported skills + the
# bmad-shared policy home. It deliberately does NOT emit the colon-command aliases: the overlay's
# own generated /bmad:bmm:workflows:* commands already provide slash invocation, and adding aliases
# on top re-introduces the skill-routing-surface dilution documented on the cash-recovery pilot
# (bmad-v68-skills-pilot). Only after cutover — when the workflows overlay is removed and the project
# becomes a pure skills-layout project — does deliver_skills_layout_project run and add the aliases.
project_in_skills_transition() {
  local cfg="$1/_bmad/bmm/config.yaml"
  [[ -f "$cfg" ]] || return 1
  grep -qE '^skills_native_transition:[[:space:]]*true([[:space:]]|$)' "$cfg"
}

deliver_skills_native_overlay() {
  local proot="$1"
  ensure_skills_native_built || { echo "  WARN  skills-native ports unavailable (engine: $PORT_ENGINE)"; return; }
  local sk_dst="$proot/.claude/skills"; mkdir -p "$sk_dst"; local n=0 d nm
  for d in "$SKILLS_NATIVE"/bmad-*/; do
    [[ -d "$d" ]] || continue
    nm="$(basename "$d")"
    rsync -a --delete --exclude='.DS_Store' "$d" "$sk_dst/$nm/"
    n=$((n + 1))
  done
  echo "  OK    skills-native transition ($n port(s) delivered alongside overlay)"
  if [[ -d "$SKILLS_NATIVE/_shared" ]]; then
    mkdir -p "$proot/_bmad/bmad-shared"
    rsync -a --delete --exclude='.DS_Store' "$SKILLS_NATIVE/_shared/" "$proot/_bmad/bmad-shared/"
    echo "  OK    bmad-shared ($(ls "$SKILLS_NATIVE/_shared" 2>/dev/null | wc -l | xargs) policies)"
  fi
}

# ============================================================================
# Local-only classification (manifest-aware, content-hashed) — the deadlock fix.
#
# diff alone cannot tell two kinds of "file in target but not in source" apart:
#   (a) a file the sync DELIVERED earlier, since REMOVED/renamed at source
#       → a propagated deletion → safe to purge (rsync --delete handles it).
#   (b) a file that is GENUINE LOCAL WORK in the target → must be protected.
# Before this, BOTH counted as local-only and BLOCKED the project — so removing
# one shared standard at source deadlocked all targets ("Done: 1 synced, N blocked").
#
# The manifest gives the sync a MEMORY of what it delivered to each project — as
# "<sha256>\t<relpath>" lines. A file is PURGEABLE only when it is in the manifest
# AND its current bytes still match the recorded hash (provably our untouched copy).
# Any divergence — absent entry, changed content (locally edited), unreadable hash,
# or no manifest at all — falls through to BLOCKING. This closes the one fail-open a
# name-only manifest had: a file DELIVERED, then LOCALLY EDITED, then REMOVED at
# source would otherwise be purged, silently destroying the local edit. Fail-closed
# in every uncertain state: we auto-delete only what we can prove we put there and
# that no one has touched since.
# ============================================================================
MANIFEST_REL="_bmad/_config/sync-manifest.txt"

# Hash a file's contents (sha256 hex); empty on any failure → caller treats as divergence.
hash_file() {
  shasum -a 256 "$1" 2>/dev/null | awk '{print $1}'
}

# Emit the delivered-file set as "<sha256>\t<relpath>" lines: every file under
# SOURCE/<SYNC_DIRS>, path relative to the workflows dir (e.g. "shared/STANDARDS.md").
# After an rsync of SYNC_DIRS this is exactly what was laid down, with the exact
# bytes — so it == the delivered set plus the fingerprint to detect later local edits.
compute_source_manifest() {
  local d rel
  for d in "${SYNC_DIRS[@]}"; do
    [[ -d "$SOURCE/$d" ]] || continue
    while IFS= read -r rel; do
      printf '%s\t%s\n' "$(hash_file "$SOURCE/$rel")" "$rel"
    done < <( cd "$SOURCE" && find "$d" -type f ! -name '.DS_Store' )
  done | LC_ALL=C sort -t$'\t' -k2
}

# Recorded hash for a path in the manifest ("" if absent). Exact field match.
manifest_recorded_hash() {
  awk -F'\t' -v p="$2" '$2==p {print $1; exit}' "$1" 2>/dev/null
}

# Classify a project's local-only content against its prior manifest. Sets two
# newline-delimited globals: LOCAL_ONLY_BLOCKING (protect) and LOCAL_ONLY_PURGEABLE.
# Args: $1 = target workflows dir, $2 = project_root
classify_local_only() {
  local target="$1" project_root="$2"
  local manifest="$project_root/$MANIFEST_REL"
  LOCAL_ONLY_BLOCKING=""
  LOCAL_ONLY_PURGEABLE=""
  local have_manifest=false
  [[ -f "$manifest" ]] && have_manifest=true

  local d rel legacy is_legacy src_dir_missing recorded current
  for d in "${SYNC_DIRS[@]}"; do
    [[ -d "$target/$d" ]] || continue
    src_dir_missing=false
    [[ -d "$SOURCE/$d" ]] || src_dir_missing=true
    while IFS= read -r rel; do
      [[ -z "$rel" ]] && continue
      [[ -f "$SOURCE/$rel" ]] && continue          # still in source — not local-only
      is_legacy=false
      for legacy in "${LEGACY_SUBPATHS_TO_REMOVE[@]}"; do
        [[ "$rel" == "$legacy" || "$rel" == "$legacy"/* ]] && { is_legacy=true; break; }
      done
      $is_legacy && continue                        # migration step removes these
      if $src_dir_missing; then
        LOCAL_ONLY_BLOCKING+="$rel"$'\n'            # whole source dir gone — anomaly, protect
        continue
      fi
      # Purge ONLY a file we delivered AND whose bytes are unchanged since delivery.
      recorded=""
      $have_manifest && recorded="$(manifest_recorded_hash "$manifest" "$rel")"
      if [[ -n "$recorded" ]]; then
        current="$(hash_file "$target/$rel")"
        if [[ -n "$current" && "$current" == "$recorded" ]]; then
          LOCAL_ONLY_PURGEABLE+="$rel"$'\n'         # delivered & untouched → safe to purge
        else
          LOCAL_ONLY_BLOCKING+="$rel"$'\n'          # locally edited since delivery → protect
        fi
      else
        LOCAL_ONLY_BLOCKING+="$rel"$'\n'            # never delivered (or no manifest) → protect
      fi
    done < <( cd "$target" && find "$d" -type f ! -name '.DS_Store' )
  done
}

# Delivery contract (fork-gap 2026-07-05 "sync has no delivery contract", parts a+b):
# after a project is synced, make "did this land durably?" VISIBLE instead of leaving a
# silently-dirty tree. Reports the count of uncommitted BMAD-managed path changes
# (tracked-modified vs untracked); with --commit, scoped-commits just those paths.
# Gitignored paths are neither reported nor committed (git never sees them) — that's the
# correct conservative behavior; we never force-add ignored files.
summarize_bmad_delivery() {
  local project_root="$1"
  $CHECK_ONLY && return 0
  git -C "$project_root" rev-parse --is-inside-work-tree &>/dev/null || return 0
  local bmad_paths=(_bmad .claude/skills .claude/commands/bmad CLAUDE.md)
  local status total untracked tracked
  status=$(git -C "$project_root" status --porcelain -- "${bmad_paths[@]}" 2>/dev/null || true)
  [[ -z "$status" ]] && return 0
  total=$(printf '%s\n' "$status" | grep -c . || true)
  untracked=$(printf '%s\n' "$status" | grep -c '^??' || true)
  tracked=$(( total - untracked ))
  echo "  ℹ  delivery: $total BMAD path change(s) uncommitted ($tracked tracked-modified, $untracked untracked)"
  if $COMMIT_SYNCED; then
    git -C "$project_root" add -- "${bmad_paths[@]}" 2>/dev/null || true
    if git -C "$project_root" diff --cached --quiet -- "${bmad_paths[@]}" 2>/dev/null; then
      echo "         nothing stageable (all changes gitignored) — commit skipped"
    elif git -C "$project_root" commit -q -m "chore(bmad): deliver synced fork workflows/skills/commands" -- "${bmad_paths[@]}" 2>/dev/null; then
      echo "  OK    delivery: scoped-committed BMAD path changes"
    else
      echo "  ⚠  delivery: scoped commit failed — resolve by hand"
    fi
  else
    echo "         run with --commit to deliver them, or commit by hand"
  fi
}

synced=0
skipped=0
stale=0
blocked=0
seen_targets=()

while IFS= read -r target || [[ -n "$target" ]]; do
  target="${target%%[[:space:]]}"
  target="${target##[[:space:]]}"
  [[ -z "$target" || "$target" == \#* ]] && continue

  # --only <path>: process just this one project (match its root or workflows path); skip the rest.
  if [[ -n "$ONLY_TARGET" ]]; then
    only_proot="${target%/_bmad/bmm/workflows}"
    [[ "$target" != "$ONLY_TARGET" && "$only_proot" != "$ONLY_TARGET" ]] && continue
  fi

  # Deduplicate
  for seen in "${seen_targets[@]+"${seen_targets[@]}"}"; do
    if [[ "$seen" == "$target" ]]; then
      continue 2
    fi
  done
  seen_targets+=("$target")

  if [[ ! -d "$target" ]]; then
    # No old-layout workflows dir. If it's a real skills-layout project (v6.8 install), deliver the
    # migrated skills layer instead of skipping. Otherwise it's a stale/empty target — skip.
    sl_proot="${target%/_bmad/bmm/workflows}"
    if [[ "$sl_proot" != "$target" && -d "$sl_proot/.claude/skills" ]]; then
      if $CHECK_ONLY; then
        echo "CHECK $(basename "$sl_proot") (skills-layout — would deliver migrated ports + bmad-shared)"
      else
        deliver_skills_layout_project "$sl_proot"
        synced=$((synced + 1))
      fi
      continue
    fi
    echo "SKIP  $target (not found — run onboard-project.sh to set this project up, or remove the stale line from ~/.bmad-targets)"
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
    done

    # Local-only classification (manifest-aware): genuine local work (would be
    # DELETED — protect) vs propagated deletions (source removed; would be purged).
    classify_local_only "$target" "$project_root"
    if [[ -n "$LOCAL_ONLY_BLOCKING" ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ⚠  LOCAL-ONLY work (would be DELETED on sync — pull or --force):"
      echo "$LOCAL_ONLY_BLOCKING" | sed '/^$/d; s/^/     /'
    fi
    if [[ -n "$LOCAL_ONLY_PURGEABLE" ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↻  propagated deletion(s) (source removed; purged on sync):"
      echo "$LOCAL_ONLY_PURGEABLE" | sed '/^$/d; s/^/     /'
    fi

    # Skip-if-dirty guard preview (fork-gap 2026-07-10): would a real sync REFUSE this target?
    check_dirty_managed="$(bmad_managed_dirty "$project_root")"
    if [[ -n "$check_dirty_managed" ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ⛔ uncommitted BMAD-managed changes — sync would SKIP this target (commit, or --force):"
      echo "$check_dirty_managed" | sed 's/^/     /'
    fi

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

    # Check custom agent personas sync
    agents_drift=$(sync_agents_for_project "$project_root" "check")
    if [[ "$agents_drift" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  agents ($agents_drift agent(s) missing/outdated)"
    fi

    # Check git-hook entrypoints sync + activation (STD-HOOKACTIVATE-001)
    githooks_drift=$(sync_githooks_for_project "$project_root" "check")
    if [[ "$githooks_drift" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  githooks ($githooks_drift entrypoint(s) missing/outdated)"
    fi
    hooks_activation_drift=$(activate_hooks_for_project "$project_root" "check")
    if [[ "$hooks_activation_drift" -gt 0 ]]; then
      if ! $dirty; then
        echo "STALE $project"
        dirty=true
      fi
      echo "  ↳  git-hook activation (core.hooksPath not set to .githooks)"
    fi

    if project_in_skills_transition "$project_root"; then
      echo "  ↳  skills-native transition ON — sync delivers $(ls -d "$SKILLS_NATIVE"/bmad-*/ 2>/dev/null | wc -l | xargs) ported skill(s) + bmad-shared alongside overlay"
    fi

    if $dirty; then
      stale=$((stale + 1))
    else
      echo "OK    $project"
    fi
  else
    # --- Deterministic skip-if-dirty guard (fork-gap 2026-07-10) ---
    # The destructive rsync -a --delete fan-out below overwrites BMAD-managed paths in the
    # target. If a peer session has uncommitted TRACKED modifications there, --delete would
    # clobber working-tree edits git can't recover. Refuse THIS target (safe-partial: the
    # fan-out continues to the clean projects) unless --force. Only tracked modifications
    # count — untracked local-only content is handled by classify_local_only + the manifest.
    # SAFE-PARTIAL over REFUSE-ALL by design: this workspace is perpetually multi-session, so
    # refuse-all would never fan out. Over-block note: an uncommitted PRIOR sync (ran without
    # --commit) also trips this — the fix is `sync --commit` (leaves a clean tree) or --force.
    if ! $FORCE; then
      dirty_managed="$(bmad_managed_dirty "$project_root")"
      if [[ -n "$dirty_managed" ]]; then
        echo "BLOCK $project — uncommitted TRACKED changes in BMAD-managed paths (a peer session may be mid-edit; --delete would clobber them):"
        echo "$dirty_managed" | sed 's/^/    /'
        echo "  Resolve (pick one):"
        echo "    • Commit them (often an uncommitted prior sync):  git -C $project_root commit -- ${BMAD_MANAGED_GIT_PATHS[*]}   (or re-run sync with --commit)"
        echo "    • Override (DESTRUCTIVE — overwrites the edits):   $0 --force"
        blocked=$((blocked + 1))
        continue
      fi
    fi

    # --- Pre-sync safety check: local-only content (manifest-aware) ---
    classify_local_only "$target" "$project_root"

    if [[ -n "$LOCAL_ONLY_BLOCKING" ]] && ! $FORCE; then
      echo "BLOCK $project — local-only content NOT delivered by sync (protected from deletion):"
      echo "$LOCAL_ONLY_BLOCKING" | sed '/^$/d; s/^/    /'
      echo "  Resolve (pick one):"
      echo "    • Promote into the fork:  $0 --pull $target   (then commit + re-sync)"
      echo "    • Discard local-only:     $0 --force          (DESTRUCTIVE — overwrites & deletes local-only)"
      if [[ -n "$LOCAL_ONLY_PURGEABLE" ]]; then
        echo "  (Also $(echo "$LOCAL_ONLY_PURGEABLE" | grep -c .) propagated-deletion file(s) pending purge once unblocked.)"
      fi
      blocked=$((blocked + 1))
      continue
    fi

    if [[ -n "$LOCAL_ONLY_PURGEABLE" ]]; then
      echo "SYNC  $project (purging $(echo "$LOCAL_ONLY_PURGEABLE" | grep -c .) propagated deletion(s))"
    else
      echo "SYNC  $project"
    fi

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
        dropped_hooks=$(jq -rn 'input as $b | input as $t | ([$t.hooks[]?[]?.name]) as $tn | [$b.hooks[]?[]? | (.name // "") | select(startswith("bmad-")) | select(($tn|index(.))|not)] | unique | join(", ")' "$settings_file" "$HOOKS_SRC" 2>/dev/null)
        jq -n "$JQ_MERGE" "$settings_file" "$HOOKS_SRC" > "$settings_file.tmp"
        mv "$settings_file.tmp" "$settings_file"
        echo "  OK    hooks (upserted)"
        [[ -n "$dropped_hooks" ]] && echo "  WARN  dropped non-template bmad- hook(s): $dropped_hooks — add them to $HOOKS_SRC (the template owns the bmad- hook namespace; hand-added project hooks do not survive sync)"
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

    # Sync custom agent personas from custom/agents/ (+ generate slash wrappers)
    agents_synced=$(sync_agents_for_project "$project_root" "sync")
    if [[ "$agents_synced" -gt 0 ]]; then
      echo "  OK    agents ($agents_synced agent(s) synced)"
    fi

    # Sync canonical git-hook entrypoints from custom/githooks/ + activate them
    # (STD-HOOKACTIVATE-001) so distributed gates are reliably WIRED, not silently off.
    githooks_synced=$(sync_githooks_for_project "$project_root" "sync")
    if [[ "$githooks_synced" -gt 0 ]]; then
      echo "  OK    githooks ($githooks_synced entrypoint(s) synced)"
    fi
    hooks_activated=$(activate_hooks_for_project "$project_root" "sync")
    if [[ "$hooks_activated" -gt 0 ]]; then
      echo "  OK    git-hook activation (core.hooksPath=.githooks)"
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

    # Delivered-file manifest: memory of what this sync laid down, so the NEXT
    # run can tell a propagated deletion (purge) from genuine local work (protect).
    if [[ -d "$stamp_dir" ]]; then
      compute_source_manifest > "$stamp_dir/sync-manifest.txt"
    fi

    # v6.8 dual-layout transition (opt-in via `skills_native_transition: true` in config.yaml):
    # also deliver the skills-native layer alongside the commands overlay. Overlay stays until
    # cutover (MIGRATION-v6.8-skills-plan.md Phase 5).
    if project_in_skills_transition "$project_root"; then
      deliver_skills_native_overlay "$project_root"
    fi

    # Delivery contract: report (and optionally --commit) the synced BMAD paths.
    summarize_bmad_delivery "$project_root"

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
