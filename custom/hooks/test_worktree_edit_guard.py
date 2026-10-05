#!/usr/bin/env python3
"""Golden cases for worktree-edit-guard.py.

Run: python3 custom/hooks/test_worktree_edit_guard.py      (in the fork)
     python3 .claude/hooks/test_worktree_edit_guard.py     (installed in a project)

Every case runs the hook as a SUBPROCESS through the real stdin JSON contract, inside a
throwaway tree with its own HOME, its own project, its own worktree and a stand-in `ps`
that reports however many claude processes the case wants. Nothing here reads or writes
the real home directory.

MOST CASES ASSERT "NO DECISION". That is the guard's answer for everything it is not sure
about, and it is the direction the four defects of 2026-10-05 all failed in the other way:
an `allow` nobody intended, or a refusal that an exemption quietly cancelled.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / 'worktree-edit-guard.py'
HOOK_NAME = 'worktree-edit-guard.py'

# Where the wiring lives depends on where this file is: installed in a project it is
# <root>/.claude/settings.json; in the fork it is the distribution template.
_INSTALLED = Path(__file__).resolve().parents[1] / 'settings.json'
_TEMPLATE = (
    Path(__file__).resolve().parents[2] / 'src/modules/bmm/_module-installer/assets/hooks.json'
)
SETTINGS = _INSTALLED if _INSTALLED.exists() else _TEMPLATE

FAILURES: list[str] = []
RAN = 0
SKIPPED: list[str] = []


def check(name: str, actual, expected) -> None:
    global RAN
    RAN += 1
    if actual != expected:
        FAILURES.append(f'{name}\n    expected: {expected!r}\n    actual:   {actual!r}')


# --- the throwaway world -------------------------------------------------------------


class World:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.home = base / 'home'
        self.code = self.home / 'code'
        self.proj = self.code / 'proj'
        self.wt = self.proj / '.claude' / 'worktrees' / 'wt'
        self.other = self.code / 'other'
        self.plain = self.code / 'plain'  # a project that is not a git repository
        self.fork = self.home / 'bmad-method-v6'
        for directory in (
            self.wt / 'src',
            self.proj / 'src' / '.claude',
            self.proj / '.claude' / 'worktrees' / 'second' / 'src',
            self.proj / '_bmad-output',
            self.proj / '_bmad' / '.sprint-apply-1',
            self.proj / 'vendor' / '_bmad-output',
            self.proj / 'vendor' / '_bmad' / '.sprint-apply-1',
            self.proj / 'vendor' / 'Users' / 'x' / 'bmad-method-v6',
            self.other / 'src',
            self.other / '.claude',
            self.other / '.git' / 'hooks',
            self.plain / 'src',
            self.fork / 'custom',
            self.home / '.ssh' / 'x' / '.claude',
            self.home / '.claude',
        ):
            directory.mkdir(parents=True, exist_ok=True)
        (self.home / '.zshrc').write_text('# shell profile\n')
        subprocess.run(
            ['git', 'init', '-q', str(self.proj)], check=True, capture_output=True, env=self.env(1)
        )

        # Symlinks: each one says, in its name, where it starts and where it lands.
        os.symlink(self.home / '.ssh', self.other / 'to-ssh')
        os.symlink(self.home / '.zshrc', self.other / 'to-zshrc.txt')
        os.symlink(self.home / '.ssh' / 'not-yet-created', self.other / 'dangling-to-ssh')
        os.symlink(self.proj / 'src', self.other / 'to-proj-src')
        os.symlink(self.proj / 'src', self.wt / 'escape-to-main')
        os.symlink(self.proj / '.claude', self.proj / 'src' / 'to-dot-claude')
        os.symlink(self.other / 'src', self.proj / 'src' / 'to-other-src')
        for where in (self.proj / 'src', self.other):
            os.symlink(where / 'loop-b', where / 'loop-a')
            os.symlink(where / 'loop-a', where / 'loop-b')

        for count in (0, 1, 3):
            bindir = base / f'bin-{count}'
            bindir.mkdir()
            fake = bindir / 'ps'
            lines = ''.join('echo "claude --session"\n' for _ in range(count))
            fake.write_text('#!/bin/sh\necho "/sbin/launchd"\necho "node claude-helper"\n' + lines)
            fake.chmod(0o755)
        broken = base / 'bin-broken'
        broken.mkdir()
        (broken / 'ps').write_text('#!/bin/sh\nexit 1\n')
        (broken / 'ps').chmod(0o755)

    def env(self, count, **extra: str) -> dict:
        env = {
            'PATH': f'{self.base}/bin-{count}{os.pathsep}{os.environ.get("PATH", "")}',
            'HOME': str(self.home),
        }
        env.update(extra)
        return env

    def run(self, path, cwd: Path, count=1, stdin: str | None = None, **extra: str):
        """-> (kind, reason, raw stdout). kind is none | allow | deny | INVALID."""
        if stdin is None:
            stdin = json.dumps(
                {
                    'session_id': 's1',
                    'hook_event_name': 'PreToolUse',
                    'tool_name': 'Edit',
                    'cwd': str(cwd),
                    'tool_input': {'file_path': path, 'old_string': 'a', 'new_string': 'b'},
                }
            )
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cwd),
            env=self.env(count, PWD=str(cwd), **extra),
        )
        out = result.stdout
        if result.returncode != 0:
            return (f'EXIT {result.returncode}', result.stderr[-300:], out)
        if not out.strip():
            return ('none', '', out)
        try:
            body = json.loads(out)['hookSpecificOutput']
            assert body['hookEventName'] == 'PreToolUse'
            return (body['permissionDecision'], body['permissionDecisionReason'], out)
        except Exception:
            return ('INVALID', out[:300], out)

    def kind(self, path, cwd: Path, count=1, **extra: str) -> str:
        return self.run(path, cwd, count, **extra)[0]


# --- rule 1 and 2: inside a worktree -------------------------------------------------


def in_a_worktree(w: World) -> None:
    cwd = w.wt / 'src'
    p, wt = str(w.proj), str(w.wt)

    # No decision: the worktree itself and the shared directories.
    for name, path in [
        ('worktree file, absolute', f'{wt}/src/a.ts'),
        ('worktree file, relative', 'a.ts'),
        ('worktree file, not created yet', f'{wt}/new/dir/a.ts'),
        ('worktree file, dressed up', f'{wt}/src/../src/./a.ts'),
        ('P/_bmad-output', f'{p}/_bmad-output/story.md'),
        ('P/.claude', f'{p}/.claude/settings.json'),
        ('P/_bmad/.sprint-apply-*', f'{p}/_bmad/.sprint-apply-1/x.yaml'),
        ('P/_bmad/.sprint-apply-* as a file', f'{p}/_bmad/.sprint-apply-9.lock'),
        ('the fork checkout', f'{w.fork}/custom/x.md'),
        ('another worktree of P (it is under P/.claude — unchanged)', f'{p}/.claude/worktrees/second/src/a.ts'),
        ('symlink in P that lands in P/.claude', f'{p}/src/to-dot-claude/x.json'),
    ]:
        check(f'worktree · no decision · {name}', w.kind(path, cwd), 'none')

    # DENY: inside P, outside the worktree.
    kind, reason, _ = w.run(f'{p}/src/a.ts', cwd)
    check('worktree · main-checkout file is refused', kind, 'deny')
    check(
        'worktree · the refusal reason is the existing text',
        reason,
        f'BLOCKED: target {p}/src/a.ts is inside THIS project ({p}) but outside the active '
        f'worktree {wt} — editing the main checkout (or another worktree) from here is the '
        'cross-session collision the guard prevents. Use a relative path inside the worktree.',
    )
    for name, path in [
        ('project root file', f'{p}/package.json'),
        ('_bmad that is not a sprint-apply path', f'{p}/_bmad/bmm/config.yaml'),
        ('double slash at the front', f'/{p}/src/a.ts'),
        ('double slash in the middle', f'{p}/src//a.ts'),
        ('dot segment', f'{p}/./src/a.ts'),
        ('dot-dot out of the worktree', f'{wt}/../../../src/a.ts'),
        ('dot-dot through another repo', f'{w.other}/../proj/src/a.ts'),
        ('relative path that climbs out of the worktree', '../../../../src/a.ts'),
        ('symlink in the worktree that lands in the main checkout', f'{wt}/escape-to-main/a.ts'),
        ('symlink in another repo that lands in the main checkout', f'{w.other}/to-proj-src/a.ts'),
        # defect (a): an exemption name that is NOT at the place it is meant for.
        ('(a) .claude nested inside P/src', f'{p}/src/.claude/y.json'),
        ('(a) _bmad-output nested inside P/vendor', f'{p}/vendor/_bmad-output/z.md'),
        ('(a) _bmad/.sprint-apply nested inside P/vendor', f'{p}/vendor/_bmad/.sprint-apply-1/x'),
        ('(a) a bmad-method-v6 directory inside P', f'{p}/vendor/Users/x/bmad-method-v6/f.md'),
    ]:
        check(f'worktree · DENY · {name}', w.kind(path, cwd), 'deny')


# --- rule 3 and 4: outside the project -----------------------------------------------

SENSITIVE = [
    '.env',
    '.ENV',
    '.env.local',
    '.envrc',
    '.secrets',
    '.secrets.json',
    '.git/config',
    '.GIT/hooks/x',
    '.git',
    '.ssh/config',
    '.npmrc',
    '.netrc',
    '.pypirc',
    '.aws/credentials',
    '.gnupg/pubring.kbx',
    '.docker/config.json',
    'certs/server.pem',
    'certs/SERVER.KEY',
    'keys/id_rsa',
    'keys/id_rsa.pub',
    'keys/id_ed25519',
    'config/credentials',
    'config/credentials.json',
    'src/.env.production',
]
NOT_SENSITIVE = [
    'src/a.ts',
    'src/environment.ts',
    'src/keys.ts',
    'src/monkey.ts',
    '.gitignore',
    '.github/workflows/ci.yml',
    '.envoy.yaml',
    'docs/credentials-howto.md',
    'docker/config.json',
    'README.md',
]


def outside_the_project(w: World) -> None:
    for label, cwd in (('worktree', w.wt / 'src'), ('main checkout', w.proj)):
        for rel in NOT_SENSITIVE:
            check(f'{label} · cross-repo allow · {rel}', w.kind(f'{w.other}/{rel}', cwd), 'allow')
        for rel in SENSITIVE:
            check(f'{label} · sensitive, no decision · {rel}', w.kind(f'{w.other}/{rel}', cwd), 'none')
        for name, path in [
            ('~/code/../.zshrc', f'{w.code}/../.zshrc'),
            ('~/.zshrc', f'{w.home}/.zshrc'),
            ('~/.ssh', f'{w.home}/.ssh/config'),
            ('~/.claude (machine-wide settings)', f'{w.home}/.claude/settings.json'),
            ('/etc/hosts', '/etc/hosts'),
            ('~/code itself is not a repo file... sibling of code', f'{w.home}/codex/a.ts'),
            ('(a) ~/.ssh/x/.claude/y', f'{w.home}/.ssh/x/.claude/y'),
            ('(a) /etc/_bmad-output/z', '/etc/_bmad-output/z'),
            ("another repo's .claude/settings.json (unchanged: prompt)", f'{w.other}/.claude/settings.json'),
            ("another repo's _bmad-output (unchanged: prompt)", f'{w.other}/_bmad-output/x.md'),
            ('(c) symlinked directory under ~/code that lands in ~/.ssh', f'{w.other}/to-ssh/config'),
            ('(c) symlinked file under ~/code that lands on ~/.zshrc', f'{w.other}/to-zshrc.txt'),
            ('(c) dangling symlink under ~/code that points into ~/.ssh', f'{w.other}/dangling-to-ssh'),
            ('(b) symlink loop under ~/code', f'{w.other}/loop-a/x.ts'),
            ('(b) NUL byte in a path under ~/code', f'{w.other}/src/a\x00.ts'),
        ]:
            check(f'{label} · no decision · {name}', w.kind(path, cwd), 'none')

    other = str(w.other)
    kind, reason, _ = w.run(f'{other}/src/a.ts', w.wt / 'src')
    check(
        'worktree · cross-repo reason is the existing text',
        reason,
        f'Cross-repo edit: {other}/src/a.ts is outside this session project (worktree of '
        f'{w.proj}). A worktree of THIS project cannot isolate a different repo, so the '
        'worktree rule does not apply — allowed (the sanctioned cross-repo path). Ensure no '
        'parallel session is editing that repo.',
    )
    kind, reason, _ = w.run(f'{other}/src/a.ts', w.proj)
    check(
        'main checkout · cross-repo reason is the existing text',
        reason,
        f'Cross-repo edit: {other}/src/a.ts is outside this session project {w.proj}. A '
        'worktree of THIS project cannot isolate a different repo, so the worktree rule does '
        'not apply here — allowed (the sanctioned cross-repo path). Ensure no parallel '
        'session is editing that repo.',
    )
    # A symlink inside P that lands in another repo is a cross-repo edit, judged where it lands.
    check(
        'symlink in P that lands in another repo under ~/code',
        w.kind(f'{w.proj}/src/to-other-src/a.ts', w.wt / 'src'),
        'allow',
    )
    # Many parallel sessions do not change the cross-repo answer, and neither does the override.
    check('main checkout · cross-repo, 3 sessions', w.kind(f'{other}/src/a.ts', w.proj, 3), 'allow')
    check(
        'main checkout · sensitive cross-repo stays a prompt even with the override set',
        w.kind(f'{other}/.env', w.proj, 3, BMAD_ALLOW_MAIN_EDIT='1'),
        'none',
    )
    # No HOME -> there is no ~/code to anchor an allow to.
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({'tool_input': {'file_path': f'{other}/src/a.ts'}}),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(w.proj),
        env={'PATH': w.env(1)['PATH']},
    )
    check('no HOME · never an allow', (result.returncode, result.stdout), (0, ''))


# --- rule 2: the main checkout -------------------------------------------------------


def in_the_main_checkout(w: World) -> None:
    p = str(w.proj)
    for cwd in (w.proj, w.proj / 'src'):
        check(f'main · alone, no decision · cwd={cwd.name}', w.kind(f'{p}/src/a.ts', cwd, 1), 'none')
        check(f'main · no claude process, no decision · cwd={cwd.name}', w.kind(f'{p}/src/a.ts', cwd, 0), 'none')
        check(f'main · 3 sessions, DENY · cwd={cwd.name}', w.kind(f'{p}/src/a.ts', cwd, 3), 'deny')

    kind, reason, _ = w.run(f'{p}/src/a.ts', w.proj, 3)
    check(
        'main · the refusal reason is the existing text',
        reason,
        'BLOCKED: 3 parallel claude sessions detected and you are NOT in a worktree. Set '
        'BMAD_ALLOW_MAIN_EDIT=1 for a LOGGED main-checkout maintenance edit, call '
        'EnterWorktree, or use the bash cross-repo route. See CLAUDE.md.',
    )
    for name, path in [
        ('relative path', 'src/a.ts'),
        ('double slash at the front', f'/{p}/src/a.ts'),
        ('triple slash at the front', f'//{p}/src/a.ts'),
        ('dot-dot through another repo', f'{w.other}/../proj/src/a.ts'),
        ('symlink in another repo that lands in P', f'{w.other}/to-proj-src/a.ts'),
        ('(a) .claude nested inside P/src', f'{p}/src/.claude/y.json'),
        ('(a) _bmad-output nested inside P/vendor', f'{p}/vendor/_bmad-output/z.md'),
        ('(a) a bmad-method-v6 directory inside P', f'{p}/vendor/Users/x/bmad-method-v6/f.md'),
        ('(b) symlink loop inside P', f'{p}/src/loop-a/x.ts'),
        ('(b) NUL byte in a path inside P', f'{p}/src/a\x00.ts'),
    ]:
        check(f'main · 3 sessions, DENY · {name}', w.kind(path, w.proj, 3), 'deny')
    for name, path in [
        ('P/.claude', f'{p}/.claude/settings.json'),
        ('P/_bmad-output', f'{p}/_bmad-output/story.md'),
        ('P/_bmad/.sprint-apply-*', f'{p}/_bmad/.sprint-apply-1/x.yaml'),
        ('a worktree of P, edited from the main checkout', f'{w.wt}/src/a.ts'),
        ('the fork checkout', f'{w.fork}/custom/x.md'),
    ]:
        check(f'main · 3 sessions, no decision · {name}', w.kind(path, w.proj, 3), 'none')
        check(
            f'main · the override does not turn an exemption into an allow · {name}',
            w.kind(path, w.proj, 3, BMAD_ALLOW_MAIN_EDIT='1'),
            'none',
        )

    # The override: allow, and a line in the log.
    log = w.proj / '.claude' / 'main-edit-overrides.log'
    kind, reason, _ = w.run(f'{p}/src/a.ts', w.proj, 3, BMAD_ALLOW_MAIN_EDIT='1')
    check('main · override allows', kind, 'allow')
    check(
        'main · override reason is the existing text',
        reason,
        'Main-checkout maintenance edit override (BMAD_ALLOW_MAIN_EDIT=1) — LOGGED to '
        f'.claude/main-edit-overrides.log. Confirm no parallel session is editing {p}/src/a.ts.',
    )
    logged = log.read_text().splitlines() if log.exists() else []
    check('main · override wrote exactly one log line', len(logged), 1)
    check(
        'main · the log line has the existing shape',
        logged[0].split(' ', 1)[1] if logged else '',
        f'main-edit-override FILE={p}/src/a.ts PWD={p}',
    )
    check('main · override only on the value 1', w.kind(f'{p}/src/a.ts', w.proj, 3, BMAD_ALLOW_MAIN_EDIT='true'), 'deny')
    w.run(f'{p}/src/new\nforged-line FILE=x', w.proj, 3, BMAD_ALLOW_MAIN_EDIT='1')
    check('main · a newline in the file name cannot add a log line', len(log.read_text().splitlines()), 2)

    # (b) An unresolvable path never gets the override's allow.
    check(
        '(b) main · override does NOT allow a path that would not resolve (alone)',
        w.kind(f'{p}/src/loop-a/x.ts', w.proj, 1, BMAD_ALLOW_MAIN_EDIT='1'),
        'none',
    )
    check(
        '(b) main · override does NOT allow a path that would not resolve (3 sessions)',
        w.kind(f'{p}/src/loop-a/x.ts', w.proj, 3, BMAD_ALLOW_MAIN_EDIT='1'),
        'deny',
    )
    kind, reason, _ = w.run(f'{p}/src/loop-a/x.ts', w.wt / 'src')
    check('(b) worktree · a path in P that would not resolve is refused', kind, 'deny')
    check('(b) worktree · and the reason says it could not be resolved', 'could not be resolved' in reason, True)
    check('(b) worktree · NUL byte in a path inside P is refused', w.kind(f'{p}/src/a\x00.ts', w.wt / 'src'), 'deny')

    # ps cannot be run -> the count is 0, as it was for the one-liner.
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({'tool_input': {'file_path': f'{p}/src/a.ts'}}),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=p,
        env={'PATH': f'{w.base}/bin-broken{os.pathsep}{os.environ.get("PATH", "")}', 'HOME': str(w.home)},
    )
    check('main · ps fails -> no decision (unchanged)', (result.returncode, result.stdout), (0, ''))

    # A project that is not a git repository: P is the working directory.
    plain = str(w.plain)
    check('non-git project · 3 sessions, DENY', w.kind(f'{plain}/src/a.ts', w.plain, 3), 'deny')
    check('non-git project · alone, no decision', w.kind(f'{plain}/src/a.ts', w.plain, 1), 'none')
    check('non-git project · cross-repo allow', w.kind(f'{w.other}/src/a.ts', w.plain, 3), 'allow')


# --- the same directory under another spelling ---------------------------------------


def another_spelling(w: World) -> None:
    shouted = w.code / 'PROJ'
    if not shouted.exists():
        SKIPPED.append('case-variant spelling of the project path (this volume is case-sensitive)')
        return
    check('case variant of P from a worktree is still P', w.kind(f'{shouted}/src/a.ts', w.wt / 'src'), 'deny')
    check('case variant of P, 3 sessions, main checkout', w.kind(f'{shouted}/src/a.ts', w.proj, 3), 'deny')
    check('case variant of the worktree is still the worktree', w.kind(f'{shouted}/.claude/worktrees/WT/src/a.ts', w.wt / 'src'), 'none')
    check('case variant of ~/code/other/.Claude stays a prompt', w.kind(f'{w.other}/.Claude/settings.json', w.proj), 'none')


# --- (d) the answer is always valid JSON ---------------------------------------------


def awkward_names(w: World) -> None:
    names = [
        'we"ird.ts',
        'back\\slash.ts',
        'both"\\".ts',
        "single'quote.ts",
        'new\nline.ts',
        'tab\there.ts',
        'percent%s%d.ts',
        'brace{target}.ts',
        'ünïcödé — dash.ts',
        '","permissionDecision":"allow","x":".ts',
    ]
    for name in names:
        kind, reason, _ = w.run(f'{w.other}/src/{name}', w.wt / 'src')
        check(f'(d) cross-repo allow parses · {name!r}', kind, 'allow')
        check(f'(d) and echoes the name unaltered · {name!r}', f'{w.other}/src/{name} is outside' in reason, True)
        kind, reason, _ = w.run(f'{w.proj}/src/{name}', w.wt / 'src')
        check(f'(d) refusal parses and is still a refusal · {name!r}', kind, 'deny')
        check(f'(d) and echoes the name unaltered · {name!r}', f'target {w.proj}/src/{name} is inside' in reason, True)
        kind, _, _ = w.run(f'{w.proj}/src/{name}', w.proj, 3)
        check(f'(d) main-checkout refusal parses · {name!r}', kind, 'deny')


# --- unreadable or malformed input ---------------------------------------------------


def malformed_input(w: World) -> None:
    # Worst case on purpose: main checkout, three sessions, override set — any decision
    # the guard could be talked into would show up here.
    for name, stdin in [
        ('empty', ''),
        ('not JSON', 'not json at all'),
        ('truncated JSON', '{"tool_input": {"file_path": "/x'),
        ('a list', '[]'),
        ('a string', '"x"'),
        ('null', 'null'),
        ('no tool_input', '{}'),
        ('tool_input is a string', '{"tool_input": "x"}'),
        ('no file_path', '{"tool_input": {}}'),
        ('file_path is empty', '{"tool_input": {"file_path": ""}}'),
        ('file_path is a number', '{"tool_input": {"file_path": 7}}'),
        ('file_path is a list', '{"tool_input": {"file_path": ["/etc/hosts"]}}'),
        ('file_path is null', '{"tool_input": {"file_path": null}}'),
    ]:
        for label, cwd in (('main', w.proj), ('worktree', w.wt / 'src')):
            kind, _, out = w.run(None, cwd, 3, stdin=stdin, BMAD_ALLOW_MAIN_EDIT='1')
            check(f'malformed input · silent, exit 0 · {name} · {label}', (kind, out), ('none', ''))
    # The environment fallback the one-liner had is kept, for valid input without a path.
    check(
        'no file_path in the JSON -> CLAUDE_TOOL_INPUT_FILE_PATH is used',
        w.run(None, w.proj, 3, stdin='{"tool_input": {}}', CLAUDE_TOOL_INPUT_FILE_PATH=f'{w.proj}/src/a.ts')[0],
        'deny',
    )
    check(
        'but never on input that did not parse',
        w.run(None, w.proj, 3, stdin='garbage', CLAUDE_TOOL_INPUT_FILE_PATH=f'{w.other}/src/a.ts')[0],
        'none',
    )


# --- the wiring ----------------------------------------------------------------------


def wiring(w: World) -> None:
    settings = json.loads(SETTINGS.read_text())
    groups = [
        group
        for group in settings['hooks'].get('PreToolUse', [])
        if HOOK_NAME in json.dumps(group)
    ]
    check(f'wired exactly once on PreToolUse in {SETTINGS.name}', len(groups), 1)
    if len(groups) != 1:
        return
    group = groups[0]
    check('wired on Edit|Write', group.get('matcher'), 'Edit|Write')
    command = group['hooks'][0]['command']
    # The decisions live in the script. If the wrapper could answer allow or deny by
    # itself, the one-liner would be growing back.
    check('the wrapper itself decides nothing', 'permissionDecision' in command, False)
    for event, entries in settings['hooks'].items():
        if event != 'PreToolUse':
            check(f'not wired on {event}', HOOK_NAME in json.dumps(entries), False)
    if SETTINGS == _TEMPLATE:
        check('the old inline guard is gone from the template', 'Cross-repo edit' in SETTINGS.read_text(), False)
        check('declared in bmadTrackedHookScripts', HOOK_NAME in settings.get('bmadTrackedHookScripts', []), True)

    # Run the wired command itself, the way the harness would.
    hooks_dir = w.proj / '.claude' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    installed = hooks_dir / HOOK_NAME

    def wired(path: str, cwd: Path, count: int) -> tuple[int, str]:
        result = subprocess.run(
            ['bash', '-c', command],
            input=json.dumps({'tool_input': {'file_path': path}}),
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cwd),
            env=w.env(count, PWD=str(cwd), CLAUDE_PROJECT_DIR=str(w.proj)),
        )
        return result.returncode, result.stdout

    def decision_of(out: str) -> str:
        if not out.strip():
            return 'none'
        try:
            return json.loads(out)['hookSpecificOutput'].get('permissionDecision', 'context-only')
        except Exception:
            return 'INVALID'

    code, out = wired(f'{w.proj}/src/a.ts', w.wt / 'src', 1)
    check('wired · script not delivered -> exit 0', code, 0)
    check('wired · script not delivered -> says so, decides nothing', decision_of(out), 'context-only')
    check('wired · script not delivered -> names the missing file', 'GUARD IS MISSING' in out, True)

    shutil.copy(HOOK, installed)
    for name, path, cwd, count, expected in [
        ('refuses a main-checkout edit from a worktree', f'{w.proj}/src/a.ts', w.wt / 'src', 1, 'deny'),
        ('is silent for an edit inside the worktree', f'{w.wt}/src/a.ts', w.wt / 'src', 1, 'none'),
        ('refuses in the main checkout with 3 sessions', f'{w.proj}/src/a.ts', w.proj, 3, 'deny'),
        ('is silent in the main checkout alone', f'{w.proj}/src/a.ts', w.proj, 1, 'none'),
        ('allows the cross-repo edit', f'{w.other}/src/a.ts', w.proj, 1, 'allow'),
        ('is silent for ~/.zshrc', f'{w.home}/.zshrc', w.proj, 1, 'none'),
    ]:
        code, out = wired(path, cwd, count)
        check(f'wired · {name}', (code, decision_of(out)), (0, expected))

    installed.write_text('raise SystemExit(3)\n')
    code, out = wired(f'{w.other}/src/a.ts', w.proj, 1)
    check('wired · a crashing script -> exit 0, decides nothing', (code, decision_of(out)), (0, 'context-only'))
    check('wired · a crashing script -> says the check did not run', 'ERRORED' in out, True)
    installed.unlink()


def main() -> int:
    for key in [k for k in os.environ if k.startswith('GIT_')]:
        os.environ.pop(key)  # a pre-commit hook exports these; they would redirect `git init`
    base = Path(os.path.realpath(tempfile.mkdtemp(prefix='worktree-edit-guard-')))
    try:
        world = World(base)
        in_a_worktree(world)
        outside_the_project(world)
        in_the_main_checkout(world)
        another_spelling(world)
        awkward_names(world)
        malformed_input(world)
        wiring(world)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    for skipped in SKIPPED:
        print(f'SKIPPED (not run, not passed): {skipped}')
    if FAILURES:
        print(f'{len(FAILURES)} of {RAN} FAILED\n')
        for failure in FAILURES:
            print(f'  {failure}\n')
        return 1
    print(f'all {RAN} worktree-edit-guard cases pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
