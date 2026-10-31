#!/usr/bin/env python3
"""Golden cases for claude-md-admission-gate.py.

MOST OF THESE ASSERT SILENCE, and the weighting is the point rather than a style choice.
CLAUDE.md is edited constantly — 79 commits have touched it — and 49 of those added no section
heading at all. A gate that spoke on ordinary editing would be switched off inside a week, and
this repository has catalogued four mechanisms that died exactly that way
(docs/specs/context-capture-and-delivery.md).

THE THREE CASES THAT MATTER MOST ARE SILENT ONES, and each is a real edit from this file's
history rather than an invention:

  * the ONE-ROW addition to the MCP cheat-sheet table — one line, thousands of characters
  * the row REWRITE — 7,142 characters added and 5,990 removed in ONE line (commit 7566aa7),
    the largest single edit the file has ever received
  * the one-character count correction (commit c56df5b, "fifty-nine" -> "sixty-two")

Any size-based trigger low enough to catch the smallest genuine new section (917 characters)
fires on all three. That is why the trigger is the heading.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("claude-md-admission-gate.py")

# A realistic stand-in: a couple of sections, a table, and a fenced block.
BASE = """# Amazon Removal Assistant

Some preamble about what this repo is.

## MCP Tool Cheat Sheet

| Lane | Start here | Then |
|---|---|---|
| `pallet_` | **`pallet_status`** — where the pilot is | `pallet_cost` (what it costs) |
| `prep_` | **`prep_refresh_lot_list`** | `prep_tag_flagged_inbounds` (writes) |

## A record id is not an answer

Never name a record without saying what it is.

## Google Sheets Access

The shared sheet id is `1zWEL`.
"""


def workspace(tmp: Path, name: str = "proj") -> Path:
    """A directory the gate will recognise as a project root: CLAUDE.md beside a package.json,
    with a .claude/ alongside. Mirrors the real repo and a real worktree, both of which were
    checked against the live paths on 2026-09-17."""
    root = tmp / name
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text("{}", encoding="utf-8")
    (root / "CLAUDE.md").write_text(BASE, encoding="utf-8")
    return root


def run(payload: dict) -> str:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert proc.returncode == 0, f"hook must always exit 0, got {proc.returncode}: {proc.stderr}"
    return proc.stdout.strip()


def verdict(payload: dict) -> str:
    """'silent', 'notice' or 'ask'."""
    out = run(payload)
    if not out:
        return "silent"
    body = json.loads(out)["hookSpecificOutput"]
    assert body["hookEventName"] == "PreToolUse"
    decision = body.get("permissionDecision")
    if decision == "ask":
        # AN ASK NOW HAS TWO CAUSES and the assertion has to name both, or closing the shell
        # hole would have "passed" by silently weakening what an ask is allowed to say.
        # RUNAWAY is the measured tier; CANNOT MEASURE is the scripted one, which is an ask
        # precisely BECAUSE no measurement stands behind it.
        reason = body["permissionDecisionReason"]
        assert "RUNAWAY" in reason, reason
        assert "CLAUDE.md" in reason, reason
        return "ask"
    assert decision == "allow", f"unexpected decision {decision!r} — this hook must never deny"
    assert "ADMISSION" in body["additionalContext"]
    return "notice"


def edit(path: Path, old: str, new: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": str(path), "old_string": old, "new_string": new}}


def write(path: Path, content: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}}


# A real cheat-sheet row: one line, and very long. Shortened here but the same shape.
LONG_ROW = (
    "| `amazon_` — Amazon's own inbound plan | **`amazon_inbound_plan`** — builds the Amazon "
    "side of the pallet over Fulfillment Inbound v2024-03-20, far enough to learn the "
    "destination fulfilment centre and the freight rate, and stops. Steps 6 and 8 are refused "
    "BY CONSTRUCTION rather than skipped. Dry run is the default. | **`amazon_declare_freight`** "
    "(tells Amazon the carrier's bill of lading and freight bill on a pallet moving with a "
    "carrier Amazon did not book; it records rather than commits, reads before it writes "
    "because the PUT replaces the whole tracking block, and a write is never retried) |"
) * 3


def build_cases(tmp: Path):
    root = workspace(tmp)
    md = root / "CLAUDE.md"
    cases = []

    # ---------- MUST NOTICE: a new section is being admitted ----------
    cases.append((
        "a new ## section",
        edit(md, "## Google Sheets Access", "## A brand new rule\n\nDo the thing.\n\n## Google Sheets Access"),
        "notice",
    ))
    cases.append((
        "a new ### subsection (7 of 37 firing commits arrived this way)",
        edit(md, "Never name a record", "### The sharper instance\n\nSay which one.\n\nNever name a record"),
        "notice",
    ))
    cases.append((
        "Write of the whole file with one section added",
        write(md, BASE + "\n## Another rule\n\nBody.\n"),
        "notice",
    ))
    cases.append((
        "MultiEdit where one of the edits adds a heading",
        {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(md),
                "edits": [
                    {"old_string": "Some preamble", "new_string": "Some amended preamble"},
                    {"old_string": "## Google Sheets Access", "new_string": "## New lane\n\nBody.\n\n## Google Sheets Access"},
                ],
            },
        },
        "notice",
    ))
    cases.append((
        "a SECOND section carrying a title the file already has",
        edit(md, "## Google Sheets Access", "## A record id is not an answer\n\nAgain.\n\n## Google Sheets Access"),
        "notice",
    ))
    cases.append((
        "a stale old_string that cannot be replayed but still adds a heading",
        edit(md, "text that is not in the file", "## Smuggled in\n\nBody.\n"),
        "notice",
    ))

    # ---------- MUST ASK: a bulk addition no edit in 79 commits has matched ----------
    cases.append((
        "13,244+ net characters pasted inside an existing section",
        edit(md, "The shared sheet id is `1zWEL`.", "The shared sheet id is `1zWEL`.\n\n" + ("Procedure paragraph. " * 700)),
        "ask",
    ))
    cases.append((
        "a Write that balloons the file past the runaway ceiling",
        write(md, BASE + "\n" + ("More resident procedure. " * 600)),
        "ask",
    ))

    # ---------- MUST BE SILENT: ordinary editing, which is nearly all editing ----------
    cases.append((
        "the one-row cheat-sheet addition the brief named",
        edit(md, "| `prep_` | **`prep_refresh_lot_list`** | `prep_tag_flagged_inbounds` (writes) |",
             "| `prep_` | **`prep_refresh_lot_list`** | `prep_tag_flagged_inbounds` (writes) |\n" + LONG_ROW),
        "silent",
    ))
    cases.append((
        "the largest edit in the file's history: a one-line row REWRITE (7566aa7)",
        edit(md, "| `pallet_` | **`pallet_status`** — where the pilot is | `pallet_cost` (what it costs) |", LONG_ROW),
        "silent",
    ))
    cases.append((
        "a one-character count correction (c56df5b, fifty-nine -> sixty-two)",
        edit(md, "Some preamble about what this repo is.", "Some preamble about what this repo was."),
        "silent",
    ))
    cases.append((
        "a typo fix",
        edit(md, "Never name a record", "Never name a recod"),
        "silent",
    ))
    cases.append((
        "expanding an existing rule by a paragraph, no new heading",
        edit(md, "Never name a record without saying what it is.",
             "Never name a record without saying what it is. " + ("The identifier goes at the end. " * 30)),
        "silent",
    ))
    cases.append((
        "MOVING a section — removed and re-added, so nothing is admitted",
        edit(md, "## A record id is not an answer\n\nNever name a record without saying what it is.\n\n## Google Sheets Access",
             "## Google Sheets Access\n\n## A record id is not an answer\n\nNever name a record without saying what it is.\n"),
        "silent",
    ))
    cases.append((
        "DELETING a section",
        edit(md, "## Google Sheets Access\n\nThe shared sheet id is `1zWEL`.\n", ""),
        "silent",
    ))
    cases.append((
        "a ## heading inside a fenced example block",
        edit(md, "Some preamble about what this repo is.",
             "Some preamble.\n\n```\n## Not a real section\n\nAn example of the shape.\n```\n"),
        "silent",
    ))
    cases.append((
        "a #### heading — below the declared scope of ## and ###",
        edit(md, "Some preamble about what this repo is.", "Some preamble.\n\n#### A deep sub-part\n"),
        "silent",
    ))
    cases.append((
        "'##' appearing inline in prose rather than at line start",
        edit(md, "Some preamble about what this repo is.", "Some preamble mentioning ## as a literal."),
        "silent",
    ))

    # ---------- MUST BE SILENT: not this file ----------
    other = tmp / "elsewhere"
    other.mkdir(parents=True, exist_ok=True)
    cases.append((
        "a docs/ page gaining a section",
        edit(other / "policy.md", "x", "## A new section\n\nBody."),
        "silent",
    ))
    cases.append((
        "the GLOBAL ~/.claude/CLAUDE.md — explicitly not ours to police",
        edit(Path.home() / ".claude" / "CLAUDE.md", "x", "## A new global rule\n\nBody."),
        "silent",
    ))
    cases.append((
        "the workspace /Users/masonwood/code/CLAUDE.md",
        edit(Path("/Users/masonwood/code/CLAUDE.md"), "x", "## A new workspace rule\n\nBody."),
        "silent",
    ))
    bare = tmp / "bare"
    bare.mkdir(parents=True, exist_ok=True)
    (bare / "CLAUDE.md").write_text(BASE, encoding="utf-8")
    cases.append((
        "a CLAUDE.md with no package.json beside it — not a project root",
        edit(bare / "CLAUDE.md", "x", "## A new rule\n\nBody."),
        "silent",
    ))

    # ---------- MUST BE SILENT: not a write tool ----------
    cases.append((
        "Read of CLAUDE.md",
        {"tool_name": "Read", "tool_input": {"file_path": str(md)}},
        "silent",
    ))
    # ---------- SCRIPTED WRITES: the hole this file used to assert, now closed ----------
    #
    # This case read "silent" until 2026-09-18 and was correct: the matcher was Edit|Write|
    # MultiEdit and a shell write went straight past it. A cold-session test that day put
    # 20,725 characters into CLAUDE.md through a python splice with every tier quiet, so the
    # assertion was flipped rather than the hole being re-documented. The ceiling cannot be
    # applied to a scripted write — the content is computed while the command runs — so this
    # is an ask that says so, never a measurement.
    cases.append((
        "a Bash sed against CLAUDE.md — the hole closed 2026-09-18",
        {"tool_name": "Bash", "tool_input": {"command": f"sed -i '' 's/x/y/' {md}"}},
        "ask",
    ))
    cases.append((
        "a python splice through the shell — the exact shape that got 20,725 chars through",
        {"tool_name": "Bash", "tool_input": {"command":
            f"python3 - <<'PY'\nimport pathlib\n"
            f"p = pathlib.Path({str(md)!r})\np.write_text(p.read_text() + '## New\\n')\nPY"}},
        "ask",
    ))
    cases.append((
        "a heredoc redirected over CLAUDE.md",
        {"tool_name": "Bash", "tool_input": {"command": f"cat > {md} <<'EOF'\n# x\nEOF"}},
        "ask",
    ))
    cases.append((
        "an append redirect",
        {"tool_name": "Bash", "tool_input": {"command": f"echo '## New rule' >> {md}"}},
        "ask",
    ))
    cases.append((
        "tee into CLAUDE.md",
        {"tool_name": "Bash", "tool_input": {"command": f"printf '## x' | tee {md}"}},
        "ask",
    ))
    cases.append((
        "a relative path from inside the project root",
        {"tool_name": "Bash", "tool_input": {"command": "sed -i '' 's/a/b/' ./CLAUDE.md"},
         "cwd": str(md.parent)},
        "ask",
    ))

    # ---------- MUST BE SILENT: reads of CLAUDE.md through the shell ----------
    #
    # This matcher now sees EVERY Bash call in the session, so these are the cases that decide
    # whether it survives contact with ordinary work. A read of CLAUDE.md outnumbers a write by
    # orders of magnitude, and a gate that spoke on `grep` would be switched off in a week.
    for label, command in (
        ("cat", f"cat {md}"),
        ("grep", f"grep -c CRITICAL {md}"),
        ("wc", f"wc -c {md}"),
        ("head", f"head -40 {md}"),
        ("sed -n, a PRINT not an in-place edit", f"sed -n '1,45p' {md}"),
        ("a revision read piped into a counter", f"git show origin/main:CLAUDE.md | wc -c"),
        ("a write to a DIFFERENT file that merely mentions CLAUDE.md",
         f"echo 'see CLAUDE.md' > notes.txt"),
        ("sed -i against an unrelated file, CLAUDE.md only named in a message",
         "sed -i '' 's/x/y/' README.md && echo 'now update CLAUDE.md by hand'"),
    ):
        cases.append((f"shell read of CLAUDE.md — {label}",
                      {"tool_name": "Bash", "tool_input": {"command": command}}, "silent"))

    # The global and workspace files stay out of scope under the shell path too, the same way
    # they do under Edit — by marker, not by path. Neither has a package.json beside it.
    cases.append((
        "a scripted write to the GLOBAL ~/.claude/CLAUDE.md",
        {"tool_name": "Bash", "tool_input":
            {"command": "python3 -c \"open('/Users/masonwood/.claude/CLAUDE.md','a').write('x')\""}},
        "silent",
    ))
    cases.append((
        "a Bash call with no command at all",
        {"tool_name": "Bash", "tool_input": {}},
        "silent",
    ))
    cases.append((
        "Grep over CLAUDE.md",
        {"tool_name": "Grep", "tool_input": {"pattern": "## ", "path": str(md)}},
        "silent",
    ))
    cases.append((
        "an Edit with no file_path at all",
        {"tool_name": "Edit", "tool_input": {"old_string": "a", "new_string": "## b"}},
        "silent",
    ))
    cases.append((
        "an Edit whose payload is not a dict",
        {"tool_name": "Edit", "tool_input": "nonsense"},
        "silent",
    ))
    return cases


def main() -> int:
    failures = []
    cases = []
    tmp = Path(tempfile.mkdtemp(prefix="claude-md-admission-"))
    try:
        cases = build_cases(tmp)
        for name, payload, expected in cases:
            try:
                actual = verdict(payload)
            except AssertionError as exc:
                failures.append(f"{name}: {exc}")
                continue
            if actual != expected:
                failures.append(f"{name}: expected {expected}, got {actual}")

        # A malformed payload must be a silent no-op, never a crash that blocks an edit.
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=20
        )
        if proc.returncode != 0 or proc.stdout.strip():
            failures.append("malformed payload: expected a silent exit 0")

        # No stdin at all — the shape a misconfigured wiring produces.
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input="", capture_output=True, text=True, timeout=20
        )
        if proc.returncode != 0 or proc.stdout.strip():
            failures.append("empty stdin: expected a silent exit 0")

        total = len(cases) + 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures:
        print("FAIL:", f)
    silent = sum(1 for c in cases if c[2] == "silent") + 2  # + the two malformed-input cases
    print(f"{total - len(failures)}/{total} cases passed  ({silent} of them assert SILENCE)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
