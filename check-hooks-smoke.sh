#!/usr/bin/env bash
# Hook smoke-test — a broken hook must not ship silently (fork-gaps: "Hooks ship
# unvalidated"). For each FORK hook script, feed a representative stdin fixture and
# assert: (1) exit 0, (2) output is EMPTY or parseable JSON. Plus a few BEHAVIORAL
# cases that pin the stdin contract — these catch the class of bug where a hook
# ignores its stdin and emits valid-but-wrong JSON (the friction-reflect
# `python3 - <<PY` heredoc-becomes-stdin bug). Run standalone or from pre-push.
#
#   ~/bmad-method-v6/check-hooks-smoke.sh   # exits non-zero if any hook fails
set -uo pipefail
cd "$(dirname "$0")" || exit 1

PASS=0; FAIL=0; FAILED=()

# is_json: empty is OK; otherwise must parse as JSON.
is_json() { [ -z "$1" ] || printf '%s' "$1" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; }

# run <script> <stdin-fixture> <expect: empty|json|either> <label>
run() {
  local script="$1" fixture="$2" expect="$3" label="$4" out rc
  if [ ! -f "$script" ]; then FAIL=$((FAIL+1)); FAILED+=("$label: MISSING $script"); return; fi
  out=$(printf '%s' "$fixture" | bash "$script" 2>/dev/null); rc=$?
  if [ "$rc" -ne 0 ]; then FAIL=$((FAIL+1)); FAILED+=("$label: exit $rc (want 0)"); return; fi
  case "$expect" in
    empty)  [ -z "$out" ] && { PASS=$((PASS+1)); } || { FAIL=$((FAIL+1)); FAILED+=("$label: expected SILENT, got output"); } ;;
    json)   { [ -n "$out" ] && is_json "$out"; } && { PASS=$((PASS+1)); } || { FAIL=$((FAIL+1)); FAILED+=("$label: expected JSON, got '${out:0:40}'"); } ;;
    either) is_json "$out" && { PASS=$((PASS+1)); } || { FAIL=$((FAIL+1)); FAILED+=("$label: output not empty-or-JSON: '${out:0:40}'"); } ;;
    # SessionStart may emit plain text (surfaced as a banner) OR JSON additionalContext.
    # Only fail if it LOOKS like JSON but is malformed (a silently-dropped additionalContext).
    ok)     case "${out#"${out%%[![:space:]]*}"}" in
              "{"*|"["*) is_json "$out" && { PASS=$((PASS+1)); } || { FAIL=$((FAIL+1)); FAILED+=("$label: looks like JSON but is malformed: '${out:0:40}'"); } ;;
              *)         PASS=$((PASS+1)) ;;
            esac ;;
  esac
}

# --- generic contract: emits empty-or-valid-JSON, exits 0 (catches crash/garbage) ---
run check-fork-gaps.sh        ''  ok "fork-gaps/sessionstart"
run check-standards-drift.sh  ''  ok "standards-drift/sessionstart"
run check-claude-md-drift.sh  ''  ok "claude-md-drift/sessionstart"
run check-upstream-drift.sh   ''  ok "upstream-drift/sessionstart"
run check-hook-activation.sh  ''  ok "hook-activation/sessionstart"

# --- behavioral contract: the hook must actually READ its stdin ---
# friction-reflect: stop_hook_active=true MUST be silent (the heredoc-stdin bug
# ignored this and always fired). This is the regression test for that bug.
run check-friction-reflect.sh '{"stop_hook_active":true}'                                              empty "friction-reflect/loop-guard"
# CONTRACT CHANGED 2026-08-31 (owner instruction): the hook is SCOPED and WARN-ONLY.
# It used to fire on any fresh session with no evidence at all - that unconditional
# block is exactly what was removed, so "fires-fresh" is no longer the contract and
# asserting it would pin the defect in place. A session with no transcript, or one
# that never wrote to an infra surface, MUST now be silent; only a write-shaped
# interaction with fork/hook/settings/skills/_bmad/doctrine surfaces may warn.
run check-friction-reflect.sh "{\"session_id\":\"smoke-a$$\",\"stop_hook_active\":false}"               empty "friction-reflect/no-transcript-silent"
FR_TR="$(mktemp -t frictionsmoke).jsonl"
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","name":"Read","input":{"file_path":"/x/src/app.ts"}}]}}' > "$FR_TR"
run check-friction-reflect.sh "{\"session_id\":\"smoke-b$$\",\"stop_hook_active\":false,\"transcript_path\":\"$FR_TR\"}" empty "friction-reflect/read-only-silent"
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","name":"Write","input":{"file_path":"/x/.claude/hooks/z.py"}}]}}' > "$FR_TR"
run check-friction-reflect.sh "{\"session_id\":\"smoke-c$$\",\"stop_hook_active\":false,\"transcript_path\":\"$FR_TR\"}" json  "friction-reflect/infra-write-warns"
rm -f "$FR_TR"
for s in "smoke-a$$" "smoke-b$$" "smoke-c$$"; do
  rm -f "/tmp/claude-fork-reflect-$(printf '%s' "$s" | python3 -c 'import hashlib,sys; print(hashlib.sha1(sys.stdin.read().encode()).hexdigest()[:16])' 2>/dev/null)" 2>/dev/null
done
# claude-md-lint: non-CLAUDE.md path MUST be silent; CLAUDE.md + signals MUST nudge.
run check-claude-md-lint.sh   '{"tool_input":{"file_path":"/x/README.md","content":"memory-library-discipline admin-merge"}}' empty "claude-md-lint/non-claude-silent"
run check-claude-md-lint.sh   '{"tool_input":{"file_path":"/x/CLAUDE.md","content":"memory-library-discipline and admin-merge"}}'  json  "claude-md-lint/restatement-nudge"
# fork-authoring-collision: a non-shared path must be silent (proves stdin is read).
run check-fork-authoring-collision.sh '{"tool_input":{"file_path":"/x/README.md"}}' empty "fork-authoring/non-shared-silent"

echo "Hook smoke-test: $PASS passed, $FAIL failed"
if [ "$FAIL" -ne 0 ]; then printf '  FAIL %s\n' "${FAILED[@]}"; exit 1; fi
exit 0
