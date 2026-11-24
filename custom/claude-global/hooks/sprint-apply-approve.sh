#!/usr/bin/env bash
# UserPromptSubmit — SPRINT-APPLY APPROVAL.
#
# Clears the sprint-apply gate when the user sends the approval token:
#   APPROVE: APPLY_SPRINT_PROPOSAL::<proposal_id>
# The token's <proposal_id> MUST match the pending marker; a free-form "go ahead"
# does NOT clear the gate (that is the whole point — the token is the proof tier).
# On match it copies the pending marker to .sprint-apply-approved.json, opening the
# gate for exactly that proposal's files_to_change set.
#
# Always exits 0 (never blocks a prompt). Inert until wired into settings + restart.
in=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"
prompt=$(printf '%s' "$in" | python3 -c "import sys,json;print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null)
id=$(printf '%s' "$prompt" | sed -n 's/.*APPROVE: APPLY_SPRINT_PROPOSAL::\([A-Za-z0-9._-]\{1,\}\).*/\1/p' | head -1)
[ -n "$id" ] || exit 0

pending="$root/_bmad/.sprint-apply-pending.json"
[ -f "$pending" ] || exit 0
grep -q "\"$id\"" "$pending" 2>/dev/null || exit 0      # token id must match the pending proposal

cp "$pending" "$root/_bmad/.sprint-apply-approved.json" 2>/dev/null
printf '%s APPROVE %s :: %s\n' "$(date '+%F %T' 2>/dev/null || echo '?')" "$(basename "$root")" "$id" >> "$HOME/.claude/sprint-apply-gate.log" 2>/dev/null
echo "Sprint Change Proposal $id approved — its files_to_change set is now writable this session."
exit 0
