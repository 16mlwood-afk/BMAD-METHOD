#!/usr/bin/env bash
# PostToolUse(EnterWorktree) — bootstrap a fresh worktree's VERIFIABILITY.
#
# A new worktree shares tracked files but NOT generated state, so a SvelteKit
# project's ambient types ($app / $lib / $types, and the .svelte-kit/tsconfig.json
# the root tsconfig `extends`) are absent until `svelte-kit sync` runs. Until then
# the LSP/tsc emit HUNDREDS of phantom diagnostics (whole stdlib + every internal
# import reads as broken), so the fastest correct instinct — trust the editor's
# red — is the WRONG move on exactly the change a worktree was mandated for.
# Generate the types now so diagnostics are trustworthy from the first edit.
#
# svelte-kit resolves @sveltejs/kit via upward node_modules traversal to the main
# checkout, so this works in a worktree with no node_modules of its own.
#
# Additive AWARENESS/bootstrap — always exits 0, never blocks EnterWorktree.
# Doc: custom/workflows/shared/worktree-portability.md §9. fork-gaps 2026-07-04.
set -u

# Only inside a worktree (PostToolUse fires for EnterWorktree; cwd is the new root).
case "$PWD" in */.claude/worktrees/*) ;; *) exit 0 ;; esac

# Detect a SvelteKit project at the worktree root.
is_svelte=false
if [ -f "$PWD/svelte.config.js" ] || [ -f "$PWD/svelte.config.ts" ]; then
  is_svelte=true
elif [ -f "$PWD/package.json" ] && grep -q '"@sveltejs/kit"' "$PWD/package.json" 2>/dev/null; then
  is_svelte=true
fi
$is_svelte || exit 0

# Already generated → nothing to do.
[ -d "$PWD/.svelte-kit" ] && exit 0

emit() {
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg m "$1" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
  else
    printf '%s\n' "$1"
  fi
}

if ! command -v npx >/dev/null 2>&1; then
  emit "Worktree bootstrap: SvelteKit project whose ambient types (.svelte-kit/) are not generated and npx is unavailable — run \`npx svelte-kit sync\` before trusting LSP/tsc diagnostics (they will otherwise show phantom errors on the whole stdlib + every import). worktree-portability.md §9"
  exit 0
fi

# Run synchronously (usually 1-3s when kit is installed); the ensure_cmd timeout
# (30s) is the backstop. Success = types exist and diagnostics are trustworthy.
if npx svelte-kit sync >/dev/null 2>&1; then
  emit "Worktree bootstrap: generated SvelteKit ambient types (\`svelte-kit sync\`) — LSP/tsc diagnostics are now trustworthy in this worktree. worktree-portability.md §9"
else
  emit "Worktree bootstrap: attempted \`svelte-kit sync\` but it failed (kit may be uninstalled in the resolvable node_modules) — run \`npx svelte-kit sync\` manually before trusting LSP/tsc diagnostics, and remember any sub-package (e.g. an MCP-server dir) needs its own \`npm ci\` before tsc/build passes there. worktree-portability.md §9"
fi
exit 0
