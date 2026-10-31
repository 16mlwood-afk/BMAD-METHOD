#!/usr/bin/env python3
"""Golden cases for branch-switch-removal-guard.py.

MOST OF THESE ASSERT SILENCE, and that is the point. The guard's whole value rests on
firing rarely enough to be believed: the obvious version of this rule fires on 38 of
40 branches here, which is the indiscriminate gate the project's doctrine forbids. A
test suite that only proved it CAN fire would pass while the guard was useless.

Run: python3 .claude/hooks/test_branch_switch_removal_guard.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / 'branch-switch-removal-guard.py'

sys.path.insert(0, str(GUARD.parent))
_mod = __import__('branch-switch-removal-guard'.replace('-', '_')) if False else None


def _load():
    """Import the guard by path, since its filename is not an identifier."""
    import importlib.util

    spec = importlib.util.spec_from_file_location('guard', GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load()

FAILURES: list[str] = []


def check(name: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


# ---------------------------------------------------------------- target extraction

def targets_cases() -> None:
    """Which commands name a ref to switch TO — the only ones worth diffing."""
    cases = [
        # (command, expected refs)
        ('git switch main', ['main']),
        ('git checkout origin/main', ['origin/main']),
        ('git reset --hard origin/main', ['origin/main']),
        ('git switch docs/spec-backlog-triage', ['docs/spec-backlog-triage']),
        # A NEW branch starts at HEAD, so nothing can leave the disk.
        ('git switch -c feat/new-thing', []),
        ('git checkout -b feat/new-thing', []),
        ('git checkout --detach', []),
        # A path restore is not a switch. This is the form that would otherwise make
        # the guard fire on `git checkout main -- some/file`, which removes nothing.
        ('git checkout main -- docs/box-size-policy.md', []),
        ('git checkout -- .', []),
        # Not a switch at all.
        ('git status --short', []),
        ('git log --oneline -3', []),
        ('git stash push -u -m wip', []),
        ('git worktree remove foo', []),
        ('npm run prep:carton-sweep', []),
        ('git commit -m "switch to a new approach"', []),
        # A soft reset keeps every file on disk.
        ('git reset --soft HEAD~1', []),
        ('git reset HEAD~1', []),
        # Chained: the ref must not swallow the separator.
        ('git switch main && npm test', ['main']),
        ('git fetch -q; git switch main', ['main']),
    ]
    for command, expected in cases:
        check(f'targets({command!r})', guard.targets(command), expected)


# ------------------------------------------------------------------- path filtering

def recognisable_cases() -> None:
    """Which paths a person would actually notice vanishing from their folder."""
    noticed = [
        'docs/box-size-policy.md',
        'docs/specs/outbound-carton-geometry.md',
        'data/outbound-cartons.json',
        'data/claims-ledger.jsonl',
        'CLAUDE.md',
    ]
    ignored = [
        # Real work, but not a surface the owner watches — and including it is what
        # turns a 2-name prompt into a 33-name one nobody reads.
        'src/pallet-forecast.ts',
        'src/pallet-forecast.test.ts',
        'scripts/carton-sweep.ts',
        'package.json',
        'package-lock.json',
        '.claude/hooks/stash-untracked-guard.py',
        # Near-misses that must not match on a loose prefix.
        'docsite/index.html',
        'database/schema.sql',
        'CLAUDE.md.bak',
        'output/CLAUDE.md',
    ]
    for path in noticed:
        check(f'recognisable({path})', bool(guard.RECOGNISABLE.match(path)), True)
    for path in ignored:
        check(f'not recognisable({path})', bool(guard.RECOGNISABLE.match(path)), False)


# ------------------------------------------------------------------ the prompt text

def reason_cases() -> None:
    """The prompt has to answer his actual question: is this a deletion?"""
    text = guard.reason_for(['docs/box-size-policy.md'])
    check('reason names the file', 'docs/box-size-policy.md' in text, True)
    check('reason says NOT deleted', 'NOT being deleted' in text, True)
    check('reason says they come back', 'come back' in text, True)
    check('reason counts them', 'TAKES 1 RECENTLY-ADDED FILE' in text, True)

    many = [f'docs/spec-{n}.md' for n in range(12)]
    text = guard.reason_for(many)
    check('long list is truncated', text.count('\n  - '), guard.MAX_NAMED)
    check('truncation is declared', '...and 4 more' in text, True)
    check('count is the full count', 'TAKES 12 RECENTLY-ADDED FILE' in text, True)


# -------------------------------------------------------------- end-to-end, no fire

def _run(payload: dict) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return done.returncode, done.stdout.strip()


def silence_cases() -> None:
    """A guard that cries wolf gets switched off. These must all pass in silence."""
    quiet = [
        {'tool_name': 'Bash', 'tool_input': {'command': 'git status --short'}},
        {'tool_name': 'Bash', 'tool_input': {'command': 'npm test'}},
        {'tool_name': 'Bash', 'tool_input': {'command': 'git switch -c feat/x'}},
        # A ref that cannot resolve must ALLOW rather than guess.
        {'tool_name': 'Bash', 'tool_input': {'command': 'git switch no-such-branch-xyz'}},
        # Switching to where we already are removes nothing.
        {'tool_name': 'Bash', 'tool_input': {'command': 'git switch HEAD'}},
        # Not a Bash call at all.
        {'tool_name': 'Read', 'tool_input': {'file_path': '/tmp/x'}},
        {'tool_name': 'Edit', 'tool_input': {'command': 'git switch main'}},
        # Malformed input must never block a session.
        {},
        {'tool_name': 'Bash'},
        {'tool_name': 'Bash', 'tool_input': {}},
        {'tool_name': 'Bash', 'tool_input': {'command': ''}},
    ]
    for payload in quiet:
        code, out = _run(payload)
        label = payload.get('tool_input', {}).get('command', '<no command>')
        check(f'silent: {label!r} exit', code, 0)
        check(f'silent: {label!r} stdout', out, '')


def malformed_stdin_case() -> None:
    """Not JSON at all — allow, never crash the tool call."""
    done = subprocess.run(
        [sys.executable, str(GUARD)], input='not json', capture_output=True, text=True
    )
    check('malformed stdin exit', done.returncode, 0)
    check('malformed stdin stdout', done.stdout.strip(), '')


def main() -> int:
    targets_cases()
    recognisable_cases()
    reason_cases()
    silence_cases()
    malformed_stdin_case()

    if FAILURES:
        print(f'{len(FAILURES)} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print('all branch-switch-removal-guard cases pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
