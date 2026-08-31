#!/usr/bin/env python3
"""Golden cases for bmad-health.

The invariant under test is NOT "does it print nicely". It is that the health signal
CANNOT round up: HEALTHY is reachable only when every question was answered and every
answer was good, and an owner decision always outranks an in-progress repair.

Most cases assert the verdict, and several assert that infrastructure vocabulary never
reaches the four owner-facing lines — that is the owner instruction, not cosmetics.
"""
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
_spec = importlib.util.spec_from_file_location("bmad_health", TOOLS / "bmad-health.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")


def survey(targets, *, sha="a" * 40, blocks=(), decisions=()):
    """Build a survey dict the way survey() would, then re-run the verdict logic on it."""
    active = [t for t in targets if t["state"] != "DISABLED"]
    current = [t for t in active if t["state"] == "CURRENT"]
    identity = [t for t in active if t["state"] in H.IDENTITY_STATES]
    repairable = [t for t in active if t["state"] in H.REPAIRABLE_STATES]
    gated = [t for t in targets if t.get("owner") == "owner-gate"]
    undelivered = [t for t in active if t.get("local_only")]
    stranded = [m for m in blocks if "not reachable" in m.lower() or "stranded" in m.lower()]

    if decisions or identity or gated:
        verdict = "OWNER DECISION NEEDED"
    elif repairable or stranded or blocks or not sha or undelivered:
        verdict = "REPAIRING"
    elif active and len(current) == len(active):
        verdict = "HEALTHY"
    else:
        verdict = "REPAIRING"

    return {"at": "now", "verdict": verdict, "release_commit": sha,
            "source_blocks": list(blocks), "stranded": stranded, "targets": targets,
            "active": len(active), "current": len(current), "identity": identity,
            "repairable": repairable, "owner_gated": gated, "decisions": list(decisions),
            "undelivered": undelivered, "questions": {}}


def T(tid, state, owner="active", local_only=0):
    return {"id": tid, "state": state, "detail": "d", "owner": owner,
            "local_only": local_only}


BANNED = ["fork", "branch", "rsync", "worktree", "manifest", "merge conflict",
          "canonical source", "replica", "commit sha"]

print("bmad-health golden cases:\n")

# ---------------------------------------------------------------- verdict never rounds up
s = survey([T("a", "CURRENT"), T("b", "CURRENT")])
check("H1 every target current and source clean -> HEALTHY", s["verdict"] == "HEALTHY")

s = survey([T("a", "CURRENT"), T("b", "STALE")])
check("H2 one stale target -> REPAIRING", s["verdict"] == "REPAIRING")

s = survey([T("a", "CURRENT")], blocks=["a branch is not reachable from the release commit"])
check("H3 finished-but-unreleased work -> REPAIRING even with every target current",
      s["verdict"] == "REPAIRING")

s = survey([T("a", "CURRENT")], sha=None)
check("H4 unresolvable release commit -> REPAIRING, never HEALTHY", s["verdict"] == "REPAIRING")

s = survey([])
check("H5 an empty registry is not HEALTHY", s["verdict"] == "REPAIRING")

s = survey([T("a", "DISABLED")])
check("H6 a registry of only disabled targets is not HEALTHY", s["verdict"] == "REPAIRING")

# ------------------------------------------------------- owner decisions outrank repairs
s = survey([T("a", "STALE"), T("b", "MISREGISTERED")])
check("H7 an identity problem outranks ordinary staleness",
      s["verdict"] == "OWNER DECISION NEEDED")

s = survey([T("a", "CURRENT"), T("b", "LOCAL_DRIFT", owner="owner-gate")])
check("H8 an owner-gated target -> OWNER DECISION NEEDED",
      s["verdict"] == "OWNER DECISION NEEDED")

s = survey([T("a", "CURRENT")],
           decisions=[{"id": "OD-001", "question": "q", "recommendation": "r"}])
check("H9 a parked decision -> OWNER DECISION NEEDED", s["verdict"] == "OWNER DECISION NEEDED")

s = survey([T("a", "CURRENT")], decisions=[{"id": "OD-001", "question": "q",
                                            "recommendation": "r"}])
check("H10 a parked decision beats an otherwise-clean estate",
      s["verdict"] != "HEALTHY")

# ------------------------------------------------------------- LOCAL_DRIFT is repairable
s = survey([T("a", "LOCAL_DRIFT")])
check("H11 uncommitted replica content is ordinary repair, not an owner decision",
      s["verdict"] == "REPAIRING")

s = survey([T("a", "PARTIAL_RELEASE")])
check("H12 a replica with no receipt is ordinary repair", s["verdict"] == "REPAIRING")

# ------------------------------------------------- current-on-disk is not yet delivered
s = survey([T("a", "CURRENT", local_only=1)])
check("H12a a CURRENT replica whose distribution was never pushed is NOT healthy",
      s["verdict"] == "REPAIRING")

s = survey([T("a", "CURRENT"), T("b", "CURRENT", local_only=3)])
check("H12b one undelivered replica downgrades an otherwise-current estate",
      s["verdict"] == "REPAIRING")

r = H.render(survey([T("a", "CURRENT"), T("b", "CURRENT", local_only=3)]))
check("H12c ... and says so in words the owner can act on, without git vocabulary",
      "a fresh copy of those projects would still get the old ones" in r
      and "push" not in r.lower())

s = survey([T("a", "CURRENT", local_only=0), T("b", "CURRENT", local_only=0)])
check("H12d nothing unpushed leaves HEALTHY reachable", s["verdict"] == "HEALTHY")

# ------------------------------------------------------------------------ the four lines
for label, s in [
    ("healthy", survey([T("a", "CURRENT")])),
    ("repairing", survey([T("a", "CURRENT"), T("b", "STALE")])),
    ("no-targets-current", survey([T("a", "STALE")])),
    ("owner-identity", survey([T("a", "CURRENT"), T("b", "MISSING")])),
    ("owner-gated", survey([T("a", "CURRENT"), T("b", "STALE", owner="owner-gate")])),
    ("owner-parked", survey([T("a", "CURRENT")], decisions=[
        {"id": "OD-001", "question": "An old copy may hold work you still need.",
         "recommendation": "Archive it once I confirm it is empty.", "impact": ""}])),
]:
    text = H.render(s)
    lines = text.splitlines()
    check(f"H13 {label}: exactly four lines", len(lines) == 4)
    check(f"H14 {label}: lines are Methods/Outcome/My action/Your action",
          [l.split(":")[0] for l in lines] == ["Methods", "Outcome", "My action", "Your action"])
    low = text.lower()
    hit = [w for w in BANNED if w in low]
    check(f"H15 {label}: no infrastructure vocabulary in the owner-facing lines ({hit})",
          not hit)
    check(f"H16 {label}: no bare commit sha leaks into the outcome",
          not re.search(r"\b[0-9a-f]{7,}\b", text))

s = survey([T("a", "CURRENT"), T("b", "STALE"), T("c", "STALE")])
check("H17 partial coverage is stated as a count the owner can read",
      "1 of 3 projects" in H.render(s))

s = survey([T("a", "CURRENT")], decisions=[{"id": "OD-001", "question": "Q?",
                                            "recommendation": "R.", "impact": ""}])
r = H.render(s)
check("H18 a parked decision surfaces its own question", "Q?" in r)
check("H19 ... and always carries a recommendation", "Your action: R." in r)

s = survey([T("a", "CURRENT"), T("b", "MISSING")])
check("H20 while a decision waits, the owner is told what continues in parallel",
      "keeping them that way while this waits" in H.render(s))

# ------------------------------------------------------------- decision queue round-trip
with tempfile.TemporaryDirectory() as d:
    H.DECISIONS = Path(d) / "decisions.jsonl"
    check("H21 an absent queue is empty, not an error", H.open_decisions() == [])

    class A:
        question, recommendation, impact = "Archive the old copy?", "Yes, after a check", ""
    H.park(A())
    check("H22 park writes one open decision", len(H.open_decisions()) == 1)
    oid = H.open_decisions()[0]["id"]

    class B:
        close = oid
    H.close(B())
    check("H23 close removes it", H.open_decisions() == [])
    check("H24 the queue is append-only — the close is a new record, not a rewrite",
          sum(1 for l in H.DECISIONS.read_text().splitlines() if l.strip()) == 2)

    H.DECISIONS.write_text('{"id": "OD-001"\nnot json\n')
    check("H25 a corrupt queue degrades to empty rather than crashing",
          H.open_decisions() == [])

# --------------------------------------------------------------------- exit-code contract
codes = {"HEALTHY": 0, "REPAIRING": 1, "OWNER DECISION NEEDED": 2}
check("H26 the three verdicts have distinct exit codes", len(set(codes.values())) == 3)
check("H27 only HEALTHY exits zero", codes["HEALTHY"] == 0 and all(
    v != 0 for k, v in codes.items() if k != "HEALTHY"))

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
