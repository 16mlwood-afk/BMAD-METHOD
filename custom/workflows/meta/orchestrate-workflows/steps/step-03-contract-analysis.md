---
name: 'step-03-contract-analysis'
description: 'Analyze cross-workflow contracts — do handoff outputs match follow-up inputs? Are workflow chains coherent?'
---

# Step 3: Contract Analysis

**Progress: Step 3 of 4** — Next: Tune (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Focus on the CONNECTIONS between workflows, not the workflows themselves (step 2 covered individual health).
- A contract mismatch is when workflow A's output doesn't match what workflow B expects as input.

## AVAILABLE STATE

From previous steps:

- `{workflow_inventory}` — structural map of all workflows
- `{handoff_map}` — which workflows suggest which follow-ups
- `{health_checks}` — individual workflow health findings

## STATE VARIABLES (set in this step)

- `{contract_map}` — verified connections between workflows
- `{coverage_analysis}` — what scenarios have workflow coverage and what doesn't

## SEQUENCE OF INSTRUCTIONS

### 1. Map Workflow Connections

Using `{handoff_map}`, build a directed graph of workflow connections:

```
workflow_A --[handoff artifact]--> workflow_B
workflow_A --[copy-paste prompt]--> workflow_C
```

For each connection, identify:

- **Output format:** What does workflow A produce? (handoff artifact path, state variables, a report file)
- **Input format:** What does workflow B expect? (a handoff path, a route, a PR number, "nothing")
- **Contract match:** Does A's output actually satisfy B's input requirements?

### 2. Verify Contract Alignment

For each connection in the graph:

**Check the handoff-to-input contract:**

- If workflow B expects a handoff path as input, does workflow A actually write a handoff artifact?
- If workflow B expects specific fields in the handoff (e.g., "PR URL", "gaps found"), does workflow A's handoff template include those fields?
- If workflow B expects a route or anchor point, does workflow A's output include one?

**Check copy-paste prompt completeness:**

- If workflow A generates a copy-paste prompt for workflow B, does that prompt include all the context workflow B needs?
- Is the slash command in the prompt correct? (matches the actual command file name)
- Are file paths in the prompt absolute or properly templated?

**Finding categories:**
- `contract-mismatch` (critical) — A's output format doesn't match B's expected input
- `incomplete-prompt` (moderate) — copy-paste prompt is missing context the target workflow needs
- `stale-reference` (moderate) — prompt references a workflow that was renamed or removed
- `missing-connection` (low) — two workflows that should chain but don't reference each other

### 3. Coverage Analysis

Assess what development scenarios have workflow coverage:

| Scenario | Expected coverage | Check |
|----------|------------------|-------|
| **New feature built** | quick-dev → wire-check → design-handoff | Does quick-dev's handoff suggest wire-check? Does wire-check suggest design-handoff when UI is involved? |
| **Bug fix shipped** | quick-dev → wire-check | Does the chain exist? |
| **UI page modified** | trace-flow or design-review | Do any workflows suggest these after UI changes? |
| **Schema change** | migration applied → wire-check | Is there a workflow that detects schema changes need wire-checking? |
| **New workflow created** | create-workflow → orchestrate-workflows | Does create-workflow suggest running orchestrate to verify the new workflow fits? |
| **Design brief produced** | design-handoff → design-review (after implementation) | Does the chain exist? |

For each scenario:
- **Covered:** the workflow chain exists and contracts align
- **Partial:** some workflows exist but the chain has gaps
- **Missing:** no workflow coverage for this scenario

### 4. Identify Redundancies

Check for workflows that overlap:

- Do any two workflows check the same things? (e.g., both wire-check and trace-flow audit dead fields)
- Do any two workflows produce the same type of output? (e.g., both produce handoff artifacts for the same scenario)
- Is the overlap intentional (different depth/focus) or accidental (copy-paste drift)?

For intentional overlaps, verify they don't contradict each other. For accidental overlaps, recommend consolidation.

### 5. Compile Contract Report

Store findings as `{contract_map}` and `{coverage_analysis}`.

### 6. Proceed to Tune

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-04-tune.md`

---

## SUCCESS METRICS

- Every workflow connection verified (output → input contract)
- Copy-paste prompts checked for completeness
- Development scenarios mapped to workflow coverage
- Redundancies identified and classified (intentional vs accidental)
- `{contract_map}` and `{coverage_analysis}` populated

## FAILURE MODES

- Only checking adjacent pairs, missing transitive chains (A → B → C where A→C is broken)
- Assuming all handoff artifacts have the same format (they don't — check each)
- Not verifying copy-paste prompts actually work (stale slash commands, missing context)
- Flagging intentional overlap as redundancy without checking if they serve different purposes
