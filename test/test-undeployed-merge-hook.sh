#!/usr/bin/env bash
# Golden suite for bmad-undeployed-merge-check.
#
# Proves the OLD hook fails the load-bearing case (a fresh session inherits a
# stale baseline and warns about history it had nothing to do with) and the NEW
# hook passes it, without regressing what the hook already got right.
#
# Sessions are simulated by varying CLAUDE_CODE_SESSION_ID -- the harness-
# exported per-session UUID the new marker key is built from. (PPID is readonly
# in bash and cannot be faked, and it is NOT stable across subshells, which is
# precisely why the key must not depend on it.)
#
# Run: bash test-undeployed-hook.sh

set -uo pipefail
cd "$(dirname "$0")"

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  PASS  %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  FAIL  %s\n          -> %s\n' "$1" "$2"; }

# The historical (broken) command, frozen as a fixture so the suite can prove it
# is actually discriminating between old and new behaviour.
OLD_CMD=$(cat "$(dirname "$0")/fixtures/undeployed-hook-pre-2026-08-17.txt")

# The CURRENT command is extracted from the shipped asset, never copied — a
# copy would silently drift from what actually runs.
ASSET="${BMAD_HOOKS_ASSET:-$HOME/bmad-method-v6/src/modules/bmm/_module-installer/assets/hooks.json}"
NEW_CMD=$(python3 - "$ASSET" <<'EXTRACT'
import json, sys
def walk(o):
    if isinstance(o, dict):
        c = o.get("command")
        if isinstance(c, str) and "claude-bmad-session-main" in c:
            yield c
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)
cmds = list(walk(json.load(open(sys.argv[1]))))
if len(cmds) != 1:
    sys.exit("expected exactly 1 undeployed-merge hook in the asset, found %d" % len(cmds))
sys.stdout.write(cmds[0])
EXTRACT
)
[ -n "$NEW_CMD" ] || { echo "could not extract the hook from $ASSET"; exit 2; }

# run_hook spawns /bin/bash directly from THIS script (never inside a `( )`
# subshell, which would fork a new pid every call and make $PPID vary per
# invocation — that would silently defeat any PPID-keyed marker). So the PPID
# the hook body observes is this script's own pid, constant for the whole run,
# which is how PPID behaves inside one real session.
HOOK_PPID=$$

make_repo() {
  local d; d=$(mktemp -d)
  mkdir -p "$d/_bmad/bmm/workflows" "$d/.claude"
  git -C "$d" init -q -b main
  git -C "$d" config user.email t@t.t; git -C "$d" config user.name t
  echo a > "$d/f"; git -C "$d" add f; git -C "$d" commit -qm c1
  echo "$d"
}

advance() {
  local d=$1 n=$2 i
  for i in $(seq 1 "$n"); do
    echo "$i" >> "$d/f"; git -C "$d" add f; git -C "$d" commit -qm "adv$i"
  done
}

run_hook() {  # body, repo, session-epoch
  env CLAUDE_CODE_SESSION_ID="$3" /bin/bash -c "cd \"$2\" || exit 0; $1" 2>/dev/null
}

unrate() { rm -f "$1/.claude/.undeployed-warn-last"; }

echo
echo "=== OLD hook — reproduce the defect ==="

repo=$(make_repo)
run_hook "$OLD_CMD" "$repo" 1000 >/dev/null    # an early session stamps the baseline
advance "$repo" 20                              # 20 PRs merge over the following weeks

out=$(run_hook "$OLD_CMD" "$repo" 2000)         # a brand-new session that has done nothing
[ -n "$out" ] && ok "OLD: a fresh session that did nothing still warns (the bug)" \
              || bad "OLD: expected the stale-baseline warning" "(silent)"

printf '%s' "$out" | grep -q "since session start" \
  && ok "OLD: and it claims the movement happened 'since session start'" \
  || bad "OLD: expected the misleading wording" "$out"

unrate "$repo"
out=$(run_hook "$OLD_CMD" "$repo" 3000)         # and again, forever
[ -n "$out" ] && ok "OLD: the warning never clears on later sessions" \
              || bad "OLD: expected a persistent warning" "(silent)"

echo
echo "=== NEW hook — the fix ==="

# G1 — the golden case this fix exists for.
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 1000 >/dev/null
advance "$repo" 20
unrate "$repo"
out=$(run_hook "$NEW_CMD" "$repo" 2000)
[ -z "$out" ] && ok "G1  a new session re-baselines; no warning about prior history" \
              || bad "G1  a new session must not inherit a stale baseline" "$out"

# G2 — the hook's actual job still works.
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 5000 >/dev/null
advance "$repo" 3
unrate "$repo"
out=$(run_hook "$NEW_CMD" "$repo" 5000)
[ -n "$out" ] && ok "G2  movement during the SAME session still warns" \
              || bad "G2  must still fire on real in-session movement" "(silent)"

printf '%s' "$out" | grep -q "moved 3 commit" \
  && ok "G3  the warning reports the commit count (3)" \
  || bad "G3  expected 'moved 3 commit(s)'" "$out"

printf '%s' "$out" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null \
  && ok "G4  emitted payload is valid JSON" \
  || bad "G4  payload must be valid JSON" "$out"

# G5 — no movement, no warning.
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 6000 >/dev/null
unrate "$repo"
out=$(run_hook "$NEW_CMD" "$repo" 6000)
[ -z "$out" ] && ok "G5  no movement -> silent" || bad "G5  expected silence" "$out"

# G6 — a deploy this session suppresses it. The deploy marker is keyed on the
# SAME session id as the baseline; if the two halves disagreed about session
# identity (they used to — one on $PPID, one on the repo) suppression breaks.
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 7000 >/dev/null
advance "$repo" 2
unrate "$repo"
touch "/tmp/claude-bmad-deployed-7000"
out=$(run_hook "$NEW_CMD" "$repo" 7000)
rm -f "/tmp/claude-bmad-deployed-7000"
[ -z "$out" ] && ok "G6  a deploy marker suppresses the warning" \
              || bad "G6  expected silence after a deploy" "$out"

# G7 — the 15-minute rate limit still holds.
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 8000 >/dev/null
advance "$repo" 2
first=$(run_hook "$NEW_CMD" "$repo" 8000)
second=$(run_hook "$NEW_CMD" "$repo" 8000)
{ [ -n "$first" ] && [ -z "$second" ]; } \
  && ok "G7  rate limit — warns once, then quiet inside the window" \
  || bad "G7  expected warn-then-quiet" "first='$first' second='$second'"

# G8 — worktrees exempt.
repo=$(make_repo); wt="$repo/.claude/worktrees/x"
mkdir -p "$wt/_bmad/bmm/workflows" "$wt/.claude"
out=$(run_hook "$NEW_CMD" "$wt" 9000)
[ -z "$out" ] && ok "G8  worktrees stay exempt" || bad "G8  expected exemption" "$out"

# G9 — non-BMAD repo exempt.
d=$(mktemp -d); git -C "$d" init -q -b main
out=$(run_hook "$NEW_CMD" "$d" 9100)
[ -z "$out" ] && ok "G9  non-BMAD repo stays exempt" || bad "G9  expected exemption" "$out"

# G10 — bmad_contract: skip honoured.
repo=$(make_repo); printf 'bmad_contract: skip\n' > "$repo/_bmad/bmm/config.yaml"
run_hook "$NEW_CMD" "$repo" 9200 >/dev/null
advance "$repo" 2
unrate "$repo"
out=$(run_hook "$NEW_CMD" "$repo" 9200)
[ -z "$out" ] && ok "G10 bmad_contract: skip is honoured" || bad "G10 expected skip" "$out"

# G11 — two projects in ONE session keep separate baselines.
r1=$(make_repo); r2=$(make_repo)
run_hook "$NEW_CMD" "$r1" 9300 >/dev/null
run_hook "$NEW_CMD" "$r2" 9300 >/dev/null
advance "$r1" 4
unrate "$r1"; unrate "$r2"
o1=$(run_hook "$NEW_CMD" "$r1" 9300)
o2=$(run_hook "$NEW_CMD" "$r2" 9300)
{ [ -n "$o1" ] && [ -z "$o2" ]; } \
  && ok "G11 per-project baselines don't bleed across repos in one session" \
  || bad "G11 project A should warn, project B should not" "A='$o1' B='$o2'"

# G12 — OLD would have failed G1; pin that the suite is actually discriminating.
repo=$(make_repo)
run_hook "$OLD_CMD" "$repo" 1000 >/dev/null
advance "$repo" 5
unrate "$repo"
old_out=$(run_hook "$OLD_CMD" "$repo" 2000)
repo=$(make_repo)
run_hook "$NEW_CMD" "$repo" 1000 >/dev/null
advance "$repo" 5
unrate "$repo"
new_out=$(run_hook "$NEW_CMD" "$repo" 2000)
{ [ -n "$old_out" ] && [ -z "$new_out" ]; } \
  && ok "G12 same scenario: OLD warns, NEW is silent (suite discriminates)" \
  || bad "G12 suite must separate old from new" "old='$old_out' new='$new_out'"

echo
printf 'RESULT: %d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
