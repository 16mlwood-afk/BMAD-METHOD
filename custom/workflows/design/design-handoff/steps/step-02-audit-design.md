---
name: 'step-02-audit-design'
description: 'Audit existing design system: tokens, patterns, reference pages'
---

# Step 2: Audit Existing Design System

**Goal:** Understand the visual language already in place so Claude Design can work within (or intentionally break from) the existing system.

---

## GREENFIELD SKIP — check first

**If `{skip_step_02}` is true (set in step-01 §1c when `{is_greenfield}`), SKIP this entire step** and proceed to step-03. There is nothing built to audit — a greenfield project has no other pages and no in-app design language; the visual direction comes entirely from `docs/design-policy.md` (residue + named overlay per §1c gap rule 3), already loaded as `{brand_identity}` in step-01 §1b. Do NOT attempt to read CSS/token files or "other pages" (there are none). `{design_tokens}`/`{existing_patterns}`/`{reference_pages}` are sourced from the policy; `{hard_failures}` from the policy's hard-failure list.

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

Set `{reference_pages}` from observing which pages look best. **A page picked this way is not an accepted reference**: in §3a it may be offered only as `unconfirmed`, which Gate 1 reports.

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
- `{picture_of_good}` ✓ (§3a — a reference with its recorded acceptance, or a stated reason there is none; and 3–8 components) · `{type_policy_conflict}` (set only when the project policy mandates a data face)

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03-generate-brief.md`

---

## 3a. The picture of good — one accepted reference and a short vocabulary (EVERY run)

> **Claude Design, 2026-10-04:** *"There was no picture of good. You kept the existing page from me so I
> wouldn't anchor on it, which also removed the product's visual vocabulary... One reference, like v7
> now, would have done more than pages of rules."* Standard: `../../shared/presentation-floor.md` §12 O1.

Runs on every run, greenfield included (a greenfield project usually ends at step 3 below). Set
`{picture_of_good}`.

**1. Find ONE reference screen, in this order, and stop at the first that exists:**

1. **The latest accepted iteration of this design.** A design bundle or screenshot of this same surface
   that the owner accepted, or that `design-tuning` closed as approved. Typical on a re-run, a
   `policy-delta`, an `elevation` or a `refine-screen`. Set `is_this_surface: true`. This is the one file
   about the target the designer may open; the developer-built current view stays on the DO-NOT-READ list.
2. **An accepted surface from the same product family.** A page listed as a reference page in the brand
   identity or design policy, or a surface whose design the owner accepted (an approved bundle on `main`,
   an owner sign-off in the project's records).
3. **None.** Set `reference` to nothing and write `none_reason` in plain words: what was looked for and
   why nothing qualifies (*"this is the first designed surface in the product"*).

**Acceptance is EVIDENCED, never judged here.** Record `accepted_by`: who accepted it and when, with
where that is recorded. A page this step merely thinks looks good (the "existing" variant's
`{reference_pages}`) is offered as `accepted_by: "unconfirmed — picked by the workflow, not accepted by
the owner"`. Gate 1 does not fail that; it **reports** it, and the close-out says so. Never write an
acceptance that is not on record.

**2. Say what to take and what not to copy.** `borrow`: the vocabulary and the level of finish, named
(*"its grouped table, its record sheet, how quiet its secondary text is"*). `not_copy`: the layout, and
why it does not transfer (*"that page compares terms; this one ranks lines"*). Give `where` as a path
the designer can open in the repository (a screenshot or a bundle file tracked on `main`) or a URL. A
reference the designer cannot open is not a reference: if only a live route exists, capture a
screenshot into the repository and name that file.

**3. Name 3–8 components** as `vocabulary`, each `{component, use}`, in plain words and from the
reference and the product's design system, never from the target's current view: *a grouped table with
aligned columns · an expandable record sheet of label and value rows · a status dot with the stage in
text*. With no reference, take them from the design system or the brand identity's component section;
with neither, name the two or three forms the data's shape calls for and say they are the workflow's
suggestion.

**4. Note a type-by-datum mandate.** If the project design policy requires a second typeface for codes
or amounts (a data or monospace face), set `{type_policy_conflict}` = `{what, source}` quoting the
policy line. Do not edit the policy. Step-03 carries the project's rule and lists the conflict in Part 5.

Add `{picture_of_good}` and `{type_policy_conflict}` to the summary below.
