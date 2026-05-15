---
name: 'step-01-intake'
description: 'Screenshot inventory, context gathering, gap identification, and question surfacing'

nextStepFile: './step-02-design.md'
---

# Step 1: Intake — Inventory and Context

**Goal:** Catalogue everything visible in the screenshot, understand context, identify gaps, and surface questions for the dev team — all before making any design decisions.

---

## RULES

- MUST NOT skip steps or reorder the sequence.
- MUST NOT start designing yet — this step is observation only.
- MUST catalogue every visible element, not just the ones you plan to change.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From workflow initialization:

- `{baseline_commit}` - Git HEAD at workflow start
- `{design_standards}` - Loaded design standards reference
- `{project_context}` - Loaded if exists

---

## EXECUTION SEQUENCE

### 1. Capture Baseline

- Run `git rev-parse HEAD` and store as `{baseline_commit}` (or "NO_GIT" if not a git repo)

### 2. Receive Input

The user provides one or more of:

- Screenshot(s) of a page they want restyled
- A description of the page or component
- Notes about what they dislike or want changed

### 3. Request Additional Screenshots (if needed)

A single screenshot rarely tells the full story. Before proceeding, check for:

- Content cut off below the fold
- Tabs with hidden content
- Collapsed sections or accordions
- Modals behind trigger buttons
- Other pages that share the same components

If any of these are likely, ask for additional screenshots:

- "Can you scroll down and grab the rest of this page?"
- "What does the [tab name] tab look like?"
- "Can you trigger the modal from that button and screenshot it?"

**If autonomous mode:** Proceed with what's visible. Note assumptions about unseen content in `{open_questions}`.

### 4. Inventory the Screenshot

Before writing a single design recommendation, list **every** visible element:

- Page title / heading
- Navigation elements (tabs, breadcrumbs, sidebar items)
- Data fields and their labels
- Buttons and their labels/states
- Status indicators (badges, icons, colors)
- Table columns and their headers
- Cards and their content structure
- Filters, search bars, dropdowns
- Pagination or load-more controls
- Empty states or loading indicators
- Modals, tooltips, popovers (if visible)
- Footer or secondary navigation

Store this complete list as `{screenshot_inventory}`.

**This inventory is the safety net.** Every element here must either appear in the final spec or be explicitly listed as "omitted but still required in production."

### 5. Establish Context

Answer these questions (from the screenshot, user notes, or by asking):

- **Who sees this?** (Internal team? Customer-facing? Warehouse worker?)
- **What's the one thing they need?** (The primary job this page does)
- **Where does this appear?** (Dashboard? Detail page? Modal? Email?)
- **What's the emotional register?** (Data-heavy calm? Urgent alert? Onboarding?)
- **What breakpoints matter?** (Desktop-only internal tool? Needs mobile?)

Store answers as `{context_answers}`.

### 6. Identify Gaps

A screenshot shows one state of one viewport. Flag what you can't determine:

- How many possible values exist for status badges/dropdowns
- What happens at 0 items, 1 item, 50+ items
- Whether the page paginates, infinite-scrolls, or loads all
- What modals/panels open from visible buttons
- Whether the sidebar/nav is collapsible
- What the page looks like in error states
- Data types and formats for ambiguous fields

Store these as `{open_questions}` — they'll go to the dev team in the handoff.

**Don't block on questions.** Still proceed with best assumptions, but flag them so devs know what might need to change.

---

## PRESENT INVENTORY

Display to user:

```
**Screenshot Inventory:**

**Page context:** {one-sentence description of what this page does}

**Visible elements catalogued:** {count}
- {grouped list of elements by area: header, main content, sidebar, footer}

**Context:**
- Who: {audience}
- Primary job: {what user needs from this page}
- Platform: {where it appears}
- Register: {emotional tone}
- Breakpoints: {desktop/mobile/both}

**Open questions for dev team:** {count}
- {list of gaps that affect design decisions}

Ready to proceed to design? (y/n/adjust)
```

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true`, skip the confirmation menu. Proceed immediately to step-02.

---

## NEXT STEP DIRECTIVE

When confirmed, explicitly state:

"**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-agent/steps/step-02-design.md`"

---

## SUCCESS METRICS

- Complete screenshot inventory captured in `{screenshot_inventory}`
- Context questions answered in `{context_answers}`
- Gaps identified and stored in `{open_questions}`
- No design decisions made yet — observation only
- User confirmed readiness (or autonomous mode proceeded)

## FAILURE MODES

- Starting to design before completing the inventory
- Missing visible elements in the catalogue (leads to accidental feature deprecation)
- Not asking for additional screenshots when content is clearly cut off
- Blocking on questions instead of proceeding with flagged assumptions
