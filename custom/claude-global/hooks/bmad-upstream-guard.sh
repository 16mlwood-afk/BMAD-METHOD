#!/usr/bin/env bash
#
# bmad-upstream-guard.sh — PreToolUse (Bash) GATE for fork-of-upstream repos.
#
# When the current repo was onboarded with topology `fork-of-upstream`, a personal fork must
# NEVER push to / force-reset from its external upstream — work is delivered to the fork's OWN
# origin via PRs; upstream is pull-only (fetch + rebase). This hook is the DETERMINISTIC tier of
# that rule (the CLAUDE.md "Upstream fork — sync safety" section is the awareness tier).
#
# CONSERVATIVE BY DESIGN — fires only when BOTH hold:
#   1. the repo's _bmad/bmm/config.yaml stamps `topology: fork-of-upstream`, AND
#   2. the bash command clearly targets `upstream` destructively
#      (push to upstream, force-push, or `reset --hard upstream/*`).
# Anything else → allow (exit 0). A guard that false-fires on normal git work gets ripped out.
#
# OVERRIDE (logged, never silent): prefix the command env with BMAD_ALLOW_UPSTREAM_PUSH=1.
#
# Distributed to ~/.claude/hooks via install-global-assets.sh; registered PreToolUse/Bash.

set -uo pipefail

INPUT="$(cat)"

# Extract the command being run (jq if present, else a tolerant grep fallback).
if command -v jq >/dev/null 2>&1; then
  CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)"
else
  CMD="$(printf '%s' "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"]|\\")*"' | head -1 | sed -E 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')"
fi
[[ -n "${CMD:-}" ]] || exit 0

# Explicit, logged override.
if printf '%s' "$CMD" | grep -qE 'BMAD_ALLOW_UPSTREAM_PUSH=1'; then
  echo "bmad-upstream-guard: override present (BMAD_ALLOW_UPSTREAM_PUSH=1) — allowing, logged." >&2
  exit 0
fi

# Resolve repo root and read the topology stamp.
ROOT="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
CONFIG="$ROOT/_bmad/bmm/config.yaml"
[[ -f "$CONFIG" ]] || exit 0
TOPOLOGY="$(grep -E '^[[:space:]]*topology:' "$CONFIG" 2>/dev/null | head -1 | sed -E 's/.*topology:[[:space:]]*//; s/[[:space:]]*$//' | tr -d '"')"
[[ "$TOPOLOGY" == "fork-of-upstream" ]] || exit 0

# Destructive-upstream patterns.
deny() {
  local reason="$1"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' \
    "$(printf '%s' "$reason" | sed -E 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "\"%s\"", $0}')"
  exit 0
}

NORM="$(printf '%s' "$CMD" | tr -s ' ')"
if printf '%s' "$NORM" | grep -qE 'git[[:space:]]+push([[:space:]]+[^|;&]*)?[[:space:]]+upstream(\b|/)'; then
  deny "Blocked: pushing to upstream. This repo is a personal fork (topology: fork-of-upstream) — deliver to your own origin via a PR; upstream is pull-only. Override: prefix BMAD_ALLOW_UPSTREAM_PUSH=1."
fi
if printf '%s' "$NORM" | grep -qE 'git[[:space:]]+push[[:space:]]+(-f|--force|--force-with-lease)\b' && printf '%s' "$NORM" | grep -qE '\bupstream(\b|/)'; then
  deny "Blocked: force-pushing to upstream on a personal fork (topology: fork-of-upstream). Override: prefix BMAD_ALLOW_UPSTREAM_PUSH=1."
fi
if printf '%s' "$NORM" | grep -qE 'git[[:space:]]+reset[[:space:]]+--hard[[:space:]]+upstream/'; then
  deny "Blocked: hard-resetting onto upstream/* on a personal fork — this discards your fork's divergence. Use 'git rebase upstream/<branch>' instead. Override: prefix BMAD_ALLOW_UPSTREAM_PUSH=1."
fi

exit 0
