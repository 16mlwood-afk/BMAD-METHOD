---
name: 'step-01b-decide'
description: 'Decide page mode, composition fit, and the analytics decision stack (band-belongs, archetype, rigor, decision analysis). The §5–§5c-3 block, split out of step-01-gather for context budget — same content, no behaviour change.'
---

# Step 1b: Page Mode & Analytics Decisions (Bias-Free)

**Progress: Step 1b of the step-01 gather** — continues from `step-01-gather.md`; next is `step-01c-topology.md`.

This step carries forward ALL state set in `step-01-gather.md` (`{data_shape}`, `{api_surface}`, `{feature_purpose}`, `{user_context}`, `{linked_records_inventory}`, `{must_support_capabilities}`, the finance-pass fields, `{injected_placement}`/`{injected_archetype}` if passed, etc.). Apply each section below in order; the anti-bias RULES at the top of step-01-gather still hold.

## EXECUTION SEQUENCE (continued)

### 5. Determine Page Mode

Set `{page_mode}` based on the feature's **dominant user task**:

- **"operational"** — the user processes, reviews, approves, reconciles, files, or resolves records. The page is a worklist. The design should prioritize throughput, scanability, and status visibility. Most pages are operational.
- **"analytical"** — the user discovers trends, compares segments, diagnoses anomalies, explains changes, or moves from summary insight to supporting evidence. The page is an analysis tool.
- **"detail"** — the user reads or edits the fields of **one record**. The page is a drawer or full-page extension of an operational list (the thing you reach by drilling INTO a worklist row), not a queue and not an analysis tool. The design should prioritize legible single-record layout, field grouping, and inline edit/action affordances. Composition is neither table-first nor chart-led — it is a record view. (Per project policy §6/§7: "a drawer or full-page extension of an operational list, never a re-skin.")

**Signals for analytical:** user goals center on "understand", "compare", "spot trends", "review performance", "analyze", "diagnose", or the data has time-series dimensions and the user's job is pattern discovery rather than row processing.

**Signals for detail:** the route is single-entity (ends in `/[id]`, `/[slug]`, a record drawer), the primary surface is ONE record's fields rather than a multi-row table, and the page is reached by drilling from a worklist. A detail page almost never carries an analytics band — a single record has no aggregate dimension (§5b will resolve `band_provenance: none`).

**Hybrid handling:** Some pages mix modes.
- If analysis exists to support immediate row-level action (e.g., a summary chart above a worklist), keep the page in **operational** mode.
- If row-level detail exists mainly to verify or explain summarized behavior (e.g., a trend chart with a drill-down table), keep the page in **analytical** mode.
- A page that contains a worklist AND a per-row detail surface is **operational** — `detail` is for a page whose dominant (often only) job is the single record.
- The dominant user task determines the mode — not the presence of a chart or a table.

If unclear, default to "operational." These three values are the full `page_mode` enum the whole brief contract uses (`brief-revision-policy.md` Block B; consumed by `design-synthesize` / `design-implement`) — emit one of them, never a fourth.

**Capture the reasoning (not just the label).** Set `{page_mode_rationale}` to the concrete signal that selected the mode — the user-goal phrasing or data property that decided it (e.g. "user goal is 'spot which week slipped' → pattern discovery, not row processing"). This is recorded verbatim in the analytics rationale artifact (step-03b) when a band exists; capturing it now means the deliberation is not thrown away once the mode label is set. (Skip the capture only when `{has_analytics_band}` resolves to `false` below — no rationale artifact is emitted then.)

### 5a. Composition Fit Check — does the page-mode's default composition fit THIS surface?

Page mode (§5) names the *kind of work*; the project design policy attaches a **default composition** to each mode (operational → table-first worklist + right-side detail drawer; analytical → chart-led; detail → record-view). That default is a sensible starting point, **not** a certification that this surface's job fits it. Stamping it in unquestioned is the policy-default bias (see workflow.md Anti-Bias Principle II) — as real as inheriting the legacy layout, and harder to see because it feels like "just following the system."

So decide the **primary composition** the same way §5b decides the band: by the **job**, not by the policy default and not by the legacy render. Answer three questions about the feature:

1. **Selection model** — does the operator *choose the next item by scanning* a list (a worklist's core competency), or is the work *dispensed / pull-based* (the system hands them the next item — a queue, an inbox, a "next task")? If the work is dispensed, a table's scan-to-select competency is dead weight.
2. **Per-item cost** — is the dominant cost *scanning many rows* (favours a table), or a *decision / comparison on one item* that needs width — image, candidates, evidence side-by-side (which a ~400px right-side drawer physically cannot hold at legible size)?
3. **Dominant loop** — does the operator live *in the list* (scan → pick → glance → next), or *in one item at a time* (read → decide → advance)? A one-item loop is served by a focused full-surface composition, not list + drawer.

The three questions above decide list-bearing modes. **For `detail` mode there is no list to select from — the operator is already inside one record — so the fit turns on the record's *interaction verb*, not list-vs-item.** Ask one more question:

4. **Interaction verb (`detail` mode)** — is the record surface's job (a) **data entry** (create / fill a new record), (b) **passive review** (read or confirm an existing record's fields), or (c) **verification against a source** (confirm extracted, imported, OCR'd, or scraped field values against the originating document — an order-confirmation email, a receipt image, a customs PDF, a parsed web page)? For (a) and (b) the grouped-fields record view fits. For (c) the operator's eye must move **value ↔ source**, so the source has to be **co-present** with the fields — which a plain grouped-fields record view does not provide. A verify-against-source surface wants a **source-co-present verification layout** (extracted record and source rendered together, the source sticky), and is therefore `recommended-alt`. The in-system exemplar is the **CDS customs page** (extracted record left / source PDF right, per-line values highlighted on the document). The cost of missing this: a "capture form" that discards the source the moment it is consumed, breaking the verify loop the surface exists for.

Set `{composition_provenance}`:

- **`policy-default`** — the page-mode's default composition fits the job. The common case. (Most operational pages really are scan-to-select worklists; most detail pages really are record views.)
- **`recommended-alt`** — the answers point away from the default: the job wants a different *primary* composition than the policy attaches to this mode. This is a **net-scope / IA recommendation** — surface it to the user for veto before it lands in the brief (one line — "this surface is `{page_mode}`, but its job is {dispensed / comparison-heavy / single-item}; the policy's default {table-first / chart-led / …} doesn't fit — recommend {named composition} as the primary surface, with {the table demoted to a triage view / …}. Use it?"). Handoff recommends; it never silently overrides the policy's composition.

**`composition_provenance` does NOT change `{page_mode}`.** A pull-based mapping/resolution queue is still `operational` — it processes records — but its *composition* may be a single-item decision surface, not a worklist table. The two axes are orthogonal: `{page_mode}` = what kind of work; `{composition_provenance}` = whether the mode's default composition is the right shape for it. Keep `{page_mode}` honest (the work type) and let `{composition_provenance}` carry the composition deviation.

**Capture the reasoning.** Set `{composition_rationale}` to the three answers + the named alt composition + (for `recommended-alt`) the veto outcome (`accepted | declined | pending`), so step-03 §4a renders the override with its justification and the deviation stays auditable. If the three questions genuinely don't resolve, do not silently default — ask the user the one composition question above.

This check applies to every mode but bites differently per mode. `operational` is where the table-first default is most over-applied — questions 1 and 3 decide it. `detail` is `policy-default` for data-entry and passive-review surfaces, but `recommended-alt` when the verb is verification-against-a-source (question 4) — the source must be co-present, which the record-view default does not provide. This is the detail-mode analogue of the operational table-vs-resolve miss, and just as easy to wave through, because the bare record view *feels* like correctly following the system. `analytical` is usually chart-led, but a surface whose real job is a single ranked decision can still warrant `recommended-alt`.

### 5b. Decide Whether an Analytics Band Belongs

**Injected-placement short-circuit (consumability contract).** If `{injected_placement}` is set (passed via `--placement` or by `analytics-placement-triage`), the band decision for this surface was already made upstream by *this same §5b brain* applied at the placement-triage gate. Honor it: `band` / `tab` / `sibling-page` → a band belongs (`{band_provenance}` = `inherited` if the page already shows an analytics surface, else `recommended-new`); `remove-band` → `{band_provenance}` = `recommended-drop`. Stamp the provenance note `injected-by-triage`, verify only that it does not *flatly contradict* the data (if it does, surface the conflict — do not silently override the upstream call), and SKIP the three-question re-derivation below. When `{injected_placement}` is empty (the default), ignore this short-circuit and derive normally.

This is a **design judgment about the data and the user's job — not a detection of what the legacy page renders.** `design-handoff` exists to start the designer from a blank canvas; inheriting band presence/absence from the current layout is the one place that mandate matters most. A bare legacy table sitting on time-series, multi-segment data where the user's real job is "spot which one slipped" *should* get a band even though the current page has none.

So do NOT decide by inspecting the current render. Decide by answering three questions about the feature itself:

1. **Aggregate dimension** — does the data carry a dimension the rows don't expose (time, segment, category, stage, completeness)?
2. **Pattern job** — is part of the user's job pattern / comparison / anomaly / coverage work, rather than pure row-by-row processing?
3. **Changes next action** — would seeing an aggregate layer change what the user does next (which rows they open, which exception they chase)?

If the **pattern job** answer is yes, a band belongs — regardless of whether the legacy page had one.

Set `{band_provenance}` to record *why* the band exists (or doesn't), keeping the blank-canvas reasoning auditable:

- **`inherited`** — the legacy page already had an analytics surface AND the data + job still justify it.
- **`recommended-new`** — the legacy page had no band, but the three questions justify one. This is a **net-new scope recommendation**: surface it explicitly to the user for veto before it lands in the brief (one line — "this feature has no analytics surface today; the data + job warrant one of shape X — include it?"). Handoff recommends; it never silently invents scope.
- **`recommended-drop`** — the legacy page has a band, but the job is pure row-processing and the band is ornamental. Recommend removing it (also veto-surfaced).
- **`none`** — no analytics surface justified. Pure data-entry forms, single-record detail views, settings pages, list-only pages with no aggregate dimension. Section 4b is omitted entirely from the brief.

`{has_analytics_band}` = `true` iff `{band_provenance}` ∈ {`inherited`, `recommended-new`}. When `true`, section 4b (Analytics Structure) MUST be filled in step 3. When `false` (`none` or `recommended-drop`), section 4b is omitted.

`{page_mode}` = "analytical" forces `{has_analytics_band}` = `true` (an analytical page is analytics-led by definition); set `{band_provenance}` to `inherited` or `recommended-new` accordingly.

If the three questions genuinely don't resolve, do not default to a band *or* to none silently — ask the user the one band question above. A guessed band is worse than an asked one.

**Capture the reasoning.** When `{has_analytics_band}` is `true`, set `{band_decision_log}` to the three questions answered for THIS feature — each a one-liner of `yes/no + the specific dimension / job / next-action`, exactly as they'll appear in step-03b §2. If `{band_provenance}` is `recommended-new` or `recommended-drop`, also record the veto outcome (`accepted | declined | pending`) so the rationale can state that the scope recommendation was surfaced, not silently injected.

### 5c. Select the Analytics Archetype

Skip this section entirely if `{has_analytics_band}` is `false` — `{analytics_archetype}` and all the capture fields below stay empty.

**Injected-archetype short-circuit (consumability contract).** If `{injected_archetype}` is set (passed via `--archetype` or by `analytics-placement-triage`, which already selected the shape at the placement-triage gate using *this same* `analytics-surface-architect` skill), do not re-select: set `{analytics_archetype}` = `{injected_archetype}` with provenance `injected-by-triage` and SKIP the `select` invocation below. **Sanity-gate it first (mirroring §5b):** confirm it is one of the nine archetypes and not *flatly* contradicted by the data (e.g. `trend` on data with no time dimension); if it flatly contradicts, surface the conflict rather than silently honoring it. The archetype was already chosen by this same skill upstream, so honor that choice rather than re-deriving it — this threads provenance and avoids the redundant re-derivation. If a rationale artifact is being written (step-03b), populate its supporting fields (candidates / drill-map / prohibited) by invoking the skill in **`explain`** mode around the fixed archetype, OR carry them from the upstream placement-decision artifact — never re-run `select` (that would re-open the choice the gate already made). When `{injected_archetype}` is empty (the default), ignore this short-circuit and select normally below.

When `{has_analytics_band}` is `true`, the archetype selection is delegated to the **`analytics-surface-architect` skill** — the single brain for this decision, so handoff, design-review-pr, and any human all reason the same way instead of re-deriving it. Do not hand-reason the archetype inline when the skill is available.

**Multiple analytics surfaces on one page.** A page can carry more than one distinct analytics surface — e.g. a product view with price-over-time, sales-rank, and competitor-share, which are three surfaces, not one band. When it does, run this selection **once per surface** (each gets its own captured archetype), and **§5e** then ranks them into hero / supporting / drill. For the common single-surface page, run it once exactly as written below.

**Invoke the skill (mode: `select`).** Load `analytics-surface-architect` via the Skill tool and pass it:
- the **data shape** (`{data_shape}` — the domain entities and their dimensions from §3),
- the **user's question** in their words (from `{feature_purpose}` / `{user_context}` — the single thing the band must answer),
- the **page mode** (`{page_mode}`).

The skill runs its selection procedure (start from the question, ground-or-flag, weigh candidates incl. an explicit ruling on `trend` when time is in the data, pick one dominant + at most one subordinate, map every element to a drill target) and returns its **decision object**. Capture it field-for-field — the names already match what step-03b and §4b consume:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `archetype` | `{analytics_archetype}` (one of the nine, or `unclear`) | frontmatter, §4b, rationale |
| `candidates` | `{archetype_candidates}` (chosen / secondary / rejected + why) | rationale §3 table |
| `winner_reason` | `{archetype_winner_reason}` | rationale §3 |
| `secondary` | `{archetype_secondary}` (or `none`) | rationale §3 |
| `time_present_check` | `{time_present_check}` (set iff time in data) | rationale §3 |
| `drill_map` | `{archetype_drill_map}` | §4b C, rationale §3 evidence |
| `prohibited` | `{archetype_prohibited}` | §4b E, rationale §4 |

**Ground-or-flag is preserved through the skill:** if it returns `archetype: unclear` (it could not name BOTH a data dimension and a user question), do NOT default to `trend` — ask the user the one resolving question the skill surfaced, then re-invoke. A guessed archetype is worse than an asked one.

**Fallback (skill not available).** If the `analytics-surface-architect` skill is not present in this project (e.g. an older sync), apply `shared/analytics-archetypes.md`'s selection rule directly — identical logic — and populate the same capture fields by hand: name the dominant archetype from the nine; ground-or-flag (data dimension AND user question, else `unclear` → ask); record the candidates weighed with the most-tempting rejected alternative (for time-bearing data, almost always `trend`); the winner reason; the secondary or `none`; and the time-in-data check. The skill is the preferred path because it makes the road-not-taken and the drill map mandatory outputs rather than easily-skipped prose, but handoff must not hard-fail when it is absent.

Either path populates the same state, so step-03b renders identically. `{analytics_archetype}` empty ⇒ no band.

### 5c-2. Specify the Analytics Rigor — depth, not shape

§5c picked the *shape* of the analytics band; this picks the *depth* of **every decision-bearing figure on the surface** — and depth is **not** confined to the band. A correctly-shaped band can still be schoolboy-grade (every figure a naked point estimate, nothing compared to a baseline, no connective read — *correct and useless*), and so can a **bandless decision surface**: a `detail` buy/verdict page whose hero shows `ROI 42%`, `+£840 est. net profit`, `Headroom 18%` is exactly the case — those are decision numbers in the §4a record/hero, not in any §4b band, and they are the worst schoolboy offenders.

**Gate — `{has_decision_numbers}` (broader than `{has_analytics_band}`).** Set `{has_decision_numbers}` = `true` iff the surface presents one or more figures the user **acts on** — a verdict, recommendation, score, ROI / margin / profit, KPI, or any number that drives the next decision. Concretely:
- `{has_analytics_band}` is `true` → `true` (a band is decision context).
- `{page_mode}` ∈ {`detail`, `analytical`} AND the record/hero/verdict cluster presents figures the user acts on → `true` (this is the lead-detail case the band gate misses).
- A single-item **decision composition** (§5a `recommended-alt`) whose surface is one ranked/scored decision → `true`.
- Pure **data-entry**, **passive-review**, or list-only CRUD with no figure the user acts on → `false`. Rigor does not apply; leave all `{rigor_*}` empty and skip the rest of this section.

**Per surface.** When the page carries multiple analytics/decision surfaces (the §5e gate fired), run this **once per surface**, exactly as §5c does — each surface gets its own rigor spec. For the common single-surface page, run it once.

**Invoke the skill (mode: `spec`).** Load `analytics-rigor` via the Skill tool and pass it:
- the **surface's decision-bearing figures**, wherever they sit (the §4b band's values AND the §4a record/hero/verdict numbers — not just the band),
- the **decision the surface serves**, in the user's words (from `{feature_purpose}` / `{user_context}`),
- the **§5c archetype** if a band exists (the shape it must deepen; omit for a bandless decision surface).

The skill runs its procedure (state the decision; list the decision-bearing numbers; run the eight rigor moves; name the deciding field per series; find the connective read; separate fixes from data gaps; cut ornament) and returns its **rigor decision object**. Capture it field-for-field:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `read_sentence` | `{rigor_read_sentence}` (or `none`) | brief §4d, rationale §3b |
| `decision_numbers` (metric · uncertainty · base_rate) | `{rigor_decision_numbers}` | brief §4d (the design contract `C-RIGOR-01` checks) |
| `deciding_field_check` | `{rigor_deciding_fields}` | brief §4d, `C-RIGOR-01` |
| `data_gaps` | `{rigor_data_gaps}` | brief §4d — surfaced as enrichment requirements |
| `verdict` | `{rigor_verdict}` (analyst-grade / schoolboy / mixed) | brief §4d, rationale §3b |

The rigor spec lands in the **brief §4d** (a surface-level section — it covers decision numbers whether they sit in the band or the record/hero), so it reaches the designer and `C-RIGOR-01` even when there is no band. The rationale §3b additionally records the *reasoning* when a rationale exists (i.e. when `{has_analytics_band}`), parallel to how §3 records the archetype reasoning while the brief carries the conclusion.

**Honesty gate (mirrors §5c's ground-or-flag).** If a required uncertainty or base rate is not computable from the available data, the skill returns it as a `data_gap`, NOT a fabricated figure. Carry the gap into the brief as a data requirement — never instruct the designer to draw a confidence interval the data can't support. **False precision is worse than an honest bare number**; a decorative error bar lies. This is the same honesty posture as the no-silent-fallbacks rule.

**Fallback (skill not available).** Apply the eight rigor moves by hand — lead with the read; no naked decision number; sensitivity to drivers; base rate; deciding field; trend magnitude + dispersion; rank by impact; missing-vs-weak — and populate the same fields. The skill is preferred because it makes the read sentence and per-number uncertainty mandatory outputs rather than skippable prose.

Set `{has_decision_numbers}` and the `{rigor_*}` fields (all empty when `{has_decision_numbers}` is `false`).

### 5c-3. Decision analysis — the executive layer (capital-commitment surfaces only)

Skip unless the surface is a **capital decision** — its primary job is to commit a scarce resource (capital, inventory slots, time) under uncertainty with a real downside (a buy / reorder / sizing / go-no-go-with-stake). This is **narrower than §5c-2**: a coverage strip, a trend dashboard, or a status worklist carries decision *numbers* but commits nothing — it stops at rigor. Set `{is_capital_decision}` accordingly; when `false`, leave all `{decision_*}` empty and skip the rest of this section.

§5c-2 made the figures honest (senior-analyst grade); this models and sizes the *decision* (executive / quant-desk grade). A surface can pass rigor — honest ranges, named gaps — and still leave the operator to decide how much to bet and whether the downside is survivable. Closing that is a distinct discipline.

**Invoke the skill (mode: `spec`).** Load `decision-analysis` via the Skill tool and pass it:
- the **commitment the surface serves** — action · stake (capital at risk) · horizon · downside,
- the **rigor figures** from §5c-2 (the honest inputs it builds the decision on),
- the **data sources** for the uncertain inputs (live data, an owned-history reference class, or absent).

The skill runs its procedure (frame the bet; model the outcome distribution; size to the loss tail; find the breakeven driver; compute the reference class; weight the decision-relevant regime; state the value-of-information gap; decide under asymmetry) and returns its **decision object**. Capture it field-for-field:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `frame` (action · stake · horizon · payoff) | `{decision_frame}` | brief §4e, rationale §3c |
| `outcome` (method · P(success) · EV · P10 · P90) | `{decision_outcome}` | brief §4e (the design contract `C-DECISION-01` checks) |
| `sizing` (quantity · basis · downside_survived) | `{decision_sizing}` | brief §4e, `C-DECISION-01` |
| `sensitivity` (swing driver · breakeven threshold) | `{decision_sensitivity}` | brief §4e, `C-DECISION-01` |
| `reference_class` / `regime` / `value_of_info` / `asymmetry` | `{decision_context}` | brief §4e, rationale §3c |
| `gaps` | `{decision_gaps}` | brief §4e — surfaced as enrichment requirements |
| `verdict` | `{decision_verdict}` (decision-grade / risk-modelled / single-scenario) | brief §4e, rationale §3c |

**Model-honesty gate (paramount — outranks the rest).** If the key probabilistic input is missing AND no reference class is computable, the skill returns `verdict: single-scenario` with the VOI gap — NOT a fabricated outcome distribution. Carry that honestly into the brief: an honest single-scenario read plus the named gap, never a confident P(success) off an invented win-rate. A fake distribution is worse than an honest point estimate. Same honesty posture as §5c-2 and the no-silent-fallbacks rule.

**Per surface.** On a page with more than one capital decision, run once per decision surface.

**Fallback (skill not available).** Apply the eight decision moves by hand — frame the bet; model the outcome distribution; size to the loss tail; breakeven driver; compute the reference class; weight the regime; value of information; asymmetry — and populate the same fields.

Set `{is_capital_decision}` and the `{decision_*}` fields (all empty when `{is_capital_decision}` is `false`).


---

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01c-topology.md`
