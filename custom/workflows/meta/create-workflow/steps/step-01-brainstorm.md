---
name: 'step-01-brainstorm'
description: 'Short interactive brainstorm to define what the workflow does, then hand off to autonomous build'
---

# Step 1: Brainstorm & Define

**Progress: Step 1 of 4** — Next: Investigate Patterns (autonomous)

## RULES:

- This is the ONLY interactive step. Keep it tight — 2-3 exchanges max.
- Do NOT present option menus. Assess the user's input and ask targeted questions.
- Do NOT ask about implementation details (file structure, frontmatter, step count). You decide those.
- DO ask about intent, scope, and behavior.

## SEQUENCE OF INSTRUCTIONS

### 1. Greet and Get Intent

Ask the user one question: **"What should this workflow do?"**

If they already described it (in the message that triggered this workflow), skip the greeting and go straight to analysis.

### 2. Analyze and Ask Targeted Questions

From the user's description, classify the workflow type:

| Type | Signal | Example |
|------|--------|---------|
| **Document** | Produces a markdown artifact (spec, plan, report) | PRD, architecture doc, audit report |
| **Action** | Performs operations on code or systems | Refactoring, migration, deployment |
| **Autonomous** | Runs end-to-end without interaction | Story generation, code review, trace |
| **Interactive** | Needs ongoing user input throughout | Brainstorming, discovery sessions |
| **Meta** | Orchestrates other workflows | Greenfield setup, sprint planning |

Ask at most 2-3 clarifying questions based on what's UNCLEAR. Skip questions where the answer is obvious from context. Good questions:

- "Should this run autonomously once started, or does it need user decisions along the way?"
- "What's the input — a user prompt, a file, a page route, a PR number?"
- "What's the deliverable — a document, code changes, a report, or just console output?"
- "Is this project-specific or should it work across all BMAD projects?"

Do NOT ask:
- "How many steps should it have?" (you decide)
- "What should the frontmatter look like?" (you decide)
- "Should it have a template?" (you decide)

### 3. Confirm Understanding

Present a concise summary (not a menu, not a checklist — a paragraph):

```
Got it. I'll build a {type} workflow called "{name}" that {one-sentence description}. 
Input: {what triggers it}. Output: {what it produces}. 
It'll run {autonomously / with checkpoints at X and Y}.

Building it now.
```

Wait for the user to confirm or adjust. If they say anything affirmative ("yes", "go", "y", "perfect", "do it"), proceed immediately. If they correct something, adjust and re-confirm.

### 4. Capture State Variables

Extract and store:

- `{wf_name}` — kebab-case workflow name (e.g., `audit-pr-coverage`)
- `{wf_slug}` — same as name for workflows
- `{wf_description}` — CLI description string (used in frontmatter and command generation)
- `{wf_type}` — document | action | autonomous | interactive | meta
- `{wf_inputs}` — what the workflow receives (user prompt, file path, PR number, etc.)
- `{wf_outputs}` — what it produces (document, code changes, report, etc.)
- `{wf_step_outline}` — your designed step breakdown (step name + one-line goal for each)
- `{wf_needs_template}` — boolean: does this workflow produce a document with a consistent structure?
- `{wf_needs_checklist}` — boolean: does the output need validation criteria?
- `{wf_autonomous}` — boolean: should it run without user input after initialization?
- `{wf_category}` — which category directory: implement | verify | design | meta
- `{wf_target_dir}` — where to create the workflow. Default: `{bmad_root}/custom/workflows/{wf_category}/{wf_name}`

### 5. Proceed to Investigation

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-workflow/steps/step-02-investigate.md`

---

## SUCCESS METRICS

- User described a workflow idea
- Agent asked at most 2-3 clarifying questions
- Summary was confirmed in a single exchange
- All state variables captured
- Total interaction: under 4 messages
