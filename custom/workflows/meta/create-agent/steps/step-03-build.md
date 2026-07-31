---
name: 'step-03-build'
description: 'Autonomously write the agent persona file in the established XML format, bypassing the _bmad write-guard via the shell'
---

# Step 3: Build the Persona File

**Progress: Step 3 of 4** — Next: Wire the Command Wrapper (autonomous)

## RULES:

- **EMIT THE PROVENANCE BLOCK (STD-SKILLPROV-001 §3).** The persona frontmatter carries
  `id / version / created_at / author / source_research / origin_type / adoption_reason /
  last_reviewed_at`. A persona without it is **UNVERIFIED** — not banned, but it must be described
  that way whenever its trustworthiness is at issue.
  - `source_research` takes **≥1 URL** from step-01's outward pass. If that pass genuinely found no
    external prior art, write `source_research: []` **and** an `exemption_reason` naming why none
    could exist. An empty list with no exemption is the one shape that is never acceptable — it is
    indistinguishable from not having looked.
  - `adoption_reason` is **required** when `origin_type: original`, and must name one of: licence,
    security/privacy, candidate quality, poor fit. *"Didn't find anything"* is not a reason.
  - **Nested under `metadata:`, not top-level** — the Agent Skills standard keeps non-spec fields
    there for cross-tool portability.
  - **`discovery_performed` and `discovery_ran_at` come from step-01 and are MACHINE facts.** Stamp
    what step-01 actually did. Never set `discovery_performed: true` because a search was intended,
    and never invent a `source_research` URL to make the block look complete — a false record is
    worse than an honest `false` with an `override_reason`.

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Write a real, complete persona. **Soft gate — the persona MUST cover all 8 sections of the
  persona content contract** (`../persona-content-contract.md`), scaffolded into the XML. For any
  section you can safely infer from step-01/step-02, write the real content. For a section that
  genuinely **cannot** be safely defaulted, write an obvious `<!-- TODO(persona): <section> — <why>;
  fill from first real use -->` marker at the right spot and KEEP GOING — do NOT halt, and do NOT
  invent a fact to avoid the TODO. (This deliberately reverses the old "no TODOs ever" rule: a small,
  greppable, clearly-marked TODO beats an invented detail. TODOs are for un-inferable content
  ONLY — never for something inferable. The human-tone floor in §3 of the contract is always
  inferable and is therefore NEVER TODO'd.)
- Follow the exact XML format observed from sibling agents in Step 2 (`design-pm`/Devon, `data-integrity-lead`/Vera).
- **Write the persona to the fork lane: `{bmad_root}/custom/agents/{agent_slug}.md`.** Fork paths are allowlisted by the edit-guard, so a normal `Write` works. Do NOT write into a project's `_bmad/` (guarded, and the wrong home — the sync owns it).

## CONTEXT

From step 2 you have `{agent_persona}` (the full designed structure), `{resolved_routes}`, and all identity variables. This step renders the design into the persona file on disk.

**Read the content contract first.** Load `../persona-content-contract.md` (installed at
`{project-root}/_bmad/bmm/workflows/meta/create-agent/persona-content-contract.md`). It maps the 8
persona sections onto their XML homes and defines the human-tone behavior-contract floor that EVERY
persona inherits (acknowledge → clarify → close-loops, plus three never-dos). The render skeleton in
section 1 below already folds the contract in; the contract file is the authority if anything is
ambiguous.

## SEQUENCE OF INSTRUCTIONS

### 1. Render the Persona Markdown

Assemble the full persona file content. **Structure — follow it exactly (this is the design-pm/Vera format):**

```
---
name: "{agent_slug}"
description: "{agent_description}"
metadata:
  # MACHINE-GENERATED — this workflow writes these; never hand-authored.
  id: "{agent_slug}"
  version: 1
  created_at: "{date}"
  authored_by: "create-agent"
  discovery_performed: {discovery_performed}
  discovery_ran_at: "{discovery_ran_at}"
  # SELF-ASSERTED — the author's claims, recorded as claims (STD-SKILLPROV-001 §3).
  source_research:
    - "{source_research_url}"
  origin_type: "{origin_type}"
  adoption_reason: "{adoption_reason}"
  override_reason: "{override_reason}"
  last_reviewed_at: "{date}"
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
      <!-- Human-tone floor (contract §3 never-dos — bake into EVERY persona, in the agent's voice): -->
      <r>Never overrule an explicit user choice without checking first.</r>
      <r>Never fake certainty when constraints or facts are unclear — say what is unknown.</r>
      <r>Never break BMAD standards — defer to STANDARDS.md and this lane's policies.</r>
      <r>{escalation rule (contract §4) — when intent is ambiguous or two goals conflict, surface it and offer 1-2 options; do not guess silently.}</r>
      <r>{router only} Never invent workflow names. Only recommend from the supported-routes list. ALWAYS run the availability-check before emitting a recommendation; on a missing file, switch to the fallback-map entry.</r>
    </rules>
</activation>

<persona>
    <role>{agent_role}</role>
    <identity>{2-3 sentence backstory carrying {agent_voice}; states the user knows them by name ({agent_name}), not by command code}</identity>
    <communication_style>{matches {agent_voice} — 4-6 core adjectives + the tone spectrum (contract §2)}</communication_style>
    <principles>
      <!-- Human-tone floor (contract §3 always-dos — bake into EVERY persona, in the agent's voice): -->
      - Acknowledge what {user_name} just did or said before proposing the next step — don't open cold.
      - When intent is genuinely ambiguous, ask ONE targeted clarifying question rather than guessing.
      - Close loops: at the end of a multi-step interaction, summarise what changed and what's still open.
      <!-- Then 3-4 domain principles (contract §1 scope, §7 knowledge/boundaries, plus any signature principle the user gave): -->
      {3-4 domain principles, including any signature principle and the agent's source-of-truth}
    </principles>
    <style-examples>
      <!-- Contract §6. Use real in-character snippets when inferable; otherwise TODO (do NOT invent a fake exchange). -->
      <good>{1-2 short replies that sound like this agent doing its job well}</good>
      <avoid>{1-2 replies to avoid — e.g. jargon-dump, guessing instead of asking}</avoid>
      <!-- If no concrete example is safely inferable: replace the two lines above with:
           <!-\- TODO(persona): style examples — no concrete in-character reply inferable pre-first-run; fill from first real use -\-> -->
    </style-examples>
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
grep -c "<style-examples>" "{agent_file}"
grep -n "TODO(persona)" "{agent_file}"   # surface any soft-gate breadcrumbs left behind
```

Confirm: frontmatter has `name` + `description`; exactly one `<agent>` open tag; an `<activation>`
block; a `<menu>` block; a `<style-examples>` block (real or TODO'd). If any structural check fails,
re-render and re-write before proceeding. Any `TODO(persona)` lines are expected only for genuinely
un-inferable sections — they do NOT block the run, but report them in the final summary so {user_name}
knows what to fill in.

### 4. Proceed to Wiring

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-agent/steps/step-04-wire.md`

---

## SUCCESS METRICS

- Persona written to `{agent_file}` (`{bmad_root}/custom/agents/{agent_slug}.md`) via a normal `Write` — the fork lane, not a project
- File matches the design-pm/Vera XML format (frontmatter + embodiment preamble + `<agent>` with activation/persona/routing-or-ownership/menu)
- **All 8 content-contract sections covered** — real content where inferable, an obvious `TODO(persona)` marker only where genuinely un-inferable (typically §6 style examples, sometimes §4 escalation target)
- **Human-tone floor present** — the 3 always-do principles + 3 never-do rules are baked in, never TODO'd
- Middle block matches `{agent_kind}` (routing for router, ownership for owner, neither for advisor)
- No INVENTED facts (workflow names, fake style exchanges) — an un-inferable section is TODO'd, not fabricated
- Verification greps all pass; any TODO breadcrumbs are reported in the final summary

## FAILURE MODES

- Writing the persona into a project's `_bmad/bmm/agents/` instead of the fork lane — guarded, undistributed, and wipe-exposed; it must go to `{bmad_root}/custom/agents/`
- **Inventing content to avoid a TODO** (a fake style example, a guessed escalation target) — the soft gate exists precisely so un-inferable content is marked, not fabricated
- **TODO'ing an inferable section** — scope, tone, knowledge, the human-tone floor are all inferable from the lane; a TODO there means you skipped the inference, not that it was un-inferable
- Halting mid-build to ask the user to fill a section — the gate is a SCAFFOLD, never an interactive wizard; build it, mark the gap, report it at the end
- Writing a routing block for an owner/advisor (wrong shape) or omitting it for a router
- Leaving the persona in the lane and calling the workflow done — it is NOT invokable until the sync runs; step 4 (sync + verify) is mandatory
