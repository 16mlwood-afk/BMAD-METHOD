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
MSG=""
if [ "${hits:-0}" -ge 3 ]; then
  MSG="CLAUDE.md drift: this project's CLAUDE.md matches ${hits} shared-doctrine signals — it may be RESTATING shared standards instead of pointing at them. Consider thinning it per STD-CLAUDE-001 (point to STD-* by ID; see shared/claude-md-standard.md + the cash-recovery reference)."
fi

# Stale sweep stamp (owner ruling 10 Nov 2026): a swept project CLAUDE.md is re-swept at least every
# 90 days. Warn-only, and repeated EVERY session while true (a standing condition, never "shown once").
# The date arithmetic lives in the one checker script; if it cannot be read, say so (never silent).
case "$(head -n 30 "$F" 2>/dev/null)" in
  *"Swept on "*)
    CHECKER="${CLAUDE_MD_SWEEP_CHECKER:-$HOME/.claude/scripts/claude-md-sweep/claude-md-tag-check.py}"
    STALE_MSG=""
    if [ -f "$CHECKER" ] && command -v python3 >/dev/null 2>&1; then
      AGE=$(python3 "$CHECKER" --file "$F" --stamp-age-days 2>&1)
      RC=$?
      if [ "$RC" -eq 0 ] && [ "${AGE:-0}" -gt 90 ] 2>/dev/null; then
        STALE_MSG="CLAUDE.md sweep is STALE: the 'Swept on' stamp is ${AGE} days old (limit 90). Re-sweep this project's CLAUDE.md with ~/.claude/docs/claude-md-sweep-method.md, then update the stamp."
      elif [ "$RC" -ne 0 ]; then
        STALE_MSG="CLAUDE.md sweep stamp: COULD NOT CHECK its age — ${AGE}"
      fi
    else
      STALE_MSG="CLAUDE.md sweep stamp: COULD NOT CHECK its age — checker script (${CHECKER}) or python3 not available."
    fi
    if [ -n "$STALE_MSG" ]; then
      MSG="${MSG:+$MSG }$STALE_MSG"
    fi
    ;;
esac

[ -n "$MSG" ] && emit "$MSG"
exit 0
