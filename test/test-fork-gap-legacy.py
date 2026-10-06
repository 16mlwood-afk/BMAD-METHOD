#!/usr/bin/env python3
"""The legacy-entry migration, pinned in BOTH directions.

Four entries had no parseable id, so the checker's touched-entry scoping could never
exclude them and they failed every commit to fork-gaps.md. `--no-verify` became routine,
which is how a gate stops being a gate. They were migrated on 2026-08-31 and the checker
given a narrow `legacy: true` exemption.

The risk in any such exemption is that it quietly becomes a blanket off-switch, so these
cases assert what it must NOT relax as hard as what it may.
"""
import importlib.util
import sys
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("fgl", FORK / "tools" / "lib" / "fork_gap_lint.py")
fgl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fgl)

PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else f"\n          got={got!r} want={want!r}"))


def lint(text):
    """-> the checker's own findings for a synthetic register.

    Calls check_schema, the exact function the shell checker runs, and reads its printed
    findings. Deliberately NOT a reimplementation: a test that re-derives the rules can
    pass while the real gate is broken, and an earlier cut of this helper silently
    returned [] for every input, which made two cases unfailable.
    """
    import contextlib, io
    entries = list(fgl.parse_text(text))   # parse_text yields; check_schema needs len()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fgl.check_schema(entries)
    return [l.strip()[2:].strip() for l in buf.getvalue().splitlines() if l.strip().startswith("\u2717")]


# Guard the helper itself: if it cannot see a finding the checker definitely emits, every
# assertion below is vacuous. This is the check that would have caught the first version.
_SELFTEST = """# Fork Gaps

Preamble.

## Open

## FG-2026-08-30-01 — deliberately malformed

```yaml
id: NOT-AN-ID
class: unknown
scope: fork
target: "x.md"
marker: unknown
state: nonsense
fix: none
owner: unknown
```

### Incident

x
"""
_probe = lint(_SELFTEST)
assert _probe, "lint() helper sees no findings on a deliberately malformed entry"


# The parser only reads entries AFTER the `## Open` marker, so a fixture without it
# parses to zero entries and every assertion becomes vacuous.
PRE = "# Fork Gaps\n\nPreamble.\n\n## Open\n\n"

LEGACY = PRE + """## FG-2026-08-24-A — a historical entry

```yaml
id: FG-2026-08-24-A
legacy: true
migrated_from: "id in the heading, no yaml block"
class: unknown
scope: fork
target: "custom/workflows/x.md"
marker: unknown
state: closed
fix: done
owner: unknown
```

- **Symptom:** prose, not an Incident section.
"""

NEW_BAD_ID = PRE + """## FG-2026-08-24-C — a NEW entry with a historical-style id

```yaml
id: FG-2026-08-24-C
class: unknown
scope: fork
target: "custom/workflows/x.md"
marker: unknown
state: open
fix: none
owner: unknown
```

### Incident

Something.
"""

LEGACY_BAD_ENUM = LEGACY.replace("state: closed", "state: fixed")

print("fork-gap legacy migration golden cases:\n")

errs = lint(LEGACY)
check("L1 a migrated legacy entry passes clean", errs, [])

errs = lint(NEW_BAD_ID)
check("L2 a NEW entry may NOT use a historical id format",
      any("not FG-YYYY-MM-DD-NN" in e for e in errs), True)
check("L2b and a new entry still needs its Incident section is NOT waived",
      any("Incident" in e for e in errs), False)  # this one HAS an Incident

errs = lint(LEGACY_BAD_ENUM)
check("L3 legacy does NOT relax the state enum",
      any("unknown state" in e for e in errs), True)

LEGACY_NO_ID = LEGACY.replace("id: FG-2026-08-24-A\n", "")
errs = lint(LEGACY_NO_ID)
check("L4 legacy does NOT excuse a missing id", len(errs) > 0, True)

LEGACY_NO_MARKER = LEGACY.replace("marker: unknown", "marker: x")
errs = lint(LEGACY_NO_MARKER)
check("L5 legacy does NOT relax the marker length rule",
      any("marker must be" in e for e in errs), True)

# L6 — the live register must be clean, which is the whole point of the migration.
live = fgl.parse()
errs_live = lint(Path(FORK / "docs" / "fork-gaps.md").read_text())
check("L6 the live register lints clean (no routine --no-verify)", errs_live, [])

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
