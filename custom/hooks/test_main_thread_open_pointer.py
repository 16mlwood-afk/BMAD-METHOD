#!/usr/bin/env python3
"""Golden cases for main-thread-open-pointer.py.

Run: python3 .claude/hooks/test_main_thread_open_pointer.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / 'main-thread-open-pointer.py'

# WHERE THE WIRING LIVES DEPENDS ON WHERE THIS FILE IS.
# Installed in a project it is <root>/.claude/settings.json. In the BMAD fork — the
# SOURCE of this hook, which has no .claude/settings.json of its own — the wiring that
# decides whether fourteen projects get it is the DISTRIBUTION TEMPLATE. Checking that
# here makes this a completeness invariant on the distribution: add a hook to
# custom/hooks/ and forget to wire it, and this case says so.
_INSTALLED = Path(__file__).resolve().parents[1] / 'settings.json'
_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / 'src/modules/bmm/_module-installer/assets/hooks.json'
)
SETTINGS = _INSTALLED if _INSTALLED.exists() else _TEMPLATE


def _load():
    spec = importlib.util.spec_from_file_location('mtop', HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = _load()
FAILURES: list[str] = []

MAIN = {
    'session_id': 's1',
    'transcript_path': '/Users/x/.claude/projects/p/s1.jsonl',
    'cwd': '/Users/x/code/amazon-removal-assistant',
    'hook_event_name': 'UserPromptSubmit',
    'prompt': 'how is the parcel draft looking?',
}


def check(name: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


def run(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30
    )


def content() -> None:
    text = hook.REMINDER
    # The three halves of the rule, each of which the owner asked for by name.
    check('names background agents', 'run_in_background: true' in text, True)
    check('names SendMessage for mid-task information', 'SendMessage' in text, True)
    check('says not to wait for the agent', 'Do not wait for the agent to finish' in text, True)
    # The carve-out that stops it being delegation theatre.
    check('keeps quick work in the main thread', 'a quick answer stays in this thread' in text, True)
    check('says it is not a quota', 'not a quota' in text, True)
    # SendMessage is a deferred tool in this harness; a reminder naming an unloadable tool
    # would be followed straight into an InputValidationError.
    check('says how to load SendMessage', 'ToolSearch' in text, True)
    check('points at the CLAUDE.md section', 'The main conversation stays open' in text, True)
    # One paragraph, and short: it is paid for on every turn of every session.
    check('one paragraph', '\n' in text, False)
    check('stays short', len(text) < 1000, True)
    # It must never read as a count-based gate.
    for word in ('tool calls', 'word count', 'blocked', 'denied'):
        check(f'no count or gate language: {word}', word in text.lower(), False)


def silence_inside_a_subagent() -> None:
    check('main thread speaks', hook.reminder_for(MAIN), hook.REMINDER)
    check('agent_id silences', hook.reminder_for({**MAIN, 'agent_id': 'a1b2'}), None)
    check('agent_type silences', hook.reminder_for({**MAIN, 'agent_type': 'general-purpose'}), None)
    check(
        'subagent transcript silences',
        hook.reminder_for(
            {**MAIN, 'transcript_path': '/Users/x/.claude/projects/p/s1/subagents/agent-9.jsonl'}
        ),
        None,
    )
    # Empty values are the absence of a signal, not a subagent.
    check('empty agent_id is still main', hook.reminder_for({**MAIN, 'agent_id': ''}), hook.REMINDER)
    check('null agent_type is still main', hook.reminder_for({**MAIN, 'agent_type': None}), hook.REMINDER)
    # A prompt that merely TALKS about subagents is the owner speaking, not a subagent.
    check(
        'a prompt about subagents is still main',
        hook.reminder_for({**MAIN, 'prompt': 'use subagents, agent_id and all'}),
        hook.REMINDER,
    )
    check('non-object payload is silent', hook.reminder_for(['not', 'a', 'dict']), None)
    check('minimal payload speaks', hook.reminder_for({}), hook.REMINDER)


def end_to_end() -> None:
    done = run(json.dumps(MAIN))
    check('exit', done.returncode, 0)
    whole = json.loads(done.stdout)
    out = whole['hookSpecificOutput']
    check('event name', out['hookEventName'], 'UserPromptSubmit')
    check('carries the reminder', out['additionalContext'], hook.REMINDER)
    # Never blocks: no decision field, no continue:false, nothing on stderr.
    check('no block decision', 'decision' in whole, False)
    check('no continue:false', whole.get('continue', True), True)
    check('no permissionDecision', 'permissionDecision' in out, False)
    check('quiet stderr', done.stderr.strip(), '')

    sub = run(json.dumps({**MAIN, 'agent_id': 'x'}))
    check('subagent exit', sub.returncode, 0)
    check('subagent stdout empty', sub.stdout.strip(), '')

    for label, stdin in [('malformed', 'not json'), ('empty', ''), ('array', '[1,2]')]:
        bad = run(stdin)
        check(f'{label} exit', bad.returncode, 0)
        check(f'{label} stdout', bad.stdout.strip(), '')


def wiring() -> None:
    """Wired once, on UserPromptSubmit, in its own group appended LAST, fail-open."""
    settings = json.loads(SETTINGS.read_text())
    groups = settings['hooks']['UserPromptSubmit']
    commands = [h['command'] for g in groups for h in g['hooks']]
    ours = [c for c in commands if 'main-thread-open-pointer.py' in c]
    check('wired exactly once', len(ours), 1)
    check(
        'wired in the last group',
        any('main-thread-open-pointer.py' in h['command'] for h in groups[-1]['hooks']),
        True,
    )
    check('alone in its group', len(groups[-1]['hooks']), 1)
    if ours:
        cmd = ours[0]
        # Fail-open: a missing or crashing script must never cost the prompt.
        check('fail-open on a missing script', '[ -f "$S" ] || exit 0' in cmd, True)
        check('fail-open on a crash', '|| true; exit 0' in cmd, True)
        # RESOLVES A CHECKOUT FROM ANYWHERE, and the PROPERTY is what is asserted
        # rather than one spelling of it. This used to demand the literal string
        # `/.claude/worktrees/`, which pinned the old idiom: strip $PWD back to the
        # main checkout. The fork standardised on walking UP from $PWD instead
        # (docs/hooks-registry.md), which finds the worktree's own copy first and falls
        # through to the main checkout — and reaches a hook that has not been merged
        # yet. Neither $PWD nor $CLAUDE_PROJECT_DIR identifies the checkout on its
        # own: the docs say CLAUDE_PROJECT_DIR stays where the SESSION started, so it
        # is the main checkout for a worktree entered mid-session and the worktree
        # for a session spawned into one. Hence walk, then fall back.
        check('walks up from $PWD to find a checkout', 'while [ -n "$D" ]' in cmd, True)
        check('falls back to $CLAUDE_PROJECT_DIR', 'CLAUDE_PROJECT_DIR' in cmd, True)
        check('runs the script rather than inlining the logic',
              '/.claude/hooks/$N' in cmd and 'python3 "$S"' in cmd, True)
    for event in ('PreToolUse', 'Stop', 'SessionStart'):
        wired = json.dumps(settings['hooks'].get(event, []))
        check(f'not wired on {event}', 'main-thread-open-pointer' in wired, False)
    # It must never be able to block, whatever the payload.
    source = HOOK.read_text()
    code = re.sub(r'""".*?"""', '', source, count=1, flags=re.S)
    check('never emits a block', '"block"' in code or "'block'" in code, False)
    check('never exits 2', 'return 2' in code or 'exit(2)' in code, False)


def main() -> int:
    content()
    silence_inside_a_subagent()
    end_to_end()
    wiring()
    if FAILURES:
        print(f'{len(FAILURES)} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print('all main-thread-open-pointer cases pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
