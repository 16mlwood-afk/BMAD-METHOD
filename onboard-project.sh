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
#
# Usage:
#   onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed] [--force]
#
#   <project-dir>   defaults to the current directory
#   --name          defaults to the directory basename
#   --phase         defaults to greenfield (new build)
#   --force         re-seed even if _bmad already exists (DESTRUCTIVE to _bmad)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-bmad-workflows.sh"
CLAUDEMD_TEMPLATE="$SCRIPT_DIR/src/modules/bmm/_module-installer/assets/CLAUDE.md.template"
REFERENCE_FILE="$HOME/.bmad-reference"
TARGETS_FILE="$HOME/.bmad-targets"

PROJECT_DIR=""
PROJECT_NAME=""
PROJECT_PHASE="greenfield"
FORCE=false

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)  PROJECT_NAME="$2"; shift 2 ;;
    --phase) PROJECT_PHASE="$2"; shift 2 ;;
    --force) FORCE=true; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *)  PROJECT_DIR="$1"; shift ;;
  esac
done

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"
mkdir -p "$PROJECT_DIR"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-$(basename "$PROJECT_DIR")}"

case "$PROJECT_PHASE" in
  greenfield|brownfield|mixed) ;;
  *) echo "ERROR: --phase must be greenfield|brownfield|mixed (got: $PROJECT_PHASE)" >&2; exit 1 ;;
esac

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

echo
echo "✅ '$PROJECT_NAME' onboarded. Custom workflows, skills, hooks, and commands are wired."
echo "   Next: fill in CLAUDE.md's stack/structure TODOs and scaffold your app."
echo "   Memory: already under the global doctrine (~/.claude, see CLAUDE.md's Memory section)."
echo "           Create MEMORY.md + memory/<slug>.md when you have your first durable project fact."
