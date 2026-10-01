#!/usr/bin/env bash
# migrate-bash-edit-guard.sh — replace the LEGACY inline regex edit-guard with the reviewed
# implementation, one project at a time.
#
#   DRY RUN (default):  bash tools/migrate-bash-edit-guard.sh
#   ONE project:        bash tools/migrate-bash-edit-guard.sh --apply --only ~/code/inbound-flow
#   ALL targets:        bash tools/migrate-bash-edit-guard.sh --apply
#
# WHY. `bash_edit_guard.py` (cash-recovery, 47 golden cases) is the authoritative guard. The
# other projects still run a 2050-char inline regex in `settings.local.json` that classifies
# the COMMAND STRING instead of the write TARGET, and therefore:
#   - blocks read-only commands that merely mention `sed -i` / `cat >` / `tee`
#   - blocks allowlisted paths (`~/bmad-method-v6/`, `_bmad-output/`, project `.claude/`)
#   - resolves relative targets against the wrong directory after a `cd`
#   - names `BMAD_ALLOW_MAIN_EDIT=1` in its deny message and honours it nowhere
#   - and had a false NEGATIVE: one exempt target exempted the whole command
# So the legacy blob is not a conservative fallback — it is actively wrong in both directions.
#
# WHY THIS IS A SCRIPT AND NOT THE BMAD SYNC. `settings.local.json` is gitignored and is NOT a
# BMAD-managed path: the fork sync does not carry it. Hooks distribute on a separate track from
# workflows, which is exactly why this guard sat in one project for a day while docs said
# otherwise. This script IS that track, made explicit.
#
# SAFETY CONTRACT
#   * Dry run by default. `--apply` is required to change anything.
#   * Backs up `settings.local.json` to `.bak-guardmigrate-<UTC>` before touching it.
#   * Edits ONLY the PreToolUse hook entry whose command contains the legacy marker. Every other
#     hook, permission, and env entry is left byte-identical (json round-trip, indent=2).
#   * SKIPS a project whose settings already invoke the reviewed guard (idempotent).
#   * SKIPS rather than guesses when the shape is unexpected: no legacy entry, more than one
#     legacy entry, or unparseable JSON.
#   * Runs the health check after each apply and reports per project. A project that fails the
#     check is reported LOUDLY and its backup path is printed — it is not silently left broken.
#   * Never touches git. It does not commit, stage, or push: `settings.local.json` is gitignored,
#     and the guard + suite ARE tracked, so those go through each project's normal PR flow.
set -uo pipefail

FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_PROJECT="$HOME/code/cash-recovery"
GUARD_SRC="$SOURCE_PROJECT/.claude/hooks/bash_edit_guard.py"
TEST_SRC="$SOURCE_PROJECT/.claude/hooks/test_bash_edit_guard.py"
HEALTH_SRC="$SOURCE_PROJECT/.claude/hooks/guard-health-check.sh"
AUDIT_SRC="$SOURCE_PROJECT/.claude/hooks/audit-override-log.py"
TARGETS_FILE="$HOME/.bmad-targets"
LEGACY_MARKER='edit-equivalent (sed -i / cat >'

APPLY=0
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --only) ONLY="${2:-}"; shift ;;
    *) printf 'unknown arg: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

for f in "$GUARD_SRC" "$TEST_SRC" "$HEALTH_SRC" "$AUDIT_SRC"; do
  [ -f "$f" ] || { printf 'FATAL: source missing: %s\n' "$f" >&2; exit 1; }
done

if [ -n "$ONLY" ]; then
  projects="$ONLY"
elif [ -f "$TARGETS_FILE" ]; then
  # ~/.bmad-targets lists <project>/_bmad/bmm/workflows paths, with a comment header and blank
  # lines. Take ABSOLUTE PATHS ONLY — the first dry run parsed the header prose into 13 phantom
  # "projects" ("targets", "one", "workflows", "#") and reported them as WOULD MIGRATE. A
  # migration script whose project list is word salad must not be trusted with --apply.
  projects=$(grep -E '^[[:space:]]*/' "$TARGETS_FILE" \
             | sed 's#^[[:space:]]*##; s#/_bmad/bmm/workflows.*$##; s#/*$##' \
             | grep -E '^/.+' | sort -u)
  [ -n "$projects" ] || { printf 'FATAL: no absolute project paths parsed from %s\n' "$TARGETS_FILE" >&2; exit 1; }
else
  printf 'FATAL: no --only and no %s\n' "$TARGETS_FILE" >&2; exit 1
fi

printf '\nedit-guard migration · %s\n' "$([ "$APPLY" -eq 1 ] && echo 'APPLY' || echo 'DRY RUN (nothing will change)')"
printf 'source of truth: %s\n\n' "$GUARD_SRC"

migrated=0; skipped=0; failed=0
for proj in $projects; do
  name=$(basename "$proj")
  settings="$proj/.claude/settings.local.json"

  if [ ! -d "$proj" ]; then printf '  SKIP %-22s project dir not found\n' "$name"; skipped=$((skipped+1)); continue; fi
  if [ "$proj" = "$SOURCE_PROJECT" ]; then printf '  SKIP %-22s source of truth\n' "$name"; skipped=$((skipped+1)); continue; fi
  if [ ! -f "$settings" ]; then printf '  SKIP %-22s no settings.local.json (no guard wired here)\n' "$name"; skipped=$((skipped+1)); continue; fi

  if grep -q 'bash_edit_guard' "$settings" 2>/dev/null; then
    printf '  SKIP %-22s already invokes the reviewed guard\n' "$name"; skipped=$((skipped+1)); continue
  fi
  if ! grep -qF "$LEGACY_MARKER" "$settings" 2>/dev/null; then
    printf '  SKIP %-22s no legacy edit-guard entry found — unexpected shape, not guessing\n' "$name"
    skipped=$((skipped+1)); continue
  fi

  if [ "$APPLY" -eq 0 ]; then
    printf '  WOULD MIGRATE %-13s legacy entry present; would copy 4 files + rewire 1 hook\n' "$name"
    migrated=$((migrated+1)); continue
  fi

  mkdir -p "$proj/.claude/hooks"
  cp "$GUARD_SRC" "$TEST_SRC" "$HEALTH_SRC" "$AUDIT_SRC" "$proj/.claude/hooks/"
  chmod +x "$proj/.claude/hooks/guard-health-check.sh" "$proj/.claude/hooks/audit-override-log.py"

  if ! MIG_SETTINGS="$settings" MIG_MARKER="$LEGACY_MARKER" python3 - <<'PY'
import json, os, shutil, sys
from datetime import datetime, timezone

p, marker = os.environ["MIG_SETTINGS"], os.environ["MIG_MARKER"]
try:
    d = json.load(open(p))
except Exception as e:
    print(f"      unparseable settings.local.json ({e}) — skipped", file=sys.stderr); sys.exit(1)

hits = [(i, j) for i, h in enumerate(d.get("hooks", {}).get("PreToolUse", []))
        for j, x in enumerate(h.get("hooks", [])) if marker in (x.get("command") or "")]
if len(hits) != 1:
    print(f"      expected exactly 1 legacy entry, found {len(hits)} — skipped", file=sys.stderr); sys.exit(1)

shutil.copy2(p, p + ".bak-guardmigrate-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
i, j = hits[0]
d["hooks"]["PreToolUse"][i]["hooks"][j]["command"] = (
    'S="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/hooks/bash_edit_guard.py"; '
    'case "$PWD" in */.claude/worktrees/*) S="${PWD%/.claude/worktrees/*}/.claude/hooks/bash_edit_guard.py";; esac; '
    '[ -f "$S" ] || exit 0; exec python3 "$S"')
json.dump(d, open(p, "w"), indent=2)
open(p, "a").write("\n")
PY
  then
    printf '  FAIL %-22s settings rewrite refused (see reason above)\n' "$name"; failed=$((failed+1)); continue
  fi

  if CLAUDE_PROJECT_DIR="$proj" bash "$proj/.claude/hooks/guard-health-check.sh" >/tmp/gh-$name.log 2>&1; then
    printf '  OK   %-22s migrated · health check PASSED\n' "$name"; migrated=$((migrated+1))
  else
    printf '  FAIL %-22s migrated but HEALTH CHECK FAILED — see /tmp/gh-%s.log\n' "$name" "$name"
    printf '       rollback: cp %s.bak-guardmigrate-* %s\n' "$settings" "$settings"
    failed=$((failed+1))
  fi
done

printf '\n  %d migrated · %d skipped · %d failed\n' "$migrated" "$skipped" "$failed"
if [ "$APPLY" -eq 0 ]; then
  printf '  DRY RUN — nothing changed. Re-run with --apply (optionally --only <project>).\n'
else
  printf '  The guard + suite are TRACKED files: each project still needs its own commit/PR.\n'
  printf '  settings.local.json is gitignored and is not committed anywhere.\n'
fi
[ "$failed" -eq 0 ] || exit 1
