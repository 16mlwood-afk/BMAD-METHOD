---
name: maintenance-triage
description: 'Front door for production-driven work in brownfield projects. Take user reports, telemetry observations, error logs, dependency alerts — classify each by shape and route it: code-shaped to quick-spec/quick-dev, design-shaped to a Claude Design paste prompt or design-review/design-elevation. Use when the user says "what should I work on this week", "triage the backlog", or drops a list of production issues.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

quick_spec_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
design_elevation_workflow: '{project-root}/_bmad/bmm/workflows/design/design-elevation/workflow.md'
---

# Maintenance Triage Workflow

**Goal:** Convert raw production-driven signals (user reports, telemetry, error logs, dependency alerts, recent git churn) into 1–N small, prioritized tech-specs ready to feed into quick-spec or quick-dev. Provides structure for brownfield work that would otherwise free-fall into direct Mode B input and lose its provenance.

**Your Role:** You are a maintenance lead triaging the brownfield backlog. You don't *solve* problems here — you *frame* them as small implementable units, prioritize, and route. Solving happens downstream.

---

## SCOPE AND PHASE GATE

This workflow is for **brownfield** and **mixed** projects only. It assumes:
- There are production users whose reports carry weight
- The codebase has accumulated symptoms worth triaging
- "Done" is closer to "no regressions" than "shipped a new feature"

If `project_phase: greenfield`, HALT this workflow. Tell the user: *"Maintenance-triage is for post-launch projects. Your config says `project_phase: greenfield` — use quick-spec for new feature specs and dev-story for planned work."*

---

## WORKFLOW ARCHITECTURE

Three-step linear flow:

1. **step-01-gather-signals** — collect inputs. User-provided (default) or, where wired up, query project-specific signal sources (admin APIs, error logs).
2. **step-02-cluster-and-prioritize** — group related signals, score by severity × frequency × effort.
3. **step-03-emit-tech-specs** — for the top N items, decide each cluster's shape (code-shaped vs design-shaped) and produce a small triage-spec. Code-shaped → quick-spec (needs investigation) or quick-dev (already clear); design-shaped → a Claude Design paste prompt (surface + change clear) or design-review/design-elevation (needs design investigation). A design-shaped cluster must NOT be forced into a code spec.

State variables: `{signals}`, `{clusters}`, `{prioritized}`, `{emitted_spec_paths}`.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `project_phase` — **REQUIRED for this workflow**. If `greenfield`, HALT (see SCOPE AND PHASE GATE above).
- `date` as system-generated current datetime

### Autonomous Mode

`autonomous_mode` applies to *decision autonomy* — picking which signals to include, how to cluster, what severity to assign. It does NOT apply to *intent autonomy*:

- If the user provides no signals AND no project-specific signal source is wired up, HALT and ask: *"What should I triage? Paste any of: user reports, recent error log excerpts, dependency alerts, observations like 'the queries page feels slow.' I'll cluster and produce small tech-specs."*
- Do NOT invent signals. The whole point is to anchor on real production reality, not imagined work.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/maintenance-triage`
- `tech_spec_output_dir` = `{implementation_artifacts}` (specs written here use the standard quick-spec naming convention)

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/maintenance-triage/steps/step-01-gather-signals.md` to begin.
