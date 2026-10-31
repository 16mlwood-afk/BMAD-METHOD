#!/usr/bin/env python3
"""A compacted or opted-out project CLAUDE.md is byte-identical after --sync and --check is clean."""
import subprocess
import sys
import tempfile
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
SCRIPT = FORK / "sync-claudemd-sections.py"
TEMPLATE = FORK / "src/modules/bmm/_module-installer/assets/CLAUDE.md.template"

PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else f"\n          got={got!r} want={want!r}"))


def run(mode, path):
    return subprocess.run([sys.executable, str(SCRIPT), mode, str(TEMPLATE), str(path)],
                          capture_output=True, text=True)


BASE = "# Proj\n\n## Agent Behavior Rules\n\n### ALWAYS Use Worktrees\nx\n"
CASES = {
    "compacted (archive pointer)": BASE + "\nFull text: docs/claude-md-archive/old.md\n",
    "explicit marker": BASE + "\n<!-- bmad:claudemd-sync off -->\n",
}

print("claudemd-sync opt-out cases:\n")
with tempfile.TemporaryDirectory() as d:
    for name, text in CASES.items():
        f = Path(d) / "CLAUDE.md"
        f.write_text(text)
        before = f.read_bytes()
        r = run("--sync", f)
        check(f"{name}: --sync exits 0, no stdout", (r.returncode, r.stdout), (0, ""))
        check(f"{name}: file byte-identical after --sync", f.read_bytes(), before)
        r = run("--check", f)
        check(f"{name}: --check reports nothing missing", (r.returncode, r.stdout), (0, ""))

    # Control: an ordinary project still gets missing sections (default behaviour unchanged).
    f = Path(d) / "plain.md"
    f.write_text(BASE)
    r = run("--sync", f)
    check("control: ordinary project still receives sections", f.read_text() != BASE and r.stdout != "", True)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
