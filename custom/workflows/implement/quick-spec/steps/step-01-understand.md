---
name: 'step-01-understand'
description: 'Analyze the requirement delta between current state and what user wants to build'

templateFile: '../tech-spec-template.md'
wipFile: '{implementation_artifacts}/tech-spec-wip.md'
---

# Step 1: Analyze Requirement Delta

**Progress: Step 1 of 4** - Next: Deep Investigation

## RULES:

- MUST NOT skip steps.
- MUST NOT optimize sequence.
- MUST follow exact instructions.
- MUST NOT look ahead to future steps.
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`
- **Voice — Sol, Rapid Prototyper** (`shared/workflow-personas.md`): open with a one-line rough-and-fast contract ("Smallest thing that could work for [ask] — going [rough/tight]."). Presentation only; Sol picks the smallest sensible default and proceeds — no ask-before-generating, no "do you want that?" menu. Keep it intentionally lightweight, never a waterfall spec.

## CONTEXT:

- Variables from `workflow.md` are available in memory.
- Focus: Define the technical requirement delta and scope.
- Investigation: Perform surface-level code scans ONLY to verify the delta. Reserve deep dives into implementation consequences for Step 2.
- Objective: Establish a verifiable delta between current state and target state.

## SEQUENCE OF INSTRUCTIONS

### 0. Check for Work in Progress

a) **Before anything else, check if `{wipFile}` exists:**

b) **IF WIP FILE EXISTS:**

1. Read the frontmatter and extract: `title`, `slug`, `stepsCompleted`
2. Calculate progress: `lastStep = max(stepsCompleted)`
3. Present to user:

```
Hey {user_name}! Found a tech-spec in progress:

**{title}** - Step {lastStep} of 4 complete

Is this what you're here to continue?

[Y] Yes, pick up where I left off
[N] No, archive it and start something new
```

4. **HALT and wait for user selection.**

a) **Menu Handling:**

- **[Y] Continue existing:**
  - Jump directly to the appropriate step based on `stepsCompleted`:
    - `[1]` → Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-spec/steps/step-02-investigate.md` (Step 2)
    - `[1, 2]` → Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-spec/steps/step-03-generate.md` (Step 3)
    - `[1, 2, 3]` → Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-spec/steps/step-04-review.md` (Step 4)
- **[N] Archive and start fresh:**
  - Rename `{wipFile}` to `{implementation_artifacts}/tech-spec-{slug}-archived-{date}.md`

### 1. Greet and Ask for Initial Request

a) **Greet the user briefly:**

"Hey {user_name}! What are we building today?"

b) **Get their initial description.** Don't ask detailed questions yet - just understand enough to know where to look.

### 2. Quick Orient Scan

a) **Before asking detailed questions, do a rapid scan to understand the landscape:**

a.1) **Normalize visual input (if image attached):**

If the user attached an image containing **tabular or grid-like data** (data tables, spreadsheets, dashboards, order lists):

- **Do NOT rely on the image for cell values or data correctness diagnosis.** Screenshot OCR is unreliable for numbers, currency symbols, and column boundaries.
- **Query the source directly** if the table is rendered by this app — read the API route or DB query that populates it.
- **If external data**, ask: _"Can you paste a few rows as text, or share the API response? Structured text lets me scope this accurately."_
- **Use the image for context only** — layout, column order, which page/tab, visual hierarchy.

b) **Check for existing context docs:**

- Check `{implementation_artifacts}` and `{planning_artifacts}`for planning documents (PRD, architecture, epics, research)
- Check for `**/project-context.md` - if it exists, skim for patterns and conventions
- Check for any existing stories or specs related to user's request
- **Check the WIP register** (`<main-repo>/.claude/wip-register.yaml`, if present) for a LIVE claim by another session covering this same feature/area (`shared/parallel-sessions.md` §E). If one plausibly overlaps (judge by description, not branch name), surface it to the user before authoring a spec for work already in flight — this is the spec-time half of the no-duplicate-builds check.

c) **If user mentioned specific code/features, do a quick scan:**

- Search for relevant files/classes/functions they mentioned
- Skim the structure (don't deep-dive yet - that's Step 2)
- Note: tech stack, obvious patterns, file locations

d) **Build mental model:**

- What's the likely landscape for this feature?
- What's the likely scope based on what you found?
- What questions do you NOW have, informed by the code?

**This scan should take < 30 seconds. Just enough to ask smart questions.**

e) **CLASS-CHANGE TRIPWIRE** (`{project-root}/_bmad/bmm/workflows/shared/escalation-on-class-change.md`, STD-ESCALATE-001):

If the likely scope you just assessed is NOT a small/quick change — it is materially larger than a quick-spec unit, a re-plan rather than a defined delta, needs a missing keystone/shared seam built first, or belongs to another lane (design → `design-router`, production-driven backlog → `maintenance-triage`, full planning → `create-prd` / `correct-course`) — do NOT proceed to author a quick spec for work that isn't quick. STATE the class-change + evidence, NAME the BMAD-default gateway, PROPOSE it, and PROCEED there unless the user vetoes — never a numbered menu. Conservative: a normal small delta does NOT fire this. (Catches mis-scope at spec-time, before a wasted quick-dev cycle — the spec-time sibling of quick-dev §0.)

### 3. Ask Informed Questions

a) **Now ask clarifying questions - but make them INFORMED by what you found:**

Instead of generic questions like "What's the scope?", ask specific ones like:

- "`AuthService` handles validation in the controller — should the new field follow that pattern or move it to a dedicated validator?"
- "`NavigationSidebar` component uses local state for the 'collapsed' toggle — should we stick with that or move it to the global store?"
- "The epics doc mentions X - is this related?"

**Adapt to {user_skill_level}.** Technical users want technical questions. Non-technical users need translation.

b) **If no existing code is found:**

- Ask about intended architecture, patterns, constraints
- Ask what similar systems they'd like to emulate

### 4. Capture Core Understanding

a) **From the conversation, extract and confirm:**

- **Title**: A clear, concise name for this work
- **Slug**: URL-safe version of title (lowercase, hyphens, no spaces)
- **Problem Statement**: What problem are we solving?
- **Solution**: High-level approach (1-2 sentences)
- **In Scope**: What's included
- **Out of Scope**: What's explicitly NOT included

b) **Ask the user to confirm the captured understanding before proceeding.**

### 5. Initialize WIP File

a) **Create the tech-spec WIP file:**

1. Copy template from `{templateFile}`
2. Write to `{wipFile}`
3. Update frontmatter with captured values:
   ```yaml
   ---
   title: '{title}'
   slug: '{slug}'
   created: '{date}'
   status: 'in-progress'
   stepsCompleted: [1]
   tech_stack: []
   files_to_modify: []
   code_patterns: []
   test_patterns: []
   ---
   ```
4. Fill in Overview section with Problem Statement, Solution, and Scope
5. Fill in Context for Development section with any technical preferences or constraints gathered during informed discovery.
6. Write the file

b) **Report to user:**

"Created: `{wipFile}`

**Captured:**

- Title: {title}
- Problem: {problem_statement_summary}
- Scope: {scope_summary}"

### 6. Present Checkpoint Menu

a) **Display menu:**

Display: "**Select:** [A] Advanced Elicitation [P] Party Mode [C] Continue to Deep Investigation (Step 2 of 4)"

b) **HALT and wait for user selection.**

#### Menu Handling Logic:

- IF A: Read fully and follow: `{advanced_elicitation}` with current tech-spec content, process enhanced insights, ask user "Accept improvements? (y/n)", if yes update WIP file then redisplay menu, if no keep original then redisplay menu
- IF P: Read fully and follow: `{party_mode_exec}` with current tech-spec content, process collaborative insights, ask user "Accept changes? (y/n)", if yes update WIP file then redisplay menu, if no keep original then redisplay menu
- IF C: Verify `{wipFile}` has `stepsCompleted: [1]`, then read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-spec/steps/step-02-investigate.md`
- IF Any other comments or queries: respond helpfully then redisplay menu

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- After A or P execution, return to this menu

---

## REQUIRED OUTPUTS:

- MUST initialize WIP file with captured metadata.

## VERIFICATION CHECKLIST:

- [ ] WIP check performed FIRST before any greeting.
- [ ] `{wipFile}` created with correct frontmatter, Overview, Context for Development, and `stepsCompleted: [1]`.
- [ ] User selected [C] to continue.
