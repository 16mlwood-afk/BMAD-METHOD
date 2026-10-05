#!/usr/bin/env python3
"""Every hook wrapper runs its script from a TRUSTED root — asserted over the whole set.

Run: python3 custom/hooks/test_hook_wrapper_resolution.py     (in the fork)
     python3 .claude/hooks/test_hook_wrapper_resolution.py    (installed in a project)

WHAT THIS PINS. A hook in the template is an inline shell command that finds a script
under `.claude/hooks/` and runs it. Until 2026-10-05 thirteen of them chose that script
from the working directory — eleven by walking UP from $PWD to the first
`.claude/hooks/<name>` they met, two by cutting $PWD at `/.claude/worktrees/`. Either way a
file at <somewhere under the cwd>/.claude/hooks/<name> ran in place of the real hook, which
switches a guard off or lets it approve anything.

THE RULE, the same text in every wrapper apart from the script's name:
  * the trusted root is $CLAUDE_PROJECT_DIR when the harness sets it;
  * the copy in the git toplevel of $PWD is preferred ONLY when that toplevel is the
    project or one of its own worktrees — same git common dir AND listed by
    `git worktree list` — so a session in a worktree runs the hook it has checked out;
  * with CLAUDE_PROJECT_DIR unset, the git toplevel of $PWD, never an ancestor found by
    walking up.

IT IS ASSERTED OVER THE SET, NOT A LIST OF NAMES. A "wrapper" is every command in the
settings file that mentions `.claude/hooks/`. Add one that resolves its script any other
way and this fails, with nothing here to update first.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_INSTALLED = Path(__file__).resolve().parents[1] / 'settings.json'
_TEMPLATE = (
    Path(__file__).resolve().parents[2] / 'src/modules/bmm/_module-installer/assets/hooks.json'
)
SETTINGS = _INSTALLED if _INSTALLED.exists() else _TEMPLATE

# The one resolution every wrapper carries, after `N=<script name>; `.
RESOLVER = (
    'P="${CLAUDE_PROJECT_DIR:-}"; T=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null); S=""; '
    'if [ -n "$P" ]; then S="$P/.claude/hooks/$N"; '
    'if [ -n "$T" ] && [ "$T" != "$P" ] && [ -f "$T/.claude/hooks/$N" ]; then '
    'A=$(git -C "$T" rev-parse --path-format=absolute --git-common-dir 2>/dev/null); '
    'B=$(git -C "$P" rev-parse --path-format=absolute --git-common-dir 2>/dev/null); '
    'if [ -n "$A" ] && [ "$A" = "$B" ] && git -C "$P" worktree list --porcelain 2>/dev/null '
    '| grep -qxF "worktree $T"; then S="$T/.claude/hooks/$N"; fi; fi; '
    'elif [ -n "$T" ]; then S="$T/.claude/hooks/$N"; fi; '
)
SHAPE = re.compile(r'^N=([A-Za-z0-9_.-]+\.(?:py|sh)); ' + re.escape(RESOLVER))

FAILURES: list[str] = []
RAN = 0


def check(name: str, actual, expected) -> None:
    global RAN
    RAN += 1
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


def wrappers() -> list[tuple[str, str, str]]:
    """(event, label, command) for every command that reaches into .claude/hooks/."""
    settings = json.loads(SETTINGS.read_text())
    found = []
    for event, groups in settings.get('hooks', {}).items():
        for group in groups:
            for hook in group.get('hooks', []):
                command = hook.get('command', '')
                if '.claude/hooks/' in command:
                    found.append((event, group.get('name') or group.get('matcher') or '?', command))
    return found


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
    )


def plant(directory: Path, name: str, label: str) -> None:
    """A stand-in hook script that records WHICH copy ran, and does nothing else."""
    hooks = directory / '.claude' / 'hooks'
    hooks.mkdir(parents=True, exist_ok=True)
    if name.endswith('.sh'):
        body = f'#!/bin/sh\ncat >/dev/null 2>&1\necho {label} >> "$RAN_LOG"\n'
    else:
        body = f"import os\nopen(os.environ['RAN_LOG'], 'a').write('{label}\\n')\n"
    (hooks / name).write_text(body)


class World:
    def __init__(self, base: Path, names: set[str]) -> None:
        self.base = base
        self.proj = base / 'proj'
        self.wt = self.proj / '.claude' / 'worktrees' / 'wt'
        self.bare_wt = self.proj / '.claude' / 'worktrees' / 'no-copy'
        self.sub = self.proj / 'sub'
        self.nested = self.proj / 'nested-repo'
        self.forged = self.proj / 'forged'
        self.log = base / 'ran.log'
        self.proj.mkdir(parents=True)
        git(self.proj, 'init', '-q')
        (self.proj / 'README').write_text('x\n')
        git(self.proj, 'add', 'README')
        git(self.proj, 'commit', '-q', '-m', 'init')
        git(self.proj, 'worktree', 'add', '-q', str(self.wt), '-b', 'wt')
        git(self.proj, 'worktree', 'add', '-q', str(self.bare_wt), '-b', 'no-copy')
        for directory in (
            self.sub / 'deeper',
            self.wt / 'sub' / 'deeper',
            self.nested / 'src',
            self.forged / 'src',
            self.bare_wt / 'src',
        ):
            directory.mkdir(parents=True, exist_ok=True)
        git(self.nested, 'init', '-q')
        # A directory dressed up as a checkout of the project: a .git FILE aimed at the
        # project's own .git makes git report the SAME common dir for it.
        (self.forged / '.git').write_text('gitdir: ../.git\n')
        for name in names:
            plant(self.proj, name, 'project')
            plant(self.wt, name, 'worktree')
            plant(self.sub, name, 'PLANTED')
            plant(self.wt / 'sub', name, 'PLANTED')
            plant(self.nested, name, 'PLANTED')
            plant(self.forged, name, 'PLANTED')
            plant(base, name, 'PLANTED')  # an ancestor of the project itself

    def run(self, command: str, cwd: Path, project_dir: Path | None) -> str:
        """Which copies ran, as one string — '' when none did."""
        if self.log.exists():
            self.log.unlink()
        env = {
            'PATH': os.environ.get('PATH', ''),
            'HOME': str(self.base),
            'PWD': str(cwd),
            'RAN_LOG': str(self.log),
        }
        if project_dir is not None:
            env['CLAUDE_PROJECT_DIR'] = str(project_dir)
        subprocess.run(
            ['bash', '-c', command],
            input='{}',
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(cwd),
            env=env,
        )
        return ','.join(self.log.read_text().split()) if self.log.exists() else ''


def main() -> int:
    for key in [k for k in os.environ if k.startswith('GIT_')]:
        os.environ.pop(key)  # a pre-commit hook exports these; they would redirect `git init`
    found = wrappers()
    check(f'{SETTINGS.name} has hook wrappers to check', len(found) > 0, True)

    names: set[str] = set()
    shaped = []
    for event, label, command in found:
        match = SHAPE.match(command)
        check(f'{event} · {label} · resolves its script by the shared rule', bool(match), True)
        check(f'{event} · {label} · does not walk up from $PWD', 'D="${D%/*}"' in command, False)
        check(f'{event} · {label} · does not derive a path by trimming $PWD', '${PWD%' in command, False)
        # Whatever the text looks like, the behaviour below is what decides.
        name = match.group(1) if match else None
        if name is None:
            guess = re.search(r'([A-Za-z0-9_.-]+\.(?:py|sh))', command)
            name = guess.group(1) if guess else None
        if name:
            names.add(name)
            shaped.append((event, label, command, name))

    base = Path(os.path.realpath(tempfile.mkdtemp(prefix='hook-wrapper-resolution-')))
    try:
        world = World(base, names)
        for event, label, command, name in shaped:
            tag = f'{event} · {label} ({name})'
            for where, cwd in [
                ('a planted copy in an ancestor of the cwd', world.sub / 'deeper'),
                ('a planted copy in a nested git repository', world.nested / 'src'),
                ('a planted copy behind a forged .git file', world.forged / 'src'),
            ]:
                check(f'{tag} · (a) {where} does not run', world.run(command, cwd, world.proj), 'project')
            check(
                f'{tag} · (a) a planted copy inside a worktree does not run',
                world.run(command, world.wt / 'sub' / 'deeper', world.proj),
                'worktree',
            )
            check(f"{tag} · (b) a real worktree runs the worktree's own copy", world.run(command, world.wt, world.proj), 'worktree')
            check(
                f'{tag} · (b) a worktree with no copy falls back to the project',
                world.run(command, world.bare_wt / 'src', world.proj),
                'project',
            )
            check(
                f'{tag} · (b) a session started IN the worktree runs its copy',
                world.run(command, world.wt, world.wt),
                'worktree',
            )
            check(f"{tag} · (c) the project root runs the project's copy", world.run(command, world.proj, world.proj), 'project')
            check(
                f'{tag} · no CLAUDE_PROJECT_DIR: the git toplevel, never an ancestor',
                world.run(command, world.sub / 'deeper', None),
                'project',
            )
            check(
                f'{tag} · no CLAUDE_PROJECT_DIR, not in a repository: nothing runs',
                world.run(command, base, None),
                '',
            )
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if FAILURES:
        print(f'{len(FAILURES)} of {RAN} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print(f'all {RAN} hook-wrapper-resolution cases pass ({len(found)} wrappers in {SETTINGS.name})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
