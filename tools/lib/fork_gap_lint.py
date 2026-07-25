#!/usr/bin/env python3
"""fork_gap_lint.py — the ONE parser + the three checks for docs/fork-gaps.md.

Single source of truth for reading the typed ledger (schema v1,
docs/proposals/fork-gaps-schema-v1-DRAFT.md). Three shell entry points delegate here so
that a tightening applies to all of them at once — the same reason the previous
`fork-gap-paths.sh` existed:

    tools/check-fork-gap-schema.sh      -> schema      (all ERROR)
    tools/check-fork-gap-targets.sh     -> targets     (ERROR on scope:fork rot, else WARN)
    tools/check-fork-gap-stale-open.sh  -> stale-open  (ERROR at creation, WARN on sweep)

INVARIANT, inherited and non-negotiable: nothing here ever mutates the register, and
nothing here ever closes an entry. A marker proves a STRING exists, not that a gap is
fixed. Closing stays a human call made after reading the implementing section.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

# FORK_GAP_ROOT lets the hermetic test drive a sandbox tree; unset it resolves to the fork.
ROOT = os.environ.get("FORK_GAP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAPS = os.path.join(ROOT, "docs", "fork-gaps.md")

STATES = {"open", "blocked", "partly", "fork-fixed-distribution-owed", "superseded", "closed"}
SCOPES = {"fork", "project", "machine-local", "harness"}
REQUIRED = ("id", "class", "scope", "target", "marker", "state", "owner")
ID_RE = re.compile(r"^FG-\d{4}-\d{2}-\d{2}-\d{2}$")

# A heading may legitimately contain backticked brackets (`[Image #N]` is part of one title).
# A STATE BLOB is the migrated-away form: a backticked bracket group CLOSING THE LINE.
HEADING_BLOB_RE = re.compile(r"`\[.*\]`\s*$")


class Entry:
    def __init__(self, heading: str, line_no: int, header: dict, body: str, has_incident: bool):
        self.heading = heading
        self.line_no = line_no
        self.header = header
        self.body = body
        self.has_incident = has_incident

    @property
    def id(self) -> str:
        return self.header.get("id", f"(no id @ line {self.line_no})")


def parse(path: str = GAPS):
    """Yield an Entry per `## ` block after the `## Open` marker."""
    text = open(path).read()
    lines = text.split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Open")
    except StopIteration:
        return
    cur, cur_no, buf = None, 0, []
    for i in range(start + 1, len(lines) + 1):
        line = lines[i] if i < len(lines) else "## __EOF__"
        if line.startswith("## "):
            if cur is not None:
                yield _build(cur, cur_no, "\n".join(buf))
            cur, cur_no, buf = line, i + 1, []
        elif cur is not None:
            buf.append(line)


def _build(heading: str, line_no: int, body: str) -> Entry:
    header = {}
    m = re.search(r"```yaml\n(.*?)```", body, re.S)
    if m:
        for raw in m.group(1).split("\n"):
            if ":" not in raw:
                continue
            k, v = raw.split(":", 1)
            header[k.strip()] = v.strip().strip('"')
    return Entry(heading, line_no, header, body, "### Incident" in body)


# --------------------------------------------------------------------- checks

def _checkable(target: str) -> bool:
    """Is this target a path we can resolve inside the fork tree?

    Ported verbatim in spirit from tools/lib/fork-gap-paths.sh: deliberately conservative,
    near-zero false positives. Placeholders, globs, absolutes, prose and scope-prefixed
    non-fork targets are all skipped rather than guessed at.
    """
    t = target.strip()
    if not t or t == "unknown" or t.startswith(("project:", "machine:", "harness:")):
        return False
    if any(c in t for c in "…<>*{}~ "):
        return False
    if t.startswith("/"):
        return False
    if t.startswith(("custom/", "docs/", "tools/", ".githooks/")):
        return True
    return "/" not in t and t.endswith(".sh")


def check_schema(entries) -> int:
    errors, seen_ids = [], set()
    for e in entries:
        eid = e.id
        if HEADING_BLOB_RE.search(e.heading):
            errors.append(f"{eid}: heading carries a state blob — move it to the Work Status line")
        if not e.header:
            errors.append(f"{eid}: no ```yaml header block")
            continue
        for f in REQUIRED:
            if f not in e.header:
                errors.append(f"{eid}: missing required field `{f}`")
        hid = e.header.get("id", "")
        if hid and not ID_RE.match(hid):
            errors.append(f"{eid}: id `{hid}` is not FG-YYYY-MM-DD-NN")
        if hid in seen_ids:
            errors.append(f"{eid}: duplicate id")
        seen_ids.add(hid)

        state, scope = e.header.get("state", ""), e.header.get("scope", "")
        if state and state not in STATES:
            errors.append(f"{eid}: unknown state `{state}` (allowed: {', '.join(sorted(STATES))})")
        if scope and scope not in SCOPES and scope != "unknown":
            errors.append(f"{eid}: unknown scope `{scope}`")

        marker = e.header.get("marker", "")
        if marker == "n/a":
            if scope != "harness":
                errors.append(f"{eid}: `marker: n/a` is legal ONLY with scope: harness (this is {scope or 'unset'})")
        elif len(marker.strip()) < 3:
            errors.append(f"{eid}: marker must be >=3 non-space chars (blank/short markers match every file)")

        if state == "superseded" and not e.header.get("superseded_by"):
            errors.append(f"{eid}: state superseded requires superseded_by")
        if state == "blocked" and not e.header.get("blocked_by"):
            errors.append(f"{eid}: state blocked requires blocked_by naming an OBSERVABLE condition")
        if state == "fork-fixed-distribution-owed" and not e.header.get("distribution"):
            errors.append(f"{eid}: state fork-fixed-distribution-owed requires distribution")
        if not e.has_incident:
            errors.append(f"{eid}: no `### Incident` block")

    unknowns = sum(1 for e in entries for f in ("class", "scope", "target", "owner")
                   if e.header.get(f) == "unknown")
    for msg in errors:
        print(f"  ✗ {msg}")
    print(f"check-fork-gap-schema: {len(errors)} error(s) across {len(entries)} entry/entries.")
    if unknowns:
        print(f"  ⚠ {unknowns} field(s) still `unknown` — declared debt, not a blocker. Fill when known.")
    return 1 if errors else 0


def check_targets(entries) -> int:
    errors = warns = 0
    for e in entries:
        target, scope = e.header.get("target", ""), e.header.get("scope", "")
        if not _checkable(target):
            continue
        if os.path.exists(os.path.join(ROOT, target)):
            continue
        if scope == "fork":
            print(f"  ✗ {e.id}: scope:fork target does not resolve — `{target}` (pointer rot)")
            errors += 1
        else:
            print(f"  ⚠ {e.id}: target does not resolve here — `{target}` (scope: {scope or 'unset'})")
            warns += 1
    print(f"check-fork-gap-targets: {errors} error(s), {warns} warning(s).")
    return 1 if errors else 0


def _staged_new_ids() -> set:
    """Ids that exist in the staged register but did NOT exist in HEAD's version.

    Deliberately a SET DIFFERENCE against the pre-image, not a scan of `+` diff lines.
    "Added line" is not the same as "new entry": any bulk edit — a migration, a reformat,
    a mass status update — re-adds every `id:` line in the file, which would classify all
    47 pre-existing entries as newly created and turn every legitimate stale-open candidate
    into a blocking error. That fired on the schema-v1 migration commit itself.

    Fails OPEN: if git is unreadable, returns the empty set, so creation mode degrades to
    advisory rather than blocking. A detector that cannot see must not block.
    """
    try:
        head = subprocess.run(
            ["git", "show", "HEAD:docs/fork-gaps.md"],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
        staged = subprocess.run(
            ["git", "show", ":docs/fork-gaps.md"],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
    except Exception:
        return set()
    if staged.returncode != 0:
        return set()
    ids = lambda blob: set(re.findall(r"(?m)^id: (FG-[\d-]+)", blob))
    before = ids(head.stdout) if head.returncode == 0 else set()
    after = ids(staged.stdout)
    # PRE-SCHEMA PRE-IMAGE: if HEAD's register carries no ids at all, this diff is the format
    # migration itself — every entry looks new because ids are being introduced, not entries.
    # Novelty is undeterminable, so fail open. Narrow by construction: it can only hold while
    # the pre-image predates schema v1.
    if not before and after:
        return set()
    return after - before


#: INVARIANT I1 — THE REGISTER NEVER COUNTS ITSELF AS EVIDENCE.
#: A marker's own entry text lives in fork-gaps.md, so a target that IS the register (or a
#: directory containing it) would self-match every marker and manufacture candidates out of
#: nothing. Locked by test/test-fork-gap-detector.js; the 2026-07-20 `image-cache` case was
#: exactly this — a hit fabricated by the tool from the gap's own prose.
SELF_FILES = ("fork-gaps.md", "fork-gaps-archive.md")


def _target_hit(full: str, marker: str) -> bool:
    """Does `marker` appear in the target, EXCLUDING the register's own files?"""
    if os.path.isdir(full):
        for dirpath, _dirs, files in os.walk(full):
            for fn in files:
                if fn in SELF_FILES:
                    continue
                try:
                    with open(os.path.join(dirpath, fn), errors="ignore") as fh:
                        if marker in fh.read():
                            return True
                except (OSError, UnicodeDecodeError):
                    continue
        return False
    if os.path.basename(full) in SELF_FILES:
        return False
    try:
        with open(full, errors="ignore") as fh:
            return marker in fh.read()
    except (OSError, UnicodeDecodeError):
        return False


def check_stale_open(entries, creation_mode: bool) -> int:
    new_ids = _staged_new_ids() if creation_mode else set()
    errors = warns = checked = 0
    for e in entries:
        state = e.header.get("state", "")
        marker, target = e.header.get("marker", ""), e.header.get("target", "")
        if state == "closed" or marker == "n/a" or not _checkable(target):
            continue
        full = os.path.join(ROOT, target)
        if not os.path.exists(full):
            continue
        if os.path.basename(full) in SELF_FILES:
            continue
        checked += 1
        hit = _target_hit(full, marker)
        if not hit:
            continue
        if creation_mode and e.header.get("id") in new_ids:
            print(f"  ✗ {e.id}: NEW entry whose marker `{marker}` ALREADY exists in {target}.")
            print("     Either the marker is too generic to prove anything, or the gap is already fixed.")
            errors += 1
        else:
            print(f"  ⚠ stale-open candidate: {e.id} — marker `{marker}` present in {target}")
            warns += 1
    print(f"check-fork-gap-stale-open: {errors} error(s), {warns} candidate(s) from {checked} checkable entry/entries.")
    if warns:
        print("  ⚠ RULE — NEVER close a gap on a grep hit alone. A marker proves a STRING exists, not")
        print("    that the gap is resolved. Open the implementing section, read it, and confirm it")
        print("    matches the entry's stated fix direction before changing any state.")
    print("  DETECTOR ONLY — the register was not modified.")
    return 1 if errors else 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "schema"
    entries = [e for e in parse() if e.heading.strip() != "## Open"]
    if mode == "schema":
        return check_schema(entries)
    if mode == "targets":
        return check_targets(entries)
    if mode == "stale-open":
        return check_stale_open(entries, creation_mode="--creation-mode" in sys.argv)
    print(f"unknown mode: {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
