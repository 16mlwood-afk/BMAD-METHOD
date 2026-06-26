#!/usr/bin/env bash
# Stop hook — fire-once end-of-session friction reflection.
#
# Asks ONCE per session, as the agent goes to finish: "did the fork/infra/method
# structurally fight you? if so, log it to fork-gaps.md." Then the agent chooses.
#
# Enforcement class: DETERMINISTIC delivery of the prompt (the Stop hook WILL fire
# and the reflection WILL reach the model exactly once) — but the act of noticing
# friction and logging is irreducibly PROBABILISTIC (no hook can force a model to
# recognise that friction was structural). This is the honest best lever for the
# write side, paired with the SessionStart awareness surfacer + the prose policy.
#
# Fire-once, loop-safe by two guards: (1) `stop_hook_active` — the harness sets it
# when a stop is itself the result of a stop-hook continuation, so we never re-block
# our own continuation; (2) a per-session marker keyed on session_id. Either alone
# prevents an infinite "can't finish" loop; both = belt-and-suspenders.
#
# Wired from ~/.claude/settings.json Stop (machine-local — does not sync to the 13
# projects). Conservative by design: a no-friction session dismisses in one line.
python3 - <<'PY'
import json, sys, os, hashlib

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

# Guard 1: never re-block a stop that we ourselves forced a continuation into.
if data.get("stop_hook_active"):
    sys.exit(0)

# Guard 2: one prompt per session.
sid = str(data.get("session_id") or os.environ.get("CLAUDE_SESSION_EPOCH", "unknown"))
marker = "/tmp/claude-fork-reflect-" + hashlib.sha1(sid.encode()).hexdigest()[:16]
if os.path.exists(marker):
    sys.exit(0)
try:
    open(marker, "w").close()
except Exception:
    pass  # if we can't write the marker, stop_hook_active still prevents a loop

reason = (
    "Before finishing — one reflection: did the fork / infra / method "
    "structurally fight you this session? Not a one-off bug, but the WIRING "
    "making normal work painful (a deploy path that isn't legible, a hook with "
    "nowhere to redirect, sync drift, a workflow step that overran, shared "
    "state). If yes, log it once to ~/bmad-method-v6/docs/fork-gaps.md per the "
    "workflow-friction policy — name the specific target file. If nothing "
    "structural fought you, say 'no fork-gaps to log' in one line and finish."
)
print(json.dumps({"decision": "block", "reason": reason}))
PY
exit 0
