---
name: design-review
description: 'Senior product designer audit of a live page in Chrome — hierarchy, information architecture, density. Audit only, no implementation. In artifact mode emits the *initial* `screen-review-*.md` for a target from live pixels. To re-audit an existing screen-review on main (preserving V-ID lineage), use `design-artifact-loop` in `review-only` mode instead.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Design Review Workflow

**Goal:** Audit the frontend design of the page the user has open in Chrome. Review for hierarchy, information architecture, and density — not just a11y or bugs.

**Your Role:** Senior product designer. You compare the page under review against peer detail views in the same repo to set the quality bar. You cite real class names, real file paths, and real measurements. You do NOT implement — this workflow produces a design review document, not a PR.

**When NOT to use this — entry-point routing.** This workflow *creates the first `screen-review-*.md`* for a target by auditing live pixels in Chrome. If a `screen-review-{slug}-*.md` already exists on `main` for this target, prefer `design-artifact-loop` in `review-only` mode — it re-audits the existing artifact, preserves V-ID lineage and verdict history across iterations, and avoids duplicate review files. Quick check before invoking:

```bash
ls _bmad-output/implementation-artifacts/screen-review-{slug}-*.md 2>/dev/null
```

Empty result → run this workflow with `--artifact`. Non-empty → run `design-artifact-loop` review-only instead.

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
- `{policy_version}` — Integer version of `docs/design-policy.md` at review time (parsed from frontmatter `version:` field; `1` if no version field; `0` if no policy file). Stamped into the screen-review artifact's `policy_version_required:` frontmatter in artifact mode so downstream consumers can detect when the policy has moved past the review's pinned version.
- `{output_mode}` — `"interactive"` (default) emits the human-readable review in chat. `"artifact"` additionally writes a structured `screen-review-{slug}-{date}.md` file to `{implementation_artifacts}` that downstream workflows (notably `design-handoff` in refine-screen mode) can consume programmatically.
- `{target_slug}` — kebab-case slug derived from the route (used for the artifact filename and to let design-handoff match the right artifact to the target feature)
- `{artifact_path}` — Absolute path where the artifact is written (only set when `{output_mode}` = "artifact")
- `{review_findings}` — Structured findings object built during audit: `{ violations: [...], edge_states: [...], peer_steals: [...], keepers: [...], measurements: {...} }`. The interactive review and the artifact are both rendered from this single source. `violations` is an ordered list (hard failure → major → minor); no fixed count.

---

## INITIALIZATION

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/design/design-review`
- `design_standards` = `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md` (shared reference — superseded by brand identity on project-specific values)
- `design_policy` = `{project-root}/docs/design-policy.md` (canonical project policy slot)
- `brand_identity_legacy` = `{project-root}/_bmad-output/planning-artifacts/brand-identity.md` (legacy slot; some older projects still use this)

### Project Policy Loading

Check both possible locations, in order. `docs/design-policy.md` is the canonical location; `{planning_artifacts}/brand-identity.md` is the legacy slot. Prefer the first if both exist:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {project-root}/_bmad-output/planning-artifacts/brand-identity.md 2>/dev/null
```

If either is found, read and store as `{brand_identity}` (variable name retained for backward compatibility with downstream templates). Set `{brand_identity_path}` to the absolute path of whichever file was loaded. Parse the file's frontmatter `version:` field into `{policy_version}` (integer, default `1` if no version field). When no policy file is found at all, set `{policy_version}` = `0` (sentinel for "no policy in effect at review time"). This value is stamped into the screen-review artifact's `policy_version_required` field in artifact mode so downstream consumers (refine-screen briefs, design-implement) can detect drift when the policy has moved past the review's pinned version.

The project policy provides project-specific visual standards (exact typography, exact colors, exact component patterns) that are more authoritative than the generic `design-standards.md`. When both exist, the policy wins on specifics — use `design-standards.md` only for categories the policy doesn't cover (functional UX, accessibility, severity levels).

**Load the shared standards file — do not audit from a citation.** Read `{design_standards}` and hold its `## AI Fingerprint Detection` (all six category tables + the composite test), `## Quality Checklist`, and `## Severity Levels` sections in working state for the audit. Citing this file as authority #2 while never opening it is the exact drift that let a taxonomy-listed pattern ship unflagged (2026-08-24) — the audit evaluates against the file's CURRENT tables, not a remembered list. If the file is unreadable, say so in the review output and mark the fingerprint dimension `UNVERIFIED — standards file unreadable`; never substitute a from-memory taxonomy.

**If `{project-root}/docs/design-policy.md` should exist for this project but the bash check returned nothing, STOP and report the path you tried. Silent fallback to "no policy" mode is the loader-drift bug this section exists to prevent — surface it instead of swallowing it.**

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow audits a page or emits a screen-review artifact, the order of authority is:

1. **Project design policy** — `docs/design-policy.md` (canonical) or `planning-artifacts/brand-identity.md` (legacy). Loaded directly above. Hard failures, status rules, layout principles defined here.
2. **Shared BMAD design standards** — `_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails.
3. **The audited page itself.** What the page does is evidence to compare against (1) and (2); the page is never authoritative for what it *should* do.

**Implication for artifact mode:** Every violation block's `Rule violated:` field must cite the policy section directly (e.g., `docs/design-policy.md §5 (Hard Failures): "Emoji as UI icons"`) — not a brief section, and not a peer page. Briefs and peer pages may inform peer-steals or context, but the rule itself originates in the policy. This guarantees downstream consumers (e.g., `design-handoff` in refine-screen mode) can re-resolve each rule against the canonical source.

### Prerequisites (one of three measurement modes)

Step-01 must run in exactly one of the three measurement modes below. The mode is recorded in the artifact's `measurement_method` field so downstream consumers know what to trust.

1. **`chrome-live` (preferred).** Chrome is open with the page under review visible in a tab AND `mcp__claude-in-chrome__*` tools are available (load via ToolSearch if needed). All of step-01 §2 (read page) and §3 (measure) run against the live DOM.
2. **`source-derived` (fallback).** Chrome MCP is unavailable but the auditor has full source-tree access AND at least one screenshot of the rendered page. Measurements in §3 are derived from source (Tailwind classes, source-grep of identifiers, source-counted DOM elements) plus screenshot reading. The artifact MUST carry a non-empty `measurement_caveat` explaining what was NOT measured live (typically: real computed `getComputedStyle`, real `scrollWidth` deltas, real-render counts).
3. **`screenshot-only` (weakest).** No source access AND no live Chrome — only one or more screenshots of the rendered page. Use this only when reviewing an external system, a deployed app the auditor cannot clone, or a designer-supplied mockup. Composition violations (§5 anti-AI layout principles) and visible-class violations are still in scope; precise measurement-evidence and `file:line` citations are not. The `measurement_caveat` must say so explicitly.

**Mode selection is sticky for the whole run.** Do not start in `chrome-live` and degrade silently mid-step. If a tool fails after the run starts, halt, downgrade the mode, re-record `measurement_method`, and write the appropriate caveat into `measurement_caveat`.

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
policy_version_required: <int — version of docs/design-policy.md this screen-review was authored against. Downstream (design-handoff in refine-screen mode, design-implement) MUST halt or warn if the current policy version exceeds this value, since rules ratified after this review may have re-classified violations. Default `0` if no policy exists.>
measurement_method: <chrome-live | source-derived | screenshot-only>   # see step-01 §3
measurement_caveat: |                                                  # REQUIRED when measurement_method != chrome-live; empty/null otherwise
  <one-paragraph statement of what was NOT measured live and why downstream
   consumers should treat the artifact accordingly.>
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

## Anti-AI Checklist

<Three binary checks the page must pass on top of the violation list. Each is checked iff the reviewer can defend the "yes" with a one-line rationale on the same line. Boxes are filled in by the audit (not left blank for a human). If any item fails, it MUST also appear as a violation above — the checklist is a summary, not a parallel track. Wording is fixed across projects so the screen-review contract stays comparable.>

- [ ] **1. No generic card row layout.** The page does not lean on a row of identical (or near-identical) cards as its primary structure. Rationale: <one line — e.g., "page is table-first with a single inline summary line; no card row anywhere">.
- [ ] **2. Domain-authored hierarchy.** Order, grouping, and visual weight of major regions are driven by domain logic (risk, urgency, lifecycle, workflow state), not template defaults or alphabetical sorting. Rationale: <one line — name the domain logic, e.g., "countries ordered by VAT-at-stake descending; in-row weight pulls eye to overdue action items">.
- [ ] **3. Recognizably this product.** A user familiar with the rest of this product would recognize the page as belonging here, not as "any AI-generated admin UI". Rationale: <one line — name what makes it specific, e.g., "slate-navy accent + 13px dense rows + monospace IDs match `/avask` and `/queries` exactly">.

**Failure → violation rule:** If a check is `[ ]` (failed), there must be a matching block in `## Violations` above with severity `hard failure`. The checklist alone is not a punishment; it is a final cross-check that the violation list captured the AI-default failure modes the policy bans.
```

---

## RULES

- Cite real class names and real file paths. No hand-waving.
- Measurements are evidence — include numbers (px sizes, scrollWidth, cell counts).
- Don't flag dark-mode issues.
- Don't propose new tokens — use what's in the design system.
- Don't implement. This is a design review, not a PR.
- **Artifact-mode rule:** Violations, Edge States, and Peer Steals must all be populated. Emit every violation you'd act on — do not cap, do not pad. Order by severity (hard failure → major → minor) and number V1, V2, … as stable IDs the consumer references. The interactive chat review may still surface the top 3 for the user to skim; the artifact carries the full list and consumers decide how many to act on.
