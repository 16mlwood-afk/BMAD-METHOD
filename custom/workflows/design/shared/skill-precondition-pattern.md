# Skill precondition pattern

Workflows that rely on a specific skill must halt cleanly when that skill is not loaded into the session, rather than improvising the work the skill was supposed to do. This file documents the canonical pattern.

## Why

A workflow that says "invoke skill X" but doesn't check whether X is available will degrade silently when run in a project that hasn't been synced. The output looks plausible but is missing the discipline the skill was meant to enforce — a worse failure mode than halting, because the user has no signal that something is wrong.

Skill availability cannot be inferred from the project's filesystem alone — the agent only sees skills that the session-start runtime surfaces in the available-skills list. Missing skills must be detected by the workflow itself, before any output is produced.

## Pattern

A workflow that requires a skill MUST do all of the following:

1. **Declare the requirement explicitly.** In the workflow's `SKILL ROUTING` (or equivalent) section, list each required skill with its purpose and its resolution order (artifact frontmatter → project config → available-skills fallback).
2. **Add a Gate 0 in the APPROVAL GATES section.** Gate 0 is the first gate evaluated by step 1; it fires before any input-validity, context-sufficiency, or substantive work. It halts with a fixed diagnostic that names the missing skill and points the user at `~/bmad-method-v6/sync-bmad-workflows.sh`.
3. **Distinguish portable vs project-local skills in the halt message.** Portable skills live in `~/bmad-method-v6/custom/skills/` and are distributed by the sync script; project-local skills live in `<project>/.claude/skills/` and are not distributed. The diagnostic must tell the user which case they are in so the resolution is obvious.

## Canonical Gate 0 wording

```markdown
### Gate 0 — required skills available (step 1)

For <list the modes that produce skill-dependent output>, the relevant skills declared in <SKILL ROUTING section name> must be present in the session's available-skills list before the workflow proceeds. Resolution order for <skill name>: (i) `<field>:` in <source A>; (ii) `<field>:` in <source B>; (iii) <fallback rule>.

If any required skill cannot be resolved, halt with: `"Required skill <name> not available in this project. Skills are distributed by ~/bmad-method-v6/sync-bmad-workflows.sh — run it from any session, then re-invoke this workflow. (Project-local skills must already exist under .claude/skills/; portable skills are seeded from ~/bmad-method-v6/custom/skills/.)"`

<Optional: state any modes where this gate does not fire and why.>
```

## What this pattern does not do

- It does not load skills automatically. The agent must call the `Skill` tool with the resolved name once the gate passes.
- It does not enforce a particular set of required skills across workflows — each workflow declares its own routing matrix per its scope.
- It does not replace `design-synthesize`'s Gate 5a halt (which is more granular and includes the page-mode-mandatory matrix); it complements it for workflows that don't need that level of detail.

## Distribution

This file is synced into every BMAD-targeted project by `sync-bmad-workflows.sh` as part of the `design/shared/` directory. Workflows reference it by path when explaining the pattern to the agent — e.g., "see `_bmad/bmm/workflows/design/shared/skill-precondition-pattern.md`."
