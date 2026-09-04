---
name: 'step-01c-topology'
description: 'Surface topology, analytics hierarchy, spawned-surface inventory, user context, and the gather COMPLETION checklist. The §5d–§6 block, split out of step-01-gather for context budget — same content, no behaviour change.'
---

# Step 1c: Surface Topology & Context (Bias-Free)

**Progress: Step 1c of the step-01 gather** — continues from `step-01b-decide.md`; next is `step-02-audit-design.md`.

This step carries forward ALL state from `step-01-gather.md` and `step-01b-decide.md`. The COMPLETION checklist below is the final gather checklist for the whole of step-01 (§1–§6), not just this sub-step.

**Chrome short-circuit:** when `{surface_class}` = `chrome` (step-01 §0), the topology / analytics-hierarchy / spawned-surface machinery in this file is n/a — run ONLY the user-context capture (if not already done) and the COMPLETION checklist, marking page-machinery boxes `n/a — chrome` and verifying instead that step-01 §0's chrome captures are present: route inventory, per-item states, role visibility, breakpoints, and the chrome `frames` list.

## EXECUTION SEQUENCE (continued)

### 5d. Surface Topology Assessment

**Injected-placement short-circuit (consumability contract — analytics-home axis ONLY).** If `{injected_placement}` is set, `analytics-placement-triage` already decided *where the analytics surface lives* — but that is only the **analytics-home** axis of topology, NOT the worklist's own **per-item depth**. So honor the analytics-home and skip re-deriving *it*, but **STILL run question 2 below** (per-item detail depth → `needs-detail-route`), which the injection does not speak to. Resolve `{surface_topology_verdict}`: if question 2 independently finds the items warrant their own detail route, **`needs-detail-route` wins** (and the analytics home rides alongside, recorded `injected-by-triage`: tab / sibling / rides-the-page); otherwise set it from the analytics-home mapping — `tab` → `needs-tab-views`, `sibling-page` → `needs-sibling-route`, `band` / `remove-band` → `single-page-appropriate` — noted `injected-by-triage`. When `{injected_placement}` is empty (the default), ignore this short-circuit and derive all four questions normally.

**The question:** Given everything gathered above, is this feature's scope correctly bounded at a single route — or does the data depth, capability breadth, or user job structure suggest multiple surfaces?

**Reason from the evidence, not from thresholds.** You have already captured: the data model (entities and their depth), the user goals, the capabilities list, the data volumes, and the existing routes in `{implementation_files}`. Work through these four questions from the gathered evidence:

**1. How many distinct user jobs live on this route?**
Count from `{must_support_capabilities}` and the primary goals. Jobs that operate at fundamentally different depths — a triage queue and a deep-dive evidence panel, a batch management view and the items within it — are structural signals, not just UX variety. If the same route is expected to do two distinct jobs at different depths, ask whether splitting is the better architectural choice.

**2. What is the realistic capacity of the primary surface?**
A right-drawer holds a moderate-depth record view. A full-page detail view holds more — but there is a ceiling. If the per-item evidence layer (fields, charts, sub-tables, provenance panels) would span several full-page scroll-sections, the item record has outgrown a secondary panel and warrants its own route. Check whether `/[feature]/[id]` already exists in `{implementation_files}`.

**3. Are there sub-entities that belong on a sibling route?**
Import batches, audit history, configuration records, and provenance tables are frequently embedded in a primary surface when they'd be better served by an adjacent route — `/[feature]/batches`, `/[feature]/history`, `/[feature]/config`, etc. Check whether such routes already exist or are implied by the implementation. A sibling route serves a distinct operator job and does NOT require a return to the primary surface mid-task.

**4. Would tab/view navigation help — or just add chrome?**
Tab-level views are appropriate when the surface has two or three genuinely distinct slices of the same primary data that users switch between deliberately — not as a workaround for content overflow. The test: can you name the operator job that owns each tab? "Active queue" and "batch history" pass. "Main" and "Other" fail. If tabs would just partition what should be one coherent view, they are chrome. If they represent distinct operator modes, they earn their place.

**5. Do the records on this surface span multiple operational handlers the project policy requires be split?**
Some project design policies forbid merging records from distinct **operational handlers** — a routing/dispatch warehouse, a shipping lane, a fulfilment provider, or any analogous per-record processor — into one front-end list, and require a split by view instead. **Consult the project `design-policy.md` for whether such a rule exists and what counts as a "handler" in this domain — the concrete handler set is the policy's to define, never this workflow's** (this question is a no-op in projects whose policy defines no such rule). Where the policy defines the split, it is a **forcing condition, not a soft signal:** a surface whose records resolve to **two or more** such handlers (any number ≥2) CANNOT be `single-page-appropriate` as one undifferentiated worklist — the operator works in a per-handler frame and the merge strips it. The records may share one underlying queue/table; this governs presentation only, not storage. When the condition holds, the verdict MUST be the split — `needs-tab-views` when the handlers are switched-between modes of one route, or `needs-sibling-route` when each handler warrants its own surface. Detect the condition from the gathered data model / capabilities and recommend the split for the operator to confirm; never default to the merged list.

**Verdict — one of:**

| Verdict | When to use |
|---------|------------|
| `single-page-appropriate` | All jobs are coherently served from one route. Scope, depth, and volume fit the surface. |
| `needs-detail-route` | The per-item depth warrants its own route (`/[feature]/[id]`). The primary route covers the queue/list; the item's full evaluation belongs on a second route. Most common for data-heavy operational surfaces. |
| `needs-tab-views` | Two or three genuinely distinct operator modes on the same primary data justify top-level tab navigation within the current route. The tabs represent mode-switching, not content overflow. |
| `needs-sibling-route` | A distinct sub-feature (batch management, history, configuration) belongs on its own adjacent route rather than embedded in the primary surface. |
| `not-a-route` | **The DEMOTING verdict — this should not be a route at all.** The job is served by a SECTION of an existing surface, a drawer on it, or a contextual LINK from the surface the operator is already standing on. Name which existing route absorbs it and in which form. |

**`not-a-route` exists because every OTHER verdict points OUTWARD.** `single-page-appropriate`,
`needs-detail-route`, `needs-tab-views` and `needs-sibling-route` between them can only keep a route
or add one — so a step meant to catch surface sprawl could previously only ever grow it. That is a
ratchet, and it is not hypothetical: cash-recovery spent a permanent nav slot on 2026-08-24 to fix an
unreachability that a contextual link fixed instead the next day. The sibling precedent is
`analytics-placement-triage`, which has carried demoting verdicts (`no-surface`, `remove-band`) all
along and is merely scoped to analytics.

**Reach for it FIRST when any of these hold:** the job is a read-only view of data another surface
already owns · the new route's only argument is that the content is hard to reach today (fix the
reachability, not the topology) · the operator would have to leave the surface they work on to use it
and then come straight back · the "page" is one list, one panel, or one form with no state of its own.
**When it holds, say which surface absorbs the job and in what form** — section, drawer, or link —
and stop. A `not-a-route` verdict is a complete, successful outcome of this step, not a failure to
decide, and it must never be softened into `needs-sibling-route` to keep the handoff moving.

**When the verdict is not `single-page-appropriate` (and not `not-a-route`):**
Describe the recommended topology in 2-4 sentences: which route covers which job. Note any routes that already exist in `{implementation_files}` for this feature prefix.

Before generating the brief, surface to the user:
> *"The gathered scope suggests this feature spans multiple surfaces. This brief will cover `{route}` ([primary job]). Also recommended: a brief for [other routes + their jobs]. Generate now, or continue with primary only?"*

In autonomous mode, proceed with the primary brief and surface the topology in §4c of the generated brief.

Set `{surface_topology_verdict}` and `{surface_topology_notes}`.

**HALT on `not-a-route` — do NOT generate a brief.** There is no surface to design, so continuing
would produce a brief for a page the step just decided should not exist. Stop here and emit the
demotion record instead:

> **`not-a-route` — this job does not warrant its own surface.**
> **Absorbed by:** `{existing route}` · **as a:** section | drawer | contextual link
> **Why not a route:** {2–4 sentences}
> **If it should be a route anyway, the owner says so** — an agent may argue for the surface and may
> build it once admitted, but may not be the sole reader of its own case.

This is a **successful** terminal outcome of `design-handoff`, not a failure or a blocked run: report
it as the answer to the ask. Where the project keeps a scope register, the demotion is recorded there
as the surface's admission record. **`{surface_topology_notes}` MUST be non-empty on this verdict** —
a demotion that does not name the absorbing surface is not actionable by anyone downstream.

#### 5d-i. Surface part — is THIS brief targeting a sub-surface?

Now fix the brief's position *within* its route. `{surface_part}` is part of the **surface identity** (`normalise(route)` + `surface_part`, within `mode`) that `step-03-generate-brief.md` §1a and `brief-revision-policy.md` invariant 6 use to detect a same-surface predecessor — so it must be decided here, at topology time, not re-inferred at brief-gen time.

- If the handoff **target is a tab / section / panel that lives inside a page** — `{route}` is a parent page and the target is one named slice of it (e.g. a `raw-records` tab on the ingestion-run view) — set `{surface_part}` = the kebab name of that slice (e.g. `raw-records`).
- Otherwise — the target IS the route's whole primary surface — set `{surface_part}` = `""`.
- A §13 expand-in-context **lookup drawer is NOT a surface**; it was already redirected to its parent brief in `step-01-gather` §2a. Never set `{surface_part}` for one.

A `needs-tab-views` topology verdict does **not** by itself make `{surface_part}` non-empty: that verdict means the *primary* brief recommends sibling tab briefs, but this brief still targets the primary surface (`{surface_part}: ""`). `{surface_part}` is non-empty only when the handoff was pointed AT a sub-surface from the start.

Set `{surface_part}`.

### 5e. Analytics Surface Hierarchy — rank multiple co-resident surfaces

**Gate:** run this section ONLY when the route (after §5d topology) carries **two or more distinct analytics surfaces** — a "surface" being a dataset + question pair that earns its own §5c archetype (a price-over-time chart, a seller-share composition, and a buy-box-ownership ranking are three surfaces, not one band). Zero or one surface → skip; §5b/§5c already handle the singular case. **This gate fires regardless of `{page_mode}`, including `detail`:** an analytics-rich single-entity page (a product research / monitoring view whose record carries time-series and competitive aggregates) is exactly the case §5b's "a single record has no aggregate dimension" misses.

**The problem this prevents:** left unranked, multiple legitimate surfaces render at equal visual weight — the flat panel-stack the policy bans (§6 "the visual lead must be one or two restrained charts… supporting tables"; §5 no card-grid-as-structure). The handoff has named the *shape* of each surface (§5c) but never said which one *leads*. This section carries that decision into the brief so the designer ranks deliberately instead of stacking by default.

**Rank by the page's primary question, not the legacy render.** You have already captured the one job this page exists for (§4 feature purpose / §6 user context). Run §5c once per surface to get each one's archetype, then assign each surface a tier:

| Tier | Test | Form in the brief |
|------|------|-------------------|
| **hero** (1, rarely 2) | Most directly answers the page's primary question | Full-weight chart, top of the analytics region |
| **supporting** | Qualifies or contextualises the hero's answer | Demoted to a compact form — sparkline / strip / mini-chart, not a full panel |
| **drill** | Consulted only on a specific doubt, not in the default scan | Collapsed behind an expand/toggle; available, not displayed |

The anti-bias is the same as §5a/§5b: rank by the **job**, never by the order the legacy page happened to stack them (flat-equal *is* the legacy bias). Demotion is real form, not a smaller title — a supporting surface becomes a sparkline, a drill surface collapses.

**Ground or flag (reuses §5d).** If you **cannot name a single primary question that designates one hero** — two surfaces are genuinely co-equal because the page serves two unrelated jobs — do not flatten them to a tie. That is the §5c "two co-equal archetypes → split it" rule at the page level: **route back to §5d** (`needs-tab-views` if the two jobs are deliberately switched between, `needs-sibling-route` if they are distinct sub-features). If you can't rank it to one hero, it may not be one page.

**Capture the reasoning.**
- `{analytics_surface_inventory}` — the distinct surfaces found, each with its dataset + question + §5c archetype.
- `{analytics_hierarchy}` — each surface tagged `hero | supporting | drill`.
- `{hierarchy_rationale}` — the primary question, why the hero answers it, and why each other surface is **demoted, not deleted** (richness is preserved — a research/detail page wants all of it, ranked).
- `{hierarchy_unresolved}` — set when no single hero emerges; record the §5d verdict it routed to.

In autonomous mode, proceed with the inferred hierarchy and surface it in the brief (§4b); the ground-or-flag still fires — a wrong hero is confident nonsense, so an unresolvable primary question is asked/routed, not guessed.

Set `{analytics_hierarchy}` and `{hierarchy_rationale}` (both empty when the gate doesn't fire — zero or one analytics surface).

### 5f. Spawned-surface inventory — every frame this page must DELIVER

A page is never one frame. It spawns secondary surfaces the operator reaches at runtime — the **detail drawer** they drill into, and the **§13 expand-in-context lookup drawers** that open over it — and the downstream pipeline draws and checks **only the frames the brief enumerates** (workflow.md Deliverable-Completeness Principle). A drawer the brief leaves implicit is never drawn by Claude Design and is then *inferred* by `design-implement` — which is precisely how a drilled drawer ships thin and unformalised (bare `€60` with no GBP/VAT basis, a lookup drawer showing only code/type/status). So enumerate the frames here, **derived** from what you already captured — never recalled, never deferred to a "pending" brief.

**Faithful-mirror short-circuit (check FIRST).** If `{suppress_expand_in_context}` is `true` (the §5a `source-mirror` archetype — a `raw-records` faithful source mirror): `{spawned_surfaces}` = **frame #1 only** (the primary mirror table). Emit **no** detail-drawer frame and **no** lookup-drawer frames — the §3a identifiers render as verbatim source columns (scan/trace anchors), not §13 expand-in-context drawers. Skip the three-item derivation below; this is the guard that stops a faithful mirror over-producing drawer frames it must not have. (Brief §7 then carries the single mirror frame.)

**Derive `{spawned_surfaces}` (don't recall).** One entry per frame, mechanically from §5/§5a/§3a:

1. **The primary surface** — always frame #1. `frame_name` = the route's surface (e.g. `orders-worklist`); `render_as` = `full-bleed` (or the §5a composition); `must_contain` = the primary job; `figures` = the §4d decision numbers it carries (if any); `lookups` = `—` (its linked records are their own frames, below).
2. **The drilled detail drawer** — emit this frame **iff** `{page_mode}` ∈ {`operational`, `analytical`} AND the surface drills into a per-record view (the policy-default "table-first worklist + right-side detail drawer" composition — the common case). `frame_name` = `{record}-drawer` (e.g. `order-drawer`); `trigger` = "click a worklist row"; `render_as` = `drawer-over-{primary}`; `must_contain` = the record's formalised field groups; `figures` = **every §4d decision number the record carries** (cost/value/ROI/margin — these are the figures `docs/design-policy.md` §15 governs; name them so the drawer is drawn basis-complete, not as a bare-number dump); `lookups` = the depth-1 §2a fields this drawer shows through its relations. For `{page_mode}: detail` the primary surface (#1) IS this drawer — do not emit a duplicate.
3. **One lookup drawer per `{linked_records_inventory}` entry (§3a)** — each §13 expand-in-context target is its own frame. `frame_name` = `{foreign-record}-lookup` (e.g. `warehouse-lookup`, `catalog-lookup`); `trigger` = "act on the {reference} on {parent surface}"; `render_as` = `drawer-over-{parent}`; `must_contain` = the foreign record's own identifying fields **plus what this relation needs** (a warehouse opened from an order shows code/type/status/location AND what is routed through it for THIS order — not a bare stub); `figures` = any decision numbers it carries; `lookups` = its **depth-1** inline lookups only (the foreign record's own §2a owns the next level — do NOT inline the recursive order→catalog→supplier graph).
4. **One state-variant frame per operator-distinct lifecycle state — ONLY when `{is_live_process_surface}` (§3c).** The `{runtime_behavior_contract}` run lifecycle names the states; each state that **changes what the operator sees or can do** is its own frame of the primary surface: `frame_name` = `{primary}--{state}` (e.g. `run-console--running`, `run-console--partial-failure`, `run-console--done-with-exceptions`); `trigger` = the §3c transition that enters it; `render_as` = same as frame #1; `must_contain` = what is true in that state + the control verbs legal in it; `figures`/`lookups` per the state. Frame #1 IS the resting/idle state — emit variants for the others only. Do NOT emit a frame for a state that is visually indistinct to the operator (collapse it into its neighbour and say so) — the film-strip communicates the dynamic mechanism without exploding the inventory. This is the brief-level twin of `design-implement`'s state axis (§2d lineage): a state the brief never frames is a state the bundle never draws. **On a handheld-first surface, a state-variant frame is a DEGRADED STATE of frame #1, never a peer design** (`shared/operator-artifact-contract.md` B3): same chrome, same layout skeleton, same primary-action position, ONE legible region differing, rendered as a subordinate strip beneath the canonical frame — never a full-page comp at equal size, never with its own nav or hero. A variant that needs its own navigation has become a second product, which means the state was mis-modelled — collapse it or re-model it, do not draw it.
5. **One workflow-state frame per operator-distinct step of a multi-step flow — when the surface has ≥2 operator-distinct steps, INDEPENDENT of `{is_live_process_surface}`.** Rule 4 fires only for a *watched* long-running process; this rule covers the request/response multi-step surface it misses — a single-route entry/verify/commit flow (`ingest → verify → preflight (duplicate + staging gate, with overrides) → outcome (live vs staged)`; e.g. Log Order `/orders/new`) where `{is_live_process_surface}` is `false` yet the steps are genuinely distinct operator surfaces. **Derive the steps from the §3 mutation-derivation audit, not from a lifecycle contract:** a `preflight`/pre-commit action (duplicate check, staging gate) ⇒ a **gate** state (what the operator confirms/overrides before committing); a `create`/commit action ⇒ an **outcome** state (live vs staged, the committed result). `frame_name` = `{primary}--{state}` (e.g. `order-entry--preflight`, `order-entry--committed`); `trigger` = the action that enters the step; `render_as` = same as frame #1; `must_contain` = what is true in that step + the verbs legal in it (a duplicate-gate names the duplicate evidence AND the override control — never a bare confirm); `figures` = the §4d decision numbers that step carries (a preflight gate over money shows GBP/VAT basis-complete, not a bare `€60` — the §7/§15 thinness this rule exists to prevent). **Gate on "≥2 operator-distinct steps," never on live-process.** Reuse the same discipline as rule 4: frame #1 IS the resting/entry step (emit variants for the others only); apply the richness floor below; **collapse** a step that is visually indistinct to the operator into its neighbour and say so; each frame renders into §7 and is cross-checked at build by `design-implement` step-03 §2f. This is additive — it does not change rule 4's live-process behaviour (a surface that is both a watched process AND multi-step derives from both, deduped by `frame_name`). Without it these gate/outcome frames survive only by the author reasoning up from workflow.md's Deliverable-Completeness Principle — exactly what this derivation makes unnecessary. (Root-cause class: `contract-dimension-gap` — the frame-generation contract was missing the workflow-state axis on the non-live-process path.)

**Richness floor (the anti-stub rule).** No frame's `must_contain` may be a bare identity stub (code/type/status alone) when the owning record carries decision-relevant fields. A `warehouse-lookup` that lists only `code/type/status/location` is the silent thinness this inventory exists to prevent — name the fields the relation actually needs. If a lookup record genuinely has nothing beyond identity, say so explicitly (`must_contain: identity only — {record} carries no decision fields`), never leave it to default thin.

Set `{spawned_surfaces}` — frame #1 always present; the detail-drawer frame present per the §5a composition; one frame per linked record; the state-variant frames present iff `{is_live_process_surface}` (rule 4); the workflow-state frames present iff the surface has ≥2 operator-distinct steps (rule 5). Empty only for a true leaf surface (no drawer, no linked records, single step). This renders into brief **§7 (Surface Inventory)** as the required deliverable list, and is cross-checked at build time by `design-implement` step-03 §2f (a brief-promised frame absent from the rendered bundle = "not drawn → route back", never a silent pass).

### 5g. List-rendering — pagination / virtualization is a DERIVED requirement, not flavour text

The gather already captures **Data volume** (§1 — "Typical data volume", e.g. "1,400+ records/quarter") and §5d uses it to decide *page splits*. But volume is never **derived into a list-rendering requirement** — so an operational/analytical worklist whose row count grows unbounded ships as a single un-paginated render, every time. Volume captured as flavour text is the gap; the fix is to derive a verdict and make it a **deliverable**, the same way §5b derives the band and §5f derives the frames. (Contract-dimension-gap, derive-to-requirement flavour: the input axis exists, the requirement never gets formed.)

**Gate:** run this section when the surface's PRIMARY composition is a **list / worklist / table** (`{page_mode}` ∈ {`operational`, `analytical`} with a row-bearing primary surface; skip for `detail` and for a surface with no primary list). Decide from the **job + the captured Data volume**, NOT the legacy render:

1. **Bounded & small** — a handful of rows with a hard ceiling (e.g. "always ≤ the day's open sessions") → `single-render`. No pagination machinery; rendering all rows is correct.
2. **Grows, scan-and-act worklist** — the operator processes many, ordered by urgency/recency; counts in the hundreds–thousands or **unbounded over time** → `paginate` (page controls + a visible count). The operational default.
3. **Large, dense, continuous scroll** — thousands of rows the operator scrolls rather than pages → `virtualize` (windowed rows; the table stays performant).
4. **Append-only / open-ended feed** — the operator pulls "more" of a stream → `load-more`.

Set `{list_rendering_verdict}` ∈ `single-render | paginate | virtualize | load-more`. When it is **NOT `single-render`**, the chosen mechanism is a **REQUIRED §7 deliverable** on the primary list frame (the frame's `must_contain` names it — e.g. "paginated worklist: page controls + total count") **AND** a `{must_support_capabilities}` entry (e.g. "page the worklist — the list grows past one screen") — so it is drawn by the design and enforced by `design-implement` (its step-03 **List-rendering** row, the §2d page-shell analog, fails a build that omits a required mechanism). A growing list shipped as a single render is the silent miss this derivation closes.

**Capture the reasoning.** `{list_rendering_rationale}` — the volume + growth read that selected the verdict (e.g. "removal orders accumulate every ingestion run → unbounded → paginate"). For `single-render`, record the **hard ceiling** that justifies it, so "I'll just render all the rows" is a *decision*, not a silent default.

In autonomous mode, derive the verdict and surface it in the brief; a list-bearing surface NEVER defaults silently to `single-render` — that default IS the gap. If volume genuinely can't be read, ask the one volume question (do not guess `single-render`).

Set `{list_rendering_verdict}` and `{list_rendering_rationale}` (both empty only for a non-list surface — `detail`, or a surface with no primary list).

### 5h. Spawned-surface completeness gate — every required frame is DERIVED-and-present, not self-attested

§5f *derives* `{spawned_surfaces}` and step-03 §3 *self-attests* the §7 list — both probabilistic. The only deterministic completeness gate today fires **downstream** (`design-synthesize` Gate 1f / `design-implement` §2f) and "never bites if those consumers don't run." So a run can silently under-read the edge map (miss a foreign record that IS in the map) or under-derive §5f (capture the linked record, emit no frame) and ship a brief that under-enumerates frames. This section closes that at the producer, before the brief is written. **Full rule: `shared/spawned-surface-completeness.md` (STD-SURFACECOMPLETE-001).** It is **additive** — step-04's Block-B `frames` internal-consistency assertion (well-formedness *after* write) stays and still runs.

**One derivation basis — the same source `relational-coherence-audit` walks:** Drizzle schema FKs (auto-derived) + the declared `{project-root}/docs/relational-coherence/relational-edges.yaml` (`edges:` + `co_views:`). §3a already read this map to seed `{linked_records_inventory}`; this gate re-uses that read and asserts nothing was dropped between the map/FKs and `{spawned_surfaces}`. **Derive no relationship of your own** — an on-surface relationship absent from both FKs and the map routes back to the audit ("declare a derived edge / co-view"), never invented here (no-guessed-edges).

**Build `{expected_required_frames}` (short-circuits FIRST):**
- If `{suppress_expand_in_context}` is `true` (§5a `source-mirror`) → expected set = **frame #1 only**; never fail a faithful mirror for missing drawer/lookup frames. Skip the rest.
- True-leaf surface (no drill, no linked records) → expected set = frame #1 only.
- Otherwise: **E1** primary surface (always); **E2** detail drawer (iff `{page_mode}` ∈ {operational, analytical} and the surface drills to a per-record view — for `detail`, frame #1 IS the record view, no separate E2); **E3** one lookup drawer per FK / edge-map edge from this surface whose foreign record the surface **displays**; **E4** one state-variant frame per operator-distinct lifecycle state (iff `{is_live_process_surface}` — §5f rule 4); **E5** one workflow-state frame per operator-distinct step (iff the surface has ≥2 operator-distinct steps — §5f rule 5), deduped against E4 by `frame_name` where a surface is both watched and multi-step.

**Classify every FK / edge-map edge explicitly — none silently absent (anti-silent-drop, same discipline as `{dropped_capabilities}`):**
1. **Required frame missing → HARD HALT** (before step-02/03/04). Any `{expected_required_frames}` entry with no `frame_name` match in `{spawned_surfaces}` → collect into `{completeness_gap_required}` and halt with the STD-SURFACECOMPLETE-001 diagnostic (names each missing frame + its source edge/FK + the per-frame fix).
2. **Displayed-but-undeclared edge → HARD HALT** as a required gap. Surface displays a foreign record with no backing FK / map entry → halt and route "declare it in `relational-edges.yaml`, then re-run." Do NOT invent the edge into the brief.
3. **Edge whose foreign record is NOT displayed → SOFT.** The audit's OUT-OF-SCOPE CANDIDATE class — needs no frame, but log it in `{surface_completeness_notes}` as `edge · why-not-displayed`. Warn and proceed; never halt.

**Graceful degradation — do NOT hard-fail on a thin basis.** No `relational-edges.yaml` → FKs only, note the map couldn't be checked. `{is_greenfield}` → derive from architecture entity relationships (`GREENFIELD-BRIEF-DERIVATION.md`); if neither map nor architecture is available, warn and fall back to the §5f derivation + step-03 §3 self-review — never hard-fail a greenfield surface for a missing map. Basis genuinely unavailable → set `{surface_completeness_verdict}` = `unverified-basis-absent`, warn once, proceed.

Set `{surface_completeness_verdict}` ∈ `complete | complete-with-noted-exceptions | unverified-basis-absent` (rules 1/2 halt instead of a passing "incomplete" state) and `{surface_completeness_notes}` (the out-of-scope-edge rationales + any degradation note; empty only when the verdict is `complete`).

### 6. Identify User Context

Set `{user_context}`:

- What role uses this page?
- What's the job-to-be-done?
- How often? (daily tool vs. occasional reference)
- What's the emotional state? (urgent task vs. exploratory browsing)

If undetermined from code, ask the user ONE question:
> "Who uses this and what are they trying to accomplish?"

---

## COMPLETION

Confirm populated:
- `{github_repo_url}` ✓
- `{feature_name}` ✓
- `{feature_scope}` ✓
- `{feature_purpose}` ✓
- `{data_shape}` ✓
- `{api_surface}` ✓ (incl. the §3 **mutation-derivation audit** — every server action the current surface invokes is accounted for: carried into `{must_support_capabilities}` or logged in `{dropped_capabilities}`)
- `{dropped_capabilities}` ✓ (each a deliberate drop with `capability · backing_action · reason`; empty list only when every action the current surface exposes is carried forward — never empty by omission)
- `{implementation_files}` ✓
- `{page_mode}` ✓ ("operational", "analytical", or "detail")
- `{composition_provenance}` ✓ (`policy-default` | `recommended-alt`; decided in §5a from the job, NOT inherited from the policy default; `recommended-alt` veto-surfaced and `{composition_rationale}` captured) — and `{page_mode}` stays the honest work type even when composition deviates
- `{band_provenance}` ✓ (`inherited` | `recommended-new` | `recommended-drop` | `none`; net-new/drop recommendations veto-surfaced)
- `{has_analytics_band}` ✓ (`true` iff band_provenance ∈ {inherited, recommended-new})
- `{analytics_archetype}` ✓ (one of the nine, or `unclear` → asked; empty when no band)
- **Analytics reasoning capture** ✓ (populated iff `{has_analytics_band}` is `true`; all empty otherwise) — `{page_mode_rationale}`, `{band_decision_log}`, and the archetype decision object captured from the `analytics-surface-architect` skill in §5c: `{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`, `{archetype_drill_map}`, `{archetype_prohibited}`. These feed the rationale artifact (step-03b) and §4b; capturing the deliberation here is what makes the presentation decision auditable instead of discarded.
- `{has_decision_numbers}` ✓ (`true` iff the surface presents figures the user acts on — verdict, score, ROI/margin/profit, KPI; broader than `{has_analytics_band}`, so it captures bandless `detail`/`analytical` decision surfaces like a lead buy page; `false` for pure data-entry/passive-review/CRUD — §5c-2)
- **Analytics rigor capture** ✓ (populated iff `{has_decision_numbers}` is `true`; all empty otherwise — run **per surface** on multi-surface pages) — `{rigor_read_sentence}`, `{rigor_decision_numbers}`, `{rigor_deciding_fields}`, `{rigor_data_gaps}`, `{rigor_verdict}` from the `analytics-rigor` skill in §5c-2. These render into **brief §4d** (surface-level — covers decision numbers in the band AND the record/hero) and drive `C-RIGOR-01` at review; rationale §3b records the reasoning when a band exists. The §5c-2 honesty gate holds — data gaps are surfaced as enrichment requirements, never fabricated into figures.
- `{is_capital_decision}` ✓ (`true` iff the surface's job is to commit a scarce resource — capital / inventory slots / time — under uncertainty with a real downside; narrower than `{has_decision_numbers}`, so a buy/reorder/sizing surface is `true` but a dashboard/coverage/status surface is `false` — §5c-3)
- **Decision analysis capture** ✓ (populated iff `{is_capital_decision}` is `true`; all empty otherwise — run **per decision surface**) — `{decision_frame}`, `{decision_outcome}`, `{decision_sizing}`, `{decision_sensitivity}`, `{decision_context}`, `{decision_gaps}`, `{decision_verdict}` from the `decision-analysis` skill in §5c-3. These render into **brief §4e** (the executive layer — modelled outcome + sizing + breakeven driver + reference class) and drive `C-DECISION-01` at review; rationale §3c records the reasoning when a band exists. The §5c-3 model-honesty gate holds — an un-modellable decision is an honest `single-scenario` read + a named VOI gap, never a fabricated outcome distribution.
- `{surface_topology_verdict}` ✓ (one of: `single-page-appropriate` | `needs-detail-route` | `needs-tab-views` | `needs-sibling-route` | `not-a-route`)
- `{analytics_hierarchy}` ✓ (each surface tagged hero | supporting | drill — §5e; empty when the page has 0–1 analytics surface) — plus `{hierarchy_rationale}` and `{analytics_surface_inventory}`; `{hierarchy_unresolved}` set only when no single hero emerged (→ routed to §5d topology)
- `{surface_topology_notes}` ✓ (recommended topology in 2-4 sentences; empty string when verdict is `single-page-appropriate`; on `not-a-route` it MUST name the absorbing surface and the form — section, drawer, or link — and may never be empty)
- `{surface_part}` ✓ (§5d-i — the kebab name of the sub-surface within `{route}` when the handoff target is a tab/section/panel inside a page; `""` when the target is the route's whole primary surface; never set for a §13 lookup drawer. Part of the surface identity step-03 §1a / `brief-revision-policy.md` invariant 6 use for predecessor detection.)
- `{linked_records_inventory}` ✓ (§3a — one entry per on-screen value that IS a record another surface owns: foreign reference · owning surface+route · expand-in-context target (§7 drawer over the current surface, NOT navigate-away; "Open full {sibling} →" secondary inside it) · inline lookups read through the relation; empty **only** for a true leaf surface that references no foreign record. Renders into brief §2a and is enforced at review by `design-review-pr` §13/§12.)
- `{spawned_surfaces}` ✓ (§5f — one **required deliverable frame** per surface this page spawns: the primary surface, the drilled detail drawer (per the §5a composition), one lookup drawer per `{linked_records_inventory}` entry, one state-variant frame per operator-distinct lifecycle state from `{runtime_behavior_contract}` (iff `{is_live_process_surface}` — rule 4), and one workflow-state frame per operator-distinct step (iff ≥2 operator-distinct steps — rule 5, deduped against rule 4 by `frame_name`); each with `frame_name · trigger · render_as · must_contain · figures (§4d) · lookups (depth-1 §2a)`; richness floor applied — no bare identity stubs; depth-1 lookups. Renders into brief **§7 Surface Inventory** and is cross-checked by `design-implement` step-03 §2f. Empty only for a true leaf surface with no drawer, no linked records, and a single step.)
- `{is_live_process_surface}` ✓ (§3c — `true` iff the surface's primary job is watching/controlling a long-running in-flight process; `false` for CRUD and finished-output surfaces) — plus `{runtime_behavior_contract}` (populated iff `true`: run lifecycle state machine · per-item states incl. failure/partial lanes · update transport & staleness · control verbs as outcomes · available progress signals; derived from the driving code, never invented; renders into brief **§2c** and feeds the §5f state-variant frames)
- `{surface_completeness_verdict}` ✓ (§5h — `complete | complete-with-noted-exceptions | unverified-basis-absent`; a **required** frame missing from `{spawned_surfaces}`, or a displayed-but-undeclared edge, HALTs here before step-02 rather than producing a passing "incomplete" verdict — `shared/spawned-surface-completeness.md`/STD-SURFACECOMPLETE-001. Derivation basis = Drizzle FKs + `docs/relational-coherence/relational-edges.yaml`, same source as `relational-coherence-audit`. Additive to step-04's Block-B `frames` well-formedness assertion, not a replacement) — plus `{surface_completeness_notes}` (out-of-scope-edge rationales `edge · why-not-displayed` + any degradation note; empty only when verdict is `complete`)
- `{list_rendering_verdict}` ✓ (§5g — `single-render | paginate | virtualize | load-more` for a list-bearing operational/analytical surface; NOT `single-render` ⇒ the mechanism is a REQUIRED §7 deliverable + a `{must_support_capabilities}` entry, enforced by `design-implement` step-03's List-rendering row; empty only for a non-list `detail` surface) — plus `{list_rendering_rationale}` (the volume/growth read, or the hard ceiling that justifies `single-render`)
- `{user_context}` ✓
- `{brand_identity}` ✓ (may be empty)
- `{design_system}` ✓ ("branded", "existing", or "external")
- `{handoff_mode}` ✓ ("fresh-design", "policy-delta", "elevation", or "refine-screen")
- If `{handoff_mode}` = "refine-screen": `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}` ✓ (loaded by workflow.md before this step)

**Refine-screen mode reminder:** Do NOT ask the user "what feels wrong?" or "what are the top issues?" — those came from the artifact loaded in workflow.md. The user-context question (who uses this, how often) is still valid; the diagnostic question is not.

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md`
