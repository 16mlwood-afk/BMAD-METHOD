---
name: 'step-03-report'
description: 'Produce the wire-check report with connected/loose/mismatched/dead classifications and actionable fix suggestions'

nextStepFile: './step-04-fix-issues.md'
---

# Step 3: Wire Check Report

**Goal:** Produce a structured report of all findings. The report should be immediately actionable — a developer should be able to pick up any loose wire and fix it without further investigation.

---

## AVAILABLE STATE

From previous steps:

- `{handoff_path}` — Handoff artifact path
- `{wires}` — Complete wire inventory
- `{findings}` — Classification and details for each wire

---

## REPORT FORMAT

Write the report to `{implementation_artifacts}/wire-check-{slug}-{date}.md` where `{slug}` comes from the handoff filename.

```markdown
---
title: 'Wire Check: {brief description of what was audited}'
created: '{date}'
source_handoff: '{handoff_path}'
type: wire-check
---

# Wire Check: {brief description}

**Handoff:** {handoff_path}
**Date:** {date}
**Wires traced:** {total_count}

## Summary

| Status     | Count |
| ---------- | ----- |
| Connected  | {n}   |
| Loose      | {n}   |
| Mismatched | {n}   |
| Dead       | {n}   |

{If all connected: "All wires connected — no issues found."}
{If issues found: "**{n} issues found** requiring attention."}

## Connected Wires

{For each connected wire:}

- **{field_name}** — {source file} → {transport mechanism} → {sink component}

## Issues

{For each non-connected wire, in priority order (Dead > Loose > Mismatched):}

### {n}. {field_name} — {status}

- **Break point:** {layer where it fails}
- **Source:** {file:line} — {what the source produces}
- **Transport:** {file:line} — {what transport carries (or doesn't)}
- **Sink:** {file:line} — {what the sink expects}
- **Details:** {specific description of the mismatch or break}
- **Fix:** {concrete, actionable fix — name the file, the line, and the change}
- **Severity:** {critical (user-visible bug) | moderate (metric/counter wrong) | low (cosmetic or edge case)}

## Pattern Notes

{Optional section. If the audit revealed a recurring pattern (e.g., "all counters use JSON parsing but tools return markdown"), describe it here so the developer can apply the fix systematically rather than one-off.}
```

---

## PRESENT TO USER

After writing the report, present a brief summary:

```
**Wire check complete:** {report_file_path}

**{total} wires traced:**
- {connected} connected
- {loose} loose
- {mismatched} mismatched
- {dead} dead

{If issues found:}
**Top issues:**
1. {one-line summary of highest-severity issue}
2. {one-line summary of next issue}
...

{If no issues:}
All wires connected — implementation is fully integrated.
```

---

## SUCCESS METRICS

- Report written to implementation artifacts directory
- Every wire from the inventory accounted for
- Issues are ordered by severity
- Fix suggestions include file paths and specific changes
- Pattern notes capture systemic issues (not just individual wires)
- Summary presented to user

## NEXT STEP

If issues were found (any loose, mismatched, or dead wires), proceed immediately to `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/wire-check/steps/step-04-fix-issues.md`.

If ALL wires are connected (zero issues), skip steps 04-06. The workflow is complete — present the summary and end.

---

## FAILURE MODES

- Writing the report without tracing all wires (some just marked "assumed connected")
- Fix suggestions that are vague ("fix the counter logic" instead of "in src/main.py:1127, replace isinstance(data, list) check with tool-name-based detection")
- Not writing the report to a file (verbal-only findings are lost when session ends)
- Missing the pattern-notes section when multiple wires fail for the same reason
