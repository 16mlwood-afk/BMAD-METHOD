#!/usr/bin/env python3
"""PreToolUse: an Agent that will WRITE FILES must be given its own worktree at the spawn.

WHY. `CLAUDE.md` § *ALWAYS Use Worktrees — CRITICAL* already says it, verbatim:

    "When spawning sub-agents via the `Agent` tool for work that edits files, always set
     isolation: \"worktree\" so each agent gets its own copy of the repo."

This is not a new policy. It is the missing enforcement tier under an old one, and the rule
above is prose of exactly the kind that decays — it names a parameter on a tool call, which
is the one thing a PreToolUse hook can inspect and the model cannot talk itself out of.

WHAT WENT WRONG WITHOUT IT, 2026-09-14. A subagent was spawned with no isolation to build a
priority gauge. Having no worktree of its own it made one with `git worktree add` and worked
there — a directory the harness knows nothing about. The parent session then entered two
other worktrees in sequence for unrelated delivery. The harness's own isolation guard
compares the SESSION's worktree against the working directory a command resolves to, so from
that moment every Bash, Write and Edit the agent attempted was refused — mid-task, after four
calls had already succeeded. The agent tried to spawn a sub-agent to escape and was refused
by the delegation-card gate; tried `EnterWorktree` on its own directory and was told it was
already the cwd; and finally had to message the parent and wait. Roughly 285,000 tokens, and
the work survived only because it was still in the transcript.

WHY THE FIX IS AT THE SPAWN AND NOWHERE ELSE. The refusal text ("This session is isolated in
the worktree ... but this command's working directory resolved to ...") appears in NO file
under `~/.claude/` or this project's `.claude/` — grepped both. It is harness-internal and
cannot be patched, softened or taught about. By the time it fires the agent is already
mid-task with no route out. The only moment anything here can act is before the agent starts.

THE PREDICATE, and it is a DECLARED FIELD rather than a guess at prose. Every spawn in this
environment already carries a delegation card (`~/.claude/hooks/delegation-card-guard.py`,
PreToolUse deny on `Agent|Task`), and that card carries a literal `AUTHORITY:` line whose
value must be one of `read-only | diagnosis | implementation`. `implementation` means it
writes. Nothing is inferred from the objective's wording.

THE FIRST ENUM TOKEN IN THE VALUE WINS, and that detail is load-bearing rather than fussy.
Measured over 191 real spawns in this project's transcripts, a naive "does the value contain
the word implementation" test produced TWO false positives out of 26 fires, both of them
cards reading `AUTHORITY: read-only. You hold no implementation authority.` A card is written
as `<verdict> — <elaboration>`, and the elaboration routinely negates the other enum members.
Position resolves it; substring does not.

DIAGNOSIS WARNS, IT DOES NOT DENY — and the brief for this gate guessed the other way, so the
measurement is worth stating. `diagnosis` was expected to be read-only in practice. It is
not: of 11 diagnosis spawns in the transcripts, 9 were told to write exactly one spec file,
and 4 of those had already been given a worktree by a parent who saw the need. So diagnosis
is neither safely silent nor honestly deniable — it straddles. It gets a note on the allow
path, which costs nothing and surfaces the real number, mirroring the two-tier split the
delegation-card guard already uses on this same tool.

WHAT STAYS SILENT, each for a stated reason, because a gate that fires on ordinary research
is switched off within a week and then guards nothing on the day it matters:

  * `AUTHORITY: read-only` — 79 of the 191 measured spawns. The whole read lane.
  * `isolation` already `worktree` — the rule is satisfied; 66 measured spawns.
  * `isolation: remote` — its own environment entirely, per the Agent tool's own contract.
  * A card with NO `AUTHORITY:` field at all. The delegation-card guard DENIES that upstream
    on the same event. Repeating it here would double-refuse one fault and teach the reader
    that two things are wrong when one is.
  * A subagent type that cannot write. The ten bench agents under `~/.claude/agents/` declare
    `tools: Read, Glob, Grep, Bash` (verified by reading their frontmatter, not assumed), and
    the harness's own `Explore` and `Plan` are documented as excluding Edit, Write and
    NotebookEdit. If such a type is paired with implementation authority the contradiction is
    the card's, and refusing the spawn would be the wrong end to correct it.

FAIL-OPEN ON AN UNREADABLE PAYLOAD, and this differs from its two sibling gates on purpose.
`attachment-preview-gate.py` and `humanizer-gate.py` deny when they cannot read the SESSION
TRANSCRIPT, because for them the evidence is external and a missing precondition means the
check has not run. Here the evidence is INSIDE the tool call: there is no external
precondition to go missing. A payload this cannot parse is a payload the delegation-card
guard cannot parse either, and that guard already fails closed to ASK on the same event. So
silence here is composition, not a hole.

CEILING — state it, because the gate reads stronger than it is. It proves the spawn DECLARED
implementation authority without asking for isolation. It cannot tell whether an agent will
actually write, whether its writes land in this repository or somewhere else entirely, or
whether the worktree it is given is the right one. A read-only card on an agent that then
writes passes silently, and nothing here would catch it. What it removes is the specific
discretion that cost 285,000 tokens: declaring implementation and spawning shared anyway.

OVERRIDE: AGENT_ISOLATION_OVERRIDE=1, named in the pass-through text so it is a choice
somebody can see. Using it is how 2026-09-14 happens again — the agent starts in the parent's
checkout, and the parent's next worktree hop refuses everything it tries from that point on.

SECOND MODE — `EnterWorktree`, WARN ONLY, NEVER DENY. The parent hopping worktrees is the
other half of the cause, so this warns when the session enters a worktree while a subagent
that has NO worktree of its own looks live. The signal is stronger than mtime alone: the
harness writes `subagents/<agent-id>.meta.json` beside each subagent transcript carrying
`spawnedWithWorktree`, which says definitively whether that agent is immune to this. Only the
non-immune ones are considered, and recency then comes from the transcript's mtime. Its blind
spot is honest and only ever causes a MISS: an agent blocked waiting writes nothing, so it
looks idle exactly when it is most exposed. It never denies — a stale file must not block
ordinary work, and entering a worktree is how delivery gets done here.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# ── the declared field ───────────────────────────────────────────────────────
# The SAME regex the delegation-card guard uses to read this field, deliberately
# copied rather than re-invented: tolerant of markdown bullets and of the
# `**AUTHORITY:** value` bold form, which appears in real cards.
AUTHORITY_RX = re.compile(
    r"^[ \t>*\-]*\**\s*authority\s*\**\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE
)

# Order matters nowhere here — position in the VALUE decides, not position in
# this tuple. These are the delegation card's own three.
AUTHORITY_ENUM = ("read-only", "diagnosis", "implementation")

# ── isolation values that satisfy or sidestep the rule ───────────────────────
SATISFIES = {"worktree"}
OUT_OF_SCOPE = {"remote"}  # its own environment; this repo's worktrees are irrelevant to it

# ── subagent types that cannot write ─────────────────────────────────────────
# Harness built-ins, documented as excluding Edit, Write and NotebookEdit. Named
# literally because they have no definition file on disk to read.
BUILTIN_READ_ONLY = {"Explore", "Plan"}

AGENTS_DIR = Path(os.path.expanduser("~/.claude/agents"))

# ── EnterWorktree warning ────────────────────────────────────────────────────
# How recently a subagent's transcript must have been written for it to count as
# live. Generous on purpose: the cost of a wrong warning is one line of context,
# and the cost of a miss is the 285,000-token failure this file documents.
LIVE_WINDOW_SECONDS = 600


def read_payload() -> dict | None:
    """The hook payload, or None when it cannot be parsed.

    None is a SILENT exit here rather than a refusal — see FAIL-OPEN above.
    """
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def authority_of(prompt: str) -> str | None:
    """The first enum token appearing in the card's AUTHORITY value.

    Returns None when the field is absent (the delegation-card guard owns that
    fault) or when its value names none of the three (likewise).
    """
    m = AUTHORITY_RX.search(prompt or "")
    if not m:
        return None
    value = m.group(1).lower()
    found = [(value.index(tok), tok) for tok in AUTHORITY_ENUM if tok in value]
    if not found:
        return None
    return min(found)[1]


def declared_tools(agent_file: Path) -> str | None:
    """The `tools:` frontmatter line of an agent definition, lowercased."""
    try:
        for line in agent_file.read_text(errors="replace").splitlines()[:40]:
            if line.lower().startswith("tools:"):
                return line.split(":", 1)[1].strip().lower()
    except Exception:
        return None
    return None


def cannot_write(subagent_type: str) -> bool:
    """True when this agent type's own definition denies it Edit and Write.

    Derived from the definition files rather than a list kept here, because a
    hardcoded roster is a drift surface and this repository has been bitten by
    one before. An unreadable directory means "cannot tell", which is False —
    the AUTHORITY field is the primary predicate and stands on its own.
    """
    if not subagent_type:
        return False
    if subagent_type in BUILTIN_READ_ONLY:
        return True
    f = AGENTS_DIR / f"{subagent_type}.md"
    tools = declared_tools(f)
    if tools is None:
        return False
    if "*" in tools:
        return False
    return "edit" not in tools and "write" not in tools


def emit(obj: dict) -> None:
    print(json.dumps(obj))
    sys.exit(0)


def deny(reason: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def note(text: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": text,
            }
        }
    )


DENIAL = """Wait. AGENT ISOLATION GATE — this spawn declares `AUTHORITY: implementation` and does not ask for its own worktree.

Add `isolation: "worktree"` to the Agent call and spawn again. That is the whole fix.

CLAUDE.md § ALWAYS Use Worktrees: "When spawning sub-agents via the `Agent` tool for work that edits files, always set isolation: \\"worktree\\" so each agent gets its own copy of the repo."

What happens if you spawn it shared. The agent starts in this session's checkout. The moment this session enters any worktree, the harness's isolation guard compares the SESSION's worktree against the agent's working directory and refuses every Bash, Write and Edit the agent attempts from then on — mid-task, with no route out. On 2026-09-14 that cost roughly 285,000 tokens: the agent made its own untracked worktree with `git worktree add`, worked there for four calls, then had everything refused, could not spawn a helper, could not EnterWorktree its own directory, and ended up messaging the parent to wait. The refusal is harness-internal and cannot be patched, which is why this gate is at the spawn.

A worktree the agent does not need costs almost nothing. A collision costs the session.

If this agent genuinely writes no files in this repository — its writes land under ~/.claude, or in another checkout entirely — say so and use the override; there is no way to read that off the card.

Override (named in the reply, never silent): AGENT_ISOLATION_OVERRIDE=1"""


def gate_agent(payload: dict) -> None:
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return

    isolation = str(ti.get("isolation") or "").strip().lower()
    if isolation in SATISFIES or isolation in OUT_OF_SCOPE:
        return

    prompt = str(ti.get("prompt") or "")
    authority = authority_of(prompt)
    if authority is None:
        # No parseable AUTHORITY. The delegation-card guard denies this upstream
        # on the same event; a second refusal for one fault would read as two.
        return

    subagent_type = str(ti.get("subagent_type") or "")

    if authority == "implementation":
        if cannot_write(subagent_type):
            note(
                f"AGENT ISOLATION: this card says `AUTHORITY: implementation` but "
                f"`{subagent_type}` declares no Edit or Write in its own definition, so it "
                "cannot write files and needs no worktree. The contradiction is in the card "
                "— one of the two is wrong."
            )
            return
        if os.environ.get("AGENT_ISOLATION_OVERRIDE") == "1":
            note(
                "AGENT_ISOLATION_OVERRIDE=1 honoured — an implementation agent is being "
                "spawned into this session's own checkout with no worktree of its own. If "
                "this session later enters a worktree, every write that agent attempts will "
                "be refused mid-task. Say so in the reply."
            )
            return
        deny(DENIAL)

    if authority == "diagnosis":
        note(
            "AGENT ISOLATION: this spawn declares `AUTHORITY: diagnosis` and no worktree. "
            "Diagnosis is not read-only in practice here — of 11 diagnosis spawns in this "
            "project's transcripts, 9 were told to write exactly one spec file, and 4 had "
            "already been given a worktree. If this agent writes ANY file, set "
            "`isolation: \"worktree\"` now: a shared agent stops being able to write the "
            "moment this session enters a worktree of its own."
        )


def session_dir(payload: dict) -> Path | None:
    """The harness's per-session directory, found from the transcript path.

    Derived rather than reconstructed from the project path, because the encoding
    of a project directory into a folder name is the harness's business and
    guessing at it is how a check silently matches nothing.
    """
    tp = payload.get("transcript_path")
    if not tp:
        return None
    p = Path(os.path.expanduser(str(tp)))
    d = p.with_suffix("")
    return d if d.is_dir() else None


def exposed_subagents(sdir: Path, now: float) -> list[str]:
    """Subagents in this session with NO worktree of their own that look live."""
    out: list[str] = []
    subs = sdir / "subagents"
    if not subs.is_dir():
        return out
    try:
        metas = sorted(subs.glob("*.meta.json"))
    except Exception:
        return out
    for meta in metas:
        try:
            info = json.loads(meta.read_text(errors="replace"))
        except Exception:
            continue
        if info.get("spawnedWithWorktree") is True:
            continue  # immune: it has its own registered worktree
        transcript = meta.with_name(meta.name.replace(".meta.json", ".jsonl"))
        try:
            age = now - transcript.stat().st_mtime
        except OSError:
            continue
        if age <= LIVE_WINDOW_SECONDS:
            label = info.get("description") or info.get("agentType") or transcript.stem
            out.append(f"{label} (last wrote {int(age)}s ago)")
    return out


def warn_enter_worktree(payload: dict) -> None:
    sdir = session_dir(payload)
    if sdir is None:
        return
    exposed = exposed_subagents(sdir, time.time())
    if not exposed:
        return
    listed = "\n".join(f"    - {e}" for e in exposed)
    note(
        "AGENT ISOLATION (warning, not a block — entering the worktree is fine): a subagent "
        "of this session has no worktree of its own and was writing recently.\n"
        f"{listed}\n"
        "Once this session is isolated in a worktree, the harness refuses every Bash, Write "
        "and Edit that agent attempts, mid-task, with no route out — that is the 2026-09-14 "
        "failure. If it is still working, let it finish before hopping, or accept that it "
        "will need respawning with `isolation: \"worktree\"`.\n"
        "This reads recent writes to the agent's transcript, so an agent sitting blocked "
        "looks idle here. Absence of a name above is not proof that nothing is live."
    )


def main() -> None:
    payload = read_payload()
    if payload is None:
        return  # see FAIL-OPEN: the card guard fails closed on the same event

    tool = str(payload.get("tool_name") or "")
    if tool in ("Agent", "Task"):
        gate_agent(payload)
        return
    if tool == "EnterWorktree":
        warn_enter_worktree(payload)
        return


if __name__ == "__main__":
    main()
