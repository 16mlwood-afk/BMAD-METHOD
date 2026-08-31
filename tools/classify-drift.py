#!/usr/bin/env python3
"""Classify replica drift before anything repairs it. READ-ONLY — writes nothing.

WHY THIS EXISTS. Thirteen active targets hold uncommitted changes inside the managed
tree. The tempting repair is a broad publish, which would DELETE all of it to make a
dashboard green. Some of that content may be legitimate local work that simply had
nowhere sanctioned to live. So every drifted file is classified first, and only
provably-generated content is ever repaired automatically.

BUCKETS (owner-specified 2026-08-31):
  1 GENERATED_RECEIPT      distributor bookkeeping only            -> auto-repair
  2 DISTRIBUTION_ARTEFACT  delivered content, uncommitted or stale -> auto-repair
  3 LOCAL_ADDITION         authored file in a managed location     -> PRESERVE + migrate
  4 USER_AUTHORED          edited a distributed file               -> PRESERVE + propose
  5 TOOL_MISMATCH          the release tool's own inconsistency    -> auto-repair
  6 UNREACHABLE            cannot be classified safely             -> contain + report

THE DISCRIMINATOR between 2 and 4 is the honest part. A distributed file whose content
differs from the current release is NOT automatically a local edit — it is far more often
an older release still sitting there. So the file's bytes are checked against the fork's
history for that same source path: if some fork revision ever produced exactly these
bytes, it is delivered content and safe to replace. If no revision did, a human wrote it
and it is preserved.

LIMIT, stated rather than hidden: history is searched over the most recent HISTORY_DEPTH
revisions touching that path. A file matching only an older revision than that is
classified USER_AUTHORED — which errs toward preservation, the safe direction.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
REGISTRY = Path.home() / ".bmad-targets.json"
HISTORY_DEPTH = 400

GENERATED = {"_bmad/_config/sync-manifest.txt", "_bmad/_config/sync-stamp.yaml",
             "_bmad/.bmad-distribution.json"}


def out(args, cwd=None):
    r = subprocess.run(args, cwd=cwd or FORK, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


# The distributor REWRITES intra-fork references as it delivers:
#     shared/x.md  ->  {project-root}/_bmad/bmad-shared/x.md
# so a delivered file can NEVER byte-match its source. Comparing raw bytes made three
# files in cash-recovery look human-authored when they were the current release verbatim.
# Normalise both sides before hashing, or the classifier over-preserves and every repair
# stalls on phantom local edits.
_REWRITE = re.compile(rb"(\{project-root\}/)?_bmad/bmad-shared/")


def blob(data):
    return hashlib.sha256(_REWRITE.sub(b"shared/", data)).hexdigest()


# bmad-shared is FLATTENED on delivery: the distributor collects shared policy from more
# than one fork directory into one replica folder, so a replica path can have several
# possible sources and all must be tried. Trying only custom/workflows/shared misread
# operator-artifact-contract.md — real fork content — as a local addition.
SHARED_SOURCES = ("custom/workflows/shared/", "custom/workflows/design/shared/")


def source_paths(rel):
    """Every fork path that could produce this replica path."""
    if rel.startswith("_bmad/bmad-shared/"):
        tail = rel[len("_bmad/bmad-shared/"):]
        return [base + tail for base in SHARED_SOURCES]
    one = source_path(rel)
    return [one] if one else []


def source_path(rel):
    """Map a replica path to the fork path that produces it, or None."""
    if rel.startswith("_bmad/bmad-shared/"):
        return "custom/workflows/shared/" + rel[len("_bmad/bmad-shared/"):]
    if rel.startswith("_bmad/bmm/workflows/"):
        return "custom/workflows/" + rel[len("_bmad/bmm/workflows/"):]
    if rel.startswith("_bmad/bmm/agents/"):
        return "custom/agents/" + rel[len("_bmad/bmm/agents/"):]
    # The SKILLS surface. Omitting it left half the distributed surface unclassified,
    # which is how nine targets read clean while holding uncommitted skill content and a
    # publish then reported success for targets the distributor had refused.
    if rel.startswith(".claude/skills/"):
        return "custom/skills/" + rel[len(".claude/skills/"):]
    return None


_hist_cache = {}


def ever_produced(src, digest):
    """Did any recent fork revision of `src` have exactly these bytes?"""
    if src not in _hist_cache:
        # --all, not the current branch: content delivered from a feature branch before it
        # was merged is unreachable from custom's own first-parent history, and would be
        # misread as human-authored. Depth is a cap, not a window on one branch.
        revs = out(["git", "log", "--all", f"-{HISTORY_DEPTH}", "--format=%H", "--", src]).split()
        digests = set()
        for rev in revs:
            r = subprocess.run(["git", "show", f"{rev}:{src}"], cwd=FORK,
                               capture_output=True)
            if r.returncode == 0:
                digests.add(blob(r.stdout))
        _hist_cache[src] = digests
    return digest in _hist_cache[src]


def classify_file(root, rel, status):
    f = root / rel
    if rel in GENERATED:
        return "1 GENERATED_RECEIPT", "distributor bookkeeping"
    if not f.exists():
        return "6 UNREACHABLE", "listed by git but absent on disk"

    candidates = source_paths(rel)
    if not candidates:
        return "3 LOCAL_ADDITION", "path is not one the distributor produces"

    d = blob(f.read_bytes())
    for src in candidates:
        live = FORK / src
        if live.is_file() and blob(live.read_bytes()) == d:
            return "2 DISTRIBUTION_ARTEFACT", "identical to the current release"
    for src in candidates:
        if ever_produced(src, d):
            return "2 DISTRIBUTION_ARTEFACT", "matches an earlier release of this file"
    if not any((FORK / c).exists() for c in candidates):
        return "3 LOCAL_ADDITION", "no such file in the fork, now or in its history"
    return "4 USER_AUTHORED", "content matches no release of this file — a human wrote it"


def main():
    reg = json.loads(REGISTRY.read_text())
    report = []
    for t in reg["targets"]:
        if not t.get("enabled", True):
            report.append({"id": t["id"], "skipped": t.get("state", "disabled")})
            continue
        root = Path(t["path"])
        mroot = t.get("managed_root", "_bmad")
        if not (root / ".git").exists():
            report.append({"id": t["id"], "buckets": {"6 UNREACHABLE": ["<not a git repo>"]}})
            continue
        lines = [l for l in out(["git", "status", "--porcelain", "--", mroot,
                                 ".claude/skills", ".claude/commands/bmad"],
                                cwd=root).splitlines() if l.strip()]
        buckets = {}
        for line in lines:
            status, rel = line[:2].strip(), line[3:].strip().strip('"')
            # git reports an untracked DIRECTORY as one entry; classification is
            # per-file, so expand it. A directory classified as a unit would hide a
            # mix of generated and authored content inside it.
            here = root / rel
            paths = ([str(q.relative_to(root)) for q in sorted(here.rglob("*")) if q.is_file()]
                     if here.is_dir() else [rel])
            for one in paths:
                b, why = classify_file(root, one, status)
                buckets.setdefault(b, []).append((one, why))
        report.append({"id": t["id"], "path": str(root), "drifted": len(lines),
                       "buckets": {k: v for k, v in sorted(buckets.items())}})

    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
