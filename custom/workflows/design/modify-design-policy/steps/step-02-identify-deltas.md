# Step 2: Identify Change Axes and Deltas

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Stay surgical. Only flag sections that genuinely need to change. Untouched sections must remain bit-for-bit identical in the final write.
- Translate vague language ("more corporate", "tighter") into concrete policy text before proposing edits.

## YOUR TASK:

Map the user's change request to a small set of policy sections that need editing. Resist the urge to rewrite adjacent sections "while you're in there."

## CHANGE AXES (pick one or more):

- `tone` — register, copy voice, error/empty state personality
- `density` — table-first vs card-first, information per screen, whitespace budget
- `component-language` — when to use cards / tables / lists, badge patterns, button hierarchy
- `status-system` — number of status colors, what each means, default treatment
- `hard-failures` — adding or removing non-negotiable anti-patterns
- `layout` — primary layout pattern, page structure, navigation philosophy
- `typography` — font approach, size scale, monospace usage
- `color` — palette restraint rules, accent usage

Set `{change_axes}` to the minimal subset that covers the user's request.

## DELTA SEQUENCE:

### 1. Classify the request

Take the user's `{change_description}` (verbatim) and decide which axes it touches. If the request is genuinely cross-cutting (e.g., "make the whole thing more enterprise-y"), pick the 2-3 axes with the highest leverage rather than every axis.

If unclear, ask ONE targeted clarifier — not a multi-question survey. Examples:

- "Is 'more corporate' mostly about copy voice, or also about layout density?"
- "When you say 'too playful', is it the badge colors specifically, or the entire status system?"

### 2. Translate vague language into concrete text

For each axis being changed, draft the new policy language *before* showing the user. Vague-to-concrete examples:

| Vague request | Concrete policy text |
|---|---|
| "more corporate" | "Copy voice: declarative, no contractions, no exclamation marks. Error states state the fact, no apology or emoji." |
| "tighter density" | "Default to table-first layouts. Card layouts only for entity overview pages. Body text 13px, line-height 1.4." |
| "less playful badges" | "Status badges use a single neutral grey by default. Active states use one accent color. No multi-color status taxonomy." |

If you cannot make the request concrete without more information, stop and ask. Never guess and write.

### 3. Build the deltas map

For each affected section, capture:

- The exact section heading (e.g., `## Tone & Personality`)
- The current text (verbatim slice)
- The proposed new text
- A one-line rationale tying it back to `{change_description}`

Store these in `{proposed_deltas}`.

### 4. Spot ripple effects

Some changes force changes elsewhere. Examples:

- Changing density from card-first to table-first usually requires a Component Language update too.
- Adding a new hard failure may invalidate guidance in Status System or Component Language.
- Tone shifts often pull copy voice changes through the Hard Failures section.

Add ripple-effect sections to `{proposed_deltas}` only if leaving them out would create a contradictory policy. Note the ripple in the rationale.

### 5. Identify downstream impact

Scan for artifacts that consumed the old policy:

```bash
ls {project_knowledge}/brand-identity.md 2>/dev/null
find _bmad-output/implementation-artifacts -name "handoff-*" -mtime -90 2>/dev/null | head -10
```

Set `{downstream_impact}` to a list of:

- Pages or features designed under the old policy (look at recent handoff artifacts)
- Brand identity tokens that may now contradict the revised policy
- Recent or in-flight implementations that referenced the policy

This list does NOT get fixed here — it gets surfaced so the user can decide whether to run `apply-design-policy-change` afterward.

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/design/modify-design-policy/steps/step-03-propose-changes.md`.
