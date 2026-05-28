---
name: 'step-01-receive-and-lock-mode'
description: 'Parse the handoff block, classify the artifact, lock one of four modes, and restate the run context block'
---

# Step 1: Receive Handoff & Lock Mode

**Progress: Step 1 of 4** — Next: Load Sources & Build Evidence (autonomous)

## RULES:

- This is the ONLY conditionally-interactive step. Halt for mode disambiguation only when the mode-detection rules below produce a genuine tie AND `autonomous_mode` is `false`.
- Do NOT present option menus, do NOT ask the user to "tell us what you want." If the handoff block is parseable, parse it and proceed.
- Once `{mode}` is set, it is LOCKED for the run. Mid-run scope expansion requires terminating this run and starting a new one.

---

## SEQUENCE OF INSTRUCTIONS

### 1. Parse the Handoff Block

The handoff block (in the user's message that triggered this workflow, or in the message immediately prior) has these expected components. Extract each:

| Component | How to find it |
|---|---|
| `{repo_url}` | The `https://github.com/ORG/REPO` URL, no trailing `.git` |
| `{artifact_path}` | Repo-relative path on `main`, e.g. `_bmad-output/implementation-artifacts/design-brief-foo-2026-05-26.md` |
| `{user_summary}` | The 1–3 line bullet list under "Summary (3 lines):" — convenience only, NOT authoritative |
| `{user_instruction}` | The free-text directive after "Hand off to design-artifact-loop:" (e.g., "Design the UI following the brief exactly") |
| `{screenshot_paths}` | Any image paths/URLs the user attached; empty if none |

**If the handoff block is malformed** (no artifact path resolvable, or the file does not exist on disk), STOP and emit a one-paragraph diagnostic that names the missing field. Do NOT guess paths or fall back to "the most recent brief" — that defeats the artifact-first contract.

### 2. Resolve the Artifact

Convert `{artifact_path}` (repo-relative) to `{artifact_abs_path}` using the current `{project-root}`:

```bash
{artifact_abs_path} = {project-root}/{artifact_path}
```

Read the file fully into `{artifact_content}`. Parse its YAML frontmatter (if any) to determine `{artifact_type}`:

| Frontmatter `type:` field | `{artifact_type}` |
|---|---|
| `design-brief` | `design-brief` |
| `screen-review` | `screen-review` |
| `policy-delta` (rare; emitted by `apply-design-policy-change`) | `policy-delta` |
| anything else, or no frontmatter | infer from filename prefix: `design-brief-*` → `design-brief`; `screen-review-*` → `screen-review`; `design-policy-change-*` → `policy-delta` |

If neither frontmatter nor filename resolves the type, set `{artifact_type}` = `unknown` and surface the file path to the user — do NOT proceed.

### 2a. Validate Brief Revision Provenance (only when `{artifact_type}` = `design-brief`)

Briefs are subject to the contract defined in `{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md`. Validate the provenance frontmatter BEFORE extracting target identity (§3) — a brief that fails validation is unconsumable and step-01 must halt without proceeding to step-02.

**Skip this section entirely** when `{artifact_type}` ∈ {`screen-review`, `policy-delta`, `unknown`} — those artifacts have their own lineage models and are not governed by `brief-revision-policy.md`.

**Escape hatch:** if the user's invocation includes the literal token `--allow-superseded` AND `{artifact_path}` names a specific superseded brief, skip Check 3 only. All other checks still run. Do NOT auto-apply this escape hatch — it exists for narrow audit cases ("what did we tell the designer two weeks ago") and must be passed explicitly each run.

Run the checks in order; halt on the first failure with the diagnostic shown.

**Check 1 — fields present.** Parse the provenance block. Required fields: `target_slug`, `brief_status`, `revision_mode`, `change_class`, `supersedes`, `superseded_by`, `source_workflow`, `source_run_date`, `last_modified_by`, `last_modified_date`. Empty strings are allowed only for `supersedes` and `superseded_by`. If any required field is missing or carries a disallowed empty value, halt:

```
Brief frontmatter missing provenance field(s): <comma-separated list>.
Brief: {artifact_path}
This brief predates the revision policy (or was malformed) and cannot be safely consumed.
Re-run design-handoff to regenerate it under the current contract, or back-fill the provenance block per brief-revision-policy.md §7.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md
```

**Check 2 — invariants.** Run invariants 2–8 from `brief-revision-policy.md` §2 against the parsed frontmatter:

- `revision_mode == "workflow_generated"` ⇒ `change_class ∈ {"original", "material_revision"}`
- `revision_mode == "manual_minor_revision"` ⇒ `change_class == "clarification"`
- `change_class == "original"` ⇒ `supersedes` is empty
- `change_class == "material_revision"` ⇒ `supersedes` names an existing file in `{implementation_artifacts}`
- `brief_status == "superseded"` ⇒ `superseded_by` is non-empty
- `revision_mode == "workflow_generated"` ⇒ `last_modified_by == "workflow"` AND `last_modified_date == source_run_date`

On any failure, halt with a diagnostic naming the specific invariant and the conflicting fields. Do NOT attempt to "fix" the file — surface to the user.

**Check 3 — superseded.** If `brief_status == "superseded"`:

```
Refusing to consume a superseded brief.
Brief: {artifact_path}
Superseded by: <superseded_by value>
If you really need to consume this older brief (e.g. for audit), restate the handoff with --allow-superseded; otherwise switch to the successor in {implementation_artifacts}.
```

Skipped only when `--allow-superseded` was passed AND the user named this specific file (per the escape-hatch rule above).

**Check 4 — active uniqueness.** Resolve `{this_target_slug}` from this brief's frontmatter `target_slug:` field; if absent, derive it from the filename (strip the `design-brief-` prefix and the trailing `-{date}.md`). Glob `{implementation_artifacts}/design-brief-{this_target_slug}-*.md`, parse each match's frontmatter, and count those with `brief_status: active`. If more than one match, halt:

```
Active-uniqueness invariant violated for target_slug "<slug>":
  - <path 1>
  - <path 2>
  - ...
Exactly one active brief per target_slug is permitted. Fix the predecessor chain
(set brief_status: superseded and superseded_by on the older briefs) and retry.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §2.6
```

**Check 5 — material change with manual revision.** If `change_class == "material_revision"` AND `revision_mode == "manual_minor_revision"`:

```
Forbidden combination: material change with manual revision.
Brief: {artifact_path}
A material revision must go through design-handoff (which sets revision_mode: workflow_generated).
Re-run design-handoff for this feature; do not hand-edit a brief into a material revision.
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

**Check 6 — workflow-generated brief was hand-edited.** If `revision_mode == "workflow_generated"` AND `last_modified_by == "human"` AND `last_modified_date > source_run_date`:

```
Brief was hand-edited after workflow generation, but revision_mode still claims workflow_generated.
Brief: {artifact_path}
Either re-run design-handoff (if the edit was material), or update the frontmatter
(if the edit was a minor revision: set revision_mode: manual_minor_revision and change_class: clarification).
See: {project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md §3
```

**On success**, capture the provenance into local state for inclusion in step-3's output context block:

- `{brief_revision_mode}` = `revision_mode` value
- `{brief_change_class}` = `change_class` value
- `{brief_last_modified_by}` = `last_modified_by` value
- `{brief_last_modified_date}` = `last_modified_date` value
- `{brief_supersedes}` = `supersedes` value (may be empty)

Step-3 surfaces these in the output's "Sources consulted" / context block so the next consumer in the chain sees provenance one hop back without re-reading the brief.

### 3. Extract Target Identity

From the artifact's frontmatter and body, extract:

- `{target_label}` — `target:` frontmatter field, or the H1 of the artifact (e.g., "AVASK VAT reclaim")
- `{target_route}` — `target_route:` frontmatter field, or scan the body for the first `/route/path` token under "Route:" or "Target:"
- `{target_slug}` — `target_slug:` frontmatter field if present; otherwise derive from `{target_route}` by stripping leading slash, replacing `/` with `-`, and lowercasing (e.g., `/reclaim/avask` → `reclaim-avask`)

Extract the **context block** fields if the artifact carries them:

- `{user_role}` — "User:" line, "Persona:" line, or first paragraph of a "Who uses this" section
- `{frequency}` — "Frequency:" line or "How often:" mention
- `{stakes}` — "Stakes:" line, "Consequence:" line, or "What's at stake" mention
- `{out_of_scope}` — "Out of scope:" line, "Boundaries:" line, or explicit "Do not change" list

If any field is missing from the artifact, set the variable to the literal string `"(not specified in artifact)"` — do NOT invent a value. The context block in step 3's output will surface the gap.

### 4. Classify Mode

Apply the mode-detection table in order. The FIRST rule that matches wins.

| Rule | Signal | `{mode}` |
|---|---|---|
| 1 | `{artifact_type}` = `policy-delta`, OR `{user_instruction}` contains "policy lift", "raise to policy", "apply policy change" | `policy-lift` |
| 2 | `{user_instruction}` contains "review only", "critique", "audit", "pass/fail", or asks for an assessment without proposed changes | `review-only` |
| 3 | `{artifact_type}` = `screen-review`, OR `{user_instruction}` contains "refine", "iterate", "tighten", "polish", "second pass on", "fix the top issues" | `refine-screen` |
| 4 | `{artifact_type}` = `design-brief` AND `{user_instruction}` is silent on refinement | `design-from-brief` |
| 5 | Tie or no rule matched | see "Tie-break" below |

**Tie-break:**

- If `autonomous_mode` = `true`, default to the first mode listed in this priority: `design-from-brief` → `refine-screen` → `review-only` → `policy-lift`. The first sentence of the output's context block must state the chosen mode AND the priority-default reason.
- If `autonomous_mode` = `false`, halt with this one-paragraph question:

  ```
  Mode is ambiguous from the handoff. The artifact is a {artifact_type}, the instruction says "{user_instruction}", and the rules support both {mode_A} and {mode_B}. Which mode? Reply with one of: design-from-brief, refine-screen, review-only, policy-lift. Mode locks for the rest of the run.
  ```

  Do NOT volunteer a recommendation; the user picks. Once they reply, lock `{mode}` and proceed.

### 5. Lock the Mode

Set `{mode}` to the resolved value. From this point in the run, every later step rejects work that violates the mode's scope (see workflow.md → "Mode scope" matrix).

If the user later asks for work that crosses a "no" cell mid-run, do NOT silently expand. Terminate the current run and instruct the user to restate the handoff under the new mode:

```
That change is out of scope for {mode}. Mode-locked runs do not silently expand. To do {requested-work}, restate the handoff block under {target_mode} and rerun design-artifact-loop.
```

### 6. Run Gates 1–2 and Restate the Run Context Block

**Gate 1 — input validity** (per workflow.md → "Approval gates"): confirm the artifact exists on `main`, the target route/slug is known or explicitly unknown, the mode is explicit or unambiguously inferred, and screenshots are present if the task is screenshot-led refinement. If any check fails, stop and request the specific missing input — do NOT guess.

**Gate 2 — context sufficiency**: confirm the context block has user/role, frequency, stakes, source-of-truth artifact, and an explicit out-of-scope boundary. If any field is missing AND no mode default covers it, ask ONCE for the missing field before proceeding. Mode defaults: `refine-screen` and `policy-lift` derive out-of-scope from the mode-scope matrix; `review-only` has no implicit defaults. Missing-but-asked fields that the user can't supply are recorded as `(not specified)` and become evidence gaps in the output — never silently invented.

Emit a single short message to the user — this is the ONLY output of step 1. It is not a menu, not a checklist, just a paragraph and a quoted block:

```
Locked mode: {mode}. Target: {target_label} ({target_route}). Source of truth: {artifact_path} ({artifact_type}, {N} lines). Gates 1–2 cleared. Proceeding autonomously.

Context:
- User: {user_role}
- Frequency: {frequency}
- Stakes: {stakes}
- Source of truth: {artifact_path}
- Out of scope: {out_of_scope}
```

Any field with the value `"(not specified)"` or `"(not specified in artifact)"` is rendered exactly so the gap is visible to the user and propagates into the output's evidence-gaps line.

### 7. Proceed to Step 2

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/steps/step-02-load-sources.md`

---

## SUCCESS METRICS

- The handoff block was parsed into all named state variables, or the user was told exactly which field was missing.
- `{artifact_type}` was resolved deterministically — no guessing.
- `{mode}` was set by the first matching rule, or by an explicit user choice if the auto-rules tied.
- The context block was restated in a single short message, and every field is either populated or explicitly marked as missing.

## FAILURE MODES

- Falling back to "the most recent design-brief" when the handoff's artifact path doesn't exist. The artifact-first contract is broken — STOP instead.
- Picking `refine-screen` because there's a screenshot in the handoff, when the actual artifact is a `design-brief` and the instruction is "design the UI." The artifact wins; the screenshot is evidence, not the input.
- Presenting an option menu when `autonomous_mode` is true.
- Silently morphing the mode after step 1. If the user asks for IA changes in `refine-screen`, terminate the run; do not stretch the scope.
