---
name: 'step-01-load-context'
description: 'Load design brief, visual references, corporate guardrails, and previous iteration state'
---

# Step 1: Load Context

**Progress: Step 1 of 3** — Next: Analyze Screenshot (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- If a required file is missing, work with what's available — don't block.
- Extract constraints precisely from the brief — quote section numbers when possible.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## SEQUENCE OF INSTRUCTIONS

### 1. Locate and Read the Design Brief

Find `{brief_path}`:

- If the user specified a brief → use that path
- Otherwise, find the most recent design brief:
  ```bash
  ls -t {implementation_artifacts}/design-brief-*.md | head -1
  ```

Read the full brief. Extract and store:

- `{feature_name}` — from the brief's frontmatter `feature:` field
- `{brief_path}` — absolute path to the brief file

### 1b. Load Project Design Policy (canonical source)

Check both possible locations for a project-level design system declaration, in order. `docs/design-policy.md` is the canonical location; `{planning_artifacts}/brand-identity.md` is the legacy slot. Prefer the first if both exist:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {implementation_artifacts}/../planning-artifacts/brand-identity.md 2>/dev/null
```

**If either is found:**
- Read the entire file and store as `{brand_identity}` (variable name retained for backward compatibility with downstream templates)
- Set `{brand_identity_path}` to the absolute path of whichever file was loaded
- Extract `{hard_failures}` from the policy's hard-failures section (numbered list in §5 of `docs/design-policy.md` or §8 of legacy `brand-identity.md`)
- Extract `{policy_constraints}` — the full set of testable rules from the policy (status palette, color count limits, badge shapes, layout principles, page-mode rules, detail-view rules). This is the source-of-truth set against which any brief-derived constraint will be contradiction-scanned in step-02.
- Extract `{visual_references}` from the policy's external-influences / reference-products section — these persist across iterations and don't need user re-input
- Report: "Project design policy loaded from `{brand_identity_path}` — evaluating against project visual language. Brief is derivative; policy wins on conflict."

**If neither is found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty, `{policy_constraints}` = empty
- Report: "No project design policy. Evaluating against brief constraints and generic guardrails. Consider running `create-design-policy` to make future runs deterministic."

### 2. Extract Constraints from the Brief (derivative — not authoritative)

Parse the brief and extract its stated constraints. **The brief is derivative of the policy loaded in step 1b.** Step-02 will contradiction-scan brief-derived constraints against `{policy_constraints}`; on conflict, policy wins.

**If a project design policy exists (`{brand_identity}` populated):**

The brief's section 4 (Visual Identity) and section 5 (Hard Constraints) were generated from the policy — but **the policy file itself is the authoritative source for everything covered there.** The brief may legitimately:
- Restate, focus, or summarize the policy for one feature.
- Add feature-specific constraints the policy doesn't cover (responsive targets for this page, data density expectations, navigation position, interaction model).

The brief MAY NOT:
- Introduce parentheticals or carve-outs that soften policy hard rules.
- Permit something the policy bans.
- Drop a hard-failure bullet the policy declares.

When the brief and policy disagree, the policy text is what step-02 evaluates against. Drift is logged, not honored.

Extract `{brief_constraints}` from:
- Section 5 (Hard Constraints) — capture the brief's full bullet list; step-02 will diff this against `{hard_failures}` from policy.
- Section 5's feature-specific tail — responsive targets, data density, navigation position, interaction model (these are net-new from the brief; no policy version to compare).
- Section 6 (Design Ask) — the specific design directive and scope.

Set `{corporate_guardrails}` from `{hard_failures}` (loaded from policy in step 1b) + the AI fingerprint sensitivity section of the policy + the standard AI fingerprint list. **Do NOT pull `{corporate_guardrails}` from the brief; the brief may have softened items.**

**If no project design policy exists (`{brand_identity}` empty):**

The brief is the only available source — there is nothing to contradiction-scan against. Be aware that brief-stated hard rules are unverifiable in this mode.

Extract `{brief_constraints}` from:
- Section 5 (Constraints) — responsive targets, data density, navigation position, interaction model
- Section 4 (Design System Context) — tokens, patterns, reference pages
- Section 6 (Design Ask) — the specific design directive and scope

Extract `{corporate_guardrails}` from:
- Section 4a (Corporate Design Guardrails) — if present
- If section 4a does not exist, check for a standalone corporate guidelines doc:
  ```bash
  ls {implementation_artifacts}/../planning-artifacts/corporate-design-system-guidelines.md 2>/dev/null
  ```

Store the anti-patterns as a numbered checklist — each one becomes a violation check in step 2.

### 3. Load Visual References

Check for visual references in this order:

1. **State file** — if `{state_file_path}` exists and contains a `## Visual References` section, load from there (persisted from a previous iteration)
2. **Companion file** — check for `{implementation_artifacts}/visual-references-{feature-slug}.md`
3. **User input** — if the user pasted visual reference research inline (e.g., Perplexity output), capture it as `{visual_references}`
4. **None found** — set `{visual_references}` to empty. The workflow still works using the brief's constraints alone, but correction messages will lack positive product anchors.

Store `{visual_references}` — should contain:
- Named products (e.g., Stripe, Linear, Ramp, Mercury)
- What to borrow from each (table structure, badge treatment, filter patterns, color strategy)
- Any concrete specs (row heights, chip sizes, spacing values)

### 4. Load Previous Iteration State

Resolve `{state_file_path}`:
```
{implementation_artifacts}/design-tuning-state-{feature-slug}.md
```

**If the file exists:**
- Read it and extract:
  - `{iteration_number}` — increment by 1
  - `{previous_violations}` — the violations list from the last iteration
  - `{visual_references}` — if not already loaded from a higher-priority source
- Report: "Iteration {N} — {X} violations from last round to check."

**If the file does not exist:**
- Set `{iteration_number}` = 1
- Set `{previous_violations}` = empty
- Report: "First iteration — establishing baseline."

### 5. Verify Minimum Context

Confirm at least these are populated:
- `{brief_path}` ✓ (required — cannot proceed without a brief)
- `{feature_name}` ✓
- `{brand_identity_path}` ✓ (path or explicit empty — must be a deliberate value, not unchecked)
- `{policy_constraints}` ✓ (populated if policy loaded; empty otherwise — must be a deliberate value)
- `{brief_constraints}` ✓
- `{corporate_guardrails}` ✓ (may be empty if not a corporate project — that's OK)
- `{iteration_number}` ✓

**If `{brand_identity_path}` is empty in a project that appears to have a policy file you didn't find, STOP and report which paths you checked.** Silent fallback to brief-only mode is the loader-drift bug this workflow exists to prevent — surface it instead of swallowing it.

---

## COMPLETION

Load and follow: `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-02-analyze.md`

---

## SUCCESS METRICS

- Design brief located and read
- Constraints extracted as a checkable list
- Corporate guardrails extracted as a numbered checklist (if applicable)
- Visual references loaded from the best available source
- Previous iteration state loaded (if exists)
- Iteration number set correctly
