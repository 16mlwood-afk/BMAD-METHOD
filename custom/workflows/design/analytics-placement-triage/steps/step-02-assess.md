---
name: 'step-02-assess'
description: 'Run the decision brains — band-belongs (§5b), topology (§5d), hierarchy (§5e) — single-sourced and verbatim, with none/recommended-drop short-circuits'
---

# Step 2: Assess via the Decision Brains

**Progress: Step 2 of 4** — Next: Name Shape (autonomous)

## RULES — read before acting

- **SINGLE-SOURCE, DO NOT RE-DERIVE.** This step *applies* reasoning that lives elsewhere; it does not restate or fork it. For each brain, **read the named section on demand and apply it verbatim** to this surface. If your output contradicts the source section, the source wins. (Router invariant — the whole point of this workflow is to assemble, not re-implement.)
- FULLY AUTONOMOUS for decisions. No menus. Do not emit the placement verdict yet — that is step-04.
- Apply each brain to the **analytics surface in question**, not the whole page in the abstract.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## AVAILABLE STATE

From step-01: `{target_route}`, `{target_component}`, `{analytics_question}`, `{analytics_dataset}`, `{existing_band}`.
Pointers to the brains (design-handoff's step-01 gather was split for context budget): `{design_handoff_decide}` holds **§5b** (band-belongs); `{design_handoff_topology}` holds **§5d** (topology) and **§5e** (hierarchy).

## SEQUENCE OF INSTRUCTIONS

### 1. Band-belongs — does an analytics surface belong at all? (§5b)

Read `{design_handoff_decide}` **§5b** and apply its three band-belongs questions (aggregate dimension / pattern job / changes-next-action) to `{analytics_dataset}` + `{analytics_question}`. Honor its `{existing_band}` distinction: a present primitive band resolves toward `inherited`, a bare page toward `recommended-new`.

Set `{band_belongs}` ∈ `inherited | recommended-new | recommended-drop | none`.

**Branch on the outcome — two short-circuits (skip §2–§3 and the whole shape step):**

- `{band_belongs}` = **`none`** (no analytics surface justified): set `{placement_verdict}` = `no-surface`, `{analytics_shape}` = `n/a`. Proceed to step-04 — the honest answer is "no analytics here."
- `{band_belongs}` = **`recommended-drop`** (a band exists but is ornamental and should be removed): set `{placement_verdict}` = `remove-band`, `{analytics_shape}` = `n/a`. This is a real design task (redesign the page WITHOUT the band), NOT a no-op — proceed to step-04, which routes it to a sans-band `design-handoff`. Do **not** conflate it with `no-surface`.
- `{band_belongs}` = **`inherited`** or **`recommended-new`**: a band belongs — continue to §2.

### 2. Topology — is this its own surface? (§5d)

Read `{design_handoff_topology}` **§5d** and apply its surface-topology reasoning to the *analytics surface* specifically: does the analytics constitute a distinct operator job at a different depth than the worklist, or does it ride alongside the rows?

Map §5d's verdict to a placement-relevant `{topology_verdict}`:

| §5d verdict | `{topology_verdict}` | Meaning for analytics placement |
|---|---|---|
| `single-page-appropriate` | `single-page-appropriate` | Analytics rides on the worklist → **band** candidate |
| `needs-tab-views` | `needs-tab-views` | Analytics is a distinct mode of the same data → **tab** candidate |
| `needs-sibling-route` | `needs-sibling-route` | Analytics is its own job/surface → **sibling-page** candidate |
| `needs-detail-route` | *(not an analytics home)* | Per-item depth of the worklist, unrelated to where the analytics band goes — treat as `single-page-appropriate` for THIS question and note it |

If §5d genuinely does not resolve to one home (two co-equal jobs), do NOT pick silently — record `{topology_verdict}` = `unresolved` and carry it to step-04 to surface the fork.

### 3. Hierarchy — rank co-resident surfaces (§5e, conditional)

Only if `{analytics_dataset}` + `{analytics_question}` imply **more than one** distinct analytics surface (a dataset+question pair that earns its own shape): read `{design_handoff_topology}` **§5e** and rank them `hero | supporting | drill`. Store as `{surface_hierarchy}`. Otherwise set `{surface_hierarchy}` = `single`.

### 4. Proceed to Shape

Confirm `{band_belongs}`, `{topology_verdict}`, `{surface_hierarchy}` are set (or a short-circuit fired in §1). Then read fully and follow: `{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage/steps/step-03-shape.md`

---

## SUCCESS METRICS

- Each brain was read from its named source section and applied verbatim — none re-derived inline
- `{band_belongs}`, `{topology_verdict}`, `{surface_hierarchy}` populated (or `none`/`recommended-drop` short-circuit recorded with the right verdict)
- `unresolved` recorded rather than guessed where §5d could not resolve
- `recommended-drop` carried as `remove-band` (a real removal task), NOT silently terminated as `no-surface`

## FAILURE MODES

- Re-stating or paraphrasing §5b/§5d/§5e logic instead of reading and applying the source (router invariant break — causes drift the moment the source changes)
- Emitting a placement verdict here instead of in step-04
- Conflating `recommended-drop` with `none` (drops a real band-removal design task)
- Treating §5d's `needs-detail-route` as an analytics home (it is per-item worklist depth, not an analytics surface)
