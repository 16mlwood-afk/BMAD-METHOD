#!/usr/bin/env bash
#
# check-skill-drift.sh — DELIVERED-vs-FORK drift checker for skills-layout projects.
#
# WHY THIS EXISTS (2026-07-31 audit of create-workflow / create-agent):
#   A gate authored in the fork enforces nothing until it is DELIVERED. `create-agent` gained an
#   outward-discovery HALT gate + an STD-SKILLPROV-001 provenance stamp in the fork, and the copy
#   actually invokable in cash-recovery carried neither — the gate was real and fired nowhere.
#   Nothing detected that, because every existing fork check reads the FORK. This reads the PROJECT.
#
# WHAT IT DOES
#   Rebuilds the skills-native ports from the fork (the porter is deterministic and re-runnable) and
#   diffs them against what the project actually has. Re-running the porter IS the "modulo the porter
#   rewrite rules" comparison, exactly — it does not approximate the six rewrite regexes, it EXECUTES
#   them. If the porter's rules change, this check follows for free and cannot fall out of step with
#   them. (An independent re-implementation of those regexes here would be a second source of truth
#   for the same transform — the drift class this tool exists to catch.)
#
# SCOPE — deliberately narrow, so it does not become an indiscriminate detector.
#   Only skills the FORK DELIVERS are compared:
#     · porter output from custom/workflows/  -> rsync'd to .claude/skills/bmad-<name>/
#     · custom/skills/bmad-*                  -> hand-authored fork skills (e.g. bmad-correct-course)
#   A `bmad-*` skill present in the project but delivered by neither is UPSTREAM-INSTALLED
#   (bmad-cli v6.8) and is reported as INFO, never as a finding. Flagging those would bury the real
#   signal under ~40 false positives and get the check switched off.
#
# WHAT IT DOES NOT DO
#   It does not sync, does not write to the project, and does not judge whether the fork version is
#   the RIGHT one — only whether the project is running what the fork says it should be.
#
# EXIT
#   1 if any fork-delivered skill is DRIFTED or MISSING. 0 otherwise (including the loud SKIP).
#
# Usage: check-skill-drift.sh [<project-root>]
#        default: $BMAD_DRIFT_REF_PROJECT, else ~/code/cash-recovery

set -euo pipefail

FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT_ENGINE="$FORK/tools/port-workflows-to-skills.sh"
CUSTOM_SKILLS="$FORK/custom/skills"

PROJECT="${1:-${BMAD_DRIFT_REF_PROJECT:-$HOME/code/cash-recovery}}"
SKILLS_DIR="$PROJECT/.claude/skills"

# A missing reference project is a LOUD skip, never a silent pass — this check is wired into
# `npm run quality`, which must stay runnable on a machine with no project checkout.
if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "skill-drift: SKIP — no skills-layout project at $PROJECT (.claude/skills absent)."
  echo "             Pass a project root explicitly, or set BMAD_DRIFT_REF_PROJECT."
  exit 0
fi

if [[ ! -x "$PORT_ENGINE" ]]; then
  echo "skill-drift: FAIL — port engine missing or not executable: $PORT_ENGINE" >&2
  exit 1
fi

TMP="$(mktemp -d -t bmad-skill-drift)"
trap 'rm -rf "$TMP"' EXIT

# Rebuild the ports. The engine is `set -euo pipefail`; a failure here must never be swallowed and
# must never fall back to a pre-existing tree — that is the exact silent-failure class already fixed
# inside ensure_skills_native_built() in the sync.
if ! "$PORT_ENGINE" "$TMP/ports" >"$TMP/port.log" 2>&1; then
  echo "skill-drift: FAIL — port engine exited non-zero; NO comparison was made." >&2
  sed 's/^/  | /' "$TMP/port.log" >&2
  exit 1
fi

drifted=()
missing=()
expected=()
ok=0

compare_one() {
  local name="$1" src="$2"
  local dst="$SKILLS_DIR/$name"
  if [[ ! -d "$dst" ]]; then
    missing+=("$name")
    return
  fi
  # Same exclusion the delivering rsync uses, so a stray .DS_Store is not reported as drift.
  if diff -r -q --exclude='.DS_Store' "$src" "$dst" >"$TMP/detail.$name" 2>&1; then
    ok=$((ok + 1))
  else
    drifted+=("$name")
  fi
}

for d in "$TMP/ports"/bmad-*/; do
  [[ -d "$d" ]] || continue
  n="$(basename "$d")"
  expected+=("$n")
  compare_one "$n" "${d%/}"
done

for d in "$CUSTOM_SKILLS"/bmad-*/; do
  [[ -d "$d" ]] || continue
  n="$(basename "$d")"
  expected+=("$n")
  compare_one "$n" "${d%/}"
done

# Project-side bmad-* skills the fork does not deliver = upstream-installed. INFO only.
upstream=0
for d in "$SKILLS_DIR"/bmad-*/; do
  [[ -d "$d" ]] || continue
  n="$(basename "$d")"
  found=0
  for e in "${expected[@]}"; do
    [[ "$e" == "$n" ]] && { found=1; break; }
  done
  (( found == 0 )) && upstream=$((upstream + 1))
done

echo "skill-drift: project $PROJECT"
echo "  fork-delivered skills compared : ${#expected[@]}"
echo "  in sync                        : $ok"
echo "  DRIFTED                        : ${#drifted[@]}"
echo "  MISSING in project             : ${#missing[@]}"
echo "  upstream-installed (not fork)  : $upstream  [INFO — out of scope]"

if (( ${#drifted[@]} > 0 )); then
  echo ""
  echo "DRIFTED — fork source and delivered copy disagree. The DELIVERED copy is what runs:"
  for n in "${drifted[@]}"; do
    echo "  x $n"
    sed 's/^/      /' "$TMP/detail.$n" | head -8
  done
fi

if (( ${#missing[@]} > 0 )); then
  echo ""
  echo "MISSING — delivered by the fork, absent from the project (never synced):"
  for n in "${missing[@]}"; do echo "  x $n"; done
fi

if (( ${#drifted[@]} > 0 || ${#missing[@]} > 0 )); then
  echo ""
  echo "Remedy (respect the STATUS.md fleet re-sync gate — do not open a window for one skill):"
  echo "  $FORK/sync-bmad-workflows.sh --only \"$PROJECT\""
  exit 1
fi

echo "skill-drift: OK — every fork-delivered skill matches the project."
