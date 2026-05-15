---
name: 'step-01-mode-detection'
description: 'Determine execution mode (tech-spec vs direct), handle escalation, set state variables'

nextStepFile_modeA: './step-03-execute.md'
nextStepFile_modeB: './step-02-context-gathering.md'
---

# Step 1: Mode Detection

**Goal:** Determine execution mode, capture baseline, handle escalation if needed.

---

## STATE VARIABLES (capture now, persist throughout)

These variables MUST be set in this step and available to all subsequent steps:

- `{baseline_commit}` - Git HEAD at workflow start (or "NO_GIT" if not a git repo)
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Path to tech-spec file (if Mode A)

---

## EXECUTION SEQUENCE

### 1. Capture Baseline

First, check if the project uses Git version control:

**If Git repo exists** (`.git` directory present or `git rev-parse --is-inside-work-tree` succeeds):

- Run `git rev-parse HEAD` and store result as `{baseline_commit}`

**If NOT a Git repo:**

- Set `{baseline_commit}` = "NO_GIT"

### 2. Load Project Context

Check if `{project_context}` exists (`**/project-context.md`). If found, load it as a foundational reference for ALL implementation decisions.

### 3. Normalize Visual Input

If the user attached an image (screenshot, photo), classify it and follow the appropriate digestion process:

#### 3a. Data / Table Screenshots

If the image contains **tabular or grid-like data** (data tables, spreadsheets, dashboard grids, order lists, etc.):

**Do NOT use the image as your primary data source for identifying issues.** Images of tables are lossy — OCR is unreliable for numbers/currency symbols, column alignment is ambiguous, and you cannot grep or diff an image.

Instead, follow this priority order:

1. **Query the source directly.** If the table is rendered by this app, read the API route or database query that populates it. The actual data is always more reliable than a screenshot of it.
2. **Ask the user for structured text.** If the data is external or you cannot access the source, ask: *"Can you paste 3-5 rows as text (copy from browser/DevTools/export), or share the API response? Structured text lets me pinpoint the exact issue."*
3. **Extract from the image as a last resort.** If neither option is available, transcribe the visible data into a markdown table in your response, then confirm with the user: *"I read these values from the screenshot — can you confirm they're accurate before I proceed?"*

**The image is still valuable for context** — use it to understand layout, column order, visual hierarchy, and which page/tab the user is on. Just don't rely on it for the actual cell values or for diagnosing data correctness issues.

#### 3b. Visual / Layout Bug Screenshots

If the image shows a **layout, spacing, sizing, or styling issue** (things that look wrong visually — not a data problem):

The screenshot IS the source of truth for what's wrong — but the **code** is the source of truth for what to change. Do not guess pixel values from the image. Instead, follow this digestion process:

1. **Identify the component.** Use the visible page URL, section headings, or distinctive UI elements to locate the React component that renders the area shown in the screenshot.
2. **Read the full render tree.** Read the component and its relevant children. Map out every spacing/sizing value in the affected area — padding, margin, gap, width, height, font-size. Write them down explicitly.
3. **Produce a visual digest.** Before making any changes, present a structured summary:
   - **Component:** file path and line range
   - **Current values:** list every spacing/sizing property in the affected area with its current value
   - **Issues identified:** what specifically looks wrong (e.g., "24px padding between sections creates too much whitespace", "40px image is undersized relative to 3-line product title")
   - **Proposed changes:** each value change with old → new and rationale
4. **Confirm with user** (non-autonomous) or **proceed** (autonomous), then apply all changes in a single pass.

**Why this matters:** Without reading the actual values first, the agent tends to make small incremental tweaks that don't fully solve the problem — requiring multiple rounds. Reading everything upfront lets you make one informed pass.

### 4. Parse User Input

Analyze the user's input to determine mode:

**Mode A: Tech-Spec**

- User provided a path to a tech-spec file (e.g., `quick-dev tech-spec-auth.md`)
- Load the spec, extract tasks/context/AC
- Set `{execution_mode}` = "tech-spec"
- Set `{tech_spec_path}` = provided path
- **NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-03-execute.md`

**Mode B: Direct Instructions**

- User provided task description directly (e.g., `refactor src/foo.ts...`)
- Set `{execution_mode}` = "direct"
- **NEXT:** Evaluate escalation threshold, then proceed

---

## ESCALATION THRESHOLD (Mode B only)

Evaluate user input with minimal token usage (no file loading):

**Triggers escalation (if 2+ signals present):**

- Multiple components mentioned (dashboard + api + database)
- System-level language (platform, integration, architecture)
- Uncertainty about approach ("how should I", "best way to")
- Multi-layer scope (UI + backend + data together)
- Extended timeframe ("this week", "over the next few days")

**Reduces signal:**

- Simplicity markers ("just", "quickly", "fix", "bug", "typo", "simple")
- Single file/component focus
- Confident, specific request

Use holistic judgment, not mechanical keyword matching.

---

## ESCALATION HANDLING

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true` in config, skip all menus below. Auto-select [E] Execute directly and proceed immediately to step-02-context-gathering. Do not halt or wait for user input.

### No Escalation (simple request)

Display: "**Select:** [P] Plan first (tech-spec) [E] Execute directly"

#### Menu Handling Logic:

- IF P: Direct user to `{quick_spec_workflow}`. **EXIT Quick Dev.**
- IF E: Proceed to **NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-02-context-gathering.md`

#### EXECUTION RULES:

- If `autonomous_mode`: auto-select [E] and proceed immediately
- Otherwise: halt and wait for user input after presenting menu

---

### Escalation Triggered - Level 0-2

Present: "This looks like a focused feature with multiple components."

Display:

**[P] Plan first (tech-spec)** (recommended)
**[W] Seems bigger than quick-dev** - Recommend the Full BMad Flow PRD Process
**[E] Execute directly**

#### Menu Handling Logic:

- IF P: Direct to `{quick_spec_workflow}`. **EXIT Quick Dev.**
- IF W: Direct user to run the PRD workflow instead. **EXIT Quick Dev.**
- IF E: Proceed to **NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-02-context-gathering.md`

#### EXECUTION RULES:

- If `autonomous_mode`: auto-select [E] and proceed immediately
- Otherwise: halt and wait for user input after presenting menu

---

### Escalation Triggered - Level 3+

Present: "This sounds like platform/system work."

Display:

**[W] Start BMad Method** (recommended)
**[P] Plan first (tech-spec)** (lighter planning)
**[E] Execute directly** - feeling lucky

#### Menu Handling Logic:

- IF P: Direct to `{quick_spec_workflow}`. **EXIT Quick Dev.**
- IF W: Direct user to run the PRD workflow instead. **EXIT Quick Dev.**
- IF E: Proceed to **NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-02-context-gathering.md`

#### EXECUTION RULES:

- If `autonomous_mode`: auto-select [E] and proceed immediately
- Otherwise: halt and wait for user input after presenting menu

---

## NEXT STEP DIRECTIVE

**CRITICAL:** When this step completes, explicitly state which step to load:

- Mode A (tech-spec): "**NEXT:** read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-03-execute.md`"
- Mode B (direct, [E] selected): "**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-02-context-gathering.md`"
- Escalation ([P] or [W]): "**EXITING Quick Dev.** Follow the directed workflow."

---

## SUCCESS METRICS

- `{baseline_commit}` captured and stored
- `{execution_mode}` determined ("tech-spec" or "direct")
- `{tech_spec_path}` set if Mode A
- Project context loaded if exists
- Escalation evaluated appropriately (Mode B)
- Explicit NEXT directive provided

## FAILURE MODES

- Proceeding without capturing baseline commit
- Not setting execution_mode variable
- Loading step-02 when Mode A (tech-spec provided)
- Attempting to "return" after escalation instead of EXIT
- No explicit NEXT directive at step completion
