# Step 1: Load the Current Design Policy

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Do NOT skip this step. If no policy exists, this workflow is the wrong one — route to `create-design-policy` instead.

## YOUR TASK:

Locate and load the current design policy so subsequent steps have full context.

## LOAD SEQUENCE:

### 1. Find the policy

```bash
ls {project_knowledge}/design-policy.md 2>/dev/null
find {project-root} -name "design-policy.md" -not -path "*node_modules*" -not -path "*.claude/worktrees*" 2>/dev/null | head -5
```

If multiple are found, prefer `{project_knowledge}/design-policy.md` and confirm with the user before proceeding.

If NONE is found:
- **STOP** — this workflow is not applicable.
- Tell the user: "No design policy found. Use `/bmad:bmm:workflows:create-design-policy` first, then come back if you need to refine it."
- Exit the workflow.

### 2. Read the policy completely

- Set `{policy_path}` to the file path
- Set `{current_policy}` to the full file contents
- Set `{current_version}` by reading the `version` field from the frontmatter (default to 1 if not present)
- Set `{output_path}` = `{policy_path}` (we revise in place)

### 3. Summarize the current direction

In 4-6 lines, summarize what the policy currently says about:

- Visual direction (the one-sentence identity)
- Tone & register
- Density preference
- Primary layout pattern
- Status system constraints
- Top 2-3 hard failures

This summary anchors the rest of the workflow and helps the user spot if the policy they're remembering matches the policy on disk.

### 4. Present and confirm

"Loaded design policy at `{policy_path}` (version `{current_version}`). Current direction:

`<summary from step 3>`

Tell me what you want to change. The more concrete the better — 'too casual' is workable, 'replace the badge system' is better."

In autonomous mode: skip the prompt and proceed directly to step-02 using the user's original request as `{change_description}`.

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/design/modify-design-policy/steps/step-02-identify-deltas.md`.
