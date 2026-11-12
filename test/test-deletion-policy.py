#!/usr/bin/env python3
"""The seven deletion cases, pinned. A missing file is not an intentional deletion."""
import importlib.util
import sys
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("dp", FORK / "tools" / "deletion_policy.py")
dp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dp)

PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else f"\n          got={got!r} want={want!r}"))


print("deletion-classification golden cases:\n")

# D1 — removed by an OLD PARTIAL SYNC. The release still has it, so absence is damage.
#      This is the exact 2026-08-31 case: 17 files, blanket-staged as deletions.
v, _ = dp.classify_deletion("_bmad/bmm/workflows/design/x.md", release_has=True, in_plan=True)
check("D1 partial-sync casualty is PRESERVED", v, dp.PRESERVE_PARTIAL)

# D2 — intentionally removed by the approved release, and in this run's plan.
v, _ = dp.classify_deletion(".claude/skills/gone/SKILL.md", release_has=False, in_plan=True)
check("D2 a release-removed file may be deleted", v, dp.ALLOW_DELETE)

# D2b — release omits it but the plan does not cover the path. Absence of a plan is not
#       permission; this is what turns a scoped repair into a bulk wipe.
v, _ = dp.classify_deletion(".claude/skills/gone/SKILL.md", release_has=False, in_plan=False)
check("D2b release-omits but out-of-plan is PRESERVED", v, dp.PRESERVE_AMBIGUOUS)

# D3 — a user-authored file inside the managed root.
digests = {dp._h(b"a release version")}
check("D3a content matching no release reads as user-authored",
      dp.is_user_authored(b"something a human wrote", digests), True)
check("D3b content matching a release does not",
      dp.is_user_authored(b"a release version", digests), False)

# D4 — a sanctioned local extension. Distribution must never touch it.
v, _ = dp.classify_deletion(".bmad-local/notes.md", release_has=False, in_plan=True)
check("D4 a sanctioned local extension is PRESERVED", v, dp.PRESERVE_EXTENSION)

# D5 — the generated receipt. Reissued by the release, safe to remove.
v, _ = dp.classify_deletion("_bmad/.bmad-distribution.json", release_has=False, in_plan=True)
check("D5 the generated receipt may be deleted", v, dp.ALLOW_RECEIPT)

# D6 — a concurrent repairer. Outranks everything: a decision against a moving tree is
#      not a decision. This is the condition the fleet lock exists to make impossible.
v, _ = dp.classify_deletion(".claude/skills/gone/SKILL.md", release_has=False,
                            in_plan=True, concurrent=True)
check("D6 concurrent repairer forces an EXCEPTION", v, dp.EXCEPTION_CONCURRENT)
v, _ = dp.classify_deletion("_bmad/x.md", release_has=True, in_plan=True, concurrent=True)
check("D6b concurrency outranks even a clear preserve", v, dp.EXCEPTION_CONCURRENT)

# D7 — ambiguous: outside every managed root. Not the distributor's to remove.
v, _ = dp.classify_deletion("src/app/page.tsx", release_has=False, in_plan=True)
check("D7 a path outside the managed roots is PRESERVED", v, dp.PRESERVE_AMBIGUOUS)

# D8 — the safe default: nothing is ALLOW_DELETE unless the release omits it AND the plan
#      covers it AND it is inside a managed root. Assert the negative directly.
allowed = [dp.classify_deletion(p, release_has=rh, in_plan=ip)[0]
           for p, rh, ip in (("_bmad/a.md", True, True), ("_bmad/a.md", True, False),
                             ("_bmad/a.md", False, False), (".bmad-local/a.md", False, True),
                             ("other/a.md", False, True))]
check("D8 none of the unsafe combinations reach ALLOW_DELETE",
      dp.ALLOW_DELETE in allowed, False)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
