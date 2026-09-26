#!/usr/bin/env bash
# PreToolUse (Edit|Write) — enforcement-surface nudge.
#
# DETERMINISTIC AWARENESS tier for the `enforcement-expert` skill (its own
# self-application). When an Edit/Write targets an enforcement surface
# (a hook, settings*.json, a CLAUDE.md guardrail), inject a reminder to consult
# the skill. Deliberately a NUDGE (additionalContext), never a deny — hard-
# blocking edits to settings/CLAUDE.md would be the indiscriminate-gate
# anti-pattern. Pure-bash + a single grep: no per-edit subprocess, ~5ms, and a
# no-op for the 99% of edits that don't touch an enforcement surface.
in=$(cat)
if printf '%s' "$in" | grep -qE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*(settings\.json|settings\.local\.json|/\.husky/|/hooks/|CLAUDE\.md)"'; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"You are editing an enforcement surface (hook / settings / CLAUDE.md). Per the global Enforcement Gate: consult the enforcement-expert skill before authoring or changing any mechanism meant to make a context-free agent comply. Classify each tier DETERMINISTIC (harness/tooling enforces) vs PROBABILISTIC (model must choose) — a non-negotiable rule needs a deterministic tier, not prose."}}'
fi
exit 0
