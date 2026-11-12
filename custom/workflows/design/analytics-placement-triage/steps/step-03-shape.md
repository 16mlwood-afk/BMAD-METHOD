---
name: 'step-03-shape'
description: 'Name the analytics archetype via the analytics-surface-architect skill, with the page-mode derived from the topology verdict'
---

# Step 3: Name the Shape

**Progress: Step 3 of 4** — Next: Route (autonomous)

## RULES — read before acting

- **DELEGATE THE SHAPE — do not hand-reason it.** Shape selection is owned by the `analytics-surface-architect` skill; this step invokes it and captures its decision. (Router invariant — defer by name.)
- **SKIP this step entirely** when a short-circuit already fired in step-02: if `{placement_verdict}` is `no-surface` or `remove-band`, `{analytics_shape}` is already `n/a` — proceed straight to step-04. There is no surface to shape.
- FULLY AUTONOMOUS for decisions. No menus.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## AVAILABLE STATE

From step-02: `{band_belongs}` (here always `inherited`/`recommended-new`), `{topology_verdict}`, `{surface_hierarchy}`, plus step-01's `{analytics_dataset}`, `{analytics_question}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Derive the page-mode for the shape call

The archetype must be selected under the page-mode of the *home it will land in*, not a hardcoded default. Derive it from `{topology_verdict}` (already decided in step-02, so the input is never stale):

| `{topology_verdict}` | page-mode passed to the skill |
|---|---|
| `single-page-appropriate` (band) | `operational` (rides the worklist) |
| `needs-tab-views` (tab) | `operational` (a mode of the same operational data) |
| `needs-sibling-route` (sibling-page) | `analytical` (the sibling becomes a `page_mode: analytical` surface) |
| `unresolved` | `operational` (conservative; re-confirm downstream if it resolves to a sibling) |

### 2. Invoke the shape skill

For each surface that belongs, invoke the **`analytics-surface-architect`** skill (mode: `select`), passing `{analytics_dataset}`, `{analytics_question}` (the user's words), and the page-mode derived in §1. Capture its archetype into `{analytics_shape}`. On a multi-surface page (`{surface_hierarchy}` ≠ `single`), run it once per surface.

**Fallback / honesty:** if the skill is not synced, fall back to `shared/analytics-archetypes.md` inline (same rule). If it returns `unclear`, carry that to step-04 rather than guessing a shape — an asked shape beats a guessed one.

### 3. Proceed to Route

Confirm `{analytics_shape}` is set (or `unclear` recorded). Then read fully and follow: `{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage/steps/step-04-route.md`

---

## SUCCESS METRICS

- Skipped cleanly when `{placement_verdict}` was already `no-surface`/`remove-band`
- Page-mode passed to the skill was derived from `{topology_verdict}`, not hardcoded
- `{analytics_shape}` populated by the skill (or `unclear` carried forward, not guessed)

## FAILURE MODES

- Hand-reasoning the archetype instead of invoking the skill (router invariant break)
- Passing `operational` page-mode when the home is a sibling analytical page (stale input — derive from topology)
- Guessing a shape the skill returned `unclear` on
