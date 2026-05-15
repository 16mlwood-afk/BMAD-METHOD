---
name: 'step-02-investigate'
description: 'Autonomously scan existing workflows for reusable patterns, then design the step architecture'
---

# Step 2: Investigate Patterns & Design Architecture

**Progress: Step 2 of 4** — Next: Build Files (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Make expert decisions about step count, file structure, and patterns.
- Reuse patterns from peer workflows — don't invent new conventions.

## SEQUENCE OF INSTRUCTIONS

### 1. Scan Peer Workflows

Read the workflow.md files of the most relevant peer workflows across `{bmad_root}/custom/workflows/{build,verify,design,meta}/`:

- Find workflows with similar `{wf_type}` (document, action, autonomous, etc.)
- Note their step count, file structure, and frontmatter patterns
- Identify which ones have templates, checklists, shared components

Focus on:
- **Frontmatter fields** used by peers (which are standard, which are workflow-specific)
- **Step naming conventions** (verb-noun: `map-stages`, `snapshot-data`, `generate`, `review`)
- **How they handle initialization** (config loading, input validation, path resolution)
- **How they handle output** (WIP files, final documents, code changes, console output)
- **Shared components** in `{bmad_root}/custom/workflows/shared/` — can any be reused?

### 2. Check for Shared Components

Read `{bmad_root}/custom/workflows/shared/` to see what reusable components exist:

- Stack detection
- Config loading patterns
- Common validation logic

Determine if the new workflow should use any of these.

### 3. Design Step Architecture

Based on the captured state variables and peer patterns, design the step breakdown:

**Guidelines:**
- 3-5 steps is the sweet spot. More than 6 is a smell — combine related actions.
- First step handles input/initialization (may be interactive or autonomous depending on `{wf_autonomous}`)
- Last step handles output delivery and cleanup
- Middle steps do the actual work
- Each step should have a single clear goal

**For each step, define:**
- Step number and name (kebab-case, verb-noun: `gather-context`, `build-spec`, `validate-output`)
- One-line goal
- Key actions (3-5 bullet points)
- Whether it reads from or writes to files
- Whether it needs user input (should be rare — only step 1 for interactive workflows)

Store as `{wf_step_design}` — a structured outline of all steps.

### 4. Design Template (if needed)

If `{wf_needs_template}` is true, design the output document structure:

- Section headings
- Variable placeholders (`{{variable_name}}`)
- Which steps populate which sections
- Frontmatter fields for the output document

Store as `{wf_template_design}`.

### 5. Design Checklist (if needed)

If `{wf_needs_checklist}` is true, design validation criteria:

- Measurable, specific checks (not vague "good quality")
- Tied to the template sections or output requirements
- Follow the pattern from peer workflow checklists

Store as `{wf_checklist_design}`.

### 6. Proceed to Build

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-workflow/steps/step-03-build.md`

---

## SUCCESS METRICS

- At least 2 peer workflows scanned for patterns
- Shared components checked for reuse opportunities
- Step architecture designed with 3-5 focused steps
- Each step has a clear goal and action list
- Template designed (if applicable) with concrete sections
- Checklist designed (if applicable) with measurable criteria
