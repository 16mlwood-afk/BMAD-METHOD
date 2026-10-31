#!/usr/bin/env bash
# SessionStart soft-warn — flags a project CLAUDE.md that is MISSING or looks
# like it RESTATES shared standards (vs being a thin pointer file). Per
# STD-CLAUDE-001. Warn-only, conservative (silent when the CLAUDE.md is thin).
#
# Enforcement class: DETERMINISTIC delivery of awareness; the act of fixing is
# the model/user's choice. Runs at SessionStart in the project cwd.
F="CLAUDE.md"

emit() {
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$1" 2>/dev/null || true
}

# Only act inside what looks like a real project (has a git repo or _bmad).
[ -d .git ] || [ -d _bmad ] || exit 0

if [ ! -f "$F" ]; then
  emit "CLAUDE.md drift: this project has NO CLAUDE.md. Per STD-CLAUDE-001, add a thin pointer-based one (shape: Overview / Dev / Deploy / Memory / Notes; reference shared standards by ID). Reference project: cash-recovery."
  exit 0
fi

# Count shared-doctrine RESTATEMENT signals; thin pointer files won't have them.
#
# The count is line-based, not substring-based, so a correct pointer scores
# differently from a re-derivation (the STD-CLAUDE-001 distinction the detector
# approximates — see shared/claude-md-standard.md):
#   1. Find lines that mention a shared-doctrine signal term.
#   2. DROP the ones that also carry a canonical-home marker — a path/ID/section
#      reference or a pointer lead-phrase. Those NAME where the rule lives (the
#      correct thin-file shape) and must not be counted as drift.
#   3. Case-fold dedup (sort -uf) so a term appearing sentence-initial AND
#      mid-sentence ("Admin-merge" / "admin-merge") counts once, not twice.
# Markers are deliberately high-precision: a bare ".md" is NOT one, because a
# genuine restatement can name a file ("write memory/<slug>.md FIRST"); we only
# treat a reference to a specific canonical-home doc, an STD- id, a § section, a
# _bmad/ path, or a "see/per/follows/rulebook" lead-phrase as a pointer.
signals='memory-library-discipline|memory-retrieval-policy|admin-merge|sender-strict|receiver-lenient|6 intake checks|grounding gate|diagnostics-gate|worktree-portability|prove-don'\''t-assert|exit-code grammar|brief provenance'
pointer_markers='_bmad/|STD-[A-Z]|§|deployment-to-prod\.md|claude-md-standard\.md|[Ss]ee the |[Pp]er the |[Ff]ollows the |rulebook is'
hits=$(grep -iE "$signals" "$F" 2>/dev/null \
        | grep -ivE "$pointer_markers" \
        | grep -ioE "$signals" \
        | sort -uf | wc -l | tr -d ' ')
if [ "${hits:-0}" -ge 3 ]; then
  emit "CLAUDE.md drift: this project's CLAUDE.md matches ${hits} shared-doctrine signals — it may be RESTATING shared standards instead of pointing at them. Consider thinning it per STD-CLAUDE-001 (point to STD-* by ID; see shared/claude-md-standard.md + the cash-recovery reference)."
fi
exit 0
