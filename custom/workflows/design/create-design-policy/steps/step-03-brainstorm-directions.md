# Step 3: Brainstorm Visual Directions

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Present directions as SHORT, opinionated proposals — not exhaustive specifications
- Each direction must feel genuinely different, not variations on the same theme
- In autonomous mode: evaluate all directions against the product type and user context, pick the strongest, document the reasoning in the policy

## CONTEXT BOUNDARIES:

- Product type, user role, and any partial answers from step-02 are available
- Existing codebase signals from step-01 are available, but governed by `{legacy_ui_disposition}` — see the inference guard below
- The goal is to help the user DISCOVER their preference, not to design the UI

## CRITICAL INFERENCE GUARD (restated from step-01):

Existing UI may provide implementation clues, but must NOT be treated as evidence of intended design policy unless documented elsewhere. The current UI reflects developer decisions, not design intent. A developer choosing `rounded-lg` everywhere does not mean the project's policy is "rounded corners" — it means nobody wrote a policy yet.

**Direction generation is the highest-risk step for legacy-UI bias.** The codebase scan from step-01 sits in your context window with no labeled role unless you give it one. Before generating directions, branch on `{legacy_ui_disposition}`:

- **`reset`** — The user has explicitly rejected the current UI. The codebase scan is QUARANTINED from direction-shaping. Use it ONLY to (a) confirm the framework/stack so directions reference real tokens, and (b) cross-check that generated directions are concretely different from the current implementation. The directions themselves must be generated as if the project were greenfield: drawn from product type, user role, tone, reference products, and the named anti-references — including the `[from-scan]` anti-references step-02 derived from the rejected current UI. If a generated direction is plausibly an evolution of the current implementation, discard it and regenerate. Treat similarity to current UI as a failure signal, not a success signal.
- **`evolve`** — The user wants to refine the current direction. The codebase scan informs the directions (the user's frame is "make this better," not "make this different"), but the inference guard still applies: extract factual observations as starting points, do not promote any current pattern to "intended policy" without the user's explicit endorsement.
- **`unstated`** — Should not occur at step-03; step-02 resolves it. If you somehow arrive here with `unstated`, STOP and route back to step-02 to resolve.

This guard is the load-bearing protection against the brownfield-bias failure mode: a client who hates the current UI getting a policy that looks suspiciously like an evolution of what they wanted to escape.

## YOUR TASK:

Generate 2-4 distinct visual directions tailored to the product type and user context. Present them as opinionated proposals with clear tradeoffs.

## DIRECTION GENERATION:

### How to Generate Directions

Each direction must include:

1. **Name** — a short, evocative label (e.g., "Calm Fintech Operations")
2. **One-sentence description** — what it feels like
3. **Visual characteristics** — 3-4 bullet points covering density, color, typography, layout
4. **Best for** — when this direction works well
5. **Tradeoff** — what you give up by choosing this

### Direction Template

```
### Direction {letter} — {Name}

**Feel:** {one sentence}

- **Density:** {high/medium/low} — {what this means in practice}
- **Color:** {palette approach} — {e.g., "neutral with one restrained accent"}
- **Typography:** {type approach} — {e.g., "system font, tight line heights, weight hierarchy only"}
- **Layout:** {layout approach} — {e.g., "tables over cards, full-width, minimal chrome"}

**Best for:** {when/why this works}
**Tradeoff:** {what you sacrifice}
```

### Direction Selection

Directions must be tailored to the product type gathered in step-02. Do NOT use generic directions — each must be a credible, specific proposal for THIS kind of product.

**For operations tools**, consider directions along these axes:
- Dense vs spacious
- Neutral vs colored status system
- Table-first vs card-first
- Utilitarian vs polished

**For analytics platforms**, consider:
- Chart-led vs number-led
- Dashboard-grid vs scrolling-report
- Dark vs light default
- Data-dense vs narrated

**For workflow managers**, consider:
- Kanban vs list vs timeline
- Status-color-heavy vs minimal-color
- Compact vs comfortable spacing
- Process-centric vs people-centric

### Presentation

Present all directions in a single message, then ask:

"Which direction feels closest to what you want? You don't have to pick one exactly — you can say 'mostly B, but borrow the density from A and avoid the color approach in C.'"

### Processing the Answer

**If the user picks one cleanly:**
- Use that direction as `{visual_direction}`
- Fill in any gaps from step-02 that the direction implies (e.g., if Direction A is "dense operations", that implies operational bias and restrained tone)

**If the user combines elements:**
- Synthesize their picks into a coherent `{visual_direction}` paragraph
- Confirm: "So the direction is: {synthesized description}. Sound right?"

**If the user rejects all directions:**
- Ask: "What's missing? Can you describe what you're picturing, even vaguely?"
- Generate 2 more directions based on their feedback
- Maximum 2 rounds of brainstorming — after that, proceed with the closest match and note the uncertainty in the policy

## MANDATORY RESOLUTION — PAGE MODES

Before proceeding to step-04, the chosen direction MUST explicitly resolve all three page modes. If the direction does not naturally address them, ask directly:

1. **Operational default:** "When users open this app to DO work (process items, approve things, take actions), what does that page look like? Table-first? Queue? Cards?"
2. **Analytical rule:** "When users need to UNDERSTAND data (trends, comparisons, patterns), how should those pages differ from operational ones?"
3. **Hybrid rule:** "Some pages serve both. Which mode is primary? How does the user switch between them?"

These three answers become the Page Mode Rules section (section 9) of the policy. Without them, every future handoff will re-invent the answer — which is exactly the drift this policy exists to prevent.

In autonomous mode: derive the answers from the product type and operational bias gathered in step-02. Document the reasoning.

## NEXT STEP:

After `{visual_direction}` is set AND all three page modes are resolved, proceed to `{project-root}/_bmad/bmm/workflows/design/create-design-policy/steps/step-04-write-policy.md`.
