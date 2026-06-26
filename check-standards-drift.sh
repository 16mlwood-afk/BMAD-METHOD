#!/usr/bin/env bash
# SessionStart standards-drift check (Phase 1: WARN-only, non-blocking).
#
# Compares the FORK CANONICAL standards versions against the copy synced into the
# CURRENT project, by scanning the ID:/Version: lines in STANDARDS.md. The
# project's synced STANDARDS.md IS its declaration of "what versions I last
# pulled" — no separate lock file or CLAUDE.md block to maintain.
#
# Enforcement class: DETERMINISTIC delivery of awareness (the comparison runs and
# the result reaches context every session). Phase 1 = WARN only. Phase 2 would
# hard-warn on missing; Phase 3 would BLOCK on a `Breaking: yes` mismatch (a
# PreToolUse gate on deploy/etc) — see STANDARDS.md §"Versioning & drift".
#
# Conservative: SILENT when fully in sync (a "you're fine" message every session
# erodes trust). Emits the structured block only when there is real drift.
#
# Dumb by design: line-scan, no YAML parser, no file-content diffing.
CANON="$HOME/bmad-method-v6/custom/workflows/shared/STANDARDS.md"
[ -f "$CANON" ] || exit 0

# Locate the project's synced copy: command-layout first, then skills-layout.
PROJ=""
for p in "_bmad/bmm/workflows/shared/STANDARDS.md" "_bmad/bmad-shared/STANDARDS.md"; do
  [ -f "$p" ] && { PROJ="$p"; break; }
done

python3 - "$CANON" "$PROJ" <<'PY' 2>/dev/null || true
import json, re, sys

def parse(path):
    """Return {ID: Version}. Scans `ID:` then the next `Version:` line — block order."""
    out = {}
    if not path:
        return out
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return out
    cur = None
    for line in text.splitlines():
        a = re.match(r"^ID:\s*(\S+)", line)
        if a:
            cur = a.group(1); continue
        v = re.match(r"^Version:\s*(\S+)", line)
        if v and cur:
            out[cur] = v.group(1); cur = None
    return out

canon = parse(sys.argv[1])
proj_path = sys.argv[2] if len(sys.argv) > 2 else ""
proj = parse(proj_path)
if not canon:
    sys.exit(0)

def emit(msg):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": msg}}))

# Canon exists but never synced into this project.
if not proj_path:
    emit("Standards Drift Check\n\nWARN:\n- STANDARDS.md not synced into this "
         "project (run `sync bmad`).\n\nAction: sync the standards canon before "
         "deploy / memory / webhook-related tasks. WARN-only — not blocking.")
    sys.exit(0)

ok, warn = [], []
for sid in sorted(canon):
    cv = canon[sid]
    pv = proj.get(sid)
    if pv is None:
        warn.append(f"- {sid} missing (canonical={cv})")
    elif pv != cv:
        warn.append(f"- {sid} project={pv} canonical={cv}")
    else:
        ok.append(f"- {sid} @ {cv}")

if not warn:
    sys.exit(0)  # conservative: silent when fully in sync

parts = ["Standards Drift Check", ""]
if ok:
    parts += ["OK:"] + ok + [""]
parts += ["WARN:"] + warn + [""]
parts += ["Action:",
          "- Re-sync this project (`sync bmad`) or update it to match the "
          "canonical standards before deploy / memory / webhook-related tasks. "
          "WARN-only — not blocking."]
emit("\n".join(parts))
PY
exit 0
