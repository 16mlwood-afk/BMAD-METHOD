---
name: 'step-02-audit-design'
description: 'Audit existing design system: tokens, patterns, reference pages'
---

# Step 2: Audit Existing Design System

**Goal:** Understand the visual language already in place so Claude Design can work within (or intentionally break from) the existing system.

---

## RULES

- Read CSS/token files to extract the actual values — don't guess
- Identify patterns from **other pages in the app** — NOT the target feature's page. The target feature's current layout is a developer implementation, not a design standard. Auditing it would bias the designer toward the existing structure.
- Note what works well AND what feels inconsistent in the app's existing design language — this gives the designer room to improve
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From step-01:
- `{feature_name}`, `{feature_scope}`, `{feature_purpose}`
- `{data_shape}`, `{api_surface}`, `{implementation_files}`, `{user_context}`

---

## EXECUTION SEQUENCE

### 1. Extract Design Tokens (conditional)

**If `{design_system}` = "external":** SKIP this step entirely. Set `{design_tokens}` = "EXTERNAL — using {design_system_name}". Do NOT read CSS token files — inlining dev tokens when an external design system exists is a form of design bias (anchoring the designer to developer placeholder values).

**If `{design_system}` = "existing":** Extract tokens from the codebase:

Find and read the project's design token files:

```bash
# Common locations
find . -name "tokens.css" -o -name "variables.css" -o -name "theme.css" -o -name "colors*.css" | head -5
find . -name "tailwind.config.*" | head -2
```

Capture as `{design_tokens}`:
- **Colors:** background, foreground, primary, muted, border, card, accent colors
- **Typography:** font families, size scale, weight scale
- **Spacing:** padding/margin scale (4px grid? 8px grid?)
- **Borders:** radius values, border widths, border colors
- **Shadows:** if any
- **Transitions:** easing, duration

### 2. Identify Existing Component Patterns (conditional)

**If `{design_system}` = "external":** SKIP detailed pattern extraction. Set `{existing_patterns}` = "EXTERNAL — designer will apply {design_system_name} component patterns." Existing dev patterns would compete with the external design system's own component library.

**If `{design_system}` = "existing":** Extract patterns from other pages:

Look at 2-3 **other** pages in the app (NOT the target feature) for patterns. Good candidates:
- The page with the most complex data display (tables, cards, lists)
- The page with the best-looking forms/inputs
- The main dashboard or landing page

**WARNING:** Do NOT look at the target feature's page for patterns. Its structure is a developer implementation that should not influence the designer.

For each, note:
- Card/container patterns (border, radius, padding, background)
- Table/list patterns (row height, hover states, column alignment)
- Form patterns (input styling, button hierarchy, validation display)
- Status/badge patterns (colors, shapes, sizes)
- Header/section patterns (heading sizes, spacing, dividers)
- Empty state patterns
- Loading state patterns

Capture these as `{existing_patterns}`.

### 3. Identify Reference Pages

**If `{design_system}` = "external":** Set `{reference_pages}` = "N/A — external design system". Skip reference page identification — the external system IS the reference.

**If `{design_system}` = "existing":**

Set `{reference_pages}` — pages the designer should look at to understand the visual language:
- Which page is the "gold standard" for this app's design?
- Which page is closest in function to the feature being designed?

### 4. Define Constraints

Set `{constraints}` — hard requirements that limit design freedom:
- **Responsive breakpoints** — is this desktop-only? Mobile-first?
- **Data density** — how many items typically show? (10? 100? 1000?)
- **Accessibility** — any specific requirements (WCAG level, screen reader support)?
- **Performance** — any render constraints (virtualization needed for long lists)?
- **Navigation** — where does this page live in the app shell? Sidebar? Tab? Modal?
- **Interaction model** — does the user need to take bulk actions? Single-item focus?

---

## COMPLETION

Confirm the following state variables are populated:
- `{design_tokens}` ✓
- `{existing_patterns}` ✓
- `{reference_pages}` ✓
- `{constraints}` ✓

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03-generate-brief.md`
