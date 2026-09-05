#!/usr/bin/env python3
"""bmad-health — the one honest answer to "are my methods current?"

Owner instruction, 2026-08-31: BMAD fork maintenance is no longer an owner-operated
workstream. Mason is not the operator, reviewer, or decision-maker for fork mechanics.
He gets an OUTCOME, in four lines, in plain English:

    Methods:     HEALTHY | REPAIRING | OWNER DECISION NEEDED
    Outcome:     what is true, for him, right now
    My action:   what has already happened or is running
    Your action: None, or exactly one plain-English decision

This tool exists so that line can never be typed from memory or optimism. It composes the
existing release boundary (tools/bmad-release.py) rather than reimplementing it, and answers
the four accountability questions:

    1. Are all active projects current?               -> every enabled target classifies CURRENT
    2. Any completed improvements not yet active?     -> stranded fork branches + non-CURRENT targets
    3. Any unsafe/stale/duplicate project copies?     -> MISSING/MISREGISTERED/UNSAFE_PATH/UNREACHABLE
    4. Anything blocked on the owner?                 -> the owner-decision queue + owner-gate targets

HEALTHY is a VERIFIED state, never a default. Any question this tool could not answer
downgrades the verdict; it never rounds up.

    bmad-health.py            the four-line outcome
    bmad-health.py --why      the same, plus the infrastructure detail (on request only)
    bmad-health.py --json     machine-readable
    bmad-health.py --park     open an owner decision   (--question --recommendation [--impact])
    bmad-health.py --close ID close one

Read-only except for --park/--close, which append to ~/.bmad-owner-decisions.jsonl.
"""
import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "bmad_release", Path(__file__).resolve().parent / "bmad-release.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

DECISIONS = Path.home() / ".bmad-owner-decisions.jsonl"

# STD-DEPLOY-002 — the deploy-lane standard. Loaded the same way as the release
# helper; a missing checker is reported as such, never as "met".
_lane_spec = importlib.util.spec_from_file_location(
    "check_deploy_lane", Path(__file__).resolve().parent / "check-deploy-lane.py")
try:
    L = importlib.util.module_from_spec(_lane_spec)
    _lane_spec.loader.exec_module(L)
except Exception:  # noqa: BLE001
    L = None


def deploy_lane(targets):
    """-> the STD-DEPLOY-002 fleet summary over the ACTIVE targets, or a stub that
    says the checker was unavailable. Never rounds up: an unreadable project is
    UNKNOWN, and UNKNOWN keeps the fleet off STANDARD MET."""
    if L is None:
        return {"fleet": "UNAVAILABLE", "results": [], "gaps": [], "not_declared": [],
                "unknown": [], "on_trust": {}, "note": "tools/check-deploy-lane.py missing"}
    try:
        results = [L.assess_project(Path(t["path"])) for t in targets if t.get("path")]
        return L.summarise(results)
    except Exception as e:  # noqa: BLE001
        return {"fleet": "UNAVAILABLE", "results": [], "gaps": [], "not_declared": [],
                "unknown": [], "on_trust": {}, "note": f"{type(e).__name__}: {e}"}

# A target in one of these states is not a maintenance problem — it is an identity problem,
# and the owner-gate rule reserves identity for Mason ("a target project appears to be a
# different/unknown project and could receive the wrong methods").
IDENTITY_STATES = {"MISSING", "MISREGISTERED", "UNSAFE_PATH", "UNREACHABLE"}
# Ordinary divergence. Repaired silently, never surfaced as a decision.
REPAIRABLE_STATES = {"STALE", "LOCAL_DRIFT", "PARTIAL_RELEASE", "BLOCKED"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def open_decisions():
    if not DECISIONS.is_file():
        return []
    rows, closed = [], set()
    for line in DECISIONS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("op") == "close":
            closed.add(d.get("id"))
        else:
            rows.append(d)
    return [d for d in rows if d.get("id") not in closed]


def park(args):
    DECISIONS.touch()
    n = sum(1 for line in DECISIONS.read_text().splitlines() if line.strip()) + 1
    rec = {"id": f"OD-{n:03d}", "opened": now(), "question": args.question,
           "recommendation": args.recommendation, "impact": args.impact or ""}
    with DECISIONS.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"parked {rec['id']}")
    return 0


def close(args):
    if not any(d["id"] == args.close for d in open_decisions()):
        print(f"no open decision {args.close}")
        return 1
    with DECISIONS.open("a") as fh:
        fh.write(json.dumps({"op": "close", "id": args.close, "at": now()}) + "\n")
    print(f"closed {args.close}")
    return 0


def local_only(t):
    """Managed-root commits that exist on THIS machine and nowhere else.

    A replica can be CURRENT on disk and still be undelivered: the distribution commit
    was never pushed, so a fresh clone, another machine, and CI all get the OLD methods.
    'Current' that only one laptop can see is not delivered, and the accountability
    contract asks about delivery — so this is measured, not assumed. Returns the count
    of unpushed commits touching the managed root; 0 when there is no upstream to
    compare against (unknowable, not clean — the caller must not read 0 as proof).
    """
    real, root = t["path"], t.get("managed_root", "_bmad")
    if not R.out(["git", "-C", real, "rev-parse", "--abbrev-ref", "HEAD@{u}"]):
        return 0
    n = R.out(["git", "-C", real, "rev-list", "--count", "@{u}..HEAD", "--", root])
    return int(n) if n.isdigit() else 0


def content_verified(targets, release_sha):
    """-> (list of target ids whose INSTALLED CONTENT does not match the release, note).

    A receipt is not evidence. On 2026-08-31 the distributor refused thirteen of fourteen
    targets, exited 0 anyway, and the release tool wrote all fourteen a receipt — so every
    signal upstream of this one said delivered while the files on disk were stale. The only
    honest answer compares content, so before HEALTHY can be claimed the release is
    materialised at its exact commit and every target is diffed against it.

    Run ONLY on the otherwise-clean path, because it costs a worktree: if anything is
    already known broken the verdict is decided without it. Returns ([], reason) when the
    check could not run — the caller must treat that as unverified, never as clean.
    """
    verifier = Path(__file__).resolve().parent / "verify-installed.py"
    if not verifier.is_file() or not release_sha:
        return [], "content verification unavailable"
    spec = importlib.util.spec_from_file_location("verify_installed", verifier)
    V = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(V)

    tmp = Path(tempfile.mkdtemp(prefix="bmad-verify-"))
    wt = tmp / "release"
    if R.sh(["git", "worktree", "add", "--detach", str(wt), release_sha]).returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return [], "could not materialise the release to compare against"
    try:
        bad = []
        for t in targets:
            try:
                ok, _report = V.verify(t["path"], str(wt), quiet=True)
            except Exception:                             # a verifier crash is not a pass
                bad.append(t["id"])
                continue
            if not ok:
                bad.append(t["id"])
        return bad, ""
    finally:
        R.sh(["git", "worktree", "remove", "--force", str(wt)])
        shutil.rmtree(tmp, ignore_errors=True)


def survey(fetch=True):
    """-> dict. Every field is measured; nothing is assumed."""
    release_sha, findings = R.source_gate(fetch=fetch)
    source_blocks = [m for lvl, m in findings if lvl == "BLOCK"]

    # Question 2, half one: work finished in the fork that no project can see yet.
    stranded = [m for m in source_blocks
                if "not reachable" in m.lower() or "stranded" in m.lower()]

    reg = R.load_registry()
    seen, targets = {}, []
    for t in reg["targets"]:
        if not t.get("enabled", True):
            targets.append({"id": t["id"], "state": "DISABLED",
                            "detail": t.get("decommission_reason", ""),
                            "owner": t.get("owner", "active")})
            continue
        f, _real = R.validate_target(t, seen)
        blocks = [m for lvl, m in f if lvl == "BLOCK"]
        state, detail = (("BLOCKED", blocks[0]) if blocks
                         else R.classify(t, release_sha or ""))
        targets.append({"id": t["id"], "path": t["path"], "state": state, "detail": detail,
                        "owner": t.get("owner", "active"),
                        "local_only": local_only(t)})

    active = [t for t in targets if t["state"] != "DISABLED"]
    current = [t for t in active if t["state"] == "CURRENT"]
    identity = [t for t in active if t["state"] in IDENTITY_STATES]
    repairable = [t for t in active if t["state"] in REPAIRABLE_STATES]
    gated = [t for t in targets if t["owner"] == "owner-gate"]
    undelivered = [t for t in active if t.get("local_only")]
    decisions = open_decisions()

    # The verdict never rounds up. Without a resolved release commit we do not KNOW
    # whether anything is current, so the answer cannot be HEALTHY.
    unresolved = not release_sha

    # TWO DIFFERENT QUESTIONS, and conflating them produced a false REPAIRING on 2026-08-31.
    #
    #   "Are the owner's methods current everywhere?"   -> the TARGETS answer this.
    #   "Could a new release be cut this second?"       -> the SOURCE GATE answers this.
    #
    # A dirty fork worktree blocks the second and says nothing about the first. When someone
    # is simply mid-edit, the estate can be perfectly current while a release is momentarily
    # uncuttable — and reporting that as "your improvements are finished but not yet released"
    # is false twice over: uncommitted work is not finished, and every project already holds
    # the current release. So a dirty tree is recorded and reported, never a health downgrade.
    #
    # STRANDED work is the opposite case and DOES downgrade: a branch carrying COMMITTED work
    # that is not on the canonical channel is genuinely finished and genuinely invisible.
    # That is the distinction — committed-and-undelivered, not merely in-progress.
    blocking = [m for m in source_blocks if "dirty" not in m.lower()]

    # STD-DEPLOY-002. A project that ships without a lane that meets the standard, or
    # that has not said whether it ships, is a REPAIR (Claude's), never an owner
    # question — unless an inspection cannot tell, which is parked as a decision.
    lane = deploy_lane(active)
    lane_gaps = list(lane.get("gaps", [])) + list(lane.get("not_declared", [])) \
        + list(lane.get("unknown", []))
    lane_unmet = lane.get("fleet") != "STANDARD MET"

    # Content verification is the LAST gate and runs only when nothing else is wrong, because
    # it costs a worktree. Everything upstream of it — receipts, exit codes, the sync manifest
    # — has been observed lying on the same day this was written, so HEALTHY is never claimed
    # on their word alone.
    mismatched, verify_note = [], "not reached"
    if not (decisions or identity or gated or repairable or stranded
            or blocking or unresolved or undelivered) and active:
        mismatched, verify_note = content_verified(active, release_sha)

    if decisions or identity or gated:
        verdict = "OWNER DECISION NEEDED"
    elif (repairable or stranded or blocking or unresolved or undelivered
          or mismatched or (verify_note and verify_note != "not reached")):
        verdict = "REPAIRING"
    elif lane_unmet:
        verdict = "REPAIRING"
    elif active and len(current) == len(active):
        verdict = "HEALTHY"
    else:
        verdict = "REPAIRING"

    return {"at": now(), "verdict": verdict, "release_commit": release_sha,
            "deploy_lane": {"fleet": lane.get("fleet"), "gaps": lane.get("gaps", []),
                            "not_declared": lane.get("not_declared", []),
                            "unknown": lane.get("unknown", []),
                            "on_trust": lane.get("on_trust", {}),
                            "note": lane.get("note", ""),
                            "results": [{"id": r["id"], "state": r["state"],
                                         "rows": r.get("rows", {}),
                                         "why": r.get("notes", {}).get("why", "")}
                                        for r in lane.get("results", [])]},
            "lane_gaps": lane_gaps,
            "mismatched": mismatched, "verify_note": verify_note,
            "release_uncuttable": [m for m in source_blocks if "dirty" in m.lower()],
            "source_blocks": source_blocks, "stranded": stranded, "targets": targets,
            "active": len(active), "current": len(current), "identity": identity,
            "repairable": repairable, "owner_gated": gated, "decisions": decisions,
            "undelivered": undelivered,
            "questions": {
                "all_projects_current": bool(active) and len(current) == len(active),
                "undelivered_improvements": (bool(stranded) or bool(repairable)
                                             or bool(undelivered) or bool(mismatched)),
                "unsafe_or_duplicate_copies": bool(identity) or bool(gated),
                "blocked_on_owner": bool(decisions) or bool(identity) or bool(gated),
                "deploy_lane_standard_met": not lane_unmet,
            }}


def render(s):
    n, c = s["active"], s["current"]
    lines = [f"Methods: {s['verdict']}"]

    if s["verdict"] == "HEALTHY":
        lines.append(f"Outcome: Your methods are current across all {n} active projects.")
        lines.append("My action: Verified this run; nothing needed repair.")
        lines.append("Your action: None")
        return "\n".join(lines)

    if s["verdict"] == "REPAIRING":
        u, m = len(s.get("undelivered", [])), len(s.get("mismatched", []))
        lg = s.get("lane_gaps", [])
        only_lane = lg and not (s.get("repairable") or s.get("stranded") or s.get("source_blocks")
                                or not s.get("release_commit") or s.get("undelivered") or m)
        if only_lane:
            dl = s.get("deploy_lane", {})
            g, nd = len(dl.get("gaps", [])), len(dl.get("not_declared", []))
            parts = []
            if g:
                parts.append(f"{g} ship to production through a deploy method that cannot yet "
                             f"prove what it shipped")
            if nd:
                parts.append(f"{nd} have not yet said whether they ship at all")
            outcome = (f"Your methods are current everywhere, but of your {n} projects "
                       + " and ".join(parts) + ". I am bringing them up to the deploy standard.")
            lines.append(f"Outcome: {outcome}")
            lines.append("My action: Inspecting each of those projects and either building its "
                         "deploy lane to the standard or recording that it does not ship. "
                         "No action is needed from you.")
            lines.append("Your action: None")
            return "\n".join(lines)
        if m:
            outcome = (f"{m} of {n} projects are not yet holding exactly the methods they "
                       f"should be. I am putting that right.")
        elif n and c == n and u:
            outcome = (f"Your methods are active in all {n} projects on this machine, but in "
                       f"{u} of them that has not been saved anywhere else yet — a fresh copy "
                       f"of those projects would still get the old ones.")
        elif n and c == n:
            outcome = ("Your latest workflow improvements are finished but not yet released, "
                       "so no project can see them yet.")
        elif c:
            outcome = (f"Your methods are current across {c} of {n} projects; "
                       f"I am repairing the remaining {n - c}.")
        else:
            outcome = ("Your latest workflow improvements are not yet active in your projects. "
                       "I have identified the cause and am repairing it.")
        lines.append(f"Outcome: {outcome}")
        lines.append("My action: Releasing the finished work and bringing every project up to "
                     "it. No action is needed from you.")
        lines.append("Your action: None")
        return "\n".join(lines)

    # OWNER DECISION NEEDED — exactly one decision, with a recommendation.
    if s["decisions"]:
        d = s["decisions"][0]
        question, recommendation = d["question"], d.get("recommendation", "")
        extra = f" {d['impact']}" if d.get("impact") else ""
    elif s["identity"]:
        t = s["identity"][0]
        question = (f"One project copy ({t['id']}) may hold work you still need, and I will "
                    f"not touch it until you say so.")
        recommendation = ("Leave it untouched and keep every other project current; archive it "
                          "once I have confirmed it holds no uncommitted work.")
        extra = ""
    else:
        t = s["owner_gated"][0]
        question = (f"One project copy ({t['id']}) is waiting on your review before it "
                    f"receives methods.")
        recommendation = "Confirm it should keep receiving your methods, or retire it."
        extra = ""

    lines.append(f"Outcome: Maintenance needs one decision. {question}{extra}")
    if c:
        lines.append(f"My action: {c} of {n} projects are current and I am keeping them that "
                     f"way while this waits.")
    else:
        lines.append("My action: Everything safe and reversible is being repaired while this "
                     "waits.")
    lines.append(f"Your action: {recommendation}")
    return "\n".join(lines)


def why(s):
    sha = s["release_commit"][:12] if s["release_commit"] else "(unresolved)"
    out = ["", "--- infrastructure detail (requested) ---", f"release commit : {sha}"]
    for m in s["source_blocks"]:
        kind = "release blocked" if "dirty" not in m.lower() else "not cuttable now"
        out.append(f"{kind:<15}: {m.splitlines()[0]}")
    width = max([len(t["id"]) for t in s["targets"]] or [10]) + 2
    for t in s["targets"]:
        lo = f"  [{t['local_only']} unpushed]" if t.get("local_only") else ""
        out.append(f"  {t['id']:<{width}}{t['state']:<16}{t['detail'][:60]}{lo}")
    for d in s["decisions"]:
        out.append(f"  OPEN {d['id']}: {d['question']}")
    dl = s.get("deploy_lane") or {}
    out.append(f"  deploy lane (STD-DEPLOY-002): {dl.get('fleet', '?')}"
               + (f" — {dl['note']}" if dl.get("note") else ""))
    for r in dl.get("results", []):
        rows = " ".join(f"{k}:{'✓' if v == 'verified' else '~' if v == 'declared' else '✗'}"
                        for k, v in r.get("rows", {}).items())
        out.append(f"    {r['id']:<{width - 2}}{r['state']:<13}{rows or r.get('why', '')[:60]}")
    for k, v in s["questions"].items():
        out.append(f"  {k:<28}{v}")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="BMAD methods health — outcome, not mechanism.")
    p.add_argument("--why", action="store_true", help="append the infrastructure detail")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-fetch", action="store_true")
    p.add_argument("--park", action="store_true", help="open an owner decision")
    p.add_argument("--question")
    p.add_argument("--recommendation")
    p.add_argument("--impact")
    p.add_argument("--close", metavar="ID")
    a = p.parse_args()

    if a.park:
        if not (a.question and a.recommendation):
            p.error("--park needs --question and --recommendation")
        return park(a)
    if a.close:
        return close(a)

    s = survey(fetch=not a.no_fetch)
    if a.json:
        print(json.dumps(s, indent=2))
    else:
        print(render(s))
        if a.why:
            print(why(s))
    return {"HEALTHY": 0, "REPAIRING": 1, "OWNER DECISION NEEDED": 2}[s["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
