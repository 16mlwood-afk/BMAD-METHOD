#!/usr/bin/env bash
# SessionStart — prod-readiness probe (Phase 1, WARN-ONLY).
#
# AWARENESS tier of prod-readiness-charter.md for a LIVE project: warns (never blocks)
# on a deploy-doc gap (State 2) and/or a memory-discipline gap (§4). Detection is the
# shared pr_* library, so it can never diverge from the deploy gate. Conservative:
# silent unless clearly live AND a domain has zero signals.
. "$(dirname "$0")/lib/prod-readiness-detect.sh" 2>/dev/null || exit 0

start="${CLAUDE_PROJECT_DIR:-$PWD}"
root=$(pr_find_root "$start") || exit 0   # not a BMAD project → no-op
pr_is_live "$root" || exit 0              # greenfield / not live → no-op

proj=$(basename "$root"); phase=$(pr_phase "$root"); out=""
pr_has_deploy_doc "$root" "$start" || out="${out}⚠ PROD-READINESS (warn-only): ${proj} is project_phase=${phase} (live) but has NO deploy contract/doc — no \`deploy:\` block, no scripts/bmad-deploy.sh, no CLAUDE.md deploy section, no docs/*deploy*. Author one before any production deploy (prod-readiness-charter.md State 2).
"
pr_has_memory "$root" "$start" || out="${out}⚠ PROD-READINESS (warn-only): ${proj} is live but has NO memory discipline — no project MEMORY.md and no memory section in CLAUDE.md (prod-readiness-charter.md §4).
"
[ -n "$out" ] && printf '%s' "$out"
exit 0
