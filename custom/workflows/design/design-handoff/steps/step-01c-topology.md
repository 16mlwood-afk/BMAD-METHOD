---
name: 'step-01c-topology'
description: 'Surface topology, analytics hierarchy, spawned-surface inventory, user context, and the gather COMPLETION checklist. The §5d–§6 block, split out of step-01-gather for context budget — same content, no behaviour change.'
---

# Step 1c: Surface Topology & Context (Bias-Free)

**Progress: Step 1c of the step-01 gather** — continues from `step-01b-decide.md`; next is `step-02-audit-design.md`.

This step carries forward ALL state from `step-01-gather.md` and `step-01b-decide.md`. The COMPLETION checklist below is the final gather checklist for the whole of step-01 (§1–§6), not just this sub-step.

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

**When the verdict is not `single-page-appropriate`:**
Describe the recommended topology in 2-4 sentences: which route covers which job. Note any routes that already exist in `{implementation_files}` for this feature prefix.

Before generating the brief, surface to the user:
> *"The gathered scope suggests this feature spans multiple surfaces. This brief will cover `{route}` ([primary job]). Also recommended: a brief for [other routes + their jobs]. Generate now, or continue with primary only?"*

In autonomous mode, proceed with the primary brief and surface the topology in §4c of the generated brief.

Set `{surface_topology_verdict}` and `{surface_topology_notes}`.

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

**Derive `{spawned_surfaces}` (don't recall).** One entry per frame, mechanically from §5/§5a/§3a:

1. **The primary surface** — always frame #1. `frame_name` = the route's surface (e.g. `orders-worklist`); `render_as` = `full-bleed` (or the §5a composition); `must_contain` = the primary job; `figures` = the §4d decision numbers it carries (if any); `lookups` = `—` (its linked records are their own frames, below).
2. **The drilled detail drawer** — emit this frame **iff** `{page_mode}` ∈ {`operational`, `analytical`} AND the surface drills into a per-record view (the policy-default "table-first worklist + right-side detail drawer" composition — the common case). `frame_name` = `{record}-drawer` (e.g. `order-drawer`); `trigger` = "click a worklist row"; `render_as` = `drawer-over-{primary}`; `must_contain` = the record's formalised field groups; `figures` = **every §4d decision number the record carries** (cost/value/ROI/margin — these are the figures `docs/design-policy.md` §15 governs; name them so the drawer is drawn basis-complete, not as a bare-number dump); `lookups` = the depth-1 §2a fields this drawer shows through its relations. For `{page_mode}: detail` the primary surface (#1) IS this drawer — do not emit a duplicate.
3. **One lookup drawer per `{linked_records_inventory}` entry (§3a)** — each §13 expand-in-context target is its own frame. `frame_name` = `{foreign-record}-lookup` (e.g. `warehouse-lookup`, `catalog-lookup`); `trigger` = "act on the {reference} on {parent surface}"; `render_as` = `drawer-over-{parent}`; `must_contain` = the foreign record's own identifying fields **plus what this relation needs** (a warehouse opened from an order shows code/type/status/location AND what is routed through it for THIS order — not a bare stub); `figures` = any decision numbers it carries; `lookups` = its **depth-1** inline lookups only (the foreign record's own §2a owns the next level — do NOT inline the recursive order→catalog→supplier graph).

**Richness floor (the anti-stub rule).** No frame's `must_contain` may be a bare identity stub (code/type/status alone) when the owning record carries decision-relevant fields. A `warehouse-lookup` that lists only `code/type/status/location` is the silent thinness this inventory exists to prevent — name the fields the relation actually needs. If a lookup record genuinely has nothing beyond identity, say so explicitly (`must_contain: identity only — {record} carries no decision fields`), never leave it to default thin.

Set `{spawned_surfaces}` — frame #1 always present; the detail-drawer frame present per the §5a composition; one frame per linked record. Empty only for a true leaf surface (no drawer, no linked records). This renders into brief **§7 (Surface Inventory)** as the required deliverable list, and is cross-checked at build time by `design-implement` step-03 §2f (a brief-promised frame absent from the rendered bundle = "not drawn → route back", never a silent pass).

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
- `{surface_topology_verdict}` ✓ (one of: `single-page-appropriate` | `needs-detail-route` | `needs-tab-views` | `needs-sibling-route`)
- `{analytics_hierarchy}` ✓ (each surface tagged hero | supporting | drill — §5e; empty when the page has 0–1 analytics surface) — plus `{hierarchy_rationale}` and `{analytics_surface_inventory}`; `{hierarchy_unresolved}` set only when no single hero emerged (→ routed to §5d topology)
- `{surface_topology_notes}` ✓ (recommended topology in 2-4 sentences; empty string when verdict is `single-page-appropriate`)
- `{linked_records_inventory}` ✓ (§3a — one entry per on-screen value that IS a record another surface owns: foreign reference · owning surface+route · expand-in-context target (§7 drawer over the current surface, NOT navigate-away; "Open full {sibling} →" secondary inside it) · inline lookups read through the relation; empty **only** for a true leaf surface that references no foreign record. Renders into brief §2a and is enforced at review by `design-review-pr` §13/§12.)
- `{spawned_surfaces}` ✓ (§5f — one **required deliverable frame** per surface this page spawns: the primary surface, the drilled detail drawer (per the §5a composition), and one lookup drawer per `{linked_records_inventory}` entry; each with `frame_name · trigger · render_as · must_contain · figures (§4d) · lookups (depth-1 §2a)`; richness floor applied — no bare identity stubs; depth-1 lookups. Renders into brief **§7 Surface Inventory** and is cross-checked by `design-implement` step-03 §2f. Empty only for a true leaf surface with no drawer and no linked records.)
- `{user_context}` ✓
- `{brand_identity}` ✓ (may be empty)
- `{design_system}` ✓ ("branded", "existing", or "external")
- `{handoff_mode}` ✓ ("fresh-design" or "refine-screen")
- If `{handoff_mode}` = "refine-screen": `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}` ✓ (loaded by workflow.md before this step)

**Refine-screen mode reminder:** Do NOT ask the user "what feels wrong?" or "what are the top issues?" — those came from the artifact loaded in workflow.md. The user-context question (who uses this, how often) is still valid; the diagnostic question is not.

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md`
