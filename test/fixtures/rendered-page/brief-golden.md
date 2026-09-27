# Design Brief: price list (golden fixture — Part 2b only)

A worked Part 2b, rendered from `custom/workflows/design/design-handoff/brief-template.md` for the
brand-source-finder price-list page the owner rejected on 2026-09-27. Used by
`test/test-rendered-page-check.js` as the brief that validates clean at Gate 1 and whose floor the
rendered-page goldens run against. Values are the fork default (the project declares no scale).

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

A one-block summary, then the lines as cards, three fields at rest: product, the most it could make a unit, and its basis.

### 5. Banned on this surface

Tinted callout boxes, coloured edge stripes, stacked badges, all-caps labels, the same fact twice. Most tempting here: the freight question, the £30 floor per row, the import time.

### 6. Markers the design must carry

`data-answer` · `data-first-item` · `data-item` · `data-page`.

### 7. The policies behind this part

| Policy | Path | The rule you are held to |
|---|---|---|
| artifact-policy | `docs/artifact-policy.md` | A border or accent means someone must act and nobody is acting yet; headline to first figure within 12 words. |
| artifact-brief-policy | `docs/artifact-brief-policy.md` | The first line stays true alone; no identifier as a row label; colour never means important. |
| document-design-format | `docs/document-design-format.md` | One module owns every size and colour. |
| anti-ai-research | `~/.claude/docs/research/anti-ai-ui-patterns-2026-09-26.md` | No tinted callouts, edge stripes or micro-chrome. |
| copy-screen | `custom/workflows/design/shared/on-screen-copy-screen.md` | Every string is plain English a stranger understands. |
| presented-figures-basis | memory `presented-figures-declare-their-basis` | Every figure says what kind it is and how many observations back it. |
| reference-policy | `docs/transcript-policy.md` | A reader can tell which thing is meant and what state it is in. |
| supplier-relationship | `docs/supplier-buyer-profile.md` | A supplier question asks only whether they invoice the UK company; never mentions Amazon. |
| human-facing-documents | `docs/human-facing-documents.md` | Say it once; the first line does not mislead; no capitals for emphasis. |
| provenance-to-footer | `docs/artifact-policy.md` §2 | Provenance lives in the footer only. |

### 8. The machine copy

```json presentation-floor
{
  "standard": "STD-PRESENTATION-FLOOR-001",
  "viewport": { "width": 1440, "height": 900 },
  "typeScale": {
    "answer": { "size": 28, "weight": 600, "use": "the sentence that answers the page" },
    "sectionHeading": { "size": 18, "weight": 600, "use": "the name of a group of lines" },
    "figure": { "size": 16, "weight": 500, "use": "the most a line could make a unit" },
    "body": { "size": 14, "weight": 400, "use": "product names and sentences" },
    "caption": { "size": 12, "weight": 400, "use": "the basis beside a figure, and the footer" }
  },
  "spacing": [4, 8, 12, 16, 24, 32, 48],
  "colours": [
    { "name": "ink", "value": "oklch(0.2 0 0)", "means": "text and figures" },
    { "name": "muted", "value": "oklch(0.45 0 0)", "means": "captions and the footer" },
    { "name": "ground", "value": "oklch(1 0 0)", "means": "the page" },
    { "name": "rule", "value": "oklch(0.9 0 0)", "means": "hairlines between lines" },
    { "name": "act", "value": "oklch(0.5 0.15 255)", "means": "someone must act and nobody is acting yet; links" }
  ],
  "attention": {
    "top": "the answer",
    "firstItem": "the first line worth a look",
    "provenance": ["FX rate and source", "Keepa read dates", "import stamp", "file name and check id", "figures-before-freight note"],
    "provenanceTo": "footer"
  },
  "layout": { "summaryFirst": true, "items": "cards", "atRestFields": 3, "detailOnOpen": true },
  "banned": ["tinted-callout", "edge-stripe", "stacked-badges", "all-caps-labels", "repeated-fact"],
  "budgets": { "wordsToFigure": 12, "proseAboveFirstItem": 60, "borderedAllowed": 0, "headerMaxFraction": 0.4, "repeatedClauseMax": 4 },
  "citations": [
    { "id": "artifact-policy", "path": "docs/artifact-policy.md", "rule": "accent means act-now; bordered blocks 0 clean, 1 on a breach; identifiers to the footer; headline to figure within 12 words" },
    { "id": "artifact-brief-policy", "path": "docs/artifact-brief-policy.md", "rule": "rules 10-15" },
    { "id": "document-design-format", "path": "docs/document-design-format.md", "rule": "one module owns every size and colour" },
    { "id": "anti-ai-research", "path": "~/.claude/docs/research/anti-ai-ui-patterns-2026-09-26.md", "rule": "template-look catalogue" },
    { "id": "copy-screen", "path": "custom/workflows/design/shared/on-screen-copy-screen.md", "rule": "STD-COPY-SCREEN-001" },
    { "id": "presented-figures-basis", "path": "memory presented-figures-declare-their-basis", "rule": "every figure declares its basis and observation count" },
    { "id": "reference-policy", "path": "docs/transcript-policy.md", "rule": "every reference says which one and what state" },
    { "id": "supplier-relationship", "path": "docs/supplier-buyer-profile.md", "rule": "invoice-the-UK-company question only; never mention Amazon" },
    { "id": "human-facing-documents", "path": "docs/human-facing-documents.md", "rule": "R1 say it once, R7 first line not misleading, R9 no caps for emphasis" },
    { "id": "provenance-to-footer", "path": "docs/artifact-policy.md", "rule": "provenance is footer-only" }
  ]
}
```

## Part 3 · What must dominate

(omitted in this fixture)
