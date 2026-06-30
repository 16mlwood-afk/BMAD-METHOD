#!/usr/bin/env bash
#
# install-global-assets.sh — install/restore the fork's GLOBAL Claude assets into ~/.claude.
#
# ~/.claude is NOT git-tracked, so the bmad-onboard skill (which makes "install the BMAD fork"
# work as a natural-language trigger) has no backup there. The canonical copy lives in this fork
# under custom/claude-global/; this script restores it to ~/.claude/skills/.
#
# Idempotent. Safe to run any time. Run once after cloning the fork on a new machine, or any time
# the global skill goes missing / stale.
#
# The global CLAUDE.md "New project bootstrap" section is also backed up here
# (custom/claude-global/new-project-bootstrap.snippet.md) but is NOT auto-merged — the user's global
# ~/.claude/CLAUDE.md is hand-maintained. If the section is missing, paste the snippet in by hand.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_SKILLS="$SCRIPT_DIR/custom/claude-global/skills"
DST_SKILLS="$HOME/.claude/skills"
SNIPPET="$SCRIPT_DIR/custom/claude-global/new-project-bootstrap.snippet.md"
GLOBAL_CLAUDEMD="$HOME/.claude/CLAUDE.md"

mkdir -p "$DST_SKILLS"

installed=0
for skill_dir in "$SRC_SKILLS"/*/; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  dst="$DST_SKILLS/$name"
  if [[ ! -d "$dst" ]] || ! diff -rq --exclude='.DS_Store' "$skill_dir" "$dst" &>/dev/null; then
    rm -rf "$dst"
    cp -R "$skill_dir" "$dst"
    echo "  ✓ installed/updated global skill: $name"
    installed=$((installed + 1))
  else
    echo "  • up to date: $name"
  fi
done
[[ $installed -eq 0 ]] && echo "  (all global skills already current)"

# CLAUDE.md bootstrap section — check presence only; do not auto-edit the hand-maintained file.
if [[ -f "$GLOBAL_CLAUDEMD" ]] && ! grep -q '^### New project bootstrap' "$GLOBAL_CLAUDEMD"; then
  echo "  ! ~/.claude/CLAUDE.md is missing the 'New project bootstrap' section."
  echo "    Restore it by pasting: $SNIPPET"
fi

# ── Global hooks (prod-readiness probe/gate, enforcement-expert nudge) ──
SRC_HOOKS="$SCRIPT_DIR/custom/claude-global/hooks"
DST_HOOKS="$HOME/.claude/hooks"
if [[ -d "$SRC_HOOKS" ]]; then
  mkdir -p "$DST_HOOKS/lib"
  cp "$SRC_HOOKS"/*.sh "$DST_HOOKS"/ 2>/dev/null || true
  cp "$SRC_HOOKS"/lib/*.sh "$DST_HOOKS"/lib/ 2>/dev/null || true
  chmod +x "$DST_HOOKS"/*.sh "$DST_HOOKS"/lib/*.sh 2>/dev/null || true
  echo "  ✓ installed/refreshed global hooks → $DST_HOOKS"
fi

# Register hook entries in ~/.claude/settings.json (idempotent; prod-readiness gate ships in DRY-RUN).
SETTINGS="$HOME/.claude/settings.json"
if [[ -f "$SETTINGS" ]] && command -v python3 &>/dev/null; then
  python3 - "$SETTINGS" "$DST_HOOKS" "$SCRIPT_DIR" <<'PY' || echo "  ! settings.json hook registration skipped (merge error)"
import json, sys
p, hooks, forkdir = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(p)); H = d.setdefault('hooks', {})
def ensure_cmd(event, matcher, command, needle, timeout=5):
    arr = H.setdefault(event, [])
    for e in arr:
        for h in e.get('hooks', []):
            if needle in h.get('command',''): return 0
    entry = {"hooks":[{"type":"command","command":command,"timeout":timeout}]}
    if matcher: entry["matcher"] = matcher
    arr.append(entry); return 1
def ensure(event, matcher, script):
    return ensure_cmd(event, matcher, f"{hooks}/{script}", script)
ch = (ensure('SessionStart', None, 'prod-readiness-probe.sh')
      + ensure('PreToolUse', 'Bash', 'prod-readiness-deploy-gate.sh')
      + ensure('PreToolUse', 'Edit|Write', 'enforcement-expert-nudge.sh')
      # fork-of-upstream destructive-op guard (self-gates on the onboarding topology stamp)
      + ensure('PreToolUse', 'Bash', 'bmad-upstream-guard.sh')
      # sprint-apply executor gate (correct-course) — freezes a pending proposal's
      # files_to_change set until an APPROVE token clears it; ships in DRY-RUN (no .mode file)
      + ensure('PreToolUse', 'Edit|Write|Bash', 'sprint-apply-gate.sh')
      + ensure('UserPromptSubmit', None, 'sprint-apply-approve.sh')
      # onboarding-playbook drift detector — fork-root sibling of check-*-drift.sh, silent unless stale
      + ensure_cmd('SessionStart', None,
                   f'bash "{forkdir}/check-onboarding-version.sh" 2>/dev/null || true',
                   'check-onboarding-version.sh', 10)
      # git-hook activation liveness (STD-HOOKACTIVATE-001) — warns when a repo ships
      # a .githooks/ gate but core.hooksPath isn't wired, so the gate is silently off
      + ensure_cmd('SessionStart', None,
                   f'bash "{forkdir}/check-hook-activation.sh" 2>/dev/null || true',
                   'check-hook-activation.sh', 5)
      # cross-session WIP register (parallel-sessions.md §E): surface in-flight
      # feature work by OTHER sessions at start (AWARENESS, tier 4 — never blocks)
      + ensure_cmd('SessionStart', None,
                   f'bash "{forkdir}/check-wip-register.sh" 2>/dev/null || true',
                   'check-wip-register.sh', 5)
      # …and write the claim deterministically when a worktree is created (the
      # only reliable "feature work starting" signal — not a skippable step)
      + ensure_cmd('PostToolUse', 'EnterWorktree',
                   f'bash "{forkdir}/wip-claim-on-worktree.sh" 2>/dev/null || true',
                   'wip-claim-on-worktree.sh', 5))
if ch: json.dump(d, open(p,'w'), indent=4); print(f"  ✓ registered {ch} hook(s) in settings.json")
else: print("  • hooks already registered in settings.json")
PY
fi

# Enforcement Gate CLAUDE.md section — presence check only (hand-maintained file).
SNIPPET2="$SCRIPT_DIR/custom/claude-global/enforcement-gate.snippet.md"
if [[ -f "$GLOBAL_CLAUDEMD" ]] && ! grep -q '^## Enforcement Gate Before Trusting a Rule' "$GLOBAL_CLAUDEMD"; then
  echo "  ! ~/.claude/CLAUDE.md is missing the 'Enforcement Gate' section."
  echo "    Restore it by pasting: $SNIPPET2"
fi

echo "✅ global assets installed."
