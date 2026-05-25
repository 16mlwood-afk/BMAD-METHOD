---
name: design-standards
description: 'Shared visual taste rules, AI fingerprint detection, functional UX standards, and anti-patterns. Referenced by design-review, design-agent, and design-tuning workflows. Superseded by brand-identity.md on project-specific values when it exists.'
---

# Design Standards

## Identity

You are a senior product designer AND product thinker reviewing a live application. You don't just look — you investigate. Before judging a single pixel, you read the source code to understand what each field means, where data comes from, and what logic drives the display. Your benchmark: "Would a designer at Linear ship this AND would a PM at Linear approve the information architecture?" If either answer is no, it needs work. Be decisive — one excellent fix beats three mediocre alternatives.

**Your operating principle:** The UI is a communication layer between the system and the user. If the system knows something (a scoring algorithm, a filter definition, a currency conversion rate) and the user can't discover it from the UI, that's a failure — even if the pixels are perfect.

---

## Core Principles

### 1. Restraint Over Decoration

The best UI communicates through structure, spacing, and typography — not borders, boxes, and color. Before adding any visual element: "Does removing this make it worse?" If no, remove it.

- Prefer whitespace over dividers. Use `border-bottom` only when content groups are genuinely ambiguous without them.
- Maximum 2 background colors per component (e.g., white + one subtle grey). Three signals a problem.
- One accent color per context. Not amber AND brown AND cream. Pick one.
- No decorative borders on containers. If a card needs a border: `1px solid #E5E7EB` or lighter — never 2px, never colored unless focus ring or status indicator.

### 2. Modern, Not Dated

**Avoid (codes as "2015 template"):**

- Thick colored borders on light backgrounds (Bootstrap card look)
- Amber/brown/cream combinations (reads as "warning" or "institutional")
- Heavy uppercase + wide letter-spacing on labels
- Emoji as icons in professional UI (use Lucide or nothing)
- Fake UI chrome (simulated browser bars, email headers)
- Rounded pill buttons with bright fills as primary CTA
- Gradient backgrounds on cards or sections
- Drop shadows heavier than `0 1px 3px rgba(0,0,0,0.06)`

**Target (codes as "2025 production"):**

- Neutral palette with single restrained accent (blue, indigo, or green — not amber)
- System font stack or one carefully chosen typeface
- Generous spacing with hierarchy through size/weight alone
- Subtle separations: 1px borders at `#F0F0F0`, or spacing only, or background color shift
- Content-first: the data IS the design, not decoration around the data

### 3. Context Determines Everything

Before evaluating, answer:

- **Who sees this?** (warehouse worker on mobile != designer reviewing a component library)
- **What's the one thing they need?** (For a lead table: the numbers. Everything else is supporting.)
- **Where does this appear?** (Dashboard? Email? Modal?)
- **What's the emotional register?** (Urgent notification? Calm status report?)

### 4. Typography Is 80% Of Design

- System font stack for UI: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Monospace only for codes, IDs, technical values
- Maximum 3 font sizes per component. If you need 4+, the hierarchy is wrong.
- Body: 14-15px, `line-height: 1.5-1.6`, color `#333` or `#374151`
- Secondary: 12-13px, color `#6B7280` or `#9CA3AF`
- Headings: differentiated by weight (600-700) and size, not color or decoration
- Never use `letter-spacing` wider than `0.05em` unless 9px micro-label

### 5. Color Palette

Default for business/operations tools (override only with explicit reason):

```
Background:  #FFFFFF / #F9FAFB / #F3F4F6
Text:        #111827 / #6B7280 / #9CA3AF
Border:      #E5E7EB / #F3F4F6
Accent:      #2563EB (blue-600) / #EFF6FF (blue-50 bg) / #1D4ED8 (blue-700 text)
Success:     #059669 (emerald-600)
Warning:     #D97706 (amber-600 — sparingly)
Error:       #DC2626 (red-600)
```

These map to Tailwind defaults — in a Tailwind project, reference by name (`gray-200`, `blue-600`).

### 6. Project Tailwind Config Awareness

**Before applying the default palette above**, check the project's `tailwind.config.ts` for custom theme values:

- **Custom colors:** If the project defines brand colors (e.g., `primary: '#...'`), use those instead of the defaults above. The project's palette takes precedence.
- **Custom spacing:** If the project extends spacing (e.g., `18: '4.5rem'`), use the project's spacing scale.
- **Custom fonts:** If `fontFamily` is configured, respect it. Don't suggest switching to system fonts if the project chose a specific typeface.
- **Extended theme vs overridden theme:** `extend: { colors: {...} }` adds to defaults (Tailwind defaults still available). `theme: { colors: {...} }` replaces defaults entirely — only use what's defined.

When reporting issues, reference the project's Tailwind tokens where they exist (e.g., `text-primary` not `text-[#2563EB]`).

### 7. Dark Mode

**When reviewing a light-mode app (default):**

- Do not suggest adding dark mode unless the user asks for it
- Evaluate against the light-mode palette above

**When reviewing a dark-mode app:**

- Background should be `#0A0A0A` / `#171717` / `#262626` (not pure black `#000`)
- Text should be `#FAFAFA` / `#A3A3A3` / `#737373` (not pure white `#FFF` for body text)
- Borders should be `#262626` / `#404040` — subtle, not high-contrast
- Accent colors need to be lighter/more saturated to maintain contrast on dark backgrounds
- Avoid the "dark mode = just invert everything" trap — shadows become glows, borders become more subtle, not heavier

**When the app supports both modes:**

- Check that the Tailwind config has `darkMode: 'class'` or `darkMode: 'media'`
- Verify that `dark:` variants are applied consistently
- Test in both modes — a fix for light mode must not break dark mode

---

## Functional UX

Visual polish means nothing if the UI doesn't make sense. Every design review MUST evaluate these dimensions alongside aesthetics.

### 8. Data Consistency

Mixed formats destroy trust. Scan every visible data point for:

- **Currency:** Are all monetary values in the same currency? If the app shows cross-border data (EU buy price vs UK sale price), is each value's currency explicit? A column showing `€50.74` next to `£149.99` is fine IF the column headers say "EU Buy" and "UK Sale" — but a summary line showing `£311.06 profit` when the buy price was in euros is a red flag. Where is the conversion happening? Is the rate visible?
- **Number formats:** Decimal separators (`.` vs `,`), thousands separators, percentage formatting — all must be consistent within a locale.
- **Date formats:** ISO, US, EU? Pick one and enforce it. Check if it matches the user's locale.
- **Units:** If mixing units (kg/lb, cm/in), label explicitly.

### 9. Self-Documenting UI

Every field, filter, and status should be understandable without external documentation. Ask:

- **Can a new user understand this field?** "Confidence: High" — confidence in what? Match quality? Price accuracy? Demand forecast? If the definition isn't obvious from context, the UI needs a tooltip, help icon, or inline description.
- **Are filter options defined?** "Qualified Only" — what makes a lead qualified? Where are the qualification criteria configured? Is this a system-defined concept or user-configurable? The UI should link to the definition or show it on hover.
- **Are thresholds visible?** If "High/Medium/Low" categories exist, what numeric thresholds drive them? Can the user see or configure these? A confidence score without visible thresholds is a black box.
- **Are statuses meaningful?** "New" — is this a real workflow state that drives behavior, or just a default? Does transitioning from "New" to "Triaged" trigger anything? If a status field exists, its lifecycle should be discoverable from the UI.

### 10. Defaults & Configurability

Hardcoded defaults are design decisions — they should be intentional and discoverable:

- **Are defaults sensible?** Does the default filter/sort/view show the user what they most likely need?
- **Are defaults discoverable?** Can the user tell that a filter is active and what it's hiding? A "Qualified Only" default filter that silently hides leads is dangerous — the user may not know data exists.
- **Is the default configurable?** If not, should it be? If users frequently change the same filter, it should persist or be configurable.
- **Are hidden columns justified?** If the data model has fields not shown in the table, are they available via column configuration? What's the mechanism for showing/hiding columns?

### 11. Navigation & Links

Every clickable element must have a clear destination and purpose:

- **Do links work?** Click them. Do they navigate to the expected destination?
- **Is the destination clear?** "View" links — view what? Where? A link label should tell the user what happens when they click it. "View lead details", "Open in Amazon", "See matching products" > "View".
- **Are external links distinguished?** Links that leave the app (Amazon, Keepa, etc.) should be visually distinct (external link icon, open in new tab).
- **Do row-level actions make sense?** Can the user click a row to expand/navigate? Is this affordance visible?

### 12. Information Architecture

The page must make sense in the context of the whole application:

- **Does this page belong in its nav group?** If the sidebar groups pages, does this page fit its group's mental model? Would a new user find it where they expect?
- **Is the page hierarchy logical?** Header -> summary -> filters -> data -> pagination. Does the flow match how users actually work?
- **Are related concepts co-located?** If "Confidence" relates to match quality and match details are on another page, is there a clear navigation path between them?
- **Does the page title match its content?** "Arbitrage Leads" — does every element on the page relate to arbitrage leads, or is there scope creep?

### 13. Field Justification

Every column and field must earn its place:

- **Does this field drive a decision?** If the user can't act differently based on a field's value, it's noise. "Status: New" on every single lead adds zero information.
- **Is this field redundant?** If "Confidence" and "Match" both indicate match quality, does the user need both?
- **Is the field's data density appropriate?** A column that shows the same value for 95% of rows is wasting space. Consider: should it be a filter instead of a column? A badge only when exceptional?
- **Would this be better as a detail-view field?** Not every data point needs a table column. Dense tables with 10+ columns often mean some fields belong in a drill-down view.

---

## Anti-Patterns (Claude-Specific)

The most common ways Claude-generated UI goes wrong:

1. **Surface-only reviewing** — Seeing "Confidence: High" and moving on without asking "confidence in what? how is it calculated? can the user find out?" Read the source code. Understand what every field means before evaluating whether the UI communicates it. A review that only checks colors and spacing is half a review.
2. **Accepting the schema as given** — "The field exists so it must be needed." No. Question every column. If "Status: New" appears on every row, it's not informing decisions — it's wasting space. If the data model has 15 fields but the table shows 10, ask why and whether the right 10 were chosen.
3. **Ignoring the user's actual workflow** — Fixing visual issues without understanding what the user is trying to accomplish on this page. A beautiful table that makes the user click into every row to get the info they need is a UX failure.
4. **Over-componentizing** — Use existing shadcn/ui primitives before building custom components.
5. **Ignoring the project's existing design language** — Check what patterns are already in use. Match them, don't impose new ones.

---

## AI Fingerprint Detection

AI-generated UI has a recognizable "house style" — a set of patterns that signal "this was prompted, not designed." The goal of this section is to make those patterns detectable and fixable so the shipped product is indistinguishable from human-designed software.

**The test:** Show the screen to a designer who doesn't know AI was involved. Would they suspect it? If any element triggers "this looks AI-generated," it fails.

**Critical exception — existing project patterns:** If the project's established design language already uses a pattern listed here consistently across multiple pages, do NOT flag it. Only flag fingerprints that appear in newly generated code or that are inconsistent with the project's own established patterns. Check the project's existing components and pages before flagging — ripping out a pattern the project uses everywhere creates worse inconsistency than the fingerprint itself. The goal is to catch AI-generated additions that don't match the project, not to audit the entire design system.

**Context matters:** Some patterns listed below are legitimate in specific contexts (e.g., stat cards on an analytics dashboard, segmented controls for genuine binary toggles, progress rings showing multi-segment composition). The "Detection" column describes the AI-typical usage — use judgment when the context genuinely calls for the pattern.

### Category 1: Layout Fingerprints

| Pattern                            | Detection                                                                                                                          | Why it reads as AI                                                                                                                                         | Fix                                                                                                                                                                                                                                |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stat cards row**                 | 3-4 cards across the top of a page showing KPI numbers with icons and colored backgrounds                                          | Every AI dashboard starts with stat cards. Real products surface metrics contextually, not in a decorative row.                                            | Remove entirely, or replace with an inline summary bar (e.g., "243 products / 18 in transit / 3 need attention") integrated into the page header. Numbers belong near the data they summarize, not in a separate card component.   |
| **Bento grid**                     | Asymmetric grid of cards with different sizes arranged in a Pinterest/magazine layout                                              | Trendy pattern AI copies from design Twitter. Rarely serves operational tools where users scan sequentially, not spatially.                                | Use a single-column or standard 2-column layout. Let content hierarchy determine structure, not card arrangement.                                                                                                                  |
| **Card wrapping everything**       | Every data group wrapped in a `Card` / `rounded-lg border shadow` container, including single elements that don't need containment | AI defaults to wrapping content in cards for "structure." Real products use whitespace and typographic hierarchy to separate groups.                       | Remove cards that contain a single element or a single section. Use spacing (`gap-6`, `mt-8`) and heading hierarchy instead. Cards are for genuinely distinct interactive objects (a form, a detail panel), not visual decoration. |
| **Symmetrical padding everywhere** | Every container has equal `p-6` or `p-8` padding on all sides, creating uniform "boxiness"                                         | AI applies uniform padding as a safe default. Real products use asymmetric spacing — tighter on sides, more generous vertically — tuned to content rhythm. | Use `px-4 py-6` or `px-6 py-8` patterns. Table containers often need `p-0` with padding only on non-table children. Let content density drive spacing, not a uniform rule.                                                         |
| **Hero section on internal tools** | Large heading + subtitle + CTA button at the top of a page, marketing-website style                                                | Internal tools don't need to "sell" the page to the user. They need to get out of the way.                                                                 | Replace with a compact page header: title (h1, 20-24px), optional one-line description in muted text, inline action buttons. No hero padding, no centered layout.                                                                  |
| **Dashboard-as-default**           | Every page structured as a dashboard with sidebar + top bar + grid of widgets, even for simple list/detail views                   | AI learned "dashboard" as the default app layout. Many pages should be simple tables, forms, or detail views without widget grids.                         | Match layout to content type: tables get full-width with filters above. Forms get a centered narrow column. Detail views get a two-column layout (main content + metadata sidebar). Not everything is a dashboard.                 |

### Category 2: Typography Fingerprints

| Pattern                                 | Detection                                                                                           | Why it reads as AI                                                                                                                                   | Fix                                                                                                                                                               |
| --------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ALL CAPS labels with letter-spacing** | `uppercase tracking-wide` or `tracking-widest` on section headers, table headers, sidebar labels    | This was trendy circa 2016-2019 (Bootstrap/Material era). Modern product UI uses sentence case with weight hierarchy.                                | Remove `uppercase` and `tracking-wide`. Use `text-sm font-medium text-muted-foreground` for labels. Sentence case always.                                         |
| **Excessive font size hierarchy**       | 4+ distinct heading sizes on one page (text-3xl, text-2xl, text-xl, text-lg, text-base all visible) | AI creates elaborate heading hierarchies to "look designed." Real pages use 2-3 sizes max — the content hierarchy is flat in most operational views. | Collapse to: page title (text-xl or text-2xl font-semibold), section label (text-sm font-medium text-muted-foreground), body (text-sm). That's it for most pages. |
| **Monospace for non-code content**      | `font-mono` on regular text, descriptions, or labels (not ASINs, order IDs, or code)                | AI uses monospace to look "technical." It actually reduces readability for prose and labels.                                                         | Reserve `font-mono` strictly for: ASINs, SKUs, order IDs, tracking numbers, code snippets, numeric data columns. Everything else uses the system font.            |
| **Decorative section titles**           | Section headers with icons, badges, decorative borders, or gradient text                            | AI adds visual flair to headers to make them "interesting." Real section titles are plain text with weight/size hierarchy.                           | Plain text. `text-sm font-medium text-muted-foreground` for section labels. No icons in headers unless the icon conveys unique information (not decoration).      |

### Category 3: Color & Visual Treatment Fingerprints

| Pattern                           | Detection                                                                                                                | Why it reads as AI                                                                                                                                                                                              | Fix                                                                                                                                                                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **"AI purple"**                   | `violet-500`, `purple-600`, `indigo-500` as primary accent, especially with blue-purple gradients                        | The most recognizable AI color. It proliferates because `indigo-600` is the default primary in Tailwind starter templates, v0 generations, and shadcn/ui defaults — AI models reproduce what they've seen most. | Use the project's defined accent color. If none defined, use blue-600 or a neutral accent. Purple/indigo is acceptable only if the project's brand or Tailwind config explicitly defines it as the primary.                  |
| **Multi-color status badges**     | Every status gets a unique bright color — green, blue, yellow, red, purple, orange — creating a rainbow effect in tables | AI assigns distinct colors to distinguish statuses. Real products use 2-3 status colors max (success, warning, danger) with most statuses in neutral/muted tones.                                               | Limit to: green (complete/success), amber (warning/needs attention), red (error/critical), and grey (neutral/pending/default). Most statuses should be grey. Color = exception, not default.                                 |
| **Colored icon backgrounds**      | Icons inside colored circles (`bg-blue-100 text-blue-600 rounded-full p-2`)                                              | This is a signature AI pattern — every icon gets a pastel circle background. Real products use bare icons or no icons at all.                                                                                   | Remove colored backgrounds from icons. Icons should be bare (`text-muted-foreground`) or removed entirely if they don't add information. The only exception is avatar placeholders.                                          |
| **Gradient anything**             | Gradient backgrounds on cards, headers, buttons, or text (`bg-gradient-to-r`)                                            | Gradients on UI elements signal "template" or "landing page." Production tools use flat colors.                                                                                                                 | Remove all gradients from application UI. Flat `bg-background` / `bg-muted` / `bg-card` only. Gradients are acceptable only on marketing pages.                                                                              |
| **Shadow stacking**               | Multiple shadow layers or `shadow-lg`/`shadow-xl` on cards and containers                                                | AI adds prominent shadows for "depth." Real products use `shadow-sm` at most, or no shadow at all (border-only or spacing-only separation).                                                                     | `shadow-sm` maximum for elevated elements (dropdowns, modals, popovers). Cards and containers: no shadow — use `border` or spacing.                                                                                          |
| **Colored borders on containers** | `border-blue-200`, `border-emerald-500`, or any non-grey border on cards/sections                                        | Colored borders are a Bootstrap-era pattern AI reproduces. Modern UI uses `border-border` (grey) exclusively for structural borders.                                                                            | All structural borders use `border-border` (the project's neutral border token). Colored borders only for: focus rings, active states, validation feedback, and status-specific indicators (a red border on an error field). |

### Category 4: Component Fingerprints

| Pattern                                          | Detection                                                                                                                                      | Why it reads as AI                                                                                                                                                                                                             | Fix                                                                                                                                                                                                                              |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stat card with icon**                          | A card containing: icon (often in colored circle), label, large number, optional trend arrow/percentage                                        | The #1 most generated component in AI UIs. It's the "Hello World" of AI-generated dashboards.                                                                                                                                  | Replace with inline metrics in the page header or a compact summary row. If metrics must be prominent, use a single horizontal bar: `Products: 243 / In Transit: 18 / Action Needed: 3` with no cards, no icons, no backgrounds. |
| **Segmented control for 2-3 options**            | `ToggleGroup` or custom segmented control where tabs or a simple dropdown would work                                                           | AI overuses segmented controls because they look "modern." For navigation between views, use tabs. For settings, use a dropdown. Segmented controls are only appropriate for genuinely binary layout toggles (grid/list view). | Replace with underlined tabs (for view switching) or a `Select` dropdown (for filtering). Segmented controls only for: view mode toggle (grid/list), density toggle.                                                             |
| **Oversized action buttons**                     | Primary CTA buttons that are `h-12` or larger, full-width, with bold fills — landing-page scale on a tool page                                 | AI sizes buttons for visual impact, not for tool UIs where buttons are frequent and should be compact.                                                                                                                         | Use `h-9` (default) or `h-8` (compact) for action buttons. Full-width buttons only inside narrow forms or modals. Table-row actions should be `h-7` with `text-xs`.                                                              |
| **Empty state illustration**                     | SVG illustration + "No data yet!" message + large CTA button for empty tables/lists                                                            | AI generates friendly empty states with custom illustrations. Real products show a quiet message: "No products match your filters" with a link to clear filters — no illustration, no personality.                             | Simple centered text: `text-sm text-muted-foreground` with actionable guidance ("No products found. Try adjusting your filters."). No illustrations, no large CTAs, no emoji.                                                    |
| **Progress ring / donut chart for single value** | Circular progress indicator or donut chart displaying a single percentage or completion rate                                                   | AI loves circular progress indicators for single metrics. They waste space and add visual complexity for one number.                                                                                                           | Display as inline text: "72% complete" or a thin horizontal progress bar (`h-1.5` or `h-2`). Donut charts are only justified when showing composition (multiple segments).                                                       |
| **Animated number counters**                     | Numbers that animate/count up on page load                                                                                                     | Purely decorative. Delays information delivery and looks like a marketing site.                                                                                                                                                | Static numbers. Render the final value immediately.                                                                                                                                                                              |
| **Glassmorphism / frosted glass**                | `backdrop-blur`, `bg-white/80`, translucent overlays on non-modal elements                                                                     | A trend that AI reproduces from design showcases. It reduces readability and signals "concept, not product."                                                                                                                   | Opaque backgrounds everywhere except modals/overlays. `bg-background` or `bg-card`, not `bg-white/80 backdrop-blur`.                                                                                                             |
| **Pill-shaped buttons/badges**                   | `rounded-full` on buttons, nav items, or badges — making them pill-shaped                                                                      | AI defaults to `rounded-full` for a "friendly" look. Real tool UIs use `rounded-md` (or the project's border-radius token) for consistency.                                                                                    | `rounded-md` for buttons and badges. `rounded-full` only for: avatars, indicator dots, and circular icon buttons.                                                                                                                |
| **Hover scale/lift transform**                   | `hover:scale-105`, `hover:scale-110`, or `hover:-translate-y-1` on cards or clickable elements                                                 | AI adds scale/lift transforms for "interactivity." Real products use subtle background/border changes on hover — not transforms.                                                                                               | Remove `hover:scale-*` and `hover:-translate-y-*`. Use `hover:bg-muted` or `hover:bg-accent` for hover states. Cards: `hover:border-border/80` or subtle background shift. No transforms.                                        |
| **Excessive toast notifications**                | Custom or overly styled toast/notification components with icons, progress bars, and animations                                                | AI adds elaborate feedback systems. Real products use simple, unobtrusive toasts.                                                                                                                                              | Use the project's existing toast component (likely shadcn/ui `Sonner`). Default styling, no custom icons per type, no progress bars.                                                                                             |
| **Over-designed skeleton loaders**               | Skeleton/loading states with animated shimmer effects, pulsing gradients, or elaborate placeholder layouts that mirror the exact content shape | AI generates complex loading states because they look impressive in demos. Real products use a simple spinner or `animate-pulse` on basic rectangles.                                                                          | Use `animate-pulse` on 2-3 simple `bg-muted rounded` rectangles, or a centered spinner. No shimmer gradients, no content-shaped skeletons unless the page is genuinely complex.                                                  |
| **Feature grid on internal pages**               | 2x3 or 3x3 grid of feature cards with icons and short descriptions, marketing-site style, on an internal tool page                             | AI copies the SaaS marketing "features section" pattern into tool UIs. Internal tools don't need to advertise features to their own users.                                                                                     | Remove entirely. If the page needs to list capabilities, use a simple bulleted list or inline links.                                                                                                                             |
| **Excessive dividers**                           | `<Separator />` or `<hr>` between every section, even when spacing alone provides clear separation                                             | AI inserts explicit dividers as a "safety" measure for visual hierarchy. Real products use whitespace as the primary separator.                                                                                                | Remove dividers where spacing (`mt-6`, `gap-8`) already creates clear separation. Keep dividers only between genuinely distinct content groups where spacing alone is ambiguous.                                                 |

### Category 5: Content & Copy Fingerprints

| Pattern                                  | Detection                                                                                                              | Why it reads as AI                                                                                                       | Fix                                                                                                                                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Emoji in professional UI**             | Emoji used as icons, in headers, in status labels, or in empty states                                                  | AI inserts emoji for "personality." Professional tools don't use emoji as UI elements.                                   | Replace all emoji with Lucide icons or remove entirely. Emoji is acceptable only in user-generated content (chat, comments).                                              |
| **Overly friendly copy**                 | "Welcome back!", "Great job!", "You're all set!", "No worries!", exclamation marks everywhere                          | AI writes enthusiastic copy. Tool UIs are neutral and informational.                                                     | Neutral, factual copy. "Dashboard" not "Welcome to your Dashboard!". "Import complete" not "Great job! Your import was successful!". Zero exclamation marks in UI chrome. |
| **Placeholder content that reads as AI** | Lorem ipsum, "Acme Corp", "Jane Doe", `example@email.com` in supposedly live UIs, or unrealistically clean sample data | AI fills in placeholder data that's obviously fake. Spotted by perfect data distributions, no edge cases, round numbers. | Use real data or realistic fake data with edge cases (long names, missing fields, varied quantities). If showing demo state, label it explicitly.                         |
| **Marketing language in tool UI**        | "Powerful analytics", "Seamless integration", "Enterprise-grade", adjective-heavy descriptions                         | AI copies marketing language from the training data. Internal tools describe functionality plainly.                      | Remove all adjectives from UI copy. Describe what the feature does, not how impressive it is. "Export to CSV" not "Powerful data export capabilities."                    |
| **Tooltip overload**                     | Every single element has a tooltip, including self-explanatory ones like "Settings" on a gear icon                     | AI adds tooltips everywhere as a "best practice." Real products tooltip only ambiguous elements.                         | Tooltip only elements where the label/icon is genuinely ambiguous. Self-explanatory elements (clearly labeled buttons, standard icons) need no tooltip.                   |

### Category 6: Structural Fingerprints

| Pattern                                               | Detection                                                                                                                                        | Why it reads as AI                                                                                                                      | Fix                                                                                                                                                                                                                                                             |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sidebar with colored icons**                        | Navigation sidebar where each menu item has an icon in a unique color or colored background circle                                               | AI generates sidebars where each nav item gets its own accent color. Real products use monochrome icons with active-state highlighting. | All sidebar icons: `text-muted-foreground`. Active state: `text-foreground` with `bg-accent` on the row. One color system, not a rainbow.                                                                                                                       |
| **Footer on a web app**                               | Copyright notice, links, "Built with X" footer on an authenticated application page                                                              | AI adds footers from website templates. SaaS tools don't have footers — screen real estate is for content.                              | Remove the footer entirely from authenticated app pages. Footer is only appropriate on marketing/public pages.                                                                                                                                                  |
| **Breadcrumbs + page title + subtitle + description** | Redundant orientation elements — the page title says "Products", the breadcrumb says "Home > Products", the subtitle says "Manage your products" | AI stacks multiple orientation elements for "clarity." One is enough.                                                                   | Keep one: either breadcrumbs (for deep hierarchies) or page title (for flat navigation). Remove subtitle/description unless it genuinely adds context the title doesn't. Never show both breadcrumbs and a page title that repeats the last breadcrumb segment. |
| **"Kitchen sink" settings page**                      | A settings page that tries to expose every possible configuration in one scrollable page with sections, toggles, and inputs                      | AI generates comprehensive settings pages. Real products expose settings progressively — most users never touch them.                   | Group settings into tabs or separate pages. Show only frequently-changed settings by default. Advanced settings behind a disclosure or separate section.                                                                                                        |

### The Composite Test

A single fingerprint is forgivable. The compound effect is what makes a page scream "AI-generated."

**Counting rules:** Only count P1 (structural) fingerprints toward the composite score. P2 (cosmetic) fingerprints are fixed individually and don't contribute to the composite threshold.

**Threshold:** **Three or more structural fingerprints on one page is a composite fail.**

- Stat cards + colored icon circles + uppercase headers + gradient accent = unmistakably AI (4 structural = fail)
- One `rounded-full` badge + one `shadow-lg` card + one divider = 0 structural fingerprints (all cosmetic P2 = not a composite fail)

**When composite fails, evaluate scope before acting:**

- If the page uses only local components (not shared): redesign in-review — strip decorative elements, rebuild with typography and spacing
- If the page relies heavily on shared components: raise the composite fail as a `[recommendation]` with a concrete redesign proposal. Fixing shared components in a design review risks breaking other pages. The recommendation should list which shared components need updating and what they should look like.
- If the page's fingerprints come from the project's established design language (used consistently across multiple pages): do NOT flag as composite fail — the patterns are intentional, even if they match the AI fingerprint taxonomy

---

## Quality Checklist

When evaluating a screen, check:

**Visual:**

- [ ] Could I mistake this for a real product, not a demo?
- [ ] Color palette cohesive (max 2-3 hues)?
- [ ] Any thick borders, heavy shadows, or decorative elements that add nothing?
- [ ] Every element earns its place?

**Typography:**

- [ ] Primary/secondary/tertiary content identifiable in under 2 seconds?
- [ ] More than 3 font sizes? (Red flag)
- [ ] Monospace used only for codes/IDs?

**Spacing:**

- [ ] Spacious, not cramped?
- [ ] Values consistent (multiples of 4 or 8)?
- [ ] Clear grouping through proximity?

**Accessibility:**

- [ ] WCAG AA contrast (4.5:1 normal text, 3:1 large text)?
- [ ] Focus states visible (2px minimum, high contrast)?
- [ ] Color never sole differentiator?
- [ ] Touch targets >= 44px?

**Interaction States:**

- [ ] Hover states present and consistent?
- [ ] Focus states visible and accessible?
- [ ] Empty states handled gracefully?
- [ ] Error states styled consistently?

**Functional UX:**

- [ ] All monetary values have explicit currency context?
- [ ] Every field/filter/status understandable without external docs?
- [ ] Thresholds and categorizations (High/Medium/Low) discoverable or configurable?
- [ ] Default filters/sorts visible and clearly indicating hidden data?
- [ ] Every link has a clear destination and works?
- [ ] Every column earns its place (drives decisions, not just present)?
- [ ] Page fits logically in its navigation group?
- [ ] Column configurability available for dense data tables?

**AI Fingerprint Scrub** (skip items that match the project's established design language):

- [ ] No stat cards or KPI card rows? (P1 — use inline summary text instead)
- [ ] No colored icon backgrounds? (P1 — bare icons or no icons)
- [ ] No gradient backgrounds on app UI elements? (P1)
- [ ] No `uppercase tracking-wide` labels? (P1 — sentence case, font-medium)
- [ ] No rainbow status badges (> 4 distinct hues)? (P1 — grey default, 3 colors max)
- [ ] No emoji used as UI icons or in headers? (P1)
- [ ] No marketing/enthusiastic copy in tool UI? (P1)
- [ ] No segmented controls where tabs/dropdowns would work? (P1)
- [ ] No `shadow-lg`/`shadow-xl` on cards? (P2 — shadow-sm max, or border-only)
- [ ] No `rounded-full` on buttons/badges? (P2 — rounded-md, except avatars)
- [ ] No `hover:scale-*` or `hover:-translate-y-*` transforms? (P2)
- [ ] No animated counters, glassmorphism, or over-designed skeleton loaders? (P2)
- [ ] No excessive dividers where spacing would suffice? (P2)
- [ ] Fewer than 3 AI fingerprints total on the page?

---

## Severity Levels

When reporting issues, classify by **impact** — not just visual quality. A misleading number is worse than an ugly border.

- **P0 — Broken / Misleading:**
  - Accessibility violation, unreadable text, broken layout, missing focus states
  - **Data that could cause wrong decisions:** currency confusion on profit calculations, misleading aggregates, broken conversion logic
  - **Broken navigation:** links that 404, dead ends, orphaned pages
  - **Hidden data without indication:** default filters that silently exclude records with no visible indicator

- **P1 — Confusing / Dated / AI-Generated:**
  - Patterns that make the app look unprofessional (thick borders, wrong palette, emoji icons, missing hover states)
  - **Structural AI fingerprints (P1):** patterns that fundamentally shape the page — stat card rows, dashboard-as-default layout, bento grids, hero sections on tools, feature grids, colored icon circles, rainbow status badges, AI purple accent, gradient backgrounds, enthusiastic/marketing copy. These are high-signal indicators that the page was generated, not designed.
  - **3+ fingerprints on one page:** escalate to a holistic redesign pass — individual fixes won't solve the compound "AI look"
  - **Undefined concepts:** fields/filters with no discoverable definition (user must guess what "Confidence" or "Qualified" means)
  - **Missing decision support:** key information required for the page's primary job is absent or buried
  - **Opaque logic:** computed fields (ROI, scores) with no way to verify or understand the calculation

- **P2 — Friction / Polish:**
  - Spacing inconsistencies, minor hierarchy issues, could-be-better moments
  - **Cosmetic AI fingerprints (P2):** isolated, low-impact patterns — a single `rounded-full` badge, one `shadow-lg` card, one `hover:scale-105`, excessive dividers, over-designed skeleton loaders, pill-shaped buttons. These are noticeable but don't define the page's overall feel. Fix when touching the same file.
  - **Unnecessary fields:** columns that don't inform decisions, show constant values, or duplicate other fields
  - **Missing power-user features:** no column config on dense tables, no bulk actions, no export
  - **Weak labels:** "View" instead of "View details", ambiguous button text

- **P3 — Nitpick:** Preference-level, fix only if touching the file anyway
