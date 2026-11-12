#!/usr/bin/env python3
"""Resolve a conflicted package.json when — and only when — the conflict is additive.

WHY. Every fork branch that adds a test adds a `test:<thing>` script AND wires it into the
aggregate `test` chain. Two such branches always collide on those exact lines, always in the
same shape, and the correct answer is always "keep both". On 2026-08-31 that one pattern was
the ONLY thing standing between three finished branches and `custom`. Resolving it by hand
each time is how fork work ends up parked on a branch for five weeks.

WHAT IT REFUSES. This is a union, not a merge strategy. It exits non-zero, changing nothing,
if the two sides disagree about anything rather than merely each adding something:
  - a script key present on both sides with DIFFERENT values (except `test`, whose chain is
    unioned step-wise) — that is a real disagreement and a human has to pick;
  - any conflict outside `.scripts`;
  - a malformed conflict region.
Refusing is the safe outcome: the caller aborts the rebase and reports the branch.

Usage:  resolve-package-union.py <path/to/package.json>
Exit:   0 resolved (file rewritten) · 1 refused (file untouched)
"""
import collections
import json
import sys


def split_conflicts(raw):
    """Return (ours, theirs) as full file texts, or None if markers are malformed."""
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


def chain_steps(chain):
    return [s.strip() for s in chain.split("&&") if s.strip()]


def main(path):
    raw = open(path).read()
    sides = split_conflicts(raw)
    if sides is None:
        print("refused: malformed or absent conflict markers", file=sys.stderr)
        return 1
    try:
        a = json.loads(sides[0], object_pairs_hook=collections.OrderedDict)
        b = json.loads(sides[1], object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as e:
        print(f"refused: a conflict side is not valid JSON ({e})", file=sys.stderr)
        return 1

    # Everything outside .scripts must already agree — otherwise this is not the shape
    # this resolver is allowed to touch.
    for side in (a, b):
        side.setdefault("scripts", collections.OrderedDict())
    if {k: v for k, v in a.items() if k != "scripts"} != {k: v for k, v in b.items() if k != "scripts"}:
        differing = sorted(k for k in set(a) | set(b)
                           if k != "scripts" and a.get(k) != b.get(k))
        print(f"refused: the sides disagree outside .scripts: {differing}", file=sys.stderr)
        return 1

    sa, sb = a["scripts"], b["scripts"]
    merged = collections.OrderedDict(sa)
    for k, v in sb.items():
        if k in merged and merged[k] != v and k != "test":
            print(f"refused: script {k!r} has a different value on each side — "
                  "that is a real disagreement, not an addition", file=sys.stderr)
            return 1
        merged.setdefault(k, v)

    # Union the aggregate chain step-wise, keeping every test:* step ahead of the first
    # lint/validate/check step, which is the order both sides already use.
    out, seen = [], set()
    for step in chain_steps(sa.get("test", "")) + chain_steps(sb.get("test", "")):
        if step not in seen:
            seen.add(step)
            out.append(step)
    if out:
        pivot = next((i for i, s in enumerate(out) if not s.startswith("npm run test")), len(out))
        tests = out[:pivot] + [s for s in out[pivot:] if s.startswith("npm run test")]
        rest = [s for s in out[pivot:] if not s.startswith("npm run test")]
        merged["test"] = " && ".join(tests + rest)

    a["scripts"] = collections.OrderedDict(sorted(merged.items(), key=lambda kv: kv[0]))
    open(path, "w").write(json.dumps(a, indent=2) + "\n")

    added = sorted(set(sb) - set(sa)) + sorted(set(sa) - set(sb))
    print(f"resolved package.json — {len(a['scripts'])} scripts, union-added: {added or 'none'}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
