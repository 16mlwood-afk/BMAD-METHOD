#!/usr/bin/env bash
# PreToolUse(Edit|Write) nudge — when a CLAUDE.md edit looks like it RESTATES a
# shared standard (rather than pointing at it), suggest a pointer. Per
# STD-CLAUDE-001: project CLAUDE.md must be thin and pointer-based.
#
# Enforcement class: PROBABILISTIC nudge (message only, NEVER blocks). Keeping
# CLAUDE.md thin is guidance, not a safety gate — a nudge is the right tier.
# Conservative: only fires on a CLAUDE.md target whose new content carries
# multiple shared-doctrine signals (low false-positive).
#
# NOTE: capture the hook's stdin into a var FIRST, then feed the python program
# via the heredoc — otherwise `python3 - <<PY` makes the heredoc itself stdin and
# json.load(sys.stdin) reads the program, not the tool input.
INPUT="$(cat)"
python3 - "$INPUT" <<'PY' 2>/dev/null || true
import json, sys, re

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)

ti = data.get("tool_input", {}) or {}
path = ti.get("file_path", "") or ""
if not re.search(r"(^|/)CLAUDE\.md$", path):
    sys.exit(0)  # only CLAUDE.md edits

content = ti.get("content") or ti.get("new_string") or ""
if not content:
    sys.exit(0)

SIGNALS = [
    "memory-library-discipline", "memory-retrieval-policy", "admin-merge",
    "sender-strict", "receiver-lenient", "6 intake checks", "grounding gate",
    "diagnostics-gate", "worktree-portability", "dirty-path", "exit-code grammar",
    "brief provenance", "prove-don't-assert", "sender/receiver duties",
]
hits = [s for s in SIGNALS if s.lower() in content.lower()]
if len(hits) >= 2:
    msg = (
        "Heads-up (STD-CLAUDE-001): this CLAUDE.md edit looks like it RESTATES "
        "shared standard(s) — matched: %s. Project CLAUDE.md should be thin and "
        "POINTER-based: replace the restated block with a pointer, e.g. "
        "\"Deploy follows STD-DEPLOY-001 — see shared/deployment-to-prod.md\". "
        "(Nudge only — not blocking; see shared/claude-md-standard.md.)"
        % ", ".join(hits[:4])
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}))
PY
exit 0
