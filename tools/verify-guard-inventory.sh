#!/usr/bin/env bash
# Fixture test for guard-wiring-check.sh's project-data inventory.
# Proves BOTH branches: declared inventory fires; absent inventory falls back
# without regressing (the fallback name is skipped when the project lacks it).
set -uo pipefail

CHECK="$1"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

mk() { # $1=name  -> a minimal project with a wired reviewed guard
  local p="$TMP/$1"
  mkdir -p "$p/.claude/hooks"
  : > "$p/.claude/hooks/bash_edit_guard.py"
  printf '{"hooks":{"PreToolUse":[{"hooks":[{"command":"bash_edit_guard.py"}]}]}}' \
    > "$p/.claude/settings.json"
  echo "$p"
}

fails=0
say() { printf '%-58s %s\n' "$1" "$2"; }

# --- A: inventory declares a guard that is merged but registered nowhere ---
A=$(mk a)
: > "$A/.claude/hooks/some-guard.py"
echo "some-guard.py" > "$A/.claude/guard-inventory.txt"
outA=$(CLAUDE_PROJECT_DIR="$A" bash "$CHECK" 2>&1)
if printf '%s' "$outA" | grep -q "some-guard.py is merged but registered in NEITHER"; then
  say "A declared+merged+unwired -> reported" "PASS"
else
  say "A declared+merged+unwired -> reported" "FAIL"; printf '   got: %s\n' "$outA"; fails=1
fi

# --- B: same guard merged, but NOT declared -> not this check's business ---
B=$(mk b)
: > "$B/.claude/hooks/some-guard.py"
echo "# nothing declared" > "$B/.claude/guard-inventory.txt"
outB=$(CLAUDE_PROJECT_DIR="$B" bash "$CHECK" 2>&1)
if [ -z "$outB" ]; then
  say "B merged but undeclared -> silent" "PASS"
else
  say "B merged but undeclared -> silent" "FAIL"; printf '   got: %s\n' "$outB"; fails=1
fi

# --- C: NO inventory file -> falls back; fallback name absent -> silent ---
C=$(mk c)
outC=$(CLAUDE_PROJECT_DIR="$C" bash "$CHECK" 2>&1)
if [ -z "$outC" ]; then
  say "C no inventory file -> fallback, silent" "PASS"
else
  say "C no inventory file -> fallback, silent" "FAIL"; printf '   got: %s\n' "$outC"; fails=1
fi

# --- D: NO inventory file, fallback guard PRESENT and unwired -> reported ---
#     This is the no-regression case: cash-recovery ships no inventory file and
#     must keep its operator-path-guard.py check.
D=$(mk d)
: > "$D/.claude/hooks/operator-path-guard.py"
outD=$(CLAUDE_PROJECT_DIR="$D" bash "$CHECK" 2>&1)
if printf '%s' "$outD" | grep -q "operator-path-guard.py is merged but registered in NEITHER"; then
  say "D no inventory, fallback present -> reported" "PASS"
else
  say "D no inventory, fallback present -> reported" "FAIL"; printf '   got: %s\n' "$outD"; fails=1
fi

# --- E: comments and blank lines ignored ---
E=$(mk e)
: > "$E/.claude/hooks/some-guard.py"
printf '# a comment\n\n   \nsome-guard.py\n' > "$E/.claude/guard-inventory.txt"
outE=$(CLAUDE_PROJECT_DIR="$E" bash "$CHECK" 2>&1)
if printf '%s' "$outE" | grep -q "some-guard.py is merged but registered in NEITHER"; then
  say "E comments/blanks ignored" "PASS"
else
  say "E comments/blanks ignored" "FAIL"; printf '   got: %s\n' "$outE"; fails=1
fi

echo
[ "$fails" -eq 0 ] && echo "all inventory cases passed" || echo "FAILURES PRESENT"
exit "$fails"
