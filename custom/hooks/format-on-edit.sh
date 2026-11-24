#!/usr/bin/env bash
# format-on-edit.sh — PostToolUse(Edit|Write) auto-formatter. Fork-owned:
# delivered from ~/bmad-method-v6/custom/hooks/ by sync-bmad-workflows.sh and
# wired as the "bmad-auto-format" hook. Edit it in the fork, never in a project.
#
# Python files: ruff format, as before.
#
# Prettier files (.ts .tsx .js .jsx .json .css .svelte): formatted ONLY when the
# committed copy of the file (HEAD) is already prettier-clean, or the file has no
# committed copy yet (new file). A repo whose code was never run through prettier
# would otherwise turn a one-line Edit into a whole-file diff (friction
# WF-20260925-059/062). HEAD is checked rather than the working copy because the
# edit has already landed when this runs: a clean file with a sloppy edit would
# fail a working-copy check and never be tidied.
#
# Outside a git repository there is no baseline to check against, so the file is
# left alone rather than formatted whole.
#
# Prettier is looked up in node_modules/.bin of every directory from the file up
# to the repository root (so frontend/ or packages/x/ installs are found without
# naming them), then on PATH, then in the npx cache. If none answers, the hook
# says so on stderr instead of doing nothing silently (WF-20260925-063).
#
# Never blocks and never fails the tool call: always exits 0.

set -u

input=$(cat 2>/dev/null)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$file" ] && file="${CLAUDE_TOOL_INPUT_FILE_PATH:-}"
[ -z "$file" ] && exit 0
[ -f "$file" ] || exit 0

case "$file" in
  *.py)
    ruff format --quiet "$file" 2>/dev/null || .venv/bin/ruff format --quiet "$file" 2>/dev/null
    exit 0
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.svelte) ;;
  *) exit 0 ;;
esac

dir=$(cd "$(dirname "$file")" 2>/dev/null && pwd -P) || exit 0
root=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || exit 0
root=$(cd "$root" 2>/dev/null && pwd -P) || exit 0
# Absolute path, then run from the file's directory so an npx lookup resolves
# against this project rather than whatever directory the hook was started in.
file="$dir/$(basename "$file")"
cd "$dir" || exit 0

prettier_cmd=()
d="$dir"
while :; do
  if [ -x "$d/node_modules/.bin/prettier" ]; then
    prettier_cmd=("$d/node_modules/.bin/prettier")
    break
  fi
  [ "$d" = "$root" ] && break
  case "$d" in "$root"/*) ;; *) break ;; esac
  d=$(dirname "$d")
done
if [ ${#prettier_cmd[@]} -eq 0 ]; then
  if command -v prettier >/dev/null 2>&1; then
    prettier_cmd=(prettier)
  elif npx --no-install prettier --version >/dev/null 2>&1; then
    prettier_cmd=(npx --no-install prettier)
  else
    echo "format-on-edit: no prettier found for $file (no node_modules/.bin/prettier between the file and $root, none on PATH, none in the npx cache); file left unformatted. Add prettier as a devDependency to enable it." >&2
    exit 0
  fi
fi

rel=$(git -C "$root" ls-files --full-name -- "$file" 2>/dev/null)
if [ -n "$rel" ] && git -C "$root" cat-file -e "HEAD:$rel" 2>/dev/null; then
  committed=$(mktemp) || exit 0
  formatted=$(mktemp) || { rm -f "$committed"; exit 0; }
  git -C "$root" show "HEAD:$rel" >"$committed" 2>/dev/null
  if ! "${prettier_cmd[@]}" --stdin-filepath "$file" <"$committed" >"$formatted" 2>/dev/null; then
    # prettier could not parse the committed copy: leave the file alone.
    rm -f "$committed" "$formatted"
    exit 0
  fi
  if ! cmp -s "$committed" "$formatted"; then
    # Committed copy is not prettier-formatted: do not reformat the whole file.
    rm -f "$committed" "$formatted"
    exit 0
  fi
  rm -f "$committed" "$formatted"
fi

"${prettier_cmd[@]}" --write --log-level silent "$file" 2>/dev/null
exit 0
