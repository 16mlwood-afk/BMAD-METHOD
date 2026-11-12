---
name: 'step-03-ground-and-ideate'
description: 'Divergent branch: read the real repo/artifact context FIRST, auto-select 1-2 techniques, generate ~20-30 grounded ideas'
---

# Step 3: Ground & Ideate (Divergent Branch)

**Progress: Step 3 of 4** — Next: Converge (mandatory)

## RULES — read before acting

- **Grounding is FIRST-CLASS, not optional.** Read the actual code/artifacts `{ask_target}` touches BEFORE generating a single idea. Ungrounded ideation produces plausible-sounding ideas the codebase can't support.
- **Techniques are AUTO-SELECTED.** Pick 1-2 from `{brain_techniques_csv}` yourself, name them in one line, and start. Never present the technique library or an approach menu.
- **Target ~20-30 ideas, then STOP generating.** This is the quick lane. If the space is still visibly rich at 30, note it — step-04 carries the escalation aside.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Ground in the repo

Identify and READ the context `{ask_target}` actually lives in — the named source files/routes, the relevant planning artifacts (`{planning_artifacts}`, `{implementation_artifacts}`), schema/config where applicable. Record what you read as `{grounding_sources}`.

If the reading spans many files, delegate to a read-only sub-agent that returns a distilled summary (constraints, data shapes, adjacent features, known pain points) — the raw files need not enter this context.

Store the result as `{grounding_summary}` — ≤1 short paragraph naming the real constraints and materials ideas must respect — and show it to the user. It is written into the session artifact in step-04, so keep it standalone, not chat-flavored.

### 2. Auto-select 1-2 techniques

Read `{brain_techniques_csv}` (the core lane's library — reference it, never copy it into this workflow). Pick the 1-2 techniques whose description best fits the ask's shape — e.g. "First Principles Thinking" for "rethink X", "Cross-Pollination" for "new directions", "Question Storming" for fuzzy problem spaces, "Constraint Mapping" for hemmed-in ones. Use the CSV's `technique_name` values verbatim — never invent or shorten technique names. Set `{selected_techniques}` and announce in one line:

```
Using {technique}: {one-clause why}. Ideating.
```

### 3. Generate ~20-30 grounded ideas

Apply the selected technique(s) against the GROUNDED context — every idea must be compatible with (or explicitly challenge) a named real constraint from §1:

- Work in 2-3 batches of ~10. In interactive mode, END THE TURN after each batch — that turn boundary IS the riff window (the user may riff, steer, or kill threads; an invitation, not a questionnaire). Under `autonomous_mode: true`, single-turn generation of all batches is allowed.
- Shift creative domain between batches (technical → user experience → business/ops → edge cases) to avoid semantic clustering.
- Number ideas continuously; one line each — a name plus a concrete one-clause mechanism. No essays per idea.
- Fold the user's riffs in as first-class ideas, attributed inline.

Store the full list as `{ideas}` and its length as `{idea_count}`.

### 4. Proceed to convergence

Convergence is NOT optional — never end the session on a raw idea list. Read fully and follow: `{installed_path}/steps/step-04-converge.md`

---

## SUCCESS METRICS

- `{grounding_sources}` names real files/artifacts actually read before ideation
- `{selected_techniques}` chosen autonomously (1-2), announced in one line
- 20-30 ideas generated, each traceable to the grounded context
- User riffed between batches without ever facing a menu

## FAILURE MODES

- Ideating from general knowledge with the repo unread (grounding skipped)
- Presenting the 60-technique library or asking "which approach appeals to you?"
- Chasing 100+ ideas — that's the core workflow's contract, not this one's
- Ending after generation without loading step-04
