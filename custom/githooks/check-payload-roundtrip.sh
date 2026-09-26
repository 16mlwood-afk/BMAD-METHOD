#!/usr/bin/env sh
# .githooks/check-payload-roundtrip.sh — STD-HOOKACTIVATE-001
#
# Tier C of the cross-service round-trip contract (fork-gaps "Cross-service
# payload fixes have NO mandatory end-to-end round-trip gate"): the DETERMINISTIC
# INVOCATION TRIGGER at the sender's push moment. Tiers A+B already exist and are
# probabilistic-for-invocation: webhook-contract-check step-05 computes the
# `verified` disposition from an observed round-trip (live or synthetic-replay),
# and deployment-to-prod §1B says a cross-service payload change is not "done"
# at deploy-on-both-sides. This hook exists ONLY so those tiers get invoked:
# it fires when a push touches the repo's DECLARED payload-builder paths and
# prints one reminder. Deterministic delivery, probabilistic action — per
# enforcement-expert the correct ceiling here (harm is recoverable: a mis-shipped
# payload can be re-webhooked once caught).
#
# WARN ONLY, permanently by design (not a warn-then-gate phase): a round-trip
# cannot be machine-verified at push time (it needs a live source page or the
# receiver's DB — see the fork-gaps entry), so a hard gate here would fake a
# check. This never blocks and ALWAYS exits 0.
#
# OPT-IN, conservative detector: fires only in repos that declare their sender
# payload-builder paths in the PROJECT-owned file:
#
#   .githooks/payload-builder-paths.conf
#     # shell-case glob per line; * crosses slashes (POSIX case semantics)
#     src/utils/webhook*
#     src/background/*payload*
#
# No conf file -> silent no-op fleet-wide (zero false positives on the 12 repos
# that aren't webhook senders). Deliberately stdin-independent (the dispatcher
# may run several pre-push gates; stdin is a shared, drainable resource): the
# outgoing range is computed as merge-base(HEAD, upstream-or-origin/main)..HEAD.
#
# Registered in .githooks/gates.d/payload-roundtrip.conf (fork-owned drop-in).
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CONF="$ROOT/.githooks/payload-builder-paths.conf"
[ -f "$CONF" ] || exit 0

# Outgoing changes: what this push would land that the base doesn't have.
upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
base=""
if [ -n "$upstream" ]; then
  base="$(git merge-base HEAD "$upstream" 2>/dev/null || true)"
fi
if [ -z "$base" ]; then
  base="$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null || true)"
fi
[ -n "$base" ] || exit 0
changed="$(git diff --name-only "$base" HEAD 2>/dev/null || true)"
[ -n "$changed" ] || exit 0

hits=""
while IFS= read -r pat || [ -n "$pat" ]; do
  case "$pat" in '' | \#*) continue ;; esac
  # trim trailing whitespace/comments after the glob
  pat="$(printf '%s' "$pat" | sed 's/[[:space:]]*#.*$//; s/[[:space:]]*$//')"
  [ -n "$pat" ] || continue
  while IFS= read -r f || [ -n "$f" ]; do
    [ -n "$f" ] || continue
    # shellcheck disable=SC2254 — unquoted $pat is the point: glob match
    case "$f" in
      $pat) hits="$hits  $f
" ;;
    esac
  done <<EOF
$changed
EOF
done <"$CONF"

if [ -n "$hits" ]; then
  {
    echo "payload-roundtrip [WARN]: this push touches declared webhook payload-builder path(s):"
    printf '%s' "$hits" | sort -u
    echo "  A cross-service payload change is not 'done' at deploy-on-both-sides — it is done after ONE"
    echo "  observed round-trip (live or synthetic-replay) lands the expected value on the receiver."
    echo "  Run webhook-contract-check: its step-05 computes the 'verified' disposition from evidence"
    echo "  (deployment-to-prod contract §1B). Warn-only: this hook never blocks."
  } >&2
fi
exit 0
