#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# wip-claim-on-worktree.sh — PostToolUse(EnterWorktree) hook: write a WIP claim
# for the worktree just created, so parallel sessions see this in-flight work.
#
# This is the DETERMINISTIC write tier of the cross-session register: worktree
# creation is the only reliable "feature work is starting" signal, so the claim
# hangs off the tool event, not a workflow step the agent might skip. The claim
# starts description-less; quick-spec step-01 / quick-dev step-03 ENRICH it with
# the feature description (the probabilistic, human-intent layer).
#
# Only fires for worktree CREATION (name=), not for entering an existing one
# (path=, signalled by CLAUDE_TOOL_INPUT_PATH). Silent + non-blocking always.
# Mirrors the existing EnterWorktree sync hook's CLAUDE_TOOL_OUTPUT parsing.
# ──────────────────────────────────────────────────────────────────────────
[ -n "${CLAUDE_TOOL_INPUT_PATH:-}" ] && exit 0   # entered an existing worktree — not a new claim

out="${CLAUDE_TOOL_OUTPUT:-}"
wt=$(printf %s "$out" | sed -nE 's|.*Created worktree at ([^ ]+) on branch ([^ .]+).*|\1|p' | head -1)
br=$(printf %s "$out" | sed -nE 's|.*Created worktree at ([^ ]+) on branch ([^ .]+).*|\2|p' | head -1)
[ -z "$wt" ] && exit 0

# Main checkout root = everything left of /.claude/worktrees/...
proj_root="${wt%/.claude/worktrees/*}"
{ [ -d "$proj_root/_bmad" ] || [ -d "$proj_root/.git" ]; } || exit 0

baseline=$(git -C "$wt" rev-parse --short HEAD 2>/dev/null || echo "")
bash "$HOME/bmad-method-v6/wip-register.sh" claim "$proj_root" "$wt" "$br" "$baseline" "" 2>/dev/null || true
exit 0
