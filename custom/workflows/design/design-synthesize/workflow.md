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

**Policy non-overridability:** The brief (1) may narrow, focus, or summarize the policy (2) for a feature, but it MUST NOT loosen, carve out, or contradict the policy's hard failures or contract-critical positive-assertion allowlist. A brief that asks for behavior the policy forbids does not earn an exception — it surfaces a `modify-design-policy` candidate to the user. `design-synthesize` halts rather than honoring a brief that conflicts with policy. The brief's authority is over scope and emphasis, not over the policy's floors.

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
- `{mode}` — `fresh-design` | `refine-screen`. Inherited from the brief's mode field; refine-screen requires the brief to reference a `screen-review-*.md` artifact and to declare targeted vs unchanged regions.
- `{target_slug}` — Kebab-case slug for the feature/flow (e.g., `reclaim-avask`).
- `{target_route}` — Route the bundle represents (e.g., `/reclaim/avask`). May be a single route or a flow of routes for multi-screen bundles.
- `{screens}` — Ordered list of screen names for multi-screen bundles. Single-screen runs have `len(screens) == 1`.
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
- `{compliance_state}` — `pass` | `hard_failed` | `positive_failed` | `drift_failed`. Recorded in manifest after step 6.
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

- Never halt for user input. The only legitimate halts are the four gates below.
- When the policy is missing → halt (this is one of the gates).
- When >5 tokens would be proposed → halt (this is one of the gates).
- When Playwright is unavailable → halt (this is one of the gates).
- When the brief is missing or malformed → halt (this is one of the gates).

These four gates are the only autonomous-mode exits. Everything else proceeds.

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

1. **`step-01-load-brief.md`** — Resolve the brief artifact, parse YAML frontmatter, extract feature purpose / data shape / user context / visual direction / hard constraints / design ask / mode / target slug / screens list / (refine-screen only) targeted vs unchanged regions. **Halts** if the brief is missing or malformed (Gate 1).
2. **`step-02-load-policy.md`** — Resolve and load `{policy_path}`, compute `{policy_version_hash}`, extract `{hard_failures}` and `{positive_allowlist}`. **Halts** if the policy is missing (Gate 2).
3. **`step-03-load-frontend-context.md`** — Detect `{framework}` from `package.json`, locate and parse `{tailwind_config_path}` and the project token file, populate `{project_tokens}`. In refine-screen mode, also locate `{prior_impl_paths}` for the drift baseline.
4. **`step-04-synthesize.md`** — Invoke the relevant sister skills (per Skill Routing below) and generate `bundle/<screen>.html` + `bundle/tokens.css` for each screen in `{screens}`. Every visual property is an explicit value. **Halts** if synthesis would introduce >5 new tokens (Gate 3).
5. **`step-05-render-screenshot.md`** — Run Playwright (headless Chromium) against each `bundle/<screen>.html` at the brief's primary viewport. Save `bundle/screenshot-<screen>.png`. **Halts** if Playwright is unavailable (Gate 4).
6. **`step-06-self-critique.md`** — Run three sub-checks:
   - **(a) Hard-failure check** against `{hard_failures}` from the policy.
   - **(b) Policy-derived positive-assertion check** against `{positive_allowlist}` from the policy — items the policy itself ratifies as contract-critical (e.g., "status indicators use status tokens not raw colors", "components have stable identifiers"). `design-synthesize` does NOT invent allowlist items.
   - **(c) Drift check** (refine-screen only) — diff bundle against prior implementation; non-empty diff in any `unchanged_region` is a failure.

   Note: workflow invariants (every `var(--*)` resolves, no config-dependent Tailwind, manifest visual-disagreement-tiebreaker, bundle self-containment) are NOT in this self-critique pass — they are unconditional and run in step 7's manifest-validation gate. The allowlist is reserved for policy-derived assertions only.

   On failure of any sub-check, return to step 4 with a targeted correction note. Max 3 iterations across all sub-checks. On the 3rd failure, set `{compliance_state}` to the failure mode and proceed to step 7 anyway.
7. **`step-07-emit-manifest.md`** — Run the **unconditional manifest-validation pass** first: every `var(--*)` in any `<screen>.html` resolves in `tokens.css`; no config-dependent Tailwind classes appear; no values in `manifest.yaml` disagree with HTML + tokens; bundle is self-contained (no external imports beyond `tokens.css`). A failure here is a workflow bug — halt and report; do NOT emit a bundle that violates workflow invariants. If validation passes, write `bundle/manifest.yaml` per the Manifest Schema below. Print bundle path, screen list, compliance state, and the next-agent hand-off line directing the user to `design-implement`.

---

## SKILL ROUTING

`design-synthesize` MUST invoke the relevant frontend/design skills BEFORE generating output in step 4. Skill invocation is logged in the manifest under `skills_invoked:` for audit. Improvising visual decisions from workflow prose alone is the failure mode this section exists to prevent.

### Routing rules

Because **every run of this workflow synthesizes actual HTML**, the project frontend/webapp design skill is mandatory in both modes — not conditional. Generating HTML without frontend design vocabulary is the exact failure mode this routing rule prevents. The conditional skills are `operational-finance-ui` and `operational-analytics-band`, which depend on screen type.

#### In `fresh-design` mode (new screen or full redesign)

Always invoke:
- `design-policy-canonical`
- Project frontend / webapp design skill (e.g., `website-building`) — page composition, spacing, hierarchy, component treatment, web UI conventions.

Conditionally invoke:
- `operational-finance-ui` when the screen is a dense worklist, table, queue, filter row, status hierarchy, or operational finance surface.
- `operational-analytics-band` when the screen includes KPI strips, analytics rows, trend bands, or quarter-by-quarter summary bands.

#### In `refine-screen` mode (iteration bounded by screen-review artifact)

Always invoke:
- `design-policy-canonical`
- Project frontend / webapp design skill — same reason as `fresh-design`: synthesis emits HTML and needs design vocabulary regardless of how bounded the changes are.

Conditionally invoke:
- `operational-finance-ui` when the screen being refined is a finance worklist / table / queue / operational surface.
- `operational-analytics-band` when the targeted changes touch an analytics band / KPI row.

### Enforcement

A run that emits a bundle with no entries under `manifest.skills_invoked` is a failed routing pass. Step 6 must rewind to step 4 to load the missing skills before continuing. Skills are loaded once per run (cache on the first invocation); subsequent step-04 iterations within the self-critique loop reuse the cached skill context.

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
- Brief contains valid YAML frontmatter with at least: `target_slug`, `mode`, `route` (or `routes` for multi-screen).
- In `refine-screen` mode: brief references a `screen-review-*.md` and declares `targeted_changes` + `unchanged_regions`.

If this gate fails, halt and report the missing field(s). Do NOT guess paths or substitute a stale brief.

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
  iterations: {integer}
  compliance_state: {pass | hard_failed | positive_failed | drift_failed | dev_only}
  dev_no_render: {false | true}  # true ONLY when --no-render was used; design-implement refuses these bundles
  skills_invoked:
    - design-policy-canonical
    - {project-frontend-skill}     # MANDATORY — synthesis always emits HTML
    - operational-finance-ui       # if applicable to screen type
    - operational-analytics-band   # if applicable to screen type

# Mode and scope — authoritative
mode: {fresh-design | refine-screen}
target_slug: {kebab-case slug}
target_route: {single route or null}
routes: [{list of routes for multi-screen flows}]
screens: [{ordered list of screen names}]

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
- `synthesis.*` — for audit and re-run reproducibility
- `mode`, `screens`, `routes` — for per-screen iteration
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
- `manifest.skills_invoked` includes the skills required for the mode (always: `design-policy-canonical` and project frontend skill; conditional: `operational-finance-ui`, `operational-analytics-band`).
- `manifest.compliance_state` is `pass` OR a documented failure mode (`hard_failed | positive_failed | drift_failed | dev_only`) and the user sees it in the handoff print.
- `bundle/screenshot-<screen>.png` exists for every screen and is non-empty — UNLESS the run used `--no-render`, in which case `manifest.synthesis.dev_no_render: true` is set and `design-implement` will refuse the bundle.
- In `refine-screen` mode: the drift check has run and any drift has either been eliminated or explicitly moved into `targeted_changes`.
- The next agent in the chain (`design-implement`) can work from the bundle alone without re-prompting the user.

---

## WHAT THIS WORKFLOW DOES NOT DO

These boundaries are intentional — they preserve the separation of concerns across the design pipeline.

- **Does not generate briefs.** Brief authoring is `design-handoff` / `design-artifact-loop`'s job. If the brief is missing, halt — do not improvise.
- **Does not edit the policy.** Policy changes go through `modify-design-policy`. If synthesis surfaces a policy gap (e.g., >5 proposed tokens), surface it; do not silently extend.
- **Does not enforce values against the running app.** That is `design-implement`'s job (per-screen grid) and `design-review`'s job (post-implementation visual review).
- **Does not run positive-assertion checks for specific values** (row heights, font sizes, etc.). Only contract-critical positive assertions from the allowlist are checked here. Specific-value checks remain in `design-review`.
- **Does not produce a markdown summary of the design.** The brief already exists upstream; the bundle is the design's code-shaped resolution, not a parallel prose spec.
- **Does not invoke `design-implement`.** The handoff line printed at the end of step 7 directs the user; this workflow does not chain.
