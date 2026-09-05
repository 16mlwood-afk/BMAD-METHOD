#!/usr/bin/env python3
"""Catch the distributor defect class that syntax checks and unit tests both miss.

WHY THIS EXISTS. Three distributor defects shipped on 2026-08-31 and every one was a
RUNTIME path, not a syntax error: a blanket `git add` that committed deletions, a refresh
that ran only on one delivery path, and a block pasted into the target loop that referenced
`$proot` when that loop's variable is `$project_root`. The last one aborted the sync for all
fourteen targets under `set -u`, and its visible output was three green OK lines followed by
a non-zero exit — success-looking output on a failed run.

`bash -n` cannot catch it: the syntax is valid. A unit test cannot catch it without actually
executing the loop against a target. So this checks the one thing that is statically decidable
and was actually wrong — that a variable used inside a block is bound in the scope that block
lives in.

Deliberately narrow. It reads the target loop only, and only flags a `$var` that appears
nowhere as an assignment or `local` in that same scope. A false positive here is cheap (rename
or assign); a false negative is a fleet-wide outage.
"""
import re
import sys
from pathlib import Path

SYNC = Path(__file__).resolve().parent.parent / "sync-bmad-workflows.sh"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail and not cond else ''}")


def main():
    src = SYNC.read_text()
    lines = src.splitlines()

    # S1 — the file must parse. Cheap, and it is the floor.
    import subprocess
    r = subprocess.run(["bash", "-n", str(SYNC)], capture_output=True, text=True)
    check("S1 the distributor parses", r.returncode == 0, r.stderr.strip()[:120])

    # S2 — the target loop must not reference a variable it never binds.
    #
    # The loop is the one reading the targets file. Everything from its `while` to the
    # matching `done < "$TARGETS_FILE"` is one scope; a `local` from some other function is
    # not in it, however similar the name.
    start = next((i for i, l in enumerate(lines)
                  if re.search(r"^while IFS=.*read -r target", l)), None)
    end = next((i for i, l in enumerate(lines[start or 0:], start or 0)
                if re.search(r'^done < "\$TARGETS_FILE"', l)), None) if start is not None else None
    check("S2a the target loop is locatable", start is not None and end is not None,
          f"start={start} end={end}")
    if start is None or end is None:
        return finish()

    body = lines[start:end]
    text = "\n".join(body)

    # Strip single-quoted spans and comments before looking for shell variables. An embedded
    # jq program is full of `$b`, `$t`, `$tn` that are jq's, not the shell's, and a comment
    # that NAMES the bug ("this loop uses $project_root") would otherwise report it as one.
    # Per LINE, not across the file: a lone apostrophe in prose would otherwise pair with a
    # quote hundreds of lines away and swallow every assignment between them, which reports
    # real, correctly-bound variables as unbound.
    text = "\n".join(re.sub(r"'[^'\n]*'", "''", re.sub(r"#.*$", "", l))
                     for l in text.splitlines())

    bound = set(re.findall(r"^\s*(?:local\s+|declare\s+\w*\s+)?([A-Za-z_]\w*)=", text, re.M))
    bound |= set(re.findall(r"for\s+([A-Za-z_]\w*)\s+in", text))
    bound |= set(re.findall(r"read -r\s+([A-Za-z_]\w*)", text))
    # Globals assigned anywhere above the loop, plus the environment, are legitimately in scope.
    above = "\n".join(lines[:start])
    bound |= set(re.findall(r"^\s*(?:readonly\s+|export\s+)?([A-Za-z_]\w*)=", above, re.M))
    bound |= set(re.findall(r"^\s*([A-Za-z_]\w*)\(\)", above, re.M))
    bound |= {"HOME", "PATH", "PWD", "IFS", "BASH_SOURCE", "FUNCNAME", "PIPESTATUS", "RANDOM"}

    used = set(re.findall(r'\$\{?([A-Za-z_]\w*)', text))
    unbound = sorted(u for u in used - bound if not u.isupper())

    check("S2b every variable the target loop uses is bound in a scope it can see",
          not unbound, f"unbound: {unbound}")

    # S3 — the regression that motivated this file, named so it cannot come back quietly.
    check("S3 the shared-policy refresh in the target loop uses the loop's own root variable",
          not re.search(r'\$proot/_bmad/bmad-shared', text),
          "$proot is a local of the per-project helpers, not of the target loop; "
          "under set -u it aborts the run for every target")

    return finish()


def finish():
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
