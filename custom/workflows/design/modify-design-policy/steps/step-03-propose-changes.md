# Step 3: Propose Changes for Confirmation

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Do NOT write the file in this step. This step is the gate.
- Present every delta in a uniform format so the user can scan them quickly.
- In autonomous mode: skip the user gate, log the proposed deltas, and proceed directly to step-04.

## YOUR TASK:

Present `{proposed_deltas}` to the user as a clean before/after summary, and confirm before writing.

## PRESENTATION FORMAT:

For each entry in `{proposed_deltas}`, render:

```
### <section heading>
**Why:** <one-line rationale>

**Before:**
> <current text slice>

**After:**
> <proposed new text>
```

Order by importance: the section that most directly addresses the user's request first, ripple-effect sections last.

## DOWNSTREAM IMPACT NOTICE:

After the deltas, surface `{downstream_impact}` as a separate section:

```
### Downstream impact (informational, not changed here)
- <artifact 1> — <how it may be affected>
- <artifact 2> — <how it may be affected>
- ...
```

If `{downstream_impact}` is empty, write: "No in-flight artifacts reference this policy. The change can ship in isolation."

## CONFIRMATION PROMPT:

End with:

"Confirm to write the revision (version `{current_version}` → `{current_version + 1}`), or tell me what to adjust. After the policy is updated, you can run `/bmad:bmm:workflows:apply-design-policy-change` to re-baseline the downstream artifacts listed above."

Wait for the user response. Accept:

- "yes" / "confirm" / "go" → proceed to step-04
- Any text describing adjustments → revise `{proposed_deltas}` accordingly and re-present (loop within this step)
- "cancel" / "stop" → exit the workflow without writing

In autonomous mode: log the proposed deltas to the conversation, then proceed directly to step-04 without waiting.

## NEXT STEP:

Once the user confirms, proceed to `{project-root}/_bmad/bmm/workflows/design/modify-design-policy/steps/step-04-write-revision.md`.
