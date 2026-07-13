---
name: operational-cockpit
description: Design, audit, or refine an operational COCKPIT — a decide-one-at-a-time operator surface whose job is to make one consequential decision fully, visibly, and continuously on one screen (a grading bench, a claim-filing station, an approval queue, a per-unit review/pricing/publish gate, a mapping/triage queue). Use when composing or auditing a per-item decision surface, when deciding whether a surface should be a cockpit vs a scan-many worklist, or when the user says "is this a cockpit", "should this be a cockpit", "this decision surface feels wrong/slow", or "the operator is clicking too much / working blind". Applies the mandatory floor (classify-first, queue+workspace co-present, per-item momentum, keyboard-first, consequence-visibility before an irreversible commit, no working blind) over a heuristic layer (confidence-scaling, geometry, one-viewport, reversibility calibration). Do NOT use for scan-many operational worklists/tables (that is `design-policy-canonical`, §F operational mode), analytics/BI surfaces (`operational-analytics-band` / `analytics-surface-architect`), pure visual treatment / tokens / status colors (the project design policy), or backend/schema/data work.
metadata:
  short-description: Design/audit decide-one operator decision cockpits
---

# Operational Cockpit

> **A cockpit is not defined by having a queue and a form; it is defined by making one consequential decision fully, visibly, and continuously on one screen.**

This skill governs **one surface archetype**: the *operational cockpit* — a surface where the operator's unit of work is a single per-item decision (grade this unit, file this claim, approve this offer, price/publish this listing, map this record), opened one at a time, decided, committed, and left behind. It is the decide-**one** counterpart to the scan-**many** operational worklist that `design-policy-canonical` (§F) governs.

The archetype is a source-agnostic promotion of the "operational cockpit" sub-pattern first written for one Bison surface; it is domain-neutral and applies to any product with expert operators clearing per-item decisions. The rules below are grounded in a real audit of six cockpit-shaped surfaces — one was a genuine cockpit, five drifted in repeatable ways; the mandatory floor is the fix for those drift modes.

## Trust hierarchy

When sources conflict, resolve in this order:

1. **The project design policy (`docs/design-policy.md`) and the family overlay (`_bmad/bmad-shared/bison-product-family-policy.md`) own VISUAL treatment** — status pills, tokens, density, color hierarchy, typography, drawer/pill/filter grammar. This skill never restyles; it cites those files and defers. Cockpit surfaces still obey every hard-failure and status rule there.
2. **This skill owns cockpit STRUCTURE and INTERACTION doctrine** — the queue↔workspace composition and the interaction spine (momentum, keyboard, consequence-visibility, no-working-blind). Those rules are not yet in any project policy, so **this skill is their source** until a project overrides one explicitly in its own `docs/design-policy.md` (project policy wins — record the divergence there).
3. **The live UI is not a source of truth.** Treat any shipped decision surface as possible drift. Where the shipped surface conflicts with this doctrine, recommend changing the surface — not relaxing the rule.
4. **Compose with the sibling interpreters, don't restate them.** `design-policy-canonical` for page mode and visual decisions; `operational-analytics-band` for any evidence band *inside* the workspace; `operational-finance-ui` when the decision is a finance decision (money must still be basis-complete per overlay §K). Invoke each within its scope.

## When to invoke (plain language)

- **Use it** when you are designing, auditing, or refining a surface where the operator opens one record, weighs its evidence, and commits one outcome — a grading/receiving bench, a claim-filing or approval queue, a per-unit review/pricing/publish gate, a mapping or triage queue. Also use it to answer "is this a cockpit / should this be one?" and to diagnose "the operator is clicking too much / working blind / this feels slow."
- **Don't use it** for a scan-many worklist or data table (→ `design-policy-canonical` §F), an analytics band or BI surface (→ `operational-analytics-band` / `analytics-surface-architect`), pure visual treatment/tokens (→ the project design policy), or backend/schema work.
- **If uncertain**, run the classification gate (§0) first — decide-one earns the cockpit, scan-many does not. That single question resolves most of the ambiguity.

## 0. Classify first — the entry gate (M1)

Before any layout decision, state the unit of work in one line: **decide-one** or **scan-many**.

- **scan-many** (the operator scans a wide list, filters, and acts on rows in bulk or in passing) → **STOP. This is not a cockpit.** Route to `design-policy-canonical` §F operational mode. Do not apply the rest of this skill.
- **decide-one** (the operator opens one record, weighs its evidence, and commits one outcome) → this surface earns the cockpit; continue.

The most common failure in the wild is decide-one work silently inheriting the family's **table-first §F default** — a wide table with the decision cramped into a side drawer. The classification gate exists to catch that before it ships. A `/[unitId]` full-page form with no queue is the opposite failure of the same missed classification (see anti-patterns 1 and 2).

## The mandatory floor (M1–M6)

A cockpit that violates any of these fails design review. Each is stated with its rule and its review check.

### M1 — Classify first
The surface has been explicitly classified decide-one, and does **not** use a table-first + drawer-as-workspace composition. *(Gate above.)*
**Check:** the primary work surface is the decision workspace, not a wide multi-column table.

### M2 — Queue and workspace are co-present on one screen
A triage/navigation rail (**navigation only — no per-row decision controls, no checkboxes, no inline commit buttons**) beside a **dominant** decision workspace that holds the full evidence for the one decision. A per-item page with no queue rail and no path in is not a cockpit. Geometry is flexible (H2); co-presence is not.
**Check:** can the operator see the queue and the current decision context at the same time, and reach the workspace and the *next* item without leaving the surface?

### M3 — Per-item momentum
After a commit, the surface **auto-advances to the next actionable item** (skipping claimed/read-only), with an **undo/toast safety window**. Continuous motion — never commit → return to list → re-hunt → click.
**Check:** does a commit advance to the next item automatically, and can the last commit be undone within a short window?

### M4 — Keyboard-first for every commit
**Every** per-item action is reachable and committable from the keyboard, with a **persistent shortcut affordance**. Keyboard support at only one control (e.g. a scan field) while every surrounding commit is mouse-only does not satisfy this.
**Check:** can the operator complete a full decide→commit→advance loop without touching the mouse, and is the shortcut set visible?

### M5 — Consequence-visibility before an irreversible commit
Before an irreversible write, the operator **SEES the resulting record/figure that will be persisted** — rendered and basis-labelled — not a prose sentence describing it. Reversible commits may relax to a live recomputed preview (H4).
**Check:** for the irreversible action, is the exact record/figure that will be written shown on screen before commit — or only described in words?

### M6 — No working blind
The workspace **surfaces the evidence its own decision requires.** If the job is "verify claim against evidence," the evidence must be wired and on-screen. A workspace that hosts a commit button but not the evidence for the decision has failed its core purpose — it is a form, not a cockpit.
**Check:** is every input the decision depends on present and populated on the surface? (Mandatory in review; judgment-based in application — this rule is deliberately not machine-checkable on day one. "Hard to lint" is not "optional".)

## The heuristic layer (H1–H5)

Strong "should"s — apply with judgment, calibrated to the surface. Not a review-failing floor.

- **H1 — Confidence-scaled effort.** The confident/unambiguous case gets a one-action fast path; the ambiguous case (detectors disagree, evidence thin) forces the full decision. Avoid uniform max-effort *and* avoid rubber-stamps. Hard to make binary — kept heuristic.
- **H2 — Geometry is flexible.** A left queue rail is typical, but not mandatory. A scan-driven intake variant may put concurrent **sessions** in a right-hand rail with the scan hero as the workspace — legitimate. *Separation* is mandatory (M2); *placement* is not.
- **H3 — One-viewport workspace.** The workspace should hold the decision in a single viewport; a long vertical scroll that pushes the decision's own evidence off-screen is a smell. Some decisions legitimately need scroll — heuristic, not fail.
- **H4 — Reversibility calibrates M5.** A reversible commit (append-only, re-settable) is satisfied by a live recomputed preview. An irreversible commit (goes live externally, cannot be undone) demands the full rendered resulting record. Match strictness to blast radius.
- **H5 — Inert-control checks live in the enforcement/wire-check lane, not doctrine prose.** A primary or throughput control that is a no-op (a Route/Approve/File button that only sets local state or has no handler) is a recurring shipped defect — but it is a `design-review-pr` grep + wire-check concern, surfaced there, not a design rule to reason about here.

## Cockpit IA rules (mandatory)

Two archetype-specific rules the cockpit carries **directly** — preserved from the origin policy §6. They are **not** in the extracted family overlay or the project residue, so this skill is their only home; do not assume a project policy backs them.

- **Truthful labels.** Every action / next-step / destination label matches the real destination and the actual operator action — never a label driven by a simplified branch when routing is driven by a richer contract. A control that opens Blocked stock must not read "Staged review"; one that opens Listings must not read "Mapping queue". Labels ↔ routing derive from one source of truth.
- **Waiting is not actionable.** A state that requires no operator action now — an external or system process already in progress — belongs in a waiting / informational lane, never an actionable review bucket. Do not surface a no-op as a task.

## Refusals (and what to offer instead)

When this skill is active, refuse these drift modes and propose the alternative each time. Ordered by how often they occur in the wild.

1. **Refusal:** A wide multi-column table with the per-item decision in a side drawer, as the main way to work a decide-one job. *(the "table+drawer trap")*
   **Why:** M1/M2 — for a decide-one unit of work the table dominates and the evidence is cramped into a thin pane; the surface inherited the §F table-first default it should have been classified out of.
   **Counter-offer:** A triage rail (navigation only) beside a dominant decision workspace on one screen. Move the per-row checkboxes/commit buttons out of the table into the workspace.

2. **Refusal:** A `/[unitId]` full-page decision form with no queue rail and no path in (reachable only by direct URL, no advance to next). *(the "stranded form")*
   **Why:** M2/M3 — a workspace with no queue is a form; the operator has no way in and no momentum out.
   **Counter-offer:** Give it a queue rail and an advance-to-next commit loop. The center panel may already be cockpit-grade — wrap it in the spine.

3. **Refusal:** Commit → close/revalidate the same item → return the operator to the list to re-pick the next one.
   **Why:** M3 — commit→hunt→click is the exact motion the archetype exists to eliminate.
   **Counter-offer:** Auto-advance to the next actionable item with an undo/toast window.

4. **Refusal:** Mouse/tap-only commits with no shortcut affordance (even if one control, like a scan field, is keyboard-driven).
   **Why:** M4 — a click-only cockpit fails the speed job it exists for.
   **Counter-offer:** Bind every per-item action to the keyboard and show the shortcut set persistently.

5. **Refusal:** A footer sentence describing what an irreversible commit will write, in place of showing the resulting record/figure.
   **Why:** M5 — prose is weaker than sight for an irreversible write; the operator commits without seeing the actual write.
   **Counter-offer:** Render the resulting record (fields, references, basis-labelled figures) as a preview before commit.

6. **Refusal:** A decision workspace that hosts the commit control but not the evidence the decision needs (unwired/empty evidence panes, signals scrolled off-screen).
   **Why:** M6 — the operator is asked to commit blind; the cockpit has failed to assemble the decision.
   **Counter-offer:** Wire and surface every input the decision depends on before the commit control is reachable.

## Positive exemplars

Two shapes that satisfy the floor — cite them when designing:

- **Scan-driven intake bench (interaction spine).** A scanner-first hero that auto-refocuses so "the gun stays pointed" for the next scan; a persistent expected-vs-actual baseline as the cross-check; a per-scan consequence-preview banner ("captured X — now scan its Y") *before* the bind persists; concurrent sessions in a quiet subordinate rail; tools in read-only drawers. The reference for M2 geometry (H2), M4 (at the scan step), and M5. *Gap even here: extend keyboard-first past the scan field, and add a post-commit undo window.*
- **Per-unit consequence-preview panel (evidence pattern).** A price/figure entry whose derived result (e.g. net-after-fees) **recomputes live** from the working input before commit; advisory aids (comps, distribution) explicitly subordinate to the decision and labelled "never writes your value"; unset is first-class (distinct from zero); no invented numbers. The reference for M5 on a reversible commit (H4). *Gap even here: it is a stranded form — wrap it in a queue + advance loop (M2/M3).*

## Review test (apply M1–M6)

Take any decide-one surface and confirm, in order: (1) it is classified decide-one and is not a table+drawer; (2) queue and workspace are co-present, the rail is navigation-only, the workspace is dominant; (3) a commit auto-advances to the next actionable item with an undo window; (4) the full loop is committable from the keyboard with a visible shortcut set; (5) an irreversible commit shows the resulting record before writing; (6) the workspace surfaces all the evidence the decision requires. If any of the six fails, it is not on-doctrine — name the failed rule and route the fix.

## Examples

**Good fit for this skill**
Auditing or composing a grading bench, a claim-filing station, an approval queue, a per-unit review/pricing/publish gate, or a mapping/triage queue — any surface where the operator opens one record, weighs evidence, and commits one outcome.

**Out of scope**
A scan-many operational worklist or data-heavy table (→ `design-policy-canonical` §F). An analytics band or a BI/reporting surface (→ `operational-analytics-band` / `analytics-surface-architect`). Pure visual treatment, tokens, or status colors (→ the project design policy). Backend, schema, or data wiring with no decision-surface composition question. Do not stretch the cockpit archetype over a surface whose real unit of work is scan-many — that misclassification is the first thing this skill exists to prevent.
