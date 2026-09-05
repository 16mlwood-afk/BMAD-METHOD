#!/usr/bin/env python3
"""
hook-resolve-check — report any WIRED hook whose script is not on disk.

THE PATTERN THIS CATCHES (FG-2026-07-31-15). Twice on 2026-07-31, commit `827e9c3`
("chore(snapshot): parked main-checkout working state") left four wired hook scripts missing
from the working tree — `session_audit_stop.py` (Stop hook, exiting 2 every turn),
`brief_regen_guard.py` (hard-erroring EVERY Edit call for every session in the checkout),
`autonomy_friction_log.py`, `deploy_script_freshness_guard.py`.

**Both were found incidentally.** One surfaced because it blocked an unrelated edit mid-build;
the other because the owner reported the exit-2. Nobody was watching, and nothing was. The
scripts are wired in `settings.local.json`, which is gitignored by policy, so they are absent
from `origin/main` entirely — a fresh clone cannot know they should exist, and no diff against
the remote can detect their absence.

Run by hand for that fork-gap entry, this check found all four in a single sweep. This file is
that sweep, at login, every session.

SILENT WHEN CLEAN — non-negotiable. A banner that prints on every healthy session becomes
wallpaper, and wallpaper is how the real warning gets skipped. It speaks only when something is
actually missing.

RESOLUTION IS BY BASENAME, DELIBERATELY. Eight distinct path prefixes are in live use across the
two settings files — `$CLAUDE_PROJECT_DIR/`, `$D/`, `$R/`, `${CLAUDE_PROJECT_DIR:-$PWD}/`,
`${PWD%%/.claude/worktrees/*}/`, `$HOME/code/cash-recovery/`, a bare relative path, and one
inside a subshell. Every one of them denotes this project's `.claude/hooks/`. Rather than
expand shell variables — the guesswork that produced four separate false-positive classes in
the Bash edit-guard — this keys on the `.claude/hooks/<basename>` fragment and resolves it
against the MAIN checkout. A hook deliberately wired to some other directory would be a false
negative; none exists, and inventing a shell parser to cover a hypothetical is the wrong trade.

REPORTS, NEVER BLOCKS. SessionStart cannot block anyway, and this is an awareness tier by
design: it names the file, the settings file that wires it, the event, and the recovery route
that actually worked twice today (`git log --all -- <path>`, then `git show <sha>:<path>`).

FAIL OPEN. Unreadable settings, malformed JSON, missing hooks dir → exit 0 in silence.
"""
import json
import os
import re
import sys

HOOK_REF = re.compile(r"\.claude/hooks/([A-Za-z0-9_.-]+\.(?:py|sh))")
SETTINGS = ("settings.json", "settings.local.json")


def main_checkout(cwd):
    d = cwd or os.getcwd()
    return d.split("/.claude/worktrees/")[0] if "/.claude/worktrees/" in d else d


def wired(root):
    """{basename: [(settings_file, event), ...]} for every hook script referenced."""
    found = {}
    for name in SETTINGS:
        p = os.path.join(root, ".claude", name)
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue                       # malformed settings is not this check's job
        for event, groups in (data.get("hooks") or {}).items():
            if not isinstance(groups, list):
                continue
            for g in groups:
                for h in (g or {}).get("hooks", []) or []:
                    for m in HOOK_REF.finditer(str(h.get("command", ""))):
                        found.setdefault(m.group(1), []).append((name, event))
    return found


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {}
    root = main_checkout(data.get("cwd"))
    hooks_dir = os.path.join(root, ".claude", "hooks")
    if not os.path.isdir(hooks_dir):
        return 0

    refs = wired(root)
    missing = {n: w for n, w in refs.items() if not os.path.exists(os.path.join(hooks_dir, n))}
    if not missing:
        return 0                            # silent when clean — the whole point

    out = ["─" * 58,
           f"⚠ {len(missing)} WIRED HOOK(S) MISSING — the guard is configured and NOT running"]
    for name in sorted(missing):
        where = ", ".join(sorted({f"{f}:{e}" for f, e in missing[name]}))
        out.append(f"    · {name}")
        out.append(f"        wired in {where}")
    out += [
        "",
        "  A wired hook with no file is silently inert. On 2026-07-31 this state went",
        "  unnoticed twice until something unrelated broke — a Stop hook exiting 2, and an",
        "  Edit guard erroring on every call.",
        "",
        "  RECOVER (this worked both times):",
        "    git log --all -1 --format=%H -- .claude/hooks/<name>",
        "    git show <sha>:.claude/hooks/<name> > .claude/hooks/<name>",
        "",
        "  If it is in no commit, it was never tracked — see FG-2026-07-31-15.",
        "─" * 58,
    ]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                        # noqa: BLE001 - awareness tier, never a blocker
        sys.exit(0)
