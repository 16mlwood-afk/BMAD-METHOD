---
name: 'step-02-map-implementation'
description: 'Find the corresponding implementation files, read them, resolve Tailwind classes to computed values, and catalog every CSS property'
---

# Step 2: Map Implementation

**Progress: Step 2 of 4** — Next: Build Comparison Grid (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Resolve EVERY Tailwind class through the project's `tailwind.config.js` — never assume default values.
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

### 3. Read Every Implementation Component

For each component in `{design_components}`, find and read the implementation file:

```bash
# Try exact name match first
find src/lib/components -name "{ComponentName}.svelte" -o -name "{ComponentName}.tsx" | head -3

# Try kebab-case variant
find src/lib/components -name "{component-name}.svelte" -o -name "{component-name}.tsx" | head -3
```

For each implementation file, catalog every CSS-relevant class and inline style:

| Component | Element | Tailwind Classes | Resolved Values |
|-----------|---------|-----------------|-----------------|
| QualityVerdict | card wrapper | rounded-lg border | border-radius: 10px, border: 1px |
| QualityVerdict | icon container | grid-cols-[28px_1fr_auto] | col-1 width: 28px |
| QualityVerdict | SVG icon | width="20" height="20" | 20×20px |
| HeatGrid | cell | rounded-sm min-w-[50px] | border-radius: 4px, min-width: 50px |
| ... | ... | ... | ... |

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
- Every CSS property on every implementation component cataloged with resolved values
- Missing/extra components flagged
- `{impl_components}` and `{impl_config}` populated
- `{baseline_commit}` recorded

## FAILURE MODES

- Assuming Tailwind defaults without checking `tailwind.config.js` (the single biggest source of false "matches")
- Reading only the page file and not tracing into child components
- Skipping inline `style` attributes while only reading Tailwind classes (or vice versa)
- Not resolving CSS custom properties to actual values
- Stopping after finding "most" components instead of all of them
