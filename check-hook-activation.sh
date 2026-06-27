#!/usr/bin/env bash
# SessionStart soft-warn — flags a repo that SHIPS a git-hook gate (tracked
# .githooks/) but has NOT activated it (core.hooksPath unset/divergent, or a
# husky↔githooks conflict), so the gate is silently OFF. Per STD-HOOKACTIVATE-001.
#
# Enforcement class: DETERMINISTIC delivery of AWARENESS; it cannot activate
# anything — it makes the dead state visible between syncs. The fix is one
# command: scripts/activate-hooks.sh (which sync/onboard also run automatically).
#
# Conservative: SILENT when wired correctly, and SILENT when the repo ships no
# .githooks/ gate at all (no false fire on gate-less repos). Warn-only.
set -uo pipefail

emit() {
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$1" 2>/dev/null || true
}

# Only act inside a real project.
[ -d .git ] || [ -d _bmad ] || exit 0

# Gate is "expected" only if the repo actually ships a tracked .githooks/ dir.
[ -d .githooks ] || exit 0

hookspath="$(git config --get core.hooksPath 2>/dev/null || true)"

# Husky↔githooks conflict: husky present and still owning core.hooksPath while a
# .githooks/ also ships → the two mutually-exclusive mechanisms are fighting.
if [ -d .husky ] && printf '%s' "$hookspath" | grep -q '\.husky'; then
  emit "HOOK ACTIVATION conflict: this repo ships .githooks/ but core.hooksPath still points at husky (${hookspath}). They are mutually exclusive — run scripts/activate-hooks.sh to consolidate on .githooks/ (STD-HOOKACTIVATE-001)."
  exit 0
fi

if [ "$hookspath" != ".githooks" ]; then
  emit "HOOK ACTIVATION drift: this repo ships a git-hook gate (.githooks/) but core.hooksPath is '${hookspath:-unset}', so the gate is NOT firing — pushes/commits are not gated. Run scripts/activate-hooks.sh to wire it (STD-HOOKACTIVATE-001)."
  exit 0
fi

# Activated but an entrypoint lost its exec bit (copy/checkout can drop it).
for ep in .githooks/pre-push .githooks/pre-commit; do
  if [ -f "$ep" ] && [ ! -x "$ep" ]; then
    emit "HOOK ACTIVATION drift: core.hooksPath=.githooks but ${ep} is not executable, so it won't run. Run scripts/activate-hooks.sh (STD-HOOKACTIVATE-001)."
    exit 0
  fi
done

exit 0
