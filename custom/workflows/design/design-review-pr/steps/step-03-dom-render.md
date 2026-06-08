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

  // ----- S-STATUS-03 (broadened): status color across ALL state-encoding elements, not just badges -----
  // The badge selector above misses status color rendered OUTSIDE a pill — a progress/lifecycle/
  // coverage bar segment, a row tint, a dot. A 3-segment reconciliation bar mapping each stage to
  // its own hue is a status-color set with zero badges; scoping the count to badges lets it pass.
  const statusBgEls = [...badges, ...document.querySelectorAll('[class*="seg"],[class*="stage"],[class*="meter"],[class*="track"],[class*="dot"],[data-stage],[data-tone]')];
  const statusBgColors = new Set(
    statusBgEls.map((el) => getComputedStyle(el).backgroundColor)
      .filter((c) => c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent'),
  );
  result.distinctStatusColorsAllEls = statusBgColors.size;

  // ----- S-STATUS-09: rainbow stage mapping inside a single progress/lifecycle bar -----
  // A multi-segment bar must distinguish stages by position/width, not by giving each its own hue
  // (policy §3 "no rainbow status mappings"). Catches the per-bar case that the page-wide count
  // (≥5) misses because one bar's 3 hues stay under the page cap.
  const segBars = [...document.querySelectorAll('[class*="recon"],[class*="progress"],[class*="lifecycle"],[class*="flow"],[class*="-bar"],[class*="segmented"]')];
  result.rainbowBars = segBars
    .map((bar) => new Set([...bar.querySelectorAll('[class*="seg"],[data-stage],span,div')]
      .map((s) => getComputedStyle(s).backgroundColor)
      .filter((c) => c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent')).size)
    .filter((n) => n >= 3).length;

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
    // stat-row-in-disguise: a row of big-number blocks above the table, regardless of card framing.
    // The cards filter above sees zero when a stat row is unframed (no rounded+border); this catches
    // the count figures themselves so a flattened "3 big numbers" band still fires.
    const bigAbove = [...document.querySelectorAll('div, span, p, dd, strong')].filter((c) => {
      const r = c.getBoundingClientRect();
      const fs = parseFloat(getComputedStyle(c).fontSize);
      const t = (c.textContent || '').trim();
      return r.top >= aboveBox.top && r.bottom <= aboveBox.bottom && r.width > 40
        && fs >= 22 && c.children.length <= 1 && /[\d.,]/.test(t) && t.length <= 16;
    });
    return { tableTop: rect.top, cardsAbove: above.length, sameHeightCardsAbove: sameHeightCount, bigNumberBlocksAbove: bigAbove.length };
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
| S-STATUS-03 | `distinctBadgeColors` ≥ 5 **OR** `distinctStatusColorsAllEls` ≥ 5 → P1 finding (status color counted across ALL state-encoding elements — pills, progress/meter/segments, dots, tints — not just badges) |
| S-STATUS-09 | `rainbowBars` ≥ 1 → P1 finding (a single progress/lifecycle bar maps ≥3 stages to ≥3 distinct hues — rainbow stage mapping, policy §3 "no rainbow status mappings"; stages must read by position/width, not hue) |
| L-LAYOUT-03 / A-ANALYTICS-03 | `sameHeightCardsAbove` ≥ 3 **OR** `bigNumberBlocksAbove` ≥ 3 → P1 finding (a stat-card row OR an unframed row of big-number stat figures above the table — the figures are the tell, framing is not required) |
| T-TABLE-04 | `tableOverflows` non-empty → P0 finding |
| A-ANALYTICS-06 | `tableFraction` < 0.6 on operational pages → P1 finding |
| L-LAYOUT-07 | `singleChildCards` non-empty → P2 finding |
| L-LAYOUT-08 | `symmetricPaddingPanels` non-empty → P2 finding |

For rules whose detection needs more than a single measurement (e.g., `S-STATUS-05` pastel-pill-with-dot, `S-STATUS-08` parity between list and detail views), run additional targeted scripts per the rule's Detection guidance.

### 3b. Analytics band archetype conformance (C-ARCHETYPE-01)

Run this ONLY for routes present in `{brief_archetype_map}`. Skip entirely otherwise.

The band region is the content above (or beside) the primary `table`/`[role="table"]` that is not the table itself. Harvest its form signals in one round-trip:

```javascript
(() => {
  const table = document.querySelector('table, [role="table"]');
  if (!table) return JSON.stringify({ noTable: true });
  const tableTop = table.getBoundingClientRect().top;
  const inBand = (el) => { const r = el.getBoundingClientRect(); return r.bottom <= tableTop + 8 && r.width > 80; };

  const svgSeries = [...document.querySelectorAll('svg')].filter(inBand)
    .map(s => s.querySelectorAll('path, polyline, rect, line').length);
  const band = [...document.querySelectorAll('section, div, header')].filter(inBand);
  const text = band.map(e => e.textContent || '').join(' ').toLowerCase();

  // form signals
  const hasGapStrip = /gap|missing|uncovered|no statement|not imported/.test(text)
    || [...document.querySelectorAll('[class*="hatch"],[class*="stripe"],[class*="diagonal"]')].some(inBand);
  const bars = [...document.querySelectorAll('[class*="bar"], rect')].filter(inBand);
  const bigNumbers = band.filter(e => /\b[\d.,]{1,}\b/.test(e.textContent || '') && parseFloat(getComputedStyle(e).fontSize) >= 28).length;
  const sortedSignal = /top \d|ranked|highest|largest/.test(text);
  const funnelSignal = /stage|step \d|drop|converted|funnel/.test(text);

  // drill affordance: every band element of substance should be actionable
  const interactiveInBand = band.filter(e =>
    e.matches('a[href], button, [role="button"], [onclick]') ||
    getComputedStyle(e).cursor === 'pointer' ||
    e.querySelector('a[href], button, [role="button"]'));
  const substantiveBand = band.filter(e => (e.textContent || '').trim().length > 12);

  return JSON.stringify({
    seriesCount: svgSeries.reduce((a, b) => a + b, 0),
    panelCount: svgSeries.length,
    hasGapStrip, barCount: bars.length, bigNumbers, sortedSignal, funnelSignal,
    substantiveBandEls: substantiveBand.length,
    drillableBandEls: interactiveInBand.length,
  }, null, 2);
})();
```

Compare the harvest against the declared `archetype` from `{brief_archetype_map}[route]`. Read `{archetypes_path}` for the authoritative form of each. Fire `C-ARCHETYPE-01` (P1) on a clear contradiction:

| Declared archetype | Contradiction that fires C-ARCHETYPE-01 |
|---|---|
| `coverage` | `hasGapStrip` false AND `seriesCount` ≥ 3 (shipped a trend chart, not a completeness surface) |
| `trend` | `panelCount` ≤ 1 with `seriesCount` ≥ 3 (single multi-series chart — taxonomy bans it; expects small multiples) |
| `ranking` | `sortedSignal` false and bars present in arbitrary order |
| `composition` | `panelCount` ≥ 3 or `seriesCount` ≥ 3 (split into many charts instead of one part-to-whole) |
| `single-metric` | `bigNumbers` = 0, or ≥ 3 same-size metric blocks (a KPI-card wall, not one number) |
| `flow` | `funnelSignal` false and no stage-to-stage structure detected |
| `waterfall` | `barCount` < 2 — no stepped opening→deltas→closing bar structure, i.e. not rendered as a reconciliation bridge (deltas double-encoded as bar segments *and* separate reason chips is a human-judgment flag for step-04, not a DOM-firable contradiction) |
| any except `single-metric` | `bigNumbers` ≥ 3 AND weak visualization signal (`!hasGapStrip` AND `barCount` < 2 AND `seriesCount` < 2 AND `!funnelSignal`) → the band's content is a row of big-number figures, not a visualization (stat-row-in-disguise — the `bigNumbers` harvest was previously read only for `single-metric`, so a `coverage`/`flow`/`ranking` band rendered as 3 big counts passed). A legitimate band of any archetype renders a strip/chart/meter; the counts belong in the inline header summary line, not the band. |
| any | `drillableBandEls` < `substantiveBandEls` → at least one ornamental band element with no drill target (cross-cutting rule in `{archetypes_path}`) — fire as P1 with the count of non-drillable elements |

A contradiction is a P1 `change-requested` finding citing the brief filename and the declared archetype. When the harvest is ambiguous (signals don't clearly contradict but don't clearly confirm), do NOT fire — defer to the human-judgment prompt step-04 emits. False-firing this check trains reviewers to ignore it.

### 3c. Canonical-identifier formatting conformance (C-IDENTFMT-01)

The authoritative arm of the §13(a) check — policy §13 "Canonical identifier": a record *"reads, formats … and links the same way everywhere it appears … do not relabel, reformat, or re-key the same record per surface."* §3b covers §13's *component-treatment* half; this covers its *identifier-formatting* half. Run on every route in `{affected_routes}` (no brief map needed — it reads the rendered page).

Harvest the rendered string of each canonical-identifier class wherever it appears, in one round-trip. Identify identifier cells heuristically (monospace/`tabular-nums`/`id`/`code` classes, ASIN/SKU shapes `\b[A-Z0-9]{10}\b`, and columns whose header matches supplier/marketplace/order/sku):

```javascript
(() => {
  const norm = (s) => (s || '').trim();
  // collect candidate identifier strings from table cells, headers, and any open drawer/detail panel
  const cells = [...document.querySelectorAll('td, th, [role="cell"], [class*="mono"], [class*="tabular"], dd, dt')];
  const buckets = {}; // class -> Set of distinct rendered forms
  const add = (cls, val) => { if (!val) return; (buckets[cls] ||= new Set()).add(val); };
  const RX = {
    asin_sku: /^[A-Z0-9]{8,14}$/,
    marketplace: /^(amazon|amzn)[ _-]?[a-z]{2}$|^AMAZON_[A-Z]{2}$|^Amazon\s+[A-Z]{2}$/i,
    snake_enum: /^[A-Z][A-Z0-9]+_[A-Z0-9_]+$/, // raw enum leakage, any class
  };
  for (const el of cells) {
    const t = norm(el.textContent);
    if (!t || t.length > 40) continue;
    if (RX.asin_sku.test(t)) add('asin_sku', t);
    if (RX.marketplace.test(t)) add('marketplace', t);
    // supplier: short single-token alpha in a column whose header says supplier — approximate by low-card alpha tokens
    if (/^[a-z][a-z .&-]{1,24}$/.test(t) || /^[A-Z][A-Za-z .&-]{1,24}$/.test(t)) add('alpha_token', t);
    if (RX.snake_enum.test(t)) add('raw_enum_rendered', t);
  }
  // casing-variant detection: same token, different case, in the same class
  const variants = {};
  for (const [cls, set] of Object.entries(buckets)) {
    const byLower = {};
    for (const v of set) (byLower[v.toLowerCase().replace(/[ _-]/g,'')] ||= new Set()).add(v);
    const clashed = Object.values(byLower).filter((s) => s.size > 1).map((s) => [...s]);
    if (clashed.length) variants[cls] = clashed;
  }
  return JSON.stringify({
    rawEnumRendered: [...(buckets.raw_enum_rendered || [])],
    casingVariants: variants,            // e.g. { marketplace: [["AMAZON_ES","Amazon UK"]], alpha_token: [["amazon","Amazon"]] }
  }, null, 2);
})();
```

Fire `C-IDENTFMT-01` (P1 `change-requested`) on a clear result:

| Signal | Fires when |
|---|---|
| Casing/format variant within a canonical-identifier class | `casingVariants` has an entry for a canonical class (marketplace, asin_sku, supplier) — the same record class rendered two ways across cells or the list↔drawer boundary |
| Raw-enum leakage | `rawEnumRendered` non-empty AND a sibling surface renders the same class as a human label (e.g. `AMAZON_ES` rendered while `Amazon UK` appears elsewhere) |

Quote the divergent strings verbatim in the finding and cite policy §13 (and §4 for casing). A single isolated `alpha_token` casing variant that is not a canonical-identifier class is at most P3 — do not P1 a one-off. When the harvest is ambiguous (e.g. `alpha_token` clashes that may be distinct real values, not the same record), do NOT fire — defer to the step-04 human-judgment prompt. False-firing trains reviewers to ignore the check.

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
