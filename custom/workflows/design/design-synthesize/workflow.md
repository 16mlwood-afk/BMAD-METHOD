---
name: design-synthesize
description: 'Terminal-native replacement for Claude Design. Reads a design-handoff or design-brief markdown artifact, the project design policy, and frontend context, then synthesizes a code-shaped design bundle (HTML + tokens.css + screenshot + manifest) that design-implement can consume without changing its non-interpretive enforcement model. Use after design-handoff/design-artifact-loop has emitted a handoff artifact and before invoking design-implement.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_artifact_loop_workflow: '{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/workflow.md'
design_implement_workflow: '{project-root}/_bmad/bmm/workflows/implement/design-implement/workflow.md'
design_review_workflow: '{project-root}/_bmad/bmm/workflows/design/design-review/workflow.md'
---

# Design Synthesize Workflow

**Goal:** Sit between `design-handoff` (brief side) and `design-implement` (enforcement side). Take a markdown brief plus project design policy plus frontend context, and produce a code-shaped design bundle that `design-implement` can read property-by-property with no design judgment of its own.

**Your Role:** You are a terminal-native design synthesizer. You produce code, not prose. Every visual decision lands as an explicit value in `bundle/<screen>.html` or `bundle/tokens.css`. You do not summarize the design; you emit it. The bundle is the design — there is no parallel spec.

**Key Insight:** `design-implement` is intentionally non-interpretive. It reads CSS values from code, not from screenshots or summaries. If `design-synthesize` emits anything other than renderable code with explicit values, `design-implement` is forced to interpret — and interpretation is design judgment, which belongs in this workflow, not in `design-implement`. The bundle's whole purpose is to preserve that boundary.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow encounters conflicting guidance, the order of authority is:

1. **The referenced brief / handoff artifact on `main`** — `design-handoff-*.md`, `design-brief-*.md`, or `design-response-*.md` resolved from the invocation. This is the canonical input.
2. **Project design policy** — `{project-root}/docs/design-policy.md` (canonical) or `{planning_artifacts}/brand-identity.md` (legacy slot). Hard failures, contract-critical positive-assertion allowlist, status systems, palette, typography, layout principles.
3. **Canonical sister skills** — `design-policy-canonical` (page mode, palette, typography, layout, components), `operational-finance-ui` (work-surface-first layouts, dense finance table ergonomics), `operational-analytics-band` (analytics-row / trend-band structure). Invoked within their scope; their rules are not restated here.
4. **Shared BMAD design standards** — `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails.
5. **Project frontend conventions** — Tailwind config, existing token file, component patterns, framework version. Discovered from the repo. Determines real tokens vs invented values.
6. **Workflow defaults** — sensible defaults defined in this file (e.g., 1440px viewport for screenshots). Used only when none of the above specifies.

**Implication:** Every CSS value emitted by `design-synthesize` must trace back to (1), (2), or (5). Values from (3) or (4) appear only through the sister skills' published patterns. (6) is reserved for purely operational defaults that have no design meaning. Inventing a value with no trace is a synthesis failure — re-derive from the brief or surface the gap.

**Tokens are inventory, choices are authorized.** The Tailwind config and project token file at (5) are the **inventory** of valid values that the system contains — the ground truth for *what tokens exist*. The brief (1) and policy (2) are the authority for *which token to use* for any given decision. These are distinct questions, which is why (5) appears below (1) and (2) in this precedence: synthesis cannot use a token that doesn't exist (inventory check), but a token's existence does not authorize its use without a brief/policy justification (authority check). The `design-policy-canonical` skill ranks `tailwind.config.ts` as its #1 trust source for *what is in the system*; this workflow's precedence ranks the brief #1 for *what to do with the system* — the two are compatible, not in conflict.

**Policy non-overridability:** The brief (1) may narrow, focus, or summarize the policy (2) for a feature, but it MUST NOT loosen, carve out, or contradict the policy's hard failures or contract-critical positive-assertion allowlist. A brief that asks for behavior the policy forbids does not earn an exception — it surfaces a `modify-design-policy` candidate to the user. `design-synthesize` halts rather than honoring a brief that conflicts with policy. The brief's authority is over scope and emphasis, not over the policy's floors.

**Brief revision provenance** is governed by `{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md`. Step-01 validates the provenance frontmatter at intake (Gate 1) and halts on missing fields, broken invariants, forbidden combinations, or consumption of a superseded brief (without explicit `--allow-superseded` opt-in). The validated provenance flows into `manifest.synthesis.brief_provenance` via step-07 so every bundle is traceable to the exact brief revision it was synthesized from.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All 7 steps are FULLY AUTONOMOUS — no user interaction after invocation.
- State persists via variables (see below).
- Sequential progression: load brief → load policy → load frontend context → synthesize → render → self-critique → emit manifest.
- Step 6 (self-critique) is a bounded loop back to step 4 — max 3 iterations across all three sub-checks.

### State Variables

- `{brief_path}` — Absolute path to the input brief artifact (`design-handoff-*.md`, `design-brief-*.md`, or `design-response-*.md`).
- `{brief_type}` — `design-handoff` | `design-brief` | `design-response`. Parsed from filename prefix.
- `{brief_content}` — Full contents of the brief artifact.
- `{brief_frontmatter}` — Parsed YAML frontmatter from the brief (mode, target slug, route, etc.).
- `{mode}` — `fresh-design` | `refine-screen`. Inherited from the brief's mode field; refine-screen requires the brief to reference a `screen-review-*.md` artifact and to declare targeted vs unchanged regions. This is the **synthesis mode**, distinct from `{page_mode}` below.
- `{page_mode}` — `operational` | `analytical` | `detail`. The **page composition mode** from policy §6 / §7. Operational = table-first. Analytical = chart-first with drill-down. Detail = drawer or full-page extension of an operational list, never a re-skin. Hybrid pages default to `operational` per policy §6. Extracted from the brief's frontmatter (`page_mode:` field) or, if absent, inferred from the brief's data shape and design ask. Synthesis without a declared page mode is forbidden (Gate 1).
- `{policy_sections_cited}` — Ordered list of policy section identifiers (e.g., `§2`, `§3 Color hierarchy`, `§6 operational mode`) that drove the synthesis. Recorded in the manifest per the `design-policy-canonical` exemplar-disclosure rules (skill §"Exemplars" / policy §10).
- `{target_slug}` — Kebab-case slug for the feature/flow (e.g., `reclaim-avask`).
- `{target_route}` — Route the bundle represents (e.g., `/reclaim/avask`). May be a single route or a flow of routes for multi-screen bundles.
- `{routes}` — Ordered list of all routes the bundle represents (multi-screen). For single-screen runs this is `[{target_route}]`. Recorded in manifest under `routes:`.
- `{screens}` — Ordered list of screen names for multi-screen bundles. Single-screen runs have `len(screens) == 1`. Recorded in manifest under `screens:`.
- `{skills_invoked}` — Ordered list of skill names actually invoked during synthesis. Always includes `design-policy-canonical` and the resolved `{frontend_skill}`; conditionally includes `operational-finance-ui` and/or `operational-analytics-band` per the page-mode matrix in SKILL ROUTING. Recorded in manifest under `synthesis.skills_invoked` and checked by step 6's binary skill-routing check.
- `{policy_path}` — Resolved path to `docs/design-policy.md` or `{planning_artifacts}/brand-identity.md`.
- `{policy_content}` — Loaded policy contents.
- `{policy_version_hash}` — SHA of the policy file at synthesis time (recorded in the manifest for reproducibility).
- `{hard_failures}` — Extracted hard-failure list from the policy.
- `{positive_allowlist}` — Extracted contract-critical positive-assertion allowlist from the policy.
- `{framework}` — Detected frontend framework: `svelte` | `react` | `vue` | `none` (HTML-only).
- `{tailwind_config_path}` — Path to `tailwind.config.{js,ts}` if present, else null.
- `{project_tokens}` — Map of `var(--*)` → value resolved from the project's existing token file.
- `{components_emitted}` — Map of component name → region span within the emitted HTML.
- `{tokens_used}` — Map of `var(--*)` → source (`project` | `proposed`) used in the emitted HTML.
- `{tokens_proposed}` — Subset of `{tokens_used}` flagged `proposed`. Hard-capped at 5 (see Critical Rules).
- `{targeted_changes}` — In refine-screen mode, list of regions the bundle is intentionally changing. Lifted from the brief.
- `{unchanged_regions}` — In refine-screen mode, list of regions that must match the prior implementation byte-for-byte (modulo token substitution).
- `{prior_impl_paths}` — In refine-screen mode, absolute paths to the prior implementation's screen files (for the drift check).
- `{flow_invariants}` — Cross-screen invariants for multi-screen bundles (e.g., status-badge token consistency).
- `{bundle_dir}` — Absolute path to the output bundle directory (`{implementation_artifacts}/bundles/<target_slug>-<date>/`).
- `{iteration_count}` — Number of synthesis attempts so far in the self-critique loop (max 3).
- `{review_iterations}` — Number of visual-quality refine passes consumed by step 6 sub-checks (d)/(e)/(f). Distinct from `{iteration_count}` (which covers ALL critique loop returns including policy failures); `{review_iterations}` counts only the visual-quality / lift / exemplar-alignment loops. Recorded in manifest.
- `{compliance_state}` — `pass` | `under_grounded` | `hard_failed` | `positive_failed` | `drift_failed` | `lift_failed` | `exemplar_failed` | `dev_only`. Recorded in manifest after step 6. **`under_grounded`** = brief-faithful and policy-conformant on every checked axis, but at least one of: a mandated skill was not actually loaded (in `{skills_unloaded}`), at least one exemplar was path-only resolved (in `{exemplars_consulted_mode}`), or a high-confidence visual verdict was claimed without evidence. Always forces `needs_human_review: true` and `handoff_target: design-review`.
- `{visual_quality}` — `excellent` | `unverified-strong` | `acceptable` | `weak`. Synthesizer's own assessment after the last review pass — recorded in manifest. `weak` forces `needs_human_review: true`. **`unverified-strong`** is the honest downgrade from `excellent` when the rating was not backed by actual screenshot-vs-evidence comparison (per Critical Rules → "Synthesis honesty"); also forces `needs_human_review: true`.
- `{visual_lift_passed}` — Boolean. `true` only if the positive half of the lift test (Critical Rules) cleared. Recorded in manifest as `visual_lift_over_baseline`.
- `{exemplar_alignment}` — `aligned` | `unverified` | `deviated_with_brief_authorization` | `deviated_unauthorized`. Aggregated from per-screen exemplar comparisons in step 6 (f). Recorded in manifest under `visual_review.exemplar_alignment`. `deviated_unauthorized` at the final iteration sets `{compliance_state} = "exemplar_failed"`. **`unverified`** is the honest downgrade from `aligned` when at least one exemplar in `{exemplars_consulted_mode}` is `path_only` (per Critical Rules → "Exemplar alignment requires actual visual consultation"); forces `{compliance_state} = "under_grounded"` and `needs_human_review: true`.
- `{exemplars_consulted_mode}` — Map of `exemplar_path → "template_markup" | "rendered_screenshot" | "path_only"`. Populated in step 3 §9.4 per the consultation contract. Any `path_only` entry forces `{exemplar_alignment} = "unverified"` and `{compliance_state} = "under_grounded"`. Recorded in manifest under `exemplars.selected[].consulted_mode`.
- `{skills_unloaded}` — Ordered list of skills mandated by the routing matrix (workflow.md §SKILL ROUTING) that were NOT actually loaded via the Skill tool. Each entry: `{name, reason}` where `reason` is one of: `skill_tool_unavailable | skill_not_in_available_list | tool_call_failed | tool_call_skipped`. A non-empty list forces `{compliance_state} = "under_grounded"`. Recorded in manifest under `synthesis.skills_unloaded`.
- `{visual_quality_axes}` — Per-axis ratings + evidence from step 6 (d), all five axes mandatory: `{hierarchy, density, typography, table_ergonomics, generic_look}` → `{rating: strong | adequate | weak, evidence: <one-line string citing test-case IDs like T1/T2/...>}`. Recorded in manifest under `visual_review.visual_quality_axes`. Missing evidence string or unevidenced "strong" rating is a workflow bug. Audit trail for the manifest; not a gating signal on its own except for the anti-spreadsheet floor (Axis 5 T4 caps `visual_quality` at `acceptable`).
- `{macro_hierarchy}` — Per-screen above-the-fold judgment from step 6 (d). Map of `screen_path → {eye_lands_first: <element name>, above_fold_allocation: {band, table, controls, header, other}, evidence: <one-line>}`. `above_fold_allocation` percentages MUST sum to exactly 100. Unresolvable `eye_lands_first` forces Axis 1 (visual hierarchy) to `weak`. Recorded in manifest under `visual_review.macro_hierarchy`.
- `{negative_lift_violations}` — List of negative-half lift-test violations from step 6 (e) — placeholder data, generic SaaS chrome, CRM composition, wrong locale, page-mode mismatch. Each entry: `{screen, detector, detail, line}`. **Always emitted, including empty `[]`** — empty array is the affirmative no-violations claim. Recorded in manifest under `violations.lift.negative_half`.
- `{positive_lift_violations}` — List of positive-half lift-test violations from step 6 (e). Each entry: `{requirement, requirement_label, screen, detail, fix}` covering the 4 positive lift requirements (core question answered, key states surfaced, primary actions escalated, exemplar-aligned). **Always emitted, including empty `[]`.** Recorded in manifest under `violations.lift.positive_half`.
- `{exemplar_violations}` — List of exemplar-alignment deviations from step 6 (f). Each entry: `{screen, dimension, exemplar, diff, detail, fix}`. **Always emitted, including empty `[]`.** Recorded in manifest under `violations.exemplar`.
- `{exemplar_comparisons}` — Per-exemplar audit trail from step 6 (f). Map of `exemplar_path → {consulted: bool, consulted_at_step: int, diffs: {<screen_path>: {hierarchy, density, top_band, table_framing, state_presentation}}}` where each dimension carries `{aligned: bool, diff: <one-line string>}`. Every exemplar must end the run with `consulted: true` (a `consulted: false` entry is a routing failure — not iteration-counted — that loops step 4). Every diff string is mandatory, even on alignment ("matches: both X" is valid). Recorded in manifest under `exemplars.selected[].comparison.diffs` AND `exemplars.selected[].consulted` / `.consulted_at_step`.
- `{needs_human_review}` — Boolean. `true` whenever `{visual_quality} == "weak"`, `{visual_lift_passed} == false`, or `{exemplar_alignment} == "deviated_unauthorized"` at the final iteration. Recorded in manifest; downstream consumers (`design-implement`) refuse to auto-consume — they bounce-back to `design-review`.
- `{exemplars}` — Ordered list of 2–3 absolute paths to gold-standard operational screens loaded in step 3, used as anchoring references during synthesis (step 4) and exemplar-alignment check (step 6). Recorded in manifest under `exemplars:`.
- `{exemplars_rationale}` — Map of `path → rationale string` paired 1:1 with `{exemplars}`. Each rationale states why the exemplar was selected (page-mode match, surface-family match, policy conformance, recency). Recorded in manifest under `exemplars.selected[].rationale`.
- `{exemplar_gallery_path}` — Path to a project-maintained design gallery file (e.g., `docs/design-gallery.md`) if it exists; null otherwise. When present, `{exemplars}` are resolved from it; when absent, step 3 falls back to scanning the repo for high-confidence operational screens (see step 3 contract).
- `{frontend_skill}` — Name of the resolved project frontend skill (e.g., `website-building`, `frontend-design`, or a project-specific name). Resolution order is documented in SKILL ROUTING → "Always invoke". Unresolved = Gate 5a halt.
- `{frontend_skill_source}` — Which tier resolved `{frontend_skill}`: `brief` (brief frontmatter) | `config` (`_bmad/bmm/config.yaml`) | `fallback` (available-skills scan). Surfaced in step 3 §10 summary and in step 7 handoff line for audit; not recorded in the manifest as a separate field but inferable from the manifest's `skills_invoked` entry.
- `{baseline_commit}` — Git SHA before any changes.

### Step Processing Rules

1. **READ COMPLETELY** — read each step file before taking action.
2. **FOLLOW SEQUENCE** — execute numbered sections in order; step 6 is the only step allowed to loop back, and only to step 4.
3. **ALL STEPS ARE AUTONOMOUS** — never halt, never present menus, never wait for input. The only halt conditions are the four documented gates below.
4. **SAVE STATE** — carry variables between steps.
5. **LOAD NEXT** — when directed, read fully and follow the next step file.

### Critical Rules

- **The bundle is the design.** Do not produce a markdown summary alongside the bundle. The summary already exists upstream (the brief); the bundle is its code-shaped resolution.
- **Every visual value is explicit at parse time.** Visual values — color, spacing, type size/weight, sizing, radius, shadow, borders — must appear as inline `style="…"` attributes or `var(--*)` references resolved in `bundle/tokens.css`. **Config-dependent Tailwind utility classes are forbidden** — i.e., any class whose computed value comes from `tailwind.config.js` (e.g., `text-primary`, `rounded-lg`, `p-4`, `bg-status-warning`). Their values aren't extractable from the HTML alone, which forces `design-implement` to resolve through `tailwind.config.js`, which is interpretation. Structural / non-visual utility classes whose meaning is universal across projects (e.g., `flex`, `grid`, `hidden`, `sr-only`, `block`) are fine — they encode layout topology, not values.
- **All `var(--*)` resolve in `bundle/tokens.css`.** No dangling references. The bundle must be self-contained — `design-implement` reads only `bundle/<screen>.html` + `bundle/tokens.css` for visual facts.
- **Token proposal cap: 5 per bundle.** If synthesis would require >5 new tokens (not present in the project's existing token file), halt before emitting and surface a policy-extension decision to the user. Silently inventing tokens is the failure mode this cap exists to prevent.
- **Screenshot is human-only.** `bundle/screenshot-<screen>.png` is for visual review before handoff. `design-implement` never reads it. If Playwright is unavailable, halt with a clear "install playwright" diagnostic — do not silently skip the render step. (See Playwright Invocation Contract for the dev-only escape hatch.)
- **Manifest is split-authority.** Authoritative for synthesis receipt, interaction semantics, region declarations, and flow invariants. NEVER authoritative for visual properties. **Tie-breaker:** if `bundle/manifest.yaml` disagrees with `bundle/<screen>.html` or `bundle/tokens.css` on any visual fact, the HTML + tokens win — full stop — and the manifest is regenerated to match. No exceptions, no edge cases. A run where the manifest "looks more correct" than the HTML is a run where the synthesizer drifted; the HTML is what `design-implement` will enforce, so the HTML is the truth.
- **Drift in refine-screen is failure, not noise.** Any non-empty diff in an `unchanged_region` against the prior implementation is a synthesis bug. Either eliminate the drift or move the region into `targeted_changes` (which surfaces the intentional scope expansion).
- **Page mode declared up front.** Step 1 must resolve `{page_mode}` from the brief — `operational` | `analytical` | `detail` per policy §6 / §7. Per policy §6, hybrid pages default to `operational`. The page mode constrains composition (table-first vs chart-first vs detail extension), skill routing (operational → `operational-finance-ui`; analytical → `operational-analytics-band`), and what the lift test considers acceptable. Synthesis without an explicit `{page_mode}` is forbidden (Gate 1).
- **No design inference from existing screens.** The current implementation may pre-date the policy or be mid-migration; it is not a design source (per `design-policy-canonical` skill: "Do not infer design from existing screens"). In `fresh-design` mode, only the brief, the policy, and the project token inventory authorize design choices. In `refine-screen` mode the prior implementation is a **drift baseline** — a reference for what NOT to alter outside `targeted_changes` — not a design source.
- **IA vs visual trust — existing UI is not a visual baseline by default.** The "No design inference" rule above handles fresh-design's blanket case. This rule covers the common situation where a brief still references current implementation files for *behavioral* context (e.g., the brief's "Implementation Files" section, references to current pages by route, or — in `refine-screen` mode — `unchanged_regions`). Split what the brief is asking you to preserve into two classes:
  - **IA / behavior keepers** — routes, fields, data binding, dependencies, sequence of user actions, keyboard affordances. The existing implementation MAY serve as a behavioral reference for these.
  - **Visual keepers** — type scale, density, column composition, spacing, chip styling, table framing, filter pills, action button treatment. The existing rendering MUST NOT serve as a visual baseline by default. Re-derive every presentational decision from the brief's visual direction (precedence 1), the project policy (2), and `{exemplars}` (anchoring rule).

  A surface earns visual-baseline status only when its current rendering traces back to a documented `design-handoff → design-synthesize → design-implement` (or `design-review`-approved) chain. Surfaces shipped via `quick-dev`, `quick-spec`, or any path without a policy / frontend-skill gate are **low-design-provenance** — their behavior is trustworthy, their pixels are not. "It exists in the codebase" is not, by itself, design authority.

  `refine-screen` mode's byte-for-byte `unchanged_regions` contract is preserved — the user has explicitly declared those regions as visual keepers via the refine-screen mechanism. This rule applies most strongly in `fresh-design` / `redesign`-scope briefs where current implementation is cited for context only. Operationalized in step 4 (planning §3 "Provenance check during planning").
- **Lift test (policy §10) — two-sided contract.** Passing the policy is the floor, not the ceiling. The bundle must clear *both* a negative test (no generic SaaS look) AND a positive test (a clear lift over a baseline operational screen). Both halves must pass; either failure is a Gate 5 failure (see Approval Gates).
  - **Negative half (anti-AI / anti-generic).** If the synthesized bundle would render acceptably as a different SaaS product (a generic CRM, an HR dashboard, a marketing tool) without modification, it has failed the lift test. The bundle must read as a high-trust UK VAT finance operations tool — calm fintech, never marketing or playful SaaS (policy §1). Real domain content from the brief's data shape (invoices, VAT periods, suppliers, CDS records) is required — never placeholder/lorem ipsum data that could belong to any product.
  - **Positive half (lift over baseline).** The **baseline** is a minimally styled table with correct tokens and status chips but no operational narrative, no top summary, and flat hierarchy. To pass the positive half, the bundle MUST:
    1. **Answer the screen's core operational question at a glance** (e.g., for an `operational` import screen: "what's happening with my imports right now?") *before* the user has to scan the table — typically via a top band (`operational-analytics-band`) or a summary header.
    2. **Surface the screen's key states** above or beside the worklist (pending, failed, anomalies, overdue, awaiting-response) — not buried inside individual rows.
    3. **Visually distinguish primary actions and alerts from background noise** — primary action affordance is unambiguous; alert/error states are escalated above policy-baseline weight; routine rows recede.
    4. **Align with the loaded exemplars** in hierarchy, density, framing, and how tables are introduced (see exemplar-alignment rule below).

    A bundle that satisfies the negative half but does not visibly lift over the baseline is a Gate 5 failure with `visual_lift_passed: false`. Bundles that fail the positive half are NOT auto-handed-off to `design-implement`; they ship with `needs_human_review: true` and the user is prompted to either accept the run as-is or re-brief.

- **Exemplar alignment (anchoring rule) — requires actual visual consultation, not just path selection.** Synthesis must anchor in 2–3 *gold-standard* operational screens loaded in step 3 as `{exemplars}` rather than free-styling. The exemplars are the project's own best work — read from the repo (or a project-maintained design gallery file) — and answer the question "what does a strong version of this kind of screen look like in *this* product?". Synthesis must keep page-level hierarchy, density, top-band summary patterns, table framing, and state-presentation consistent with the exemplars unless the brief explicitly authorizes a departure. Departure without brief authorization is a synthesis failure surfaced in step 6.

  **What counts as consultation.** For each exemplar, step 3 §9.4 must do ONE of:
  - **(a) Read the `<template>` markup section in full** — not just the `<script>` block. Visual decisions live in the markup; the `<script>` block alone tells you which components are imported, not how they're laid out.
  - **(b) Render the live exemplar via Playwright** at the bundle's primary viewport and save the screenshot as `bundle/exemplar-<name>.png`. Reference these during synthesis and during step 6 (f).
  - **(c) Path-only fallback** — file exists, recorded in `{exemplars}`, no markup or screenshot consulted. This is a **Gate 5b half-failure**: the bundle proceeds but `{exemplar_alignment}` caps at `unverified`, `{compliance_state}` becomes `under_grounded`, and `{needs_human_review} = true`.

  Per-exemplar consultation mode is recorded in `{exemplars_consulted_mode}` (map: path → `template_markup` | `rendered_screenshot` | `path_only`). Step 6 (f) checks this map before allowing an `aligned` verdict.

- **Synthesis honesty — claims require evidence.** Three honesty rules apply to the manifest's verdict fields:

  - **`skills_invoked` records actual Skill tool calls, not theoretically applicable skills.** An entry in `manifest.skills_invoked` requires that the Skill tool was invoked with that skill name during this run AND its content was loaded into context. Operating "in the spirit of" a skill — applying the workflow's summary of its rules without loading the skill itself — is NOT invocation. Skills mandated by the routing matrix but not actually loaded are recorded in `{skills_unloaded}` with a reason; the bundle's `compliance_state` becomes `under_grounded`.

  - **High-confidence visual verdicts require visual evidence.** `{visual_quality} = "excellent"`, `{visual_lift_over_baseline} = true`, and `{exemplar_alignment} = "aligned"` may only be asserted when the synthesizer has compared the bundle's rendered screenshot against (i) the exemplars' actual markup or screenshots, AND (ii) the conceptual minimally-styled baseline. Without that comparison, verdicts downgrade automatically:
    - `excellent` → `unverified-strong`
    - `aligned` → `unverified`
    - `visual_lift_over_baseline: true` → `null` (record absence, not a positive claim)

    The bundle still ships, but with `compliance_state: under_grounded` and `needs_human_review: true`.

  - **`under_grounded` is the honest label for brief-faithful, policy-conformant, visually unverified bundles.** A bundle that violates no policy rule, contains no lift-test red flag, and follows the brief's design ask — but was synthesized without actual exemplar consultation, without actual skill loading, or without comparing against rendered evidence — is NOT `pass`. It is `under_grounded`. `design-implement` refuses `under_grounded` bundles for the same reason it refuses `dev_no_render` ones: the verdict is unfalsifiable.

- **YOU MUST ALWAYS SPEAK OUTPUT** in your agent communication style with the config `{communication_language}`.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `planning_artifacts` and `implementation_artifacts` paths
- `date` as system-generated current datetime

### Paths

- `{installed_path}` = `{project-root}/_bmad/bmm/workflows/design/design-synthesize`
- `{output_dir}` = `{implementation_artifacts}/bundles` — all bundle directories are written here, one per `<target_slug>-<date>` run.
- `{policy_canonical}` = `{project-root}/docs/design-policy.md`
- `{policy_legacy}` = `{planning_artifacts}/brand-identity.md`

### Policy Loading

Check both possible locations, in order. Prefer the canonical path:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

Store the resolved path as `{policy_path}` and contents as `{policy_content}`. Compute `{policy_version_hash}` (SHA-256 of the file) and record it in the manifest.

**If neither path returns a file but the project is expected to have one, halt and report the paths tried.** Synthesis without a design policy is unsafe — the workflow has no source for hard failures or the positive-assertion allowlist.

### Input

The user invokes this workflow with one of:

- **A brief path** — `_bmad/bmm/implementation-artifacts/design-handoff-{slug}-{date}.md` (most common entry point, fed by `design-artifact-loop`).
- **A brief slug** — `design-handoff` resolves to the most recent matching artifact in `{implementation_artifacts}`.
- **A handoff block** — same canonical handoff shape as `design-artifact-loop` accepts. The block names a file on `main` which is then read locally.

If the input is ambiguous, the workflow does NOT generate its own brief — it halts and asks for a brief reference (the upstream workflow's job is to produce briefs, not this workflow's).

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- Never halt for user input. The only legitimate halts are the five gates below.
- When the brief is missing or malformed → halt (Gate 1).
- When the policy is missing → halt (Gate 2).
- When >5 tokens would be proposed → halt (Gate 3).
- When Playwright is unavailable → halt (Gate 4).
- When the project frontend skill cannot be resolved OR exemplars cannot be loaded → halt (Gate 5a / 5b). Note: Gate 5c (visual-lift failure) is the one non-halting gate — it emits the bundle with `needs_human_review: true` and blocks auto-handoff to `design-implement`, but does not halt the run.

These five gates are the only autonomous-mode exits. Everything else proceeds.

---

## INPUTS AND OUTPUTS

### Inputs

| Input | Source | Required? | Purpose |
|---|---|---|---|
| Brief artifact | `{implementation_artifacts}/design-handoff-*.md` (or `design-brief-*` / `design-response-*`) | Required | Feature purpose, data shape, user context, visual direction, hard constraints, design ask. Source-of-truth (1). |
| Project design policy | `{policy_path}` | Required | Hard failures, positive-assertion allowlist, palette, typography, layout principles. Source-of-truth (2). |
| Sister skills | `design-policy-canonical`, `operational-finance-ui`, `operational-analytics-band`, project frontend skill | Conditional (see Skill Routing) | Component vocabulary, layout grammar, anti-AI-slop guardrails. Source-of-truth (3). |
| Frontend context | `package.json`, `tailwind.config.{js,ts}`, project token file, existing component patterns | Required | Framework detection, real-tokens-vs-invented diff. Source-of-truth (5). |
| Prior implementation | Project source files for the target route(s) | Required in `refine-screen` only | Drift baseline for step 6c. |

### Outputs

Written to `{output_dir}/<target_slug>-<date>/`:

| File | Authority | Consumer |
|---|---|---|
| `bundle/<screen>.html` | Canonical visual source of truth | `design-implement` value-extraction; human review via screenshot |
| `bundle/tokens.css` | Defines every `var(--*)` used in the HTML | `design-implement` token resolution; framework scaffolds |
| `bundle/<screen>.<framework-ext>` (optional) | Convenience scaffold for implementer | Implementer starting point — NOT authoritative |
| `bundle/screenshot-<screen>.png` | Human visual review only | User; never `design-implement` |
| `bundle/manifest.yaml` | Split authority — see Manifest Schema below | `design-implement` cross-reference; user audit |

---

## STEP LIST

Each step is authored as a separate file under `steps/`. This workflow.md defines the contract; step files are authored after the workflow is stable.

1. **`step-01-load-brief.md`** — Resolve the brief artifact, parse YAML frontmatter, extract feature purpose / data shape / user context / visual direction / hard constraints / design ask / synthesis mode / **page mode (`operational | analytical | detail`, policy §6 / §7; hybrid defaults to `operational`)** / target slug / screens list / (refine-screen only) targeted vs unchanged regions. **Halts** if the brief is missing or malformed, or if `{page_mode}` cannot be resolved (Gate 1).
2. **`step-02-load-policy.md`** — Resolve and load `{policy_path}`, compute `{policy_version_hash}`, extract `{hard_failures}` and `{positive_allowlist}`. **Halts** if the policy is missing (Gate 2).
3. **`step-03-load-frontend-context.md`** — Detect `{framework}` from `package.json`, locate and parse `{tailwind_config_path}` and the project token file, populate `{project_tokens}`. In refine-screen mode, also locate `{prior_impl_paths}` for the drift baseline. **Also load `{exemplars}`**: 2–3 gold-standard operational screens for this `{page_mode}`. Resolution order: (i) read from `{exemplar_gallery_path}` (`docs/design-gallery.md` or project equivalent) if it exists and declares exemplars for this page mode; (ii) otherwise scan the repo for the highest-confidence operational screens matching the brief's data shape (e.g., the most recently shipped or most-policy-conformant screens in the same surface family) and select up to 3. Record selection rationale in `{exemplars_rationale}` for the manifest. **Halts** if no exemplars can be resolved AND the brief does not explicitly waive exemplar anchoring — this is part of Gate 5.
4. **`step-04-synthesize.md`** — Invoke the relevant sister skills (per Skill Routing below) and generate `bundle/<screen>.html` + `bundle/tokens.css` for each screen in `{screens}`. Every visual property is an explicit value. Synthesis must consult `{exemplars}` to anchor hierarchy, density, top-band patterns, table framing, and state presentation; deviation from exemplars is allowed only when the brief explicitly authorizes it. **Halts** if synthesis would introduce >5 new tokens (Gate 3).
5. **`step-05-render-screenshot.md`** — Run Playwright (headless Chromium) against each `bundle/<screen>.html` at the brief's primary viewport. Save `bundle/screenshot-<screen>.png`. **Halts** if Playwright is unavailable (Gate 4).
6. **`step-06-self-critique.md`** — Run policy-compliance sub-checks AND visual-quality sub-checks. The policy half (a/b/c) is the original critique loop. The visual half (d/e/f) is the *crit/refine* loop the workflow uses to lift bundles above baseline; passing policy is necessary but not sufficient.

   **Policy half (compliance):**
   - **(a) Hard-failure check** against `{hard_failures}` from the policy.
   - **(b) Policy-derived positive-assertion check** against `{positive_allowlist}` from the policy — items the policy itself ratifies as contract-critical (e.g., "status indicators use status tokens not raw colors", "components have stable identifiers"). `design-synthesize` does NOT invent allowlist items.
   - **(c) Drift check** (refine-screen only) — diff bundle against prior implementation; non-empty diff in any `unchanged_region` is a failure.

   **Visual half (lift & taste):**
   - **(d) Visual-quality review.** The synthesizer reviews its own screenshots and HTML for: visual hierarchy (titles, sections, table framing), whitespace and density, typography use (avoid uniformly small text; avoid all-bold or all-thin), table ergonomics (scan-ability, row states), and "AI/generic" template look (flat, spreadsheet-y, no operational story). Rate `{visual_quality}` as `excellent | acceptable | weak`. `excellent` proceeds; `acceptable` triggers one refine pass to strengthen hierarchy, density, and operational framing; `weak` proceeds to step 7 but sets `needs_human_review: true` and blocks auto-handoff.
   - **(e) Lift-over-baseline check** (Critical Rules → "Lift test"). Both halves of the lift test must pass — the negative half (no generic SaaS look, real domain content) AND the positive half (answers core operational question at a glance; key states surfaced above the worklist; primary actions and alerts visually escalated; aligned with exemplars). Positive-half failure sets `{visual_lift_passed} = false` and is a Gate 5 failure.
   - **(f) Exemplar-alignment check.** Compare the bundle's hierarchy, density, top-band patterns, and table framing against `{exemplars}`. Deviation is only acceptable when the brief explicitly authorizes it. Unauthorized deviation is a failure with mode `exemplar_failed`.

   **Loop policy:** On failure of any sub-check, return to step 4 with a targeted correction note. Max 3 iterations across all sub-checks combined. `{review_iterations}` tracks how many of those iterations were driven by visual sub-checks (d/e/f) specifically. On the 3rd failure: policy failures (a/b/c) set `{compliance_state}` to the corresponding failure mode; visual failures (d/e/f) set `{compliance_state}` to `lift_failed` or `exemplar_failed` AND `{needs_human_review} = true`. Either way, proceed to step 7.

   Note: workflow invariants (every `var(--*)` resolves, no config-dependent Tailwind, manifest visual-disagreement-tiebreaker, bundle self-containment) are NOT in this self-critique pass — they are unconditional and run in step 7's manifest-validation gate. The allowlist is reserved for policy-derived assertions only.
7. **`step-07-emit-manifest.md`** — Run the **unconditional manifest-validation pass** first: every `var(--*)` in any `<screen>.html` resolves in `tokens.css`; no config-dependent Tailwind classes appear; no values in `manifest.yaml` disagree with HTML + tokens; bundle is self-contained (no external imports beyond `tokens.css`). A failure here is a workflow bug — halt and report; do NOT emit a bundle that violates workflow invariants. If validation passes, write `bundle/manifest.yaml` per the Manifest Schema below — including `visual_review:` (visual_quality, visual_lift_over_baseline, review_iterations, needs_human_review) and `exemplars:`. Print bundle path, screen list, compliance state, `visual_quality`, `needs_human_review`, and the next-agent hand-off line. When `needs_human_review: true`, the hand-off line MUST direct the user to human design review (`design-review` or `bmad:bmm:workflows:design-review`) BEFORE `design-implement`, not directly to implementation.

---

## SKILL ROUTING

`design-synthesize` MUST invoke the relevant frontend/design skills BEFORE generating output in step 4. Skill invocation is logged in the manifest under `skills_invoked:` for audit. Improvising visual decisions from workflow prose alone is the failure mode this section exists to prevent.

### Role of each skill — non-overlapping responsibilities

Synthesis depends on three distinct sources of authority. Each owns a different slice of the visual decision; collapsing them into one (e.g., letting the domain skill make taste calls, or letting policy substitute for layout craft) is the failure mode that produces policy-compliant-but-bland output. Spell out the division explicitly:

| Skill | Owns | Does NOT own |
|---|---|---|
| `design-policy-canonical` | Palette rules, status vocab, component allowlist, anti-patterns, hard failures, positive-assertion contracts. The *floor* — what is forbidden and what is contract-critical. | Hierarchy, rhythm, where things go on a page, how dense a table should feel. Policy says what NOT to look like; it does not say what good looks like. |
| `operational-finance-ui` (or project domain skill) | Domain-specific layout patterns for financial tables, reconciliations, imports, observability surfaces. Where KPIs go relative to tables, how filings/registrations/reconciliations are framed, what an "operational story" looks like for finance ops. | Aesthetic restraint, typographic rhythm, micro-spacing, generic taste decisions outside the finance domain. |
| Project frontend skill (`{frontend_skill}` — e.g., `website-building`, `frontend-design`, or project-specific) | **Taste.** Hierarchy, spacing, rhythm, typography pairings, density calibration, aesthetic restraint. The "is this beautiful and easy to use" layer that turns policy + domain into a designed screen rather than a wireframe. | Domain semantics, policy interpretation. Frontend skill does not invent finance patterns or override hard failures. |

For `page_mode: operational`, **all three categories are required** — policy + domain + frontend. Synthesis that consults only policy + domain produces wireframes; synthesis that consults only frontend produces a pretty CRM. The combination is the contract.

### Routing rules

Skill routing is driven by **`{page_mode}`**, not by free-text screen-type inference. This makes routing deterministic and aligns with policy §6 — the page mode constrains every downstream design decision, including which sister skills are authoritative for this screen.

**Always invoke in every run (both synthesis modes, all page modes):**
- `design-policy-canonical` — the policy itself is the floor; the skill enforces the trust hierarchy and refuses anti-default compositions.
- **Project frontend / webapp design skill (`{frontend_skill}` — MANDATORY).** Synthesis emits HTML and tokens; layout, hierarchy, typography, and visual patterns must be chosen by a skill with frontend/design competence — not by policy or domain skills alone. **Absence of a project frontend skill is a Gate 5 failure** (see Approval Gates). Resolution order: (i) the `frontend_skill:` field in the brief's frontmatter; (ii) a `frontend_skill:` entry in the project's `_bmad/bmm/config.yaml`; (iii) the first skill in the available skills list whose name contains `frontend`, `website-building`, or `webapp`. If none of those resolve, halt with the diagnostic in Gate 5.

**Drive by `{page_mode}`:**

| `{page_mode}` | Mandatory in addition to always-invoke | Conditional |
|---|---|---|
| `operational` | `operational-finance-ui` (table-first composition, filter bar, status hierarchy, dense row treatment per policy §6) | `operational-analytics-band` if the screen carries a narrow analytics band above or beside the table |
| `analytical` | `operational-analytics-band` (chart-led composition, drill-down evidence, no card-grid openers per policy §6) | `operational-finance-ui` if drill-down tables are part of the brief |
| `detail` | `operational-finance-ui` (drawer/detail extends an operational list — same surface, typography, badges; policy §7) | `operational-analytics-band` is **not** applicable; detail views forbid KPI cards / charts per policy §7 |

**Refine-screen mode** uses the same page-mode-driven matrix above. Synthesis mode (`fresh-design` vs `refine-screen`) does not change which skills are authoritative — page mode does.

### Enforcement

A run that emits a bundle with `manifest.skills_invoked` missing any of the required entries (always-invoke + page-mode-mandatory) is a failed routing pass. Step 6 must rewind to step 4 to load the missing skills before continuing. Skills are loaded once per run (cache on the first invocation); subsequent step-04 iterations within the self-critique loop reuse the cached skill context. The frontend-skill requirement is hard: a run that cannot resolve a frontend skill halts at Gate 5 rather than proceeding with a "policy-compliant wireframe."

---

## PLAYWRIGHT INVOCATION CONTRACT

Step 5 shells out to Playwright for screenshot rendering. The contract:

- **Binary:** `npx playwright` (project-local installation preferred; global fallback acceptable).
- **Browser:** headless Chromium. Firefox/WebKit are NOT used — `design-implement` does not care about browser rendering differences, and using one browser keeps screenshots deterministic across runs.
- **Viewport:** read from the brief's `responsive:` field if present; default `1440 x 900` (matches the project's primary desktop target).
- **DPR:** `2` (so screenshots are crisp on Retina displays).
- **Asset loading:** `bundle/tokens.css` is loaded via `<link>` in the synthesized HTML. No external network fetches — bundles must render offline.
- **Wait condition:** `domcontentloaded` plus a 200ms settle (no animations to wait for, since interaction semantics are not exercised at synthesis time).
- **Failure modes:**
  - Playwright not installed → halt with `install playwright` diagnostic (Gate 4).
  - HTML fails to parse → synthesis failure, return to step 4 with the parse error as correction note.
  - Render produces an empty viewport (white screen) → synthesis failure, return to step 4 with the empty-render note.
- **Output:** `bundle/screenshot-<screen>.png` written next to the corresponding HTML file. Multi-screen bundles produce one screenshot per screen.

The exact Playwright invocation is a step-file implementation detail; the contract above is what the workflow guarantees.

### Dev-only escape hatch: `--no-render`

For development of `design-synthesize` itself (or for environments where installing Chromium is genuinely blocked and the user is iterating on synthesis logic rather than producing a real bundle), the workflow accepts a `--no-render` flag that skips step 5.

**Strict rules — non-negotiable:**

- **Bundles emitted with `--no-render` are not production bundles.** `manifest.yaml` MUST set `synthesis.dev_no_render: true` and `synthesis.compliance_state: dev_only`.
- **`design-implement` MUST refuse to consume bundles with `dev_no_render: true`** and exit with: "this bundle was emitted in dev-only mode (no screenshot). Re-run `design-synthesize` without `--no-render` before invoking `design-implement`." This refusal is one of the bounded changes that lands in `design-implement` alongside this workflow.
- **The flag does not bypass Gate 4 silently.** It explicitly overrides Gate 4 and records the override in the manifest. Bypass without recording is a synthesis bug.
- **Use cases:** authoring this workflow's step files; debugging synthesis logic in CI environments without Chromium; smoke-testing manifest schema changes. Never accepted ramps in a real implementation handoff.

This preserves the strict production contract (no production bundle without a screenshot) while keeping the workflow developable.

---

## APPROVAL GATES

The workflow must pass these gates in order. Each is a hard halt. Step ownership in parentheses.

### Gate 1 — brief validity (step 1)
- Brief path resolves to an existing file under `{implementation_artifacts}`.
- Brief contains valid YAML frontmatter with at least: `target_slug`, `mode` (synthesis mode), `route` (or `routes` for multi-screen).
- `{page_mode}` resolves to one of `operational | analytical | detail` — either declared in the brief frontmatter as `page_mode:` or unambiguously inferrable from the brief's data shape and design ask. If the brief describes both table-first work and analytics surfaces without a tiebreaker, default to `operational` per policy §6.
- In `refine-screen` mode: brief references a `screen-review-*.md` and declares `targeted_changes` + `unchanged_regions`.

If this gate fails, halt and report the missing field(s). Do NOT guess paths, substitute a stale brief, or invent a page mode.

### Gate 2 — policy presence (step 2)
- `{policy_path}` resolves to an existing file.
- Policy contains a hard-failure section.
- Policy contains a contract-critical positive-assertion allowlist (or the absence is explicit — `positive_allowlist: []` is acceptable but must be intentional, not missing). Allowlist items must be policy-ratified positive assertions (e.g., "status indicators use status tokens"), not workflow invariants (which are unconditional and checked in step 7, not via the allowlist).

If this gate fails, halt and report the policy path tried and what was missing.

### Gate 3 — token cap (step 4)
- Count of tokens emitted that are NOT present in the project's existing token file is ≤ 5.

If this gate fails, halt and surface: "this bundle would introduce N>5 new tokens — extend `docs/design-policy.md` first or revise the brief to use existing tokens". List the proposed tokens with their brief-section source.

### Gate 4 — Playwright availability (step 5)
- `npx playwright --version` returns successfully (or a project-equivalent local install does).

If this gate fails, halt with: "Playwright not available. Run `pnpm add -D @playwright/test && npx playwright install chromium` then re-invoke." Do NOT silently skip the screenshot step.

### Gate 5 — visual lift + frontend skill + exemplars (steps 3 and 6)

This gate has three components — all three must clear for the bundle to be auto-handed off to `design-implement`. A failure does not abort the run (the bundle is still emitted for human inspection), but it blocks the auto-handoff line and forces `needs_human_review: true` in the manifest.

- **5a — Frontend skill resolved (step 3).** Per SKILL ROUTING → "Always invoke", a project frontend skill must be resolvable via the three-tier order (brief frontmatter → project config → available-skills fallback). If none resolves, halt with: `"No project frontend skill resolved. Synthesis requires a frontend/design skill in addition to policy + domain skills. Declare frontend_skill: <name> in the brief frontmatter or in {project-root}/_bmad/bmm/config.yaml, then re-invoke."` This is a hard halt — synthesis does not proceed.
- **5b — Exemplars loaded AND consulted (step 3).** `{exemplars}` must contain 2–3 paths from either `{exemplar_gallery_path}` or the repo-scan fallback. If neither yields exemplars AND the brief does not include `exemplar_anchoring: waived` in its frontmatter, halt with: `"No exemplars resolved for page_mode={page_mode}. Either populate {project-root}/docs/design-gallery.md with 2–3 gold-standard screens for this page mode, or set exemplar_anchoring: waived in the brief's frontmatter (only acceptable for greenfield projects with no shipped exemplars)."` **Path-only resolution is a half-failure (not a halt):** if `{exemplars}` is non-empty but at least one entry has `{exemplars_consulted_mode}[path] == "path_only"` (per Critical Rules → "Exemplar alignment requires actual visual consultation" and step 3 §9.4), the bundle proceeds but `{exemplar_alignment}` caps at `unverified`, `{compliance_state}` becomes `under_grounded`, and `{needs_human_review} = true`. The handoff line directs to `design-review`, not `design-implement`.
- **5c — Visual lift (step 6).** The two-sided lift test (negative + positive halves per Critical Rules) must pass. Negative-half failure is treated as a hard-failure rule entry (existing behavior). Positive-half failure sets `{visual_lift_passed} = false` and, on the final iteration, sets `{compliance_state} = lift_failed` and `{needs_human_review} = true`. The bundle is emitted with the failure mode recorded; the manifest's hand-off line directs the user to human design review BEFORE `design-implement`, not directly to implementation.

---

## MANIFEST SCHEMA (`bundle/manifest.yaml`)

The manifest is split-authority: authoritative for synthesis receipt + interaction semantics + region declarations + flow invariants; never authoritative for visual properties.

```yaml
# Synthesis receipt — authoritative
synthesis:
  workflow: design-synthesize
  version: 1
  date: {iso8601}
  brief_path: {repo-relative path}
  brief_type: {design-handoff | design-brief | design-response}
  policy_path: {repo-relative path}
  policy_version_hash: {sha256}
  baseline_commit: {git sha}
  frontmatter_lifts:                              # map of required brief frontmatter fields lifted from brief body by step 1 (§5b / §8a). Always emitted — `{}` when zero lifts occurred (explicit, not omitted). Each entry records value + source for audit.
    {field}:
      value: {lifted value}
      source: {body location, e.g., "filename" | "body §1: 'Route: /expenses'" | "body §6: V1, V2, V3 blocks"}
  iterations: {integer}
  compliance_state: {pass | under_grounded | hard_failed | positive_failed | drift_failed | lift_failed | exemplar_failed | dev_only}
  dev_no_render: {false | true}  # true ONLY when --no-render was used; design-implement refuses these bundles
  skills_invoked:                 # ACTUAL Skill tool invocations during this run (Critical Rules → "Synthesis honesty").
    - design-policy-canonical     # ONLY list a skill here if the Skill tool was called with that name AND its content loaded.
    - {project-frontend-skill}    # Operating "in the spirit of" a skill without loading it does NOT qualify — record in skills_unloaded.
    - operational-finance-ui      # MANDATORY (page_mode-dependent); if not actually loaded, list in skills_unloaded instead.
    - operational-analytics-band  # MANDATORY (page_mode-dependent); same rule.
  skills_unloaded:                # Skills mandated by routing matrix but NOT actually loaded — forces compliance_state: under_grounded.
    - name: {skill-name}
      reason: {skill_tool_unavailable | skill_not_in_available_list | tool_call_failed | tool_call_skipped}

# Mode and scope — authoritative
mode: {fresh-design | refine-screen}            # synthesis mode
page_mode: {operational | analytical | detail}  # policy §6 / §7 composition mode
target_slug: {kebab-case slug}
target_route: {single route or null}
routes: [{list of routes for multi-screen flows}]
screens: [{ordered list of screen names}]

# Visual review — authoritative for the visual-quality + lift outcome of step 6 (d/e/f)
# Used by design-implement to decide auto-consume vs route to human review.
# MANDATORY: visual_quality_axes (per-axis rating + evidence) and macro_hierarchy
# (per-screen above-the-fold judgment) are always emitted. Omission = workflow bug.
visual_review:
  visual_quality: {excellent | unverified-strong | acceptable | weak}    # synthesizer's self-rating after step 6 (d). unverified-strong = honest downgrade from excellent when no evidence comparison was performed (per Critical Rules → "Synthesis honesty").
  evidence_basis:                                     # WHAT the visual verdicts above are actually backed by — Critical Rules → "Synthesis honesty"
    exemplar_comparison: {markup | screenshot | none}  # how the synthesizer consulted exemplars during step 6 (f)
    baseline_comparison: {explicit | implicit | none}  # did the synthesizer compare against a baseline operational screen in step 6 (e)?
    own_screenshot_reviewed: {true | false}            # did the synthesizer Read the bundle/screenshot-<screen>.png during step 6 (d)?
  visual_quality_axes:                                # per-axis rating + evidence string, all 5 axes mandatory
    hierarchy:        { rating: {strong | adequate | weak}, evidence: "passes T1 (...), T2 (...)" }
    density:          { rating: {strong | adequate | weak}, evidence: "..." }
    typography:       { rating: {strong | adequate | weak}, evidence: "..." }
    table_ergonomics: { rating: {strong | adequate | weak}, evidence: "..." }
    generic_look:     { rating: {strong | adequate | weak}, evidence: "passes T1, T2, T3, T4 (anti-spreadsheet: ...)" }
  macro_hierarchy:                                    # per-screen above-the-fold judgment, mandatory
    {screen_path}:
      eye_lands_first: {summary band | filter strip | table header | primary heading | chart | detail header | drawer}
      above_fold_allocation: { band: 35, table: 45, controls: 12, header: 8, other: 0 }   # MUST sum to 100
      evidence: "screenshot top 900px: summary band 35%, filter strip 12%, table 45%, page header 8%"
  visual_lift_over_baseline: {true | false | null}    # positive half of the lift test (step 6 (e), Gate 5c). null = no evidence comparison performed; do NOT assert true without comparison.
  exemplar_alignment: {aligned | unverified | deviated_with_brief_authorization | deviated_unauthorized}    # unverified = at least one exemplar in exemplars_consulted_mode is path_only (forces compliance_state: under_grounded).
  review_iterations: {integer}                        # how many of the step-6 loop iterations were driven by visual sub-checks (d/e/f)
  needs_human_review: {true | false}                  # true whenever visual_quality ∈ {weak, unverified-strong}, visual_lift_over_baseline ∈ {false, null}, exemplar_alignment ∈ {deviated_unauthorized, unverified}, OR compliance_state == under_grounded
  handoff_target: {design-implement | design-review}  # design-review when needs_human_review == true OR compliance_state == under_grounded

# Exemplars — the 2–3 gold-standard screens used as anchors during synthesis (loaded in step 3)
# MANDATORY: every selected entry must have consulted: true and a comparison.diffs block
# covering all 5 dimensions per screen. consulted: false would have routed step 4 — it
# cannot appear in an emitted manifest.
exemplars:
  gallery_path: {path to docs/design-gallery.md if used, else null}
  selected:
    - path: {repo-relative path to exemplar 1}
      rationale: "{why this exemplar — page-mode match, surface-family match, policy conformance, recency}"
      consulted_mode: {template_markup | rendered_screenshot | path_only}    # REQUIRED — Critical Rules → "Exemplar alignment requires actual visual consultation". path_only forces compliance_state: under_grounded.
      consulted_artifact: {path to rendered screenshot OR "src lines N-M of file"} # the artifact the synthesizer actually consulted; null when consulted_mode == path_only
      consulted: true                                  # MUST be true; consulted: false would have looped step 4
      consulted_at_step: {iteration count when the file was Read}
      comparison:
        diffs:
          {screen_path}:
            hierarchy:          { aligned: true,  diff: "matches: both open with state-grouped filter strip above table" }
            density:            { aligned: true,  diff: "matches: 28px rows + 24px section gap" }
            top_band:           { aligned: false, diff: "differs: exemplar uses summary band with sparkline; screen omits sparkline" }
            table_framing:      { aligned: true,  diff: "matches: section heading + summary line above table" }
            state_presentation: { aligned: true,  diff: "matches: status pills + escalated alert rows" }
          # ... one entry per screen in {screens}
    - path: {repo-relative path to exemplar 2}
      rationale: "..."
      consulted: true
      consulted_at_step: {int}
      comparison:
        diffs: { ... }
  # When exemplar_anchoring is waived in the brief, this section is:
  #   gallery_path: null
  #   selected: []
  #   waiver_reason: "{the brief's stated reason for waiving exemplar anchoring}"

# Violations — UNCONDITIONAL section. All six arrays are always present, even [].
# Empty array is the affirmative "no violations" claim; omission is forbidden and
# treated as a workflow bug. design-implement reads violations.* for context even on pass.
violations:
  hard_failures: []                                   # or [{rule, source_line, file, line, snippet}, ...]
  positive_assertions: []                             # or [{assertion, source_line, file, line, snippet}, ...]
  drift: []                                           # or [{region, file, lines, prior_file, prior_lines, diff}, ...]
  visual_quality:
    rating: {visual_quality}
    weak_axes: []                                     # or [{axis, screens, correction_note}, ...]
    anti_spreadsheet:
      t4_failed: {true | false}                       # true caps visual_quality at acceptable
      failed_screens: []                              # screens that failed Axis 5 T4
      detail: "n/a"                                   # or one-line when t4_failed: true
  lift:
    negative_half: []                                 # or [{screen, detector, detail, line}, ...]
    positive_half: []                                 # or [{requirement, requirement_label, screen, detail, fix}, ...]
  exemplar: []                                        # or [{screen, dimension, exemplar, diff, detail, fix}, ...]

# Policy sections that drove the synthesis — exemplar-disclosure rule
# (design-policy-canonical skill §"Exemplars" / policy §10)
policy_sections_cited:
  - "§1 Visual Direction"
  - "§2 Layout Principles"
  - "§3 Color hierarchy"
  - "§6 Operational mode (table-first)"
  - "§5 Anti-default compositions"
  # ... each section that justified a composition or component decision

# Refine-screen scope — authoritative when mode == refine-screen
targeted_changes:
  - region: {name}
    rationale: {one line tied to a screen-review V-number or brief section}
unchanged_regions:
  - region: {name}

# Tokens used — authoritative for source attribution; NOT authoritative for values
tokens:
  used:
    - name: --status-warning
      source: project
    - name: --row-height-compact
      source: project
  proposed:
    - name: --accent-warm
      source: proposed
      justification: "Brief §4 'visual direction': warm accent for opportunity badges"
      # Hard cap: tokens.proposed length ≤ 5.

# Components emitted — receipt only; layout/styling lives in HTML
components_emitted:
  - name: WorkSurface
    screen: list
    region_span: {selector or anchor}
  - name: StatusBadge
    screens: [list, detail, drawer]

# Interaction semantics — authoritative (NOT visual)
interaction:
  transitions:
    - component: Drawer
      kind: fly
      duration_ms: 200
  stores:
    - name: selectedRowId
      kind: writable
  slot_contracts:
    - component: WorkSurface
      slots: [filter, table, footer]
  event_handlers:
    - component: StatusBadge
      events: [click]
      contract: "click emits status-changed with new status enum"
  focus_management:
    - component: Drawer
      rule: "auto-focus first interactive element on open"

# Flow-level enforcement — authoritative for multi-screen bundles
flow_invariants:
  - name: status_badge_token_consistency
    applies_to: [list, detail, drawer]
    spec: "StatusBadge uses --status-* tokens only; no raw color values"
  - name: row_height
    applies_to: [list, drawer]
    spec: "Row height is --row-height-compact across both surfaces"
```

`design-implement` reads:
- `synthesis.*` — for audit and re-run reproducibility (including `dev_no_render` refusal)
- `mode`, `page_mode`, `screens`, `routes` — for per-screen iteration and to confirm the page-mode contract was honored
- `visual_review.needs_human_review` — **gating signal.** When `true`, `design-implement` refuses the bundle and points the user at `design-review` (mirrors the `dev_no_render` refusal contract). This is the auto-handoff blocker that prevents `weak`/`lift_failed`/`exemplar_failed` bundles from leaking into implementation.
- `visual_review.visual_quality`, `visual_lift_over_baseline`, `exemplar_alignment` — surfaced to the implementer for context even when `needs_human_review: false`, so the implementer knows whether the bundle is `excellent` (implement faithfully) or `acceptable` (worth a sanity check before pixel-locking).
- `visual_review.visual_quality_axes`, `visual_review.macro_hierarchy` — audit trail showing WHY the bundle earned its rating (per-axis evidence) and what the macro composition looks like above the fold. Useful for the implementer to confirm structural choices.
- `violations.*` — always present, even when all empty. Lets the implementer (and downstream review) verify that no violation slipped through silently; a manifest where every array is `[]` is provably "checked and clean" rather than "omitted".
- `exemplars.selected[].consulted` and `.comparison.diffs` — confirms each exemplar was actually opened during synthesis and lists per-dimension comparisons. The implementer can use the diffs to identify structural areas where the bundle followed the exemplar versus departed from it.
- `exemplars.selected` — implementer can cross-reference the same exemplars when making framework-level structural choices that the bundle's HTML didn't fully constrain.
- `policy_sections_cited` — for traceability when the implementer asks "why this composition?"
- `targeted_changes` / `unchanged_regions` — for drift enforcement in refine-screen
- `flow_invariants` — for the post-per-screen pass
- `tokens.proposed` — surfaces these to the implementer as policy-extension decisions
- `interaction.*` — for the implementer's framework-specific scaffolding work

`design-implement` does NOT read visual properties from the manifest. Those live only in `bundle/<screen>.html` + `bundle/tokens.css`.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-synthesize/steps/step-01-load-brief.md` to begin.

*(Step files are authored after this workflow.md is ratified — see "Spec → Workflow → Step files" sequencing in the project's design pipeline notes.)*

---

## SUCCESS CRITERIA

This workflow succeeds when:

- The bundle directory exists at `{output_dir}/<target_slug>-<date>/` and contains, at minimum: `<screen>.html`, `tokens.css`, `screenshot-<screen>.png` (unless `--no-render`), `manifest.yaml` for every screen in `{screens}`.
- Every `var(--*)` referenced in any `<screen>.html` is defined in `tokens.css` with an explicit value.
- Every visual CSS value in the bundle is explicit (inline `style="…"` or resolves through `tokens.css`) — `design-implement` can extract values without interpretation. No config-dependent Tailwind classes appear.
- The unconditional manifest-validation pass (step 7) has passed: no `var(--*)` dangles, no manifest entry disagrees with HTML + tokens on a visual fact, no external imports beyond `tokens.css`.
- `manifest.tokens.proposed` length is ≤ 5.
- `manifest.page_mode` is set to one of `operational | analytical | detail` and matches what the brief declared / what step 1 resolved.
- `manifest.policy_sections_cited` is non-empty — at least the sections that drove composition (§2, §6 for operational; §6 for analytical; §7 for detail) and any anti-default checks invoked (§5).
- `manifest.skills_invoked` includes the skills required for `{page_mode}` per the routing matrix (always: `design-policy-canonical` and the resolved project frontend skill; mandatory by page_mode: `operational-finance-ui` for operational/detail, `operational-analytics-band` for analytical). A missing frontend skill is a Gate 5a halt — not a success-criteria warning.
- `manifest.compliance_state` is `pass` OR a documented failure mode (`hard_failed | positive_failed | drift_failed | lift_failed | exemplar_failed | dev_only`) and the user sees it in the handoff print.
- `manifest.visual_review` is fully populated: `visual_quality` ∈ {`excellent`, `acceptable`, `weak`}, `visual_lift_over_baseline` is a boolean, `exemplar_alignment` is set, `review_iterations` is an integer, `needs_human_review` is a boolean, and `handoff_target` is `design-implement` (when `needs_human_review: false`) or `design-review` (when `needs_human_review: true`).
- `manifest.visual_review.visual_quality_axes` has all 5 axes (`hierarchy`, `density`, `typography`, `table_ergonomics`, `generic_look`) each with a `rating` AND a non-empty `evidence` string citing test-case IDs (T1, T2, …). An unevidenced "strong" rating is treated as `weak` for aggregation, so the absence is self-correcting on emit.
- `manifest.visual_review.macro_hierarchy` has an entry for every screen in `manifest.screens`, each with `eye_lands_first`, `above_fold_allocation` (integer percentages summing to exactly 100), and a non-generic `evidence` string. Sum ≠ 100, an unresolvable `eye_lands_first`, or a generic evidence string is a workflow bug — the manifest is not emitted.
- `manifest.violations` is present with all six arrays (`hard_failures`, `positive_assertions`, `drift`, `lift.negative_half`, `lift.positive_half`, `exemplar`) AND a `visual_quality.anti_spreadsheet` block — all unconditionally present, empty `[]` on pass. A run that omits any of these arrays is a workflow bug.
- `manifest.violations.visual_quality.anti_spreadsheet.t4_failed` is consistent with `manifest.visual_review.visual_quality`: when `t4_failed: true`, `visual_quality` MUST be `acceptable` or `weak` (never `excellent`). This is the anti-spreadsheet floor — it is a manifest-validation invariant, not a soft guideline.
- `manifest.exemplars.selected` has 2–3 entries with rationale strings — UNLESS the brief set `exemplar_anchoring: waived`, in which case `exemplars.selected: []` AND `exemplars.waiver_reason` is non-empty. Every non-waived entry has `consulted: true`, `consulted_at_step` set, and `comparison.diffs` populated for every screen × all 5 dimensions (`hierarchy`, `density`, `top_band`, `table_framing`, `state_presentation`). A `consulted: false` entry, or any missing diff, is a workflow bug — step 6 (f) should have looped step 4 before reaching emit.
- `bundle/screenshot-<screen>.png` exists for every screen and is non-empty — UNLESS the run used `--no-render`, in which case `manifest.synthesis.dev_no_render: true` is set and `design-implement` will refuse the bundle.
- In `refine-screen` mode: the drift check has run and any drift has either been eliminated or explicitly moved into `targeted_changes`.
- The next agent in the chain can work from the bundle alone without re-prompting the user. When `needs_human_review: false`, that next agent is `design-implement`; when `true`, it is `design-review` and the manifest's `handoff_target` reflects this.

---

## WHAT THIS WORKFLOW DOES NOT DO

These boundaries are intentional — they preserve the separation of concerns across the design pipeline.

- **Does not generate briefs.** Brief authoring is `design-handoff` / `design-artifact-loop`'s job. If the brief is missing, halt — do not improvise.
- **Does not edit the policy.** Policy changes go through `modify-design-policy`. If synthesis surfaces a policy gap (e.g., >5 proposed tokens), surface it; do not silently extend.
- **Does not enforce values against the running app.** That is `design-implement`'s job (per-screen grid) and `design-review`'s job (post-implementation visual review).
- **Does not run positive-assertion checks for specific values** (row heights, font sizes, etc.). Only contract-critical positive assertions from the allowlist are checked here. Specific-value checks remain in `design-review`.
- **Does not produce a markdown summary of the design.** The brief already exists upstream; the bundle is the design's code-shaped resolution, not a parallel prose spec.
- **Does not invoke `design-implement`.** The handoff line printed at the end of step 7 directs the user; this workflow does not chain.
