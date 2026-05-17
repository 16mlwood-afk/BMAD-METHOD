---
name: 'step-04-execute-followups'
description: 'Auto-execute critical/recommended workflows via Agent sub-agents; present optional workflows as copy-paste prompts'
---

# Step 4: Execute Follow-ups

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- **Critical and Recommended workflows are auto-executed** via the Agent tool — not presented as copy-paste prompts.
- **Optional workflows are presented as copy-paste prompts** for the user to run if desired.
- Chain-dependent workflows execute sequentially (wait for the previous to complete before starting the next).
- Independent workflows within the same tier execute in parallel (multiple Agent calls in one message).
- Cap auto-execution at 3 workflows. If more than 3 are critical/recommended, demote the lowest-scored to optional.

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

### 1. Classify Workflows for Execution vs. Prompt

Split `{gap_analysis}` into two groups:

- **Auto-execute:** all entries with `priority_tier` = "critical" or "recommended" (max 3)
- **Copy-paste:** all entries with `priority_tier` = "optional", plus any critical/recommended that exceed the cap of 3

If auto-execute is empty (all optional), skip to section 4.

### 2. Determine Execution Order

For the auto-execute group:

1. **Chain-dependent workflows** must run sequentially. If workflow B depends on workflow A (noted in `chain_position`), A must complete before B starts.
2. **Independent workflows** (no chain dependency between them) can run in parallel — spawn multiple Agent calls in a single message.

Build an execution plan:

```
execution_rounds = []

Round 1: [all workflows with no chain predecessor]
Round 2: [workflows whose predecessor was in round 1]
Round 3: [workflows whose predecessor was in round 2]
```

Most cases will be a single round (independent workflows).

### 3. Execute via Agent Sub-agents

For each round, spawn Agent sub-agents for every workflow in that round. Wait for the round to complete before starting the next round.

**Agent configuration per workflow:**

```
Agent({
  description: "{workflow_name}: {rationale} (one short phrase)",
  subagent_type: "general-purpose",
  isolation: "{see isolation rules below}",
  prompt: "{see prompt template below}"
})
```

**Isolation rules:**

| Workflow | Isolation |
|----------|-----------|
| wire-check | `"worktree"` — edits code to fix wiring issues |
| quick-dev | `"worktree"` — implements changes |
| code-review | omit — read-only review |
| trace-flow | omit — read-only analysis |
| design-review | omit — read-only audit |
| design-handoff | omit — writes output artifact only |
| quick-spec | omit — writes output artifact only |
| Any workflow that edits source code | `"worktree"` |
| Any workflow that only reads or writes artifacts | omit |

**Prompt template:**

The prompt must be fully self-contained. The sub-agent has zero context from this session.

```
You are in the {project-root} repository. Run the following BMAD workflow by invoking it via the Skill tool:

Skill: bmad:bmm:workflows:{workflow_name}
Args: {input_value}

Context for why this workflow is being run:
- Source: {trigger_context summary — what work was just completed}
- Changed files: {changed_files summary — categories and counts}
- Rationale: {rationale — why this workflow was recommended}
- Handoff artifact: {handoff_path if applicable}

Execute the workflow fully and autonomously. Report your findings and any changes made when complete.
```

**Parallel execution:** If round N has multiple independent workflows, spawn ALL of them in a single message with multiple Agent tool calls. Do not serialize independent workflows.

**Collect results:** Store the result summary from each Agent as `{execution_results}` — a list of `{ workflow_name, status: "completed" | "failed", summary }`.

### 4. Generate Copy-Paste Prompts for Optional Workflows

For each entry in the copy-paste group (optional tier), generate a prompt block using this format:

```
┌─────────────────────────────────────────────────────────┐
│  > {workflow_name}  (optional)
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

**Prompt generation rules:**

1. **Start with the slash command:** `/bmad:bmm:workflows:{workflow_name}`
2. **Include the input inline:** append the workflow's expected input directly after the command
3. **For handoff-based workflows** (wire-check): include the absolute path to the handoff artifact
4. **For route-based workflows** (trace-flow, design-review): include the route path derived from `{changed_files}`
5. **For context-dependent workflows** (code-review): include the PR number or branch name
6. **Never include session-specific context** — no "the changes we just made" or "as discussed"

### 5. Write Orchestration Report

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

## Executed Workflows

{for each entry in {execution_results}:}

### {n}. {workflow_name} — {status}

**Priority:** {priority_tier}
**Why:** {rationale}
**Result:** {summary from agent}

## Optional Follow-ups (Not Executed)

{for each optional workflow, the copy-paste prompt}

## Skipped Workflows

{list any workflows that were considered but excluded, with one-line reason:}
- {workflow_name}: {why excluded}
```

**File naming:** `orchestration-{slug}-{date}.md`

### 6. Present Summary to User

Display a concise execution summary — this is the primary output.

**Output format:**

```
## Orchestration Complete

Based on {work_scope} changes across {file count} files ({category summary}):

### Executed

{for each executed workflow:}
- **{workflow_name}** ({priority_tier}) — {one-line result summary}

{if any optional workflows exist:}

### Optional Follow-ups

{display copy-paste prompt blocks from section 4}

**Report saved:** {report_file_path}
```

**If no recommendations:**

```
No follow-up workflows needed — the changes are self-contained.

{work_scope} scope, {file count} files, categories: {list}.
No trigger signals matched any available workflow.
```

### 7. Self-Assessment

Before finishing, verify:

- [ ] Every critical/recommended workflow was executed (not just prompted)
- [ ] Chain-dependent workflows ran in the correct order
- [ ] Independent workflows were parallelized where possible
- [ ] Optional workflows have copy-pasteable prompts (not executed)
- [ ] Each execution result was collected and summarized
- [ ] Report file was written to `{implementation_artifacts}`
- [ ] Summary was presented directly to the user

---

## SUCCESS METRICS

- Critical/recommended workflows executed via Agent, not just prompted
- Chain dependencies respected (sequential execution)
- Independent workflows parallelized within each round
- Max 3 auto-executed workflows per run
- Optional workflows presented as self-contained copy-paste prompts
- Execution results collected and summarized
- Report written to implementation artifacts
- Summary presented directly to the user

## FAILURE MODES

- Generating copy-paste prompts for critical/recommended workflows instead of executing them
- Executing optional workflows without user consent
- Running chain-dependent workflows in parallel (B before A completes)
- Serializing independent workflows that could run in parallel
- Not passing sufficient context in the Agent prompt (sub-agent can't find the workflow or inputs)
- Exceeding 3 auto-executions (context window pressure)
- Not using `isolation: "worktree"` for workflows that edit source code
- Recommending the same workflow that was already the trigger source
