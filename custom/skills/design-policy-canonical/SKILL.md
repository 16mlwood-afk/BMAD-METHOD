---
name: design-policy-canonical
description: Enforce the project's design policy (`docs/design-policy.md` in the project root) as the authoritative source for visual and compositional decisions. Use when designing or redesigning pages, drawers, or detail views; choosing layout composition; picking or proposing components; generating Claude Design briefs; interpreting Claude Design artifacts for implementation; iterating designs against a brief; or creating or revising design-system artifacts (policy, tokens, shared components, badge/button/filter patterns). Do not use for unrelated code refactors, copy edits, bug fixes, performance work, schema changes, or backend changes that have no visual impact.
---

# Design Policy — Canonical Enforcement

`docs/design-policy.md` in the project root is the source of truth for visual direction, layout, and component decisions in this codebase. This skill exists to make sure that file is read, trusted, and enforced whenever a design decision is in scope. The tone, palette, density, and component vocabulary the skill enforces are whatever the project policy declares — this skill does not inject its own aesthetic.

## Precondition

This skill requires `docs/design-policy.md` to exist in the project root. If it does not, halt with: `"This project has no docs/design-policy.md. The design-policy-canonical skill requires one — create the policy first (the BMAD workflow create-design-policy can scaffold it), then re-invoke."` Do not improvise a policy from existing screens.

## Trust Hierarchy

When sources of design guidance conflict, resolve in this order:

1. **`tailwind.config.ts`** (or the project's equivalent token source) — live project tokens (typography scale, colors, spacing, radii) always win. Tokens are ground truth for what exists in the system.
2. **`docs/design-policy.md`** — project visual policy. This is what this skill anchors to.
3. **Shared BMAD design standards** (`_bmad/bmm/workflows/design/shared/design-standards.md`) — universal anti-fingerprint rules. They apply on top of the project policy, but never override it.

**Do not infer design from existing screens.** The current implementation may pre-date the policy or be mid-migration. When an existing page contradicts the policy, the policy wins. When proposing changes that diverge from current UI, cite the policy section that justifies the divergence.

## How to Apply the Policy

Work in this order whenever a design decision is being made:

1. **Declare page mode first** — operational (table-first) or analytical (chart-first), per the policy's Page Modes section. Hybrid pages default to operational unless the policy says otherwise. The mode constrains every downstream decision; do not skip this step.
2. **Choose composition from the mode** — operational pages are tables with a top filter bar and integrated status pills. Analytical pages are charts with tabular drill-down evidence below. Do not improvise alternative shells (sidebars, hero strips, dashboard grids) unless the policy explicitly authorizes them.
3. **Pick components from the existing system** — surface tokens, icon set, the project's pill-badge component, the project's filter chip pattern, etc. If a needed primitive is missing, propose adding it to the system rather than inventing a one-off variant for this page.
4. **Apply visual treatment from tokens and the policy's color/typography rules** — never hardcode hex/colors when a token exists. Status colors come from whatever utility the project designates (look for a `status` helper in the project's lib/ or utils/ tree). Status badges carry weight by operational urgency as defined in the policy's Status System section; respect that hierarchy explicitly. Body text density, font scale, and monospace usage are governed by the policy's Color & Typography section.
5. **Validate against the policy's Hard Failures and Anti-default compositions sections** before delivering. If any apply, revise — do not ship.

## Refuse Explicitly

When asked to produce something that conflicts with the policy, refuse and cite the specific policy section (and subsection where it exists), then offer the policy-compliant alternative. Examples of refusal templates the project policy will typically authorize:

**Composition (the policy's Anti-default compositions / Hard Failures):**
- "Add a stat-card grid to the top of the page" → refuse if the policy bans rows of identical stat cards. Counter-offer: an inline summary line in the page header.
- "Add a row of summary cards above the table" → refuse if the policy bans "summary cards + table" template layouts. Counter-offer: an inline header summary line for headline counts; reserve any narrow analytics band for content that genuinely needs a visualization.
- "Make this analytical page open with a 6-tile KPI grid" → refuse if the policy bans the analytics-dashboard tile grid as a page opener. Counter-offer: one or two restrained charts with clear narrative, supporting tables, KPI numbers integrated into a header summary line.
- "Make this a centered card layout" → refuse if the policy reserves centered card layouts for settings-style screens.
- "Add a hero strip explaining the page" → refuse if the policy bans hero strips above working tables.
- "Build this so it works as a generic admin shell" → refuse if the policy bans compositions that could be lifted into a different SaaS admin without modification.

**Status badges (per the policy's Status System):**
- "Use a pastel pill with a leading colored dot for status" → refuse if the policy bans the pastel-pill-with-dot pattern. Counter-offer the policy's actual badge shape and treatment.
- "Give every status the same visual weight" → refuse if the policy mandates a status-color hierarchy by operational urgency.
- "Show two equal-weight colored pills on each row" → refuse if the policy mandates one primary status plus at most one quieter secondary signal.
- "Use `rounded-full` for the status pill" → refuse if the policy mandates a specific rectangular radius.
- "Use a different badge style on the queue page than on the table page" → refuse if the policy mandates badge consistency across surfaces.

**Color and typography:**
- Refuse banned accent colors (e.g. "AI purple" if the policy lists it).
- Refuse banned button shapes for primary CTAs.

**Exemplars (per the policy's Exemplars section, if present):**
- "Build a demo screen with placeholder data (lorem ipsum / fake records)" → refuse if the policy mandates real domain content.
- "Make a generic example I can adapt for another product" → refuse if the policy applies a lift test (exemplars that work unchanged in a different SaaS admin fail). Counter-offer: an exemplar that declares its page mode and cites which policy sections it demonstrates.

A short "this conflicts with §X (subsection name), here's the policy-compliant alternative" is the correct response — not silent compliance.

## Detail Views

Detail drawers and detail pages are extensions of operational lists, not separate experiences:

- Right-side drawer is the typical default; full-page is the exception (only when the workflow cannot fit a drawer). The policy's Detail Views section is authoritative if it disagrees.
- Same surface, typography, and badge system as the list — never re-skin the detail view.
- No KPI cards, charts, or bento layouts inside the drawer.

## Exemplars

When producing design exemplars (BMAD `design-agent` outputs, component playground stories, brief illustrations, mockups attached to handoff or tuning artifacts), follow the policy's Exemplars section. Typical rules:

- Declare the page mode (operational / analytical / detail) before showing the surface.
- Cite which policy sections the exemplar demonstrates.
- Use real domain content from this product (the policy will name the project's canonical domain objects — invoices, tickets, orders, registrations, whatever applies) — never placeholder data that could belong to any product.
- Apply the lift test if the policy mandates it: if the exemplar would work unchanged as a generic CRM, HR dashboard, or analytics tool, it fails and must be revised.

## When This Skill Applies

Apply when the task is design-bearing:

- Designing or redesigning a page, drawer, or detail view.
- Choosing layout composition (table vs chart, single panel vs multi-section, drawer vs page).
- Proposing or picking components (badge variants, button styles, filter chips, summary headers).
- Generating a Claude Design brief (BMAD `design-handoff` workflow).
- Interpreting a Claude Design artifact for implementation (BMAD `design-implement` workflow).
- Iterating a design against the brief (BMAD `design-tuning` workflow).
- Auditing a live page for design quality (BMAD `design-review` workflow).
- Creating or extending the design system itself.

## When This Skill Does NOT Apply

Do not load policy framing for non-design work:

- Bug fixes that don't change visual structure.
- Backend refactors, schema migrations, API route additions without UI.
- Performance, type-checking, build, or tooling work.
- Documentation outside `docs/design-policy.md` itself.
- Microcopy or label tweaks that don't alter layout, color, or component choice.

If a task starts as non-design but acquires a visual change (a new field surfaces on a page, a new status state is added), re-enter design mode for that change only and apply the policy to it.

## Output Expectations

When this skill is active, design-bearing output should:

- Name the page mode explicitly (operational / analytical / detail).
- Reference policy sections by number, and subsection name where it exists, when justifying composition and component decisions.
- Use existing tokens and components by name, not invented inline values.
- For status badges, name the color weight (primary / mid / restrained / resting, per the policy's status hierarchy) explicitly so the policy is auditable.
- For exemplars, follow the policy's disclosure rules (declare mode, cite sections, use real domain content).
- Surface any tension between the request and the policy before resolving it — never silently compromise.
- Flag anti-patterns in upstream input (briefs, screenshots, prior implementations) rather than carrying them forward.
