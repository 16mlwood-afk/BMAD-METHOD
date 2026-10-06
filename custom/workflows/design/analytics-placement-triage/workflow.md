---
name: analytics-placement-triage
description: 'Decide WHERE new analytics for an existing operational page should live — an inline subordinate band on the page, a tab on the same route, or its own dedicated analytical sibling page — BEFORE committing a design-handoff target. A thin router: it single-sources band-belongs / topology / hierarchy from design-handoff step-01 and analytics SHAPE from the analytics-surface-architect skill, then emits a placement verdict plus the exact design-handoff invocation to build it. Use when you have an operational page and want analytics but do not know if it is a band, a tab, or a page.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Single-sourced reasoning — this workflow is a ROUTER. It defers to these brains
# by name and applies them verbatim; it NEVER re-derives their logic here.
# The §5x brains this leaf single-sources now live in two design-handoff sub-steps
# (design-handoff's step-01-gather was split for context budget): §5b in -decide, §5d/§5e in -topology.
design_handoff_decide: '{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01b-decide.md'
design_handoff_topology: '{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01c-topology.md'
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
band_skill: 'operational-analytics-band'
uses_skills:
  - analytics-surface-architect
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

# Analytics Placement Triage Workflow

**Goal:** Given an existing operational page and a desire to add analytics, decide the one question that should be settled *before* any `design-handoff` runs: **does the analytics live as an inline band on the page, a tab on the same route, or its own analytical sibling page?** Then route — emit the exact `design-handoff` invocation that builds it. This workflow decides the **home**; `design-handoff` and the build skills design the analytics itself.

**Your Role:** You are a surface-placement triager. You do not design the analytics, you do not pick its chart shape, and you do not decide whether the numbers are deep enough. You answer **one** question — where it belongs — by assembling decisions other tools already own, and you hand off cleanly.

---

## OWNERSHIP & MATERIALITY GATE — read first

This is a **router**. It owns exactly one decision and borrows the rest. Keep the boundary honest.

**This workflow OWNS:** the placement verdict — `band` | `tab` | `sibling-page` | `remove-band` | `no-surface` — for analytics on an *existing operational page*, and the routing that follows from it.

**This workflow does NOT own (it defers, by name, applied verbatim — never re-derived):**
- *Whether* an analytics surface belongs at all → **band-belongs**, design-handoff step-01 **§5b**.
- *Whether* the page should split into tabs / a sibling route → **surface topology**, design-handoff step-01 **§5d**.
- *Ranking* multiple co-resident analytics surfaces → **hierarchy**, design-handoff step-01 **§5e**.
- The analytics **shape** (trend / coverage / ranking / …) → the **`analytics-surface-architect`** skill.
- **Designing / building** the analytics → `design-handoff` (→ `design-synthesize` → `design-implement`), and the `operational-analytics-band` skill for an inline band.

**USE this workflow when:** you have an operational page (a worklist) and want analytics on or around it, and you do not yet know if it should be a band, a tab, or a page — and you want that decided *before* you point `design-handoff` at a target (because the target you pick partly pre-decides the answer).

**Do NOT use when:** (a) you already know the home and just want it built → run `design-handoff` directly; (b) you only need the analytics *shape* → call `analytics-surface-architect`; (c) the page is not operational (an analytical or detail page) → placement is not the open question; (d) you want to design or critique an existing band → use `design-handoff` / `operational-analytics-band`.

**If uncertain, ABSTAIN — never guess a placement:**
- Cannot ground the **target page** or the **analytics question** from the input → **HALT** and ask (intent autonomy; see Initialization). Do not invent either.
- band-belongs (§5b) resolves **no band justified** → emit a `no-surface` verdict and stop. Do not place analytics the data doesn't warrant.
- Topology (§5d) genuinely does not resolve to a single home → surface the fork to the user; do not pick one silently.

---

## WORKFLOW ARCHITECTURE

Four-step linear flow. Every step is autonomous *for decisions*; only intent grounding can halt (step-01).

1. **step-01-scope** — resolve the target operational page (route + component), the analytics dataset and the user's question in their words, and any existing primitive band on the page. Grounding gate: halt if the page or the question can't be named from the input.
2. **step-02-assess** — run the *decision* brains, single-sourced and verbatim: band-belongs (§5b), topology (§5d), hierarchy (§5e if >1 surface). Short-circuits `none`→`no-surface` and `recommended-drop`→`remove-band` (both skip shape). Produces a structured assessment, not a verdict yet.
3. **step-03-shape** — for a surface that belongs (`inherited`/`recommended-new`), name the archetype via the `analytics-surface-architect` skill, with the page-mode derived from the topology verdict (analytical for a sibling page, operational otherwise). Skipped for `no-surface`/`remove-band`.
4. **step-04-route** — map the assessment to a placement verdict (`band` | `tab` | `sibling-page` | `remove-band` | `no-surface`), write the decision artifact, surface the net-new-scope veto, and emit the exact `design-handoff` invocation **carrying `--placement` so the verdict is consumable downstream**. Does NOT auto-invoke `design-handoff`.

### State Variables

- `{target_route}` — the operational page route the analytics attaches to (e.g. `/orders`)
- `{target_component}` — source file that renders the page (resolved in step-01)
- `{analytics_question}` — the single thing the analytics must answer, in the user's words
- `{analytics_dataset}` — the data the analytics reads (entities + the aggregate dimension)
- `{existing_band}` — description of any primitive analytics surface already on the page, or `none`
- `{band_belongs}` — §5b outcome for this surface: `inherited` | `recommended-new` | `recommended-drop` | `none`
- `{topology_verdict}` — §5d outcome: `single-page-appropriate` | `needs-tab-views` | `needs-sibling-route` | `unresolved` (the §5d `needs-detail-route` value is per-item depth, NOT an analytics home — see step-02)
- `{surface_hierarchy}` — §5e ranking when >1 analytics surface (`hero|supporting|drill` per surface), else `single`
- `{analytics_shape}` — the `analytics-surface-architect` archetype per surface, or `n/a` for `no-surface`/`remove-band`
- `{placement_verdict}` — `band` | `tab` | `sibling-page` | `remove-band` | `no-surface`
- `{is_net_new_scope}` — `true` when the verdict is `tab` or `sibling-page` (new surface area), else `false`
- `{handoff_invocation}` — the exact next `design-handoff` command string the verdict implies
- `{decision_artifact_path}` — path to the written placement-decision artifact

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode — decision autonomy only

`autonomous_mode` governs *decision* autonomy (which §5b answer, which topology verdict, how to rank surfaces) — proceed and decide. It does NOT grant *intent* autonomy:

- If the input names **no target page** OR **no analytics question/dataset**, HALT and ask: *"Which operational page is this for, and what should the analytics answer? (e.g. '/orders — show capital-at-risk and receiving gaps over time.')"* Do NOT guess the page or invent the analytics job.
- The **net-new-scope veto** (step-04) under autonomous mode becomes *surface-and-proceed*, not a hard stop: the veto *concept* is design-handoff §5b's `recommended-new` posture; the surface-and-proceed *behavior* under autonomy mirrors design-handoff §5d. Proceed with the recommended home and surface that it is net-new scope, so the user can veto after the fact.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage`
- `decision_artifact_dir` = `{implementation_artifacts}` (the placement-decision artifact is written here)
- `design_policy` = `{project-root}/docs/design-policy.md` (canonical project policy; §5b/§5d/§5e read it)

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage/steps/step-01-scope.md` to begin.

(Step chain: step-01-scope → step-02-assess → step-03-shape → step-04-route.)
