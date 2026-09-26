#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM_BRANCH="origin/main"
FORK_REMOTE="myfork"
LOCAL_BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD)"

# Quiet fetch — just update refs
git -C "$SCRIPT_DIR" fetch origin --quiet 2>/dev/null || {
  echo "BMAD drift check: could not reach upstream (offline?)"
  exit 0
}

BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count "HEAD..$UPSTREAM_BRANCH" 2>/dev/null || echo 0)

# Check if fork remote is up to date
FORK_BEHIND=0
if git -C "$SCRIPT_DIR" rev-parse "$FORK_REMOTE/$LOCAL_BRANCH" &>/dev/null; then
  FORK_BEHIND=$(git -C "$SCRIPT_DIR" rev-list --count "$FORK_REMOTE/$LOCAL_BRANCH..HEAD" 2>/dev/null || echo 0)
fi

# UNDELIVERED FORK WORK (added 2026-08-31).
# The two checks above ask "is the fork behind upstream?" and "is THIS branch pushed?".
# Neither asks the question that actually cost five weeks: is there finished fork work
# sitting on a branch that never reached `custom`? On 2026-08-31 three branches held
# completed, pushed work — the design-standards delivery, the three-gate route and the
# skill-provenance standard — and no project could see any of it, because nothing ever
# looked. Compare by PATCH ID so a branch already squash-merged or cherry-picked is not
# reported, and skip anything recorded under refs/delivered/ by deliver-fork-work.sh.
UNDELIVERED=""
UNDELIVERED_N=0
while read -r b; do
  [[ -z "$b" ]] && continue
  mark=$(git -C "$SCRIPT_DIR" rev-parse --verify --quiet "refs/delivered/$b" 2>/dev/null || true)
  tip=$(git -C "$SCRIPT_DIR" rev-parse --verify --quiet "refs/heads/$b" 2>/dev/null || true)
  [[ -n "$mark" && "$mark" == "$tip" ]] && continue
  n=$(git -C "$SCRIPT_DIR" cherry refs/heads/custom "$b" 2>/dev/null | grep -c '^+' || true)
  if [[ "${n:-0}" -gt 0 ]]; then
    UNDELIVERED_N=$((UNDELIVERED_N + 1))
    UNDELIVERED="${UNDELIVERED}  $b ($n commit(s), newest $(git -C "$SCRIPT_DIR" log -1 --format=%ad --date=short "$b" 2>/dev/null))
"
  fi
done < <(git -C "$SCRIPT_DIR" for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null          | grep -vE '^(custom|main|backup/|deliver/)' || true)

if [[ "$BEHIND" -eq 0 && "$FORK_BEHIND" -eq 0 && "$UNDELIVERED_N" -eq 0 ]]; then
  exit 0
fi

echo "──────────────────────────────────────────"
echo "⚠ BMAD fork drift detected (~/bmad-method-v6)"
if [[ "$BEHIND" -gt 0 ]]; then
  echo "  $BEHIND commit(s) behind upstream main"
fi
if [[ "$FORK_BEHIND" -gt 0 ]]; then
  echo "  $FORK_BEHIND unpushed commit(s) to GitHub fork"
fi
if [[ "$UNDELIVERED_N" -gt 0 ]]; then
  echo "  $UNDELIVERED_N branch(es) hold fork work that is NOT on custom, so NO project can see it:"
  printf '%s' "$UNDELIVERED"
  echo "  Deliver it all:  ~/bmad-method-v6/deliver-fork-work.sh"
fi
if [[ "$BEHIND" -gt 0 || "$FORK_BEHIND" -gt 0 ]]; then
  echo "  Run: ~/bmad-method-v6/upgrade-bmad.sh"
fi
echo "──────────────────────────────────────────"
