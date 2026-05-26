---
name: 'step-03-generate-correction'
description: 'Generate a paste-ready correction message for Claude Design and persist iteration state'
---

# Step 3: Generate Correction

**Progress: Step 3 of 3** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- The correction message must be PASTE-READY — the user copies it directly into Claude Design with no editing.
- Write for Claude Design as the audience, not the user. Be direct, specific, and imperative.
- Organize violations by priority — hard failures first, issues second.
- Always include "what to keep" — Claude Design tends to throw everything out and start over if it only receives criticism.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From steps 01–02:
- `{feature_name}`, `{brief_path}`, `{iteration_number}`
- `{brief_constraints}`, `{corporate_guardrails}`, `{visual_references}`
- `{current_violations}`, `{fixed_violations}`, `{kept_elements}`
- `{previous_violations}`

## SEQUENCE OF INSTRUCTIONS

### 1. Determine Output Type

Based on findings:

- **If 0 violations (all checks pass):** Generate an APPROVAL message, not a correction. Skip to section 5.
- **If 1+ violations:** Generate a correction message. Continue to section 2.

### 2. Build the Correction Message

Use this structure for `{correction_message}`:

```markdown
**Iteration {iteration_number} feedback. {X} violations found — {Y} are hard failures.**

{If iteration > 1:}
**Progress from V{N-1}:** {count} violations fixed: {list fixed items}. {count} still remain.

**Violations — fix these before iterating on anything else:**

{For each violation, ordered by severity (hard-failure first):}
**{ID}. {Short title}** ({category})
{What the brief/guardrail says — quote the constraint.}
{What the mockup shows instead — be specific about what you see.}
{If visual reference exists: "Reference: {product} does {X} — match that pattern."}

**What to keep — do NOT change these:**
{For each kept element:}
- {Specific element that works and why}

**Visual direction reminder:**
{If visual_references populated, restate the product anchors and what to borrow from each — Claude Design may lose context across iterations.}

**All other constraints from the original brief still apply.** Re-read sections {relevant section numbers} if needed.
```

### 3. Self-Review the Correction Message

Before finalizing, verify:

- [ ] Every violation cites a specific constraint from the brief (section number or guardrail name)
- [ ] Every violation describes what the mockup shows (not just "this is wrong")
- [ ] No design opinions injected — every critique traces to a written constraint
- [ ] "What to keep" section is non-empty (even if the mockup is poor, something works)
- [ ] Visual references restated (if applicable) — Claude Design loses context between messages
- [ ] Message is addressed to Claude Design, not to the user
- [ ] No ambiguous language ("consider", "maybe", "you might want to") — use imperatives ("fix", "remove", "change to")

### 4. Persist Iteration State

Write (or update) the state file at `{state_file_path}`:

```markdown
---
feature: {feature_name}
brief: {brief_path}
iteration: {iteration_number}
date: {date}
status: {iterating | approved}
---

# Design Tuning State: {feature_name}

## Current Status

Iteration: {iteration_number}
Assessment: {PASS | FAIL}
Violations: {count}
Fixed this round: {count}

## Visual References

{visual_references — persisted here so subsequent iterations can load them without the user re-providing}

## Violation History

### Iteration {N}

| ID | Category | Severity | Description | Status |
|----|----------|----------|-------------|--------|
{table of all violations with their status}

{Include previous iteration tables too — append-only history}

## Kept Elements

{List of elements that work well, accumulated across iterations}
```

### 5. Generate Approval Message (if no violations)

If all checks pass:

```markdown
**Design approved — iteration {iteration_number}.**

All constraints from the design brief are satisfied. No corporate guardrail violations. Visual direction aligns with references.

**Approved elements:**
{List all kept_elements}

**Ready for implementation.** The design can now be handed to the dev workflow.
```

Update the state file with `status: approved`.

### 5b. Brand Identity Feedback (on approval only)

When a design is approved AND `{brand_identity_path}` exists, evaluate whether the brand identity should be updated:

**Check for new reference page candidates:**
If the approved design is notably well-executed, suggest adding it to the brand identity's section 6 (Reference Pages):
> "Consider adding {feature_name} at {route} to the brand identity's reference pages — its {specific quality} sets a new bar."

**Check for new anti-patterns discovered:**
If any violation persisted for 3+ iterations before being fixed, it's a pattern Claude Design is strongly biased toward. Suggest adding it to the brand identity's section 9 (AI Fingerprint Sensitivity):
> "Claude Design repeatedly produced {pattern} despite explicit prohibition. Consider adding this to the brand identity's AI sensitivity table."

**Check for brand identity drift:**
If the approved design intentionally deviated from any brand identity value (e.g., used a different badge pattern that looked better), flag it:
> "The approved design uses {new pattern} instead of the brand identity's stated {old pattern}. If this is intentional, update the brand identity to reflect the new direction."

Output these suggestions in a `**Brand Identity Updates**` section after the approval message. Do NOT modify the brand identity file directly — surface the suggestions for the user to review.

### 6. Present to User

Display to the user:

1. **Summary line:** "Iteration {N}: {PASS|FAIL} — {X} violations ({Y} hard failures), {Z} fixed from last round"
2. **The full correction message** inside a clearly marked block — ready to copy
3. **Brand identity update suggestions** (if any — approval only)
4. **Next step instruction:**
   - If FAIL: "Paste the message above into Claude Design. Drop the next screenshot here when ready."
   - If PASS: "Design approved. Run the design-implement workflow to bring the approved design into the codebase. For a single, isolated component change, quick-dev may be sufficient."

---

## SUCCESS METRICS

- Correction message is paste-ready (no user editing needed)
- Every violation traces to a specific brief constraint
- "What to keep" section prevents Claude Design from starting over
- State file persisted with full violation history
- Visual references persisted for subsequent iterations
- User has clear next step

## FAILURE MODES

- Generating a correction that requires the user to edit it before pasting
- Forgetting to restate visual references (Claude Design loses context between messages)
- Writing "consider doing X" instead of "do X" — Claude Design responds better to direct imperatives
- Not persisting state — losing iteration tracking between invocations
- Approving a design that still has hard failures
