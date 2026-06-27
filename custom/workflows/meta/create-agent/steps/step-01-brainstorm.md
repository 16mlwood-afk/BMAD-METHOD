---
name: 'step-01-brainstorm'
description: 'Short interactive brainstorm to define the agent identity and the lane it fronts, then hand off to autonomous build'
---

# Step 1: Brainstorm & Define Identity

**Progress: Step 1 of 4** — Next: Investigate the Lane (autonomous)

## RULES:

- This is the ONLY interactive step. Keep it tight — 2-3 exchanges max.
- Do NOT present option menus. Assess the user's input and ask targeted questions.
- Do NOT ask about implementation details (XML structure, activation steps, wrapper format). You decide those.
- DO ask about identity, lane, and voice.
- **Grounding gate:** if the input does not let you state a candidate *name* and a candidate *lane* (what the agent owns or routes to), you cannot proceed. Ask. Do NOT invent an identity from nothing. If args/context already ground both, infer and skip straight to confirmation.

## SEQUENCE OF INSTRUCTIONS

### 1. Greet and Get Intent

Ask the user one question: **"Who is this agent — what's their job, and what workflows or lane do they front?"**

If they already described it (in the message that triggered this workflow), skip the greeting and go straight to analysis.

### 2. Analyze and Ask Targeted Questions

**Placement gate first (`shared/persona-placement.md`, STD-PERSONA-002): personas are for human-facing judgment, not plumbing.** Before classifying kind, confirm the candidate actually warrants an agent — human-facing AND distinct judgment AND a named identity reduces genuine confusion. If it is **mechanical** (sync, formatting, rails, hooks, CI, scaffolding), an **internal sub-step** of a larger flow, or **machine-to-machine** (its output feeds another workflow, not a human), it is **not an agent** — stop, say so plainly, and point the user at `create-workflow` for the mechanical flow. Do not build a persona to decorate plumbing.

If it clears the gate, establish the agent's **shape** — every BMAD custom agent so far is a *named human persona that fronts a lane*. Classify which kind:

| Kind | Signal | Example |
|------|--------|---------|
| **Router** | Classifies an incoming request and recommends exactly ONE downstream workflow | Devon (design intake → design-handoff/review/policy), Vera (verify intake → audits) |
| **Owner** | Embodies and runs a specific cluster of workflows directly | Rowan (owns design synthesis/review), Jules (owns implementation) |
| **Advisor** | Answers domain questions in a persona voice without owning workflows | a domain expert persona |

Ask at most 2-3 clarifying questions based on what's UNCLEAR. Skip questions where the answer is obvious from context. Good questions:

- "What's the human name and one-word personality? (Devon is warm + decisive; Vera is skeptical: 'an empty column is a hypothesis, not a fact.')"
- "Does this agent ROUTE to workflows (recommend one and stop) or OWN them (run them directly)?"
- "Which workflows / lane does it front — name them, or name the problem space and I'll find them."
- "Is there an existing cast it joins (Devon/Rowan/Jules), or is it standalone?"

Do NOT ask:
- "What should the activation steps be?" (you decide)
- "What should the XML look like?" (you decide)
- "Should it have a fallback-map?" (you decide — yes, if it routes)

**Opportunistic capture (do NOT add questions for these — keep it tight).** The persona content
contract (`../persona-content-contract.md`) has two TODO-prone sections — §4 escalation target and
§6 style examples. If the user *volunteers* an escalation target ("when stuck, hand off to X") or a
"a good reply sounds like…" example, capture it into `{agent_escalation}` / `{agent_style_example}`.
Do NOT interrogate for them — step-03 scaffolds the human-tone floor for free and leaves an obvious
TODO marker for anything genuinely un-inferable. The build never blocks on these.

### 3. Confirm Understanding

Present a concise summary (not a menu, not a checklist — a paragraph):

```
Got it. I'll build {agent_name} — a {kind} agent ({title}, {icon}) who {one-sentence job}.
{agent_name} {routes to / owns} {the named workflows or lane}.
Voice: {one-line personality}.
I'll write the persona to the fork's custom/agents/ lane and sync — that distributes it to
every project AND auto-generates the command wrapper, so /bmad:bmm:agents:{agent_slug} resolves.

Building it now.
```

Wait for the user to confirm or adjust. If they say anything affirmative ("yes", "go", "y", "perfect", "do it"), proceed immediately. If they correct something, adjust and re-confirm.

### 4. Capture State Variables

Extract and store:

- `{agent_name}` — the human name (e.g., `Devon`, `Vera`). MUST be a person's name, not a function label.
- `{agent_slug}` — kebab-case file/command name (e.g., `design-pm`, `data-integrity-lead`). Used for both the persona filename and the command wrapper.
- `{agent_title}` — the role title (e.g., `Design Product Manager`, `Data Integrity Lead`).
- `{agent_icon}` — a single emoji for the persona (e.g., `🧭`, `🔎`).
- `{agent_role}` — one-line role string for the `<persona><role>` field.
- `{agent_description}` — short description string for BOTH the persona frontmatter and the wrapper frontmatter (e.g., `"Data Integrity Lead (Vera) — verify-lane intake and routing"`).
- `{agent_kind}` — router | owner | advisor.
- `{agent_lane}` — the problem space / lane the agent fronts (e.g., "design intake", "verify / is-this-data-right").
- `{agent_routes}` — the named workflows the agent routes to or owns (may be partial — step 2 resolves them). Empty for a pure advisor.
- `{agent_voice}` — one-line personality + a signature principle if the user gave one.
- `{agent_cast}` — existing cast it joins (Devon/Rowan/Jules) or `standalone`.
- `{agent_escalation}` — (optional, contract §4) escalation target the user volunteered, or empty → step-03 TODOs it for owner/advisor.
- `{agent_style_example}` — (optional, contract §6) a "good reply sounds like…" snippet the user volunteered, or empty → step-03 TODOs it.
- `{agent_file}` — `{bmad_root}/custom/agents/{agent_slug}.md` (the fork lane — the one file this workflow authors; the sync mirrors it to every project's `_bmad/bmm/agents/` and generates the wrapper)

### 5. Proceed to Investigation

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-agent/steps/step-02-investigate.md`

---

## SUCCESS METRICS

- User described an agent identity
- Agent name + lane were groundable from input (grounding gate passed) — invented neither
- Agent asked at most 2-3 clarifying questions
- Summary was confirmed in a single exchange
- All state variables captured (name is a human name, slug is kebab-case)
- Total interaction: under 4 messages

## FAILURE MODES

- Inventing a name/lane the user never grounded (grounding-gate violation — ask instead)
- Capturing a function label ("the-router") as `{agent_name}` instead of a human name
- Asking about XML/activation/wrapper internals — those are your job, not the user's
