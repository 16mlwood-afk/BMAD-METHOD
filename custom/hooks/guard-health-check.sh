#!/usr/bin/env bash
# guard-health-check.sh — is the edit-guard actually WIRED and actually working?
#
# Run: bash .claude/hooks/guard-health-check.sh
# Run it: whenever the guard code changes, and after fanning it out to a project.
#
# WHY THIS EXISTS. On 2026-07-26 the reviewed guard was found to have never been wired: the
# file was present, its 43-case suite was green, and CLAUDE.md asserted it was live — while
# settings.local.json still ran the legacy regex blob. **A passing unit suite proves the
# LOGIC. Only a live tool call proves the WIRING.** Those are different claims and the whole
# incident came from conflating them. So this check deliberately does NOT import the guard;
# it invokes it the way the harness does, through its stdin/JSON contract.
#
# Two probes, and both directions are load-bearing:
#   ALLOW probe — a harmless command that MENTIONS write-ish tokens but writes nothing.
#                 Catches over-blocking (the false-positive class that erodes the guard).
#   DENY  probe — a real write to a tracked source file. Catches under-blocking (a guard
#                 that is present but toothless, which is worse than an absent one).
#
# It also checks that the wiring points at the REVIEWED implementation, because a green
# pair of probes is satisfiable by the legacy blob too.
#
# Exit 0 = healthy. Exit 1 = a finding. Nothing is mutated: no file is written by either
# probe (the deny probe is expected never to run its redirect).

set -uo pipefail
PROJECT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
GUARD="$PROJECT/.claude/hooks/bash_edit_guard.py"
SETTINGS="$PROJECT/.claude/settings.local.json"
fail=0

say() { printf '%s\n' "$1"; }
bad() { printf '  ✗ %s\n' "$1"; fail=1; }
ok()  { printf '  ✓ %s\n' "$1"; }

say ""
say "edit-guard health check · $PROJECT"

# --- 0. The reviewed implementation is present and is what settings invokes -------------
[ -f "$GUARD" ] || bad "reviewed guard missing at .claude/hooks/bash_edit_guard.py"
if [ -f "$SETTINGS" ]; then
  if grep -q "bash_edit_guard" "$SETTINGS"; then
    ok "settings.local.json invokes the reviewed guard"
  else
    bad "settings.local.json does NOT invoke bash_edit_guard.py — the legacy inline regex is
      probably still live. This is the exact 2026-07-26 finding: green suite, zero wiring."
  fi
  if grep -q "edit-equivalent (sed -i / cat >" "$SETTINGS"; then
    bad "the LEGACY regex blob is still present in settings.local.json — it is superseded and
      must not run anywhere new (CLAUDE.md § Worktree Enforcement Hooks)."
  fi
else
  bad "no settings.local.json found — cannot confirm the guard is wired at all"
fi

# --- helper: ask the guard, exactly as the harness does ---------------------------------
verdict() {  # $1 = command string
  local payload out
  payload=$(python3 -c 'import json,sys; print(json.dumps({"tool_input":{"command":sys.argv[1]}}))' "$1")
  out=$(printf '%s' "$payload" | BMAD_ALLOW_MAIN_EDIT= CLAUDE_PROJECT_DIR="$PROJECT" \
        python3 "$GUARD" 2>/dev/null)
  if [ -z "$out" ]; then
    printf 'allow'
  else
    printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])' 2>/dev/null \
      || printf 'malformed'
  fi
}

# --- 1. ALLOW probe: mentions the tokens, writes nothing --------------------------------
got=$(verdict "python3 -c \"print('tokens: sed -i / cat > file / tee x')\"")
if [ "$got" = "allow" ]; then
  ok "ALLOW probe: read-only command mentioning sed -i / cat > / tee is permitted"
else
  bad "ALLOW probe got '$got' — the guard is over-blocking read-only commands. That is the
      false-positive class that trains everyone to ignore it."
fi

# --- 2. DENY probe: a real write to tracked source -------------------------------------
got=$(verdict "echo '// must never land' > src/db/schema.ts")
if [ "$got" = "deny" ]; then
  ok "DENY probe: a real write to tracked source is blocked"
elif [ "$got" = "allow" ]; then
  bad "DENY probe got 'allow' — the guard is TOOTHLESS. Note: it allows by design when only
      ONE claude session is running, so re-check with parallel sessions before concluding
      it is broken."
else
  bad "DENY probe got '$got'"
fi

# --- 3. The override works and logs ----------------------------------------------------
tmplog=$(mktemp)
payload=$(python3 -c 'import json; print(json.dumps({"tool_input":{"command":"echo x > src/db/schema.ts"}}))')
printf '%s' "$payload" | BMAD_ALLOW_MAIN_EDIT=1 BASH_EDIT_GUARD_LOG="$tmplog" \
  CLAUDE_PROJECT_DIR="$PROJECT" python3 "$GUARD" >/dev/null 2>&1
if [ -s "$tmplog" ]; then
  ok "override probe: BMAD_ALLOW_MAIN_EDIT=1 permits AND writes an audit row"
else
  bad "override probe wrote NO audit row — a silent override defeats the audit trail"
fi
rm -f "$tmplog"

say ""
if [ "$fail" -eq 0 ]; then
  say "  HEALTHY — guard is wired, precise in both directions, and logging its override."
  say "  (Scripts remain out of scope by design: a python3/node script can perform edits this"
  say "   guard would block. Documented gap, not a defect — CLAUDE.md § Edit guard overrides.)"
else
  say "  FINDINGS ABOVE — do not report this guard as live until they are cleared."
fi
exit "$fail"
