---
name: 'step-04-audit'
description: 'Audit the traced pipeline for gaps, dead fields, redundant fetches, type drift, and optimization opportunities'

nextStepFile: './step-05-evaluate-purpose.md'
---

# Step 4: Audit

**Goal:** Now that the pipeline is mapped and data captured, audit it for issues that aren't obvious from tracing alone. This step looks at the pipeline holistically — not just "does data flow?" but "does it flow *well*?"

---

## AVAILABLE STATE

From previous steps:

- `{anchor}` — The anchor point
- `{stages}` — Ordered pipeline stages
- `{live_data}` — Captured data values
- `{stack}` — Project stack
- `{server_live}` — Whether live data was captured

## STATE VARIABLES (set in this step)

- `{gaps}` — Audit findings list, each with category, severity, file:line, and suggested fix

---

## AUDIT CHECKS

Run each audit check against the traced pipeline. Record findings as `{gaps}`.

### Audit 1: Dead Fields

Fields that exist at one stage but are never consumed downstream.

**How to check:**
- For each field in the source/model stage, verify it appears in at least one downstream stage
- For each field in the transport stage, verify the frontend actually destructures and uses it
- `grep -rn "{field_name}" frontend/src/` to confirm consumption

**Common patterns:**
- DB column included in query but filtered out before API response
- API response field that no component ever reads
- SSE event field that frontend receives but never displays
- Pydantic model field with a default that's never overridden

**Classification:** `dead-field` — severity based on whether the dead field adds unnecessary payload size or suggests a missed feature.

### Audit 2: Missing Display

Fields that reach the frontend but aren't rendered anywhere.

**How to check:**
- For each field destructured from API responses or SSE events in frontend code
- `grep -rn "{field_name}" frontend/src/**/*.tsx` — look for JSX usage, not just imports
- A field stored in state but only used in conditions (`if (x)`) without display is "used but not displayed" — note it separately

**Common patterns:**
- Field stored in React state but never referenced in JSX
- Field available in a hook's return value but no component destructures it
- Field rendered in one view (detail) but missing from another (list/card)

**Classification:** `missing-display` — moderate severity (data available but user can't see it).

### Audit 3: Type Drift

Fields whose type changes unexpectedly across stages.

**How to check:**
- Compare the actual runtime type at each stage (from `{live_data}`)
- Watch for: number → string (JSON serialization), Date → ISO string → displayed as raw string, null vs undefined, snake_case → camelCase name changes without mapping

**Common patterns:**
- `python-fastapi-sse`: Python `datetime` → ISO string in JSON → rendered without formatting
- `python-fastapi-sse`: Python `None` → JSON `null` → JavaScript `null` but component expects `undefined`
- `express-react-drizzle`: Drizzle JSONB → parsed once in service → double-parsed in component
- `nextjs-prisma`: Prisma `Decimal` → number in server → string in client serialization

**Classification:** `type-drift` — severity depends on whether it causes runtime errors or just cosmetic issues.

### Audit 4: Redundant Fetches

Multiple stages that fetch the same data independently.

**How to check:**
- List all API calls / DB queries in the pipeline
- Look for components that fetch the same endpoint as a parent component
- Check for React Query keys that should be shared but aren't
- Look for SSE event handlers that re-fetch data that the event already contains

**Common patterns:**
- Parent component fetches lead detail, child component re-fetches the same lead for one field
- SSE event contains updated data, but handler triggers a full refetch anyway
- Multiple `useEffect` hooks hitting the same endpoint on different triggers

**Classification:** `redundant-fetch` — low severity but performance concern.

### Audit 5: Missing Error / Loading / Empty States

Stages that handle the happy path but not edge cases.

**How to check:**
- For each data-fetching stage, check if there's error handling
- For each render stage, check if there's a loading state and empty state
- Look for `{value || "—"}` patterns that incorrectly hide `0`, `false`, or `""` values

**Common patterns:**
- Component renders data but shows nothing during loading (flash of empty content)
- Error from API silently swallowed — component shows stale data instead of error state
- List component doesn't handle empty array (no "no results" message)
- SSE disconnect not detected — component shows last-known data as if it's current

**Classification:** `missing-state` — severity depends on user impact.

### Audit 6: Stale Data Risk

Points where data can become stale without the user knowing.

**How to check:**
- Identify polling intervals or lack thereof
- Check if mutations invalidate the right queries
- Look for SSE reconnection logic
- Check if cached data has TTL or is treated as forever-fresh

**Common patterns:**
- Data fetched once on mount but never refreshed (user sees stale values after background changes)
- Mutation updates local state but doesn't invalidate the server cache
- SSE connection drops silently — no reconnection, no staleness indicator
- Browser tab hidden for hours, data still shows as "current"

**Classification:** `stale-risk` — moderate severity.

---

## FINDINGS FORMAT

For each issue found:

```
### {n}. {field_or_component_name} — {classification}

- **Stage:** {which stage the issue occurs at}
- **Details:** {specific description with file:line references}
- **Impact:** {what the user experiences — or what's wasted}
- **Suggested fix:** {concrete, actionable — name the file and change}
- **Severity:** {critical | moderate | low}
```

---

## APPEND TO PIPELINE DOCUMENT

Add an `## Audit Findings` section to the pipeline document written in step 3:

```markdown
## Audit Findings

**{total} issues found** across {categories} categories.

| Category | Count | Severity |
|----------|-------|----------|
| Dead fields | {n} | {highest severity in category} |
| Missing display | {n} | ... |
| Type drift | {n} | ... |
| Redundant fetches | {n} | ... |
| Missing states | {n} | ... |
| Stale data risk | {n} | ... |

{Then list each finding using the format above}

## Recommendations

{Prioritized list of suggested improvements, grouped by effort:}

### Quick wins (< 30 min each)
- {concrete fix}

### Medium effort (1-2 hours)
- {concrete fix}

### Structural improvements
- {architectural suggestion — e.g., "consolidate these 3 fetches into one React Query hook"}
```

---

## PRESENT FINAL SUMMARY

```
**Flow trace + audit complete:** {report_file_path}

**Pipeline:** {source} → ... → {render} ({stage_count} stages)
**Data:** {live values captured | static analysis only}

**Audit results:**
- {n} dead fields
- {n} missing display
- {n} type drift
- {n} redundant fetches
- {n} missing states
- {n} stale data risks

{If issues found:}
**Top priority:**
1. {one-line summary of highest-severity issue}
2. {next issue}

{If no issues:}
**Pipeline is clean — no audit issues found.**
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/trace-flow/steps/step-05-suggest-ui.md` — evaluate whether this pipeline would benefit from a user-facing visualization component.

---

## SUCCESS METRICS

- All 6 audit categories checked
- Each finding has file:line references and a concrete fix suggestion
- Findings appended to the pipeline document (single deliverable)
- Recommendations prioritized by effort
- Summary presented to user

## FAILURE MODES

- Running audits against types/shapes only, not against the live captured data
- Flagging intentional design choices as issues (e.g., a field that's deliberately not displayed)
- Audit findings too vague to act on ("consider improving error handling")
- Not checking the frontend for dead fields (only checking backend → transport)
- Missing the `{value || "—"}` anti-pattern for numeric fields
