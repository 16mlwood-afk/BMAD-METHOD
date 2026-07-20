#!/usr/bin/env bash
# check-fork-gap-targets.sh — conservative, WARN-ONLY validator for docs/fork-gaps.md.
#
# Every open fork-gap entry names a `Target file:` — the load-bearing pointer an actioning
# session (often cold, days later) uses to find what to edit. That field is unvalidated free
# prose at log time, so a mistyped or rotted path silently taxes every actioning session with a
# re-discovery hop (see fork-gaps.md 2026-07-11 "Target file unvalidated" entry).
#
# This script greps each entry's backtick-quoted `Target file:` paths and WARNS on any that do
# not resolve in the fork tree. It NEVER blocks (always exits 0) — a rotted pointer is a hint to
# fix the doc, not a reason to fail a commit or a session start. Global-track paths (~/.claude,
# absolute ~, upstream marketplace notes) and template placeholders are skipped by design.
#
# Usage:  tools/check-fork-gap-targets.sh [path-to-fork-gaps.md]
# Wire into the ~monthly trend scan or check-fork-gaps.sh so rot is caught at surface time.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAPS="${1:-$ROOT/docs/fork-gaps.md}"

if [[ ! -f "$GAPS" ]]; then
  echo "check-fork-gap-targets: no fork-gaps file at $GAPS — nothing to check."
  exit 0
fi

heading=""
warn_count=0
checked=0

# Path resolution is SHARED with tools/check-fork-gap-stale-open.sh via the library below —
# one resolver so pointer-rot and stale-open detection stay consistent (a tightening applies
# to both at once). Do not re-implement is_checkable here.
# shellcheck source=lib/fork-gap-paths.sh
. "$ROOT/tools/lib/fork-gap-paths.sh"
is_checkable() { fg_is_checkable "$@"; }

while IFS= read -r line; do
  case "$line" in
    "## "*) heading="${line###\# }" ;;
  esac
  # only inspect lines that name a Target file
  case "$line" in
    *[Tt]"arget file"*) : ;;
    *) continue ;;
  esac
  # extract every backtick-quoted token on the line
  while IFS= read -r tok; do
    [[ -z "$tok" ]] && continue
    tok="${tok#\`}"; tok="${tok%\`}"
    is_checkable "$tok" || continue
    checked=$((checked+1))
    if [[ ! -e "$ROOT/$tok" ]]; then
      warn_count=$((warn_count+1))
      echo "  ⚠ unresolved Target file: \`$tok\`"
      echo "      in: ${heading:0:100}"
    fi
  done < <(grep -oE '`[^`]+`' <<<"$line")
done < "$GAPS"

if [[ "$warn_count" -eq 0 ]]; then
  echo "check-fork-gap-targets: OK — $checked fork-tree Target paths all resolve."
else
  echo "check-fork-gap-targets: $warn_count unresolved of $checked checked (WARN-only — the doc pointer rotted, not a build failure)."
fi
exit 0
