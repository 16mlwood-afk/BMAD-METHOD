#!/usr/bin/env sh
# .githooks/check-claude-md-shape.sh — FORK-owned pre-commit gate (STD-HOOKACTIVATE-001).
#
# A project's root CLAUDE.md cannot drift from the owner's approved shape without the commit saying
# so. Owner ruling, 10 Nov 2026 (record ~/.claude/docs/decisions/2026-11-10-claude-md-legacy-content-
# across-projects.md; method ~/.claude/docs/claude-md-sweep-method.md; global file § Project
# exceptions [G-EXC]).
#
#   SWEPT file (a "Swept on <date>" line before the first heading) is ENFORCED, and a failure
#     REFUSES the commit: five ## blocks in order, every section tagged FACT / STRICTER(<G-id>: <reason>)
#     / POINTER, every STRICTER citing a G-id that exists in the CURRENT ~/.claude/CLAUDE.md with a
#     reason, no run of 12+ words copied from that file.
#   UNSWEPT file is WARN-ONLY: one notice pointing at the sweep method. Never refuses.
#   Cannot read ~/.claude/CLAUDE.md or the checker -> "COULD NOT CHECK" is printed and the commit
#     is allowed. Never silent.
#
# The rules live in ONE place, ~/.claude/scripts/claude-md-sweep/claude-md-tag-check.py. This gate
# CALLS it on the STAGED text (not the working copy); it carries none of the checking logic.
#
# Override (logged, 12+ characters):  CLAUDE_MD_PROJECT_SHAPE_OVERRIDE="<why>" git commit ...
#   -> appended to ~/.claude/logs/claude-md-shape-overrides.jsonl (the global gate's log).
# Test seams (env): CLAUDE_MD_SWEEP_CHECKER, CLAUDE_MD_GLOBAL_FILE, CLAUDE_MD_SHAPE_OVERRIDE_LOG.
#
# Enforcement: DETERMINISTIC on shape, ids and copied runs. It cannot see whether a FACT is true, whether
# a STRICTER reason is true, or whether a section sits in block 2 or block 3 (both carry FACT).
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Silent unless the root CLAUDE.md is added or modified in this commit.
STATUS="$(git diff --cached --name-status --no-renames -- CLAUDE.md | awk '{print $1}')"
[ -n "$STATUS" ] || exit 0
[ "$STATUS" != "D" ] || exit 0

CHECKER="${CLAUDE_MD_SWEEP_CHECKER:-$HOME/.claude/scripts/claude-md-sweep/claude-md-tag-check.py}"
GLOBAL="${CLAUDE_MD_GLOBAL_FILE:-$HOME/.claude/CLAUDE.md}"
LOG="${CLAUDE_MD_SHAPE_OVERRIDE_LOG:-$HOME/.claude/logs/claude-md-shape-overrides.jsonl}"
METHOD="~/.claude/docs/claude-md-sweep-method.md"

could_not() {
  printf 'CLAUDE.md shape: COULD NOT CHECK — %s (commit allowed; this is not a pass)\n' "$1" >&2
  exit 0
}

command -v python3 >/dev/null 2>&1 || could_not "python3 is not installed"
[ -f "$CHECKER" ] || could_not "checker script not found at $CHECKER"
[ -r "$GLOBAL" ] || could_not "global file not readable at $GLOBAL, so no rule id can be verified"

TMP="$(mktemp "${TMPDIR:-/tmp}/claude-md-shape.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
git show :CLAUDE.md > "$TMP" 2>/dev/null || could_not "could not read the staged CLAUDE.md"

set +e
OUT="$(python3 "$CHECKER" --file "$TMP" --global "$GLOBAL" --unswept-ok 2>&1)"
RC=$?
set -e

case "$RC" in
  0) exit 0 ;;
  3)
    printf 'CLAUDE.md shape: UNSWEPT — this project CLAUDE.md has no "Swept on <date>" line, so the approved five-block shape is not enforced here. Re-sweep with %s. (warning only; commit allowed)\n' "$METHOD" >&2
    exit 0
    ;;
  1) ;;
  2) could_not "$(printf '%s' "$OUT" | tail -n 1)" ;;
  *) could_not "the checker crashed (exit $RC): $(printf '%s' "$OUT" | tail -n 1)" ;;
esac

REASON="${CLAUDE_MD_PROJECT_SHAPE_OVERRIDE:-}"
if [ "${#REASON}" -ge 12 ]; then
  mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
  OUT_TEXT="$OUT" REASON_TEXT="$REASON" ROOT_DIR="$ROOT" LOG_FILE="$LOG" python3 -c '
import json, os, datetime
rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "gate": "claude-md-project-shape", "repo": os.environ["ROOT_DIR"],
       "reason": os.environ["REASON_TEXT"],
       "failures": [l[5:] for l in os.environ["OUT_TEXT"].splitlines() if l.startswith("RED  ")]}
open(os.environ["LOG_FILE"], "a", encoding="utf-8").write(json.dumps(rec) + "\n")
' || could_not "override given but the log could not be written to $LOG"
  printf 'CLAUDE.md shape: OVERRIDDEN (%s); logged to %s\n' "$REASON" "$LOG" >&2
  exit 0
fi

{
  printf 'REFUSED by claude-md-shape (project CLAUDE.md is SWEPT, so its approved shape is enforced):\n'
  printf '%s\n' "$OUT" | grep '^RED  ' | sed 's/^RED  /  /'
  printf 'Fix: re-shape the file per %s (five ## blocks in order; tag every section FACT, STRICTER(<G-id>: <reason>) or POINTER;\n' "$METHOD"
  printf '     cite a G-id that exists in ~/.claude/CLAUDE.md; point at a rule, never copy 12+ words of it).\n'
  printf 'Override (logged): CLAUDE_MD_PROJECT_SHAPE_OVERRIDE="<why, 12+ characters>" git commit ...\n'
} >&2
exit 1
