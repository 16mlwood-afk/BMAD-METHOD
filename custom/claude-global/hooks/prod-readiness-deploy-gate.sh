#!/usr/bin/env bash
# PreToolUse(Bash) — prod-readiness DEPLOY GATE.
#
# Stops a production deploy of a live BMAD project that has NO deploy contract.
#   MODE dry-run (DEFAULT): logs what it WOULD block, ALLOWS, emits NO stdout
#     → zero risk of interfering with the Bash call. This is the live "Item A" watch.
#   MODE enforce: denies via permissionDecision. Flip ONLY after the dry-run log is
#     proven clean (warn-then-gate) by writing "enforce" to
#     ~/.claude/prod-readiness-gate.mode.
# Override (deliberate + LOGGED): a marker file <root>/_bmad/.prod-readiness-override.
# Detection is the shared pr_* library — identical to the SessionStart probe.
. "$(dirname "$0")/lib/prod-readiness-detect.sh" 2>/dev/null || exit 0

in=$(cat)
# Fast pre-filter: 99% of Bash calls aren't deploys → one grep, then exit (no python).
printf '%s' "$in" | grep -qE 'railway[[:space:]]+(up|redeploy)|bmad-deploy\.sh|git[[:space:]]+push' || exit 0

cmd=$(printf '%s' "$in" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
case "$cmd" in
  *"railway up"*|*"railway redeploy"*|*"bmad-deploy.sh"*) : ;;   # explicit deploy verb
  *"git push"*" main"*|*"git push"*" master"*) : ;;             # push to default branch → auto-deploy
  *) exit 0 ;;                                                   # ambiguous → allow
esac
# The " main"/" master" match needs a leading space, so a branch like feature/main
# (no space) does NOT match. A ref like HEAD:main is a false-negative (acceptable —
# bias to allow). Direct pushes to the default branch are rare (the contract is
# branch+PR), so this fires almost only on a genuine auto-deploy push.

start="${CLAUDE_PROJECT_DIR:-$PWD}"
root=$(pr_is_gap "$start") || exit 0   # not a gap (or not BMAD / not live / has doc) → allow

log="$HOME/.claude/prod-readiness-gate.log"
proj=$(basename "$root")
ts=$(date '+%F %T' 2>/dev/null || echo '?')

# Deliberate, logged override → allow.
if [ -f "$root/_bmad/.prod-readiness-override" ]; then
  printf '%s OVERRIDE %s :: %s :: %s\n' "$ts" "$proj" "$(head -1 "$root/_bmad/.prod-readiness-override" 2>/dev/null)" "$cmd" >> "$log" 2>/dev/null
  exit 0
fi

mode=""
[ -f "$HOME/.claude/prod-readiness-gate.mode" ] && mode=$(tr -d '[:space:]' < "$HOME/.claude/prod-readiness-gate.mode" 2>/dev/null)
if [ "$mode" = "enforce" ]; then
  printf '%s DENY %s :: %s\n' "$ts" "$proj" "$cmd" >> "$log" 2>/dev/null
  reason="$proj is live (project_phase=$(pr_phase "$root")) with NO deploy contract/doc. Author one (prod-readiness-charter.md State 2), or create $root/_bmad/.prod-readiness-override with a reason to deploy anyway (logged)."
  rj=$(python3 -c "import json,sys;print(json.dumps(sys.argv[1]))" "$reason" 2>/dev/null)
  [ -n "$rj" ] && printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}' "$rj"
  exit 0
fi

# dry-run (default): record what it WOULD block, but ALLOW (no stdout).
printf '%s WOULD-BLOCK %s :: %s\n' "$ts" "$proj" "$cmd" >> "$log" 2>/dev/null
exit 0
