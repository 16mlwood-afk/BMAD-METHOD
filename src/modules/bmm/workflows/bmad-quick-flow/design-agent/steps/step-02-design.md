---
name: 'step-02-design'
description: 'Run AI fingerprint scan, make design decisions, produce styling specification'

nextStepFile: './step-03-handoff.md'
---

# Step 2: Design — Fingerprint Scan and Spec Generation

**Goal:** Evaluate the current UI against design standards, run the AI fingerprint scan, make specific styling decisions, and produce a concrete specification.

---

## RULES

- MUST run the fingerprint scan before producing any spec.
- MUST reference `{design_standards}` for every decision.
- MUST preserve every element from `{screenshot_inventory}` — either include it in the spec or add it to `{omissions_list}`.
- Every recommendation must have a rationale (before/after + why).
- Be decisive — one excellent solution beats three mediocre alternatives.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From step-01:

- `{baseline_commit}` - Git HEAD
- `{screenshot_inventory}` - Complete element catalogue
- `{context_answers}` - Who, what, where, register, breakpoints
- `{open_questions}` - Gaps flagged for dev team
- `{design_standards}` - Loaded design standards reference

---

## EXECUTION SEQUENCE

### 1. AI Fingerprint Scan

Check the screenshot against the P1 and P2 fingerprint lists in `{design_standards}`.

**First rule:** Check if the pattern is already used consistently across the project. If it's the established design language, skip it — ripping it out would create worse inconsistency.

**For each P1 (structural) fingerprint found:**

- Document: what it is, where it appears, what to replace it with
- The fix is almost always removal or reduction to the plainest alternative

**For each P2 (cosmetic) fingerprint found:**

- Document: what it is, fix when touching the affected component

**Composite test:** If 3+ P1 fingerprints exist on one page, recommend a holistic redesign rather than piecemeal fixes.

Store findings as `{fingerprint_findings}`.

### 2. Make Design Decisions

For each area of the page, decide what changes to recommend. Structure each decision as:

```
**Element:** {what}
**Current:** {what it looks like now — be specific: colors, sizes, borders}
**Proposed:** {exact values — hex colors, px sizes, Tailwind classes}
**Rationale:** {why this is better — reference design standards}
```

Categories to evaluate (from `{design_standards}`):

- **Color:** Palette cohesion, accent usage, status colors
- **Typography:** Font sizes, weights, line-heights, hierarchy
- **Spacing:** Padding, margins, gaps — consistent multiples of 4 or 8
- **Borders/Shadows:** Weight, color, necessity
- **Layout:** Information hierarchy, grouping, whitespace usage
- **Components:** Badge styling, button treatments, card patterns

Store all decisions as `{design_decisions}`.

### 3. Track Omissions

Walk through `{screenshot_inventory}`. For every element that the spec does NOT propose changes to:

- If no change needed: skip (it's fine as-is)
- If intentionally omitted from the spec for simplicity: add to `{omissions_list}` with note: "Still required in production — apply same styling principles"

**This step is mandatory.** Skipping it is how features get deprecated.

### 4. Classify Recommendations

Separate design decisions into:

**Styling changes (implement directly):**
Changes to colors, typography, spacing, borders, shadows — these don't affect functionality.

**Design recommendations (discuss before implementing):**
Proposed removals, replacements, or restructuring of UI elements. These affect what users see and interact with.

Flag these clearly so devs know the difference.

### 5. Map to Existing Components

If you have access to the codebase (or the user described the tech stack):

- Map spec elements to existing components (e.g., "restyle your existing `<Card>`, don't create a new one")
- Identify the component library / design system in use (shadcn, MUI, Ant, custom)
- Note where Tailwind classes can be swapped vs. where custom CSS is needed

If the component library is unknown, flag it as a question.

---

## PRESENT DESIGN SPEC

Display the full specification:

```
**Fingerprint Scan Results:**
- P1 issues found: {count} — {summary}
- P2 issues found: {count} — {summary}
- Composite assessment: {holistic redesign needed / piecemeal fixes sufficient}

**Styling Changes ({count}):**
{For each change: element, current, proposed, rationale}

**Design Recommendations ({count}):**
{For each: what to change, rationale, flagged as "discuss before implementing"}

**Omitted Elements (still required):**
{List from {omissions_list}, or "All visible elements are addressed in this spec."}

**Styling Tokens:**
- Colors: {key hex values or Tailwind names}
- Font sizes: {px values}
- Spacing: {key padding/margin values}
- Border radius: {values}
- Shadows: {values}

Ready to finalize handoff? (y/n/adjust)
```

> **AUTONOMOUS MODE:** If `autonomous_mode` is `true`, skip the confirmation menu. Proceed immediately to step-03.

---

## ON USER FEEDBACK

1. **Diagnose the real issue** — "I don't like it" means something specific. Find it.
2. **Fix it** — don't add process, add quality.
3. **Re-run the cross-check** against `{screenshot_inventory}`.
4. **Be decisive** — the user's aesthetic preferences are valid. Adjust.

---

## NEXT STEP DIRECTIVE

When confirmed, explicitly state:

"**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/design-agent/steps/step-03-handoff.md`"

---

## SUCCESS METRICS

- Fingerprint scan completed and documented
- Every design decision has exact values and rationale
- Omissions list accounts for all `{screenshot_inventory}` elements
- Recommendations clearly separated from styling-only changes
- Component mapping attempted (or flagged as unknown)

## FAILURE MODES

- Skipping the fingerprint scan
- Vague recommendations without exact values ("make it lighter")
- Missing elements from `{screenshot_inventory}` without adding to `{omissions_list}`
- Not separating styling changes from feature-level recommendations
- Proposing feature removals without flagging them as "discuss first"
