#!/usr/bin/env python3
"""
hook-resolve-check — report a guard that is configured but cannot actually run.

TWO FINDINGS, ONE FAMILY: a thing that looks exactly like a working guard and is not.

  1. WIRED BUT ABSENT  — settings name a hook script that is not on disk.
  2. PRESENT BUT NOT CARRIED — the script is on disk and the repository is set to
     ignore it, so a fresh clone gets a project that looks guarded and has none.

Both are silent by construction. Neither shows up in a diff, a test run, or a status
line. Each was found by accident, and each stayed true for weeks before it was.

FINDING 1 — WIRED BUT ABSENT (FG-2026-07-31-15). Twice on 2026-07-31, commit `827e9c3`
("chore(snapshot): parked main-checkout working state") left four wired hook scripts missing
from the working tree — `session_audit_stop.py` (Stop hook, exiting 2 every turn),
`brief_regen_guard.py` (hard-erroring EVERY Edit call for every session in the checkout),
`autonomy_friction_log.py`, `deploy_script_freshness_guard.py`.

**Both were found incidentally.** One surfaced because it blocked an unrelated edit mid-build;
the other because the owner reported the exit-2. Nobody was watching, and nothing was. The
scripts are wired in `settings.local.json`, which is gitignored by policy, so they are absent
from `origin/main` entirely — a fresh clone cannot know they should exist, and no diff against
the remote can detect their absence.

FINDING 2 — PRESENT BUT NOT CARRIED (added 2026-09-21). The paragraph above names this exact
gap and then does not check for it: it observes that a gitignored wiring file is absent from
the remote, and stops.

Measured by running this check against all fourteen registered targets on 2026-09-21, it fires
on FIVE. Four — comms_dashboard, bison-ops, bison-website, inbound-flow — ignore
`.claude/hooks/` wholesale and each already held six or more fork-delivered hook files with
**zero tracked**; three of those four also ignore `.claude/settings.json`, the registration
itself. A fifth, amazon-lead-generator, carries its guards fine and ignores only the wiring,
so a clone of it gets the scripts and nothing to fire them. Seven projects are clean and the
check says nothing about them.

Those five repositories are guarded on exactly one disk. A second machine, a colleague, CI,
or a re-clone after a laptop dies gets a repository with the guards deleted and nothing
anywhere saying so.

The sync already self-repairs the `.gitignore` when it runs in such a project, so the gap was
never the repair — it was that **nothing said the repository was in that state until somebody
happened to run a sync.** This says it at every session start.

THE DISTINCTION THE WHOLE CHECK RESTS ON: **ignored, not untracked.** A hook file that is
merely new and uncommitted is ordinary work — it is what every guard looks like in the minute
after it is written, and a check that fires on that gets switched off within a week, taking
the real finding with it. So being untracked is never the trigger. `git check-ignore` answers
"will this repository refuse to carry the file" exactly, with no heuristic and no guessing,
and cases S4 / N3 in `test_hook_resolve_check.py` pin both directions.

`settings.local.json` is EXEMPT and stays exempt. It holds per-machine permissions and trust
decisions and is gitignored deliberately; reporting it would fire in every project forever.
Only the tracked-by-intent `settings.json` is checked.

SILENT WHEN CLEAN — non-negotiable. A banner that prints on every healthy session becomes
wallpaper, and wallpaper is how the real warning gets skipped. It speaks only when something
is actually wrong.

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

FAIL OPEN. Unreadable settings, malformed JSON, missing hooks dir, no VCS, no `git` on PATH →
exit 0 in silence. A check that cannot look says nothing rather than something reassuring.

Golden cases: `python3 test_hook_resolve_check.py` (21, most asserting SILENCE).
"""
import json
import os
import re
import subprocess
import sys

HOOK_REF = re.compile(r"\.claude/hooks/([A-Za-z0-9_.-]+\.(?:py|sh))")
SETTINGS = ("settings.json", "settings.local.json")
# Only settings.json is expected to survive a clone. settings.local.json is
# gitignored on purpose — see the module docstring.
TRACKED_BY_INTENT = "settings.json"
SCRIPT_SUFFIXES = (".py", ".sh")
MAX_LISTED = 8


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


def _git(root, *args):
    """Run a read-only VCS query. None on any failure — this check never blocks."""
    try:
        r = subprocess.run(["git", "-C", root, *args],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r


def not_carried(root, relpaths):
    """Which of `relpaths` this repository will REFUSE to carry, in input order.

    A path qualifies only when it is BOTH untracked AND ignored. Untracked alone
    is a file somebody just wrote, which is ordinary work and must stay silent —
    that distinction is the difference between a usable check and one that gets
    switched off. Returns [] when the question cannot be answered at all.
    """
    if not relpaths:
        return []
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != "true":
        return []                          # not a repository — nothing to say

    listed = _git(root, "ls-files", "-z", "--", *relpaths)
    if listed is None or listed.returncode != 0:
        return []
    tracked = {p for p in listed.stdout.split("\0") if p}
    untracked = [p for p in relpaths if p not in tracked]
    if not untracked:
        return []

    # check-ignore exits 1 when NOTHING matches, which is a clean answer and not
    # an error; only a >1 code means it could not decide.
    try:
        proc = subprocess.run(["git", "-C", root, "check-ignore", "-z", "--stdin"],
                              input="\0".join(untracked), capture_output=True,
                              text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode > 1:
        return []
    ignored = {p for p in proc.stdout.split("\0") if p}
    return [p for p in untracked if p in ignored]


def hook_scripts_on_disk(hooks_dir):
    try:
        names = sorted(os.listdir(hooks_dir))
    except OSError:
        return []
    return [n for n in names
            if n.endswith(SCRIPT_SUFFIXES)
            and os.path.isfile(os.path.join(hooks_dir, n))]


def _listed(items):
    shown = [f"    · {i}" for i in items[:MAX_LISTED]]
    if len(items) > MAX_LISTED:
        shown.append(f"    · … and {len(items) - MAX_LISTED} more")
    return shown


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
    out = []

    # --- FINDING 1: wired, and the file is not there ------------------------
    missing = {n: w for n, w in refs.items() if not os.path.exists(os.path.join(hooks_dir, n))}
    if missing:
        out += [f"⚠ {len(missing)} WIRED HOOK(S) MISSING — the guard is configured and NOT running"]
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
        ]

    # --- FINDING 2: on disk, and the repository will not carry it -----------
    # Candidates are the guards themselves plus the registration that makes them
    # fire. Both have to survive a clone for the repository to be guarded at all.
    candidates = [f".claude/hooks/{n}" for n in hook_scripts_on_disk(hooks_dir)]
    settings_rel = f".claude/{TRACKED_BY_INTENT}"
    if os.path.exists(os.path.join(root, settings_rel)):
        candidates.append(settings_rel)

    uncarried = not_carried(root, candidates)
    stray_guards = [p.rsplit("/", 1)[-1] for p in uncarried if p != settings_rel]
    wiring_uncarried = settings_rel in uncarried

    if stray_guards or wiring_uncarried:
        if out:
            out.append("")
        n = len(stray_guards) + (1 if wiring_uncarried else 0)
        out.append(f"⚠ {n} GUARD FILE(S) NOT CARRIED BY THIS REPOSITORY — a fresh clone has none")
        if stray_guards:
            out += _listed(stray_guards)
        if wiring_uncarried:
            out.append(f"    · {TRACKED_BY_INTENT}  (the wiring — without it nothing fires at all)")
        out += [
            "",
            "  These files are on disk and the repository is set to IGNORE them, so they exist",
            "  on this machine only. A fresh clone, a second device or CI gets a project that",
            "  LOOKS guarded and is not, and nothing says so. Measured 2026-09-21: five of the",
            "  fourteen registered projects were in this state — four of them ignoring the whole",
            "  hooks directory, six files each, zero tracked.",
            "",
            "  This is NOT about an uncommitted file — a guard you just wrote is ordinary work",
            "  and is never reported here. These are IGNORED, which is a different thing.",
            "",
            "  FIX: run the fork sync in this project. It narrows the .gitignore and re-verifies,",
            "  or tells you exactly which negation to add:",
            "    ~/bmad-method-v6/sync-bmad-workflows.sh --only " + os.path.basename(root),
            "  then commit .claude/hooks/ and .claude/settings.json.",
        ]

    if not out:
        return 0                            # silent when clean — the whole point
    print("\n".join(["─" * 58] + out + ["─" * 58]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                        # noqa: BLE001 - awareness tier, never a blocker
        sys.exit(0)
