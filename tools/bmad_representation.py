#!/usr/bin/env python3
"""The single canonical representation for comparing distributed BMAD content.

THE RULE THIS EXISTS TO ENFORCE:

    A mismatch is a LEAD, not proof of content drift, stale delivery, authorship, or
    local work.

A file in a project is not a copy of its release source. The distributor REWRITES
references as it delivers, so a correctly delivered file never byte-matches its source.
Comparing the two without applying every producer-side transformation to BOTH sides does
not measure the fleet — it measures the comparison.

WHY ONE LIBRARY AND NOT A REGEX PER CONSUMER. The same one-sided fold was independently
present in the verifier, the drift classifier and the deletion policy. Fixing it in one
left it live in the other two, and the identical line failed in OPPOSITE directions:

    verifier    one-sided fold -> a delivered file never matches      -> phantom STALENESS
    classifier  one-sided fold -> content matching a release does not -> phantom AUTHORSHIP

The second is the dangerous one: it fabricates local work, so genuine repair is withheld
from files nobody wrote. It blocked repair on five projects for ten files, every one of
which matched the shipped release exactly.

THE TRANSFORMATION PATH every comparison must be able to state:

    release source
      -> producer transformation(s)      (T1-T5 below)
      -> installed target form
      -> consumer normalisation          (this module, applied to BOTH sides)
      -> comparison

If any leg is unknown for a file, the verdict is AMBIGUOUS. Not "stale", not
"user-authored".

PRODUCER TRANSFORMATIONS, taken from tools/port-workflows-to-skills.sh's own header —
the authority — rather than inferred from observed diffs:

  T1 shared policy    .../workflows/[design/]shared/P and bare shared/P
                        -> {project-root}/_bmad/bmad-shared/P
  T2 cross-workflow   .../workflows/<group>/<w>/{workflow.md|steps/X}
                        -> {project-root}/.claude/skills/bmad-<w>/{SKILL.md|X}
  T3 core workflow    {project-root}/_bmad/core/workflows/<w>/workflow.(md|xml)
                        -> {project-root}/.claude/skills/bmad-<w>/SKILL.md
  T4 self step refs   {project-root}/_bmad/bmm/workflows/<self>/steps/X -> ./X
  T5 left literal     config.yaml, docs/*, core/tasks/*   (NOT rewritten — never fold)

TWO LEVELS, deliberately. `canonical` folds only T1, which is exact and cannot hide a
content change. `canonical_pointers` also collapses every rewritable POINTER (T2/T3/T4)
and is materially blunter: a real edit inside a backticked path is folded away with it.
So it may NEVER decide that a file is current. It exists only to separate "differs solely
by a rewritten pointer" from "differs in content", and a caller must report that as its
own class rather than as a match.
"""
import hashlib
import re

# T1 — every shared-policy location the producer can emit, INCLUDING the fork's own bare
# `shared/` form. Folding only the _bmad forms leaves the SOURCE side carrying a string
# the installed side no longer has, which doubled the false positives (7 -> 14) rather
# than removing them.
_T1_SHARED = re.compile(
    rb"(\{project-root\}/)?(_bmad/(bmad-shared|bmm/workflows/design/shared"
    rb"|bmm/workflows/shared)|shared)/")

# T2/T3 — a rewritten pointer changes the FILE NAME as well as the directory, so no
# prefix fold can express it. Collapse the whole backticked pointer instead.
_T2_POINTER = re.compile(rb"`\{project-root\}/[^`]*`")

# T4 — a self step reference becomes relative on delivery.
_T4_SELFSTEP = re.compile(rb"`\./[A-Za-z0-9._-]+\.md`")

SHARED_TOKEN = b"<SHARED>/"
POINTER_TOKEN = b"`<POINTER>`"

#: T5 — paths the producer leaves literal. Folding these would hide a genuine change.
NEVER_FOLD = ("config.yaml", "/docs/", "core/tasks/")

CURRENT = "current"
REWRITE_ONLY = "rewrite-only"
DIFFERS = "differs"
AMBIGUOUS = "ambiguous"


def canonical(data: bytes) -> bytes:
    """Apply T1 to either side of a comparison. Exact: cannot mask a content change."""
    return _T1_SHARED.sub(SHARED_TOKEN, data)


def canonical_pointers(data: bytes) -> bytes:
    """T1 plus pointer collapse (T2/T3/T4). BLUNT — see the module docstring.

    Never use this to decide a file is CURRENT. Only to separate a pointer-rewrite
    difference from a content difference.
    """
    out = _T1_SHARED.sub(SHARED_TOKEN, data)
    out = _T2_POINTER.sub(POINTER_TOKEN, out)
    return _T4_SELFSTEP.sub(POINTER_TOKEN, out)


def digest(data: bytes) -> str:
    """THE canonical content digest. Every consumer uses this, never its own hash."""
    return hashlib.sha256(canonical(data)).hexdigest()


def digest_pointers(data: bytes) -> str:
    return hashlib.sha256(canonical_pointers(data)).hexdigest()


def compare(source: bytes, installed: bytes, *, transformation_path_known: bool = True):
    """-> (verdict, evidence). The evidence IS the required classification record.

    `transformation_path_known=False` forces AMBIGUOUS: an incomplete transformation path
    may never be reported as stale or as local work.
    """
    evidence = {
        "producer_transformations": "T1-T5 (see module docstring)",
        "normalisation_applied_to_source": "T1",
        "normalisation_applied_to_target": "T1",
        "raw_comparison": "equal" if source == installed else "differing",
    }
    if not transformation_path_known:
        evidence["normalised_comparison"] = "not attempted — path incomplete"
        evidence["verdict"] = AMBIGUOUS
        return AMBIGUOUS, evidence

    if digest(source) == digest(installed):
        evidence["normalised_comparison"] = "equal"
        evidence["verdict"] = CURRENT
        return CURRENT, evidence

    evidence["normalised_comparison"] = "differing"
    if digest_pointers(source) == digest_pointers(installed):
        evidence["pointer_collapsed_comparison"] = "equal"
        evidence["verdict"] = REWRITE_ONLY
        return REWRITE_ONLY, evidence

    evidence["pointer_collapsed_comparison"] = "differing"
    evidence["verdict"] = DIFFERS
    return DIFFERS, evidence


def evidence_block(path, source_repr, target_repr, verdict, evidence):
    """Render the classification-evidence record the owner requires on every claim."""
    return "\n".join([
        f"path: {path}",
        f"source release representation: {source_repr}",
        f"producer/distributor transformations: {evidence['producer_transformations']}",
        f"target installed representation: {target_repr}",
        f"verifier/classifier transformations: T1 (+T2/T3/T4 on the second pass)",
        f"normalisation applied to source: {evidence['normalisation_applied_to_source']}",
        f"normalisation applied to target: {evidence['normalisation_applied_to_target']}",
        f"raw comparison result: {evidence['raw_comparison']}",
        f"normalised comparison result: {evidence['normalised_comparison']}",
        f"verdict: {verdict}",
    ])
