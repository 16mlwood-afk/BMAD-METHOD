# Step 04 — Emit Code-Shaped Token Bundle

**Goal:** Express the brand identity as **renderable code** Claude Design can ingest. The form says "What works best: code and designs" and ingests via GitHub — a markdown doc underfeeds it. This step emits a small, self-contained, frontend-focused bundle of real values.

---

## 1. Bundle location & contents

Write to `{bundle_dir}` = `{planning_artifacts}/design-system/`:

- **`tokens.css`** — every brand-identity value as CSS custom properties under `:root` (color, type scale, spacing, radius, shadow, status colors). Real values only — no placeholders.
- **`sample.html`** — a single self-contained page that applies the tokens to representative components (buttons, a data table, status badges, a form field, headings). This is the "design" half of "code and designs" — it shows the tokens in use so Claude Design learns the *system*, not just a variable list. Inline the `tokens.css` via `<link>` or a `<style>` block so the file renders standalone.
- **`README.md`** — names the source (`brand-identity.md` version N), the project, and a one-line "this is the design-system reference Claude Design ingests" note.

The bundle is **derivative** of `brand-identity.md`. Record the source version in `README.md` so a future regeneration is traceable.

## 2. Also align the real token surface (framework-aware)

Claude Design ingests best from the **real frontend**, so the project's actual token surface should agree with the bundle. Based on `{framework}` / `{token_surface}`:

- **`next` / `react` + Tailwind** → propose the `theme.extend` colors/fonts/spacing in `tailwind.config.*` and the `:root` vars in the global stylesheet (`globals.css`) so they match `tokens.css`. Set `{frontend_subfolder}` to the app/src frontend dir.
- **`svelte` / `vue`** → align the equivalent token file / global style.
- **`none` (no framework yet, greenfield)** → the bundle in `{bundle_dir}` *is* the frontend surface for now. Set `{frontend_subfolder}` to `{bundle_dir}`'s repo-relative path.

**Do not** scaffold framework code the project hasn't opted into. If aligning the real token surface means creating/altering app files, present the diff and get explicit approval first — that is app code, separate from the always-safe `{bundle_dir}` artifact. If the user declines, the bundle alone still serves the form.

## 3. Render check

Open `sample.html` (headless screenshot or visual check) to confirm it renders with the tokens applied and contains no placeholder text or broken vars. A bundle that doesn't render is not shippable — fix before proceeding. This mirrors `design-synthesize`'s "the bundle is the design" discipline: explicit values, no interpretation required of the consumer.

## NEXT

→ **step-05-assemble-claude-design-intake.md**
