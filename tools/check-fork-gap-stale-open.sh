#!/usr/bin/env bash
# check-fork-gap-stale-open.sh — DETECTOR (never an auto-resolver) for fork-gap entries whose
# fix has already landed but whose entry is still open.
#
# WHY: three entries in one session (2026-07-20) were "fixed but never closed" — #503
# operator-domain-pass, the skills-layout dirty-guard gap, and #321/#333 earlier. A third of what
# looked like open backlog was already done. Pointer rot has a validator
# (check-fork-gap-targets.sh); stale-open had nothing. This is that.
#
# HOW: an entry may declare an optional `**Marker:**` one-liner — a backticked string that MUST
# exist in the entry's `Target file:` once the fix has landed (a function name, a guard call, a
# section heading, a config key). If the marker is found in a resolving target, the entry is a
# STALE-OPEN CANDIDATE for human close-out review.
#
# IT NEVER MUTATES THE REGISTER. It flags candidates and exits 0. Closing an entry stays a
# human judgement — a present marker proves the string exists, not that the gap is truly resolved.
#
# Usage:
#   tools/check-fork-gap-stale-open.sh            # open (untagged) entries only — the routine run
#   tools/check-fork-gap-stale-open.sh --all      # include already-tagged entries (audit / proof mode)
#   tools/check-fork-gap-stale-open.sh --help

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAPS="$ROOT/docs/fork-gaps.md"
INCLUDE_TAGGED=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) INCLUDE_TAGGED=true; shift ;;
    --help|-h) sed -n '2,22p' "$0"; exit 0 ;;
    *) GAPS="$1"; shift ;;
  esac
done

# Shared Target-path resolution — same brain as the pointer validator (gate 4).
# shellcheck source=lib/fork-gap-paths.sh
. "$ROOT/tools/lib/fork-gap-paths.sh"

[[ -f "$GAPS" ]] || { echo "check-fork-gap-stale-open: no fork-gaps file at $GAPS"; exit 0; }

candidates=0; checked=0; nomarker=0; unresolved=0

emit() {
  local heading="$1" target="$2" marker="$3" file="$4"
  local sha
  sha="$(git -C "$ROOT" log -1 --format=%h -- "$file" 2>/dev/null || true)"
  candidates=$((candidates + 1))
  echo "  ── STALE-OPEN CANDIDATE ──────────────────────────────────────────"
  echo "     gap:      ${heading:0:96}"
  echo "     target:   $target"
  echo "     marker:   $marker            found? Y"
  echo "     evidence: present in $file${sha:+  (last commit $sha)}"
  echo "     action:   review and close if correct"
  echo
}

heading=""; tagged=false; targets=(); markers=()

flush() {
  [[ -z "$heading" ]] && return 0
  if ! $INCLUDE_TAGGED && $tagged; then return 0; fi
  if [[ ${#markers[@]} -eq 0 ]]; then nomarker=$((nomarker + 1)); return 0; fi
  checked=$((checked + 1))
  local m t found=false
  for m in "${markers[@]}"; do
    for t in "${targets[@]}"; do
      local abs="$ROOT/$t"
      # The register itself must NEVER count as evidence: fork-gaps.md lives under docs/, so a
      # broad `docs/` target would otherwise self-match on the gap's own prose and report a
      # phantom that does not exist (observed 2026-07-20 on the pasted-image entry).
      if [[ -f "$abs" ]]; then
        case "$(basename "$abs")" in fork-gaps.md|fork-gaps-archive.md) continue ;; esac
        if grep -qF -- "$m" "$abs" 2>/dev/null; then emit "$heading" "$t" "$m" "$t"; found=true; break 2; fi
      elif [[ -d "$abs" ]]; then
        if grep -rqF --exclude='fork-gaps.md' --exclude='fork-gaps-archive.md' -- "$m" "$abs" 2>/dev/null; then
          emit "$heading" "$t" "$m" "$t"; found=true; break 2
        fi
      fi
    done
  done
  if ! $found; then
    if [[ ${#targets[@]} -eq 0 ]]; then unresolved=$((unresolved + 1)); fi
  fi
  return 0
}

while IFS= read -r line; do
  case "$line" in
    "## "*)
      flush
      heading="${line###\# }"; tagged=false; targets=(); markers=()
      fg_heading_is_tagged "$line" && tagged=true
      continue ;;
  esac
  [[ -z "$heading" ]] && continue
  case "$line" in
    *[Tt]"arget file"*)
      while IFS= read -r tok; do
        fg_is_checkable "$tok" && targets+=("$tok")
      done < <(fg_backticked_tokens "$line") ;;
    *"Marker:"*)
      while IFS= read -r tok; do
        # Reject a BLANK or trivially-short marker rather than accepting it.
        # A whitespace-only token passes `[[ -n ]]` and then grep -F matches EVERY file,
        # so the entry reports a stale-open candidate on no evidence at all — the
        # register-matches-itself failure this tool is explicitly built not to commit.
        # Seen in the wild from the double-backtick form ``` **Marker:** `` `x` `` ```,
        # whose outer pair tokenizes to a single space. (fork-gaps 2026-07-25)
        trimmed="${tok#"${tok%%[![:space:]]*}"}"
        trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
        [[ ${#trimmed} -ge 3 ]] && markers+=("$trimmed")
      done < <(fg_backticked_tokens "$line") ;;
  esac
done < "$GAPS"
flush

echo "check-fork-gap-stale-open: $candidates stale-open candidate(s) from $checked entry with a declared Marker."
echo "  $nomarker entry/entries declared no Marker (not checkable — add a **Marker:** line to include them)."
echo "  DETECTOR ONLY — the register was not modified. Closing an entry remains a human call."
if [[ "$candidates" -gt 0 ]]; then
  echo
  echo "  ⚠ RULE — NEVER close a gap on a grep hit alone. A marker proves a STRING exists, not"
  echo "    that the gap is resolved. Open the implementing section, read it, and confirm it"
  echo "    matches the entry's stated fix direction before tagging anything RESOLVED."
fi
exit 0
