---
name: presentation-floor
description: 'The binding presentation floor every design brief SPECIFIES and every rendered page is CHECKED against: a named type scale (one size, one job), spacing tokens, a colour set with meanings, a where-the-user-looks plan, the summary-then-items layout, a banned-patterns list, and "the answer is heavier than the evidence". Replaces the advisory style floor for these seven things.'
standard: STD-PRESENTATION-FLOOR-001
version: 4
ratified: 2026-09-27
amended: 2026-09-28 (v2 — §8 brief completeness, B12–B20, from Claude Design's pre-build review of the price-list v4 brief); 2026-09-28 (v3 — §9 below the fold, B21 and R12–R14, from the price-list v6 design's prose wall); 2026-09-28 (v4 — §10 label/value row groups, B22 and R15–R18, from the bundle 6 drawer's journey section)
---

# The presentation floor — what a brief specifies, and what a rendered page must pass

> **Owner, 2026-09-27, verbatim:** *"we need to go back to the drawing board with the UI... treat
> Claude Design like an idiot... we've left basic gaps to Claude Design... it's reading like a ledger
> printed on a screen... no font size enforcement... that yellow thing at the top, the most AI pattern
> I've ever seen, which hasn't been caught by our anti-AI patterns... audit text at the top... a
> complete violation of our user attention policy... the design handoff workflow we're using is not up
> to date with some of our recent policies."*

Evidence: the price-list page audit of 2026-09-27 (brand-source-finder `/product/190`, measured at
1440×900), filed verbatim in the fork at `docs/price-list-ui-audit-evidence-2026-09-27.md`. It found a page with three font sizes doing opposite jobs (the 33-word headline and all 17
row profits at 18px/600), six near-identical greys, 288 words above the first product, provenance and
import stamps at the top, the freight question said three times, and a tinted amber notice box that
Claude Design introduced in bundle 3 and the implementation copied. Every rule that would have caught
it was either **advisory** in the brief (`brief-binding-contract.md` §1 v1 made tokens, colour, the
AI-fingerprint floor and the comfort floor "a note, never a failure") or **tested only inside
amazon-removal-assistant** against that repository's own generated pages. The brief also told Claude
Design *"What IS yours: typography and scale, spacing and rhythm…"* and pointed at a design policy that
did not exist, so no concrete scale was ever handed over.

**The correction is two-sided.** The brief now SPECIFIES the seven things below instead of delegating
them, and they BIND: a design that breaks them fails, at Gate 1 of the brief, at design review, and at
the rendered-page check in `design-implement`. Claude Design still does the heavy lifting on
composition, wording and everything this file does not name — but it no longer chooses the type
scale, the colours, what sits at the top, or whether a notice box is acceptable.

## 1. What binds — the seven parts of the floor

Every brief renders all seven as **Part 2b** (`design-handoff/brief-template.md`), with concrete values,
plus the machine block the checker reads. A brief that leaves any of them to the designer is not
deliverable (Gate 1, `tools/check-rendered-page.js --validate-brief`).

| # | Part | What the brief must say | Checked by |
|---|---|---|---|
| F1 | **Type scale, one size one job** | Five named roles — `answer`, `sectionHeading`, `figure`, `body`, `caption` — each with ONE size, ONE weight and a sentence of what it is for. Five distinct sizes. The answer size is used by the answer alone. No other size exists on the surface. | R1, R2 · B3 |
| F2 | **Spacing tokens** | One scale of even pixel values. Every margin, padding and gap comes from it; the gap between groups is visibly larger than the gap inside one. | B4 (review for use) |
| F3 | **Colour set, each with a meaning** | A short list of named colours, each with the one thing it means and nothing else. One secondary grey, not six. An accent means *someone must act and nobody is acting yet* — never "important". | B5, R9 (contrast) |
| F4 | **Where the user looks** | The top holds the answer (`[data-answer]`), and the first actionable item (`[data-first-item]`) is fully visible at 1440×900 with the header taking no more than 40% of the height. A word budget above the first item (default 60). Provenance and audit text — FX rate, data dates, import stamps, file names, run ids, "figures before freight"-type bookkeeping — is named in a list and goes to the **footer or behind a disclosure**, never at the top. | R6, R7, R11 · B6 |
| F5 | **Layout pattern** | A summary first, then the items as scannable **cards or groups** (`[data-item]`), each showing a small declared number of fields at rest, with the detail on open. Not a ledger of every field. | B7 (review for the rest) |
| F6 | **Banned patterns** | The list in §3, verbatim, at minimum. | R3, R4, R5, R8, R10 · B8 |
| F7 | **The answer is heavier than the evidence** | The answer is set larger than every figure and every heading on the surface; a figure never shares the answer's size. | R1, R2 · B3 |

**Markers the page must carry.** `[data-answer]` on the element holding the page's answer,
`[data-first-item]` on the first actionable item, `[data-item]` on each item card or group, and
optionally `[data-page]` on the surface root. The brief names them and the designer draws them into the
bundle's HTML; the implementation keeps them. A page without them cannot be checked, and the checker
reports that as **unchecked**, which is not a pass.

## 2. Where the values come from — never "yours"

Step-03 fills Part 2b in this order, and records which source it used:

1. **The project's design policy / brand identity**, where it declares a scale, spacing and colours.
2. **The project's token file** (`{design_system_pointer}`), mapping each role to an existing token —
   e.g. brand-source-finder's `--font-size-3xl` 24 → answer, `xl` 18 → section heading, `lg` 16 →
   figure, `base` 14 → body, `xs` 12 → caption. Roles that share a token are a defect to resolve in the
   brief, not to hand the designer.
3. **The fork default below**, stated in the brief as the default and flagged in Part 5 as "the project
   should adopt or replace this".

**Fork default** (used only when the project declares nothing):

| Role | Size | Weight | For |
|---|---|---|---|
| answer | 28px | 600 | the one sentence that answers the page, carrying its deciding figure |
| sectionHeading | 18px | 600 | the name of a group of items |
| figure | 16px | 500, tabular numerals | the deciding figure on each item |
| body | 14px | 400 | item names and sentences |
| caption | 12px | 400 | the basis beside a figure, and the footer |

Spacing `4 8 12 16 24 32 48`. Colours: `ink` (text and figures) · `muted` (captions and footer — the one
secondary grey, ≥ 4.5:1 on the ground in both themes) · `ground` · `rule` (hairlines between items) ·
`act` (someone must act and nobody is; links). A `danger` colour exists only where a figure can be
wrong or refused on this surface.

**This supersedes "three font sizes or fewer"** (`design-standards.md` quality checklist and the brief's
§5a comfort floor) for any surface with a Part 2b. The audit's page obeyed the three-size rule and failed
because three sizes carried nine jobs; five named roles with one job each is the stricter rule.

**The shape borrowed from `document-design-format.md`**, which does not transfer its print sizes: one
module owns every size and colour, and no literal `font-size` or colour exists outside it. The brief says
so to the implementation; the rendered check enforces the outcome (R1).

## 3. Banned patterns — binding, each with the construction that makes it

| Key | Banned | The construction to recognise | Instead |
|---|---|---|---|
| `tinted-callout` | A tinted notice / callout / admonition box | A block of prose on a pastel or chromatic fill, usually with a matching 1px border, a small radius and a bold lead-in word, sitting as its own block. **The price-list `.plr-next`**: `border:1px solid oklch(0.62 0.13 70); background:oklch(0.98 0.02 85); border-radius:4px`, reading *"Next: get Spain → Leipzig priced. It is question 1 on the right…"* | The next action said once, in body weight, inside the header as part of the answer's line |
| `edge-stripe` | A coloured stripe on one edge of a card or callout | A 2–4px border on the left or top in an accent colour, or in a colour the other edges do not share | Position and weight; if something must act, the act colour on the words |
| `stacked-badges` | Badges, pills or chips stacked on one item | Two or more pills in a row or column on one item, or a pill carrying what a sentence would say | One state, in words; a pill only for a small fixed status set |
| `all-caps-labels` | All-capital labels, kickers or pills | `text-transform: uppercase`, or a word in capitals that is not an acronym (`CHECK`, `SKIP`, `BUY`) | Sentence case; emphasis by weight or size |
| `repeated-fact` | The same fact said twice at rest | A sentence repeated anywhere on the surface; a clause restated down every row (*"£N over the £30 floor"* ×17); one question said three ways (the freight question in the headline, the box and the side panel) | Say it once where it governs; per row, only what differs |

Also banned, carried from the fork's existing floor and now binding for a Part 2b surface: a hero strip
or banner above working content; a separate summary card or stat-card grid as the opener; monospace for
anything but codes; an identifier as the label of a row or the subject of a sentence.

## 4. The policies the brief carries — cited by path, with the rule stated

Claude Design cannot read these files, so the brief carries each rule in a sentence **and** names its
path, so an implementer and a reviewer can check the source. The citation set is fixed; Gate 1 (B10)
fails a brief missing any of them. Paths are relative to amazon-removal-assistant unless shown otherwise.

| id | Path | The rule the brief carries |
|---|---|---|
| `artifact-policy` | `docs/artifact-policy.md` §3–§5 | A border or accent means someone must act and nobody is acting yet; bordered blocks 0 on a clean page, ≤ 1 on a breach; a filename, code, box id or SKU goes to the footer or is cut; headline to first figure ≤ 12 words. |
| `artifact-brief-policy` | `docs/artifact-brief-policy.md` rules 10–15 | The first line and every heading stay true alone; a caveat stays beside the figure it qualifies; no identifier as a subject or a row label; nothing added; no chart where a number was given; colour never means "important". |
| `document-design-format` | `docs/document-design-format.md` | One module owns every size and colour; no literal size or colour outside it (the shape transfers; the print sizes do not). |
| `anti-ai-research` | `~/.claude/docs/research/anti-ai-ui-patterns-2026-09-26.md` | The template-look catalogue: tinted callouts, edge stripes, icon chips, middle-dot meta strings, monospace micro-labels, warm cream with amber, low-contrast grey. |
| `copy-screen` | fork `custom/workflows/design/shared/on-screen-copy-screen.md` (STD-COPY-SCREEN-001) | Every on-screen string is plain English a stranger understands; no internal vocabulary or codes as labels. |
| `presented-figures-basis` | memory `presented-figures-declare-their-basis` | Every price or metric says what kind it is (spot, 30-day, 90-day, owner-stated) and how many observations back it — beside the figure. |
| `reference-policy` | `docs/transcript-policy.md` and CLAUDE.md § *Every reference says WHICH ONE* | A reader not in the conversation can tell which thing is meant and what state it is in; a line that travels alone carries its own subject. |
| `supplier-relationship` | `docs/supplier-buyer-profile.md`; memory `supplier-enquiries-leave-amazon-out` | A question composed for a supplier asks only whether they will invoice the UK company, and never mentions Amazon or the resale channel. |
| `human-facing-documents` | `docs/human-facing-documents.md` R1, R7, R9 | Say it once; a reader who stops at the first line is not misled; emphasis by type, never by capitals. |
| `provenance-to-footer` | `docs/artifact-policy.md` §2 and §4 | Provenance is conditional and lives in the footer only; it is never the first thing read. |

## 5. The checks

**Gate 1, the brief** — `node ~/bmad-method-v6/tools/check-rendered-page.js --validate-brief <brief.md>`:
B1 Part 2b present · B2 the `presentation-floor` JSON block parses · B3 five roles, five distinct sizes,
answer largest and at least as heavy as a figure · B4 spacing scale · B5 colours with meanings · B6 the
attention plan, provenance to footer or disclosure · B7 the layout pattern · B8 the five banned keys ·
B9 1440×900 · B10 all ten citations by path with their rule · B11 no unrendered `{placeholder}` ·
**B12–B20 brief completeness (§8)**: B12 a ranked list orders by evidence tier first · B13 a truncated
field names what must survive and the near-duplicates · B14 the Copy deck says nothing twice · B15 the
brief is self-contained · B16 a states × views matrix · B17 1440, 1280 and a narrow width · B18
feedback after an action · B19 15% headroom under the word budget · B20 the brief's notation is not
rendering. **B21 (§9)** every section of the page declares its form and word budget. **B22 (§10)** every label/value row group is specified as one.

**design-implement, the rendered page** — `steps/step-04b-rendered-page-checks.md`, running
`check-rendered-page.js --snapshot|--url … --brief <brief.md>` on the rendered DOM, both themes:

| Id | Check | Fails when |
|---|---|---|
| R1 | type-tokens | a computed font size is not a declared role size; the answer is not at the answer size; anything else uses the answer size |
| R2 | answer-heaviest | any other text is set as large as the answer |
| R3 | tinted-callout | a block of four or more words sits on a chromatic fill (items and controls excepted) |
| R4 | bordered-budget | all-round bordered prose blocks outside `[data-item]` exceed the brief's budget (default 0) |
| R5 | edge-stripe | a left/top/right edge is drawn ≥ 2px in a colour, or in a colour the other edges lack |
| R6 | headline-figure | the answer does not reach a figure within 12 words |
| R7 | prose-above-item | more than the budget of words (default 60) sits above `[data-first-item]` |
| R8 | repeated-sentence | a sentence (≥ 25 characters, numbers normalised) appears twice, or a clause appears in more than 4 places |
| R9 | contrast | a text colour is under WCAG AA (4.5:1, 3:1 large) against its composited ground |
| R10 | all-caps | `text-transform: uppercase`, or a non-acronym word in capitals |
| R11 | above-the-fold | at 1440×900 the first item is cut by the fold or starts below 40% of the height |
| R12 | prose-wall | anywhere on the page, more than 2 paragraphs run back to back, or a paragraph is over 40 words |
| R13 | section-form | a section the brief declares is not in its form at rest: over its word budget; a rows section without labelled rows, over 5 rows, or a row over 12 words after its label; a held, provenance, method, skipped or message section open at rest or with a summary over 12 words; a marked section the brief never declared |
| R14 | footer-at-rest | the footer shows more than 2 lines at rest, or has no disclosure for the rest |
| R15 | row-cells | in a `[data-row-group]`: a row has other than one value cell or more than one status; a cell repeats another cell of its row; a value is more than 4 words and not money or a count; an explanation is over 12 words |
| R16 | row-grid | value cells do not share one right edge, or status cells one left edge (±2px); a figure is not right-aligned or not in tabular numerals; rows are no further apart than the lines inside a row |
| R17 | internal-words | a row group shows a word from `internalWords` (default: export, handoff, pipeline, record, run) |
| R18 | row-total | a group with an unpriced row has no total, or its total is not labelled as partial |

Each check is **pass**, **fail** or **unchecked**; unchecked is reported and never counts as a pass.
Goldens: `npm run test:rendered-page` — the yellow box and the 288-words case fail, and so does the live
page rebuilt from the audit's measurements.

## 6. How this sits with the binding contract, and with "the design is the authority"

- `brief-binding-contract.md` v2 makes this floor a **binding class** beside the Part 2 truth tests.
  Everything this file does not name stays advisory, as before.
- `design-implement` transcribes the design, and departures go back as a SENDBACK. **A floor failure that
  is in the design itself is a SENDBACK**, not a silent fix: run the check on the design bundle first. A
  failure the build introduced is fixed in the build.

## 7. Enforcement, honestly

**DETERMINISTIC:** Gate 1's brief check (B1–B22) and the eighteen rendered checks, each with goldens that fail the
audit's live examples. **PROBABILISTIC:** whether the answer is the right answer, whether the page reads
well, whether items are genuinely scannable (F5 beyond its declared count), and whether spacing tokens are
used (F2 is declared and checked in the brief, not on the page). A page can pass every check and still bury
the answer; T0 and TD0 remain a reader's judgement. The checks prove counts and presence, never quality.

## 8. Brief completeness — the gaps a designer should never have to find (v2, 2026-09-28)

> **Owner, 2026-09-28, verbatim:** *"ensure this is systematic brief workflow fix not a one time brief
> patch."*

The price-list v4 brief passed B1–B11 and Claude Design, asked to review it before building, still
found nine gaps. Each was a class, not a slip: nothing in the template asked for the thing, so every
future brief would have had it too. Each is now a rule here, a subsection of Part 2b (§9 in
`brief-template.md`) and a Gate 1 check. The running record, and every gap found since, is
`brief-gap-ledger.md`. The triggers are read from the brief's prose; the specification they demand
is read from the `presentation-floor` block, so the right words in the wrong place do not pass.

| # | Rule | Machine block | Check |
|---|---|---|---|
| G1 | **A ranked list orders by evidence strength before magnitude.** Tiers first — confirmed and live, then unconfirmed, then stale or absent — and the figure ranks only within a tier. Ranking by magnitude alone puts the weakest evidence at the top. | `ordering: [{ list, tiers[≥2, strongest first], thenBy }]` | B12, when the prose ranks, sorts or orders a list |
| G2 | **A truncated field names what must survive**, the token that tells near-identical items apart (colour, pack size, model suffix), and the brief lists the near-duplicate items in the data so the designer can test the rule. | `truncation: [{ field, mustSurvive, nearDuplicates[] \| "none: <how checked>" }]` | B13, when the prose mentions an ellipsis, truncation or a clamp |
| G3 | **Say-once holds inside the brief's own Copy deck.** A phrase of four or more words in two at-rest strings is said twice on the surface. Alternatives for one slot (same *Where* before its first comma), toasts, tooltips, screen-reader text and control labels are not compared. An unavoidable repeat is declared with its reason. | `sayOnceExceptions: [{ phrase, why }]` (optional) | B14 |
| G4 | **The brief is self-contained.** No deck row is a placeholder or a pointer; no view is kept "as it is"; no content is "in the older brief". Claude Design can read this brief and nothing else, so every referenced view carries its content inline. | — | B15 |
| G5 | **Every state has a layout in every view.** A states × views matrix (e.g. buy / check / skip × card / drawer, plus empty, loading and error), each cell a layout, "same as <state>" or "cannot arise: <why>". This is binding; §2g's state MATERIAL stays advisory. | `states: [{ state, view, layout }]` | B16 |
| G6 | **A responsive spec**: at least 1440, 1280 and one narrow width (≤ 1024), each with a layout, and for a drawer whether it overlays or pushes. | `responsive: [{ width, layout, drawer? }]` | B17 |
| G7 | **Feedback after an action is designed**: where it appears, how it looks, how long it stays (or what dismisses it), and its wording. | `feedback: { position, look, durationMs \| duration: "until …", wording }` | B18, when the prose names an action |
| G8 | **Headroom under the word budget.** The brief counts the words its own design puts above the first item and spends at most 85% of the budget, so a designer's heading does not break it. | `attention.wordsAboveFirstItem` | B19 |
| G9 | **The brief's notation is not rendering.** The brief says its own marks (`·`, `»`, braces) are not printed, and names the separators the page does print. | `notation: { notLiteral, separators }` | B20 |

**What these checks cannot do.** They prove a specification is PRESENT and well-formed, never that it
is right: a tier order can be wrong, a "must survive" token can be the wrong one, a layout can be
described badly. The deck screen (B14) reads phrases, not meaning, so a repeat said in different
words passes and a shared proper name can fire (declare it). Those stay with the designer's pre-build
review and the Gate 1 reviewer.

**How the list grows.** `design-handoff` step-05 asks Claude Design to review the brief against its
tests before building. Each finding that reveals a gap in the template, rather than in one brief, is
appended to `brief-gap-ledger.md` with the rule and the check added for it, in the same change.

## 9. Below the fold — structure, never running prose (v3, 2026-09-28)

> **Owner, 2026-09-28, verbatim,** on Claude Design's v6 of the price-list page after scrolling down:
> *"not too happy when I scrolled down.. looks like text printed on a screen with no thought."* Earlier
> the same day: *"ensure this is systematic brief workflow fix not a one time brief patch."*

The floor of §1 limited prose **above** the first item (F4, R7) and said nothing about the rest of the
page, so v6 met every check and still ended in a wall: six paragraphs of caveats under *Before you
order*, five long held questions each open with its trigger line, a *stand-in wording* note, and a
six-line provenance footer. The brief had asked for exactly that (*"Before you order, body text, in this
order: …"*). The gap was the template's, so the rule is the template's: **every section of the page has
a visual structure, and no section is running prose.** Gap G10 in `brief-gap-ledger.md`.

| Kind of section | Form | At rest |
|---|---|---|
| `items` — the cards or groups | `cards` | the layout of §1 F5 |
| `caveats` — conditions and cautions before acting | `rows` | at most **5** short labelled rows: a label, then at most **12** words; the "why" behind each is a disclosure on the row |
| `held` — questions held for later · `provenance` · `method` — how the figures were worked out · `skipped` | `disclosure` | **collapsed**, showing one summary line of at most 12 words (*5 questions held for later*) |
| `message` — a verbatim outbound message (the question to send a supplier) | `message-block` | **collapsed**, with its controls (Copy, Open WhatsApp); opened, the message word for word in a block |
| `footer` | `disclosure` (or `rows`) | at most **2** lines; everything else behind a disclosure |
| `other` | any form above | within its word budget |

Every section also carries a **word budget at rest**, at most 60 for anything that is not the items.
**No section is written as paragraphs**: on the rendered page, more than two paragraphs in a row, or one
paragraph over 40 words, fails wherever it sits (R12). A note about the brief itself (*stand-in wording*,
*sample*) is not a section; if something is sample, it is labelled on its face, in the element it
qualifies.

**Machine block:** `sections: [{ name, kind, form, wordBudget, summary?, maxRows?, rowMaxWords?,
controls?, linesAtRest?, disclosure? }]`. **Markers the page carries:** `data-section="<name>"` on each
section root (optionally `data-section-kind` / `data-section-form`), `data-row` on each row with its label
in `data-row-label`, and `data-footer` on the footer (else `<footer>`). A collapsed section is a `<details>`
without `open`, or holds an `[aria-expanded="false"]` control.

**Checks.** Gate 1 **B21**: `sections` present; every entry has a valid kind, form and budget; caveats are
rows with `maxRows` ≤ 5 and `rowMaxWords` ≤ 12; held, provenance, method and skipped are disclosures, a
message is a message block with its controls, each with a summary of ≤ 12 words; the footer declares
`linesAtRest` ≤ 2 and its disclosure. Rendered **R12–R14** (§5). Goldens: the v6 lower half as the owner's
screenshot showed it fails R12, R13 and R14; the same content structured passes.

**What these cannot do.** They prove the page is structured, not that the right thing is in the rows. A
row can be twelve true words that miss the point; a summary line can be vague. That stays with the
designer's pre-build review and the reader.

## 10. Label/value row groups — a grid, not text in rows (v4, 2026-09-28)

> **Owner, 2026-09-28,** on the line drawer's *The journey to Amazon UK, cost by cost* in Claude
> Design's bundle 6: it *"reads as a mess printed on a screen, not much thought about font size,
> spacing."*

The brief asked for three columns "separated by space alone" and a caption under every leg, and gave
an unpriced leg the words *not priced* both as its standing and in its figure's place. Design drew
exactly that: *not priced | not priced*, the standing at a different x on every row, a bold sentence
about our own tooling in the value column, two-line notes, rows as close as the lines inside a row,
and no total. The gap was the template's. Gap G11 in `brief-gap-ledger.md`.

**A label/value row group** — a cost breakdown, a fact list, the money section of a drawer — is the
named form `value-rows`, section kind `facts`. Its rules:

| Rule | Why, or where it is already stated |
|---|---|
| One value cell per row, and at most one status badge | a badge that restates the value is the same fact twice (§3 `repeated-fact`) |
| A fixed column grid: every value ends on one right edge, every badge starts on one left edge | amazon-removal-assistant `docs/decision-document-policy.md` §2a: *"the figure (tabular, in a table)"* is its own register |
| Values right-aligned, in tabular numerals, at the `figure` role | §1 F1; the figure role already says tabular |
| A value is money, a count, or at most 4 words — never a sentence | `docs/artifact-policy.md` §4: *"a figure goes in a sentence when it is the point, and in a table when it is one of several being compared. Not both."* |
| An explanation is at most 12 words, in the `caption` role, under the label | a longer reason goes behind the section's disclosure |
| Rows sit further apart than the lines inside a row (`rowGap` > `innerGap`, both from the spacing scale) | §1 F2: the gap between groups is larger than the gap inside one |
| A status badge is from a small fixed set, and never says a figure is missing (that is the value's job) | `docs/decision-document-policy.md` §2b: *a status tag, set apart* — one state, said once |
| No internal vocabulary: `export`, `handoff`, `pipeline`, `record`, `run`, and any the project adds | `on-screen-copy-screen.md` (STD-COPY-SCREEN-001) and `docs/artifact-policy.md` §4 (identifiers go to the footer or are cut) |
| A total over rows with an unpriced value is labelled as partial (*Priced so far, partial*); no total needs a stated reason | `docs/human-facing-documents.md` R7: a reader who stops at the figure is not misled |

**Machine block:** a section `{ name, view?, kind: "facts", form: "value-rows", wordBudget, columns:
[label, value, status?, note?], valueMaxWords ≤ 4, noteMaxWords ≤ 12, valueAlign: "right", numerals:
"tabular", rowGap, innerGap, maxRows ≤ 10, statusValues?, total: { label, partial } | "none: <why>" }`,
and at floor level `internalWords` carrying at least the five. `view` names the `data-page` the group
lives on (a drawer), so a page snapshot does not look for it. **Markers:** `data-row-group="<name>"` on
the group, `data-row` on each row, `data-cell="label|value|status|note"` on each cell,
`data-row-total` on the total row (with `data-total="partial"` when it is).

**Checks.** Gate 1 **B22**. Rendered **R15–R18** (§5). Goldens: bundle 6's drawer journey fails all
four; the same five legs as a grid, with a partial total, pass.

**What these cannot do.** They prove the grid, the counts and the words, not that the right figure is
in the right row or that a 12-word note is the useful 12 words.

## Prose consumers

| Consumer | Bound how |
|---|---|
| `design-handoff` | Renders Part 2b with concrete values and the machine block (step-03); Gate 1 runs `--validate-brief` (step-03c) |
| `design-implement` | Runs the rendered-page checks on the design bundle and the built page (step-04b); a design-side failure is a SENDBACK |
| `shared/brief-binding-contract.md` | Lists the floor as a binding class (v2) |
| `shared/claude-design-prompt.md` | Tells the designer Part 2b binds and names the markers |
| `shared/brief-gap-ledger.md` | The running record of §8's gaps: every template gap a designer finds, with the rule and check added |
| `design-handoff` step-05 | The designer's pre-build review of the brief; template gaps it finds are appended to the ledger (§8) |
| `design-handoff/brief-template.md` Part 2b §10 | Renders the sections table of §9 and the `sections` machine entry (B21) |
| `design-handoff/brief-template.md` Part 2b §11 | Renders each label/value row group of §10 and its machine entry (B22) |
