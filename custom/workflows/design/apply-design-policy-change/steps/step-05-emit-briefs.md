# Step 5: Emit Briefs

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Every brief must include `design_policy_version` in its frontmatter — this is how future runs of this workflow detect stale pages
- Write briefs to `{implementation_artifacts}/` with clear naming
- In autonomous mode: write all briefs without pausing, present a summary at the end

## CONTEXT BOUNDARIES:

- `{page_action_map}` from step 04 defines what each page needs
- `{policy_current}` is the target policy
- `{section_diffs}` provides the specific changes to reference

## YOUR TASK:

Generate a scoped brief for each affected page. The brief type matches the action level.

## BRIEF GENERATION:

### Restyle Brief (Level 1)

**Filename:** `{implementation_artifacts}/restyle-{page-slug}-policy-v{version}-{date}.md`

```markdown
---
type: restyle-brief
page: {route}
design_policy_version: {policy_version_current}
previous_policy_version: {policy_version_used_by_page}
date: {date}
priority: {P1/P2/P3}
scope: visual-only
---

# Restyle Brief: {page name}

**Policy change:** v{old} → v{new}
**Scope:** Visual properties only — keep information architecture and workflow intact.

## What Changed in the Policy

{List only the sections relevant to this page, with specific before/after}

## Changes Required

| Element | Current | Target | CSS/Tailwind Change |
|---------|---------|--------|-------------------|
| {element} | {current value} | {new value} | {exact class change} |

## What NOT to Change

- Page layout and section structure
- Component hierarchy
- Data display order
- Navigation behavior

## Verification

After applying changes, the page should pass a design-review against policy v{version} with zero new findings in the affected sections.
```

### Component Refresh Brief (Level 2)

**Filename:** `{implementation_artifacts}/component-refresh-{page-slug}-policy-v{version}-{date}.md`

```markdown
---
type: component-refresh-brief
page: {route}
design_policy_version: {policy_version_current}
previous_policy_version: {policy_version_used_by_page}
date: {date}
priority: {P1/P2/P3}
scope: component-level
shared_components: [{list of shared components affected}]
---

# Component Refresh Brief: {page name}

**Policy change:** v{old} → v{new}
**Scope:** Update specific components to match new policy patterns. Page layout stays intact.

## Policy Sections That Changed

{Only sections relevant to this page's components}

## Components to Update

### {Component name} {shared: yes/no}

**Current pattern:** {what it looks like now}
**New policy pattern:** {what the policy now requires}
**Change:** {specific implementation change}
**Pages affected:** {list of pages using this component, if shared}

{Repeat for each component}

## Hard Failure Fixes

{If the page currently violates a new hard failure, list it here with the specific fix}

## What NOT to Change

- Page layout and section ordering
- Information architecture
- Data flow and API usage

## Verification

After applying changes, run design-review for this page. Zero hard-failure violations and zero P1 findings in sections {affected section numbers}.
```

### Full Handoff Brief (Level 3)

**Filename:** `{implementation_artifacts}/handoff-rerun-{page-slug}-policy-v{version}-{date}.md`

```markdown
---
type: handoff-rerun-brief
page: {route}
design_policy_version: {policy_version_current}
previous_policy_version: {policy_version_used_by_page}
date: {date}
priority: {P1/P2/P3}
scope: structural
previous_brief: {path to old brief, or "none"}
---

# Handoff Rerun Brief: {page name}

**Policy change:** v{old} → v{new}
**Scope:** Full design-handoff rerun. The page's structure or mode behavior no longer aligns with the policy.

## Why This Page Needs a Full Handoff

{Explain which structural policy changes invalidate the current design}

## What Changed

| Policy Section | Old Rule | New Rule | Impact on This Page |
|---------------|---------|---------|-------------------|
| {section} | {old} | {new} | {how this affects the page} |

## Instructions for design-handoff

Run `/bmad:bmm:workflows:design-handoff` for route `{route}` with these notes:

1. **Do NOT reference the previous brief** at `{previous_brief}` for layout or structure — it was designed under policy v{old} and is now obsolete.
2. **DO reference it for domain context** — the data model, API surface, and user context sections are still valid.
3. **Apply policy v{new} for all visual and structural decisions.**
4. **Page mode is now:** {operational | analytical | hybrid} per updated policy section 9.

## Previous Brief Location

`{previous_brief}` — contains valid domain data and user context. Layout and visual direction sections are obsolete.
```

## WRITE ALL BRIEFS:

For each entry in `{page_action_map}`, generate the appropriate brief type and write it to disk. Track all output paths in `{output_briefs}`.

## FINAL SUMMARY:

"**Policy migration complete (v{old} → v{new}).**

**Briefs generated: {count}**

| Brief | Page | Type | Priority | Path |
|-------|------|------|----------|------|
| {name} | {route} | {restyle/component/handoff} | {P1/P2/P3} | {path} |

**Shared component tasks:**
{list of components that affect multiple pages — update these first}

**Execution order:**
1. Update shared components (affects {N} pages)
2. Apply P1 fixes (hard failure violations)
3. Apply P2 restyles and component refreshes
4. Run design-handoff for P2/P3 structural refreshes
5. Schedule P3 items for next sprint

**Next steps:**
- For restyle briefs: implement directly or pass to `design-implement`
- For component refreshes: update shared components first, then page-specific patches
- For full handoffs: run `/bmad:bmm:workflows:design-handoff` for each affected route"

## SUCCESS METRICS:

- Every affected page has exactly one brief
- Every brief has `design_policy_version` in frontmatter
- Shared component dependencies are identified and consolidated
- Priority ordering reflects hard-failure urgency
- No brief prescribes changes outside its scope (a restyle brief must not restructure)

## FAILURE MODES:

- Generating a full handoff brief when a restyle would suffice (over-scoping)
- Missing a shared component that affects multiple pages (under-scoping)
- Writing a restyle brief for a page that violates a new hard failure (wrong level)
- Not including `design_policy_version` in output frontmatter (breaks future detection)
