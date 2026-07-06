#!/usr/bin/env bash
# ============================================================================
# bmad-deploy.sh — universal post-merge deploy executable
#
# Implements the contract in _bmad/bmm/workflows/shared/deployment-to-prod.md.
# Reads per-project values from _bmad/bmm/config.yaml under the `deploy:` key.
# Exit-code grammar matches §6 of that document.
#
# This file is synced from ~/bmad-method-v6/custom/scripts/bmad-deploy.sh into
# every BMAD-managed project's ./scripts/. DO NOT edit in projects directly —
# edit the source in the fork and re-sync.
# ============================================================================

set -euo pipefail

# Resolve project root from git, not from $PWD.
if ! PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  echo "✗ Not inside a git repository." >&2
  exit 16
fi
cd "$PROJECT_ROOT"

CONFIG="$PROJECT_ROOT/_bmad/bmm/config.yaml"
if [[ ! -f "$CONFIG" ]]; then
  echo "✗ Missing config: $CONFIG" >&2
  echo "  This script requires a project with the BMAD config installed." >&2
  exit 17
fi

# --- yq compatibility shim -------------------------------------------------
# Both Mike Farah's Go yq (4.x) and the Python wrapper are common on dev
# machines. We use `yq eval` syntax which works on both. If yq is missing,
# fall back to grep/awk for the few values we need.
have_yq=false
if command -v yq >/dev/null 2>&1; then
  have_yq=true
fi

cfg_get() {
  # cfg_get <yaml-path> [default]
  local path="$1"
  local default="${2:-}"
  if $have_yq; then
    local val
    val=$(yq eval "$path // \"\"" "$CONFIG" 2>/dev/null || true)
    if [[ -z "$val" || "$val" == "null" ]]; then
      echo "$default"
    else
      echo "$val"
    fi
  else
    # Minimal yaml fallback: grep for "key:" under the deploy: section.
    # Only handles flat key: value pairs; lists fall through to default.
    local key
    key=$(echo "$path" | sed -E 's/^\.deploy\.//')
    local val
    val=$(awk -v k="$key" '
      /^deploy:/ { in_d=1; next }
      in_d && /^[^[:space:]]/ { in_d=0 }
      in_d && $1 == k":" { sub(/^[^:]*: */,""); print; exit }
    ' "$CONFIG")
    if [[ -z "$val" ]]; then
      echo "$default"
    else
      # Strip surrounding quotes if present.
      echo "$val" | sed -E 's/^"(.*)"$/\1/; s/^'\''(.*)'\''$/\1/'
    fi
  fi
}

cfg_get_list() {
  # cfg_get_list <yaml-path> — prints one item per line.
  local path="$1"
  if $have_yq; then
    yq eval "$path[]" "$CONFIG" 2>/dev/null || true
  else
    # awk-based list parser for paths like .deploy.deploy_irrelevant_paths
    local key
    key=$(echo "$path" | sed -E 's/^\.deploy\.//')
    awk -v k="$key" '
      /^deploy:/ { in_d=1; next }
      in_d && /^[^[:space:]]/ { in_d=0 }
      in_d && $0 ~ "^[[:space:]]+" k ":" { in_l=1; next }
      in_l && /^[[:space:]]+- / { sub(/^[[:space:]]+- */,""); print; next }
      in_l { in_l=0 }
    ' "$CONFIG"
  fi
}

# --- 1. Opt-out -------------------------------------------------------------

contract=$(cfg_get '.deploy.bmad_contract' '')
if [[ "$contract" == "skip" ]]; then
  echo "→ Project opts out of the BMAD deploy contract (deploy.bmad_contract: skip)."
  echo "  Defer to project CLAUDE.md for deploy choreography."
  exit 99
fi

# --- 2. Validate required config -------------------------------------------

build_command=$(cfg_get '.deploy.build_command' '')
deploy_command=$(cfg_get '.deploy.deploy_command' '')
dep_state_check=$(cfg_get '.deploy.dep_state_check' '')
dep_install_command=$(cfg_get '.deploy.dep_install_command' '')

missing=()
[[ -z "$build_command" ]] && missing+=("deploy.build_command")
[[ -z "$deploy_command" ]] && missing+=("deploy.deploy_command")
[[ -z "$dep_state_check" ]] && missing+=("deploy.dep_state_check")
[[ -z "$dep_install_command" ]] && missing+=("deploy.dep_install_command")

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "✗ Missing required deploy.* fields in $CONFIG:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  echo "" >&2
  echo "  See _bmad/bmm/workflows/shared/deployment-to-prod.md §5 for the schema." >&2
  exit 14
fi

# Validate the dep_install_command is lockfile-clean.
case "$dep_install_command" in
  "npm ci"|"pnpm install --frozen-lockfile"|"yarn install --immutable")
    : # allowed
    ;;
  *)
    echo "✗ deploy.dep_install_command must be lockfile-clean." >&2
    echo "  Got: '$dep_install_command'" >&2
    echo "  Allowed: 'npm ci', 'pnpm install --frozen-lockfile', 'yarn install --immutable'" >&2
    echo "  See _bmad/bmm/workflows/shared/deployment-to-prod.md §3b." >&2
    exit 15
    ;;
esac

# --- 3. Dirty-tree filter --------------------------------------------------

# Collect all dirty paths (modified + untracked).
mapfile -t dirty_paths < <(git status --porcelain | sed -E 's/^.{3}//' | sort -u)

if [[ ${#dirty_paths[@]} -gt 0 ]]; then
  mapfile -t irrelevant_globs < <(cfg_get_list '.deploy.deploy_irrelevant_paths')

  # Fork-synced tooling scripts (delivered into ./scripts/ by sync-bmad-workflows.sh)
  # are deploy-irrelevant BY NATURE — they are tooling, never part of the build
  # output — but a project's OWN uncommitted script (e.g. scripts/deploy-prod.sh)
  # must still block. The sync writes the exact basenames it delivered to this
  # manifest so the filter can tell fork-owned from project-owned WITHOUT a broad
  # `scripts/` exemption. Missing manifest (project not yet re-synced) → no exemption
  # → today's behavior, so this is a strict de-false-positiving with no regression.
  declare -A synced_scripts=()
  synced_manifest=".claude/bmad-synced-scripts.txt"
  if [[ -f "$synced_manifest" ]]; then
    while IFS= read -r _s; do
      [[ -n "$_s" ]] && synced_scripts["scripts/$_s"]=1
    done < "$synced_manifest"
  fi

  # Build a set of "still-dirty" paths after irrelevant-glob subtraction.
  still_dirty=()
  for path in "${dirty_paths[@]}"; do
    [[ -z "$path" ]] && continue
    is_irrelevant=false
    for glob in "${irrelevant_globs[@]}"; do
      [[ -z "$glob" ]] && continue
      # Trailing-slash glob is a directory prefix match. Bare glob is a prefix match too.
      case "$path" in
        "$glob"*|"$glob") is_irrelevant=true; break ;;
      esac
    done
    # A fork-synced script (exact basename in the manifest) is deploy-irrelevant too.
    if ! $is_irrelevant && [[ -n "${synced_scripts[$path]:-}" ]]; then
      is_irrelevant=true
    fi
    $is_irrelevant || still_dirty+=("$path")
  done

  if [[ ${#still_dirty[@]} -gt 0 ]]; then
    echo "✗ Dirty working tree has deploy-relevant changes." >&2
    echo "  These paths are dirty and NOT in deploy.deploy_irrelevant_paths:" >&2
    printf '    %s\n' "${still_dirty[@]}" >&2
    echo "" >&2
    echo "  Commit, stash, or add to deploy_irrelevant_paths if appropriate." >&2
    exit 10
  fi

  ignored_count=${#dirty_paths[@]}
  echo "→ ${ignored_count} dirty path(s) matched deploy_irrelevant_paths and were ignored."
fi

# --- 3a. Stale-checkout guard ----------------------------------------------
# A deploy ships the BUILD OF THE CURRENT CHECKOUT. If that checkout is behind
# origin/<default-branch> — e.g. a feature worktree branched before a parallel
# session's PR merged — the build is MISSING those commits, and deploying it
# SILENTLY REVERTS them in production. (accounting-tools 2026-05-30: a deploy
# from a stale worktree rolled back a just-merged worklist redesign.)
#
# The check compares deploy-relevant CONTENT (a commit-to-commit tree diff),
# NOT commit ancestry — so a freshly squash-merged worktree, whose HEAD
# diverges from main by commit but is identical by tree, still passes. The
# deploy_irrelevant_paths globs are reused as diff excludes so a docs-only or
# _bmad-only delta on main does not false-positive the guard.
default_branch=$(cfg_get '.deploy.default_branch' 'main')

if git fetch origin "$default_branch" --quiet 2>/dev/null \
   && git rev-parse --verify --quiet "origin/${default_branch}^{commit}" >/dev/null; then

  mapfile -t stale_irrelevant_globs < <(cfg_get_list '.deploy.deploy_irrelevant_paths')
  stale_excludes=()
  for glob in "${stale_irrelevant_globs[@]}"; do
    [[ -z "$glob" ]] && continue
    stale_excludes+=( ":(exclude)${glob}" )
  done

  if ! git diff --quiet HEAD "origin/${default_branch}" -- . "${stale_excludes[@]}" 2>/dev/null; then
    behind=$(git rev-list --count "HEAD..origin/${default_branch}" 2>/dev/null || echo '?')
    echo "✗ Stale checkout — deploy-relevant content differs from origin/${default_branch}." >&2
    echo "  origin/${default_branch} has ${behind} commit(s) not in this checkout. Deploying now" >&2
    echo "  would ship a build MISSING them and REVERT them in production." >&2
    echo "" >&2
    echo "  Deploy from the current ${default_branch} tip instead — e.g. a fresh worktree:" >&2
    echo "      git fetch origin ${default_branch}" >&2
    echo "      git worktree add /tmp/deploy-head origin/${default_branch}" >&2
    echo "      cd /tmp/deploy-head && ./scripts/bmad-deploy.sh" >&2
    echo "" >&2
    echo "  (Intentional off-main deploy? Use deploy-hotfix.sh or set deploy.bmad_contract: skip.)" >&2
    exit 19
  fi
else
  echo "→ Stale-checkout guard skipped (could not fetch origin/${default_branch})." >&2
fi

# --- 4. Dep-state precondition ---------------------------------------------

if [[ ! -e "$PROJECT_ROOT/$dep_state_check" ]]; then
  echo "→ Dependencies missing ($dep_state_check not found). Running: $dep_install_command"
  if ! $dep_install_command; then
    echo "✗ Dep install failed." >&2
    exit 11
  fi
  # Sanity check the install populated the expected entry.
  if [[ ! -e "$PROJECT_ROOT/$dep_state_check" ]]; then
    echo "✗ Dep install completed but $dep_state_check is still missing." >&2
    echo "  Check whether deploy.dep_state_check points at a valid sentinel." >&2
    exit 11
  fi
fi

# --- 4b. Auth pre-flight (fail fast BEFORE the build) ----------------------
# Generic guard: when the deploy targets Cloudflare via wrangler, verify the
# API token is valid up front. An expired/revoked CLOUDFLARE_API_TOKEN otherwise
# only surfaces AFTER a full build, as a confusing wrangler stack trace
# (API errors 9109 / 10000). Catching it here turns a wasted build + cryptic
# failure into a fast, actionable message. Non-wrangler deploy targets skip this.
case "$deploy_command" in
  *wrangler*)
    echo "→ Checking Cloudflare auth (wrangler whoami)…"
    if ! npx wrangler whoami >/dev/null 2>&1; then
      echo "✗ Cloudflare auth failed — wrangler cannot authenticate." >&2
      echo "  CLOUDFLARE_API_TOKEN is missing, expired, or revoked (API 9109/10000)." >&2
      echo "  Re-mint a token (Pages:Edit), set CLOUDFLARE_API_TOKEN in ~/.secrets," >&2
      echo "  then restart the session OR re-source it for this run:" >&2
      echo "      set -a; source ~/.secrets; set +a; ./scripts/bmad-deploy.sh" >&2
      exit 18
    fi
    ;;
esac

# --- 5. Build --------------------------------------------------------------

echo "→ Running build: $build_command"
if ! $build_command; then
  echo "✗ Build failed." >&2
  exit 12
fi

# --- 6. Deploy -------------------------------------------------------------

echo "→ Running deploy: $deploy_command"
success_pattern=$(cfg_get '.deploy.success_pattern' '')

if [[ -n "$success_pattern" ]]; then
  # Capture output to assert success pattern.
  deploy_log=$(mktemp -t bmad-deploy-XXXXXX.log)
  trap 'rm -f "$deploy_log"' EXIT
  if ! $deploy_command 2>&1 | tee "$deploy_log"; then
    echo "✗ Deploy command exited non-zero." >&2
    exit 13
  fi
  if ! grep -qE "$success_pattern" "$deploy_log"; then
    echo "✗ Deploy command exited zero but success pattern not found in output." >&2
    echo "  Pattern: $success_pattern" >&2
    exit 13
  fi
else
  if ! $deploy_command; then
    echo "✗ Deploy command exited non-zero." >&2
    exit 13
  fi
fi

echo "✓ Deploy complete."
exit 0
