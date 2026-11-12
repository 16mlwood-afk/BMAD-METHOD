---
name: 'step-02-investigate'
description: 'Autonomously read the lane the agent will front and the sibling agents it learns voice from, then design the persona structure'
---

# Step 2: Investigate the Lane & Design the Persona

**Progress: Step 2 of 4** — Next: Build the Persona (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Read the actual lane — do NOT invent workflow names or slash commands. A routing block that names a non-existent workflow sends the user into a dead end.
- Reuse the established persona format from sibling agents — don't invent a new agent shape.

## CONTEXT

From step 1 you have `{agent_kind}`, `{agent_lane}`, `{agent_routes}` (possibly partial), `{agent_cast}`, and the rest of the identity variables. This step grounds the routing/ownership block against what actually exists on disk.

## SEQUENCE OF INSTRUCTIONS

### 1. Resolve the Lane's Workflows

For each workflow the agent routes to or owns (`{agent_routes}`), and for any others in `{agent_lane}` the user named only by problem space, find the real workflow on disk:

```bash
ls {project_root}/_bmad/bmm/workflows/{design,verify,implement,meta}/*/workflow.md 2>/dev/null
```

For each candidate workflow, read the `name:` and `description:` from its `workflow.md` frontmatter. Capture, per route:

- The exact **slash command** — `/bmad:bmm:workflows:<name>` (from frontmatter `name`, NOT guessed).
- The **one-line description** of what it does (from frontmatter `description`).
- The **file path** (for the agent's availability-check block).
- **When** to route to it (derive from its description — the trigger condition).

Store as `{resolved_routes}` — a structured list. If a workflow the user named does NOT exist on disk, record it as `missing` (the persona's fallback-map will name it as not-installed rather than dropping it).

### 2. Read Sibling Agents as Voice References

Read the established persona files to mirror their format and learn the house voice:

```bash
ls {project_root}/_bmad/bmm/agents/*.md 2>/dev/null
```

Read at least `design-pm.md` (Devon) and, if present, `data-integrity-lead.md` (Vera). The canonical copies live in the fork lane (`{bmad_root}/custom/agents/`); read them there if a project's synced copy is absent. Note:

- The exact `<agent>` element shape: `id` / `name` / `title` / `icon` / `capabilities` attributes.
- The `<activation critical="MANDATORY">` block — the MANDATORY step sequence: (1) load persona from current file, (2) load config NOW and store `{user_name}` etc., (3) remember user's name, (4) greet by name + show menu, (5) STOP and WAIT for input, (6) process input (number → menu item, text → fuzzy match), (7) execute the chosen route.
- The `<rules>` inside activation (communicate in `{communication_language}`, stay in character, the agent's scope-discipline rule — e.g. "routing-only, never designs").
- The `<persona>` block: `<role>`, `<identity>`, `<communication_style>`, `<principles>`.
- The routing apparatus (router agents): `<supported-routes>`, optional `<cast>`, `<availability-check>`, `<fallback-map>`, `<decision-logic>`, `<response-template>`. An **owner** agent embeds the workflows it runs instead of a routing block; an **advisor** has neither.
- The `<menu>` block — `<item cmd="...">rendered text</item>`, including a help item and a dismiss item.

### 3. Read the Wrapper Format (the load-bearing reference for step 4)

Read an existing command wrapper so step 4 reproduces it exactly:

```bash
cat {project_root}/.claude/commands/bmad/bmm/agents/pm.md 2>/dev/null
```

Note the shape: frontmatter (`name` + `description`) + a `<agent-activation CRITICAL="TRUE">` block whose first instruction is `LOAD the FULL agent file from @_bmad/bmm/agents/<name>.md`. This is the entire wrapper — tiny. **The sync now generates it** for every `custom/agents/` persona (`sync_agents_for_project`); read it so you recognize a correct wrapper when verifying in step 4.

### 4. Note the Lane Distribution Model

Record (so step-03/04 target the right place): the persona is authored to the fork lane `{bmad_root}/custom/agents/{agent_slug}.md`. The sync mirrors it into every project's `_bmad/bmm/agents/` AND generates the `.claude/commands/` wrapper, and — because `sync_agents_for_project` runs *after* the upstream `bmm/agents` mirror (`rsync -a --delete`) — a lane agent is re-written every sync and cannot be stripped by that delete. (The old pattern of writing straight into one project's `_bmad/bmm/agents/` WAS wipe-exposed — which is exactly why this workflow writes to the lane instead.)

### 5. Design the Persona Structure

Based on `{agent_kind}`, `{resolved_routes}`, and the sibling format, design the persona:

- **Activation block** — the 7 MANDATORY steps above, customized: the greeting paraphrase introduces `{agent_name}` by name in plain language (no command codes in the greeting), then renders the menu.
- **Persona block** — `<role>` from `{agent_role}`; `<identity>` a 2-3 sentence backstory carrying `{agent_voice}`; `<communication_style>` matching the voice; `<principles>` 4-6 bullets including any signature principle the user gave.
- **Routing/ownership block** (shape depends on kind):
  - *router* → `<supported-routes>` (one `<route>` per resolved workflow with exact cmd + file + when), `<availability-check>`, `<fallback-map>` (per route, including any `missing` ones), `<decision-logic>`, and a strict `<response-template>`. Add a `<cast>` block only if `{agent_cast}` names other agents.
  - *owner* → an embedded list of the workflows this agent runs and the order it runs them, no routing recommendation apparatus.
  - *advisor* → neither; just persona + menu.
- **Menu block** — a help item, one item per primary action (classify/run/answer), and a dismiss item.

Store the full design as `{agent_persona}`.

### 6. Proceed to Build

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-agent/steps/step-03-build.md`

---

## SUCCESS METRICS

- Every routed/owned workflow resolved to a REAL slash command + file path (none invented)
- Missing workflows recorded as `missing`, not silently dropped
- At least one sibling persona read for format + voice (from the fork lane `custom/agents/` if a project copy is absent)
- The wrapper format (`pm.md`) read so step 4 can verify the sync-generated wrapper is correct
- Lane distribution model understood (persona → `custom/agents/`; sync mirrors it + generates the wrapper + keeps it wipe-safe)
- Persona structure designed to match `{agent_kind}` (router/owner/advisor)

## FAILURE MODES

- Inventing a slash command for a workflow that doesn't exist on disk
- Designing a routing block for an owner/advisor agent (wrong shape for the kind)
- Skipping the wrapper-format read — step 4 then guesses the wrapper and gets it subtly wrong
