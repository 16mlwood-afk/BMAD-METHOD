---
name: 'step-03-dom-render'
description: 'Render each affected route in Chrome, run dom-render lane checks, append findings.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review-pr'
thisStepFile: './step-03-dom-render.md'
---

# Step 3: DOM Render

**Goal:** For rules that can't be evaluated from source alone, render the affected routes in Chrome and run computed-style / layout / counting checks.

This step is **optional** — it runs only if `{chrome_available}` is true. If skipped, every `dom-render` lane rule must be listed in the coverage notes.

---

## AVAILABLE STATE

- `{affected_routes}` — routes whose rendered output may have changed
- `{checklist.dom_render}` — rules to check
- `{chrome_available}` — boolean (set in step-01)

---

## PRECONDITIONS

- `mcp__claude-in-chrome__*` tools must be loadable via ToolSearch.
- A running dev server reachable at a known base URL. Try in this order:
  - `http://localhost:8787` (wrangler pages dev — this project's standard)
  - `http://localhost:5173` (vite default)
  - `http://localhost:3000` (next/express default)

If none are reachable, set `{chrome_available} = false` and skip this step.

---

## EXECUTION SEQUENCE

### 1. For each route in `{affected_routes}`

```javascript
// Pseudocode — actual calls are MCP tool invocations
await mcp.chrome.tabs_navigate({ url: `${base_url}${route}` });
await mcp.chrome.wait_for_load();
const dom = await mcp.chrome.read_page();
const measurements = await mcp.chrome.javascript_tool({ code: HARVEST_SCRIPT });
```

### 2. Harvest script (single round-trip)

```javascript
(() => {
  const result = {};

  // ----- G-TYPO-02: distinct font sizes per component -----
  const componentSubtrees = [...document.querySelectorAll('[data-component]')];
  result.fontSizesByComponent = componentSubtrees.map((node) => {
    const sizes = new Set(
      [...node.querySelectorAll('*')]
        .map((el) => getComputedStyle(el).fontSize)
        .filter(Boolean),
    );
    return {
      component: node.dataset.component,
      distinctSizes: sizes.size,
      sizes: [...sizes],
    };
  });

  // ----- G-COLOR-06: distinct background colors per panel -----
  const panels = [...document.querySelectorAll('section, [role="region"], .panel, .card')];
  result.bgColorsPerPanel = panels.map((node) => {
    const bgs = new Set(
      [...node.querySelectorAll('*')]
        .map((el) => getComputedStyle(el).backgroundColor)
        .filter((c) => c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent'),
    );
    return { panel: node.className.slice(0, 60), distinctBgs: bgs.size };
  });

  // ----- S-STATUS-03: distinct badge colors on page -----
  const badges = [...document.querySelectorAll('[class*="badge"], [class*="Badge"], [class*="pill"], [class*="Pill"]')];
  const badgeColors = new Set(
    badges.map((el) => {
      const s = getComputedStyle(el);
      return `${s.backgroundColor}|${s.color}`;
    }),
  );
  result.distinctBadgeColors = badgeColors.size;

  // ----- L-LAYOUT-03 / A-ANALYTICS-03: stat-card row above table -----
  const tables = document.querySelectorAll('table, [role="table"]');
  result.statCardsAboveTable = [...tables].map((table) => {
    const rect = table.getBoundingClientRect();
    const aboveBox = { top: 0, bottom: rect.top };
    const cards = [...document.querySelectorAll('[class*="rounded"][class*="border"], [class*="Card"]')];
    const above = cards.filter((c) => {
      const r = c.getBoundingClientRect();
      return r.top >= aboveBox.top && r.bottom <= aboveBox.bottom && r.width > 100;
    });
    // Detect "row of similar-sized cards" — same height, side-by-side
    const heights = above.map((c) => Math.round(c.getBoundingClientRect().height));
    const sameHeightCount = heights.filter((h) => h === heights[0]).length;
    return { tableTop: rect.top, cardsAbove: above.length, sameHeightCardsAbove: sameHeightCount };
  });

  // ----- T-TABLE-04: horizontal overflow on tables -----
  result.tableOverflows = [...document.querySelectorAll('table, [role="table"], [class*="overflow-x"]')]
    .filter((el) => el.scrollWidth > el.clientWidth)
    .slice(0, 5)
    .map((el) => ({
      cls: el.className.slice(0, 60),
      scrollW: el.scrollWidth,
      clientW: el.clientWidth,
    }));

  // ----- A-ANALYTICS-06: above-the-fold table dominance -----
  const viewportH = window.innerHeight;
  const firstTable = document.querySelector('table, [role="table"]');
  if (firstTable) {
    const rect = firstTable.getBoundingClientRect();
    const visibleTableH = Math.max(0, Math.min(viewportH, rect.bottom) - Math.max(0, rect.top));
    result.tableFraction = +(visibleTableH / viewportH).toFixed(2);
  }

  // ----- L-LAYOUT-07: card wrapping a single element -----
  const cards = [...document.querySelectorAll('[class*="rounded-lg"][class*="border"], [class*="Card"]')];
  result.singleChildCards = cards
    .filter((c) => c.children.length === 1 && c.children[0].children.length === 0)
    .slice(0, 5)
    .map((c) => c.className.slice(0, 80));

  // ----- L-LAYOUT-08: symmetric padding everywhere -----
  result.symmetricPaddingPanels = [...document.querySelectorAll('section, .panel, [class*="Card"]')]
    .map((el) => {
      const s = getComputedStyle(el);
      return { cls: el.className.slice(0, 60), padding: `${s.paddingTop}/${s.paddingRight}/${s.paddingBottom}/${s.paddingLeft}` };
    })
    .filter((p) => {
      const [t, r, b, l] = p.padding.split('/');
      return t === r && r === b && b === l;
    })
    .slice(0, 5);

  return JSON.stringify(result, null, 2);
})();
```

### 3. Translate measurements into findings

For each measurement, apply the rule threshold:

| Rule | Threshold |
|---|---|
| G-TYPO-02 | `distinctSizes` ≥ 4 in any component → P1 finding |
| G-COLOR-06 | `distinctBgs` ≥ 3 in a single panel → P2 finding |
| S-STATUS-03 | `distinctBadgeColors` ≥ 5 → P1 finding |
| L-LAYOUT-03 / A-ANALYTICS-03 | `sameHeightCardsAbove` ≥ 3 → P1 finding |
| T-TABLE-04 | `tableOverflows` non-empty → P0 finding |
| A-ANALYTICS-06 | `tableFraction` < 0.6 on operational pages → P1 finding |
| L-LAYOUT-07 | `singleChildCards` non-empty → P2 finding |
| L-LAYOUT-08 | `symmetricPaddingPanels` non-empty → P2 finding |

For rules whose detection needs more than a single measurement (e.g., `S-STATUS-05` pastel-pill-with-dot, `S-STATUS-08` parity between list and detail views), run additional targeted scripts per the rule's Detection guidance.

### 4. Apply established-pattern exceptions

Same logic as step-02: if a flagged pattern appears in `≥3` routes already, downgrade by one tier and tag `established`.

---

## OUTPUT

Append findings to `{findings}`. Each follows the same shape as step-02 findings, with `lane: dom-render` and an additional `route` field.

Proceed to step-04.

---

## FAILURE MODES

- **Dev server isn't ready.** First navigation may hit a build/compile step. Wait for `wait_for_load` AND a 500ms settle before harvesting.
- **Page requires auth.** If `{affected_routes}` are under `(authed)`, the workflow needs a session. Either: (a) the dev server is configured with a dev session cookie, or (b) skip the page and surface in coverage notes.
- **Harvesting too much.** Don't pull entire DOMs back. The harvest script returns aggregated counts only. If a finding needs the actual offending element, run a follow-up query for just that selector.
- **Measuring at the wrong viewport.** Pages render differently at 1440px vs 1920px vs mobile. Default to 1440×900 (Chrome MCP default) and note the viewport in findings.
- **Forgetting to navigate.** Each route needs an explicit `tabs_navigate`; reusing a stale tab silently scores the wrong page.
