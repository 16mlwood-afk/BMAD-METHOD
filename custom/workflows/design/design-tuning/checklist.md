---
name: design-tuning-checklist
description: 'Role-keyed guardrail checklist — a quick companion to step-02. Project-specific VALUES (palette, fonts, radii, status colors, badge treatment) live in the project design policy, never here.'
---

# Design Tuning Checklist

> **This checklist is project-agnostic and role-keyed.** It names the *roles* to inspect and the *rules* that govern each, but it deliberately holds **no project-specific values** — no palette, no font names, no radius/shadow numbers, no badge-treatment specifics. Those are read from the project's `docs/design-policy.md` (loaded in step-01 §1b) at run time. Hardcoding one project's values here is exactly the drift this rewrite removed.
>
> **Inspect by semantic ROLE, not element type.** The recurring failure is a rule that governs a role (status indicator, CTA, identifier, analytics viz, surface fill, drawer) slipping through because it appeared on an element the reviewer wasn't looking at — a band's stat-row content, a progress bar's status colors. For every role below, inspect the rule *wherever it appears*, not only on the canonical element. See step-02 §1b "Role catch-all" for the authoritative procedure.

## Role: status indicator

Includes pills, badges, dots, row tints, left-borders, **progress / meter / lifecycle-stage segments, chart series, coverage strips** — anything whose color or shape encodes state.

- [ ] Shape and treatment match the project policy's status pattern (loaded from policy; e.g. rectangular pill vs capsule, tint vs saturated fill, leading dot present/absent)
- [ ] Total distinct status colors across **all** state-encoding elements stays within the policy cap
- [ ] No off-palette status hue (no hue the policy excludes from the status set)
- [ ] No rainbow stage mapping — a multi-segment lifecycle/progress bar distinguishes stages by position/order/weight, not by giving each its own hue
- [ ] Tone matches meaning — failure tone (red, where the policy defines one) is reserved for genuine failures; pending/awaiting/unmatched use the attention tone, never the failure tone
- [ ] The same state reads in the same tone on every element and every surface (list ↔ drawer ↔ sibling pages)
- [ ] One primary status per row; secondary signals are quieter (muted text/icon), never a second equal-weight pill
- [ ] No status over-encoding by repetition — the same status/severity is not repainted 3–4× on one row (left-border + pill + colored secondary text + colored count). The 4-color cap is breadth; this is repetition on one row (step-02 §2 Craft & legibility)

## Role: primary action / CTA

Any button, wherever it sits — header, row, footer, bulk bar.

- [ ] Primary CTA shape matches policy (e.g. rectangular, not capsule/`rounded-full`)
- [ ] At most one primary action per row; others move to overflow/drawer
- [ ] Bulk actions use the policy's bulk-action pattern (e.g. a transient floating bar), not an inline/header toolbar or a button row above the table

## Role: canonical identifier

ASIN/SKU, order/batch number, supplier, marketplace, product/prep-center code, currency, date.

- [ ] Each identifier class renders in one consistent casing/label form across every cell and across the list ↔ drawer boundary
- [ ] No raw enum/code leakage where a human label is expected
- [ ] Format (monospace for IDs, etc.) matches the policy and is consistent with sibling surfaces

## Role: analytics visualization

Bands, strips, charts, meters on operational/analytical pages.

- [ ] Subordinate to the table — ≤ one compact row; the table keeps the majority of above-the-fold height
- [ ] Content is a *visualization* (coverage strip / trend / meter), not a row of summary count figures (those belong in the inline header summary line)
- [ ] Reads as a single shared band — not a row of per-panel cards (per-tile border/fill/shadow = card-grid violation)
- [ ] Every element drills somewhere — no ornamental figures
- [ ] Not redundant with adjacent text — a per-row micro-bar/meter/sparkline must show something its own caption/value does not (proportion/position/trend); if the text beside it already says it, the element is decoration (step-02 §2 Craft & legibility)

## Role: surface fill / layout

- [ ] No status-colored card fills (green card / red card); status lives in badges, not fills
- [ ] No sidebar inside the feature page; full-width content
- [ ] No hero strip, banner, or marketing intro above the working table
- [ ] No centered card-on-gray layout
- [ ] No gradient/glassmorphism backgrounds; container radius and shadow within policy limits

## Role: detail drawer / overflow

Applies even on an operational/analytical page (the §7 default pattern).

- [ ] No KPI cards, charts, or mini-dashboard inside the drawer
- [ ] No more than the policy's max field groups (typically 3–4)
- [ ] Same surface/typography/status system as the list — not a form from another app

## Role: labels & wording (craft & legibility)

- [ ] No label collision — one label does not name two different quantities on the same screen (e.g. a chip "To commit" counting partners while a column "To commit" counts orders)
- [ ] Label↔severity wording matches — a genuine-failure (red) status is worded as a failure ("Commit failed"), not softened ("Needs attention") while the real attention state owns a different word
- [ ] Iconography↔meaning matches — each icon's glyph denotes its action (no theme toggle wearing a "layers" glyph, no refresh with an unrelated icon)

## Cross-cutting (read from policy)

- [ ] Typography: within the policy's font family/size/casing rules — no uppercase tracking-wide tool chrome, no all-caps headers, monospace only where the policy allows
- [ ] Icons: no emoji as UI icons; no icon-on-every-label overload; no colored-icon-circle clusters / 3-feature icon rows
- [ ] Voice: functional labeling, no marketing copy, no editorial numbering
- [ ] No AI-tool fingerprints the policy names (animated counters, hover scale, gradient dividers, etc.)

## Self-test

- [ ] A reasonable observer would NOT guess this design is AI-generated
- [ ] The design would look at home beside the policy's named reference pages
