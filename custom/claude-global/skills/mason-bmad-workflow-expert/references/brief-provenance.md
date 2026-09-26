# Brief Provenance Contract

Design briefs in Mason-BMAD are versioned, auditable artifacts — not loose markdown. The contract is defined in `brief-revision-policy.md` (`~/bmad-method-v6/custom/workflows/design/shared/brief-revision-policy.md`) and enforced by every workflow that produces or consumes a brief.

This file is your in-skill reference for the actual field names, values, and invariants. When reviewing or authoring, you can reason from here; when in doubt, the policy file in the fork is the source of truth.

---

## Authoritative reading — eleven fields (corrected 2026-06-10)

Block A has **eleven** fields. The prior "ten is authoritative; eleven is a miscount" ruling was **wrong** and has been reversed — it was based on the §2 YAML *example* (which had dropped a field) and an incorrect premise ("ten is what `design-handoff` emits"). The producer actually emits **eleven**: `brief-template.md` Block A stamps `policy_version_required` (the policy-version pin), documented in `design-handoff/workflow.md`, and the policy's own `§1a` references `policy_version_required` as a Block-A backward-compat field. So the count "eleven" was intentional; the §2 example/table (and this reference) had simply dropped the row. Fixed in the fork 2026-06-10 (`brief-revision-policy.md` §2 now enumerates all eleven).

**The nuance the old ruling was half-reaching for is real, though.** `policy_version_required` is **backward-compat-defaulted** — `§1a` says an absent value is treated as `0`, NOT a halt — exactly like `band_provenance` / `composition_provenance`. So:

- **Block A field count (producer-emitted enumeration): eleven.**
- **Strict halt-on-missing set: the ten lifecycle fields** (`target_slug` + the 9 below). `policy_version_required` absent ⇒ defaults to `0`, does not halt (a pre-policy-version brief is still consumable).

Carry **eleven** as the field count in every Mode, and cite the default-not-halt behaviour when reasoning about Check 1 on older briefs. Do NOT revert to "ten fields" — that drops a real producer-emitted field.

---

## The 11 Block-A Fields

Every brief carries these fields in its YAML frontmatter, alongside whatever feature/route/mode fields the workflow already requires.

| # | Field | Allowed values | Meaning |
|---|---|---|---|
| 1 | `target_slug` | kebab-case string | Stable identifier of the design target. All briefs sharing a `target_slug` are part of the same lineage. Doubles as the active-uniqueness key. For `refine-screen` runs, prefix with `refine-`. |
| 2 | `brief_status` | `active`, `superseded` | Only one `active` brief per `target_slug` may exist at a time. Consumers refuse `superseded` briefs unless explicitly cited with `--allow-superseded`. |
| 3 | `revision_mode` | `workflow_generated`, `manual_minor_revision` | How the current file state came to be. |
| 4 | `change_class` | `original`, `clarification`, `material_revision` | What kind of change this file represents relative to its predecessor. |
| 5 | `supersedes` | filename string, or empty | When this brief replaces a prior brief on the same feature. Filename only (no path). |
| 6 | `superseded_by` | filename string, or empty | Set on the **older** brief when a newer one takes over. Pairs with the newer brief's `supersedes`. |
| 7 | `source_workflow` | `design-handoff` | The workflow that generated this brief. (Reserved for future producers.) |
| 8 | `source_run_date` | ISO date (`YYYY-MM-DD`) | When `source_workflow` last produced this file. Never updated by a minor revision. |
| 9 | `policy_version_required` | integer (`0` if no policy) | Version of `docs/design-policy.md` the brief was authored against. Consumers halt/warn when the current policy version exceeds it. **Backward-compat-defaulted: absent ⇒ `0`, not a halt** (§1a) — so it is in the 11-field enumeration but NOT the strict halt-on-missing set. |
| 10 | `last_modified_by` | `workflow`, `human` | The hand that touched the file most recently. |
| 11 | `last_modified_date` | ISO date | When the file was last written, regardless of by whom. |

Empty strings are allowed ONLY for `supersedes` and `superseded_by`. `policy_version_required` defaults to `0` when absent. Every other field must be populated.

### Canonical example block

```yaml
---
# ... existing feature/route/mode fields ...

target_slug: invoice-review-queue
brief_status: active
revision_mode: workflow_generated
change_class: original
supersedes:
superseded_by:
source_workflow: design-handoff
source_run_date: 2026-05-26
policy_version_required: 0
last_modified_by: workflow
last_modified_date: 2026-05-26
---
```

---

## Edit Classification

The policy splits edits into two classes. The class determines whether a hand-edit is allowed.

### Minor revision — hand-edit allowed

- Wording clarity, typo fixes, punctuation, formatting cleanup
- Phrasing cleanup that does not change meaning
- Explicit restatement of a decision already made elsewhere
- Changelog-only edits

A minor revision must NOT change scope, add/remove views, change hierarchy goals, change the interaction model, change constraints, or alter the questions in §6 (Design Ask).

### Material revision — must re-run `design-handoff`

- Scope changes (add/remove features, surfaces, screens)
- Added or removed views
- Changed hierarchy or layout goals
- Changed interaction model
- New constraints (or removed constraints)
- Anything likely to alter downstream design output

**Test.** Read the diff. If a downstream synthesizer or implementer would produce a meaningfully different output from the new text than from the old text — it is material. If the output would be identical and only the reader experience improves — it is minor.

---

## The 8 Invariants

A brief is valid iff all eight hold. Consumers reject briefs that violate any.

1. **Field completeness.** All eleven Block-A fields present. Empty strings allowed only for `supersedes` / `superseded_by`; `policy_version_required` absent ⇒ defaults to `0` (§1a), not a halt. So the strict halt-on-missing set is the ten lifecycle fields.
2. **Workflow-generated ⇒ original or material.** `revision_mode: workflow_generated` requires `change_class ∈ {original, material_revision}`. Never `clarification`.
3. **Manual ⇒ clarification only.** `revision_mode: manual_minor_revision` requires `change_class: clarification`. A hand-edited brief MUST NOT carry `change_class: material_revision` — this is the forbidden combination.
4. **Original ⇒ no predecessor.** `change_class: original` requires `supersedes` to be empty.
5. **Material revision ⇒ predecessor.** `change_class: material_revision` requires `supersedes` to name an existing prior brief.
6. **Active uniqueness.** For a given `target_slug`, at most one brief in `{implementation_artifacts}` may have `brief_status: active` at any time.
7. **Superseded ⇒ pointer set.** A brief with `brief_status: superseded` must have `superseded_by` naming the successor.
8. **Workflow-generated ⇒ matching `last_modified_*`.** If `revision_mode: workflow_generated`, then `last_modified_by: workflow` and `last_modified_date == source_run_date`. A workflow-generated brief claiming a later human edit is a contract bug.

---

## The 6 Intake Checks

Every brief-consuming workflow (`design-artifact-loop`, `design-synthesize`, `design-tuning`) runs these six checks at intake. If any fails, the workflow halts with a clear diagnostic. Run them in order. Naming style matches the policy file (`brief-revision-policy.md §5`) so citations in reviews and diagnoses are greppable across files.

- **Check 1 — fields present.** All 11 Block-A fields parsed from frontmatter. The 10 lifecycle fields halt on missing; `policy_version_required` absent ⇒ default `0` (§1a backward-compat), not a halt. Missing lifecycle field → halt with the missing-field list.
- **Check 2 — invariants.** Run invariants 2 through 8 above. First failure halts.
- **Check 3 — superseded.** If `brief_status: superseded`, halt unless `--allow-superseded` is set.
- **Check 4 — active uniqueness.** `ls {implementation_artifacts}` and filter by `target_slug == X AND brief_status: active`. More than one → halt with the conflicting filenames.
- **Check 5 — material change with manual revision.** If `change_class: material_revision` AND `revision_mode: manual_minor_revision`, halt. This is the forbidden combination from §3.
- **Check 6 — manual edit on a workflow-generated brief (advisory).** If `revision_mode: workflow_generated` AND `last_modified_by: human` AND `last_modified_date > source_run_date`, halt. Tells the user to either re-run design-handoff (if the edit was material) or update the frontmatter to reflect a clarification.

When a consumer passes all six and proceeds, it must log the brief's provenance into its own output (so the next downstream consumer sees one hop back without re-reading the brief).

---

## Producer Responsibilities (`design-handoff`)

When `design-handoff` runs:

1. Emit the full 11-field Block-A provenance block (including `policy_version_required`, stamped from the policy version resolved in step-01).
2. Search `{implementation_artifacts}` for active predecessor matching `target_slug`.
3. Classify:
   - **0 matches** → `change_class: original`, `supersedes: <empty>`.
   - **1 match** → `change_class: material_revision`, `supersedes: <predecessor filename>`. (Re-running design-handoff on the same target IS material by definition.)
   - **2+ matches** → halt and surface — the active-uniqueness invariant is already broken.
4. If `material_revision`: flip the predecessor's `brief_status` to `superseded` and set `superseded_by` to this filename. This is the only edit `design-handoff` makes to an existing file.
5. Set `revision_mode: workflow_generated`, `last_modified_by: workflow`, `last_modified_date == source_run_date == {date}`.
6. Cite `brief-revision-policy.md` in the brief's "For Claude Design" / handoff intro block.

---

## Consumer Responsibilities

Every brief consumer:

1. Runs the 6 intake checks (in order, halting on first failure).
2. Halts with a clear diagnostic on any failure. **Never "best-effort"** through a broken brief.
3. **Propagates provenance** into its own outputs:

```
Brief: <filename>
  revision_mode: <value>
  change_class: <value>
  last_modified_by: <value> on <last_modified_date>
```

This is the chain that lets a downstream consumer of the consumer's output (e.g., `design-implement` reading a `design-handoff-*.md`) see one hop back without re-reading the brief.

---

## Migration (briefs that pre-date the policy)

Existing briefs without provenance frontmatter fail Check 1. Two recovery paths:

- **Re-run `design-handoff`** for the active feature. New brief gets proper provenance; if a predecessor exists it gets flipped to `superseded`.
- **Manual backfill** for briefs that should remain consumable: add the 11-field block with `revision_mode: workflow_generated`, `change_class: original`, `last_modified_by: workflow`, `policy_version_required: 0` (pre-policy-version brief), and dates matching the brief's existing `date:` field. Acceptable because we're reconstructing what the producer *would have* written.

Migration is best-effort. Briefs not in active use can be left — they'll halt the next time anyone tries to consume them, at which point the active/superseded decision becomes obvious.

---

## Review Checklist (when reviewing a PR touching brief-producing/consuming workflows)

- [ ] All 11 Block-A fields handled (no silent drop of provenance fields — incl. `policy_version_required`)
- [ ] Edit classification logic intact (material vs minor)
- [ ] All 6 intake checks present on consumers (in the correct order)
- [ ] Producer correctly handles predecessor lookup and supersession (the 0/1/2+ branches)
- [ ] Back-fill logic preserved (for pre-policy briefs)
- [ ] Downstream propagation of provenance into the workflow's own output
- [ ] Diagnostic messages on halt are specific (cite the check that failed by number, not just "intake failed")

If any of the above is missing or weakened, **halt the review**.

---

## Out of Scope

- **Screen-reviews.** This policy governs briefs from `design-handoff` (`design-brief-*.md`, `design-handoff-*.md`). Screen-review artifacts (`screen-review-*.md`) have their own V-ID lineage model documented in `design-review/workflow.md` and `design-artifact-loop/workflow.md`.
- **`design-review` is not a brief consumer.** It audits live screens and emits screen-reviews; it does not read briefs. No intake checks to add.
- **`design-implement` is downstream of consumers.** It reads the consumer's output (a handoff or response), not the brief directly. The provenance log from §5 is the bridge.
