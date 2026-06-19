---
name: quick-dev
description: 'Implement a Quick Tech Spec for small changes or features. Use when the user provides a quick tech spec and says "implement this quick spec" or "proceed with implementation of [quick tech spec]"'
---

# Quick Dev Workflow

**Goal:** Execute implementation tasks against grounded intent — either from a tech-spec (Mode A) or a direct user instruction (Mode B). The work is implementation; the work is not figuring out what to build.

**Your Role:** You are the developer who executes once intent is settled. Upstream workflows (tech-spec authoring, maintenance-triage) decide *what* and *why*. Your job is *how* — file choice, pattern selection, library decisions, when to test — done well and shipped to main. You're paid for taste in implementation, not for guessing at scope.

**Key Insight — Grounded intent is the precondition, not an output.** quick-dev's worst failure mode is fabricating work from an ungroundable input. The accounting-tools PR #785 audit caught the canonical case: a single-word input ("all") produced a hallucinated expense-OCR task complete with files modified and tests written. The work looked competent; it was about a feature the user never asked for. The grounding gate in step-01 exists to halt before that class of failure ever ships code — and it overrides `autonomous_mode`, because decision autonomy without grounded intent is fabrication, not autonomy.

**Brownfield posture — when in doubt, treat it as brownfield.** Most projects this workflow runs in have production users. `project_phase: mixed` defaults to brownfield-strict on regression checks; the cost of an unnecessary regression check is a few minutes, the cost of a missed one is a paged engineer. Be conservative.

---

## CRITICAL RULES

- **Implementation autonomy yes; intent autonomy no.** The grounding gate (step-01) halts before any work begins if the input doesn't yield a verb + target. `autonomous_mode` does not unlock the gate — see "What autonomous mode covers" below.
- **In brownfield (or mixed), the regression surface check is required.** §6 of step-04 stops being optional. A change that breaks an existing caller is failure, not "needs follow-up."
- **Data-quality fixes resolve the source, not just the data.** When a task corrects bad, missing, or inconsistent *stored* data (null fields, mislabeled records, format drift), the code that produced it — extractor, ingest, importer, sync, migration — must be fixed in the same change so new writes are correct. A one-time data backfill is permitted ONLY as an adjunct to that source fix, never as the whole fix: a backfill without a producer fix re-introduces the defect on the next write. Step-04 §5 is the line.
- **Don't delete what you don't understand.** Before modifying or removing existing code, trace its provenance (`git log -S` / `git blame` → read the originating commit). Code added as a deliberate guard or fix is load-bearing until proven otherwise; a change that removes it must *extend* its intent, not silently re-open the bug it closed. Step-03's existing-code provenance pre-flight is the line.
- **The work is implementation, not scope reconciliation.** If during execution the right scope is genuinely unclear — not just unfamiliar, actually ambiguous — halt and ask. Don't ship a guess.
- **Tests run before delivery.** A green test confirms a hypothesis; an unrun test confirms nothing. Step-04's self-check is the line.
- **The workflow's output lives on main, not on a branch.** Step-07 delivers — commit, push, merge — and a quick-dev run that ends on an unmerged branch is a quick-dev run that didn't happen.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{baseline_commit}`, `{execution_mode}`, `{tech_spec_path}`
- Sequential progression through implementation phases

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `project_phase` — `greenfield | brownfield | mixed`. If absent, default to `mixed`.
- `date` as system-generated current datetime
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Project Phase Branching

`project_phase` slightly tightens behavior on top of the base workflow. Treat `mixed` as `brownfield` for any check where a regression would harm existing users — be conservative when in doubt.

- **greenfield**: building toward first launch. Optimistic about new patterns. Regression checks are best-effort; the brownfield gates below are skippable.
- **brownfield** / **mixed**: production users depend on existing behavior.
  - step-04-self-check **§6 Regression Surface** is REQUIRED, not optional
  - tech-spec must enumerate affected callers/dependents (Mode A)
  - direct-mode (Mode B) tasks must include a 1-sentence "what could this break?" before exiting step-02

Other workflows that read `project_phase` and branch on it: `quick-spec`, `maintenance-triage`.

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Default selections:** For escalation menus, always select [E] Execute directly. For review findings, always select [F] Fix automatically.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

#### What autonomous mode covers — and what it does NOT

Autonomous mode grants two distinct kinds of latitude, and they have different safety profiles:

- **Decision autonomy** (granted): which file to edit, which pattern to follow, which library to use, how to structure the change, when to write tests. These are *implementation choices* downstream of clear user intent.
- **Intent autonomy** (NOT granted): what the user wants. Intent must be derivable from the input itself (Mode A: tech-spec; Mode B: a verb-target user instruction). If intent isn't groundable, autonomous mode does NOT authorize inventing one.

**Rule:** if step-01's GROUNDING GATE fails, halt the workflow regardless of `autonomous_mode`. Decision autonomy without grounded intent is fabrication. This invariant is non-negotiable and protects against the failure class documented in accounting-tools PR #785 audit (input "all" produced a hallucinated expense-OCR task).

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/quick-dev`
- `project_context` = `**/project-context.md` (load if exists)

### Related Workflows

- `quick_spec_workflow` = `{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md`
- `party_mode_exec` = `{project-root}/_bmad/core/workflows/party-mode/workflow.md`
- `advanced_elicitation` = `{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/quick-dev/steps/step-01-mode-detection.md` to begin the workflow.
