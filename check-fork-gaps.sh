#!/usr/bin/env bash
# SessionStart awareness hook — surface OPEN entries from the fork-gaps backlog
# (docs/fork-gaps.md) so they don't rot in a file nobody opens.
#
# Enforcement class: DETERMINISTIC delivery of AWARENESS (tier 4). The text WILL
# reach the agent's context every session; the agent acting on it (surfacing to
# the user, routing a fix) is still probabilistic — paired with the prose policy
# (workflow-friction-and-process-issues) and the mason-bmad-workflow-expert
# first-action read. There is no deterministic GATE here on purpose: an open
# fork-gap is not a dangerous action to block, just rot to keep visible.
#
# Conservative detector: silent when there are zero open gaps (a false "you have
# work" every session erodes trust). Counts only un-resolved `### ` entries under
# `## Open` (entries closed in place with a `[resolved: …]` heading are excluded).
#
# Wired from ~/.claude/settings.json SessionStart (machine-local — hooks do NOT
# sync to the 13 projects; this surfacer ships only where settings.json calls it).
F="$HOME/bmad-method-v6/docs/fork-gaps.md"
[ -f "$F" ] || exit 0

python3 - "$F" <<'PY' 2>/dev/null || true
import json, re, sys

text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^## Open\b(.*?)(?=^## |\Z)", text, re.S | re.M)
body = m.group(1) if m else ""
titles = [
    h.strip()
    for h in re.findall(r"^### (.+)$", body, re.M)
    if "[resolved" not in h.lower()
]
if titles:
    msg = (
        "⚠ %d open fork-gap(s) in ~/bmad-method-v6/docs/fork-gaps.md "
        "(top: %s). If the user asks what to work on, or you're doing fork "
        "maintenance, surface these; route a chosen one via the "
        "mason-bmad-workflow-expert skill (it does not auto-action — the "
        "investment decision is the user's)." % (len(titles), titles[0])
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }))
PY
exit 0
