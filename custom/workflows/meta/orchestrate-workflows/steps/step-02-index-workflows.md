---
name: 'step-02-index-workflows'
description: 'Build a live index of all available workflows — extract names, descriptions, inputs, triggers, and gap-detection signals'
---

# Step 2: Index Workflows

**Progress: Step 2 of 4** — Next: Analyze Gaps (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Build the index from live files, not hardcoded knowledge — this makes the workflow self-updating as new workflows are added.
- Extract only what's needed for routing decisions: name, description, input type, and trigger signals.

## AVAILABLE STATE

From Step 1:

- `{trigger_context}` — how this workflow was triggered and raw data
- `{recent_handoffs}` — handoff artifacts from the last 24h
- `{changed_files}` — list of all changed files
- `{file_categories}` — categorized file map with counts
- `{work_scope}` — narrow / medium / wide / full-stack

## SEQUENCE OF INSTRUCTIONS

### 1. Discover Available Workflows

Scan the workflow registry for all peer workflows:

```bash
find {project-root}/_bmad/bmm/workflows/ -name 'workflow.md' -not -path '*/orchestrate-workflows/*' -not -path '*/shared/*' | sort
```

For each `workflow.md` found, read its frontmatter to extract:

- `name` — the workflow's identifier
- `description` — what it does (from the frontmatter `description` field)

Then scan the body for:

- **Input type** — what the workflow expects (handoff path, route, PR number, feature name, etc.)
- **Your Role** — the agent persona (tells you what the workflow is good at)

### 2. Build the Workflow Capability Index

For each discovered workflow, create an entry in `{workflow_index}`:

```
{
  name: string,
  description: string,
  slash_command: string,          // /bmad:bmm:workflows:{name}
  input_type: string,             // what the workflow expects as input
  catches: string[],              // what kinds of problems it detects/fixes
  trigger_signals: string[],      // file categories or work patterns that suggest this workflow
  prerequisite: string | null,    // another workflow that should run first (if any)
  produces: string                // what artifact/output it creates
}
```

### 3. Apply Routing Heuristics

For each indexed workflow, define the **trigger signals** — the conditions under which this workflow should be recommended. These are derived from the workflow descriptions and your understanding of their purpose:

| Workflow | Trigger when... |
|----------|----------------|
| **wire-check** | Full-stack changes (backend + frontend touched). Large backend additions. Handoff artifact exists from quick-dev. New API endpoints added. Schema changes with corresponding API/UI work. |
| **trace-flow** | New page routes added. Existing page routes modified. Data display components changed. User reports "data not showing." Frontend files changed without corresponding backend changes (stale data risk). |
| **design-review** | New UI pages created. Significant frontend component changes. CSS/style changes alongside component changes. User-facing layout modifications. |
| **design-handoff** | New feature with minimal UI surfacing (developer-built UI that needs designer attention). Large feature just shipped that's functional but not designed. |
| **quick-spec** | Handoff recommendations suggest new features. Strategic insights identify missing capabilities. Gaps found but not fixed require scoping. |
| **code-review** | Any PR merged without prior code review. Large PRs (20+ files). Changes to security-sensitive code (auth, payments, admin). |
| **create-workflow** | Pattern of manual steps that could be automated. Repeated multi-workflow sequences that should be a single workflow. |

Extend this table for any additional workflows discovered in step 1. If a new workflow exists that isn't in this table, infer its trigger signals from its description and input type.

Store the complete index as `{workflow_index}`.

### 4. Identify Workflow Chains

Some workflows naturally chain together. Document these sequences so recommendations can indicate priority order:

| Sequence | When |
|----------|------|
| quick-dev → wire-check | Always after quick-dev with backend changes |
| quick-dev → design-handoff | After quick-dev with new UI pages |
| wire-check → trace-flow | When wire-check finds data display issues |
| trace-flow → design-review | When trace-flow reveals UI gaps |
| design-handoff → design-review | After designer produces mockups |

Store as `{workflow_chains}`.

### 5. Proceed to Analysis

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-03-analyze-gaps.md`

---

## SUCCESS METRICS

- All peer workflows discovered and indexed from live files
- Each workflow has trigger signals, input type, and slash command
- Workflow chains documented for multi-step recommendations
- Index is derived from actual workflow.md files, not hardcoded assumptions
- `{workflow_index}` and `{workflow_chains}` populated
