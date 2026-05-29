# Step 4: Write Design Policy

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Use the template — do not invent a new structure
- Every section must contain CONCRETE guidance, not platitudes. "Clean and modern" is useless. "Neutral palette, single blue accent, 13px body text, tables over cards" is useful.
- The policy must be project-agnostic in structure but project-specific in content
- In autonomous mode: write the full policy without pausing. Present the complete document for review at the end.

## CONTEXT BOUNDARIES:

- All state variables from steps 01-03 are available
- `{visual_direction}` contains the chosen or synthesized direction
- Brand identity (if it exists) provides concrete token values
- Codebase scan from step-01 provides current implementation context

## YOUR TASK:

Write the design policy document using the template. Every section must be populated with specific, actionable guidance derived from the gathered inputs.

## WRITING SEQUENCE:

### 1. Load the template

Read `{project-root}/_bmad/bmm/workflows/design/create-design-policy/design-policy-template.md`

### 1b. Populate frontmatter

Set the metadata fields:
- `project` = `{project_name}`
- `status` = "approved" (or "draft" if the user requested a review cycle)
- `source` = how the policy was created — e.g., "stakeholder + create-design-policy workflow" or "brainstorming mode (Direction B selected)" or "autonomous inference from codebase"
- `created` and `last_updated` = `{date}`
- `created_by` = `{user_name}`
- `version` = 1
- `consumed_by` and `precedence` are pre-filled in the template — leave them as-is

### 2. Populate each section

For each section in the template, translate the gathered inputs into concrete policy:

**Visual Direction** — from `{visual_direction}` and `{tone}`
- Write the one-sentence identity
- Define the register
- State the density preference
- List what the product is NOT

**Reference Products** — from `{reference_products}` and `{anti_references}`
- For each reference, specify WHAT to borrow (not just the name)
- For each anti-reference, specify WHAT to avoid

**Tone & Personality** — from `{tone}` and `{user_role}`
- How the UI speaks to the user (copy voice)
- Error/empty state personality
- Level of explanation vs assumed expertise

**Layout Principles** — from `{operational_bias}` and `{product_type}`
- Primary layout pattern (table-first? card-first? split-pane?)
- Page structure (header → filters → content → pagination)
- Responsive behavior
- Navigation philosophy

**Component Language** — derived from direction + existing codebase
- What components are used for what purpose
- When to use cards vs tables vs lists
- Badge/tag patterns
- Button hierarchy

**Status System** — derived from product type + existing codebase
- How many status colors (constrain this)
- What each color means
- Default status treatment (most statuses should be neutral)

**Typography & Color Principles** — directional guidance, not exact tokens
- Font approach (system? specific face?)
- Size scale philosophy (how many sizes, what range)
- Color restraint rules
- Monospace usage rules

**Hard Failures** — from `{anti_references}` + AI fingerprint awareness
- Non-negotiable anti-patterns
- The policy MUST include at least one concrete hard failure traceable to each of the six AI Fingerprint Detection categories in `_bmad/bmm/workflows/design/shared/design-standards.md`:
  1. **Layout Fingerprints** (e.g., stat-card rows, bento/magazine grids, hero strips above working tables)
  2. **Typography Fingerprints** (e.g., uppercase tracking-wide labels, mismatched display+body pairings)
  3. **Color & Visual Treatment Fingerprints** (e.g., AI-purple as primary accent, gradient backgrounds, glassmorphism)
  4. **Component Fingerprints** (e.g., stat-card-with-icon, pastel pill-with-dot, animated number counters)
  5. **Content & Copy Fingerprints** (e.g., marketing copy in tool chrome, emoji as UI elements, hover lift/scale transforms framed as "delight")
  6. **Structural Fingerprints** (e.g., evenly modular card grids as primary page structure, compositions liftable into a generic SaaS admin)
- For each category, either (a) reuse the example anti-pattern that matches the project's risk profile, or (b) write a project-specific variant. A policy that lists "see shared design-standards.md" for a category without naming a concrete failure for that category fails this step.
- Add any project-specific hard failures on top (color counts, badge consistency rules, etc.).

**Page Mode Rules** — from `{operational_bias}`
- What "operational mode" pages look like
- What "analytical mode" pages look like
- How hybrid pages balance both

### 3. Cross-reference with existing state

**If brand identity exists:**
- Ensure the policy doesn't contradict it
- Note where the policy adds strategic direction beyond what brand identity captures
- Add a note: "This policy is the strategic complement to `{brand_identity_path}`, which contains concrete design tokens."

**If codebase has established patterns:**
- Note which current patterns align with the policy
- Note which current patterns the policy would change (these become design debt items)

### 4. Write the file

Write the populated template to `{output_path}`.

### 5. Update architecture doc (if applicable)

Check if `{project_knowledge}/PROJECT.md` or `{project_knowledge}/architecture.md` exists. If so, add a reference:

```markdown
## Design Policy
The project's visual policy is defined in `design-policy.md`. All design workflows (`design-handoff`, `design-tuning`, `design-implement`) consume this document.
```

### 6. Present the result

Show the user the complete policy and ask for confirmation:

"Design policy written to `{output_path}`. This document will be consumed by:

- **design-handoff** — uses it to anchor Claude Design briefs to your visual direction
- **design-tuning** — checks correction messages against it for consistency
- **design-implement** — references it when building components

Review the policy above. If anything doesn't match your intent, tell me what to change."

In autonomous mode: skip the confirmation prompt. State what was written and move on.

## SUCCESS METRICS:

- Every section contains specific, actionable guidance (no generic platitudes)
- The policy is self-contained — a new team member could read it and understand the visual direction
- Hard failures are concrete and testable (not "don't make it ugly")
- The policy references shared design-standards.md rather than duplicating it
- Downstream workflows can consume this document without ambiguity

## FAILURE MODES:

- Sections filled with generic advice ("use a clean, modern design")
- Contradicting the existing brand identity document
- Hardcoding values that belong in brand identity (hex codes, Tailwind classes)
- Missing the page-mode rules section (operational vs analytical)
- Not referencing the shared design standards for AI fingerprint rules
- Hard Failures section lists fewer than six concrete anti-patterns (one per AI-fingerprint category), or substitutes "see shared design-standards.md" in place of a category-specific failure
- Hard Failures section is generic enough to belong to any product (no project-specific anti-pattern reflecting `{anti_references}` or `{user_role}`)
