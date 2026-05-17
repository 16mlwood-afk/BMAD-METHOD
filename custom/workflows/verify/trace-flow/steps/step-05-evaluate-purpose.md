---
name: 'step-05-evaluate-purpose'
description: 'Product-level intelligence layer — evaluates what data SHOULD be surfaced given the pages purpose, not just what IS wired correctly'

nextStepFile: './step-06-suggest-ui.md'
---

# Step 5: Evaluate Purpose

**Goal:** Step back from the mechanical wiring audit and think about this page as a product. Given what this page is FOR — what decision does the user make here, what workflow does it support — evaluate whether the right data is being surfaced. Identify data that EXISTS upstream but isn't shown, and assess whether surfacing it would help the user.

**Why this step exists:** The trace-flow audit (step 4) answers "is the wiring correct?" This step answers "is the right data being shown?" Dead fields get flagged for removal by the audit — but some of those fields might actually be valuable if surfaced properly. And there may be data in the DB or upstream services that never enters the pipeline at all but would serve the page's purpose.

---

## AVAILABLE STATE

From previous steps:

- `{anchor}` — The anchor point (page, endpoint, component)
- `{anchor_type}` — Classification
- `{stages}` — Ordered pipeline stages with shape in/out
- `{live_data}` — Captured data values at each stage
- `{gaps}` — Audit findings from step 4
- `{stack}` — Project stack

## STATE VARIABLES (set in this step)

- `{page_purpose}` — One-sentence statement of the page's purpose
- `{user_decisions}` — What decisions the user makes on this page
- `{available_not_shown}` — Fields available upstream but not rendered
- `{recommendations}` — Product-level suggestions for what to add/surface

---

## EXECUTION SEQUENCE

### 1. Identify the Page's Purpose

Read the page holistically — not just the data pipeline, but the UI layout, headings, actions, and navigation context. Answer:

- **What is this page FOR?** (e.g., "Verify UK VAT return figures before filing", "Monitor invoice processing pipeline", "Review and approve supplier invoices")
- **What decisions does the user make here?** (e.g., "Confirm Box 4/7 totals are correct", "Decide which invoices need manual review", "Trigger the quarterly filing")
- **What would make the user CONFIDENT in their decision?** (e.g., "Seeing the VAT rate per invoice to spot-check calculations", "Knowing which invoices have verified IFD evidence vs estimates")

Store these as `{page_purpose}` and `{user_decisions}`.

### 2. Inventory Available-but-Not-Shown Data

Compare the full schema (source stage) against what reaches the render stage. For each field that exists in the DB but isn't rendered:

**Categorize:**

| Category | Description | Example |
|----------|-------------|---------|
| **Available upstream, never queried** | Column exists in DB table but the page's query doesn't select it | `supplier_country` exists but isn't in the SELECT |
| **Queried but dropped** | Selected from DB but filtered out before reaching the UI | `order_number` used for joins then discarded |
| **Reaches client, not rendered** | In the SSR payload but no component reads it | `totalAmount` serialized but never displayed |
| **Available via related table** | Not on the primary table but joinable | `order_summaries.raw_html` available but not linked from the invoice row |
| **Available via API/service** | Could be fetched from an external source | Exchange rate history from HMRC, filing deadline from AVASK |

List these in a structured inventory. Don't list every column — focus on fields that are plausibly relevant to `{page_purpose}`.

### 3. Evaluate Each Candidate

For each available-but-not-shown field, evaluate:

| Question | What to assess |
|----------|----------------|
| **Does it serve the page's purpose?** | Would seeing this help the user make their decision or increase confidence? |
| **Is there a user story?** | Can you articulate WHO wants to see this and WHY? |
| **Is it verifiable from context?** | Could the user cross-check this value against something else they know? |
| **What's the cost of NOT showing it?** | Does the user have to go elsewhere to find this? |
| **Is it noise for most views?** | Would it clutter the default view? Should it be behind an expand/detail/tooltip? |

Score each candidate:

- **High value:** Directly supports the page's purpose, users would want it on every visit
- **Medium value:** Useful for some workflows or occasionally needed for verification
- **Low value:** Nice to have but adds clutter; better in a detail view or export
- **No value:** Truly irrelevant to this page's purpose — correct to omit

### 4. Cross-Reference with Audit Findings

Review the step-4 audit findings through the product lens:

- **Dead fields flagged for removal:** Are any of them actually HIGH or MEDIUM value? If so, the recommendation should be "surface properly" not "remove."
- **Missing display findings:** Upgrade the recommendation from "field not rendered" to a specific suggestion of WHERE and HOW to render it.
- **Fields currently shown:** Are any LOW value and adding noise? Could they be moved to an expand/detail view?

### 5. Check Adjacent Pages

Briefly check what related pages show. If there's data surfaced on page X that would also serve this page's purpose:

```bash
# Find related pages (same feature area, linked from navigation)
grep -rn "{page_route}" src/routes --include="*.svelte" | head -5
```

Look for patterns like:
- A detail page shows a field that the list page omits
- An export includes columns that the UI doesn't show (the export might be compensating for a UI gap)
- A different page shows the same data with additional context

### 6. Produce Recommendations

For each HIGH or MEDIUM value candidate, produce a concrete recommendation:

```
### {n}. Surface {field_name} — {value_level}

**User story:** As a {role}, I want to see {field} on the {page} so I can {reason}.
**Where:** {Specific UI location — e.g., "Add column to invoice table", "Show in IFD breakdown expand"}
**Data source:** {Where it comes from — already in query, needs join, needs new fetch}
**Effort:** {trivial | small | medium}
**Trade-off:** {What clutter this adds, and whether it should be default-visible or behind an interaction}
```

For fields confirmed as NO VALUE, explicitly state why omission is correct — this prevents the next trace-flow from re-flagging them.

---

## APPEND TO PIPELINE DOCUMENT

Add a `## Purpose Evaluation` section to the pipeline document (after `## Audit Findings`):

```markdown
## Purpose Evaluation

**Page purpose:** {one-sentence purpose}
**User decisions:** {what the user decides here}

### Available but not surfaced

| Field | Category | Value | Recommendation |
|-------|----------|-------|----------------|
| {field} | {category} | {high/medium/low/none} | {one-line action} |

### Product Recommendations

{Numbered list of HIGH/MEDIUM value recommendations with user stories}

### Confirmed Omissions

{Fields that are correctly NOT shown, with brief rationale — prevents re-flagging}
```

---

## INTERACTION WITH AUDIT FINDINGS

This step may **override** audit step-4 recommendations:

- If step 4 said "remove dead field X" but step 5 says "X is HIGH value, surface it" → the recommendation becomes "surface X properly" (add UI), not "remove X from the query"
- If step 4 found no issues but step 5 identifies valuable unsurfaced data → the pipeline has a product gap even though it's technically clean
- If step 5 confirms all omissions are correct → the audit recommendations from step 4 stand as-is

When overriding, update the audit section with a note: `**Overridden by purpose evaluation:** recommend surfacing, not removing.`

---

## AUTONOMOUS MODE BEHAVIOR

In autonomous mode:
- Make product-level judgments based on the page's apparent purpose and the user's role (from project context/memory)
- Default to recommending surface for HIGH value fields, noting for MEDIUM, omitting for LOW/NONE
- Do not halt for product decisions — assess and recommend

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/trace-flow/steps/step-06-suggest-ui.md` — evaluate whether this pipeline would benefit from a user-facing visualization component.

---

## SUCCESS METRICS

- Page purpose clearly articulated (not just "shows data")
- User decisions identified (what the user DOES with this page)
- Available-not-shown inventory covers DB, joins, and related services
- Each candidate evaluated against the page's purpose with a clear value score
- Recommendations are concrete (user story + where + effort), not vague
- Audit findings cross-referenced — dead field recommendations potentially overridden
- Adjacent pages checked for patterns and opportunities
- Confirmed omissions documented to prevent re-flagging

## FAILURE MODES

- Treating every available field as "should be shown" (not everything is relevant)
- Not identifying the page's purpose (just listing fields without product context)
- Recommending additions without considering clutter/noise trade-offs
- Accepting all audit "remove" recommendations without product evaluation
- Being too conservative ("everything is fine as-is") without genuinely considering the user's workflow
- Not checking adjacent pages (missing obvious parity opportunities)
- Vague recommendations ("maybe show more data") instead of specific user stories with locations

---

## RECORD DECISIONS

After producing recommendations, persist all findings to the decisions file at `{implementation_artifacts}/flow-trace-decisions.yaml`. This enables the feedback loop — the next trace-flow on this anchor won't re-flag resolved items.

### File Format

```yaml
# flow-trace-decisions.yaml
# Auto-maintained by trace-flow workflow. Do not edit manually.

anchor: "{anchor}"
last_traced: "{date}"

decisions:
  - field: "totalAmount"
    category: "dead-field"
    status: "resolved"
    action: "removed"
    resolved_date: "2026-05-17"
    pr: "#353"
    reason: "Only consumer (client CSV export) was removed in PR #344"

  - field: "vatRate"
    category: "dead-field"
    status: "resolved"
    action: "removed"
    resolved_date: "2026-05-17"
    pr: "#353"
    reason: "Same as totalAmount — orphaned by CSV export removal"

  - field: "supplier_country"
    category: "available-not-queried"
    status: "keep-omitted"
    reason: "Not relevant to UK VAT return verification — correct omission"
    decided_date: "2026-05-17"

  - field: "vat_reclaim_method"
    category: "available-not-shown"
    status: "pending"
    value_score: "medium"
    recommendation: "Surface in IFD expand row for verification"
    flagged_date: "2026-05-17"
```

### Status Values

| Status | Meaning |
|--------|---------|
| `resolved` | Issue was fixed — field removed, surfaced, or refactored. Include PR reference. |
| `keep-omitted` | Evaluated and confirmed: correct to NOT show this field. Won't be re-flagged. |
| `pending` | Recommendation made but not yet actioned. Will be re-checked on next trace. |
| `superseded` | Recommendation no longer relevant due to page redesign or feature removal. |

### Rules

- **Create the file** if it doesn't exist (first trace for this anchor)
- **Append new entries** — never remove old ones (they're the audit trail)
- **Update status** of existing entries when re-tracing finds them resolved
- **One file per anchor** — if a project has multiple traced pages, each gets its own decisions file: `flow-trace-decisions-{slug}.yaml`
- **Confirmed omissions from step 5 section 6** become `keep-omitted` entries — this is the primary mechanism that prevents re-flagging
