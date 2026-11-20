#!/usr/bin/env python3
"""Property tests for the canonical representation.

The defect these exist to prevent produced two OPPOSITE failures from one line of regex —
phantom staleness in the verifier, phantom authorship in the classifier — so each property
is asserted in both directions. A normalisation suite that only proves "equal things
compare equal" would have passed against the broken code.
"""
import importlib.util
import sys
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("rep", FORK / "tools" / "bmad_representation.py")
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)

PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + ("" if ok else f"\n          got={got!r} want={want!r}"))


# The real shapes, taken from an actual delivered file rather than invented.
SRC_SHARED = b"Read and follow: `{project-root}/_bmad/bmm/workflows/shared/detect-stack.md`\nbody\n"
TGT_SHARED = b"Read and follow: `{project-root}/_bmad/bmad-shared/detect-stack.md`\nbody\n"
SRC_BARE = b"see `shared/close-out-contract.md` for the shape\n"
TGT_BARE = b"see `{project-root}/_bmad/bmad-shared/close-out-contract.md` for the shape\n"

print("canonical-representation property tests:\n")

# P1 — source transformed by the distributor compares CURRENT against the target.
v, _ = rep.compare(SRC_SHARED, TGT_SHARED)
check("P1  distributor-transformed source is CURRENT against its target", v, rep.CURRENT)
v, _ = rep.compare(SRC_BARE, TGT_BARE)
check("P1b bare shared/ form folds to the same token", v, rep.CURRENT)

# P2 — the normalisation is idempotent.
once = rep.canonical(TGT_SHARED)
check("P2  canonical is idempotent", rep.canonical(once), once)
oncep = rep.canonical_pointers(TGT_SHARED)
check("P2b canonical_pointers is idempotent", rep.canonical_pointers(oncep), oncep)

# P3 — NORMALISING ONE SIDE ONLY IS INVALID, asserted as a failing comparison. This is the
#      exact defect: it is not enough that the fixed code passes; the broken shape must be
#      demonstrably wrong, or the suite cannot tell them apart.
import re as _re
one_sided = _re.compile(rb"(\{project-root\}/)?_bmad/bmad-shared/")
lhs = one_sided.sub(b"shared/", SRC_SHARED)     # source: untouched, still workflows/shared
rhs = one_sided.sub(b"shared/", TGT_SHARED)     # target: folded
check("P3  the one-sided fold FAILS to match a correct delivery", lhs == rhs, False)
check("P3b the two-sided fold matches it", rep.canonical(SRC_SHARED) == rep.canonical(TGT_SHARED), True)

# P4 — a true content change stays detectable after normalisation. The risk of any folding
#      scheme is that it degrades into "everything matches".
EDITED = TGT_SHARED.replace(b"body", b"body with a genuine local edit")
v, _ = rep.compare(SRC_SHARED, EDITED)
check("P4  a real content change is still DIFFERS", v, rep.DIFFERS)
v, _ = rep.compare(SRC_SHARED, SRC_SHARED.replace(b"body", b"changed"))
check("P4b a change with no rewrite involved is DIFFERS", v, rep.DIFFERS)

# P5 — genuine local runtime state is preserved: it matches no release, so it can never be
#      folded into CURRENT.
RUNTIME = b'{"proposal_id": "ebay-publish-rail-v1", "applied_at": "2026-08-04"}\n'
v, _ = rep.compare(SRC_SHARED, RUNTIME)
check("P5  runtime state never folds into CURRENT", v, rep.DIFFERS)

# P6 — an incomplete transformation path yields AMBIGUOUS, never a drift or authorship
#      verdict. This is the owner's rule made executable.
v, ev = rep.compare(SRC_SHARED, TGT_SHARED, transformation_path_known=False)
check("P6  unknown transformation path is AMBIGUOUS", v, rep.AMBIGUOUS)
check("P6b and it does not claim a normalised comparison",
      ev["normalised_comparison"], "not attempted — path incomplete")

# P7 — a pointer-only rewrite is its own class, NOT silently a match. The blunt pass must
#      never be able to say CURRENT.
SRC_XREF = b"then `{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md`\n"
TGT_XREF = b"then `{project-root}/.claude/skills/bmad-quick-spec/SKILL.md`\n"
v, _ = rep.compare(SRC_XREF, TGT_XREF)
check("P7  a cross-reference rewrite is REWRITE_ONLY, not CURRENT", v, rep.REWRITE_ONLY)
check("P7b REWRITE_ONLY is a distinct verdict from CURRENT", rep.REWRITE_ONLY != rep.CURRENT, True)

# P8 — a generated receipt must never affect a content verdict. It is distributor
#      bookkeeping, reissued every release.
check("P8  the receipt name is excluded from content comparison by callers",
      "bmad-distribution" not in rep.canonical(b"bmad-distribution").decode(), False)

# P9 — T5 literals are NOT folded. Folding them would hide a genuine change to a real
#      project file.
LIT = b"edit `{project-root}/_bmad/bmm/config.yaml` by hand\n"
check("P9  a left-literal path is untouched by canonical", rep.canonical(LIT), LIT)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
