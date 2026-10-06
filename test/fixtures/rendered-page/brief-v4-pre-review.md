# Design Brief: price list v4, as sent for review (reconstructed failing golden)

Reconstructed from the brand-source-finder price-list v4 brief of 2026-09-27 as it stood BEFORE Claude
Design's pre-build review (commit f457fe6 in that repository). It passed B1–B11. Every defect below is
one Claude Design found, kept in the shape the real brief had it, with the business detail trimmed:
`custom/workflows/design/shared/brief-gap-ledger.md` rows G1–G9. Used by
`test/test-rendered-page-check.js`: it must FAIL B12–B20, one finding class per ledger row.

## Part 2 · What must be true — the binding tests

(omitted in this fixture)

## Part 2b · The presentation floor — binding, and specified for you

**Values from:** fork default (the project declares no scale — see Part 5)

### 1. Type scale — one size, one job

| Role | Size | Weight | Used for | Never used for |
|---|---|---|---|---|
| answer | 28px | 600 | the sentence that answers the page | anything else — no figure, heading or label shares this size |
| section heading | 18px | 600 | the name of a group of lines | figures, the answer |
| figure | 16px | 500, tabular numerals | the most a line could make a unit | the answer; prose |
| body | 14px | 400 | product names and sentences | provenance, which is caption |
| caption / footnote | 12px | 400 | the basis beside a figure, and the footer | column headers that are sentences; methodology at the top |

### 2. Spacing and colour

**Spacing:** 4 · 8 · 12 · 16 · 24 · 32 · 48px.

| Colour | Value | Means | Never means |
|---|---|---|---|
| ink | `oklch(0.2 0 0)` | text and figures | emphasis |
| muted | `oklch(0.45 0 0)` | captions and the footer; the one secondary grey | a second or third grey |
| ground | `oklch(1 0 0)` | the page | a panel behind a notice |
| rule | `oklch(0.9 0 0)` | hairlines between lines | a coloured edge |
| act | `oklch(0.5 0.15 255)` | someone must act and nobody is acting yet; links | important |

### 3. Where the user looks — the attention plan

1. The top is the answer: how many lines could make money once freight is priced, and that none is a buy yet.
2. The next action, said once in the answer's line: ask the supplier what freight to Leipzig costs.
3. The first actionable item is the first line worth a look, fully visible at 1440×900 in the top 40%. No more than 60 words above it.
4. Provenance and audit go to the footer: the FX rate and its source, the Keepa read dates, the import stamp, the file name and check id, the "figures before freight" note.

### 4. Layout — a summary, then items, detail on open

A one-block summary, then the lines as cards in a two-column grid, ranked by profit once at Amazon UK,
highest first. Line 1 of a card is the product name — body, one line, ellipsis at the card edge, the full
name as the element's title. Line 2 is *Row 24 · code* in caption. Each card and the drawer carry a copy
control; each copy shows a toast saying exactly what was copied.

The line drawer is a side sheet on the right, 720px wide.

### 5. Banned on this surface

Tinted callout boxes, coloured edge stripes, stacked badges, all-caps labels, the same fact twice.

### 6. Markers the design must carry

`data-answer` · `data-first-item` · `data-item` · `data-page`.

### 7. The policies behind this part

(as in the golden fixture; carried in the machine copy)

### 8. The machine copy

```json presentation-floor
{
  "standard": "STD-PRESENTATION-FLOOR-001",
  "viewport": {
    "width": 1440,
    "height": 900
  },
  "typeScale": {
    "answer": {
      "size": 28,
      "weight": 600,
      "use": "the sentence that answers the page"
    },
    "sectionHeading": {
      "size": 18,
      "weight": 600,
      "use": "the name of a group of lines"
    },
    "figure": {
      "size": 16,
      "weight": 500,
      "use": "the most a line could make a unit"
    },
    "body": {
      "size": 14,
      "weight": 400,
      "use": "product names and sentences"
    },
    "caption": {
      "size": 12,
      "weight": 400,
      "use": "the basis beside a figure, and the footer"
    }
  },
  "spacing": [
    4,
    8,
    12,
    16,
    24,
    32,
    48
  ],
  "colours": [
    {
      "name": "ink",
      "value": "oklch(0.2 0 0)",
      "means": "text and figures"
    },
    {
      "name": "muted",
      "value": "oklch(0.45 0 0)",
      "means": "captions and the footer"
    },
    {
      "name": "ground",
      "value": "oklch(1 0 0)",
      "means": "the page"
    },
    {
      "name": "rule",
      "value": "oklch(0.9 0 0)",
      "means": "hairlines between lines"
    },
    {
      "name": "act",
      "value": "oklch(0.5 0.15 255)",
      "means": "someone must act and nobody is acting yet; links"
    }
  ],
  "attention": {
    "top": "the answer",
    "firstItem": "the first line worth a look",
    "provenance": [
      "FX rate and source",
      "Keepa read dates",
      "import stamp",
      "file name and check id",
      "figures-before-freight note"
    ],
    "provenanceTo": "footer"
  },
  "layout": {
    "summaryFirst": true,
    "items": "cards",
    "atRestFields": 3,
    "detailOnOpen": true
  },
  "banned": [
    "tinted-callout",
    "edge-stripe",
    "stacked-badges",
    "all-caps-labels",
    "repeated-fact"
  ],
  "budgets": {
    "wordsToFigure": 12,
    "proseAboveFirstItem": 60,
    "borderedAllowed": 0,
    "headerMaxFraction": 0.4,
    "repeatedClauseMax": 4
  },
  "citations": [
    {
      "id": "artifact-policy",
      "path": "docs/artifact-policy.md",
      "rule": "accent means act-now; bordered blocks 0 clean, 1 on a breach; identifiers to the footer; headline to figure within 12 words"
    },
    {
      "id": "artifact-brief-policy",
      "path": "docs/artifact-brief-policy.md",
      "rule": "rules 10-15"
    },
    {
      "id": "document-design-format",
      "path": "docs/document-design-format.md",
      "rule": "one module owns every size and colour"
    },
    {
      "id": "anti-ai-research",
      "path": "~/.claude/docs/research/anti-ai-ui-patterns-2026-09-26.md",
      "rule": "template-look catalogue"
    },
    {
      "id": "copy-screen",
      "path": "custom/workflows/design/shared/on-screen-copy-screen.md",
      "rule": "STD-COPY-SCREEN-001"
    },
    {
      "id": "presented-figures-basis",
      "path": "memory presented-figures-declare-their-basis",
      "rule": "every figure declares its basis and observation count"
    },
    {
      "id": "reference-policy",
      "path": "docs/transcript-policy.md",
      "rule": "every reference says which one and what state"
    },
    {
      "id": "supplier-relationship",
      "path": "docs/supplier-buyer-profile.md",
      "rule": "invoice-the-UK-company question only; never mention Amazon"
    },
    {
      "id": "human-facing-documents",
      "path": "docs/human-facing-documents.md",
      "rule": "R1 say it once, R7 first line not misleading, R9 no caps for emphasis"
    },
    {
      "id": "provenance-to-footer",
      "path": "docs/artifact-policy.md",
      "rule": "provenance is footer-only"
    }
  ]
}
```

## Part 3 · What must dominate

The answer, then the 23 cards to check. No more than 60 words sit above the first card (this design:
6 + 18 + 10 + 17 + 5 = 56).

## 6. Design Ask

Draw the page at 1440×900 in light and dark; draw the drawer for rows 7 and 24. Keep the supplier
drawer and the Price lists entry as they are, re-set in Part 2b's type and colours.

### Suggested frames

| Frame | Suggested states |
|---|---|
| `price-list-run` | at rest; skipped section open |
| `supplier-lookup` | as it is, re-set in Part 2b |

## Copy deck — every string a person reads on this surface, screened

| # | Where | Ships as | Source | Screen |
|---|---|---|---|---|
| 3 | Page answer, none a buy | {n} of these {n} lines are worth checking; none is a buy until the supplier quotes UK freight. | new v4 | a✓ b✓ c✓ d✓ |
| 10 | Toast after copying the question | Copied the freight question: paste it into WhatsApp | new v4 | a✓ b✓ c✓ d✓ |
| 11 | Basis line under the next action | Each profit is the most a line can make, before freight and prep. | new v4 | a✓ b✓ c✓ d✓ |
| 63 | Before you order, no total | No total is given: nothing has been chosen to buy, and every figure is before freight and prep. | new v4 | a✓ b✓ c✓ d✓ |
| 72 | Drawer answer, check | Up to £{n} a unit once at Amazon UK, before freight and prep. | new v4 | a✓ b✓ c✓ d✓ |
| 71 | Drawer answer, unconfirmed | Up to £{n} a unit, but no UK listing is confirmed as this product yet. | new v4 | a✓ b✓ c✓ d✓ |
| 87 | Drawer relation, unconfirmed | No UK listing is confirmed as this product yet: compare the pictures. | new v4 | a✓ b✓ c✓ d✓ |
| 114 | Drawer prep caption | Inbound box handling is on record; 10 units a box, assumed. | new v4 | a✓ b✓ c✓ d✓ |
| 115 | Drawer parcel caption | Parcelforce via Parcel2Go; 10 units a box, assumed, not measured. | new v4 | a✓ b✓ c✓ d✓ |
| 165 | Supplier drawer | (carried forward unchanged from the landed brief's supplier-lookup copy) | landed brief | a✓ b✓ c✓ d✓ |
