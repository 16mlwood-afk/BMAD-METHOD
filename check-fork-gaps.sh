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
# Entry detection (fixed 2026-07-03 — the original matched only `### ` headings
# inside a `## Open` section capture, which went blind the day entries started
# using `## YYYY-MM-DD — title` headings): an entry is ANY ##/### heading after
# the `## Open` line. Closed = `[resolved`/`[closed` in the heading (any case),
# OR a bold `**CLOSED`/`**RESOLVED` closure paragraph in the body.
# `[partly resolved …]` stays OPEN (it names an owed follow-up).
#
# Also nudges (one line) when the periodic fork-gaps TREND SCAN is overdue:
# stamp file .fork-gaps-last-scan (gitignored, touched by the scan) older than
# 30 days or missing. Deterministic delivery, probabilistic action — the scan
# itself runs via the maintenance-session skill's "fork-gaps trend scan" lane.
#
# Conservative detector: silent when there are zero open gaps AND the scan is
# fresh (a false "you have work" every session erodes trust).
#
# Wired from ~/.claude/settings.json SessionStart (machine-local — hooks do NOT
# sync to the 13 projects; this surfacer ships only where settings.json calls it).
F="$HOME/bmad-method-v6/docs/fork-gaps.md"
STAMP="$HOME/bmad-method-v6/.fork-gaps-last-scan"
[ -f "$F" ] || exit 0

python3 - "$F" "$STAMP" <<'PY' 2>/dev/null || true
import json, os, re, sys, time

text = open(sys.argv[1], encoding="utf-8").read()
stamp = sys.argv[2]

entries = []  # [title, body_lines]
cur = None
started = False
for ln in text.splitlines():
    m = re.match(r"^#{2,3} (.+)$", ln)
    if m:
        title = m.group(1).strip()
        if title == "Open":
            started = True
            cur = None
            continue
        if not started:
            continue
        cur = [title, []]
        entries.append(cur)
    elif cur is not None:
        cur[1].append(ln)

def is_open(title, body_lines):
    t = title.lower()
    if "[resolved" in t or "[closed" in t:
        return False
    body = "\n".join(body_lines).lower()
    if "**closed" in body or "**resolved" in body:
        return False
    return True

open_titles = [t for t, b in entries if is_open(t, b)]

parts = []
if open_titles:
    parts.append(
        "⚠ %d open fork-gap(s) in ~/bmad-method-v6/docs/fork-gaps.md "
        "(top: %s). If the user asks what to work on, or you're doing fork "
        "maintenance, surface these; route a chosen one via the "
        "mason-bmad-workflow-expert skill (it does not auto-action — the "
        "investment decision is the user's)." % (len(open_titles), open_titles[-1][:120])
    )

THIRTY_DAYS = 30 * 24 * 3600
try:
    age = time.time() - os.path.getmtime(stamp)
except OSError:
    age = None
if age is None or age > THIRTY_DAYS:
    last = "never" if age is None else "%dd ago" % (age // 86400)
    parts.append(
        "fork-gaps trend scan overdue (last: %s) — when the user starts a "
        "maintenance session, offer the 'fork-gaps trend scan' lane "
        "(3 questions over the last ~10 entries; see fork-gaps.md § Trend scan)." % last
    )

if parts:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": " | ".join(parts),
        }
    }))
PY
exit 0
