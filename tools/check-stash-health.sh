#!/usr/bin/env bash
# check-stash-health.sh — pre-commit PREFLIGHT: refuse to start a commit when an existing stash
# is corrupt, BEFORE lint-staged tries to stash the working state.
#
# WHY (fork-gap 2026-07-20): lint-staged backs up the working state with a stash on every commit.
# If ANY existing stash references an object that is missing from the object store, that backup
# fails and git reports:
#
#     fatal: unable to read <sha>
#     error: invalid object 100644 <sha> for '<some/unrelated/path>'
#     error: Error building trees
#
# Every obvious reading of that message is wrong. The named path is typically not in HEAD and not
# in the index; `git fsck --connectivity-only` comes back CLEAN (unreachable stash objects are not
# "missing reachable objects"); `git write-tree` succeeds. So it reads as repo corruption and
# invites destructive "repair" of a perfectly healthy repo — and the only escape that works is
# `--no-verify`, i.e. bypassing the very gates that matter. In a fork shared by ~25 concurrent
# sessions, one stale stash is a repo-wide commit outage.
#
# This turns a six-hop diagnosis into one line with the exact remedy.
#
# POSTURE: conservative. Fails CLOSED only on a PROVEN-missing object. Any inability to determine
# health (no git, not a repo, unexpected output) fails OPEN — a diagnostic aid must never become a
# new way to block commits.

set -uo pipefail

command -v git >/dev/null 2>&1 || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# Fast path: no stashes at all (the overwhelmingly common case) — zero cost.
git rev-parse --verify --quiet refs/stash >/dev/null 2>&1 || exit 0
stash_count="$(git stash list 2>/dev/null | wc -l | tr -d ' ')"
[ "${stash_count:-0}" -eq 0 ] && exit 0

bad=0
i=0
while [ "$i" -lt "$stash_count" ]; do
  ref="stash@{$i}"
  # Enumerate the objects belonging to THIS stash only (--no-walk: do not traverse history),
  # across its commit and its index/untracked parents, then header-check each for existence.
  # --batch-check reads object headers only, so this stays cheap.
  refs="$ref"
  for p in 2 3; do
    if git rev-parse --verify --quiet "${ref}^${p}" >/dev/null 2>&1; then
      refs="$refs ${ref}^${p}"
    fi
  done

  # Detection: `git rev-list --objects` ABORTS on the first unreadable object
  # ("fatal: missing blob object '<sha>'") and never emits it, so enumerating-then-checking finds
  # nothing. The abort itself IS the signal. Capture stderr only, and fail closed ONLY when git
  # explicitly reports a missing object — any other failure fails open (see POSTURE above).
  # shellcheck disable=SC2086
  err="$(git rev-list --objects --no-walk $refs 2>&1 >/dev/null)"
  rc=$?
  missing=0
  if [ "$rc" -ne 0 ] && printf '%s' "$err" | grep -qiE "missing (blob|tree|commit|object)"; then
    missing="$(printf '%s\n' "$err" | grep -ciE "missing (blob|tree|commit|object)" || true)"
  fi

  if [ "${missing:-0}" -gt 0 ]; then
    if [ "$bad" -eq 0 ]; then
      echo ""
      echo "  ✗ STASH PREFLIGHT — commit refused before lint-staged could fail confusingly."
      echo ""
    fi
    bad=$((bad + 1))
    desc="$(git log -1 --format='%h  %an  %ar  %s' "$ref" 2>/dev/null || echo "$ref")"
    echo "     $ref is CORRUPT — $missing object(s) missing from the store."
    echo "       $desc"
    echo "       It is UNRESTORABLE: the missing objects are gone, so nothing can be recovered from it."
    echo "       Remedy:  git stash drop $ref"
    echo ""
  fi
  i=$((i + 1))
done

if [ "$bad" -gt 0 ]; then
  echo "     WHY THIS BLOCKS: lint-staged stashes your working state before every commit. A corrupt"
  echo "     stash makes that backup fail as 'invalid object … Error building trees', naming a path"
  echo "     unrelated to your commit. HEAD, the index and git fsck all look CLEAN, so the message"
  echo "     misleads toward destructive repair of a healthy repo. Drop the stash above and commit"
  echo "     normally — do NOT reach for --no-verify, which skips every gate."
  echo ""
  exit 1
fi

exit 0
