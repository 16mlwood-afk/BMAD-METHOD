---
name: brief-revision-policy
description: 'Canonical policy for how design briefs may be revised. Defines the minor/material split, the provenance frontmatter contract, the editing rules, and the halt conditions consumer workflows enforce at intake. Referenced by design-handoff (producer) and design-artifact-loop / design-synthesize (consumers).'
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
- **Block B — Content** (3–6 fields, mode-dependent). Tracks what the brief contains: handoff mode, page mode, route, source diagnostic, and (in refine-screen mode) the targeted-changes / unchanged-regions / deferred-violations breakdown.

Both blocks are validated by consumers at intake. Missing a required field in either block halts consumption.

```yaml
---
# Block A — Provenance (always required)
target_slug: my-feature                  # kebab-case identifier; doubles as the active-uniqueness key. For refine-screen runs, prefix with "refine-".
brief_status: active                     # active | superseded
revision_mode: workflow_generated        # workflow_generated | manual_minor_revision
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
band_provenance: none                    # inherited | recommended-new | recommended-drop | none
analytics_archetype:                     # required iff band_provenance ∈ {inherited, recommended-new}; omit otherwise

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
| `revision_mode` | `workflow_generated`, `manual_minor_revision` | How the current file state came to be. `workflow_generated` means produced (or last produced) by `design-handoff`; `manual_minor_revision` means a human hand-edited the file after generation. |
| `change_class` | `original`, `clarification`, `material_revision` | What kind of change this file represents relative to its predecessor. `original` = first brief for the feature. `clarification` = minor revision. `material_revision` = workflow re-generation triggered by a scope/intent change. |
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
| `route` | pathname string | every brief | The primary route this brief targets. Used by downstream consumers to verify the brief and the implementation target line up. |
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
1a. **Field completeness — Block B.** `mode`, `page_mode`, `route`, `composition_provenance`, and `band_provenance` are present in every brief. `analytics_archetype` is present iff `band_provenance` ∈ {`inherited`, `recommended-new`} and absent otherwise. When `mode: refine-screen`, the additional fields `screen_review_ref`, `targeted_changes`, `unchanged_regions`, and `deferred_violations` are also present (the latter may be an empty list but the key must exist). `collapse_note` is conditional — required iff a collapse occurred, absent otherwise. **Backward compatibility:** a brief authored before the analytics-archetype contract (no `band_provenance` key) is interpreted as `band_provenance: none`, and a brief authored before the composition-fit contract (no `composition_provenance` key) is interpreted as `composition_provenance: policy-default` — consumers MUST treat each absent field as its default rather than halting, the same way an absent `policy_version_required` defaults to `0`. New briefs from `design-handoff` always emit both.
2. **Workflow-generated ⇒ original or material.** `revision_mode: workflow_generated` requires `change_class ∈ {original, material_revision}`. A workflow-generated brief cannot be a `clarification`.
3. **Manual ⇒ clarification only.** `revision_mode: manual_minor_revision` requires `change_class: clarification`. A hand-edited brief MUST NOT carry `change_class: material_revision` — that combination is the forbidden case (see §3).
4. **Original ⇒ no predecessor.** `change_class: original` requires `supersedes` to be empty.
5. **Material revision ⇒ predecessor.** `change_class: material_revision` requires `supersedes` to name an existing prior brief on the same feature.
6. **Active uniqueness.** For a given `target_slug`, at most one brief in `{implementation_artifacts}` may have `brief_status: active` at any time. When a new active brief is written, the predecessor's `brief_status` flips to `superseded` and its `superseded_by` is set in the same edit.
7. **Superseded ⇒ pointer set.** A brief with `brief_status: superseded` must have `superseded_by` naming the successor. (Together with §6, this gives a navigable chain.)
8. **Workflow-generated ⇒ matching `last_modified_*`.** If `revision_mode: workflow_generated`, then `last_modified_by: workflow` and `last_modified_date == source_run_date`. A workflow-generated brief that claims a later human edit is a contract bug.

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
2. **Decide `change_class`** by checking `{implementation_artifacts}` for a prior brief with `target_slug == this brief's target_slug AND brief_status == active`:
   - Zero matches → `change_class: original`, `supersedes: <empty>`.
   - Exactly one match → `change_class: material_revision` (`design-handoff` is being re-run on the same surface; by definition this is material — minor revisions don't go through this workflow). Set `supersedes: <predecessor filename>`.
   - Two or more matches → halt and surface to the user: the active-uniqueness invariant (§2.6) is already broken, fix it before generating a new brief. (This indicates a previous run failed mid-write.)
3. **Flip the predecessor** in the same step when `change_class: material_revision`: edit the prior brief's frontmatter to set `brief_status: superseded` and `superseded_by: <this filename>`. This is the only edit `design-handoff` makes to an existing file.
4. **Set `revision_mode: workflow_generated`**, `last_modified_by: workflow`, and `last_modified_date == source_run_date == {date}`.
5. **Cite this policy** in the brief's "For Claude Design" / handoff intro block, with a one-liner: "Revision provenance follows `brief-revision-policy.md` in the shared design workflow docs."

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

### Check 4 — active uniqueness
List all briefs in `{implementation_artifacts}` matching the same `target_slug` with `brief_status: active`. If more than one is found, halt:

```
Active-uniqueness invariant violated for target_slug "<slug>":
  - <path 1>
  - <path 2>
  - ...
Exactly one active brief per target_slug is permitted. Fix the predecessor chain
(set brief_status: superseded and superseded_by on the older briefs) and retry.
```

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
- **`design-implement` is downstream of the consumers.** It reads the consumer's output (a handoff or response), not the brief directly. The provenance log added by consumers in §5 is the bridge.

---

## 7. Migration

Existing briefs in `{implementation_artifacts}` that predate this policy do not carry provenance frontmatter. They will fail Check 1 (`fields present`) at intake. Two paths:

- **Re-run `design-handoff`** for the active feature. The new brief carries proper provenance; if a predecessor exists on disk it gets flipped to `superseded` per §4.2.
- **One-time manual backfill** for briefs that should remain consumable: add the provenance block with `revision_mode: workflow_generated`, `change_class: original`, `last_modified_by: workflow`, and dates matching the brief's existing `date:` field. This is acceptable because we are reconstructing what the producer *would have* written; the brief is otherwise unchanged.

Migration is best-effort. Briefs that aren't currently in active use can be left as-is — they will halt loudly the next time anyone tries to consume them, at which point the active/superseded decision is obvious.
