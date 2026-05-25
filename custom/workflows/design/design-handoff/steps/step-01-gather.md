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

### 1b. Load Brand Identity

```bash
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

**If found:**
- Read the entire file → `{brand_identity}`
- Set `{brand_identity_path}` to the absolute path
- Set `{design_system}` = "branded"

**If not found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty
- Set `{design_system}` = "existing" (may be overridden to "external" by user input)

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

1. **Open the DB schema** (`src/lib/server/db/schema.ts` or equivalent). Find the tables this feature reads from.
2. **For each entity**, list its columns: name, type, nullability. These are the primitive fields.
3. **Stop. Do NOT open `+page.server.ts` to get the data shape.** The page server denormalizes, groups, pre-computes, and adds rendering hints — all of which bias the designer. If you need to know which entities the feature uses, check the page server's imports or queries, but do NOT copy its return type.
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

**Signals for analytical:** user goals center on "understand", "compare", "spot trends", "review performance", "analyze", "diagnose", or the data has time-series dimensions and the user's job is pattern discovery rather than row processing.

**Hybrid handling:** Some pages mix both modes.
- If analysis exists to support immediate row-level action (e.g., a summary chart above a worklist), keep the page in **operational** mode.
- If row-level detail exists mainly to verify or explain summarized behavior (e.g., a trend chart with a drill-down table), keep the page in **analytical** mode.
- The dominant user task determines the mode — not the presence of a chart or a table.

If unclear, default to "operational."

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
- `{page_mode}` ✓ ("operational" or "analytical")
- `{user_context}` ✓
- `{brand_identity}` ✓ (may be empty)
- `{design_system}` ✓ ("branded", "existing", or "external")

Then load and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md`
