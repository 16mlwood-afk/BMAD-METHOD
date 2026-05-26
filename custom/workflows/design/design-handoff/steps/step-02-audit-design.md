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
- `{brand_identity}`, `{brand_identity_path}`, `{design_system}`

---

## EXECUTION SEQUENCE

### 1. Design Tokens, Patterns, and References (conditional on design_system)

**If `{design_system}` = "branded" (brand identity exists):**

The brand identity document is the primary source. Extract directly from it:

- `{design_tokens}` ← sections 2 (Typography), 3 (Color System), 5 (Spacing & Layout)
- `{existing_patterns}` ← section 4 (Component Language)
- `{reference_pages}` ← section 6 (Reference Pages)
- `{hard_failures}` ← section 8 (Hard Failures)

**Do NOT re-extract tokens from CSS/Tailwind files** — the brand identity has already distilled the intentional design decisions from the codebase. Re-extracting from code risks pulling in incidental values that the brand identity deliberately excluded.

**Do verify** that the brand identity's token values still match the codebase (spot-check 2-3 values). If they've drifted, note it for the user but proceed with the brand identity values — they represent the intended design, not the current implementation.

**If `{design_system}` = "external":**

SKIP token extraction entirely. Set:
- `{design_tokens}` = "EXTERNAL — using {design_system_name}"
- `{existing_patterns}` = "EXTERNAL — designer will apply {design_system_name} component patterns"
- `{reference_pages}` = "N/A — external design system"
- `{hard_failures}` = empty (external system defines its own constraints)

**If `{design_system}` = "existing" (no brand identity, no external system):**

Fall back to extracting tokens from the codebase:

```bash
# CSS token files (framework-agnostic)
find . -name "tokens.css" -o -name "variables.css" -o -name "theme.css" -o -name "colors*.css" -o -name "globals.css" -o -name "app.css" | head -5
# Framework-specific config (whichever applies to this project)
find . -maxdepth 3 \( -name "tailwind.config.*" -o -name "panda.config.*" -o -name "uno.config.*" -o -name "stitches.config.*" -o -name "theme.config.*" -o -name "design-tokens.json" \) | head -5
```

Capture `{design_tokens}`: colors, typography, spacing, borders, shadows, transitions.

Look at 2-3 **other** pages (NOT the target feature) for `{existing_patterns}`: card styles, table patterns, badge patterns, button hierarchy.

Set `{reference_pages}` from observing which pages look best.

Set `{hard_failures}` from the generic anti-AI-slop guardrails (section 5 variant C template in step-03).

**WARNING for "existing" mode:** Without a brand identity, the extracted tokens are raw CSS values — they may include incidental choices (a shadow that was copied from a tutorial, a color that was a placeholder). The designer will treat them as intentional design decisions. Consider creating a brand identity document to disambiguate.

### 2. Define Constraints

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
- `{hard_failures}` ✓ (may be empty for external design systems)
- `{constraints}` ✓

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03-generate-brief.md`
