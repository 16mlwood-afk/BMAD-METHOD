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

path = (data.get("tool_input", {}) or {}).get("file_path", "") or ""
# Only fire when authoring in the fork's SHARED standards namespace.
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
