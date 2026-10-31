# Design Brief: price list (golden fixture — the opening and Part 2b)

A worked Part 2b, rendered from `custom/workflows/design/design-handoff/brief-template.md` for the
brand-source-finder price-list page the owner rejected on 2026-09-27. Used by
`test/test-rendered-page-check.js` as the brief that validates clean at Gate 1 and whose floor the
rendered-page goldens run against. Values are the fork default (the project declares no scale). The
five-role scale this fixture carried before 2026-10-04 is kept beside it as `brief-legacy-five-role.md`.

## The job

The owner opens this page after a supplier sends a price list, to decide which lines to chase a
freight price for. Within five seconds they can say how many lines could make money and that none is
a buy yet.

## Picture of good

**Reference screen:** the supplier terms page, as accepted by the owner on 26 September 2026 —
`docs/design-references/supplier-terms-accepted.png`. Borrow its vocabulary and its level of finish.
Do not copy its layout: that page compares terms, this one ranks lines.

**Component vocabulary:**

- A grouped table with aligned columns, for the lines.
- An expandable record sheet of label and value rows, for one line opened.
- A status dot with the stage in text, for where a line stands.

## The five rules

1. **Use the product's vocabulary.** Build from the components above before inventing one.
2. **Claims are verbatim; chrome is yours.** A value and its qualifier ship word for word. Column
   headers, section labels and group names are your call.
3. **One value leads.** On a line, the most it could make a unit leads; everything else is secondary.
4. **Type by position.** One typeface, four sizes, set by where text sits. Never two sizes on one line.
5. **Absence is quiet.** A value that is not there is set small and grey.

## Before you deliver — self-review

Render the draft, screenshot it, and judge it against the five rules and against one question: would
this ship at a good product company? Fix what fails, then deliver.

# Reference — read as needed

## Screen words

| Field | State | Value | Qualifier | Tone | Basis, shown when the line is opened |
|---|---|---|---|---|---|
| what a line could make | priced | £{profit} a unit | before freight | ink | Sells at £{price}, the lowest offer on {date}; freight to the warehouse is not priced. |
| selling price | read | Matched | — | ink | The selling price was read from the matched listing on {date}. |
| selling price | not read | Not checked | — | muted | Nobody has read the selling price for this line yet. |
| selling price | read, nothing there | None reported | — | muted | The listing was read on {date} and shows no selling price. |

**Missing values, in grey:** *Not checked* (nobody looked) · *None* (we asked; there is nothing) · *n/a* (does not apply) · *Not set* (nothing chosen yet).
**Your moves:** *Send draft to supplier* · *Copy link*. **Whose move:** You · Supplier · Nobody.
**Labels on an opened line:** Where it stands · Money · Journey.
**Never confuse:** *Not checked* (nobody looked) with *None reported* (we looked and the seller lists none).

**Worked example.** Raw: *"the 90-day Buy Box is blank — none, or not read"*. Value: *Not checked*.
Basis: *Nobody has read the selling price for this line yet.*

## Part 2 · What must be true — the binding tests

(omitted in this fixture)

## Part 2b · The presentation floor — binding, and specified for you

**Values from:** fork default (the project declares no scale — see Part 5)

### 1. Type scale — four sizes, set by position

| Position | Size | Weight | What sits here |
|---|---|---|---|
| the page's lead line (answer) | 28px | 600 | the sentence that answers the page |
| a block's lead line (section heading) | 18px | 600 | the name of a group of lines, or the one value that leads an opened line |
| inside an item or row (body) | 14px | 400, 600 for the value that leads | names, values, figures and sentences alike |
| secondary (caption) | 12px | 400 | the basis under a value, an absent value, and the footer |

One typeface. A line of text is one size; the value that leads a row is heavier, never larger.
An absent value is set in the secondary size, in muted.

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
Cards are ranked by how firmly the figure is known first, then by the most a line could make, highest first
(the ordering in the machine copy). A product name longer than the card ends in an ellipsis, and the
variant words that tell two near-identical lines apart are kept (the truncation in the machine copy).
Each card has a copy control for the line's link; what the page says after a copy is the feedback in the
machine copy. The drawer that opens a line, the states it can be in and how the page reflows at 1440,
1280 and 768 are all in the machine copy.

### 4a. Below the items, as drawn for this list

Before you order, as rows: *Prep* — *Labels and cartons: ask our prep.* · *VAT* — *0% while billed as an export.* Held questions, closed: *3 questions held for later*. The question, closed: *The freight question, ready to send*. Footer line: *Checked 25 September; rate of 25 September.*

### 4b. Notation in this brief

The middle dot and the » in this brief separate alternatives and steps; they are never printed. On the
page, fields sit on their own lines and a list inside a sentence is joined with commas.

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
    "sectionHeading": { "size": 18, "weight": 600, "use": "a block's lead line: the name of a group of lines, or the value that leads an opened line" },
    "body": { "size": 14, "weight": 400, "use": "everything inside an item or row: names, values, figures and sentences" },
    "caption": { "size": 12, "weight": 400, "use": "the basis beside a figure, and the footer" }
  },
  "pictureOfGood": {
    "reference": {
      "surface": "the supplier terms page",
      "where": "docs/design-references/supplier-terms-accepted.png",
      "acceptedBy": "the owner, 26 September 2026",
      "borrow": "its component vocabulary and its level of finish",
      "notCopy": "its layout: that page compares terms, this one ranks lines"
    },
    "vocabulary": [
      { "component": "a grouped table with aligned columns", "use": "the lines" },
      { "component": "an expandable record sheet of label and value rows", "use": "one line opened" },
      { "component": "a status dot with the stage in text", "use": "where a line stands" }
    ]
  },
  "focal": [
    { "item": "a line in the list", "leads": "the most it could make a unit", "secondary": ["the product name", "the basis of the price"] },
    { "item": "a line opened", "leads": "whether it is worth chasing a freight price for", "secondary": ["the money rows", "the journey rows", "how it was matched"] }
  ],
  "absence": { "role": "caption", "colour": "muted" },
  "screenWords": {
    "fields": [
      { "field": "what a line could make", "state": "priced", "value": "£{profit} a unit", "qualifier": "before freight", "tone": "ink", "basis": "Sells at £{price}, the lowest offer on {date}; freight to the warehouse is not priced." },
      { "field": "selling price", "state": "read", "value": "Matched", "tone": "ink", "basis": "The selling price was read from the matched listing on {date}." },
      { "field": "selling price", "state": "not read", "value": "Not checked", "tone": "muted", "basis": "Nobody has read the selling price for this line yet." },
      { "field": "selling price", "state": "read, nothing there", "value": "None reported", "tone": "muted", "basis": "The listing was read on {date} and shows no selling price." }
    ],
    "tones": { "ink": "ink", "muted": "muted" },
    "missing": [
      { "means": "nobody looked", "word": "Not checked" },
      { "means": "we asked and there is nothing", "word": "None" },
      { "means": "does not apply", "word": "n/a" },
      { "means": "nothing chosen yet", "word": "Not set" }
    ],
    "actions": [{ "move": "ask the supplier for a freight price", "phrase": "Send draft to supplier" }, { "move": "share a line", "phrase": "Copy link" }],
    "whoseMove": ["You", "Supplier", "Nobody"],
    "openedLabels": ["Where it stands", "Money", "Journey"],
    "distinctions": [{ "a": "Not checked", "b": "None reported", "means": "nobody looked, against we looked and the seller lists none" }],
    "examples": [
      { "raw": "the 90-day Buy Box is blank — none, or not read", "value": "Not checked", "basis": "Nobody has read the selling price for this line yet." },
      { "raw": "margin 24.1% · floor is 30.0%", "value": "24% margin", "qualifier": "under your floor", "basis": "The margin is 24.1% against your floor of 30.0%." }
    ]
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
    "provenanceTo": "footer",
    "wordsAboveFirstItem": 38
  },
  "layout": { "summaryFirst": true, "items": "cards", "atRestFields": 3, "detailOnOpen": true },
  "ordering": [
    { "list": "the cards worth a look", "tiers": ["listing confirmed and price read in the last 7 days", "listing unconfirmed", "price stale or absent"], "thenBy": "the most a line could make a unit, highest first" }
  ],
  "truncation": [
    { "field": "product name on a card", "mustSurvive": "the variant words (colour, pack size, model suffix) that differ between near-identical lines; the middle of the name is cut, never the end", "nearDuplicates": ["rows 24 and 25: the same brush in white and in black", "rows 40 and 41: heads in packs of 4 and 8"] }
  ],
  "states": [
    { "state": "worth a look", "view": "card", "layout": "name, figure, basis on three lines" },
    { "state": "worth a look", "view": "drawer", "layout": "answer, next action, product, money, journey" },
    { "state": "skipped", "view": "card", "layout": "name and the reason in place of the figure" },
    { "state": "skipped", "view": "drawer", "layout": "answer names the reason; money and journey sections are not drawn; the product section is kept" },
    { "state": "empty list", "view": "card", "layout": "cannot arise: an empty list draws no cards, only the answer saying so" },
    { "state": "empty list", "view": "drawer", "layout": "cannot arise: there is no line to open" },
    { "state": "loading", "view": "card", "layout": "three grey lines per card at the card's height, no spinner" },
    { "state": "loading", "view": "drawer", "layout": "same as loading card, one block per section" },
    { "state": "far end unreachable", "view": "card", "layout": "the card draws; the figure reads 'price not read' in body, muted" },
    { "state": "far end unreachable", "view": "drawer", "layout": "same as far end unreachable card, and the money section says which read failed" }
  ],
  "responsive": [
    { "width": 1440, "layout": "two card columns; drawer 720px", "drawer": "overlay" },
    { "width": 1280, "layout": "two card columns; drawer 640px", "drawer": "overlay" },
    { "width": 768, "layout": "one card column; drawer full width", "drawer": "overlay" }
  ],
  "feedback": { "position": "bottom left of the content area, 24px in", "look": "ink text on the surface colour, 1px rule, no icon, no colour", "durationMs": 4000, "wording": "says exactly what was copied, from the Copy deck toast rows" },
  "notation": { "notLiteral": "the middle dot and the » in this brief separate alternatives and steps and are never printed", "separators": "on the page, fields sit on their own lines and a list inside a sentence is joined with commas" },
  "sections": [
    { "name": "items", "kind": "items", "form": "cards", "wordBudget": 400 },
    { "name": "before-you-order", "kind": "caveats", "form": "rows", "wordBudget": 60, "maxRows": 4, "rowMaxWords": 12, "sample": ["Prep", "Labels and cartons: ask our prep.", "VAT", "0% while billed as an export."] },
    { "name": "held-questions", "kind": "held", "form": "disclosure", "wordBudget": 6, "summary": "3 questions held for later", "sample": ["3 questions held for later"] },
    { "name": "question", "kind": "message", "form": "message-block", "wordBudget": 10, "summary": "The freight question, ready to send", "controls": ["Copy", "Open WhatsApp"], "sample": ["The freight question, ready to send"] },
    { "name": "footer", "kind": "footer", "form": "disclosure", "wordBudget": 30, "linesAtRest": 2, "disclosure": "How these figures were worked out", "sample": ["Checked 25 September; rate of 25 September."] }
  ],
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

## Copy deck — every string a person reads on this surface, screened

| # | Where | Kind | Ships as | Source | Screen |
|---|---|---|---|---|---|
| 1 | Page answer | claim | {n} of these {n} lines could make money once freight is priced; none is a buy yet. | new | a✓ b✓ c✓ d✓ |
| 2 | Next action | claim | Next: ask the supplier what freight to Leipzig costs. | new | a✓ b✓ c✓ d✓ |
| 3 | Card, figure | claim | £{profit} a unit | new | a✓ b✓ c✓ d✓ |
| 4 | Card, basis | claim | sells at £{price}, lowest offer | new | a✓ b✓ c✓ d✓ |
| 5 | Card, skipped reason | claim | Sells under £{floor} | new | a✓ b✓ c✓ d✓ |
| 6 | Card copy control | chrome | Copy link | new | a✓ b✓ c✓ d✓ |
| 7 | Toast after copying | claim | Copied a link to row {n} | new | a✓ b✓ c✓ d✓ |
| 8 | Drawer answer | claim | Up to £{profit} a unit once at the warehouse. | new | a✓ b✓ c✓ d✓ |
| 9 | Footer | claim | Prices as Keepa read them on {date}. | new | a✓ b✓ c✓ d✓ |
| 10 | Table, column head over the figure | chrome | Most a unit | new | a✓ b✓ c✓ d✓ |
