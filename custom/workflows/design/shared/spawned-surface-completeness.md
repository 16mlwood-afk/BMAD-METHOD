# Spawned-Surface Completeness Gate — STD-SURFACECOMPLETE-001

Producer-side completeness gate for `design-handoff`. Referenced by `design-handoff` step-01c-topology §5h (which runs it) and named by step-04 as the upstream twin of its internal-consistency assertion. Read on demand; the load-bearing rule is re-stated at point-of-use in §5h.

## Why this file exists

`design-handoff`'s whole value rides on the brief being **complete** — every secondary surface the page spawns at runtime (the drilled detail drawer, each §13 expand-in-context lookup drawer, each live-process state variant) enumerated as a required frame in §7 Surface Inventory. The downstream pipeline is **non-interpretive by design**: `design-synthesize` / Claude Design draws only the frames §7 lists, and `design-implement` pixel-matches only the frames the bundle contains. So a spawned surface the brief never enumerated is never drawn — it is then *inferred* by `design-implement`, which is exactly how a drilled drawer ships thin (bare `€60` with no GBP/VAT basis; a lookup drawer showing only code/type/status). "If you want it built well, it must be drawn" (workflow.md Deliverable-Completeness Principle).

Before this gate, completeness was checked in only two places, and both are too weak:

- **At the producer, probabilistically** — step-01c §5f *derives* `{spawned_surfaces}` and the step-03 §3 self-review *self-attests* the §7 list. The model can silently under-read the edge map (miss a foreign record that IS in the map) or under-derive §5f (capture the linked record but emit no frame for it). Nothing bites.
- **Downstream, deterministically but conditionally** — `design-synthesize` Gate 1f and `design-implement` step-03 §2f *do* hard-fail an undrawn frame, but only against the frames the brief already promised, and **only if those consumers run**. As step-04's assertion comment concedes, that gate "never bites if those consumers don't run." A brief that under-enumerated frames sails past.

This gate moves the completeness check to the **cheapest place** — the producer, before the brief is written — and derives the *expected* frame set from the app's own sources instead of trusting the model to have derived it. It is **additive**: it does not replace step-04's Block-B `frames` internal-consistency assertion (that checks the list is well-formed *after* the brief is written; this checks the list is *complete before it is written*). Both run.

## One derivation basis — the same as relational-coherence-audit

The expected required-frame set is derived from **one** source, identical to the basis `relational-coherence-audit` walks, so producer and auditor reason from the same contract:

1. **Drizzle schema FKs** — auto-derived. An FK from this surface's primary entity to a foreign entity is an edge that COULD require a §13 link.
2. **The declared edge map** — `{project-root}/docs/relational-coherence/relational-edges.yaml` (`edges:` for foreign-record relationships the schema can't see — a derived correlation, a join through a link table, a status fold; `co_views:` for same-record sibling partitions). Hand-maintained source of truth; a derived edge with no entry cannot be expected — route "declare it," never invent it.

step-01c §3a already **reads this map** to seed `{linked_records_inventory}`. This gate re-uses that read and additionally asserts nothing was dropped between the map/FKs and `{spawned_surfaces}`. It **derives no relationship of its own**: an on-surface relationship absent from both FKs and the map is routed back to the audit ("declare a derived edge / co-view") exactly as `relational-coherence-audit` requires — no-guessed-edges holds on the producer side too.

## The expected required-frame set

Build `{expected_required_frames}` from the derivation basis, honoring the short-circuits FIRST:

- **Faithful-mirror short-circuit (check first).** If `{suppress_expand_in_context}` is `true` (the §5a `source-mirror` archetype), the expected set is **frame #1 only**. Do NOT expect a detail drawer or any lookup frames — the §3a identifiers are verbatim source columns, not §13 drawers. A source mirror is never failed for missing drawer frames.
- **True-leaf short-circuit.** A surface with no drill and no linked records has `{spawned_surfaces}` = frame #1 (or empty). Expect frame #1 only.

Otherwise:

| # | Expected required frame | Required when | Source |
|---|---|---|---|
| E1 | **Primary surface** (frame #1) | always | the route itself |
| E2 | **Drilled detail drawer** | `{page_mode}` ∈ {operational, analytical} AND the surface drills into a per-record view (§5f rule 2). For `{page_mode}: detail`, frame #1 IS the record view — no separate E2. | §5a composition |
| E3 | **One lookup drawer per DISPLAYED foreign record** | for every FK / edge-map edge whose `from` = this surface AND whose foreign record the surface **displays** | FKs + `relational-edges.yaml` |
| E4 | **One state-variant frame per operator-distinct lifecycle state** | `{is_live_process_surface}` is `true` (§3c) — one per state that changes what the operator sees or can do | `{runtime_behavior_contract}` |

## The rule — hard-fail required, soft-warn optional

Every FK / edge-map edge from this surface must be **explicitly classified** — none may be silently absent (the anti-silent-drop core, the same discipline as `{dropped_capabilities}`):

1. **Required frame missing → HARD HALT.** If any frame in `{expected_required_frames}` has no matching entry (by `frame_name`) in `{spawned_surfaces}`, collect it into `{completeness_gap_required}` and **halt before step-02/03/04** with the diagnostic below. This is the gate's teeth: a required deliverable frame cannot be missing from the inventory.

2. **Displayed-but-undeclared edge → HARD HALT (as a required gap).** If the surface displays a foreign record for which no FK and no `relational-edges.yaml` entry exists, the relationship is real but the map is incomplete. Halt and route "declare a derived edge / co-view in `docs/relational-coherence/relational-edges.yaml`, then re-run" — do NOT invent the edge into the brief (no-guessed-edges).

3. **Edge whose foreign record is NOT displayed → SOFT, rationale required.** An FK / edge-map edge from this surface whose foreign record the surface deliberately does not display is the `relational-coherence-audit` **OUT-OF-SCOPE CANDIDATE** class — named, not failed. It needs **no frame**, but it must carry a one-line rationale in `{surface_completeness_notes}` (`edge · why-not-displayed`). Warn and proceed; never halt. An out-of-scope edge with no rationale is a soft finding to record, not a blocker.

4. **Verdict.** Set `{surface_completeness_verdict}`:
   - `complete` — every required frame present, no out-of-scope edges.
   - `complete-with-noted-exceptions` — every required frame present; ≥1 out-of-scope edge logged with rationale.
   - (No passing "incomplete" state exists — rule 1/2 halt instead.)

## Graceful degradation — do not become a false-positive halt

The gate is only as authoritative as its derivation basis. When the basis is thin, it **degrades to the existing probabilistic check with a warning — it does NOT hard-fail spuriously**:

- **No `docs/relational-coherence/relational-edges.yaml`** → derive the expected set from **Drizzle FKs only**; note in `{surface_completeness_notes}` that declared/derived edges could not be checked (the map is the only source for schema-invisible relationships).
- **`{is_greenfield}`** (step-01 §1c) → there is no code and usually no map. Derive expected edges from the **architecture entity relationships** (per `GREENFIELD-BRIEF-DERIVATION.md`); if neither a map nor architecture relationships are available, SOFT-degrade: warn that completeness could not be mechanically verified and fall back to the §5f derivation + step-03 §3 self-review. Never hard-fail a greenfield surface for a missing map.
- **Basis genuinely unavailable** (no FKs resolvable, no map, no architecture) → warn once, set `{surface_completeness_verdict}` = `unverified-basis-absent`, and proceed. A gate that cannot see the contract must not block the work — it must say it couldn't check.

## Halt diagnostic (required-gap)

```
HALT — spawned-surface completeness (STD-SURFACECOMPLETE-001, design-handoff §5h)

Required deliverable frame(s) missing from {spawned_surfaces}:
  - {frame_name} — expected because {FK <table>.<col> → <foreign> | edge-map <from>→<to>};
    the surface displays this record, so its §13 lookup drawer is a required frame.
  - {record}-drawer — expected because {page_mode} is {operational|analytical} and the
    surface drills to a per-record view (§5f rule 2).

Fix (choose per frame):
  • The foreign record IS displayed → add the frame to §5f {spawned_surfaces}
    (frame_name · trigger · render_as · must_contain · figures · depth-1 lookups;
     richness floor — no bare identity stub) and re-run.
  • The foreign record is NOT displayed on this surface → it is an out-of-scope edge;
    log it in {surface_completeness_notes} with a one-line rationale (soft, not a frame).
  • The relationship exists on-surface but no FK / edge-map entry backs it → declare it in
    docs/relational-coherence/relational-edges.yaml (edges: or co_views:), then re-run.
    Do NOT invent the edge into the brief.
```

## What this gate does NOT do

- Does not verify a frame's **contents** are correct (that a `warehouse-lookup` shows the right fields) — the §5f richness floor + step-03 §3 self-review own that.
- Does not verify the frames list is **well-formed** (present / non-empty / unique / mirrored in §7 body) — that is step-04's Block-B `frames` internal-consistency assertion, which stays and runs after the brief is written.
- Does not **fix** anything or edit the map — it detects, classifies, and either halts with a fix recipe or records a soft exception. Extending `relational-edges.yaml` is a deliberate, routed action (owned by `relational-coherence-audit`), not an auto-edit.
