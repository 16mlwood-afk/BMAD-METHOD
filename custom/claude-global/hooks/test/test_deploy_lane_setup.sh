#!/usr/bin/env bash
# Golden cases for custom/claude-global/hooks/deploy-lane-setup.sh — BOTH directions.
#
#   bash custom/claude-global/hooks/test/test_deploy_lane_setup.sh
#
# A SessionStart hook that speaks when it should not is a hook that gets switched off, so
# the SILENT cases are the load-bearing half. The checker is stubbed (DEPLOY_LANE_CHECKER)
# so each case controls the state the hook sees; the real checker has its own suite.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/../deploy-lane-setup.sh"
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then pass=$((pass+1)); else fail=$((fail+1)); printf '  ✗ %s\n      expected: %s\n      actual:   %s\n' "$1" "$2" "$3"; fi; }

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home"; mkdir -p "$HOME/.claude/logs"

# A stub checker: emits the state named in the project's STUB_STATE file.
STUB="$T/stub-checker.py"
cat > "$STUB" <<'PY'
import json, sys, os
proj = sys.argv[sys.argv.index("--project") + 1]
state = open(os.path.join(proj, "STUB_STATE")).read().strip()
rows = {} if state in ("MET", "N/A", "NOT DECLARED", "UNKNOWN") else {"R1": "verified", "R4": "missing", "R6": "missing", "R7": "declared"}
print(json.dumps({"results": [{"state": state, "rows": rows, "notes": {"why": "no deploy block"}}]}))
# The REAL checker exits 1 whenever the fleet is not STANDARD MET. Mirror that, or the
# suite cannot catch a hook that treats a non-zero exit as "nothing to say".
sys.exit(0 if state in ("MET", "N/A") else 1)
PY
export DEPLOY_LANE_CHECKER="$STUB"

mkproj() { # name state
  local p="$T/$1"; mkdir -p "$p/_bmad/bmm" "$p/.claude"; : > "$p/_bmad/bmm/config.yaml"; echo "$2" > "$p/STUB_STATE"; echo "$p"; }
run() { (cd "$1" && CLAUDE_PROJECT_DIR="$1" bash "$HOOK" 2>/dev/null); }

echo "── silent cases ──"
mkdir -p "$T/plain"; check "non-BMAD directory: silent" "" "$(cd "$T/plain" && CLAUDE_PROJECT_DIR="$T/plain" bash "$HOOK" 2>/dev/null)"
check "MET project: silent" "" "$(run "$(mkproj met MET)")"
check "N/A (method none): silent" "" "$(run "$(mkproj na N/A)")"
p="$(mkproj nochk GAPS)"; check "checker missing: silent" "" "$(cd "$p" && DEPLOY_LANE_CHECKER=/nonexistent CLAUDE_PROJECT_DIR="$p" bash "$HOOK" 2>/dev/null)"
p="$(mkproj snoozed GAPS)"; echo "$(date -u -v+3d +%Y-%m-%d 2>/dev/null || date -u -d '+3 days' +%Y-%m-%d) waiting on the owner" > "$p/.claude/.deploy-lane-setup.snooze"
check "valid dated snooze (≤14d): silent" "" "$(run "$p")"
check "…and the snooze is LOGGED" "1" "$(grep -c '"snoozed_until"' "$HOME/.claude/logs/deploy-lane-setup.jsonl")"

echo "── fires ──"
p="$(mkproj undeclared 'NOT DECLARED')"; out="$(run "$p")"
check "NOT DECLARED fires as FIRST PRIORITY" "1" "$(printf '%s' "$out" | grep -c 'FIRST PRIORITY THIS SESSION')"
check "…names the project" "1" "$(printf '%s' "$out" | grep -c 'undeclared: NOT DECLARED')"
check "…tells the agent how to declare method: none" "1" "$(printf '%s' "$out" | grep -c 'method: none')"
check "…names the done condition" "1" "$(printf '%s' "$out" | grep -c 'reports MET or N/A')"
check "…bounded (≤12 lines)" "1" "$([ "$(printf '%s\n' "$out" | wc -l | tr -d ' ')" -le 12 ] && echo 1 || echo 0)"
p="$(mkproj gaps GAPS)"; out="$(run "$p")"
check "GAPS fires and lists the missing rows" "1" "$(printf '%s' "$out" | grep -c 'Missing: R4, R6')"
check "…and the on-trust rows" "1" "$(printf '%s' "$out" | grep -c 'on trust only: R7')"
p="$(mkproj unknown UNKNOWN)"; check "UNKNOWN fires" "1" "$(run "$p" | grep -c 'could not assess')"
p="$(mkproj expired GAPS)"; echo "2020-01-01 long ago" > "$p/.claude/.deploy-lane-setup.snooze"
check "expired snooze does NOT suppress" "1" "$(run "$p" | grep -c 'FIRST PRIORITY')"
p="$(mkproj toolong GAPS)"; echo "2099-01-01 forever" > "$p/.claude/.deploy-lane-setup.snooze"
check "a snooze beyond 14 days does NOT suppress" "1" "$(run "$p" | grep -c 'FIRST PRIORITY')"
p="$(mkproj undated GAPS)"; echo "later" > "$p/.claude/.deploy-lane-setup.snooze"
check "an undated snooze does NOT suppress" "1" "$(run "$p" | grep -c 'FIRST PRIORITY')"

echo "── worktree resolution ──"
p="$(mkproj wt GAPS)"; mkdir -p "$p/.claude/worktrees/feat-x"
check "a task worktree resolves to the project root and fires" "1" "$(cd "$p/.claude/worktrees/feat-x" && CLAUDE_PROJECT_DIR="$p/.claude/worktrees/feat-x" bash "$HOOK" 2>/dev/null | grep -c 'deploy lane for wt')"
mkdir -p "$p/src/deep"; check "a subdirectory walks up to the root" "1" "$(cd "$p/src/deep" && CLAUDE_PROJECT_DIR="$p/src/deep" bash "$HOOK" 2>/dev/null | grep -c 'FIRST PRIORITY')"

echo
if [ "$fail" -eq 0 ]; then echo "ok — $pass cases, both directions"; else echo "FAIL — $fail failing, $pass passing"; exit 1; fi
