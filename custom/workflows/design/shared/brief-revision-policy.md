---
name: brief-revision-policy
description: 'Canonical policy for how design briefs may be revised. Defines the minor/material split, the provenance frontmatter contract, the editing rules, and the halt conditions consumer workflows enforce at intake. Referenced by design-handoff (producer) and design-artifact-loop / design-synthesize (consumers). §8 adds tolerant supersede-awareness for the non-consumer downstream pair design-ingest / design-implement (stamp + explain, never refuse).'
---

# Design Brief Revision Policy

**Why this exists.** A design brief is the durable contract between the engineer who described the feature and every downstream design / synthesis / implementation run. When a brief drifts silently — a hand-edit that changes scope, a clarification that quietly tightens a constraint, a stale brief that a consumer picks up without realising a newer one exists — the rot propagates into every artifact derived from it (design-handoff, design-response, screen-review, design-implement). Catching drift at the brief is the cheapest place to fix it.

This policy is intentionally light. Briefs are markdown and humans will edit them; the goal is to make legitimate edits cheap and illegitimate ones halt loudly, not to gate every edit behind a workflow.

---

## 1. Two classes of changes

Every change to a brief falls into one of two classes. The class determines whether a hand-edit is allowed.

### Minor revision — hand-edit allowed

- Wording clarity, typo fixes, punctuation, formatting cleanup.
- Pagination / phrasing cleanup that does not change meaning.
- Explicit restatement of a decision already made elsewhere (e.g., the policy was tightened upstream and the brief is being brought into line with the new wording).
- Changelog-only edits.

A minor revision must NOT change scope, add/remove views, change hierarchy goals, change the interaction model, change constraints, or alter the questions in §6 (Design Ask). If any of those move, it is not minor.

### Material revision — must re-run `design-handoff`

- Scope changes (adding or removing features, surfaces, or screens within the feature).
- Added or removed views.
- Changed hierarchy or layout goals.
- Changed interaction model.
- New constraints (or removed constraints).
- Anything likely to alter downstream design output — if a synthesizer would have produced a different layout under the new brief, the change is material.

Material revisions produce a **new brief file** via `design-handoff`. The old brief is marked `superseded`; the new brief sets `supersedes` to the old filename. Hand-editing a brief into a material revision is forbidden by this policy and consumer workflows halt on the combination.

**Test for which class a change is.** Read the diff. If a downstream synthesizer or implementer would produce a meaningfully different output from the new text than from the old text — it is material. If the output would be identical and only the reader experience improves — it is minor.

---

## 2. Frontmatter contract

Every brief carries **two named blocks** in its YAML frontmatter, in addition to whatever feature-level fields the workflow already requires (`type`, `feature`, `scope`, `date`, `author`, `status`):

- **Block A — Provenance** (11 fields). Tracks brief lifecycle: identity, status, predecessor chain, who/when last touched.
- **Block B — Content** (mode-dependent). Tracks what the brief contains: handoff mode, page mode, route, composition, the **structural contract** the bundle→implement conformance gate diffs against (`frames`, `shell_role` — `design-implement` step-01 §SHARED.1b), source diagnostic, and (in refine-screen mode) the targeted-changes / unchanged-regions / deferred-violations breakdown.

Both blocks are validated by consumers at intake. Missing a required field in either block halts consumption.

```yaml
---
# Block A — Provenance (always required)
target_slug: my-feature                  # kebab-case identifier; doubles as the active-uniqueness key. For refine-screen runs, prefix with "refine-".
brief_status: active                     # active | superseded
revision_mode: workflow_generated        # workflow_generated | manual_minor_revision | spec_derived
change_class: original                   # original | clarification | material_revision
supersedes:                              # filename of the brief this one replaces (null/empty if original)
superseded_by:                           # filename of the brief that replaced this one (null/empty until superseded)
source_workflow: design-handoff
source_run_date: 2026-05-27
policy_version_required: 0               # version of docs/design-policy.md this brief was authored against (its frontmatter `version:`; 0 if no policy). Consumers halt/warn when the current policy version exceeds this. Absent ⇒ treated as 0 (§2 invariant 1a).
last_modified_by: workflow               # workflow | human
last_modified_date: 2026-05-27

# Block B — Content (always required; refine-screen mode adds more)
mode: fresh-design                       # fresh-design | refine-screen
page_mode: operational                   # operational | analytical | detail
route: /my-feature                       # the primary route this brief targets
composition_provenance: policy-default   # policy-default | recommended-alt — does the page-mode's default composition fit the job? (design-handoff §5a)
composition: worklist                    # machine-readable composition key the bundle→implement gate diffs against (design-implement §SHARED.1b check 3). Default = the page-mode default (operational→worklist | analytical→chart-led | detail→record-view); a recommended-alt sets the named job-fit key (scanner-terminal | single-item-stream | source-co-present | source-mirror | …). A non-default key means the gate verifies the bundle expresses the JOB LOOP, not a hero card. (source-mirror is the faithful-source-mirror archetype — render source rows verbatim at fidelity; §13 expand-in-context is suppressed, canonical identifiers are scan/trace anchors not lookup-drawer targets. It is always composition_provenance: recommended-alt — a mirror is NOT the operational worklist default.)
band_provenance: none                    # inherited | recommended-new | recommended-drop | none
analytics_archetype:                     # required iff band_provenance ∈ {inherited, recommended-new}; omit otherwise
frames: [my-feature]                     # machine-readable list of the §7 Surface Inventory contract-key ids (mirrors the §7 table rows; never empty — ≥ the primary frame). Gate check 1 diffs the bundle's DRAWN frames against this list.
shell_role:                              # the page-shell & role contract. REQUIRED when the app has >1 role/shell (clerk vs owner); OMIT the block for a single-role app. forbidden_chrome is load-bearing — gate check 2 + design-implement §2d enforce it.
  required_shell: clerk                  # layout / route-group the surface MUST render under
  required_chrome: "clerk header + role chip"   # chrome this surface MUST carry (verbatim where drawn)
  forbidden_chrome: "owner global nav"   # chrome that MUST NOT appear; an ancestor injecting it over the surface is a Tier-1 violation

# Block B (refine-screen mode only — required when mode == refine-screen)
screen_review_ref:                       # relative path to the consumed screen-review-*.md artifact
targeted_changes:                        # list of regions this round will touch, each with rationale tied to a V-ID
  - region: <name>
    rationale: "V1 — <one-line summary of the fix>"
collapse_note:                           # optional; required iff two V-IDs were collapsed per the design-handoff "Collapse allowance"
unchanged_regions:                       # list of regions this round explicitly preserves; refine-screen must NOT touch them
  - region: <name>
    note: "<one-line reason this region is protected>"
deferred_violations:                     # V-IDs from the artifact that are NOT addressed in this brief and the reason
  - V4: "<why deferred>"
---
```

### Field semantics — Block A (Provenance)

| Field | Allowed values | Meaning |
|---|---|---|
| `target_slug` | kebab-case identifier | Active-uniqueness key. For refine-screen runs, prefix with `refine-`. |
| `brief_status` | `active`, `superseded` | Only one `active` brief per `target_slug` is permitted. Consumers refuse to consume a `superseded` brief unless the user explicitly cites its filename. |
| `revision_mode` | `workflow_generated`, `manual_minor_revision`, `spec_derived` | How the current file state came to be. `workflow_generated` means produced (or last produced) by `design-handoff` reading built code; `manual_minor_revision` means a human hand-edited the file after generation; `spec_derived` means produced by the `design-handoff` **greenfield** path (executed by hand or agent from `docs/design-policy.md` + schema docs + UX/architecture specs, because no built code exists yet — see `design-handoff/GREENFIELD-BRIEF-DERIVATION.md`). `spec_derived` is the honest slot for a greenfield original: it is neither an automated workflow run (`workflow_generated`) nor a minor edit of a predecessor (`manual_minor_revision`). When the greenfield branch is later codified into `design-handoff` step-01, those briefs revert to `workflow_generated`. |
| `change_class` | `original`, `clarification`, `material_revision` | What kind of change this file represents relative to its predecessor. `original` = first brief for the feature (greenfield originals use `original` too — the production method is recorded by `revision_mode`, not here). `clarification` = minor revision. `material_revision` = re-generation triggered by a scope/intent change. |
| `supersedes` | filename, or empty | Set when this brief replaces a prior brief on the same feature. Filename only, not a full path. |
| `superseded_by` | filename, or empty | Set on the **older** brief (retroactively) when a newer brief takes over. Pairs with the newer brief's `supersedes`. |
| `source_workflow` | `design-handoff` | The workflow that generated this brief. Reserved for future workflows that may also emit briefs. |
| `source_run_date` | ISO date | When `source_workflow` last produced this file. Never updated by a minor revision. |
| `policy_version_required` | integer (`0` if no policy) | Version of `docs/design-policy.md` the brief was authored against (its frontmatter `version:`). Consumers (`design-synthesize`, `design-implement`) MUST halt or warn when the current policy version exceeds this — rules ratified after the brief may invalidate its assumptions. Stamped by `design-handoff` step-03 from the policy resolved in step-01. Absent ⇒ treated as `0` (§2 invariant 1a backward-compat). |
| `last_modified_by` | `workflow`, `human` | The hand that touched the file most recently. |
| `last_modified_date` | ISO date | When the file was last written, regardless of by whom. |

### Field semantics — Block B (Content)

| Field | Allowed values | Required in | Meaning |
|---|---|---|---|
| `mode` | `fresh-design`, `refine-screen` | every brief | Which handoff mode produced this brief. Refine-screen briefs are bounded; fresh-design briefs are open creative scope. |
| `page_mode` | `operational`, `analytical`, `detail` | every brief | The kind of work the surface supports (process records / analyse / read-one-record). Names the page-mode default composition; whether that default is actually used is governed by `composition_provenance`. Drives §4a / §4b inclusion in the brief body. |
| `composition_provenance` | `policy-default`, `recommended-alt` | every brief | WHETHER the page-mode's DEFAULT composition (operational→table-first worklist; analytical→chart-led; detail→record-view) fits THIS surface's job — decided from the job, NOT inherited from the policy default or the legacy render (design-handoff §5a). `recommended-alt` means the default was rejected and §4a names the job-fit composition instead (e.g. a pull-based dispensing queue that wants a single-item decision surface, not a table+drawer); like `recommended-new` it is a net-scope/IA recommendation that must have been veto-surfaced to the user. It does NOT change `page_mode`. Consumers currently read the §4a body for the composition; the field is the auditable hook (and future `design-review-pr` enforcement target). |
| `composition` | kebab key — `worklist`, `chart-led`, `record-view` (the page-mode defaults), or a `recommended-alt` name (`scanner-terminal`, `single-item-stream`, `source-co-present`, `source-mirror`, …) | every brief | Machine-readable composition the `design-implement` bundle→implement gate (step-01 §SHARED.1b check 3) and `design-synthesize` step-06 (h) diff against. Default = the page-mode default; a non-default key means the surface is a station/stream/verify/mirror whose JOB LOOP must be expressed, not a hero card. The vocabulary is **open** — consumers branch on "non-default key", not a closed allowlist. `source-mirror` is the **faithful-source-mirror** archetype (a raw-records surface): render the source rows verbatim at fidelity; **§13 expand-in-context is suppressed** — canonical identifiers are scan/trace anchors, NOT lookup-drawer targets, so `design-handoff` §3a/§5f/§7 must NOT spawn lookup-drawer frames for them. A `source-mirror` brief is always `composition_provenance: recommended-alt` (a mirror is not the operational `worklist` default). The auditable form of `composition_provenance` + §4a. |
| `route` | pathname string | every brief | The primary route this brief targets. Used by downstream consumers to verify the brief and the implementation target line up. Together with `surface_part` (route-normalised) and `mode` it forms the **surface identity** that keys the active-uniqueness invariant (§2 invariant 6). |
| `surface_part` | kebab string, or empty | every brief (absent ⇒ `""`) | The sub-surface within `route` this brief targets — a tab / section / panel that lives inside a page (e.g. `raw-records` for a raw-records tab on the ingestion-run view). Empty (`""`) when the brief targets the route's whole primary surface. A §13 expand-in-context lookup drawer is NOT a surface and never carries a `surface_part`. Part of the surface identity (with `route` + `mode`) — see invariant 6. |
| `frames` | list of contract-key ids (the §7 Surface Inventory rows) | every brief | Machine-readable mirror of the §7 frame names. The bundle→implement gate (check 1) diffs the bundle's DRAWN frames against this list; never empty (≥ the primary frame). Identical ids to the §7 table — kept in sync. |
| `shell_role` | `{required_shell, required_chrome, forbidden_chrome}` object | iff the app has a role/shell distinction (clerk vs owner) | The page-shell & role contract. `forbidden_chrome` is load-bearing — gate check 2 + `design-implement` §2d flag an ancestor layout injecting it over the surface (the owner-nav-on-a-clerk-station case) as Tier-1. Omitted for single-role apps. |
| `band_provenance` | `inherited`, `recommended-new`, `recommended-drop`, `none` | every brief | WHY an analytics band exists (or doesn't), decided by the feature's data + user job — **not** by the legacy render. `recommended-new`/`recommended-drop` are net-scope changes that must have been veto-surfaced to the user. Drives §4b inclusion: present iff `inherited` or `recommended-new`. Keeps `design-handoff`'s blank-canvas mandate auditable. |
| `analytics_archetype` | `trend`, `distribution`, `composition`, `ranking`, `coverage`, `flow`, `waterfall`, `single-metric`, `correlation` | iff `band_provenance` ∈ {inherited, recommended-new} | The *shape* of the analytics band, selected from the user's question (see `analytics-archetypes.md`). Omitted entirely when there is no band. Downstream consumers (design-synthesize, design-review-pr) read it to verify the band's form matches its stated archetype. |
| `screen_review_ref` | relative path to `screen-review-*.md` | refine-screen only | The diagnostic artifact this refinement brief was generated from. Consumers re-resolve violation references against the cited artifact. |
| `targeted_changes` | list of `{region, rationale}` objects | refine-screen only | Which regions of the screen the refinement will touch. Each rationale must cite the V-ID(s) from the artifact that justify the touch. |
| `collapse_note` | free text | required iff a Vx+Vy collapse occurred (see design-handoff "Collapse allowance") | One-line statement of which V-IDs were collapsed and which design-requiring violation was promoted in their place. |
| `unchanged_regions` | list of `{region, note}` objects | refine-screen only | Page regions this round must NOT touch. The refinement brief uses this to make the "do not break" contract machine-readable in addition to the body's prose. |
| `deferred_violations` | list of `V<N>: <reason>` entries | refine-screen only when the artifact has V4+ entries the brief does not address | V-IDs not in scope this round and the reason (severity, mechanical-only, IA decision deferred, etc.). Empty list is permitted; the field itself must be present. |

### Invariants

A brief is **valid** iff all of the following hold. Consumers reject briefs that violate any of them.

1. **Field completeness — Block A.** All eleven Block-A fields are present. Empty strings are allowed only for `supersedes` and `superseded_by`.
1a. **Field completeness — Block B.** `mode`, `page_mode`, `route`, `composition_provenance`, `composition`, `frames`, and `band_provenance` are present in every brief (`frames` is never empty — ≥ the primary frame). `shell_role` is present iff the app has a role/shell distinction (clerk vs owner), omitted otherwise. `analytics_archetype` is present iff `band_provenance` ∈ {`inherited`, `recommended-new`} and absent otherwise. When `mode: refine-screen`, the additional fields `screen_review_ref`, `targeted_changes`, `unchanged_regions`, and `deferred_violations` are also present (the latter may be an empty list but the key must exist). `collapse_note` is conditional — required iff a collapse occurred, absent otherwise. **Backward compatibility:** a brief authored before the analytics-archetype contract (no `band_provenance` key) is interpreted as `band_provenance: none`, and a brief authored before the composition-fit contract (no `composition_provenance` key) is interpreted as `composition_provenance: policy-default` — consumers MUST treat each absent field as its default rather than halting, the same way an absent `policy_version_required` defaults to `0`. **Likewise, a brief authored before the structural-contract fields (no `composition` / `frames` / `shell_role` / `surface_part` keys) is interpreted as `composition`: the page-mode default, `frames`: UNVERIFIED (the `design-implement` bundle→implement gate discloses, never halts), `shell_role`: absent, `surface_part`: `""` (the whole-route primary surface) — consumers degrade gracefully and NEVER halt on their absence** (the gate only bites on a present contract; a missing one is disclosed, per the SP-API lesson). New briefs from `design-handoff` always emit `composition` + `frames` + `surface_part` (and `shell_role` when the app is multi-role).
2. **Workflow-generated or spec-derived ⇒ original or material.** `revision_mode ∈ {workflow_generated, spec_derived}` requires `change_class ∈ {original, material_revision}`. Neither a workflow-generated nor a spec-derived brief can be a `clarification` (a clarification is a hand-edit, which is `manual_minor_revision` per invariant 3).
3. **Manual ⇒ clarification only.** `revision_mode: manual_minor_revision` requires `change_class: clarification`. A hand-edited brief MUST NOT carry `change_class: material_revision` — that combination is the forbidden case (see §3).
4. **Original ⇒ no predecessor.** `change_class: original` requires `supersedes` to be empty.
5. **Material revision ⇒ predecessor.** `change_class: material_revision` requires `supersedes` to name an existing prior brief on the same feature.
6. **Active uniqueness (per surface).** For a given **surface identity** — `normalise(route)` + `surface_part` (absent ⇒ `""`), evaluated within one `mode` — at most one brief in `{implementation_artifacts}` may have `brief_status: active` at any time. Uniqueness is keyed on the **surface, NOT on `target_slug`**: two differently-named slugs that target the same surface are a violation (the slug-EXACT collision class — see `docs/fork-gaps.md`). When a new active brief is written, the predecessor's `brief_status` flips to `superseded` and its `superseded_by` is set in the same edit. (`normalise(route)` = `route` lower-cased, trailing `/` stripped, dynamic segments left verbatim. fresh-design and refine-screen briefs on one route are deliberately distinct surfaces — the `mode` scoping keeps them apart.)
7. **Superseded ⇒ pointer set.** A brief with `brief_status: superseded` must have `superseded_by` naming the successor. (Together with §6, this gives a navigable chain.)
8. **Workflow-generated / spec-derived ⇒ matching `last_modified_*`.** If `revision_mode: workflow_generated`, then `last_modified_by: workflow` and `last_modified_date == source_run_date`. If `revision_mode: spec_derived`, then `last_modified_by: human` (the recipe is hand/agent-driven, not an automated workflow run) and `last_modified_date == source_run_date`. In both cases a later genuine human edit must flip `revision_mode` to `manual_minor_revision` + `change_class: clarification` (per §3); a `workflow_generated`/`spec_derived` brief that silently claims a later edit is a contract bug.

---

## 3. Editing rules

### When a hand-edit IS allowed

A human may edit a brief directly on disk **only** when the change is a minor revision per §1. The edit must:

1. Preserve the filename (do not rename — pure minor revisions are not new brief files).
2. Set `revision_mode: manual_minor_revision`.
3. Set `change_class: clarification`.
4. Update `last_modified_by: human` and `last_modified_date` to the current ISO date.
5. Leave `source_workflow`, `source_run_date`, and `supersedes` untouched.
6. Append a one-line entry to the brief's `## Changelog` section at the bottom of the body. Create the section if it doesn't exist. Format:

   ```
   - YYYY-MM-DD — {one-line description of the clarification}. Author: {name}.
   ```

The changelog is human-readable provenance and is the only place a hand-edit narrates *why*. The frontmatter records the *what*.

### When a hand-edit is FORBIDDEN

Hand-editing a brief into a material revision (per §1) is forbidden. The legitimate flow is:

1. Re-run `design-handoff` with the new intent. It writes a fresh file with a new date and `change_class: material_revision`.
2. The new brief's `supersedes` names the prior brief's filename.
3. The prior brief's `brief_status` flips to `superseded` and its `superseded_by` is set. `design-handoff` performs this edit on the predecessor as part of step-03 (see Producer rules below).

If `design-handoff` cannot run (e.g. the user only has the markdown file and no working repo), the user must still manually replicate the same shape: write a new file with the new date, set `change_class: material_revision` and `supersedes`, flip the predecessor's `brief_status` to `superseded` and set `superseded_by`. Consumers will accept this — it satisfies every invariant in §2 — but the user is doing by hand what the workflow exists to automate.

### What "material" really means in practice

Most edits people *think* are minor are actually minor. The most common material edits are:

- Adding or removing an entry from the brief's data model (§2) — design will hang information off that entity.
- Changing the design ask questions (§6) — different questions produce different designs.
- Changing `page_mode` (`operational` ↔ `analytical` ↔ `detail`) — these have different composition contracts.
- Flipping `composition_provenance` (`policy-default` ↔ `recommended-alt`), or changing the named job-fit composition in §4a — the primary composition is the spine the whole design hangs off; changing it is at least as material as changing `page_mode`.
- Adding or removing the analytics band (`band_provenance` to/from `none`), or changing `analytics_archetype` — the band's presence and shape are composition decisions; design hangs a whole layer off them.
- Changing the `routes` list — that's a different feature surface.
- Adding or removing a hard constraint in §5.
- Materially rewriting the user context (§3) in a way that would change density / register / urgency choices.

When in doubt, re-run `design-handoff`. It is cheaper than a downstream chain that synthesised against a stale brief.

---

## 4. Producer rules (design-handoff)

`design-handoff` is the only workflow that emits briefs (today). At brief-write time, step-03 must:

1. **Populate the full provenance block** per §2.
2. **Decide `change_class`** by checking `{implementation_artifacts}` for a prior **active** brief on the **same surface** — same surface identity (`normalise(route)` + `surface_part`, within `mode`), **NOT** same `target_slug` (see invariant 6 and `step-03-generate-brief.md` §1a):
   - Zero same-surface actives → `change_class: original`, `supersedes: <empty>`.
   - Exactly one, **same** `target_slug` → `change_class: material_revision` (`design-handoff` is being re-run on the same surface; by definition this is material — minor revisions don't go through this workflow). Set `supersedes: <predecessor filename>`.
   - Exactly one, **different** `target_slug` → halt: a different-slug active brief already targets this surface (the slug-EXACT collision class — `docs/fork-gaps.md`). Reconcile deliberately — supersede it and re-run, or align the slugs — never auto-supersede across slugs.
   - Two or more → halt and surface to the user: the active-uniqueness invariant (invariant 6) is already broken, fix it before generating a new brief. (This indicates a previous run failed mid-write.)
3. **Flip the predecessor** in the same step when `change_class: material_revision`: edit the prior brief's frontmatter to set `brief_status: superseded` and `superseded_by: <this filename>`. This is the only edit `design-handoff` makes to an existing file.
4. **Set `revision_mode: workflow_generated`**, `last_modified_by: workflow`, and `last_modified_date == source_run_date == {date}`.
5. **Cite this policy** in the brief's "For Claude Design" / handoff intro block, with a one-liner: "Revision provenance follows `brief-revision-policy.md` in the shared design workflow docs."

**Greenfield (spec-derived) path.** When `design-handoff` cannot read built code (a surface declared in `docs/design-policy.md` / specs but not yet implemented), its greenfield path — `design-handoff/GREENFIELD-BRIEF-DERIVATION.md`, run by hand or agent — emits the same provenance block with `revision_mode: spec_derived`, `last_modified_by: human`, and the same `change_class` / `supersedes` logic as item 2 above (predecessor lookup is unchanged: zero matches → `original`, one → `material_revision`). This is the honest declaration for a greenfield original; it satisfies invariants 2 and 8. Once the greenfield branch is codified into step-01, those briefs revert to `workflow_generated`.

---

## 5. Consumer rules (design-artifact-loop, design-synthesize)

Any workflow that consumes a brief must, at intake, validate the provenance frontmatter and halt on invalid combinations BEFORE running the rest of the workflow. The validation order is deterministic:

### Check 1 — fields present
Parse the frontmatter. Halt if any required field is missing.

**Required from Block A (Provenance):** all 11 fields listed in §2 (`target_slug` plus the 10 provenance fields).

**Required from Block B (Content):**
- Always: `mode`, `page_mode`, `route`.
- When `mode: refine-screen`: also `screen_review_ref`, `targeted_changes`, `unchanged_regions`, `deferred_violations`. `collapse_note` is conditional (required only if the brief collapsed two V-IDs per the design-handoff "Collapse allowance").

Halt diagnostic:

```
Brief frontmatter missing required field(s): <comma-separated list>.
Brief: <path>
Block A (Provenance) missing: <list, or "none">
Block B (Content) missing:    <list, or "none">

This brief predates the current revision policy or was generated by a workflow
that has not migrated to the Block A + Block B contract. It cannot be safely
consumed.

Re-run design-handoff to regenerate it under the current contract.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §2
```

### Check 1b — field values in-enum
Halt if any closed-enum field carries a value outside its allowed set (§2 field-semantics tables). This runs BEFORE Check 2 because the invariants in Check 2 are conditionals keyed on valid enum values — an out-of-enum value (e.g. a hand-authored brief stamped `revision_mode: hand_authored`, `change_class: new_surface`) fires none of them and would otherwise slip through unvalidated. Closed enums:

- `brief_status ∈ {active, superseded}`
- `revision_mode ∈ {workflow_generated, manual_minor_revision, spec_derived}`
- `change_class ∈ {original, clarification, material_revision}`
- `last_modified_by ∈ {workflow, human}`
- `mode ∈ {fresh-design, refine-screen}`
- `page_mode ∈ {operational, analytical, detail}`
- `composition_provenance ∈ {policy-default, recommended-alt}`
- `band_provenance ∈ {inherited, recommended-new, recommended-drop, none}`
- `analytics_archetype ∈ {trend, distribution, composition, ranking, coverage, flow, waterfall, single-metric, correlation}` (only when present)

`composition` is **deliberately NOT enum-validated** — it is an open vocabulary (the page-mode defaults plus any named `recommended-alt` such as `scanner-terminal` / `source-mirror` / …); consumers branch on "non-default key", not a closed allowlist. Validate only that it is a non-empty kebab string.

Halt diagnostic:

```
Brief field value(s) outside the allowed enum:
  <field>: "<value>" — allowed: <set>
Brief: <path>

This brief carries a value the contract does not define. It was likely hand-authored
against an invented vocabulary. Re-stamp it to a contract value (see the §2 field-semantics
tables) before it can be consumed — out-of-enum values are rejected, not silently tolerated.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §2
```

### Check 2 — invariants
Run §2 invariants 2 through 8 against the parsed frontmatter. If any invariant fails, halt with a diagnostic naming the specific invariant and the conflicting fields. Do not attempt to "fix" the file — surface to the user.

### Check 3 — superseded
If `brief_status: superseded`, halt:

```
Refusing to consume a superseded brief.
Brief: <path>
Superseded by: <superseded_by value>
If you really need to consume the older brief, pass its filename explicitly with --allow-superseded; otherwise switch to the successor.
```

The `--allow-superseded` escape hatch is for narrow audit cases (e.g., "what did we tell the designer two weeks ago"). It is not a default and consumers must require the explicit flag — never auto-fall-back.

### Check 4 — active uniqueness (per surface)
Compute THIS brief's surface identity — `normalise(route)` + `surface_part` (absent ⇒ `""`), within its `mode`. Scan ALL `design-brief-*.md` in `{implementation_artifacts}`, parse each one's frontmatter, and list those with `brief_status: active` whose surface identity matches. If more than one is found (including this brief), halt:

```
Active-uniqueness invariant violated for surface "<normalised_route>[#<surface_part>]" (mode <mode>):
  - <path 1>  (target_slug: <slug 1>)
  - <path 2>  (target_slug: <slug 2>)
  - ...
Exactly one active brief per surface is permitted — uniqueness is keyed on the
route-normalised surface, not the filename slug, so two differently-named slugs
targeting one surface is a violation. Fix the predecessor chain (set
brief_status: superseded and superseded_by on the older briefs) and retry.
```

(`normalise(route)` = `route` lower-cased, trailing `/` stripped, dynamic segments verbatim. A brief with no `surface_part` key is treated as `surface_part: ""` — the whole-route surface.)

### Check 5 — material change with manual revision
If `change_class: material_revision` AND `revision_mode: manual_minor_revision`, halt:

```
Forbidden combination: material change with manual revision.
Brief: <path>
A material revision must go through design-handoff (which sets revision_mode: workflow_generated).
Re-run design-handoff for this feature; do not hand-edit a brief into a material revision.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

### Check 6 — manual edit on a workflow-generated brief (advisory)
If `revision_mode: workflow_generated` AND `last_modified_by: human` AND `last_modified_date > source_run_date`, this is the "someone hand-edited a workflow brief but didn't flip revision_mode" case. Halt:

```
Brief was hand-edited after workflow generation, but revision_mode still claims workflow_generated.
Brief: <path>
Either re-run design-handoff (if the edit was material), or update the frontmatter
(if the edit was a minor revision: set revision_mode: manual_minor_revision and change_class: clarification).
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

### What consumers must log in their output

When a consumer proceeds successfully past the checks above, it records the brief's provenance in its own output's context block or sources-consulted line:

```
Brief: <filename>
  revision_mode: <value>
  change_class: <value>
  last_modified_by: <value> on <last_modified_date>
```

This carries provenance forward so the downstream consumer of the consumer's output (e.g. `design-implement` reading a `design-handoff-*.md`) can see one hop back without re-reading the brief.

---

## 6. Scope notes

- **Brief consumers** (apply the §5 checks at intake): `design-artifact-loop`, `design-synthesize`, `design-tuning`.
- **Screen-reviews are out of scope.** This policy governs briefs produced by `design-handoff` (today: `design-brief-*.md` and `design-handoff-*.md` in the handoff-from-implementation flow). Screen-review artifacts (`screen-review-*.md`) have their own V-ID lineage model documented in `design-review/workflow.md` and `design-artifact-loop/workflow.md` ("POLISH ITEMS BELOW V3"). They are not affected by this policy.
- **`design-review` is not a brief consumer.** It audits live screens and emits screen-reviews; it does not read briefs. So it has no intake checks to add.
- **`design-ingest` / `design-implement` are downstream of the consumers**, and read a handoff/manifest, not the brief directly — so they do NOT run the §5 *refuse* checks. They run a distinct **tolerant supersede-awareness check** instead (§8): `design-ingest` detects + stamps + reports, `design-implement` explains a no-op and guards apply. The provenance log added by consumers in §5 is the bridge for the brief→handoff hop.

---

## 7. Migration

Existing briefs in `{implementation_artifacts}` that predate this policy do not carry provenance frontmatter. They will fail Check 1 (`fields present`) at intake. Two paths:

- **Re-run `design-handoff`** for the active feature. The new brief carries proper provenance; if a predecessor exists on disk it gets flipped to `superseded` per §4.2.
- **One-time manual backfill** for briefs that should remain consumable: add the provenance block with `revision_mode: workflow_generated`, `change_class: original`, `last_modified_by: workflow`, and dates matching the brief's existing `date:` field. This is acceptable because we are reconstructing what the producer *would have* written; the brief is otherwise unchanged.

Migration is best-effort. Briefs that aren't currently in active use can be left as-is — they will halt loudly the next time anyone tries to consume them, at which point the active/superseded decision is obvious.

---

## 8. Ingest-tolerance for superseded handoffs

`design-ingest` and `design-implement` are downstream of the brief consumers (§6) — they read a handoff/manifest, not the brief — so they do NOT run the §5 *refuse* contract. But `design-ingest` IS the non-destructive checkpoint (it catalogs and pauses; it never applies), which makes it the right place to surface supersede BEFORE any code moves. So these two workflows run a distinct, **tolerant** supersede-awareness check:

- **`design-ingest`** derives the handoff's `target_slug` (step-01) and resolves it against the briefs in `{implementation_artifacts}`. If the matched brief is `brief_status: superseded`, ingest does NOT refuse — it builds the manifest anyway (you stay able to ingest a superseded handoff for review/audit/diff), **stamps** `ingest.supersede_status` + `ingest.superseded_by` into the manifest, and **leads its handoff pause** by naming the successor and noting the work may already be applied. On a raw-URL run with no brief on disk it records `supersede_status: no_brief` and says so — it never infers `active`. On `>1 active` it records `ambiguous` and surfaces the broken predecessor chain (§2.6) without blocking.
- **`design-implement`** copes on every input path. On the **manifest path** it reads the stamp at intake: a superseded manifest with no remaining deltas yields a no-op that *explains itself* ("already applied, and superseded by `<X>`"); a superseded manifest **with** deltas HALTS for explicit confirmation. On a **direct URL/bundle run** (no `design-ingest` in front, so no stamp) it resolves supersede INDEPENDENTLY in step-01 §SHARED.1a — deriving the slug from the frame inventory and matching it against the briefs, the same contract as `design-ingest` step-01 §5 — and on `superseded` SURFACES and HALTS before the apply pipeline. Either way it is symmetric: no hard refuse, but no silent apply, because building the surface toward a superseded design is intent, not decision autonomy, so autonomous mode does not do it unasked.

This is deliberately weaker than the §5 consumer refuse: a consumer that synthesizes off a superseded brief silently corrupts everything downstream, so it must refuse; a non-destructive cataloguer that pauses for review only needs to *tell the truth loudly*. The `--allow-superseded` escape hatch in §5 Check 3 has no analog here because `design-ingest` never blocks in the first place — the gate that matters is `design-implement`'s apply-time confirmation on a superseded-with-deltas run.

**The honest limit.** Supersede status lives in the *brief* frontmatter, but ingest's input is a design URL/bundle. So ingest can only know a handoff is superseded when its surface confidently corresponds to a brief's `target_slug` on disk. A raw-URL run with no brief is `no_brief` — ingest states it cannot check, rather than asserting the handoff is current. Diffing a superseded handoff against its successor (so `design-implement` applies only the delta) is explicitly **out of scope** here — it would require both to be ingestable design sources of the same kind, which a handoff and a markdown brief are not; it is a candidate for a future dedicated workflow.
