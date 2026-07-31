#!/usr/bin/env python3
"""fork_gap_lint.py — the ONE parser + the three checks for docs/fork-gaps.md.

Single source of truth for reading the typed ledger (schema v1,
docs/proposals/fork-gaps-schema-v1.md). Three shell entry points delegate here so
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

import hashlib
import os
import re
import subprocess
import sys

# FORK_GAP_ROOT lets the hermetic test drive a sandbox tree; unset it resolves to the fork.
ROOT = os.environ.get("FORK_GAP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAPS = os.path.join(ROOT, "docs", "fork-gaps.md")

FIX_VALUES = {"none", "partial", "done"}
DELIVERY_VALUES = {"n/a", "owed", "done"}
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
    return parse_text(open(path).read())


def parse_text(text: str):
    """Same parse, from a string — so a git blob (HEAD's or the staged version of the
    register) can be parsed without being written to disk. Used by the touched-entry
    scoping below."""
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
            v = v.strip()
            # Strip a trailing inline comment on an UNQUOTED value (`delivery: owed  # why`).
            # Only when unquoted: a quoted value may legitimately contain `#`, and eating that
            # would silently truncate a marker or a distribution note. Enum fields carry their
            # reason inline — that reason is the difference between a value and a decision.
            if not v.startswith(('"', "'")):
                v = re.split(r"\s+#", v, maxsplit=1)[0].strip()
            header[k.strip()] = v.strip('"')
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


def check_schema(entries, touched=None) -> int:
    # (id, message) — the id decides whether a finding may BLOCK; the rules are unchanged.
    errors, seen_ids = [], set()
    for e in entries:
        eid = e.id
        add = lambda msg, _eid=e.header.get("id", ""): errors.append((_eid, msg))
        if HEADING_BLOB_RE.search(e.heading):
            add(f"{eid}: heading carries a state blob — move it to the Work Status line")
        if not e.header:
            # No header means no id, so this can never be attributed — invariant 3 blocks it.
            errors.append(("", f"{eid}: no ```yaml header block"))
            continue
        for f in REQUIRED:
            if f not in e.header:
                add(f"{eid}: missing required field `{f}`")
        hid = e.header.get("id", "")
        if hid and not ID_RE.match(hid):
            add(f"{eid}: id `{hid}` is not FG-YYYY-MM-DD-NN")
        if hid in seen_ids:
            add(f"{eid}: duplicate id")
        seen_ids.add(hid)

        state, scope = e.header.get("state", ""), e.header.get("scope", "")
        if state and state not in STATES:
            add(f"{eid}: unknown state `{state}` (allowed: {', '.join(sorted(STATES))})")
        if scope and scope not in SCOPES and scope != "unknown":
            add(f"{eid}: unknown scope `{scope}`")

        marker = e.header.get("marker", "")
        if marker == "n/a":
            if scope != "harness":
                add(f"{eid}: `marker: n/a` is legal ONLY with scope: harness (this is {scope or 'unset'})")
        elif len(marker.strip()) < 3:
            add(f"{eid}: marker must be >=3 non-space chars (blank/short markers match every file)")

        if state == "superseded" and not e.header.get("superseded_by"):
            add(f"{eid}: state superseded requires superseded_by")
        if state == "blocked" and not e.header.get("blocked_by"):
            add(f"{eid}: state blocked requires blocked_by naming an OBSERVABLE condition")
        if state == "fork-fixed-distribution-owed" and not e.header.get("distribution"):
            add(f"{eid}: state fork-fixed-distribution-owed requires distribution")
        if not e.has_incident:
            add(f"{eid}: no `### Incident` block")

        # --- fix + delivery axes (schema v2, docs/proposals/fork-gap-axes-v2.md) ---------
        # MIGRATION WINDOW: `state` remains a deprecated alias and stays REQUIRED, so a
        # parallel session's in-flight entry cannot fail this gate mid-write. This register
        # takes concurrent writes from many sessions; a hard cutover would block all of them.
        # The pair is WARNED-on-absent, ERRORED-on-invalid — you may not have migrated yet,
        # but you may never write a value that means nothing.
        fix, delivery = e.header.get("fix"), e.header.get("delivery")
        if fix is not None and fix not in FIX_VALUES:
            add(f"{eid}: unknown fix `{fix}` (allowed: {', '.join(sorted(FIX_VALUES))})")
        if delivery is not None and delivery not in DELIVERY_VALUES:
            add(f"{eid}: unknown delivery `{delivery}` (allowed: {', '.join(sorted(DELIVERY_VALUES))})")
        # `delivery` is meaningless while nothing is built — §2 of the proposal.
        if fix == "none" and delivery not in (None, "n/a"):
            add(f"{eid}: fix `none` with delivery `{delivery}` — nothing is built, so there "
                          "is nothing to deliver. Set `delivery: n/a`.")
        # The value that rotted the old field: `partial` with no enumeration of what remains.
        if fix == "partial" and not re.search(r"\bNOT taken\b|\bstill (?:open|owed)\b|\bremain(?:s|ing)\b|"
                                              r"\bowed\b|\bnot done\b|\bunbuilt\b", e.body, re.I):
            add(f"{eid}: fix `partial` but the body never names what is OUTSTANDING. "
                          "`partly` with no enumeration is exactly what rotted the old single field — "
                          "name the residue, or the honest value is `none` or `done`.")

    unknowns = sum(1 for e in entries for f in ("class", "scope", "target", "owner")
                   if e.header.get(f) == "unknown")
    # The register is open-only by construction — a plain heading grep should equal the open
    # set. Terminal entries left in the live file erode that quietly, so NOTICE them here.
    # WARN, never error: archiving MUTATES, and this tooling does not mutate the register.
    terminal = [e.id for e in entries if e.header.get("state") in ("closed", "superseded")]
    rc = _emit(errors, touched, "check-fork-gap-schema", len(entries))
    if unknowns:
        print(f"  ⚠ {unknowns} field(s) still `unknown` — declared debt, not a blocker. Fill when known.")
    if terminal:
        print(f"  ⚠ {len(terminal)} terminal entry/entries still in the live register "
              f"({', '.join(terminal[:4])}{'…' if len(terminal) > 4 else ''}).")
        print("    Run: python3 tools/archive-fork-gaps.py --write   (explicit, never automatic)")
    return rc


def check_targets(entries, touched=None) -> int:
    # scope:fork rot is an ERROR (blocking only on a touched entry); every other scope stays a
    # WARN exactly as before — a project/machine-local/harness target legitimately does not
    # resolve from the fork tree, so it never blocks anyone regardless of who touched it.
    errors, warns = [], 0
    for e in entries:
        target, scope = e.header.get("target", ""), e.header.get("scope", "")
        if not _checkable(target):
            continue
        if os.path.exists(os.path.join(ROOT, target)):
            continue
        if scope == "fork":
            errors.append((e.header.get("id", ""),
                           f"{e.id}: scope:fork target does not resolve — `{target}` (pointer rot)"))
        else:
            print(f"  ⚠ {e.id}: target does not resolve here — `{target}` (scope: {scope or 'unset'})")
            warns += 1
    rc = _emit(errors, touched, "check-fork-gap-targets", len(entries))
    if warns:
        print(f"  ⚠ {warns} non-fork-scope target(s) unresolvable here — expected, never blocking.")
    return rc


# ---------------------------------------------------------------------------
# TOUCHED-ENTRY SCOPING — which findings may BLOCK this commit
# ---------------------------------------------------------------------------
# WHY. fork-gaps.md is one append-only file written by many sessions, and `schema` and
# `targets` rejected the whole COMMIT on any finding anywhere in it. So one malformed or
# rotted entry froze gap logging for EVERYONE: a session would author a perfectly valid
# entry, hit a wall left by a previous session days earlier, abandon the commit, and leave
# its entry dirty in the working tree. The next session did the same. The pile grew with
# nobody consciously deciding not to log.
#
# Observed 2026-07-31: three finished entries stranded uncommitted since 07-30 — one blocked
# by its own missing `### Incident`, the other two blocked by FG-2026-07-30-10's `target:`
# pointing at a path that stopped existing in a directory reorg. Logging rate over the same
# window: 12-14/day on 07-25..28, then 3, 4, 1.
#
# THE FIX IS SCOPE, NOT STRICTNESS. Every rule stays exactly as strict; what changes is WHICH
# findings are allowed to block. A finding on an entry this commit touched blocks, as before.
# A finding on an untouched historical entry is printed just as loudly and does not block —
# you cannot be held responsible at commit time for rot you did not write and are not editing.
#
# THREE INVARIANTS:
#   1. TOUCHED = new OR edited. Not "new" (an edit that breaks an entry must still block) and
#      not "appears in the + lines" (a reformat re-adds every line and would scope to
#      everything — the same trap _staged_new_ids documents).
#   2. UNDETERMINABLE => EVERYTHING BLOCKS. No staged register, unreadable git, or a
#      pre-schema pre-image means we cannot tell touched from historical, so the check
#      degrades to the FULL audit it has always been. Scoping may never be the reason a real
#      finding goes unenforced — that would relax the gate, which is explicitly not the ask.
#      This is also what keeps a manual `bash tools/check-fork-gap-schema.sh` and `npm test`
#      a whole-file audit: neither has a staged blob, so neither is scoped.
#   3. AN UNATTRIBUTABLE ENTRY IS TOUCHED. An entry with no id, or an id that does not parse,
#      cannot be proven historical — and a brand-new entry missing its id is exactly the case
#      this gate exists to catch. Fail closed.

def _register_blobs():
    """(head_text, staged_text) for docs/fork-gaps.md, or None if not determinable."""
    try:
        head = subprocess.run(["git", "show", "HEAD:docs/fork-gaps.md"],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
        staged = subprocess.run(["git", "show", ":docs/fork-gaps.md"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if staged.returncode != 0:
        return None                      # nothing staged -> not a commit of this file
    return (head.stdout if head.returncode == 0 else ""), staged.stdout


def _touched_ids():
    """Ids whose entry block differs between HEAD and the staged register.

    Returns a set, or None meaning "cannot tell — treat every finding as blocking".
    """
    blobs = _register_blobs()
    if blobs is None:
        return None
    before_text, after_text = blobs
    if not before_text.strip():
        return None                      # no pre-image to diff against
    # `git show :<path>` succeeds for ANY tracked file — an unmodified one just returns HEAD's
    # blob. So a zero-diff index is NOT "a commit that touches nothing"; it is "this run is not
    # a commit of the register at all" (a manual sweep, npm test, or a commit of other files).
    # Treating it as scoped-to-zero would silently pass a broken register — the exact
    # relaxation this change must not make. Invariant 2: undeterminable => full audit.
    if before_text == after_text:
        return None
    def blocks(text):
        out = {}
        for e in parse_text(text):
            if e.heading.strip() == "## Open":
                continue
            hid = e.header.get("id")
            if hid:
                # Heading + body: an edit to either is a real change to the entry.
                out[hid] = e.heading.strip() + "\n" + e.body.strip()
        return out
    before, after = blocks(before_text), blocks(after_text)
    # Invariant 2: a pre-image carrying no ids is the schema migration itself — every entry
    # would look new. Novelty undeterminable -> full audit.
    if not before:
        return None
    touched = {hid for hid, blk in after.items() if before.get(hid) != blk}
    # The register changed but no ENTRY did — the edit was to the preamble, the `## Open`
    # marker, or some other non-entry prose. Nothing is attributable, so fall back to the full
    # audit rather than scoping to nothing. Fail closed, same as invariant 3.
    return touched or None


def _is_blocking(eid: str, touched) -> bool:
    """touched is None (full audit) or a set of ids this commit created/edited."""
    if touched is None:
        return True
    if not eid or not ID_RE.match(eid):
        return True                      # invariant 3 — unattributable entries fail closed
    return eid in touched


def _emit(findings, touched, check_name: str, entry_count: int) -> int:
    """Print blocking findings as errors and untouched ones as advisory. Exit 1 iff blocking.

    Advisory findings are printed in FULL, never summarised to a count — the whole point is
    that pre-existing rot stays visible so it can be cleaned up deliberately, instead of
    being discovered the next time it blocks somebody.
    """
    blocking = [(eid, m) for eid, m in findings if _is_blocking(eid, touched)]
    advisory = [(eid, m) for eid, m in findings if not _is_blocking(eid, touched)]
    for _eid, msg in blocking:
        print(f"  ✗ {msg}")
    if advisory:
        print(f"  ── {len(advisory)} pre-existing finding(s) on entries this commit did NOT touch "
              "— reported, NOT blocking:")
        for _eid, msg in advisory:
            print(f"     · {msg}")
        print("     These are real and still want fixing; they are simply not this commit's to fix.")
        print("     Sweep them with:  bash tools/check-fork-gap-schema.sh  (unscoped, audits everything)")
    scope_note = "full audit (unscoped)" if touched is None else \
                 f"scoped to {len(touched)} touched entry/entries"
    print(f"{check_name}: {len(blocking)} error(s), {len(advisory)} pre-existing, "
          f"across {entry_count} entry/entries · {scope_note}.")
    return 1 if blocking else 0


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


# ---------------------------------------------------------------------------
# CONTRADICTION — the prose says the fix landed; the field still says it hasn't
# ---------------------------------------------------------------------------
# WHY (FG-2026-07-27-04). A verify-and-close sweep on 2026-07-27 reclassified EIGHT entries in
# one sitting. None needed work: every one already recorded, in its own status line, that the
# fork fix was DONE with distribution the only residue — while still sitting at `open`/`partly`.
# Eight independent authors wrote the truth in prose and left the field wrong, which is the
# signature of a field that cannot express what the author needed to say.
#
# THIS IS A SYMPTOM CATCHER, NOT THE MODEL FIX. The root cause is that one enum spans three
# lifecycles (finding / decision / delivery); the real repair is the fix+delivery axis split.
# This check exists because it would have caught all 8 today, needs no migration, and keeps
# catching them while the split is designed.
#
# SEVERITY: WARN, never error — deliberately, and the reason matters. The register's gate is
# armed in pre-commit, so an erroring keyword heuristic would block EVERY session's commit to
# this file on a false positive. That already happened twice this week from unrelated schema
# omissions, and a gate that blocks the whole team on a guess is the one that gets deleted.
# Promotion to error requires the same bar as every other gate here: a proven-quiet window.
#
# ACKNOWLEDGEMENT: an entry may carry `contradiction_ack: <reason>` in its yaml header to
# silence a known-fine case (e.g. prose quoting ANOTHER entry's closure). The ack must give a
# reason — a bare ack is not accepted, same discipline as a parked scope row owing a trigger.

# THE RULE IS A CONJUNCTION, NOT A KEYWORD LIST — and the first cut proved why.
#
# Naive version fired 15 times on 69 entries, and 8 of those were `partly resolved` prose on a
# `state: partly` entry — which is AGREEMENT, not contradiction. Others fired on entries whose
# body DESCRIBES the problem (this very check's own entry flagged itself). A detector that
# cannot tell agreement from disagreement teaches everyone to ignore it, and the register's
# gate is armed in pre-commit, so noise here is expensive.
#
# The precise signature of the bug — the one all 8 swept entries actually had — is BOTH:
#   (a) the prose asserts the FIX IS DONE at source, AND
#   (b) the prose says the only residue is DISTRIBUTION,
# while the field is NOT `fork-fixed-distribution-owed`. That pair has exactly one correct
# state, so disagreement is decidable rather than guessed. Anything weaker is a hint, not a
# finding, and is deliberately not reported.
_FIX_DONE = [
    (re.compile(r"\bfork fix (?:is )?done\b", re.I), "the fork fix is done"),
    (re.compile(r"\bfix (?:is )?done at source\b", re.I), "the fix is done at source"),
    (re.compile(r"\bfix (?:is )?done\b", re.I), "the fix is done"),
    (re.compile(r"\bverified built\b", re.I), "it was verified built"),
    (re.compile(r"\bfixes? \([a-c]\)(?:\+\([a-c]\))* (?:are |appear )?landed\b", re.I), "the named fixes landed"),
]
_DELIVERY_ONLY = [
    (re.compile(r"\bdistribution\b[^.\n]{0,60}\bowed\b", re.I), "distribution is the only residue"),
    (re.compile(r"\bowed\b[^.\n]{0,40}\bdistribution\b", re.I), "distribution is the only residue"),
    (re.compile(r"\bstill open only on distribution\b", re.I), "it is open only on distribution"),
    (re.compile(r"\barchive on distribution\b", re.I), "it archives on distribution"),
]

# `fork-fixed-distribution-owed` is the CORRECT home for a done-but-undelivered entry, so it is
# never a contradiction. `open`/`partly`/`blocked` all claim someone still has work to do.
_UNFINISHED_STATES = {"open", "partly", "blocked"}


def check_contradiction(entries) -> int:
    findings = []
    for e in entries:
        state = e.header.get("state", "")
        if state not in _UNFINISHED_STATES:
            continue
        ack = e.header.get("contradiction_ack", "").strip()
        if ack and len(ack) >= 8:
            continue
        done = [why for rx, why in _FIX_DONE if rx.search(e.body)]
        deliv = [why for rx, why in _DELIVERY_ONLY if rx.search(e.body)]
        if done and deliv:          # conjunction — see the rule note above
            findings.append((e.id, state, sorted(set(done)) + sorted(set(deliv))))

    for eid, state, hits in findings:
        print(f"  ⚠ {eid}: state `{state}` but the prose says {'; and '.join(hits)}.")
        print("     Either the field is stale (move it — `fork-fixed-distribution-owed` is the")
        print("     home for fixed-but-undelivered), or the prose overclaims. Read the entry and")
        print("     resolve the disagreement; do NOT silence it by editing the prose to match.")
        print("     Legitimately fine? add `contradiction_ack: <reason>` to the yaml header.")
    print(f"check-fork-gap-contradiction: {len(findings)} contradiction(s) across {len(entries)} entry/entries "
          f"(WARN-only — never blocks a commit).")
    if findings:
        print("  This is a SYMPTOM catcher. The model fix is the fix+delivery axis split")
        print("  (FG-2026-07-27-04); until that lands, expect this to keep finding them.")
    return 0  # never blocks


def check_report(entries) -> int:
    """Standing monitor for the three numbers that hid the problem (FG-2026-07-27-04 §4)."""
    contradictions = 0
    for e in entries:
        if e.header.get("state") in _UNFINISHED_STATES and not e.header.get("contradiction_ack"):
            if any(rx.search(e.body) for rx, _ in _FIX_DONE) and \
               any(rx.search(e.body) for rx, _ in _DELIVERY_ONLY):
                contradictions += 1

    # Count on the AXES now that every entry carries them (migration complete 2026-07-27).
    # `state` is kept alongside for one deprecation cycle, so report BOTH and show the gap —
    # a silent divergence between the old field and the new pair is how the next rot starts.
    owed = [e for e in entries if e.header.get("fix") == "done" and e.header.get("delivery") == "owed"]
    owed_by_state = [e for e in entries if e.header.get("state") == "fork-fixed-distribution-owed"]

    # Entries whose prose names another FG id as a blocker, where that id is now terminal.
    terminal = {e.header.get("id") for e in entries
                if e.header.get("state") in ("closed", "superseded")}
    blocked_on_delivered = []
    for e in entries:
        if e.header.get("state") not in _UNFINISHED_STATES:
            continue
        for ref in set(re.findall(r"FG-\d{4}-\d{2}-\d{2}-\d{2}", e.body)):
            if ref in terminal and ref != e.header.get("id"):
                blocked_on_delivered.append((e.id, ref))
                break

    live = [e for e in entries if e.header.get("state") not in ("closed", "superseded")]
    print("\nfork-gap register — standing report")
    print(f"  live entries:                      {len(live)}")
    print(f"  prose/field contradictions:        {contradictions}   (fix the FIELD, not the prose)")
    print(f"  fix done + delivery owed:          {len(owed)}   ← ONE sync, not {len(owed)} investigations")
    if len(owed) != len(owed_by_state):
        print(f"  (deprecated `state` says {len(owed_by_state)} — the axes are authoritative; the")
        print("   difference is entries whose delivery was DERIVED and corrected, which `state` cannot express)")
    print(f"  blocked on an already-closed gap:  {len(blocked_on_delivered)}")
    for eid, ref in blocked_on_delivered:
        print(f"      • {eid} references {ref}, which is terminal — re-read; it may be unblocked")
    print("\n  The middle number is the one that lies about backlog size. The bottom one is how a")
    print("  real unblock stayed invisible (FG-2026-07-20-01 sat blocked on work that had shipped).\n")
    return 0



# ---------------------------------------------------------------------------
# DERIVED DELIVERY — step 3 of FG-2026-07-27-04, and deliberately SELECTIVE
# ---------------------------------------------------------------------------
# Written delivery state is a cached value with no invalidation: someone types `owed`, the
# sync runs, and nothing updates it. Where distribution is machine-checkable we should not be
# typing it at all — we should be diffing.
#
# THREE RULES, and the third is the one that gets forgotten:
#   1. Derivation BACKS the written axis, it never replaces it. This mode reports; it does not
#      mutate the register. The written value stays authoritative because it is the one a human
#      reasoned about.
#   2. Where derivation is impossible the written value stands, and this says so explicitly
#      rather than leaving a blank that reads as agreement.
#   3. A derivation that CANNOT ANSWER returns UNKNOWN — never `done`. Absence of a diff is not
#      proof of delivery when the comparison could not run. Same discipline as
#      "unparseable is not young" and "no signal is not a story"; getting this backwards would
#      let a broken mapping silently mark the whole register delivered.
#
# COVERAGE IS HALF THE REGISTER, ON PURPOSE. Only two target classes have a verified fork ->
# project mapping (both used in anger this week):
#     custom/workflows/<rest>  ->  <project>/_bmad/bmm/workflows/<rest>
#     custom/githooks/<file>   ->  <project>/.githooks/<file>
# `custom/skills/` is NOT derived: the project-side layout differs between the old layout and
# the v6.8 skills-native one, so a single mapping would be wrong for some projects — and a
# confidently wrong derivation is worse than an honest UNKNOWN.

DERIVABLE_PREFIXES = (
    ("custom/workflows/", "_bmad/bmm/workflows/"),
    ("custom/githooks/", ".githooks/"),
)
# Consumed FROM the fork by definition — there is no project copy to compare, and that is
# `n/a`, not an unknown.
FORK_LOCAL_PREFIXES = ("tools/", "docs/", "test/", "evals/")


def _targets_file_projects():
    """Project roots from ~/.bmad-targets. Absolute-path lines only — the header prose in that
    file has already been parsed into phantom projects once (migrate-bash-edit-guard.sh)."""
    tf = os.path.join(os.path.expanduser("~"), ".bmad-targets")
    if not os.path.exists(tf):
        return []
    roots = []
    for line in open(tf):
        line = line.strip()
        if not line.startswith("/"):
            continue
        roots.append(re.sub(r"/_bmad/bmm/workflows/?$", "", line).rstrip("/"))
    return sorted(set(roots))


def _digest(path):
    """Content digest of a file or directory tree; None if it does not exist."""
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    if os.path.isfile(path):
        h.update(open(path, "rb").read())
        return h.hexdigest()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            if f == ".DS_Store":
                continue
            h.update(f.encode())
            h.update(open(os.path.join(root, f), "rb").read())
    return h.hexdigest()


def derive_delivery(target):
    """-> (verdict, detail). verdict in {done, owed, n/a, unknown}."""
    t = target.strip()
    if t.startswith(FORK_LOCAL_PREFIXES) or ("/" not in t and t.endswith(".sh")):
        return "n/a", "fork-local: consumed from the fork, nothing to distribute"

    rel = None
    for fork_prefix, proj_prefix in DERIVABLE_PREFIXES:
        if t.startswith(fork_prefix):
            rel = proj_prefix + t[len(fork_prefix):]
            break
    if rel is None:
        return "unknown", "no verified fork->project mapping for this target class"

    src = os.path.join(ROOT, t)
    if not os.path.exists(src):
        return "unknown", "fork-side target does not exist (pointer rot — see the targets check)"

    projects = _targets_file_projects()
    if not projects:
        return "unknown", "~/.bmad-targets unreadable — comparison could not run"

    want = _digest(src)
    # A project on the v6.8 SKILLS-NATIVE layout has no `_bmad/bmm/workflows` tree at all, so a
    # missing file there is a LAYOUT FACT, not staleness. Counting it stale reported cash-recovery
    # — the skills-native pilot — as behind on 9 entries it had never been behind on.
    checked = [p for p in projects
               if os.path.isdir(p) and (not rel.startswith("_bmad/bmm/workflows/")
                                        or os.path.isdir(os.path.join(p, "_bmad/bmm/workflows")))]
    stale = [os.path.basename(p) for p in checked if _digest(os.path.join(p, rel)) != want]
    if not checked:
        return "unknown", "no project roots resolved on disk"
    if stale:
        return "owed", f"{len(stale)}/{len(checked)} project(s) stale or missing: {', '.join(stale[:4])}" + \
                       ("…" if len(stale) > 4 else "")
    return "done", f"byte-identical in all {len(checked)} project(s)"


def check_derive(entries) -> int:
    agree = disagree = unknown = 0
    rows = []
    for e in entries:
        if e.header.get("state") in ("closed", "superseded"):
            continue
        # DERIVATION ONLY APPLIES ONCE SOMETHING IS BUILT. The question is "did THIS entry's fix
        # reach the projects", and a target file can differ from its project copies for reasons
        # that have nothing to do with this entry (another session's unsynced edit to the same
        # file). Asking it about a `fix: none` entry compares the wrong thing — the first cut did
        # exactly that and produced 14 confident false disagreements. `fix: none` already implies
        # `delivery: n/a` by schema rule, so there is nothing to check.
        if e.header.get("fix") in (None, "none"):
            continue
        target = e.header.get("target", "")
        written = e.header.get("delivery")
        verdict, detail = derive_delivery(target)
        if verdict == "unknown":
            unknown += 1
            continue
        if written is None:
            rows.append(("UNSET  ", e.id, written, verdict, detail))
            disagree += 1
        elif written == verdict:
            agree += 1
        else:
            rows.append(("DIFFERS", e.id, written, verdict, detail))
            disagree += 1

    print("\nderived delivery — selective, report-only (FG-2026-07-27-04 step 3)")
    for kind, eid, written, verdict, detail in rows:
        print(f"  {kind} {eid}: written `{written}` vs derived `{verdict}` — {detail}")
    print(f"\n  agree: {agree} · disagree/unset: {disagree} · NOT DERIVABLE (unknown): {unknown}")
    print("  Derivation BACKS the written axis and never replaces it: nothing here was mutated,")
    print("  and an UNKNOWN means the comparison could not run — never that delivery is done.")
    print(f"  Coverage is partial by design: {unknown} entries have no verified fork->project")
    print("  mapping (project-scope, machine-local, harness, or custom/skills whose project-side")
    print("  layout differs between the old and skills-native layouts).\n")
    return 0

# --------------------------------------------------- orphan cross-entry annotation

ANNOT_HEADING_RE = re.compile(r"^#{2,3}\s+.*?(FG-\d{4}-\d{2}-\d{2}-\d{2})", re.M)


def check_orphan_annotation(entries) -> int:
    """A later annotation of an EXISTING entry must be reachable FROM that entry.

    fork-gaps.md is an append-only log well past 5,000 lines, so an annotation of an
    older entry necessarily lands far from it — 2,170 lines away, in the case that
    produced this check (2026-07-28, FG-2026-07-26-04). Anyone reaching the original
    the normal way (a grep, a triage sweep, the stale-open detector) reads its header
    and never learns the annotation exists.

    That is not a formatting nit. The orphaned content in the originating case was the
    inoculation against a REPRODUCIBLE FALSE DIAGNOSIS that every blocked agent derives
    independently with convincing evidence — precisely what a blocked reader needs and
    precisely what they would not have found.

    WARN-ONLY, and the remedy is ADDITIVE: add a `see_also` to the referenced entry.
    It never asks anyone to alter a prior finding — that would be the quiet
    history-rewrite the append-only discipline exists to prevent. A pointer is metadata,
    not a claim.
    """
    text = open(GAPS).read()
    lines = text.split("\n")
    by_id = {e.id: e for e in entries if getattr(e, "id", None)}

    # line_no -> owning entry, so a heading can be attributed to its enclosing ## block.
    bounds = sorted(((e.line_no, e) for e in entries if getattr(e, "id", None)))

    def owner_of(lineno):
        own = None
        for start, e in bounds:
            if start <= lineno:
                own = e
            else:
                break
        return own

    warns = 0
    for m in ANNOT_HEADING_RE.finditer(text):
        ref_id = m.group(1)
        lineno = text[: m.start()].count("\n") + 1
        owner = owner_of(lineno)
        # A heading inside the entry it names is a self-reference, not an annotation.
        if owner is not None and owner.id == ref_id:
            continue
        ref = by_id.get(ref_id)
        if ref is None:
            continue  # dangling id is check-fork-gap-schema's business, not ours
        if "see_also" in ref.header:
            continue
        heading_txt = lines[lineno - 1].lstrip("# ").strip()
        print(
            f"  \u26a0 {ref_id}: annotated at line {lineno} but the entry (line {ref.line_no}) "
            f"has no `see_also` pointing at it — a reader landing on the entry never finds it.\n"
            f"      annotation: {heading_txt[:96]}\n"
            f"      fix: add to {ref_id}'s yaml header ->  see_also: \"<what it says, and where>\"\n"
            f"      (ADDITIVE ONLY — do not edit the entry's existing claims.)"
        )
        warns += 1

    print(
        f"check-fork-gap-orphan-annotation: {warns} orphaned annotation(s) across "
        f"{len(by_id)} entry/entries. WARN-only — never blocks."
    )
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "schema"
    entries = [e for e in parse() if e.heading.strip() != "## Open"]
    # Scoping applies to the two BLOCKING checks only, and only when a staged register exists
    # (i.e. we are in a pre-commit for this file). `--all` forces the full audit explicitly.
    if mode in ("schema", "targets"):
        touched = None if "--all" in sys.argv else _touched_ids()
        return check_schema(entries, touched) if mode == "schema" \
            else check_targets(entries, touched)
    if mode == "stale-open":
        return check_stale_open(entries, creation_mode="--creation-mode" in sys.argv)
    if mode == "orphan-annotation":
        return check_orphan_annotation(entries)
    if mode == "contradiction":
        return check_contradiction(entries)
    if mode == "report":
        return check_report(entries)
    if mode == "derive":
        return check_derive(entries)
    print(f"unknown mode: {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
