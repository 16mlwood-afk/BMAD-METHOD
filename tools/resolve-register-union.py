#!/usr/bin/env python3
"""Resolve a conflicted append-only register (docs/fork-gaps.md) by unioning ENTRIES.

WHY. fork-gaps.md is append-only: every branch that logs a gap appends entries at the end,
so every branch merge collides there. It is the second half of the pair that stalled fork
delivery for five weeks (the first is package.json).

WHY ENTRY-WISE, NOT LINE-WISE. On 2026-08-31 a hand resolution concatenated the conflict
hunks ours-then-theirs. Every entry id survived and the file still looked plausible — but the
hunks interleaved mid-entry, so FG-2026-08-10-01 was left with an unclosed yaml block and its
three sections reparented under FG-2026-08-12-01. Only markdownlint caught it, via a duplicate
sibling heading. An id-count check passes straight through that failure. So the unit here is
the ENTRY, never the line: entries cannot be split because they are never taken apart.

WHAT IT REFUSES (exits non-zero, changes nothing):
  - the preamble (everything above the first entry) differs between the sides — that is a
    contract change, not an append;
  - an entry with the same heading has a DIFFERENT body on each side — one side edited an
    existing entry, which is a real disagreement;
  - malformed conflict markers, or an entry id that would be lost.

Usage:  resolve-register-union.py <path/to/register.md>
Exit:   0 resolved (file rewritten) · 1 refused (file untouched)
"""
import difflib
import re
import sys

# An entry begins at a heading naming a gap id or a date. Deliberately NOT any heading:
# `### Incident`, `### Why it is structural` and `### Fix candidates` are sections INSIDE an
# entry, and treating them as boundaries is what would split an entry apart again.
ENTRY_RE = re.compile(r"^#{2,3} (FG-\d{4}-\d{2}-\d{2}|\d{4}-\d{2}-\d{2})")
ID_RE = re.compile(r"FG-\d{4}-\d{2}-\d{2}-[0-9A-Za-z]+")


def split_conflicts(raw):
    ours, theirs, mode, seen = [], [], None, False
    for line in raw.splitlines(keepends=True):
        if line.startswith("<<<<<<<"):
            if mode is not None:
                return None
            mode, seen = "ours", True
            continue
        if line.startswith("=======") and mode == "ours":
            mode = "theirs"
            continue
        if line.startswith(">>>>>>>"):
            if mode != "theirs":
                return None
            mode = None
            continue
        if mode == "ours":
            ours.append(line)
        elif mode == "theirs":
            theirs.append(line)
        else:
            ours.append(line)
            theirs.append(line)
    if mode is not None or not seen:
        return None
    return "".join(ours), "".join(theirs)


def parse(text):
    """-> (preamble, [(heading, body_text)]) preserving order."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if ENTRY_RE.match(ln)]
    if not starts:
        return text, []
    preamble = "".join(lines[: starts[0]])
    entries = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        entries.append((lines[i].rstrip("\n"), "".join(lines[i:end])))
    return preamble, entries


def main(path):
    raw = open(path).read()
    sides = split_conflicts(raw)
    if sides is None:
        print("refused: malformed or absent conflict markers", file=sys.stderr)
        return 1

    pre_a, ents_a = parse(sides[0])
    pre_b, ents_b = parse(sides[1])

    if pre_a != pre_b:
        print("refused: the register preamble differs between the sides — that is a "
              "contract change, not an append", file=sys.stderr)
        return 1

    # An entry that differs is still an APPEND if one side is the other with lines added
    # and none removed or changed — a later datapoint appended to a standing entry, which
    # is how this register is actually written. Take the superset. Anything else (a line
    # removed, or reworded) is a genuine edit on one side and not this script's call.
    def superset(x, y):
        """Return the longer body if it is y-plus-insertions, else None."""
        for short, long_ in ((x, y), (y, x)):
            ops = difflib.SequenceMatcher(
                None, short.splitlines(), long_.splitlines(), autojunk=False
            ).get_opcodes()
            if all(tag in ("equal", "insert") for tag, *_ in ops):
                return long_
        return None

    by_a = dict(ents_a)
    resolved = {}
    for head, body in ents_b:
        if head in by_a and by_a[head] != body:
            merged_body = superset(by_a[head], body)
            if merged_body is None:
                print(f"refused: entry {head[:70]!r} differs on each side by more than an "
                      "append — a line was removed or reworded, which is a real edit",
                      file=sys.stderr)
                return 1
            resolved[head] = merged_body

    seen, merged = set(), []
    for head, body in ents_a + ents_b:
        if head in seen:
            continue
        seen.add(head)
        merged.append(resolved.get(head, body))

    out = pre_a + "".join(merged)

    if "<<<<<<<" in out or ">>>>>>>" in out:
        print("refused: conflict markers survive in the output", file=sys.stderr)
        return 1

    before = set(ID_RE.findall(sides[0])) | set(ID_RE.findall(sides[1]))
    lost = before - set(ID_RE.findall(out))
    if lost:
        print(f"refused: entry ids would be lost: {sorted(lost)}", file=sys.stderr)
        return 1

    open(path, "w").write(out)
    print(f"resolved register — {len(merged)} entries "
          f"({len(merged) - len(ents_a)} added from the other side), "
          f"{len(set(ID_RE.findall(out)))} ids, none lost")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
