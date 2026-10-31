#!/usr/bin/env bash
#
# check-onboarding-version.sh — SessionStart detector for onboarding-playbook drift.
#
# Sibling of check-upstream-drift.sh / check-claude-md-drift.sh / check-standards-drift.sh.
# Registered in the hand-maintained ~/.claude/settings.json SessionStart chain.
#
# CONTRACT (enforcement-expert lane):
#   - The canonical stamp lives in <project>/_bmad/bmm/config.yaml under `onboarding:`
#     (machine-checkable PROOF, written by onboard-project.sh). This script is the
#     DETERMINISTIC DELIVERY of AWARENESS: it always runs at session start and surfaces
#     one line when the repo's stamped playbook_version is OLDER than the fork currently ships.
#   - CONSERVATIVE BY DESIGN: a MISSING stamp is SILENT, not flagged. The ~14 repos onboarded
#     before this marker existed have a config.yaml but no `onboarding:` block — screaming
#     "pre-playbook!" in every one of them every session is the indiscriminate-detector
#     anti-pattern. Absent/unparseable → say nothing. It speaks ONLY on a present-but-stale stamp.
#   - It is awareness, not a gate: it cannot block. Acting on the line is the agent's choice.
#
# Exit 0 always (a detector must never break session start).

set -uo pipefail

FORK_DIR="$HOME/bmad-method-v6"
VERSION_FILE="$FORK_DIR/onboarding-playbook.version"
CONFIG="$PWD/_bmad/bmm/config.yaml"

# Not a BMAD project (no config) → silent.
[[ -f "$CONFIG" ]] || exit 0
# Fork version source missing → can't compare → silent.
[[ -f "$VERSION_FILE" ]] || exit 0

CURRENT="$(grep -oE '[0-9]+' "$VERSION_FILE" | head -1)"
[[ -n "$CURRENT" ]] || exit 0

# Parse the stamped playbook_version. The key is unique to the onboarding block.
STAMPED="$(grep -E '^[[:space:]]*playbook_version:' "$CONFIG" 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1)"

# No stamp → pre-playbook / legacy onboard → SILENT (conservative).
[[ -n "$STAMPED" ]] || exit 0

# Stamp present and current → silent.
[[ "$STAMPED" -lt "$CURRENT" ]] || exit 0

# Present-but-stale → the one signal worth surfacing.
echo "──────────────────────────────────────────"
echo "⚠ Onboarding playbook drift: this repo was onboarded under v$STAMPED; the fork now ships v$CURRENT."
echo "  Re-stamp (rewrites the marker only, no re-clone/sync): ~/bmad-method-v6/onboard-project.sh --restamp"
echo "──────────────────────────────────────────"
exit 0
