---
name: 'step-04b-rendered-page-checks'
description: 'Run the presentation-floor checks on the RENDERED DOM — the design bundle first, then the built page, both themes at 1440×900 — before commit. A failure the design drew goes back as a SENDBACK; a failure the build introduced is fixed. Called from step-04 §5b item 5; not a separate pass of the workflow.'
---

# Step 4b: Rendered-page checks — the presentation floor, measured

**Standard:** `../../../design/shared/presentation-floor.md` (STD-PRESENTATION-FLOOR-001, 2026-09-27).
**Tool:** `~/bmad-method-v6/tools/check-rendered-page.js` · goldens `npm run test:rendered-page` in the fork.

> **Owner, 2026-09-27, verbatim:** *"it's reading like a ledger printed on a screen... no font size
> enforcement... that yellow thing at the top, the most AI pattern I've ever seen, which hasn't been
> caught by our anti-AI patterns... audit text at the top... a complete violation of our user attention
> policy."*

**Why this step exists.** The grid (step-03) certifies that the code matches the design, and the copy
screen (step-04 §5b.4) reads strings. Neither looks at the rendered page as a reader meets it. The
price-list page shipped with a green grid and a clean copy screen while its headline and all 17 row
figures shared one size, 288 words sat above the first product, and an amber notice box repeated the
next action. Every one of those is measurable on the rendered DOM, and this step measures them.

## RULES

- **Runs on every design-implement pass that changes a rendered surface**, before §6 commit. Not
  optional, not skippable for "CSS-only" changes — a CSS-only change is exactly what moves a size.
- **The brief is the floor.** The checker reads the brief's `presentation-floor` block (Part 2b). A brief
  with no Part 2b predates 2026-09-27: run with the fork default floor (`--floor` built from
  `presentation-floor.md` §2) and say so in §9 — never skip the step because the brief is old.
- **Unchecked is not passed.** A check that could not run (no `data-answer`, no `data-first-item`, a
  snapshot not at 1440×900, an unparseable colour, no renderer available) is reported by name and
  blocks the merge exactly as a failure does, until it runs.
- **Never loosen the floor to pass.** Budgets are the brief's. Changing a budget is a brief revision
  (`design-handoff`), not an implementation decision.

## SEQUENCE

### 1. Check the DESIGN first — so a design failure goes back, not into the code

Render the design bundle (the runnable HTML from step-01, or the synthesize bundle) at **1440×900**, in
light and in dark, and capture a snapshot of each:

```bash
# Where playwright resolves from the project:
node ~/bmad-method-v6/tools/check-rendered-page.js --url "file://{bundle_html}" --brief "{brief_path}"
node ~/bmad-method-v6/tools/check-rendered-page.js --url "file://{bundle_html}" --brief "{brief_path}" --theme dark

# Where it does not: print the probe, run it in the page (Claude-in-Chrome javascript tool or the
# console) at 1440×900, save the JSON it returns, and check the file.
node ~/bmad-method-v6/tools/check-rendered-page.js --print-probe > /tmp/probe.js
node ~/bmad-method-v6/tools/check-rendered-page.js --snapshot {snapshot.json} --brief "{brief_path}"
```

**A failure here is in the design.** It is NOT fixed silently in the build — that would be an unlogged
departure, which step-04 §5c forbids. Record it as a `floor` departure and send it back under §5c's
SENDBACK with the check id, its evidence lines and the Part 2b clause it breaks. Where the fix is
unambiguous and mechanical (a size one token off the scale, capitals on a label), the SENDBACK may state
the fix; the design is still the authority for anything else.

### 2. Check the BUILT page — the same checks, the same brief

Render the built surface the same way (local dev server per the project's CLAUDE.md, or the deployed
URL where the project is production-only), both themes, at 1440×900:

```bash
node ~/bmad-method-v6/tools/check-rendered-page.js --url "{built_url}" --brief "{brief_path}" --json > {artifacts}/rendered-page-{target_slug}-light.json
node ~/bmad-method-v6/tools/check-rendered-page.js --url "{built_url}" --brief "{brief_path}" --theme dark --json > {artifacts}/rendered-page-{target_slug}-dark.json
```

**A failure the design did not have is a build defect: fix it and re-run.** The usual causes: a literal
`font-size` or colour copied from the bundle instead of the token (the price-list stylesheet had 25
literal sizes and 0 token uses), a local grey ramp, a missing `data-*` marker, a component default that
brings capitals or a tinted panel. A failure the design also had is already in the SENDBACK from §1.

**If the built page cannot be rendered in this run** (auth-walled, prod-only, no server): use step-04
§5b's fallback ladder — the bundle checks from §1 stand in, and the built-page check is **OWED**, named
in §9 with the exact command to run. It is never reported as passed.

### 3. Record it

In the §9 report, one line per theme: `rendered-page (light): 11 checks, 0 failed, 0 unchecked` — or the
failing ids with their one-line detail, and where each went (fixed in build · SENDBACK · owed). Keep the
JSON under `_bmad-output/implementation-artifacts/` beside the grid.

## What this does not prove

That the page reads well, that the answer is the right one, or that a reader gets it in five seconds. T0,
TD0 and TA1 stay a reader's judgement; the render-compare in step-04 §5b.2 stays the done-gate for
fidelity. These checks prove counts and presence: the sizes are the declared ones, the answer is the
largest text, nothing is tinted, boxed, striped, shouted or said twice, the top holds the answer and the
first item is on screen.
