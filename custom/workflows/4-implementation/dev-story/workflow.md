---
name: dev-story
description: 'Execute story implementation following a context filled story spec file. Use when the user says "dev this story [story file]" or "implement the next story in the sprint plan"'
---

# Dev Story Workflow

**Goal:** Execute story implementation following a context filled story spec file.

**Your Role:** Developer implementing the story.
- Communicate all responses in {communication_language} and language MUST be tailored to {user_skill_level}
- Generate all documents in {document_output_language}
- Only modify the story file in these areas: YAML frontmatter `baseline_commit`, Tasks/Subtasks checkboxes, Dev Agent Record (Debug Log, Completion Notes), File List, Change Log, and Status
- Execute ALL steps in exact order; do NOT skip steps
- Absolutely DO NOT stop because of "milestones", "significant progress", or "session boundaries". Continue in a single execution until the story is COMPLETE (all ACs satisfied and all tasks/subtasks checked) UNLESS a HALT condition is triggered or the USER gives other instruction.
- Do NOT schedule a "next session" or request review pauses unless a HALT condition applies. Only Step 9 decides completion.
- User skill level ({user_skill_level}) affects conversation style ONLY, not code updates.

## Conventions

- Bare paths (e.g. `steps/step-01-init.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

**If the script fails**, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying the same structural merge rules as the resolver:

1. `{skill-root}/customize.toml` — defaults
2. `{project-root}/_bmad/custom/{skill-name}.toml` — team overrides
3. `{project-root}/_bmad/custom/{skill-name}.user.toml` — personal overrides

Any missing file is skipped. Scalars override, tables deep-merge, arrays of tables keyed by `code` or `id` replace matching entries and append new entries, and all other arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context you carry for the rest of the workflow run. Entries prefixed `file:` are paths or globs under `{project-root}` — load the referenced contents as facts. All other entries are facts verbatim.

### Step 4: Load Config

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `project_name`, `user_name`
- `communication_language`, `document_output_language`
- `user_skill_level`
- `implementation_artifacts`
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)

### Step 5: Greet the User

Greet `{user_name}`, speaking in `{communication_language}`.

### Step 6: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

Activation is complete. If `activation_steps_prepend` or `activation_steps_append` were non-empty, confirm every entry was executed in order before proceeding. Do not begin the main workflow until all activation steps have been completed.

## Paths

- `story_file` = `` (explicit story path; auto-discovered if empty)
- `sprint_status` = `{implementation_artifacts}/sprint-status.yaml`

## Execution

<workflow>
  <critical>Communicate all responses in {communication_language} and language MUST be tailored to {user_skill_level}</critical>
  <critical>Generate all documents in {document_output_language}</critical>
  <critical>Only modify the story file in these areas: YAML frontmatter `baseline_commit`, Tasks/Subtasks checkboxes, Dev Agent Record (Debug Log, Completion Notes), File List,
    Change Log, and Status</critical>
  <critical>Execute ALL steps in exact order; do NOT skip steps</critical>
  <critical>Absolutely DO NOT stop because of "milestones", "significant progress", or "session boundaries". Continue in a single execution
    until the story is COMPLETE (all ACs satisfied and all tasks/subtasks checked) UNLESS a HALT condition is triggered or the USER gives
    other instruction.</critical>
  <critical>Do NOT schedule a "next session" or request review pauses unless a HALT condition applies. Only Step 9 decides completion.</critical>
  <critical>User skill level ({user_skill_level}) affects conversation style ONLY, not code updates.</critical>
  <critical>PARALLEL-SAFE STORY HANDLING. Other agent sessions may be running dev-story on this same project at the same time. Before doing ANY work on a story you must (a) RECONCILE its two state records and (b) atomically CLAIM it — and you must REFUSE a story already claimed by a live session. The full protocol is `{project-root}/_bmad/bmad-shared/parallel-sessions.md` §C (claim token, reconcile, dead-claim detection). Step 1 performs the claim + reconcile; do not skip it, and do not invent a second worktree or a second parallel-session warning — §C reuses the §A1 worktree identity.</critical>
  <critical>WAVE IMPLEMENT MODE (OPT-IN). This default flow implements ONE story. When the user passes the wave flag (`wave` / `--parallel`) AND more than one `ready-for-dev` story exists, run the OPT-IN wave-implement variant in `{project-root}/_bmad/bmad-shared/wave-orchestration.md`: fan out one implementer subagent per ready story (concurrency cap 6, default grouped by epic), each in ITS OWN worktree (parallel-sessions §A1) and atomically §C-claiming its own story, returning a structured result the orchestrator merges and gates wave-to-wave. Wave mode is ADDITIVE and never the silent default (invariant W0): independent solo parallel-worktree development is ALWAYS available unchanged — a wave just spawns implementers that use the same §A worktree + §C claim primitives a solo dev uses, so the two coexist without colliding. Without the flag, ignore this and run the single-story flow below.</critical>

  <step n="1" goal="Find next ready story and load it" tag="sprint-status">
    <check if="{{story_path}} is provided">
      <action>Use {{story_path}} directly</action>
      <action>Read COMPLETE story file</action>
      <action>Extract story_key from filename or metadata</action>
      <goto anchor="task_check" />
    </check>

    <!-- Sprint-based story discovery -->
    <check if="{{sprint_status}} file exists">
      <critical>MUST read COMPLETE sprint-status.yaml file from start to end to preserve order</critical>
      <action>Load the FULL file: {{sprint_status}}</action>
      <action>Read ALL lines from beginning to end - do not skip any content</action>
      <action>Parse the development_status section completely to understand story order</action>

      <action>Find the FIRST story (by reading in order from top to bottom) where:
        - Key matches pattern: number-number-name (e.g., "1-2-user-auth")
        - NOT an epic key (epic-X) or retrospective (epic-X-retrospective)
        - Status value equals "ready-for-dev"
      </action>

      <check if="no ready-for-dev or in-progress story found">
        <output>📋 No ready-for-dev stories found in sprint-status.yaml

          **Current Sprint Status:** {{sprint_status_summary}}

          **What would you like to do?**
          1. Run `create-story` to create next story from epics with comprehensive context
          2. Run `*validate-create-story` to improve existing stories before development (recommended quality check)
          3. Specify a particular story file to develop (provide full path)
          4. Check {{sprint_status}} file to see current sprint status

          💡 **Tip:** Stories in `ready-for-dev` may not have been validated. Consider running `validate-create-story` first for a quality
          check.
        </output>
        <ask>Choose option [1], [2], [3], or [4], or specify story file path:</ask>

        <check if="user chooses '1'">
          <action>HALT - Run create-story to create next story</action>
        </check>

        <check if="user chooses '2'">
          <action>HALT - Run validate-create-story to improve existing stories</action>
        </check>

        <check if="user chooses '3'">
          <ask>Provide the story file path to develop:</ask>
          <action>Store user-provided story path as {{story_path}}</action>
          <goto anchor="task_check" />
        </check>

        <check if="user chooses '4'">
          <output>Loading {{sprint_status}} for detailed status review...</output>
          <action>Display detailed sprint status analysis</action>
          <action>HALT - User can review sprint status and provide story path</action>
        </check>

        <check if="user provides story file path">
          <action>Store user-provided story path as {{story_path}}</action>
          <goto anchor="task_check" />
        </check>
      </check>
    </check>

    <!-- Non-sprint story discovery -->
    <check if="{{sprint_status}} file does NOT exist">
      <action>Search {implementation_artifacts} for stories directly</action>
      <action>Find stories with "ready-for-dev" status in files</action>
      <action>Look for story files matching pattern: *-*-*.md</action>
      <action>Read each candidate story file to check Status section</action>

      <check if="no ready-for-dev stories found in story files">
        <output>📋 No ready-for-dev stories found

          **Available Options:**
          1. Run `create-story` to create next story from epics with comprehensive context
          2. Run `*validate-create-story` to improve existing stories
          3. Specify which story to develop
        </output>
        <ask>What would you like to do? Choose option [1], [2], or [3]:</ask>

        <check if="user chooses '1'">
          <action>HALT - Run create-story to create next story</action>
        </check>

        <check if="user chooses '2'">
          <action>HALT - Run validate-create-story to improve existing stories</action>
        </check>

        <check if="user chooses '3'">
          <ask>It's unclear what story you want developed. Please provide the full path to the story file:</ask>
          <action>Store user-provided story path as {{story_path}}</action>
          <action>Continue with provided story file</action>
        </check>
      </check>

      <check if="ready-for-dev story found in files">
        <action>Use discovered story file and extract story_key</action>
      </check>
    </check>

    <action>Store the found story_key (e.g., "1-2-user-authentication") for later status updates</action>
    <action>Find matching story file in {implementation_artifacts} using story_key pattern: {{story_key}}.md</action>
    <action>Read COMPLETE story file from discovered path</action>

    <anchor id="task_check" />

    <!-- PARALLEL-SAFE: RECONCILE the two state records, then atomically CLAIM the story.
         Full protocol: {project-root}/_bmad/bmad-shared/parallel-sessions.md §C. Runs for BOTH the
         sprint-discovered story and a user-/path-provided story. Skip ONLY the sprint-status side
         when no sprint-status.yaml exists (story-file Status is then the sole record). -->
    <check if="{{sprint_status}} file exists">
      <action>RECONCILE (parallel-sessions §C3): re-read {{sprint_status}} FRESH (a parallel session may have just changed it — do not trust an earlier in-context copy). Compare {{story_key}}'s story-file `Status:` against development_status[{{story_key}}] and its claim token (trailing `# claim: owner=… session=… at=… baseline=…` comment).</action>
      <action>Gather drift evidence ONCE: `git log {{baseline_commit or HEAD}}..HEAD --oneline` (and `git log --all --oneline` for a possibly-merged PR) for the story's code paths; count checked `[x]` task boxes; check for a "Senior Developer Review (AI)" section / merged PR.</action>
      <action if="DRIFT CLASS 1 — sprint says done/review but story shows an earlier state AND evidence shows work landed">Evidence is authoritative: heal BOTH ledgers UP to the highest justified state (done if a merged PR exists, else review), check the satisfied task boxes (or add a Dev Agent Record note that boxes were not individually back-verified), per §C3. Do NOT re-open finished work. This story is NOT claimable as fresh work — emit the reconcile note and <goto step="9">treat as already-complete / completion path</goto> or return to discovery for the next free story.</action>
      <action if="DRIFT CLASS 2 — claimed/in-progress but baseline==HEAD, zero commits past baseline, no checked boxes (zombie)">Run the dead-claim check (§C4). If the holding session is dead (worktree branch gone AND pid not running, or session=unknown) or there is no token: RESET to free — clear the claim token, set both ledgers to ready-for-dev, discard the stale story-file `baseline_commit`. Emit the 🧟 reset note. Then continue to CLAIM below.</action>

      <action>CLAIM (parallel-sessions §C2): inspect development_status[{{story_key}}]'s value + claim token on the FRESH read:
        - `ready-for-dev`, no token → FREE. Flip value to `in-progress` and write the claim token `# claim: owner={user_name} session={{session_sig}} at={iso8601-utc} baseline={{baseline_commit or HEAD}}` as a §B1 per-key edit, then re-read the line to confirm YOUR `session=` landed.
        - token `session=` is YOURS → you already hold it; resume.
        - token `session=` is ANOTHER session AND that session is LIVE (§C4) → REFUSE: emit `⛔ {{story_key}} is claimed by {owner}/{session} since {at} — skipping to the next free story.`, return to the discovery scan, take the NEXT ready-for-dev story, and repeat reconcile+claim.
        - token `session=` is DEAD (§C4) → reclaim (rewrite session= to yours; keep/refresh baseline per the reconcile result).
      </action>
      <action>Compute {{session_sig}} ONCE for this run: if in a worktree, `git rev-parse --abbrev-ref HEAD` (branch slug — preferred, teammate-verifiable via `git worktree list`); else the controlling claude PID (`echo $PPID`); else `unknown`.</action>
      <action if="you LOST the claim race (re-read shows a different session=)">Return to discovery, pick the next free story, repeat. NEVER two sessions on one key.</action>
    </check>
    <check if="{{sprint_status}} file does NOT exist">
      <action>No shared claim ledger exists — reconcile is story-file-only. If the story-file `Status:` is `in-progress` with a `baseline_commit` but there are zero commits past baseline and no checked boxes, treat as a zombie (reset `Status:` to ready-for-dev, discard baseline) before proceeding; otherwise proceed.</action>
    </check>

    <action>Parse sections: Story, Acceptance Criteria, Tasks/Subtasks, Dev Notes, Dev Agent Record, File List, Change Log, Status</action>

    <action>Load comprehensive context from story file's Dev Notes section</action>
    <action>Extract developer guidance from Dev Notes: architecture requirements, previous learnings, technical specifications</action>
    <action>Use enhanced story context to inform implementation decisions and approaches</action>

    <action>Identify first incomplete task (unchecked [ ]) in Tasks/Subtasks</action>

    <action if="no incomplete tasks">
      <goto step="9">Completion sequence</goto>
    </action>
    <action if="story file inaccessible">HALT: "Cannot develop story without access to story file"</action>
    <action if="incomplete task or subtask requirements ambiguous">ASK user to clarify or HALT</action>
  </step>

  <step n="2" goal="Load project context and story information">
    <critical>Load all available context to inform implementation</critical>

    <action>Load {project_context} for coding standards and project-wide patterns (if exists)</action>
    <action>Parse sections: Story, Acceptance Criteria, Tasks/Subtasks, Dev Notes, Dev Agent Record, File List, Change Log, Status</action>
    <action>Load comprehensive context from story file's Dev Notes section</action>
    <action>Extract developer guidance from Dev Notes: architecture requirements, previous learnings, technical specifications</action>
    <action>Use enhanced story context to inform implementation decisions and approaches</action>
    <output>✅ **Context Loaded**
      Story and project context available for implementation
    </output>
  </step>

  <step n="3" goal="Detect review continuation and extract review context">
    <critical>Determine if this is a fresh start or continuation after code review</critical>

    <action>Check if "Senior Developer Review (AI)" section exists in the story file</action>
    <action>Check if "Review Follow-ups (AI)" subsection exists under Tasks/Subtasks</action>

    <check if="Senior Developer Review section exists">
      <action>Set review_continuation = true</action>
      <action>Extract from "Senior Developer Review (AI)" section:
        - Review outcome (Approve/Changes Requested/Blocked)
        - Review date
        - Total action items with checkboxes (count checked vs unchecked)
        - Severity breakdown (High/Med/Low counts)
      </action>
      <action>Count unchecked [ ] review follow-up tasks in "Review Follow-ups (AI)" subsection</action>
      <action>Store list of unchecked review items as {{pending_review_items}}</action>

      <output>⏯️ **Resuming Story After Code Review** ({{review_date}})

        **Review Outcome:** {{review_outcome}}
        **Action Items:** {{unchecked_review_count}} remaining to address
        **Priorities:** {{high_count}} High, {{med_count}} Medium, {{low_count}} Low

        **Strategy:** Will prioritize review follow-up tasks (marked [AI-Review]) before continuing with regular tasks.
      </output>
    </check>

    <check if="Senior Developer Review section does NOT exist">
      <action>Set review_continuation = false</action>
      <action>Set {{pending_review_items}} = empty</action>

      <output>🚀 **Starting Fresh Implementation**

        Story: {{story_key}}
        Story Status: {{current_status}}
        First incomplete task: {{first_task_description}}
      </output>
    </check>
  </step>

  <step n="4" goal="Mark story in-progress" tag="sprint-status">
    <critical>The atomic CLAIM + RECONCILE already happened in Step 1 (parallel-sessions §C2/§C3). Step 4 only mirrors the in-progress lifecycle into the story file and confirms the claim token is intact — it does NOT re-claim and must NOT overwrite another session's claim token. If a fresh read of {{sprint_status}} now shows {{story_key}}'s claim token carries a DIFFERENT `session=` than yours, a race was lost after Step 1: HALT with `⛔ Lost claim on {{story_key}} to {owner}/{session} — stopping to avoid double-work.`</critical>
    <action>If story file YAML frontmatter already contains `baseline_commit`, preserve the existing value and do not overwrite it</action>

    <check if="{{sprint_status}} file exists">
      <action>Load the FULL file: {{sprint_status}}</action>
      <action>Read all development_status entries to find {{story_key}}</action>
      <action>Set {{current_status}} to development_status[{{story_key}}]</action>
    </check>

    <check if="{{sprint_status}} file does NOT exist">
      <action>Set {{current_status}} to the story file Status section value</action>
    </check>

    <check if="{{current_status}} == 'ready-for-dev' AND story file YAML frontmatter does NOT contain baseline_commit">
      <action>Run `git rev-parse HEAD` to capture current commit into {{baseline_commit}}; if git/version control is unavailable, set {{baseline_commit}} = `NO_VCS`</action>
      <action>If story file YAML frontmatter exists, add `baseline_commit: {{baseline_commit}}` to the frontmatter</action>
      <action>If story file has no YAML frontmatter, create frontmatter at the top containing only `baseline_commit: {{baseline_commit}}`</action>
    </check>

    <check if="{{sprint_status}} file exists">
      <check if="{{current_status}} == 'ready-for-dev' OR (review_continuation == true AND {{current_status}} != 'in-progress')">
        <action>Set development_status[{{story_key}}] = "in-progress" AND ensure the claim token from Step 1 is present on that key as a §B1 per-key edit: `in-progress  # claim: owner={user_name} session={{session_sig}} at={iso8601-utc} baseline={{baseline_commit}}`. (If Step 1 already wrote it during the claim, this is a confirm-no-op, not a second write.)</action>
        <action>Update last_updated field to current date</action>
        <output>🚀 Starting work on story {{story_key}}
          Status updated: {{current_status}} → in-progress (claimed by {user_name}/{{session_sig}})
        </output>
      </check>

      <check if="{{current_status}} == 'in-progress'">
        <action>Confirm the claim token's `session=` is yours (parallel-sessions §C4). If it is a DIFFERENT live session, HALT per the Step-4 critical rule above. If it is yours or dead-and-reclaimed in Step 1, proceed.</action>
        <output>⏯️ Resuming work on story {{story_key}}
          Story is already marked in-progress (claim: {{session_sig}})
        </output>
      </check>

      <check if="{{current_status}} is neither ready-for-dev nor in-progress">
        <output>⚠️ Unexpected story status: {{current_status}}
          Expected ready-for-dev or in-progress. Continuing anyway...
        </output>
      </check>

      <action>Store {{current_sprint_status}} for later use</action>
    </check>

    <check if="{{sprint_status}} file does NOT exist">
      <output>ℹ️ No sprint status file exists - story progress will be tracked in story file only</output>
      <action>Set {{current_sprint_status}} = "no-sprint-tracking"</action>
    </check>
  </step>

  <step n="5" goal="Implement task following red-green-refactor cycle">
    <critical>FOLLOW THE STORY FILE TASKS/SUBTASKS SEQUENCE EXACTLY AS WRITTEN - NO DEVIATION</critical>

    <action>Review the current task/subtask from the story file - this is your authoritative implementation guide</action>
    <action>Plan implementation following red-green-refactor cycle</action>

    <!-- RED PHASE -->
    <action>Write FAILING tests first for the task/subtask functionality</action>
    <action>Confirm tests fail before implementation - this validates test correctness</action>

    <!-- GREEN PHASE -->
    <action>Implement MINIMAL code to make tests pass</action>
    <action>Run tests to confirm they now pass</action>
    <action>Handle error conditions and edge cases as specified in task/subtask</action>

    <!-- REFACTOR PHASE -->
    <action>Improve code structure while keeping tests green</action>
    <action>Ensure code follows architecture patterns and coding standards from Dev Notes</action>

    <action>Document technical approach and decisions in Dev Agent Record → Implementation Plan</action>

    <action if="new dependencies required beyond story specifications">HALT: "Additional dependencies need user approval"</action>
    <action if="3 consecutive implementation failures occur">HALT and request guidance</action>
    <action if="required configuration is missing">HALT: "Cannot proceed without necessary configuration files"</action>

    <action>CLASS-CHANGE TRIPWIRE (propose-and-act, do NOT menu — `{project-root}/_bmad/bmm/workflows/shared/escalation-on-class-change.md`): if mid-implementation the work reveals it has changed CLASS from the story — scope materially larger or differently shaped than the story's tasks+ACs, a missing keystone/shared seam the story must build first, the work is really a re-plan rather than execution, or it belongs to another lane (design → `design-router`, production backlog → `maintenance-triage`) — do NOT silently keep coding the now-mis-scoped story and do NOT hand {user_name} a numbered 1–4 menu. STATE the detected class-change + the concrete evidence, NAME the BMAD-default gateway (execution-lane default: `correct-course`), PROPOSE the route in one line, and PROCEED to it unless the user vetoes — the story HALTs while the gateway runs. Conservative: when uncertain whether scope truly changed class, this does NOT fire (a missed escalation is recoverable next pass; a false one is friction).</action>

    <critical>NEVER implement anything not mapped to a specific task/subtask in the story file</critical>
    <critical>NEVER proceed to next task until current task/subtask is complete AND tests pass</critical>
    <critical>Execute continuously without pausing until all tasks/subtasks are complete or explicit HALT condition</critical>
    <critical>Do NOT propose to pause for review until Step 9 completion gates are satisfied</critical>
  </step>

  <step n="6" goal="Author comprehensive tests">
    <action>Create unit tests for business logic and core functionality introduced/changed by the task</action>
    <action>Add integration tests for component interactions specified in story requirements</action>
    <action>Include end-to-end tests for critical user flows when story requirements demand them</action>
    <action>Cover edge cases and error handling scenarios identified in story Dev Notes</action>
  </step>

  <step n="7" goal="Run validations and tests">
    <action>Determine how to run tests for this repo (infer test framework from project structure)</action>
    <action>Run all existing tests to ensure no regressions</action>
    <action>Run the new tests to verify implementation correctness</action>
    <action>Run linting and code quality checks if configured in project</action>
    <action>Validate implementation meets ALL story acceptance criteria; enforce quantitative thresholds explicitly</action>
    <action if="regression tests fail">STOP and fix before continuing - identify breaking changes immediately</action>
    <action if="new tests fail">STOP and fix before continuing - ensure implementation correctness</action>
  </step>

  <step n="8" goal="Validate and mark task complete ONLY when fully done">
    <critical>NEVER mark a task complete unless ALL conditions are met - NO LYING OR CHEATING</critical>

    <!-- VALIDATION GATES -->
    <action>Verify ALL tests for this task/subtask ACTUALLY EXIST and PASS 100%</action>
    <action>Confirm implementation matches EXACTLY what the task/subtask specifies - no extra features</action>
    <action>Validate that ALL acceptance criteria related to this task are satisfied</action>
    <action>Run full test suite to ensure NO regressions introduced</action>
    <action>DIAGNOSTICS GATE (prove, don't assert — `{project-root}/_bmad/bmm/workflows/shared/diagnostics-gate.md`): if ANY new diagnostic surfaced during this task (type error, "cannot find module", lint/compile failure) — including after a merge or worktree teardown — the gate is RED until a re-run IN THE CURRENT CHECKOUT proves zero errors. Re-run the relevant check and quote the result; never reason a diagnostic away as "stale". "Gate green" with no quoted re-run is an unbacked claim.</action>

    <!-- REVIEW FOLLOW-UP HANDLING -->
    <check if="task is review follow-up (has [AI-Review] prefix)">
      <action>Extract review item details (severity, description, related AC/file)</action>
      <action>Add to resolution tracking list: {{resolved_review_items}}</action>

      <!-- Mark task in Review Follow-ups section -->
      <action>Mark task checkbox [x] in "Tasks/Subtasks → Review Follow-ups (AI)" section</action>

      <!-- CRITICAL: Also mark corresponding action item in review section -->
      <action>Find matching action item in "Senior Developer Review (AI) → Action Items" section by matching description</action>
      <action>Mark that action item checkbox [x] as resolved</action>

      <action>Add to Dev Agent Record → Completion Notes: "✅ Resolved review finding [{{severity}}]: {{description}}"</action>
    </check>

    <!-- ONLY MARK COMPLETE IF ALL VALIDATION PASS -->
    <check if="ALL validation gates pass AND tests ACTUALLY exist and pass">
      <action>ONLY THEN mark the task (and subtasks) checkbox with [x]</action>
      <action>Update File List section with ALL new, modified, or deleted files (paths relative to repo root)</action>
      <action>Add completion notes to Dev Agent Record summarizing what was ACTUALLY implemented and tested</action>
    </check>

    <check if="ANY validation fails">
      <action>DO NOT mark task complete - fix issues first</action>
      <action>HALT if unable to fix validation failures</action>
    </check>

    <check if="review_continuation == true and {{resolved_review_items}} is not empty">
      <action>Count total resolved review items in this session</action>
      <action>Add Change Log entry: "Addressed code review findings - {{resolved_count}} items resolved (Date: {{date}})"</action>
    </check>

    <action>Save the story file</action>
    <action>Determine if more incomplete tasks remain</action>
    <action if="more tasks remain">
      <goto step="5">Next task</goto>
    </action>
    <action if="no tasks remain">
      <goto step="9">Completion</goto>
    </action>
  </step>

  <step n="9" goal="Story completion and mark for review" tag="sprint-status">
    <action>Verify ALL tasks and subtasks are marked [x] (re-scan the story document now)</action>
    <action>Run the full regression suite (do not skip)</action>
    <action>Confirm File List includes every changed file</action>
    <action>Execute enhanced definition-of-done validation</action>
    <action>Update the story Status to: "review"</action>

    <!-- Enhanced Definition of Done Validation -->
    <action>Validate definition-of-done checklist with essential requirements:
      - All tasks/subtasks marked complete with [x]
      - Implementation satisfies every Acceptance Criterion
      - Unit tests for core functionality added/updated
      - Integration tests for component interactions added when required
      - End-to-end tests for critical flows added when story demands them
      - All tests pass (no regressions, new tests successful)
      - Code quality checks pass (linting, static analysis if configured)
      - File List includes every new/modified/deleted file (relative paths)
      - Dev Agent Record contains implementation notes
      - Change Log includes summary of changes
      - Only permitted story sections were modified
    </action>

    <!-- Mark story ready for review - sprint status conditional -->
    <check if="{sprint_status} file exists AND {{current_sprint_status}} != 'no-sprint-tracking'">
      <action>Load the FULL file: {sprint_status}</action>
      <action>Find development_status key matching {{story_key}}</action>
      <action>Verify current status is "in-progress" (expected previous state) AND that its claim token's `session=` is yours (parallel-sessions §C). If the claim token belongs to a different session, HALT — another session owns this story and you must not flip it to review.</action>
      <action>Update development_status[{{story_key}}] = "review" AND REMOVE the claim token comment (a completed story carries no active claim — leaving it would read as a zombie to the next session). This is a §B1 per-key edit.</action>
      <action>Update last_updated field to current date</action>
      <action>Save file, preserving ALL comments and structure including STATUS DEFINITIONS</action>
      <output>✅ Story status updated to "review" in sprint-status.yaml (claim released)</output>
    </check>

    <check if="{sprint_status} file does NOT exist OR {{current_sprint_status}} == 'no-sprint-tracking'">
      <output>ℹ️ Story status updated to "review" in story file (no sprint tracking configured)</output>
    </check>

    <check if="story key not found in sprint status">
      <output>⚠️ Story file updated, but sprint-status update failed: {{story_key}} not found

        Story status is set to "review" in file, but sprint-status.yaml may be out of sync.
      </output>
    </check>

    <!-- Final validation gates -->
    <action if="any task is incomplete">HALT - Complete remaining tasks before marking ready for review</action>
    <action if="regression failures exist">HALT - Fix regression issues before completing</action>
    <action if="File List is incomplete">HALT - Update File List with all changed files</action>
    <action if="definition-of-done validation fails">HALT - Address DoD failures before completing</action>
    <action>CLASS-CHANGE FINAL CHECK (escalation-on-class-change.md §1): before flipping to review, confirm the delivered work still matches the story's CLASS. If implementation revealed the story was materially mis-scoped — a seam was built that belongs in its own story, scope outgrew the unit, or a needed follow-on is really a re-plan — do NOT silently mark it review-complete. Surface the class-change and PROPOSE `correct-course` (proceed unless vetoed) per the standard, so the scope delta is recorded, not buried. Does not fire when the story was delivered as scoped.</action>
  </step>

  <step n="10" goal="Completion communication and user support">
    <action>Execute the enhanced definition-of-done checklist using the validation framework</action>
    <action>Prepare a concise summary in Dev Agent Record → Completion Notes</action>

    <action>Emit the completion communication per `shared/close-out-contract.md` (STD-CLOSEOUT-001): audience-first for the reviewer/next actor — NOT a process recap of how you implemented it. Process narration ("I did X then Y", step replay) is forbidden by default; explanations are on request only (the support step below). If the user later critiques the SHAPE of this close-out, that is a workflow-PATCH request — patch this step in the fork, do not just rewrite the message or write a memory (contract §4).</action>
    <action>Communicate to {user_name} that story implementation is complete and ready for review</action>
    <action>State the outcome, not the steps: story ID/key/title, current status (now "review"), the material change, and what the reviewer should verify (tests added, files touched as evidence — not a narrated build log)</action>
    <action>Provide the story file path and current status (now "review")</action>

    <action>Based on {user_skill_level}, ask if user needs any explanations about:
      - What was implemented and how it works
      - Why certain technical decisions were made
      - How to test or verify the changes
      - Any patterns, libraries, or approaches used
      - Anything else they'd like clarified
    </action>

    <check if="user asks for explanations">
      <action>Provide clear, contextual explanations tailored to {user_skill_level}</action>
      <action>Use examples and references to specific code when helpful</action>
    </check>

    <action>Once explanations are complete (or user indicates no questions), suggest logical next steps</action>
    <action>Recommended next steps (flexible based on project setup):
      - Review the implemented story and test the changes
      - Verify all acceptance criteria are met
      - Ensure deployment readiness if applicable
      - Run `code-review` workflow for peer review
      - Optional: If Test Architect module installed, run `/bmad:tea:automate` to expand guardrail tests
    </action>

    <output>💡 **Tip:** For best results, run `code-review` using a **different** LLM than the one that implemented this story.</output>
    <check if="{sprint_status} file exists">
      <action>Suggest checking {sprint_status} to see project progress</action>
    </check>
    <action>Remain flexible - allow user to choose their own path or ask for other assistance</action>
  <action>Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow.on_complete` — if the resolved value is non-empty, follow it as the final terminal instruction before exiting.</action>
  </step>

</workflow>
