# Step 1: Detect and Load Versions

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Do NOT skip version detection — the diff drives every downstream decision

## YOUR TASK:

Load the current and previous policy versions, identify which design briefs and pages are affected.

## DETECTION SEQUENCE:

### 1. Load current policy

```bash
cat {project_knowledge}/design-policy.md 2>/dev/null || cat {project-root}/docs/design-policy.md 2>/dev/null
```

If NOT found: **abort** — "No design-policy.md found. Run `/bmad:bmm:workflows:create-design-policy` first."

Parse frontmatter:
- `version` → `{policy_version_current}`
- `last_updated` → note the date
- `status` → if "draft", warn: "Policy is still in draft. Changes won't be applied until status is 'approved'. Continue anyway?"

Store full contents as `{policy_current}`.
Set `{policy_path}` to the file path.

### 2. Load previous policy version

Get the previous version from git history:

```bash
git log --oneline --follow -- {policy_path} | head -10
```

If only one commit exists (policy was just created):
- Set `{policy_previous}` = empty
- Set `{policy_version_previous}` = 0
- Report: "This is the first version of the policy — no previous version to diff. All existing pages are effectively 'version 0' (no policy). Every page needs at least a Level 1 assessment."

If multiple commits exist:
```bash
git show HEAD~1:{policy_path_relative_to_repo_root}
```
- Parse frontmatter for `version` → `{policy_version_previous}`
- Store contents as `{policy_previous}`

### 3. Check the changelog section

If the policy has a section 10 (Changelog), read it to get the author's summary of what changed between versions. Store as `{policy_changelog}`. This is advisory — the structured diff in step 02 is authoritative, but the changelog provides intent.

### 4. Find affected design briefs

Scan for design-handoff output briefs that track their policy version:

```bash
find {implementation_artifacts} -name "design-brief-*.md" 2>/dev/null
find {implementation_artifacts} -name "handoff-*.md" 2>/dev/null
```

For each brief found:
- Read frontmatter for `design_policy_version`
- If `design_policy_version` < `{policy_version_current}`: add to `{affected_briefs}`
- If `design_policy_version` is missing: treat as version 0 (pre-policy), add to `{affected_briefs}`

### 5. Identify affected pages

From `{affected_briefs}`, extract the `feature` or route each brief covers. Also scan the routes directory:

```bash
find {project-root}/src/routes -maxdepth 2 -name "+page.svelte" -o -name "+page.ts" 2>/dev/null | head -30
```

Build `{affected_pages}` — a list of:

| Page / Route | Brief File | Policy Version Used | Gap |
|-------------|-----------|-------------------|-----|
| {route} | {brief path or "none"} | {version} | {current - used} |

### 6. Present findings

"Design policy is at version **{policy_version_current}** (updated {last_updated}).

**{count} pages are behind:**
{table of affected pages with version gaps}

**{count} pages have no brief on record** — these will be assessed based on their implementation vs the current policy.

Proceeding to diff the policy changes."

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/design/apply-design-policy-change/steps/step-02-diff-policy.md`.

In autonomous mode: proceed immediately.
