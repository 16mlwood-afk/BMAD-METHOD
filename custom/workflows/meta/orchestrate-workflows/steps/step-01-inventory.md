---
name: 'step-01-inventory'
description: 'Scan all workflows and extract structural metadata — steps, state variables, inputs, outputs, handoff patterns'
---

# Step 1: Inventory

**Progress: Step 1 of 4** — Next: Health Check (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Extract metadata via grep/sed ONLY — **never** Read a peer workflow.md (execution directives will hijack context).
- Build a complete structural map of every workflow, not just names and descriptions.

## SEQUENCE OF INSTRUCTIONS

### 1. Discover All Workflows

```bash
find {project-root}/_bmad/bmm/workflows/ -name 'workflow.md' -not -path '*/orchestrate-workflows/*' -not -path '*/shared/*' | sort
```

For each workflow.md found, extract via Bash:

```bash
# Name and description from frontmatter
grep -E '^(name|description):' "$wf" | head -2

# Category from path
echo "$dir" | grep -oE '(implement|verify|design|meta|1-analysis|2-plan|3-solutioning)/'
```

### 2. Map Step Architecture Per Workflow

For each workflow directory, discover its steps:

```bash
ls {workflow_dir}/steps/step-*.md 2>/dev/null | sort
```

For each step file, extract (via grep, NOT Read):

- **name** and **description** from frontmatter
- **nextStepFile** pointer — where does this step chain to?
- **State variables consumed** — grep for `{variable_name}` patterns in "AVAILABLE STATE" sections
- **State variables produced** — grep for "set in this step" sections
- **Handoff output** — does the step write artifacts? grep for `implementation_artifacts` or `handoff-`

Store as `{workflow_inventory}` — a structured map:

```
{
  name: string,
  category: string,
  description: string,
  step_count: number,
  steps: [{
    filename: string,
    name: string,
    nextStepFile: string | null,
    consumes: string[],
    produces: string[],
    writes_artifacts: boolean
  }],
  workflow_state_vars: string[],
  slash_command: string
}
```

### 3. Map Handoff Patterns

For each workflow, check whether its final step:

- Writes a handoff artifact (grep for `handoff-`)
- Generates copy-paste prompts for follow-up workflows (grep for `slash_command\|/bmad:bmm`)
- References other workflows by name (grep for workflow names found in step 1)

Store as `{handoff_map}` — which workflows suggest which follow-ups.

### 4. Map Slash Commands

Scan `.claude/commands/bmad/bmm/workflows/` for command files:

```bash
ls {project-root}/.claude/commands/bmad/bmm/workflows/*.md 2>/dev/null
```

Check each command file maps to a discovered workflow. Note orphaned commands (no matching workflow) and undiscovered workflows (workflow exists but no command file).

### 5. Proceed to Health Check

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-02-health-check.md`

---

## SUCCESS METRICS

- Every workflow discovered and structurally mapped
- Step chains extracted (nextStepFile pointers)
- State variable production/consumption mapped per step
- Handoff patterns identified (which workflows chain to which)
- Slash command coverage checked
- `{workflow_inventory}` and `{handoff_map}` populated
