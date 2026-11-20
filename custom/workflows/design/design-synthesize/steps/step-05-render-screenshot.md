---
name: 'step-05-render-screenshot'
description: 'Render each bundle/<screen>.html via headless Playwright. Halt on Gate 4 if Playwright is unavailable. Honor --no-render dev escape hatch with manifest flag.'
---

# Step 5: Render Screenshot

**Goal:** Produce `bundle/screenshot-<screen>.png` for every screen in `{screens}` by rendering the HTML through headless Chromium. The screenshot is for human visual review only — `design-implement` never reads it — but the production contract requires it to exist.

**Gate owned:** Gate 4 — Playwright availability (workflow.md §APPROVAL GATES).

---

## RULES

- **Screenshots are for humans, not for `design-implement`.** `design-implement` reads `bundle/<screen>.html` + `bundle/tokens.css` and extracts CSS values. The screenshot exists so the user can visually verify the bundle before consuming it downstream.
- **Halt loudly on Playwright absence.** Do NOT silently skip the screenshot step. A bundle without a screenshot is not a production bundle — `design-implement` is configured to refuse such bundles unless the `--no-render` dev flag was used.
- **One browser, one viewport per screen.** Headless Chromium only. Brief's `responsive` field picks the viewport; default `1440 × 900`. No Firefox/WebKit cross-rendering.
- **Render must produce something.** An empty viewport (uniform white pixels at the bundle's background color, or unresolved CSS) is a synthesis failure → return to step 4 with the empty-render note.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Check the --no-render flag

If the workflow was invoked with `--no-render`:

- Skip the rest of this step.
- Set `{dev_no_render} = true`.
- Set `{compliance_state} = "dev_only"` (overrides any value from step 6).
- Print: `⚠ --no-render in effect: skipping screenshot step. Bundle will be marked dev-only in manifest. design-implement WILL refuse this bundle.`
- Load step 6 and proceed.

Otherwise set `{dev_no_render} = false` and continue.

### 2. Check Playwright availability (Gate 4)

```bash
npx playwright --version
```

- **Exits 0** → Playwright is installed. Capture the version into `{playwright_version}` for the manifest. Proceed to step 3.
- **Exits non-zero or `npx playwright` is not found** → Gate 4 fails. Halt with:

  ```
  Gate 4 (Playwright availability): npx playwright is not available.

  Install with:
    pnpm add -D @playwright/test && npx playwright install chromium
    # or:
    npm install --save-dev @playwright/test && npx playwright install chromium

  Then re-invoke design-synthesize. Do NOT use --no-render to bypass this — bundles emitted with --no-render are refused by design-implement.
  ```

Do not attempt to install Playwright automatically — `npm install` is forbidden by project rules (see CLAUDE.md). The user installs; this workflow halts and waits.

### 3. Resolve the viewport

**Read the brief's §4g CANONICAL viewport FIRST — the desktop default is a fallback, not a premise.** Resolution order:

1. **Brief §4g canonical viewport (authoritative when present).** If the brief declares a canonical viewport (`mobile-first`/handheld-first ⇒ **375 × 812 portrait**; `desktop-only`/`desktop-primary` ⇒ **1440 × 900**; `tablet-down` ⇒ the brief's named tablet reference), render THAT as the primary screenshot — `screenshot-<screen>.png`, unsuffixed. This is the canonical render, and it is the one `design-implement` pixel-matches against.
2. `responsive.viewport` / `responsive.dpr` in `{brief_frontmatter}`, if §4g is absent.
3. **Fallback only: `1440 × 900` at DPR 2.** Historically this default was described as "the project's primary desktop target" — that framing is wrong on any handheld-first surface and is exactly how a phone-primary brief acquired a desktop-premised bundle. Treat it as *no viewport was declared*, not as *desktop is correct*.

**Additive viewports render SECOND and are named as such.** Every non-canonical breakpoint the brief lists goes into a suffixed file (`screenshot-<screen>-additive-tablet.png`, `screenshot-<screen>-additive-desktop.png`) — the `additive-` prefix in the filename is deliberate: a bare `-desktop` suffix beside an unsuffixed phone render reads as two peers. **Never render a viewport listed in the brief's `device_exclusions`.**

The manifest's `screens` array records, per entry, `viewport`, `dpr`, and a **`role`** of `canonical` | `additive`. Exactly one entry per screen carries `canonical`. A screens array with no canonical entry, or two, is a synthesis failure — return to step 4 rather than emitting an unlabelled multi-viewport bundle.

### 4. Write the Playwright runner script

Write a one-shot script to `{bundle_dir}/.render.mjs` (the leading `.` is intentional — it's a render artifact, not part of the bundle's design content):

```javascript
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const screens = [
  // Populated from {screens} array. Each entry: { name, file, viewport, dpr }
  // Example: { name: 'main', file: 'main.html', viewport: { width: 1440, height: 900 }, dpr: 2 }
];

const browser = await chromium.launch({ headless: true });
try {
  for (const s of screens) {
    const context = await browser.newContext({
      viewport: s.viewport,
      deviceScaleFactor: s.dpr,
    });
    const page = await context.newPage();
    await page.goto(`file://${path.join(__dirname, s.file)}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(200); // settle
    // role: 'canonical' -> unsuffixed; 'additive' -> `-additive-<label>` (never a bare `-desktop`,
    // which reads as a peer of the canonical render). Exactly one canonical entry per screen.
    const suffix = s.role === 'additive' ? `-additive-${s.label}` : '';
    const outPath = path.join(__dirname, `screenshot-${s.name}${suffix}.png`);
    await page.screenshot({ path: outPath, fullPage: true });
    console.log(`✓ rendered ${outPath}`);
    await context.close();
  }
} finally {
  await browser.close();
}
```

### 5. Execute the renderer

```bash
cd {bundle_dir} && node .render.mjs
```

Per-screen handling:

- **Success:** screenshot file exists at `{bundle_dir}/screenshot-<screen>.png` and is non-empty (>0 bytes). Record into `{screenshots_rendered}`.
- **HTML parse error** (Playwright reports a navigation error): synthesis failure. Capture the parse error and return to step 4 with: `step 5: bundle/<screen>.html failed to parse. Error: <parser message>. Fix the malformed HTML.`
- **Empty render** (screenshot is a uniform color across the entire viewport — detectable via a quick byte-distribution check on the PNG): synthesis failure. Return to step 4 with: `step 5: bundle/<screen>.html rendered an empty viewport. Likely cause: missing tokens.css link, fatal CSS error, or hidden root element. Inspect the HTML before retrying.`
- **External network fetch attempted** (Playwright logs a network request to a host other than `file://`): synthesis failure. Bundles must render offline. Return to step 4 with: `step 5: bundle/<screen>.html attempted an external fetch (<url>). Inline the resource or remove the reference.`

### 6. Clean up the render script

After all screens render successfully, delete `.render.mjs`:

```bash
rm {bundle_dir}/.render.mjs
```

The render script is an ephemeral build artifact. Leaving it in the bundle directory clutters the audit trail and risks future runs being confused about which `.mjs` is the renderer vs a synthesis output.

### 7. Print the render summary and proceed

```
✓ Screenshots rendered:
  playwright:  {playwright_version}
  viewport:    {width}×{height} @ DPR {dpr}
  rendered:    {comma-separated screenshot filenames}

Proceeding to step 6: self-critique.
```

Then load `step-06-self-critique.md` and follow it.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{playwright_version}` (or `null` if `--no-render` was used)
- `{dev_no_render}` (true | false)
- `{screenshots_rendered}` — list of screenshot file paths (or empty list if `--no-render`)
- Files exist: `{bundle_dir}/screenshot-<screen>.png` for every `screen ∈ {screens}` — UNLESS `--no-render` was used.

Any unset required variable, or any missing screenshot file in non-`--no-render` mode, is a workflow bug — halt before step 6.
