#!/usr/bin/env bash
# Stop hook — SCOPED, WARN-ONLY structural-friction reflection.
#
# SCOPE CLASS: fork-MAINTENANCE, not fork-canon. This file lives in the fork repo
# root but is NOT under custom/workflows/ and is NOT referenced by
# sync-bmad-workflows.sh, so it is not distributed to the 13 projects. Its blast
# radius is this machine's sessions, via ~/.claude/settings.json. Editing it owes
# no sync fan-out and does not touch the OWED sync window in STATUS.md.
#
# POLICY OBJECTIVE (unchanged, still valid): catch recurring wiring defects — a
# deploy path that is not legible, a guard with nowhere to redirect, sync drift,
# a workflow step that overran, shared state — and get them into fork-gaps.md
# once, while the session that hit them still remembers.
#
# WHAT CHANGED, 2026-08-31 (owner instruction). The previous implementation
# examined NOTHING about the session: no transcript, no tool calls, no paths. It
# emitted `decision: block` unconditionally, once per session, in EVERY session
# regardless of domain — turning ordinary completion into a mandatory
# infrastructure questionnaire. A missing friction log is not remotely the same
# risk class as an unsafe external mutation, so it must not block. Three repairs:
#
#   1. SCOPE.   Fires only on evidence that this session WROTE to fork / hook /
#               settings / skills / _bmad / doctrine / distribution surfaces.
#               Reads never count, so it cannot fire on read-only work and it
#               cannot fire because a doctrine file was merely opened.
#   2. DEMOTE.  Non-blocking `systemMessage`. Silence is the correct no-op — the
#               model is NEVER required to emit "no fork-gaps to log".
#   3. DEDUP.   Flags when fork-gaps.md already carries an entry dated today, so
#               a session does not stack a second entry on a known defect.
#
# It deliberately does NOT fire because the user pasted the words "fork", "hook",
# "infra" or "workflow", or because the assistant discussed infrastructure. Those
# are topic signals; this keys on WRITE ACTIONS against real paths.
#
# ENFORCEMENT CLASS: DETERMINISTIC delivery of a WARNING once the scope test
# passes; PROBABILISTIC as to whether real friction is then recognised and
# logged — no hook can judge that. Output bounded to <= 12 lines.
#
# NOTE: capture stdin into a var FIRST, then feed python via the heredoc —
# otherwise the heredoc becomes stdin and json.load(sys.stdin) reads the program.
INPUT="$(cat)"
python3 - "$INPUT" <<'PY'
import json, sys, os, re, hashlib, datetime

try:
    data = json.loads(sys.argv[1]) if sys.argv[1].strip() else {}
except Exception:
    sys.exit(0)

if data.get("stop_hook_active"):
    sys.exit(0)

sid = str(data.get("session_id") or os.environ.get("CLAUDE_SESSION_EPOCH", "unknown"))
marker = "/tmp/claude-fork-reflect-" + hashlib.sha1(sid.encode()).hexdigest()[:16]
if os.path.exists(marker):
    sys.exit(0)

path = data.get("transcript_path")
if not path or not os.path.exists(path):
    sys.exit(0)  # no evidence available -> silent, never block

# --- the scope test ---------------------------------------------------------
# Surfaces whose MODIFICATION is method / infrastructure maintenance.
SURFACES = [
    ("the BMAD fork",               r"bmad-method-v6"),
    ("a hook or guard",             r"[/\\]\.claude[/\\]hooks[/\\]"),
    ("harness settings",            r"settings(\.local)?\.json"),
    ("skills / agents / commands",  r"[/\\]\.claude[/\\](skills|agents|commands)[/\\]"),
    ("project BMAD workflows",      r"[/\\]_bmad[/\\]"),
    ("always-loaded doctrine",      r"CLAUDE\.md"),
    ("sync / upgrade / onboarding", r"(sync-bmad-workflows|upgrade-bmad|onboard-project)"),
]
# A Bash command counts ONLY when it mutates. `grep`/`cat`/`sed -n` over a fork
# path is reading, and reading must never trigger this hook.
MUTATING = re.compile(
    r"(>>?\s*\S|sed\s+-i|\bcp\s|\bmv\s|\brm\s|\btee\b|\bchmod\b|\bmkdir\b|"
    r"git\s+(commit|push|merge|apply)|"
    r"(sync-bmad-workflows|upgrade-bmad|onboard-project))"
)
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}

found = set()
try:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            content = (entry.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                name = item.get("name", "")
                inp = item.get("input") or {}
                if name in WRITE_TOOLS:
                    target = str(inp.get("file_path", ""))
                elif name == "Bash":
                    cmd = str(inp.get("command", ""))
                    target = cmd if MUTATING.search(cmd) else ""
                else:
                    continue
                if not target:
                    continue
                for label, pat in SURFACES:
                    if re.search(pat, target):
                        found.add(label)
except Exception:
    sys.exit(0)

if not found:
    sys.exit(0)  # session never wrote to infra -> SILENT. This is the no-op.

# --- dedup against the existing ledger --------------------------------------
logged_today = False
try:
    gaps = os.path.expanduser("~/bmad-method-v6/docs/fork-gaps.md")
    with open(gaps, "r", encoding="utf-8") as fh:
        tail = fh.read()[-40000:]
    logged_today = datetime.date.today().isoformat() in tail
except Exception:
    pass

try:
    open(marker, "w").close()
except Exception:
    pass

lines = [
    "WARN - friction reflection (non-blocking, no output required).",
    "This session WROTE to: %s." % ", ".join(sorted(found)),
    "If the WIRING structurally fought you - a guard with nowhere to redirect, a",
    "deploy path that is not legible, sync drift, shared state, a step that overran",
    "- log it once to ~/bmad-method-v6/docs/fork-gaps.md naming the target path,",
    "the user impact, and the shape of the fix. A one-off bug is NOT a fork-gap.",
]
if logged_today:
    lines.append("NOTE: an entry dated today already exists - check before adding another.")
lines.append("If nothing structural fought you, say nothing and finish. Silence is correct.")

print(json.dumps({"systemMessage": "\n".join(lines)}))
PY
exit 0
