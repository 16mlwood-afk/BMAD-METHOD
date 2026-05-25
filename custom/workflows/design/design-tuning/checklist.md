---
name: design-tuning-checklist
description: 'Guardrail violation checks — used by step-02 to systematically evaluate each screenshot'
---

# Design Tuning Checklist

## Brand Identity Alignment (when brand identity exists)

### Visual Personality
- [ ] Design register matches the brand identity's stated personality (e.g., "dense, precise, restrained" — not airy, playful, or marketing-adjacent)
- [ ] Data density matches the stated preference (e.g., "high — tables over cards")
- [ ] Design does NOT feel like any of the "what it's NOT" items from the brand identity

### Typography (exact match required)
- [ ] Primary font matches brand identity (e.g., Inter Variable, not system sans-serif)
- [ ] Monospace font used ONLY for specified contexts (financial numbers, codes, IDs) — never decorative
- [ ] Body text size matches the brand's specified scale (e.g., 13px, not 14px)
- [ ] Heading letter-spacing matches (e.g., negative tracking, not default)
- [ ] No more than 3 font sizes per component

### Color (exact match required)
- [ ] Background color matches brand identity (e.g., off-white hsl(0,0%,98%), not pure white or cream)
- [ ] Semantic status colors match the brand's palette (e.g., emerald/amber/rose/stone/indigo)
- [ ] Badge pattern matches exactly (e.g., ring-inset, not filled or outlined)
- [ ] No colors outside the brand's defined palette without justification
- [ ] Domain-specific colors (if applicable) match the brand's assignments

### Component Patterns (exact match required)
- [ ] Card style matches (border, shadow, radius, padding — check each value)
- [ ] Button style matches (height, radius, press effect)
- [ ] Table styling matches (header style, row hover, alignment, monospace columns)
- [ ] Navigation matches (header height, tab style, active state)
- [ ] Status indicators match (badges, left borders, confidence bars)

### Reference Page Alignment
- [ ] Design would look at home alongside the brand's listed reference pages
- [ ] Same visual register as the gold-standard pages

### Hard Failures (from brand identity section 8)
- [ ] None of the numbered hard failure items are present in the design

### AI Sensitivity (from brand identity section 9)
- [ ] None of the project-specific sensitivity patterns are present

---

## Generic Guardrails (when no brand identity exists, or as supplement)

### Aesthetic
- [ ] Background is pure white or cool neutral gray — no cream, warm, or off-white tints
- [ ] Single neutral sans-serif family — no personality or display fonts
- [ ] Monospace used ONLY for IDs, codes, and tabular numbers — never in headings, labels, or navigation
- [ ] Color used functionally (state indication) — not for personality or branding
- [ ] Dark mode uses true dark neutrals — not navy or deep blue

### Voice
- [ ] Functional labeling — no marketing copy or aspirational headlines
- [ ] All UI elements are self-explanatory — no unexplained badges, no icons without labels
- [ ] No truncated text without a tooltip or expand affordance
- [ ] No editorial numbering ("01 —") or playful section names

### AI Design Tool Fingerprints
- [ ] No bento grid layout (asymmetric mixed-size card grids)
- [ ] No hero section on internal pages — content starts immediately
- [ ] No dashboard metric card grid as the page opener
- [ ] Dense layout — appropriate padding and section gaps for a tool UI
- [ ] No purple/violet primary color (unless assigned to a specific domain concept)
- [ ] No gradient text, gradient backgrounds, or glassmorphism
- [ ] Border radius appropriate for the brand (typically ≤ 10px on containers)
- [ ] No heavy decorative card shadows — elevation reserved for overlays/modals
- [ ] No gradient or colored dividers — 1px solid border only
- [ ] No per-item colored nav icons — monochrome, color = state only
- [ ] No semantic card fills (green card = good, red card = bad) — use badges, not fills
- [ ] No chatty empty states with illustrations
- [ ] No icon overload — icons only where they add recognition speed
- [ ] No hover scale transforms on cards — use background/border changes
- [ ] No animated number counters
- [ ] Status colors within the brand's stated limit (typically 4-5 max)

### Self-Test
- [ ] A reasonable observer would NOT guess this design is AI-generated

---

## Brief-Specific Constraints

- [ ] Navigation matches the app's existing structure — not invented or redesigned
- [ ] Viewport width matches the brief's responsive target
- [ ] Layout handles the stated data volume without overflow or cramming
- [ ] Stated user actions are accommodated (filters, bulk operations, etc.)
- [ ] Design tokens are consistent with stated values (if using existing system)
- [ ] No invented elements (branding, product names, version numbers, features not in the brief)
- [ ] Content fills the available container width — not a narrow centered card on a gray background

## Visual Reference Alignment

- [ ] Table structure aligns with the referenced product pattern
- [ ] Status badge treatment matches the specified approach
- [ ] Filter bar follows the referenced pattern
- [ ] Row density and spacing align with the specified targets
- [ ] Color strategy matches the referenced approach (restrained, state-only)
