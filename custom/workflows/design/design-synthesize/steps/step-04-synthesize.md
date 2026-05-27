---
name: 'step-04-synthesize'
description: 'Invoke sister skills, generate bundle/<screen>.html and bundle/tokens.css per screen with explicit visual values, enforce the 5-token proposal cap (Gate 3).'
---

# Step 4: Synthesize

**Goal:** Produce the actual design artifact. For each screen in `{screens}`, emit `bundle/<screen>.html` + a shared `bundle/tokens.css` such that `design-implement` can extract every visual value at parse time without interpretation.

**Gate owned:** Gate 3 — token cap (workflow.md §APPROVAL GATES). Halt before emitting if synthesis would require more than 5 tokens that don't already exist in `{project_tokens}`.

**Loop target:** This step is the target of step 6's self-critique loop. On the 2nd or 3rd entry, the synthesizer receives a `{correction_note}` from step 6 — apply the correction precisely; do not rewrite unrelated regions.

---

## RULES

- **The bundle is the design.** Do not produce a parallel markdown summary. The brief already exists upstream.
- **Every visual value is explicit at parse time.** Visual values — color, spacing, type size/weight, sizing, radius, shadow, borders — must appear as inline `style="…"` attributes or `var(--*)` references defined in `bundle/tokens.css`. **Config-dependent Tailwind utility classes are forbidden** — any class whose computed value comes from `tailwind.config.js` (e.g., `text-primary`, `rounded-lg`, `p-4`, `bg-status-warning`). Structural utility classes whose meaning is universal (`flex`, `grid`, `hidden`, `sr-only`, `block`, `relative`, `absolute`, `inset-0`) are fine — they encode layout topology, not values.
- **Token reuse first, propose second.** When you need a value, check `{project_tokens}` for a matching token. Only if no project token matches the brief's intent do you propose a new one. Each proposal counts against the 5-cap.
- **No lorem ipsum.** Realistic content comes from `{data_shape}`. If the brief says the table shows invoices with VAT rates, populate rows with realistic invoice numbers, supplier names, GBP amounts at plausible VAT rates. Empty states, error states, loading states — render them with realistic copy too.
- **The HTML is canonical; framework files are scaffolds.** Emit `<screen>.html` first, every time. The framework file (e.g., `<screen>.svelte`) is an OPTIONAL convenience for the implementer; if you emit it, it must match the HTML's visual decisions exactly. `design-implement` reads the HTML.
- **Refine-screen: respect the scope.** In `refine-screen` mode, regions declared in `{unchanged_regions}` must match `{prior_impl_content}` byte-for-byte (modulo token substitution). Touching them is a step-6c failure.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Resolve the bundle directory

```
{bundle_dir} = {implementation_artifacts}/bundles/{target_slug}-{date}/
```

Where `{date}` is `YYYY-MM-DD` from the system clock. Create the directory if it doesn't exist:

```bash
mkdir -p {bundle_dir}
```

If a `{target_slug}-{date}` bundle already exists from an earlier run today, append a run suffix (`-r2`, `-r3`, …). Do NOT overwrite a prior bundle — each run is a separate artifact for audit.

### 2. Invoke sister skills (first iteration only) — driven by `{page_mode}`

Per workflow.md §SKILL ROUTING, skill routing is **driven by `{page_mode}`**, not by free-text screen-type inference. This makes routing deterministic. Skill invocation is cached across self-critique iterations — load once per run.

**Always invoke in every run (every page_mode, both synthesis modes):**

- `design-policy-canonical` — the policy is the floor; the skill enforces the trust hierarchy and refuses anti-default compositions.
- **`{frontend_skill}`** (resolved in step 3 §8 — MANDATORY). Synthesis emits HTML and tokens; layout, hierarchy, typography, and visual patterns MUST be chosen by a skill with frontend/design competence — not by policy or domain skills alone. Per the role split in workflow.md §SKILL ROUTING → "Role of each skill", this skill owns taste (hierarchy, rhythm, density calibration, aesthetic restraint) — without it, synthesis produces a policy-compliant wireframe rather than a designed screen. Gate 5a in step 3 already halted the workflow if this skill couldn't be resolved.

**Consult `{exemplars}` (loaded in step 3 §9) BEFORE composing each screen.** Read 1–2 exemplars whose page-mode and surface-family best match the screen being synthesized. Anchor hierarchy, density, top-band summary patterns, table framing, and state presentation to the exemplars unless the brief explicitly authorizes a departure. Step 6 (f) will flag unauthorized deviation as `exemplar_failed`.

**Drive by `{page_mode}`:**

| `{page_mode}` | Mandatory in addition to always-invoke | Conditional |
|---|---|---|
| `operational` | `operational-finance-ui` — table-first composition, filter bar, status hierarchy, dense row treatment per policy §6 | `operational-analytics-band` if the screen carries a narrow analytics band above or beside the table |
| `analytical` | `operational-analytics-band` — chart-led composition, drill-down evidence, no card-grid openers per policy §6 | `operational-finance-ui` if drill-down tables are part of the brief |
| `detail` | `operational-finance-ui` — drawer/detail extends an operational list; same surface, typography, badges per policy §7 | `operational-analytics-band` is **NOT applicable** — detail views forbid KPI cards / charts per policy §7 |

Record every invocation into `{skills_invoked}` (a list). This list is written to `manifest.skills_invoked` in step 7. A bundle emitted with `{skills_invoked}` missing the mandatory entries for `{page_mode}` is a routing failure — step 6's enforcement rule rewinds to this step.

**Track policy citations:** as each skill is invoked, record which policy sections it points at into `{policy_sections_cited}` (e.g., `["§1 Visual Direction", "§2 Layout Principles", "§6 Operational mode"]`). This list is written to `manifest.policy_sections_cited` per the exemplar-disclosure rule (`design-policy-canonical` skill §"Exemplars" / policy §10) so a reader of the manifest can trace any composition decision back to the policy line that ratified it.

**Iteration cache:** On 2nd or 3rd entry to this step (from step 6's loop), reuse the cached skill context — do not re-invoke. The skills' guidance does not change mid-run. `{policy_sections_cited}` may grow as later iterations consult additional sections (e.g., §5 Anti-default compositions during a hard-failure correction).

### 3. Plan the bundle structure (before writing files)

For each screen in `{screens}`, plan:

- **Layout topology:** what flex/grid containers, what major regions, what nesting depth. Refer to the project frontend skill's page composition vocabulary. Avoid decorative wrappers — every container should justify its existence (it groups content, it provides spacing, it constrains width).
- **Components:** which named components appear (e.g., `WorkSurface`, `FilterRow`, `DataTable`, `StatusBadge`). These names go into `{components_emitted}` and the manifest. Component identity is stable across screens — the same `StatusBadge` should look identical wherever it appears.
- **Data binding:** which fields from `{data_shape}` populate which regions. Realistic content only.
- **Density:** dense vs comfortable. Driven by `{user_context}` (operator-facing → dense; auditor-facing → comfortable).
- **State variations:** if the brief asks for empty/loading/error states, plan their treatment. For multi-screen bundles, plan each screen's state variations independently.

**Refine-screen scope (mode == refine-screen):**

- Mark each planned region as `targeted` (in `{targeted_changes}`) or `unchanged` (in `{unchanged_regions}`).
- For `unchanged` regions, copy the prior implementation's markup (translated to inline-style HTML if it currently uses Tailwind classes — token substitution is allowed, structural changes are not).
- For `targeted` regions, apply the brief's correction.

Do not write any file yet. Planning happens first so the token budget is known before emission.

### 4. Build the proposed token list (Gate 3 check)

For each visual value in the plan, decide: token (reuse) or literal (inline)?

**Prefer tokens** when the value has semantic meaning the policy or brief names:

- "Status warning amber" → token (`--status-warning`).
- "Brand primary" → token (`--primary` or `--color-primary`).
- "Compact row height" → token (`--row-height-compact`).
- "Surface background" → token (`--surface`, `--bg-card`).

**Prefer literals** when the value is purely structural or one-off:

- A specific pixel offset for a decorative element.
- An interpolated value that won't recur (a unique mask-image, a one-off shadow combination).

For each token chosen, check `{project_tokens}`:

- **Hit:** the token name + value already exists in the project. Use it directly. Add to `{tokens_used}` with `source: "project"`. No cap impact.
- **Miss:** the token name doesn't exist, OR the name exists but with a different value. **This is a proposal.** Add to `{tokens_used}` with `source: "proposed"` and to `{tokens_proposed}` with a `justification` tying back to the brief section that motivated it.

**Gate 3 enforcement:**

```
if len({tokens_proposed}) > 5:
    halt with:
      "Gate 3 (token cap): this bundle would introduce N>5 new tokens.
       Proposed tokens:
         {list each with --name → value and justification}
       Options:
         (a) Extend docs/design-policy.md to ratify the new tokens — run modify-design-policy.
         (b) Revise the brief to reuse existing project tokens — list of available tokens at {project_token_paths}.
         (c) Inline more values as literals instead of var(--*) references.
       Do not bypass this gate."
```

The 5-cap is a deliberate forcing function — silently expanding the design system is exactly the failure mode this cap exists to prevent. Halting here is correct.

### 5. Emit `bundle/tokens.css`

Write the shared tokens file. Structure:

```css
/* tokens.css — design-synthesize bundle for {target_slug}
 * synthesized: {iso8601}
 * policy version: {policy_version_hash[:12]}
 * brief: {repo-relative brief path}
 */

:root {
  /* Project tokens (source: {project_token_paths}) */
  --status-warning: #f59e0b;       /* src/app.css:142 */
  --status-success: #10b981;       /* src/app.css:143 */
  --row-height-compact: 32px;      /* src/app.css:201 */
  /* ... every token referenced in any <screen>.html that came from {project_tokens} ... */

  /* Proposed tokens (NOT YET in project; flagged in manifest.tokens.proposed) */
  --accent-warm: #f97316;          /* PROPOSED — brief §4 visual direction */
  /* ... up to 5 proposed tokens ... */
}
```

Token rules:

- Every `var(--*)` referenced in any `<screen>.html` MUST be defined here. Unresolved references fail step 7's validation pass.
- Project tokens cite their source file:line as a comment, so the implementer can verify the bundle's value matches the project's.
- Proposed tokens carry a `/* PROPOSED — {justification} */` comment.
- Do NOT include tokens that aren't referenced in any HTML. Unused tokens muddy the manifest.

If the project supports dark mode (detected in step 3 by scanning for `[data-theme="dark"]` or `.dark` scopes in `{project_token_paths}`) AND the brief calls for dark-mode awareness, emit a `[data-theme="dark"]` block with the overridden values.

### 6. Emit `bundle/<screen>.html` for each screen

For each screen in `{screens}`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{target_slug} — {screen}</title>
  <link rel="stylesheet" href="tokens.css">
  <style>
    /* Reset / normalize — minimal. The bundle is a design artifact, not a production page. */
    body { margin: 0; font-family: system-ui, -apple-system, sans-serif; background: var(--bg-app, #f9fafb); color: var(--fg, #111827); }
    *, *::before, *::after { box-sizing: border-box; }
  </style>
</head>
<body>
  <!-- All visual values below are inline style="..." or var(--*) references.
       NO config-dependent Tailwind classes. Structural utilities (flex, grid, hidden) are fine. -->

  <main style="max-width: 1440px; margin: 0 auto; padding: 24px;">
    {synthesized content per the plan, with inline styles for every visual decision}
  </main>
</body>
</html>
```

Visual-value rules (the workflow's central invariants):

- **Inline `style="..."`** for one-off values: `style="padding: 16px; border-radius: 8px; background: #ffffff;"`.
- **`var(--name)`** for semantic values: `style="background: var(--surface); color: var(--fg-muted);"`.
- **Structural utility classes** are fine: `class="flex items-center gap-3"`. (Note: `gap-3` resolves to a spacing value in Tailwind, which IS config-dependent. Use `style="gap: 12px"` or `style="gap: var(--spacing-3)"` instead.) Stick to truly structural classes: `flex`, `grid`, `hidden`, `block`, `absolute`, `relative`, `inset-0`.
- **Stable component identifiers** via `data-component="WorkSurface"` etc. — `design-implement` uses these to map bundle regions to implementation regions.
- **Region anchors** for refine-screen targeted/unchanged regions: `data-region="header"`, `data-region="filter-row"`. These map to `manifest.targeted_changes` and `manifest.unchanged_regions` entries.

### 7. Emit framework scaffolds (optional)

If `{framework} != "none"`, optionally emit `bundle/<screen>.<ext>` matching the project's component format. The scaffold:

- Translates the HTML into framework syntax (`{#each items}` for Svelte, `{items.map(...)}` for React).
- Preserves every visual decision from the HTML (same inline styles, same `var(--*)` references).
- Wires up the data binding using realistic types derived from `{data_shape}`.
- Is NOT authoritative. If the scaffold and HTML disagree on a visual fact, the HTML wins.

This is optional convenience for the implementer. Skipping it does not break the bundle.

### 8. Take screenshots (deferred to step 5)

Do not invoke Playwright here. Step 5 owns rendering. This step only writes HTML + tokens (and optional scaffolds).

### 9. Record components and tokens used

Populate state for step 7's manifest emission:

- `{components_emitted}` — list of `{name: "WorkSurface", screen: "main", region_span: "main > [data-component='WorkSurface']"}` records.
- `{tokens_used}` — list of `{name: "--status-warning", source: "project" | "proposed"}` records.
- `{tokens_proposed}` — subset of `{tokens_used}` with `source == "proposed"`. Already validated against the 5-cap.

### 10. Print the synthesis summary and proceed

```
✓ Synthesis emitted:
  bundle:           {bundle_dir}
  screens:          {comma-separated screen filenames}
  framework files:  {comma-separated scaffold filenames, or "none"}
  tokens:           {len(tokens_used)} used ({len(project tokens used)} project, {len(tokens_proposed)} proposed)
  components:       {comma-separated component names}
  skills invoked:   {comma-separated skills_invoked}
  iteration:        {iteration_count + 1}/3

Proceeding to step 5: render screenshots.
```

Then load `step-05-render-screenshot.md` and follow it.

---

## INTERACTION WITH STEP 6 (self-critique loop)

This step is invoked up to 3 times per run. The second and third invocations carry a `{correction_note}` from step 6 describing the failure:

- **Hard-failure correction:** "Step 6a: bundle/main.html line 47 commits the 'colored pill badge' anti-pattern (policy line 89). Replace with a token-driven status badge."
- **Positive-allowlist correction:** "Step 6b: status indicators in bundle/main.html use raw color #f59e0b instead of --status-warning (policy line 134)."
- **Drift correction:** "Step 6c: bundle/list.html region 'footer' diverged from prior implementation (src/routes/.../+page.svelte:412-440) but 'footer' is declared in unchanged_regions. Either eliminate the diff or move 'footer' into targeted_changes."

Apply the correction narrowly. Do NOT rewrite unrelated regions. Re-run the steps in this file from §4 (token budget recheck) → §5 (re-emit tokens.css if tokens changed) → §6 (re-emit the affected HTML file). Then return to step 5.

On the 3rd correction attempt that still fails, step 6 will record the failure mode in `{compliance_state}` and proceed to step 7 with the failed bundle flagged. Step 4 itself never halts the workflow; that's step 6's job.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{bundle_dir}` (directory exists)
- `{skills_invoked}` (non-empty)
- `{tokens_used}` (may be empty if no var(--*) used), `{tokens_proposed}` (length ≤ 5)
- `{components_emitted}` (non-empty)
- Files exist: `{bundle_dir}/tokens.css`, `{bundle_dir}/<screen>.html` for every `screen ∈ {screens}`

Any unset required variable or missing file is a workflow bug — halt before step 5.
