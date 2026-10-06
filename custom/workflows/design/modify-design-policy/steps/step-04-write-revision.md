# Step 4: Write the Revised Policy

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Apply ONLY the deltas in `{proposed_deltas}`. Every other byte of the file must be preserved exactly.
- Bump version. Update `last_updated`. Append a one-line entry to the change log if the policy has one.
- After writing, surface the downstream impact list so the user has a clear next step.

## YOUR TASK:

Apply the confirmed deltas to `{current_policy}`, bump metadata, write the file, and report the result.

## WRITING SEQUENCE:

### 1. Apply the deltas

For each entry in `{proposed_deltas}`:

- Locate the exact `Before:` slice in `{current_policy}`
- Replace it with the `After:` text
- Preserve surrounding whitespace, headings, and adjacent content

If any `Before:` slice cannot be located exactly, STOP. Report the mismatch and do not write a partial revision. This usually means the policy was edited between step-01 and now — re-run from step-01.

### 2. Update frontmatter

- `version` = `{current_version + 1}`
- `last_updated` = `{date}`
- If a `change_log` field exists, append: `- vN (YYYY-MM-DD): <one-line summary of the change, e.g. "Tightened tone toward declarative, removed multi-color status taxonomy">`
- Leave `created`, `created_by`, `source`, `consumed_by`, and `precedence` unchanged

### 3. Write the file

Write the revised content to `{output_path}` (same path as `{policy_path}`).

### 4. Verify

Re-read the file and confirm:

- The deltas are applied
- No section outside `{proposed_deltas}` was touched
- Frontmatter version, last_updated, and change_log are updated

If verification fails, STOP and report. Never silently leave a partial revision.

### 5. Report the result

Present a tight summary:

```
Updated `{output_path}` (v`{current_version}` → v`{current_version + 1}`)

Sections changed:
- <section 1>
- <section 2>
- ...

Downstream artifacts that may need re-baselining:
- <impact 1>
- <impact 2>
- ...

Next step (only if downstream artifacts exist):
Run `/bmad:bmm:workflows:apply-design-policy-change` to generate correction briefs for each.
```

If `{downstream_impact}` is empty, omit the last two sections and end at "Sections changed".

In autonomous mode: same report format, no follow-up prompt.

### 6. Auto-trigger apply-design-policy-change (autonomous mode only)

When `autonomous_mode` is `true` AND `{downstream_impact}` is non-empty, do NOT stop at the report. Immediately invoke `/bmad:bmm:workflows:apply-design-policy-change` with the just-written policy file as input. The autonomy contract states: "Make expert-level decisions and proceed" — leaving impacted pages flagged but unactioned violates that contract.

Pass the following context to the apply-workflow:

- `{policy_path}` — the file just written
- `{from_version}` = `{current_version}` (the pre-revision version)
- `{to_version}` = `{current_version + 1}` (the new version)
- `{downstream_impact}` — the list surfaced in §5

The apply-workflow classifies each impacted page into restyle / component-refresh / full-handoff and emits scoped briefs. Those briefs become the next actionable artifact for the user, so the loop closes within a single autonomous run.

In interactive mode (autonomous_mode = false): do NOT auto-invoke. The report's "Next step" line is the user's prompt to invoke manually if they want scoped briefs — they may prefer to inspect the policy diff first.

**Halt condition:** If `apply-design-policy-change` is missing from the workflow set OR errors at startup, log the failure under "Sections changed" and continue — never silently swallow the auto-trigger. The user must know the loop did not close.

## SUCCESS METRICS:

- Only the sections in `{proposed_deltas}` differ between the old and new file
- Version is bumped exactly by 1
- `last_updated` matches `{date}`
- A reader can diff old vs new and see only intentional changes
- Downstream impact is surfaced (not buried)

## FAILURE MODES:

- Rewriting sections that weren't in `{proposed_deltas}` (scope creep)
- Forgetting to bump version or update `last_updated`
- Writing the file when a `Before:` slice didn't match exactly (silent corruption)
- Hiding the downstream impact list (user ships the policy change without realizing existing pages need updating)
- Adding generic "modernization" tweaks beyond the confirmed deltas
