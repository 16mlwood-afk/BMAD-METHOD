# Step 1: Load the Current Design Policy

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Do NOT skip this step. If no policy exists, this workflow is the wrong one — route to `create-design-policy` instead.

## YOUR TASK:

Locate and load the current design policy so subsequent steps have full context.

## LOAD SEQUENCE:

### 1. Find the policy

```bash
ls {project_knowledge}/design-policy.md 2>/dev/null
find {project-root} -name "design-policy.md" -not -path "*node_modules*" -not -path "*.claude/worktrees*" 2>/dev/null | head -5
```

If multiple are found, prefer `{project_knowledge}/design-policy.md` and confirm with the user before proceeding.

If NONE is found:
- **STOP** — this workflow is not applicable.
- Tell the user: "No design policy found. Use `/bmad:bmm:workflows:create-design-policy` first, then come back if you need to refine it."
- Exit the workflow.

### 2. Read the policy completely

- Set `{policy_path}` to the file path
- Set `{current_policy}` to the full file contents
- Set `{current_version}` by reading the `version` field from the frontmatter (default to 1 if not present)
- Set `{output_path}` = `{policy_path}` (we revise in place)

### 3. Summarize the current direction

In 4-6 lines, summarize what the policy currently says about:

- Visual direction (the one-sentence identity)
- Tone & register
- Density preference
- Primary layout pattern
- Status system constraints
- Top 2-3 hard failures

This summary anchors the rest of the workflow and helps the user spot if the policy they're remembering matches the policy on disk.

### 3b. Baseline category-coverage audit

Before presenting the policy to the user, audit §5 Hard Failures (or whichever section the policy uses for hard failures) against the six AI-fingerprint categories from `_bmad/bmm/workflows/design/shared/design-standards.md`:

1. Layout fingerprints (stat-card rows, bento/magazine grids, hero strips above tables)
2. Typography fingerprints (uppercase tracking-wide, mismatched display+body)
3. Color & visual treatment (AI-purple, gradients, glassmorphism)
4. Component fingerprints (stat-card-with-icon, pastel pill-with-dot, animated counters, hover lift/scale)
5. Content & copy (emoji as UI, marketing copy in tool chrome)
6. Structural (modular card grids as primary structure, compositions liftable to a generic SaaS admin)

For each category, scan the hard-failures section (and adjacent §3/§4 anti-pattern subsections) for at least one concrete anti-pattern traceable to it. Set `{baseline_gaps}` to the list of categories with no concrete coverage. Set `{baseline_audit_status}` to `"compliant"` if `{baseline_gaps}` is empty, otherwise `"has_gaps"`.

This audit is informational at this step — it does not block. It exists so the user knows the policy's quality baseline before deciding what to change. step-02 still runs its delta-touching guard independently; the two cooperate but don't overlap.

### 4. Present and confirm

"Loaded design policy at `{policy_path}` (version `{current_version}`). Current direction:

`<summary from step 3>`

`<if {baseline_audit_status} == "has_gaps", append:>` *Baseline audit:* §5 Hard Failures is missing concrete coverage for category(ies) `{baseline_gaps}`. This is informational — the policy still works, but it falls below the bar `create-design-policy` step-04 now sets for new policies. While you're here, you may want to add coverage for `{baseline_gaps}` in addition to your other changes. Tell me to include it and I'll add a delta for §5 in step-02.

Tell me what you want to change. The more concrete the better — 'too casual' is workable, 'replace the badge system' is better."

In autonomous mode: skip the prompt and proceed directly to step-02 using the user's original request as `{change_description}`. If `{baseline_audit_status} == "has_gaps"`, automatically expand `{change_description}` to include "and add a §5 hard failure for category(ies) `{baseline_gaps}` to bring the baseline to six-category coverage." This honors the autonomy contract — leaving a known gap unactioned in autonomous mode is the wrong default.

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/design/modify-design-policy/steps/step-02-identify-deltas.md`.
