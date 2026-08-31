#!/usr/bin/env bash
# verify-settings-merge.sh — regression suite for sync-bmad-workflows.sh's JQ_MERGE.
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
# THE SUITE EXTRACTS JQ_MERGE VERBATIM FROM sync-bmad-workflows.sh — same discipline as
# tools/verify-policy-freshness-gate.sh — so it can never certify a drifted copy of the
# logic it claims to test.
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
[[ -s "$TMP/jq.txt" ]] || { echo "FAIL: could not extract JQ_MERGE from $SCRIPT"; exit 2; }

if grep -q "'" "$TMP/jq.txt"; then
  echo "FAIL X2 apostrophe inside JQ_MERGE — it is a single-quoted bash string:"
  grep -n "'" "$TMP/jq.txt"; exit 1
else echo "PASS X2 no apostrophe inside the single-quoted JQ_MERGE block"; fi

merge() { jq -n "$(cat "$TMP/jq.txt")" "$1" "$TEMPLATE"; }

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

merge "$TMP/base.json"    > "$TMP/out.json"   || { echo "FAIL: merge errored on base";  exit 1; }
merge "$TMP/empty.json"   > "$TMP/oute.json"  || { echo "FAIL: merge errored on empty"; exit 1; }
merge "$TMP/mcptrue.json" > "$TMP/outt.json"  || { echo "FAIL: merge errored on mcptrue"; exit 1; }

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

if [[ "${CONV_FAIL:-0}" == "1" ]]; then
  echo; echo "FAILURES: convergence cases (I1-I3) — see above."; exit 1
fi

COLLIDE="$COLLIDE" python3 - "$TMP" <<'PY'
import json, os, sys
t = sys.argv[1]
base = json.load(open(f"{t}/base.json")); out = json.load(open(f"{t}/out.json"))
empt = json.load(open(f"{t}/oute.json"))
collide = os.environ.get("COLLIDE", "")
bp, op = base["permissions"], out.get("permissions", {})
post = out.get("hooks", {}).get("PostToolUse", [])
names = [e.get("name") for e in post]
fails = []
def check(label, got, want):
    print(("PASS " if got == want else "FAIL ") + label + (f"   got={got!r} want={want!r}" if got != want else ""))
    if got != want: fails.append(label)

# --- the permissions contract (the defect this suite exists for) -------------
check("P1 allow preserved",                      op.get("allow"), bp["allow"])
check("P2 deny preserved",                       op.get("deny"), bp["deny"])
check("P3 restrictive defaultMode not widened",  op.get("defaultMode"), "acceptEdits")
check("P4 template default applies when project has none",
      empt.get("permissions", {}).get("defaultMode"), "bypassPermissions")

# --- hook merge behaviour ----------------------------------------------------
check("H1 local non-bmad hook survives",         "local-only-formatter" in names, True)
check("H2 template bmad- hooks merge in",        len([n for n in names if (n or "").startswith("bmad-")]) > 0, True)
check("H3 base-only event untouched (Stop)",
      [e.get("name") for e in out.get("hooks", {}).get("Stop", [])], ["local-stop-guard"])

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
      out.get("enableAllProjectMcpServers"), False)
check("S2 explicit project true stays true",
      json.load(open(f"{t}/outt.json")).get("enableAllProjectMcpServers"), True)
check("S3 absent field receives the template default",
      empt.get("enableAllProjectMcpServers"), True)

print()
if fails:
    print(f"FAILURES: {len(fails)} -> " + ", ".join(fails)); sys.exit(1)
print("ALL GREEN — permissions contract, hook merge, collision case, structured fields.")
PY
