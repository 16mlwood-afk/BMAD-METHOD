# Step 03 — Establish Brand Identity (tactical, concrete tokens)

**Goal:** Produce `{planning_artifacts}/brand-identity.md` — the concrete, value-level expression of the design system and the **priority source** downstream workflows inject. This is where the policy's directional intent becomes exact hex codes, px values, fonts, and class patterns.

---

## 1. If brand identity already exists

`{has_brand_identity}` = yes → load `{brand_identity_path}`, verify its `version` frontmatter, and skip to NEXT (the token bundle in step 04 will regenerate from it). Confirm it isn't stale relative to the policy; if it is, offer to refresh the affected sections.

## 2. If none exists — populate from the template

Load `brand_identity_template` and populate every section. The population method depends on phase:

### Greenfield (`{project_phase}` = greenfield)

There is little or no existing UI to audit. **Design the tokens** from the chosen policy direction + the user's intent:

- Derive a concrete palette (exact hex) from the policy's tone/register and any reference products it named.
- Choose typography (exact families) consistent with the register — propose, confirm with the user, do not silently pick.
- Set density, spacing scale, radius, and status-color system as concrete values.
- Fill "What it's NOT" with 2-3 concrete anti-patterns from the policy's anti-references.

**`[led]`** — Claude decides every value from the committed `{direction}` and writes them directly. No proposal gate. The full palette/type/density set is shown in the step-06 end review for veto, and lands in the delivery PR.
**`[collaborative]`** — Every value the user hasn't specified is **proposed and confirmed**, never imposed. Surface the proposed palette/type as a short block the user can approve or adjust before writing.

### Brownfield / mixed (`{project_phase}` = brownfield | mixed)

Follow the template's audit method: read `tailwind.config.*`, global CSS, 3-5 representative pages, shared components, and status/color utilities. Extract recurring patterns — **what the app actually is**, not what a template says it should be. Fill the template with the extracted concrete values. Identify 2-3 internal reference pages and 2-3 external influences.

## 3. Write the document

Write to `{brand_identity_path}` (= `{planning_artifacts}/brand-identity.md`) with frontmatter:

```yaml
---
type: brand-identity
project: {project_name}
last_updated: {date}
version: 1
derived_from_policy: docs/design-policy.md   # provenance link, not a brief-revision block
---
```

No `{placeholder}` tokens may remain — every value is concrete. This document, not the policy, is what step 04 reads to emit code.

## NEXT

→ **step-04-emit-token-bundle.md**
