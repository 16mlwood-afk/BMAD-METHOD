---
name: 'step-01-gather'
description: 'Gather feature purpose, data model, API surface, and user context — without capturing current layout or component structure'
---

# Step 1: Gather Feature Context (Bias-Free)

**Goal:** Extract the raw materials a designer needs — data model, user purpose, API surface, constraints — without describing the current UI's layout, information grouping, or visual hierarchy.

---

## RULES

- **NEVER describe the current page layout, component structure, or information grouping.** The current UI was built by a developer, not a designer. Describing it anchors the designer to implementation choices instead of letting them create their own vision.
- DO NOT read component JSX to summarize what sections the page currently shows — that's the bias vector. Read component files ONLY to extract data types, API calls, and route paths.
- Focus on WHAT DATA is available and WHO needs it — not HOW it is currently presented.
- Capture the data shape precisely (TypeScript interfaces / Python models) — designers need to know what fields exist.
- Present all data fields neutrally. Do NOT rank fields as "prominent" or "secondary" — that's a design decision.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## EXECUTION SEQUENCE

### 1. Resolve Repository URL

Capture `{github_repo_url}` — Claude Design needs this to connect to the repo:

```bash
git remote get-url origin
```

Convert SSH URLs to HTTPS format if needed (e.g., `git@github.com:org/repo.git` → `https://github.com/org/repo`). Strip the trailing `.git`.

### 2. Identify the Feature

Determine `{feature_name}` and `{feature_scope}` from user input or recent git history:

```bash
# If no explicit input, check recent commits
git log --oneline -10
git diff --name-only HEAD~3..HEAD  # files changed recently
```

Set `{feature_scope}`:
- **"new"** — component file was created (not modified) in recent commits
- **"redesign"** — component exists and user wants it redesigned

### 3. Map the Data Surface

For the identified feature, collect:

**Route:**
- What URL path does this feature live at?
- Note the route path — NOT the component that renders at it

**Data Model (CRITICAL):**
- Find the TypeScript interface(s) or Python model(s) that define what data the UI can render
- Capture the FULL interface definition as `{data_shape}`
- Note which fields are nullable (need empty state handling), which are arrays (need list/collection handling), which are computed
- **Do NOT annotate which fields are "important" or "primary"** — present them all equally

**API Surface:**
- What endpoints does the frontend call? List as `{api_surface}`
- What does each response look like? (reference the data shape)
- What mutations are available? (POST/PUT/DELETE endpoints)

**Implementation Files:**
- List relevant file paths as `{implementation_files}` — these are for the designer's reference if they want to dig into technical details, NOT for understanding the current layout
- Include: type definitions, API route handlers, the main page component path, CSS/style files

### 4. Capture Feature Purpose

Write `{feature_purpose}` — what the feature DOES, not how it LOOKS:

```
Feature: {feature_name}
Route: /path
Scope: new | redesign
Purpose: [1-2 sentences: what problem does this solve for the user?]
Data source: GET /api/endpoint → TypeInterface
Available mutations: [list of actions the user can take — e.g., "create", "delete", "filter", "export"]
Data volume: [typical count — "usually 10-50 items", "single detail view", etc.]
```

**WARNING:** Do NOT include "Main component", "Child components", "Current sections", or "Key interactions" — these describe the current implementation, not the requirements. The designer decides what components, sections, and interaction patterns to use.

### 5. Identify User Context

Set `{user_context}` — WHO uses this and WHY:

- What role uses this page? (e.g., "wholesale buyer sourcing distributors")
- What's the job-to-be-done? (e.g., "track outreach attempts, know who to follow up with")
- How often? (daily tool vs. occasional reference)
- What's the emotional state? (urgent task vs. exploratory browsing)

If this can't be determined from code, ask the user ONE question:
> "Who uses this and what are they trying to accomplish?"

---

## COMPLETION

Confirm the following state variables are populated:
- `{github_repo_url}` ✓
- `{feature_name}` ✓
- `{feature_scope}` ✓
- `{feature_purpose}` ✓
- `{data_shape}` ✓
- `{api_surface}` ✓
- `{implementation_files}` ✓
- `{user_context}` ✓

Then load and follow: `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/design-handoff/steps/step-02-audit-design.md`
