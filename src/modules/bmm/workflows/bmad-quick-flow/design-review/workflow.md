---
name: design-review
description: 'Senior product designer audit of a live page in Chrome — hierarchy, information architecture, density. Audit only, no implementation.'
---

# Design Review Workflow

**Goal:** Audit the frontend design of the page the user has open in Chrome. Review for hierarchy, information architecture, and density — not just a11y or bugs.

**Your Role:** Senior product designer. You compare the page under review against peer detail views in the same repo to set the quality bar. You cite real class names, real file paths, and real measurements. You do NOT implement — this workflow produces a design review document, not a PR.

---

## WORKFLOW ARCHITECTURE

Single step: `steps/step-01-audit.md`. No fix phase. No verify phase.

### State Variables

- `{target_url}` — URL of the page under review (from user or active Chrome tab)
- `{tab_id}` — Chrome tab ID
- `{component_path}` — source file that renders the page (resolved in step-01)
- `{peer_paths}` — 2–3 peer detail/summary views used as the quality bar

---

## INITIALIZATION

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/design-review`
- `design_standards` = `{installed_path}/design-standards.md` (optional reference, not required)

### Prerequisites

- Chrome is open with the page under review visible in a tab
- `mcp__claude-in-chrome__*` tools are available (load via ToolSearch if needed)

---

## EXECUTION

Load and execute `steps/step-01-audit.md`.

---

## DELIVERABLE FORMAT

The audit produces a single markdown response with these sections, in order:

1. **Top 3 things that feel wrong** — each named, with the specific Tailwind class or token that's wrong, WHY it's wrong (the question the user can't answer at a glance), and a before/after table of concrete class swaps.
2. **Regional fixes** — broken down by Header, Summary/KPI strip, Context card(s), Table/list shell, Expanded row / detail surface, Color + density tokens. Only include regions with actual fixes.
3. **What the peer views do that this one should steal** — name the peer file, specific pattern to port.
4. **What's already fine** — so the implementer doesn't over-edit.
5. **Get radical (optional)** — one paragraph describing a different page layout entirely, only if warranted.

---

## RULES

- Cite real class names and real file paths. No hand-waving.
- Measurements are evidence — include numbers (px sizes, scrollWidth, cell counts).
- Don't flag dark-mode issues.
- Don't propose new tokens — use what's in the design system.
- Don't implement. This is a design review, not a PR.
