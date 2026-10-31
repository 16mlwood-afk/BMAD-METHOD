---
name: 'step-03-handoff'
description: 'Cross-check inventory, run quality checklist, produce final handoff spec'
---

# Step 3: Handoff — Quality Gate and Delivery

**Goal:** Cross-check the spec against the screenshot inventory, run the quality checklist, and produce the final handoff-ready specification.

---

## RULES

- MUST complete the cross-check before delivering.
- MUST run the quality checklist from `{design_standards}`.
- The handoff spec is the final deliverable — it goes directly to devs.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From step-02:

- `{screenshot_inventory}` - Complete element catalogue from screenshot
- `{context_answers}` - Who, what, where, register, breakpoints
- `{open_questions}` - Gaps flagged for dev team
- `{design_decisions}` - All styling changes with rationale
- `{omissions_list}` - Features omitted from spec but still required
- `{fingerprint_findings}` - AI fingerprint scan results
- `{design_standards}` - Loaded design standards reference

---

## EXECUTION SEQUENCE

### 1. Cross-Check: Inventory vs. Spec

Walk through every element in `{screenshot_inventory}`. For each element, verify ONE of:

- It appears in `{design_decisions}` (has a styling change proposed)
- It appears in `{omissions_list}` (intentionally omitted, flagged as still required)
- It is unchanged and doesn't need either (fine as-is — no action needed)

**If any element is unaccounted for:** Add it to `{omissions_list}` or `{design_decisions}` before proceeding.

**This step is the highest-stakes part of the workflow.** Skipping it is how features get deprecated.

### 2. Run Quality Checklist

From `{design_standards}`, evaluate:

**Visual:**

- [ ] Could I mistake this for a real product, not a demo?
- [ ] Color palette cohesive (max 2-3 hues)?
- [ ] Any thick borders, heavy shadows, or decorative elements that add nothing?
- [ ] Every element earns its place?

**Typography:**

- [ ] Primary/secondary/tertiary content identifiable in under 2 seconds?
- [ ] No more than 3 font sizes per component?
- [ ] Monospace used only for codes/IDs?

**Spacing:**

- [ ] Spacious, not cramped?
- [ ] Values consistent (multiples of 4 or 8)?
- [ ] Clear grouping through proximity?

**Context:**

- [ ] Would the actual end-user find this useful on their actual device?
- [ ] Matches the platform it lives on?
- [ ] Emotional register is right?

**Handoff Safety:**

- [ ] Omitted features explicitly listed as "still required"?
- [ ] Any proposed removals/replacements clearly flagged as recommendations?
- [ ] No ambiguity where a dev might interpret "not shown" as "not needed"?

If any checklist item fails, fix it before delivering.

### 3. Produce Final Handoff Spec

Structure the deliverable as follows:

---

```markdown
# Design Spec: {page/component name}

## STYLING REFERENCE ONLY — DO NOT DEPRECATE FEATURES

This spec demonstrates visual direction (colors, typography, spacing, component styling).
It is not a complete feature inventory. Any existing feature, field, interaction, or data
point not addressed in this spec **must be preserved** in the production implementation.
When in doubt, ask — do not remove.

## What this spec covers

- {brief list of areas addressed}

## Key changes from current

{For each change: before -> after with rationale}

- {e.g., "Amber status badges -> neutral grey default + blue for active. Rationale: amber reads as 'warning' in most design systems."}
- {e.g., "2px colored card borders -> 1px #E5E7EB. Rationale: lighter borders feel modern, reduce visual noise."}

## Detailed styling changes

{Full list from {design_decisions} with exact values}

## Design recommendations (discuss before implementing)

{Feature-level changes that need team discussion, or: "No feature changes proposed. This is a styling-only update."}

## What this spec does NOT cover (STILL REQUIRED IN PRODUCTION)

{List from {omissions_list}, or: "All visible elements are addressed. No features were omitted."}

## Questions for dev team

{From {open_questions}, or: "No open questions."}

## Implementation mapping

{Map spec elements to existing components, or ask about the component library}

## Styling tokens

- Colors: {hex values / Tailwind names}
- Font sizes: {px values}
- Spacing: {padding/margin values}
- Border radius: {values}
- Shadows: {values}
```

---

### 4. Self-Review

Final gate: would this pass a senior design review at a top-tier product company, AND does it satisfy the quality bar named in the project's `docs/design-policy.md` (if present — match the reference products and visual anchors it specifies)?

If no — iterate before presenting. Fix the weakest part, then re-check.

---

## DELIVERY

Present the final spec to the user. The spec is ready to be handed off to the dev team directly.

If the user wants to iterate:

1. Take feedback
2. Update `{design_decisions}` and/or `{omissions_list}`
3. Re-run the cross-check (step 1 above)
4. Re-run the quality checklist (step 2 above)
5. Re-deliver the updated spec

---

## SUCCESS METRICS

- Cross-check completed — every inventory element accounted for
- Quality checklist passed — all items green
- Final spec includes: disclaimer, changes with rationale, omissions list, open questions, implementation mapping, tokens
- Self-review passed — senior-designer quality bar met (and project design-policy bar, if one is defined)

## FAILURE MODES

- Delivering without completing the cross-check
- Missing the disclaimer header
- Empty omissions list when elements were clearly skipped
- Vague tokens ("light grey" instead of `#F3F4F6`)
- Proposed feature removals buried in styling changes instead of flagged separately
