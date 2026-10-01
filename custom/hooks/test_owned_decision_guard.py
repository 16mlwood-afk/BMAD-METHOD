#!/usr/bin/env python3
"""Golden cases for owned-decision-guard.py.

THE SILENCE CASES ARE THE IMPORTANT ONES. This hook blocks a reply from finishing, which is
the most intrusive thing a guard here can do. Every false positive is a session stopped
mid-delivery for no reason, and two of those would be enough for somebody to unwire it. So
the suite is weighted towards proving it stays quiet: an ordinary explanation of what is
gitignored must pass, and a genuine owner question must pass.

Run: python3 .claude/hooks/test_owned_decision_guard.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / 'owned-decision-guard.py'


def _load():
    spec = importlib.util.spec_from_file_location('owned_guard', GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load()
FAILURES: list[str] = []


def check(name: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


# ------------------------------------------------------------------ must FIRE

FIRES = [
    # The reply that produced the rule, near-verbatim.
    "The full ranking goes to output/ - rebuilt each run, not committed - because a run "
    "against different stock is a different answer. If you'd rather every run be "
    "permanently archived, say so and I'll change where it lands.",
    # Same deferral, shorter.
    "I put it in output/ and gitignored it. Let me know if you'd prefer it tracked.",
    # Dated-vs-stable, the other half of the same doctrine.
    'I used a stable path and overwrite it. Would you prefer a dated file each run?',
    # Delivery mechanics, the other settled class.
    'Both branches carry the fix. Tell me which branch you want me to merge it from.',
    'Do you want me to open a PR, or would you rather I push straight through?',
    'Happy to change it if you want the snapshot tracked instead.',
]

# ------------------------------------------------------------- must STAY SILENT

SILENT = [
    # Explaining placement WITHOUT offering it back. This is the correct shape and the
    # single most important thing not to block.
    'The full ranking goes to output/, rebuilt each run and gitignored, because a rerun '
    'against different stock answers a different question. The version worth keeping is '
    'copied into a dated document, which I did today.',
    'It is tracked and committed in the same change that regenerated it.',
    'That file is gitignored — the tool rebuilds it and a dry run costs nothing.',
    # A REAL owner question, with no settled-class term anywhere near it. Must reach him.
    'Two prices are missing before the forecast can give a per-machine figure. Let me know '
    'which of the two orders you want me to use.',
    "If you'd rather leave both boxes parked, nothing else waits on them.",
    # An offer about something that is genuinely his: a commercial commitment.
    "Leipzig can build the carton but has not quoted. Do you want me to ask them for a price?",
    # Delivery mechanics REPORTED rather than offered.
    'Merged and the branch is deleted. Nothing else is outstanding.',
    # Discussing tracking in the abstract, no offer.
    'A tracked generated file that nobody commits is the worst of both worlds — it dirties '
    'the tree on every run and blocks a fast-forward pull for every session.',
    '',
]


def detection_cases() -> None:
    for text in FIRES:
        check(f'FIRES: {text[:52]!r}', guard.offending(text) is not None, True)
    for text in SILENT:
        check(f'SILENT: {text[:52]!r}', guard.offending(text) is None, True)


# ------------------------------------------------------------------ end to end

def _run(payload: dict, env: dict | None = None) -> tuple[int, str]:
    import os

    done = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
        timeout=30,
    )
    return done.returncode, done.stdout.strip()


def end_to_end_cases() -> None:
    offending = {'last_assistant_message': FIRES[0]}
    code, out = _run(offending)
    check('blocks: exit', code, 0)
    payload = json.loads(out) if out else {}
    check('blocks: decision', payload.get('decision'), 'block')
    check('blocks: names the doctrine', 'Which generated files are tracked' in
          payload.get('reason', ''), True)
    check('blocks: names the marker', payload.get('reason', '').startswith('OWNED-DECISION'),
          True)
    check('blocks: offers the real escape', 'OWNER GATE' in payload.get('reason', ''), True)

    # A clean reply must finish.
    code, out = _run({'last_assistant_message': SILENT[0]})
    check('clean reply: exit', code, 0)
    check('clean reply: stdout', out, '')

    # Never block twice on one turn.
    code, out = _run({**offending, 'stop_hook_active': True})
    check('re-entry: stdout', out, '')

    # The override exists for a real owner question, and it works.
    code, out = _run(offending, env={'OWNED_DECISION_OVERRIDE': '1'})
    check('override: stdout', out, '')

    # No inline reply text means it is grading the wrong turn — stay silent, never guess.
    code, out = _run({'transcript_path': '/nonexistent/path.jsonl'})
    check('no inline text: stdout', out, '')

    # Malformed input must never wedge a session.
    done = subprocess.run(
        [sys.executable, str(GUARD)], input='not json', capture_output=True, text=True
    )
    check('malformed stdin: exit', done.returncode, 0)
    check('malformed stdin: stdout', done.stdout.strip(), '')


def main() -> int:
    detection_cases()
    end_to_end_cases()
    if FAILURES:
        print(f'{len(FAILURES)} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print('all owned-decision-guard cases pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
