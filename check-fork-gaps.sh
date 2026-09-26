#!/usr/bin/env bash
# SessionStart awareness hook — surface OPEN entries from the fork-gaps backlog
# (docs/fork-gaps.md) so they don't rot in a file nobody opens.
#
# Enforcement class: DETERMINISTIC delivery of AWARENESS (tier 4). The text WILL
# reach the agent's context every session; the agent acting on it (surfacing to
# the user, routing a fix) is still probabilistic — paired with the prose policy
# (workflow-friction-and-process-issues) and the mason-bmad-workflow-expert
# first-action read. There is no deterministic GATE here on purpose: an open
# fork-gap is not a dangerous action to block, just rot to keep visible.
#
# Entry detection (fixed 2026-07-03 — the original matched only `### ` headings
# inside a `## Open` section capture, which went blind the day entries started
# using `## YYYY-MM-DD — title` headings): an entry is ANY ##/### heading after
# the `## Open` line. Closed = `[resolved`/`[closed` in the heading (any case),
# OR a bold `**CLOSED`/`**RESOLVED` closure paragraph in the body.
# `[partly resolved …]` stays OPEN (it names an owed follow-up).
#
# Archive split (2026-07-06, gap 874): resolved entries now MOVE to
# docs/fork-gaps-archive.md; docs/fork-gaps.md holds ONLY open gaps, so the
# open set == every entry in the live file and the count matches a trivial
# heading grep. The body `**RESOLVED`/`**CLOSED` scan is kept as a harmless
# belt (a resolved entry should never be left here in the first place). This
# surfacer reads ONLY the live file. It also LISTS the open headings, not just
# a count, so the backlog is visible without opening the file.
#
# Also nudges (one line) when the periodic fork-gaps TREND SCAN is overdue:
# stamp file .fork-gaps-last-scan (gitignored, touched by the scan) older than
# 30 days or missing. Deterministic delivery, probabilistic action — the scan
# itself runs via the maintenance-session skill's "fork-gaps trend scan" lane.
#
# Conservative detector: silent when there are zero open gaps AND the scan is
# fresh (a false "you have work" every session erodes trust).
#
# Wired from ~/.claude/settings.json SessionStart (machine-local — hooks do NOT
# sync to the 13 projects; this surfacer ships only where settings.json calls it).
F="$HOME/bmad-method-v6/docs/fork-gaps.md"
STAMP="$HOME/bmad-method-v6/.fork-gaps-last-scan"
[ -f "$F" ] || exit 0

python3 - "$F" "$STAMP" <<'PY' 2>/dev/null || true
import json, os, re, subprocess, sys, time

text = open(sys.argv[1], encoding="utf-8").read()
stamp = sys.argv[2]


# WRITTEN IS NOT LOGGED (2026-07-31). This surfacer reads the WORKING TREE, so an entry that
# was authored and never committed is announced every session as a live open gap — identical
# in the banner to one that is safely in git. That is a false green, and it is the one that
# hid the 2026-07-30/31 stall: three finished entries sat uncommitted for two days while being
# reported as logged. An uncommitted entry exists on ONE machine, is invisible to every other
# session, and dies to a single `git checkout`.
#
# So: diff the live ids against HEAD's and name the ones that were never committed. FAILS
# OPEN AND SILENT — if git cannot be read we say nothing about commit state rather than guess.
# Claiming "uncommitted" about a committed entry would be its own false alarm, and this hook's
# whole value is that it is quiet when there is nothing to say.
def committed_ids(register_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(register_path)))
    try:
        r = subprocess.run(["git", "show", "HEAD:docs/fork-gaps.md"],
                           cwd=root, capture_output=True, text=True, timeout=15)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return set(re.findall(r"(?m)^id: (FG-[\d-]+)", r.stdout))

entries = []  # [title, body_lines]
cur = None
started = False
for ln in text.splitlines():
    # LEVEL-2 ONLY (schema v1, 2026-07-25). An entry is a `## ` block; `### Incident` /
    # `### Work` / `### Doctrine` are its INTERNAL structure. Matching `###` too counted
    # every block as its own gap — 47 entries surfaced as 141 "open gaps" whose titles
    # read "Incident · Work ·". The `## Open` section marker is still level 2, so the
    # start detection below is unaffected.
    m = re.match(r"^## (.+)$", ln)
    if m:
        title = m.group(1).strip()
        if title == "Open":
            started = True
            cur = None
            continue
        if not started:
            continue
        cur = [title, []]
        entries.append(cur)
    elif cur is not None:
        cur[1].append(ln)

def is_open(title, body_lines):
    # STATE FIELD (schema v1, 2026-07-25). Closure now lives in the typed header's
    # `state:` — headings carry id + title only, so the old heading-tag scan would
    # report every entry as open forever. Only `closed` and `superseded` are done;
    # `partly` / `blocked` / `fork-fixed-distribution-owed` all name owed work and
    # stay surfaced. An entry with no readable state is treated as OPEN — an
    # unparseable entry must never disappear from the backlog.
    for ln in body_lines:
        m = re.match(r"^state:\s*(\S+)", ln.strip())
        if m:
            return m.group(1) not in ("closed", "superseded")
    # legacy fallback for any entry not yet migrated
    t = title.lower()
    return "[resolved" not in t and "[closed" not in t

def field(body_lines, name):
    for ln in body_lines:
        m = re.match(r"^%s:\s*(.+)$" % name, ln.strip())
        if m:
            return m.group(1).strip().strip('"')
    return None


def short(t):
    # drop any trailing `[…]` closure/status tag and clip for the list line
    t = re.split(r"\s*`?\[", t, 1)[0].strip()
    return t[:80]


# TWO STATUS AXES, SURFACED SEPARATELY (FG-2026-07-10-01 fix (a)).
# `## Open` used to be one undifferentiated list, but it holds two kinds of item with
# OPPOSITE handling: an open INVESTIGATION (what should we do?) and a DELIVERY
# OBLIGATION (the fork fix is written, pushed, and simply not distributed yet). Lumping
# them together is why four fully-engineered fixes once sat undelivered — the owed action
# had no owner and no count, so nobody revisited it. A distribution-owed entry does not
# need an investment decision; it needs a sync. Say so, separately, with the owed command.
owed, investigations = [], []
for t, b in entries:
    if not is_open(t, b):
        continue
    (owed if field(b, "state") == "fork-fixed-distribution-owed" else investigations).append((t, b))

parts = []

# Lead with it: an entry that is not committed is not logged, whatever the count says.
known = committed_ids(sys.argv[1])
if known is not None:
    uncommitted = []
    for t, b in entries:
        if not is_open(t, b):
            continue
        gid = field(b, "id")
        if gid and gid not in known:
            uncommitted.append(gid)
    if uncommitted:
        parts.append(
            "🚨 %d fork-gap entry/entries exist ONLY in this working tree — WRITTEN, NOT "
            "COMMITTED: %s. They are being counted as 'open gaps' below, but they are on this "
            "machine alone: invisible to every other session, absent from myfork/custom, and "
            "destroyed by one `git checkout`. This exact false green hid a two-day logging "
            "stall on 2026-07-30/31. Commit them by explicit path — `git add docs/fork-gaps.md` "
            "— NEVER `git add -A` (the register takes concurrent writes and you would scoop "
            "another session's in-flight entry). If a commit is rejected, read the finding: "
            "since 2026-07-31 only a defect in an entry YOU added or edited can block you."
            % (len(uncommitted), ", ".join(uncommitted))
        )

if investigations:
    listed = " · ".join(short(t) for t, _ in investigations)
    parts.append(
        "⚠ %d open fork-gap(s) in ~/bmad-method-v6/docs/fork-gaps.md "
        "(open-only file; resolved history in fork-gaps-archive.md). "
        "Open: %s. If the user asks what to work on, or you're doing fork maintenance, "
        "surface these. ROUTING (owner-ratified 2026-07-26, global-bmad-workflow.md "
        "§ Autonomous maintenance): a clear owner maintenance instruction — \"fix the "
        "fork gaps\", \"do the fork maintenance\" — IS routing for MAINTENANCE-lane work "
        "(execution defects, safety + coherence), so log AND fix in the same pass. A "
        "per-entry routing marker is still required for NEW DESIGN / DOCTRINE / POLICY "
        "changes (changing what a rule IS) — propose those, don't ship them."
        % (len(investigations), listed)
    )
if owed:
    rows = []
    for t, b in owed:
        gid = field(b, "id") or short(t)
        act = field(b, "distribution") or "distribution action NOT RECORDED — add a `distribution:` field"
        rows.append("%s → %s" % (gid, act[:120]))
    parts.append(
        "📦 %d fork-gap(s) are FORK-FIXED, DISTRIBUTION OWED — the code is written and "
        "pushed to myfork/custom, and it fires in ZERO projects until a sync runs. This is "
        "a DELIVERY obligation, not an open investigation: it needs the owed command, not an "
        "investment decision. %s. Distribution is a Tier-3 blast-radius action (cross-project "
        "rsync --delete over possibly-dirty trees) — surface it and get an explicit go; never "
        "fan out unasked." % (len(owed), " · ".join(rows))
    )

THIRTY_DAYS = 30 * 24 * 3600
try:
    age = time.time() - os.path.getmtime(stamp)
except OSError:
    age = None
if age is None or age > THIRTY_DAYS:
    last = "never" if age is None else "%dd ago" % (age // 86400)
    parts.append(
        "fork-gaps trend scan overdue (last: %s) — when the user starts a "
        "maintenance session, offer the 'fork-gaps trend scan' lane "
        "(3 questions over the last ~10 entries; see fork-gaps.md § Trend scan)." % last
    )

if parts:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": " | ".join(parts),
        }
    }))
PY
exit 0
