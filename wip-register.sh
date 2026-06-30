#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# wip-register.sh — the WRITE side of the cross-session in-flight-work register.
#
# WHY: parallel Claude sessions doing ad-hoc quick-spec/quick-dev feature work
# (driven from a tech-spec, NOT a sprint story) are invisible to each other —
# parallel-sessions.md §C only claims SPRINT STORIES, so two sessions can build
# the same feature blind and one gets thrown away. This is the non-story claim
# ledger that closes that gap (parallel-sessions.md §E).
#
# Enforcement class: DETERMINISTIC write. The claim is written by the
# EnterWorktree PostToolUse hook (worktree creation is the only reliable
# "feature work starting" signal) — it does NOT depend on a workflow step the
# agent might skip under load. quick-spec/quick-dev steps later ENRICH the entry
# with the human-readable description (probabilistic, additive).
#
# Ledger: <main-repo>/.claude/wip-register.yaml — one flow-map line per claim,
# anchored at the MAIN checkout (shared by every worktree of the repo) so a
# claim written from one worktree is visible to every other session. NEVER in
# per-worktree _bmad-output (gitignored + not shared → the blind spot we fix).
# Safe from sync: rsync --delete only touches .claude/{skills,commands,worktrees}.
#
# One claim per WORKTREE PATH (the stable key). Branch names differ between
# sessions building the same feature, so the register gives AWARENESS (branch +
# description + age) and a human/agent judges overlap — there is no deterministic
# "same feature" test, by design (a hard gate here would be the indiscriminate-
# gate anti-pattern).
#
# Usage:
#   wip-register.sh claim  <repo_root> <worktree_path> <branch> <baseline_sha> [description]
#   wip-register.sh clear  <repo_root> <worktree_path>
#   wip-register.sh enrich <repo_root> <worktree_path> <description>
#
# Read side lives in check-wip-register.sh (SessionStart surfacer).
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

cmd="${1:-}"
repo_root="${2:-}"
[ -z "$repo_root" ] && { echo "wip-register: repo_root required" >&2; exit 2; }

reg_dir="$repo_root/.claude"
reg="$reg_dir/wip-register.yaml"

ensure_header() {
  mkdir -p "$reg_dir"
  if [ ! -f "$reg" ]; then
    {
      echo "# In-flight feature claims — auto-managed by wip-register.sh."
      echo "# Cross-session awareness for ad-hoc quick-flow work (parallel-sessions.md §E)."
      echo "# One flow-map line per worktree; dead entries are filtered at read time."
      echo "claims:"
    } > "$reg"
  fi
}

# Drop any existing claim line for this worktree path (the stable key).
drop_worktree() {
  local wt="$1"
  [ -f "$reg" ] || return 0
  grep -vF "worktree: \"$wt\"" "$reg" > "$reg.tmp" 2>/dev/null || true
  mv "$reg.tmp" "$reg"
}

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# Escape a value for a double-quoted YAML flow scalar.
esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

# GC: drop any claim line whose worktree directory no longer exists (the dead-
# claim collector — lets us skip an ExitWorktree hook; removal is detected here).
prune_dead() {
  [ -f "$reg" ] || return 0
  python3 - "$reg" <<'PY' || true
import os, re, sys
reg = sys.argv[1]
out = []
for ln in open(reg, encoding="utf-8"):
    s = ln.rstrip("\n")
    if s.strip().startswith("- {"):
        m = re.search(r'worktree: "((?:[^"\\]|\\.)*)"', s)
        wt = (m.group(1).replace('\\"', '"').replace("\\\\", "\\")) if m else ""
        if wt and not os.path.isdir(wt):
            continue
    out.append(s)
open(reg, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
}

case "$cmd" in
  claim)
    wt="${3:-}"; branch="${4:-}"; baseline="${5:-}"; desc="${6:-}"
    [ -z "$wt" ] && { echo "wip-register claim: worktree_path required" >&2; exit 2; }
    ensure_header
    drop_worktree "$wt"
    printf '  - {branch: "%s", worktree: "%s", session: "%s", baseline: "%s", started: "%s", description: "%s"}\n' \
      "$(esc "$branch")" "$(esc "$wt")" "$(esc "$(basename "$wt")")" "$(esc "$baseline")" "$(now_iso)" "$(esc "$desc")" >> "$reg"
    prune_dead
    ;;
  clear)
    wt="${3:-}"
    [ -z "$wt" ] && { echo "wip-register clear: worktree_path required" >&2; exit 2; }
    drop_worktree "$wt"
    ;;
  enrich)
    wt="${3:-}"; desc="${4:-}"
    [ -z "$wt" ] && { echo "wip-register enrich: worktree_path required" >&2; exit 2; }
    [ -f "$reg" ] || exit 0
    python3 - "$reg" "$wt" "$desc" <<'PY' || true
import re, sys
reg, wt, desc = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(reg, encoding="utf-8").read().splitlines()
needle = f'worktree: "{wt}"'
esc = desc.replace("\\", "\\\\").replace('"', '\\"')
out = []
for ln in lines:
    if needle in ln:
        if "description:" in ln:
            ln = re.sub(r'description: "[^"]*"', 'description: "%s"' % esc, ln)
        else:
            ln = ln.rstrip("}") + ', description: "%s"}' % esc
    out.append(ln)
open(reg, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
    ;;
  *)
    echo "wip-register.sh: unknown command '$cmd' (claim|clear|enrich)" >&2
    exit 2
    ;;
esac
exit 0
