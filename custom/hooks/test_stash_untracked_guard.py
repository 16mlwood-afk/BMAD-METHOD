#!/usr/bin/env python3
"""Golden cases for stash-untracked-guard.py.

MOST OF THESE ASSERT SILENCE. A guard that fires on ordinary work gets switched
off, and then it guards nothing — so the ordinary shapes are tested harder than
the offending one.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).with_name("stash-untracked-guard.py")

DENY = 2
ALLOW = 0


def run(command: str, tool: str = "Bash") -> tuple[int, str]:
    payload = {"tool_name": tool, "tool_input": {"command": command}}
    p = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return p.returncode, p.stderr


CASES: list[tuple[str, str, int]] = [
    # ---- the incident, and its neighbours -------------------------------
    ("the exact command from 2026-09-13", 'git stash push -u -m "close-out"', DENY),
    ("the 2026-09-10 one, same shape", "git stash push -u", DENY),
    ("long form", "git stash push --include-untracked", DENY),
    ("-a takes ignored files too", "git stash push -a", DENY),
    ("--all", "git stash --all", DENY),
    ("bundled short flags", "git stash push -um 'wip'", DENY),
    ("save, the older spelling", "git stash save -u 'wip'", DENY),
    ("with a -C before the subcommand", "git -C /repo stash push -u", DENY),
    ("hiding after a harmless command", "ls -la && git stash push -u", DENY),
    ("second in a chain", "git fetch; git stash -u; git pull", DENY),
    # ---- ordinary work that MUST NOT fire -------------------------------
    ("a plain stash — what the incident actually needed", 'git stash push -m "wip"', ALLOW),
    ("bare stash", "git stash", ALLOW),
    ("naming paths, the right answer", "git stash push src/foo.ts", ALLOW),
    ("popping", "git stash pop", ALLOW),
    ("applying by sha", "git stash apply 41fef2d", ALLOW),
    ("listing", "git stash list --format='%gd %gs'", ALLOW),
    ("showing untracked in a stash is a READ", "git stash show --include-untracked sha", ALLOW),
    ("dropping", "git stash drop stash@{0}", ALLOW),
    # `-u` and `-a` are ordinary flags on other git commands. None of these
    # touches an untracked file the way `stash -u` does.
    ("add -u is tracked-only by definition", "git add -u", ALLOW),
    ("commit -a stages tracked changes", "git commit -a -m 'x'", ALLOW),
    ("push --all is about refs", "git push --all origin", ALLOW),
    ("log --all", "git log --all --oneline", ALLOW),
    ("branch -a", "git branch -a", ALLOW),
    ("a -u belonging to a NEIGHBOUR command", "git add -u && git stash push -m 'x'", ALLOW),
    ("ls -u beside a clean stash", "ls -u; git stash", ALLOW),
    # ---- not our business ------------------------------------------------
    ("a different tool entirely", "git stash push -u", ALLOW),  # tool overridden below
    ("the override, used deliberately", "STASH_UNTRACKED_OVERRIDE=1 git stash push -u", ALLOW),
    ("the word stash in prose", "echo 'do not git stash -u here'", DENY),
]


# The guard being right is HALF of it. On 2026-09-13 the script denied correctly
# and the settings line said `[ -f "$S" ] && python3 "$S" || exit 0` — in which
# `||` catches python's exit 2 and turns the refusal into an ALLOW. The hook was
# wired, tested, and a no-op. So the wiring is a golden case of its own: these run
# the command string out of settings.json exactly as the harness would.
# WHERE THE WIRING LIVES DEPENDS ON WHERE THIS FILE IS.
# Installed in a project, it is <root>/.claude/settings.json. In the BMAD fork — which
# is the SOURCE of this guard and has no .claude/settings.json of its own — the wiring
# that matters is the DISTRIBUTION TEMPLATE, because that is the artefact that decides
# whether fourteen projects get the hook wired at all. Checking the template here turns
# this case into a completeness invariant on the distribution: add a guard to
# custom/hooks/ and forget to wire it in hooks.json, and this test says so.
# Returning None for "no settings anywhere" is NOT an option: silence would read as a
# pass, and an unwired guard is exactly what this case exists to catch.
def settings_source() -> Path | None:
    installed = GUARD.parent.parent / "settings.json"
    if installed.exists():
        return installed
    template = (
        GUARD.parent.parent.parent
        / "src/modules/bmm/_module-installer/assets/hooks.json"
    )
    if template.exists():
        return template
    return None


def wiring_command() -> str | None:
    settings = settings_source()
    if settings is None:
        return None
    data = json.loads(settings.read_text())
    for event in data.get("hooks", {}).get("PreToolUse", []):
        for hook in event.get("hooks", []):
            cmd = hook.get("command", "")
            if GUARD.name in cmd:
                return cmd
    return None


def check_wiring(failures: list[str]) -> None:
    cmd = wiring_command()
    if cmd is None:
        failures.append(
            "  the guard is NOT WIRED — neither .claude/settings.json nor the fork "
            "distribution template references it, and a passing script that nothing "
            "calls guards nothing"
        )
        return
    # Run the wiring string against a DISPOSABLE project laid out the way the sync
    # delivers one: <root>/.claude/hooks/<guard>. The command string is the artefact
    # under test, so it has to be executed the way the harness executes it — against a
    # real installed layout, not against whatever directory this file happens to sit in.
    tmp = tempfile.mkdtemp()
    hooks = Path(tmp) / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shutil.copy2(GUARD, hooks / GUARD.name)
    root = tmp
    for name, command, expected in [
        ("wiring passes the refusal through", "git stash push -u", DENY),
        ("wiring stays silent on ordinary work", "git stash pop", ALLOW),
    ]:
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        p = subprocess.run(
            ["sh", "-c", cmd],
            input=payload,
            capture_output=True,
            text=True,
            env={"PATH": os.environ.get("PATH", ""), "CLAUDE_PROJECT_DIR": root},
            cwd=root,
        )
        if p.returncode != expected:
            failures.append(
                f"  {name}\n    the wiring command returned {p.returncode}, "
                f"expected {expected} — the deny is being swallowed by the shell"
            )
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    failures: list[str] = []
    for name, command, expected in CASES:
        tool = "Edit" if name == "a different tool entirely" else "Bash"
        code, err = run(command, tool)
        if code != expected:
            failures.append(
                f"  {name}\n    command:  {command}\n"
                f"    expected: {'DENY' if expected == DENY else 'ALLOW'}, got "
                f"{'DENY' if code == DENY else 'ALLOW'}"
            )
        if expected == DENY and code == DENY:
            # A refusal has to say what to do instead, or it is just an obstacle.
            for needle in ("git stash push <paths>", "STASH_UNTRACKED_OVERRIDE=1"):
                if needle not in err:
                    failures.append(f"  {name}: refusal does not mention {needle!r}")

    # Unreadable input must never block: a guard that fails closed on its own
    # bug stops every Bash call in the session.
    p = subprocess.run(
        [sys.executable, str(GUARD)], input="not json", capture_output=True, text=True
    )
    if p.returncode != 0:
        failures.append("  malformed stdin must ALLOW, not block the session")

    check_wiring(failures)

    if failures:
        print(f"{len(failures)} failure(s):\n" + "\n".join(failures))
        return 1
    print(
        f"{len(CASES) + 2} golden cases pass "
        f"({sum(1 for c in CASES if c[2] == ALLOW)} assert silence, 2 run the settings.json wiring)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
