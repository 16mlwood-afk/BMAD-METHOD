---
name: 'step-01-intake'
description: 'Accept the raw observation, classify input type, extract page/feature context, formulate investigation plan'

nextStepFile: './step-02-investigate.md'
---

# Step 1: Intake

**Goal:** Normalize whatever the user gave you — screenshot, error text, vague concern — into a structured observation with enough context to begin investigation.

---

## STATE VARIABLES (set in this step)

- `{observation}` — normalized description of what the user reported
- `{observation_type}` — classification (see table below)
- `{page_context}` — which page, route, feature, or system area the observation relates to
- `{investigation_plan}` — list of specific queries and code reads to perform in step 2

---

## EXECUTION SEQUENCE

### 1. Classify the Observation

Read the user's input and classify it:

| Type | Signal | Example |
|------|--------|---------|
| `error-count` | A number paired with a failure/error state — banner, badge, status count | "37 invoices failed extraction", screenshot showing error count |
| `error-message` | A specific error string or stack trace | "FOREIGN KEY constraint failed", a pasted log line |
| `unexpected-state` | Data that doesn't match expectations — wrong values, missing fields, stuck records | "This column is always empty", "these orders show £0" |
| `ui-concern` | Something about the interface feels wrong but isn't a data error | "I can't tell which invoices need attention", "this page is confusing" |
| `silent-failure` | Something should have happened but didn't — no error, just absence | "I uploaded invoices yesterday but nothing processed", "the cron didn't run" |
| `performance` | Slowness, timeouts, resource issues | "This page takes 10 seconds to load", "the export times out" |
| `vague` | Insufficient context to classify — needs one clarifying question | "Something's broken", "things don't look right" |

Store as `{observation_type}`.

**If `vague`:** Ask ONE question — "Which page or feature are you looking at?" — then reclassify with the response. Do not ask more than one question.

### 2. Extract Page Context

Identify what part of the system the observation relates to:

**From screenshots:**
- Read the URL bar if visible (e.g., `/invoices`, `/queries/123`)
- Read page headings, breadcrumbs, tab labels
- Note the current filter/view state (period selector, active tab, search query)

**From text:**
- Look for route references, page names, feature names
- Look for table/entity names (invoices, orders, queries, expenses)
- Look for process names (extraction, classification, reconciliation, sync)

**From error messages:**
- Extract the error code prefix if present (e.g., `[EXTRACTION_PDF_NOT_FOUND]`)
- Identify which system produced the error (OCR pipeline, Xero sync, DB constraint)

Store as `{page_context}` — include route, entity, and any visible filter state.

### 3. Normalize the Observation

Write a structured one-paragraph summary:

```
{observation}: "{user's symptom in plain language}. Observed on {page/route} with {filter state if any}. 
Classification: {observation_type}. Context: {any additional details extracted from screenshot or text}."
```

### 4. Formulate Investigation Plan

Based on `{observation_type}`, plan the investigation queries for step 2:

| Type | Investigation approach |
|------|----------------------|
| `error-count` | Query the relevant table for status distribution. Break down errors by error_message, supplier/source, batch, and time range. Look for clustering. |
| `error-message` | Find the error string in the codebase (grep). Trace the code path that produces it. Query the DB for how many records have this error. |
| `unexpected-state` | Query the table for the field in question. Check if the value is missing at the source (DB), in transport (API), or in rendering (UI component). |
| `ui-concern` | Read the page component. Check what data is available (from the loader/API) vs what's rendered. Check if relevant data exists in the DB but isn't surfaced. |
| `silent-failure` | Check the processing pipeline — cron history, queue status, recent activity. Query for records stuck in intermediate states. Check error logs. |
| `performance` | Check data volumes, query patterns, index coverage. Look for N+1 queries, missing pagination, or unbounded fetches. |

Store the plan as `{investigation_plan}` — a numbered list of specific queries and file reads.

---

## PRESENT INTAKE SUMMARY

Before proceeding, briefly state what you understood:

```
**Triaging:** {one-line observation summary}
**Context:** {page/route/feature}
**Classification:** {observation_type}
**Investigating:** {2-3 line summary of investigation plan}
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/triage/steps/step-02-investigate.md`.

---

## SUCCESS METRICS

- Observation classified into a specific type (not left as `vague`)
- Page/feature context extracted — route, entity, or process identified
- Investigation plan has specific, actionable queries — not "look at the database"
- Summary presented to the user so they know the workflow understood their input

## FAILURE MODES

- Asking the user what they want instead of investigating
- Classifying everything as `vague` and asking multiple clarifying questions
- Formulating an investigation plan that's too generic ("check the code") instead of specific ("query invoices table grouped by error_message")
- Skipping the screenshot analysis — URL bar, page headings, and filter state contain critical context
- Jumping to a fix without investigating first
