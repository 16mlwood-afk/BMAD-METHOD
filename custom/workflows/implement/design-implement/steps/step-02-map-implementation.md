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

### 4. Handle Missing or Extra Components

- **In design but not implementation:** Mark as `MISSING — needs creation`. Note what the component does.
- **In implementation but not design:** Mark as `EXTRA — verify intentional`. These might be implementation-only UI (loading states, error boundaries).

### 5. Handle CSS Custom Properties and Computed Styles

Some implementations use CSS custom properties (e.g., shadcn tokens like `bg-card`, `text-foreground`). For these:

1. Find where the custom property is defined (usually in `app.css` or a theme file)
2. Resolve to the actual computed value
3. Record both the property reference and the resolved value

### 6. Record Baseline Commit

```bash
git rev-parse HEAD
```

Store as `{baseline_commit}`.

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-03-build-grid.md`

---

## SUCCESS METRICS

- Implementation page and all component files located and read
- Tailwind config read and class resolution table built
- **Every colour (incl. default Tailwind palette) resolved to a concrete hex/oklch value — `{impl_colors}` populated**
- **Every render site of every primitive enumerated (not just the named component) — `{impl_render_sites}` populated, multi-implementation primitives captured in full**
- Every CSS property on every implementation component cataloged with resolved values
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
