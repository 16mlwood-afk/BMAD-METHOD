#!/usr/bin/env bash
#
# onboard-project.sh — one-command BMAD-fork onboarding for a new project.
#
# Brings a directory from "nothing" to "fully wired to the Mason-BMAD fork,
# same layout as all other projects" with no manual steps and no hurdles.
#
# What it does (idempotent):
#   1. git init (if not already a repo)
#   2. Clone the reference project's _bmad/ base (the fork's source-of-truth
#      install — see ~/.bmad-reference) into the new project
#   3. Sanitize project-specific bits (project_name, project_phase, clear the
#      reference's sidecar memory + stale sync stamp)
#   4. Create CLAUDE.md from the fork template (so the sync can manage its sections)
#   5. Register the project in ~/.bmad-targets
#   6. Run sync-bmad-workflows.sh → custom workflows, skills, hooks, commands, CLAUDE.md sections
#   7. Detect/record TOPOLOGY (standalone | fork-of-upstream) — for a personal fork of an
#      external upstream, record the upstream remote + add a CLAUDE.md sync-safety section
#      (the upstream destructive-op guard is a global hook that self-gates on this stamp)
#   8. Write the COMPLETION MARKER: an `onboarding:` stamp block in _bmad/bmm/config.yaml
#      (machine-checkable: playbook_version/onboarded_at/topology/guarantees), a human-facing
#      ONBOARDING.md, and a `project-onboarding-done` project memory
#
# Usage:
#   onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed]
#                      [--topology standalone|fork-of-upstream] [--upstream <url>] [--force]
#   onboard-project.sh --restamp [<project-dir>]   # rewrite the marker ONLY (no re-clone/sync) —
#                                                   # for a repo onboarded before the marker existed,
#                                                   # or after the fork bumps the playbook version
#
#   <project-dir>   defaults to the current directory
#   --name          defaults to the directory basename
#   --phase         defaults to greenfield (new build)
#   --topology      standalone (default) or fork-of-upstream; auto-detected as fork-of-upstream
#                   when an `upstream` git remote exists or --upstream is given
#   --upstream      URL of the external upstream this repo forks; implies --topology fork-of-upstream
#                   and adds an `upstream` remote if absent
#   --force         re-seed even if _bmad already exists (DESTRUCTIVE to _bmad)
#   --restamp       rewrite the completion marker only; requires _bmad to already exist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-bmad-workflows.sh"
CLAUDEMD_TEMPLATE="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/CLAUDE.md.template"
REFERENCE_FILE="$HOME/.bmad-reference"
TARGETS_FILE="$HOME/.bmad-targets"

PROJECT_DIR=""
PROJECT_NAME=""
PROJECT_PHASE="greenfield"
TOPOLOGY=""
UPSTREAM_URL=""
FORCE=false
RESTAMP=false

VERSION_FILE="$SCRIPT_DIR/onboarding-playbook.version"
PLAYBOOK_VERSION="$( [[ -f "$VERSION_FILE" ]] && grep -oE '[0-9]+' "$VERSION_FILE" | head -1 || echo 1 )"
PLAYBOOK_VERSION="${PLAYBOOK_VERSION:-1}"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)     PROJECT_NAME="$2"; shift 2 ;;
    --phase)    PROJECT_PHASE="$2"; shift 2 ;;
    --topology) TOPOLOGY="$2"; shift 2 ;;
    --upstream) UPSTREAM_URL="$2"; shift 2 ;;
    --force)    FORCE=true; shift ;;
    --restamp)  RESTAMP=true; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *)  PROJECT_DIR="$1"; shift ;;
  esac
done

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"
mkdir -p "$PROJECT_DIR"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# Resolve the CANONICAL repo root for IDENTITY (project name + memory slug). If PROJECT_DIR is a
# git worktree (…/.claude/worktrees/<branch>/), this resolves to the MAIN checkout — so restamping
# from a worktree (the common case, since the tracked marker files need a PR) uses the project's
# real identity, not the worktree's basename/path. The in-repo writes still target PROJECT_DIR
# (the worktree) so they can be committed; only name + slug follow CANON_ROOT. Falls back to
# PROJECT_DIR when not in a git repo yet (a brand-new onboard, which is canonical anyway).
CANON_ROOT="$PROJECT_DIR"
if [[ -e "$PROJECT_DIR/.git" ]]; then
  _gcd="$(git -C "$PROJECT_DIR" rev-parse --git-common-dir 2>/dev/null || true)"
  if [[ -n "$_gcd" ]]; then
    case "$_gcd" in /*) ;; *) _gcd="$PROJECT_DIR/$_gcd" ;; esac
    CANON_ROOT="$(cd "$(dirname "$_gcd")" 2>/dev/null && pwd || echo "$PROJECT_DIR")"
  fi
fi
PROJECT_NAME="${PROJECT_NAME:-$(basename "$CANON_ROOT")}"

case "$PROJECT_PHASE" in
  greenfield|brownfield|mixed) ;;
  *) echo "ERROR: --phase must be greenfield|brownfield|mixed (got: $PROJECT_PHASE)" >&2; exit 1 ;;
esac

# ── Topology + completion-marker helpers (used by both normal flow and --restamp) ──

# Resolve TOPOLOGY (standalone | fork-of-upstream). Must run AFTER git exists (init or restamp):
# an `upstream` remote, an explicit --upstream URL, or --topology fork-of-upstream all imply a fork.
resolve_topology() {
  local existing=""
  if [[ -d "$PROJECT_DIR/.git" ]]; then
    existing="$(git -C "$PROJECT_DIR" remote get-url upstream 2>/dev/null || true)"
  fi
  if [[ -n "$UPSTREAM_URL" ]]; then
    TOPOLOGY="fork-of-upstream"
  elif [[ -z "$TOPOLOGY" && -n "$existing" ]]; then
    TOPOLOGY="fork-of-upstream"; UPSTREAM_URL="$existing"
  fi
  TOPOLOGY="${TOPOLOGY:-standalone}"
  case "$TOPOLOGY" in
    standalone|fork-of-upstream) ;;
    *) echo "ERROR: --topology must be standalone|fork-of-upstream (got: $TOPOLOGY)" >&2; exit 1 ;;
  esac
  if [[ "$TOPOLOGY" == "fork-of-upstream" && -n "$UPSTREAM_URL" && -z "$existing" && -d "$PROJECT_DIR/.git" ]]; then
    git -C "$PROJECT_DIR" remote add upstream "$UPSTREAM_URL" 2>/dev/null \
      && echo "  ✓ added 'upstream' remote → $UPSTREAM_URL" || true
  fi
  if [[ -z "$UPSTREAM_URL" && -n "$existing" ]]; then UPSTREAM_URL="$existing"; fi
  return 0
}

write_onboarding_md() {
  local today="$1" up_display="—"
  if [[ -n "$UPSTREAM_URL" ]]; then up_display="$UPSTREAM_URL"; fi
  cat > "$PROJECT_DIR/ONBOARDING.md" <<EOF
# Onboarding

This repository was onboarded to the **Mason-BMAD fork** by \`onboard-project.sh\`.
_Generated file — do not hand-edit; re-run \`onboard-project.sh --restamp\` to regenerate._

| Field | Value |
|---|---|
| Onboarding playbook version | $PLAYBOOK_VERSION |
| Onboarded at | $today |
| Topology | $TOPOLOGY |
| Upstream remote | $up_display |
| Project | $PROJECT_NAME |

## What this guarantees
- Fork-synced custom workflows, skills, hooks, and slash commands (\`sync-bmad-workflows.sh\`).
- A thin, pointer-based \`CLAUDE.md\` (STD-CLAUDE-001).
- Worktree + enforcement PreToolUse hooks installed.
- Global memory doctrine (the \`~/.claude\` memory library).

## Machine-checkable marker
The canonical stamp lives in \`_bmad/bmm/config.yaml\` under the \`onboarding:\` key. A SessionStart
hook (\`check-onboarding-version.sh\`) reads it and warns when this repo was onboarded under an older
playbook than the fork currently ships. Re-stamp after a bump:

    ~/bmad-method-v6/onboard-project.sh --restamp
EOF
  echo "  ✓ wrote ONBOARDING.md"
}

write_upstream_claude_section() {
  local claude="$PROJECT_DIR/CLAUDE.md"
  [[ -f "$claude" ]] || return 0
  if grep -qE '^## Upstream fork' "$claude"; then return 0; fi
  local up_display="the external upstream"
  if [[ -n "$UPSTREAM_URL" ]]; then up_display="\`$UPSTREAM_URL\`"; fi
  cat >> "$claude" <<EOF

## Upstream fork — sync safety
This repo is a personal fork of $up_display (git remote \`upstream\`).
- **Pull updates:** \`git fetch upstream && git rebase upstream/<branch>\`.
- **Never** \`git push upstream\`, force-push to upstream, or \`git reset --hard upstream/*\` — a
  PreToolUse guard (\`bmad-upstream-guard.sh\`) blocks these. Override only when you truly mean it:
  prefix the command with \`BMAD_ALLOW_UPSTREAM_PUSH=1\`.
- **Deliver your work to your own \`origin\`** via PRs — never to upstream.
EOF
  echo "  ✓ added 'Upstream fork — sync safety' section to CLAUDE.md"
}

write_onboarding_memory() {
  local today="$1"
  # Memory slug follows the CANONICAL repo root, never a worktree path (see CANON_ROOT above).
  local slug; slug="$(printf '%s' "$CANON_ROOT" | sed 's#/#-#g')"
  local memdir="$HOME/.claude/projects/$slug/memory"
  mkdir -p "$memdir"
  local up_note=""
  if [[ "$TOPOLOGY" == "fork-of-upstream" ]]; then up_note=" Upstream: ${UPSTREAM_URL:-(recorded)}."; fi
  cat > "$memdir/project-onboarding-done.md" <<EOF
---
name: project-onboarding-done
description: This repo was onboarded to the Mason-BMAD fork under onboarding playbook v$PLAYBOOK_VERSION on $today (topology: $TOPOLOGY).
metadata:
  type: project
---

Onboarded to the Mason-BMAD fork via \`onboard-project.sh\` under **playbook v$PLAYBOOK_VERSION** on $today.

- **Topology:** $TOPOLOGY.$up_note
- **Guarantees:** fork-synced workflows/skills/hooks/commands; thin pointer CLAUDE.md (STD-CLAUDE-001); worktree + enforcement hooks; global memory doctrine.
- **Canonical stamp:** \`_bmad/bmm/config.yaml\` → \`onboarding:\` block (machine-checkable; the SessionStart \`check-onboarding-version.sh\` hook reads it).

**Why:** lets a cold session tell a fully-onboarded repo from a pre-playbook one, and detect when the fork's onboarding playbook has advanced past this repo's stamp.
**How to apply:** trust the stamp as source of truth. If the SessionStart detector reports playbook drift, re-stamp via \`onboard-project.sh --restamp\` — don't hand-edit the marker.
EOF
  local memidx="$memdir/MEMORY.md"
  [[ -f "$memidx" ]] || printf '# Memory Index\n\n## Project\n' > "$memidx"
  if ! grep -q 'project-onboarding-done' "$memidx"; then
    grep -qE '^## Project' "$memidx" || printf '\n## Project\n' >> "$memidx"
    printf -- '- [project-onboarding-done](project-onboarding-done.md) — onboarded under the fork playbook; stamp in config.yaml, SessionStart detector reads it\n' >> "$memidx"
  fi
  echo "  ✓ wrote project-onboarding-done memory ($memdir)"
}

# Write the completion marker: stamp config.yaml + ONBOARDING.md + (fork) CLAUDE.md section + memory.
# Idempotent — the onboarding block is always appended last, so a re-stamp strips it to EOF first.
write_marker() {
  local config="$PROJECT_DIR/_bmad/bmm/config.yaml" today
  today="$(date +%F)"
  [[ -f "$config" ]] || { echo "ERROR: no $config to stamp." >&2; return 1; }
  if grep -qE '^onboarding:' "$config"; then
    sed -i.bak '/^onboarding:/,$d' "$config" && rm -f "$config.bak"
  fi
  printf '\n' >> "$config"
  cat >> "$config" <<EOF
onboarding:
  playbook_version: $PLAYBOOK_VERSION
  onboarded_at: $today
  topology: $TOPOLOGY
  upstream_remote: "${UPSTREAM_URL}"
  guarantees:
    - fork-synced            # custom workflows/skills/hooks/commands via sync-bmad-workflows.sh
    - claude-md-std-001      # thin, pointer-based CLAUDE.md
    - hooks-installed        # worktree + enforcement PreToolUse hooks
    - memory-doctrine        # global ~/.claude memory library
EOF
  echo "  ✓ stamped onboarding marker in config.yaml (playbook v$PLAYBOOK_VERSION, topology=$TOPOLOGY)"
  write_onboarding_md "$today"
  if [[ "$TOPOLOGY" == "fork-of-upstream" ]]; then write_upstream_claude_section; fi
  write_onboarding_memory "$today"
  return 0
}

# ── --restamp: rewrite the marker ONLY (no clone/sync) ──
if $RESTAMP; then
  [[ -d "$PROJECT_DIR/_bmad" ]] || { echo "ERROR: --restamp needs an already-onboarded repo (no $PROJECT_DIR/_bmad)." >&2; exit 1; }
  echo "▶ Re-stamping onboarding marker for '$PROJECT_NAME' at $PROJECT_DIR"
  resolve_topology
  write_marker
  echo "✅ marker refreshed (playbook v$PLAYBOOK_VERSION, topology=$TOPOLOGY)."
  exit 0
fi

echo "▶ Onboarding '$PROJECT_NAME' at $PROJECT_DIR (phase: $PROJECT_PHASE)"

# Self-heal: make sure the global bmad-onboard skill is installed (best-effort, non-fatal) so the
# natural-language trigger keeps working even if ~/.claude was wiped. Canonical copy lives in the fork.
if [[ -x "$SCRIPT_DIR/install-global-assets.sh" ]]; then
  "$SCRIPT_DIR/install-global-assets.sh" >/dev/null 2>&1 || true
fi

# --- Resolve reference project ---
[[ -f "$REFERENCE_FILE" ]] || { echo "ERROR: $REFERENCE_FILE not found — can't locate the BMAD base source." >&2; exit 1; }
REF_ROOT="$(grep -v '^#' "$REFERENCE_FILE" | grep -v '^$' | head -1 | xargs)"
[[ -n "$REF_ROOT" && -d "$REF_ROOT/_bmad" ]] || { echo "ERROR: reference project '$REF_ROOT' has no _bmad/ tree." >&2; exit 1; }
# Guard: the reference must be a HEALTHY OLD-LAYOUT install (6.0.4 base + overlay), not a
# v6.8.0 skills-layout one and not a partial/broken tree — onboarding clones its base, so
# whatever the reference is missing, every new project inherits.
REF_REQUIRED=(
  "_bmad/bmm/workflows/1-analysis"      # old-layout marker (absent in v6.8.0 skills layout)
  "_bmad/core/agents"
  "_bmad/bmm/agents"
  "_bmad/bmm/data"
  "_bmad/_config/manifest.yaml"
)
ref_missing=()
for item in "${REF_REQUIRED[@]}"; do
  [[ -e "$REF_ROOT/$item" ]] || ref_missing+=("$item")
done
if [[ ${#ref_missing[@]} -gt 0 ]]; then
  echo "ERROR: reference '$REF_ROOT' is not a healthy old-layout BMAD install — missing:" >&2
  printf '         %s\n' "${ref_missing[@]}" >&2
  echo "       Onboarding clones the reference base, so a new project would inherit these gaps." >&2
  echo "       Do NOT point ~/.bmad-reference at a fresh 'bmad-cli install' (v6.8.0 skills layout);" >&2
  echo "       point it at a healthy, complete old-layout project." >&2
  exit 1
fi
echo "  reference: $REF_ROOT (health check passed)"

# --- Guard against clobbering an existing install ---
if [[ -d "$PROJECT_DIR/_bmad" ]] && ! $FORCE; then
  echo "ERROR: $PROJECT_DIR/_bmad already exists. Re-run with --force to re-seed, or just run sync-bmad-workflows.sh." >&2
  exit 1
fi

# --- 1. git init ---
if [[ ! -d "$PROJECT_DIR/.git" ]]; then
  git -C "$PROJECT_DIR" init -q
  git -C "$PROJECT_DIR" symbolic-ref HEAD refs/heads/main 2>/dev/null || true
  echo "  ✓ git init (main)"
else
  echo "  • git repo already present"
fi

# --- 1b. Resolve topology now that a git repo exists ---
resolve_topology
echo "  • topology: $TOPOLOGY${UPSTREAM_URL:+ (upstream: $UPSTREAM_URL)}"

# --- 2. Clone reference _bmad base ---
rm -rf "$PROJECT_DIR/_bmad"
cp -R "$REF_ROOT/_bmad" "$PROJECT_DIR/_bmad"
echo "  ✓ cloned _bmad base from reference"

# --- 3. Generate a CLEAN config + clear reference-specific state ---
# Rather than inherit the reference project's bmm/config.yaml (which carries its deploy contract,
# phase-rationale comments, and skill pins), regenerate the stable required keys from scratch.
# Future-proof: whatever project-specific cruft accumulates in the reference's config never leaks.
# The sync then backfills autonomous_mode/autonomous_rules from config-defaults.yaml.
CONFIG="$PROJECT_DIR/_bmad/bmm/config.yaml"
USER_NAME="$(grep -E '^user_name:' "$PROJECT_DIR/_bmad/core/config.yaml" 2>/dev/null | head -1 | sed -E 's/^user_name:[[:space:]]*//')"
USER_NAME="${USER_NAME:-Mason Wood}"
cat > "$CONFIG" <<EOF
# BMM Module Configuration — generated by onboard-project.sh
project_name: $PROJECT_NAME
user_name: $USER_NAME
user_skill_level: intermediate
planning_artifacts: "{project-root}/{output_folder}/planning-artifacts"
implementation_artifacts: "{project-root}/{output_folder}/implementation-artifacts"
project_knowledge: "{project-root}/docs"
project_phase: $PROJECT_PHASE

# Deployment contract (see _bmad/bmm/workflows/shared/deployment-to-prod.md).
# Opted out on onboard — set real deploy config when this project has a pipeline.
# Skip-mode posture: deploy is the owner's manual step — the agent states deploy
# status after merge and STOPS, it never asks "want me to deploy?" (CLAUDE.md
# "Deployment — BMAD contract" section).
# autonomous: when a real deploy is configured, the agent OWNS deploy choices
# end-to-end and never routes them back to the owner (fresh origin/main checkout,
# verify the deploy target, apply ADDITIVE migrations) — it still gates a
# DESTRUCTIVE migration. Set false to keep the owner-only state-and-stop posture.
deploy:
  bmad_contract: skip
  autonomous: true
EOF
# Clear the reference's project-specific sidecar memory + stale sync stamp.
find "$PROJECT_DIR/_bmad/_memory" -type f -name '*.md' -delete 2>/dev/null || true
rm -f "$PROJECT_DIR/_bmad/_config/sync-stamp.yaml" 2>/dev/null || true
echo "  ✓ generated clean config (name=$PROJECT_NAME, phase=$PROJECT_PHASE, deploy=skip, deploy.autonomous=true) + cleared reference state"

# --- 4. CLAUDE.md from template ---
if [[ ! -f "$PROJECT_DIR/CLAUDE.md" ]]; then
  if [[ -f "$CLAUDEMD_TEMPLATE" ]]; then
    cp "$CLAUDEMD_TEMPLATE" "$PROJECT_DIR/CLAUDE.md"
    echo "  ✓ created CLAUDE.md from template (fill in the TODO stack/structure sections)"
  else
    echo "  ! CLAUDE.md template not found — skipping (sync will not manage sections until one exists)"
  fi
else
  echo "  • CLAUDE.md already present"
fi

# --- 5. Register in ~/.bmad-targets ---
TARGET_LINE="$PROJECT_DIR/_bmad/bmm/workflows"
mkdir -p "$TARGET_LINE"
if [[ -f "$TARGETS_FILE" ]] && grep -qxF "$TARGET_LINE" "$TARGETS_FILE"; then
  echo "  • already in ~/.bmad-targets"
else
  printf '%s\n' "$TARGET_LINE" >> "$TARGETS_FILE"
  echo "  ✓ registered in ~/.bmad-targets"
fi

# --- 6. Sync (just this project) ---
echo "  → running sync-bmad-workflows.sh --only $PROJECT_DIR ..."
"$SYNC_SCRIPT" --only "$PROJECT_DIR" >/tmp/onboard-sync.log 2>&1 || { echo "ERROR: sync failed. See /tmp/onboard-sync.log" >&2; exit 1; }
grep -A14 "$(basename "$PROJECT_DIR")\b" /tmp/onboard-sync.log | head -16 || true

# --- 7. Completion marker (stamp + ONBOARDING.md + memory + fork CLAUDE.md section) ---
write_marker

echo
echo "✅ '$PROJECT_NAME' onboarded (playbook v$PLAYBOOK_VERSION, topology=$TOPOLOGY)."
echo "   Custom workflows, skills, hooks, and commands are wired; completion marker stamped."
echo "   Next: fill in CLAUDE.md's stack/structure TODOs and scaffold your app."
echo "   Then run the 'bmad-onboard-tutorial' skill to walk the gates once by doing:"
echo "         a safe sync dry-run, and a first feature branch + tests + commit."
echo "   Memory: under the global doctrine (~/.claude); the project-onboarding-done fact is recorded."
