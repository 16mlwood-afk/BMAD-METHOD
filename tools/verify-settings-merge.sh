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

# Verbatim extraction — the whole point.
awk "/^JQ_MERGE='/{f=1;next} f&&/^'/{exit} f{print}" "$SCRIPT" > "$TMP/jq.txt"
[[ -s "$TMP/jq.txt" ]] || { echo "FAIL: could not extract JQ_MERGE from $SCRIPT"; exit 2; }

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
