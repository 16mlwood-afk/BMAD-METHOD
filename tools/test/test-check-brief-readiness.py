#!/usr/bin/env python3
"""Golden suite for tools/check-brief-readiness.py — BOTH directions.

Run: python3 tools/test/test-check-brief-readiness.py
     npm run test:brief-readiness

WHY BOTH DIRECTIONS. Most rows here assert SILENCE. A probe suite measured only on what it
catches drifts into an indiscriminate detector, and an instrument that fires on everything
is switched off — at which point it protects nothing. The fire/silent split IS the test.

THE TWO PILOT DEFECT ROWS ARE CANDIDATE FIXES PENDING F1 RUN 2.
D1 (`sold` matching inside `soldPrice`) and D2 (the `confirm` homonym) were CONFIRMED as
defects by the F1 pilot run under pre-registered predictions. That run was declared invalid
for headline measurement because of a fixture-schema defect, so the DEFECTS are measured and
the FIXES are not. These rows pin the intended new behaviour; they are not evidence that the
fixes improve real-brief precision. Validation awaits a corrected, pre-registered F1 run 2.

Each defect therefore carries TWO rows:
  · the preserved original regression case, which must now FIRE, and
  · a non-regression case, which must stay SILENT — proving the fix did not simply break
    the thing the probe already got right.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "check-brief-readiness.py")

FM = """---
target_slug: fixture
brief_status: active
mode: fresh-design
page_mode: operational
route: /fixture
{frames}
---
"""

# A body that determines every probed concept. Used as the clean control, and as the base
# other fixtures mutate — so a fixture tests ONE thing, and the pilot's "the control was not
# a control" defect cannot recur silently.
COMPLETE_BODY = """
# Fixture surface

## 7. Surface Inventory

| Frame | Trigger | Must contain |
|---|---|---|
| `queue` | route load | the worklist |
| `queue--detail` | row select | the record |

The surface defaults to the unshipped subset when it opens. The operator can advance to the
next unit without returning to the list. The list paginates at 50 rows per page.

Disposal is irreversible, so the operator must confirm before it commits, and the dialog
restates what will be lost.

A unit that has been sold is terminal and has left the workflow.

For every control, the pending state and each outcome must be drawn.

## States

| State | Meaning |
|---|---|
| awaiting | not yet handled |
| handled | handled |

These states are mutually exclusive and partition the population.
"""


def write(tmp, name, body, frames="frames: [queue, queue--detail]"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(FM.format(frames=frames) + body)
    return path


def run(path, *flags):
    proc = subprocess.run([sys.executable, TOOL, path, *flags],
                          capture_output=True, text=True)
    return proc


def fired_ids(path):
    proc = run(path, "--json")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    return {f["probe_id"] for f in report["findings"] if not f["informational"]}, report


FAILURES = []


def check(name, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(name)


def main():
    tmp = tempfile.mkdtemp(prefix="brief-readiness-")
    print("check-brief-readiness golden suite\n")

    # ── clean control — everything determined, nothing fires ────────────────────
    control = write(tmp, "fx0-complete.md", COMPLETE_BODY)
    ids, rep = fired_ids(control)
    check("C0  clean control fires NOTHING", ids == set(), f"fired: {sorted(ids)}")
    check("C0b clean control exits 0 under --strict",
          run(control, "--strict").returncode == 0)

    # ── D1 · SUBSTRING (candidate fix pending F1 run 2) ─────────────────────────
    # Preserved original regression case: "sold" occurs ONLY inside `soldPrice`, and the
    # brief carries no terminal-state requirement. Pre-fix this probe was SILENT.
    d1 = write(tmp, "fx7-substring-sold.md", """
The row shows `soldPrice` for each unit. `soldPrice` is populated by the listing feed.
""")
    ids, _ = fired_ids(d1)
    check("D1  `soldPrice` no longer satisfies terminal-states", "terminal-states" in ids)
    check("D1b `sold_price` no longer satisfies terminal-states",
          "terminal-states" in fired_ids(write(tmp, "fx7b.md", "The `sold_price` column."))[0])

    # Non-regression: a genuine terminal-state requirement still passes.
    d1ok = write(tmp, "fx7c-terminal-real.md",
                 COMPLETE_BODY.replace("has been sold is terminal", "has been sold is final"))
    ids, _ = fired_ids(d1ok)
    check("D1c a real terminal-state sentence still SILENCES the probe",
          "terminal-states" not in ids, f"fired: {sorted(ids)}")

    # ── D2 · HOMONYM (candidate fix pending F1 run 2) ───────────────────────────
    # Preserved original regression case, verbatim from the pilot fixture.
    d2 = write(tmp, "fx6-homonym-confirm.md", """
The confirmation guard must confirm a specific payload identified by content digest.
""")
    ids, _ = fired_ids(d2)
    check("D2  confirm-the-payload homonym no longer satisfies the probe",
          "irreversible-confirmation" in ids)

    # Non-regression: a real confirmation requirement still passes.
    d2ok = write(tmp, "fx6b-confirm-real.md", """
Disposing of a unit is irreversible, so the owner must confirm and the dialog restates
what will be destroyed.
""")
    ids, _ = fired_ids(d2ok)
    check("D2b a real irreversible-action confirm still SILENCES the probe",
          "irreversible-confirmation" not in ids, f"fired: {sorted(ids)}")

    # ── P1 frames ───────────────────────────────────────────────────────────────
    ids, _ = fired_ids(write(tmp, "fx-frames-inline-missing.md", "No frame names here.\n"))
    check("P1  inline frames declared but unreferenced FIRES", "frames-unreferenced" in ids)

    blockfm = "frames:\n  - queue\n  - queue--detail"
    ids, _ = fired_ids(write(tmp, "fx-frames-block-missing.md", "No frame names here.\n",
                             frames=blockfm))
    check("P1b BLOCK-list frames are parsed at all (were invisible before)",
          "frames-unreferenced" in ids)

    ids, _ = fired_ids(write(tmp, "fx-frames-block-ok.md", COMPLETE_BODY, frames=blockfm))
    check("P1c block-list frames referenced in the body stay SILENT",
          "frames-unreferenced" not in ids)

    # ── P2 partition claim ──────────────────────────────────────────────────────
    nopart = COMPLETE_BODY.replace(
        "These states are mutually exclusive and partition the population.", "")
    ids, _ = fired_ids(write(tmp, "fx-nopartition.md", nopart))
    check("P2  a state table with no partition claim FIRES", "state-set-no-partition" in ids)
    ids, _ = fired_ids(write(tmp, "fx-partition.md", COMPLETE_BODY))
    check("P2b an explicit partition claim stays SILENT", "state-set-no-partition" not in ids)

    # ── P3 word-boundary discipline in the other direction ──────────────────────
    ids, _ = fired_ids(write(tmp, "fx-advanced.md",
                             "Advanced filters sit above the table.\n"))
    check("P3  `Advanced` does not satisfy per-item navigation",
          "per-item-navigation" in ids)
    ids, _ = fired_ids(write(tmp, "fx-advance.md",
                             "The operator can advance to the next unit from the detail.\n"))
    check("P3b a real advance requirement stays SILENT", "per-item-navigation" not in ids)

    # ── P4 money co-enumeration ─────────────────────────────────────────────────
    ids, _ = fired_ids(write(tmp, "fx-money.md",
                             "| unit | price | net | recovery | fees |\n"))
    check("P4  three+ money semantics on one line FIRES", "money-co-enumeration" in ids)
    ids, _ = fired_ids(write(tmp, "fx-money-ok.md", "| unit | price |\n"))
    check("P4b a single money field stays SILENT", "money-co-enumeration" not in ids)

    # ── body SHA lifecycle ──────────────────────────────────────────────────────
    a = write(tmp, "sha-a.md", COMPLETE_BODY)
    b = write(tmp, "sha-b.md", COMPLETE_BODY, frames="frames: [queue, queue--detail]\nauthor: someone-else")
    c = write(tmp, "sha-c.md", COMPLETE_BODY + "\nOne more required sentence.\n")
    sha = lambda p: run(p, "--body-sha").stdout.strip()  # noqa: E731
    check("S1  frontmatter change does NOT move the body SHA", sha(a) == sha(b))
    check("S2  a body edit DOES move the body SHA", sha(a) != sha(c))
    check("S3  the JSON report carries the same SHA", fired_ids(a)[1]["body_sha256"] == sha(a))

    # ── CLI contract ────────────────────────────────────────────────────────────
    check("X1  fired probes still exit 0 by default (warn-only)", run(d1).returncode == 0)
    check("X2  --strict exits 1 when a probe fired", run(d1, "--strict").returncode == 1)
    bad = subprocess.run([sys.executable, TOOL, "--json"], capture_output=True, text=True)
    check("X3  no brief argument exits 2", bad.returncode == 2)
    missing = subprocess.run([sys.executable, TOOL, os.path.join(tmp, "nope.md")],
                             capture_output=True, text=True)
    check("X4  unreadable brief exits 2", missing.returncode == 2)
    check("X5  the report states the warn-only phase",
          "WARN-ONLY" in fired_ids(a)[1]["phase"])

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
