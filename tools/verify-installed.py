#!/usr/bin/env python3
"""Independently verify that a target actually holds the approved release. READ-ONLY.

WHY. On 2026-08-31 the release tool reported fourteen projects delivered. The distributor
had refused most of them and exited 0 anyway; the tool believed the exit code, wrote each
refused target a receipt, and thirteen of fourteen receipts were false. A receipt the
release tool just wrote is not evidence, and neither is an exit code.

So this verifier trusts NONE of: the distributor's exit code, the wrapper's return code,
the receipt, or the distributor's own sync-manifest. It reads the RELEASE WORKTREE and the
INSTALLED TREE and compares content, per surface.

Normalisation: the distributor rewrites intra-fork references on delivery
(shared/x.md -> {project-root}/_bmad/bmad-shared/x.md), so a delivered file never
byte-matches its source. Both sides are normalised before hashing — otherwise every file
reads as mismatched and the verifier is useless.

Exit 0 = every checked surface matches the release. Exit 1 = it does not.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

# NORMALISE THE SOURCE SIDE BY EVERY REWRITE THE DISTRIBUTOR CAN APPLY, not just the one
# it applies most often. The first cut folded only `_bmad/bmad-shared/`, which rewrites the
# INSTALLED side and leaves the RELEASE side alone — so a correctly delivered file hashed
# as differing forever. It reported seven stale shared-policy files across three targets
# that were not stale at all, and very nearly bought a rewrite of a distributor that had no
# bug in it. Caught by a parallel session; confirmed here against bison-ops, where the
# entire difference was one line:
#     installed  {project-root}/_bmad/bmad-shared/detect-stack.md
#     release    {project-root}/_bmad/bmm/workflows/shared/detect-stack.md
# Every shared location the distributor can emit folds to ONE token, so both sides land on
# the same string whichever form they carry.
# The fork ALSO refers to shared policy by its own bare `shared/x.md` form, so that has to
# fold to the same token or the source side keeps a string the installed side no longer
# has. Folding only the _bmad forms doubled the false positives rather than removing them.
_REWRITE = re.compile(
    rb"(\{project-root\}/)?(_bmad/(bmad-shared|bmm/workflows/design/shared"
    rb"|bmm/workflows/shared)|shared)/")

# A second rewrite class exists that a prefix fold cannot express: on a skills-native
# target a workflow cross-reference becomes a SKILL path, changing the file name as well as
# the directory. Rather than pretend that away, a file that still differs is compared again
# with every backticked {project-root} pointer removed. If it then matches, the only
# difference was a rewritten pointer — reported as REWRITE-ONLY: neither hidden, nor
# counted as stale content.
_ANYPATH = re.compile(rb"`\{project-root\}/[^`]*`")

# The directories the distributor delivers, and where each lands in a target.
WORKFLOW_DIRS = ("implement", "verify", "design", "meta", "shared",
                 "4-implementation/code-review", "4-implementation/sprint-planning")
SHARED_SOURCES = ("custom/workflows/shared", "custom/workflows/design/shared")


def h(data):
    return hashlib.sha256(_REWRITE.sub(b"<SHARED>/", data)).hexdigest()


def h_nopaths(data):
    """Hash with every distributor-rewritable pointer collapsed."""
    return hashlib.sha256(
        _ANYPATH.sub(b"`<PATH>`", _REWRITE.sub(b"<SHARED>/", data))).hexdigest()


def _sources_for(release, rel):
    """Candidate release paths that could produce this target-relative path."""
    if rel.startswith(".claude/skills/"):
        return [release / "custom" / "skills" / rel[len(".claude/skills/"):]]
    if rel.startswith("_bmad/bmm/workflows/"):
        return [release / "custom" / "workflows" / rel[len("_bmad/bmm/workflows/"):]]
    if rel.startswith("_bmad/bmad-shared/"):
        tail = rel[len("_bmad/bmad-shared/"):]
        return [release / b / tail for b in SHARED_SOURCES]
    return []


def expected(release, target=None):
    """-> {target-relative path: normalised hash} straight off the release worktree.

    LAYOUT-AWARE, and it has to be. Two layouts are live: a skills-native target receives
    shared policy in BOTH _bmad/bmad-shared/ and _bmad/bmm/workflows/shared/, while an
    old-layout target receives it only in the latter. Expecting bmad-shared everywhere
    reported 34 phantom missing files on a target that was correctly up to date — an
    over-reporting verifier is as useless as a lying receipt, just in the other direction.
    The flattened copy is expected only where the target already has that directory.
    """
    exp = {}
    for d in WORKFLOW_DIRS:
        base = release / "custom" / "workflows" / d
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if f.is_file() and ".git" not in f.parts:
                rel = f.relative_to(release / "custom" / "workflows")
                exp[f"_bmad/bmm/workflows/{rel}"] = h(f.read_bytes())
    if target is not None and (Path(target) / "_bmad" / "bmad-shared").is_dir():
        for s in SHARED_SOURCES:
            base = release / s
            if not base.is_dir():
                continue
            for f in base.rglob("*"):
                if f.is_file() and ".git" not in f.parts:
                    exp[f"_bmad/bmad-shared/{f.relative_to(base)}"] = h(f.read_bytes())
    skills = release / "custom" / "skills"
    if skills.is_dir():
        for f in skills.rglob("*"):
            if f.is_file() and ".git" not in f.parts:
                exp[f".claude/skills/{f.relative_to(skills)}"] = h(f.read_bytes())
    return exp


def verify(target, release, quiet=False):
    """-> (ok, per-surface report). Compares installed content to the release."""
    target = Path(target)
    exp = expected(Path(release), target)
    surfaces = {"workflow": ("_bmad/bmm/workflows", "_bmad/bmad-shared"),
                "skills": (".claude/skills",)}
    report = {}
    for name, prefixes in surfaces.items():
        want = {k: v for k, v in exp.items() if k.startswith(prefixes)}
        missing, differing = [], []
        for rel, digest in want.items():
            f = target / rel
            if not f.is_file():
                # The FLATTENED shared copy (_bmad/bmad-shared) is a CURATED subset the
                # distributor chooses — not every shared file lands there. Demanding
                # completeness re-derives that curation and reported real, up-to-date
                # targets as missing files they were never meant to have. Content of what
                # IS installed is still verified; completeness is checked only on the
                # surfaces whose delivered set can be derived exactly (workflows, skills).
                if not rel.startswith("_bmad/bmad-shared/"):
                    missing.append(rel)
            elif h(f.read_bytes()) != digest:
                differing.append(rel)

        # A surface the distributor does not deliver to this target (no files expected,
        # or the whole tree absent) is NOT a failure — it is out of scope. Reporting it
        # as a mismatch would make every old-layout project permanently unverifiable.
        # Split the differences: a file whose only remaining difference is a rewritten
        # pointer is correctly delivered and must not read as stale content.
        rewrite_only = []
        if differing:
            still = []
            for rel in differing:
                src = next((c for c in _sources_for(Path(release), rel) if c.is_file()), None)
                if src and h_nopaths((target / rel).read_bytes()) == h_nopaths(src.read_bytes()):
                    rewrite_only.append(rel)
                else:
                    still.append(rel)
            differing = still

        # SCOPE, and `any` was wrong here. The workflow surface lives in two places, and a
        # fully skills-native target has _bmad/bmad-shared but NO _bmad/bmm/workflows at
        # all — by design, not by omission. With `any`, one present location put the whole
        # surface in scope and every workflow file was then reported missing: cash-recovery
        # read as 254 missing while missing nothing. Require the surface's PRIMARY location
        # (the first prefix) to exist; a target without it is out of scope, not broken.
        present = (target / prefixes[0]).exists()
        report[name] = {
            "expected": len(want), "missing": len(missing), "differing": len(differing),
            "rewrite_only": len(rewrite_only),
            "in_scope": present and bool(want),
            "ok": (not missing and not differing) if (present and want) else None,
            "sample": (missing + differing)[:5],
        }
    ok = all(v["ok"] is not False for v in report.values())
    if not quiet:
        for name, v in report.items():
            state = "n/a" if v["ok"] is None else ("MATCHES release" if v["ok"] else "MISMATCH")
            print(f"  {name:10}{state:18}expected={v['expected']:<5}"
                  f"missing={v['missing']:<5}differing={v['differing']:<5}"
                  f"rewrite-only={v['rewrite_only']}")
            for s in v["sample"]:
                print(f"      ! {s}")
    return ok, report


def main():
    if len(sys.argv) != 3:
        print("usage: verify-installed.py <target-root> <release-worktree>")
        return 2
    ok, _ = verify(sys.argv[1], sys.argv[2])
    print("VERIFIED" if ok else "NOT VERIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
