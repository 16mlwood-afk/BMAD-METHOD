---
name: 'step-03-build'
description: 'Autonomously create all workflow files — workflow.md, steps, template, checklist'
---

# Step 3: Build All Workflow Files

**Progress: Step 3 of 4** — Next: Wire & Verify (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Write real, complete files — no placeholders, no TODOs, no "fill in later."
- Follow the exact patterns observed in peer workflows from Step 2.
- Every file must be self-contained and production-ready.
- **Respect the context budget.** Workflows are dense instruction documents executed step-by-step by a model with a finite *usable* context (reliably ~50–65% of the advertised window, far less for reasoning). A step that is too long or too instruction-dense gets silently compressed and detail gets dropped. Build within the budget: **one job per step, ≤ ~10 hard must-dos per step.** If a step would carry more, split it. Never emit a single mega-step.

## SEQUENCE OF INSTRUCTIONS

### 1. Create Directory Structure

Create the workflow directory at `{wf_target_dir}`:

```
{wf_target_dir}/
├── workflow.md
├── steps/
│   ├── step-01-{name}.md
│   ├── step-02-{name}.md
│   └── ...
├── template.md          (if {wf_needs_template})
└── checklist.md          (if {wf_needs_checklist})
```

### 2. Write workflow.md

Create the main workflow file with:

**Frontmatter:**
```yaml
---
name: '{wf_name}'
description: '{wf_description}'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---
```

Add workflow-specific frontmatter fields as needed (following peer patterns).

**Body — follow this structure exactly:**

1. **Title and Goal** — one-sentence purpose
2. **Your Role** — who the agent becomes when running this workflow
3. **Workflow Architecture** — step-file architecture declaration, state variables, processing rules
4. **Critical Rules** — workflow-specific constraints
5. **Initialization** — config loading, input resolution, path setup
6. **Execution** — "Read fully and follow: `{path}/steps/step-01-{name}.md` to begin."

**Autonomous mode handling:**
- If `{wf_autonomous}` is true: declare in the architecture section that ALL steps run without user input
- If `{wf_autonomous}` is false: declare which steps are interactive and which are autonomous

### 3. Write Step Files

For each step in `{wf_step_design}`, create a step file:

**Frontmatter:**
```yaml
---
name: 'step-{nn}-{name}'
description: '{one-line goal}'
---
```

**Body — follow this structure:**

1. **Title with progress** — `# Step N: {Title}` + `**Progress: Step N of M** — Next: {next step name}`
2. **Rules** — standard rules block (no skipping, no optimizing, follow sequence)
3. **Context** (if needed) — what state variables are available, what was produced in prior steps
4. **Sequence of Instructions** — numbered sections with specific, actionable instructions
5. **Next Step** — "Read fully and follow: `{path}/steps/step-{nn+1}-{name}.md`" (or for the last step: output delivery instructions)
6. **Success Metrics** — how to know this step succeeded
7. **Failure Modes** (optional) — common mistakes to avoid

**Step content guidelines:**
- Be SPECIFIC. "Scan `src/routes/` for page components" not "Look at the codebase"
- Use tables for classification logic (like the anchor type table in trace-flow)
- Use code blocks for output formats
- Include shape/format examples for any data the step produces
- Reference `{state_variables}` for data from prior steps
- **Place load-bearing constraints at the top of the step file AND restate the one or two that govern an action immediately beside that action.** A critical rule buried in the middle of a long step is followed less reliably (lost-in-the-middle); don't rely on a constraint stated only in a distant global preamble.
- **Pointer over inline.** Reference a file/query the step reads on demand rather than inlining a large corpus. Keep mutually-exclusive branches in separate step files so unused paths cost zero tokens.
- **Classify each step's shape and structure it accordingly** (the context-budget decision-rule): a *read-heavy / parallelizable* step (multi-file scan, research, audit) should delegate the heavy reading to a sub-agent and consume its distilled ~1–2k-token return, so raw material never enters the orchestrator's context; a *long sequential build* keeps continuity through a durable progress/manifest artifact written between fresh-context phases; a *write-one-coherent-artifact* step stays single-threaded. Any delegated step carries an explicit handoff contract: objective, output schema, tools/sources, boundaries.

### 4. Write Template (if applicable)

If `{wf_needs_template}` is true, create `template.md` based on `{wf_template_design}`:

- Use `{{variable_name}}` placeholders that map to step outputs
- Include frontmatter for the output document (status, date, metadata)
- Structure sections logically — the most important information first
- Include brief inline guidance comments where the content is non-obvious

### 5. Write Checklist (if applicable)

If `{wf_needs_checklist}` is true, create `checklist.md` based on `{wf_checklist_design}`:

- Use `- [ ]` checkbox format
- Group by category (Structure, Content, Completeness)
- Every criterion must be objectively verifiable — no subjective quality judgments
- Tie criteria to specific template sections or output requirements

### 6. Verify File Completeness

Before proceeding, verify:

- [ ] `workflow.md` exists with valid frontmatter and all required sections
- [ ] All step files exist in `steps/` directory
- [ ] Step files reference each other correctly (step N points to step N+1)
- [ ] Last step has proper output/delivery instructions instead of a next-step reference
- [ ] Template exists if `{wf_needs_template}` (with all variable placeholders)
- [ ] Checklist exists if `{wf_needs_checklist}` (with measurable criteria)
- [ ] No placeholder text, TODOs, or incomplete sections in any file
- [ ] **Context budget respected** — no step carries more than ~10 hard must-dos or inlines a large corpus it could point to; load-bearing constraints sit at the top + point of use, not buried mid-step; read-heavy steps delegate rather than inline

### 7. Proceed to Wiring

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-workflow/steps/step-04-wire.md`

---

## SUCCESS METRICS

- All files written to disk and verified
- workflow.md follows the exact structure of peer workflows
- Step files are self-contained with clear instruction sequences
- No placeholders or incomplete content
- Template variable names match step output names
- Step chain is unbroken (each step points to the next)

## FAILURE MODES

- Writing vague step instructions ("analyze the codebase" instead of specific file paths and actions)
- Missing the initialization section in workflow.md
- Step files that assume context from other steps without declaring it
- Template variables that no step produces
- Checklist criteria that are subjective ("good documentation" instead of "each function has a JSDoc comment")
- A single over-dense mega-step (20+ must-dos, or a whole corpus inlined) that overruns the model's usable context and gets silently compressed — split it into one-job-per-step instead
