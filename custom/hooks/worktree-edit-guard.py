#!/usr/bin/env python3
"""
worktree-edit-guard — PreToolUse (Edit|Write): keep a session's edits inside its own worktree.

WHAT IT IS FOR. Several Claude sessions share one checkout of a project. Two of them
editing the same working tree overwrite each other silently, so each session works in its
own worktree under <project>/.claude/worktrees/<name>/ and this guard refuses an Edit or
Write that would land in the project's shared tree from the wrong place.

It replaces a 2,900-character shell one-liner that made the same decisions. The one-liner
was patched four times on 2026-10-05 (da84c7d7, d055b46e, a90c7b8d, 796bc01a) and each
patch left a neighbouring hole, because nobody could read it. This file is the same
decision table, written so it can be read and tested.

THE DECISIONS. "P" is the session's project: in a worktree, the checkout that owns it;
otherwise the git toplevel of the working directory. Every rule is decided on where the
target REALLY is — symlinks, `..`, `.` and stray slashes resolved first.

  1. The target is in one of the shared directories        -> no decision
       P/.claude/   P/_bmad-output/   P/_bmad/.sprint-apply-*   ~/bmad-method-v6/
  2. In a worktree, and the target is inside that worktree  -> no decision
  3. The target is inside P (and not covered by 1 or 2):
       in a worktree                                        -> DENY
       main checkout, BMAD_ALLOW_MAIN_EDIT=1                -> allow, and LOG it
       main checkout, more than one claude process running  -> DENY
       main checkout, otherwise                             -> no decision
  4. The target is outside P:
       under ~/code, not sensitive, not a tool-config path  -> allow (cross-repo edit)
       anything else                                        -> no decision

"No decision" means this guard prints nothing and the normal permission flow applies. It is
the answer for everything the guard is not sure about: an `allow` removes a permission
prompt, so it is only ever emitted for a path that resolved cleanly to a place it is meant
for.

WHAT CANNOT HAPPEN, each pinned by a golden case in test_worktree_edit_guard.py:

  * An exemption cannot reach outside its directory. Each one is anchored to P (or to the
    fork checkout) and tested on the resolved path. The one-liner matched `*/.claude/*`
    anywhere in the string, so P/src/.claude/x and P/vendor/_bmad-output/y skipped the
    refusal.
  * Resolution cannot fail open. If the path cannot be resolved (a symlink loop, a NUL
    byte) no `allow` is emitted, and a path that looks like it is inside P gets the refusal
    rule 3 would have given. The one-liner fell back to the raw string.
  * A symlink under ~/code that lands outside it is judged by where it lands.
  * The answer is built with json.dumps, so no file name can garble or alter it.
  * Unreadable or malformed hook input produces no output at all.

EXIT CODES. 0 always, except an internal error (an unexpected exception), which exits 1
with nothing on stdout so the wrapper in the hook wiring can say the check did not run.
A crash must never read as "checked and fine".

Golden cases: python3 custom/hooks/test_worktree_edit_guard.py
"""

from __future__ import annotations

import datetime
import fnmatch
import json
import os
import subprocess
import sys

WORKTREE_MARKER = '/.claude/worktrees/'

# Never auto-approved, wherever they are. Matched case-insensitively against EVERY path
# component, because the common filesystems here ignore case (.ENV and .GIT/ reach the same
# files) and because a directory called `.ssh` makes everything under it sensitive.
SENSITIVE_NAMES = (
    '.git',
    '.env',
    '.env.*',
    '.envrc',
    '.secrets*',
    '.ssh',
    '.npmrc',
    '.netrc',
    '.pypirc',
    '.aws',
    '.gnupg',
    '*.pem',
    '*.key',
    'id_rsa*',
    'id_ed25519*',
    'credentials',
    'credentials.*',
)
SENSITIVE_PAIRS = (('.docker', 'config.json'),)

DENY_OUTSIDE_WORKTREE = (
    'BLOCKED: target {target} is inside THIS project ({project}) but outside the active '
    'worktree {worktree} — editing the main checkout (or another worktree) from here is '
    'the cross-session collision the guard prevents. Use a relative path inside the worktree.'
)
DENY_UNRESOLVED_IN_WORKTREE = (
    'BLOCKED: target {target} could not be resolved to a real location ({error}) and it '
    'looks like it is inside THIS project ({project}). Refusing rather than guessing where '
    'it lands. Use a plain path inside the active worktree {worktree}.'
)
DENY_PARALLEL_SESSIONS = (
    'BLOCKED: {count} parallel claude sessions detected and you are NOT in a worktree. Set '
    'BMAD_ALLOW_MAIN_EDIT=1 for a LOGGED main-checkout maintenance edit, call EnterWorktree, '
    'or use the bash cross-repo route. See CLAUDE.md.'
)
ALLOW_MAIN_OVERRIDE = (
    'Main-checkout maintenance edit override (BMAD_ALLOW_MAIN_EDIT=1) — LOGGED to '
    '.claude/main-edit-overrides.log. Confirm no parallel session is editing {target}.'
)
ALLOW_CROSS_REPO_FROM_WORKTREE = (
    'Cross-repo edit: {target} is outside this session project (worktree of {project}). A '
    'worktree of THIS project cannot isolate a different repo, so the worktree rule does '
    'not apply — allowed (the sanctioned cross-repo path). Ensure no parallel session is '
    'editing that repo.'
)
ALLOW_CROSS_REPO_FROM_MAIN = (
    'Cross-repo edit: {target} is outside this session project {project}. A worktree of '
    'THIS project cannot isolate a different repo, so the worktree rule does not apply here '
    '— allowed (the sanctioned cross-repo path). Ensure no parallel session is editing '
    'that repo.'
)


# --- answering -----------------------------------------------------------------------


def decision(kind: str, reason: str) -> dict:
    return {
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': kind,
            'permissionDecisionReason': reason,
        }
    }


# --- paths ---------------------------------------------------------------------------


def collapse_leading_slashes(path: str) -> str:
    """POSIX keeps a leading `//` as its own root; here it is just `/`."""
    return '/' + path.lstrip('/') if path.startswith('//') else path


def lexical_path(raw: str, cwd: str) -> str:
    """The path as written, made absolute and tidied — no filesystem access."""
    joined = raw if os.path.isabs(raw) else os.path.join(cwd, raw)
    return collapse_leading_slashes(os.path.normpath(collapse_leading_slashes(joined)))


def resolve(raw: str, cwd: str) -> str:
    """Where the target really is. Raises rather than return something it did not resolve.

    realpath resolves every symlink on the part of the path that exists and treats the
    rest as plain names, which is what a not-yet-created file needs. It does not raise on a
    symlink loop — it hands back the path with the link still in it — so the result is
    checked: if any component is still a symlink, the path was not resolved.
    """
    if '\0' in raw:
        raise ValueError('NUL byte in path')
    joined = raw if os.path.isabs(raw) else os.path.join(cwd, raw)
    real = collapse_leading_slashes(os.path.realpath(collapse_leading_slashes(joined)))
    probe = real
    while True:
        if os.path.islink(probe):
            raise OSError('symlink that does not resolve')
        parent = os.path.dirname(probe)
        if parent == probe:
            return real
        probe = parent


def parts_below(path: str, root: str | None) -> list[str] | None:
    """The components of `path` below `root`, or None when it is not under `root`.

    The string test is the ordinary case. The second test catches the same directory
    reached under another spelling — /Users/x/Code/proj on a volume that ignores case —
    by asking the filesystem whether an ancestor of the path IS the root, rather than by
    guessing whether this volume folds case.
    """
    if not root:
        return None
    root = root.rstrip('/') or '/'
    if path == root:
        return []
    prefix = root if root.endswith('/') else root + '/'
    if path.startswith(prefix):
        return [part for part in path[len(prefix) :].split('/') if part]
    try:
        root_stat = os.stat(root)
    except OSError:
        return None
    probe = path
    while True:
        try:
            if os.path.samestat(os.stat(probe), root_stat):
                return [part for part in path[len(probe) :].split('/') if part]
        except OSError:
            pass
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent


def is_sensitive(path: str) -> bool:
    parts = [part for part in path.lower().split('/') if part]
    for part in parts:
        if any(fnmatch.fnmatchcase(part, pattern) for pattern in SENSITIVE_NAMES):
            return True
    for first, second in SENSITIVE_PAIRS:
        if any(a == first and b == second for a, b in zip(parts, parts[1:])):
            return True
    return False


def is_tool_config_path(path: str) -> bool:
    """A .claude/, _bmad-output/ or _bmad/.sprint-apply-* path in ANOTHER repository.

    The one-liner gave these no decision (its exemptions matched anywhere), so a
    cross-repo edit to another project's .claude/settings.json or its guards still met a
    permission prompt. That is kept: inside P these names are exemptions, outside P they
    only ever withhold the auto-approval.
    """
    parts = [part for part in path.lower().split('/') if part]
    if '.claude' in parts or '_bmad-output' in parts:
        return True
    return any(a == '_bmad' and b.startswith('.sprint-apply-') for a, b in zip(parts, parts[1:]))


# --- the session ---------------------------------------------------------------------


class Session:
    """Where this session is working: its project, and its worktree if it is in one."""

    def __init__(self, cwd: str) -> None:
        self.cwd = cwd
        self.worktree: str | None = None
        padded = cwd + '/'
        at = padded.rfind(WORKTREE_MARKER)
        name = padded[at + len(WORKTREE_MARKER) :].split('/')[0] if at >= 0 else ''
        if name:
            self.project = cwd[:at]
            self.worktree = self.project + WORKTREE_MARKER + name
        else:
            self.project = git_toplevel(cwd) or cwd

    def shared_directory(self, target: str, fork: str | None) -> bool:
        """Rule 1 — anchored to this project and to the fork checkout, nowhere else."""
        if parts_below(target, os.path.join(self.project, '.claude')) is not None:
            return True
        if parts_below(target, os.path.join(self.project, '_bmad-output')) is not None:
            return True
        below_bmad = parts_below(target, os.path.join(self.project, '_bmad'))
        if below_bmad and below_bmad[0].startswith('.sprint-apply-'):
            return True
        return parts_below(target, fork) is not None


def git_toplevel(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = result.stdout.strip()
    if result.returncode != 0 or not top:
        return None
    return os.path.realpath(top)


def running_claude_processes() -> int:
    """Same count the one-liner took: `ps -eo command | grep -c "^claude"`.

    If ps cannot be run the count is 0 and the main-checkout refusal does not fire — the
    one-liner behaved the same way, and that is unchanged here.
    """
    try:
        result = subprocess.run(
            ['ps', '-eo', 'command'], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    return sum(1 for line in result.stdout.splitlines() if line.startswith('claude'))


def log_main_override(project: str, target: str) -> None:
    printable = ''.join(ch if ch.isprintable() else '?' for ch in target)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    pwd = os.environ.get('PWD') or project
    try:
        with open(os.path.join(project, '.claude', 'main-edit-overrides.log'), 'a') as log:
            log.write(f'{stamp} main-edit-override FILE={printable} PWD={pwd}\n')
    except OSError:
        pass


# --- the decision --------------------------------------------------------------------


def decide(raw: str, session: Session, home: str | None) -> dict | None:
    code_root = os.path.realpath(os.path.join(home, 'code')) if home else None
    fork = os.path.realpath(os.path.join(home, 'bmad-method-v6')) if home else None
    lexical = lexical_path(raw, session.cwd)

    try:
        target = resolve(raw, session.cwd)
    except (OSError, ValueError) as error:
        return decide_unresolved(lexical, session, str(error))

    # 1 and 2 — places this session may always write.
    if session.shared_directory(target, fork):
        return None
    if session.worktree and parts_below(target, session.worktree) is not None:
        return None

    # 3 — the project's shared tree.
    if parts_below(target, session.project) is not None:
        if session.worktree:
            return decision(
                'deny',
                DENY_OUTSIDE_WORKTREE.format(
                    target=target, project=session.project, worktree=session.worktree
                ),
            )
        return decide_main_checkout(target, session, may_override=True)

    # 4 — somewhere else entirely.
    if parts_below(target, code_root) is None:
        return None
    if any(is_sensitive(p) or is_tool_config_path(p) for p in (target, lexical)):
        return None
    template = ALLOW_CROSS_REPO_FROM_WORKTREE if session.worktree else ALLOW_CROSS_REPO_FROM_MAIN
    return decision('allow', template.format(target=target, project=session.project))


def decide_main_checkout(target: str, session: Session, may_override: bool) -> dict | None:
    if may_override and os.environ.get('BMAD_ALLOW_MAIN_EDIT') == '1':
        log_main_override(session.project, target)
        return decision('allow', ALLOW_MAIN_OVERRIDE.format(target=target))
    count = running_claude_processes()
    if count > 1:
        return decision('deny', DENY_PARALLEL_SESSIONS.format(count=count))
    return None


def decide_unresolved(lexical: str, session: Session, error: str) -> dict | None:
    """The path would not resolve. Never an allow; a refusal if it looks like ours."""
    project = session.project.rstrip('/')
    if lexical != project and not lexical.startswith(project + '/'):
        return None
    printable = ''.join(ch if ch.isprintable() else '?' for ch in lexical)
    if session.worktree:
        return decision(
            'deny',
            DENY_UNRESOLVED_IN_WORKTREE.format(
                target=printable, error=error, project=session.project, worktree=session.worktree
            ),
        )
    return decide_main_checkout(printable, session, may_override=False)


def read_target() -> str | None:
    """The file path from the hook's stdin, or None when the input cannot be trusted."""
    try:
        payload = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get('tool_input')
    raw = tool_input.get('file_path') if isinstance(tool_input, dict) else None
    if raw is None:
        raw = os.environ.get('CLAUDE_TOOL_INPUT_FILE_PATH')
    return raw if isinstance(raw, str) and raw else None


def main() -> int:
    raw = read_target()
    if raw is None:
        return 0
    try:
        cwd = os.path.realpath(os.getcwd())
    except OSError:
        return 0
    answer = decide(raw, Session(cwd), os.environ.get('HOME') or None)
    if answer is not None:
        print(json.dumps(answer))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:  # an internal error is reported by the wrapper, never as a decision
        sys.exit(1)
