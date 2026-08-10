---
name: design-handoff
description: 'Generate an unbiased Claude Design brief from a completed implementation. Gathers data model, user context, design tokens, and constraints — deliberately excludes current layout and component structure so the designer starts from a blank canvas. Use after building a feature when you want Claude Design to design or redesign the UI.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_agent_workflow: '{project-root}/_bmad/bmm/workflows/design/design-agent/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
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

# Design Handoff Workflow

**Goal:** After an implementation is complete (or partially complete), produce a structured design brief that Claude Design can consume directly from the repo. The brief gives Claude Design everything it needs to design (or redesign) the UI without asking clarifying questions about architecture, data shape, or constraints.

**Your Role:** You are a bridge between engineering and design. You understand both the technical implementation and what a designer needs to produce great work. You extract the right context from code — not too much (overwhelming), not too little (ambiguous) — and structure it for a design tool that has repo access.

**Key Insight:** Claude Design can read files from the repo (GitHub is linked). The brief should reference file paths for deep context rather than inlining everything. But it MUST inline enough for Claude Design to start working immediately — don't require it to read 20 files before understanding the ask.

**Anti-Bias Principle — CRITICAL:** The current UI was built by a developer, not a designer. Its layout, information grouping, visual hierarchy, and component structure are *implementation choices*, not design requirements. The brief must **never** describe what the current page looks like or how information is currently organized. Instead, give the designer the raw materials — data model, user purpose, constraints, visual direction — and let them create their own vision. The brief describes the desired aesthetic (theme, reference products, tokens), not the current structure.

**Anti-Bias Principle II — policy defaults are bias too — CRITICAL:** The project design policy supplies two different things, and they carry different authority. The **visual system** (tokens, colour, type, component treatment, hard failures) is non-negotiable — the brief inherits it verbatim. But the policy also attaches a **default composition to each page-mode** (operational → table-first worklist + right-side detail drawer; analytical → chart-led; detail → record-view), and that default is *not* a certification that THIS surface's job fits it. Stamping the mode's default composition into the brief unquestioned is a bias as real as inheriting the legacy layout — and harder to catch, because it feels like correctly following the system. A pull-based dispensing queue, or a per-item comparison surface, can be fully "operational" and yet be actively harmed by a table-first worklist + right-side drawer. §5a (Composition Fit Check) decides the *primary composition* from the job, and surfaces a `recommended-alt` for veto when the default doesn't fit. **Inherit the visual system; verify the composition.**

**Deliverable-Completeness Principle — every spawned surface must be DRAWN, not inferred — CRITICAL:** A page does not render in isolation — it spawns secondary surfaces at runtime: the right-side **detail drawer** the operator drills into, and the **§13 expand-in-context lookup drawers** that open over it (a warehouse, a catalog record, a supplier — the foreign record read through a relation). These are part of THIS brief's deliverable, never a separate "pending" brief and never left to the implementer to improvise. The downstream pipeline is **non-interpretive by design**: `design-synthesize` / Claude Design renders only the frames the brief's §7 **Surface Inventory** enumerates, and `design-implement` pixel-matches only the frames the bundle actually contains — so a drawer the brief never listed as a required frame is never drawn, and `design-implement` then *infers* it. That inference is exactly the thin, unformalised drawer this principle exists to prevent: bare `€60` money with no GBP/VAT basis (a `docs/design-policy.md` §15 violation that ships because the drawer was never a designed surface), a lookup drawer showing only code/type/status because its §2a inline-lookups were never specified. **If you want it built well, it must be drawn.** Step-01 §5f derives `{spawned_surfaces}` (one frame per spawned surface) and §7 renders it as the Surface Inventory — a required deliverable list, **frame-name keyed** so the same name travels brief → rendered frame → `design-implement` grid row with zero inference at any hop. Escalation to a *separate* brief is reserved for a drawer that has outgrown a drawer — a deep full-page record route (§5d `needs-detail-route`); a drawer that fits a drawer is drawn in THIS brief. The corollary holds at intake: a §13 **lookup drawer targeted directly** as a handoff is **redirected, not accepted** (step-01 §2a) — it is owned by the relation and drawn as a frame in its parent's §7, so handing it off standalone would duplicate an owned frame (multiple-active-brief invariant). And the render half is enforced downstream: `design-synthesize` step-01 §7a turns every §7 Surface Inventory frame into a rendered screen (Gate 1f halts if a frame would go undrawn), so the frames this principle enumerates are actually drawn, not just listed.

**Brief Section Order:** The template follows this sequence for optimal handoff to Claude Design: Feature purpose → Domain data → User context → Visual direction → Hard constraints → Design ask. This order lets the designer understand the business problem before encountering visual constraints.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow encounters conflicting guidance, the order of authority is:

1. **Project design policy** — `{project-root}/docs/design-policy.md` (canonical) or `{planning_artifacts}/brand-identity.md` (legacy slot). Hard failures, status rules, layout principles, and reference patterns are defined here.
2. **Shared BMAD design standards** — `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails that the project policy can override but not contradict.
3. **Generated design briefs** — `{implementation_artifacts}/design-brief-*.md`. Derivative of (1) and (2). Briefs MAY restate, focus, or summarize the policy for one feature. Briefs MUST NOT introduce carve-outs, softenings, exceptions, parentheticals, or anti-patterns the policy does not contain.
4. **Review/refinement artifacts** — `{implementation_artifacts}/screen-review-*.md`, design-tuning state files. Derivative of (3). Cannot contradict higher levels.

**Implications for this workflow:**
- When step-03 generates the brief, sections quoted from the policy (visual identity, hard failures, AI sensitivity, component patterns) must appear **verbatim** — no inserted exceptions, no editorializing parentheticals, no "the codebase already does X so the designer may also" softenings.
- If the brief author (you) believes the policy is wrong or incomplete, surface that to the user as a `modify-design-policy` candidate. Do NOT route around the policy by patching the brief.
- A brief that fails the precedence check propagates the drift into every downstream design-review and design-tuning run, because those workflows treat the brief as authoritative for the feature. Catching drift here is the cheapest fix.

---

## BRIEF REVISION POLICY — CRITICAL

This workflow is the **producer** under `shared/brief-revision-policy.md`. Every brief written by step-03 must carry the provenance frontmatter block defined there. Step-03 is responsible for:

- Detecting whether an active predecessor brief already exists for this `target_slug` (§1a of step-03).
- Setting `change_class` to `original` (no predecessor) or `material_revision` (one predecessor) — a re-run of `design-handoff` on the same surface is material by definition.
- Halting if two or more active predecessors exist — that's a pre-existing invariant break that this workflow cannot silently paper over.
- Flipping the predecessor's `brief_status` to `superseded` and setting its `superseded_by` in the same run (§1b of step-03) when superseding.

Consumers (`design-artifact-loop`, `design-synthesize`) validate the provenance block at intake and halt on missing fields, broken invariants, or forbidden combinations. A brief that fails consumer validation is unconsumable — there is no fallback. See `shared/brief-revision-policy.md` for the full contract, the editing rules, and the halt diagnostics consumers emit.

---

## OUTPUT CONTRACT & WORKFLOW-FEEDBACK ROUTING — CRITICAL

This workflow's closing hand-off message is governed by **`shared/close-out-contract.md` (STD-CLOSEOUT-001)** — the corpus-wide standard. The essentials it binds here:

- **Audience-first, never process narration.** The close is a hand-off to the NEXT consumer (Claude Design / `design-synthesize`), not a report of what you did. Process narration ("I did X then Y", branch/PR choreography, workflow history, decision diary, provenance bookkeeping) is forbidden by default — trace on demand only. `step-04-deliver.md` §10 is this workflow's design-lane instantiation of the contract's shape (Active artifact → What changed → Substantive corrections → Delivery status → For {consumer}); §10 owns that template, do not restate it here.
- **Output-shape feedback is a workflow-PATCH request.** When the user critiques the *shape* of this workflow's output ("stop narrating history", "speak in active-artifact / material-delta / next-consumer terms", "fix this at the workflow root"), patch the fork step FIRST (normally `step-04-deliver.md` §10, or `shared/close-out-contract.md` if the rule itself is wrong) so it propagates by sync, then regenerate — memory is a soft backstop, never the primary remediation. Full rule: `shared/close-out-contract.md` §4.
- **Completion disposition.** As a completion workflow, design-handoff's close must declare a `completion_disposition` per **`shared/completion-contract.md` (STD-COMPLETION-001)**. `step-04-deliver.md` §10 owns the disposition template (the `Completion:` line in its Delivery block — `pr_merged` / `pr_open` / `owner_gated_residue`); diagnosis with no disposition is an invalid exit. Do not restate the template here.

---

## GATE 1 — BRIEF-READY (step-03c) — CRITICAL

This workflow owns **Gate 1** of the three-gate design route. After step-03 writes the brief
and **before** step-04 delivers it, `steps/step-03c-gate1-brief-ready.md` answers one question:
*does this exact brief contain unresolved material brief-visible defects?*

Everything inside it is an **internal mechanic of that one gate**, never a separate step or a
separate approval: the deterministic checker (`tools/check-brief-readiness.py`), an **isolated
adversary reviewer that did not author the brief**, the review bound to the exact brief body by
SHA-256, evidence-bounded auto-repair of draft-only defects, a re-check of the repaired text,
and a disposition per finding. It emits `brief-adversary-{target_slug}-{date}.md`, which
step-04 stages in the same commit as the brief.

**Phase 1 is WARN-ONLY, and warn-only is NOT uniform** — both halves must be stated on the
artifact and in the close-out:

- **Instrument results never block.** A fired probe, an adversary finding, an `open`
  disposition: recorded, surfaced, delivery proceeds.
- **A genuine missing OWNER product/design decision PAUSES this brief.** Do not invent the
  value; do not hand an incomplete contract to Claude Design. This is not the gate blocking on
  findings — it is the route refusing to guess a decision that is the owner's to make.

**Scope: DRAFTS ONLY.** A backlog brief is never forced through Gate 1 — it enters the route at
**Gate 3** (`design-tuning` step-04) and reaches Gate 2 only via an accepted brief-gap finding.
**Gate 2 is not consulted at Gate 1**: an undelivered draft has no supersession problem.

Promotion to Phase 2 (blocking on findings) is a **separate owner decision**. Full contract —
artifact schemas, SHA lifecycle, disposition enum, entry points, promotion evidence:
`shared/design-gate-artifacts.md`.

---

## ANALYTICS PRESENTATION RATIONALE — companion artifact

When a brief carries an analytics band (`{has_analytics_band}` is `true`), this workflow emits a **second** artifact beside the brief: `design-rationale-{target_slug}-{date}.md`. It documents *how* the analytics presentation was decided — the page-mode signal, the band-belongs answers, the archetype candidates weighed, the shapes rejected, and the explicit time≠trend check. The brief records the winning choices; the rationale records the deliberation behind them.

This exists because the brief is a **bias filter** (it withholds the current layout so the designer starts blank) — so the reasoning cannot live inside the brief without breaking that mandate. Key rules (full spec in `shared/analytics-rationale.md`):

- **Conditional.** No band → no rationale file. Never emitted for a plain operational worklist.
- **Not a brief.** Out of scope for `brief-revision-policy.md` — no Block A, no 6 intake checks, no consumer validation. It carries only its own `rationale_status`/`supersedes`/`superseded_by` lineage, derived 1:1 from the brief it accompanies.
- **One-way linkage.** The rationale's `accompanies_brief` names the brief; the brief never references the rationale. Claude Design reads the brief, never the rationale.
- **Delivered together.** step-04 stages both in one commit/PR so a brief on `main` always has its rationale beside it.

The archetype reasoning is produced by the `analytics-surface-architect` skill (invoked in step-01 §5c — the single selection brain, so handoff, design-review-pr, and a human all reason the same way), captured at decision time, and rendered by step-03b. Capturing it where the decision is made is what turns a discarded deliberation into an auditable record. The skill is the preferred path; §5c falls back to applying `shared/analytics-archetypes.md` inline if the skill isn't synced into the project.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables (see below)
- Sequential progression: gather → audit → generate → deliver

**Step 4 (deliver)** is governed by `shared/delivery-to-main.md`. It commits the brief, opens a PR, merges to `main`, and surfaces the merged URL — closing the gap between "file written to disk" and "file accessible to external consumers (Claude Design, downstream synthesize, design-implement) via `origin/main`". Skippable via `--no-deliver` or `delivery.design-handoff: skip` in config.

### State Variables

One-line definition · allowed values · where set. The **rationale** for each variable — the failure it guards, the anti-bias reasoning, the cross-variable contract — lives in **`./state-variables.md`** (read on demand; kept out of this hot-path index for context budget). Load-bearing semantics are also re-stated at point-of-use in the step files.

- `{feature_name}` - Name of the feature being handed off.
- `{injected_placement}` - `band` | `tab` | `sibling-page` | `remove-band` | empty. Set from `--placement` (or an `analytics-placement-triage` handoff). Non-empty → §5b/§5d honor it and skip re-deriving the analytics-home axis (the consumability contract — see Input + state-variables.md). Empty (default) → derive as before.
- `{injected_archetype}` - one of the nine archetypes, or empty. Set from `--archetype`. Non-empty → §5c sanity-gates then honors it (`injected-by-triage`) and skips re-selection. Empty → §5c selects normally.
- `{feature_scope}` - "new" (design from scratch) or "redesign" (improve existing).
- `{project_phase}` / `{is_greenfield}` - `greenfield` | `brownfield` | `mixed` (absent ⇒ `brownfield`); `{is_greenfield}` = true iff `greenfield`. Governs step-01 §1c source binding (greenfield reads specs not code, skips step-02); brief shape is phase-agnostic. Rationale → state-variables.md.
- `{feature_purpose}` - What the feature does and why it exists — NOT how it is currently laid out.
- `{must_support_capabilities}` - Jobs the operator must accomplish beyond the primary goals, as outcomes (NOT UI mechanics); set step-01 §4, rendered into brief §1. The anti-silent-drop "keep" list. Empty when none beyond primary goals. Rationale → state-variables.md.
- `{dropped_capabilities}` - Capabilities deliberately NOT carried into this brief, each `{ capability · backing_action · reason∈relocated|obsolete|out-of-scope-by-design }`; set step-01 §3 mutation audit, surfaced step-03 §5. The anti-silent-drop "shed" log — never empty by omission. Rationale → state-variables.md.
- `{data_shape}` - Domain entities + primitive fields in domain language — walked up from DB schema, NOT the page server return type. Capture rules in step-01.
- `{api_surface}` - Endpoints and response shapes the frontend can call.
- `{implementation_files}` - File paths for technical reference only (not for layout inspiration).
- `{brand_identity_path}` - Path to the project's brand identity / design-policy document (if it exists).
- `{brand_identity}` - Contents of that document — the PRIMARY source for design-system context when present (supersedes token extraction + generic guardrails).
- `{policy_version}` - Integer version of `docs/design-policy.md` at brief-gen time (`1` if no version field; `0` if no policy). Stamped into the brief's `policy_version_required:` for downstream drift detection. Rationale → state-variables.md.
- `{design_system}` - "branded" | "existing" | "external". Controls which variant of §4 (Visual Direction) and §5 (Hard Constraints) the brief uses.
- `{design_system_name}` - If external: the system name (e.g. "Meridian"). Empty otherwise.
- `{design_tokens}` - Design tokens — from brand identity (preferred) or extracted from codebase.
- `{existing_patterns}` - Component patterns — from brand identity (preferred) or observed in other pages.
- `{page_mode}` - `operational` | `analytical` | `detail` (the full three-value contract enum; `brief-revision-policy.md` Block B). Selected step-01 §5; governs §4a composition + §4b analytics inclusion (detail never carries a band).
- `{composition_provenance}` / `{composition_rationale}` - `policy-default` | `recommended-alt`. WHETHER the page-mode default composition fits the job — decided step-01 §5a by the job, not inherited. `recommended-alt` is veto-surfaced and does NOT change `{page_mode}`. Rationale (Anti-Bias Principle II) → state-variables.md. `{composition_rationale}` empty when `policy-default`.
- `{spawned_surfaces}` - The required deliverable frames §7 enumerates: primary surface + detail drawer + one frame per `{linked_records_inventory}` entry. Derived step-01 §5f (NOT recalled); each `{ frame_name · trigger · render_as · must_contain · figures · lookups (depth-1) }`; frame-name keyed. The Deliverable-Completeness contract. Empty only for a true leaf surface. Rationale → state-variables.md.
- `{band_provenance}` / `{has_analytics_band}` - `inherited` | `recommended-new` | `recommended-drop` | `none`. WHY a band exists — decided step-01 §5b by data + job, not the legacy render. `{has_analytics_band}` = true iff `inherited`/`recommended-new`, gates §4b. Rationale (band presence is a judgment) → state-variables.md.
- `{analytics_archetype}` - The band *shape*: `trend` | `distribution` | `composition` | `ranking` | `coverage` | `flow` | `waterfall` | `single-metric` | `correlation` (or `unclear` → ask); empty when no band. **Selected step-01 §5c via the `analytics-surface-architect` skill** (single selection brain; `shared/analytics-archetypes.md` is the taxonomy SoT). Rationale → state-variables.md.
- **Analytics reasoning capture** — the `analytics-surface-architect` decision object, captured step-01 §5c (populated iff `{has_analytics_band}`; rendered by step-03b + §4b; empty otherwise). Fields + rationale → state-variables.md: `{page_mode_rationale}`, `{band_decision_log}`, `{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`, `{archetype_drill_map}`, `{archetype_prohibited}`.
- `{rationale_output_path}` / `{rationale_output_filename}` / `{rationale_path_relative_to_repo_root}` - the analytics rationale artifact written by step-03b (only when `{has_analytics_band}`); delivered in the same commit by step-04.
- **Gate 1 (step-03c)** — `{gate1_artifact_path}` (the `brief-adversary-*.md` written by the gate; delivered in the same commit by step-04) · `{brief_body_sha}` / `{brief_body_sha_after_repair}` (the review binding — brief body only, frontmatter excluded; a mismatch at step-04 INVALIDATES the review and the gate re-runs) · `{gate1_owner_decisions}` (genuine missing owner product/design decisions; **empty is the normal case**) · `{gate1_paused}` (true iff `{gate1_owner_decisions}` is non-empty — the one thing that stops step-04 in Phase 1). Contract → `shared/design-gate-artifacts.md`.
- `{constraints}` - Hard constraints (responsive breakpoints, data density, accessibility).
- `{user_context}` - Who uses this feature, what they're accomplishing, frequency of use.
- `{reference_pages}` - Existing app pages with good design to reference — from brand identity (preferred).
- `{hard_failures}` - Non-negotiable anti-patterns from brand identity — any match fails review.
- `{github_repo_url}` - GitHub HTTPS URL for the repo (no trailing `.git`).
- `{output_path}` / `{output_path_relative_to_repo_root}` - Absolute brief path on disk / path relative to repo root (for GitHub URLs + Claude Design references).
- `{handoff_mode}` - `"fresh-design"` (default) | `"refine-screen"`. Refine-screen consumes a `screen-review` artifact (auto-running `design-review --artifact` if none exists) and produces a tightly-scoped refinement brief.
- `{review_artifact_path}` - Absolute path to the consumed `screen-review-*.md` (refine-screen only).
- `{refine_focus}` / `{required_variants}` / `{peer_steals}` / `{already_fine}` - parsed from the screen-review artifact (refine-screen only): violations / edge states / peer-pattern transplants / keepers-that-must-not-break.
- **Finance-domain pass** — set step-01 §3b only when `{is_finance_surface}` = `true` (else empty/absent); produced by the `finance-domain-pass` skill (inline fallback if not synced). Captures finance MEANING, never layout. Fields + rationale → state-variables.md: `{is_finance_surface}`, `{finance_report_type}`, `{finance_column_semantics}`, `{finance_exception_expectations}`, `{finance_unresolved_assumptions}`, `{finance_terminology}`, `{finance_must_not_infer}` (its capability/surface outputs travel `{must_support_capabilities}` / `{dropped_capabilities}` / `{spawned_surfaces}` — no new vars).
- **Ledger-archetype pass** — `{is_ledger_surface}` + `{ledger_view}` (`not-a-ledger` | `register` | `running-balance`) + `{ledger_archetype_policy_source}`, set step-01 §3g. Asked when `{is_finance_surface}` is true OR rows are quantity/stock movements — finance-shaped is the PRE-FILTER, not the answer. The test is **movements over time on an account with a column meant to be summed**; a route NAME is never evidence. Renders brief §2d. The view declaration is REQUIRED only when a ledger archetype actually resolves in this project's policy chain (detected from what the policy DECLARES — never a hardcoded project list); where none resolves the surface is still classified and an Open Question is recorded, never fabricated rules. Gate class **(g)** in step-03 fires on ABSENCE of the field, never on a value. Fields + rationale → state-variables.md.
- **Live-process pass** — `{is_live_process_surface}` (`true` iff the surface's primary job is watching/controlling a long-running in-flight process — set step-01 §3c) + `{runtime_behavior_contract}` (run lifecycle state machine · per-item states incl. failure/partial lanes · update transport & staleness budget · control verbs as outcomes · available progress signals; derived from the driving code, never invented). Captures TIME semantics, never widgets. Renders into brief §2c; each operator-distinct lifecycle state becomes a `{primary}--{state}` state-variant frame via §5f. Rationale → state-variables.md.
- **Interaction-model pass** — `{is_processing_cockpit}` (`true` iff `page_mode: operational` AND §2 user context is expert/high-frequency/keyboard-first — a queue cleared one item at a time at speed; set step-01 §3d) + `{interaction_model_contract}` (operation surface keyboard-first · per-item action set & commit weight reversible-vs-irreversible · momentum-after-commit auto-advance+undo · consequence-preview before an irreversible commit · confidence-scaled fast-path-vs-forced-decision; derived from §1 capabilities + §2 user context + the §3 mutation audit, never invented). Captures the OPERATION, never key maps. Renders into brief §4f (cross-cutting behavior contract — no new frames). Rationale → state-variables.md.
- **Operator-domain pass** — `{operator_domain_present}` (`true` iff `{is_processing_cockpit}` AND a profile resolved AND the validation gate passed — set step-01 §3e, **co-fires with §3d**) + the `{operator_*}` block (`{operator_role}` · `{operator_trust_boundary}` may/may-not-decide+write-trust · per-decision `{operator_decides}`/`{operator_known_before_ask}`/`{operator_evidence_required}`/`{operator_forbidden_asks}` · top-level `{operator_must_not_infer}` · `{operator_ordering_invariants}` · `{operator_policy_collisions}`). Produced by the `operator-domain-pass` skill (inline fallback if not synced), which SELECTS from `docs/<operator>-operational-profile.md` and never invents operator facts. Captures WHO the operator is + what to SHOW before ASK (the twin of §3b finance-domain-pass, for OPERATOR ROLE), never layout. **HALT-on-missing-profile** when `{is_processing_cockpit}` and no profile resolves. Renders into brief §4f (cross-cutting operator-meaning contract — no new frames). Rationale → state-variables.md.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)
- `project_phase` (`greenfield` | `brownfield` | `mixed`; absent ⇒ treat as `brownfield`). Sets `{project_phase}` and `{is_greenfield}` (= true iff `greenfield`). When `{is_greenfield}` the gather step reads **specs instead of built code** (there is no code yet) — see step-01 §1c (Project-phase source binding), which rebinds §2–§4 sources, relaxes the §2-pre grounding gate to a settled-spec/policy basis, and skips step-02. `brownfield`/`mixed` → the existing code-reading path, unchanged.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- **Never halt or wait for user input.** Make expert-level decisions and proceed.
- **Infer feature scope from git history** — if the feature was just committed, it's "new" unless the user says otherwise.
- **Auto-detect design tokens** from CSS/style files without asking which file.

### Input

The user may provide:

- **A feature name or description** — "the outreach queue I just built"
- **A commit hash or branch** — the workflow will diff to understand what changed
- **A route** — `/outreach`, `/pipeline` — the page to design
- **A design system directive** — "use Meridian", "use the corporate design system", "external design system"
- **An injected placement decision** — `--placement <band|tab|sibling-page|remove-band>` (passed directly, or by `analytics-placement-triage`, which decided the analytics *home* upstream using the same §5b band-belongs and §5d topology brains this workflow owns). Sets `{injected_placement}` to that value. When present, the band/topology decision for this surface was **already made by the single-source brain at the placement-triage gate** — so §5b/§5d **honor it and skip re-derivation** (see step-01 §5b/§5d short-circuits). This is the *consumability contract*: it stops the placement verdict from degrading into advisory prose this workflow silently re-decides. Absent (the default) → `{injected_placement}` is empty and the workflow derives band/topology as before — fully backward-compatible.
- **An injected analytics archetype** — `--archetype <trend|distribution|composition|ranking|coverage|flow|waterfall|single-metric|correlation>` (passed by `analytics-placement-triage`, which already selected the shape via the same `analytics-surface-architect` skill). Sets `{injected_archetype}`. §5c honors it and skips re-selection — the shape was already chosen by the same `analytics-surface-architect` skill upstream, so it is honored (after a §5b-style sanity gate), not re-derived; this threads provenance and avoids the redundant re-derivation. Absent (the default) → `{injected_archetype}` is empty and §5c selects normally.
- **An explicit supersede directive** — `--supersede <predecessor-brief-filename>` (e.g. `--supersede design-brief-clerk-grading-workspace-v2-2026-06-28.md`). Use ONLY to deliberately re-issue the SAME surface under a cleaner `target_slug` than the active predecessor carries. Without it, step-03 §1a HALTs on a different-slug active brief for this surface (the slug-EXACT safety gate — never auto-supersede across slugs). With it, that HALT becomes a `material_revision`: the named predecessor is flipped to `superseded`, `supersedes:` is set to it, and a `slug renamed {old}→{new}` note is recorded. This is the in-situ rename path so a mis-slugged predecessor is never a permanent trap (`docs/fork-gaps.md` §1a slug-rename). Absent (the default) → no rename; same-surface/different-slug still HALTs.
- **Nothing** — the workflow will look at the most recent commit(s) on the current branch

If the input is ambiguous, ask ONE clarifying question maximum, then proceed.

### Brand Identity & Design System Detection

**Step 1 — Check for a project design policy (highest priority):**

Projects may declare visual direction, layout principles, status systems, and hard failures in one of two locations. Check both, in order:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

If `{project-root}/docs/design-policy.md` exists, prefer it. Otherwise fall back to `{planning_artifacts}/brand-identity.md`. Both files play the same role — they describe the project's design system. `design-policy.md` is the canonical name; `brand-identity.md` is the legacy slot.

If either file exists:
- Read it and store as `{brand_identity}`
- Set `{brand_identity_path}` to the file path
- Set `{design_system}` = "branded"
- Extract `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, and `{hard_failures}` directly from the document
- **Skip design system questions entirely** — the project policy IS the design system

**Step 2 — If no brand identity, check for external directive:**

- If the user mentions an external design system by name → `{design_system}` = "external", `{design_system_name}` = that name
- If NOT in autonomous mode → ask: **"Should this design use the existing tokens from the codebase, or an external design system?"**
- If in autonomous mode → default to "existing"

**Step 3 — Fallback (no brand identity, no external directive):**

Set `{design_system}` = "existing" — tokens will be extracted from the codebase in step 02.

**Why brand identity first:** A brand identity document captures the project's ACTUAL visual language — not raw CSS tokens, not generic anti-patterns, but the specific decisions that make this app look like this app. When one exists, it provides both positive anchors (what we look like) and negative constraints (what we never do), which are far more effective than generic guardrails. Without it, Claude Design fills the vacuum with its strongest priors (generic SaaS templates).

### Refine-Screen Detection & Artifact Loading

The workflow handles two modes:

- **`fresh-design`** (default) — new page, new feature, structural redesign. The brief is open and creative. The rest of this section does not apply.
- **`refine-screen`** — iteration on an existing baseline screen. The brief is tightly scoped to the diagnostic from a `design-review` artifact. NO USER COMPLAINTS ARE COLLECTED — the diagnostic is automated.

**Detect mode** in this order:

1. If the user's invocation or prompt-expansion contains the literal `--refine-screen`, `--refine`, or starts with "refine"/"iterate"/"tighten"/"polish"/"second pass on" → `{handoff_mode}` = `"refine-screen"`.
2. If `design-pm` set `{handoff_mode}` in state when routing → honor it.
3. Otherwise → `{handoff_mode}` = `"fresh-design"`.

**If `{handoff_mode}` = `"refine-screen"`, run artifact loading BEFORE step-01:**

1. **Resolve target slug.** From the user's input identify the target route or feature slug. Same kebab-case rule as `design-review`: pathname → strip slashes → replace `/` with `-` → lowercase. Examples: `/reclaim/avask` → `reclaim-avask`; "iterate AVASK" + the AVASK page in context → `reclaim-avask`.

2. **Search for an existing artifact:**

   ```bash
   ls -t {implementation_artifacts}/screen-review-{target_slug}-*.md 2>/dev/null | head -1
   ```

   Pick the most recent. Also accept matches where the slug is a prefix (e.g., `reclaim-avask-v2-...md`).

3. **Branch on result:**

   - **Artifact found AND less than 24 hours old:** Load it. Set `{review_artifact_path}` to its absolute path. Parse the YAML frontmatter into state, then parse the body's Violations → `{refine_focus}` (preserve V-IDs, severities, and all per-violation fields), Edge States → `{required_variants}`, Peer Steals → `{peer_steals}`, Keepers → `{already_fine}`. Proceed to step-01.

   - **Artifact found but older than 24 hours:** The screen may have changed. Surface to the user: "Found a screen-review artifact from {age}. Use it as-is, or re-run design-review --artifact?" In autonomous mode, prefer fresh — re-run design-review.

   - **No artifact found AND `autonomous_mode` = true:** Auto-invoke `design-review` with `{output_mode}` = `"artifact"` and the same `{target_url}` / target context. Load the resulting artifact and proceed.

   - **No artifact found AND `autonomous_mode` = false:** Stop. Tell the user: "Refine-screen mode requires a screen-review artifact. Run `/bmad:bmm:workflows:design-review --artifact` on the target page first, then retry this workflow." Do NOT fall back to asking the user for complaints — the whole point of refine-screen mode is that the diagnostic is automated.

4. **Skip the "ask user what's wrong" prompt in step-01.** The artifact replaces it. The user-context question in step-01 still applies (who uses this, how often) since the artifact doesn't cover that.

5. **In step-03, the Design Ask section is rewritten** to the refine-screen variant — see step-03 for the bounded refinement template.

**Refine-screen rule:** The brief produced in this mode must be BOUNDED. It addresses the artifact's top 3 violations (by severity order) and requires variants for the artifact's edge states. It does NOT redesign the IA, does NOT introduce new components unless required to land one of those top 3, and does NOT propose a "get radical" alternative. Open creative freedom belongs in `fresh-design`. Lower-severity violations (V4+) remain in the artifact for visibility but are not in-scope for the brief unless the user explicitly asks.

**Collapse allowance (one collapse max).** Strict severity ordering can fill all three slots with mechanical token / class-swap violations (hex literal cleanup, `rounded-full` → `rounded-md`, `uppercase tracking-wide` removal, etc.) when a higher-leverage design-requiring violation sits at V4+. The brief is meant to drive design work, not enumerate find-and-replace. Therefore: **if two or more of the top 3 violations are mechanical (no design decision required — concrete class swap fully specified by the policy)**, collapse them into one combined fix labeled `Vx+Vy (combined)` and promote the next design-requiring hard failure into the freed slot.

Constraints on the collapse:
- **At most one collapse per brief.** Never collapse two pairs.
- **The collapsed entry must keep both V-IDs visible** so artifact-to-brief lineage stays traceable: `Vx+Vy (combined)` in the section header, both V-IDs cited in the body.
- **Only mechanical violations are collapsible.** Litmus test: if the Required Correction in the artifact gives an exact class swap or token table that an implementer can apply without a designer thinking, it is mechanical. If the correction requires choosing a layout, sizing, or interaction pattern, it is design-requiring and must keep its own slot.
- **Severity floor.** The promoted violation must be `hard failure` — never promote a `major` or `minor` into the top 3 just to fill the slot. If the next-highest hard failure also turns out to be mechanical, do NOT collapse a second time; emit the brief with only 2 design-requiring fixes and a combined entry, and surface to the user that the artifact's hard-failure list is mostly mechanical.
- **Document the collapse.** In the brief's `mode` / `targeted_changes` frontmatter (per `brief-revision-policy.md` §2), add a `collapse_note:` line stating which V-IDs were collapsed and why.

---

## EXECUTION

Read fully and follow each step file in sequence:

1. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01-gather.md` — gather feature purpose, data shape, linked records, user purpose (§1–§4). **Split for context budget, it chains through two more sub-steps before step-02:** `step-01b-decide.md` (§5 page mode → §5a composition → the §5b–§5c-3 analytics decision stack; when a band is in play §5c **invokes the `analytics-surface-architect` skill** to select the archetype and capture its full decision object — candidates weighed, drill map, prohibited) and `step-01c-topology.md` (§5d topology → §5e hierarchy → §5f spawned surfaces → §6 user context → the gather COMPLETION checklist). Same content as the former single step-01-gather; no behaviour change. Chain: 01-gather → 01b-decide → 01c-topology → step-02.
2. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md` — audit the current design system / extract tokens / locate reference pages. **Skipped when `{is_greenfield}`** (`{skip_step_02}` set in step-01 §1c — nothing built to audit; tokens come from the policy).
3. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03-generate-brief.md` — write the brief to `{output_path}` with full Block A + Block B frontmatter.
3b. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03b-emit-rationale.md` — **conditional: only when `{has_analytics_band}` is `true`.** Write the analytics presentation rationale (`design-rationale-{target_slug}-{date}.md`) — the human-facing record of HOW the page-mode/band/archetype were chosen. Skipped entirely for no-band features.
3c. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03c-gate1-brief-ready.md` — **Gate 1 (brief-ready).** Runs the deterministic brief probes, spawns an isolated adversary reviewer bound to the brief body by SHA-256, auto-repairs only evidence-backed draft-only defects, re-checks, and emits `brief-adversary-{target_slug}-{date}.md`. **WARN-ONLY in Phase 1 for every instrument result**; the single exception is a genuine missing owner product/design decision, which PAUSES this brief before step-04. Skippable via `--no-gate1` or `gates.design-handoff-gate-1: skip`. Never run on a backlog brief.
4. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-04-deliver.md` — commit, push, PR, merge to `main`, surface the merged URL. Stages the rationale **and the Gate 1 adversary artifact** alongside the brief when they were written. Skippable via `--no-deliver`.
