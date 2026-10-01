---
name: claude-design-intake-template
description: 'Template for the Claude Design intake card produced by onboard-design-system step 05. Mirrors the fields of the claude.ai/design "Set up your design system" form so the user can fill it field-by-field. Populated per project and saved at {planning_artifacts}/claude-design-intake.md.'
---

# Claude Design Intake Card Template

> **Purpose:** A paste-ready card mapped 1:1 to the claude.ai/design "Set up your
> design system" form. Each block below corresponds to one form field.
> **Location:** Save the populated version at `{planning_artifacts}/claude-design-intake.md`.
> **Form URL:** `claude.ai/design` → "Set up your design system" → "Continue to generation".

---

## File Template

```markdown
---
type: claude-design-intake
project: {project_name}
created: {date}
brand_identity_version: {N}          # the brand-identity.md version this card reflects
design_system_url_status: {pending-delivery | live | local-only}
---

# Claude Design Intake — {project_name}

> Fill the form at claude.ai/design → "Set up your design system" with the blocks below.

## 1. Company name and blurb (or name of design system)

{One paragraph. What this product IS + the surfaces it spans + its register.
 Sourced from design-policy.md (product type) + brand-identity.md §1.
 Concrete, no marketing fluff. Mirror the form's example shape.}

## 2. Link code on GitHub

- **Repo:** {repo_url}                          # status: {PENDING DELIVERY | live | LOCAL ONLY}
- **Attach ONLY this curated bundle subfolder:** {seed_subfolder}   # = {planning_artifacts}/design-system/
- ⚠️ **Do NOT connect the whole repo or the live `src/` frontend dir.** The
  "Set up your design system" form SEEDS a persistent workspace and generates a
  reusable UI kit ONE-SHOT from whatever is attached — so attach only the curated,
  current-UI-FREE bundle (tokens.css + sample.html). Connecting the live frontend
  re-encodes current product screens into every future prototype.

## 3. Upload a .fig file

{path to user's Figma export, OR "(none yet — optional)". Parsed locally in-browser, never uploaded.}

## 4. Add fonts, logos and assets

- **Fonts:** {exact families + where to get them, OR "(none yet — optional)"}
- **Logos/assets:** {repo paths that exist, OR "(none yet — optional)"}

## 5. Any other notes

{2-4 sentences: register + density + "what it's NOT" (brand-identity.md) and
 anti-references (design-policy.md). Project-specific tone, not generic.}

---

## Provenance

- Source of truth: `brand-identity.md` v{N} → `docs/design-policy.md`
- Token bundle: `{planning_artifacts}/design-system/` (delivered to origin/main: {yes/no})
- Re-run `onboard-design-system` steps 04-06 when the system changes so the GitHub
  source Claude Design reads stays current.
```
