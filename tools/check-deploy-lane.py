#!/usr/bin/env python3
"""check-deploy-lane — does a project's deploy lane meet STD-DEPLOY-002?

    python3 tools/check-deploy-lane.py --project /path/to/repo
    python3 tools/check-deploy-lane.py --all            # every enabled target in ~/.bmad-targets.json
    python3 tools/check-deploy-lane.py --all --json
    python3 tools/check-deploy-lane.py --project . --run-tests   # R9 runs the suite, not just finds it

Exit: 0 = every assessed project MET or N/A · 1 = gaps / not declared / unknown · 2 = usage.

THE STANDARD is shared/deploy-lane-standard.md (fork: custom/workflows/shared/). This file is
the probe half. Every verdict here is a statement about ARTEFACTS — a pattern in a file — and
the standard's Ceiling section says what that does and does not prove. A row reads:

    verified   the artefact shows the behaviour
    declared   only a `# STD-DEPLOY-002 R<n>: <how>` marker vouches for it — a claim
    missing    neither

The checker never guesses a provider. An unfamiliar lane is assessable through markers and
is reported as MET-on-trust when it passes only that way.

Pure functions (assess_project, probe_*) take paths and text; nothing here talks to a
provider or the network. `tools/test/test-check-deploy-lane.py` drives both directions.

TRACKED FILES ARE READ FROM origin/<default> WHEN THE PROJECT IS A GIT REPO. The registry
points at each project's shared main checkout, which is where parallel sessions park their
in-flight branches — on 2026-09-04 cash-recovery's was three weeks behind, and its
working-tree deploy.sh lacked the checks its origin/main carried. A checker that read the
working tree would have reported the reference lane as failing its own standard. The
LOCAL ref is used (no fetch): a checker must not touch the network, so "behind" means
"behind what this machine last fetched" — stated here so a green is not over-read.
Settings files are machine-local and untracked; those are read from the working tree.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

STANDARD = "STD-DEPLOY-002"
DEFAULT_LANE = "scripts/deploy.sh"
FINGERPRINT = "scripts/deploy-fingerprint.sh"
GUARD = ".claude/hooks/deploy_lane_guard.py"
REGISTRY = Path.home() / ".bmad-targets.json"

REQUIREMENTS = {
    "R1": "one lane script, executable",
    "R2": "pinned at the remote default tip, shipping paths clean",
    "R3": "commit stamp derived from git rev-parse HEAD on every deploy",
    "R4": "upload/build root asserted to be this directory",
    "R5": "post-upload convergence read-back with a verdict",
    "R6": "source fingerprint compared inside the running environment",
    "R7": "concurrent deploys serialised by a lock",
    "R8": "orphaned stamp restored on failure",
    "R9": "golden tests, both directions",
    "R10": "raw ship command guarded (deploy_lane_guard.py present and wired)",
}


# ── tracked reads ─────────────────────────────────────────────────────────────

def _git(project: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def default_ref(project: Path) -> str | None:
    """`origin/<default>` when it resolves locally, else None (working tree it is)."""
    for ref in ("origin/main", "origin/master"):
        if _git(project, "rev-parse", "--verify", "--quiet", ref) is not None:
            return ref
    return None


def tracked_text(project: Path, rel: str) -> str | None:
    """The file's content at the default ref, else None if untracked there."""
    ref = default_ref(project)
    if ref is None:
        p = project / rel
        return p.read_text(errors="ignore") if p.is_file() else None
    return _git(project, "show", f"{ref}:{rel}")


def tracked_mode(project: Path, rel: str) -> str | None:
    """'100755' / '100644' at the default ref, else None."""
    ref = default_ref(project)
    if ref is None:
        p = project / rel
        if not p.is_file():
            return None
        return "100755" if os.access(p, os.X_OK) else "100644"
    out = _git(project, "ls-tree", ref, "--", rel)
    return out.split()[0] if out and out.strip() else None


def tracked_names(project: Path, subdir: str, pattern: str) -> list[str]:
    ref = default_ref(project)
    if ref is None:
        d = project / subdir
        return sorted(p.name for p in d.glob(pattern)) if d.is_dir() else []
    out = _git(project, "ls-tree", "--name-only", f"{ref}:{subdir}") or ""
    import fnmatch
    return sorted(n for n in out.split() if fnmatch.fnmatch(n, pattern))


# ── config ───────────────────────────────────────────────────────────────────

def read_deploy_block(project: Path) -> dict | None:
    """The `deploy:` mapping from _bmad/bmm/config.yaml, flat keys only.

    Deliberately not a YAML parser: the block is one level deep by contract, and a
    dependency-free reader is what lets this run on a machine with nothing installed.
    Returns None when the config or the block is absent.
    """
    text = tracked_text(project, "_bmad/bmm/config.yaml")
    if text is None:
        cfg = project / "_bmad" / "bmm" / "config.yaml"
        if not cfg.is_file():
            return None
        text = cfg.read_text(errors="ignore")
    out, inside = {}, False
    for raw in text.splitlines():
        if re.match(r"^deploy:\s*(#.*)?$", raw):
            inside, out = True, {}
            continue
        if inside:
            if raw.strip() == "" or raw.startswith("#"):
                continue
            if not raw.startswith((" ", "\t")):
                break
            m = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$", raw)
            if not m:
                continue
            val = m.group(2).split("#", 1)[0].strip().strip("'\"")
            out[m.group(1)] = val
    return out if inside else None


def applicability(project: Path, block: dict | None) -> tuple[str, str]:
    """-> (state, lane_relpath). state ∈ {applicable, n/a, not-declared}."""
    lane = (block or {}).get("lane") or DEFAULT_LANE
    method = (block or {}).get("method", "").lower()
    if method in {"none", "not-deployed", "not_deployed", "no"}:
        return "n/a", lane
    declared = bool((block or {}).get("method") or (block or {}).get("platform")
                    or (block or {}).get("lane"))
    if declared or tracked_text(project, lane) is not None:
        return "applicable", lane
    return "not-declared", lane


# ── probes ───────────────────────────────────────────────────────────────────

def _marker(text: str, rid: str) -> bool:
    return re.search(rf"{STANDARD}\s+{rid}\b", text) is not None


def _verdict(verified: bool, text: str, rid: str) -> str:
    if verified:
        return "verified"
    return "declared" if _marker(text, rid) else "missing"


def probe_lane(project: Path, lane: str, script: str) -> dict:
    """R1–R8 over the lane script text; R6 also needs the fingerprint file."""
    v = {}
    mode = tracked_mode(project, lane)
    v["R1"] = "verified" if mode == "100755" else ("declared" if mode else "missing")
    v["R2"] = _verdict(
        bool(re.search(r"rev-parse\s+origin/", script)) and "rev-parse HEAD" in script
        and bool(re.search(r"git status --porcelain", script)),
        script, "R2")
    v["R3"] = _verdict(
        bool(re.search(r"(COMMIT|SHA|sha)[A-Z_a-z]*\s*=.*rev-parse HEAD", script))
        or bool(re.search(r"head_sha=\"?\$\(git rev-parse HEAD\)", script)),
        script, "R3")
    v["R4"] = _verdict(bool(re.search(r"upload_root", script)), script, "R4")
    v["R5"] = _verdict(
        bool(re.search(r"[Cc]onverg", script)) and "superseded" in script
        and "diverged" in script and "behind" in script, script, "R5")
    v["R6"] = _verdict(
        tracked_text(project, FINGERPRINT) is not None and "deploy-fingerprint.sh" in script,
        script, "R6")
    v["R7"] = _verdict(
        bool(re.search(r"deploy\.lock|flock\b", script)), script, "R7")
    v["R8"] = _verdict(
        bool(re.search(r"trap\s+\S+\s+EXIT", script)) and "restore" in script.lower(),
        script, "R8")
    return v


def probe_tests(project: Path, run: bool) -> tuple[str, str]:
    names = tracked_names(project, "scripts", "deploy*.test.sh")
    if not names:
        return "missing", "no scripts/deploy*.test.sh"
    if not run:
        return "verified", ", ".join(names)
    # --run-tests executes the WORKING-TREE copy: that is the only one that can run.
    for n in names:
        t = project / "scripts" / n
        if not t.is_file():
            return "missing", f"{n} is tracked but absent from the working tree"
        r = subprocess.run(["bash", str(t)], cwd=project, capture_output=True, text=True)
        if r.returncode != 0:
            return "missing", f"{n} FAILED: {(r.stdout + r.stderr).strip().splitlines()[-1:] or ['(no output)']}"
    return "verified", f"{len(names)} suite(s) green"


def probe_guard(project: Path) -> tuple[str, str]:
    if tracked_text(project, GUARD) is None and not (project / GUARD).is_file():
        return "missing", "no .claude/hooks/deploy_lane_guard.py"
    wired = []
    for name in ("settings.json", "settings.local.json"):
        s = project / ".claude" / name
        if s.is_file() and "deploy_lane_guard" in s.read_text(errors="ignore"):
            wired.append(name)
    if not wired:
        return "declared", "guard present, not named in .claude/settings*.json"
    return "verified", "wired in " + ", ".join(wired)


# ── assessment ───────────────────────────────────────────────────────────────

def assess_project(project: Path, run_tests: bool = False) -> dict:
    project = project.resolve()
    out = {"project": str(project), "id": project.name, "state": "UNKNOWN",
           "lane": None, "rows": {}, "notes": {}}
    try:
        block = read_deploy_block(project)
        app, lane = applicability(project, block)
        out["lane"] = lane
        out["declared"] = block or {}
        if app == "n/a":
            out["state"] = "N/A"
            out["notes"]["why"] = "deploy.method: none — this project does not ship"
            return out
        if app == "not-declared":
            out["state"] = "NOT DECLARED"
            out["notes"]["why"] = ("no deploy.method / platform / lane in _bmad/bmm/config.yaml "
                                   f"and no {DEFAULT_LANE}")
            return out
        script = tracked_text(project, lane) or ""
        rows = probe_lane(project, lane, script)
        rows["R9"], out["notes"]["R9"] = probe_tests(project, run_tests)
        rows["R10"], out["notes"]["R10"] = probe_guard(project)
        out["rows"] = rows
        out["state"] = "GAPS" if any(r == "missing" for r in rows.values()) else "MET"
        out["on_trust"] = [k for k, r in rows.items() if r == "declared"]
        return out
    except Exception as e:  # noqa: BLE001 — a checker must not crash a health run
        out["notes"]["error"] = f"{type(e).__name__}: {e}"
        return out


def load_targets() -> list[dict]:
    if not REGISTRY.is_file():
        return []
    data = json.loads(REGISTRY.read_text())
    return [t for t in data.get("targets", []) if t.get("enabled", True)]


def assess_all(run_tests: bool = False) -> dict:
    results = [assess_project(Path(t["path"]), run_tests) for t in load_targets()]
    return summarise(results)


def summarise(results: list[dict]) -> dict:
    met = [r for r in results if r["state"] == "MET"]
    gaps = [r for r in results if r["state"] == "GAPS"]
    undeclared = [r for r in results if r["state"] == "NOT DECLARED"]
    na = [r for r in results if r["state"] == "N/A"]
    unknown = [r for r in results if r["state"] == "UNKNOWN"]
    fleet = "STANDARD MET" if not (gaps or undeclared or unknown) else "GAPS"
    return {"standard": STANDARD, "fleet": fleet, "results": results,
            "met": [r["id"] for r in met], "gaps": [r["id"] for r in gaps],
            "not_declared": [r["id"] for r in undeclared], "n_a": [r["id"] for r in na],
            "unknown": [r["id"] for r in unknown],
            "on_trust": {r["id"]: r.get("on_trust", []) for r in met if r.get("on_trust")}}


# ── render ───────────────────────────────────────────────────────────────────

def render(summary: dict) -> str:
    lines = [f"{STANDARD} — deploy lane: {summary['fleet']}"]
    width = max([len(r["id"]) for r in summary["results"]] or [8]) + 2
    for r in summary["results"]:
        if r["state"] in ("MET", "GAPS"):
            detail = " ".join(f"{k}:{'✓' if v == 'verified' else '~' if v == 'declared' else '✗'}"
                              for k, v in r["rows"].items())
        else:
            detail = r["notes"].get("why") or r["notes"].get("error", "")
        lines.append(f"  {r['id']:<{width}}{r['state']:<13}{detail}")
        if r["state"] == "GAPS":
            for k, v in r["rows"].items():
                if v == "missing":
                    lines.append(f"  {'':<{width}}  {k} missing — {REQUIREMENTS[k]}"
                                 + (f" ({r['notes'][k]})" if k in r["notes"] else ""))
    if summary["on_trust"]:
        lines.append("  on trust (declared, not verified): "
                     + "; ".join(f"{k} {','.join(v)}" for k, v in summary["on_trust"].items()))
    lines.append("  legend: ✓ verified · ~ declared (a claim) · ✗ missing")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--project", help="one repo root")
    p.add_argument("--all", action="store_true", help="every enabled target in ~/.bmad-targets.json")
    p.add_argument("--run-tests", action="store_true", help="R9: run the suites, not just find them")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    if bool(a.project) == bool(a.all):
        p.error("give exactly one of --project or --all")
    summary = (summarise([assess_project(Path(a.project), a.run_tests)])
               if a.project else assess_all(a.run_tests))
    print(json.dumps(summary, indent=2) if a.json else render(summary))
    return 0 if summary["fleet"] == "STANDARD MET" else 1


if __name__ == "__main__":
    sys.exit(main())
