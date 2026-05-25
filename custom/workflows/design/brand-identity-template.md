---
name: brand-identity-template
description: 'Template for project-specific brand identity documents. Populated per project and loaded by design-handoff and design-tuning workflows to anchor Claude Design to the project''s visual language.'
---

# Brand Identity Template

> **Purpose:** This template creates a persistent brand identity document for a project. Design workflows load this document and inject its content into briefs and tuning sessions, replacing generic anti-pattern lists with project-specific positive and negative visual anchors.
>
> **Location:** Save the populated version at `{planning_artifacts}/brand-identity.md`
>
> **How to populate:**
> 1. Audit the codebase: read `tailwind.config.*`, global CSS, 3-5 representative pages, shared components, and status/color utilities
> 2. Extract recurring patterns — what the app actually does, not what a template says it should do
> 3. Fill in each section with concrete values (hex codes, px values, Tailwind classes)
> 4. Identify 2-3 internal reference pages and 2-3 external product influences
>
> **When to update:** After a design-implement workflow delivers approved work, capture what worked. After a design-tuning session reveals a new anti-pattern, add it.

---

## File Template

```markdown
---
type: brand-identity
project: {project_name}
last_updated: {date}
version: 1
---

# Brand Identity: {project_name}

## 1. Visual Personality

**One sentence:** {What this app IS — not what it does, but what it FEELS like. e.g., "A professional accounting tool that handles real money and should feel like it."}

**Register:** {The emotional tone — e.g., "Dense, precise, restrained. Authoritative but not corporate-bureaucratic. Functional but not ugly."}

**Density:** {Data density preference — e.g., "High. Tables over cards. Numbers over charts. The UI trusts the user to read data — it doesn't over-explain."}

**What it's NOT:** {2-3 things this app must never feel like — e.g., "Not a startup dashboard. Not a marketing site. Not a design portfolio."}

---

## 2. Typography

**Primary font:** {exact font family — e.g., "Inter Variable"}
**Monospace font:** {exact font family and when used — e.g., "JetBrains Mono Variable — for financial numbers, codes, IDs only. Never decorative."}

### Type Scale

| Token | Size | Line height | Letter spacing | Usage |
|-------|------|-------------|---------------|-------|
| {token} | {px} | {px or ratio} | {em or normal} | {where used} |

### Typography Rules

- {rule 1 — e.g., "Negative letter-spacing on headings (-0.01em to -0.025em)"}
- {rule 2 — e.g., "Monospace only for financial figures, codes, and IDs — never in headings or as decorative voice"}
- {rule 3}

---

## 3. Color System

### Core Palette

| Role | Light | Dark | CSS Variable / Token |
|------|-------|------|---------------------|
| Background | {value} | {value} | {var/token} |
| Card / Surface | {value} | {value} | {var/token} |
| Foreground text | {value} | {value} | {var/token} |
| Muted text | {value} | {value} | {var/token} |
| Border | {value} | {value} | {var/token} |
| Primary accent | {value} | {value} | {var/token} |
| Accent surface | {value} | {value} | {var/token} |

### Semantic Status Colors

| State | Color | Background | Text | Ring/Border | Dark variants |
|-------|-------|-----------|------|------------|--------------|
| Success | {name} | {class} | {class} | {class} | {dark classes} |
| Warning | {name} | {class} | {class} | {class} | {dark classes} |
| Error | {name} | {class} | {class} | {class} | {dark classes} |
| Neutral | {name} | {class} | {class} | {class} | {dark classes} |
| Info | {name} | {class} | {class} | {class} | {dark classes} |

### Badge Pattern

{Describe the exact badge construction used throughout — the CSS classes, the pattern, the dark mode approach}

### Domain-Specific Colors (if any)

{Colors assigned to domain concepts — e.g., product categories, currencies, regions. List with hex values and Tailwind classes.}

---

## 4. Component Language

### Cards
{Exact pattern — e.g., "bg-card rounded-lg border shadow-sm. No heavy shadows. Left-border accent (border-l-[3px]) for colored variants. Internal padding p-4."}

### Tables
{Exact pattern — table structure, header style, row hover, alignment, monospace columns}

### Badges & Tags
{The badge construction — ring-inset? pill? what colors? what sizes?}

### Buttons
{Button hierarchy — primary, secondary, ghost, destructive. Sizes. Press effects.}

### Status Indicators
{How status is communicated visually — badges, left borders, color dots, progress bars}

### Navigation
{Header height, nav style, active state treatment, tab style}

### Data Display
{How financial numbers are formatted, how percentages appear, how dates are shown}

---

## 5. Spacing & Layout

**Container:** {max-width and padding — e.g., "max-w-[1400px] mx-auto px-4 lg:px-6"}
**Card padding:** {e.g., "p-4 standard, px-4 py-3 for header rows"}
**Section gaps:** {e.g., "gap-4 within sections, gap-6 between sections"}
**Border radius:** {e.g., "rounded-lg (10px) for cards, rounded-md (8px) for buttons, rounded-sm (4px) for small elements"}

---

## 6. Reference Pages (Internal)

Pages in this app that represent the gold standard. Designers should match their register and quality.

| Page | Route | Why it's the standard |
|------|-------|--------------------- |
| {name} | {/route} | {what makes it good} |
| {name} | {/route} | {what makes it good} |
| {name} | {/route} | {what makes it good} |

---

## 7. External Influences

Products whose visual approach we want to match for specific aspects. Be precise about WHAT to borrow.

| Product | Borrow this | Don't borrow this |
|---------|------------|------------------|
| {name} | {specific pattern} | {what to avoid from them} |
| {name} | {specific pattern} | {what to avoid from them} |

---

## 8. Hard Failures

Things this brand NEVER does. These are non-negotiable — a design that includes any of these fails review regardless of how good the rest is.

1. {hard failure — e.g., "No stat cards with icons as page openers"}
2. {hard failure}
3. {hard failure}
...

---

## 9. AI Fingerprint Sensitivity

Beyond the standard AI fingerprint checklist (which the workflow loads separately), these are patterns this specific project is extra sensitive to:

| Pattern | Why we're sensitive | What to do instead |
|---------|-------------------|-------------------|
| {pattern} | {reason} | {alternative} |
```
