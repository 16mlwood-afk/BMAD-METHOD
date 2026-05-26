---
name: 'step-02-analyze'
description: 'Compare screenshot against brief constraints, visual references, and corporate guardrails — categorize all findings'
---

# Step 2: Analyze Screenshot

**Progress: Step 2 of 3** — Next: Generate Correction (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Evaluate ONLY against the brief's explicit constraints — do not inject personal design opinions.
- Be precise: name the specific constraint violated, cite the section, describe what you see in the screenshot.
- A violation is binary — it either violates a stated constraint or it doesn't. "Feels wrong" is not a violation.
- When comparing against visual references, note deviations from the referenced product's pattern — but only when the brief or references explicitly state to match that pattern.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From step 01:
- `{feature_name}`, `{brief_path}`, `{iteration_number}`
- `{brief_constraints}`, `{corporate_guardrails}`, `{visual_references}`
- `{previous_violations}`

The user has provided screenshot(s) of Claude Design's output in the conversation.

## SEQUENCE OF INSTRUCTIONS

### 1. Inventory the Screenshots

Identify what pages/views are shown in the screenshot(s):
- Which route is depicted? (e.g., `/upload`, `/invoices`)
- Is this a full page or a detail/component view?
- Note the viewport width if discernible

### 2. Check Corporate Guardrails (if applicable)

If `{corporate_guardrails}` is populated, run through each anti-pattern check:

**Aesthetic checks:**

| Check | What to look for | Violation? |
|-------|-----------------|------------|
| Background tint | Any cream, warm, or off-white background — must be pure white or cool neutral gray | Y/N |
| Typography family | More than one sans-serif, or any personality/display fonts | Y/N |
| Monospace abuse | Monospace used in headings, labels, navigation, or section titles (OK in IDs, codes, tabular numbers) | Y/N |
| Decorative color | Color used for personality or branding rather than functional state indication | Y/N |
| Dark mode tint | Navy, deep blue, or warm dark — must be true dark neutrals if dark mode is shown | Y/N |

**Voice checks:**

| Check | What to look for | Violation? |
|-------|-----------------|------------|
| Marketing copy | Aspirational headlines, agency voice, taglines on internal pages | Y/N |
| Unexplained badges | Numeric or icon badges without adjacent text labels | Y/N |
| Truncated text | Text cut off without a visible tooltip/expand affordance | Y/N |
| Labeling style | Editorial numbering ("01 —"), playful labels, non-functional section names | Y/N |

**AI fingerprint checks:**

| Check | What to look for | Violation? |
|-------|-----------------|------------|
| Bento grid | Asymmetric mixed-size card grid layout | Y/N |
| Hero section | Tagline, stat row, or marketing-style header on an internal page | Y/N |
| Dashboard card grid | Row of metric cards as the page's opening element | Y/N |
| Excessive whitespace | Massive padding (>24px section gaps, >16px card padding for a dense tool) | Y/N |
| Purple/violet primary | Purple used as the primary accent color | Y/N |
| Gradients/glass | Gradient text, gradient backgrounds, glassmorphism effects | Y/N |
| Oversized radius | Border radius >8px on containers (pill shapes OK on tags/badges only) | Y/N |
| Heavy shadows | Card shadows used decoratively rather than for elevation hierarchy | Y/N |
| Colored dividers | Gradient or colored section dividers instead of 1px solid border | Y/N |
| Colored nav icons | Different color per navigation item | Y/N |
| Semantic card fills | Entire card background colored by status (green card, red card) | Y/N |
| Chatty empty states | Illustrations or enthusiastic copy in empty states | Y/N |
| Icon overload | Icons on every label, heading, and menu item | Y/N |
| Hover scale | Scale transforms on card hover instead of background/border change | Y/N |
| Animated counters | Number counters that animate up to their value | Y/N |
| Excessive badge colors | More than 4 distinct badge/status colors | Y/N |

**Self-test:** Would someone guess this design is AI-generated? If yes, that is itself a violation.

### 3. Check Brief-Specific Constraints

Walk through `{brief_constraints}` and check each one:

- **Navigation:** Does the mockup respect the navigation position stated in the brief? (e.g., if brief says pages are in existing nav, does the mockup invent a new nav?)
- **Responsive target:** Is the mockup at the correct viewport width?
- **Data density:** Does the layout handle the stated data volume without overflow or cramming?
- **Interaction model:** Are the stated user actions (bulk operations, filters, etc.) accommodated?
- **Design tokens:** If using existing tokens, are the colors/fonts/spacing consistent with the stated values?
- **Invented elements:** Does the mockup include branding, product names, version numbers, or UI elements not in the brief?

### 4. Check Against Visual References

If `{visual_references}` is populated, check alignment:

For each named product reference, evaluate whether the mockup borrows the specified patterns:

| Reference | Specified pattern | Followed? | Notes |
|-----------|------------------|-----------|-------|
| {product} | {what to borrow} | Y/N | {what the mockup does instead} |

Flag deviations only where the reference explicitly states what to match. Don't penalize the mockup for not being a pixel-perfect copy of any referenced product — references describe direction, not literal reproduction.

### 5. Identify What Works

List elements that are correct, well-executed, or solve a problem well. These go in the "keep" section of the correction message. Be specific:
- "Table column layout matches the specified anatomy"
- "Filter chips follow the chip-based pattern from the brief"
- "Status badges use 4 colors as required"

### 6. Compare Against Previous Iteration

If `{previous_violations}` is populated:

- For each previous violation, check if it's resolved → add to `{fixed_violations}`
- For each previous violation still present → mark as "persisting" with iteration count
- New violations not in the previous list → mark as "new"

If this is iteration 1, skip this step.

### 7. Compile Findings

Store:

- `{current_violations}` — all violations found, each with:
  - ID (V1, V2, V3...)
  - Category (corporate-guardrail | brief-constraint | visual-reference | ai-fingerprint)
  - Severity (hard-failure | issue)
  - Description (what the brief says vs. what the mockup shows)
  - Status (new | persisting-from-V{N} | regressed)
- `{fixed_violations}` — violations from previous iteration that are now resolved
- `{kept_elements}` — list of elements that work well
- Overall assessment: PASS (0 hard failures) | FAIL (1+ hard failures)

---

## COMPLETION

Load and follow: `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-03-generate-correction.md`

---

## SUCCESS METRICS

- Every corporate guardrail checked (if applicable)
- Every brief constraint checked
- Every visual reference checked (if applicable)
- Comparison against previous iteration completed (if applicable)
- Findings categorized with IDs, severity, and status
- "What works" list populated — not just negative findings
- Overall assessment determined

## FAILURE MODES

- Injecting design opinions not grounded in the brief ("I think the spacing feels too tight" when the brief doesn't specify spacing)
- Missing a hard failure because the mockup "looks nice"
- Flagging something as a violation when the brief explicitly allows it
- Not comparing against previous iteration when state exists
