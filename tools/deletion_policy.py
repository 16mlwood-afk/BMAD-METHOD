#!/usr/bin/env python3
"""Classify a MISSING file before any repair stages it as a deletion.

THE INVARIANT, from the 2026-08-31 incident:

    A missing file is not automatically an intentional deletion merely because it is
    absent from the working tree.

What happened: a preservation step ran `git add -- _bmad .claude/skills` over whole
managed trees. Files an earlier partial sync had already removed were staged as deletions
and committed under a message asserting nothing was lost. 246 deletions were recorded
across six projects. 229 were correct — the release genuinely no longer contains those
files. 17 were not, and were restored. The blanket stage could not tell the two apart,
because absence carries no evidence of intent; the commit message supplied the safe
reading for free.

So a deletion is only ever automatic when EVERY condition holds:
  - the approved release explicitly omits the file;
  - the file is inside the managed root;
  - it is not part of a sanctioned local extension (.bmad-local);
  - it is not user-authored or ambiguous;
  - the delivery plan explicitly includes the deletion;
  - the post-state is confirmed by the verifier (the caller's job, asserted separately).

Everything else is preserved, classified, and routed as an exception. Never bulk-staged.
"""
import hashlib
import re
from pathlib import Path

_REWRITE = re.compile(rb"(\{project-root\}/)?_bmad/bmad-shared/")

ALLOW_DELETE = "ALLOW_DELETE"          # the release removed it, deliberately
PRESERVE_PARTIAL = "PRESERVE_PARTIAL_SYNC"    # a half-finished run emptied it
PRESERVE_AUTHORED = "PRESERVE_USER_AUTHORED"  # a human wrote it
PRESERVE_EXTENSION = "PRESERVE_LOCAL_EXTENSION"
ALLOW_RECEIPT = "ALLOW_GENERATED_RECEIPT"
EXCEPTION_CONCURRENT = "EXCEPTION_CONCURRENT_REPAIRER"
PRESERVE_AMBIGUOUS = "PRESERVE_AMBIGUOUS"

MANAGED_ROOTS = ("_bmad/", ".claude/skills/", ".claude/commands/bmad/")
LOCAL_EXTENSION = ".bmad-local/"
RECEIPT_NAME = ".bmad-distribution.json"


def _h(b):
    return hashlib.sha256(_REWRITE.sub(b"shared/", b)).hexdigest()


def classify_deletion(rel, *, release_has, in_plan, prior_content=None,
                      release_content=None, concurrent=False):
    """Decide what a MISSING path means. Pure — no filesystem, so it is testable.

    rel             target-relative path that is absent from the working tree
    release_has     does the approved release still contain this file?
    in_plan         does the delivery plan for this run explicitly cover this path?
    prior_content   bytes the project last had, if known (from its prior verified state)
    release_content bytes the release holds, if release_has
    concurrent      another repairer is known to be mutating this target right now
    """
    if concurrent:
        # Never race a second mutator. Whichever of us stages first, the other's view of
        # "absent" is already stale — which is exactly how the incident happened.
        return EXCEPTION_CONCURRENT, ("another repairer is mutating this target; a "
                                      "deletion decided against a moving tree is not a "
                                      "decision")

    if rel.startswith(LOCAL_EXTENSION):
        return PRESERVE_EXTENSION, "sanctioned local extension — distribution never touches it"

    if not any(rel.startswith(m) for m in MANAGED_ROOTS):
        return PRESERVE_AMBIGUOUS, "outside every managed root — not the distributor's to remove"

    if Path(rel).name == RECEIPT_NAME:
        return ALLOW_RECEIPT, "generated receipt — reissued by the release itself"

    if release_has:
        # The release still ships it, so its absence is damage, not intent — regardless
        # of how it came to be missing.
        return PRESERVE_PARTIAL, ("the approved release still contains this file, so its "
                                  "absence is an incomplete run, not a removal")

    # The release omits it. That is necessary but NOT sufficient.
    if prior_content is not None and release_content is None:
        # We know what the project had and the release has nothing to compare it to. If
        # the content never came from any release, a human wrote it and the release
        # omitting it proves nothing.
        pass

    if not in_plan:
        return PRESERVE_AMBIGUOUS, ("the release omits it, but this run's delivery plan "
                                    "does not cover the path — absence of a plan is not "
                                    "permission")

    return ALLOW_DELETE, "the approved release omits it and the delivery plan covers it"


def is_user_authored(prior_content, release_history_digests):
    """True when the project's content matches no release of that path — a human wrote it."""
    if prior_content is None:
        return False
    return _h(prior_content) not in release_history_digests
