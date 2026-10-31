#!/bin/sh
# scripts/deploy-fingerprint.sh — one number that says WHICH SOURCE TREE this is.
#
# Run in the directory about to be uploaded, and again INSIDE the container after
# the deploy converged. Equal outputs mean the container is running the source
# this deploy uploaded. Unequal outputs mean the stamp is lying about the code.
#
# WHY THIS EXISTS (2026-09-04)
#
# `APP_COMMIT_SHA` is a service VARIABLE. The deploy script sets it, uploads, and
# then "reads it back off the container" — but a variable can only ever say what
# the script wrote, never what the container's filesystem holds. On 2026-09-04 a
# session ran `./scripts/deploy.sh` from a task worktree that had never itself
# been `railway link`ed; the Railway CLI resolves an unlinked directory to the
# nearest LINKED ancestor and uploads THAT directory, which was the shared main
# checkout, parked on a branch from before the day's merges. The stamp said
# d3aa7184, the converge check read d3aa7184 back, and production served a page
# that commit did not contain. Nothing in the lane could see it, by construction.
#
# This closes it: the fingerprint is computed from the FILES, on both sides.
#
# WHAT IS FINGERPRINTED
#
# Exactly the paths that can change what ships — the same list the deploy
# script's dirty-tree check protects. Build output, node_modules, docs and
# session state are excluded: they either do not ship or do not enter the build.
# Untracked files under these paths ARE included, deliberately: they upload too,
# so a fingerprint that ignored them would certify a tree that is not the one
# running.
#
# PORTABILITY
#
# POSIX sh, because it runs under `railway ssh -- sh scripts/deploy-fingerprint.sh`
# on the container (no bash guarantee, no git) and under macOS locally (no
# `sha256sum`). Sort order is pinned with LC_ALL=C so the two sides agree.

set -eu
LC_ALL=C
export LC_ALL

cd "${1:-.}"

if command -v sha256sum >/dev/null 2>&1; then
  SUM="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
  SUM="shasum -a 256"
else
  echo "no sha256 tool" >&2
  exit 2
fi

# The shipping surface. Add a path here only if a change to it would change the
# built app — and add it to deploy.sh's dirty-tree check in the same edit.
SHIP="src public package.json package-lock.json next.config.mjs tsconfig.json drizzle drizzle.config.ts middleware.ts"

present=""
for p in $SHIP; do
  [ -e "$p" ] && present="$present $p"
done

# shellcheck disable=SC2086
find $present -type f \
  ! -name '.DS_Store' \
  2>/dev/null | sort | while IFS= read -r f; do
    $SUM "$f"
  done | $SUM | cut -c1-64
