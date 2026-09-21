#!/usr/bin/env python3
"""Stop — WARN when a reply hands Mason a step he did not need to take.

WHY THIS EXISTS
---------------
2026-09-19, one session, three times, each time after something refused it:

  (a) Claude Code's worktree isolation refused `git -C <main checkout> pull`. The reply
      said "I can't do that from here, run `! cd ... && git pull`". ExitWorktree (a deferred
      tool, loaded through ToolSearch) leaves the worktree in one call and the pull then
      works. Proven the same day.
  (b) The reply said "start a new session" for a hook to take effect, without testing it.
      The hook was live on the very next prompt.
  (c) The auto-mode classifier refused a subagent's spend on a MyFlyingBox booking and the
      step went back to him as a `!` command. Run in the main thread on his in-the-moment
      words ("can you put in via api for me"), it worked.

The owner, verbatim: *"you're treating the refusal as a dead end. You keep seeing this
pattern behavior... if you can just perform the next autonomous action"*.

A refusal is information about what ONE route covers. It is not a verdict on the task.

WHAT IT DETECTS, AND WHY A CONJUNCTION
--------------------------------------
It fires when the reply being closed carries a HAND-BACK SHAPE and NO STATED REASON only
Mason can do the step.

  Hand-back shapes: a runnable `! <command>` (at the start of a line, fenced or not, or as
  inline code), "with a leading !", "run this yourself", "paste this into your terminal",
  "you'll need to run",
  "I can't do that from here", "start a new session", "restart Claude Code for the hook to
  take effect".

  Allowed reasons: a login, a card or payment, a physical act, an authority decision
  (`[OWNER GATE: ...]`, "your approval", "only you can"), or the literal marker
  `[OWNER STEP: <reason>]`.

Material inside double quotes is ignored, so a reply that QUOTES a hand-back while
discussing one stays quiet. A command shown for reference ("I ran `git pull --ff-only`")
has no `!` and no hand-back phrase, so it stays quiet too.

"Restart Claude Code so the MCP server reloads" is NOT a trigger. The server holds its code
as at startup and no session can restart itself, which this repository has proved; the
trigger is the restart claimed for a hook or setting, which is failure (b).

WHY WARN-ONLY, AND IT IS THE DESIGN RATHER THAN A STAGE
-------------------------------------------------------
Whether a legitimate alternative route existed is a judgement no regex can make. A block on
a correct hand-back — a genuine login, a card — would stop a session mid-delivery for no
reason, and a guard that does that gets unwired. So it never blocks and never emits
`decision`. It prints a `systemMessage`, the same convention as the global warn-only Stop
hooks, and exits 0 on every path.

TIERS, HONESTLY
---------------
  DETERMINISTIC: delivery of the warning, whenever the shape matches and no reason is stated.
  PROBABILISTIC: whether the session then finds the alternative route. And the warning is
  shown on screen at the end of the turn: the session is not guaranteed to read it before
  the next prompt, so its practical effect is that Mason can see the rule was broken.

WHAT IT CANNOT DO, so a silent run is not a certificate
--------------------------------------------------------
It reads words. A hand-back phrased differently passes. A stated reason that is false
("this needs your login" when it does not) passes. It grades the reply being closed and, if
the harness does not pass that text inline, it stays silent rather than grade the previous
turn from the transcript.

Golden cases: python3 .claude/hooks/test_owner_step_handback_warn.py
Rule: CLAUDE.md, "A refusal covers one route, not the task".
"""

from __future__ import annotations

import json
import re
import sys

MARKER = 'OWNER-STEP HANDBACK'

# Double-quoted spans, straight and curly: quoted material is being discussed, not said.
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”')

# A runnable `! command` — the Claude Code shell-escape Mason would type.
BANG_LINE = re.compile(r'(?m)^[ \t]*(?:[-*>][ \t]+)?!\s+[A-Za-z0-9./~$(]')
BANG_INLINE = re.compile(r'`!\s+[A-Za-z0-9./~$(][^`]*`')

HANDBACK_PHRASES = re.compile(
    r"with a leading `?!`?"
    r"|prefix(?:ed)? (?:it )?with `?!`?"
    r"|\brun (?:this|it|that|these|them|the following) yourself\b"
    r"|\byou(?:'ll| will)? (?:need|have) to run\b"
    # Paste is a trigger only into a TERMINAL. Pasting a prompt into another chat or into
    # Claude Design is a surface on his account that no session can reach, and measured over
    # 384 real turns those were the only paste hits that were not a hand-back.
    r"|\b(?:copy and )?paste (?:this|it|that|these|the following)(?: command)? (?:in|into) (?:your|a|the) (?:terminal|shell)\b"
    r"|\bI (?:can't|cannot|can not|am not able to|'m not able to) (?:do|run) (?:that|this|it) from here\b"
    r"|\bstart (?:a )?(?:new|fresh) (?:session|conversation)\b"
    r"|\bopen (?:a )?(?:new|fresh) session\b"
    r"|\bin (?:a )?(?:new|fresh) session\b"
    r"|\brestart (?:Claude Code|the session|your session)\b[^.\n]{0,40}\b(?:hook|setting|settings|rule|change)s?\b",
    re.IGNORECASE,
)

REASONS = re.compile(
    r"\[OWNER STEP:\s*[^\]\s][^\]]*\]"
    r"|\[OWNER GATE:\s*[^\]\s][^\]]*\]"
    # a login
    r"|\blog ?in\b|\blogin\b|\bsign(?:ed)? ?in\b|\b2FA\b|two-factor|\bpassword\b"
    r"|one-time code|\bre-?authenticat"
    # a card or payment
    r"|\bcard\b|\bpayment\b|\bpay\b"
    # a physical act
    r"|\bphysical(?:ly)?\b|\bin person\b"
    # an authority decision
    r"|\byour (?:approval|authority|sign-off|decision)\b|\bonly you can\b",
    re.IGNORECASE,
)

ALTERNATIVES = (
    '(a) a step on the MAIN CHECKOUT for already-merged work: call ExitWorktree (load it '
    'through ToolSearch), then run it from there; '
    '(b) "start a new session" / "restart for it to take effect": TEST it on the next '
    'prompt before claiming it; '
    '(c) an owner-authorised spend the classifier refused in a subagent: run it in the '
    'MAIN THREAD on his in-the-moment words.'
)


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                out.append(block.get('text') or '')
        return '\n'.join(out)
    return ''


def current_turn_text(payload: dict) -> str:
    """The reply being closed, passed inline under a version-dependent key.

    The transcript file still ends at the PREVIOUS turn when a Stop hook fires, so if the
    inline text is absent this returns empty and the caller stays silent.
    """
    for key in ('last_assistant_message', 'assistant_message', 'response', 'message', 'output'):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, dict):
            text = _content_text(val.get('content'))
            if text.strip():
                return text
    return ''


def handback(text: str) -> str | None:
    """The hand-back shape, when the reply hands over a step and states no allowed reason."""
    if not text:
        return None
    spoken = QUOTED.sub(' ', text)
    if REASONS.search(spoken):
        return None
    for pattern in (BANG_LINE, BANG_INLINE, HANDBACK_PHRASES):
        hit = pattern.search(spoken)
        if hit:
            return hit.group(0).strip()
    return None


def warning(shape: str) -> str:
    return (
        f'{MARKER} (warn-only, nothing blocked): this reply hands Mason a step to take '
        f'himself — "{shape[:80]}" — and states no reason only he can do it (a login, a '
        'card payment, a physical act, an authority decision, or [OWNER STEP: <reason>]). '
        'A refusal covers ONE route, not the task. Name what refused and what it covers, '
        f'then take the legitimate route: {ALTERNATIVES} Never route around a safety '
        'boundary itself, and worktrees stay mandatory. '
        'CLAUDE.md: "A refusal covers one route, not the task".'
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        if not isinstance(payload, dict) or payload.get('stop_hook_active'):
            return 0
        shape = handback(current_turn_text(payload))
        if shape:
            print(json.dumps({'systemMessage': warning(shape)}))
    except Exception:
        pass  # fail-open: a warning is never worth wedging a session
    return 0  # WARN-ONLY — never blocks


if __name__ == '__main__':
    sys.exit(main())
