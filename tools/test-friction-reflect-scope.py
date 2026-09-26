#!/usr/bin/env python3
"""Golden suite for check-friction-reflect.sh (scope + severity).

End-to-end: builds a synthetic transcript per case, runs the real hook, and
asserts on what it emits. Covers the scenarios the hook quality contract
requires: true positive, normal no-op, pasted transcript, quoted policy
language, code fence, read-only task, unrelated project, and a repeated
trigger in one session.

The decisive assertions are the SILENT ones. Before 2026-08-31 this hook
blocked unconditionally in every session, so every case below was a false
positive; the point of the suite is that ordinary work now passes untouched.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "check-friction-reflect.sh")
HOOK = os.path.normpath(HOOK)

WARN, SILENT = "warn", "silent"


def tool_use(name, **inp):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": inp}]}}


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def assistant(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


def clear_marker(session_id):
    """The hook writes a once-per-session marker to /tmp. It survives between
    suite runs, so without this the repeat-trigger case sees the PREVIOUS run's
    marker and reports silent-then-silent on a hook that is behaving correctly.
    """
    import hashlib
    p = "/tmp/claude-fork-reflect-" + hashlib.sha1(session_id.encode()).hexdigest()[:16]
    try:
        os.unlink(p)
    except OSError:
        pass


def run(entries, session_id):
    tf = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for e in entries:
        tf.write(json.dumps(e) + "\n")
    tf.close()
    payload = json.dumps({"session_id": session_id, "stop_hook_active": False,
                          "transcript_path": tf.name})
    p = subprocess.run(["bash", HOOK], input=payload, capture_output=True, text=True)
    os.unlink(tf.name)
    out = p.stdout.strip()
    if not out:
        return SILENT, ""
    try:
        d = json.loads(out)
    except Exception:
        return "MALFORMED(%s)" % out[:60], ""
    if "decision" in d:
        return "BLOCK", d.get("reason", "")
    if "systemMessage" in d:
        return WARN, d["systemMessage"]
    return "UNKNOWN", out


CASES = [
    # ---- must WARN: the session genuinely wrote to an infra surface ---------
    (WARN, "wrote a hook file",
     [tool_use("Write", file_path="/Users/x/.claude/hooks/autonomy-gate.py", content="x")]),
    (WARN, "edited harness settings",
     [tool_use("Edit", file_path="/Users/x/.claude/settings.json", old_string="a", new_string="b")]),
    (WARN, "edited global doctrine",
     [tool_use("Edit", file_path="/Users/x/.claude/CLAUDE.md", old_string="a", new_string="b")]),
    (WARN, "appended to a fork doc via bash redirect",
     [tool_use("Bash", command="cat >> ~/bmad-method-v6/docs/fork-gaps.md <<'EOF'\nx\nEOF")]),
    (WARN, "ran the sync script",
     [tool_use("Bash", command="~/bmad-method-v6/sync-bmad-workflows.sh")]),
    (WARN, "wrote a skill file",
     [tool_use("Write", file_path="/Users/x/.claude/skills/foo/SKILL.md", content="x")]),
    (WARN, "edited a project _bmad workflow",
     [tool_use("Edit", file_path="/repo/_bmad/bmm/workflows/x.md", old_string="a", new_string="b")]),

    # ---- must be SILENT: read-only work on infra ----------------------------
    (SILENT, "READ a fork file",
     [tool_use("Read", file_path="/Users/x/bmad-method-v6/STATUS.md")]),
    (SILENT, "cat a hook file (read-only bash)",
     [tool_use("Bash", command="cat ~/.claude/hooks/scope-tag-warn.py")]),
    (SILENT, "grep across the fork (read-only bash)",
     [tool_use("Bash", command="grep -rn 'sync' ~/bmad-method-v6/docs/")]),
    (SILENT, "sed -n range read of settings",
     [tool_use("Bash", command="sed -n '1,40p' ~/.claude/settings.json")]),
    (SILENT, "read global doctrine only",
     [tool_use("Read", file_path="/Users/x/.claude/CLAUDE.md")]),

    # ---- must be SILENT: ordinary application work -------------------------
    (SILENT, "normal app code edit",
     [tool_use("Edit", file_path="/repo/src/server/listings/sku.ts",
               old_string="a", new_string="b")]),
    (SILENT, "ran the test suite",
     [tool_use("Bash", command="npx vitest run")]),
    (SILENT, "unrelated project write",
     [tool_use("Write", file_path="/repo/docs/data-flows.md", content="x")]),
    (SILENT, "empty session", []),
    (SILENT, "conversation only, no tools",
     [user("what's the plan?"), assistant("Merge, then fix the parser.")]),

    # ---- must be SILENT: topic words without any infra WRITE ----------------
    (SILENT, "user pasted the words fork/hook/infra",
     [user("The fork and the hook and the infra workflow are all annoying."),
      assistant("Noted."), tool_use("Read", file_path="/repo/src/a.ts")]),
    (SILENT, "assistant discussed infrastructure abstractly",
     [assistant("A Stop hook in ~/.claude/hooks/ could enforce that."),
      tool_use("Read", file_path="/repo/src/a.ts")]),
    (SILENT, "pasted transcript mentioning sync-bmad-workflows",
     [user("Log said: `~/bmad-method-v6/sync-bmad-workflows.sh` ran and failed."),
      tool_use("Read", file_path="/repo/src/a.ts")]),
    (SILENT, "quoted policy language in a fence",
     [user("```\nEdit ~/.claude/hooks/x.py then re-sync\n```\nIs that right?"),
      tool_use("Read", file_path="/repo/src/a.ts")]),
]


def main():
    failures = []
    for want, name, entries in CASES:
        # stable id per case + explicit marker clear = deterministic across runs
        sid = "golden-" + hashlib.sha1(name.encode()).hexdigest()[:12]
        clear_marker(sid)
        got, msg = run(entries, sid)
        if got != want:
            failures.append("  %-46s want %-6s got %s" % (name, want, got))
        if got == WARN and len(msg.split("\n")) > 12:
            failures.append("  %-46s WARN exceeded 12 lines (%d)"
                            % (name, len(msg.split("\n"))))

    # repeated trigger in one session -> exactly one emission
    sid = "golden-repeat"
    clear_marker(sid)
    e = [tool_use("Write", file_path="/Users/x/.claude/hooks/a.py", content="x")]
    first, _ = run(e, sid)
    second, _ = run(e, sid)
    if first != WARN or second != SILENT:
        failures.append("  %-46s want warn-then-silent got %s then %s"
                        % ("repeated trigger in one session", first, second))

    # nothing may ever BLOCK
    print("friction-reflect scope suite: %d cases, %d failed"
          % (len(CASES) + 1, len(failures)))
    if failures:
        print("\n".join(failures))
        return 1
    print("all green (and no case emitted BLOCK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
