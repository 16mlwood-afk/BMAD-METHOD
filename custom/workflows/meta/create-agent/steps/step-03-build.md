---
name: 'step-03-build'
description: 'Autonomously write the agent persona file in the established XML format, bypassing the _bmad write-guard via the shell'
---

# Step 3: Build the Persona File

**Progress: Step 3 of 4** — Next: Wire the Command Wrapper (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Write a real, complete persona — no placeholders, no TODOs, no "fill in later."
- Follow the exact XML format observed from sibling agents in Step 2 (`design-pm`/Devon, `data-integrity-lead`/Vera).
- **Write the persona to the fork lane: `{bmad_root}/custom/agents/{agent_slug}.md`.** Fork paths are allowlisted by the edit-guard, so a normal `Write` works. Do NOT write into a project's `_bmad/` (guarded, and the wrong home — the sync owns it).

## CONTEXT

From step 2 you have `{agent_persona}` (the full designed structure), `{resolved_routes}`, and all identity variables. This step renders the design into the persona file on disk.

## SEQUENCE OF INSTRUCTIONS

### 1. Render the Persona Markdown

Assemble the full persona file content. **Structure — follow it exactly (this is the design-pm/Vera format):**

```
---
name: "{agent_slug}"
description: "{agent_description}"
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified. NEVER break character until given an exit command.

​```xml
<agent id="{agent_slug}.agent.yaml" name="{agent_name}" title="{agent_title}" icon="{agent_icon}" capabilities="...">
<activation critical="MANDATORY">
      <step n="1">Load persona from this current agent file (already in context)</step>
      <step n="2">🚨 IMMEDIATE ACTION REQUIRED - BEFORE ANY OUTPUT:
          - Load and read {project-root}/_bmad/bmm/config.yaml NOW
          - Store ALL fields as session variables: {user_name}, {communication_language}, {output_folder}
          - VERIFY: If config not loaded, STOP and report error to user
          - DO NOT PROCEED to step 3 until config is successfully loaded
      </step>
      <step n="3">Remember: user's name is {user_name}</step>
      <step n="4">Greet {user_name} warmly in plain language — no command codes in the greeting itself — introducing yourself as {agent_name}. Then display the menu using the rendered text of each <item> as a numbered list.</step>
      <step n="5">STOP and WAIT for user input - do NOT execute menu items automatically - accept number or cmd trigger or fuzzy command match.</step>
      <step n="6">On user input: Number → process menu item[n] | Text → case-insensitive substring match | Multiple matches → ask user to clarify | No match → {default action for this agent's kind}.</step>
      <step n="7">{For a router: when processing the classify item, follow the <routing> block precisely, run the <availability-check> before emitting, and output ONLY the response template. For an owner: invoke the chosen workflow directly. For an advisor: answer in persona.}</step>

    <rules>
      <r>ALWAYS communicate in {communication_language} UNLESS contradicted by communication_style.</r>
      <r>Stay in character until exit selected.</r>
      <r>{the agent's scope-discipline rule — e.g. "You are routing-only. You do NOT do the work; you classify and recommend exactly ONE workflow."}</r>
      <r>{router only} Never invent workflow names. Only recommend from the supported-routes list. ALWAYS run the availability-check before emitting a recommendation; on a missing file, switch to the fallback-map entry.</r>
    </rules>
</activation>

<persona>
    <role>{agent_role}</role>
    <identity>{2-3 sentence backstory carrying {agent_voice}; states the user knows them by name ({agent_name}), not by command code}</identity>
    <communication_style>{matches {agent_voice}}</communication_style>
    <principles>{4-6 bullets, including any signature principle the user gave}</principles>
</persona>

{routing OR ownership block per {agent_kind} — see below}

<menu>
    <item cmd="MH or fuzzy match on menu or help">Show this menu again</item>
    {one or more action items}
    <item cmd="DA or fuzzy match on exit, leave, goodbye or dismiss agent">Dismiss me — exit {agent_name} and return to regular chat.</item>
</menu>
</agent>
​```
```

**Kind-specific middle block:**

- **router** — emit `<routing>` containing: `<supported-routes>` (one `<route id="..." cmd="/bmad:bmm:workflows:..." file="...">When: ...</route>` per resolved route), an optional `<cast>` if `{agent_cast}` is set, `<availability-check>` (ls the route's `file` before recommending), `<fallback-map>` (per route, including `missing` ones), `<decision-logic>` (priority-ordered rules), and a strict `<response-template>` with Recommendation / Why / Inputs to prepare / If this is not the case sections.
- **owner** — emit a `<workflows-owned>` block listing each workflow the agent runs, its slash command, and the order/conditions; the menu items invoke them directly.
- **advisor** — no routing/ownership block; the menu items map to domain questions the agent answers in persona.

### 2. Write the Persona File to the Lane

`{agent_file}` = `{bmad_root}/custom/agents/{agent_slug}.md`. This is a fork path (allowlisted by the edit-guard), so write it with a normal `Write`:

```bash
mkdir -p "{bmad_root}/custom/agents"
```

Then `Write` the full rendered persona content from section 1 to `{agent_file}`. The `{...}` placeholders in the persona body (e.g. `{user_name}`, `{project-root}`) are part of the agent's runtime contract — write them literally, exactly as rendered. (If for any reason you fall back to a shell heredoc, use a quoted `'AGENT_EOF'` delimiter so backticks, `$`, and `{...}` are not expanded.)

### 3. Verify the Persona Wrote Correctly

```bash
head -12 "{agent_file}"
grep -c "<agent " "{agent_file}"
grep -c "<activation" "{agent_file}"
grep -c "<menu>" "{agent_file}"
```

Confirm: frontmatter has `name` + `description`; exactly one `<agent>` open tag; an `<activation>` block; a `<menu>` block. If any check fails, re-render and re-write before proceeding.

### 4. Proceed to Wiring

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-agent/steps/step-04-wire.md`

---

## SUCCESS METRICS

- Persona written to `{agent_file}` (`{bmad_root}/custom/agents/{agent_slug}.md`) via a normal `Write` — the fork lane, not a project
- File matches the design-pm/Vera XML format (frontmatter + embodiment preamble + `<agent>` with activation/persona/routing-or-ownership/menu)
- Middle block matches `{agent_kind}` (routing for router, ownership for owner, neither for advisor)
- No placeholders, TODOs, or invented workflow names
- Verification greps all pass

## FAILURE MODES

- Writing the persona into a project's `_bmad/bmm/agents/` instead of the fork lane — guarded, undistributed, and wipe-exposed; it must go to `{bmad_root}/custom/agents/`
- Writing a routing block for an owner/advisor (wrong shape) or omitting it for a router
- Leaving the persona in the lane and calling the workflow done — it is NOT invokable until the sync runs; step 4 (sync + verify) is mandatory
