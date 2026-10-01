#!/usr/bin/env bash
# SessionStart — deploy-lane setup nudge (STD-DEPLOY-002, AWARENESS tier).
#
# The standard says a project's deploy lane must PROVE ten things, and that bringing a
# project up to it is Claude's job. This is the hook that puts that job in front of the
# next agent to open the project — as the FIRST priority of the session, not a line in a
# health report nobody re-reads. Owner instruction 2026-09-05: "the next agent in the
# relevant directory will auto-setup as their first priority".
#
# WHAT IT DOES. Runs the fork's checker on THIS project (the one the session opened,
# worktree-aware) and, only when the project is not MET / N/A, injects a bounded,
# structured first-priority instruction naming the state and the missing requirements.
#
# WHAT IT IS, HONESTLY. Tier 4: delivery is deterministic (the text WILL be in context),
# acting on it is the model's choice. It cannot make a session build a lane. It makes not
# knowing impossible, and it tells the agent exactly what "done" is (re-run the checker,
# get MET or N/A), which is the shape the enforcement-expert findings say persists.
#
# SILENT unless ALL of: the directory is a BMAD project (`_bmad/bmm/config.yaml`) · the
# fork checker is present · the state is GAPS, NOT DECLARED or UNKNOWN · no unexpired
# snooze. A non-BMAD directory, the fork itself, a MET project, a project declared
# `method: none`: nothing. Chattiness is what gets a SessionStart hook switched off.
#
# SNOOZE — for a session that genuinely must do something else first. Not silent:
#   echo "2026-09-12 reason" > .claude/.deploy-lane-setup.snooze     # ≤ 14 days, dated
# The date is read and enforced; an undated or expired snooze does not suppress. The
# snooze is logged when honoured, so a permanently-snoozed project is visible.
#
# Fails OPEN: any error exits 0 silently.

start="${CLAUDE_PROJECT_DIR:-$PWD}"
case "$start" in */.claude/worktrees/*) start="${start%%/.claude/worktrees/*}" ;; esac

# Walk up to the BMAD project root.
root="$start"
while [ -n "$root" ] && [ "$root" != "/" ]; do
  [ -f "$root/_bmad/bmm/config.yaml" ] && break
  root="$(dirname "$root")"
done
[ -f "$root/_bmad/bmm/config.yaml" ] || exit 0

CHECKER="${DEPLOY_LANE_CHECKER:-$HOME/bmad-method-v6/tools/check-deploy-lane.py}"
[ -f "$CHECKER" ] || exit 0

# Snooze: dated, bounded, logged.
snooze="$root/.claude/.deploy-lane-setup.snooze"
if [ -f "$snooze" ]; then
  until_day="$(head -1 "$snooze" | awk '{print $1}')"
  today="$(date -u +%Y-%m-%d)"
  max_day="$(date -u -v+14d +%Y-%m-%d 2>/dev/null || date -u -d '+14 days' +%Y-%m-%d 2>/dev/null || echo "$today")"
  if printf '%s\n' "$until_day" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' \
     && [ "$until_day" \> "$today" ] && [ ! "$until_day" \> "$max_day" ]; then
    mkdir -p "$HOME/.claude/logs" 2>/dev/null
    printf '{"at":"%s","hook":"deploy-lane-setup","project":"%s","snoozed_until":"%s"}\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(basename "$root")" "$until_day" \
      >> "$HOME/.claude/logs/deploy-lane-setup.jsonl" 2>/dev/null
    exit 0
  fi
fi

# The checker exits NON-ZERO whenever the project is not MET / N/A — the very case
# this hook exists to speak on — so its exit code is ignored and only its JSON counts.
# (The first cut did `|| exit 0` here and was silent on every project that needed it;
# the unit stub exited 0 and hid it. The suite now stubs the real exit code.)
out="$(python3 "$CHECKER" --project "$root" --json 2>/dev/null || true)"
[ -n "$out" ] || exit 0

python3 - "$out" "$(basename "$root")" <<'PY' 2>/dev/null || exit 0
import json, sys
s = json.loads(sys.argv[1]); name = sys.argv[2]
r = (s.get("results") or [{}])[0]
state = r.get("state", "UNKNOWN")
if state in ("MET", "N/A"):
    sys.exit(0)
rows = r.get("rows") or {}
missing = [k for k, v in rows.items() if v == "missing"]
declared = [k for k, v in rows.items() if v == "declared"]
why = (r.get("notes") or {}).get("why") or (r.get("notes") or {}).get("error") or ""
lines = [
    f"▶ FIRST PRIORITY THIS SESSION — deploy lane for {name}: {state} (STD-DEPLOY-002).",
]
if state == "NOT DECLARED":
    lines.append("  This project has never said whether it ships to production. Before other work:")
    lines.append("  1. Inspect: does it have a production environment? (Dockerfile / railway / vercel /")
    lines.append("     wrangler / fly / a deploy workflow / a deploy script are the tells; ask if unclear.)")
    lines.append("  2. Does not ship → declare it: _bmad/bmm/config.yaml → deploy: { method: none }.")
    lines.append("     Ships → declare deploy: { method, lane: scripts/deploy.sh } and build the lane to")
    lines.append("     the standard (_bmad/bmad-shared/deploy-lane-standard.md; reference: cash-recovery).")
elif state == "GAPS":
    lines.append(f"  Missing: {', '.join(missing) or '—'}"
                 + (f" · on trust only: {', '.join(declared)}" if declared else ""))
    lines.append("  Before other work, bring the lane to the standard —")
    lines.append("  _bmad/bmad-shared/deploy-lane-standard.md (reference: cash-recovery scripts/deploy.sh")
    lines.append("  + scripts/deploy-upload-root.test.sh; scripts/deploy-fingerprint.sh is already synced).")
else:
    lines.append(f"  The checker could not assess this project: {why[:120]}")
    lines.append("  Before other work, make it assessable (a readable _bmad/bmm/config.yaml deploy: block).")
lines.append("  Done when: python3 ~/bmad-method-v6/tools/check-deploy-lane.py --project . reports MET or N/A.")
lines.append("  Must defer? echo \"<YYYY-MM-DD ≤14d> <reason>\" > .claude/.deploy-lane-setup.snooze (logged).")
print("\n".join(lines))
PY
exit 0
