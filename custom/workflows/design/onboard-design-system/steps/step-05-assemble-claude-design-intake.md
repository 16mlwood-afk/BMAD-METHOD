# Step 05 — Assemble the Claude Design Intake Card

**Goal:** Produce `{intake_card_path}` (= `{planning_artifacts}/claude-design-intake.md`) — a paste-ready card mapped 1:1 to the fields on the **claude.ai/design "Set up your design system"** form. After this, the user can fill every field without guessing. This card IS the workflow's primary deliverable.

---

## 1. Load the template

Load `intake_template` and fill each field from the established artifacts (mapping table in `workflow.md` §SOURCE-OF-TRUTH).

## 2. Fill each form field

**Company name and blurb (or name of design system)** → `{company_blurb}`
One paragraph. Pull product-type + what-it-is from `design-policy.md`, register from `brand-identity.md` §1. Write it the way the form's example reads ("X: <what it is>, <surfaces it spans>"). Keep it concrete and free of marketing fluff.

**Link code on GitHub** → `{repo_url}` + the curated bundle subfolder
- The repo URL from `{repo_url}`.
- The subfolder to attach: `{seed_subfolder}` — which resolves to the **curated bundle dir `{bundle_dir}` for ALL phases**, greenfield AND brownfield. The bundle already carries the aligned token values; the live app/`src/` frontend must NOT be the seed.
- ⚠️ **Do not attach the whole repo or the live frontend dir.** Claude Design seeds a *persistent workspace* and generates a reusable UI kit from whatever is attached, so current product screens would be re-encoded into every future prototype. The subfolder is the curated current-UI-free vocabulary regardless of codebase size — bias-exclusion is the reason, not a size optimization.
- ⚠️ This link is only valid **after step 06 delivers the bundle to `origin/main`.** The card marks it `PENDING DELIVERY` until step 06 confirms the merge, then flips it to the live URL.

**Upload a .fig file** → user-supplied
If the user has a Figma export, note where it is and that it's parsed locally in-browser (never uploaded). If none, mark `(none yet — optional)`. Never fabricate.

**Add fonts, logos and assets** → from `brand-identity.md` + project assets
List the exact font families (and where to get them — e.g. Google Fonts / local files) and any logo/asset paths that exist in the repo. Mark missing ones `(none yet — optional)`.

**Any other notes** → distilled guidance
2-4 sentences from `brand-identity.md` register + density + "what it's NOT", plus `design-policy.md` anti-references. This is where tone lands ("warm, earthy, rounded" in the form's example) — make it specific to this project, not generic.

## 3. Write the card and present it

Write `{intake_card_path}`. Then present the card inline to the user as copy-paste blocks, each labeled with its form field, so they can fill the form field-by-field. Include the direct form context: the system is configured at `claude.ai/design` → "Set up your design system" → "Continue to generation".

## NEXT

→ **step-06-deliver-and-guide.md** (delivers the bundle so the GitHub link works, then finalizes the card).
