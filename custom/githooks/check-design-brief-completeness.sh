#!/usr/bin/env sh
# .githooks/check-design-brief-completeness.sh — STD-HOOKACTIVATE-001
#
# Warn-first (Phase 1) PRODUCER-side gate for design-handoff briefs — the
# deterministic tier-6 companion to the in-flow assertion in design-handoff
# step-04 §3. When a design-brief-*.md is staged, it verifies the Block B
# `frames:` contract (what design-implement step-01 §SHARED.1b diffs the bundle
# against) is present, non-empty, unique, and mirrored in the §7 body — at commit
# time, outside the agent, independent of whether the design-handoff workflow ran.
#
# PHASE 1 = WARN ONLY: prints findings to stderr and ALWAYS exits 0, so it never
# blocks a commit while the false-positive rate is being observed. Promote to a
# hard gate (exit 1 on a finding) only after the warn phase proves quiet
# (warn-then-gate). The dispatcher's override is `git commit --no-verify` (logged).
#
# SCOPE (honest cede): INTERNAL consistency of the artifact only. It does NOT
# verify completeness-against-the-schema (whether every drawer that SHOULD exist
# was captured) — that needs the gather context and stays with design-handoff
# step-01 §5f + step-03 §3 + the downstream synthesize/implement gates.
#
# Registered in .githooks/gates.conf as: pre-commit .githooks/check-design-brief-completeness.sh
# Graceful: no-ops when no design-brief is staged, so it is safe in every project.
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
staged=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '(^|/)design-brief-[^/]*\.md$' || true)
[ -z "$staged" ] && exit 0

findings=0
warn() { printf 'design-brief-completeness [WARN]: %s\n' "$1" >&2; findings=$((findings + 1)); }

# Check ONE brief file's frames/§7 internal consistency. Mirrors design-handoff
# step-04 §3 (the in-flow tier). Uses while-read+case, never `for f in $frames`,
# so it is correct under both sh and zsh.
check_brief() {
  brief="$1"
  [ -f "$brief" ] || return 0

  frames=$(awk '
    NR==1 && $0=="---"{infm=1; next}
    infm && $0=="---"{exit}
    infm && /^frames:/{
      if ($0 ~ /\[/){ s=$0; sub(/^[^[]*\[/,"",s); sub(/\].*/,"",s); gsub(/,/," ",s); print s; next }
      blk=1; next }
    infm && blk && /^[[:space:]]*-[[:space:]]/{ s=$0; sub(/^[[:space:]]*-[[:space:]]*/,"",s); print s; next }
    infm && blk && /^[^[:space:]]/{ blk=0 }
  ' "$brief" | tr -d "\"'," | tr -s " " "\n" | sed '/^$/d')

  n=$(printf '%s\n' "$frames" | sed '/^$/d' | wc -l | tr -d ' ')
  if [ "$n" -eq 0 ]; then
    warn "$brief: no non-empty 'frames:' in Block B (brief-revision-policy.md §2 invariant 1a) — ships UNVERIFIED; design-implement's §SHARED.1b gate cannot bite."
    return 0
  fi

  dupes=$(printf '%s\n' "$frames" | sort | uniq -d)
  [ -n "$dupes" ] && warn "$brief: duplicate frame id(s) in 'frames:': $dupes — frame names must be unique."

  body=$(awk 'NR==1 && $0=="---"{infm=1;next} infm && $0=="---"{infm=0;next} !infm{print}' "$brief")
  missing=""
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$body" in *"$f"*) : ;; *) missing="$missing $f" ;; esac
  done <<EOF
$frames
EOF
  [ -n "$missing" ] && warn "$brief: frame id(s) in 'frames:' absent from the body / §7 Surface Inventory:$missing — Block B 'frames' must mirror the §7 rows."

  if printf '%s' "$body" | grep -qiE '^#+.*linked records'; then
    printf '%s' "$body" | grep -qiE 'surface inventory' \
      || warn "$brief: has a Linked Records (§2a) section but no §7 Surface Inventory — each linked record needs a lookup-drawer frame."
  fi
}

# sh/dash word-splits unquoted $staged on newlines (design-brief filenames are
# kebab-case, no spaces); fine here. (zsh wouldn't, but the dispatcher runs `sh`.)
for brief in $staged; do
  check_brief "$ROOT/$brief"
done

if [ "$findings" -gt 0 ]; then
  printf 'design-brief-completeness: %s finding(s) (Phase-1 WARN — commit NOT blocked). Fix the §7/frames contract in design-handoff, or re-run delivery.\n' "$findings" >&2
fi
exit 0
