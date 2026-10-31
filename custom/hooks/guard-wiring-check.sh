#!/usr/bin/env bash
# guard-wiring-check.sh — the CHEAP half of guard-health-check.sh.
#
# Answers exactly one question: **is the reviewed edit-guard the thing that runs?**
#   1. settings.local.json invokes bash_edit_guard.py
#   2. the superseded legacy inline regex blob is absent
#
# WIRED HERE on SessionStart via the tracked .claude/settings.json (2026-09-03).
# Imported from cash-recovery, where it is also wired on SessionStart. The upstream
# copy's docstring still claims "NOT WIRED ANYWHERE YET" — that claim is stale.
#
# WHY SPLIT IT OUT
# ----------------
# The full `guard-health-check.sh` also fires LIVE PROBES through the guard, one of
# which exercises `BMAD_ALLOW_MAIN_EDIT=1` and therefore appends a row to
# `~/.claude/logs/bash-edit-guard-override.jsonl`. Running that on every session start
# would (a) cost a python round-trip per probe and (b) steadily poison the override
# audit log with synthetic entries — the log whose whole value is that a human can scan
# it for real misuse. A check that corrupts the evidence it exists to protect is not a
# check you want on a hot path.
#
# These two assertions are the ones that actually caught the regression: on 2026-07-28
# `bash_edit_guard.py` was found invoked by NO Bash matcher while the 2050-char legacy
# blob adjudicated every command — a recurrence of the 2026-07-26 finding. Both halves
# are pure file reads. No subprocess, no probe, no log write, no network.
#
# The behavioural probes (ALLOW / DENY / override-logging) stay in guard-health-check.sh
# and stay manual: they answer "is it PRECISE", which is a question for after a guard
# edit or a fan-out, not for every session start.
#
# Exit 0 = wired correctly. Exit 1 = findings (safe to gate on).
set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
# A worktree has no settings of its own — the guard and its wiring live in the main
# checkout, so resolve there rather than reporting a false "not wired".
case "$PROJECT" in */.claude/worktrees/*) PROJECT="${PROJECT%%/.claude/worktrees/*}";; esac

GUARD="$PROJECT/.claude/hooks/bash_edit_guard.py"
# BOTH settings files are legitimate homes for a registration. The tracked
# settings.json is what survives a clone; settings.local.json is machine-local.
# Reading only one reports a false "not wired" on a project that used the other --
# which is exactly what this project does (the guard is wired in settings.json).
SETTINGS_LOCAL="$PROJECT/.claude/settings.local.json"
SETTINGS_TRACKED="$PROJECT/.claude/settings.json"
LEGACY_TELL="edit-equivalent (sed -i / cat >"
fail=0

bad() { printf '  ✗ %s\n' "$1"; fail=1; }

if [ ! -f "$GUARD" ]; then
  bad "reviewed guard missing at .claude/hooks/bash_edit_guard.py"
elif [ ! -f "$SETTINGS_LOCAL" ] && [ ! -f "$SETTINGS_TRACKED" ]; then
  bad "no settings.json or settings.local.json — cannot confirm the guard is wired at all"
else
  grep -qs "bash_edit_guard" "$SETTINGS_LOCAL" "$SETTINGS_TRACKED" || bad \
    "NEITHER settings file invokes bash_edit_guard.py — the legacy inline regex is probably live (the 2026-07-26 finding: green suite, zero wiring)"
  # The blob ships FROM the fork template (assets/hooks.json) into settings.local.json
  # on every sync, so this stays a finding until the fork template is corrected --
  # removing it locally is undone by the next distribution.
  grep -qs "$LEGACY_TELL" "$SETTINGS_LOCAL" && bad \
    "the superseded LEGACY regex blob is still present in settings.local.json (source: fork assets/hooks.json)"
fi

# --- registration inventory: is a MERGED guard also WIRED? --------------------------
# The two checks above ask whether the RIGHT edit-guard runs. This asks the reverse
# question, for the small set of guards that have actually been merged-and-inert here.
# hook-resolve-check.py reports wired-but-missing and is structurally blind to
# merged-but-unwired: it stayed silent on operator-path-guard.py from 2026-08-27, because
# that guard's wiring was itself the thing that was missing. One name per line. BOTH
# settings files count -- the tracked settings.json and the machine-local
# settings.local.json are each a legitimate home for a registration, and a check that
# reads only one reports a false "not wired" on a project that used the other.
# NO control-plane fallback here, deliberately. cash-recovery resolves hooks through
# a pinned clone at ~/.claude/control-plane/cash-recovery; inheriting that path would
# make THIS project execute cash-recovery's copy of a guard. All wiring here uses
# direct project paths. Inventory = the guards merged into this project.
# Inventory is PROJECT-DATA, not a fork constant. This file is distributed to every
# project; a hardcoded list would impose one project's merged guards on all of them and,
# worse, silently DROP a check a project already relied on (cash-recovery watches
# operator-path-guard.py, merged-but-unwired on 2026-08-27). Projects declare their own
# in .claude/guard-inventory.txt, one basename per line, '#' for comments. With no such
# file the default preserves the pre-distribution behaviour exactly -- and the [ -f ]
# test below means a name a project does not have is simply skipped.
_inv_file="$PROJECT/.claude/guard-inventory.txt"
if [ -f "$_inv_file" ]; then
  _inventory=$(grep -vE '^[[:space:]]*(#|$)' "$_inv_file" 2>/dev/null)
else
  _inventory="operator-path-guard.py"
fi
for _h in $_inventory; do
  if [ -f "$PROJECT/.claude/hooks/$_h" ]; then
    grep -qs -- "$_h" "$SETTINGS_LOCAL" "$SETTINGS_TRACKED" || bad \
      "$_h is merged but registered in NEITHER settings file -- it fires nowhere"
  fi
done

if [ "$fail" -ne 0 ]; then
  printf '  → run: bash .claude/hooks/guard-health-check.sh   (full diagnosis)\n'
fi
# Silent when healthy: a session-start check that speaks on every boot gets ignored,
# and an ignored check is indistinguishable from an absent one.
exit "$fail"
