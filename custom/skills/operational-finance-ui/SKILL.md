---
name: operational-finance-ui
description: Design and refine dense, high-stakes operational finance screens (VAT, registrations, reconciliations, filings) in the Bison product. Use when designing a new operational finance screen, refining an existing one against a screen-review artifact, lifting a screen to match updated design policy, or producing a review-only diagnostic. Locks an explicit invocation mode (new-screen, refine-screen, policy-lift, review-only) and respects the BMAD design-review → design-handoff → implementation chain. Do NOT use for full BI/executive dashboards, marketing/landing surfaces, copy-only edits, schema/backend work, or pages without an operational finance surface.
metadata:
  short-description: Design ops-finance screens within BMAD chain
provenance:
  id: operational-finance-ui
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://github.com/bmad-code-org/BMAD-METHOD  # upstream BMAD-METHOD project; source of the design-review -> design-handoff -> implementation chain this skill locks into
    - https://deepwiki.com/bmad-code-org/BMAD-METHOD/12.2-review-and-quality-skills  # upstream's generic review/quality skill pattern (micro-file skill: persona, inputs, mandatory execution steps) this skill specializes
  origin_type: adapted
  exemption_reason: ""
  predecessor_id:
  superseded_by:
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. Core design-review/design-handoff chain and mode-locked review-skill pattern trace to upstream BMAD-METHOD's UX/review workflow; this skill materially reworks it for this fork's operational finance screens (VAT/registrations/reconciliations) with a fork-specific trust hierarchy and invocation-mode contract, so no direct external analog covers the specific job."
---

## External research checked
- Date: 2026-07-24 · Queries: "AI design skill financial dashboard UI review tool operational finance screens" · "Claude Code skill design review financial UI GitHub open source" · "BMAD-METHOD bmad-code-org design-review design-handoff workflow finance UI skill"
- Sources: <https://github.com/bmad-code-org/BMAD-METHOD> · <https://deepwiki.com/bmad-code-org/BMAD-METHOD/12.2-review-and-quality-skills> · <https://github.com/bitjaru/styleseed>
- Verdict: ADAPTED — no external tool does mode-locked, finance-domain-specific screen design/review tied to this fork's design-policy trust hierarchy; the closest generic analogs are upstream BMAD-METHOD's design-review/design-handoff chain (which this skill explicitly chains into) and general Claude Code design-judgment engines like StyleSeed, neither of which is finance-specific or fork-policy-aware.

# Operational Finance UI

This skill guides design and refinement of the dense, high-stakes operational finance screens in this product (VAT reclaims, registrations, reconciliations, filings, query review). It defines how an agent should interpret use cases, respect BMAD workflows, and apply design rules without overstepping into IA redesign.

## Trust hierarchy

When sources of guidance conflict, resolve in this order:

1. **`tailwind.config.ts`** — live tokens win for typography, color, spacing, radii.
2. **`docs/design-policy.md`** — project visual policy (page modes, hard failures, control rules, table rules, status hierarchy).
3. **Existing screen-review artifact** for the target screen, if one exists in `_bmad/` or `.claude/worktrees/...`.
4. **Shared BMAD design standards** (`_bmad/bmm/workflows/design/shared/design-standards.md`) — universal anti-fingerprint rules. They apply on top of the policy, but never override it.

`design-policy-canonical` is the formal interpreter of `docs/design-policy.md` for page mode, color hierarchy, and component decisions; `operational-analytics-band` is the formal interpreter for the analytics row on operational/hybrid pages. Invoke them within their scopes rather than restating their rules — duplicated rules drift from the single source of truth.

Cite sections by number when explaining a decision. Never infer design from the current shipped UI — treat any live page as possible drift.

## 1. Invocation modes

Every run must declare and lock exactly one mode at the top. If the user has not stated one, ask before proceeding.

- **new-screen** — design a net-new screen.
  - Inputs: use-case brief, route/slug, relevant policy sections.
  - Outputs: design-handoff brief + initial screen-review artifact.
- **refine-screen** — bounded refinement of an existing screen.
  - Inputs: screenshot of shipped state, existing screen-review artifact if present, relevant policy sections.
  - Constraints: fix only top N issues and named edge states; do not redesign IA; introduce a new component only when a top screen-review issue requires it, and only at component-level granularity (not a wholesale swap of a major component — see §5).
- **policy-lift** — raise an existing screen to match new or updated policy.
  - Inputs: screenshot, screen-review artifact, diff between old and new policy sections.
  - Behaviour: change only what is required by the policy delta.
- **review-only** — produce a diagnostic artifact, no design proposals.
  - Inputs: screenshot and policies.
  - Outputs: screen-review artifact only.

The mode locks for the entire run. A request that drifts outside the locked mode (e.g. an IA change inside `refine-screen`) requires a clarifying question, not silent expansion. If the user authorises scope expansion mid-run, terminate the current invocation, restate the context block under the new mode, and start a new run. Mode never silently morphs.

## 2. Required context per run

Before doing any design work, restate the following at the top of the working brief. Do not skip — missing context means missing decisions later.

- **Use case**
  - Who uses the screen (role, e.g. "Mason, owner-operator").
  - Frequency (e.g. "quarterly, days 4–8 of the filing month").
  - Stakes (e.g. "£233k reclaimable this quarter").
- **Screen identity**
  - Route/slug (e.g. `/reclaim/avask`, `/vat/registrations`).
  - Component path (e.g. `src/routes/reclaim/avask/+page.svelte`).
- **Mode** — `new-screen`, `refine-screen`, `policy-lift`, or `review-only`.
- **Artifacts present**
  - Existing screen-review artifact? path?
  - Existing design-handoff brief? path?
  - Which `docs/design-policy.md` sections apply (tables, dropdowns, anti-AI, status, analytics)?

## 3. Workflow integration (BMAD)

Respect this chain — do not bypass steps:

1. **`design-review --artifact`** produces a screen-review artifact describing issues and edge states, sourced from screenshot + policy.
2. **`design-handoff`** consumes screen-review + policy + use case and produces either a refinement brief (refine-screen / policy-lift) or a full handoff spec (new-screen).
3. **Implementation** updates `src/routes/...` from the handoff.

This skill's responsibilities inside that chain:

- If in `refine-screen` or `policy-lift` mode and no screen-review artifact exists, **synthesize one** from screenshot + policy first — but only describe visible, provable issues. Do not skip the artifact step.
- Write outputs where BMAD expects them: `.claude/worktrees/<branch>/_bmad/...` or the canonical `_bmad-output/implementation-artifacts/` location, matching the conventions already in this repo.

## 4. Screen-review artifact contract

When synthesizing or extending a screen-review artifact:

- **Anchor every issue in visible evidence** — quote what the screenshot shows ("row actions hidden behind a meatball dropdown", "trend strip reads as three identical mini-cards").
- **Classify issues under agreed sections** — status hierarchy, tables, controls, analytics band, anti-default layouts, edge states.
- **Limit the primary issue list** (top 3 is the default ceiling) and list edge states separately.
- **No speculation** — do not assert facts about invisible flows, data models, routes, or behaviour not present in the screenshot.

## 5. Refinement rules (refine-screen mode)

**Definitions for this section:**

- **IA** = navigation, route hierarchy, page-to-page flow, the conceptual model of how content is divided across screens. Visual hierarchy (which element draws the eye, density, control prominence within a page) is **not** IA.
- **Major component** = the primary work surface (table/worklist), the primary action area, the main filter row. A swap is "major" if it changes what data or actions the area exposes.

**May do:**

- Adjust visual hierarchy, spacing, control choice, status presentation, and table structure **within the existing IA**.
- Introduce a new component only when a top screen-review issue requires it, and only at component-level granularity (e.g. swap a meatball dropdown for segmented controls when the filter is frequent) — never a wholesale swap of a major component.
- Tweak the analytics band per `operational-analytics-band` rules — e.g. collapse mini-cards into a single shared band.

**Must not:**

- Change navigation structure or route-level IA.
- Introduce new feature flows.
- Replace major components wholesale unless the brief explicitly authorises it.

Every change must trace back to either an issue in the screen-review artifact or a specific design-policy clause. If a proposed change cannot cite one, drop it.

## 6. Domain rules

This skill defers to two more specific skills where they apply — invoke or consult them rather than duplicating their rules:

- **`design-policy-canonical`** — page mode declaration, color hierarchy, component selection, hard failures.
- **`operational-analytics-band`** — the supporting analytics row on operational/hybrid pages.

Beyond those, the domain heuristics this skill genuinely owns for operational finance screens in this product:

- **Work surface first.** The table/worklist is the primary surface. Everything else (filters, analytics, status summary) is subordinate. Above-the-fold space stays majority table (~60–70% vertical, per policy §2 *Analytics visual weight*).
- **Control rules.**
  - Frequent filters used most sessions → exposed controls (segmented switch, chip row, inline search).
  - Occasional filters → compact picklist, ideally typeahead.
  - Rare or destructive actions → dropdown or kebab menu — never the primary path.
- **Table rules.**
  - Right-align numeric and currency columns; left-align text; status pill column has fixed narrow width.
  - Sticky header on any table that can scroll past one viewport.
  - Row actions live in the row, not in a global header — at most one inline primary action and a quiet overflow.
- **Analytics band** → see `operational-analytics-band` (do not restate its rules here).
- **Status and risk hierarchy / color** → see `design-policy-canonical` §3 *Color hierarchy* (do not restate its rules here).

## 7. Output artifacts

For each run, produce:

- **Updated or new screen-review artifact** — required in `review-only`, and in `refine-screen`/`policy-lift` when none exists.
- **Design-handoff brief** — required in `new-screen`, `refine-screen`, and `policy-lift`. The brief states:
  - locked mode,
  - use case (role, frequency, stakes),
  - top issues addressed (with screen-review references),
  - planned changes with rationale and policy section references,
  - edge states to cover.
- **Optional inline implementation notes** — column changes, control swaps, specific CSS or token references — only when the change is small enough to ship without a separate spec.

## 8. Safety rails

When in doubt, ask a clarifying question rather than expand scope.

- **IA changes and new flows are out-of-mode for `refine-screen` and `policy-lift`.** They are not authorisable mid-run — surface the conflict, then per §1 terminate and restart under `new-screen` if the user wants them.
- **Conflicts between user commentary and the artifacts win for the artifacts.** When user commentary conflicts with the screen-review artifact or `docs/design-policy.md`, the artifact and policy win unless the user explicitly overrides them with a citation or correction to those documents.

## Refusals (and what to offer instead)

When this skill is active, refuse the following and propose the alternative.

1. **Refusal:** Silently expanding from `refine-screen` into IA changes ("while we're at it, let's restructure the nav").
   **Why:** Section 1 — mode locks for the run; Section 5 — IA changes are out of scope for refine.
   **Counter-offer:** Ship the bounded refinement; raise the IA concern as a separate `new-screen` or design-review follow-up.

2. **Refusal:** Designing without restating use case, mode, and policy references.
   **Why:** Section 2 — context is a prerequisite; without it, decisions cannot be justified or audited.
   **Counter-offer:** Pause, restate the context block, then proceed.

3. **Refusal:** Treating the current shipped UI as a source of truth ("the existing page does X, so we should match it").
   **Why:** Policy §8 *Precedence* and the trust hierarchy above — the policy wins over drift.
   **Counter-offer:** Cite the policy section, propose changing the UI to match.

4. **Refusal:** Replacing a major component (table, primary filter, main action area) wholesale during refinement without explicit authorisation.
   **Why:** Section 5 — refinement is bounded to within-IA changes.
   **Counter-offer:** Propose the swap as a `new-screen` or design-handoff item with rationale; ship the smaller fix now.

5. **Refusal:** Producing a design-handoff brief without an underlying screen-review artifact in `refine-screen` or `policy-lift` mode.
   **Why:** Section 3 — the BMAD chain requires the artifact step.
   **Counter-offer:** Synthesize the artifact first from the screenshot and policy, then build the brief on top.
