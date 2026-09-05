#!/usr/bin/env bash
# audit-brief-gate-reachability.sh — SR-35 / FG-2026-07-25-10.
#
# THE QUESTION: in each synced project, can the design-brief gate actually SEE a brief?
#
# `check-design-brief-completeness.sh` only ever inspects files that are STAGED. The
# fork-standard `.gitignore` shape is `/_bmad-output/*`, which means a BRAND-NEW brief —
# exactly what a fresh design-handoff emits — cannot be staged without `git add -f` and
# therefore never reaches the gate at all. Existing briefs were often force-added once, so
# EDITS still reach it. Coverage is inverted: the low-risk path covered, the high-risk path
# missed, while the gate reports as armed.
#
# This audit answers, per project, three separate questions that are easy to conflate:
#   1. is the gate DELIVERED?      (.githooks/check-design-brief-completeness.sh present)
#   2. is the gate ACTIVATED?      (core.hooksPath = .githooks)
#   3. is its INPUT REACHABLE?     (can a NEW design-brief-*.md be staged without -f)
# A project can pass 1 and 2 and fail 3, which is the inert-gate case and the whole point.
#
# READ-ONLY. Creates no commits, stages nothing, and cleans up its probe file. The probe
# uses `git check-ignore`, which does not touch the index.
#
# Usage:  bash tools/audit-brief-gate-reachability.sh [--projects-file <file>]
# Exit 0 always — this is a report, not a gate.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORK_ROOT="$(dirname "$SCRIPT_DIR")"

# Reuse the sync tool's own target list so this audit and the sync never disagree about
# which projects exist. Falls back to a directory scan if the list cannot be read.
targets=()
if [ -f "$FORK_ROOT/sync-targets.txt" ]; then
  while IFS= read -r line; do
    line="${line%%#*}"; line="$(echo "$line" | xargs)"
    [ -n "$line" ] && targets+=("$line")
  done < "$FORK_ROOT/sync-targets.txt"
else
  for d in "$HOME"/code/*/ ; do
    [ -d "$d/.git" ] && targets+=("${d%/}")
  done
fi

printf '\n%-26s %-9s %-9s %-11s %s\n' "PROJECT" "GATE" "ACTIVE" "NEW-BRIEF" "VERDICT"
printf '%s\n' "-------------------------------------------------------------------------------"

inert=0; ok=0; nogate=0

for proj in "${targets[@]}"; do
  name="$(basename "$proj")"
  [ -d "$proj/.git" ] || continue

  gate="absent"
  [ -f "$proj/.githooks/check-design-brief-completeness.sh" ] && gate="present"

  # `core.hooksPath` is legally EITHER relative (`.githooks`) or absolute
  # (`/Users/x/code/proj/.githooks`) — both activate the same directory. Comparing against
  # the relative form alone reported cash-recovery as INACTIVE while its gate was demonstrably
  # firing on every commit. An audit that under-reports activation sends someone to "fix" a
  # working project, which is how audits lose their audience. Resolve, then compare.
  active="no"
  hp="$(git -C "$proj" config core.hooksPath 2>/dev/null || true)"
  if [ -n "$hp" ]; then
    case "$hp" in
      /*) resolved="$hp" ;;
      *)  resolved="$proj/$hp" ;;
    esac
    # Normalise a trailing slash and compare against this project's own .githooks.
    [ "${resolved%/}" = "$proj/.githooks" ] && active="yes"
  fi

  # Can a NEW brief be staged without -f? Ask git's own ignore engine about a path that
  # does not exist yet — the exact path a fresh design-handoff would write.
  probe="_bmad-output/implementation-artifacts/design-brief-gate-probe.md"
  if git -C "$proj" check-ignore -q "$probe" 2>/dev/null; then
    newbrief="IGNORED"
  else
    newbrief="stageable"
  fi

  if [ "$gate" = "absent" ]; then
    verdict="no gate delivered — sync owed (or project has no design lane)"
    nogate=$((nogate + 1))
  elif [ "$newbrief" = "IGNORED" ]; then
    verdict="** INERT — gate delivered but cannot see a NEW brief **"
    inert=$((inert + 1))
  elif [ "$active" = "no" ]; then
    verdict="delivered + reachable, but hooksPath not set — gate never runs"
  else
    verdict="OK — delivered, active, input reachable"
    ok=$((ok + 1))
  fi

  printf '%-26s %-9s %-9s %-11s %s\n' "$name" "$gate" "$active" "$newbrief" "$verdict"
done

printf '\n  %d OK · %d INERT (gate present, input unreachable) · %d without the gate\n' \
  "$ok" "$inert" "$nogate"
printf '  Fix for an INERT project — in its .gitignore, after the existing /_bmad-output/* line:\n'
printf '      !/_bmad-output/implementation-artifacts/\n'
printf '      /_bmad-output/implementation-artifacts/*\n'
printf '      !/_bmad-output/implementation-artifacts/design-brief-*.md\n'
printf '  Verify after: a new brief stages WITHOUT -f; an untracked non-brief artifact stays ignored.\n'
printf '  Reference: SR-35 (cash-recovery scope register) · FG-2026-07-25-10.\n\n'
