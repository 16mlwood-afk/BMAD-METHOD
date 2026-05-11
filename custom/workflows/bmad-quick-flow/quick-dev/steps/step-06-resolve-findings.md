---
name: 'step-06-resolve-findings'
description: 'Handle review findings interactively, apply fixes, update tech-spec with final status'

nextStepFile: './step-07-deliver.md'
---

# Step 6: Resolve Findings

**Goal:** Handle adversarial review and edge-case findings interactively, apply fixes, finalize tech-spec.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)
- Unified findings table from step-05 (adversarial review + edge-case hunter)

---

## RESOLUTION OPTIONS

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true` in config, auto-select [F] Fix automatically and proceed immediately. Do not halt or wait for user input.

Present: "How would you like to handle these findings?"

Display:

**[W] Walk through** - Discuss each finding individually
**[F] Fix automatically** - Automatically fix issues classified as "real"
**[S] Skip** - Acknowledge and proceed to commit

### Menu Handling Logic:

- IF W: Execute WALK THROUGH section below
- IF F: Execute FIX AUTOMATICALLY section below
- IF S: Execute SKIP section below

### EXECUTION RULES:

- If `autonomous_mode`: auto-select [F] and proceed immediately
- Otherwise: halt and wait for user input after presenting menu

---

## WALK THROUGH [W]

For each finding in order:

1. Present the finding with context
2. Ask: **fix now / skip / discuss**
3. If fix: Apply the fix immediately
4. If skip: Note as acknowledged, continue
5. If discuss: Provide more context, re-ask
6. Move to next finding

After all findings processed, summarize what was fixed/skipped.

---

## FIX AUTOMATICALLY [F]

**CRITICAL: Never silently skip findings.** Every finding must be presented to the user with its classification and reasoning, regardless of validity.

1. Present ALL findings with analysis — do not omit any:

```
**Review findings analysis:**

ID: {id}
Source: {adversarial | edge-case}
Severity: {severity}
Validity: {validity}
Description: {reasoning for classification — explain WHY it is real/noise/uncertain}
────────────────────────────────────────
... (repeat for every finding, ordered by severity)
```

2. Apply fixes for each finding classified as "real"
3. Report what was done:

```
**Fixes applied:**
- F{n}: {description of fix}
...

**Dismissed (noise):** F{n} — {one-line reason}
...
```

4. **High-severity gate:** If ANY finding classified as "noise" or "uncertain" has severity Critical or High, flag it with a visible warning:

```
⚠️ High-severity finding dismissed as noise: F{n}
Reason: {why it was classified as noise}
```

In autonomous mode, proceed after flagging (but the warning MUST still be displayed). In interactive mode, ask: "Confirm these high-severity dismissals? [Y/N]"

---

## SKIP [S]

1. Acknowledge all findings were reviewed
2. Note that user chose to proceed without fixes
3. Continue to completion

---

## UPDATE TECH-SPEC (Mode A only)

If `{execution_mode}` is "tech-spec":

1. Load `{tech_spec_path}`
2. Update status to "Completed"
3. Add review notes:
   ```
   ## Review Notes
   - Adversarial review + edge-case hunter completed
   - Findings: {count} total ({adversarial_count} adversarial, {edge_case_count} edge-case), {fixed} fixed, {skipped} skipped
   - Resolution approach: {walk-through/auto-fix/skip}
   ```
4. Save changes

---

## COMPLETION OUTPUT

```
**Review complete. Ready to commit.**

**Implementation Summary:**
- {what was implemented}
- Files modified: {count}
- Tests: {status}
- Review findings: {X} addressed, {Y} skipped

{Explain what was implemented based on user_skill_level}
```

---

## NEXT STEP

When resolution is complete, proceed immediately to delivery:

**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-07-deliver.md`

**CRITICAL:** Do NOT stop here. Code that is reviewed but not delivered is lost work. Step 07 handles commit, push, PR, and merge.

---

## SUCCESS METRICS

- User presented with resolution options
- Chosen approach executed correctly
- Fixes applied cleanly (if applicable)
- Tech-spec updated with final status (Mode A)
- Completion summary provided
- Explicit NEXT directive to step-07 provided

## FAILURE MODES

- Not presenting resolution options
- Auto-fixing "noise" or "uncertain" findings
- **Silently skipping findings — every finding must be shown with its classification and reasoning**
- **Omitting high-severity warnings for findings dismissed as noise**
- Not updating tech-spec after resolution (Mode A)
- No completion summary
- **Declaring workflow complete without delivering (step-07)**
- Leaving code on an unmerged branch
