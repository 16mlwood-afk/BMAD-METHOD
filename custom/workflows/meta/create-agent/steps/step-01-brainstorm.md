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


## OUTWARD DISCOVERY (STD-SKILLPROV-001 §1) — run this before the persona is shaped

**Option C, owner-approved 2026-07-31: this GATES, and the override is logged.**

Before you finish this step, search OUTWARD for something that already does the job:

1. An external **web** search (docs, marketplace, vendor blog).
2. A **GitHub / MCP / extension** search.

Then make the **adopt / adapt / build-original** call out loud, with a named reason when the answer
is original — licence, security/privacy, candidate quality, or poor fit. *"Didn't find anything"* is
not a reason unless the search actually ran and its sources are named.

**Carry forward for step-03 to stamp:**

- `{discovery_performed}` — `true` only if you ACTUALLY ran both searches this step. This is a fact
  about the process, not a claim about diligence; **never set it true because you intended to.**
- `{discovery_ran_at}` — ISO timestamp, only when performed.
- `{source_research}` — the URLs you actually opened.
- `{origin_type}` + `{adoption_reason}`.

**Two different empty cases — do NOT collapse them into one field.** They mean opposite things and a
future reader must be able to tell them apart:

| case | `discovery_performed` | field to set |
|---|---|---|
| searched, found candidates | `true` | `{source_research}` — the URLs |
| **searched, genuinely nothing exists** | `true` | `{exemption_reason}` — why no prior art *could* exist |
| **did not search** | `false` | `{override_reason}` — why the pass was skipped |

An empty `{source_research}` with neither reason is indistinguishable from not having looked, which is
the exact ambiguity this standard exists to remove.

**THE GATE — this is a HALT, and it is the only new halt in this workflow.** Before you leave this
step, ONE of these three must hold:

1. `{source_research}` is non-empty, **or**
2. `{discovery_performed} = true` with an `{exemption_reason}`, **or**
3. `{discovery_performed} = false` with an `{override_reason}`.

If none holds, **HALT here and ask the user for the override reason** — do NOT proceed into step-02.
This is the one place a halt is legal (step-01 is the only interactive step; steps 2–4 are
autonomous by contract and must never block). The override is stamped on the emitted persona, so a
future session can see which agents were authored without an outward pass.

**What this gate does and does not buy — read it before trusting it.** A `source_research` URL is
SELF-ASSERTED: it proves a search was *reported*, never that it was *good*, and a lazy link that
looks compliant is worse than an honest blank. `discovery_performed` is different — the workflow
writes it, so it cannot be faked by an author filling a field. Weight them accordingly, and prefer an
honest `false` + `override_reason` over a decorative URL. Never invent a URL to clear this gate;
doing so converts an honest gap into a false record, which is the one outcome worse than no gate.

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
- `{discovery_performed}` / `{discovery_ran_at}` / `{source_research}` / `{origin_type}` /
  `{adoption_reason}` / `{exemption_reason}` / `{override_reason}` — the provenance set resolved by
  the outward-discovery gate above. Step-03 stamps these verbatim; it does not re-derive them.
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
- **The discovery gate resolved** — one of: non-empty `{source_research}` · `discovery_performed: true`
  + `{exemption_reason}` · `discovery_performed: false` + `{override_reason}`
- `{discovery_performed}` reflects what actually ran, not what was intended
- Total interaction: under 4 messages, plus the outward searches (which are tool calls, not exchanges)

## FAILURE MODES

- Inventing a name/lane the user never grounded (grounding-gate violation — ask instead)
- Capturing a function label ("the-router") as `{agent_name}` instead of a human name
- Asking about XML/activation/wrapper internals — those are your job, not the user's
- **Leaving step-01 with the discovery gate unresolved** — step-03 cannot halt, so an unresolved gate
  becomes a permanently un-auditable persona
- **Setting `discovery_performed: true` without having run both searches** — it is the one field a
  reader is entitled to trust, because the workflow writes it; falsifying it destroys the only
  non-self-asserted signal in the block
- **Filling `{source_research}` with a plausible-looking URL to clear the gate** — an honest
  `override_reason` is worth more than a decorative link
