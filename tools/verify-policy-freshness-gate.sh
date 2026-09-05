#!/usr/bin/env bash
# Golden matrix for design-handoff §1b's POLICY FRESHNESS GATE.
#
# WHY THIS IS A SCRIPT AND NOT A PARAGRAPH
# ----------------------------------------
# The gate is prose in a workflow file, executed by a model, and it fans out to 13
# projects. Owner standing rule (2026-07-29): *never rely on prose alone for a gate that
# touches many projects; when a gate's failure mode is indistinguishable from its trigger,
# treat it as broken until a concrete multi-case check has passed.*
#
# The first cut of this gate earned that rule. It was:
#     git fetch -q origin 2>/dev/null
#     git diff --quiet origin/HEAD -- <path> || echo STALE
# which (1) never consulted `git fetch`'s exit code, making its own documented offline
# branch unreachable, and (2) turned `fatal: bad revision` — the check COULD NOT RUN —
# into "STALE", the check ran and found divergence. Measured: it halted a disconnected
# session, and reported STALE for a tree that was actually current.
#
# The gate body below is EXTRACTED FROM THE WORKFLOW FILE AT RUN TIME, never retyped, so
# this check cannot pass against a copy that has drifted from the doc it certifies.
#
# Run: bash tools/verify-policy-freshness-gate.sh
set -uo pipefail

FORK="$(cd "$(dirname "$0")/.." && pwd)"
STEP="$FORK/custom/workflows/design/design-handoff/steps/step-01-gather.md"
POLICY="docs/design-policy.md"

[ -f "$STEP" ] || { echo "FATAL: step file not found: $STEP"; exit 2; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

# --- extract the gate verbatim ----------------------------------------------------
python3 - "$STEP" "$WORK/gate.sh" <<'PY'
import sys
step, out = sys.argv[1], sys.argv[2]
src = open(step, encoding='utf-8').read()
i = src.find('# FOUR outcomes')
if i == -1:
    sys.exit("FATAL: could not find the gate body ('# FOUR outcomes') in the step file. "
             "If the gate was rewritten, update this extractor deliberately — do NOT "
             "let the check silently certify nothing.")
j = src.find('```', i)
body = src[i:j]
body = '\n'.join(l[2:] if l.startswith('  ') else l for l in body.split('\n'))
body = body.replace('<resolved policy path>', '"$POLICY"')
open(out, 'w').write('gate() {\n' + body + '\n}\n')
PY
# shellcheck source=/dev/null
source "$WORK/gate.sh"

pass=0; fail=0
check() {  # expected label description
  local got; got=$(gate)
  if [ "$got" = "$1" ]; then
    printf '  \033[32mPASS\033[0m  %-3s %-34s -> %s\n' "$2" "$3" "$got"; pass=$((pass+1))
  else
    printf '  \033[31mFAIL\033[0m  %-3s %-34s -> %s (expected %s)\n' "$2" "$3" "$got" "$1"; fail=$((fail+1))
  fi
}

mkdir -p "$WORK/up" && cd "$WORK/up"
git init -q -b main .; git config user.email t@t; git config user.name t
mkdir -p docs && printf -- '---\nversion: 18\n---\n' > "$POLICY"
git add -A && git commit -qm v18

cd "$WORK" && git clone -q up A && cd A
git config user.email t@t; git config user.name t; git remote set-head origin -a >/dev/null 2>&1

echo
echo "policy-freshness gate · matrix (gate body extracted verbatim from step-01-gather.md §1b)"
echo
check CLEAN A "online, tree current"

cd "$WORK/up"; printf -- '---\nversion: 21\n---\n' > "$POLICY"; git add -A; git commit -qm v21
cd "$WORK/A"
check STALE B "online, genuinely behind"

git remote set-url origin "file://$WORK/NOPE"
check OFFLINE-STALE C "offline, behind last-known ref"

cd "$WORK" && git clone -q up D && cd D
git config user.email t@t; git config user.name t; git remote set-head origin -a >/dev/null 2>&1
git fetch -q origin 2>/dev/null; git remote set-url origin "file://$WORK/NOPE"
check OFFLINE-MATCHES-LAST-KNOWN D "offline, matches last-known ref"

# D' — the reason D is not called CLEAN.
cd "$WORK/up"; printf -- '---\nversion: 22\n---\n' > "$POLICY"; git add -A; git commit -qm v22
cd "$WORK/D"
check OFFLINE-MATCHES-LAST-KNOWN "D'" "offline, remote MOVED since last fetch"

cd "$WORK" && git clone -q up E && cd E
git config user.email t@t; git config user.name t
git update-ref -d refs/remotes/origin/HEAD 2>/dev/null
git remote set-url origin "file://$WORK/NOPE"
check OFFLINE-NO-REF E "offline, no ref at all"

echo
if [ "$fail" -eq 0 ]; then
  echo "  $pass/$((pass+fail)) PASS."
  echo "  D and D' are DELIBERATELY identical: offline, a tree matching its last-known ref"
  echo "  is byte-identical whether the remote has moved or not. That is why D is reported"
  echo "  as OFFLINE-MATCHES-LAST-KNOWN and never as CLEAN — a CLEAN there would stamp"
  echo "  policy_version_required at full confidence and skip the Open Question, which is"
  echo "  the original defect re-created through a label."
else
  echo "  $fail FAILURE(S) — the gate does not match its contract. Do NOT queue the fleet batch."
fi
exit $(( fail > 0 ? 1 : 0 ))
