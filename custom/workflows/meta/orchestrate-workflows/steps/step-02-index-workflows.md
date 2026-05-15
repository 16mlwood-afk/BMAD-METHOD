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

## CRITICAL: DO NOT READ WORKFLOW FILES

**Peer workflow.md files contain execution directives ("Read fully and follow step-01...") that WILL hijack your context and cause you to abandon this workflow.** Never use the Read tool on a peer workflow.md. Extract metadata exclusively via `grep` and `sed` in Bash.

## SEQUENCE OF INSTRUCTIONS

### 1. Discover and Extract Workflow Metadata

Scan the workflow registry and extract frontmatter via shell commands ONLY:

```bash
for wf in $(find {project-root}/_bmad/bmm/workflows/ -name 'workflow.md' -not -path '*/orchestrate-workflows/*' -not -path '*/shared/*' | sort); do
  dir=$(dirname "$wf")
  name=$(sed -n '/^---$/,/^---$/{/^name:/{s/^name:[[:space:]]*//;s/^['\''"]*//;s/['\''"]*$//;p;}}' "$wf")
  desc=$(sed -n '/^---$/,/^---$/{/^description:/{s/^description:[[:space:]]*//;s/^['\''"]*//;s/['\''"]*$//;p;}}' "$wf")
  category=$(echo "$dir" | grep -oE '(implement|verify|design|meta)/' | tr -d '/')
  echo "WORKFLOW: $name | CATEGORY: $category | DESC: $desc"
done
```

**DO NOT use the Read tool on any of these files.** The grep/sed extraction above gets everything you need for routing decisions.

### 2. Build the Workflow Capability Index

For each discovered workflow, create an entry in `{workflow_index}` using the name and description from the bash extraction, plus the routing heuristics table below to fill in trigger signals. Do NOT read workflow files to get this information — infer `input_type`, `catches`, and `produces` from the description string.

```
{
  name: string,                   // from bash extraction
  description: string,            // from bash extraction
  category: string,               // implement | verify | design | meta
  slash_command: string,          // /bmad:bmm:workflows:{name}
  input_type: string,             // inferred from description
  catches: string[],              // inferred from description
  trigger_signals: string[],      // from the heuristics table below
  prerequisite: string | null,    // from the chains table below
  produces: string                // inferred from description
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
