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

### 1b. Load Brand Identity

Check if the project has a brand identity document:

```bash
ls {implementation_artifacts}/../planning-artifacts/brand-identity.md 2>/dev/null
```

**If found:**
- Read the entire file and store as `{brand_identity}`
- Set `{brand_identity_path}` to the absolute path
- Extract `{hard_failures}` from section 8 (Hard Failures)
- Extract `{visual_references}` from section 7 (External Influences) — these persist across iterations and don't need user re-input
- Report: "Brand identity loaded — evaluating against project visual language."

**If not found:**
- Set `{brand_identity}` = empty
- Report: "No brand identity document. Evaluating against brief constraints and generic guardrails."

### 2. Extract Constraints from the Brief

Parse the brief and extract constraints. The approach depends on whether a brand identity exists:

**If brand identity exists:**

The brief's section 4 (Visual Identity & Design Constraints) was generated FROM the brand identity — but the brand identity document itself is the authoritative source. Use it for:
- Component patterns (section 4 of brand identity) — exact Tailwind classes for cards, badges, buttons, tables
- Typography rules (section 2) — exact type scale with sizes
- Color values (section 3) — exact palette
- Hard failures (section 8) — numbered non-negotiable list
- AI sensitivity (section 9) — project-specific fingerprint concerns

Extract `{brief_constraints}` from:
- Section 5 (Constraints) — responsive targets, data density, navigation position
- Section 6 (Design Ask) — the specific design directive and scope

Set `{corporate_guardrails}` from the brand identity's hard failures + AI sensitivity table + the standard AI fingerprint list.

**If no brand identity:**

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
- `{brief_constraints}` ✓
- `{corporate_guardrails}` ✓ (may be empty if not a corporate project — that's OK)
- `{iteration_number}` ✓

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
