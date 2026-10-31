#!/usr/bin/env python3
"""PreToolUse(Bash) worktree guard — edit-equivalent detection by WRITE TARGET.

Replaces the inline 2050-char regex chain that lived in .claude/settings.local.json.

WHY THIS EXISTS AS A FILE
------------------------
The inline version had two defects that a regex chain in JSON cannot express, and
that nobody could test:

  1. FALSE POSITIVE (the reason this was written).  Its allowlist matched only
     `/Users/*/.claude/` — the HOME dotfile dir — never the PROJECT `.claude/`,
     `_bmad-output/`, or `_bmad/.sprint-apply-*`.  The Edit|Write matcher allowlists
     `*/.claude/*` for all three.  So the same target was permitted via Edit and
     DENIED via Bash, purely by which tool the agent reached for.

     That landed hardest on `.claude/wip-register.yaml`: CLAUDE.md mandates the WIP
     claim be written in the MAIN CHECKOUT (a claim written inside a worktree is
     invisible to other sessions until committed AND pushed), while the guard's only
     offered remedy was "call EnterWorktree" — the exact thing the register contract
     forbids.  The claim-before-you-act protocol was blocked by default on its most
     obvious write route.  collision_guard.py already solved this shape for its own
     deny tier via DENY_EXEMPT_ZONES: you cannot require a claim to write the file
     that IS the claim.  This guard now honours the same exemption.

  2. FALSE NEGATIVE (found while fixing 1, not previously known).  The old check was
     "does the command contain an exempt-looking target anywhere?" -> exit 0.  So

         echo a > /tmp/x; echo b > src/db/schema.ts

     was ALLOWED: `> /tmp/` matched, and the schema write rode along unexamined.  A
     mixed command was exempted by its most innocent target.

Both are the same root cause: the old guard classified the command STRING, this one
enumerates WRITE TARGETS and classifies each.  Deny if ANY target is non-exempt.
That is also what makes the register carve-out safe — see MIXED TARGETS below.

MIXED TARGETS ARE NOT EXEMPT
----------------------------
A command that writes the register AND a protected path is DENIED.  An unconditional
string-match exemption ("the command mentions wip-register.yaml") would be a general
bypass of the entire worktree guard: write anything you like, name the register in a
comment.  Mirrors collision_guard.py's documented rule that a mixed target is not
exempt.

HONEST LIMITS
-------------
This is a heuristic over a shell string, not a shell parser.  It does not expand
variables, command substitution, globs, or aliases; a target behind `$VAR` is
unresolvable and is treated as NON-exempt (fail closed toward the guard).  It cannot
see through `bash -c "..."`, `xargs`, or a script file's contents.  Detection is
deliberately conservative in the direction that matters: an unrecognised write shape
is not an edit-equivalent (no deny), but an unresolvable target inside a recognised
write shape IS treated as protected.

BARE-FILENAME FOOTGUN (observed 2026-07-25, mailbox write)
----------------------------------------------------------
Exempt-path matching requires an absolute path.  A prior `cd` that leaves a bare
filename will lose the .claude/ component and trigger a false block.  Always pass
absolute paths to mailbox writes.

Mechanism: the guard absolutises a relative target against the SESSION cwd, not
against a `cd` performed earlier in the same command string (it does not execute the
command, so it cannot know the shell moved).  So

    cd ~/.claude/mailbox && cat >> cash-recovery.inbox.md   # BLOCKED (resolves to
                                                            # <project>/cash-recovery.inbox.md)
    cat >> /Users/<you>/.claude/mailbox/cash-recovery.inbox.md   # ALLOWED

Same shape for any exempt dir (`_bmad-output/`, `_bmad/.sprint-apply-*`, the fork).
Fail-closed by design — the retry with an absolute path is the fix, not an override.

Distribution: machine-local.  Wired via .claude/settings.local.json, which is
gitignored and does NOT sync — the other projects carry the old inline guard until
each is updated.  This file is tracked so the logic is reviewable and testable.
"""

import json
import os
import re
import subprocess
import sys

# --- Allowlist ------------------------------------------------------------------
# Aligned with the Edit|Write matcher's `case "$FILE" in` allowlist:
#     */_bmad-output/*  |  */.claude/*  |  */_bmad/.sprint-apply-*  |  /Users/*/bmad-method-v6/*
# plus the transient/scratch paths the Bash route legitimately needs and the Edit
# route never touches.
#
# Substring match against the RESOLVED (absolutised, normalised) target path.
EXEMPT_SUBSTRINGS = (
    "/.claude/",            # project AND home .claude/ — machine-local config, hooks,
                            # markers, mailbox, and the WIP register. Never deliverable
                            # code; the worktree/PR pipeline does not apply.
    "/_bmad-output/",       # BMAD artifact dir — exists outside worktrees by design
    "/_bmad/.sprint-apply-",
    "/tmp/",
    "/private/tmp/",
    "/var/tmp/",
    "/var/folders/",        # macOS $TMPDIR
    "/private/var/folders/",
    "/dev/",
    "/bmad-method-v6/",     # the fork — its own repo, its own delivery flow
    "/.secrets",
)

# Named explicitly even though "/.claude/" above already covers it.
# This is the load-bearing case: if the general .claude/ rule is ever tightened, the
# register must survive that tightening, because requiring a worktree to write the
# claim file deadlocks the claim protocol itself (see module docstring).
# Cross-reference: collision_guard.py DENY_EXEMPT_ZONES.
REGISTER_SUFFIX = "/.claude/wip-register.yaml"


# --- Resolution context ---------------------------------------------------------
# Two things made this guard judge the WRONG PATH, which is worse than judging it
# strictly: a correct verdict about a file the command never touches is still a false
# positive, and every one of those teaches the agent the block is noise.
#
#   (1) A leading `cd <dir> &&` was ignored, so every RELATIVE target in a
#       `cd ~/bmad-method-v6 && sed -i … tools/x.js` command was resolved against
#       CLAUDE_PROJECT_DIR (cash-recovery) instead. The fork is on the exempt list;
#       cash-recovery/tools/x.js is not — so an allowlisted fork edit was denied for
#       a path that does not exist. (Observed 2026-07-26; fork-gaps FG-2026-07-21-02.)
#   (2) A `$VAR` target failed closed even when the variable was assigned to a LITERAL
#       earlier in the same command: `T=/tmp/probe; printf x > "$T/f"` denied a /tmp
#       write while `> /tmp/probe/f` is exempt. The deny message even told the agent to
#       "use a literal path" — i.e. the guard knew it could not resolve, and blocked.
#
# Both are resolution fixes, NOT a loosening: substitution can equally turn an
# unresolvable target into a PROTECTED one, which strengthens the verdict. Anything
# still unresolvable after substitution fails closed exactly as before.

_LEADING_CD = re.compile(r"^\s*cd\s+(\"[^\"$`]+\"|'[^'$`]+'|[^\s;&|$`*?]+)\s*(?:&&|;)")
# `VAR=<value>` — the value is captured WHOLE and then validated. Do NOT exclude `$` in
# the character class: that truncates instead of skipping. `T=/tmp/probe-$$` matched as
# `T=/tmp/probe-`, which then resolved `$T/f` to `/tmp/probe-/f` and exempted it — a
# silently WRONG resolution, the exact class of bug this whole block exists to remove.
# Capture, then reject anything non-literal.
_ASSIGN = re.compile(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|'[^']*'|[^\s;&|<>()]+)")
_NON_LITERAL = ("$", "`", "*", "?")


def resolution_base(cmd: str, cwd: str) -> str:
    """The directory relative targets should resolve against.

    Honours a single LEADING literal `cd <dir> &&|;`. Deliberately only the leading
    one: a `cd` buried mid-command changes the base for some targets and not others,
    and guessing which is worse than not guessing. Mirrors what the sibling
    fg-routing-notice.py hook already does.
    """
    m = _LEADING_CD.match(cmd)
    if not m:
        return cwd
    d = os.path.expanduser(m.group(1).strip("\"'"))
    if not os.path.isabs(d):
        d = os.path.join(cwd, d)
    return os.path.normpath(d)


def literal_assignments(cmd: str) -> dict:
    """`VAR` -> literal value, for FULLY LITERAL assignments in this same command string.

    A partially-literal value is SKIPPED, never truncated. Half-resolving a path is worse
    than not resolving it: it produces a confident verdict about a path that does not
    exist. (Caught by golden case V3 before this shipped.)
    """
    out = {}
    for name, val in _ASSIGN.findall(cmd):
        v = val.strip("\"'")
        if any(ch in v for ch in _NON_LITERAL):
            continue
        out[name] = v
    return out


def substitute_literals(target: str, env: dict) -> str:
    """Replace `$VAR` / `${VAR}` with a literal assigned in the same command."""
    if "$" not in target or not env:
        return target

    def repl(m):
        return env.get(m.group(1) or m.group(2), m.group(0))

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", repl, target)


def is_exempt_target(target: str, cwd: str) -> bool:
    """True if this write target is outside the worktree pipeline's remit."""
    if not target:
        return False
    # Unresolvable (variable / substitution / glob) -> NOT exempt. Fail closed.
    if any(ch in target for ch in "$`*?"):
        return False

    t = os.path.expanduser(target)
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    t = os.path.normpath(t)

    if t.endswith(REGISTER_SUFFIX):
        return True
    return any(s in t for s in EXEMPT_SUBSTRINGS)


# --- Write-target extraction ----------------------------------------------------

# `> target` / `>> target`, excluding fd-dups (`>&2`, `2>&1`) and comparisons.
# Leading char class rejects `2>`, `&>`, `->`, `=>`, `!>`, `<>`.
# The `(?!=)` lookahead rejects the GREATER-OR-EQUAL operator: `len(x)>=2` is a
# comparison, not a redirect to a file named "=2". Found by this guard firing on the
# very script written to clean up after it — `)` is not in the lookbehind set, so
# `>=` slipped through. Comparison operators are ubiquitous in inline python/awk
# passed through Bash, so this is a high-frequency false positive, not an edge case.
_REDIRECT = re.compile(r"(?<![0-9&<>=!|-])>>?(?!=)\s*([^\s|&;<>()]+)")
# `tee target`, `tee -a target`
_TEE = re.compile(r"(?:^|[\s;|&(])tee\s+(?:-a\s+)?([^\s|&;<>()-][^\s|&;<>()]*)")
# `sed -i` / `sed -i.bak` / `sed -i ''` ... trailing operands are the files.
_SED_I = re.compile(r"(?:^|[\s;|&(])sed\s+(?:-[a-zA-Z]*i[a-zA-Z]*(?:\.\S+)?|--in-place\S*)\s+(.*)$")
# `awk -i inplace ... file`
_AWK_I = re.compile(r"(?:^|[\s;|&(])awk\s+-i\s+inplace\s+(.*)$")


def _trailing_operands(rest: str) -> list:
    """Best-effort: the file operands at the end of a sed/awk in-place invocation.

    BSD `sed -i ''` takes an EMPTY backup-suffix argument, so the operand list is
    ['', 's/a/b/', file]. Dropping empties before picking the script is required —
    otherwise the script ('s/a/b/') is mistaken for the file and the real file is
    never classified. (Golden case P3.)
    """
    parts = []
    for tok in rest.split():
        if tok.startswith("-"):
            continue
        tok = tok.strip("'\"")
        if tok:                      # drop the BSD empty backup-suffix
            parts.append(tok)
    # First remaining operand is the script ('s/a/b/'); the rest are files. A lone
    # operand IS the file (the script came via -e).
    return parts[1:] if len(parts) > 1 else parts


_HEREDOC_TAG = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")


def strip_heredoc_bodies(cmd: str) -> str:
    """Remove heredoc BODIES, keeping the header lines.

    A heredoc body is data handed to another program (python, awk, node, jq), not
    shell syntax — its `>` and `>=` are that program's operators. The redirect that
    matters lives on the HEADER line (`cat >> file <<'EOF'`), which is preserved.

    Without this, any inline script containing a comparison reads as a redirect:
    `while len(keep) > 1` was parsed as a write to a file named "1". Unlike `>=`,
    a spaced `>` is genuinely ambiguous to a regex — `echo x > 1` IS a real redirect
    to "1" — so it cannot be fixed by tightening the operator pattern. Scoping it out
    of program bodies is the only correct discrimination available without a parser.
    """
    lines = cmd.split("\n")
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        m = _HEREDOC_TAG.search(lines[i])
        if m:
            tag = m.group(1)
            i += 1
            while i < len(lines) and lines[i].strip() != tag:
                i += 1  # drop the body
            if i < len(lines):
                i += 1  # drop the closing tag
            continue
        i += 1
    return "\n".join(out)


def _quoted_spans(cmd: str) -> list:
    """(start, end) ranges of single/double-quoted regions, for redirect filtering."""
    spans, i, n = [], 0, len(cmd)
    while i < n:
        ch = cmd[i]
        if ch in "'\"":
            j = cmd.find(ch, i + 1)
            if j == -1:
                break
            spans.append((i, j))
            i = j + 1
        else:
            i += 1
    return spans


def extract_write_targets(cmd: str) -> list:
    """Every path this command appears to WRITE. Empty => not an edit-equivalent."""
    targets = []
    # Heredoc bodies are program data, not shell syntax. (Golden cases N7/N9.)
    cmd = strip_heredoc_bodies(cmd)
    # A '>' inside a quoted string is DATA, not a redirect: `grep -r 'foo > bar' src/`
    # must not read as a write to `bar`. (Golden case N1.)
    spans = _quoted_spans(cmd)
    for m in _REDIRECT.finditer(cmd):
        if any(s <= m.start() <= e for s, e in spans):
            continue
        targets.append(m.group(1).strip("'\""))
    # The SAME quoted-span rule must apply to tee/sed/awk, not just redirects. It did not,
    # and that is the documented read-only false-positive class: a command that merely
    # MENTIONS `sed -i` or `tee x` inside a quoted argument was classified as writing.
    # Observed live 2026-07-26 on `python3 -c "... sed -i / cat > file / tee x ..."`, which
    # writes nothing — the deny message listed "x, cat, >, but, writes, nothing" as its
    # targets, and a verdict whose own evidence is word salad is a verdict to distrust.
    # Same family as fork-gaps FG-2026-07-16-03 (read-only `python3 -c` blocked) and
    # FG-2026-07-18-01 (read-only `env | sed -E` blocked).
    def outside_quotes(m):
        return not any(s <= m.start() <= e for s, e in spans)

    for m in _TEE.finditer(cmd):
        if outside_quotes(m):
            targets.append(m.group(1).strip("'\""))
    for pat in (_SED_I, _AWK_I):
        for m in pat.finditer(cmd):
            if outside_quotes(m):
                targets.extend(_trailing_operands(m.group(1)))
    return [t for t in targets if t]


# --- Non-edit shapes that must never be treated as writes -----------------------

def is_message_bearing_vcs(cmd: str) -> bool:
    """git commit/tag/notes or a gh subcommand carrying prose.

    A commit message or PR body routinely contains `>`, `>>`, and file paths — those
    are TEXT, not redirects. Without this the guard fires on its own commit message.
    """
    if not re.search(r"(git\s+(commit|tag|notes)|gh\s+[a-z-]+)", cmd):
        return False
    return bool(re.search(r"<<|\s-F[\s=]|--body-file|\s-m[\s=]|--message[\s=]|\s-b[\s=]|--body[\s=]", cmd))


def parallel_session_count() -> int:
    try:
        out = subprocess.run(["ps", "-eo", "command"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return 0
    return sum(1 for line in out.splitlines() if line.startswith("claude"))


def allow():
    sys.exit(0)


def deny(reason: str):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def ask(reason: str):
    """Surface the decision to the human instead of blocking or waving it through.

    Why this tier exists (owner ruling 2026-07-26). A hard `deny` on a low-risk text edit
    does not stop the edit — it reroutes it. The agent writes the identical change into a
    script and runs that, because a script has no shell-visible write target. So the deny
    bought nothing and cost the audit trail: the sanctioned route became the bypass. `ask`
    costs one prompt, keeps the human at the dangerous moment with full context, and leaves
    nothing to route around.

    It is NOT a general softening. It applies only to the low-risk text set below; source,
    migrations, lockfiles and CI stay `deny`. And it cannot replace the env-var override,
    which is the headless path — an `ask` in an unattended run just blocks.
    """
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


# Low-risk TEXT that a human edits deliberately and a reviewer reads as prose. An accidental
# write here is cheap and obvious; a blocked one is expensive and reroutes into a bypass.
# Deliberately NOT extension-only: a `.md` under `src/` is still adjacent to code, and a
# lockfile/CI file is never in this set regardless of how text-like it looks.
_ASK_SUFFIXES = (".md", ".mdx", ".txt", ".rst")
_ASK_DIR_HINTS = ("/docs/", "/runbooks/", "/_bmad-output/", "/planning-artifacts/")
_NEVER_ASK = ("/src/", "/drizzle/", "/migrations/", "/.github/", "/scripts/",
              "package.json", "package-lock.json", "pnpm-lock", "yarn.lock")


def is_low_risk_text(target: str, cwd: str) -> bool:
    t = os.path.expanduser(target)
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    t = os.path.normpath(t)
    if any(bad in t for bad in _NEVER_ASK):
        return False
    return t.endswith(_ASK_SUFFIXES) or any(h in t for h in _ASK_DIR_HINTS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()  # unparseable payload -> fail OPEN (never block on our own bug)

    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not cmd:
        allow()

    # OBSERVED cwd beats ASSUMED cwd (FG-2026-07-26-06). The harness passes the shell's REAL
    # working directory in the payload; `CLAUDE_PROJECT_DIR` points at the MAIN checkout and does
    # not move when the harness puts a session in a worktree. Reading only the env var meant a
    # session that had correctly called `EnterWorktree` — pwd and `git rev-parse --show-toplevel`
    # both inside `.claude/worktrees/…` — was told *"you are NOT in a worktree. Call EnterWorktree"*
    # while standing in one, and its relative target was resolved against the wrong repo.
    #
    # That is the worst shape a guard can have: it punishes the session that DID the right thing,
    # and the only way out is the bypass. Order is deliberate — payload (observed) first, env
    # (assumed) as the fallback for direct/test invocations that pass no cwd.
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # Already isolated, or explicitly operating on a worktree path.
    if "/.claude/worktrees/" in cwd or "/.claude/worktrees/" in cmd:
        allow()

    if is_message_bearing_vcs(cmd):
        allow()

    targets = extract_write_targets(cmd)
    if not targets:
        allow()  # not an edit-equivalent

    # Resolve BEFORE classifying: a leading `cd` sets the base for relative targets, and
    # a `$VAR` assigned to a literal in this same command is substituted. See the
    # "Resolution context" block — judging the wrong path is a false positive even when
    # the verdict about that path is correct.
    base = resolution_base(cmd, cwd)
    env = literal_assignments(cmd)
    targets = [substitute_literals(t, env) for t in targets]

    protected = [t for t in targets if not is_exempt_target(t, base)]
    if not protected:
        allow()  # every write lands outside the worktree pipeline's remit

    # LOGGED OVERRIDE. The Edit/Write guard's deny message has always named
    # BMAD_ALLOW_MAIN_EDIT=1 as the sanctioned route for a main-checkout maintenance edit —
    # and no guard actually honoured it, so the "override" was documented and inert. An
    # override that cannot be exercised is not an override: it makes the gate LOOK
    # well-designed while pushing every real use into a tool-swap bypass (fork-gaps
    # FG-2026-07-25-02). Honoured here, and LOGGED — an unlogged escape hatch has no signal.
    #
    # Scope note, deliberate: this only makes the ALREADY-DOCUMENTED name work. The other
    # options in that entry — a consumed-and-cleared marker file, or demoting deny to `ask`
    # for docs-only paths — are design choices and are NOT taken here; they are proposals.
    # IN-BAND OVERRIDE — a consumed-and-cleared marker file (FG-2026-07-25-02, reversal 2026-07-26).
    #
    # This was REJECTED earlier the same day in favour of the env var alone, on the grounds that a
    # marker is stale-able state with a bootstrap problem. That judgement was WRONG on the criterion
    # that decides it: REACHABILITY. `BMAD_ALLOW_MAIN_EDIT=1 <cmd>` sets the variable for the
    # COMMAND's process — the hook runs separately and reads the HARNESS environment, so an inline
    # prefix never reaches it. Combined with the Edit tool having no channel to set an env var at
    # all, the "override" could not be exercised from inside a turn by ANY route. An override that
    # cannot be reached is not an override; it is the documented-but-inert escape hatch this entry
    # was opened about, and it kept routing real work into the script bypass.
    #
    # The marker's bootstrap problem is solved by WHERE it lives: `.claude/` is already an exempt
    # zone, so creating it is never itself blocked. Its staleness problem is solved by CONSUMING it —
    # one marker, one override, deleted before the command runs.
    marker = os.path.join(cwd, ".claude", ".allow-main-edit")
    marker_used = False
    if os.path.exists(marker):
        try:
            os.remove(marker)          # consume FIRST: a crash must not leave the gate open
            marker_used = True
        except OSError:
            marker_used = False        # could not consume -> do not honour it

    if marker_used or os.environ.get("BMAD_ALLOW_MAIN_EDIT") == "1":
        try:
            # $BASH_EDIT_GUARD_LOG redirects this, so the golden suite's own override cases
            # do not write rows into the real audit log. Caught immediately: the first entry
            # in the live log came from test case O1, not from a human override — a log
            # polluted by its own tests is not an audit trail.
            log = os.environ.get("BASH_EDIT_GUARD_LOG") or os.path.join(
                os.path.expanduser("~"), ".claude", "logs", "bash-edit-guard-override.jsonl")
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, "a") as fh:
                fh.write(json.dumps({
                    "at": __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "cwd": cwd,
                    "targets": targets,          # paths only — never the command string
                    "protected": protected,
                    "via": "marker" if marker_used else "env",
                }) + "\n")
        except OSError:
            pass  # logging is best-effort; never let it block a sanctioned edit
        allow()

    count = parallel_session_count()
    if count > 1 and all(is_low_risk_text(t, base) for t in protected):
        ask(
            f"{count} parallel claude sessions and you are NOT in a worktree. This command writes "
            f"low-risk TEXT: {', '.join(protected)}. Approve if this is a deliberate local edit "
            "(CLAUDE.md, a runbook, docs, a planning artifact); decline and use a worktree if it is "
            "part of a larger change. Asking rather than blocking is deliberate: a hard deny on a "
            "text edit does not stop it, it reroutes it through a script the guard cannot see."
        )

    if count > 1:
        deny(
            f"BLOCKED: {count} parallel claude sessions detected and you are NOT in a worktree. "
            f"This bash command writes: {', '.join(protected)}. "
            "Call EnterWorktree, OR if this is a cross-repo / cross-project edit, route through a "
            "per-repo worktree. See CLAUDE.md Cross-Repo Edits. "
            "NOTE: .claude/ (incl. wip-register.yaml), _bmad-output/, _bmad/.sprint-apply-*, "
            "~/bmad-method-v6/ and the temp dirs are exempt and must be written in the MAIN "
            "CHECKOUT. A leading `cd <dir> &&` IS honoured for relative targets, and a `$VAR` "
            "assigned to a literal in the same command IS substituted — so if one of those is your "
            "only target and you still see this, the path shown above is what the guard resolved: "
            "check it. A target behind command substitution or a glob stays unresolvable and is "
            "treated as protected by design."
        )
    allow()


if __name__ == "__main__":
    main()
