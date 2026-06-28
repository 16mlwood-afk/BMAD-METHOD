---
type: design-policy
project: '{project_name}'
status: approved
source: '{source}'
created: '{date}'
last_updated: '{date}'
created_by: '{user_name}'
version: 1
# inherits: (optional) name of a product-family overlay this project inherits, e.g. `bison-product-family-policy`.
#   When set, this policy inherits every rule in shared/<overlay>.md verbatim and states ONLY its
#   project-unique residue below (its exemplar domain, surface topology, imagery, concrete tokens/routes).
#   Leave unset for a standalone project — author every section in full.
inherits: '{family_overlay_or_none}'
consumed_by:
  - design-handoff
  - design-tuning
  - design-implement
  - design-review
  - modify-design-policy
precedence: design-policy > family-overlay (if inherited) > brand-identity > code tokens > design-standards
---

# Design Policy: {project_name}

> This is the project's visual constitution. It defines WHAT the product should feel like and WHY.
> For concrete design tokens (hex values, Tailwind classes, component specs), see `brand-identity.md`.
> For AI fingerprint detection and generic anti-patterns, see `_bmad/bmm/workflows/design/shared/design-standards.md`.

---

## 1. Visual Direction

**Identity:** {One sentence — what this app IS, not what it does. e.g., "A professional accounting tool that handles real money and should feel like it."}

**Register:** {The emotional tone — e.g., "Dense, precise, restrained. Authoritative but not corporate-bureaucratic."}

**Density:** {Data density preference — e.g., "High. Tables over cards. Numbers over charts. The UI trusts the user to read data."}

**What it's NOT:**
- {Anti-reference 1 — e.g., "Not a startup dashboard with stat cards and gradients"}
- {Anti-reference 2 — e.g., "Not a marketing site that needs to sell itself"}
- {Anti-reference 3 — e.g., "Not a generic Bootstrap admin template"}

---

## 2. Reference Products

Products whose visual approach we draw from. Be specific about WHAT to borrow.

| Product | Borrow This | Don't Borrow This |
|---------|------------|------------------|
| {name} | {specific pattern — e.g., "table density and restrained color"} | {what to avoid — e.g., "their opinionated dark mode"} |
| {name} | {specific pattern} | {what to avoid} |
| {name} | {specific pattern} | {what to avoid} |

---

## 3. Tone & Personality

**Voice:** {How the UI communicates — e.g., "Neutral and factual. No exclamation marks. No personality in chrome. Data speaks for itself."}

**Expertise assumed:** {What the user knows — e.g., "Users are domain experts. Don't over-explain business concepts. Do clarify system-specific terms (tooltips on computed fields)."}

**Error states:** {How errors communicate — e.g., "Factual and actionable. 'Invoice OCR failed: image quality too low. Upload a clearer scan.' Not 'Oops! Something went wrong.'"}

**Empty states:** {How empty states communicate — e.g., "Quiet, informational. 'No invoices for this period.' Not a friendly illustration with a CTA."}

---

## 4. Layout Principles

**Primary pattern:** {The dominant layout — e.g., "Full-width tables with a filter bar above. Detail views in slide-over panels or dedicated routes. No card grids for tabular data."}

**Page structure:** {Standard page anatomy — e.g., "Page title (compact) → inline summary stats → filter bar → content table → pagination. No hero sections, no stat card rows."}

**Navigation:** {Nav philosophy — e.g., "Sidebar navigation grouped by domain (Invoices, Orders, Expenses, Queries). No breadcrumbs on flat pages — only on drill-down views."}

**Responsive:** {Responsive approach — e.g., "Desktop-first. Tables remain tables on tablet (horizontal scroll). Mobile is read-only summary view, not full functionality."}

**Whitespace:** {Spacing philosophy — e.g., "Compact but not cramped. Tighter horizontal padding, more generous vertical spacing between sections. Asymmetric, not uniform."}

---

## 5. Component Language

**Tables:** {When and how — e.g., "Primary data display. Dense rows (h-9 or h-10). Header in muted foreground. Monospace for financial columns. Row hover for interactivity."}

**Cards:** {When and how — e.g., "Only for genuinely distinct objects (a form, a detail panel). Never for wrapping a single value or a list that should be a table."}

**Badges & Tags:** {Pattern — e.g., "Restrained. Grey default. Colored only for actionable states (warning, error). No rainbow. Ring-inset style, not filled pills."}

**Buttons:** {Hierarchy — e.g., "Primary (filled, one per view), Secondary (outline), Ghost (inline actions), Destructive (red, always with confirmation). Compact sizing (h-8 to h-9)."}

**Filters:** {Pattern — e.g., "Horizontal filter bar above content. Dropdowns and text inputs, not chip toggles. Active filters visible, clearable."}

**Modals & Dialogs:** {When — e.g., "Only for destructive confirmations and focused input forms. Never for displaying data that could be on-page."}

---

## 6. Status System

**Principle:** {e.g., "Color is exception, not default. Most statuses are neutral/grey. Color draws attention to items that need action."}

**Palette:**

| State | Meaning | Usage |
|-------|---------|-------|
| Neutral (grey) | {Default, pending, informational} | {Most statuses — the quiet baseline} |
| Success (green) | {Complete, verified, matched} | {Terminal positive states only} |
| Warning (amber) | {Needs attention, approaching threshold} | {Sparingly — items requiring review} |
| Error (red) | {Failed, rejected, overdue} | {Critical items requiring immediate action} |

**Maximum distinct status colors per view:** {e.g., "4. If a view needs more than 4 colors, the status model is too complex — simplify it, don't add more colors."}

---

## 7. Typography & Color Principles

**Font approach:** {e.g., "System font stack for UI. One specific monospace face for financial data and codes."}

**Size philosophy:** {e.g., "3 sizes maximum per component. Body at 13-14px. Muted secondary at 12px. Page titles at 18-20px. Differentiate by weight, not size."}

**Color restraint:** {e.g., "One accent color (blue). Backgrounds limited to 2 tones (white + one subtle grey). No gradients, no colored borders on containers, no colored icon backgrounds."}

**Monospace rules:** {e.g., "Strictly for: financial amounts, IDs, codes, tracking numbers. Never decorative. Never in headings."}

---

## 8. Hard Failures

Non-negotiable. A design containing any of these fails review regardless of how good the rest is.

The policy must cover all six AI-fingerprint categories from `_bmad/bmm/workflows/design/shared/design-standards.md` with at least one concrete, project-specific anti-pattern each. Reusing the seed example is allowed when it genuinely fits the project; rewriting is required when it doesn't. "See shared design-standards.md" is not a substitute for a concrete failure.

**Layout fingerprints**
1. {e.g., "Stat-card rows as page openers — use an inline summary line in the page header instead"}

**Typography fingerprints**
2. {e.g., "Uppercase tracking-wide labels in tool chrome — use sentence case at the policy's body size"}

**Color & visual treatment fingerprints**
3. {e.g., "AI-purple (`indigo-600` / `violet-500`) as primary accent; gradient backgrounds; glassmorphism"}

**Component fingerprints**
4. {e.g., "Pastel pill-with-leading-colored-dot for status — use the project's tinted-fill rectangular pill instead"}

**Content & copy fingerprints**
5. {e.g., "Emoji as UI icons; marketing copy in tool chrome ('Welcome back!', 'Great job!'); hover lift/scale framed as 'delight'"}

**Structural fingerprints**
6. {e.g., "Compositions that would work unchanged in a generic CRM or HR dashboard"}

**Project-specific failures** (additional rows, numbered 7+) — anything from `Anti-references` or domain risk that isn't covered above. Examples: badge-shape inconsistency across surfaces, more than N distinct status colors, sidebar layout inside feature pages.

For the full AI fingerprint taxonomy and detection criteria for each category, see `_bmad/bmm/workflows/design/shared/design-standards.md`.

---

## 9. Page Mode Rules

### Operational Pages
{How operational pages (process work, take actions) should be structured — e.g., "Table-first. Bulk actions in toolbar. Status transitions via inline controls. Sort by urgency or recency by default. Dense rows — the user processes many items per session."}

### Analytical Pages
{How analytical pages (understand patterns, compare data) should be structured — e.g., "Summary metrics above detail. Comparison-friendly layout. Charts only when they reveal patterns a table can't. Filter-heavy — the user asks questions of the data."}

### Hybrid Pages
{How pages serving both needs should balance them — e.g., "Default to operational view. Analytics available via tab or toggle. Don't mix operational controls with analytical displays — they have different cognitive modes."}

### List Rendering — pagination / virtualization (standing rule)
Any operational or analytical surface whose primary list / worklist grows past one screen — counts in the hundreds+, or **unbounded over time** (an accumulating queue, an ingest-fed worklist) — MUST **paginate** (page controls + a visible total count) or **virtualize** (windowed rows), never render every row in a single pass. A single-render list is allowed ONLY with a hard, stated row ceiling (e.g. "≤ the day's open sessions"). This is the policy half of the design-handoff **§5g** list-rendering derivation: the handoff makes the chosen mechanism a required deliverable on the primary list frame, and `design-review-pr` enforces this rule at PR time — so a growing list never ships un-paginated.

---

## 10. Changelog

Track policy evolution so `apply-design-policy-change` can read the author's intent alongside the structural diff.

| Version | Date | Sections Changed | Summary |
|---------|------|-----------------|---------|
| 1 | {created date} | All | Initial policy creation |

_Append a row each time the policy is updated. Be specific about which sections changed and why — downstream workflows use this to classify impact per page._

---

## Precedence & Integration

### Resolution Order

When a downstream workflow needs a design decision, it resolves from the most specific source available:

| Priority | Source | What it provides | When it wins |
|----------|--------|-----------------|--------------|
| 1 | **This policy** (`design-policy.md`) | Strategic direction, page modes, hard failures, tone, and any **explicit override** of an inherited family rule | Always — this is the project's visual constitution |
| 2 | **Family overlay** (`shared/<inherits>.md`, *if `inherits` is set*) | Shared product-family rules inherited verbatim (register, status system, money/relational discipline, positive-assertion floor) | When this policy doesn't override the inherited rule. Omit this tier entirely for a standalone project |
| 3 | **Brand identity** (`brand-identity.md`) | Concrete tokens, hex values, Tailwind classes, component specs | When neither this policy nor the overlay specifies a concrete value (e.g., exact border-radius) |
| 4 | **Code tokens** (utility-CSS config, CSS variables, theme/status helper files) | Current implementation values | When nothing above addresses the specific token |
| 5 | **Design standards** (`shared/design-standards.md`) | Generic anti-patterns, AI fingerprint rules | Fallback defaults — overridden by anything project-specific above |

**Inheritance.** When `inherits` is set in frontmatter (e.g. `bison-product-family-policy`), this policy does **not** restate the shared rules — it consumes them from the overlay and authors only its **project-unique residue** (exemplar domain, surface topology, product imagery, concrete tokens/routes, and any project-specific hard failures or positive assertions appended on top of the family floor). To diverge from an inherited rule, override it explicitly in the relevant section here and record the divergence in the changelog — the project policy wins per the order above.

**Conflict rule:** If brand identity contradicts this policy, the policy wins and brand identity should be updated to match. If code tokens contradict both, the code is design debt to be resolved.

### Consumed by

- `design-handoff` — reads this policy to anchor Claude Design briefs. Checks `design-policy.md` first, falls back to `brand-identity.md`.
- `design-tuning` — checks correction messages against this policy for consistency
- `design-implement` — references this policy when building components
- `design-review` — uses this policy as the standard for audit findings
- `modify-design-policy` — reads and updates this document when the visual direction evolves
- `apply-design-policy-change` — diffs versions, classifies impact per page, emits scoped migration briefs

### Updating this document

Update after major design decisions, direction changes, or when design-tuning sessions reveal patterns that should be codified. Increment `version` in frontmatter and update `last_updated`. Set `status` to `draft` during edits, `approved` when finalized.
