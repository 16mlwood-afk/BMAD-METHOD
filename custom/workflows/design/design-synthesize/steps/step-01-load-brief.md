---
name: 'step-01-load-brief'
description: 'Resolve the brief artifact, parse YAML frontmatter, extract feature/data/visual/constraints/mode/screens. Halt on Gate 1 (brief validity) if the brief is missing or malformed.'
---

# Step 1: Load Brief

**Goal:** Resolve the input handoff/brief artifact, load it into state, and validate that it has the fields downstream steps require. This step is the entry point for the workflow — every other step depends on a valid `{brief_*}` and mode lock.

**Gate owned:** Gate 1 — brief validity (workflow.md §APPROVAL GATES).

---

## RULES

- **Do not generate a brief.** If the brief is missing or malformed, halt. Brief authoring is the upstream workflow's job (`design-handoff` / `design-artifact-loop`).
- **Do not substitute a stale brief.** If the user's input is ambiguous (e.g., they passed a slug that matches three artifacts), halt and ask for the exact path — do not pick the newest and continue.
- **Do not interpret the brief.** The brief is the canonical input; this step's job is to parse it, not to fix it. If a field is missing, halt — do not invent defaults.
- **Mode is locked here.** `{mode}` is set from the brief's frontmatter once and never reconsidered. If the brief's `mode` is `refine-screen` but it lacks `targeted_changes` / `unchanged_regions`, halt — refine-screen mode without scope declarations is unsafe (the drift check in step 6c has no baseline).
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Capture the baseline commit

Record the git SHA before any synthesis work. Stored in state as `{baseline_commit}` and copied into `manifest.synthesis.baseline_commit` in step 7 for reproducibility.

```bash
git rev-parse HEAD
```

If not in a git repository, set `{baseline_commit}` to `"non-git"` and continue — the manifest reproducibility field becomes informational rather than verifiable.

### 2. Resolve the brief path

The user invokes this workflow with one of three input shapes. Resolve each into an absolute `{brief_path}`:

**Shape A — explicit absolute or repo-relative path:**

```
_bmad/bmm/implementation-artifacts/design-handoff-{slug}-{date}.md
```

Check the file exists. If yes, set `{brief_path}` and proceed to step 3. If no, halt with: `brief path not found: <path>`.

**Shape B — slug only (e.g., `design-handoff` or `design-handoff-data-quality`):**

Resolve to the most recent matching artifact under `{implementation_artifacts}`:

```bash
ls -t {implementation_artifacts}/${slug}*.md 2>/dev/null | head -3
```

- If 1 match → set `{brief_path}` and proceed.
- If 0 matches → halt with: `no brief matched slug "<slug>" under {implementation_artifacts}`.
- If 2+ matches → halt with the list and: `slug "<slug>" is ambiguous; pass the full filename`. Do NOT silently pick the newest — slug-as-prefix collisions are common (e.g., `data-quality` matches `data-quality-2026-05-26.md` and `data-quality-2026-05-27.md`).

**Shape C — handoff block:**

The same canonical handoff shape `design-artifact-loop` accepts. The block names a file on `main`. Extract the filename, resolve under `{implementation_artifacts}`, and set `{brief_path}`.

### 3. Classify the brief type

Set `{brief_type}` from the filename prefix:

| Filename prefix | `{brief_type}` |
|---|---|
| `design-handoff-*.md` | `design-handoff` |
| `design-brief-*.md` | `design-brief` |
| `design-response-*.md` | `design-response` |
| `handoff-*.md` (legacy) | `design-handoff` |

If the prefix doesn't match any of the above, halt with: `brief filename does not match a known prefix: <filename>`. Synthesizing from an arbitrary markdown file is unsupported — the upstream contract is unclear.

### 4. Load the brief contents

Read the entire file into `{brief_content}`. Use the Read tool (not `cat`) so the harness tracks the read.

### 5. Parse YAML frontmatter

Extract the frontmatter block between the first two `---` lines. Parse into `{brief_frontmatter}` as a map. Required keys:

- `target_slug` (kebab-case identifier for the feature/flow, e.g., `data-quality`, `avask-vat-reclaim`)
- `mode` (`fresh-design` or `refine-screen`)
- `route` (single route) OR `routes` (list of routes for multi-screen)

If any required key is missing, halt with: `brief frontmatter missing required field(s): <list>`. Report ALL missing fields in one halt — do not halt-on-first-miss; the user should fix them in one pass.

If frontmatter is malformed (parser raises), halt with the parser error and the offending line range. Do not attempt to "repair" the YAML.

### 6. Project frontmatter into state

| Frontmatter field | State variable | Notes |
|---|---|---|
| `target_slug` | `{target_slug}` | Used in `{bundle_dir}` naming |
| `mode` | `{mode}` | Synthesis mode (`fresh-design | refine-screen`), locked here; never reconsidered |
| `page_mode` | `{page_mode}` | Page composition mode (`operational | analytical | detail`), see §6a below |
| `route` | `{target_route}` | Single-screen runs only |
| `routes` | `{target_route}` = null, `{screens}` derived from `routes` | Multi-screen runs |

### 6a. Resolve `{page_mode}` (Gate 1 requirement — policy §6 / §7)

`{page_mode}` declares the page's composition contract:

- **`operational`** — table-first work surface. Filter bar, dense rows, status hierarchy. Policy §6.
- **`analytical`** — chart-led composition with drill-down evidence. No card-grid openers. Policy §6.
- **`detail`** — drawer or full-page extension of an operational list. Same surface, typography, badges as its parent operational list. Forbids KPI cards / charts. Policy §7.

**Resolution order:**

1. **Explicit declaration:** if `brief_frontmatter.page_mode` is set to `operational`, `analytical`, or `detail`, use it as-is.
2. **Inference from brief body** (only when frontmatter omits it): scan `{design_ask}`, `{feature_purpose}`, `{data_shape}` for signals:
   - Operational signals: "worklist", "queue", "filter bar", "table of X", "operator workflow", "review", "approve", "reconcile".
   - Analytical signals: "trend", "summary", "dashboard", "KPI", "comparison across periods", "chart", "drill-down".
   - Detail signals: brief opens with "drawer", "detail view", "edit modal for an existing list row", and the route shape is `/parent/[id]` or `/parent/[id]/drawer`.
3. **Ambiguity tiebreaker:** if the brief describes BOTH table-first work AND analytics surfaces without a clear primary, default to `operational` per policy §6 ("hybrid pages default to operational").
4. **Unresolvable:** if none of the above produces a single mode, **halt** with Gate 1: `page_mode could not be resolved. Add page_mode: operational | analytical | detail to the brief frontmatter. See policy §6 / §7 for the composition contracts behind each mode.`

Store the resolved value as `{page_mode}` AND record HOW it was resolved (`source: "frontmatter" | "inferred" | "defaulted"`) for the manifest's audit trail.

**Reject invalid values:** if the frontmatter declares anything other than `operational | analytical | detail`, halt with Gate 1 — do not coerce a misspelling or invent a synonym.

### 7. Derive the screens list

`{screens}` is the ordered list of screen names the bundle will contain. One `<screen>.html` is emitted per entry.

**Single-screen brief (has `route`):**

Set `{screens} = ["main"]` unless the frontmatter specifies a custom `screen_name`. Single-screen bundles emit `bundle/main.html` by default.

**Multi-screen brief (has `routes`):**

Derive each screen name from the route's last meaningful segment. If the brief specifies `screens:` explicitly as an ordered array, use that instead. Example:

```yaml
routes:
  - /reclaim/avask
  - /reclaim/avask/[id]
  - /reclaim/avask/[id]/drawer
screens: [list, detail, drawer]
```

If `screens` is omitted, derive: `[list, detail, drawer]` from `[/.../avask, /.../avask/[id], /.../avask/[id]/drawer]`. Halt if the derived names collide (e.g., two routes both reduce to `list`).

### 8. Refine-screen mode validation

If `{mode} == "refine-screen"`, the brief MUST contain:

- `screen_review_ref` — path to the `screen-review-*.md` that scoped this refinement.
- `targeted_changes` — list of regions the bundle is intentionally changing (each with a `region:` name and a `rationale:` tied to a screen-review V-number or brief section).
- `unchanged_regions` — list of regions that must match the prior implementation byte-for-byte (modulo token substitution).

If any of these is missing, halt with: `refine-screen mode requires screen_review_ref, targeted_changes, and unchanged_regions in frontmatter; missing: <list>`.

Project into state:

| Frontmatter field | State variable |
|---|---|
| `screen_review_ref` | `{screen_review_ref}` |
| `targeted_changes` | `{targeted_changes}` |
| `unchanged_regions` | `{unchanged_regions}` |

`{prior_impl_paths}` is resolved in step 3 (frontend context) — it depends on framework detection.

### 9. Extract brief body sections

The brief body is structured prose. Extract the following sections into state for use in step 4. Section headings are by convention; tolerate small variations (`§4 Visual Direction` ≈ `## Visual direction`):

| Section | State variable | Source-of-truth role |
|---|---|---|
| Feature purpose / overview | `{feature_purpose}` | What the screen is for; informs information hierarchy in step 4 |
| Data shape / data model | `{data_shape}` | What fields exist; populates realistic content (no lorem ipsum) |
| User context / who needs it | `{user_context}` | Decides density and surfacing — analyst vs operator vs auditor |
| Visual direction | `{visual_direction}` | Palette/density/tone cues — feeds palette decisions in step 4 |
| Hard constraints | `{hard_constraints}` | Project-specific musts (e.g., "fits in 1440px viewport without horizontal scroll") |
| Design ask | `{design_ask}` | The deliverable scope — what regions/components the brief requires |
| Analytics structure (§4b if present) | `{analytics_structure}` | Subordinate analytics-row spec, if the brief includes one |

If a section is missing AND it is required for the mode:

- `fresh-design`: all sections except `analytics_structure` are required.
- `refine-screen`: `feature_purpose`, `data_shape`, `design_ask` are required; the rest are inherited from the screen-review baseline.

Halt with the missing-section list. Do not invent content.

### 10. Print the load summary and proceed

Print to the user (one block, concise):

```
✓ Brief loaded:
  path:            {brief_path}
  type:            {brief_type}
  slug:            {target_slug}
  synthesis mode:  {mode}
  page mode:       {page_mode}  (resolved from {page_mode_source})
  screens:         [{screens, comma-separated}]
  routes:          [{routes, comma-separated}]
  refine baseline: {screen_review_ref or "n/a"}

Proceeding to step 2: load policy.
```

Then load `step-02-load-policy.md` and follow it.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{baseline_commit}`, `{brief_path}`, `{brief_type}`, `{brief_content}`, `{brief_frontmatter}`
- `{mode}` (synthesis mode), `{page_mode}` (composition mode), `{page_mode_source}` (`frontmatter | inferred | defaulted`)
- `{target_slug}`, `{target_route}` (or null for multi-screen), `{screens}`
- `{feature_purpose}`, `{data_shape}`, `{user_context}`, `{visual_direction}`, `{hard_constraints}`, `{design_ask}`
- `{analytics_structure}` if §4b present, else null
- In `refine-screen` mode: `{screen_review_ref}`, `{targeted_changes}`, `{unchanged_regions}`

Any unset required variable is a workflow bug — halt before step 2.
