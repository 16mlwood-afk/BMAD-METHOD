---
name: 'step-07-emit-manifest'
description: 'Run the unconditional manifest-validation pass (workflow invariants), then write bundle/manifest.yaml per the schema in workflow.md and print the handoff line directing the user to design-implement.'
---

# Step 7: Emit Manifest

**Goal:** Run the workflow's unconditional validation pass (workflow invariants — separate from step 6's policy-derived checks), then write `bundle/manifest.yaml` and print the bundle handoff. This is the final step; control returns to the user.

**Gate owned:** None (Gates 1-4 already passed). But this step contains a HARD FAILURE that halts the workflow entirely if invariants are violated — workflow invariants are not allowed to fail "softly" the way policy checks can.

---

## RULES

- **Workflow invariants are unconditional.** Unlike step 6's policy-derived checks (which can fail and still emit a bundle with `compliance_state` flagged), a workflow invariant failure here is a workflow bug, not a synthesis quality issue. Halt — do NOT emit.
- **Manifest is a receipt, not a parallel spec.** The HTML + tokens.css already encode the visual decisions. The manifest records WHO/WHEN/WHAT skills + interaction semantics + region declarations + flow invariants. If the manifest disagrees with the HTML on any visual fact, the HTML wins and the manifest is regenerated to match — no exceptions.
- **The handoff line is the workflow's output to the user.** It must include: bundle path, screen list, compliance state, the exact next-step command (`design-implement <bundle path>`). The user should be able to copy-paste and proceed without re-prompting.
- **Do NOT invoke `design-implement`.** This workflow ends here. Chaining to `design-implement` is the user's decision, made after reviewing the bundle.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Run the unconditional manifest-validation pass

Four invariants. Each is checked independently; failure of any one halts the workflow. Do NOT emit the manifest if any check fails.

#### Invariant 1: every `var(--*)` resolves in `tokens.css`

Extract every `var(--name)` reference from every `<screen>.html` in the bundle (and any framework scaffold files). For each reference, verify the name is defined in `bundle/tokens.css` (in any `:root` or scoped block).

Failure → halt with:

```
WORKFLOW INVARIANT VIOLATION (1/4): unresolved var(--*) references.

The following var(--*) references appear in HTML but are NOT defined in bundle/tokens.css:
  - var(--accent-warm)         used in bundle/main.html:47
  - var(--row-height-medium)   used in bundle/list.html:102, bundle/detail.html:58
  - ...

This is a workflow bug — synthesis emitted a token reference without defining the token.
Bundle NOT emitted. Re-enter step 4 to fix.
```

#### Invariant 2: no config-dependent Tailwind classes

Extract every `class="..."` attribute from every `<screen>.html`. For each class name, check whether it matches the project's `{tailwind_config_classes}` set OR a known config-dependent prefix pattern:

- Color utilities: `text-`, `bg-`, `border-`, `ring-`, `fill-`, `stroke-` followed by a non-universal name (e.g., `text-primary`, `bg-status-warning`). Universal CSS keywords (`text-white`, `text-black`, `text-transparent`, `bg-current`) are fine because their values aren't config-dependent.
- Spacing utilities: `p-`, `px-`, `py-`, `pt-`, `pr-`, `pb-`, `pl-`, `m-`, `mx-`, `my-`, `mt-`, `mr-`, `mb-`, `ml-`, `gap-`, `space-x-`, `space-y-` followed by a number or named scale.
- Radius utilities: `rounded-`, `rounded-t-`, etc. with a named scale value (`rounded-sm`, `rounded-lg`, `rounded-2xl`). `rounded-full` and `rounded-none` resolve to fixed values and are acceptable, though preferring inline style is cleaner.
- Typography utilities: `text-` followed by a size (`text-sm`, `text-lg`, `text-base`), `font-` followed by a weight name (`font-medium`, `font-bold`), `leading-` with a named value.
- Shadow utilities: `shadow-`, `shadow-sm`, `shadow-lg`, etc.

Allowed structural classes (NOT config-dependent in any reasonable Tailwind setup):

- Layout topology: `flex`, `inline-flex`, `grid`, `inline-grid`, `block`, `inline-block`, `inline`, `hidden`, `contents`, `flow-root`.
- Positioning: `relative`, `absolute`, `fixed`, `sticky`, `static`, `inset-0`, `inset-auto`, `top-0`, `right-0`, `bottom-0`, `left-0`.
- Display modifiers: `sr-only`, `not-sr-only`.
- Flex/grid behavior: `flex-1`, `flex-auto`, `flex-none`, `flex-row`, `flex-col`, `flex-wrap`, `flex-nowrap`, `items-start`, `items-center`, `items-end`, `items-stretch`, `items-baseline`, `justify-start`, `justify-center`, `justify-end`, `justify-between`, `justify-around`, `justify-evenly`, `place-items-*`, `place-content-*`, `self-start`, `self-center`, `self-end`, `self-stretch`, `col-span-*`, `row-span-*`, `col-start-*`, `row-start-*`, `grid-cols-*`, `grid-rows-*` (note: `grid-cols-N` is a structural primitive even though N is a number — it's universal).
- Overflow: `overflow-hidden`, `overflow-auto`, `overflow-scroll`, `overflow-visible`.
- Cursor: `cursor-pointer`, `cursor-default`, `cursor-not-allowed`.
- Pointer events: `pointer-events-none`, `pointer-events-auto`.

Failure → halt with:

```
WORKFLOW INVARIANT VIOLATION (2/4): config-dependent Tailwind classes detected.

The following class names appear in HTML but resolve through tailwind.config — design-implement cannot extract their values without interpretation:
  - bundle/main.html:47   class="... text-primary ..."
  - bundle/list.html:102  class="... p-4 rounded-lg ..."
  - ...

This is a workflow bug — synthesis emitted classes whose values are not parse-time-explicit.
Replace with inline style="..." or var(--*) references.
Bundle NOT emitted. Re-enter step 4 to fix.
```

#### Invariant 3: manifest does not disagree with HTML on visual facts

The manifest hasn't been written yet, but the SHAPE the synthesizer plans to write must not contain visual properties that contradict the HTML. This check runs against the planned manifest content (`{manifest_draft}` — built in §2 below).

Verify the planned manifest contains NO entries under:

- `tokens.used[*].value` — visual values; live in `tokens.css` only.
- `components_emitted[*].style` / `*.color` / `*.spacing` / similar — visual; lives in HTML.
- Any top-level key holding a visual property (`palette:`, `typography:`, `spacing_scale:`).

The manifest only stores:

- `synthesis.*` (receipt: timestamps, paths, hashes, iterations, skills, compliance state)
- `mode`, `page_mode`, `target_slug`, `target_route`, `routes`, `screens` (scope)
- `policy_sections_cited` (exemplar-disclosure trail)
- `targeted_changes`, `unchanged_regions` (refine-screen scope)
- `tokens.used[*].name`, `*.source` (attribution, NOT value — values are in tokens.css)
- `tokens.proposed[*]` (proposals, with `justification`, NOT redefined values)
- `components_emitted[*].name`, `*.screen`, `*.region_span` (component receipt, NOT styling)
- `interaction.*` (non-visual interaction semantics)
- `flow_invariants[*]` (cross-screen rules)

Failure → halt with:

```
WORKFLOW INVARIANT VIOLATION (3/4): manifest draft contains visual properties.

The manifest must NOT be authoritative for visual values. The following draft entries duplicate visual facts that belong to bundle/<screen>.html or bundle/tokens.css:
  - tokens.used[2].value = "#f59e0b"   (value belongs only in tokens.css)
  - palette.primary = "#0ea5e9"        (palette is not a manifest concept — remove)
  - ...

Bundle NOT emitted. Strip visual properties from the manifest draft and re-validate.
```

#### Invariant 4: bundle is self-contained

Scan every file in `{bundle_dir}` for external imports beyond `tokens.css`:

- HTML: `<link rel="stylesheet" href="X">` where `X != "tokens.css"`. `<script src="X">`. `<img src="X">` where `X` is `http://` or `https://`. `<iframe src="X">`.
- CSS: `@import url("X")` where `X` is not a same-directory path. `url(X)` for fonts where `X` is `http://` or `https://`.
- JSX/Svelte/Vue scaffolds: `import` statements pointing outside the bundle directory (other than framework runtime imports like `svelte`, `react`, `vue`).

Failure → halt with:

```
WORKFLOW INVARIANT VIOLATION (4/4): bundle is not self-contained.

The following external imports/references appear in the bundle:
  - bundle/main.html:7  <link rel="stylesheet" href="https://fonts.googleapis.com/...">
  - bundle/tokens.css:1 @import url("../shared/colors.css");
  - ...

Bundles must render offline with only bundle/tokens.css as a peer dependency.
Inline the resource, or remove the reference.
Bundle NOT emitted. Re-enter step 4 to fix.
```

### 2. Build the manifest draft

Compose `{manifest_draft}` per the schema in workflow.md §MANIFEST SCHEMA. Pull every field from existing state — no recomputation. The shape:

```yaml
synthesis:
  workflow: design-synthesize
  version: 1
  date: {iso8601 now}
  brief_path: {repo-relative}
  brief_type: {brief_type}
  policy_path: {repo-relative policy_path}
  policy_version_hash: {policy_version_hash}
  baseline_commit: {baseline_commit}
  frontmatter_lifts: {frontmatter_lifts}    # map of field → {value, source} for required brief frontmatter fields that step 1 lifted from the brief body (§5b / §8a). Emit as `{}` when no lifts occurred (NOT null, NOT omitted — explicit `{}` confirms step 1 ran and recorded zero lifts). Non-empty lifts are structural decisions the bundle's reproducibility hinges on.
  iterations: {iteration_count}
  compliance_state: {compliance_state}
  dev_no_render: {dev_no_render}
  playwright_version: {playwright_version or null}
  skills_invoked:
    - {each entry in skills_invoked, one per line}

mode: {mode}                              # synthesis mode (fresh-design | refine-screen)
page_mode: {page_mode}                    # composition mode (operational | analytical | detail) — policy §6 / §7
target_slug: {target_slug}
target_route: {target_route or null}
routes: {routes or []}
screens: {screens}

# Visual review — authoritative for the visual-quality + lift outcome of step 6 (d/e/f).
# design-implement reads needs_human_review as the auto-handoff gating signal.
visual_review:
  visual_quality: {visual_quality}                            # excellent | acceptable | weak
  visual_quality_axes:                                        # per-axis ratings from step 6 (d), audit trail
    hierarchy: {strong | adequate | weak}
    density: {strong | adequate | weak}
    typography: {strong | adequate | weak}
    table_ergonomics: {strong | adequate | weak}
    generic_look: {strong | adequate | weak}
  visual_lift_over_baseline: {visual_lift_passed}             # boolean — positive half of the lift test
  exemplar_alignment: {exemplar_alignment}                    # aligned | deviated_with_brief_authorization | deviated_unauthorized
  review_iterations: {review_iterations}                      # how many of the step-6 loop iterations were driven by visual sub-checks
  needs_human_review: {needs_human_review}                    # boolean — design-implement refuses when true
  handoff_target: {"design-review" if needs_human_review else "design-implement"}

# Exemplars — 2-3 gold-standard screens used as anchors during synthesis (loaded in step 3 §9).
# When the brief sets exemplar_anchoring: waived, this section reflects the waiver.
exemplars:
  gallery_path: {exemplar_gallery_path or null}
  selected:
    - path: {repo-relative path 1}
      rationale: {one-line rationale from {exemplars_rationale}}
    - path: {repo-relative path 2}
      rationale: ...
  # When waived, omit `selected` and emit:
  # waiver_reason: {brief_frontmatter.waiver_reason}

# Policy sections that drove the synthesis — exemplar-disclosure rule
# (design-policy-canonical skill §"Exemplars" / policy §10)
policy_sections_cited:
  - {each entry in policy_sections_cited, one per line}

# Refine-screen scope (omit entire blocks if mode == fresh-design)
targeted_changes:
  - region: {name}
    rationale: {text}
unchanged_regions:
  - region: {name}

tokens:
  used:
    - name: {--token-name}
      source: project | proposed
    - ...
  proposed:
    - name: {--proposed-name}
      source: proposed
      justification: {text}
    - ...

components_emitted:
  - name: {ComponentName}
    screen: {screen_name}            # for single-screen-only components
    screens: [{list}]                # for multi-screen components
    region_span: {selector or anchor}
  - ...

interaction:
  transitions: [...]                  # if any planned in step 4
  stores: [...]                       # framework-specific stores referenced
  slot_contracts: [...]               # slot composition rules
  event_handlers: [...]               # event schemas (NOT visual)
  focus_management: [...]             # focus rules for modals/drawers

flow_invariants:
  - name: {invariant_name}
    applies_to: [{list of screens}]
    spec: {text}
  - ...
```

For single-screen bundles, omit `flow_invariants` (or set to `[]`). For `fresh-design` mode, omit `targeted_changes` and `unchanged_regions`.

For sub-checks that didn't fail, omit their violation arrays (don't write `hard_failure_violations: []` — leave silent). If sub-checks failed but the bundle still emitted (compliance_state != pass OR needs_human_review == true), include the violation arrays for audit:

```yaml
violations:
  # Policy half (step 6 a/b/c)
  hard_failures:
    - rule: {text}
      file: {path}
      line: {int}
      snippet: {text}
  positive_assertions: [...]
  drift: [...]

  # Visual half (step 6 d/e/f)
  visual_quality:
    rating: {visual_quality}
    weak_axes:
      - axis: {hierarchy | density | typography | table_ergonomics | generic_look}
        screens: [<list of screens where this axis was weak>]
        correction_note: {one-line from step 6 visual_quality_correction}
  lift:
    negative_half:
      - screen: {path}
        detector: {placeholder_data | generic_chrome | crm_composition | wrong_locale | page_mode_mismatch}
        detail: {text}
    positive_half:
      - screen: {path}
        requirement: {1 | 2 | 3}
        detail: {text}
  exemplar:
    - screen: {path}
      dimension: {hierarchy | density | top_band | table_framing | state_presentation}
      exemplar: {path}
      detail: {what departed}
```

### 3. Re-run invariant 3 against the actual draft

The draft now exists. Run the invariant-3 check (no visual properties in manifest) against the actual content. Step 1's check was anticipatory; this is the actual gate.

Failure → halt as in §1, invariant 3.

### 4. Write `bundle/manifest.yaml`

```bash
# Write the manifest using the Write tool (not echo/cat heredoc — Write is the dedicated tool).
```

Verify the file exists and is non-empty.

### 5. Print the handoff line

This is the workflow's output. The user should be able to read this and immediately proceed. The next-step command is chosen by `needs_human_review`: when true, route through `design-review` first; when false, hand directly to `design-implement`.

```
══════════════════════════════════════════════════════════════════
✓ design-synthesize complete

  bundle:              {bundle_dir}
  page_mode:           {page_mode}
  screens:             {comma-separated screen filenames}
  compliance state:    {compliance_state}
  iterations:          {iteration_count}/3 (visual: {review_iterations})
  proposed tokens:     {len(tokens_proposed)}/5
  skills invoked:      {comma-separated skills_invoked}
  frontend skill:      {frontend_skill} (resolved via {frontend_skill_source})
  exemplars:           {len(exemplars.selected)} ({comma-separated basenames or "waived"})
  policy sections:     {comma-separated policy_sections_cited}

  [VISUAL REVIEW]
  visual quality:      {visual_quality}
  lift over baseline:  {"passed" if visual_lift_over_baseline else "failed"}
  exemplar alignment:  {exemplar_alignment}
  needs human review:  {needs_human_review}
{if compliance_state != pass:}
  ⚠ failure mode:     {compliance_state} — {N} violations recorded in manifest.violations
{end if}
{if dev_no_render:}
  ⚠ dev-only build:   --no-render was used. design-implement WILL refuse this bundle.
{end if}
{if needs_human_review:}
  ⚠ blocked from auto-handoff: visual review flagged this bundle for human design review.
    design-implement WILL refuse it (per the bundle-gating contract). Route through
    design-review first.
{end if}

Next step:

{if needs_human_review:}
  # Human design review required before implementation.
  /bmad:bmm:workflows:design-review {bundle_dir}

  After design-review either confirms the bundle or you re-run design-synthesize
  to address the review notes, then hand to design-implement.
{else if dev_no_render:}
  # This bundle cannot be implemented (no screenshot). Re-run without --no-render.
  /bmad:bmm:workflows:design-synthesize {brief_path}
{else:}
  # Hand the bundle to design-implement:
  /bmad:bmm:workflows:design-implement {bundle_dir}

  design-implement will read bundle/<screen>.html + tokens.css value-by-value and
  emit a delta report against your project's current implementation.
{end if}
══════════════════════════════════════════════════════════════════
```

### 6. Workflow exits

Control returns to the user. Do not auto-invoke `design-implement` or any other workflow.

---

## STATE CHECKPOINT (final)

The bundle directory exists and contains, at minimum:

- `<screen>.html` for every `screen ∈ {screens}`
- `tokens.css`
- `screenshot-<screen>.png` for every `screen ∈ {screens}` (unless `--no-render`)
- `manifest.yaml`

Optionally (framework projects):

- `<screen>.<ext>` per screen (e.g., `<screen>.svelte`)

The manifest contains all required fields per workflow.md §MANIFEST SCHEMA. The handoff line has been printed.

This workflow run is complete.
