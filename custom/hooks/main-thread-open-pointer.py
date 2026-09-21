#!/usr/bin/env python3
"""UserPromptSubmit — keep the main conversation free for the owner to talk.

WHY THIS EXISTS
---------------
Owner instruction, 2026-09-19, the second time that day:

    "Can we set up a rule um, a keep mentioning it but it's just not getting used again
    okay, so I love the idea of keeping this main chat going while the sub agents are
    doing the work and, and therefore we can just we can pass info to mid implementation
    and, and and it makes more sense that way"

Earlier the same day: "use subagents to keep this main open so we can chat". A prose
memory held the rule (`feedback-subagents-keep-main-open.md`) and it was not being used.
That is the ordinary fate of a rule that has to be RECALLED: it is in the library, and
nothing puts it on the desk at the moment the session decides how to do the work. This
hook puts it on the desk, every turn.

THE RULE, which CLAUDE.md § "The main conversation stays open" owns:
  - multi-step work goes to a BACKGROUND agent, so the owner can keep talking;
  - what he says mid-task reaches that running agent through SendMessage, rather than
    waiting for it to finish or stopping and restarting it;
  - a quick read or one or two commands stays in the main thread.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It never blocks, never counts tool calls, words or files, and never judges whether a
turn SHOULD have delegated. The owner's global rules forbid a blunt hook that forces
subagent use from counts: it produces delegation theatre and buries the real signal.
Whether a piece of work is big enough to hand off is a judgement, and it stays one.

SILENT INSIDE A SUBAGENT. A subagent has no conversation to keep open, and telling it
to delegate further invites nested agents. UserPromptSubmit fires on a user prompt to
the main thread, so a subagent should never reach this hook at all; the check below is
the belt to that braces. It goes silent when the payload carries `agent_id` or
`agent_type` (present when a hook runs inside a subagent), or when the transcript path
is a subagent transcript (`.../subagents/...`). Any one signal is enough — a missed
reminder in the main thread costs one turn, a reminder inside an agent costs a nested
spawn.

ENFORCEMENT, split honestly.
  DETERMINISTIC DELIVERY: the reminder is in context on every main-thread turn.
  PROBABILISTIC COMPLIANCE: whether the session then delegates, and whether it relays
  mid-task information with SendMessage, is the model's choice. No hook can read that,
  and building one keyed on counts is the thing the owner has ruled out.

Golden cases: python3 .claude/hooks/test_main_thread_open_pointer.py
"""

from __future__ import annotations

import json
import sys

REMINDER = (
    'KEEP THIS CONVERSATION OPEN (owner rule, 2026-09-19). Mason wants to keep talking '
    'while work happens. Anything beyond a quick read or one or two commands (a build, a '
    'PR, a document, an investigation, a multi-step fix) goes to an Agent with '
    '`run_in_background: true`, plus `isolation: "worktree"` if it edits files, and this '
    'thread stays short. If he adds information, corrects something or changes his mind '
    'while an agent is running, pass it to THAT agent with SendMessage (by its id or name; '
    'load the tool with ToolSearch if it is deferred). Do not wait for the agent to finish, '
    'and do not stop and respawn it. Answer his question here, now. This is a reminder, '
    'not a quota: a quick answer stays in this thread. CLAUDE.md § "The main conversation '
    'stays open".'
)

SUBAGENT_KEYS = ('agent_id', 'agent_type')


def in_subagent(payload: dict) -> bool:
    """True when any signal says this hook is running inside a subagent."""
    for key in SUBAGENT_KEYS:
        if payload.get(key):
            return True
    transcript = str(payload.get('transcript_path') or '')
    return '/subagents/' in transcript.replace('\\', '/')


def reminder_for(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    if in_subagent(payload):
        return None
    return REMINDER


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # A malformed payload must never cost the session its prompt.
        return 0

    text = reminder_for(payload)
    if text is None:
        return 0

    print(
        json.dumps(
            {
                'hookSpecificOutput': {
                    'hookEventName': 'UserPromptSubmit',
                    'additionalContext': text,
                }
            }
        )
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
