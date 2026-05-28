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
- **Do not invent. Do lift.** Inventing defaults is forbidden — never fabricate a `target_slug`, a route, a V-number, or an unchanged region the brief does not state. BUT: if a required frontmatter field is missing AND the brief body authors it unambiguously (e.g., `Route: /expenses` in §1, `screen-review-{slug}-{date}.md` referenced in §6, V1/V2/V3 with explicit region+rationale, a "Do not change" list with named regions), lift the value into the resolved state and record the lift in `{frontmatter_lifts}` for audit. Lifting is structuring; inventing is fabricating. Halt only when the body is silent or ambiguous on the missing field — never bounce the user back for a mechanical copy-paste from §X into the frontmatter.
- **Mode is locked here.** `{mode}` is set from the brief's frontmatter (or inferred per §5b's mode-inference rule) once and never reconsidered. If the brief's `mode` resolves to `refine-screen` but neither frontmatter nor body unambiguously supplies `targeted_changes` AND `unchanged_regions`, halt — refine-screen mode without scope declarations is unsafe (the drift check in step 6c has no baseline).
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
_bmad-output/implementation-artifacts/design-handoff-{slug}-{date}.md
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

### 4a. Validate Brief Revision Provenance

Before parsing the brief's domain frontmatter (§5), validate the **revision provenance** block per `{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md`. A brief that fails validation is unconsumable; halt step-01 (Gate 1 failure) and surface the diagnostic to the user. Do NOT attempt to repair the file — surface and exit.

**Escape hatch:** if the user's invocation includes the literal token `--allow-superseded` AND the brief path was passed explicitly (Shape A), skip Check 3 only. All other checks still run. Never auto-fall-back to `--allow-superseded`.

Run the checks in order; halt on the first failure.

**Check 1 — fields present.** Parse the provenance block. Required fields: `target_slug`, `brief_status`, `revision_mode`, `change_class`, `supersedes`, `superseded_by`, `source_workflow`, `source_run_date`, `last_modified_by`, `last_modified_date`. Empty strings are allowed only for `supersedes` and `superseded_by`. If any field is missing, halt with:

```
Gate 1 — brief provenance: missing field(s) <list>
Brief: {brief_path}
This brief predates the revision policy (or was malformed) and cannot be safely synthesized.
Re-run design-handoff to regenerate it, or back-fill the provenance block per brief-revision-policy.md §7.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md
```

**Check 2 — invariants.** Run the invariants from `brief-revision-policy.md` §2 (items 2–8). Specifically:

- `revision_mode == "workflow_generated"` ⇒ `change_class ∈ {"original", "material_revision"}`
- `revision_mode == "manual_minor_revision"` ⇒ `change_class == "clarification"`
- `change_class == "original"` ⇒ `supersedes` is empty
- `change_class == "material_revision"` ⇒ `supersedes` names an existing file in `{implementation_artifacts}`
- `brief_status == "superseded"` ⇒ `superseded_by` is non-empty
- `revision_mode == "workflow_generated"` ⇒ `last_modified_by == "workflow"` AND `last_modified_date == source_run_date`

Halt on any failure with the specific invariant and the conflicting fields.

**Check 3 — superseded.** If `brief_status == "superseded"`:

```
Gate 1 — brief provenance: refusing to synthesize from a superseded brief.
Brief: {brief_path}
Superseded by: <superseded_by value>
If you really need to synthesize from this older brief (e.g. for audit), pass --allow-superseded explicitly; otherwise switch to the successor.
```

Skipped only when `--allow-superseded` was passed AND the brief path was explicit (Shape A).

**Check 4 — active uniqueness.** Glob `{implementation_artifacts}/design-brief-{this brief's target_slug}-*.md`, parse each match's frontmatter, and count those with `brief_status: active`. (Use the target_slug from this brief's frontmatter; if frontmatter omits it, derive from the filename per the auto-lift rule in §5b — both checks share the same slug.) If more than one match, halt:

```
Gate 1 — brief provenance: active-uniqueness invariant violated for target_slug "<slug>"
  - <path 1>
  - <path 2>
  ...
Exactly one active brief per target_slug is permitted. Fix the predecessor chain
(set brief_status: superseded and superseded_by on the older briefs) and retry.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §2.6
```

**Check 5 — material change with manual revision.** If `change_class == "material_revision"` AND `revision_mode == "manual_minor_revision"`:

```
Gate 1 — brief provenance: forbidden combination (material change + manual revision).
Brief: {brief_path}
A material revision must go through design-handoff. Re-run design-handoff for this feature.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

**Check 6 — workflow-generated brief was hand-edited.** If `revision_mode == "workflow_generated"` AND `last_modified_by == "human"` AND `last_modified_date > source_run_date`:

```
Gate 1 — brief provenance: workflow-generated brief was hand-edited but revision_mode still claims workflow_generated.
Brief: {brief_path}
Either re-run design-handoff (material edit) or update the frontmatter to revision_mode: manual_minor_revision + change_class: clarification (minor edit).
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

**On success**, capture the provenance fields into state for inclusion in the load summary (§10) and the manifest (step-7):

- `{brief_revision_mode}`, `{brief_change_class}`, `{brief_supersedes}`, `{brief_superseded_by}`, `{brief_source_run_date}`, `{brief_last_modified_by}`, `{brief_last_modified_date}`

These flow into `manifest.synthesis.brief_provenance` so downstream tooling (and humans inspecting the bundle) can trace the bundle to the exact brief revision it was synthesized from.

### 5. Parse YAML frontmatter

Extract the frontmatter block between the first two `---` lines. Parse into `{brief_frontmatter}` as a map. Required keys:

- `target_slug` (kebab-case identifier for the feature/flow, e.g., `data-quality`, `avask-vat-reclaim`)
- `mode` (`fresh-design` or `refine-screen`)
- `route` (single route) OR `routes` (list of routes for multi-screen)

For each missing required key, attempt the auto-lift in §5b BEFORE halting. Halt with `brief frontmatter missing required field(s): <list>` only for fields that §5b could not resolve from the body. Report ALL unresolved fields in one halt — do not halt-on-first-miss.

If frontmatter is malformed (parser raises), halt with the parser error and the offending line range. Do not attempt to "repair" the YAML.

### 5b. Auto-lift universal required fields from body (when frontmatter omits them)

Initialize `{frontmatter_lifts} = {}` (map of lifted-field → source-region). For each universal required field missing from `{brief_frontmatter}`, apply the resolution rule below. Lift on unambiguous success; halt on ambiguity or silence.

| Missing field | Resolution rule | Halt if |
|---|---|---|
| `target_slug` | Derive from `{brief_path}` filename: strip prefix (`design-handoff-` / `design-brief-` / `design-response-` / `handoff-`) and the trailing `-{date}.md`. The remainder is the slug. | Filename does not match the prefix-slug-date convention. |
| `mode` | Scan `{brief_frontmatter}` and `{brief_content}` for refine-screen signals: presence of `screen_review_ref`, a body reference to a `screen-review-*.md` artifact, V1/V2/V3 issue blocks tied to a prior review, or explicit "refinement of" / "refine-screen" language in §1 or the design ask. If any are present → `refine-screen`. Otherwise → `fresh-design`. | Body contains BOTH refine-screen and fresh-design signals (e.g., references a screen-review but also says "new screen, no prior implementation"). |
| `route` / `routes` | Search the body for explicit route lines. Patterns: `Route: <pathname>`, `Routes:\n- <pathname>\n- ...`, a "Route" or "Routes" section heading, or a code fence containing `/<segment>/...` lines. Lift the first unambiguous match. Single route → set `route`; multiple → set `routes`. | Body contains no explicit route declaration, OR multiple distinct route candidates without an authoring marker (`Route:`, "Routes:", a section heading) to disambiguate. |

For each successful lift, record in `{frontmatter_lifts}`:

```yaml
{frontmatter_lifts}:
  target_slug: { value: "expenses-ocr-failure-visibility", source: "filename" }
  mode: { value: "refine-screen", source: "body: §6 references screen-review-expenses-ocr-failure-visibility-2026-05-24.md" }
  route: { value: "/expenses", source: "body §1: 'Route: /expenses'" }
```

Mutate `{brief_frontmatter}` in-memory with the lifted values so downstream steps (6, 6a, 7, 8) operate on a complete frontmatter. **Do not write back to disk** — the brief file is upstream's source of truth; lifts are local-to-this-run.

If any required field cannot be lifted per the rule above, append it to the halt list. Emit one combined halt message naming both the unresolved fields AND any failed-lift attempts (so the user sees WHY the lift failed — "found 3 candidate routes, no `Route:` marker to disambiguate").

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

If `{mode} == "refine-screen"`, the brief MUST supply (in frontmatter OR unambiguously in the body):

- `screen_review_ref` — path to the `screen-review-*.md` that scoped this refinement.
- `targeted_changes` — list of regions the bundle is intentionally changing (each with a `region:` name and a `rationale:` tied to a screen-review V-number or brief section).
- `unchanged_regions` — list of regions that must match the prior implementation byte-for-byte (modulo token substitution).

For each missing field, attempt the auto-lift in §8a BEFORE halting. Halt with `refine-screen mode requires screen_review_ref, targeted_changes, and unchanged_regions; could not resolve: <list>` only for fields §8a could not lift.

### 8a. Auto-lift refine-screen required fields from body (when frontmatter omits them)

For each refine-screen required field missing from `{brief_frontmatter}`, apply the resolution rule below. Lift on unambiguous success; halt on ambiguity or silence. Append each lift to the same `{frontmatter_lifts}` map initialized in §5b.

| Missing field | Resolution rule | Halt if |
|---|---|---|
| `screen_review_ref` | Scan body for a path-shaped string matching `screen-review-{target_slug}-*.md` (anywhere — explicit "Source artifact:" line, §6 reference, prose mention). If exactly one matches, lift it. If zero, attempt the latest `screen-review-{target_slug}-*.md` under `{implementation_artifacts}` as a fallback ONLY IF the body explicitly says "based on the most recent review" or equivalent. | Multiple distinct `screen-review-*.md` paths appear in the body without a clear primary; OR zero paths AND no explicit "most recent review" instruction. |
| `targeted_changes` | Extract V-numbered issue blocks from the body. Each must have an identifiable `region:` (named UI surface — "filter bar", "table header", "expanded row drawer") and a `rationale:` (V-number reference like "V1" or "V1, V2" OR a brief-section citation like "§6"). Lift as a list. | Body has V-numbers but no nameable regions per block; OR has region names but no V-number / brief-section anchor (lift without anchor is unsafe — the drift check has no baseline). |
| `unchanged_regions` | Extract from a body list explicitly labeled "Do not change", "Do NOT break", "Preserve", "Unchanged regions", "Keepers", "What to keep", or equivalent. Lift the named regions verbatim. | No such labeled list exists in the body. (Implicit unchanged-regions are unsafe — refine-screen requires explicit scoping.) |

For each successful lift, append to `{frontmatter_lifts}`:

```yaml
{frontmatter_lifts}:
  screen_review_ref: { value: "<path>", source: "body §6: explicit reference" }
  targeted_changes:  { value: [<list>], source: "body §6: V1, V2, V3 blocks with regions+rationales" }
  unchanged_regions: { value: [<list>], source: "body §6: 'Do NOT break' list (8 entries)" }
```

Mutate `{brief_frontmatter}` in-memory with the lifted values. Do not write back to disk.

Project into state (whether from frontmatter or lifted):

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
  provenance:      revision_mode={brief_revision_mode}, change_class={brief_change_class}, last_modified_by={brief_last_modified_by} on {brief_last_modified_date}{; supersedes {brief_supersedes} if non-empty}

Frontmatter lifts (only printed when {frontmatter_lifts} is non-empty):
  - <field>: lifted from <source>
  - <field>: lifted from <source>

Proceeding to step 2: load policy.
```

If `{frontmatter_lifts}` is non-empty, the lifts block MUST appear in the print — the user needs to see which structural decisions came from body-inference rather than explicit frontmatter, so a wrong inference is caught before synthesis runs. If `{frontmatter_lifts}` is empty, omit the block entirely (don't print an empty "Frontmatter lifts:" header).

Then load `step-02-load-policy.md` and follow it.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{baseline_commit}`, `{brief_path}`, `{brief_type}`, `{brief_content}`, `{brief_frontmatter}`
- `{mode}` (synthesis mode), `{page_mode}` (composition mode), `{page_mode_source}` (`frontmatter | inferred | defaulted`)
- `{target_slug}`, `{target_route}` (or null for multi-screen), `{screens}`
- `{feature_purpose}`, `{data_shape}`, `{user_context}`, `{visual_direction}`, `{hard_constraints}`, `{design_ask}`
- `{analytics_structure}` if §4b present, else null
- `{frontmatter_lifts}` — map of `field → {value, source}` for every required field that was lifted from body rather than read directly from frontmatter. Empty map if all required fields were present in frontmatter. Non-empty lifts are not failures, but they ARE structural decisions the bundle's reproducibility hinges on — surface them in the step-10 load summary and (when step-07 is wired to read it) include them in `manifest.synthesis.frontmatter_lifts` for audit. Until step-07 wires this up explicitly, the state variable still exists for downstream introspection.
- Brief revision provenance (populated in §4a; flow into `manifest.synthesis.brief_provenance` via step-07): `{brief_revision_mode}`, `{brief_change_class}`, `{brief_supersedes}`, `{brief_superseded_by}`, `{brief_source_run_date}`, `{brief_last_modified_by}`, `{brief_last_modified_date}`
- In `refine-screen` mode: `{screen_review_ref}`, `{targeted_changes}`, `{unchanged_regions}`

Any unset required variable is a workflow bug — halt before step 2.
