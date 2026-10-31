#!/usr/bin/env sh
# .githooks/check-runbook-frontmatter.sh — FORK-owned gate (STD-HOOKACTIVATE-001).
#
# Validates the RUNBOOK METADATA CONTRACT on operator runbooks / agent briefs:
# YAML frontmatter carrying status / executor / owner / last_reviewed / version,
# so cold-delegation decisions ("only status: verified + executor: chrome-mcp
# briefs are delegated to a cold agent without review") can be made from metadata
# instead of re-reading the whole procedure. Origin: comms_dashboard
# docs/cases/tfp-fba-outbound (contract documented in that case's CLAUDE.md).
#
# OPT-IN per project (payload-roundtrip precedent): this script is distributed to
# the whole fleet via gates.d/runbook-frontmatter.conf, but it is a SILENT NO-OP
# unless the repo declares its runbook locations in:
#     .githooks/runbook-paths.conf   — one shell-case glob per line
# Absent/empty marker → exit 0, nothing checked. A repo opts in by creating that
# file with its own paths (comms: docs/cases/*/runbook*.md ; a flat repo:
# docs/runbooks/*.md). Opting in is DELIBERATE because runbook layout AND
# frontmatter schema differ across repos — a repo whose runbooks use a different
# header schema (e.g. name/description) must reconcile that FIRST; see the
# runbook metadata contract before creating the marker. Fails CLOSED: any doubt
# about opt-in → no-op, never enforce on a repo that didn't ask.
#
# Two severities (conservative detector):
#   BLOCK — a matched file that HAS frontmatter but violates the contract shape
#           (missing required field, invalid status/executor enum, malformed
#           last_reviewed date or version). Unambiguous.
#   WARN  — a NEWLY ADDED matched file with no frontmatter at all (staged mode
#           only). Pre-existing frontmatter-less files are silently skipped.
#
# Modes: default = staged files (pre-commit); --all = every tracked match (CI).
# Override (logged by the dispatcher): git commit --no-verify
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

MARKER=".githooks/runbook-paths.conf"
[ -f "$MARKER" ] || exit 0   # not opted in → no-op

REQUIRED_FIELDS="title id status executor owner last_reviewed version"
STATUS_ENUM="draft verified deprecated"
EXECUTOR_ENUM="chrome-mcp human mixed"

# matches <path> → 0 if it matches any opt-in glob in the marker file.
# Re-reads the tiny marker per candidate (candidates are few; file is cached).
matches() {
  _p="$1"
  while IFS= read -r _g || [ -n "$_g" ]; do
    case "$_g" in '' | \#*) continue ;; esac
    _g=$(printf '%s' "$_g" | sed 's/[[:space:]]*$//')   # strip trailing ws
    # shellcheck disable=SC2254
    case "$_p" in $_g) return 0 ;; esac
  done < "$MARKER"
  return 1
}

# Any non-comment, non-blank pattern present? Empty marker → no-op.
if ! grep -qvE '^[[:space:]]*(#.*)?$' "$MARKER"; then
  exit 0
fi

if [ "${1:-}" = "--all" ]; then
  candidates=$(git ls-files 2>/dev/null || true)
  mode=all
else
  candidates=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
  mode=staged
fi
[ -n "$candidates" ] || exit 0

# field <file> <key> → value from the frontmatter block only, comment/ws stripped
field() {
  awk -v k="$2" '
    NR==1 { next }                # opening ---
    /^---[ \t]*$/ { exit }        # closing --- ends the block
    index($0, k":") == 1 {
      sub("^" k ":[ \t]*", ""); sub("[ \t]*#.*$", ""); sub("[ \t]*$", "")
      print; exit
    }' "$1"
}

in_enum() { v="$1"; shift; for e in "$@"; do [ "$v" = "$e" ] && return 0; done; return 1; }

status=0
# Redirect (not a pipe) so the loop runs in THIS shell and `status` persists.
_tmp=$(mktemp)
printf '%s\n' "$candidates" > "$_tmp"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  matches "$f" || continue
  [ -f "$f" ] || continue

  if [ "$(head -n 1 "$f")" != "---" ]; then
    if [ "$mode" = "staged" ] && git diff --cached --name-only --diff-filter=A | grep -qx "$f"; then
      printf 'WARN  %s: new runbook/brief without metadata frontmatter — see the runbook metadata contract\n' "$f" >&2
    fi
    continue
  fi

  for k in $REQUIRED_FIELDS; do
    v="$(field "$f" "$k")"
    if [ -z "$v" ]; then
      printf 'BLOCK %s: missing required frontmatter field "%s"\n' "$f" "$k" >&2
      status=1; continue
    fi
    case "$k" in
      status)   in_enum "$v" $STATUS_ENUM   || { printf 'BLOCK %s: status "%s" not in {%s}\n' "$f" "$v" "$STATUS_ENUM" >&2; status=1; } ;;
      executor) in_enum "$v" $EXECUTOR_ENUM || { printf 'BLOCK %s: executor "%s" not in {%s}\n' "$f" "$v" "$EXECUTOR_ENUM" >&2; status=1; } ;;
      last_reviewed) printf '%s' "$v" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || { printf 'BLOCK %s: last_reviewed "%s" is not YYYY-MM-DD\n' "$f" "$v" >&2; status=1; } ;;
      version)       printf '%s' "$v" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'     || { printf 'BLOCK %s: version "%s" is not semver (X.Y.Z)\n' "$f" "$v" >&2; status=1; } ;;
    esac
  done
done < "$_tmp"
rm -f "$_tmp"

exit "$status"
