---
name: quick-brainstorm
description: 'Fit-for-purpose front door for brainstorms. Infers whether the ask is a bounded decision (convergent) or a genuinely open problem space (divergent), states its verdict in one line, and proceeds unless vetoed. Convergent asks route OUT (inline deliberation, quick-spec, or design-router for anything design-shaped) — no ideation machinery runs. Divergent asks get a lightweight repo-grounded session: 1-2 auto-selected techniques, ~20-30 ideas, and a MANDATORY convergence ending (themes → ranked shortlist → one biased recommendation → optional handoff artifact). Use when the user says "brainstorm X", "let''s think about X", "what are our options for X". The upstream core brainstorming workflow remains the deep-divergence specialist for 100+ idea sessions.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Dispatch targets — the convergent route defers to these by name; it never re-implements them.
quick_spec: '{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md'
design_router: '{project-root}/_bmad/bmm/workflows/design/design-router/workflow.md'

# Divergent-session sources — referenced, never duplicated. Directory path on purpose:
# the skills-layout porter rewrites workflow.md references, and core is never ported.
core_brainstorming: '{project-root}/_bmad/core/workflows/brainstorming/'
brain_techniques_csv: '{project-root}/_bmad/core/workflows/brainstorming/brain-methods.csv'
---

# Quick Brainstorm Workflow

**Goal:** Give every "let's brainstorm" ask the treatment it actually needs. Most brainstorms are bounded decisions wearing brainstorm clothes — those get routed to the lane that decides, not facilitated toward 100 ideas. The genuinely open ones get a lightweight, repo-grounded ideation session that always ends in a decision-ready shortlist and one recommendation.

**Your Role:** You are a pragmatic thinking partner, not a creativity facilitator. You classify first, ideate second, and always converge. You never run ceremony the ask doesn't need.

---

## OWNERSHIP & MATERIALITY GATE — read first

**This workflow OWNS:** the brainstorm-shaped triage decision (convergent vs divergent) and the lightweight divergent session (grounding → 20-30 ideas → convergence).

**This workflow does NOT own (it defers, by name):**
- Deciding a bounded engineering question → answered inline under answer-shape (verdict → weighted bullets → one biased recommendation), not run as a session.
- Speccing a code change → `quick-spec`.
- ALL design-shaped wants — "redesign X", "this feels wrong", "what would make X even better" → `design-router`. The design-lane front door is the single source of design-lane routing truth (its contract); this workflow never picks a design specialist, depth, or placement itself.
- Deep divergence (100+ ideas, multi-technique facilitation) → the core `brainstorming` workflow (`/bmad:core:workflows:brainstorming`, installed at `{core_brainstorming}`).

**USE when:** the user says "brainstorm X", "let's think about X", "ideas for X", "what are our options for X" and the right treatment isn't already obvious.

**Do NOT use when:** the user already named the specialist ("quick-spec this", "run design-router") — run it directly.

**Provenance:** this workflow shadows (does not patch) the upstream core brainstorming workflow — `_bmad/core/workflows/` has no fork lane, so core cannot be fork-managed in place (logged in `docs/fork-gaps.md`, 2026-07-03). The core workflow stays installed and untouched as the deep-divergence specialist.

---

## WORKFLOW ARCHITECTURE

Step-file architecture. Branching flow — exactly ONE of step-02 / steps-03+04 runs:

1. **step-01-triage** — ground the ask (grounding gate), INFER convergent vs divergent, announce a one-line verdict + route, proceed unless vetoed. The ONLY step that may halt, and only on an ungroundable ask.
2. **step-02-route-out** — convergent branch: emit the exact handoff to the owning lane, then STOP.
3. **step-03-ground-and-ideate** — divergent branch: read the named repo/artifact context FIRST, auto-select 1-2 techniques from `{brain_techniques_csv}`, generate ~20-30 grounded ideas.
4. **step-04-converge** — MANDATORY: cluster themes → ranked shortlist → one biased recommendation → write the session artifact; optional handoff line; default-no escalation aside to core brainstorming.

**Interaction model:** triage is inferred, never asked. In interactive mode the step-01 verdict line **ends the turn** — the user's reply is the veto window; any affirmative proceeds. Under `autonomous_mode: true`, proceed in the same turn (silence-of-objection). During ideation the user may riff between batches, but no step presents an option menu or a questionnaire.

### State Variables

- `{ask}` — the user's brainstorm ask, in their words
- `{ask_target}` — the concrete thing the ask is about (feature, surface, dataset, name, direction)
- `{ask_target_slug}` — kebab-case slug of `{ask_target}`: lowercase, spaces→hyphens, ≤5 words
- `{triage_verdict}` — `convergent` | `divergent`
- `{route_target}` — convergent only: `inline-deliberation` | `quick-spec` | `design-router`
- `{handoff_command}` — convergent only: the exact next command or inline answer
- `{grounding_sources}` — divergent only: files/artifacts actually read before ideating
- `{grounding_summary}` — divergent only: the ≤1-paragraph constraints-and-materials summary from step-03 §1
- `{selected_techniques}` — divergent only: the 1-2 techniques auto-picked from the CSV
- `{ideas}` — divergent only: the generated idea list; `{idea_count}` — its length
- `{ideas_by_theme}` — divergent only: the ideas regrouped under step-04 §1's themes
- `{shortlist}` — divergent only: the ranked top 3-5
- `{recommendation}` — divergent only: the ONE biased recommendation
- `{handoff}` — divergent only: the named consumer of the artifact (`quick-spec` | `design-router` | `n/a`)
- `{session_artifact_path}` — divergent only: path of the written session document

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `document_output_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`; the session artifact is written in `{document_output_language}`

### Autonomous Mode — decision autonomy only

`autonomous_mode` governs *decision* autonomy: the triage verdict, the route, technique selection, and ranking are yours — decide and proceed. It does NOT grant *intent* autonomy: if the ask names no target, HALT and ask ONE question (step-01 grounding gate). Never invent what the user wants to brainstorm about.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/quick-brainstorm`
- `session_artifact_dir` = `{planning_artifacts}/brainstorming`
- `session_artifact_path` = `{session_artifact_dir}/quick-brainstorm-{ask_target_slug}-{date}.md`

---

## EXECUTION

Read fully and follow: `{installed_path}/steps/step-01-triage.md` to begin.
