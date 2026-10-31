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
# Safeguards under test (security review of fork PR 25): protected guards cannot be
# excluded; skipped groups are always printed (sync and check); the file is honoured only
# when tracked and unchanged from HEAD.
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
    grep '^NONEXCLUDABLE_HOOK_GROUPS=' "$1" || true
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

# A target (a real git repo) seeded with a project-authored hook.
seed() {
  mkdir -p "$1/.claude"
  git -C "$1" init -q 2>/dev/null
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
# commit everything currently in the target, so the opt-out file is tracked and clean
commit_all() {
  git -C "$1" add -A >/dev/null 2>&1
  git -C "$1" -c user.email=t@t -c user.name=t commit -q -m seed >/dev/null 2>&1
}

# T1: control target, no opt-out file: new code == baseline, byte for byte.
seed "$TMP/ctl-new"; seed "$TMP/ctl-base"
run_writer "$TMP/new.sh" "$TMP/ctl-new" sync >/dev/null 2>&1
run_writer "$TMP/base.sh" "$TMP/ctl-base" sync >/dev/null 2>&1
if cmp -s "$TMP/ctl-new/.claude/settings.json" "$TMP/ctl-base/.claude/settings.json" \
   && cmp -s "$TMP/ctl-new/.claude/settings.local.json" "$TMP/ctl-base/.claude/settings.local.json"; then
  ok "T1 no opt-out file: settings.json and settings.local.json byte-identical to baseline"
else bad "T1 control target differs from baseline"; fi

# T2: ownsSettings with every protected guard wired: nothing written, byte-identical, SKIP printed.
seed "$TMP/own"
cp "$TMP/ctl-new/.claude/settings.json" "$TMP/own/.claude/settings.json"   # fully wired by the control sync
echo '{"ownsSettings": true}' > "$TMP/own/.claude/bmad-sync-optout.json"
commit_all "$TMP/own"
cp "$TMP/own/.claude/settings.json" "$TMP/own-before.json"
out="$(run_writer "$TMP/new.sh" "$TMP/own" sync 2>&1)"; rc=$?
if [[ $rc -eq 0 ]] && cmp -s "$TMP/own-before.json" "$TMP/own/.claude/settings.json" \
   && [[ ! -e "$TMP/own/.claude/settings.local.json" ]]; then
  ok "T2 ownsSettings: settings byte-identical, no local file created"
else bad "T2 ownsSettings wrote something (rc=$rc)"; fi
grep -q "SKIP" <<<"$out" && ok "T2 sync prints that settings were skipped" || bad "T2 no SKIP line in sync"
grep -q "WARN" <<<"$out" && bad "T2 spurious protected-guard warning on a fully wired project: $out" || ok "T2 no warning when every protected guard is wired"
out="$(run_writer "$TMP/new.sh" "$TMP/own" check 2>&1)"; rc=$?
[[ $rc -eq 0 ]] && grep -q "SKIP" <<<"$out" && ok "T2b --check form: no drift AND prints the skip" || bad "T2b check output: rc=$rc $out"

# T3: excludeHookGroups: excluded absent, others present, project hook kept.
seed "$TMP/ex"
cat > "$TMP/ex/.claude/bmad-sync-optout.json" <<'JSON'
{"excludeHookGroups": ["bmad-delivery-check", "bmad-design-policy-drift", "PostToolUse:Skill"]}
JSON
commit_all "$TMP/ex"
out="$(run_writer "$TMP/new.sh" "$TMP/ex" sync 2>&1)"; rc=$?
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
c_names="$(jq -r '[.hooks[][] | .name // empty] | join(" ")' "$TMP/ctl-new/.claude/settings.json")"
case " $c_names " in *" bmad-delivery-check "*) ok "T3 control still receives bmad-delivery-check" ;; *) bad "T3 control lost a group" ;; esac
grep -q "SKIP.*bmad-delivery-check.*bmad-design-policy-drift.*PostToolUse:Skill" <<<"$out" \
  && ok "T3 sync prints exactly which groups were skipped" || bad "T3 sync skip line missing: $out"
cp "$S" "$TMP/ex-after1.json"
run_writer "$TMP/new.sh" "$TMP/ex" sync >/dev/null 2>&1
cmp -s "$TMP/ex-after1.json" "$S" && ok "T3 second sync byte-identical (idempotent)" || bad "T3 second sync changed the file"
out="$(run_writer "$TMP/new.sh" "$TMP/ex" check 2>&1)"; rc=$?
[[ $rc -eq 0 ]] && ok "T3 --check form reports no drift after sync" || bad "T3 --check reports drift"
grep -q "SKIP.*bmad-delivery-check" <<<"$out" && ok "T3 --check prints which groups are skipped" || bad "T3 check skip line missing: $out"

# T4: an excluded group already in the project's file is left alone (not stripped).
seed "$TMP/keep"
echo '{"excludeHookGroups": ["bmad-single-track-guard"]}' > "$TMP/keep/.claude/bmad-sync-optout.json"
jq '.hooks.PreToolUse += [{"matcher":"Bash","hooks":[{"type":"command","command":"N=single-track-guard.py; python3 \"$N\""}]}]' "$TMP/keep/.claude/settings.json" > "$TMP/keep-seed.json"
cp "$TMP/keep-seed.json" "$TMP/keep/.claude/settings.json"
commit_all "$TMP/keep"
run_writer "$TMP/new.sh" "$TMP/keep" sync >/dev/null 2>&1
jq -e '[.hooks.PreToolUse[].hooks[].command] | map(select(contains("single-track-guard.py"))) | length == 1' "$TMP/keep/.claude/settings.json" >/dev/null \
  && ok "T4 project's own copy of an excluded group kept exactly once" || bad "T4 project's own hook stripped or duplicated"

# T5: malformed opt-out file (tracked, clean): loud failure, nothing written.
seed "$TMP/bad"
echo 'not json' > "$TMP/bad/.claude/bmad-sync-optout.json"
commit_all "$TMP/bad"
cp "$TMP/bad/.claude/settings.json" "$TMP/bad-before.json"
out="$(run_writer "$TMP/new.sh" "$TMP/bad" sync 2>&1)"; rc=$?
if [[ $rc -ne 0 ]] && cmp -s "$TMP/bad-before.json" "$TMP/bad/.claude/settings.json" && grep -q "WARN" <<<"$out"; then
  ok "T5 malformed opt-out file: warns, returns non-zero, writes nothing"
else bad "T5 malformed opt-out file mishandled (rc=$rc)"; fi

# T6: no temp file left behind.
ls "${TMPDIR:-/tmp}"/bmad-hooks-filtered.* >/dev/null 2>&1 && bad "T6 temp file leaked" || ok "T6 no filtered-template temp file left behind"

# T7: naming protected guards: warns and is ignored; they are still written.
seed "$TMP/prot"
echo '{"excludeHookGroups": ["bmad-worktree-guard", "bmad-bash-edit-guard", "bmad-credential-scan", "bmad-delivery-check"]}' > "$TMP/prot/.claude/bmad-sync-optout.json"
commit_all "$TMP/prot"
out="$(run_writer "$TMP/new.sh" "$TMP/prot" sync 2>&1)"
pn="$(jq -r '[.hooks[][] | .name // empty] | join(" ")' "$TMP/prot/.claude/settings.json")"
for g in bmad-worktree-guard bmad-bash-edit-guard bmad-credential-scan; do
  grep -q "WARN.*protected group $g" <<<"$out" && ok "T7 $g: warned" || bad "T7 $g: no warning"
  case " $pn " in *" $g "*) ok "T7 $g still written" ;; *) bad "T7 $g was excluded" ;; esac
done
case " $pn " in *" bmad-delivery-check "*) bad "T7 ordinary exclusion lost" ;; *) ok "T7 ordinary exclusion in the same file still applies" ;; esac
# every default protected name is a real group in the template (the list cannot rot silently)
for g in $(grep '^NONEXCLUDABLE_HOOK_GROUPS=' "$SCRIPT" | sed 's/^[^"]*"//; s/"$//'); do
  jq -e --arg g "$g" '[.hooks[][] | .name] | index($g)' "$TEMPLATE" >/dev/null && ok "T7 protected name $g exists in the template" || bad "T7 protected name $g is not in the template"
done

# T8: ownsSettings with a protected guard unwired: warns.
seed "$TMP/own2"
echo '{"ownsSettings": true}' > "$TMP/own2/.claude/bmad-sync-optout.json"
commit_all "$TMP/own2"
out="$(run_writer "$TMP/new.sh" "$TMP/own2" check 2>&1)"
grep -q "WARN.*ownsSettings.*bmad-worktree-guard" <<<"$out" && ok "T8 ownsSettings warns that the worktree guard is not wired" || bad "T8 no unwired warning: $out"

# T9: file untracked, or changed from HEAD: not honoured, groups written, warning printed.
seed "$TMP/untracked"
commit_all "$TMP/untracked"
echo '{"excludeHookGroups": ["bmad-delivery-check"]}' > "$TMP/untracked/.claude/bmad-sync-optout.json"
out="$(run_writer "$TMP/new.sh" "$TMP/untracked" sync 2>&1)"
grep -q "IGNORED.*not tracked" <<<"$out" && ok "T9 untracked opt-out: warned" || bad "T9 no untracked warning: $out"
jq -e '[.hooks[][] | .name] | index("bmad-delivery-check")' "$TMP/untracked/.claude/settings.json" >/dev/null \
  && ok "T9 untracked opt-out not honoured (group written)" || bad "T9 untracked opt-out was honoured"
seed "$TMP/edited"
echo '{"excludeHookGroups": []}' > "$TMP/edited/.claude/bmad-sync-optout.json"
commit_all "$TMP/edited"
echo '{"excludeHookGroups": ["bmad-delivery-check"]}' > "$TMP/edited/.claude/bmad-sync-optout.json"
out="$(run_writer "$TMP/new.sh" "$TMP/edited" sync 2>&1)"
grep -q "IGNORED.*differs from HEAD" <<<"$out" && ok "T9 uncommitted edit to the opt-out: warned" || bad "T9 no differs-from-HEAD warning: $out"
jq -e '[.hooks[][] | .name] | index("bmad-delivery-check")' "$TMP/edited/.claude/settings.json" >/dev/null \
  && ok "T9 edited opt-out not honoured (group written)" || bad "T9 edited opt-out was honoured"
# a repo with no commits at all (no HEAD) cannot honour it either
seed "$TMP/nohead"
echo '{"excludeHookGroups": ["bmad-delivery-check"]}' > "$TMP/nohead/.claude/bmad-sync-optout.json"
git -C "$TMP/nohead" add -A >/dev/null 2>&1
out="$(run_writer "$TMP/new.sh" "$TMP/nohead" sync 2>&1)"
grep -q "IGNORED" <<<"$out" && ok "T9 staged-but-uncommitted opt-out: not honoured" || bad "T9 staged-only opt-out was honoured"

exit "$fail"
