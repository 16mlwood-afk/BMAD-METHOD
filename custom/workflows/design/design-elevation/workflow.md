---
name: design-elevation
description: 'Find the highest-leverage way to deepen a settled surface — the "what would make THIS even better" pass — and let the user expand scope deliberately. Reads the surface and its artifacts of record (brief, screen-review, built code), generates enhancement candidates that deepen the core job, rejects additive chrome, ranks by leverage, recommends a focused subset, then halts for selection. On selection, classifies each chosen item and routes it back into the build loop (design-handoff for intent-changes, quick-spec for in-surface refinements) with provenance preserved.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_tuning_workflow: '{project-root}/_bmad/bmm/workflows/design/design-tuning/workflow.md'
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
quick_spec_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md'
brief_revision_policy: '{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md'
claude_design_prompt: '{project-root}/_bmad/bmm/workflows/design/shared/claude-design-prompt.md'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Design Elevation Workflow

**Goal:** A surface is settled — built, designed, and tuned to its brief. The natural next question is *"what could make THIS even better?"* This workflow answers it without letting the answer drift into feature-creep. It reads the settled surface and the artifacts of record that define its job, generates enhancement candidates that **deepen the core job**, explicitly rejects additive chrome, ranks the survivors by leverage, recommends a focused subset, and then — and only then — halts for the user to expand scope. Selected enhancements re-enter the build loop through the correct downstream workflow with brief provenance intact.

**Your Role:** You are a product lead doing a ceiling-raising pass on a surface that already works. You are NOT a constraint enforcer (that is design-tuning) and NOT a fresh designer (that is design-handoff). You start from a surface that meets its brief and ask the harder question: of everything that could be added or deepened, what would most elevate the *core job this surface exists to do* — and what would merely add surface area? You propose; the user decides what gets built. You never expand scope on your own.

**Key Insight:** When asked "what would make this better," both AI and humans default to **adding** — more features, more chrome, more surface area, more "delight." A settled surface is almost never improved by addition. It is improved by *deepening the core job*: closing loops that are currently one-way or deferred, moving signals earlier (before the user commits), and reducing operator effort on the one decision that actually matters. This workflow's entire value is resisting the additive default. Anything that does not deepen the core job is rejected — and the rejection is disclosed, so the user can see the additive ideas were considered and deliberately dropped, not overlooked. This is the same honesty posture design-tuning takes with "what to keep" and the silent-partial-implementation guard takes with per-item accountability.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Steps 01–03 are autonomous — they load the settled state, generate candidates, and rank/recommend without interaction.
- **Step 03 ends in a deliberate halt** — the workflow presents the ranked candidates plus a recommended subset, then waits for the user to select what to build. This is the only halt in the design family, and it is intentional: expanding scope is an *intent* decision (see Autonomy Model below), so it must be user-driven.
- Step 04 runs only after selection — it classifies each chosen enhancement on two axes (intent-change vs in-surface refinement, and design-shaped vs code-shaped) and routes it to where the work actually happens: a design-handoff re-brief, a focused Claude Design paste prompt, or quick-spec/code.
- State persists via variables (see below) and a state file on disk, so re-invoking on the same surface remembers what was already proposed, selected, and rejected.

### State Variables

- `{surface_name}` — The settled surface under elevation (page, drawer, detail view, or feature).
- `{surface_route}` — The route/path of the surface in the app (for grounding and for design-handoff if an intent-change is routed).
- `{core_job}` — One-sentence statement of the primary decision or action this surface exists to enable. Derived in step-01 from the brief + the built surface. The single most important variable: every candidate is judged against it.
- `{brief_path}` — Path to the design-handoff brief that is the surface's artifact of record (if one exists).
- `{brief_provenance}` — The 10-field provenance block read from the brief (per brief-revision-policy.md). Carried forward into any routed work so the lineage is unbroken.
- `{screen_review_path}` — Path to the most recent screen-review for the surface, if one exists.
- `{built_surface_refs}` — The actual component/route files implementing the surface, read from code. Grounds candidates in what exists, not what a brief imagined.
- `{policy_constraints}` — Hard constraints and named anti-defaults from `{project-root}/docs/design-policy.md`, loaded directly (not transitively through the brief).
- `{iteration_number}` — Elevation-pass count for this surface (1-based, incremented each invocation).
- `{state_file_path}` — Path to the persistent elevation state file.
- `{prior_candidates}` — Candidates proposed in earlier passes (so a re-run does not re-propose what was already accepted or explicitly declined).
- `{candidates}` — Enhancement candidates that survived the anti-chrome filter this pass.
- `{rejected_candidates}` — Additive/chrome ideas considered and rejected this pass, each with a one-line reason. Part of the deliverable, never silently dropped.
- `{ranked_candidates}` — `{candidates}` scored against the leverage rubric and ordered.
- `{recommended_subset}` — The focused subset (typically 1–3) the workflow recommends building, with a one-line rationale for the pairing.
- `{selected_enhancements}` — The subset the user chose to build (set after the step-03 halt).
- `{routing_plan}` — Per-selected-item classification on both axes (intent-change vs in-surface refinement; design-shaped vs code-shaped) and the route each is sent to (design-handoff re-brief / focused Claude Design paste prompt / quick-spec or direct code).

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action.
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order.
3. **STEPS 01–03 ARE AUTONOMOUS; STEP 03 ENDS IN A HALT**: Do not interact with the user until the step-03 selection halt. Do not skip the halt — never auto-select and proceed to routing.
4. **SAVE STATE**: Carry variables between steps and persist to the state file.
5. **LOAD NEXT**: When directed, read fully and follow the next step file.

### Critical Rules

- **Deepen the core job; do not add surface area.** The default human/AI answer to "what would make this better" is to add features. Reject that. A candidate earns its place only by deepening the decision or action the surface exists for. See the leverage rubric in `checklist.md`.
- **Disclose what you rejected.** The rejected additive ideas (`{rejected_candidates}`) are part of the output, each with a reason. A list of only the survivors looks like the filter never ran. Surfacing the rejects is the proof of work.
- **Propose, never expand scope.** You generate, rank, and recommend. The user selects. Never route an enhancement to the build loop that the user did not select — that is intent autonomy, which this workflow does not have (see Autonomy Model).
- **Ground every candidate in the real surface.** Read the built code and the brief. A candidate must reference something that actually exists on the surface ("the duplicate check only fires on Save", "field→source is one-way"). Do not invent affordances the surface doesn't have to then "improve" them.
- **Policy is authoritative; the brief is derivative.** If a candidate would violate the project design policy, it is rejected even if it deepens the core job. The policy's named anti-defaults are hard rejects.
- **Recommend a focused subset, then stop.** Do not present a flat menu of ten options for the user to wade through. Rank, recommend the 1–3 with the most leverage, name the pairing rationale, and act on the user's reply. (This honors the project's no-multi-select-menus and assess-and-act conventions: the recommendation is the headline, the full ranked list is the appendix.)

---

## AUTONOMY MODEL — CRITICAL

This workflow sits exactly on the decision/intent autonomy boundary, so the split must be explicit:

- **Decision autonomy (the workflow has this):** which candidates to generate, how to score them against the leverage rubric, what to reject as chrome, which subset to recommend, and — once the user selects — which downstream workflow each selected item routes to. All of this the workflow does on its own.
- **Intent autonomy (the workflow does NOT have this):** deciding that the surface's scope *should* grow. Expanding scope changes what the user is on the hook to build, maintain, and ship. That is the user's call, every time. The step-03 halt is where intent is handed back to the user. The workflow may strongly recommend a subset; it may not select on the user's behalf and proceed.

The failure this guards against is a workflow that helpfully "improves" a surface the user considered finished — quietly turning a settled surface into an open project. Recommending is help; deciding to expand is overreach.

---

## SOURCE-OF-TRUTH PRECEDENCE

When candidates conflict with guidance, authority runs:

1. **Project design policy** — `{project-root}/docs/design-policy.md`. Named anti-defaults are hard rejects regardless of leverage. Loaded directly in step-01.
2. **The built surface (code)** — `{built_surface_refs}`. The ground truth for what exists and what a candidate would change. A candidate that contradicts what the code actually does is mis-grounded; re-read before proposing.
3. **The surface's brief / screen-review** — `{brief_path}`, `{screen_review_path}`. Define the surface's intended job and constraints. The source of `{core_job}` and of the provenance carried into routed work.
4. **Prior elevation state** — `{state_file_path}`. Tracks what was already proposed/selected/declined. Cannot reopen something the user explicitly declined unless the user asks.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`, `project_phase`
- `implementation_artifacts` path
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

**Brownfield note:** if `project_phase = brownfield`, any in-surface refinement routed in step-04 carries the brownfield obligations forward (quick-spec §4b grounding, quick-dev §6 regression-surface gate). Elevation does not exempt work from brownfield safety.

### Input

The user provides:

- **The surface to elevate** — a route, page name, drawer, or feature ("elevate the invoice-import save flow", "design-elevation on /queries detail"). Required — this is the grounding target; if it cannot be resolved to a real surface, halt and ask which surface.
- **Brief / screen-review reference** — optional and usually inferred. If not given, step-01 finds the most recent design-handoff brief and screen-review whose target matches the surface.
- **A focus, optionally** — the user may narrow the pass ("focus on the pre-commit decision", "the verify path only"). Absent a focus, the whole core job is in scope.

### State File Resolution

```
{implementation_artifacts}/design-elevation-state-{surface-slug}.md
```

- If the file exists → load `{prior_candidates}` and prior selections/declines, increment `{iteration_number}`.
- If not → first pass, `{iteration_number}` = 1.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-elevation/steps/step-01-load-settled-state.md` to begin.
