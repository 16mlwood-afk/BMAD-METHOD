---
name: design-standards
description: 'Design philosophy, color palette, typography rules, AI fingerprint scan, quality checklist, and reference standards for the design agent workflow.'
---

# Design Standards

## Core Philosophy

### 1. Restraint Over Decoration

The best UI communicates through structure, spacing, and typography — not through borders, boxes, and color. Before adding any visual element, ask: "Does removing this make it worse?" If no, remove it.

**Concrete rules:**

- Prefer whitespace over dividers. Use border-bottom only when content groups are genuinely ambiguous without them.
- Maximum 2 background colors per component (e.g., white + one subtle grey). Three signals a problem.
- One accent color per context. Not amber AND brown AND cream. Pick one.
- No decorative borders on containers. If a card needs a border, use `1px solid` at `#E5E7EB` or lighter — never 2px, never colored borders unless it's a focus ring or status indicator.

### 2. Modern, Not Dated

**Avoid (codes as "2015 template"):**

- Thick colored borders on light backgrounds (the "Bootstrap card" look)
- Amber/brown/cream color combinations (reads as "warning" or "institutional")
- Heavy uppercase + wide letter-spacing on labels (bureaucratic)
- Emoji as icons in professional UI (use Lucide or no icons at all)
- Fake UI chrome (simulated browser bars, email headers) around content
- Rounded pill buttons with bright fills as primary CTA
- Gradient backgrounds on cards or sections
- Drop shadows heavier than `0 1px 3px rgba(0,0,0,0.06)`

**Target (codes as "2025 production"):**

- Neutral palette with a single restrained accent (blue, indigo, or green — not amber)
- System font stack or one carefully chosen typeface
- Generous spacing with clear hierarchy through size/weight alone
- Subtle separations: 1px borders at `#F0F0F0`, or spacing only, or background color shift
- Micro-interactions on hover/focus that feel natural, not decorative
- Content-first: the data IS the design, not decoration around the data

### 3. Context Determines Everything

Before designing, answer:

- **Who sees this?** (A warehouse worker at 7am on their phone != a designer reviewing a component library)
- **What's the one thing they need?** (For an OTP email: the 6-digit code. Everything else is supporting.)
- **Where does this appear?** (In Gmail? In a dashboard? In Slack? Match the surrounding context.)
- **What's the emotional register?** (Urgent notification? Calm status report? Celebration?)
- **What breakpoints matter?** (Desktop-only internal tool? Mobile-first customer-facing page? Both?)

### 4. Responsive / Mobile Scope

Be explicit about scope:

- **If mobile is important**, note it: "Mobile breakpoints should stack the sidebar below main content and increase touch targets to 48px."
- **If mobile is out of scope**, say so: "Desktop only. Mobile layout is out of scope for this pass."
- **If unknown**, ask: "Does this page need to work on mobile?"
- **Never silently design desktop-only** when the page clearly needs mobile (anything customer-facing, anything a warehouse worker uses).

---

## Typography

Typography is 80% of design. Get it right and the rest follows.

**Rules:**

- System font stack for UI: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Monospace only for codes, IDs, technical values: `'SF Mono', 'Cascadia Code', 'Consolas', monospace`
- Maximum 3 font sizes per component. If you need 4+, the hierarchy is wrong.
- Body text: 14-15px, `line-height: 1.5-1.6`, color `#333` or `#374151`
- Secondary text: 12-13px, color `#6B7280` or `#9CA3AF`
- Headings differentiated by weight (600-700) and size, not by color or decoration
- Never use `letter-spacing` wider than `0.05em` unless it's a 9px micro-label

---

## Color Palette

Default palette for business/operations tools (override only with explicit reason):

```
Background:      #FFFFFF / #F9FAFB / #F3F4F6
Text:            #111827 / #6B7280 / #9CA3AF
Border:          #E5E7EB / #F3F4F6
Accent:          #2563EB (blue-600) / #EFF6FF (blue-50 bg) / #1D4ED8 (blue-700 text)
Success:         #059669 (emerald-600)
Warning:         #D97706 (amber-600 — sparingly)
Error:           #DC2626 (red-600)
```

These map to Tailwind defaults — in a Tailwind project, reference by name (`gray-200`, `blue-600`).

**When to deviate:** Brand colors, dark mode, or when context demands it. Always deviate intentionally, never by accident.

---

## AI Fingerprint Scan (Pre-Generation Gate)

Run this before producing any design spec. This catches patterns that make UI look AI-generated.

**First rule:** Check if the pattern is already used consistently across the project. If it's the established design language, skip it — ripping it out would create worse inconsistency.

### P1 — Structural fingerprints (must fix)

These define the page's overall "AI-generated" feel:

- Stat card rows / KPI cards with icons
- Colored icon backgrounds (pastel circle + colored icon)
- Rainbow status badges (> 4 distinct hues)
- Gradient backgrounds on app UI
- ALL CAPS + letter-spacing labels
- AI purple/indigo as primary accent (unless project brand)
- Dashboard-as-default layout on non-dashboard pages
- Hero sections on internal tools
- Feature grids (marketing-style 2x3 card grids)
- Emoji as UI icons
- Marketing/enthusiastic copy ("Welcome back!", "Powerful analytics")
- Segmented controls where tabs/dropdowns would work

### P2 — Cosmetic fingerprints (fix when touching the file)

Noticeable but don't define the page:

- `rounded-full` on buttons/badges (not avatars)
- `shadow-lg` / `shadow-xl` on cards (not modals)
- `hover:scale-*` or `hover:-translate-y-*` transforms
- Over-designed skeleton loaders with shimmer
- Excessive `<Separator />` dividers
- Pill-shaped buttons
- Animated number counters
- Glassmorphism on non-modal elements

### Composite test

3+ structural (P1) fingerprints on one page = holistic redesign, not piecemeal fixes. If that touches shared components, raise as a recommendation instead of fixing in-review.

### Fix philosophy

Always reduce to the plainest alternative. Stat cards become inline text. Colored icon circles become bare icons. Rainbow badges become grey-default with 3 colors max. The correct fix is almost always removal.

---

## Anti-Patterns (Claude-Specific)

The most common ways Claude-generated UI goes wrong:

1. **"Dark mode dashboard wrapper around a simple thing"** — Match context. An email should look like an email, not a dashboard.
2. **"IBM Plex Mono for everything because it looks technical"** — System fonts render faster and look native. Custom fonts need a reason.
3. **"Scoring rubric before showing the design"** — Don't add process artifacts. User wants the design, not a score sheet.
4. **"Automation flow diagram inside the email mock-up"** — Don't mix deliverables. An email is an email. A system diagram is separate.
5. **"Amber/orange because it's notification-adjacent"** — Amber = warning in most design systems. Blue for informational. Green for success. Amber only for actual warnings.
6. **"Every section needs a border, card, or background"** — Whitespace is the best separator. Use it first, borders second, background third.
7. **"Let me add a cute toggle and tabs to a mock-up"** — If the deliverable is "what does this email look like," show the email. Not a component demo shell around it.
8. **"Silently dropping features from mockups"** — If you simplify for clarity, say so. A dev who doesn't see a feature may assume it's been cut. Always list what you omitted and confirm it's still required.

---

## Reference Standards

Don't just "reference Linear." Reference specific patterns:

**Transactional emails:** Stripe receipts, Resend notifications, Vercel deploy emails. White background, minimal color, generous whitespace, hierarchy through typography alone, no decorative borders.

**Dashboard components:** Linear's sidebar, Vercel's deployment cards, GitHub's PR timeline. Neutral palette with one accent, tight spacing, information density without clutter.

**Notification UIs:** Slack's message formatting, Apple's notification banners, Superhuman's email rendering. Content-first, minimal chrome, instant scanability.

**Common thread:** Restraint. Design serves content. Color is for meaning (status, links, emphasis), not decoration. Typography does the heavy lifting.

---

## Accessibility (Non-Negotiable)

- WCAG AA minimum (4.5:1 normal text, 3:1 large text)
- Focus states visible (2px minimum, high contrast)
- Color never sole differentiator (pair with icons or text)
- Touch targets >= 44px
- Keyboard navigable
- Screen reader tested (semantic HTML, ARIA where needed)

---

## Quality Checklist

### Visual

- Could I mistake this for a real product, not a demo?
- Color palette cohesive (max 2-3 hues)?
- Any thick borders, heavy shadows, or decorative elements that add nothing?
- Every element earns its place? Remove one thing — is it better now?

### Typography

- Primary/secondary/tertiary content identifiable in under 2 seconds?
- More than 3 font sizes? (Red flag)
- Monospace used only for codes/IDs?

### Spacing

- Spacious, not cramped?
- Values consistent (multiples of 4 or 8)?
- Clear grouping through proximity?

### Context

- Would the actual end-user find this useful on their actual device?
- Matches the platform it lives on?
- Emotional register is right?

### Handoff Safety

- Omitted features explicitly listed as "still required"?
- Any proposed removals/replacements clearly flagged as recommendations?
- No ambiguity where a dev might interpret "not shown" as "not needed"?

---

## Spec Writing Rules (When Output Goes to Claude Code)

When producing specs that a dev agent will implement:

- **Be precise:** No "should feel light" — use exact values (`opacity: 0.7`, `font-weight: 300`, `color: #6B7280`)
- **Be complete:** Every state (default, hover, active, focus, disabled, error), every breakpoint, every edge case
- **Be prioritized:** Critical changes first, nice-to-haves labeled
- **Be testable:** User can verify each item with browser DevTools
- **Be additive:** Specs describe what to _change or add_ to the existing implementation. Never imply removal by omission. If a feature should be removed, say so explicitly with rationale.

Keep specs concise. A tight 30-line spec beats a 200-line template.
