---
name: 'step-01-gather'
description: 'Gather feature purpose, data model, API surface, and user context — without capturing current layout or component structure'
---

# Step 1: Gather Feature Context (Bias-Free)

**Goal:** Extract the raw materials a designer needs — data model, user purpose, API surface, constraints — without describing the current UI's layout, information grouping, or visual hierarchy.

---

## RULES

- **NEVER describe the current page layout, component structure, or information grouping.** The current UI was built by a developer. Describing it anchors the designer to implementation choices.
- Read component files ONLY to extract data types, API calls, and route paths — NOT to summarize what sections the page shows.
- Focus on WHAT DATA is available and WHO needs it — not HOW it is currently presented.
- Present all data fields neutrally. Do NOT rank fields as "prominent" or "secondary."
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## EXECUTION SEQUENCE

### 1. Resolve Repository URL

Capture `{github_repo_url}`:

```bash
git remote get-url origin
```

Convert SSH URLs to HTTPS. Strip trailing `.git`.

### 1b. Load Project Design Policy

Check both possible locations for a project-level design system declaration. `docs/design-policy.md` is the canonical location; `planning-artifacts/brand-identity.md` is the legacy slot. Prefer the first if both exist.

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

**If either is found:**
- Read the entire file → `{brand_identity}` (variable name retained for backward compatibility)
- Set `{brand_identity_path}` to the absolute path of whichever file was loaded
- Set `{design_system}` = "branded"
- Parse the frontmatter `version:` field of the loaded file → `{policy_version}` (integer). If no version field exists, default to `1`. This value is stamped into the generated brief's `policy_version_required` field in step-03 so downstream consumers can detect when the policy has moved past the brief's pinned version.

**If neither is found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty
- Set `{design_system}` = "existing" (may be overridden to "external" by user input)
- Set `{policy_version}` = `0` (sentinel meaning "no policy in effect at brief time"; downstream consumers treat this as "no drift check possible — surface to user").

### 2. Identify the Feature

Determine `{feature_name}` and `{feature_scope}` from user input or recent git history:

```bash
git log --oneline -10
git diff --name-only HEAD~3..HEAD
```

Set `{feature_scope}`:
- **"new"** — component file was created (not modified) in recent commits
- **"redesign"** — component exists and user wants it redesigned

### 3. Map the Data Surface

**Route:**
- What URL path does this feature live at?
- Note the route path — NOT the component that renders at it

**Data Model — Procedural Capture (anti-bias):**

Follow these steps in order. The goal is to capture domain entities from the source of truth (DB schema), not from the page server's UI-shaped response.

1. **Open the DB schema** at the project's source of truth. Common locations: `src/lib/server/db/schema.ts` (Drizzle), `prisma/schema.prisma` (Prisma), `app/models/` (Rails), `models.py` (Django), `migrations/*.sql` (raw SQL), or equivalent. Find the tables this feature reads from.
2. **For each entity**, list its columns: name, type, nullability. These are the primitive fields.
3. **Stop. Do NOT open the page-shaped server response file to get the data shape.** Examples: `+page.server.ts` (SvelteKit), `getServerSideProps` or route `loader` (Next.js), controller action (Rails), view function (Django/Flask), GraphQL resolver, etc. These denormalize, group, pre-compute, and add rendering hints — all of which bias the designer. If you need to know which entities the feature uses, check the file's imports or queries, but do NOT copy its return type.
4. **Flatten any nested structures.** If the schema has a foreign key (e.g., `supplier_country` on an invoice), that's a flat field on the row — not a grouping dimension. Record it as a field.
5. **Drop anything not in the schema:**
   - Pre-computed derivations (`daysLeft`, `totalNet`, `filingProgress`, etc.) — keep only the inputs (deadline date, money amount, status enum)
   - Rendering hints (`flag`, `badgeColor`, emoji fields) — keep only the underlying data (`countryCode`, status enum)
   - UI-control enums (`'all' | 'not_filed' | 'ready'`) — "all" is a filter affordance, not data. Keep only the row-level status enum.
   - Precomputed rollups (`domesticCount`, `countryTotal`, `validCount`) — the designer decides which aggregations matter.
6. **Note which primitive fields are nullable** — these need empty-state treatment.

Capture `{data_shape}` in **domain-entity table form** (see step-03 template). If you find yourself copy-pasting `interface PageData { ... }`, you've gone off track.

**API Surface:**
- What endpoints does the frontend call? → `{api_surface}`
- What does each response look like? (reference the data shape)
- What mutations are available? (POST/PUT/DELETE endpoints)

**Implementation Files:**
- List relevant file paths → `{implementation_files}`
- Include: type definitions, API route handlers, the main page component path, CSS/style files
- These are for technical reference, NOT layout reference

### 4. Capture Feature Purpose

Write `{feature_purpose}`:

```
Feature: {feature_name}
Route: /path
Scope: new | redesign
Purpose: [1-2 sentences: what problem does this solve for the user?]
Data source: GET /api/endpoint → domain entities (see {data_shape})
User goals: [domain outcomes, NOT UI clicks.
  GOOD: "spot countries near deadline", "answer 'what's blocking filing today?'"
  BAD:  "click bulk-mark filed", "switch the active quarter"]
Data volume: [typical count — "usually 10-50 items", "1,400+ records per quarter"]
```

Do NOT include "Main component", "Child components", "Current sections", "Current tabs", or "Key interactions." Do NOT phrase user goals as UI actions.

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

Set `{composition_provenance}`:

- **`policy-default`** — the page-mode's default composition fits the job. The common case. (Most operational pages really are scan-to-select worklists; most detail pages really are record views.)
- **`recommended-alt`** — the answers point away from the default: the job wants a different *primary* composition than the policy attaches to this mode. This is a **net-scope / IA recommendation** — surface it to the user for veto before it lands in the brief (one line — "this surface is `{page_mode}`, but its job is {dispensed / comparison-heavy / single-item}; the policy's default {table-first / chart-led / …} doesn't fit — recommend {named composition} as the primary surface, with {the table demoted to a triage view / …}. Use it?"). Handoff recommends; it never silently overrides the policy's composition.

**`composition_provenance` does NOT change `{page_mode}`.** A pull-based mapping/resolution queue is still `operational` — it processes records — but its *composition* may be a single-item decision surface, not a worklist table. The two axes are orthogonal: `{page_mode}` = what kind of work; `{composition_provenance}` = whether the mode's default composition is the right shape for it. Keep `{page_mode}` honest (the work type) and let `{composition_provenance}` carry the composition deviation.

**Capture the reasoning.** Set `{composition_rationale}` to the three answers + the named alt composition + (for `recommended-alt`) the veto outcome (`accepted | declined | pending`), so step-03 §4a renders the override with its justification and the deviation stays auditable. If the three questions genuinely don't resolve, do not silently default — ask the user the one composition question above.

This check applies to every mode but bites hardest on `operational` (the table-first default is the most over-applied). For `detail`, the record-view default almost always fits (`policy-default`). For `analytical`, chart-led usually fits, but a surface whose real job is a single ranked decision can still warrant `recommended-alt`.

### 5b. Decide Whether an Analytics Band Belongs

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

When `{has_analytics_band}` is `true`, the archetype selection is delegated to the **`analytics-surface-architect` skill** — the single brain for this decision, so handoff, design-review-pr, and any human all reason the same way instead of re-deriving it. Do not hand-reason the archetype inline when the skill is available.

**Invoke the skill (mode: `select`).** Load `analytics-surface-architect` via the Skill tool and pass it:
- the **data shape** (`{data_shape}` — the domain entities and their dimensions from §3),
- the **user's question** in their words (from `{feature_purpose}` / `{user_context}` — the single thing the band must answer),
- the **page mode** (`{page_mode}`).

The skill runs its selection procedure (start from the question, ground-or-flag, weigh candidates incl. an explicit ruling on `trend` when time is in the data, pick one dominant + at most one subordinate, map every element to a drill target) and returns its **decision object**. Capture it field-for-field — the names already match what step-03b and §4b consume:

| Skill output field | Capture into | Consumed by |
|---|---|---|
| `archetype` | `{analytics_archetype}` (one of the eight, or `unclear`) | frontmatter, §4b, rationale |
| `candidates` | `{archetype_candidates}` (chosen / secondary / rejected + why) | rationale §3 table |
| `winner_reason` | `{archetype_winner_reason}` | rationale §3 |
| `secondary` | `{archetype_secondary}` (or `none`) | rationale §3 |
| `time_present_check` | `{time_present_check}` (set iff time in data) | rationale §3 |
| `drill_map` | `{archetype_drill_map}` | §4b C, rationale §3 evidence |
| `prohibited` | `{archetype_prohibited}` | §4b E, rationale §4 |

**Ground-or-flag is preserved through the skill:** if it returns `archetype: unclear` (it could not name BOTH a data dimension and a user question), do NOT default to `trend` — ask the user the one resolving question the skill surfaced, then re-invoke. A guessed archetype is worse than an asked one.

**Fallback (skill not available).** If the `analytics-surface-architect` skill is not present in this project (e.g. an older sync), apply `shared/analytics-archetypes.md`'s selection rule directly — identical logic — and populate the same capture fields by hand: name the dominant archetype from the eight; ground-or-flag (data dimension AND user question, else `unclear` → ask); record the candidates weighed with the most-tempting rejected alternative (for time-bearing data, almost always `trend`); the winner reason; the secondary or `none`; and the time-in-data check. The skill is the preferred path because it makes the road-not-taken and the drill map mandatory outputs rather than easily-skipped prose, but handoff must not hard-fail when it is absent.

Either path populates the same state, so step-03b renders identically. `{analytics_archetype}` empty ⇒ no band.

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
- `{api_surface}` ✓
- `{implementation_files}` ✓
- `{page_mode}` ✓ ("operational", "analytical", or "detail")
- `{composition_provenance}` ✓ (`policy-default` | `recommended-alt`; decided in §5a from the job, NOT inherited from the policy default; `recommended-alt` veto-surfaced and `{composition_rationale}` captured) — and `{page_mode}` stays the honest work type even when composition deviates
- `{band_provenance}` ✓ (`inherited` | `recommended-new` | `recommended-drop` | `none`; net-new/drop recommendations veto-surfaced)
- `{has_analytics_band}` ✓ (`true` iff band_provenance ∈ {inherited, recommended-new})
- `{analytics_archetype}` ✓ (one of the eight, or `unclear` → asked; empty when no band)
- **Analytics reasoning capture** ✓ (populated iff `{has_analytics_band}` is `true`; all empty otherwise) — `{page_mode_rationale}`, `{band_decision_log}`, and the archetype decision object captured from the `analytics-surface-architect` skill in §5c: `{archetype_candidates}`, `{archetype_winner_reason}`, `{archetype_secondary}`, `{time_present_check}`, `{archetype_drill_map}`, `{archetype_prohibited}`. These feed the rationale artifact (step-03b) and §4b; capturing the deliberation here is what makes the presentation decision auditable instead of discarded.
- `{user_context}` ✓
- `{brand_identity}` ✓ (may be empty)
- `{design_system}` ✓ ("branded", "existing", or "external")
- `{handoff_mode}` ✓ ("fresh-design" or "refine-screen")
- If `{handoff_mode}` = "refine-screen": `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}` ✓ (loaded by workflow.md before this step)

**Refine-screen mode reminder:** Do NOT ask the user "what feels wrong?" or "what are the top issues?" — those came from the artifact loaded in workflow.md. The user-context question (who uses this, how often) is still valid; the diagnostic question is not.

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md`
