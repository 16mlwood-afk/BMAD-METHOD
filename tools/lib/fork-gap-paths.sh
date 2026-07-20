#!/usr/bin/env bash
# fork-gap-paths.sh — shared Target-file path resolution for the fork-gap tooling.
#
# SINGLE SOURCE OF TRUTH for "is this backticked token a checkable fork-tree path?".
# Sourced by BOTH:
#   - tools/check-fork-gap-targets.sh     (pointer rot: path named but does not resolve)
#   - tools/check-fork-gap-stale-open.sh  (stale-open: path resolves AND already contains the fix marker)
# Keeping one resolver means rot is caught consistently by both, and a tightening
# applies everywhere at once (fork-gap 2026-07-11 Target-file convention).

# A token is checkable only if it points UNAMBIGUOUSLY inside this repo's
# source-of-record tree and carries no placeholder/glob. Deliberately conservative —
# near-zero false positives is the design goal. Skipped by intent: absolute/home
# globals; template placeholders/{vars}/globs; `src/` (marketplace channel, not the
# edit surface); project-side paths (`scripts/`, `.githooks/`); and bare filenames
# (`CLAUDE.md`, `STANDARDS.md`) which are contextual/relative, not fork-root files.
fg_is_checkable() {
  local t="$1"
  case "$t" in
    *"…"*|*"<"*|*">"*|*"*"*|*"{"*|*"}"*|*"~"*|*" "*) return 1 ;;
    /*) return 1 ;;
  esac
  case "$t" in
    custom/*|docs/*|tools/*) return 0 ;;
  esac
  # Fork-ROOT scripts are unambiguous fork-tree files, unlike contextual bare filenames
  # (CLAUDE.md / STANDARDS.md / deliver.md), so they are allowlisted by shape: a bare `*.sh`
  # with no slash. A named-but-absent root script is then correctly reported as rot.
  case "$t" in
    */*) return 1 ;;
    *.sh) return 0 ;;
  esac
  return 1
}

# Echo every backtick-quoted token on a line, one per line, backticks stripped.
fg_backticked_tokens() {
  local line="$1" tok
  while IFS= read -r tok; do
    [[ -z "$tok" ]] && continue
    tok="${tok#\`}"; tok="${tok%\`}"
    printf '%s\n' "$tok"
  done < <(grep -oE '`[^`]+`' <<<"$line" 2>/dev/null || true)
}

# Is a gap heading already closed out? (surfacer keys on the same tags)
fg_heading_is_tagged() {
  case "$1" in
    *"[RESOLVED"*|*"[resolved"*|*"[CLOSED"*|*"[closed"*|*"[partly resolved"*|*"[partial"*) return 0 ;;
  esac
  return 1
}
