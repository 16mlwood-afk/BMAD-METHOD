#!/usr/bin/env python3
"""gitignore_claude_block — the ONE place the fork edits a project's .gitignore.

WHY THIS EXISTS (WF-20260925-092). The sync wires the fork's guards into a TRACKED
`.claude/settings.json` and ships guard scripts into `.claude/hooks/`. Most projects ignore
`.claude/` wholesale, so the sync appends negations to make those two paths trackable. The
first version appended

    !.claude/
    !.claude/settings.json
    !.claude/hooks/

and `!.claude/` re-includes the WHOLE directory: in bison-ops and bison-website hundreds of
generated skill files, worktrees and the per-machine `settings.local.json` turned up as
untracked, one `git add -A` away from being committed. Re-including the parent was needed
(git never descends into an excluded directory), but it had to be followed by re-ignoring
its children, so only the two managed paths come back.

WHAT IT DOES.
  * The block under MARK is fork-owned. It is stripped and re-rendered on every run, so a
    project that received the broad form is repaired in place, and a project that no
    longer needs the block loses it.
  * Candidate blocks are tried narrowest-first and each is PROVEN, not assumed: it is
    evaluated in a scratch repository carrying the same ignore rules, and accepted only if
    the two managed paths become trackable AND every other probe path keeps exactly the
    ignored/visible state it had without the block.
  * After writing, the result is re-verified in the real repository; on failure the
    original bytes are restored and it exits 1.
  * It refuses to touch a .gitignore holding local edits of anyone else's. The one edit it
    will build on is its own uncommitted block — which is exactly the state bison-ops and
    bison-website were left in.

Exit codes: 0 trackable (unchanged or rewritten) · 1 cannot make trackable / refused ·
3 check mode, a rewrite would be made. Output: one line per finding on stdout; on exit 1
the block that would fix it, when one exists.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARK = "# BMAD hook wiring — fork guards are tracked config, not local state."

# The paths the fork must be able to commit. `.claude/hooks/bmad-probe.py` stands for any
# guard the fork ships; the directory pattern is what gets negated.
WANT_TRACKED = {".claude/settings.json": ".claude/settings.json",
                ".claude/hooks/bmad-probe.py": ".claude/hooks/"}

# Paths whose ignored/visible state must NOT change because of the block. The first four
# are the ones that leaked in bison-ops; the rest widen the net to generated content.
PROBES = (
    ".claude/settings.local.json",
    ".claude/skills/bmad-probe/SKILL.md",
    ".claude/commands/bmad-probe.md",
    ".claude/worktrees/probe/file.txt",
    ".claude/bmad-synced-scripts.txt",
    ".claude/hooks/__pycache__/probe.cpython-312.pyc",
    ".claude/agents/probe.md",
    ".claude/probe-generated.json",
    "src/probe.ts",
)

PYCACHE = ".claude/hooks/__pycache__/"
_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k == "GIT_ASKPASS"}


def git(root, *args, input_text=None):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          input=input_text, env=_ENV)


# ------------------------------------------------------------------ text model
def strip_block(text):
    """Remove the fork-owned block: MARK through the next blank line or EOF, plus one
    blank line immediately before it. Returns (stripped_text, had_block)."""
    lines = text.split("\n")
    out, i, had = [], 0, False
    while i < len(lines):
        if lines[i].strip() == MARK:
            had = True
            if out and out[-1].strip() == "":
                out.pop()
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                i += 1
            continue
        out.append(lines[i])
        i += 1
    stripped = "\n".join(out)
    # Normalise the tail: exactly one trailing newline when there is content.
    stripped = stripped.rstrip("\n")
    return (stripped + "\n" if stripped else ""), had


def render(stripped, body):
    if not body:
        return stripped
    head = stripped if stripped.endswith("\n") or not stripped else stripped + "\n"
    sep = "\n" if head else ""
    return head + sep + MARK + "\n" + "\n".join(body) + "\n"


def candidates(blocked_patterns):
    negs = ["!" + p for p in blocked_patterns]
    tail = [PYCACHE] if ".claude/hooks/" in blocked_patterns else []
    # Narrowest first. The second re-includes the directory only so that its children
    # can be re-ignored and the two managed paths re-included — never the whole tree.
    return [negs + tail, ["!.claude/", ".claude/*"] + negs + tail]


# ------------------------------------------------------------- evaluation
def evaluate(root, gitignore_text, paths):
    """Which of `paths` are ignored under `gitignore_text`, evaluated in a scratch repo so
    the real one is never mutated to find out. Carries .git/info/exclude across; the
    user's global excludes file applies in both places by construction."""
    with tempfile.TemporaryDirectory(prefix="bmad-gi-") as td:
        s = Path(td)
        if git(s, "init", "-q").returncode != 0:
            raise RuntimeError("could not create a scratch repository")
        (s / ".gitignore").write_text(gitignore_text)
        ex = Path(root) / ".git" / "info" / "exclude"
        if ex.is_file():
            (s / ".git" / "info").mkdir(parents=True, exist_ok=True)
            shutil.copy(ex, s / ".git" / "info" / "exclude")
        for p in paths:
            f = s / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("probe\n")
        r = git(s, "check-ignore", "--stdin", input_text="\n".join(paths) + "\n")
        return {l.strip() for l in r.stdout.splitlines() if l.strip()}


def head_text(root):
    r = git(root, "show", "HEAD:.gitignore")
    return r.stdout if r.returncode == 0 else None


def plan(root):
    """-> dict(action, text, reason, original). action ∈ keep|write|refuse|impossible."""
    gi = Path(root) / ".gitignore"
    original = gi.read_text() if gi.is_file() else ""
    stripped, had_block = strip_block(original)
    all_paths = list(WANT_TRACKED) + list(PROBES)
    base = evaluate(root, stripped, all_paths)
    blocked = [WANT_TRACKED[p] for p in WANT_TRACKED if p in base]

    if not blocked:
        body = []
    else:
        body = None
        for cand in candidates(blocked):
            got = evaluate(root, render(stripped, cand), all_paths)
            if any(p in got for p in WANT_TRACKED):
                continue
            if all((p in got) == (p in base) for p in PROBES):
                body = cand
                break
        if body is None:
            return {"action": "impossible", "original": original,
                    "reason": "no narrow block makes the managed paths trackable without "
                              "changing what else this repository ignores",
                    "text": original, "body": candidates(blocked)[-1]}

    # No block wanted and none present: leave the file byte-for-byte alone. (Rendering
    # would normalise a missing trailing newline, and a rewrite nobody needed is how a
    # project's .gitignore ends up dirty after every release.)
    if not body and not had_block:
        return {"action": "keep", "original": original, "text": original,
                "reason": "nothing to do", "body": []}
    desired = render(stripped, body)
    if desired == original:
        return {"action": "keep", "original": original, "text": original,
                "reason": "already correct", "body": body}

    # Refuse to build on anyone else's uncommitted edit. Our own block is the only
    # difference we accept between HEAD and the working copy.
    if git(root, "diff", "--cached", "--quiet", "--", ".gitignore").returncode != 0:
        return {"action": "refuse", "original": original, "text": desired,
                "reason": ".gitignore has staged changes", "body": body}
    head = head_text(root)
    if head is not None and original != head:
        if strip_block(head)[0] != stripped:
            return {"action": "refuse", "original": original, "text": desired,
                    "reason": ".gitignore holds local edits that are not the fork's block",
                    "body": body}
    return {"action": "write", "original": original, "text": desired, "body": body,
            "reason": ("repaired the fork's ignore block" if had_block
                       else "added the fork's ignore block") if body
            else "removed a fork ignore block that is no longer needed"}


def verify_real(root):
    for p in WANT_TRACKED:
        if git(root, "check-ignore", "-q", "--no-index", p).returncode == 0:
            return False, f"{p} is still ignored"
    return True, ""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--mode", choices=("check", "sync"), default="check")
    a = ap.parse_args()
    root = Path(a.root)
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return 0  # not a git repo: nothing is ignored, nothing to do
    try:
        p = plan(root)
    except RuntimeError as e:
        print(f"gitignore: could not evaluate ({e})")
        return 1
    if p["action"] == "keep":
        return 0
    if p["action"] in ("refuse", "impossible"):
        print(f"gitignore: {p['reason']}")
        if p.get("body"):
            print("gitignore: the lines that would make the fork guards trackable:")
            for line in [MARK] + p["body"]:
                print(f"  {line}")
        return 1
    if a.mode == "check":
        print(f"gitignore: would rewrite ({p['reason']})")
        return 3
    gi = root / ".gitignore"
    gi.write_text(p["text"])
    ok, why = verify_real(root)
    if not ok:
        if p["original"]:
            gi.write_text(p["original"])
        else:
            gi.unlink(missing_ok=True)
        print(f"gitignore: rewrite did not verify ({why}); original restored")
        return 1
    print(f"gitignore: {p['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
