<!--
  Canonical design-synthesize manifest schema (bundle/manifest.yaml).
  Extracted from workflow.md 2026-06-10 (digestibility) — same text, verbatim.
  Emitted by step-07-emit-manifest.md; read by design-implement. workflow.md
  keeps the one-line authority summary + a pointer here.
-->

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
