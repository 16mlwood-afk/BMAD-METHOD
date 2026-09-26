#!/usr/bin/env bash
# Shared prod-readiness detection — sourced by BOTH the SessionStart probe and the
# PreToolUse deploy gate so "ready" has ONE definition (a divergence would block on
# different rules than it warned about). Pure functions, no output. DEPLOY domain only.

# Echo the BMAD root (dir containing _bmad/bmm/config.yaml) by walking up; empty if none.
pr_find_root() {
  local d="$1"
  for _ in 1 2 3 4 5 6; do
    [ -f "$d/_bmad/bmm/config.yaml" ] && { printf '%s' "$d"; return 0; }
    [ "$d" = "/" ] && return 1
    d=$(dirname "$d")
  done
  return 1
}

pr_phase() { # $1=root → echoes project_phase value
  grep -E '^project_phase:' "$1/_bmad/bmm/config.yaml" 2>/dev/null | head -1 | sed 's/.*://; s/#.*//; s/[[:space:]]//g'
}

pr_is_live() { case "$(pr_phase "$1")" in brownfield|mixed) return 0 ;; *) return 1 ;; esac; }

# $1=root, $2=start(optional subdir, for an app-subdir CLAUDE.md). 0 if a deploy doc exists.
pr_has_deploy_doc() {
  local root="$1" start="${2:-$1}" c
  grep -qE '^deploy:' "$root/_bmad/bmm/config.yaml" 2>/dev/null && return 0
  [ -f "$root/scripts/bmad-deploy.sh" ] && return 0
  for c in "$root/CLAUDE.md" "$start/CLAUDE.md"; do
    [ -f "$c" ] && grep -qiE '^#+[[:space:]].*deploy' "$c" 2>/dev/null && return 0
  done
  ls "$root"/docs/*deploy* >/dev/null 2>&1 && return 0
  return 1
}

# $1=start dir → 0 (gap: live BMAD project with no deploy doc), else 1. Conservative:
# any non-BMAD / non-live / has-doc case returns 1 (not a gap). Echoes the root on a gap.
pr_is_gap() {
  local start="$1" root
  root=$(pr_find_root "$start") || return 1
  pr_is_live "$root" || return 1
  pr_has_deploy_doc "$root" "$start" && return 1
  printf '%s' "$root"
  return 0
}

# ── Memory domain (charter §4) — same shape as deploy ──
# Project memory is keyed by the BMAD-root absolute path with '/' → '-'.
pr_encode_path() { printf '%s' "$1" | sed 's:/:-:g'; }

# $1=root, $2=start(optional). 0 if memory discipline exists: a project MEMORY.md
# OR a memory section in CLAUDE.md.
pr_has_memory() {
  local root="$1" start="${2:-$1}" c
  [ -f "$HOME/.claude/projects/$(pr_encode_path "$root")/memory/MEMORY.md" ] && return 0
  for c in "$root/CLAUDE.md" "$start/CLAUDE.md"; do
    [ -f "$c" ] && grep -qiE '^#+[[:space:]].*memory' "$c" 2>/dev/null && return 0
  done
  return 1
}
