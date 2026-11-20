---
name: 'step-01-mode-detection'
description: 'Determine execution mode (tech-spec vs direct), handle escalation, set state variables'

nextStepFile_modeA: './step-03-execute.md'
nextStepFile_modeB: './step-02-context-gathering.md'
---

# Step 1: Mode Detection

**Goal:** Determine execution mode, capture baseline, handle escalation if needed.

**Voice — Sol, Rapid Prototyper** (`shared/workflow-personas.md`): open with a one-line rough-and-fast contract for the change. Presentation only — Sol picks the smallest sensible default and proceeds (no ask-before-acting menu); mode detection and the §0 reroute logic are unchanged.

---

## STATE VARIABLES (capture now, persist throughout)

These variables MUST be set in this step and available to all subsequent steps:

- `{baseline_commit}` - Git HEAD at workflow start (or "NO_GIT" if not a git repo)
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Path to tech-spec file (if Mode A)
- `{tech_spec_slug}` - The loaded spec's `slug` (or `title`), captured at load so step-04 can detect a mid-run swap of the shared spec path (Mode A)

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
- **Worktree resolution fallback (spec 404 in a worktree ≠ no spec).** `_bmad-output/` is commonly gitignored, so a spec quick-spec wrote in the MAIN checkout exists only as an untracked file there — a fresh worktree branched from origin/main will NOT contain it. If `{tech_spec_path}` does not exist and the cwd is under `.claude/worktrees/`, resolve against the main checkout before concluding anything:

  ```bash
  main_root="$(dirname "$(git rev-parse --git-common-dir)")"
  if [ -f "$main_root/{tech_spec_path}" ]; then
    mkdir -p "$(dirname "{tech_spec_path}")"
    cp "$main_root/{tech_spec_path}" "{tech_spec_path}"
  fi
  ```

  COPY (never just read in place) so the spec travels with the worktree: step-04 stamps completion status onto it and the delivery PR should carry the completed spec. Only if the spec exists in NEITHER location is the path genuinely wrong — do NOT silently reclassify a 404'd Mode A input as Mode B direct-instructions; the spec's settled decisions are the whole point of Mode A. Halt and say where you looked.
- **Pin the spec-of-record.** From the loaded spec's frontmatter, capture `{tech_spec_slug}` (the `slug` field; fall back to `title` if `slug` is absent). `_bmad-output/` is shared and untracked, and quick-spec's default working path (`tech-spec-wip.md`) is generic — a parallel design→dev session can overwrite the file at this path mid-run (the shared-`_bmad-output`-filename collision class, `docs/fork-gaps.md`). Capturing the identity now lets step-04 detect a swap before it stamps status onto a stranger's spec.
- **NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-03-execute.md`

**Mode B: Direct Instructions**

- User provided task description directly (e.g., `refactor src/foo.ts...`)
- Set `{execution_mode}` = "direct"
- **NEXT:** Apply the GROUNDING GATE below, then (if it passes) evaluate escalation threshold

---

## GROUNDING GATE — Mode B only (overrides autonomous_mode)

> **This gate is NOT subject to `autonomous_mode`.** Autonomous mode grants *decision autonomy* (which file, which pattern, which library). It does NOT grant *intent autonomy* — i.e., guessing what the user wants. If user intent isn't groundable, halt and ask. Inventing intent under autonomous_mode is the documented failure class that caused PR #785's audit.

Before exiting this step, you MUST be able to state both of the following in plain English. If you cannot, the input is not groundable — see HALT below.

1. **The specific change** the user wants — in one sentence, with a verb. ("Fix the null check in the supplier matcher", "Add a column to the queries table", "Make the period selector wider.")
2. **The specific target** in this codebase — at least a file glob or a clearly-named UI surface. ("`src/lib/server/amazon/match.ts`", "the `/queries` page header", "the InvoiceDetail drawer.")

### Ungroundable inputs (HALT)

You **cannot** derive both (1) and (2) when the user input is:

- A single word that isn't a verb-target ("all", "go", "do", "yes", "this", "next")
- A pure sentinel / leftover ("ok", ".", "—", a stray flag like `--check`)
- A reference to a thing that doesn't exist after one quick grep (no file matches, no UI surface matches the name)
- A task description with no nameable target ("clean things up", "make it better", "fix the issues")
- An empty argument list when one was expected

**A short input is not automatically ungroundable.** "Fix the typo in the header" is short but groundable — a verb, a target. The test is groundability, not length.

### Groundable for a DIFFERENT workflow (reroute, don't dead-end)

Before the generic HALT below, check whether the input is ungroundable *for quick-dev* only because it's the input shape of a **sibling workflow**. The most common case is a **completed-work handoff** handed to the wrong front door: the input contains a `handoff-*.md` path, or its text leads with "Handoff filed:" / "Handoff:". That is groundable — the user wants follow-up on finished work — just not as a *change request*. Reroute instead of emitting the tech-spec nudge:

> "This looks like a completed-work handoff, not a change request — quick-dev builds a change from a verb + target, it doesn't triage finished work. The right door is `dispatch-followups`: `/bmad:bmm:workflows:dispatch-followups <handoff-path>`."

Then **EXIT Quick Dev.** This is awareness/reroute only — it names the right door, it does NOT auto-run dispatch-followups (that would be the same intent-fabrication the gate exists to prevent). The anti-fabrication invariant is untouched: quick-dev still refuses to invent a build task. (Generalizes to any strict-grounding workflow handed a sibling's artifact — match the artifact shape, name the owning workflow, exit.)

### HALT response

When ungroundable **and not rerouted above**:

1. State plainly: "I can't tell what you want me to change. Quick-dev needs a verb (what to do) and a target (where in the code)."
2. Show what you parsed: the literal input you received.
3. Offer one helpful nudge — e.g., "Did you mean to point at a tech-spec file? `quick-dev path/to/spec.md`. Or describe the change: `quick-dev fix the null check in queries header`."
4. **Do NOT proceed to step-02.** Do NOT make up a task to keep the workflow moving. **EXIT Quick Dev.**

This halt fires regardless of `autonomous_mode`. The mode grants execution latitude, not the right to fabricate intent.

---

## ESCALATION THRESHOLD (Mode B only, after GROUNDING GATE passes)

> **This is the cheap, early, linguistic pre-filter** — it scores the prompt wording before loading files, to reroute obviously-too-big work fast. It is NOT the authoritative scope ceiling. The authoritative, surface-based **blast-radius eligibility** check (covering BOTH modes, on the actual intended change surface) runs at **step-03 §0** via `shared/blast-radius-eligibility.md`, backed by a deterministic diff check at step-07. Keep this filter coarse; let step-03 §0 make the real call.

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
>
> **Scope:** Autonomous mode covers *decision autonomy* — picking the implementation approach, the file to edit, the pattern to follow — when intent is already clear from the input or the tech-spec. It does NOT cover *intent autonomy*. The GROUNDING GATE above is the contract: if user intent isn't groundable, halt regardless of this flag.

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
