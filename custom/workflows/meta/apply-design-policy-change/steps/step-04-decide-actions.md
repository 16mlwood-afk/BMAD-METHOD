# Step 4: Decide Actions Per Level

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Every page must get exactly ONE action — no "maybe" or "TBD"
- In autonomous mode: assign actions for all pages and proceed to step 05 without pausing

## CONTEXT BOUNDARIES:

- `{page_impact_map}` from step 03 tells you each page's impact level
- `{section_diffs}` tells you what specifically changed
- `{policy_current}` is the target state all pages must comply with

## YOUR TASK:

Translate impact levels into concrete actions. Each action type has a defined deliverable.

## ACTION RULES:

### Level 1 → Restyle Brief

**Deliverable:** A short brief (< 1 page) that tells the implementer exactly what to change visually without touching structure.

**Scope:**
- CSS/Tailwind class changes only — no component restructuring
- Color, spacing, font-size, font-weight adjustments
- Tone/copy updates (error messages, empty states, labels)
- No new components, no layout changes, no information architecture changes

**Template signals:**
- "Restyle to policy v{N}"
- "Keep IA and workflow intact"
- "Change only: {specific properties}"

### Level 2 → Component Refresh

**Deliverable:** A component-scoped brief listing which components need updating and what the new pattern is.

**Scope:**
- Specific component patterns need to change (badges, filters, tables, buttons)
- May require shared component updates (affects multiple pages)
- Page layout stays the same — components within it change
- May include new hard-failure compliance fixes

**Template signals:**
- "Update {component} to match policy v{N} pattern"
- "Shared component: changes will affect pages {list}"
- "Hard failure fix: {what was violating, what it should be}"

**Shared component detection:**
If multiple pages use the same component and it needs updating, consolidate into a single component-level task rather than per-page tasks. List the shared component once, then reference it from each page's brief.

### Level 3 → Full Handoff Rerun

**Deliverable:** Trigger the `design-handoff` workflow for this page with the new policy version.

**Scope:**
- The page needs fresh design thinking — layout, IA, or mode behavior has changed
- The existing brief is obsolete — a new brief must be generated
- The designer should start from the policy, domain data, and user context — NOT from the current implementation

**Template signals:**
- "Rerun design-handoff for {route} under policy v{N}"
- "Previous brief at {path} is obsolete — do not reference its layout or structure"
- "Page mode changed from {old} to {new}"

## BUILD ACTION MAP:

`{page_action_map}`:

| Page / Route | Action | Deliverable | Priority | Notes |
|-------------|--------|------------|----------|-------|
| {route} | restyle | Restyle brief | {P1/P2/P3} | {what specifically changes} |
| {route} | component_refresh | Component brief | {P1/P2/P3} | {which components, shared?} |
| {route} | full_handoff | Design-handoff rerun | {P1/P2/P3} | {why structure is misaligned} |

### Priority rules:

- **P1:** Page violates a new hard failure — must be fixed before next deploy
- **P2:** Page is visually inconsistent with new policy — fix in current sprint
- **P3:** Page would benefit from update but isn't broken — schedule for next sprint

## PRESENT ACTION MAP:

"**Action plan for policy v{policy_version_previous} → v{policy_version_current}:**

**Immediate (P1):**
{list — hard failure violations}

**This sprint (P2):**
{list — visual inconsistencies}

**Next sprint (P3):**
{list — beneficial updates}

**Shared components to update first:**
{list of components used by multiple pages, with affected page count}

Ready to generate briefs?"

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/steps/step-05-emit-briefs.md`.

In autonomous mode: proceed immediately.
