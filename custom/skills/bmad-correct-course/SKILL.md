---
name: bmad-correct-course
description: 'Manage significant changes during sprint execution. Use when the user says "correct course" or "propose sprint change"'
---

# Correct Course - Sprint Change Management Workflow

**Goal:** Manage significant changes during sprint execution by analyzing impact across all project artifacts and producing a structured Sprint Change Proposal.

**Your Role:** You are a Developer navigating change management. Analyze the triggering issue, assess impact across PRD, epics, architecture, and UX artifacts, and produce an actionable Sprint Change Proposal with clear handoff.

## Conventions

- Bare paths (e.g. `checklist.md`) resolve from the skill root.
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
- `planning_artifacts`
- `project_knowledge`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- Language MUST be tailored to `{user_skill_level}`
- Generate all documents in `{document_output_language}`
- DOCUMENT OUTPUT: Updated epics, stories, or PRD sections. Clear, actionable changes. User skill level (`{user_skill_level}`) affects conversation style ONLY, not document updates.

### Step 5: Greet the User

Greet `{user_name}`, speaking in `{communication_language}`.

### Step 6: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

Activation is complete. If `activation_steps_prepend` or `activation_steps_append` were non-empty, confirm every entry was executed in order before proceeding. Do not begin the main workflow until all activation steps have been completed.

## Paths

- `default_output_file` = `{planning_artifacts}/sprint-change-proposal-{date}.md`

## Input Files

| Input | Path | Load Strategy |
|-------|------|---------------|
| PRD | `{planning_artifacts}/*prd*.md` (whole) or `{planning_artifacts}/*prd*/*.md` (sharded) | FULL_LOAD |
| Epics | `{planning_artifacts}/*epic*.md` (whole) or `{planning_artifacts}/*epic*/*.md` (sharded) | FULL_LOAD |
| Architecture | `{planning_artifacts}/*architecture*.md` (whole) or `{planning_artifacts}/*architecture*/*.md` (sharded) | FULL_LOAD |
| UX Design | `{planning_artifacts}/*ux*.md` (whole) or `{planning_artifacts}/*ux*/*.md` (sharded) | FULL_LOAD |
| Spec | `{planning_artifacts}/*spec-*.md` (whole) | FULL_LOAD |
| Document Project | `{project_knowledge}/index.md` (sharded) | INDEX_GUIDED |

## Execution

### Document Discovery - Loading Project Artifacts

**Strategy**: Course correction needs broad project context to assess change impact accurately. Load all available planning artifacts.

**Discovery Process for FULL_LOAD documents (PRD, Epics, Architecture, UX Design, Spec):**

1. **Search for whole document first** - Look for files matching the whole-document pattern (e.g., `*prd*.md`, `*epic*.md`, `*architecture*.md`, `*ux*.md`, `*spec-*.md`)
2. **Check for sharded version** - If whole document not found, look for a directory with `index.md` (e.g., `prd/index.md`, `epics/index.md`)
3. **If sharded version found**:
   - Read `index.md` to understand the document structure
   - Read ALL section files listed in the index
   - Process the combined content as a single document
4. **Priority**: If both whole and sharded versions exist, use the whole document

**Discovery Process for INDEX_GUIDED documents (Document Project):**

1. **Search for index file** - Look for `{project_knowledge}/index.md`
2. **If found**: Read the index to understand available documentation sections
3. **Selectively load sections** based on relevance to the change being analyzed — do NOT load everything, only sections that relate to the impacted areas
4. **This document is optional** — skip if `{project_knowledge}` does not exist (greenfield projects)

**Fuzzy matching**: Be flexible with document names — users may use variations like `prd.md`, `bmm-prd.md`, `product-requirements.md`, etc.

**Missing documents**: Not all documents may exist. PRD and Epics are essential; Architecture, UX Design, Spec, and Document Project are loaded if available. HALT if PRD or Epics cannot be found.

<workflow>

<step n="1" goal="Initialize Change Navigation">
  <action>Confirm change trigger and gather user description of the issue</action>
  <action>Ask: "What specific issue or change has been identified that requires navigation?"</action>
  <action>Verify access to project documents:</action>
    - PRD (Product Requirements Document) — required
    - Current Epics and Stories — required
    - Architecture documentation — optional, load if available
    - UI/UX specifications — optional, load if available
  <action>Ask user for mode preference:</action>
    - **Incremental** (recommended): Refine each edit collaboratively
    - **Batch**: Present all changes at once for review
  <action>Store mode selection for use throughout workflow</action>

<action if="change trigger is unclear">HALT: "Cannot navigate change without clear understanding of the triggering issue. Please provide specific details about what needs to change and why."</action>

<action if="PRD or Epics are unavailable">HALT: "Need access to PRD and Epics to assess change impact. Please ensure these documents are accessible. Architecture and UI/UX will be used if available."</action>
</step>

<step n="2" goal="Execute Change Analysis Checklist">
  <action>Read fully and follow the systematic analysis from: checklist.md</action>
  <action>Work through each checklist section interactively with the user</action>
  <action>Record status for each checklist item:</action>
    - [x] Done - Item completed successfully
    - [N/A] Skip - Item not applicable to this change
    - [!] Action-needed - Item requires attention or follow-up
  <action>Maintain running notes of findings and impacts discovered</action>
  <action>Present checklist progress after each major section</action>

<action if="checklist cannot be completed">Identify blocking issues and work with user to resolve before continuing</action>
</step>

<step n="3" goal="Draft Specific Change Proposals">
<action>Based on checklist findings, create explicit edit proposals for each identified artifact</action>

<action>For Story changes:</action>

- Show old → new text format
- Include story ID and section being modified
- Provide rationale for each change
- Example format:

  ```
  Story: [STORY-123] User Authentication
  Section: Acceptance Criteria

  OLD:
  - User can log in with email/password

  NEW:
  - User can log in with email/password
  - User can enable 2FA via authenticator app

  Rationale: Security requirement identified during implementation
  ```

<action>For PRD modifications:</action>

- Specify exact sections to update
- Show current content and proposed changes
- Explain impact on MVP scope and requirements

<action>For Architecture changes:</action>

- Identify affected components, patterns, or technology choices
- Describe diagram updates needed
- Note any ripple effects on other components

<action>For UI/UX specification updates:</action>

- Reference specific screens or components
- Show wireframe or flow changes needed
- Connect changes to user experience impact

<check if="mode is Incremental">
  <action>Present each edit proposal individually</action>
  <ask>Review and refine this change? Options: Approve [a], Edit [e], Skip [s]</ask>
  <action>Iterate on each proposal based on user feedback</action>
</check>

<action if="mode is Batch">Collect all edit proposals and present together at end of step</action>

</step>

<step n="4" goal="Generate Sprint Change Proposal">
<action>Compile comprehensive Sprint Change Proposal document with following sections:</action>

<action>Section 1: Issue Summary</action>

- Clear problem statement describing what triggered the change
- Context about when/how the issue was discovered
- Evidence or examples demonstrating the issue

<action>Section 2: Impact Analysis</action>

- Epic Impact: Which epics are affected and how
- Story Impact: Current and future stories requiring changes
- Artifact Conflicts: PRD, Architecture, UI/UX documents needing updates
- Technical Impact: Code, infrastructure, or deployment implications

<action>Section 3: Recommended Approach</action>

- Present chosen path forward from checklist evaluation:
  - Direct Adjustment: Modify/add stories within existing plan
  - Potential Rollback: Revert completed work to simplify resolution
  - MVP Review: Reduce scope or modify goals
- Provide clear rationale for recommendation
- Include effort estimate, risk assessment, and timeline impact

<action>Section 4: Detailed Change Proposals</action>

- Include all refined edit proposals from Step 3
- Group by artifact type (Stories, PRD, Architecture, UI/UX)
- Ensure each change includes before/after and justification

<action>Section 5: Implementation Handoff</action>

- Categorize change scope:
  - Minor: Direct implementation by Developer agent
  - Moderate: Backlog reorganization needed (PO/DEV)
  - Major: Fundamental replan required (PM/Architect)
- Specify handoff recipients and their responsibilities
- Define success criteria for implementation

<action>Section 6: Executor Manifest (machine-readable footer — REQUIRED)</action>

> **This workflow is READ-ONLY on canonical tracker state.** It writes ONLY this proposal document and hands
> off; it must never edit `sprint-status.yaml`, story files, or `epics.md` itself. The *executor* (a separate,
> later invocation) applies the change — and it must touch NOTHING outside the `files_to_change` list below.

Append this exact YAML block to the end of the proposal document so the downstream executor gate can bound the
apply to a known file set:

```yaml
proposal_id: {date}-{short-slug}-v1   # stable id; the approval token references this verbatim
files_to_change:                       # EXACT tracker paths the executor may write — nothing else
  - <e.g. {implementation_artifacts}/sprint-status.yaml>
  - <e.g. {implementation_artifacts}/stories/2.10.md>
risk_class: autopilot_safe | owner_gate_required   # OPTIONAL hint, advisory only
sprint_apply_marker: dropped | NOT_DROPPED — no tracker files | BLOCKED — slot held by <id>   # set by step 6
```

- `proposal_id` MUST be unique and is what the user echoes in `APPROVE: APPLY_SPRINT_PROPOSAL::<proposal_id>`.
- `sprint_apply_marker` records what step 6 did with `.sprint-apply-pending.json`. A proposal whose `files_to_change` has **no** sprint-execution artifact (design-lane / planning-artifact — e.g. correct-course used only as the scope-register front door) is `NOT_DROPPED — no tracker files`: it never touches the single-slot marker. If the slot is already held by a different `proposal_id`, step 6 is `BLOCKED` rather than clobbering it. Only a proposal that edits sprint-execution artifacts into a free/own slot is `dropped`.
- `risk_class` is an OPTIONAL advisory hint. **The sprint-apply gate DERIVES the real class deterministically from `files_to_change` (single repo + every path a sprint-execution artifact under `_bmad-output/implementation-artifacts/` or `epics.md` + bounded count + no governance/doctrine path) and ignores a wrong or missing label — it fails closed to owner-gate.** Declare `autopilot_safe` only for a genuinely bounded, single-project sprint-execution edit (stories, sprint-status, epics); never for `planning-artifacts/` (PRD/architecture/specs), policy/doctrine, shared BMAD infra, or multiple repos. A hint that disagrees with the gate's derivation is surfaced in the gate log (planner-vs-gate mismatch), which is itself a useful signal — so set it honestly, but know it grants nothing on its own.
- `files_to_change` MUST list every tracker file the executor will modify and NO others. An omitted file cannot
  be applied without re-approval; an extra file widens the blast radius — keep it minimal and exact.

<action>Present complete Sprint Change Proposal to user</action>
<action>Write Sprint Change Proposal document to {default_output_file}</action>
<ask>Review complete proposal. Continue [c] or Edit [e]?</ask>
</step>

<step n="4.5" goal="Record Scope Provenance — write the scope-register row(s)">

> **This step is what stops a change from becoming registered-but-inert scope.** Governed by
> `shared/scope-register-routing.md` (STD-SCOPEREG-001). This workflow is the fork's scope-change
> front door and is therefore the PRIMARY PRODUCER of scope-register rows — a proposal that names
> impacted artifacts in prose but leaves no routed row hands the next session a decision with no
> owner and no next artifact.

<action>For EVERY scope item this proposal introduces, expands, or re-dispositions, append or update a row in `{planning_artifacts}/scope-register.md`.</action>

<action>Set the three routing fields on each row (STD-SCOPEREG-001 §2):</action>

- **`route`** — one of `R1-capability` · `R2-bounded-local` · `R3-design` · `R4-operational-milestone` · `R5-parked`, decided by the §3 procedure **in order**:
  - **R0 first:** does this change an existing direction, policy, or accepted decision? Then THIS workflow leads and supersedes it on the record — then re-enter the procedure to route the *work*. This workflow is a **gateway, not a terminal**; a row whose only artifact is this proposal is not routed, it is *awaiting* routing (`route: TBD` + the named decision that unblocks it).
  - **R1** — new table · new external source · schema-level/structural model change · new PRD FR · epic-level capability. Guardrails: MATERIALITY (a small clerk-writable field or a single enum value is **R2**) and PREMISE-CHECK (verify we don't already ingest a claimed "new source" — if we do, it is **R3**).
  - **R2** — bounded to an existing surface/module; no new table, source, or schema change.
  - **R3** — the data and capability already exist; what changes is what the operator sees.
  - **R4** — **nothing to build**: running, verifying, proving, or physically executing with already-shipped code.
  - **R5** — genuinely deferred.
  - **Mixed** → name both, set `route` to the one that **LEADS**, and record the follower as its own cross-referenced row. Never two routes in one row (it has no checkable next artifact).
- **`next_artifact`** — the ONE artifact that makes this scope actionable, with its intended path. **Route-appropriate, per §3/§4:** R1 = the first **story file** at `ready-for-dev` (NOT the epic, NOT its story list) · R2 = the **quick-spec** path · R3 = the **active, provenance-valid design brief** (produced by `design-handoff` — a row whose next artifact is "hand-edit the brief" is invalid by construction) · R4 = the **milestone-block key** in `sprint-status.yaml` per §7 · R5 = `—` is legal here and ONLY here.
- **`activation`** — mandatory **and only** on `R5-parked`, and complete: `owner:` (a named human/role who re-evaluates) · `trigger:` (an **observable** condition, never "when we get to it") · `why-not-now:` (the real blocker, or the cheaper alternative that won). A parked row missing any of the three is not legally parked.

<action>On `route: R4-operational-milestone`, do NOT manufacture build stories. Emit the milestone block shape from STD-SCOPEREG-001 §7 into the proposal's Section 4 (status enum `blocked` | `in-progress` | `done`; EVERY item carries `owner: operator` | `agent` | `external`), and list `sprint-status.yaml` in `files_to_change` so the executor can apply it. An operational proof item converted into stories manufactures code for a problem that is a config check or a physical action.</action>

<action>**NAME THE TRACKER DELTA — mandatory on every row whose `route` is NOT `R5-parked`.** State the concrete entry this scope adds to the plan — an `epics.md` story line, a `sprint-status.yaml` key, or (R4) the milestone block — and ADD that file to `files_to_change`. Without it the proposal carries no sprint-execution artifact, so Step 6 writes no pending marker, so there is no `APPROVE:` token and no executor path: the item exists only as a register row and moves only if a human remembers it. That is the observed failure this step exists to close — agreed scope sitting registered-and-inert while the board never learns it exists. A row with a `next_artifact` but no tracker delta is REGISTERED, not actionable (STD-SCOPEREG-001 §4).</action>

<action>**`R5-parked` is EXEMPT — deliberately, and it is the only exemption.** A parked row names no tracker delta and adds no file; its `activation` (owner · observable trigger · why-not-now) is what makes it re-findable. Forcing a plan entry onto a park would manufacture shape for work nobody has decided to start — the opposite failure, and the one that turns a park into a fake commitment. Park honestly, or route it; never name a delta you are not ready to commit to.</action>

<action>Rows are APPEND-ONLY. Re-disposition a superseded row in place with a dated note; never delete or renumber (scope ids are cited from stories, briefs, and PRs — a renumber is a read-modify-write race, same discipline as `docs/manifest-contract.md`).</action>

<action>Record the row ids + their routes in the proposal's Section 5 (Implementation Handoff) so the handoff names WHAT becomes actionable and by WHICH workflow, not just who receives it.</action>

<check if="a scope item cannot be routed">
  Write the row with `route: TBD` and name the exact decision that unblocks it. Do NOT omit the field, and do NOT default it to `R5-parked` — parking is a positive decision that owes an owner, a trigger, and a why-not-now, not a place to put items nobody classified.
</check>

<check if="this proposal introduces no scope item (a pure re-plan of already-registered scope)">
  Append no row. State that explicitly in Section 5 and name the existing row ids this proposal re-plans — silence is indistinguishable from a forgotten append.
</check>

</step>

<step n="5" goal="Finalize and Route for Implementation">
<action>Get explicit user approval for complete proposal</action>
<ask>Do you approve this Sprint Change Proposal for implementation? (yes/no/revise)</ask>

<check if="no or revise">
  <action>Gather specific feedback on what needs adjustment</action>
  <action>Return to appropriate step to address concerns</action>
  <goto step="3">If changes needed to edit proposals</goto>
  <goto step="4">If changes needed to overall proposal structure</goto>

</check>

<check if="yes the proposal is approved by the user">
  <action>Finalize Sprint Change Proposal document</action>
  <action>Determine change scope classification:</action>

- **Minor**: Can be implemented directly by Developer agent
- **Moderate**: Requires backlog reorganization and PO/DEV coordination
- **Major**: Needs fundamental replan with PM/Architect involvement

<action>Provide appropriate handoff based on scope:</action>

</check>

<check if="Minor scope">
  <action>Route to: Developer agent for direct implementation</action>
  <action>Deliverables: Finalized edit proposals and implementation tasks</action>
</check>

<check if="Moderate scope">
  <action>Route to: Product Owner / Developer agents</action>
  <action>Deliverables: Sprint Change Proposal + backlog reorganization plan</action>
</check>

<check if="Major scope">
  <action>Route to: Product Manager / Solution Architect</action>
  <action>Deliverables: Complete Sprint Change Proposal + escalation notice</action>

<action>Confirm handoff completion and next steps with user</action>
<action>Document handoff in workflow execution log</action>
</check>

</step>

<step n="6" goal="Workflow Completion">
<action>Summarize workflow execution:</action>
  - Issue addressed: {{change_trigger}}
  - Change scope: {{scope_classification}}
  - Artifacts modified: {{list_of_artifacts}}
  - Routed to: {{handoff_recipients}}

<action>Confirm all deliverables produced:</action>

- Sprint Change Proposal document
- Specific edit proposals with before/after
- Implementation handoff plan

<action>Conditionally drop the executor-gate pending marker (PROOF tier — freezes the exact tracker files this proposal authorizes for the downstream executor gate). This drop is GATED twice: a marker is written ONLY for a proposal that actually edits sprint-execution artifacts, and it NEVER silently overwrites a live marker that belongs to a different proposal.</action>

<check if="`files_to_change` contains NO sprint-execution artifact (no `sprint-status.yaml`, no story file, no `epics.md`)">
  **This is legal ONLY when every scope row in this proposal is `R5-parked`, or the proposal introduces no scope item at all.** In that case: do NOT write `.sprint-apply-pending.json` — the marker + `sprint-apply-gate` hook exist to bound an executor's edits to sprint-execution artifacts, and a proposal that edits none has nothing to bound; a marker here would only pollute the single slot. Record `sprint_apply_marker: NOT_DROPPED — parked-only proposal` (or `— no scope item`) in the Section 6 Executor Manifest and skip the write.

  **Otherwise this is a DEFECT in Step 4.5, not a legal exit.** A proposal carrying a non-parked row reached here without naming its tracker delta, which means the scope it just agreed has no executor path. HALT and surface: "Row(s) `<ids>` are routed `<route>` but this proposal names no tracker delta. Per Step 4.5, every non-`R5-parked` row must name the `epics.md` line / `sprint-status.yaml` key it adds and list that file in `files_to_change`. Add it, or re-route the row to `R5-parked` with a complete `activation`." Do NOT record `NOT_DROPPED — no tracker files` to get past this: that string was the silent exit that let agreed scope become inert, and it is no longer a legal disposition for a routed row.
</check>

<check if="`{project-root}/_bmad/.sprint-apply-pending.json` already exists AND names a DIFFERENT `proposal_id` than this one">
  Do NOT overwrite it. The file holds exactly ONE proposal; clobbering another proposal's live marker silently disarms its gate (a later `APPROVE: APPLY_SPRINT_PROPOSAL::<other_id>` could then mis-target). HALT and surface: "A pending marker for proposal `<existing_id>` is already live (freezing `<its files_to_change>`). Apply or resolve that proposal first, or explicitly move its marker aside, before this proposal drops its own." Record `sprint_apply_marker: BLOCKED — slot held by <existing_id>` in the manifest. (Single-slot contention is a known concurrency hazard when two proposals are open in parallel — see `docs/fork-gaps.md` 2026-07-19.)
</check>

<check if="`files_to_change` contains ≥1 sprint-execution artifact AND the slot is free or already names THIS `proposal_id`">
  Write `{project-root}/_bmad/.sprint-apply-pending.json` with the proposal's manifest:

  ```json
  { "proposal_id": "<proposal_id>", "files_to_change": ["<path>", "..."], "created_at": "{date}" }
  ```
</check>

This marker is read by the `sprint-apply-gate` PreToolUse hook (separate distribution track — ships with the
hooks, not this skill). It bounds any later apply to the exact `files_to_change` set; an
`APPROVE: APPLY_SPRINT_PROPOSAL::<proposal_id>` from the user clears the gate for those files only. If the hook
is not installed, this marker is inert (no effect on the workflow).

<action>Declare scope disposition per `shared/scope-register-routing.md` (STD-SCOPEREG-001 §5) — for EACH row added or changed in Step 4.5, state its `route`, its `next_artifact`, and (if `R5-parked`) its owner + trigger + why-not-now. **"Recorded in the scope register" is NOT a completion** — that is the REGISTERED state, and reporting it as done is the scope-level form of the commentator exit STD-COMPLETION-001 §3 forbids. Equally, do not report this workflow's own success as work being ready to START: a finished correct-course means a DECISION is ready to be made (the PROPOSED state, §4). A run that registered scope and shaped none of it is `owner_gated_residue` with each unrouted row NAMED, never a bare success.</action>
<action>Report workflow completion to user with personalized message: "Correct Course workflow complete, {user_name}!"</action>
<action>Remind user of success criteria and next steps for Developer agent</action>
<action>Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow.on_complete` — if the resolved value is non-empty, follow it as the final terminal instruction before exiting.</action>
</step>

</workflow>
