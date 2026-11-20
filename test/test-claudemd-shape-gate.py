#!/usr/bin/env python3
"""Golden cases for the project CLAUDE.md commit gate and its SessionStart stale-stamp warning.

    python3 test/test-claudemd-shape-gate.py

Gate under test: custom/githooks/check-claude-md-shape.sh, registered by
custom/githooks/gates.d/claude-md-shape.conf and run by custom/githooks/pre-commit. Every case builds a real
temp git repository, installs the fork's pre-commit dispatcher + gate + drop-in as .githooks/, points
core.hooksPath at it and runs a real `git commit`, so git invokes the hook exactly as it does in a project.
Nothing here calls a function. SessionStart cases run check-claude-md-drift.sh as the harness does.

The rules themselves live in ~/.claude/scripts/claude-md-sweep/claude-md-tag-check.py (the gate calls it).
Expected answers come from the owner's ruling of 10 Nov 2026 and its approved shape (record
~/.claude/docs/decisions/2026-11-10-claude-md-legacy-content-across-projects.md § The shape; five blocks).
If that script is absent the suite says SKIPPED (NOT PASSED) and exits 0, loudly: a green over nothing is a lie.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
GITHOOKS = FORK / "custom" / "githooks"
DRIFT = FORK / "check-claude-md-drift.sh"
CHECKER = Path(os.environ.get("CLAUDE_MD_SWEEP_CHECKER", Path.home() / ".claude/scripts/claude-md-sweep/claude-md-tag-check.py"))

LONG_RULE = "never approve a command carrying an inline secret as a saved always allow permission before refactoring it"
GLOBAL = (
    "# Global\n\n## Production Safety [G-PROD]\n### Before destructive database operations [G-PROD-DB]\n"
    "### Secrets [G-SEC]\n\n" + LONG_RULE + ".\n"
)

STAMP = date(2026, 11, 10)
GOOD = """# CLAUDE.md

Swept on 10 Nov 2026.

## 1. What this project is
Tag: FACT

One line about the project.

## 2. Data, production and deploy

### The database is production
Tag: FACT

Facts.

## 3. Domain facts

### A business rule
Tag: FACT

Rule.

## 4. Stricter rules

### Migrations
Tag: STRICTER(G-PROD-DB: merging a migration file runs it on deploy here)

Body.

## 5. Pointers

### Where things are
Tag: POINTER

`docs/x.md`.
"""
UNSWEPT = GOOD.replace("Swept on 10 Nov 2026.", "Not yet swept.")


def git(repo: Path, *args: str, env=None) -> subprocess.CompletedProcess:
    base = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    base.pop("CLAUDE_MD_PROJECT_SHAPE_OVERRIDE", None)
    base.update(env or {})
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=base)


def make_repo(tmp: Path, name: str) -> Path:
    repo = tmp / name
    (repo / ".githooks" / "gates.d").mkdir(parents=True)
    git(repo, "init", "-q")
    shutil.copy(GITHOOKS / "pre-commit", repo / ".githooks" / "pre-commit")
    shutil.copy(GITHOOKS / "check-claude-md-shape.sh", repo / ".githooks" / "check-claude-md-shape.sh")
    shutil.copy(GITHOOKS / "gates.d" / "claude-md-shape.conf", repo / ".githooks" / "gates.d" / "claude-md-shape.conf")
    (repo / ".githooks" / "pre-commit").chmod(0o755)
    git(repo, "config", "core.hooksPath", ".githooks")
    (repo / "README.md").write_text("x\n")
    git(repo, "add", "README.md")
    # the very first commit has no CLAUDE.md, so the gate must be silent here too
    git(repo, "commit", "-q", "-m", "init")
    return repo


def commit_claude_md(tmp: Path, name: str, text: str, env=None, global_text: str | None = GLOBAL):
    """Stage `text` as CLAUDE.md and run a real git commit. Returns (exit code, stderr, repo)."""
    repo = make_repo(tmp, name)
    g = tmp / f"{name}-global.md"
    if global_text is not None:
        g.write_text(global_text)
    e = {"CLAUDE_MD_GLOBAL_FILE": str(g), "CLAUDE_MD_SWEEP_CHECKER": str(CHECKER),
         "CLAUDE_MD_SHAPE_OVERRIDE_LOG": str(tmp / f"{name}-overrides.jsonl")}
    e.update(env or {})
    (repo / "CLAUDE.md").write_text(text)
    git(repo, "add", "CLAUDE.md")
    r = git(repo, "commit", "-m", "change CLAUDE.md", env=e)
    return r.returncode, r.stdout + r.stderr, repo


RESULTS: list[tuple[str, bool, str]] = []


def expect(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f"\n       {detail[-400:]}"))


def gate_cases(tmp: Path) -> None:
    code, out, _ = commit_claude_md(tmp, "g1", GOOD)
    expect("swept + green allows, silent", code == 0 and "claude-md shape" not in out.lower() and "REFUSED" not in out, out)

    code, out, _ = commit_claude_md(tmp, "g2", GOOD.replace("### A business rule\nTag: FACT\n", "### A business rule\n"))
    expect("swept + untagged section refuses, names T1", code != 0 and "REFUSED" in out and "T1" in out and "Fix:" in out, out)

    code, out, _ = commit_claude_md(tmp, "g3", GOOD.replace("G-PROD-DB", "G-NOPE-9"))
    expect("swept + STRICTER unknown G-id refuses, names the id", code != 0 and "T2" in out and "G-NOPE-9" in out, out)

    code, out, _ = commit_claude_md(tmp, "g4", GOOD.replace("Body.", "Body. " + " ".join(LONG_RULE.split()[:12])))
    expect("swept + 12 copied words refuses, names C1", code != 0 and "C1" in out, out)

    code, out, _ = commit_claude_md(tmp, "g4b", GOOD.replace("Body.", "Body. " + " ".join(LONG_RULE.split()[:11])))
    expect("swept + 11 copied words allows (boundary)", code == 0, out)

    swapped = (GOOD.replace("## 2. Data, production and deploy", "@@").replace("## 3. Domain facts", "## 2. Data, production and deploy")
               .replace("@@", "## 3. Domain facts"))
    code, out, _ = commit_claude_md(tmp, "g5", swapped)
    expect("swept + blocks out of order refuses, names B1", code != 0 and "B1" in out, out)

    code, out, _ = commit_claude_md(tmp, "g5b", GOOD.replace("## 5. Pointers", "## 5. Behaviour"))
    expect("swept + a behaviour block refuses, names B1", code != 0 and "B1" in out, out)

    code, out, _ = commit_claude_md(tmp, "g6", UNSWEPT)
    expect("unswept warns and allows, points at the method doc",
           code == 0 and "UNSWEPT" in out and "claude-md-sweep-method.md" in out and "REFUSED" not in out, out)

    code, out, _ = commit_claude_md(tmp, "g6b", "# Old style project file\n\nplain prose, no headings tagged\n")
    expect("unswept free-form file warns and allows", code == 0 and "UNSWEPT" in out, out)

    code, out, _ = commit_claude_md(tmp, "g7", GOOD.replace("G-PROD-DB", "G-NOPE-9"), global_text=None)
    expect("global file unreadable -> COULD NOT CHECK printed, commit allowed",
           code == 0 and "CLAUDE.md shape: COULD NOT CHECK" in out, out)

    code, out, _ = commit_claude_md(tmp, "g7b", GOOD.replace("G-PROD-DB", "G-NOPE-9"), env={"CLAUDE_MD_SWEEP_CHECKER": str(tmp / "nope.py")})
    expect("checker script missing -> COULD NOT CHECK printed, commit allowed",
           code == 0 and "CLAUDE.md shape: COULD NOT CHECK" in out, out)

    bad = GOOD.replace("### A business rule\nTag: FACT\n", "### A business rule\n")
    code, out, repo = commit_claude_md(tmp, "g8", bad, env={"CLAUDE_MD_PROJECT_SHAPE_OVERRIDE": "sweeping this file in the next commit, owner aware"})
    log = tmp / "g8-overrides.jsonl"
    rec = json.loads(log.read_text().splitlines()[-1]) if log.exists() and log.read_text().strip() else {}
    expect("override (12+ chars) allows and appends a JSON line",
           code == 0 and "OVERRIDDEN" in out and "sweeping this file" in rec.get("reason", "") and rec.get("failures"), out + str(rec))

    code, out, _ = commit_claude_md(tmp, "g8b", bad, env={"CLAUDE_MD_PROJECT_SHAPE_OVERRIDE": "short"})
    expect("override under 12 characters does not count", code != 0 and "REFUSED" in out, out)

    # a commit not touching CLAUDE.md is silent, even though the committed CLAUDE.md is swept and bad
    repo = make_repo(tmp, "g9")
    g = tmp / "g9-global.md"
    g.write_text(GLOBAL)
    env = {"CLAUDE_MD_GLOBAL_FILE": str(g), "CLAUDE_MD_SWEEP_CHECKER": str(CHECKER),
           "CLAUDE_MD_SHAPE_OVERRIDE_LOG": str(tmp / "g9-overrides.jsonl")}
    (repo / "CLAUDE.md").write_text(bad)
    git(repo, "add", "CLAUDE.md")
    git(repo, "commit", "-q", "-m", "seed", env=dict(env, CLAUDE_MD_PROJECT_SHAPE_OVERRIDE="seeding a bad file for the test"))
    (repo / "other.txt").write_text("y\n")
    git(repo, "add", "other.txt")
    r = git(repo, "commit", "-m", "unrelated", env=env)
    out = r.stdout + r.stderr
    expect("a commit not touching CLAUDE.md is silent",
           r.returncode == 0 and "REFUSED" not in out and "UNSWEPT" not in out and "COULD NOT CHECK" not in out, out)


def session_cases(tmp: Path) -> None:
    def run(name: str, claude_md: str, days_after_stamp: int, checker: str | None = None):
        proj = tmp / name
        (proj / ".git").mkdir(parents=True)
        (proj / "CLAUDE.md").write_text(claude_md)
        today = STAMP + timedelta(days=days_after_stamp)  # one source for both sides of the date
        env = dict(os.environ, CLAUDE_MD_SWEEP_TODAY=today.isoformat(), CLAUDE_MD_SWEEP_CHECKER=checker or str(CHECKER))
        r = subprocess.run(["bash", str(DRIFT)], cwd=proj, capture_output=True, text=True, env=env)
        return r.returncode, r.stdout

    code, out = run("s91", GOOD, 91)
    expect("SessionStart: stamp 91 days old warns (names the method doc)",
           code == 0 and "STALE" in out and "91 days" in out and "claude-md-sweep-method.md" in out, out)
    code, out = run("s90", GOOD, 90)
    expect("SessionStart: stamp exactly 90 days old is silent", code == 0 and out.strip() == "", out)
    code, out = run("s30", GOOD, 30)
    expect("SessionStart: stamp 30 days old is silent", code == 0 and out.strip() == "", out)
    code, out = run("s91b", GOOD, 91)
    code2, out2 = run("s91c", GOOD, 91)
    expect("SessionStart: repeats on the next session while still stale", "STALE" in out and "STALE" in out2)
    code, out = run("sunswept", UNSWEPT, 400)
    expect("SessionStart: an unswept file gets no stale warning", code == 0 and "STALE" not in out, out)
    code, out = run("snochecker", GOOD, 400, checker=str(tmp / "missing.py"))
    expect("SessionStart: stamp present but checker missing -> COULD NOT CHECK", code == 0 and "COULD NOT CHECK" in out, out)
    code, out = run("sbaddate", GOOD.replace("Swept on 10 Nov 2026.", "Swept on the tenth."), 400)
    expect("SessionStart: unreadable stamp date -> COULD NOT CHECK", code == 0 and "COULD NOT CHECK" in out, out)


def main() -> int:
    if not CHECKER.exists():
        print(f"SKIPPED (NOT PASSED): checker {CHECKER} not found, so the gate cannot be exercised on this machine.")
        return 0
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        print("commit gate (real git commit through .githooks/pre-commit):")
        gate_cases(tmp)
        print("SessionStart stale stamp:")
        session_cases(tmp)
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
