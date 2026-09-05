#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# check-wip-register.sh — SessionStart awareness surfacer for in-flight feature
# work claimed by OTHER parallel sessions (the read side of wip-register.sh).
#
# Enforcement class: DETERMINISTIC delivery of AWARENESS (tier 4). The list WILL
# reach the arriving session's context every start; acting on it (not starting
# overlapping work) stays the model's choice — by design. There is NO hard gate:
# "same feature" is not deterministically detectable (branch names differ), so a
# block would be the indiscriminate-gate anti-pattern. Paired with the prose in
# parallel-sessions.md §E.
#
# Conservative detector: silent when there are no LIVE foreign claims (a false
# "someone's on this" every session erodes the channel). Live = the claim's
# worktree directory still exists on disk (the strongest liveness signal — an
# ExitWorktree clears the claim; a removed worktree whose claim lingered is
# filtered here as the backstop). A session never sees its OWN worktree's claim.
#
# Ledger anchored at the MAIN checkout (shared across worktrees) via
# git-common-dir, so a claim written from any worktree is visible to all.
#
# Wired from ~/.claude/settings.json SessionStart (machine-local — hooks do NOT
# sync to the projects; this surfacer ships only where settings.json calls it).
# ──────────────────────────────────────────────────────────────────────────

# Resolve the MAIN repo root from wherever the session started (worktree or not).
gcd=$(git rev-parse --git-common-dir 2>/dev/null) || exit 0
case "$gcd" in /*) ;; *) gcd="$PWD/$gcd" ;; esac   # absolutise a relative .git
main_root=$(cd "$(dirname "$gcd")" 2>/dev/null && pwd) || exit 0
reg="$main_root/.claude/wip-register.yaml"
[ -f "$reg" ] || exit 0

# This session's own worktree top-level (so we don't warn about our own claim).
self_top=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

python3 - "$reg" "$self_top" <<'PY' 2>/dev/null || true
import json, os, re, sys
from datetime import datetime, timezone

reg, self_top = sys.argv[1], sys.argv[2]
rows = []
for ln in open(reg, encoding="utf-8"):
    ln = ln.strip()
    if not ln.startswith("- {"):
        continue
    def f(key):
        m = re.search(r'%s: "((?:[^"\\]|\\.)*)"' % key, ln)
        return (m.group(1).replace('\\"', '"').replace("\\\\", "\\")) if m else ""
    wt = f("worktree")
    if not wt or not os.path.isdir(wt):   # dead claim — worktree gone
        continue
    if self_top and os.path.realpath(wt) == os.path.realpath(self_top):
        continue                          # our own claim
    rows.append({"branch": f("branch"), "wt": wt, "desc": f("description"), "started": f("started")})

if not rows:
    sys.exit(0)

def age(iso):
    try:
        t = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        h = (datetime.now(timezone.utc) - t).total_seconds() / 3600
        if h < 1:   return "%dm" % max(1, int(h * 60))
        if h < 24:  return "%dh" % round(h)
        return "%dd (stale?)" % round(h / 24)
    except Exception:
        return "?"

items = "; ".join(
    "%s%s [%s]" % (r["branch"] or "(branch?)",
                   " — " + r["desc"] if r["desc"] else "",
                   age(r["started"]))
    for r in rows
)
msg = (
    "🔨 In-flight feature work by other session(s): %s. "
    "Before starting overlapping work, check whether your task duplicates one of "
    "these (branch names differ — judge by description/area, not name). If it "
    "might, surface it to the user rather than building blind. See "
    "parallel-sessions.md §E; the register is .claude/wip-register.yaml." % items
)
print(json.dumps({
    "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}
}))
PY
exit 0
