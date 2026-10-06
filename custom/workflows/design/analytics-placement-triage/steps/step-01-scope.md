---
name: 'step-01-scope'
description: 'Resolve the target operational page, the analytics dataset and question, and any existing band — halt if intent cannot be grounded'
---

# Step 1: Scope the Placement Question

**Progress: Step 1 of 4** — Next: Assess (autonomous)

## RULES — read before acting

- **GROUNDING GATE (intent autonomy boundary).** You must be able to name BOTH the **target page** and the **analytics question** from the input alone. If either is missing, HALT and ask — do NOT guess the page or invent the analytics job. This gate fires even under `autonomous_mode` (decision autonomy ≠ intent autonomy).
- This step only *scopes*. Do NOT decide placement here, do NOT run the §5b/§5d/§5e brains here — that is step-02.
- Read the page component ONLY to confirm the route + dataset + any existing band. Do not summarize its layout.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Ground the target page

From the input, resolve `{target_route}` — the operational page the analytics attaches to (e.g. `/orders`). Confirm it is an **operational** surface (a worklist the operator processes). If the input names no route, or the route is an analytical/detail page (placement is not the open question there), HALT with:

> *"Analytics-placement-triage needs an OPERATIONAL page to attach analytics to. Name the worklist route (e.g. /orders) and what the analytics should answer."*

Locate the rendering component and store its path as `{target_component}` (one `find`/grep is enough — do not deep-read).

### 2. Ground the analytics question and dataset

Capture `{analytics_question}` — the single thing the analytics must answer, **in the user's words** (e.g. "where is capital tied up and which lanes are slipping over time?"). If the input gives no analytics job, HALT and ask (grounding gate).

Capture `{analytics_dataset}` — the entities the analytics reads and the **aggregate dimension** they carry that the worklist rows don't expose (time, lane, supplier, status, completeness). Walk this from the data the page already loads; do not invent fields.

### 3. Detect any existing analytics surface

Inspect the page for a primitive analytics surface already present (a summary strip, a coverage band, a counts row — e.g. the /orders capital-at-risk band). Record it as `{existing_band}` (one line: what it shows and where), or `none`. This matters because §5b can resolve `inherited` (keep/upgrade it) vs `recommended-new` (there was nothing).

### 4. Confirm scope and proceed

Confirm the scoped inputs in one short paragraph (not a menu):

```
Scoped: analytics for {target_route} ({target_component}).
Question: "{analytics_question}".
Dataset: {analytics_dataset}. Existing surface: {existing_band}.
Assessing placement now.
```

Then read fully and follow: `{project-root}/_bmad/bmm/workflows/design/analytics-placement-triage/steps/step-02-assess.md` (chain: 02-assess → 03-shape → 04-route).

---

## SUCCESS METRICS

- `{target_route}`, `{target_component}`, `{analytics_question}`, `{analytics_dataset}`, `{existing_band}` all populated
- The target is confirmed operational (not analytical/detail)
- Halted cleanly if the page or the analytics question could not be grounded from the input

## FAILURE MODES

- Guessing a target route or inventing the analytics job instead of halting (intent-autonomy violation)
- Summarizing the page's current layout (not this step's job, and biases the downstream brains)
- Deciding placement here instead of in step-02
