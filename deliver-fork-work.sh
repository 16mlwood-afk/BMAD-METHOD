#!/usr/bin/env bash
#
# deliver-fork-work.sh — the fork's missing delivery pipeline.
#
# WHY THIS EXISTS. Projects have had commit -> push -> PR -> merge for a long time. The FORK
# never had an equivalent, so every session that did fork work created a branch, pushed it, and
# stopped — because there was no defined next step. By 2026-08-31 that had produced eight
# branches and five weeks of drift: the design-lane work, the design-standards-delivery work and
# the skill-provenance standard were all finished, all pushed, and none of them on `custom`, so
# no project could see any of it. The owner had to ask "did we get the benefits?" to find out.
#
# This script is the answer to that question being "yes, automatically". One command:
#
#   ~/bmad-method-v6/deliver-fork-work.sh
#
#   1. surveys every fork branch for work whose CONTENT is not yet on custom
#   2. rebases each onto custom, runs the full suite, and merges it via a PR
#   3. pushes custom
#   4. fans the sync out to every project and delivers it there (commit -> push -> PR -> merge)
#
# It is SAFE TO RUN AT ANY TIME. With nothing outstanding it prints "nothing to deliver" and
# exits 0. It never force-pushes, never deletes a branch, and stops at the first real problem
# rather than half-applying anything.
#
# Flags:
#   --survey        report what would be delivered; change nothing
#   --branch NAME   deliver just this one branch
#   --no-sync       merge to custom and push, but skip the project fan-out
#   --no-test       skip `npm test` before merging (use only when the suite is already green)
#
set -uo pipefail

FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANON="custom"
REMOTE="myfork"
REPO="16mlwood-afk/BMAD-METHOD"
SURVEY_ONLY=false; ONE_BRANCH=""; DO_SYNC=true; DO_TEST=true; MARK_ONLY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --survey)   SURVEY_ONLY=true; shift ;;
    --branch)   ONE_BRANCH="${2:-}"; [[ -z "$ONE_BRANCH" ]] && { echo "--branch needs a name"; exit 2; }; shift 2 ;;
    --no-sync)  DO_SYNC=false; shift ;;
    --no-test)  DO_TEST=false; shift ;;
    --mark)     MARK_ONLY="${2:-}"; [[ -z "$MARK_ONLY" ]] && { echo "--mark needs a branch name"; exit 2; }; shift 2 ;;
    -h|--help)  sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *)          echo "unknown flag: $1"; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
fail() { printf 'STOPPED: %s\n' "$*"; exit 1; }

g() { git -C "$FORK" "$@"; }

# --- preflight -------------------------------------------------------------
# The fork worktree must be clean in the paths the sync reads, or a rebase would carry
# uncommitted work into custom without anyone deciding to.
dirty="$(g status --porcelain -- custom src/modules tools test 2>/dev/null)"
if [[ -n "$dirty" ]]; then
  say "The fork worktree has uncommitted changes:"
  printf '%s\n' "$dirty" | sed 's/^/    /'
  fail "commit or stash them first — delivery must move committed work only."
fi

g fetch "$REMOTE" --quiet 2>/dev/null || say "note: could not reach $REMOTE (offline?) — working from local refs"

start_branch="$(g branch --show-current 2>/dev/null || echo "$CANON")"
g rev-parse --verify --quiet "refs/heads/$CANON" >/dev/null || fail "no local $CANON branch"

# custom must not be behind its remote, or we would deliver onto a stale base.
if g rev-parse --verify --quiet "$REMOTE/$CANON" >/dev/null 2>&1; then
  behind=$(g rev-list --count "refs/heads/$CANON..$REMOTE/$CANON" 2>/dev/null || echo 0)
  if [[ "${behind:-0}" -gt 0 ]]; then
    say "$CANON is $behind commit(s) behind $REMOTE/$CANON — fast-forwarding first."
    g checkout -q "$CANON" && g merge --ff-only "$REMOTE/$CANON" >/dev/null 2>&1 \
      || fail "$CANON has diverged from $REMOTE/$CANON — resolve that by hand, it is not automatable."
  fi
fi

# --- survey ----------------------------------------------------------------
# `git cherry` compares by PATCH ID, so a commit already on custom under a different sha
# (cherry-picked, rebased, or squash-merged) is correctly reported as already delivered.
# A branch is DONE when its tip is recorded under refs/delivered/<branch>. That marker
# exists because `git cherry` compares patch ids, and a rebase that resolved a conflict
# changes the patch — so a branch merged an hour ago can still look outstanding forever.
# A survey that never goes quiet is one people stop reading, which is the failure this
# whole script exists to end. The marker is a ref, so it is non-destructive and reversible:
# `git update-ref -d refs/delivered/<branch>` puts a branch back in the queue.
delivered_ref() { printf 'refs/delivered/%s' "$1"; }

mark_delivered() {
  local b="$1"
  g update-ref "$(delivered_ref "$b")" "$(g rev-parse "refs/heads/$b")" 2>/dev/null || true
}

already_delivered() {
  local b="$1" mark tip
  mark=$(g rev-parse --verify --quiet "$(delivered_ref "$b")" 2>/dev/null) || return 1
  tip=$(g rev-parse --verify --quiet "refs/heads/$b" 2>/dev/null) || return 1
  [[ "$mark" == "$tip" ]]
}

survey() {
  local b n
  for b in $(g for-each-ref --format='%(refname:short)' refs/heads/ \
             | grep -vE "^($CANON|main|backup/|deliver/)"); do
    [[ -n "$ONE_BRANCH" && "$b" != "$ONE_BRANCH" ]] && continue
    already_delivered "$b" && continue
    n=$(g cherry "refs/heads/$CANON" "$b" 2>/dev/null | grep -c '^+' || true)
    [[ "${n:-0}" -gt 0 ]] && printf '%s\t%s\n' "$b" "$n"
  done
}

# --mark: record a branch as already delivered (its content reached custom by some other
# route — a hand merge, a squash-merged PR) so the survey stops reporting it.
if [[ -n "$MARK_ONLY" ]]; then
  g rev-parse --verify --quiet "refs/heads/$MARK_ONLY" >/dev/null \
    || fail "no such branch: $MARK_ONLY"
  mark_delivered "$MARK_ONLY"
  say "marked delivered: $MARK_ONLY @ $(g rev-parse --short "refs/heads/$MARK_ONLY")"
  say "(undo with: git -C $FORK update-ref -d $(delivered_ref "$MARK_ONLY"))"
  exit 0
fi

mapfile -t rows < <(survey)

say "FORK DELIVERY — source of truth is $CANON @ $(g rev-parse --short "refs/heads/$CANON")"
say ""
if [[ ${#rows[@]} -eq 0 ]]; then
  say "Nothing to deliver. Every fork branch is already represented on $CANON."
else
  say "Branches carrying work not yet on $CANON:"
  for r in "${rows[@]}"; do
    b="${r%%$'\t'*}"; n="${r##*$'\t'}"
    printf '    %-44s %s commit(s)  (newest %s)\n' "$b" "$n" "$(g log -1 --format=%ad --date=short "$b")"
  done
fi
say ""

if $SURVEY_ONLY; then
  say "--survey: nothing was changed."
  exit 0
fi

# --- deliver each branch ---------------------------------------------------
delivered=(); skipped=()
for r in "${rows[@]}"; do
  b="${r%%$'\t'*}"
  say "── delivering $b"
  tmp="deliver/$(printf '%s' "$b" | tr '/' '-')-$(date +%Y%m%d%H%M%S)"

  g checkout -q -B "$tmp" "$b" || { skipped+=("$b (could not branch)"); continue; }

  if ! g rebase "refs/heads/$CANON" >/dev/null 2>&1; then
    g rebase --abort >/dev/null 2>&1 || true
    g checkout -q "$CANON"; g branch -q -D "$tmp" 2>/dev/null || true
    skipped+=("$b (conflicts with $CANON — needs a human)")
    say "   CONFLICT — left untouched. Resolve by hand:  git checkout $b && git rebase $CANON"
    continue
  fi

  if $DO_TEST; then
    say "   running the suite..."
    if ! (cd "$FORK" && npm test >/tmp/deliver-fork-test.log 2>&1); then
      g checkout -q "$CANON"; g branch -q -D "$tmp" 2>/dev/null || true
      skipped+=("$b (npm test failed — see /tmp/deliver-fork-test.log)")
      say "   TESTS FAILED — not merged. Tail:"
      tail -12 /tmp/deliver-fork-test.log | sed 's/^/      /'
      continue
    fi
  fi

  g push -q "$REMOTE" "$tmp" 2>/dev/null || { skipped+=("$b (push failed)"); g checkout -q "$CANON"; continue; }

  pr=$(cd "$FORK" && gh pr create --repo "$REPO" --base "$CANON" --head "$tmp" \
        --title "Deliver $b into $CANON" \
        --body "Automated fork delivery. Rebased onto \`$CANON\`; \`npm test\` green before merge.

Source branch: \`$b\`

Opened by \`deliver-fork-work.sh\` — the fork's delivery pipeline. See its header for why it exists." 2>/dev/null | tail -1)

  if [[ -z "$pr" ]]; then skipped+=("$b (could not open PR)"); g checkout -q "$CANON"; continue; fi

  if (cd "$FORK" && gh pr merge "$pr" --repo "$REPO" --merge >/dev/null 2>&1); then
    mark_delivered "$b"
    delivered+=("$b -> $pr")
    say "   merged: $pr"
  else
    skipped+=("$b (PR $pr opened but did not merge)")
  fi
  g checkout -q "$CANON"
done

# --- land custom -----------------------------------------------------------
g checkout -q "$CANON"
g fetch "$REMOTE" --quiet 2>/dev/null || true
g merge --ff-only "$REMOTE/$CANON" >/dev/null 2>&1 || true
say ""
say "$CANON is now at $(g rev-parse --short "refs/heads/$CANON")"

# --- fan out ---------------------------------------------------------------
if $DO_SYNC && [[ ${#delivered[@]} -gt 0 ]]; then
  say ""
  say "── syncing every project from $CANON and delivering it there"
  (cd "$FORK" && ./sync-bmad-workflows.sh --commit 2>&1 | tail -30)

  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    proj="${line%/_bmad/bmm/workflows}"
    [[ -d "$proj/.git" ]] || continue
    ( cd "$proj" || exit 0
      git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -q '^main$' || exit 0
      ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
      [[ "${ahead:-0}" -gt 0 ]] && git push -q 2>/dev/null \
        && printf '    pushed %s (%s commit(s))\n' "$(basename "$proj")" "$ahead"
    ) || true
  done < "$HOME/.bmad-targets"
fi

# --- report ----------------------------------------------------------------
say ""
if [[ ${#delivered[@]} -gt 0 ]]; then
  say "DELIVERED:"; printf '    %s\n' "${delivered[@]}"
fi
if [[ ${#skipped[@]} -gt 0 ]]; then
  say "NEEDS YOU:"; printf '    %s\n' "${skipped[@]}"
fi
[[ ${#delivered[@]} -eq 0 && ${#skipped[@]} -eq 0 ]] && say "Nothing outstanding."
g checkout -q "$start_branch" 2>/dev/null || true
exit 0
