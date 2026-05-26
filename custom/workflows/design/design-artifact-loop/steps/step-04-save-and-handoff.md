---
name: 'step-04-save-and-handoff'
description: 'Resolve output paths, write files to implementation-artifacts, update tuning state if iterating, emit the user-facing handoff summary'
---

# Step 4: Save & Hand Off

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No menus, no halting.
- Write outputs to `{implementation_artifacts}/` only — never elsewhere.
- The final user-facing message is the handoff. Keep it short, specific, and ready to paste into the next workflow.

---

## AVAILABLE STATE FROM STEP 3

- `{output_artifact_content}` — map of `output_kind` → full file content (one or two entries)
- `{output_kind}` (or both kinds, for the synthesized-review-plus-handoff case)
- `{target_slug}`, `{mode}`, `{target_label}`, `{target_route}`
- `{artifact_path}` (source), `{repo_url}` (if provided)
- `{date}` from config

---

## SEQUENCE OF INSTRUCTIONS

### 1. Resolve Output File Paths

For each entry in `{output_artifact_content}`, build the absolute path using the filename conventions:

| `{output_kind}` | Filename |
|---|---|
| `screen-review` | `{implementation_artifacts}/screen-review-{target_slug}-{date}.md` |
| `design-handoff` | `{implementation_artifacts}/design-handoff-{target_slug}-{date}.md` |
| `design-response` | `{implementation_artifacts}/design-response-{target_slug}-{date}.md` |

If `{mode}` = `refine-screen`, prefix the slug portion with `refine-` to distinguish from a fresh design-handoff against the same target:

- `design-handoff-refine-{target_slug}-{date}.md`
- `screen-review-refine-{target_slug}-{date}.md` (when synthesized in this run)

`{date}` is the system date in `YYYY-MM-DD` format from config.

If a file with the resolved name already exists (a same-day rerun), append `-r2`, `-r3`, etc.:

- `screen-review-reclaim-avask-2026-05-26.md`
- `screen-review-reclaim-avask-2026-05-26-r2.md` (rerun later same day)

Set `{output_paths}` to the list of resolved absolute paths.

### 2. Write the Output Files

For each `(kind, content)` pair in `{output_artifact_content}`, write the file at the corresponding resolved path. Use the Write tool. Verify each write succeeded before proceeding.

If `{implementation_artifacts}` does not exist (rare — should be created by the project's first BMAD workflow run), create it first:

```bash
mkdir -p {implementation_artifacts}
```

### 3. Update the Tuning State File (if iterating)

The tuning state lives at:

```
{implementation_artifacts}/design-tuning-state-{target_slug}.md
```

Check if it exists:

- **If it exists** and this run is in `refine-screen` mode: append a new iteration block per the template at `templates/design-tuning-state.md` → "Iteration block" section. Carry forward `final_accepted_direction` (if previously set), update `previous_failures`, `fixed_issues`, `current_open_issues` from the just-produced output.
- **If it does NOT exist** and this run is in `refine-screen` mode: create it from `templates/design-tuning-state.md`. This is iteration 1.
- **If `{mode}` is anything else**: do NOT create or touch the tuning state. It tracks iteration chains, not first-time handoffs or reviews.

Set `{tuning_state_path}` to the resolved absolute path if a file was created or updated; otherwise leave empty.

### 4. Compute the GitHub URL (if applicable)

If `{repo_url}` was provided in the handoff block, build the GitHub URLs for the output files for use in the handoff summary:

```
{github_url_for_output} = {repo_url}/blob/main/{output_path_relative_to_repo_root}
```

If the output is not committed yet (it won't be — this workflow only writes to disk; commits are a separate user action), the URL will 404 until the user commits the file. Note this in the summary.

### 5. Emit the User-Facing Handoff Summary

Print a single short message — this is the workflow's deliverable to the user. Keep it tight; no preamble, no walls of explanation. The user will paste / forward this to the next workflow.

**Template:**

```
design-artifact-loop run complete.

Mode: {mode}
Target: {target_label} ({target_route})
Source artifact: {artifact_path}

Wrote:
- {output_path_1}{ if two outputs, second line for output_path_2 }

{ if {tuning_state_path} is set: Updated tuning state: {tuning_state_path} }

Sources consulted: docs/design-policy.md{ if loaded }, sister skills: {names}{ if any }, screenshots: {N} file(s){ if any }
Evidence gaps: {list, or "none"}

Next agent (paste this):

Hand off to {next_workflow}:
{one-line directive built from the output content — e.g., "Implement the changes in design-handoff-refine-reclaim-avask-2026-05-26.md" or "Re-review after implementation"}
```

Where `{next_workflow}` is decided from the table below:

| `{output_kind}` | `{mode}` | `{next_workflow}` |
|---|---|---|
| `design-handoff` | `refine-screen` | `quick-dev` (or `dev-story` if a story file exists) |
| `design-handoff` | `policy-lift` | `quick-dev` |
| `design-handoff` | `design-from-brief` | `quick-dev` |
| `design-response` | `design-from-brief` | `design-artifact-loop` again, this time with the response treated as a brief (the response will land an implementation-ready handoff on second pass) |
| `screen-review` (only) | `review-only` | `design-artifact-loop` in `refine-screen` mode when the user decides to act on it |
| `screen-review` + `design-handoff` | `refine-screen` | `quick-dev` — implement the handoff |

If no next-workflow mapping is obvious (e.g., the user explicitly framed the run as exploratory), omit the "Next agent" block and just emit the file paths.

### 6. Hand Off and Stop

The workflow ends here. Do not start a new run, do not auto-invoke the next workflow, do not propose follow-ups beyond the "Next agent" block in the summary.

---

## SUCCESS METRICS

- All staged outputs were written to `{implementation_artifacts}/` and the files are non-empty.
- The tuning state file was updated only when in `refine-screen` mode.
- The handoff summary fits on one screen, names every output path, and gives the user a paste-ready directive for the next agent.
- No write occurred outside `{implementation_artifacts}/`.

## FAILURE MODES

- Writing the output to the wrong directory ("near the source artifact" rather than `{implementation_artifacts}/`). All outputs land in `{implementation_artifacts}/` regardless of where the source artifact lived.
- Overwriting an existing same-day file silently. Use `-r2`, `-r3`, etc.
- Adding extra "What I did" narration to the handoff summary. The summary is structured paths + next-workflow directive — no editorial.
- Updating the tuning state on `review-only` or `design-from-brief` runs. The state file tracks refinement iteration only.
