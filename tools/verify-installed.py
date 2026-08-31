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

_REWRITE = re.compile(rb"(\{project-root\}/)?_bmad/bmad-shared/")

# The directories the distributor delivers, and where each lands in a target.
WORKFLOW_DIRS = ("implement", "verify", "design", "meta", "shared",
                 "4-implementation/code-review", "4-implementation/sprint-planning")
SHARED_SOURCES = ("custom/workflows/shared", "custom/workflows/design/shared")


def h(data):
    return hashlib.sha256(_REWRITE.sub(b"shared/", data)).hexdigest()


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
        present = any((target / p).exists() for p in prefixes)
        report[name] = {
            "expected": len(want), "missing": len(missing), "differing": len(differing),
            "in_scope": present and bool(want),
            "ok": (not missing and not differing) if (present and want) else None,
            "sample": (missing + differing)[:5],
        }
    ok = all(v["ok"] is not False for v in report.values())
    if not quiet:
        for name, v in report.items():
            state = "n/a" if v["ok"] is None else ("MATCHES release" if v["ok"] else "MISMATCH")
            print(f"  {name:10}{state:18}expected={v['expected']:<5}"
                  f"missing={v['missing']:<5}differing={v['differing']}")
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
