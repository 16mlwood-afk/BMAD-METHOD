# Step 3: Classify Impact Per Page

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Classify EACH page independently — the same policy change can be Level 1 for one page and Level 3 for another
- When ambiguous, classify UP not down (Level 1 → Level 2, not the reverse) — under-scoping causes drift

## CONTEXT BOUNDARIES:

- `{section_diffs}` from step 02 tells you which policy sections changed and by how much
- `{affected_pages}` from step 01 tells you which pages to assess
- For each page, you may need to read the existing implementation or brief to understand what it uses

## YOUR TASK:

For each affected page, determine the impact level based on which policy sections changed and how that page uses the affected areas.

## IMPACT LEVELS:

### Level 1 — Visual Refresh

**Trigger:** Only sections 1 (Visual Direction), 3 (Tone), 7 (Typography & Color) changed as minor tweaks.

**What it means:** The page's structure and components are fine. Colors, spacing, font weights, or tone need adjustment. The information architecture and workflow are untouched.

**Examples:**
- Accent color changed from blue-600 to blue-700
- Body text tightened from 14px to 13px
- Error messages changed from "Oops!" to factual tone
- Spacing philosophy adjusted from "generous" to "compact but not cramped"

### Level 2 — Component Refresh

**Trigger:** Sections 5 (Component Language), 6 (Status System), or 8 (Hard Failures) changed — OR sections 1/3/7 changed as major.

**What it means:** Individual components on the page need updating (badges, filters, tables, buttons), but the page layout and information flow are still valid. May require shared component updates that affect multiple pages.

**Examples:**
- Badge system changed from filled pills to ring-inset
- New hard failure added that the page currently violates
- Filter pattern changed from chip toggles to dropdowns
- Status color palette reduced from 5 to 4 max
- Table row height changed from h-10 to h-9

### Level 3 — Structural Refresh (Full Handoff)

**Trigger:** Sections 4 (Layout Principles) or 9 (Page Mode Rules) changed as major — OR section 2 (Reference Products) changed the primary reference.

**What it means:** The page's fundamental structure, layout pattern, or mode behavior no longer aligns with the policy. The page needs a fresh design pass — its information architecture may need rethinking.

**Examples:**
- Primary layout changed from card-grid to table-first
- Page mode default flipped (operational → analytical)
- Hybrid rule changed to separate modes into tabs instead of mixing
- Navigation philosophy restructured (breadcrumbs removed, sidebar groups changed)
- New primary reference product completely changes the visual model

## CLASSIFICATION PROCEDURE:

For each page in `{affected_pages}`:

### 1. Identify which policy sections the page touches

Read the page's brief (if available) or scan the implementation:
- Does it have tables? → section 5 matters
- Does it use status badges? → section 6 matters
- Is it operational or analytical? → section 9 matters
- Does it use the filter pattern? → section 5 matters
- Does it have custom typography? → section 7 matters

### 2. Cross-reference with section diffs

For each section the page touches:
- If the section is **unchanged**: no impact from this section
- If the section is **minor**: contributes to Level 1
- If the section is **major**: contributes to Level 2 or 3 depending on the section

### 3. Take the highest applicable level

A page that has Level 1 from typography AND Level 2 from badges → **Level 2**.
A page that has Level 2 from badges AND Level 3 from layout → **Level 3**.

### 4. Build the impact map

`{page_impact_map}`:

| Page / Route | Impact Level | Triggering Sections | Key Changes |
|-------------|-------------|--------------------|----|
| {route} | Level {1/2/3} | {section numbers} | {what specifically needs updating} |

## PRESENT FINDINGS:

"**Impact assessment for {count} pages:**

**Level 1 — Visual Refresh ({count}):**
{list with routes and what needs adjusting}

**Level 2 — Component Refresh ({count}):**
{list with routes and which components are affected}

**Level 3 — Full Handoff ({count}):**
{list with routes and why the structure is now misaligned}

Proceeding to define actions for each page."

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/steps/step-04-decide-actions.md`.

In autonomous mode: proceed immediately.
