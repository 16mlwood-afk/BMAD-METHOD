---
name: 'step-04-wire'
description: 'Add the new workflow to sync config and verify it distributes correctly'
---

# Step 4: Wire & Verify

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Do NOT modify the sync script's logic — only add to the SYNC_DIRS array if the workflow lives outside an already-synced directory.
- Verify everything works before reporting success.

## SEQUENCE OF INSTRUCTIONS

### 1. Check Sync Coverage

The sync script at `{bmad_root}/sync-bmad-workflows.sh` has a `SYNC_DIRS` array that controls which directories get distributed to projects.

**Read the current SYNC_DIRS array.** Check if `{wf_target_dir}` is already covered:

- If the workflow is inside an existing category (`implement/`, `verify/`, `design/`, `meta/`) → it's already covered. No change needed.
- If the workflow is in a new category directory → add it to `SYNC_DIRS`.

### 2. Add to SYNC_DIRS (if needed)

If the workflow is NOT covered by an existing SYNC_DIRS entry:

a) Read `{bmad_root}/sync-bmad-workflows.sh`
b) Find the `SYNC_DIRS=( ... )` array
c) Add the new directory path to the array
d) Write the updated file

### 3. Verify Workflow Structure

Run a structural check:

```bash
ls -la {wf_target_dir}/
ls -la {wf_target_dir}/steps/

head -5 {wf_target_dir}/workflow.md

grep -n "step-0" {wf_target_dir}/steps/*.md
```

### 4. Test Command Generation

The sync script auto-generates `.claude/commands/` files from workflow frontmatter. Verify the workflow.md has the required fields for command generation:

- `name:` field in frontmatter (used as command name)
- `description:` field in frontmatter (used as command description)

The sync script's `generate_command_content()` function reads these. No manual command file creation needed.

### 5. Run Sync Check (if targets exist)

If `~/.bmad-targets` exists and has entries, run a dry check:

```bash
{bmad_root}/sync-bmad-workflows.sh --check
```

This reports what would change without modifying anything. The actual sync can be run after the user reviews.

### 6. Report Completion

Present a concise summary:

```
Workflow "{wf_name}" built and ready.

Files created:
- {wf_target_dir}/workflow.md
- {wf_target_dir}/steps/step-01-{name}.md
- ...
- {wf_target_dir}/template.md (if created)
- {wf_target_dir}/checklist.md (if created)

Sync status: {covered by existing SYNC_DIRS entry / added to SYNC_DIRS}

To distribute to all projects:
  {bmad_root}/sync-bmad-workflows.sh

To test in the current project:
  /create-workflow
```

---

## SUCCESS METRICS

- Workflow is structurally valid (all files present, step chain unbroken)
- Sync coverage confirmed (existing SYNC_DIRS entry or new one added)
- Command generation will work (frontmatter has name + description)
- User has clear next steps for distribution and testing

## FAILURE MODES

- Modifying sync script logic instead of just the SYNC_DIRS array
- Creating a manual command file instead of relying on auto-generation
- Running sync without `--check` first (modifies all target projects)
- Forgetting to verify the step chain (step N must reference step N+1)
