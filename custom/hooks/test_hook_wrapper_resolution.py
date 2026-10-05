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
  * the script is $CLAUDE_PROJECT_DIR/.claude/hooks/<name> when the harness sets that;
  * with CLAUDE_PROJECT_DIR unset, the git toplevel of $PWD, never an ancestor found by
    walking up;
  * NEVER a worktree's own copy chosen by the working directory. A worktree is the
    workspace the guard governs: a guard loaded from it can be rewritten by the very
    session it constrains. (For a few hours on 2026-10-05 a registered worktree's copy was
    preferred; a security review reversed that the same day.)

IT IS ASSERTED OVER THE SET, NOT A LIST OF NAMES. A "wrapper" is every command in the
settings file that mentions `.claude/hooks/`. Add one that resolves its script any other
way and this fails, with nothing here to update first.
"""

from __future__ import annotations

import importlib.util
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
    'P="${CLAUDE_PROJECT_DIR:-}"; [ -n "$P" ] || P=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null); '
    'S=""; [ -n "$P" ] && S="$P/.claude/hooks/$N"; '
)
SHAPE = re.compile(r'^N=([A-Za-z0-9_.-]+\.(?:py|sh)); ' + re.escape(RESOLVER))

# What every wrapper is fed on stdin. Some wrappers pre-filter their input in shell and exit
# before reaching their script; on a bare `{}` such a wrapper runs nothing, and a case that
# passes because nothing ran has not passed. This payload carries the tool name and the word
# those filters look for, so each wrapper actually reaches its script.
PAYLOAD = '{"tool_name":"Bash","tool_response":"UNKNOWN"}'

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
        # Looks like a worktree path to anything that reads $PWD as text; git has never
        # heard of it. `sub` carries a planted copy, so cutting $PWD at the marker lands on it.
        self.fake_wt = self.sub / '.claude' / 'worktrees' / 'fake'
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
            self.fake_wt,
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
            input=PAYLOAD,
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
        check(f'{event} · {label} · never asks which worktrees exist', 'worktree list' in command, False)
        check(f'{event} · {label} · does not derive a path by trimming $PWD', '${PWD%' in command, False)
        # Whatever the text looks like, the behaviour below is what decides.
        name = match.group(1) if match else None
        if name is None:
            guess = re.search(r'([A-Za-z0-9_.-]+\.(?:py|sh))', command)
            name = guess.group(1) if guess else None
        if name:
            names.add(name)
            shaped.append((event, label, command, name))

    # THE MISSING-GUARD DETECTOR READS THE SAME SET. hook-resolve-check.py reports a wired
    # script that is not on disk; it can only do that for a script whose name it can read
    # out of the command. The two are compared as sets so they cannot drift apart again
    # (on 2026-10-05 the detector could see 2 of the 13).
    detector_path = Path(__file__).resolve().parent / 'hook-resolve-check.py'
    spec = importlib.util.spec_from_file_location('hook_resolve_check', detector_path)
    detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(detector)
    read_names = getattr(detector, 'script_names', None) or (
        lambda command: detector.HOOK_REF.findall(command)  # the detector before 2026-10-05
    )
    cannot_read = getattr(detector, 'is_unreadable', None) or (lambda command: not read_names(command))
    seen = {name for _, _, command in found for name in read_names(command)}
    # The direction that matters: a script that is RUN and not READ could go missing in
    # silence, so it fails. The other direction is allowed for one reason only — a wrapper
    # that merely PRINTS a literal .claude/hooks/<name> (a restore hint in its missing-guard
    # notice) hands the detector a name no wrapper runs. Anything else it reads is a defect.
    check(
        f'the detector reads every script the wrappers run ({len(seen & names)} of {len(names)})',
        sorted(names - seen),
        [],
    )
    literal = {name for _, _, command in found for name in detector.HOOK_REF.findall(command)}
    check('anything more the detector reads is a literal path a wrapper prints', sorted(seen - names - literal), [])
    check(
        'and no wrapper is one the detector cannot read',
        [label for _, label, command in found if cannot_read(command)],
        [],
    )
    detector_line = (
        f'the missing-hook detector reads {len(seen & names)} of the {len(names)} scripts the wrappers run'
        f' and {len(seen)} names in all'
        + (f' (also named, never run: {", ".join(sorted(seen - names))})' if seen - names else '')
    )

    base = Path(os.path.realpath(tempfile.mkdtemp(prefix='hook-wrapper-resolution-')))
    try:
        world = World(base, names)
        for event, label, command, name in shaped:
            tag = f'{event} · {label} ({name})'
            for where, cwd in [
                ('a planted copy in an ancestor of the cwd', world.sub / 'deeper'),
                ('a planted copy in a nested git repository', world.nested / 'src'),
                ('a planted copy behind a forged .git file', world.forged / 'src'),
                ('a planted copy above a path that only LOOKS like a worktree', world.fake_wt),
            ]:
                check(f'{tag} · (a) {where} does not run', world.run(command, cwd, world.proj), 'project')
            check(
                f'{tag} · (a) a planted copy inside a worktree does not run',
                world.run(command, world.wt / 'sub' / 'deeper', world.proj),
                'project',
            )
            check(
                f"{tag} · (b) a registered worktree holding its OWN different copy: the PROJECT's copy runs",
                world.run(command, world.wt, world.proj),
                'project',
            )
            check(
                f'{tag} · (b) a worktree with no copy runs the project copy',
                world.run(command, world.bare_wt / 'src', world.proj),
                'project',
            )
            check(
                f'{tag} · CLAUDE_PROJECT_DIR is followed to the letter, even when it is a worktree',
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
                f'{tag} · no CLAUDE_PROJECT_DIR, in a worktree: its git toplevel, never the planted copy below it',
                world.run(command, world.wt / 'sub' / 'deeper', None),
                'worktree',
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
    print(f'all {RAN} hook-wrapper-resolution cases pass ({len(found)} wrappers in {SETTINGS.name}); {detector_line}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
