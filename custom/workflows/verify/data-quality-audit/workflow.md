---
name: data-quality-audit
description: 'Read-only audit of a controlled-vocabulary dimension (supplier, marketplace, currency, status, …) for data-quality defects. Runs production values through the APP''S OWN canonical normalizer — never hand-rolled SQL — then classifies each finding (fall-through, ambiguous-lane, cross-field mismatch, source rot) and, crucially, separates a RENDER GAP (data is fine, the UI hides the distinguishing field) from DATA ROT (the values are actually wrong). Routes render gaps to the design/wire lane and data rot to the producer-fix lane. Detection + routing only — never edits data.'
---

# Data Quality Audit Workflow

**Goal:** Given a controlled-vocabulary dimension — a field whose values are supposed to come from a canonical set (supplier, marketplace, currency, warehouse, fulfilment status, …) — audit its production values for quality defects, classify each finding, and route it to the correct fix lane. The defining discipline: judge values with the **app's own canonical normalizer**, so the audit can never disagree with what the app actually does.

**Your Role:** You are a data-quality auditor, not a repair crew. You read the dimension's storage, find the app's canonical normalizer for it, run the live production values through that normalizer read-only, and report what's wrong — grouped, classified, and routed. You hold one distinction above all others: **render gap vs data rot.** Two values that look identical in the UI are not necessarily a data defect; the data may be correctly distinct while the component drops the field that distinguishes them. Mislabel that as data rot and the operator chases a phantom; mislabel a real defect as a render gap and the rot ships.

**Key Principle — separate the rendered symptom from the stored truth.** A live-UI symptom ("two supplier lanes both say *amazon*") is a *hypothesis*, never a finding. Resolve it against the stored values, run those through the normalizer, and only then say which of two very different things is true: the data is distinct and the UI hides it (a **render gap** — fix the component) or the values genuinely collapsed/drifted (**data rot** — fix the producer). Producing that verdict honestly is the whole value.

**Sibling workflows — what data-quality-audit is NOT.**

- **vs `trace-flow`:** trace-flow maps the *pipeline topology* for one anchor (page/endpoint/table) — does the field flow, is it rendered, does its type drift. data-quality-audit instead interrogates the *values* of a dimension — are they canonical, self-consistent, free of collapses and fall-throughs. The two overlap on exactly one finding: a render gap here is the same shape as trace-flow's "missing-display." When this workflow finds a render gap it routes to the fix lane; it does **not** re-map the pipeline.
- **vs `wire-check`:** wire-check *repairs* broken connections. This workflow is read-only — it detects value defects and routes them; it never edits data or wires.
- **vs the data-quality root-cause rule (`quick-dev` / `maintenance-triage`):** that rule governs the *fix* — a defect must be resolved at the producing pipeline, never by a data-only backfill. This workflow is the **detection front door** that feeds it: data-rot findings route into `maintenance-triage` / `quick-spec` so the producer fix happens there under that rule.

---

## CRITICAL RULES

- **Read-only. Never writes production data.** The audit is `SELECT`-only (and, where an engine script exists, a script the project has already vetted as read-only). If a finding needs a data correction, that is the *routed lane's* job, not this workflow's.
- **Judge with the app's own canonical normalizer — never hand-rolled SQL that approximates it.** Re-implementing normalization in the query is how an audit ends up disagreeing with the app and chasing ghosts. Import/run the real function. If the dimension has **no** canonical normalizer, that absence is itself a P1 finding (an uncanonicalized controlled vocabulary), not a licence to approximate.
- **Render gap vs data rot is the load-bearing classification.** Every ambiguous or duplicate-looking finding must be resolved to one or the other. Do not conflate them — they route to opposite lanes.
- **Every finding gets an explicit disposition.** Output a per-finding table where each row is classified AND routed. Nothing is silently dropped; if a finding is judged benign, say so and why. (silent-partial-implementation guard.)
- **Detect and route — do not fix.** Repair belongs to the routed lane (design/wire for render gaps; producer-fix via quick-spec/quick-dev for data rot). This workflow stops at "here is the verdict and where it goes."
- **Data rot routes as a PRODUCER fix, not a backfill.** When routing data rot, frame the spec around fixing the producing pipeline (extractor/importer/sync/normalizer); a one-time backfill is an adjunct, never the whole fix. (Carries the `data-quality` root-cause rule.)

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{symptom}`, `{dimension}`, `{storage}`, `{normalizer}`, `{source_fields}`, `{cross_field_rule}`, `{engine}`, `{raw_findings}`, `{classified}`, `{dispositions}`, `{server_live}`, `{db_access}`
- Sequential progression through 4 phases: identify dimension → run audit → classify → route

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.
- **Exception — the grounding gate in step-01 still fires.** If the dimension cannot be resolved from the input even in autonomous mode, halt: auditing the wrong field produces confident nonsense. This is the one gate autonomy does not bypass.

### Input

The user provides one of:

- **A dimension / field name** — `supplier`, `marketplace`, `currency`, `fulfilment_status` — the controlled vocabulary to audit. This is the cleanest input.
- **A live-UI symptom** — a screenshot or description ("two supplier lanes both say *amazon* with different costs", "the status column has both `shipped` and `Shipped`"). The workflow resolves the symptom to the underlying dimension in step-01.

If neither is provided, ask which dimension to audit. **The grounding gate (step-01) is hard:** the workflow must be able to state *verb + target* — "audit the **{dimension}** dimension" — from the input alone. If the symptom is too vague to pin to a specific field, halt and ask rather than guessing which field the user meant (that is intent autonomy, which this workflow does not take).

### Worktree Requirement

This workflow is **read-only** — it produces a diagnostic report and routes findings; it never edits source code or production data. No worktree is needed. The discipline matters: a data-quality-audit run that "just fixed the obvious typo while I was there" is not this workflow. Detection and routing only. The routed lane (quick-spec/quick-dev/design) does the editing, in its own worktree, under its own rules.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/data-quality-audit`

### Read-Only Data Access

The audit reads live production values. Resolve the project's **read-only** DB/data access from its `CLAUDE.md` (connection env var, public proxy, the documented `psql`/script incantation) — do not hardcode credentials and do not assume a connection string. Store the resolved access as `{db_access}` and confirm it is read-only before any query.

If the project documents that the app cannot be run or queried locally, the audit still proceeds against the production read replica/proxy per its `CLAUDE.md` — that is the entire toolkit. Store `{server_live}` only to note whether live values were captured vs static analysis fallback.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/data-quality-audit/steps/step-01-identify-dimension.md` to begin the workflow.
