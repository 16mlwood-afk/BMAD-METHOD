#!/usr/bin/env bash
# PreToolUse(Edit|Write|Bash) — SPRINT-APPLY GATE.
#
# Freezes ONLY the tracker files a pending correct-course proposal named, until an
# APPROVE: APPLY_SPRINT_PROPOSAL::<id> token clears them (via sprint-apply-approve.sh).
# Scoped to the proposal's files_to_change set — never the normal
# sprint-planning / create-story / dev-story authoring lane, which touches OTHER files.
#
#   MODE dry-run (DEFAULT): logs WOULD-BLOCK, ALLOWS, emits NO stdout → zero risk.
#   MODE enforce: denies via permissionDecision. Flip ONLY after the dry-run log is
#     proven quiet (warn-then-gate) by writing "enforce" to
#     ~/.claude/sprint-apply-gate.mode.
# Override (deliberate + LOGGED): <root>/_bmad/.sprint-apply-override with a reason.
#
# NOT wired into any project's settings yet — inert until registered + session restart.
in=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"
pending="$root/_bmad/.sprint-apply-pending.json"
[ -f "$pending" ] || exit 0                      # nothing pending → allow everything

# Extract the target path from Edit/Write file_path, or from a Bash edit-equivalent.
# Data is passed via env vars, NOT stdin — a heredoc script + a stdin pipe would collide.
target=$(CC_IN="$in" CC_ROOT="$root" python3 <<'PY' 2>/dev/null
import os, json, re
root = os.environ["CC_ROOT"]
d = json.loads(os.environ.get("CC_IN", "{}")); ti = d.get("tool_input", {})
p = ti.get("file_path") or ""
if not p:
    cmd = ti.get("command", "")
    if re.search(r'\bsed\s+-i', cmd):
        # sed -i (GNU) / sed -i '' (BSD/macOS): the file arg is conventionally last.
        toks = cmd.split()
        p = toks[-1] if toks else ""
    else:
        m = re.search(r'(?:>>?|tee|cat >)\s+([^\s;&|]+)', cmd)
        p = m.group(1) if m else ""
print(os.path.abspath(os.path.join(root, p)) if p and not p.startswith("/") else p)
PY
)
[ -n "$target" ] || exit 0

# Is the target in this proposal's frozen file set?
frozen=$(CC_PEND="$pending" CC_ROOT="$root" CC_TARGET="$target" python3 <<'PY' 2>/dev/null
import os, json
pend, root, target = os.environ["CC_PEND"], os.environ["CC_ROOT"], os.environ["CC_TARGET"]
j = json.load(open(pend))
for f in j.get("files_to_change", []):
    if os.path.abspath(os.path.join(root, f)) == target:
        print(j.get("proposal_id", "?")); break
PY
)
[ -n "$frozen" ] || exit 0                        # target not frozen → allow

# Approved already (token cleared it this session)?
appr="$root/_bmad/.sprint-apply-approved.json"
if [ -f "$appr" ] && grep -q "\"$frozen\"" "$appr" 2>/dev/null; then exit 0; fi

log="$HOME/.claude/sprint-apply-gate.log"
proj=$(basename "$root")
ts=$(date '+%F %T' 2>/dev/null || echo '?')

# Deliberate, logged override → allow.
if [ -f "$root/_bmad/.sprint-apply-override" ]; then
  printf '%s OVERRIDE %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
  exit 0
fi

mode=""
[ -f "$HOME/.claude/sprint-apply-gate.mode" ] && mode=$(tr -d '[:space:]' < "$HOME/.claude/sprint-apply-gate.mode" 2>/dev/null)
if [ "$mode" = "enforce" ]; then
  printf '%s DENY %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
  reason="$target is frozen by pending Sprint Change Proposal $frozen. To apply: send 'APPROVE: APPLY_SPRINT_PROPOSAL::$frozen' (clears the gate for exactly the proposal's files_to_change). Or write $root/_bmad/.sprint-apply-override with a reason (logged)."
  rj=$(python3 -c "import json,sys;print(json.dumps(sys.argv[1]))" "$reason" 2>/dev/null)
  [ -n "$rj" ] && printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}' "$rj"
  exit 0
fi

# dry-run (default): record what it WOULD block, but ALLOW (no stdout).
printf '%s WOULD-BLOCK %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
exit 0
