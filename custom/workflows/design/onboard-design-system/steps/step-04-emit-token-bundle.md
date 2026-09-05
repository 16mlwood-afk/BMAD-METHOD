# Step 04 — Emit Code-Shaped Token Bundle

**Goal:** Express the brand identity as **renderable code** Claude Design can ingest. The form says "What works best: code and designs" and ingests via GitHub — a markdown doc underfeeds it. This step emits a small, self-contained, frontend-focused bundle of real values.

---

## 1. Bundle location & contents

Write to `{bundle_dir}` = `{planning_artifacts}/design-system/`:

- **`tokens.css`** — every brand-identity value as CSS custom properties under `:root` (color, type scale, spacing, radius, shadow, status colors). Real values only — no placeholders.
- **`sample.html`** — a single self-contained page that applies the tokens to an **idealized component vocabulary**: buttons (primary/secondary/ghost, default/hover/disabled), inputs and a form field, status/semantic badges, cards, a generic table/row primitive, and the type scale (headings → body → caption). Make it a fuller component *sheet*, not a sparse swatch list — it must be self-sufficient enough to be the **SOLE seed** so the generated UI kit derives entirely from this vocabulary. **It must show HOW THINGS LOOK (color/type/spacing/radius/status applied to generic components) and must NOT replicate any real product page, screen, route component, or the app's IA/composition.** Inline `tokens.css` via `<link>` or a `<style>` block so the file renders standalone.
- **`README.md`** — names the source (`brand-identity.md` version N), the project, and a one-line "this is the design-system reference Claude Design ingests" note.

The bundle is **derivative** of `brand-identity.md`. Record the source version in `README.md` so a future regeneration is traceable.

## 2. Set the seed pointer, and (separately) align the real token surface

**These are two unrelated concerns — do not conflate them.**

**(a) The seed pointer — `{seed_subfolder}` ALWAYS points at the curated bundle.** For EVERY framework and EVERY phase (greenfield, brownfield, mixed), set `{seed_subfolder}` to `{bundle_dir}`'s repo-relative path (`{planning_artifacts}/design-system/`). This is the only thing Claude Design connects at setup. **Do NOT set `{seed_subfolder}` to the app/`src/` frontend dir** — that directory contains current product screens/components, and connecting it makes Claude Design copy them into the persistent workspace (observed: `src/`, `_bmad/`, `_bmad-output/` get pulled in) and template the one-shot UI kit from the existing UI. "Claude Design ingests best from the real frontend" is exactly backwards for the setup seed: the real frontend is precisely what must be excluded.

**(b) Align the app's own token surface — code hygiene, NOT the seed.** So the live app and the system agree, align the project's actual token files to `tokens.css`. This does NOT change the seed target. Based on `{framework}` / `{token_surface}`:

- **`next` / `react` + Tailwind** → propose the `theme.extend` colors/fonts/spacing in `tailwind.config.*` and the `:root` vars in the global stylesheet (`globals.css`) so they match `tokens.css`. (The seed pointer still points at `{bundle_dir}`, never here.)
- **`svelte` / `vue`** → align the equivalent token file / global style.
- **`none` (no framework yet, greenfield)** → there is no separate surface to align; the bundle in `{bundle_dir}` is the only token surface.

Aligning these app token files makes the running app match the system — it never licenses connecting the app frontend at setup.

**Do not** scaffold framework code the project hasn't opted into — adding Tailwind/CSS-in-JS where none exists is structural, not theming, and is out of scope in both modes. Aligning *existing* token files (a present `tailwind.config.*`, an existing `globals.css`) is theming and in scope:

- **`[led]`** — Apply the alignment to existing token files autonomously. These are app-code changes, so they flow through the step-06 delivery PR, which is the review/veto surface (and trivially revertable). Include them in the end-review summary.
- **`[collaborative]`** — Present the diff and get explicit approval before altering any app file. If the user declines, the bundle alone still serves the form.

## 3. Render check

Open `sample.html` (headless screenshot or visual check) to confirm it renders with the tokens applied and contains no placeholder text or broken vars. A bundle that doesn't render is not shippable — fix before proceeding. This mirrors `design-synthesize`'s "the bundle is the design" discipline: explicit values, no interpretation required of the consumer.

## NEXT

→ **step-05-assemble-claude-design-intake.md**
