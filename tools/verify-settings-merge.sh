#!/usr/bin/env bash
# verify-settings-merge.sh — regression suite for sync-bmad-workflows.sh's settings
# merge: JQ_MERGE (hooks -> tracked .claude/settings.json) and JQ_LOCAL (permissions
# and the MCP flag -> gitignored .claude/settings.local.json, demoting fork hooks).
#
# WHY THIS EXISTS. On 2026-08-16 the merge was measured against the live hook template
# with a disposable fixture and found to REPLACE a project's permissions block wholesale:
#   permissions.allow  (3 entries) -> DROPPED
#   permissions.deny   (1 entry)  -> DROPPED
#   permissions.defaultMode       -> ESCALATED acceptEdits -> bypassPermissions
# Losing a deny list and widening the permission mode are both safety regressions, and
# neither appeared in the sync's output. Cause: `.permissions = ($template.permissions //
# .permissions // {})` — the template object is truthy, so `//` returned it every time.
# Fix: `(($template.permissions // {}) * (.permissions // {}))` — template supplies
# DEFAULTS, the project WINS (jq's recursive `*` resolves right-side-last).
#
# AND ON 2026-09-21 the same kind of defect was caught here BEFORE it shipped, when the
# merge was split so hooks land in a TRACKED file (docs/hooks-registry.md). Two bugs, both
# found by running the merge against a throwaway copy of a real project rather than a
# toy fixture:
#   1. `$c | contains(.)` — inside a filter argument, `.` is re-bound to the filter's
#      own input, so the script-ownership test read `$c | contains($c)` and was TRUE for
#      every hook in the fleet. Every project hook would have been deleted.
#   2. Even once that was fixed, stripping at GROUP level destroyed project hooks that
#      merely shared a group with a fork one: one PreToolUse group in
#      amazon-removal-assistant holds two fork guards beside four of the project's.
#      Measured loss before the fix: 26 project-authored guards. Ownership is now tested
#      at hook level for the script key and group level for the name/command keys.
# L1-L4 below are the cases those two bugs would fail.
#
# THE SUITE EXTRACTS BOTH PROGRAMS VERBATIM FROM sync-bmad-workflows.sh — same discipline
# as tools/verify-policy-freshness-gate.sh — so it can never certify a drifted copy of
# the logic it claims to test.
#
# Run:  bash tools/verify-settings-merge.sh
set -uo pipefail
FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$FORK/sync-bmad-workflows.sh"
TEMPLATE="$FORK/src/modules/bmm/_module-installer/assets/hooks.json"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT"   ]] || { echo "FAIL: missing $SCRIPT"; exit 2; }
[[ -f "$TEMPLATE" ]] || { echo "FAIL: missing $TEMPLATE"; exit 2; }

# X1/X2 run FIRST and fail fast. Extracting the jq text proves nothing about whether the
# SCRIPT still parses: on 2026-08-16 an apostrophe in a comment inside JQ_MERGE (a
# single-quoted bash string) terminated the quote, turned the rest of the block into shell
# code, and broke the sync at HEAD — while this suite stayed 11/11 green, because awk
# extraction cannot see a quoting error. Text validity and script validity are two things.
if bash -n "$SCRIPT" 2>/dev/null; then echo "PASS X1 sync script parses (bash -n)"
else echo "FAIL X1 sync script does NOT parse — bash -n:"; bash -n "$SCRIPT"; exit 1; fi

# Verbatim extraction — the whole point.
awk "/^JQ_MERGE='/{f=1;next} f&&/^'/{exit} f{print}" "$SCRIPT" > "$TMP/jq.txt"
awk "/^JQ_LOCAL='/{f=1;next} f&&/^'/{exit} f{print}" "$SCRIPT" > "$TMP/jqlocal.txt"
[[ -s "$TMP/jq.txt" ]]      || { echo "FAIL: could not extract JQ_MERGE from $SCRIPT"; exit 2; }
[[ -s "$TMP/jqlocal.txt" ]] || { echo "FAIL: could not extract JQ_LOCAL from $SCRIPT"; exit 2; }

if grep -q "'" "$TMP/jq.txt" "$TMP/jqlocal.txt"; then
  echo "FAIL X2 apostrophe inside a single-quoted jq block:"
  grep -n "'" "$TMP/jq.txt" "$TMP/jqlocal.txt"; exit 1
else echo "PASS X2 no apostrophe inside either single-quoted jq block"; fi

# X3 — the two programs share three definitions and MUST agree. Two copies of one rule
# in two languages is how a demotion and a merge drift apart and leave a hook in BOTH
# files, which the harness concatenates, so it fires twice.
defs() { sed -n '/^  def owned_hook:/,/^  def prune:/p' "$1"; sed -n '/^  def prune:/,/select((.hooks | length) > 0) \]/p' "$1"; }
if diff <(defs "$TMP/jq.txt") <(defs "$TMP/jqlocal.txt") >/dev/null; then
  echo "PASS X3 JQ_MERGE and JQ_LOCAL share an identical ownership definition"
else
  echo "FAIL X3 the ownership definitions have drifted between JQ_MERGE and JQ_LOCAL:"
  diff <(defs "$TMP/jq.txt") <(defs "$TMP/jqlocal.txt"); exit 1
fi

merge()  { jq -n "$(cat "$TMP/jq.txt")"      "$1" "$TEMPLATE"; }
local_m() { jq -n "$(cat "$TMP/jqlocal.txt")" "$1" "$TEMPLATE"; }

# A statusMessage that really exists in the template — the collision case needs a true
# collision, not an invented string.
COLLIDE="$(jq -r '[.hooks[]?[]?.hooks[]?.statusMessage // empty] | .[0] // ""' "$TEMPLATE")"

cat > "$TMP/base.json" <<JSON
{
  "permissions": {
    "allow": ["Bash(git *)", "Bash(npm run test)", "Read(~/notes/**)"],
    "deny": ["Bash(rm -rf *)"],
    "defaultMode": "acceptEdits"
  },
  "enableAllProjectMcpServers": false,
  "hooks": {
    "PostToolUse": [
      {"name": "local-only-formatter", "matcher": "Write|Edit",
       "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/auto-format.sh"}]},
      {"name": "local-collider", "matcher": "Write",
       "hooks": [{"type": "command", "command": "true", "statusMessage": "${COLLIDE}"}]}
    ],
    "Stop": [
      {"name": "local-stop-guard", "hooks": [{"type": "command", "command": "true"}]}
    ]
  }
}
JSON
echo '{"hooks":{}}' > "$TMP/empty.json"
# Explicit-true project: proves the fix preserves an affirmative local choice too, not
# just the `false` that exposed the defect.
echo '{"hooks":{},"enableAllProjectMcpServers":true}' > "$TMP/mcptrue.json"

merge "$TMP/base.json"      > "$TMP/out.json"   || { echo "FAIL: merge errored on base";  exit 1; }
merge "$TMP/empty.json"     > "$TMP/oute.json"  || { echo "FAIL: merge errored on empty"; exit 1; }
local_m "$TMP/base.json"    > "$TMP/loc.json"   || { echo "FAIL: local merge errored on base"; exit 1; }
local_m "$TMP/empty.json"   > "$TMP/loce.json"  || { echo "FAIL: local merge errored on empty"; exit 1; }
local_m "$TMP/mcptrue.json" > "$TMP/loct.json"  || { echo "FAIL: local merge errored on mcptrue"; exit 1; }

# --- L1-L4: THE SPLIT, AND THE DATA LOSS IT NEARLY CAUSED --------------------
# A project fixture in the shape that broke it: one group mixing two fork-owned scripts
# with two of the project's own, plus a group of purely project hooks.
FORK_SCRIPT="$(jq -r '.bmadTrackedHookScripts[0] // "stash-untracked-guard.py"' "$TEMPLATE")"
FORK_SCRIPT2="$(jq -r '.bmadTrackedHookScripts[1] // "claude-md-drift.py"' "$TEMPLATE")"
cat > "$TMP/mixed.json" <<JSON
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3 \$R/.claude/hooks/${FORK_SCRIPT}"},
        {"type": "command", "command": "python3 \$R/.claude/hooks/project-only-a.py"},
        {"type": "command", "command": "python3 \$R/.claude/hooks/${FORK_SCRIPT2}"},
        {"type": "command", "command": "python3 \$R/.claude/hooks/project-only-b.py"}
      ]},
      {"matcher": "Edit", "hooks": [
        {"type": "command", "command": "python3 \$R/.claude/hooks/project-only-c.py"}
      ]}
    ]
  }
}
JSON
merge "$TMP/mixed.json" > "$TMP/mixedout.json" || { echo "FAIL: merge errored on mixed"; exit 1; }

kept() { jq --arg s "$1" '[.. | objects | select(has("command")) | select(.command | contains($s))] | length' "$2"; }
L_FAIL=0
for s in project-only-a.py project-only-b.py project-only-c.py; do
  n=$(kept "$s" "$TMP/mixedout.json")
  if [[ "$n" == "1" ]]; then echo "PASS L1 project hook $s survives a group it shares with fork hooks"
  else echo "FAIL L1 project hook $s: $n copies after merge (want 1)"; L_FAIL=1; fi
done
# The fork's own hooks appear exactly once — the hand-wired copy is reclaimed, the
# template copy lands, and the total is one. This is the double-fire case.
for s in "$FORK_SCRIPT" "$FORK_SCRIPT2"; do
  n=$(kept "$s" "$TMP/mixedout.json")
  if [[ "$n" == "1" ]]; then echo "PASS L2 hand-wired fork hook $s ends up wired exactly once"
  else echo "FAIL L2 fork hook $s: $n copies after merge (want 1 — it would fire $n times)"; L_FAIL=1; fi
done
# L3 — the tracked file must never carry the trust settings.
if [[ "$(jq 'has("permissions")' "$TMP/oute.json")" == "false" \
   && "$(jq 'has("enableAllProjectMcpServers")' "$TMP/oute.json")" == "false" ]]; then
  echo "PASS L3 tracked settings.json carries NO permissions and NO MCP auto-enable flag"
else
  echo "FAIL L3 the tracked file picked up a trust setting — bypassPermissions must not be committed:"
  jq '{permissions, enableAllProjectMcpServers}' "$TMP/oute.json"; L_FAIL=1
fi
# L4 — the ownership declaration is machinery and must not reach a settings file.
if [[ "$(jq 'has("bmadTrackedHookScripts")' "$TMP/oute.json")" == "false" \
   && "$(jq 'has("bmadTrackedHookScripts")' "$TMP/loce.json")" == "false" ]]; then
  echo "PASS L4 bmadTrackedHookScripts never lands in a project settings file"
else echo "FAIL L4 the template manifest key leaked into a settings file"; L_FAIL=1; fi
# L5 — DEMOTION: JQ_LOCAL strips every fork-owned hook and keeps the project's.
local_m "$TMP/mixed.json" > "$TMP/mixedloc.json" || { echo "FAIL: local merge errored on mixed"; exit 1; }
d_fork=$(( $(kept "$FORK_SCRIPT" "$TMP/mixedloc.json") + $(kept "$FORK_SCRIPT2" "$TMP/mixedloc.json") ))
d_proj=$(( $(kept project-only-a.py "$TMP/mixedloc.json") + $(kept project-only-c.py "$TMP/mixedloc.json") ))
if [[ "$d_fork" == "0" && "$d_proj" == "2" ]]; then
  echo "PASS L5 demotion removes fork hooks from settings.local.json and keeps the project's"
else
  echo "FAIL L5 demotion wrong — fork hooks left: $d_fork (want 0), project hooks kept: $d_proj (want 2)"; L_FAIL=1
fi
[[ "$L_FAIL" == "1" ]] && { echo; echo "FAILURES: split/data-loss cases (L1-L5) — see above."; exit 1; }

# --- I1-I3: CONVERGENCE (FG-2026-08-31-03) ----------------------------------
# The merge must RECOGNISE an already-installed template hook, or it appends a second
# copy every sync and --check can never go green. The identity key was statusMessage
# alone, so a template hook carrying none was invisible to it. Measured 2026-08-31:
# inbound-flow had accumulated four copies of the same statusMessage-less hook.
#
# I1/I2 run against a SYNTHETIC template that is guaranteed to contain a
# statusMessage-less hook, so the case cannot quietly go vacuous if the shipped
# template later gives every hook a label. I3 then pins the same property on the
# template that actually ships.
merge_with() { jq -n "$(cat "$TMP/jq.txt")" "$1" "$2"; }

cat > "$TMP/tmpl-nostatus.json" <<'JSON'
{
  "hooks": {
    "PostToolUse": [
      {"matcher": "Skill",
       "hooks": [{"type": "command", "command": "echo no-status-message-here"}]},
      {"matcher": "Bash",
       "hooks": [{"type": "command", "command": "echo labelled", "statusMessage": "Labelled hook..."}]}
    ]
  }
}
JSON
echo '{"hooks":{}}' > "$TMP/fresh.json"

merge_with "$TMP/fresh.json" "$TMP/tmpl-nostatus.json" > "$TMP/i1.json" \
  || { echo "FAIL I1 merge errored on a fresh project"; exit 1; }
merge_with "$TMP/i1.json"    "$TMP/tmpl-nostatus.json" > "$TMP/i2.json" \
  || { echo "FAIL I2 merge errored on the second pass"; exit 1; }
merge_with "$TMP/i2.json"    "$TMP/tmpl-nostatus.json" > "$TMP/i3.json" \
  || { echo "FAIL I2 merge errored on the third pass"; exit 1; }

n1=$(jq '[.. | objects | select(.command == "echo no-status-message-here")] | length' "$TMP/i1.json")
n2=$(jq '[.. | objects | select(.command == "echo no-status-message-here")] | length' "$TMP/i2.json")
n3=$(jq '[.. | objects | select(.command == "echo no-status-message-here")] | length' "$TMP/i3.json")

if [[ "$n1" == "1" && "$n2" == "1" && "$n3" == "1" ]]; then
  echo "PASS I1 a statusMessage-less hook is recognised as already present (1 copy after 1, 2 and 3 syncs)"
else
  echo "FAIL I1 statusMessage-less hook duplicated across syncs — copies: $n1, $n2, $n3"; CONV_FAIL=1
fi

if diff <(jq -S . "$TMP/i1.json") <(jq -S . "$TMP/i2.json") >/dev/null \
&& diff <(jq -S . "$TMP/i2.json") <(jq -S . "$TMP/i3.json") >/dev/null; then
  echo "PASS I2 hook configuration is byte-stable from the second sync onward"
else
  echo "FAIL I2 a second sync still changes the settings file:"
  diff <(jq -S . "$TMP/i1.json") <(jq -S . "$TMP/i2.json") | head -20; CONV_FAIL=1
fi

# I3 — same property, against the template that actually ships. This is what makes
# `--check` able to report hooks (outdated) truthfully rather than by construction.
merge "$TMP/empty.json"  > "$TMP/live1.json"
merge_with "$TMP/live1.json" "$TEMPLATE" > "$TMP/live2.json"
if diff <(jq -S . "$TMP/live1.json") <(jq -S . "$TMP/live2.json") >/dev/null; then
  echo "PASS I3 the SHIPPED template reaches a fixed point after one sync"
else
  echo "FAIL I3 the shipped template never converges — a second sync still differs:"
  diff <(jq -S . "$TMP/live1.json") <(jq -S . "$TMP/live2.json") | head -20; CONV_FAIL=1
fi

# I4 — the same property for the LOCAL file. A demotion that is not idempotent would
# rewrite settings.local.json on every sync and keep --check permanently red.
local_m "$TMP/base.json" > "$TMP/lc1.json"
local_m "$TMP/lc1.json"  > "$TMP/lc2.json"
if diff <(jq -S . "$TMP/lc1.json") <(jq -S . "$TMP/lc2.json") >/dev/null; then
  echo "PASS I4 the demotion is idempotent — a second pass changes nothing"
else
  echo "FAIL I4 demotion is not idempotent:"; diff <(jq -S . "$TMP/lc1.json") <(jq -S . "$TMP/lc2.json") | head -20; CONV_FAIL=1
fi

if [[ "${CONV_FAIL:-0}" == "1" ]]; then
  echo; echo "FAILURES: convergence cases (I1-I4) — see above."; exit 1
fi

COLLIDE="$COLLIDE" python3 - "$TMP" <<'PY'
import json, os, sys
t = sys.argv[1]
base = json.load(open(f"{t}/base.json")); out = json.load(open(f"{t}/out.json"))
loc  = json.load(open(f"{t}/loc.json"));  loce = json.load(open(f"{t}/loce.json"))
collide = os.environ.get("COLLIDE", "")
bp, op = base["permissions"], loc.get("permissions", {})
post = out.get("hooks", {}).get("PostToolUse", [])
names = [e.get("name") for e in post]
fails = []
def check(label, got, want):
    print(("PASS " if got == want else "FAIL ") + label + (f"   got={got!r} want={want!r}" if got != want else ""))
    if got != want: fails.append(label)

# --- the permissions contract (the defect this suite exists for) -------------
# These now live in settings.local.json, so they are asserted against JQ_LOCAL.
check("P1 allow preserved",                      op.get("allow"), bp["allow"])
check("P2 deny preserved",                       op.get("deny"), bp["deny"])
check("P3 restrictive defaultMode not widened",  op.get("defaultMode"), "acceptEdits")
check("P4 template default applies when project has none",
      loce.get("permissions", {}).get("defaultMode"), "bypassPermissions")

# --- hook merge behaviour (tracked file) -------------------------------------
check("H1 local non-bmad hook survives",         "local-only-formatter" in names, True)
check("H2 template bmad- hooks merge in",        len([n for n in names if (n or "").startswith("bmad-")]) > 0, True)
check("H3 base-only event untouched (Stop) keeps its project hook",
      "local-stop-guard" in [e.get("name") for e in out.get("hooks", {}).get("Stop", [])], True)

# --- the collision case: statusMessage is a SECOND identity field ------------
# Documented behaviour, not aspiration: a locally-named hook whose statusMessage
# matches a template hook's is DROPPED even though its name is not bmad-.
if collide:
    check("H4 statusMessage collision drops a local hook (KNOWN LIMITATION)",
          "local-collider" in names, False)
else:
    print("SKIP H4 — template exposes no statusMessage to collide against")

# --- other structured fields -------------------------------------------------
# S1-S3: the MCP-server contract. The template ships `enableAllProjectMcpServers: true`,
# and the old `//` shape meant a project's explicit `false` was silently flipped to `true`
# on every sync — auto-enabling project-scoped MCP servers against the project's stated
# choice. `has()` now distinguishes "explicitly false" from "absent"; only absent defaults.
# (The first cut of S1 used `true` in the fixture and therefore could not tell preservation
#  from override — a test that could not fail. Corrected 2026-08-16.)
check("S1 explicit project false stays false",
      loc.get("enableAllProjectMcpServers"), False)
check("S2 explicit project true stays true",
      json.load(open(f"{t}/loct.json")).get("enableAllProjectMcpServers"), True)
check("S3 absent field receives the template default",
      loce.get("enableAllProjectMcpServers"), True)

print()
if fails:
    print(f"FAILURES: {len(fails)} -> " + ", ".join(fails)); sys.exit(1)
print("ALL GREEN — split, data-loss, permissions contract, hook merge, collision case, structured fields.")
PY
