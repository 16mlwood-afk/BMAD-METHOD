#!/usr/bin/env bash
# verify-sync-hook-optout.sh — regression suite for the per-project hook opt-out in
# sync-bmad-workflows.sh (.claude/bmad-sync-optout.json, read from the TARGET repo).
#
# WHY: write_claude_settings wrote every fork hook group into a target's tracked
# .claude/settings.json. amazon-removal-assistant curates its own wiring, and the sync kept
# re-adding groups it had dropped (30 uncommitted entries, 2026-10-31).
#
# The suite extracts the functions VERBATIM from the script (it never tests a copy), and
# compares against the same functions extracted from the committed baseline on `custom`,
# so "a target with no opt-out file gets byte-identical results to before" is measured.
#
# Run:  bash tools/verify-sync-hook-optout.sh
set -uo pipefail
FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$FORK/sync-bmad-workflows.sh"
TEMPLATE="$FORK/src/modules/bmm/_module-installer/assets/hooks.json"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail=0
ok()  { echo "PASS $1"; }
bad() { echo "FAIL $1"; fail=1; }

bash -n "$SCRIPT" || { echo "FAIL script does not parse"; exit 1; }

extract() { # $1 = script file, $2 = output file
  {
    awk "/^JQ_MERGE='/{f=1} f{print} f&&/^'\$/{exit}" "$1"
    awk "/^JQ_LOCAL='/{f=1} f{print} f&&/^'\$/{exit}" "$1"
    awk '/^write_claude_settings\(\) \{/{f=1} f{print} f&&/^}/{exit}' "$1"
    awk '/^_write_claude_settings_from\(\) \{/{f=1} f{print} f&&/^}/{exit}' "$1"
  } > "$2"
}
extract "$SCRIPT" "$TMP/new.sh"
BASE_SRC="$TMP/base-script.sh"
(cd "$FORK" && git show custom:sync-bmad-workflows.sh) > "$BASE_SRC" 2>/dev/null || { echo "FAIL cannot read baseline from custom"; exit 2; }
extract "$BASE_SRC" "$TMP/base.sh"
[[ -s "$TMP/new.sh" && -s "$TMP/base.sh" ]] || { echo "FAIL extraction empty"; exit 2; }

# run_writer <impl.sh> <root> <mode>  -- prints writer output, returns its status
run_writer() {
  ( HOOKS_SRC="$TEMPLATE"
    ensure_claude_paths_trackable() { GITIGNORE_REPORT=""; return 0; }
    claude_tracking_blocked() { :; }
    # shellcheck disable=SC1090
    source "$1"
    write_claude_settings "$2" "$3" )
}

# A target seeded with a project-authored hook and one already-installed template group.
seed() {
  mkdir -p "$1/.claude"
  cat > "$1/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 project-own-guard.py"}]}
    ]
  }
}
JSON
}

# T1: control target, no opt-out file: new code == baseline, byte for byte.
seed "$TMP/ctl-new"; seed "$TMP/ctl-base"
run_writer "$TMP/new.sh" "$TMP/ctl-new" sync >/dev/null 2>&1
run_writer "$TMP/base.sh" "$TMP/ctl-base" sync >/dev/null 2>&1
if cmp -s "$TMP/ctl-new/.claude/settings.json" "$TMP/ctl-base/.claude/settings.json" \
   && cmp -s "$TMP/ctl-new/.claude/settings.local.json" "$TMP/ctl-base/.claude/settings.local.json"; then
  ok "T1 no opt-out file: settings.json and settings.local.json byte-identical to baseline"
else bad "T1 control target differs from baseline"; fi

# T2: ownsSettings: nothing written, settings byte-identical before and after.
seed "$TMP/own"
echo '{"ownsSettings": true}' > "$TMP/own/.claude/bmad-sync-optout.json"
cp "$TMP/own/.claude/settings.json" "$TMP/own-before.json"
run_writer "$TMP/new.sh" "$TMP/own" sync >/dev/null 2>&1; rc=$?
if [[ $rc -eq 0 ]] && cmp -s "$TMP/own-before.json" "$TMP/own/.claude/settings.json" \
   && [[ ! -e "$TMP/own/.claude/settings.local.json" ]]; then
  ok "T2 ownsSettings: settings byte-identical, no local file created"
else bad "T2 ownsSettings wrote something (rc=$rc)"; fi
run_writer "$TMP/new.sh" "$TMP/own" check >/dev/null 2>&1 && ok "T2b ownsSettings: --check form reports no drift" || bad "T2b check reported drift"

# T3: excludeHookGroups: excluded absent, others present, project hook kept.
seed "$TMP/ex"
cat > "$TMP/ex/.claude/bmad-sync-optout.json" <<'JSON'
{"excludeHookGroups": ["bmad-delivery-check", "bmad-design-policy-drift", "PostToolUse:Skill"]}
JSON
run_writer "$TMP/new.sh" "$TMP/ex" sync >/dev/null 2>&1; rc=$?
S="$TMP/ex/.claude/settings.json"
names="$(jq -r '[.hooks[][] | .name // empty] | join(" ")' "$S")"
[[ $rc -eq 0 ]] && ok "T3 sync with exclusions exits 0" || bad "T3 rc=$rc"
for g in bmad-delivery-check bmad-design-policy-drift; do
  case " $names " in *" $g "*) bad "T3 $g was written despite exclusion" ;; *) ok "T3 $g not written" ;; esac
done
n_skill="$(jq '[.hooks.PostToolUse[]? | select((.name // "") == "" and .matcher == "Skill")] | length' "$S")"
[[ "$n_skill" == "0" ]] && ok "T3 unnamed PostToolUse:Skill group not written" || bad "T3 unnamed group written"
case " $names " in *" bmad-worktree-guard "*) ok "T3 non-excluded group (bmad-worktree-guard) still written" ;; *) bad "T3 non-excluded group missing" ;; esac
jq -e '[.hooks.PreToolUse[].hooks[].command] | index("python3 project-own-guard.py")' "$S" >/dev/null \
  && ok "T3 project-authored hook preserved" || bad "T3 project hook lost"
# the control wrote the excluded groups, so the exclusion is what removed them
c_names="$(jq -r '[.hooks[][] | .name // empty] | join(" ")' "$TMP/ctl-new/.claude/settings.json")"
case " $c_names " in *" bmad-delivery-check "*) ok "T3 control still receives bmad-delivery-check" ;; *) bad "T3 control lost a group" ;; esac
# second sync changes nothing; check form agrees
cp "$S" "$TMP/ex-after1.json"
run_writer "$TMP/new.sh" "$TMP/ex" sync >/dev/null 2>&1
cmp -s "$TMP/ex-after1.json" "$S" && ok "T3 second sync byte-identical (idempotent)" || bad "T3 second sync changed the file"
run_writer "$TMP/new.sh" "$TMP/ex" check >/dev/null 2>&1 && ok "T3 --check form reports no drift after sync" || bad "T3 --check reports drift"

# T4: an excluded group already in the project's file is left alone (not stripped) even when
# its script is claimed by bmadTrackedHookScripts.
seed "$TMP/keep"
echo '{"excludeHookGroups": ["bmad-worktree-guard"]}' > "$TMP/keep/.claude/bmad-sync-optout.json"
jq '.hooks.PreToolUse += [{"matcher":"Edit|Write","hooks":[{"type":"command","command":"N=worktree-edit-guard.py; python3 \"$N\""}]}]' "$TMP/keep/.claude/settings.json" > "$TMP/keep-seed.json"
cp "$TMP/keep-seed.json" "$TMP/keep/.claude/settings.json"
run_writer "$TMP/new.sh" "$TMP/keep" sync >/dev/null 2>&1
jq -e '[.hooks.PreToolUse[].hooks[].command] | map(select(contains("worktree-edit-guard.py"))) | length == 1' "$TMP/keep/.claude/settings.json" >/dev/null \
  && ok "T4 project's own worktree guard kept exactly once" || bad "T4 worktree guard stripped or duplicated"

# T5: malformed opt-out file: loud failure, nothing written.
seed "$TMP/bad"
echo 'not json' > "$TMP/bad/.claude/bmad-sync-optout.json"
cp "$TMP/bad/.claude/settings.json" "$TMP/bad-before.json"
out="$(run_writer "$TMP/new.sh" "$TMP/bad" sync 2>&1)"; rc=$?
if [[ $rc -ne 0 ]] && cmp -s "$TMP/bad-before.json" "$TMP/bad/.claude/settings.json" && grep -q "WARN" <<<"$out"; then
  ok "T5 malformed opt-out file: warns, returns non-zero, writes nothing"
else bad "T5 malformed opt-out file mishandled (rc=$rc)"; fi

# T6: no temp file left behind.
ls "${TMPDIR:-/tmp}"/bmad-hooks-filtered.* >/dev/null 2>&1 && bad "T6 temp file leaked" || ok "T6 no filtered-template temp file left behind"

exit "$fail"
