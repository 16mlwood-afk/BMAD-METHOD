#!/usr/bin/env python3
"""Golden cases for owner-step-handback-warn.py.

WEIGHTED TOWARDS SILENCE. The hook is warn-only, but a warning that appears on ordinary
replies gets ignored within a week and then warns nobody. So most cases below prove it
stays quiet: ordinary replies, commands quoted for reference, a hand-back being DISCUSSED
in quotes, and hand-backs carrying a genuine owner-only reason.

The FIRE cases include one near-verbatim per failure of 2026-09-19:
  (a) worktree isolation refused a main-checkout pull, handed back as `! cd ... && git pull`
  (b) "start a new session" for a hook, untested — it was live on the next prompt
  (c) a classifier-refused spend handed back as a `!` command

Run: python3 .claude/hooks/test_owner_step_handback_warn.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / 'owner-step-handback-warn.py'


def _load():
    spec = importlib.util.spec_from_file_location('handback_warn', HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = _load()
FAILURES: list[str] = []


def check(name: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


# ------------------------------------------------------------------ must FIRE

FIRE_A = (
    "The PR is merged. I can't do that from here — the worktree isolation refuses a pull "
    "on the main checkout. Run this:\n\n```\n! cd /Users/masonwood/code/amazon-removal-assistant "
    "&& git pull --ff-only\n```"
)
FIRE_B = (
    "The hook is wired in .claude/settings.json and committed. Start a new session for it "
    "to take effect."
)
FIRE_C = (
    "The subagent was refused by the auto-mode classifier on the MyFlyingBox booking, so "
    "it is ready for you: `! npx tsx scripts/flyingbox-ship.ts --confirm --shipment 457845`"
)

FIRES = [
    ('(a) worktree pull handed back', FIRE_A),
    ('(b) untested new-session claim', FIRE_B),
    ('(c) classifier-refused spend handed back', FIRE_C),
    ('leading-! instruction',
     'Blocked here. Run npm run prep:handling -- --confirm --budget=78 with a leading `!` '
     'and I will pick up from the output.'),
    ('run it yourself',
     'The command is `npm run prep:reconcile`. You will need to run it, I will read the output.'),
    ('paste this', 'Paste this into your terminal:\n\n    git worktree prune'),
    ('restart for a hook',
     'Done. Restart Claude Code so the new hook takes effect.'),
    ('bare ! line in prose', 'Nearly there.\n! git -C ../.. pull --ff-only\nThen tell me.'),
]

# ------------------------------------------------------------- must STAY SILENT

SILENT = [
    ('ordinary report',
     'Merged. The pallet draft for Leipzig now holds 19 lines, and nothing waits on you.'),
    ('command quoted for reference',
     'I ran `git pull --ff-only` on the main checkout after leaving the worktree, and it '
     'fast-forwarded three commits.'),
    ('fenced command shown, not handed over',
     'This is what fixed it:\n\n```\ngit -C /Users/masonwood/code/amazon-removal-assistant '
     'pull --ff-only\n```\n\nIt ran cleanly.'),
    ('hand-back discussed in quotes',
     'The earlier reply said "I can\'t do that from here, run `! cd … && git pull`", which '
     'was wrong: ExitWorktree leaves the worktree in one call.'),
    ('a login is genuinely his',
     'The prep cabinet session has expired and only you can log in. Run `! open '
     'https://thefbaprep.com/login` and I will carry on once the cookie is fresh.'),
    ('a card payment is genuinely his',
     'The Parcel2Go balance needs topping up by card before the booking goes through: '
     '`! open https://www.parcel2go.com/myaccount/topup`'),
    ('a physical act',
     'Somebody has to physically count the plugs on the shelf at Leipzig. Paste this to '
     'them when you message.'),
    ('explicit marker',
     '[OWNER STEP: auto-mode classifier refused this in the main thread too]\n'
     '`! npm run prep:handling -- --confirm --budget=78`'),
    ('owner gate label',
     '[OWNER GATE: commercial-commitment] This buys 73 fittings. Run it yourself if you '
     'want it: `! npm run pallet:order -- --confirm`'),
    ('mcp restart is a real need',
     'Merged. Restart Claude Code so the MCP server reloads — the running process holds '
     'the code as at startup.'),
    ('not-equals and css bang',
     'The check is `a !== b` and the old stylesheet used `color: red !important`.'),
    ('new session mentioned without instruction',
     'The session that started this morning found the stale draft.'),
    ('prompt handed to another chat, measured real reply',
     'Your revised prompt is ready. Copy the prompt below and paste it as your first message '
     'in a new conversation, with the seven images attached.'),
    ('brief handed to Claude Design, measured real reply',
     'Here it is. Attach the two files from that folder and paste this:\n\n---\n\n'
     'I have attached a working web page and the brief that governs it.'),
    ('main checkout is not a card-payment reason, and not a hand-back either',
     'I left the worktree and pulled the main checkout; it is on main and current.'),
    ('empty', ''),
]


def detection_cases() -> None:
    for name, text in FIRES:
        check(f'FIRES {name}', hook.handback(text) is not None, True)
    for name, text in SILENT:
        check(f'SILENT {name}: got {hook.handback(text)!r}', hook.handback(text) is None, True)


# ------------------------------------------------------------------ end to end

def _run(stdin: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True,
        env=dict(os.environ), timeout=30,
    )
    return done.returncode, done.stdout.strip()


def end_to_end_cases() -> None:
    for label, text in (('(a)', FIRE_A), ('(b)', FIRE_B), ('(c)', FIRE_C)):
        code, out = _run(json.dumps({'last_assistant_message': text}))
        check(f'{label} exit 0', code, 0)
        payload = json.loads(out) if out else {}
        msg = payload.get('systemMessage', '')
        check(f'{label} warns', msg.startswith('OWNER-STEP HANDBACK'), True)
        check(f'{label} never blocks', 'decision' in payload, False)
        check(f'{label} names ExitWorktree', 'ExitWorktree' in msg, True)
        check(f'{label} names the test-it route', 'TEST it on the next prompt' in msg, True)
        check(f'{label} names the main-thread route', 'MAIN THREAD' in msg, True)

    code, out = _run(json.dumps({'last_assistant_message': SILENT[0][1]}))
    check('clean reply: exit', code, 0)
    check('clean reply: stdout', out, '')

    code, out = _run(json.dumps({'last_assistant_message': FIRE_A, 'stop_hook_active': True}))
    check('re-entry: stdout', out, '')

    code, out = _run(json.dumps({'transcript_path': '/nonexistent/path.jsonl'}))
    check('no inline text: stdout', out, '')

    code, out = _run(json.dumps({'last_assistant_message': {'content': [
        {'type': 'text', 'text': FIRE_B}]}}))
    check('content-block payload: warns', 'OWNER-STEP HANDBACK' in out, True)

    for bad in ('not json', '[]', '"a string"'):
        code, out = _run(bad)
        check(f'malformed {bad!r}: exit', code, 0)
        check(f'malformed {bad!r}: stdout', out, '')


def main() -> int:
    detection_cases()
    end_to_end_cases()
    if FAILURES:
        print(f'{len(FAILURES)} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print(f'all owner-step-handback-warn cases pass ({len(FIRES)} fire, {len(SILENT)} silent)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
