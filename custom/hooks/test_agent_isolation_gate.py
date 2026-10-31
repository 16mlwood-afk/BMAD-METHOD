#!/usr/bin/env python3
"""Golden cases for agent-isolation-gate.py.

MOST OF THESE ASSERT SILENCE, and that is the point rather than a coincidence.
Measured over 191 real spawns in this project's transcripts, 79 carried
`AUTHORITY: read-only` and 66 already set `isolation: "worktree"` — three in
four spawns must pass this gate without a word. A gate that fires on ordinary
research is switched off within a week, and then it guards nothing on the day it
matters.

Two silence cases are worth reading before changing anything here:

  * `AUTHORITY: read-only. You hold no implementation authority.` — a real card
    shape. A substring test for "implementation" denies it. Two of 26 fires in
    the measurement were exactly this, which is why position decides.
  * A card with no `AUTHORITY:` line at all. The delegation-card guard already
    DENIES that upstream on the same event. Two refusals for one fault reads as
    two faults.

The cases that DENY are the one that cost 285,000 tokens on 2026-09-14: a card
declaring implementation authority, spawned into the parent's own checkout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = Path(__file__).with_name("agent-isolation-gate.py")
AGENTS_DIR = Path(os.path.expanduser("~/.claude/agents"))

SILENT: list[tuple[str, dict, dict]] = []
NOTES: list[tuple[str, dict, dict]] = []
DENIES: list[tuple[str, dict, dict]] = []


def card(authority: str | None, extra: str = "") -> str:
    """A delegation card, optionally without its AUTHORITY line."""
    lines = [
        "OBJECTIVE: build the thing that was asked for",
        "SCOPE: src/ and its tests, nothing else",
        "NON-GOALS: no commits, no partner writes",
        "EVIDENCE STANDARD: the suite passes and tsc is clean",
        "DELIVERABLE: the code, the tests, a short report",
        "STOP CONDITION: the suite is green",
        "JUSTIFICATION: parallelism — the parent holds the owner conversation",
    ]
    if authority is not None:
        lines.insert(5, f"AUTHORITY: {authority}")
    return "\n".join(lines) + extra


def spawn(
    authority: str | None,
    isolation: str | None = None,
    subagent_type: str = "general-purpose",
    tool: str = "Agent",
    prompt: str | None = None,
) -> dict:
    ti: dict = {
        "description": "do the work",
        "prompt": prompt if prompt is not None else card(authority),
        "subagent_type": subagent_type,
    }
    if isolation is not None:
        ti["isolation"] = isolation
    return {"tool_name": tool, "tool_input": ti}


def session_with(*subagents: tuple[str, bool, float]) -> dict:
    """A payload whose transcript_path has a real session dir beside it.

    Each subagent is (label, spawned_with_worktree, age_seconds).
    """
    root = Path(tempfile.mkdtemp())
    transcript = root / "session.jsonl"
    transcript.write_text("{}\n")
    sdir = root / "session"
    subs = sdir / "subagents"
    subs.mkdir(parents=True)
    now = time.time()
    for label, isolated, age in subagents:
        stem = f"agent-{label}"
        (subs / f"{stem}.meta.json").write_text(
            json.dumps(
                {
                    "agentType": "general-purpose",
                    "description": label,
                    **({"spawnedWithWorktree": True} if isolated else {}),
                }
            )
        )
        jl = subs / f"{stem}.jsonl"
        jl.write_text("{}\n")
        os.utime(jl, (now - age, now - age))
    return {"tool_name": "EnterWorktree", "tool_input": {"name": "feat/x"},
            "transcript_path": str(transcript)}


def run(p: dict, env: dict | None = None) -> tuple[int, str, str]:
    e = dict(os.environ)
    e.pop("AGENT_ISOLATION_OVERRIDE", None)
    if env:
        e.update(env)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(p),
        capture_output=True,
        text=True,
        env=e,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── silence ──────────────────────────────────────────────────────────────────

SILENT.append(("a read-only spawn is the whole research lane and is never gated",
               spawn("read-only"), {}))
SILENT.append((
    # MEASURED FALSE POSITIVE: 2 of 26 fires under a substring test.
    "a read-only card that mentions implementation to DENY it is still read-only",
    spawn("read-only. You hold no implementation authority."), {}))
SILENT.append(("implementation WITH a worktree satisfies the rule",
               spawn("implementation", isolation="worktree"), {}))
SILENT.append(("isolation remote is its own environment entirely",
               spawn("implementation", isolation="remote"), {}))
SILENT.append((
    "a card with no AUTHORITY line is the delegation-card guard's refusal, not this one",
    spawn(None), {}))
SILENT.append(("an AUTHORITY value naming none of the three is likewise upstream's",
               spawn("whatever seems sensible at the time"), {}))
SILENT.append(("a Bash call is not this hook's event",
               {"tool_name": "Bash", "tool_input": {"command": "npm test"}}, {}))
SILENT.append((
    "the bold `**AUTHORITY:** read-only` form parses the same as the plain one",
    spawn(None, prompt=card(None) + "\n**AUTHORITY:** read-only, no writes at all"), {}))
SILENT.append(("EnterWorktree with no transcript_path cannot look and says nothing",
               {"tool_name": "EnterWorktree", "tool_input": {"name": "feat/x"}}, {}))
SILENT.append(("EnterWorktree when the live subagent already has its own worktree",
               session_with(("gauge", True, 5)), {}))
SILENT.append(("EnterWorktree when the shared subagent went quiet an hour ago",
               session_with(("gauge", False, 3600)), {}))
SILENT.append(("an unparseable payload is silent here because the card guard fails closed",
               {"tool_name": "Agent"}, {}))

# ── notes: allowed, with something said ──────────────────────────────────────

NOTES.append((
    "diagnosis warns rather than denies — 9 of 11 real diagnosis spawns wrote a file",
    spawn("diagnosis"), {}))
NOTES.append((
    "an Explore agent cannot write, so implementation authority is the card's contradiction",
    spawn("implementation", subagent_type="Explore"), {}))
NOTES.append((
    "the override is honoured and named, never silent",
    spawn("implementation"), {"AGENT_ISOLATION_OVERRIDE": "1"}))
NOTES.append((
    "EnterWorktree while a shared subagent is actively writing",
    session_with(("gauge", False, 5), ("speccer", True, 5)), {}))

if (AGENTS_DIR / "data-integrity-auditor.md").exists():
    NOTES.append((
        "a bench agent whose own definition denies it Edit and Write needs no worktree",
        spawn("implementation", subagent_type="data-integrity-auditor"), {}))

# ── denial ───────────────────────────────────────────────────────────────────

DENIES.append((
    # THE 2026-09-14 CASE, exactly as it was spawned.
    "implementation authority with no isolation is refused",
    spawn("implementation"), {}))
DENIES.append((
    "the elaboration after the verdict changes nothing",
    spawn("implementation — on the files named in SCOPE and nothing else"), {}))
DENIES.append((
    "the bold `**AUTHORITY:** implementation` form is refused the same",
    spawn(None, prompt=card(None) + "\n**AUTHORITY:** implementation, on SCOPE only"), {}))
DENIES.append((
    "an empty isolation string is not isolation",
    spawn("implementation", isolation=""), {}))
DENIES.append((
    "the Task spelling of the same tool is gated the same",
    spawn("implementation", tool="Task"), {}))


def decision(stdout: str) -> str:
    try:
        obj = json.loads(stdout)
    except Exception:
        return ""
    return str((obj.get("hookSpecificOutput") or {}).get("permissionDecision") or "")


def main() -> int:
    failures = 0

    for name, p, env in SILENT:
        code, out, err = run(p, env)
        if code != 0 or out.strip() or err.strip():
            failures += 1
            print(f"FAIL (should be silent): {name}\n  exit={code}\n  {(out + err).strip()[:240]}")

    for name, p, env in NOTES:
        code, out, err = run(p, env)
        if code != 0 or decision(out) == "deny":
            failures += 1
            print(f"FAIL (should allow with a note): {name}\n  exit={code}\n  {out.strip()[:240]}")
        elif "AGENT ISOLATION" not in out and "AGENT_ISOLATION_OVERRIDE" not in out:
            failures += 1
            print(f"FAIL (allowed without saying anything): {name}")

    for name, p, env in DENIES:
        code, out, err = run(p, env)
        if decision(out) != "deny":
            failures += 1
            print(f"FAIL (should deny): {name}\n  exit={code}\n  {(out + err).strip()[:240]}")

    # The denial must carry the FIX, not just the fault. A refusal that does not
    # say `isolation: "worktree"` makes the reader go and look it up, which is
    # how a gate earns a reputation for being in the way.
    _, out, _ = run(DENIES[0][1])
    for needle in ('isolation: \\"worktree\\"', "285,000", "AGENT_ISOLATION_OVERRIDE=1"):
        if needle not in out:
            failures += 1
            print(f"FAIL: the denial does not carry {needle!r}")

    # The diagnosis note must never be a refusal in disguise.
    _, out, _ = run(NOTES[0][1])
    if decision(out) == "deny":
        failures += 1
        print("FAIL: diagnosis was denied, and it must only warn")

    total = len(SILENT) + len(NOTES) + len(DENIES)
    print(
        f"{total - failures}/{total} golden cases pass "
        f"({len(SILENT)} of them asserting silence)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
