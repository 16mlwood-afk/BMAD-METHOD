#!/usr/bin/env python3
"""Golden suite for tools/check-deploy-lane.py — BOTH directions.

Run: python3 tools/test/test-check-deploy-lane.py

Every case builds a throwaway project directory and drives the checker through its real
module functions and its real CLI. Cases assert what must be reported as a GAP and, just as
deliberately, what must NOT be — a lane checker that flags a compliant lane is the one that
gets ignored, and then it protects nothing.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "check-deploy-lane.py"
spec = importlib.util.spec_from_file_location("cdl", CHECKER)
cdl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdl)

passed = failed = 0


def check(label, expected, actual):
    global passed, failed
    if expected == actual:
        passed += 1
    else:
        failed += 1
        print(f"  ✗ {label}\n      expected: {expected!r}\n      actual:   {actual!r}")


COMPLIANT_LANE = r"""#!/usr/bin/env bash
set -euo pipefail
git fetch -q origin
dirty="$(git status --porcelain --untracked-files=no -- .)"
head_sha="$(git rev-parse HEAD)"
origin_sha="$(git rev-parse origin/main)"
[ "$head_sha" = "$origin_sha" ] || exit 1
ur="$(upload_root_verdict "$toplevel" "$RAILWAY_CONFIG")"
lock="$common/deploy.lock"
restore_stamp_if_orphaned() { echo restore; }
trap restore_stamp_if_orphaned EXIT
local_fp="$(sh scripts/deploy-fingerprint.sh .)"
# Converging
for _ in 1 2 3; do observed="$(live_container_sha)"; done
case "$(convergence_verdict "$observed" "$head_sha")" in
  converged) ;; superseded) ;; behind) exit 1 ;; diverged) exit 1 ;;
esac
"""

MARKER_LANE = r"""#!/usr/bin/env bash
# STD-DEPLOY-002 R2: vercel --prebuilt from a CI checkout pinned by the workflow
# STD-DEPLOY-002 R3: VERCEL_GIT_COMMIT_SHA is set by the platform per deploy
# STD-DEPLOY-002 R4: vercel deploy <path> passes the root explicitly
# STD-DEPLOY-002 R5: read-back via the deployment inspect endpoint
# STD-DEPLOY-002 R6: fingerprint compared via the /_fp route
# STD-DEPLOY-002 R7: GitHub concurrency group serialises deploys
# STD-DEPLOY-002 R8: no stamp is written by hand; nothing to restore
vercel deploy --prod .
"""


def project(tmp, name, *, cfg=None, lane=None, lane_exec=True, fingerprint=False,
            tests=False, guard=False, wired=False):
    p = Path(tmp) / name
    (p / "_bmad" / "bmm").mkdir(parents=True)
    (p / "scripts").mkdir()
    (p / ".claude" / "hooks").mkdir(parents=True)
    if cfg is not None:
        (p / "_bmad" / "bmm" / "config.yaml").write_text(cfg)
    if lane is not None:
        f = p / "scripts" / "deploy.sh"
        f.write_text(lane)
        if lane_exec:
            f.chmod(0o755)
    if fingerprint:
        (p / "scripts" / "deploy-fingerprint.sh").write_text("#!/bin/sh\necho abc\n")
    if tests:
        (p / "scripts" / "deploy-lane.test.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    if guard:
        (p / ".claude" / "hooks" / "deploy_lane_guard.py").write_text("# guard\n")
    if wired:
        (p / ".claude" / "settings.local.json").write_text(
            json.dumps({"hooks": {"PreToolUse": [{"command": "python3 .claude/hooks/deploy_lane_guard.py"}]}}))
    return p


with tempfile.TemporaryDirectory() as tmp:
    print("── applicability ──")
    r = cdl.assess_project(project(tmp, "none", cfg="deploy:\n  method: none\n"))
    check("method: none is N/A, never a gap", "N/A", r["state"])

    r = cdl.assess_project(project(tmp, "undeclared", cfg="deploy:\n  bmad_contract: skip\n"))
    check("a deploy block naming no method/platform/lane and no script is NOT DECLARED",
          "NOT DECLARED", r["state"])

    r = cdl.assess_project(project(tmp, "noconfig"))
    check("no config at all is NOT DECLARED (silence is not compliance)", "NOT DECLARED", r["state"])

    r = cdl.assess_project(project(tmp, "scriptonly", lane=COMPLIANT_LANE))
    check("a scripts/deploy.sh with no config block is still assessed (applicable)",
          True, r["state"] in ("MET", "GAPS"))

    print("── the reference shape ──")
    full = project(tmp, "full", cfg="deploy:\n  method: manual_cli\n  lane: scripts/deploy.sh\n",
                   lane=COMPLIANT_LANE, fingerprint=True, tests=True, guard=True, wired=True)
    r = cdl.assess_project(full)
    check("a compliant lane is MET", "MET", r["state"])
    check("every row verified — nothing on trust", [], r.get("on_trust"))
    check("all ten rows present", sorted(cdl.REQUIREMENTS), sorted(r["rows"]))

    r = cdl.assess_project(full, run_tests=True)
    check("--run-tests runs the suite and stays MET when it is green", "MET", r["state"])
    (full / "scripts" / "deploy-lane.test.sh").write_text("#!/usr/bin/env bash\nexit 1\n")
    r = cdl.assess_project(full, run_tests=True)
    check("a RED suite is a gap under --run-tests", "missing", r["rows"]["R9"])
    check("...but only a found-file check without --run-tests", "verified",
          cdl.assess_project(full)["rows"]["R9"])

    print("── each requirement, missing direction ──")
    base = dict(cfg="deploy:\n  method: manual_cli\n", fingerprint=True, tests=True, guard=True, wired=True)
    r = cdl.assess_project(project(tmp, "noexec", lane=COMPLIANT_LANE, lane_exec=False, **base))
    check("R1: a non-executable lane is declared, not verified", "declared", r["rows"]["R1"])
    r = cdl.assess_project(project(tmp, "nolane", lane=None, **base))
    check("R1: no lane file at all is missing", "missing", r["rows"]["R1"])
    check("R1 missing ⇒ GAPS", "GAPS", r["state"])

    def without(pattern):
        return "\n".join(l for l in COMPLIANT_LANE.splitlines() if pattern not in l)

    for rid, pat in [("R2", "origin_sha"), ("R3", "head_sha=\"$(git rev-parse HEAD)"),
                     ("R4", "upload_root"), ("R5", "onverg"), ("R7", "deploy.lock"),
                     ("R8", "trap ")]:
        r = cdl.assess_project(project(tmp, f"no{rid}", lane=without(pat), **base))
        check(f"{rid} absent from the lane is missing", "missing", r["rows"][rid])

    r = cdl.assess_project(project(tmp, "nofp", lane=COMPLIANT_LANE,
                                   **{**base, "fingerprint": False}))
    check("R6: lane invokes the fingerprint but the script is absent — missing", "missing", r["rows"]["R6"])
    r = cdl.assess_project(project(tmp, "notests", lane=COMPLIANT_LANE, **{**base, "tests": False}))
    check("R9: no test file is missing", "missing", r["rows"]["R9"])
    r = cdl.assess_project(project(tmp, "noguard", lane=COMPLIANT_LANE, **{**base, "guard": False, "wired": False}))
    check("R10: no guard file is missing", "missing", r["rows"]["R10"])
    r = cdl.assess_project(project(tmp, "unwired", lane=COMPLIANT_LANE, **{**base, "wired": False}))
    check("R10: guard present but not in settings is declared (a claim), not verified",
          "declared", r["rows"]["R10"])
    check("...and declared alone does not make a GAP", "MET", r["state"])

    print("── markers: an unfamiliar provider is assessable, on trust ──")
    r = cdl.assess_project(project(tmp, "marker", lane=MARKER_LANE, **base))
    check("marker-only lane is MET", "MET", r["state"])
    check("...and every marker row is reported as on trust (R6: marker, no script)",
          ["R2", "R3", "R4", "R5", "R6", "R7", "R8"], r["on_trust"])
    check("R6 with a marker but no fingerprint script is still declared, not verified",
          "declared", r["rows"]["R6"])

    print("── config reader ──")
    blk = cdl.read_deploy_block(project(tmp, "cfg", cfg=(
        "project_name: x\ndeploy:\n  bmad_contract: skip   # comment\n  method: manual_cli # prod is Railway\n"
        "  lane: 'scripts/ship.sh'\n\nautonomous_mode: true\n")))
    check("flat keys read, comments stripped, quotes stripped, block ends at the next top key",
          {"bmad_contract": "skip", "method": "manual_cli", "lane": "scripts/ship.sh"}, blk)
    check("a custom lane path is honoured", "scripts/ship.sh",
          cdl.applicability(Path(tmp) / "cfg", blk)[1])

    print("── fleet summary + CLI ──")
    s = cdl.summarise([cdl.assess_project(full), cdl.assess_project(Path(tmp) / "none"),
                       cdl.assess_project(Path(tmp) / "undeclared")])
    check("fleet is GAPS while anything is NOT DECLARED", "GAPS", s["fleet"])
    s = cdl.summarise([cdl.assess_project(Path(tmp) / "marker"), cdl.assess_project(Path(tmp) / "none")])
    check("fleet MET with only MET + N/A", "STANDARD MET", s["fleet"])
    check("on-trust rows surface at fleet level",
          {"marker": ["R2", "R3", "R4", "R5", "R6", "R7", "R8"]}, s["on_trust"])

    r = subprocess.run([sys.executable, str(CHECKER), "--project", str(full), "--run-tests"],
                       capture_output=True, text=True)
    check("CLI exit 1 on a red suite under --run-tests (R9 red file still on disk)", 1, r.returncode)
    (full / "scripts" / "deploy-lane.test.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    r = subprocess.run([sys.executable, str(CHECKER), "--project", str(full), "--json"],
                       capture_output=True, text=True)
    check("CLI exit 0 on MET", 0, r.returncode)
    check("--json is parseable and names the standard", cdl.STANDARD, json.loads(r.stdout)["standard"])
    r = subprocess.run([sys.executable, str(CHECKER)], capture_output=True, text=True)
    check("usage error without --project/--all", 2, r.returncode)

print()
if failed:
    print(f"FAIL — {failed} failing, {passed} passing")
    sys.exit(1)
print(f"ok — {passed} cases, both directions")
