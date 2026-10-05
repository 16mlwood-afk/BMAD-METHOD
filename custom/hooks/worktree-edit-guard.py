#!/usr/bin/env python3
"""
worktree-edit-guard — PreToolUse (Edit|Write|NotebookEdit): keep a session's edits inside its own worktree.

WHAT IT IS FOR. Several Claude sessions share one checkout of a project. Two of them
editing the same working tree overwrite each other silently, so each session works in its
own worktree under <project>/.claude/worktrees/<name>/ and this guard refuses an Edit or
Write that would land in the project's shared tree from the wrong place.

It replaces a 2,900-character shell one-liner that made the same decisions. The one-liner
was patched four times on 2026-10-05 (da84c7d7, d055b46e, a90c7b8d, 796bc01a) and each
patch left a neighbouring hole, because nobody could read it. This file is the same
decision table, written so it can be read and tested.

THE DECISIONS. "P" is the session's project. It is $CLAUDE_PROJECT_DIR when the harness
sets it (taken back to the owning checkout when that is itself a worktree). Otherwise it is
what git says owns the working directory. It is never guessed from the LAST
`/.claude/worktrees/` in the working directory, which is how <P>/sub/.claude/worktrees/x
once made P itself look like somebody else's repository. When neither source answers, P is
a best guess that can still refuse and can never approve.

The path is first put in the form the tool will actually write to: surrounding whitespace
stripped and a leading `~/` expanded, exactly as Claude Code does. Every rule is then
decided on where the target REALLY is — symlinks, `..`, `.` and stray slashes resolved.

  1. The target is in one of the shared directories        -> no decision
       P/.claude/   P/_bmad-output/   P/_bmad/.sprint-apply-*   ~/bmad-method-v6/
  2. In a worktree, and the target is inside that worktree  -> no decision
  3. The target is inside P (and not covered by 1 or 2):
       in a worktree                                        -> DENY
       main checkout, BMAD_ALLOW_MAIN_EDIT=1                -> allow, and LOG it
         (never for a sensitive path, and never when the log line could not be written)
       main checkout, more than one claude process running  -> DENY
       main checkout, otherwise                             -> no decision
  4. The target is outside P:
       under ~/code, not sensitive, not a tool-config path  -> allow (cross-repo edit)
       anything else                                        -> no decision

THE OWNER'S SWITCH. The rule-4 approval sits behind AUTO_APPROVE_CROSS_REPO below. Set it
to False and this guard never approves a path outside the project again; everything else is
unchanged.

AN ALLOW IS NEVER EMITTED, by either rule, when any of these holds:
  * the path is sensitive (see SENSITIVE_NAMES), matched on the casefolded, NFKC-normalised
    path — this volume folds U+017F to `s`, so `credentialſ` IS `credentials`;
  * any component is not plain ASCII, or changes when its whitespace is stripped;
  * the file already exists with more than one hard link (it is also some other path);
and the cross-repo approval is additionally withheld when P was not confirmed, when the
target is in the same git repository as the working directory or in one that contains it,
and when git did not answer in time.

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
  * The override log cannot be forged or redirected: every field is sanitised and written
    with json.dumps, and the file is opened without following a symlink and must be a
    regular, singly-linked file in P/.claude.

EXIT CODES. 0 always, except an internal error (an unexpected exception, or a working
directory that no longer exists), which exits 1 with nothing on stdout so the wrapper in the hook wiring can say the check did not run.
A crash must never read as "checked and fine".

Golden cases: python3 custom/hooks/test_worktree_edit_guard.py
"""

from __future__ import annotations

import datetime
import fnmatch
import json
import os
import stat
import subprocess
import sys
import unicodedata

WORKTREE_MARKER = '/.claude/worktrees/'

# THE OWNER'S SWITCH. True: an edit to another repository under ~/code is approved without
# a prompt (rule 4). False: this guard never emits `allow` for a path outside the project,
# and such an edit meets the normal permission prompt. Nothing else changes either way, and
# the BMAD_ALLOW_MAIN_EDIT override is not affected. One line to change; both settings are
# covered by golden cases.
AUTO_APPROVE_CROSS_REPO = True

# The golden suite drives the False setting through this variable. It is read once, here,
# and it can only switch the approval OFF — a session's environment can never turn back on
# what the constant above turned off.
CROSS_REPO_APPROVAL = AUTO_APPROVE_CROSS_REPO and os.environ.get('BMAD_GUARD_AUTO_APPROVE') != '0'

# Each child process gets this long. The wrapper allows 5s in all and the slowest route
# makes two calls, so a hung git or ps is reported as "did not answer", never as a pass.
CHILD_TIMEOUT_SECONDS = 2

# Never auto-approved, wherever they are. Matched on the casefolded, NFKC-normalised form
# of EVERY path component, because the common filesystems here ignore case and fold
# compatibility characters (.ENV, .GIT/ and `credentialſ` reach the same files) and because
# a directory called `.ssh` makes everything under it sensitive. Besides secrets, the list
# holds the files that EXECUTE or INSTRUCT: git hooks, CI workflows, editor tasks, MCP
# server definitions and agent instruction files.
SENSITIVE_NAMES = (
    '.git',
    '*.git',
    '.git-credentials',
    '.githooks',
    '.husky',
    '.mcp.json',
    'claude.md',
    'agents.md',
    '*.env',
    '.dev.vars',
    'secrets.*',
    '*.p12',
    '*.pfx',
    'id_ecdsa*',
    'id_dsa*',
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
SENSITIVE_PAIRS = (
    ('.docker', 'config.json'),
    ('.kube', 'config'),
    ('.vscode', 'tasks.json'),
    ('.github', 'workflows'),
)

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


def printable(text: str) -> str:
    """`text` with every control, format and unpaired character replaced by `?`.

    Used for everything this guard echoes — into a reason a person reads and into the
    override log — so a newline or an escape sequence in a file name cannot dress the
    message up as something else.
    """
    return ''.join(ch if ch.isprintable() else '?' for ch in text)


# --- paths ---------------------------------------------------------------------------


def as_the_tool_writes_it(raw: str) -> str:
    """The path Claude Code will actually open: whitespace stripped, a leading `~/` expanded.

    Judging the raw string instead approved `…/other/.env ` (not sensitive as written,
    `.env` once written) and gave ` /abs/path` and `~/code/proj/src/a.ts` no decision from
    a worktree, because neither looks absolute until it is tidied.
    """
    path = raw.strip()
    if path == '~' or path.startswith('~/'):
        path = os.path.expanduser(path)
    return path


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
    raw.encode('utf-8')  # a lone surrogate is not a path; UnicodeError is a ValueError
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
    except (OSError, ValueError):
        return None
    probe = path
    while True:
        try:
            if os.path.samestat(os.stat(probe), root_stat):
                return [part for part in path[len(probe) :].split('/') if part]
        except (OSError, ValueError):
            pass
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent


def folded_parts(path: str) -> list[str]:
    """Path components as the filesystem compares them: NFKC, casefolded, whitespace off."""
    folded = unicodedata.normalize('NFKC', path).casefold()
    return [part.strip() for part in folded.split('/') if part.strip()]


def is_sensitive(path: str) -> bool:
    parts = folded_parts(path)
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
    parts = folded_parts(path)
    if '.claude' in parts or '_bmad-output' in parts:
        return True
    return any(a == '_bmad' and b.startswith('.sprint-apply-') for a, b in zip(parts, parts[1:]))


def is_plainly_named(path: str) -> bool:
    """Every component is ASCII and says the same thing with its whitespace stripped.

    A name the filesystem may fold onto another one (`ſ` onto `s`), or that the tool will
    trim before writing, is not a name this guard can vouch for.
    """
    if not path.isascii():
        return False
    return all(part == part.strip() for part in path.split('/'))


def is_also_another_path(target: str) -> bool:
    """The target exists as a file with more than one hard link.

    A hard link under ~/code/other can BE ~/.zshrc or a file in the main checkout, and no
    amount of path resolution shows it. An unreadable target counts as linked: unknown is
    not a reason to approve.
    """
    try:
        info = os.lstat(target)
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True
    return not stat.S_ISDIR(info.st_mode) and info.st_nlink > 1


def may_ever_allow(raw: str, tidy: str, target: str, lexical: str) -> bool:
    """The tests every `allow` must pass, whichever rule is about to emit it."""
    if os.path.basename(raw.rstrip('/')) != os.path.basename(tidy.rstrip('/')):
        return False  # the name that would be written is not the name that was given
    for path in (target, lexical):
        if is_sensitive(path) or not is_plainly_named(path):
            return False
    return not is_also_another_path(target)


# --- git and ps ----------------------------------------------------------------------

DID_NOT_ANSWER = object()  # a child process timed out: not "no", just no answer


def git_repository(directory: str):
    """-> (common dir, toplevel) of the repository holding `directory`.

    None when it is not in a work tree, DID_NOT_ANSWER when git timed out. The common dir
    is the one thing a checkout and all of its worktrees share, so it is what says two
    paths are the same repository.
    """
    try:
        result = subprocess.run(
            ['git', '-C', directory, 'rev-parse', '--path-format=absolute', '--git-common-dir', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT_SECONDS,
            # GIT_DIR and friends would answer for some other repository than `directory`.
            env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')},
        )
    except subprocess.TimeoutExpired:
        return DID_NOT_ANSWER
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 2 or not all(lines):
        return None
    return os.path.realpath(lines[0]), os.path.realpath(lines[1])


def nearest_directory(path: str) -> str:
    probe = path
    while not os.path.isdir(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return probe


def running_claude_processes() -> int:
    """How many claude CLI processes are running, by the basename of the first word.

    The one-liner counted lines STARTING `claude`, which misses a session launched by its
    full path (/Users/x/.local/bin/claude …) — 4 of 15 on the machine this was measured on.
    If ps cannot be run the count is 0 and the main-checkout refusal does not fire — the
    one-liner behaved the same way, and that is unchanged here.
    """
    try:
        result = subprocess.run(
            ['ps', '-eo', 'command'], capture_output=True, text=True, timeout=CHILD_TIMEOUT_SECONDS
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0
    count = 0
    for line in result.stdout.splitlines():
        words = line.split()
        if words and os.path.basename(words[0]) == 'claude':
            count += 1
    return count


# --- the session ---------------------------------------------------------------------


def before_first_marker(path: str) -> str | None:
    """`path` cut at its FIRST /.claude/worktrees/<name>, or None when it has none."""
    padded = path + '/'
    at = padded.find(WORKTREE_MARKER)
    if at < 0 or not padded[at + len(WORKTREE_MARKER) :].split('/')[0]:
        return None
    return path[:at]


class Session:
    """Where this session is working: its project, and its worktree if it is in one.

    `confirmed` says the project came from the harness or from git. When it is False the
    project is a guess from the working directory: good enough to refuse with, never good
    enough to approve with.
    """

    def __init__(self, cwd: str, declared: str | None = None) -> None:
        self.cwd = cwd
        self.declared: str | None = None
        self.confirmed = False
        self._repository = None
        self._asked_git = False

        if declared and os.path.isdir(declared):
            self.declared = os.path.realpath(declared)
            self.project = before_first_marker(self.declared) or self.declared
            self.confirmed = True
        else:
            repository = self.repository()
            if repository is None or repository is DID_NOT_ANSWER:
                self.project = before_first_marker(cwd) or cwd
            else:
                common, toplevel = repository
                owner = os.path.dirname(common) if os.path.basename(common) == '.git' else toplevel
                # A worktree kept outside its checkout is its own project, as it always was.
                self.project = owner if parts_below(toplevel, owner) is not None else toplevel
                self.confirmed = True

        self.worktree: str | None = None
        worktrees = self.project.rstrip('/') + WORKTREE_MARKER.rstrip('/')
        below = parts_below(cwd, worktrees)
        if below:
            self.worktree = os.path.join(worktrees, below[0])

    def repository(self):
        if not self._asked_git:
            self._repository = git_repository(self.cwd)
            self._asked_git = True
        return self._repository

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

    def is_a_different_repository(self, target: str) -> bool:
        """True only when git positively says the target is not this session's repository.

        False when the target shares a git common dir with the working directory, when the
        target's repository CONTAINS the working directory (a scratch `git init` inside
        the project), and when git did not answer.
        """
        theirs = git_repository(nearest_directory(target))
        ours = self.repository()
        if theirs is DID_NOT_ANSWER or ours is DID_NOT_ANSWER:
            return False
        if theirs is None:
            return True
        common, toplevel = theirs
        if ours is not None and ours[0] == common:
            return False
        roots = {toplevel}
        if os.path.basename(common) == '.git':
            roots.add(os.path.dirname(common))
        return not any(parts_below(self.cwd, root) is not None for root in roots)


def log_main_override(project: str, target: str) -> bool:
    """Append the override to P/.claude/main-edit-overrides.log. True only if it was written.

    The line is `<stamp> main-edit-override FILE=<json string> PWD=<json string>`: both
    values are sanitised and then JSON-quoted, so neither a newline nor a ` PWD=` inside a
    file name can start a line or a field of its own. The file is opened without following
    a symlink and must be a regular, singly-linked file whose directory really is P/.claude
    — the log was once a symlink to ~/.zshrc, and this guard appended to it.
    """
    directory = os.path.join(project, '.claude')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    pwd = os.environ.get('PWD') or project
    line = (
        f'{stamp} main-edit-override FILE={json.dumps(printable(target))} '
        f'PWD={json.dumps(printable(pwd))}\n'
    )
    try:
        if os.path.islink(directory) or not os.path.isdir(directory):
            return False
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW
        handle = os.open(os.path.join(directory, 'main-edit-overrides.log'), flags, 0o600)
        try:
            info = os.fstat(handle)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return False
            os.write(handle, line.encode('utf-8', 'replace'))
        finally:
            os.close(handle)
    except (OSError, ValueError):
        return False
    return True


# --- the decision --------------------------------------------------------------------


def decide(raw: str, session: Session, home: str | None) -> dict | None:
    code_root = os.path.realpath(os.path.join(home, 'code')) if home else None
    fork = os.path.realpath(os.path.join(home, 'bmad-method-v6')) if home else None
    tidy = as_the_tool_writes_it(raw)
    if not tidy:
        return None
    lexical = lexical_path(tidy, session.cwd)

    try:
        target = resolve(tidy, session.cwd)
    except (OSError, ValueError) as error:  # ValueError covers UnicodeError
        return decide_unresolved(lexical, session, printable(str(error)))

    # 1 and 2 — places this session may always write.
    if session.shared_directory(target, fork):
        return None
    if session.worktree and parts_below(target, session.worktree) is not None:
        return None

    allowable = may_ever_allow(raw, tidy, target, lexical)

    # 3 — the project's shared tree.
    in_project = parts_below(target, session.project) is not None
    if not in_project and session.declared:
        in_project = parts_below(target, session.declared) is not None
    if in_project:
        if session.worktree:
            return decision(
                'deny',
                DENY_OUTSIDE_WORKTREE.format(
                    target=printable(target), project=session.project, worktree=session.worktree
                ),
            )
        return decide_main_checkout(target, session, may_override=allowable)

    # 4 — somewhere else entirely.
    if not CROSS_REPO_APPROVAL or not session.confirmed or not allowable:
        return None
    if parts_below(target, code_root) is None:
        return None
    if is_tool_config_path(target) or is_tool_config_path(lexical):
        return None
    if not session.is_a_different_repository(target):
        return None
    template = ALLOW_CROSS_REPO_FROM_WORKTREE if session.worktree else ALLOW_CROSS_REPO_FROM_MAIN
    return decision('allow', template.format(target=printable(target), project=session.project))


def decide_main_checkout(target: str, session: Session, may_override: bool) -> dict | None:
    if may_override and os.environ.get('BMAD_ALLOW_MAIN_EDIT') == '1':
        # "Allow, and LOG it": an override that could not be logged is not allowed.
        if log_main_override(session.project, target):
            return decision('allow', ALLOW_MAIN_OVERRIDE.format(target=printable(target)))
    count = running_claude_processes()
    if count > 1:
        return decision('deny', DENY_PARALLEL_SESSIONS.format(count=count))
    return None


def decide_unresolved(lexical: str, session: Session, error: str) -> dict | None:
    """The path would not resolve. Never an allow; a refusal if it looks like ours."""
    roots = [session.project.rstrip('/')]
    if session.declared:
        roots.append(session.declared.rstrip('/'))
    if not any(lexical == root or lexical.startswith(root + '/') for root in roots):
        return None
    if session.worktree:
        return decision(
            'deny',
            DENY_UNRESOLVED_IN_WORKTREE.format(
                target=printable(lexical),
                error=error,
                project=session.project,
                worktree=session.worktree,
            ),
        )
    return decide_main_checkout(printable(lexical), session, may_override=False)


def strictest(answers: list) -> dict | None:
    """One answer for several paths: a refusal wins, then no decision, then an allow."""
    kinds = [a['hookSpecificOutput']['permissionDecision'] if a else None for a in answers]
    if 'deny' in kinds:
        return answers[kinds.index('deny')]
    if None in kinds:
        return None
    return answers[0]


def read_targets() -> list[str] | None:
    """The path(s) from the hook's stdin, or None when the input cannot be trusted.

    Edit and Write carry `file_path`; NotebookEdit carries `notebook_path`. Only what is IN
    the tool input is judged: the CLAUDE_TOOL_INPUT_FILE_PATH fallback the one-liner had is
    gone, because it could produce an approval for a path the tool was never given.
    """
    try:
        payload = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get('tool_input')
    if not isinstance(tool_input, dict):
        return None
    found = []
    for key in ('file_path', 'notebook_path'):
        value = tool_input.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value:
            return None
        found.append(value)
    return found or None


def main() -> int:
    targets = read_targets()
    if targets is None:
        return 0
    try:
        cwd = os.path.realpath(os.getcwd())
    except OSError:
        return 1  # no working directory, so nothing was checked — the wrapper says so
    session = Session(cwd, os.environ.get('CLAUDE_PROJECT_DIR') or None)
    home = os.environ.get('HOME') or None
    answer = strictest([decide(raw, session, home) for raw in targets])
    if answer is not None:
        print(json.dumps(answer))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:  # an internal error is reported by the wrapper, never as a decision
        sys.exit(1)
