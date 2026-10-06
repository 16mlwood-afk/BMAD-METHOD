#!/usr/bin/env bash
# PreToolUse(Edit|Write) awareness nudge — fork-authoring collision protection.
#
# The gap (fork-gaps): fork edits are hook-allowlisted (no worktree needed), so
# the ONLY collision protection is removed. Two cold sessions pointed at the same
# gap can both author the same new standard into custom/workflows/shared/, dupe
# the ID space, and collide — caught once only by luck.
#
# This fires when you Edit/Write a file in the fork's SHARED standards namespace
# AND ANOTHER session has uncommitted changes there. Awareness tier (additionalContext,
# never blocks — a block would stop legit parallel work on DIFFERENT shared files).
#
# Self-false-positive avoidance: git can't tell MY uncommitted files from another
# session's, so this keeps a per-session ledger of shared/ files I've touched and
# only flags files NOT in my ledger (i.e. another session's in-flight work).
#
# stdin handled correctly (capture-first; do NOT let the heredoc become stdin).
INPUT="$(cat)"
FORK="$HOME/bmad-method-v6"
LEDGER="/tmp/claude-fork-authoring-${CLAUDE_SESSION_EPOCH:-$PPID}"
python3 - "$INPUT" "$FORK" "$LEDGER" <<'PY' 2>/dev/null || true
import json, sys, os, re, subprocess

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
fork, ledger = sys.argv[2], sys.argv[3]

tool_input = data.get("tool_input", {}) or {}
path = tool_input.get("file_path", "") or ""

FG_ID = re.compile(r"FG-\d{4}-\d{2}-\d{2}-\d{2}")


def emit(msg):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}))
    sys.exit(0)


def ledger_read(prefix=""):
    try:
        if os.path.exists(ledger):
            return set(l.strip()[len(prefix):] for l in open(ledger)
                       if l.strip().startswith(prefix))
    except Exception:
        pass
    return set()


def ledger_add(items, prefix=""):
    try:
        with open(ledger, "a") as f:
            for i in sorted(items):
                f.write(prefix + i + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# BRANCH: docs/fork-gaps.md — the register. The fork-gaps entry-id collision key.
# ---------------------------------------------------------------------------
# The register is the fork's highest-contention file and is literally what "two cold
# sessions pointed at the same gap" means, yet the original matcher watched only the
# shared-standards namespace. Observed 2026-07-25: two sessions edited the SAME entry
# minutes apart with no warning either way (fork-gaps FG-2026-07-25-13).
#
# Keying on the FILE would fire on every register edit and be tuned out within a day —
# two sessions on DIFFERENT entries is the normal, healthy case. Only a shared id is an
# event. Same self-flag avoidance as below: a per-session ledger of ids I've touched.
if path.endswith("docs/fork-gaps.md"):
    payload = " ".join(str(tool_input.get(k, "") or "") for k in ("new_string", "old_string", "content"))
    my_ids = set(FG_ID.findall(payload))
    if not my_ids:
        sys.exit(0)  # can't identify the entry → say nothing. No signal is not a story.

    # Warn at most ONCE per (session, entry): ids already in my ledger are ones I've either
    # touched or been warned about. A nudge that repeats on every edit to the same entry is
    # a nudge that gets ignored.
    prior = ledger_read("FG:")
    fresh = my_ids - prior
    ledger_add(fresh, "FG:")

    # Ids appearing in the CURRENT uncommitted diff of the register. Ids in my ledger are
    # mine (or already surfaced once); what remains is another session's live work.
    try:
        diff = subprocess.run(["git", "-C", fork, "diff", "HEAD", "--unified=0", "--", "docs/fork-gaps.md"],
                              capture_output=True, text=True, timeout=5).stdout
    except Exception:
        sys.exit(0)
    # Map changed LINE NUMBERS to the entry that owns them — do NOT just grep the diff text
    # for ids. A session editing an entry's prose usually never repeats the id in the lines
    # it changes, so an id-in-the-hunk-text check would almost never fire: the "reads as live,
    # detects nothing" failure. Hunk headers give the new-file line ranges; the register's own
    # `id:` lines give the entry boundaries.
    changed = []
    for line in diff.splitlines():
        m = re.match(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            changed.extend(range(start, start + max(count, 1)))
    dirty_ids = set()
    if changed:
        try:
            reg = open(os.path.join(fork, "docs/fork-gaps.md"), errors="ignore").read().splitlines()
        except Exception:
            reg = []
        # line number (1-based) -> owning entry id, by carrying the most recent `id:` forward.
        owner, owner_by_line = None, {}
        for n, text in enumerate(reg, 1):
            m = re.match(r"^id:\s*(FG-\d{4}-\d{2}-\d{2}-\d{2})", text.strip())
            if m:
                owner = m.group(1)
            owner_by_line[n] = owner
        for n in changed:
            if owner_by_line.get(n):
                dirty_ids.add(owner_by_line[n])

    overlap = sorted(dirty_ids & fresh)
    if overlap:
        emit(
            "⚠ Fork-gap collision risk: %s already has UNCOMMITTED changes in docs/fork-gaps.md "
            "that are not from this session's ledger. Another session is very likely working the "
            "SAME entry right now — on 2026-07-25 two sessions edited one entry minutes apart and "
            "neither was told. Before writing: re-read the entry as it stands on disk (it may have "
            "moved since your last Read), and if their note conflicts with yours, correct it IN "
            "PLACE rather than appending a second, contradictory account. Nudge only — not blocking."
            % ", ".join(overlap)
        )
    sys.exit(0)

# Otherwise: only fire when authoring in the fork's SHARED standards namespace.
if not re.search(r"/custom/(workflows/shared|skills-native/_shared)/", path):
    sys.exit(0)

target = os.path.basename(path)

# Record this file in my session ledger (so my own multi-file edits don't self-flag).
mine = set()
try:
    if os.path.exists(ledger):
        mine = set(l.strip() for l in open(ledger) if l.strip())
except Exception:
    pass
if target not in mine:
    try:
        with open(ledger, "a") as f:
            f.write(target + "\n")
    except Exception:
        pass
mine.add(target)

# What's uncommitted in the shared namespace right now?
try:
    out = subprocess.run(
        ["git", "-C", fork, "status", "--porcelain", "--",
         "custom/workflows/shared", "custom/skills-native/_shared"],
        capture_output=True, text=True, timeout=5).stdout
except Exception:
    sys.exit(0)

others = []
for line in out.splitlines():
    f = line[3:].strip()
    b = os.path.basename(f)
    # Exclude my own touched files + STANDARDS.md (it churns in every standards wave).
    if b and b not in mine and b != "STANDARDS.md":
        others.append(b)
others = sorted(set(others))

if others:
    msg = (
        "⚠ Fork-authoring collision risk: another session has UNCOMMITTED "
        "changes in custom/workflows/shared/ that you haven't touched — %s. "
        "Before authoring a new standard/workflow here: grep STANDARDS.md, scan "
        "those files for a same-topic artifact, and claim the ID/Home up front "
        "(see parallel-sessions.md § 'Authoring a shared standard/workflow'). "
        "Two sessions built the SAME standard this way once. Nudge only — not blocking."
        % ", ".join(others[:5])
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}))
PY
exit 0
