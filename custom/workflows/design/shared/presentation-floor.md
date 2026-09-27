---
name: presentation-floor
description: 'The binding presentation floor every design brief SPECIFIES and every rendered page is CHECKED against: a named type scale (one size, one job), spacing tokens, a colour set with meanings, a where-the-user-looks plan, the summary-then-items layout, a banned-patterns list, and "the answer is heavier than the evidence". Replaces the advisory style floor for these seven things.'
standard: STD-PRESENTATION-FLOOR-001
version: 1
ratified: 2026-09-27
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
B9 1440×900 · B10 all ten citations by path with their rule · B11 no unrendered `{placeholder}`.

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

**DETERMINISTIC:** Gate 1's brief check and the eleven rendered checks, each with goldens that fail the
audit's live examples. **PROBABILISTIC:** whether the answer is the right answer, whether the page reads
well, whether items are genuinely scannable (F5 beyond its declared count), and whether spacing tokens are
used (F2 is declared and checked in the brief, not on the page). A page can pass every check and still bury
the answer; T0 and TD0 remain a reader's judgement. The checks prove counts and presence, never quality.

## Prose consumers

| Consumer | Bound how |
|---|---|
| `design-handoff` | Renders Part 2b with concrete values and the machine block (step-03); Gate 1 runs `--validate-brief` (step-03c) |
| `design-implement` | Runs the rendered-page checks on the design bundle and the built page (step-04b); a design-side failure is a SENDBACK |
| `shared/brief-binding-contract.md` | Lists the floor as a binding class (v2) |
| `shared/claude-design-prompt.md` | Tells the designer Part 2b binds and names the markers |
