---
name: 'step-03b-emit-rationale'
description: 'Emit the analytics presentation rationale — a human-facing record-of-decision capturing HOW page-mode, band-presence, and archetype were chosen. Conditional: runs only when the brief carries an analytics band.'
---

# Step 3b: Emit Analytics Presentation Rationale (conditional)

**Goal:** Write a companion artifact that documents the *deliberation* behind the analytics presentation decisions the brief encodes — the page-mode call, the band-belongs answers, the archetype candidates weighed, and the shapes rejected. The brief records the winner; this records how the winner won and what lost.

**When this step runs:** ONLY when `{has_analytics_band}` is `true` (set in step-01 §5b, i.e. `band_provenance ∈ {inherited, recommended-new}`). When `{has_analytics_band}` is `false`, **skip this step entirely** and proceed to step-04 — a plain operational worklist with no band produces no rationale file.

**Why a separate artifact, not a brief section:** The brief is a bias filter — it withholds the current layout so Claude Design starts from a blank canvas. Deliberation prose ("we considered `trend` but rejected it") inside the brief would hand the designer a shape and break that mandate. So the reasoning lives beside the brief, not in it. See `shared/analytics-rationale.md` "Why this file exists". Claude Design reads the brief, never this file; the brief MUST NOT reference this file in return.

---

## RULES

1. **Conditional.** No band → no file. Do not emit an empty or "n/a" rationale.
2. **Not a brief.** This artifact is out of scope for `brief-revision-policy.md` — no 11-field Block A block, no 6 intake checks, no consumer validation. It carries only its own `rationale_status` / `supersedes` / `superseded_by` lineage. See `shared/analytics-rationale.md` "PROVENANCE SCOPE".
3. **Lineage derives from the brief.** Never invent an independent supersession invariant. The predecessor rationale is found by its 1:1 link to the superseded brief (`accompanies_brief == {supersedes_filename}`), not by a second glob-and-halt.
4. **Fill every variable.** No template placeholder survives into the written file. The reasoning was captured in step-01 §5/§5b/§5c — this step renders it, it does not re-derive it.
5. **One-way linkage.** This file's `accompanies_brief` names the brief. The brief does not name this file.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From step-01:
- `{page_mode}`, `{band_provenance}`, `{has_analytics_band}`, `{analytics_archetype}`
- `{page_mode_rationale}`, `{band_decision_log}`, `{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`
- `{feature_name}`, `{user_name}`

From step-03:
- `{target_slug}`, `{date}`, `{source_run_date}`
- `{output_filename}` — the brief's filename (becomes `accompanies_brief`)
- `{change_class}` — `original | material_revision`
- `{supersedes_filename}` — the superseded brief's filename when `change_class == material_revision`, else `""`
- `{implementation_artifacts}`, `{project-root}`

---

## EXECUTION SEQUENCE

### 1. Resolve Output Path

Reuse the brief's `{project-root}` resolution from step-03 §1 — `git rev-parse --show-toplevel` for the current worktree, per `shared/worktree-portability.md` §1. Do NOT re-resolve from a cached absolute path.

```
{rationale_output_path}            = {implementation_artifacts}/design-rationale-{target_slug}-{date}.md
{rationale_output_filename}        = basename of {rationale_output_path}
{rationale_path_relative_to_repo_root} = path relative to {project-root}
```

**Worktree refusal.** Before writing, verify `{rationale_output_path}` is a descendant of `{project-root}`. If not, halt with the `shared/worktree-portability.md` §4 diagnostic — same guard the brief uses.

### 2. Resolve Predecessor Rationale (lineage derived from the brief)

Branch on the brief's `{change_class}` (decided in step-03 §1a — do not recompute):

| Brief `change_class` | Rationale resolution |
|---|---|
| `original` | `{rationale_supersedes_filename}` = `""`. No predecessor to flip. |
| `material_revision` | Find the predecessor rationale by its link to the superseded brief: scan `{implementation_artifacts}/design-rationale-{target_slug}-*.md` for the file whose frontmatter `accompanies_brief == {supersedes_filename}`. If found, capture its basename as `{rationale_supersedes_filename}`. If none is found (the superseded brief predates this rationale feature), set `{rationale_supersedes_filename}` = `""` and note "no predecessor rationale to supersede" — this is normal, not an error. |

This 1:1 link is exact: each rationale names exactly one brief, so there is no ambiguity and no second active-uniqueness halt to enforce. The brief's own §1a already guarantees at most one active predecessor brief.

### 2a. Flip the Predecessor Rationale (only when one was found)

When §2 found a predecessor rationale, edit its frontmatter in-place BEFORE writing the new file:

- Set `rationale_status: superseded`
- Set `superseded_by: {rationale_output_filename}`

Leave every other field and the body untouched. This is the only edit step-03b makes to an existing file.

### 3. Write the Rationale

Write `{rationale_output_path}` using the template in `shared/analytics-rationale.md` ("The template"). Fill every `{variable}` from the state above:

- Frontmatter: `accompanies_brief` = `{output_filename}`; `supersedes` = `{rationale_supersedes_filename}`; `superseded_by` empty; the decision-summary trio (`page_mode`, `band_provenance`, `analytics_archetype`) from state.
- §1 from `{page_mode}` + `{page_mode_rationale}`; include the hybrid note iff `page_mode == operational` (band present + operational mode = the hybrid case).
- §2 from `{band_decision_log}` + `{band_provenance}`; include the veto line iff `band_provenance ∈ {recommended-new, recommended-drop}`.
- §3 from `{archetype_candidates}` (the table), `{archetype_winner_reason}`, `{archetype_secondary}`; include the time-in-data check block iff `{time_present_check}` is set.
- §4 from the rejected rows of `{archetype_candidates}` plus the cross-cutting bans (no KPI wall, etc.).

### 4. Self-Review

Run the "Self-check" list at the bottom of `shared/analytics-rationale.md`. In particular confirm:

- [ ] This step ran because `{has_analytics_band}` is genuinely `true` — not emitted for a no-band feature.
- [ ] No placeholder text survives; the candidates table has the chosen row plus at least the most tempting rejected alternative.
- [ ] If the data carries time, the time-in-data check is present and states why `trend` was or wasn't the job.
- [ ] `accompanies_brief == {output_filename}`. If `change_class == material_revision` and a predecessor rationale existed, it was flipped to `superseded` in §2a.
- [ ] No Block A 11-field provenance block leaked in — this is not a brief.

### 5. Hand Off

The rationale is now on disk beside the brief. Proceed to step-04 (deliver). Step-04 stages BOTH files in the same commit/PR, so the brief on `main` always has its rationale beside it.

---

## SUCCESS METRICS

- Rationale written to `{rationale_output_path}` whenever — and only when — the brief carries an analytics band.
- The deliberation behind the presentation decision is now durable and auditable: page-mode signal, band-belongs answers, archetype candidates with verdicts, the road not taken, and the explicit time≠trend check when time is in the data.
- The brief stays a clean bias filter — zero reasoning prose added to it, zero pointer back to this file.
- Lineage is honest and brief-derived: `accompanies_brief` ties 1:1 to the brief; a re-run supersedes the matching predecessor rationale instead of piling up duplicates.
