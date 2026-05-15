---
name: 'step-04-generate-prompts'
description: 'Generate copy-pasteable follow-up prompts for clean terminals and write the orchestration report'
---

# Step 4: Generate Prompts & Deliver

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Prompts MUST be copy-pasteable into a clean terminal — no session context, no "as discussed", no relative references.
- Each prompt must include the slash command AND the input the workflow needs.
- Present the output directly to the user — don't bury it in a file they'll never read.

## AVAILABLE STATE

From previous steps:

- `{trigger_context}` — how this was triggered
- `{recent_handoffs}` — handoff artifacts from the last 24h
- `{changed_files}` — list of all changed files
- `{file_categories}` — categorized file map with counts
- `{work_scope}` — narrow / medium / wide / full-stack
- `{workflow_index}` — capability index of all available workflows
- `{gap_analysis}` — validated, prioritized workflow recommendations

## SEQUENCE OF INSTRUCTIONS

### 1. Generate Copy-Pasteable Prompts

For each entry in `{gap_analysis}`, generate a prompt block. The prompt must work in a **clean Claude Code terminal** — no memory of this session, no loaded context.

**Prompt format:**

```
┌─────────────────────────────────────────────────────────┐
│  {priority_tier_emoji} {workflow_name}  ({priority_tier})
│
│  Why: {rationale}
│  Value: {estimated_value}
│
│  Prompt (copy → clean terminal):
│  ──────────────────────────────────
│  {generated_prompt}
│  ──────────────────────────────────
└─────────────────────────────────────────────────────────┘
```

**Priority tier display:**

| Tier | Indicator |
|------|-----------|
| Critical | `>>>` |
| Recommended | `>>` |
| Optional | `>` |

**Prompt generation rules:**

1. **Start with the slash command:** `/bmad:bmm:workflows:{workflow_name}`
2. **Include the input inline:** append the workflow's expected input directly after the command
3. **For handoff-based workflows** (wire-check): include the absolute path to the handoff artifact
4. **For route-based workflows** (trace-flow, design-review): include the route path derived from `{changed_files}`
5. **For context-dependent workflows** (code-review): include the PR number or branch name
6. **Never include session-specific context** — no "the changes we just made" or "as discussed"

**Example generated prompts:**

```
/bmad:bmm:workflows:wire-check _bmad-output/implementation-artifacts/handoff-invoice-preview-2026-05-15.md

/bmad:bmm:workflows:trace-flow /invoices/[id]

/bmad:bmm:workflows:design-review /invoices/[id]

/bmad:bmm:workflows:quick-spec I need a spec for: {description of the gap from handoff}
```

### 2. Order by Priority and Chain Position

Sort the prompts:

1. First by priority tier: critical → recommended → optional
2. Within the same tier, by chain position (if part of a chain, lower position first)
3. If a workflow chain exists, note the dependency: "Run after {previous_workflow} completes"

### 3. Write Orchestration Report

Write a report to `{implementation_artifacts}/`:

```markdown
---
title: 'Orchestration: Follow-ups for {source description}'
created: '{date}'
source_handoff: '{handoff_path or "git state"}'
type: orchestration
---

# Workflow Orchestration Report

**Source:** {what triggered this analysis}
**Work scope:** {work_scope}
**Files changed:** {total count} across {category count} categories
**Date:** {date}

## File Category Breakdown

| Category | Count | Files |
|----------|-------|-------|
{for each category with files}

## Recommended Follow-ups

{for each recommendation in {gap_analysis}, ordered by priority:}

### {n}. {workflow_name} — {priority_tier}

**Why:** {rationale}
**Signals:** {matched_signals joined}
**Value:** {estimated_value}

**Prompt:**
```
{generated_prompt}
```

## Workflow Chain

{if recommendations form a chain:}
Recommended execution order:
1. {first workflow} — {why first}
2. {second workflow} — {why second}
{etc.}

{if no chain:}
These workflows are independent — run in any order.

## Skipped Workflows

{list any workflows that were considered but excluded, with one-line reason:}
- {workflow_name}: {why excluded}
```

**File naming:** `orchestration-{slug}-{date}.md`

### 4. Present to User

Display the prompts directly — this is the primary output. The report file is secondary (for reference).

**Output format:**

```
## Follow-up Workflows

Based on {work_scope} changes across {file count} files ({category summary}):

{For each recommendation, display the prompt block from step 1}

{If a chain exists:}
**Suggested order:** {workflow 1} → {workflow 2} → ...

**Report saved:** {report_file_path}
```

**If no recommendations:**

```
No follow-up workflows needed — the changes are self-contained.

{work_scope} scope, {file count} files, categories: {list}. 
No trigger signals matched any available workflow.
```

### 5. Self-Assessment

Before finishing, verify:

- [ ] Every prompt is copy-pasteable into a clean terminal without modification
- [ ] Every prompt includes the correct slash command for this project
- [ ] Every prompt includes the actual input value (not a placeholder)
- [ ] No prompt references "this session" or "what we just did"
- [ ] Recommendations are ordered by priority
- [ ] Chain dependencies are noted where applicable
- [ ] Report file was written to `{implementation_artifacts}`

---

## SUCCESS METRICS

- Prompts generated for all recommendations in `{gap_analysis}`
- Each prompt is self-contained and works in a clean terminal
- Prompts are ordered by priority tier, then chain position
- Report written to implementation artifacts
- Summary presented directly to the user
- No more than 4 prompts generated
- Zero prompts that reference session context

## FAILURE MODES

- Generating prompts that require manual editing before use
- Using placeholder values instead of real paths/routes/PR numbers
- Not presenting the prompts directly (only writing the report file)
- Generating prompts for workflows that don't exist in this project
- Recommending the same workflow that was already the trigger source
- Ordering chain-dependent workflows incorrectly (e.g., design-review before design-handoff)
