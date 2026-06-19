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

echo "✅ global assets installed."
