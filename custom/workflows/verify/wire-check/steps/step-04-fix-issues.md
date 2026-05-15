---
name: 'step-04-fix-issues'
description: 'Autonomously fix all non-connected wires — loose, mismatched, and dead — regardless of severity'

nextStepFile: './step-05-deliver.md'
---

# Step 4: Fix All Issues

**Goal:** Resolve every non-connected wire identified in step 02 and reported in step 03. Fix ALL issues — critical, moderate, AND low severity. No issue is too small to fix.

---

## AVAILABLE STATE

From previous steps:

- `{handoff_path}` — Handoff artifact path
- `{wires}` — Complete wire inventory
- `{findings}` — Classification and details for each wire (from step 02)
- `{baseline_commit}` — Git HEAD at workflow start

---

## WORKTREE ENTRY

**Before editing any files**, enter a worktree if not already in one:

1. Call `EnterWorktree` with a descriptive name (e.g., `fix/wire-check-{slug}`)
2. Rename the branch to follow convention: `git branch -m fix/wire-check-{slug}`

If already in a worktree (e.g., because the workflow was invoked from within a quick-dev session), skip this — verify with `pwd` containing `/.claude/worktrees/`.

---

## EXECUTION SEQUENCE

### 1. Build Fix Plan

From `{findings}`, extract every wire classified as Loose, Mismatched, or Dead. For each:

- Read the **Fix** suggestion from the report
- Identify the exact file(s) and line(s) to change
- Determine the order of operations (backend before frontend if adding new fields; frontend-only if fields already exist in transport)

Group fixes by file to minimize edit passes.

### 2. Apply Fixes

For each issue, in priority order (Dead > Mismatched > Loose):

#### Loose wires (sink doesn't consume)

- **Add rendering** in the frontend component. Use existing formatter helpers (`fmtDate`, `fmtTokens`, `fmtCost`, etc.) where available.
- Follow the established patterns in the component (same CSS classes, same table structure, same tooltip format).
- If the wire is intentionally unused (e.g., reserved for a future feature that doesn't exist yet), add it to the nearest appropriate UI element (tooltip, table column, subtitle) rather than removing it from the backend.

#### Loose wires (transport doesn't carry)

- **Add the field** to the transport layer (SSE event, API response, `progress_snapshot()`).
- Ensure the field name matches what the sink expects (case-sensitive).
- If adding to a Pydantic response model, add the corresponding TypeScript interface field too.

#### Mismatched wires (format/type/name mismatch)

- Fix at the **transport** layer if the source and sink agree but transport mangles the value.
- Fix at the **sink** if the transport is correct but the frontend reads the wrong key or applies wrong formatting.
- If source and sink disagree on the field name, prefer the backend convention and update the frontend.

#### Dead wires (source never produces value)

- Investigate WHY the source doesn't produce the value. Is the counter inside a condition that never matches? Is the field declared but never assigned?
- Fix the source to actually produce the value. If the source genuinely can't produce it (e.g., the data doesn't exist), remove the wire from all layers (source, transport, sink) cleanly.

### 3. Type Check

After all fixes are applied:

```bash
cd frontend && npx tsc --noEmit
```

If type errors appear, fix them before proceeding.

### 4. Verify Fixes

Re-trace each fixed wire mentally:

- Source produces the value ✓
- Transport carries it with the correct name and type ✓
- Sink consumes and renders it ✓

---

## NEXT STEP

When all issues are fixed and type-checked, proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/wire-check/steps/step-05-deliver.md`.

---

## SUCCESS METRICS

- Every non-connected wire from the report has been fixed
- No issues skipped due to "low severity"
- Type check passes
- Fixes follow existing code patterns (no new abstractions, no new helpers unless truly needed)
- Each fix is minimal — resolve the specific wire, don't refactor surrounding code

## FAILURE MODES

- Skipping low-severity issues ("it's just a loose wire, not a bug")
- Removing backend fields instead of wiring them to the frontend (the data is there for a reason)
- Adding new helper functions when existing ones already handle the format
- Not running type check after edits
- Editing files without entering a worktree first
