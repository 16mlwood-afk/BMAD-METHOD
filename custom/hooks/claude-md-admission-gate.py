#!/usr/bin/env python3
"""PreToolUse: put the admission test in front of a session ADDING a section to CLAUDE.md.

WHY. Owner instruction, 2026-09-17: *"we need something to police the Claude.md and sort of
stop hook it whatever it might be to prevent stuff being added without it meeting certain
requirements."*

The file is 194,166 characters — 195,595 bytes — across 57 sections. With the global and the
workspace instruction files it comes to 333,255 bytes, roughly 83,000 tokens loaded before a
word of conversation, on every turn, across the eleven sessions this repository runs at once.
Nothing has ever asked whether a new section earned that.

THE RULE BOOK IS docs/claude-md-admission-policy.md AND THIS FILE IS NOT A SECOND COPY OF IT.
This hook checks the two things a machine can check — a new section heading, and runaway
growth in one edit. Whether the rule is DURABLE, whether a cheaper surface would deliver it in
time, whether it has gone stale: none of that is machine-knowable and this file does not
pretend otherwise.

THE DISCRIMINATOR IS THE HEADING, NOT THE SIZE, AND THAT IS MEASURED. Across the 79 commits
that have touched CLAUDE.md, 49 added no section heading and 30 added a `## ` (7 more a
`### `). The 49 include the LARGEST single edits the file has ever received — 7,142 characters
(7566aa7) and 5,847 (95beb33), each a ONE-LINE rewrite of a row in the MCP cheat-sheet table.
A size trigger low enough to catch the smallest genuine new section (917 characters) would have
fired on about thirty of those forty-nine. So size is the wrong trigger and the heading is the
right one, and the numbers rather than an opinion are why.

IT JUDGES THE DELTA, NEVER THE TOTAL. The file is over budget TODAY, so a check on total size
would fire on every edit forever — the indiscriminate-gate anti-pattern. The budget appears in
the message as CONTEXT, never as a trigger. The delta-only principle is borrowed from
~/.claude/hooks/policy-change-gate.py G3b, which never examines legacy untouched wiring for
exactly this reason.

WHY A PreToolUse HOOK AND NOT A TEST OR A PRE-COMMIT CHECK. The same argument policy-change-gate
makes about the global control plane holds here unchanged: THE LIVE INSTRUCTION FILE IS THE
WORKING TREE. CLAUDE.md is loaded from disk, not from a commit, and claude-md-drift.py pushes an
uncommitted change into every running session on its next prompt. A commit-time check would pass
a session that has already been instructed by the new text. The write is the moment.

WHAT WIDENING THE MATCHER TO Bash COSTS, STATED RATHER THAN DISCOVERED. This hook now runs on
EVERY shell call in the session, not only on a file edit, so it spawns a python interpreter a few
hundred times a day for a check that answers "no" almost every time. That is the price of the
coverage and it is paid whether or not CLAUDE.md is involved. Two things keep it honest: the
first test is a substring check for "CLAUDE.md" and returns immediately when it fails, and 30 of
the 44 golden cases assert SILENCE, over half of them ordinary shell reads of the file. If the
latency is ever felt, the fix is a cheaper pre-filter in the wiring, NOT narrowing the matcher
back — the hole this closes was measured, not theorised.

TIERS, HONESTLY.
  Tier 1 NOTICE  — a new `## ` or `### ` heading -> additionalContext, permissionDecision
                   "allow". DETERMINISTIC DELIVERY, PROBABILISTIC COMPLIANCE. It NEVER blocks.
                   claude-md-drift.py argues at length in its own header that a hook
                   interrupting a routine CLAUDE.md edit gets switched off, and names the three
                   mechanisms in this repository that died that way. This inherits that ruling.
  Tier 2 ASK     — net growth in ONE edit above RUNAWAY_NET_CHARS -> permissionDecision "ask".
                   Measured: it would have fired on NONE of the 79 recorded commits.

WHY TIER 2 ASKS AND DOES NOT DENY. Denying would put a machine in front of the owner's own
instruction file — a machine that cannot read whether 13,000 characters are warranted. He can,
in one keystroke. And per ~/.claude/CLAUDE.md, his approval IS the escape hatch on an approval
gate: "such a gate needs no env override, and adding one would be a lever whose only purpose is
to route around a decision he can already make." THERE IS NO OVERRIDE AND ITS ABSENCE IS NOT A
DEFECT.

WHAT IT CANNOT SEE, stated rather than implied.
  - A write through Bash. `sed -i` or a heredoc against CLAUDE.md carries no file_path this
    matcher sees. Not covered, and pretending otherwise would be the worse failure.
  - Whether the section is any good. It counts headings and characters.
  - ~/.claude/CLAUDE.md and the workspace file. Deliberately out of scope — the global control
    plane is shared with every project on this machine and is not this repository's to police.

CALIBRATION. src/claude-md-admission-policy.test.ts reads BOTH this file and the policy and
fails if the numbers disagree. A gate quietly calibrated looser than its own doctrine is the
failure this whole mechanism exists to prevent, turned on itself — the fork's
validate-context-budget.js ran at 14 against a stated 10 until somebody checked.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
import sys
from collections import Counter
from pathlib import Path

# --- calibrated constants -----------------------------------------------------------------
# Every one of these is stated in docs/claude-md-admission-policy.md and asserted equal to it
# by src/claude-md-admission-policy.test.ts. Change one here without the policy, or the policy
# without this file, and the suite fails naming both.

#: Declared `##` sections, measured 2026-09-17.
SECTION_COUNT = 57
#: Median `##` section size in characters, measured 2026-09-17.
MEDIAN_SECTION_CHARS = 2181
#: SECTION_COUNT x MEDIAN_SECTION_CHARS. Frozen at that derivation, never recomputed from the
#: file: a budget recalculated from the thing it constrains is a mirror, not a budget.
BUDGET_CHARS = 124317
#: Largest net addition ever made (11,062 — commit f1d52ea) plus one median section. An
#: addition bigger than the biggest rule ever admitted, plus room for one more ordinary rule,
#: is not a rule; it is a document, and a document has a home.
RUNAWAY_NET_CHARS = 13243

POLICY = "docs/claude-md-admission-policy.md"

HEADING = re.compile(r"^(##|###) \S")

NOTICE = """\
CLAUDE.md ADMISSION — this edit adds a new section to the always-loaded instruction file.

{headings}

THE ADMISSION TEST ({policy}):
  Admit a section only if a session that does not know it would act WRONGLY before anything
  else could tell it — and if some other surface could tell it in time, that surface is the
  home, not this file.

  "Would act wrongly" means it costs money, writes into a partner's system, or makes somebody
  redo work already done. Not "would be less informed".

  "Before anything else could tell it" is the clause that gets skipped and the one that earns
  the always-loaded slot. Nearly everything in this file is important; the question is whether
  it must be resident BEFORE the session knows it needs it.

IF SOMETHING CHEAPER FIRES IN TIME, IT IS THE HOME — pick the strongest that does:
  pointer (docs/) · skill · tool description · hook · type · test
  Procedure, rationale, origin and worked examples belong at the pointer, not here. A rule a
  type or a test enforces needs one line naming the mechanism, not a section.

NAMING THE CHEAPER SURFACE AND SAYING WHY IT CANNOT CARRY THE RULE IS PART OF PASSING.
"Nowhere else would work", with no candidate named, is a fail.

STANDING: {current:,} characters against a budget of {budget:,} — over by {over:,}, {pct}% above
the budget.
This edit: {net:+,} characters. The budget is CONTEXT here, never the trigger — this fires on
a new heading, not on the file's size, so an ordinary edit stays silent.

THIS HOOK DOES NOT JUDGE WHETHER THE RULE IS WELL PLACED. It counted a heading. The test above
is yours to apply.\
"""

ASK = """\
CLAUDE.md RUNAWAY — this edit adds {net:,} net characters in one go, above the ceiling of \
{ceiling:,}.

That ceiling is the largest net addition ever made to this file (11,062) plus one median \
section (2,181). It would have fired on NONE of the 79 commits that have touched CLAUDE.md, so \
this edit is doing something no edit has done before.

An addition larger than the biggest rule ever admitted, plus room for one more ordinary rule, \
is usually not a rule — it is a document, and a document has a home: docs/, a skill, a hook, or \
a test. See {policy}.

{headings}
Standing: {current:,} characters against a budget of {budget:,}.

Approve if this really is instruction that must be resident before a session knows it needs it. \
There is no override flag — your answer is the escape hatch.\
"""


def read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return {}


def is_project_claude_md(raw: str, cwd: str | None = None) -> Path | None:
    """The project's own CLAUDE.md — the repo root's, or a worktree's copy of it.

    A worktree lives at <root>/.claude/worktrees/<name>, and ITS CLAUDE.md is the file the
    session is actually working against, so the worktree path is not unwound — the same
    decision claude-md-drift.py makes and for the same reason.

    Identified by markers rather than by a hardcoded path: the file is named CLAUDE.md and sits
    beside a package.json in a directory that also holds a .claude/. Verified 2026-09-17
    against all four real candidates on this machine — the repo root and a live worktree both
    match; ~/.claude/CLAUDE.md and /Users/masonwood/code/CLAUDE.md have no package.json and do
    not.
    """
    if not raw:
        return None
    try:
        path = Path(os.path.expanduser(raw))
        if not path.is_absolute():
            path = Path(cwd) / path if cwd else Path.cwd() / path
        path = Path(os.path.normpath(str(path)))
    except (OSError, ValueError):
        return None

    if path.name != "CLAUDE.md":
        return None

    # The global control plane is explicitly not ours to police, whatever the markers say.
    try:
        home_claude = Path.home() / ".claude"
        if path == home_claude / "CLAUDE.md" or home_claude in path.parents:
            # A project worktree lives under the PROJECT's .claude, never under HOME's, so
            # this exclusion cannot swallow the case the hook exists for.
            if str(path).startswith(str(home_claude) + os.sep):
                return None
    except (OSError, RuntimeError):
        pass

    parent = path.parent
    if (parent / "package.json").exists() and (parent / ".claude").is_dir():
        return path
    return None


def apply_edits(original: str, edits: list) -> str | None:
    """Replay Edit/MultiEdit against the text on disk. None when it cannot be replayed."""
    text = original
    for edit in edits:
        if not isinstance(edit, dict):
            return None
        old = edit.get("old_string")
        new = edit.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return None
        if old and old not in text:
            return None  # stale edit; the tool will fail on its own terms
        if old == "":
            text = text + new
        elif edit.get("replace_all"):
            text = text.replace(old, new)
        else:
            text = text.replace(old, new, 1)
    return text


def before_and_after(
    tool_name: str, tool_input: dict, target: Path
) -> tuple[str, str, bool] | None:
    """The file as it is and as this call would leave it.

    The third element says whether the pair is the WHOLE file. When an edit cannot be
    replayed — a stale `old_string` the tool is about to fail on anyway — the payloads alone
    still show a heading and a net size, but the resulting file size is not known from them,
    and the caller must not report a number it did not compute.
    """
    try:
        original = target.read_text(encoding="utf-8") if target.exists() else ""
    except OSError:
        return None

    if tool_name == "Write":
        content = tool_input.get("content")
        return (original, content, True) if isinstance(content, str) else None

    if tool_name in ("Edit", "MultiEdit"):
        if tool_name == "MultiEdit":
            edits = tool_input.get("edits")
            if not isinstance(edits, list) or not edits:
                return None
        else:
            edits = [tool_input]
        after = apply_edits(original, edits)
        if after is not None:
            return original, after, True
        old = "\n".join(str(e.get("old_string", "")) for e in edits if isinstance(e, dict))
        new = "\n".join(str(e.get("new_string", "")) for e in edits if isinstance(e, dict))
        return old, new, False

    return None


FENCE = re.compile(r"^\s*(```|~~~)")


def strip_fenced(text: str) -> str:
    """Drop fenced blocks before looking for headings.

    A `## ` inside a worked example is not a section — and a session writing this policy's own
    examples, or quoting a CLAUDE.md section to discuss it, would otherwise trip the gate on an
    edit that admits nothing. The same stripping that ~/.claude/hooks/delegation-card-guard.py
    does so that a prompt discussing its rule stays silent.
    """
    out, inside = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def new_headings(before: str, after: str) -> list[str]:
    """Heading lines present after and not before.

    Counted rather than set-differenced, so a second section carrying an existing title is
    still seen as new — and so that MOVING a section (one removed, the same one added) is
    correctly silent, because a move admits nothing.
    """

    def headings(text: str) -> Counter:
        return Counter(l.rstrip() for l in strip_fenced(text).split("\n") if HEADING.match(l))

    added = headings(after) - headings(before)
    return sorted(added.elements())


#: WHERE A FIRING IS RECORDED. Added 2026-09-18 after a cold-session test could not establish
#: whether this gate had fired at all: the control probe wrote a well-formed section, and the
#: only evidence it had been told to was that the section looked like the notice asked for.
#: A guard that leaves no trace cannot be audited, which is the same defect the eviction ledger
#: closes one level up. It lives outside the repo because it is telemetry about sessions rather
#: than a record of business fact — the convention ~/.claude/logs/ already holds.
LOGFILE = Path.home() / ".claude" / "logs" / "claude-md-admission.jsonl"


def log_fire(tier: str, **fields) -> None:
    """One line per firing. NEVER raises — a guard that crashes an edit is worse than one that
    misses it, and that goes double for its own bookkeeping."""
    try:
        LOGFILE.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tier": tier,
            "session": os.environ.get("CLAUDE_SESSION_ID", ""),
            "cwd": os.getcwd(),
        }
        row.update(fields)
        with LOGFILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:
        return


#: A WRITE THIS HOOK COULD NOT SEE THROUGH ITS OWN MATCHER. Measured 2026-09-18: an agent asked
#: to add a section took CLAUDE.md from 197,376 to 218,101 characters — +20,725 against a 13,243
#: ceiling — and nothing fired, because it replaced a 190-line section with a python splice run
#: through the shell. Not evasion: a splice is the obvious tool for swapping a long section,
#: which is what makes the hole dangerous rather than theoretical, and it is widest on exactly
#: the large edits the ceiling exists for. docs/claude-md-admission-policy.md § "What it cannot
#: see" had named this gap since the day it was written; this closes it.
#:
#: TWO SIGNALS ARE REQUIRED AND THAT IS THE WHOLE DESIGN. A command must NAME the project's own
#: CLAUDE.md *and* carry a write-shaped token. Either alone stays silent, because this matcher
#: sees EVERY shell call in the session and an ordinary read of the file outnumbers a real write
#: by orders of magnitude. An indiscriminate gate on the shell is the fastest way to get this
#: file switched off, which is the failure claude-md-drift.py already names three victims of.
CLAUDE_MD_TOKEN = re.compile(r"""(?:^|[\s'"=(])([~./\w-]*CLAUDE\.md)\b""")

WRITE_SHAPES = (
    re.compile(r""">>?\s*['"]?[~./\w-]*CLAUDE\.md"""),
    re.compile(r"""\btee\b(?:\s+-a)?\s+['"]?[~./\w-]*CLAUDE\.md"""),
    re.compile(r"""\b(?:sed|perl)\b[^;|&]*?\s-i"""),
    re.compile(r"""\b(?:write_text|writelines|writeFileSync|writeFile)\s*\("""),
    re.compile(r"""\bopen\s*\([^)]*['"][wa]"""),
    re.compile(r"""\b(?:mv|cp)\b[^;|&]*[~./\w-]*CLAUDE\.md\s*(?:$|[;|&])"""),
)


#: SHELL OPERATORS ONLY, NEVER NEWLINES. A command is split here so that the write shape and
#: the filename have to occur in the SAME segment: `sed -i '' README.md && echo 'update
#: CLAUDE.md by hand'` carries both signals and writes nothing, and a whole-command search
#: calls it a write. Newlines are deliberately NOT separators — a heredoc python body puts the
#: path on one line and `write_text(` on another, and splitting there would lose the real case
#: to save the false one.
SEGMENT = re.compile(r"(?:\|\||&&|[;|&])")


def scripted_claude_md_write(command: str, cwd: str | None = None) -> Path | None:
    """The project CLAUDE.md a shell command would WRITE, or None.

    Returns None for every read — a cat, a grep, a wc, a revision read piped into a counter —
    and for the global and workspace instruction files, which the policy puts out of scope on
    purpose (§ 5) and which is_project_claude_md already separates by marker, not by path.
    """
    if not command or "CLAUDE.md" not in command:
        return None
    for segment in SEGMENT.split(command):
        if "CLAUDE.md" not in segment:
            continue
        if not any(shape.search(segment) for shape in WRITE_SHAPES):
            continue
        for raw in CLAUDE_MD_TOKEN.findall(segment):
            target = is_project_claude_md(raw, cwd)
            if target is not None:
                return target
    return None


BASH_SCRIPTED = """\
CLAUDE.md ADMISSION — this shell command writes to the always-loaded instruction file.

  TARGET: {target}

THIS HOOK CANNOT MEASURE A SCRIPTED WRITE, AND SAYS SO RATHER THAN GUESSING. An Edit or a Write
carries its new text in the tool call, so the net character change is knowable before it lands.
A shell command does not — the content is computed while the command runs. So the {ceiling:,}
character RUNAWAY ceiling CANNOT MEASURE this edit, and this is an ask rather than a measurement.

  STANDING: {current:,} characters against a budget of {budget:,}.

THE ADMISSION TEST ({policy}):
  Admit a section only if a session that does not know it would act WRONGLY before anything
  else could tell it — and if some other surface could tell it in time, that surface is the
  home, not this file.

IF SOMETHING CHEAPER FIRES IN TIME, IT IS THE HOME — pick the strongest that does:
  pointer (docs/) · skill · tool description · hook · type · test

IF THIS IS A REMOVAL rather than an addition, § 3's eviction test applies instead: name the
§ 3 clause, the surface that now holds the content, and the evidence that surface reaches a
session in time. An eviction is proposed, never performed unasked.

WHY YOU ARE SEEING THIS AT ALL: measured 2026-09-18, a scripted splice put 20,725 characters
into this file with every tier of this gate silent. Answering honestly is the whole mechanism —
there is no measurement standing behind this one.\
"""


def emit(decision: str, context: str) -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
    }
    if decision == "ask":
        out["hookSpecificOutput"]["permissionDecisionReason"] = context
    else:
        out["hookSpecificOutput"]["additionalContext"] = context
    print(json.dumps(out))


def main() -> int:
    payload = read_payload()
    tool_name = payload.get("tool_name")

    if tool_name == "Bash":
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return 0
        command = tool_input.get("command")
        if not isinstance(command, str):
            return 0
        cwd = payload.get("cwd")
        target = scripted_claude_md_write(command, cwd if isinstance(cwd, str) else None)
        if target is None:
            return 0
        try:
            current = len(target.read_text(encoding="utf-8"))
        except OSError:
            current = BUDGET_CHARS
        log_fire("ask-scripted", target=str(target), current=current, tool="Bash")
        emit(
            "ask",
            BASH_SCRIPTED.format(
                target=target,
                ceiling=RUNAWAY_NET_CHARS,
                current=current,
                budget=BUDGET_CHARS,
                policy=POLICY,
            ),
        )
        return 0

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    raw = tool_input.get("file_path")
    target = is_project_claude_md(raw) if isinstance(raw, str) else None
    if target is None:
        return 0

    pair = before_and_after(tool_name, tool_input, target)
    if pair is None:
        return 0
    before, after, whole_file = pair

    net = len(after) - len(before)
    added = new_headings(before, after)

    # The size the file would be left at. Only ever REPORTED, never a trigger — the file is
    # over budget today, so triggering on the total would fire on every edit forever.
    if whole_file:
        current = len(after)
    else:
        try:
            current = len(target.read_text(encoding="utf-8")) + net
        except OSError:
            current = BUDGET_CHARS + net
    over = max(0, current - BUDGET_CHARS)
    pct = round(over * 100 / BUDGET_CHARS) if BUDGET_CHARS else 0

    if added:
        named = "\n".join("  ADDS: " + h for h in added[:6])
        if len(added) > 6:
            named += f"\n  ... and {len(added) - 6} more"
    else:
        named = "  (no new section heading — this is a bulk addition inside existing sections)"

    if net > RUNAWAY_NET_CHARS:
        log_fire("ask-runaway", net=net, headings=added, current=current, tool=tool_name)
        emit(
            "ask",
            ASK.format(
                net=net,
                ceiling=RUNAWAY_NET_CHARS,
                policy=POLICY,
                headings=named + "\n",
                current=current,
                budget=BUDGET_CHARS,
            ),
        )
        return 0

    if added:
        log_fire("notice-heading", net=net, headings=added, current=current, tool=tool_name)
        emit(
            "allow",
            NOTICE.format(
                headings=named,
                policy=POLICY,
                current=current,
                budget=BUDGET_CHARS,
                over=over,
                pct=pct,
                net=net,
            ),
        )
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A guard that crashes a CLAUDE.md edit is worse than one that misses it.
        sys.exit(0)
