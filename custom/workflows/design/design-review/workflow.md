---
name: design-review
description: 'Senior product designer audit of a live page in Chrome — hierarchy, information architecture, density. Audit only, no implementation. Supports an artifact mode that emits a structured screen-review.md for downstream consumption by design-handoff (refine-screen).'
main_config: '{project-root}/_bmad/bmm/config.yaml'
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
- `{brand_identity}` — Contents of the project's brand identity document (if it exists). When present, provides the authoritative visual language — typography, colors, component patterns, and hard failures.
- `{brand_identity_path}` — Path to the brand identity document
- `{output_mode}` — `"interactive"` (default) emits the human-readable review in chat. `"artifact"` additionally writes a structured `screen-review-{slug}-{date}.md` file to `{implementation_artifacts}` that downstream workflows (notably `design-handoff` in refine-screen mode) can consume programmatically.
- `{target_slug}` — kebab-case slug derived from the route (used for the artifact filename and to let design-handoff match the right artifact to the target feature)
- `{artifact_path}` — Absolute path where the artifact is written (only set when `{output_mode}` = "artifact")
- `{review_findings}` — Structured findings object built during audit: `{ violations: [...], edge_states: [...], peer_steals: [...], keepers: [...], measurements: {...} }`. The interactive review and the artifact are both rendered from this single source. `violations` is an ordered list (hard failure → major → minor); no fixed count.

---

## INITIALIZATION

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/design/design-review`
- `design_standards` = `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md` (shared reference — superseded by brand identity on project-specific values)
- `brand_identity` = `{project-root}/_bmad-output/planning-artifacts/brand-identity.md` (load if exists)

### Brand Identity Loading

```bash
ls {project-root}/_bmad-output/planning-artifacts/brand-identity.md 2>/dev/null
```

If found, read and store as `{brand_identity}`. The brand identity provides project-specific visual standards (exact typography, exact colors, exact component patterns) that are more authoritative than the generic `design-standards.md`. When both exist, the brand identity wins on specifics — use `design-standards.md` only for categories the brand identity doesn't cover (functional UX, accessibility, severity levels).

### Prerequisites

- Chrome is open with the page under review visible in a tab
- `mcp__claude-in-chrome__*` tools are available (load via ToolSearch if needed)

### Output Mode Detection

The workflow runs in one of two modes:

**Interactive (default).** Emit the human-readable review in chat. The user reads it and decides what to do.

**Artifact.** Additionally write a structured `screen-review-{slug}-{date}.md` to `{implementation_artifacts}`. This file is the input contract for `design-handoff` in refine-screen mode — it lets the next workflow consume the diagnostic without re-prompting the user for complaints.

Detect mode in this order:

1. If the invocation includes the literal token `--artifact` (anywhere in the user's prompt or in the prompt-expansion text), set `{output_mode}` = `"artifact"`.
2. If a caller workflow has already set `{output_mode}` in the state, honor it.
3. Otherwise default to `"interactive"`.

Artifact mode does NOT suppress the human-readable review — it adds the file alongside. This way a user running `--artifact` still sees the audit in chat AND has a file the next workflow can pick up.

---

## EXECUTION

Load and execute `steps/step-01-audit.md`.

---

## DELIVERABLE FORMAT

### Interactive output (always emitted)

A single markdown response with these sections, in order:

1. **Top 3 things that feel wrong** — each named, with the specific Tailwind class or token that's wrong, WHY it's wrong (the question the user can't answer at a glance), and a before/after table of concrete class swaps.
2. **Regional fixes** — broken down by Header, Summary/KPI strip, Context card(s), Table/list shell, Expanded row / detail surface, Color + density tokens. Only include regions with actual fixes.
3. **What the peer views do that this one should steal** — name the peer file, specific pattern to port.
4. **What's already fine** — so the implementer doesn't over-edit.
5. **Get radical (optional)** — one paragraph describing a different page layout entirely, only if warranted.

### Artifact output (only when `{output_mode}` = "artifact")

A second deliverable: a file at `{implementation_artifacts}/screen-review-{target_slug}-{date}.md` with this exact contract. The file is machine-consumable — `design-handoff` (refine-screen mode) parses it to seed the refinement brief, binding each violation back to its cited rule without ambiguity.

```markdown
---
type: screen-review
target: <free-text human label, e.g., "AVASK VAT reclaim">
target_url: <URL audited>
target_route: <pathname, e.g., /reclaim/avask>
target_slug: <kebab-case slug used in the filename>
component_path: <absolute path to the page component>
peer_paths:
  - <absolute path>
  - <absolute path>
generated_at: <ISO 8601 datetime>
brand_identity_path: <path or empty>
severity_summary:
  hard_failure: <N>
  major: <N>
  minor: <N>
---

# Screen Review: <target>

## Violations

<One block per issue, ordered by severity (hard failure → major → minor) and within a severity by impact. V1, V2, … are stable IDs the downstream brief references — never re-number across iterations of the same target. Emit every issue you'd act on; do not cap, do not pad.>

### V1. <short name>
- **Severity:** hard failure | major | minor
- **Rule violated:** <brief/policy reference — e.g., "Brief §4b Pass 2", "Brand identity §8 (hard failures)", "Design standards — density">
- **Observed failure:** <what the mockup/page actually does. `<file:line>` and the current Tailwind class are allowed here as concrete evidence.>
- **Required correction:** <exact replacement or constraint — concrete enough for refine-screen to execute without reinterpreting. May include the target class swap, the structural change, or both.>
- **Do not change:** <optional. Local protection: a nearby good pattern this fix risks touching. Omit the bullet entirely if not applicable.>

### V2. <short name>
...

## Keepers

<Page-wide protections. Things refine-screen must NOT break or rework. Distinct from per-violation "Do not change": these are global, not local.>

- <thing>
- <thing>

## Edge States to Test
<States the design must produce variants for. Pull from real data conditions, not generic "loading/error". Example: "All-action-required country (47 rows, every row needs classification)", "Filed-and-locked country (zero rows in worklist)", "Mixed-currency country (GBP + EUR on same screen)".>

- <state>: <why this needs explicit design treatment>
- <state>: <why this needs explicit design treatment>

## Peer Steals
- From `<peer_path>`: <pattern> — port by <action>
- From `<peer_path>`: <pattern> — port by <action>

## Measurement Evidence
<Raw numbers from step-3 measurement pass. Keep as YAML-ish for parseability.>

```yaml
top_visuals:
  - { tag: H1, text: "...", fontSize: "30px", fontWeight: "600" }
scrollers:
  - { cls: "...", scrollW: 1840, clientW: 1280 }
counts: { cards: 8, sections: 5, table_rows: 32 }
duplicated_data:
  - "Order ID shown in header and context card"
```
```

---

## RULES

- Cite real class names and real file paths. No hand-waving.
- Measurements are evidence — include numbers (px sizes, scrollWidth, cell counts).
- Don't flag dark-mode issues.
- Don't propose new tokens — use what's in the design system.
- Don't implement. This is a design review, not a PR.
- **Artifact-mode rule:** Violations, Edge States, and Peer Steals must all be populated. Emit every violation you'd act on — do not cap, do not pad. Order by severity (hard failure → major → minor) and number V1, V2, … as stable IDs the consumer references. The interactive chat review may still surface the top 3 for the user to skim; the artifact carries the full list and consumers decide how many to act on.
