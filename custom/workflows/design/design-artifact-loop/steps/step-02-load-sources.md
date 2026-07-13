---
name: 'step-02-load-sources'
description: 'Load the trust hierarchy in order — policy, sister-skill rules, screenshots, implementation — and build the evidence set the output will cite from'
---

# Step 2: Load Sources & Build Evidence

**Progress: Step 2 of 4** — Next: Produce Output Artifact (autonomous)

## RULES:

- FULLY AUTONOMOUS. No menus, no halting, no "should I…" questions.
- Load sources in the exact precedence order from workflow.md → "Source-of-truth precedence."
- Do NOT inline sister-skill rules into local notes — record only that they were invoked.
- The evidence set is the ONLY place step 3 may cite from. If something is not in the evidence set after this step, it cannot appear in the output's "Rule violated" or "Required correction" fields.

---

## AVAILABLE STATE FROM STEP 1

- `{mode}`, `{artifact_type}`, `{artifact_path}`, `{artifact_abs_path}`, `{artifact_content}`
- `{target_label}`, `{target_route}`, `{target_slug}`
- `{user_summary}`, `{user_instruction}`, `{screenshot_paths}`
- `{user_role}`, `{frequency}`, `{stakes}`, `{out_of_scope}`
- `{policy_path}` (resolved during workflow.md initialization)

---

## SEQUENCE OF INSTRUCTIONS

### 1. Load the Project Design Policy

Read `{policy_path}` fully into `{policy_content}`. Index its top-level sections (the `## N. Title` headings) so step 3 can cite "policy §N (Title)" without re-scanning.

Build `{policy_section_index}` as an ordered list of `{number, title, char_offset}` tuples for the citation engine in step 3.

**If `{policy_path}` is empty** (no policy file was resolved during initialization) and `{mode}` is `policy-lift`, STOP and emit:

```
policy-lift mode requires a project design policy at docs/design-policy.md or {planning_artifacts}/brand-identity.md. Neither was found. Resolve policy authorship first (run create-design-policy), then rerun design-artifact-loop.
```

For all other modes, an absent policy is acceptable but degrades the output — the context block will state "policy: not found" and only sister-skill rules + shared design-standards.md will be available for citation.

### 2. Parse the Canonical Artifact

The artifact was already loaded into `{artifact_content}` during step 1. Now parse it by type:

**If `{artifact_type}` = `design-brief`:**

Extract the brief's structured sections:

- `{brief_purpose}` — Section 1 "Feature Purpose" body
- `{brief_data_shape}` — Section 2 "Domain Data" body (entity tables)
- `{brief_user_context}` — Section 3 "User Context" body
- `{brief_visual_direction}` — Section 4 "Visual Direction" body
- `{brief_hard_constraints}` — Section 5 "Hard Constraints" body
- `{brief_design_ask}` — Section 6 "Design Ask" body (open questions OR refinement bullets)
- `{brief_open_questions}` — the question-list within Section 6, if any
- `{brief_explicitly_asks_comparison}` — boolean: `true` if section 6 contains "compare against the current page" or similar

Section headings vary slightly across briefs — match on the leading verb / noun pattern, not exact text. If a section is genuinely missing, set the variable to empty string and note it in `{evidence_gaps}`.

**If `{artifact_type}` = `screen-review`:**

Extract the structured violation set:

- `{review_violations}` — ordered list of `V1, V2, …` blocks; each with `severity`, `rule_violated`, `observed_failure`, `required_correction`, optional `do_not_change`
- `{review_keepers}` — page-wide protections
- `{review_edge_states}` — required design variants
- `{review_peer_steals}` — peer-pattern transplants
- `{review_anti_ai_checklist}` — the three checks at the end, each with its rationale

**If `{artifact_type}` = `policy-delta`:**

Extract the policy change description:

- `{policy_before}` — pre-change rule text
- `{policy_after}` — post-change rule text
- `{policy_rationale}` — why the change was made
- `{policy_affected_surfaces}` — explicit list of pages/components the delta touches

### 3. Load Screenshot Evidence (if any)

For each path in `{screenshot_paths}`:

- Read the image file via the Read tool
- Build `{screenshot_observations}` — an ordered list of one-line factual observations per image: "Header H1 reads 'AVASK Reclaim' at ~30px"; "Filter row contains 4 status chips (All / Open / Filed / Locked)"
- Do NOT interpret. Observations are pixels you can point at. Interpretation happens in step 3 and only against the policy / brief / sister skills.

If `{mode}` = `review-only` or `refine-screen` AND `{screenshot_paths}` is empty AND `{artifact_type}` ≠ `screen-review`, set `{evidence_gaps}` to include "no visual evidence (screenshot or screen-review) available" — step 3 will degrade the output to "directional refinement only, no per-pixel corrections" and the verdict cannot be `FAIL` without further evidence.

### 4. Build the Skill Routing Plan

Per workflow.md → "Frontend skill routing", routing is mode-driven. Build `{sister_skills_invoked}` by applying the rules verbatim from that section. Routing is REQUIRED for any run that produces UI-facing guidance — improvising visual decisions from workflow prose is the failure mode this gate exists to prevent.

**Always invoke (per mode):**

| `{mode}` | Required skills |
|---|---|
| `design-from-brief` | `design-policy-canonical`, `operational-finance-ui`, frontend / webapp skill (`website-building` or project-equivalent) |
| `refine-screen` | `design-policy-canonical`, plus `operational-finance-ui` when the surface is a table-, queue-, or operations-led finance UI |
| `review-only` | `design-policy-canonical` (frontend skill only required if the review will include concrete UI fix directions — flag during step 3) |
| `policy-lift` | `design-policy-canonical`, plus whichever surface skill matches the target |

**Conditionally invoke:**

- `operational-analytics-band` when the screen includes (or the brief asks for) a KPI strip, analytics row, trend band, or quarter-by-quarter summary band — applies to all modes.
- `operational-cockpit` when the surface is a decide-one triage + single-item decision workspace (`composition: operational-cockpit`, design-handoff §5a) — the canonical doctrine (M1–M6 floor + H1–H5) for the cockpit archetype; applies in operational mode.
- Frontend / webapp skill in `refine-screen` when concrete visual / layout / spacing / control / component changes are being proposed.

Record each skill name plus a one-line reason in `{sister_skills_invoked}`. Do NOT load their rules inline; step 3 invokes the skill via the Skill tool at the moment a specific decision needs interpretation.

**If a required frontend / webapp skill is not installed in this project** (no `website-building` or project-equivalent), record the absence in `{evidence_gaps}` as `"frontend skill missing — UI fix guidance falls back to policy + design-standards.md"`. Step 3 will degrade UI-fix specificity rather than improvise.

### 5. Build the Evidence Set

Assemble `{evidence_set}` — the master record step 3 cites from. Structure:

```yaml
evidence_set:
  primary:
    artifact_path: {artifact_path}
    artifact_type: {artifact_type}
    parsed_sections: { ... }  # from step 2 section 2
  policy:
    path: {policy_path}
    section_index: {policy_section_index}
    available: true | false
  sister_skills:
    - name: design-policy-canonical
      reason: "default — palette / typography / page mode"
    - name: operational-finance-ui
      reason: "target is /reclaim/avask, an operational finance page"
  screenshots:
    paths: {screenshot_paths}
    observations: {screenshot_observations}
  context_block:
    mode: {mode}
    user_role: {user_role}
    frequency: {frequency}
    stakes: {stakes}
    out_of_scope: {out_of_scope}
  evidence_gaps:
    - "{any gap recorded above}"
```

### 6. Pre-flight: Confirm Mode Is Still Viable

Run a quick consistency check before handing to step 3:

| Check | Action if it fails |
|---|---|
| `{mode}` = `design-from-brief` AND `{brief_design_ask}` is empty | Reclassify to `review-only`. Note the reason in `{evidence_gaps}`. |
| `{mode}` = `refine-screen` AND no screen-review artifact AND no screenshot | Allow, but `{output_kind}` will be `screen-review` (synthesized from policy + screenshot in step 3 cannot proceed; require user to provide a screenshot before step 3 runs). If no screenshot, halt and surface: "refine-screen needs visual evidence; attach a screenshot or hand off a screen-review artifact." |
| `{mode}` = `policy-lift` AND `{policy_affected_surfaces}` does not include `{target_route}` | Halt and surface: "policy-lift artifact does not list {target_route} as affected. Either update the artifact or rerun against a listed surface." |
| `{mode}` = `review-only` AND `{evidence_gaps}` contains "no visual evidence" | Allow, but mark the output's verdict as `INDETERMINATE — no visual evidence` rather than `PASS` / `FAIL`. |

Only `refine-screen` with no visual evidence is a hard halt; everything else degrades the output, never silently morphs the mode.

### 7. Proceed to Step 3

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/steps/step-03-produce-artifact.md`

---

## SUCCESS METRICS

- `{evidence_set}` is fully populated; every later citation in step 3 traces back to one of its fields.
- Policy was loaded and section-indexed, or its absence was explicitly recorded.
- Sister skills are listed with one-line reasons for invocation — never restated inline.
- Screenshot observations, if any, are factual (no interpretation, no "feels off").
- The mode survived the pre-flight check or was halted with a specific diagnostic — never silently changed.

## FAILURE MODES

- Pasting policy text into `{evidence_set}` to "make step 3 faster." The policy is loaded once and referenced by section number. Inlining bloats state and risks drift.
- Interpreting screenshots in this step ("the header is too small"). Interpretation is step 3's job and requires citing policy / brief — observations here are pixels and class names only.
- Treating `{user_summary}` as authoritative when it contradicts the artifact body. The file wins.
- Letting `refine-screen` continue when there is no visual evidence at all. The whole point of the mode is bounded corrections to a visible state; without evidence, switch to `review-only` or halt.
