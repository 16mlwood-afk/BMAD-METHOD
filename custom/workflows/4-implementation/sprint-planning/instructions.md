# Sprint Planning - Sprint Status Generator

<critical>The workflow execution engine is governed by: {project-root}/_bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/_bmad/bmm/workflows/4-implementation/sprint-planning/workflow.yaml</critical>

## 📚 Document Discovery - Full Epic Loading

**Strategy**: Sprint planning needs ALL epics and stories to build complete status tracking.

**Epic Discovery Process:**

1. **Search for whole document first** - Look for `epics.md`, `bmm-epics.md`, or any `*epic*.md` file
2. **Check for sharded version** - If whole document not found, look for `epics/index.md`
3. **If sharded version found**:
   - Read `index.md` to understand the document structure
   - Read ALL epic section files listed in the index (e.g., `epic-1.md`, `epic-2.md`, etc.)
   - Process all epics and their stories from the combined content
   - This ensures complete sprint status coverage
4. **Priority**: If both whole and sharded versions exist, use the whole document

**Fuzzy matching**: Be flexible with document names - users may use variations like `epics.md`, `bmm-epics.md`, `user-stories.md`, etc.

<workflow>

<step n="0" goal="Mode gate — incremental add-one-epic vs full (re)generation">
<action>Decide the mode BEFORE any parsing. Two modes:</action>

**INCREMENTAL (`--epic`) — add ONE epic's keys to a running board.** Enter this mode when BOTH hold:

1. The invocation targets a SINGLE epic — an explicit `--epic <file>` / `{epic_file}` input, OR the user asked to "add this ONE epic" / "decompose ONE new epic" and named a standalone `epic-<slug>.md`, AND
2. `{status_file}` ALREADY EXISTS and is non-empty (there is a live board to add to).

If either is false → **FULL mode**: skip to step 1 and run the whole-corpus (re)generation below, unchanged. (No `--epic` input + no board yet = first-time generation = FULL. A `--epic` input but no existing `{status_file}` also falls through to FULL — there is nothing to add to.)

<action>In INCREMENTAL mode, do NOT re-parse the epics corpus and do NOT regenerate {status_file}. Run this path, then EXIT (do not run steps 1/2/4):</action>

1. **Parse ONLY the named epic file** — extract its epic number, its stories, and derive keys with the SAME rules as step 1 (`epic-{num}`, `{epic}-{story}-{title}`, `epic-{num}-retrospective`).
2. **Read the existing {status_file}** — treat every existing key and status as authoritative and IMMUTABLE. You are ADDING keys, never rewriting.
3. **Per-key additive insert (preservation-first).** For each derived key **not already present**, insert it with its default status (`backlog` for epic/stories, `optional` for the retrospective), then run step 3's status detection on the new stories only (a story file already on disk → `ready-for-dev`). Place the new block in epic order (after the preceding epic's block, or appended if it is the highest epic). **Never** rewrite the whole file, reorder existing keys, or change an existing status. A key that is already present is a no-op (idempotent re-run).
4. **Honor the shared-board contract.** `{status_file}` is a no-lock file contended by many parallel sessions — edit it **per-key** (single-line inserts), never as a whole-file write, per `{project-root}/_bmad/bmad-shared/parallel-sessions.md` §B1/B1a. This is the entire reason INCREMENTAL exists: the FULL regeneration churns the contended board (and can pull DRAFT/proposed epics into the active sprint), which is unsafe under parallel load.
5. **Report only the delta** — list the keys ADDED and the keys SKIPPED (already present). Do NOT print a full-board summary (that implies a regeneration that did not happen).
6. **EXIT.** Do not fall through to steps 1/2/4.
</step>

<step n="1" goal="Parse epic files and extract all work items">
<action>Load {project_context} for project-wide patterns and conventions (if exists)</action>
<action>Communicate in {communication_language} with {user_name}</action>
<action>Look for all files matching `{epics_pattern}` in {epics_location}</action>
<action>Could be a single `epics.md` file or multiple `epic-1.md`, `epic-2.md` files</action>

<action>For each epic file found, extract:</action>

- Epic numbers from headers like `## Epic 1:` or `## Epic 2:`
- Story IDs and titles from patterns like `### Story 1.1: User Authentication`
- Convert story format from `Epic.Story: Title` to kebab-case key: `epic-story-title`

**Story ID Conversion Rules:**

- Original: `### Story 1.1: User Authentication`
- Replace period with dash: `1-1`
- Convert title to kebab-case: `user-authentication`
- Final key: `1-1-user-authentication`

<action>Build complete inventory of all epics and stories from all epic files</action>
</step>

  <step n="0.5" goal="Discover and load project documents">
    <invoke-protocol name="discover_inputs" />
    <note>After discovery, these content variables are available: {epics_content} (all epics loaded - uses FULL_LOAD strategy)</note>
  </step>

<step n="2" goal="Build sprint status structure">
<action>For each epic found, create entries in this order:</action>

1. **Epic entry** - Key: `epic-{num}`, Default status: `backlog`
2. **Story entries** - Key: `{epic}-{story}-{title}`, Default status: `backlog`
3. **Retrospective entry** - Key: `epic-{num}-retrospective`, Default status: `optional`

**Example structure:**

```yaml
development_status:
  epic-1: backlog
  1-1-user-authentication: backlog
  1-2-account-management: backlog
  epic-1-retrospective: optional
```

</step>

<step n="3" goal="Apply intelligent status detection">
<action>For each story, detect current status by checking files:</action>

**Story file detection:**

- Check: `{story_location_absolute}/{story-key}.md` (e.g., `stories/1-1-user-authentication.md`)
- If exists → upgrade status to at least `ready-for-dev`

**Preservation rule:**

- If existing `{status_file}` exists and has more advanced status, preserve it
- Never downgrade status (e.g., don't change `done` to `ready-for-dev`)

**Status Flow Reference:**

- Epic: `backlog` → `in-progress` → `done`
- Story: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`
- Retrospective: `optional` ↔ `done`
  </step>

<step n="4" goal="Generate sprint status file">
<action>Create or update {status_file} with:</action>

**File Structure:**

```yaml
# generated: {date}
# project: {project_name}
# project_key: {project_key}
# tracking_system: {tracking_system}
# story_location: {story_location}

# STATUS DEFINITIONS:
# ==================
# Epic Status:
#   - backlog: Epic not yet started
#   - in-progress: Epic actively being worked on
#   - done: All stories in epic completed
#
# Epic Status Transitions:
#   - backlog → in-progress: Automatically when first story is created (via create-story)
#   - in-progress → done: Manually when all stories reach 'done' status
#
# Story Status:
#   - backlog: Story only exists in epic file
#   - ready-for-dev: Story file created in stories folder
#   - in-progress: Developer actively working on implementation
#   - review: Ready for code review (via Dev's code-review workflow)
#   - done: Story completed
#
# Retrospective Status:
#   - optional: Can be completed but not required
#   - done: Retrospective has been completed
#
# WORKFLOW NOTES:
# ===============
# - Epic transitions to 'in-progress' automatically when first story is created
# - Stories can be worked in parallel if team capacity allows
# - SM typically creates next story after previous one is 'done' to incorporate learnings
# - Dev moves story to 'review', then runs code-review (fresh context, different LLM recommended)

generated: { date }
project: { project_name }
project_key: { project_key }
tracking_system: { tracking_system }
story_location: { story_location }

development_status:
  # All epics, stories, and retrospectives in order
```

<action>Write the complete sprint status YAML to {status_file}</action>
<action>CRITICAL: Metadata appears TWICE - once as comments (#) for documentation, once as YAML key:value fields for parsing</action>
<action>Ensure all items are ordered: epic, its stories, its retrospective, next epic...</action>
</step>

<step n="5" goal="Validate and report">
<action>Perform validation checks:</action>

- [ ] Every epic in epic files appears in {status_file}
- [ ] Every story in epic files appears in {status_file}
- [ ] Every epic has a corresponding retrospective entry
- [ ] No items in {status_file} that don't exist in epic files
- [ ] All status values are legal (match state machine definitions)
- [ ] File is valid YAML syntax

<action>Count totals:</action>

- Total epics: {{epic_count}}
- Total stories: {{story_count}}
- Epics in-progress: {{in_progress_count}}
- Stories done: {{done_count}}

<action>Reconcile the SCOPE REGISTER against what the board now says (STD-SCOPEREG-001 §9 — the inert-scope sweep). REPORT-ONLY.</action>

This is the sweep's designated trigger point, and until now nothing fired it: the standard named
`sprint-status` as a trigger and no step invoked it, so rows sat `pending` for weeks *after their own
answer merged*. The asymmetry that makes it rot: a workflow moves a row ONTO `pending`
automatically, but only a human moves it OFF — a one-way ratchet, and a stale `pending` row is
indistinguishable by inspection from a real open decision. Three of four rows once surfaced as
"waiting on the owner" were waiting on nobody.

```bash
node {fork_tools}/check-scope-register.js --register {planning_artifacts}/scope-register.md --audit
```

- **No register / tool not reachable** → say so in one line and continue. This step never blocks the
  sprint status, and a missing register is not a finding.
- **`DELIVERED-BUT-PENDING` rows** (still `pending` while the artifact they waited for EXISTS) → list
  them in the completion summary with the artifact each one names. **Read before believing:** an
  existing file proves a STRING resolved, not that the row's question was answered.
- **`PROMISED-NOT-PRODUCED` / inert rows** → report the count; these are the reverse case (routed,
  still not shaped).

<critical>NEVER flip a `disposition` here. Owner-only off `pending` is the audit anchor and is
deliberate (§9) — the gap this step closes is DETECTION, not authority. Report; let the owner close.</critical>

<action>Display completion summary to {user_name} in {communication_language}:</action>

**Sprint Status Generated Successfully**

- **File Location:** {status_file}
- **Total Epics:** {{epic_count}}
- **Total Stories:** {{story_count}}
- **Epics In Progress:** {{epics_in_progress_count}}
- **Stories Completed:** {{done_count}}
- **Scope register:** {{inert_count}} inert · {{delivered_but_pending_count}} delivered-but-pending (list each with its artifact; owner closes them, this workflow does not)

**Next Steps:**

1. Review the generated {status_file}
2. Use this file to track development progress
3. Agents will update statuses as they work
4. Re-run this workflow to refresh auto-detected statuses

</step>

</workflow>

## Additional Documentation

### Status State Machine

**Epic Status Flow:**

```
backlog → in-progress → done
```

- **backlog**: Epic not yet started
- **in-progress**: Epic actively being worked on (stories being created/implemented)
- **done**: All stories in epic completed

**Story Status Flow:**

```
backlog → ready-for-dev → in-progress → review → done
```

- **backlog**: Story only exists in epic file
- **ready-for-dev**: Story file created (e.g., `stories/1-3-plant-naming.md`)
- **in-progress**: Developer actively working
- **review**: Ready for code review (via Dev's code-review workflow)
- **done**: Completed

**Retrospective Status:**

```
optional ↔ done
```

- **optional**: Ready to be conducted but not required
- **done**: Finished

### Guidelines

1. **Epic Activation**: Mark epic as `in-progress` when starting work on its first story
2. **Sequential Default**: Stories are typically worked in order, but parallel work is supported
3. **Parallel Work Supported**: Multiple stories can be `in-progress` if team capacity allows
4. **Review Before Done**: Stories should pass through `review` before `done`
5. **Learning Transfer**: SM typically creates next story after previous one is `done` to incorporate learnings
