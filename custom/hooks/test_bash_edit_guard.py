#!/usr/bin/env python3
"""Golden cases for bash_edit_guard.py.

Run: python3 .claude/hooks/test_bash_edit_guard.py

The suite this replaces claimed "6/6 pass, Bash allowlist ALIGNED with Edit|Write"
(fork-gaps 2026-07-19). It was wrong on both counts:

  - it never covered `>>` APPEND forms, and
  - the Bash allowlist contained NONE of `_bmad-output/`, project `.claude/`, or
    `.sprint-apply-*` — only the HOME `~/.claude/`.

So the alignment was asserted, never tested. Every append case below (A1-A4) and
every project-path case (P1-P3) FAILS against the old inline guard. Do not re-assert
"aligned" without running this.
"""

import json
import os
import subprocess
import tempfile
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "bash_edit_guard.py")
PROJECT = os.path.dirname(os.path.dirname(HERE))

ALLOW, DENY, ASK = "allow", "deny", "ask"

# (id, command, expected, why)
CASES = [
    # --- The regression this guard was written for -------------------------------
    ("R1", "cat >> .claude/wip-register.yaml <<'EOF'\n  - surface: x\nEOF", ALLOW,
     "THE BUG. Relative-path append of the WIP claim from the main checkout. The "
     "register contract MANDATES this write happen here; the old guard said 'call "
     "EnterWorktree', which the contract forbids. Deadlocked the claim protocol."),
    ("R2", f"cat >> {PROJECT}/.claude/wip-register.yaml", ALLOW,
     "Same write, absolute path. Old guard also denied: its .claude/ exemption was "
     "/Users/*/.claude/ (HOME only), which a project path never matches."),
    ("R3", "echo x > .claude/wip-register.yaml", ALLOW,
     "Truncating write to the register — same exemption, different operator."),

    # --- Mixed targets are NOT exempt (the carve-out must not become a bypass) ----
    ("M1", "echo a >> .claude/wip-register.yaml; echo b > src/db/schema.ts", DENY,
     "Register + protected source. An unconditional string-match exemption would "
     "allow this — write anything, name the register. Mirrors collision_guard's "
     "'a mixed target is not exempt'."),
    ("M2", "echo a > /tmp/scratch; echo b > src/db/schema.ts", DENY,
     "THE FALSE NEGATIVE the old guard had: it exited 0 on seeing '> /tmp/' and "
     "never looked at the schema write. A mixed command was exempted by its most "
     "innocent target."),

    # --- Append forms across the allowlist (never previously tested) -------------
    ("A1", "echo x >> _bmad-output/planning-artifacts/scope-register.md", ALLOW,
     "Append to a BMAD artifact dir. Absent from the old Bash allowlist entirely."),
    ("A2", "cat >> ~/.claude/mailbox/cash-recovery.inbox.md", ALLOW,
     "Append to the agent mailbox — documented normal op, no worktree lane exists."),
    ("A3", f"echo x >> {PROJECT}/_bmad/.sprint-apply-pending.json", ALLOW,
     "Append to sprint-apply state. Absent from the old Bash allowlist."),
    ("A4", "echo x >> ~/bmad-method-v6/docs/fork-gaps.md", ALLOW,
     "Append to the fork — its own repo, its own delivery flow. The recurring "
     "gap-#111 case, hit again this session."),

    # --- Project-relative allowlist parity with Edit|Write -----------------------
    ("P1", "echo x > .claude/settings.local.json", ALLOW, "Machine-local config, gitignored."),
    ("P2", "tee -a .claude/main-edit-overrides.log", ALLOW, "Local audit log, tee -a form."),
    ("P3", "sed -i '' 's/a/b/' _bmad-output/notes.md", ALLOW, "sed -i on an artifact path."),

    # --- Still DENIED: real deliverable code -------------------------------------
    ("D1", "echo x > src/db/schema.ts", DENY, "Project source. The guard's actual job."),
    ("D2", "sed -i '' 's/a/b/' src/domain/units.ts", DENY, "In-place edit of source."),
    ("D3", "tee src/app/page.tsx", DENY, "tee onto source."),
    ("D4", "echo x >> drizzle/migrations/0023_thing.sql", DENY,
     "Migrations collide hardest and are caught latest — must stay gated."),

    # --- Must never fire (false-positive guards) ---------------------------------
    ("N1", "grep -r 'foo > bar' src/", ALLOW, "A redirect-looking string inside a quoted pattern."),
    ("N2", "ls -la 2>&1 | head", ALLOW, "fd-dup, not a redirect."),
    ("N3", "git commit -m 'fix: handle a > b and write .claude/wip-register.yaml'", ALLOW,
     "Commit MESSAGE containing both a '>' and a path. Prose, not a write. Without "
     "this the guard fires on its own commit."),
    ("N4", "cat src/db/schema.ts", ALLOW, "Read-only."),
    ("N5", "python3 -c \"import json; print(json.load(open('x.json')))\"", ALLOW,
     "Read-only python, no write shape. (The 2026-07-16 openpyxl false positive.)"),
    ("N6", "npm run build", ALLOW, "No write target."),
    ("N7", "python3 - <<'PY'\nwhile len(keep)>=2 and keep[-1]=='':\n    keep.pop()\nPY", ALLOW,
     "GREATER-OR-EQUAL is not a redirect. Found live: this guard fired on the very "
     "cleanup script written after wiring it, reading `len(keep)>=2` as a write to a "
     "file named '=2'. ')' is not in the lookbehind set. Comparison operators are "
     "everywhere in inline python/awk piped through Bash — high-frequency, not edge."),
    ("N8", "awk 'NR>=3 && $2>1 {print}' data.txt", ALLOW,
     "Same class in awk: >= and > as comparisons inside a quoted program."),
    ("N9", "python3 - <<'PY'\nwhile len(keep) > 1 and keep[-1]=='':\n    keep.pop()\nPY", ALLOW,
     "SPACED '>' inside a heredoc body. Fired live on the second cleanup attempt, "
     "reading `len(keep) > 1` as a write to a file named '1'. Unlike '>=', this is "
     "genuinely ambiguous to a regex — `echo x > 1` IS a real redirect — so the fix "
     "is scoping heredoc BODIES out, not tightening the operator."),
    ("H1", "cat >> .claude/wip-register.yaml <<'EOF'\nprint(1 > 0)\nEOF", ALLOW,
     "Heredoc stripping must keep the HEADER's redirect: target is the register "
     "(exempt), and the body's '>' is ignored. Both halves in one case."),
    ("H2", "cat > src/db/schema.ts <<'EOF'\nexport const x = 1;\nEOF", DENY,
     "The critical inverse: stripping BODIES must not blind the guard to a heredoc "
     "write onto real source. If this ever flips to allow, the guard is defeated."),

    # --- Fail-closed on unresolvable targets -------------------------------------
    ("U1", "echo x > $TARGET_FILE", DENY,
     "Unresolvable target inside a real write shape -> treated as protected. The "
     "guard cannot expand variables; it must not guess in the permissive direction."),
    ("U2", "echo x > $(mktemp)", DENY,
     "Command substitution stays unresolvable even now that literal $VAR assignments "
     "are substituted. Only a LITERAL assignment in the same command is resolved."),

    # --- Leading `cd` sets the resolution base (fork-gaps FG-2026-07-21-02) -------
    # Both C-cases are commands that were WRONGLY DENIED on 2026-07-26. The guard was
    # right about the path it judged and wrong about which path the command touched.
    ("C1", "cd /Users/masonwood/bmad-method-v6 && sed -i '' 's/a/b/' tools/check-scope-register.js", ALLOW,
     "THE BUG. The fork is exempt, but the relative target was resolved against "
     "CLAUDE_PROJECT_DIR, producing cash-recovery/tools/check-scope-register.js — a "
     "file that does not exist — and denying an allowlisted fork edit."),
    ("C2", "cd ~/bmad-method-v6 && printf 'x\\n' > docs/fork-gaps.md", ALLOW,
     "Same, with ~ and an append-free truncate. CLAUDE.md states fork paths are "
     "allowlisted for direct editing; before this the Bash arm disagreed."),
    ("C3", "cd /Users/masonwood/bmad-method-v6 && sed -i '' 's/a/b/' /Users/masonwood/code/cash-recovery/src/db/schema.ts", DENY,
     "A leading cd must NOT launder an ABSOLUTE protected target. The base only "
     "applies to relative paths."),
    ("C4", "cd src && echo x > db/schema.ts", DENY,
     "A leading cd into the project's own tree still resolves onto protected source. "
     "Honouring cd is about resolving correctly, not about exempting anything."),

    # --- Literal $VAR substitution (the /tmp probe case) -------------------------
    ("V1", "T=/tmp/probe-1; mkdir -p \"$T\"; printf 'x\\n' > \"$T/.gitignore\"", ALLOW,
     "WRONGLY DENIED 2026-07-26. T is assigned a literal /tmp path in the same "
     "command, so the target IS resolvable; /tmp/ is exempt. The old deny message "
     "told the agent to 'use a literal path' — the guard knew it could not resolve, "
     "and blocked anyway."),
    ("V2", "D=/Users/masonwood/code/cash-recovery/src; echo x > $D/db/schema.ts", DENY,
     "Substitution must work in BOTH directions: resolving this one turns a "
     "previously-unresolvable target into a PROTECTED one. Precision, not leniency."),
    ("V3", "T=/tmp/probe-$$; printf 'x\\n' > \"$T/f\"", DENY,
     "The assignment is not fully literal ($$ is a substitution), so T is skipped and "
     "the target stays unresolvable -> protected. Fails closed on partial knowledge. "
     "First cut TRUNCATED the value at $ instead of skipping it, resolved $T/f to "
     "/tmp/probe-/f, and allowed — a confident verdict about a nonexistent path."),

    # --- Quoted-string mentions are DATA, not writes (FG-2026-07-16-03 / -18-01) ---
    ("Q1", "python3 -c \"print('tokens: sed -i / cat > file / tee x')\"", ALLOW,
     "LIVE FALSE POSITIVE 2026-07-26. A read-only python one-liner whose STRING mentions "
     "edit-equivalent tokens was denied, and the deny listed 'x, cat, >, but, writes, "
     "nothing' as its targets. The quoted-span rule applied to redirects only; tee/sed/awk "
     "ignored it. A verdict whose own evidence is word salad is a verdict to distrust."),
    ("Q2", "echo 'run: tee /etc/hosts' >> .claude/wip-register.yaml", ALLOW,
     "The quoted mention is data; the REAL target is the exempt register. Both halves."),
    ("Q3", "echo 'harmless' | tee src/db/schema.ts", DENY,
     "The inverse that must not break: an UNQUOTED tee onto real source still denies. "
     "Quoted-span filtering must not blind the guard to the actual write."),
    ("Q4", "sed -i '' 's/a/b/' src/db/schema.ts", DENY,
     "A real in-place edit on protected source. The sed script is quoted, the FILE is not."),

    # --- ASK, not DENY, for low-risk text (owner ruling 2026-07-26) ---------------
    # A hard deny on a text edit does not stop it — it reroutes it into a script the guard
    # cannot see. `ask` costs one prompt and leaves nothing to route around.
    ("K1", "echo 'note' >> CLAUDE.md", ASK,
     "THE CASE THAT FORCED THIS. A docs-only main-checkout edit was denied, the Edit tool "
     "could not set the env-var override, and the change went through a script instead — the "
     "sanctioned route became the bypass."),
    ("K2", "echo x >> docs/deployment.md", ASK, "Docs path, low-risk text."),
    ("K3", "echo x >> RUNBOOK.txt", ASK, "Plain text at the repo root."),
    ("K4", "echo x >> src/README.md", DENY,
     "A .md ADJACENT TO CODE is not low-risk text — extension alone must never decide. If "
     "this ever flips to ask, the set is too wide."),
    ("K5", "echo x >> .github/workflows/ci.yml", DENY, "CI config is never in the ask set."),
    ("K6", "echo x >> package.json", DENY, "Dependency manifest is never in the ask set."),
    ("K7", "echo a >> CLAUDE.md; echo b > src/db/schema.ts", DENY,
     "MIXED targets: one low-risk text file does not make the whole command askable. Same "
     "rule as the register carve-out — a mixed target is not exempt."),
]


def run(cmd: str, extra_env: dict = None, payload_cwd: str = None) -> str:
    body = {"tool_input": {"command": cmd}}
    if payload_cwd:
        body["cwd"] = payload_cwd
    payload = json.dumps(body)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=PROJECT)
    env.pop("BMAD_ALLOW_MAIN_EDIT", None)  # a set override would green the whole suite
    # Never write test rows into the real override audit log (the first live entry turned out
    # to be case O1, not a human).
    # Into the system temp dir, NOT the repo: the suite must not leave an artifact behind
    # that someone then has to gitignore.
    env["BASH_EDIT_GUARD_LOG"] = os.path.join(
        tempfile.gettempdir(), "bash-edit-guard-test-override.jsonl")
    if extra_env:
        env.update(extra_env)
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, env=env, cwd=PROJECT).stdout.strip()
    if not out:
        return ALLOW
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return f"malformed: {out[:80]}"


def main():
    # Precondition: the suite must run OUTSIDE a worktree, else every case trivially
    # allows and the suite reports a meaningless green.
    if "/.claude/worktrees/" in PROJECT:
        print("REFUSING TO RUN: suite must execute from the main checkout, not a worktree.")
        return 1

    failed = []
    for cid, cmd, expected, why in CASES:
        got = run(cmd)
        ok = got == expected
        if not ok:
            failed.append((cid, cmd, expected, got, why))
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:3} expected={expected:5} got={got:5}  {cmd.splitlines()[0][:64]}")

    # The LOGGED override, checked as a pair. A one-sided check would pass on a guard that
    # ignores the variable entirely (O1 only) or on one that is simply off (O2 only).
    OVERRIDE = [
        ("O1", "echo x > src/db/schema.ts", {"BMAD_ALLOW_MAIN_EDIT": "1"}, ALLOW,
         "The documented override must actually work. Before this it was named in the deny "
         "message and honoured by no guard — an inert escape hatch, which is why every real "
         "use became a tool-swap bypass (fork-gaps FG-2026-07-25-02)."),
        ("O2", "echo x > src/db/schema.ts", {}, DENY,
         "Same command WITHOUT the override still denies. Proves O1 is the variable doing the "
         "work, not the guard being off."),
        ("O3", "echo x > src/db/schema.ts", {"BMAD_ALLOW_MAIN_EDIT": "yes"}, DENY,
         "Exact-match only. A truthy-looking value must not open the gate."),
    ]
    for cid, cmd, env, expected, why in OVERRIDE:
        got = run(cmd, env)
        ok = got == expected
        if not ok:
            failed.append((cid, cmd, expected, got, why))
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:3} expected={expected:5} got={got:5}  "
              f"{cmd[:40]} env={env or '{}'}")

    # --- The override must LOG, and the suite must not pollute the real log -----------
    # Permitting is only half the contract. An override that opens the gate and writes no
    # row is a SILENT escape hatch — the anti-pattern the override-with-logging rule names
    # explicitly — and it would pass O1 happily. So assert the row, its shape, and the
    # isolation of the real audit log. (The first entry ever written to the live log turned
    # out to be case O1 rather than a human, which is what prompted L3.)
    extra = []
    real_log = os.path.join(os.path.expanduser("~"), ".claude", "logs",
                            "bash-edit-guard-override.jsonl")
    real_before = os.path.getsize(real_log) if os.path.exists(real_log) else None

    with tempfile.TemporaryDirectory() as td:
        probe = os.path.join(td, "override-probe.jsonl")

        def fire(env_extra):
            e = dict(os.environ, CLAUDE_PROJECT_DIR=PROJECT, BASH_EDIT_GUARD_LOG=probe)
            e.pop("BMAD_ALLOW_MAIN_EDIT", None)
            e.update(env_extra)
            subprocess.run([sys.executable, GUARD],
                           input=json.dumps({"tool_input": {"command": "echo x > src/db/schema.ts"}}),
                           capture_output=True, text=True, env=e, cwd=PROJECT)

        fire({"BMAD_ALLOW_MAIN_EDIT": "1"})
        rows = [json.loads(l) for l in open(probe)] if os.path.exists(probe) else []
        extra.append(("L1", "override writes exactly one audit row", len(rows) == 1,
                      "A silent override defeats the audit; permitting without logging would pass O1."))
        shape_ok = bool(rows) and {"at", "cwd", "targets", "protected"} <= set(rows[0]) \
            and "src/db/schema.ts" in rows[0].get("protected", [])
        extra.append(("L2", "audit row names the protected target and when", shape_ok,
                      "A row that does not say WHAT was overridden is not an audit trail."))

        n_after_allow = len(rows)
        fire({})  # denied path must not log
        rows2 = [json.loads(l) for l in open(probe)] if os.path.exists(probe) else []
        extra.append(("L4", "a DENIED call writes no audit row", len(rows2) == n_after_allow,
                      "Only exercised overrides belong in the log, or the signal is diluted."))

    real_after = os.path.getsize(real_log) if os.path.exists(real_log) else None
    extra.append(("L3", "suite left the real override log untouched", real_before == real_after,
                  "A log polluted by its own tests is not an audit trail. The first live entry "
                  "was case O1, not a human."))

    for cid, what, ok, why in extra:
        if not ok:
            failed.append((cid, what, "pass", "fail", why))
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:3} {what}")

    # --- OBSERVED cwd beats ASSUMED cwd (FG-2026-07-26-06) ---------------------------
    # The harness moves a session into a worktree without moving CLAUDE_PROJECT_DIR. Reading
    # only the env var told a session standing INSIDE `.claude/worktrees/…` that it was not in a
    # worktree — punishing the session that did the right thing, whose only way out is the bypass.
    WT = os.path.join(PROJECT, ".claude", "worktrees", "feat-probe")
    cwd_cases = [
        ("W1", "echo x > src/db/schema.ts", WT, ALLOW,
         "THE BUG. Payload cwd is inside a worktree, so the session is already isolated and "
         "nothing should be denied — regardless of what CLAUDE_PROJECT_DIR says."),
        ("W2", "echo x > src/db/schema.ts", PROJECT, DENY,
         "Payload cwd is the MAIN checkout: still denied. Proves W1 is the worktree doing the "
         "work, not the payload key merely being present."),
        ("W3", "echo x > src/db/schema.ts", None, DENY,
         "No payload cwd (direct/test invocation) falls back to CLAUDE_PROJECT_DIR — the old "
         "behaviour, unchanged."),
    ]
    for cid, cmd, pcwd, expected, why in cwd_cases:
        got = run(cmd, payload_cwd=pcwd)
        ok = got == expected
        if not ok:
            failed.append((cid, cmd, expected, got, why))
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:3} expected={expected:5} got={got:5}  "
              f"payload_cwd={'<worktree>' if pcwd == WT else ('<project>' if pcwd else 'none')}")
    # --- The marker override: reachable, single-use, consumed (FG-2026-07-25-02 reversal) ------
    # The env var alone was UNREACHABLE from inside a turn: an inline `VAR=1 cmd` prefix sets the
    # variable for the COMMAND's process, while the hook runs separately off the harness env — and
    # the Edit tool has no channel to set one at all. An override no route can exercise is not an
    # override. The marker lives under `.claude/` (already exempt), so creating it is never blocked.
    mk = os.path.join(PROJECT, ".claude", ".allow-main-edit")
    marker_cases = []
    try:
        open(mk, "w").close()
        marker_cases.append(("M1", run("echo x > src/db/schema.ts") == ALLOW,
                             "marker present -> allowed (the reachable in-band override)"))
        marker_cases.append(("M2", not os.path.exists(mk),
                             "marker CONSUMED by that use — one marker, one override"))
        marker_cases.append(("M3", run("echo x > src/db/schema.ts") == DENY,
                             "the very next identical command is denied again — no lingering gate"))
    finally:
        if os.path.exists(mk):
            os.remove(mk)
    for cid, ok, why in marker_cases:
        if not ok:
            failed.append((cid, "marker override", "pass", "fail", why))
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:3} {why}")

    extra_count = len(extra) + len(cwd_cases) + len(marker_cases)

    total = len(CASES) + len(OVERRIDE) + extra_count
    print(f"\n{total - len(failed)}/{total} passed")
    for cid, cmd, expected, got, why in failed:
        print(f"\nFAILED {cid}: expected {expected}, got {got}\n  cmd: {cmd}\n  why it matters: {why}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
