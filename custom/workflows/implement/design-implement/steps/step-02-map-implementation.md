---
name: 'step-02-map-implementation'
description: 'Find the corresponding implementation files, read them, resolve Tailwind classes to computed values, and catalog every CSS property'
---

# Step 2: Map Implementation

**Progress: Step 2 of 4** — Next: Build Comparison Grid (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Resolve EVERY Tailwind class through the project's `tailwind.config.js` — never assume default values.
- **A design primitive can have MORE THAN ONE implementation.** The same concept (status pill, filter chip, money cell) is routinely built once as a shared component and again ad-hoc inline elsewhere. Enumerate ALL render sites of each primitive — never assume the first file you find is the only one. The drift that ships is usually between two implementations of the "same" thing.
- **Resolve EVERY colour to a concrete value — including the default Tailwind palette** (`bg-emerald-50` → `#ecfdf5`), not just `theme.extend.colors` overrides. Colour comparison downstream is numeric, never by class name or colour family.
- If a component exists in the design but not the implementation, mark it as "MISSING" — don't skip it.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## CONTEXT

From Step 1 you have:
- `{design_components}` — every component name and its CSS properties from the design
- `{design_tokens}` — design system token values
- `{design_file}` — the target design file name

## SEQUENCE OF INSTRUCTIONS

### 1. Identify the Implementation Page

Find the page in the codebase that corresponds to `{design_file}`:

```bash
# Search by route name (e.g., "Data Quality Dashboard" → "data-quality")
find src/routes -name "+page.svelte" -o -name "+page.tsx" -o -name "page.tsx" | head -20

# Search by component imports
grep -rl "DataQuality\|data-quality\|data_quality" src/routes/ --include="*.svelte" --include="*.tsx" | head -10
```

Read the page file. Store as `{impl_page}`. Trace all component imports:

```svelte
import QualityVerdict from '$lib/components/data-quality/QualityVerdict.svelte';
```

### 1a. Map the Page Shell — the EFFECTIVE container width

The single thing the component sweep cannot see is how the page itself is framed. Width caps are **nested**: a page wrapper can set `max-width: 1280px` while its route/app layout ALSO sets `max-w-[1440px]` — and the tightest one wins, so the page renders at 1280, centered, with dead gutters inside its 1440 content area. That mismatch is invisible to every per-component grid row (each component's CSS can be byte-identical to the design) yet it reframes the whole composition. This is the inbound-flow `/orders` miss (PR #2017).

Walk the wrapper chain from `{impl_page}` OUTWARD and resolve each layer to concrete px:

1. **The page's own wrapper** — the outermost element the page component renders (e.g. `.ord-page`, the top `<div style={{maxWidth: …}}>`). Record its `max-width`, `margin: 0 auto` / `mx-auto` (centered?), and horizontal `padding`.
2. **Every ancestor layout** — the route layout(s) and the app shell that wrap this page (`(authenticated)/layout.tsx`, `AppShell`, etc.). Record each one's container `max-width` / `mx-auto` / `padding`. (A layout often carries the real cap — e.g. `<div className="mx-auto max-w-[1440px]">`.)
3. **Resolve the effective container:** the tightest `max-width` across the chain is the rendered width; `centered = true` if any layer applies `margin:auto`/`mx-auto`; sum the relevant horizontal padding.
4. **Capture ancestor-injected chrome — anything a wrapper renders ABOVE/AROUND `{children}` that the design's frame never contained.** The same wrapper chain you just walked for width also renders *content* the component sweep is blind to, because the design bundle renders its frame **standalone** (no app shell, no section layout) — so a band injected by an ancestor layout has nothing in `{design_components}` to diff against and every component row still greens. Scan each ancestor layout's JSX for an element rendered *before* `{children}`: a **hero / banner / masthead / marketing strip** (`<HeroBanner>`, a `<div>` with a background image + title/subtitle, a tall section header band), a promo/announcement bar, or any section-level chrome. For each, record what it is and whether the design frame contains an equivalent. This is the inbound-flow `/settings/sku-format` miss: `settings/layout.tsx` injected an `<InboundHeroBanner image+title+subtitle>` above every settings page; the design had no hero; design-implement matched the worklist component-for-component and shipped the banned banner (a `docs/design-policy.md` §5 hard failure — "Hero strips, banner panels, or marketing-style intros above working tables").

Store as `{impl_page_shell} = { effective_width: "<px>" | "full-bleed", centered: bool, padding: "<value>", chain: [ {layer, max_width, centered, padding}, … ], injected_chrome: [ {layer, kind: "hero"|"banner"|"masthead"|"promo-bar"|…, summary, in_design_frame: bool} ] }`. Sibling pages are a useful cross-check: if every other feature page caps at the same inner width, note it — a design that wants this one full-width is then a deliberate divergence from a house convention, which step-03 §2d should surface (not silently "fix" the convention everywhere).

### 2. Read the Tailwind Configuration

```bash
find . -name "tailwind.config.*" -not -path "*/node_modules/*" | head -3
```

Read the config file. Extract all overrides that affect CSS properties — especially:

- `theme.extend.borderRadius` — maps like `{ lg: '10px', md: '8px', sm: '4px' }` override Tailwind defaults
- `theme.extend.fontSize` — custom type scale
- `theme.extend.colors` — custom color tokens
- `theme.extend.spacing` — custom spacing scale

Store as `{impl_config}`. Build a **Tailwind class resolution table**:

| Tailwind Class | Default Value | Project Override | Actual Value |
|---------------|---------------|------------------|-------------|
| rounded-sm | 2px | 4px | 4px |
| rounded | 4px | 4px | 4px |
| rounded-md | 6px | 8px | 8px |
| rounded-lg | 8px | 10px | 10px |
| text-sm | 14px | — | 14px |
| text-lg | 18px | — | 18px |
| ... | ... | ... | ... |

This table is critical. The #1 cause of design drift is assuming Tailwind defaults when the project overrides them.

**Colours must resolve to concrete values too — including the default Tailwind palette.** The table above covers spacing/radius/type. Colour drift hides in a different place: a design that specifies a raw `hsl(150 26% 95.5%)` and an implementation that writes `bg-emerald-50` are NOT comparable by name. Resolve every colour token to a concrete value and build a **Colour resolution table** alongside the class table:

- Default-palette classes (`bg-emerald-50`, `text-rose-700`, `ring-amber-500/30`) → their actual hex/oklch (`emerald-50` = `#ecfdf5`), NOT left as the class name.
- `theme.extend.colors` overrides → their hex.
- Opacity-suffixed classes (`/30`, `/[0.06]`) → the composited value.
- The design's own raw colours (`hsl(...)`, hex) → the same space, so the two are diffable.

| Class / token | Resolved (hex or oklch) |
|---------------|-------------------------|
| bg-emerald-50 | #ecfdf5 |
| ring-emerald-500/30 | #10b981 @ 30% |
| (design) hsl(150 26% 95.5%) | #eef5f1 |

Without this, step-03 sees `emerald-50` vs `hsl(150 26% 95.5%)`, cannot compute they are different greens, and an LLM rationalises "both pale green → ✓". That exact rationalisation shipped the invoices status-pill drift. Store as `{impl_colors}`.

### 3. Read Every Implementation of Every Primitive

A design primitive does **not** map 1:1 to a single implementation file. The same concept — a status pill, a filter chip, a money cell — is frequently implemented more than once: a shared component in one place, an ad-hoc reimplementation inline somewhere else. Find **all** of them. The drift that ships is usually *between two implementations of the same primitive*, not between the design and one file.

For each component / primitive in `{design_components}`:

**3a. Find the named component file:**

```bash
find src/lib/components -name "{ComponentName}.svelte" -o -name "{ComponentName}.tsx" | head -3
find src/lib/components -name "{component-name}.svelte" -o -name "{component-name}.tsx" | head -3
```

**3b. Enumerate EVERY render site (implementation multiplicity):**

Do not stop at the named component. Grep the whole codebase for every place the primitive is rendered — both consumers of the shared component AND inline reimplementations of the same concept (these are the dangerous ones):

```bash
# consumers of the shared component
grep -rn "{ComponentName}" src/ --include="*.svelte" --include="*.tsx"

# ad-hoc reimplementations of the same primitive — by the design's class name,
# characteristic markup, or signature style (e.g. a status pill)
grep -rn "class=\"pill\|\.pill\|rounded-md px-2 .*ring-inset\|status.*badge" src/ --include="*.svelte"
```

Record every distinct implementation as its own row, tagged with its file and the primitive it implements. A primitive with two or more implementations is expected — capture them all; step-03 cross-checks them against each other.

**3c. Catalog every CSS-relevant class and inline style** for each site (resolving colours via `{impl_colors}`):

| Component | Primitive | Element | Tailwind / inline | Resolved Values |
|-----------|-----------|---------|-------------------|-----------------|
| QualityVerdict | card | wrapper | rounded-lg border | radius 10px, border 1px |
| InvoiceStatusPill | status-pill | span | rounded-md px-2 bg-emerald-50 ring-emerald-500/30 | radius 6px, bg #ecfdf5, ring #10b981@30% |
| InvoiceDrawer (inline `.pill`) | status-pill | span.pill.green | (scoped CSS) | bg #eef5f1, border hsl(150 24% 87%) |
| ... | ... | ... | ... | ... |

Store the full set as `{impl_render_sites}`, keyed by primitive and listing every implementation found. This is the input to step-03's implementation-consistency check.

**3d. Tag the value-source of each cell (content-lane input).** For every render site, record where its **displayed text** comes from — this is cheap (you have already read the file) and feeds step-03 §2c. Tag each site:

- `value_source: literal` — the text is a static literal in the JSX/markup (a column header, a button label, a placeholder). The bundle's mock string and the impl's string are directly comparable.
- `value_source: formatter` — the text is produced by a formatter function (`fmtMoney`, `fmtDate`, `marketplaceCode(...)`, `resolveMarketplace(...).code`, a `*-display` helper).
- `value_source: enum-map` — the text maps a stored enum/code to a label (a `Record<enum, label>` lookup, a `switch`, an `IMPORT_SOURCE[...]`-style table).

Flag every site that is `formatter` or `enum-map` **AND** renders a **canonical-identifier class** (marketplace, supplier, ASIN/SKU, order/batch/shipment number, currency, date, status label) as an **identifier cell**. These are the cells whose value design-implement **cannot certify against a mock-data bundle** (the mock value exercises one variant; the real enum forms — `amazon_us`, `amazon.de`, a stray `GB` — never appear in the bundle). Record them in `{impl_identifier_cells}` (a sub-list of `{impl_render_sites}`: `{ primitive, file, identifier_class, value_source, formatter_ref }`). Do NOT try to resolve "the right label" here — step-03 §2c only needs to know which cells are formatter-driven so they are routed, not pixel-matched.

### 4. Handle Missing or Extra Components

- **In design but not implementation:** Mark as `MISSING — needs creation`. Note what the component does.
- **In implementation but not design:** Mark as `EXTRA — verify intentional`. These might be implementation-only UI (loading states, error boundaries).

### 5. Handle CSS Custom Properties and Computed Styles — resolve the value AND record its provenance

Some implementations use CSS custom properties (e.g., shadcn tokens like `bg-card`, `text-foreground`). For each one a design token maps to:

1. **Find where the custom property is defined** and resolve it to the actual computed value.
2. **Record the resolved value** AND the **source layer** it resolved from — this is the provenance axis step-03 §2g needs. A `var(--*)` that resolves is not automatically a clean "1:1" mapping; *where* it resolves from matters per the project's token precedence (`docs/design-policy.md` §8: the **canonical token surface** is `src/styles/tokens.css` + the `@theme inline` block in `globals.css` — those are "ground truth for what exists in the system"). Tag each resolved token:
   - **`canonical`** — defined in `tokens.css` or the `globals.css @theme` block.
   - **`per-screen`** — defined ONLY in a per-screen / per-feature stylesheet (e.g. `supply-orders.css`), not the canonical surface. (The project has ~25 such stylesheets the policy's v3 note marks as migration debt — a token living only here is resolvable at runtime but is NOT a system token.)
3. Also tag the token's **semantic class** — `shared-semantic` (a status / colour / type token, which §3 mandates read identically across sibling surfaces) vs `local-constant` (a one-off spacing/layout value with no cross-surface contract). This is what lets step-03 §2g flag only the tokens that *should* be canonical, not every per-screen var.
4. Store as `{impl_token_provenance}` — a list of `{ token, resolved_value, source_file, scope: canonical | per-screen, semantic_class: shared-semantic | local-constant }`.

**Resolve every referenced token before reporting any mapping as "1:1."** A token still pending lookup, or one that only half-resolved (some screens define it, others don't), is NOT resolved — do not fold it into a "tokens map ~1:1" claim. Carry the unresolved set forward explicitly; the premature "effectively 1:1" is the exact miss step-03 §2g exists to catch.

### 6. Record Baseline Commit

```bash
git rev-parse HEAD
```

Store as `{baseline_commit}`.

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-02b-regression-surface.md`

---

## SUCCESS METRICS

- Implementation page and all component files located and read
- Tailwind config read and class resolution table built
- **Every colour (incl. default Tailwind palette) resolved to a concrete hex/oklch value — `{impl_colors}` populated**
- **Every render site of every primitive enumerated (not just the named component) — `{impl_render_sites}` populated, multi-implementation primitives captured in full**
- **Every render site tagged with its value-source (§3d); formatter/enum-driven canonical-identifier cells captured in `{impl_identifier_cells}` for step-03 §2c routing**
- Every CSS property on every implementation component cataloged with resolved values
- **Every design-mapped CSS custom property resolved AND tagged with provenance (§5) — `{impl_token_provenance}` populated with `scope` (canonical vs per-screen) + `semantic_class`; no token reported as "1:1" while still unresolved**
- **Page-shell wrapper chain walked (§1a) — `{impl_page_shell}` populated with the EFFECTIVE container width after every nested layout cap, centering, and padding (plus a sibling-page convention note if relevant), AND `injected_chrome` capturing any hero/banner/masthead an ancestor layout renders above `{children}` that the design frame doesn't contain**
- Missing/extra components flagged
- `{impl_components}` and `{impl_config}` populated
- `{baseline_commit}` recorded

## FAILURE MODES

- Assuming Tailwind defaults without checking `tailwind.config.js` (the single biggest source of false "matches")
- **Mapping a design primitive to ONE implementation when it has several.** The shipped drift is usually between two implementations of the same primitive (e.g. a shared `InvoiceStatusPill` rendering Tailwind `emerald-50` and an inline `.pill` in a drawer rendering raw `hsl(150 26% 95.5%)`) — a single-file mapping never compares them and both "pass."
- **Leaving colours as class names** (`bg-emerald-50`) instead of resolving to hex — a raw-HSL design value and a Tailwind palette class are not comparable by name, and "both green" is not a match.
- Reading only the page file and not tracing into child components
- Skipping inline `style` attributes while only reading Tailwind classes (or vice versa)
- Not resolving CSS custom properties to actual values
- Stopping after finding "most" components instead of all of them
