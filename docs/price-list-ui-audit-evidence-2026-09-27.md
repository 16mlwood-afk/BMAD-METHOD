# Price-list page UI audit — Media Electrónics, price list of 23 Sep 2026

**Surface:** brand-source-finder, hosted page `/product/190` (Media Electrónics' Oral-B list, check SR-20260926-005) and its line drawer (Row 24, the iO9 Magnetic white).
**Measured:** 27 Sep 2026, headless Chromium at 1440×900, signed in as the owner, both themes. Computed styles come from `getComputedStyle` on every element that holds its own visible text. Nothing was changed anywhere.
**Source read at:** brand-source-finder `origin/main` 635e757. The local main checkout is 16 commits behind and does not contain the live callout, so it was not used.

---

## Bottom line

**The page does not have "random" font sizes. It has too few sizes doing too many jobs, six near-identical greys, and 288 words of explanation and bookkeeping above the first product.** The live page uses only 3 sizes (12, 14, 18px), 3 weights and 2 families. That is inside every "three sizes or fewer" rule we have. The feeling of randomness comes from three places:

1. **One size carries opposite roles.** 18px/600 is both the 33-word headline and all 17 rows' profit figures. 12px is used for 122 elements: methodology paragraphs, provenance lines, column headers, row subtitles, row codes and footer audit, told apart only by greys you cannot tell apart.
2. **Nothing is a token.** The app has a type scale (`--font-size-xs`…`3xl`, `h1`–`h4`), but the price-list CSS uses it **0 times out of 25** font-size declarations. It copies Design's inline pixel literals and a local six-step grey ramp that its own comment says is "not a system token". Nothing in brand-source-finder checks type, colour or spacing.
3. **The design process lets typography off.** The brief told Design *"What IS yours: typography and scale, spacing and rhythm, how the answer is made loud… and the weight system"*. The binding contract (fork `brief-binding-contract.md` line 28) makes tokens, colour, the AI-fingerprint floor and the comfort floor advisory, *"a note, never a failure"*. Only the five-second tests bind, and a loud box is the cheapest way to pass them. That is how the amber callout got in.

Label: **Established** for the counts (measured), **Likely** for the causes (inferred from the counts plus the documents quoted below).

---

## 1. What the live page and drawer actually use (computed)

The `.plr` content only, excluding the app shell. Light and dark give identical counts except for colour values.

### Page (`.plr`, 224 text elements)

| Property | Distinct | Values (count · where) |
|---|---|---|
| font-size | **3** | 12px ×122 (methodology, VAT paragraph, FX/floor/Keepa/provenance lines, column headers, row codes, row subtitles, questions, footer) · 14px ×84 (identity line, standfirst, callout, product titles, prices, secondary figures) · 18px ×18 (the headline **and** all 17 "profit once delivered" figures) |
| font-weight | **3** | 400 ×169 · 500 ×30 (column headers, product titles, "Compare boxes"/"Ask the supplier") · 600 ×25 (headline, row profit, "Next:", group heading, supplier name) |
| font-family | **2** | Inter ×204 · JetBrains Mono ×20 (the file name and every `Row NN · CODE` line, plus the run id and hash in the footer) |
| line-height | **4** | 17.4px ×122 · 20.3px ×84 · 26.1px ×17 (row profit) · 24.3px ×1 (headline). Row profit and headline share a size but not a leading |
| letter-spacing | **1** | normal everywhere |
| text colour | **7** | light: `oklch(0.15)` ×73 · `0.48` ×70 · `0.3` ×60 · `0.52` ×11 · link blue ×7 · `0.4` ×2 · `0.22` ×1. Six greys, three of them used 11 times or fewer |
| size+weight+family+colour combos | **21** | the real count of text styles a reader meets |
| spacing values (margin/padding/gap, whole page) | **20** | 4px ×185, 8px ×161, 12px ×108, 6px ×45, 16px ×27, 1px, 10px, 20px, 32px, 14px, 5px, 24px, 28px, 48px, plus computed 67.8px and 320.7px. In the price-list CSS the off-scale values are 6px, 3px, 2px |
| backgrounds / borders (whole page) | 12 / 5 | the one warm-coloured border is the callout |

### Drawer (Row 24, 81 text elements)

| Property | Distinct | Values |
|---|---|---|
| font-size | **4** | 14px ×50 · 12px ×24 · 18px ×3 (the headline *"Up to £65.34 a unit…"* **and** two figures, £111.00 and £74.64) · 20px ×4 (the picture-carousel arrows) |
| font-weight | 3 | 400 ×64 · 600 ×16 (headline and every section heading) · 500 ×1 |
| font-family | 1 | Inter only |
| line-height | 5 | 20.3, 17.4, 20, 26.1, 23.4px |
| letter-spacing | 1 | normal |
| text colour | 6 light / 7 dark | four greys, link blue, amber for "not priced" |
| style combos | 13 | |

**Contrast, computed from the oklch lightness:** in dark mode the `--plr-subtle` grey `oklch(0.55)` on the `oklch(0.145)` background is **about 4.1:1**, under WCAG AA's 4.5:1 for 12px text. It is used on 11 elements: the run id, export version, generated/imported times, hash and archive path. Every other text colour passes in both themes.

---

## 2. Does brand-source-finder have a type scale or tokens? Does anything enforce them?

**A scale exists and the page ignores it.** `frontend/src/styles/tokens.css` (origin/main) defines `--font-size-xs` 12 · `sm` 13 · `base` 14 · `lg` 16 · `xl` 18 · `2xl` 20 · `3xl` 24, radius tokens, font-family tokens, and `h1`–`h4`, `p`, `small` rules (lines 175–312).

**The price-list stylesheet does not use it.** `frontend/src/styles/sourcing-run.css` has 25 `font-size` declarations, all literal px (12px ×11, 14px ×9, 18px ×4, 20px ×1), and **0** `var(--font-size-*)`. Its own header says so: *"Nothing here is a system token: these are local names for the design's text ramp, scoped to .plr."* It defines its own ramp: `--plr-fg`, `--plr-t2`, `--plr-t3`, `--plr-t4`, `--plr-muted`, `--plr-subtle`, plus `--plr-next-line` and `--plr-next-bg` for the callout.

**No design policy.** There is no `docs/design-policy.md` in brand-source-finder. The brief says so: *"No project design policy exists, so only universal anti-AI-slop guardrails apply."*

**Enforcement: none that covers type, colour or spacing.**
- `frontend/package.json` runs `eslint` only. There is no stylelint and no token-usage check.
- `scripts/design-fingerprint-scan.sh` exists. Run over the v3 bundle and the shipped CSS and components, it finds **one** thing: the hatched placeholder's `repeating-linear-gradient` at `sourcing-run.css:595`. It does not see the callout. Its own output lists "size hierarchy", "monospace misuse" and "general colored borders" as **advisory, no machine signature**.
- The v3 build record (`_bmad-output/implementation-artifacts/design-implement-grid-price-list-run-v3-2026-09-26.md`) checks the callout's *content* (*"'Next:' callout naming the question to ask | yes"*) and records no fingerprint scan. PR #220 describes *"a Next callout"* as a feature.

---

## 3. What the briefs said, what they left to Design, and what Design used

Two briefs are in play. **Bundle (3)'s `uploads/` folder carries the long brief** (2,772 lines, `brief-sourcing-price-list-page-2026-09-26.md`), not the landed one. The landed brief (`~/Downloads/brief-sourcing-price-list-page-landed-2026-09-26.md`, 1,376 lines, 18:03) predates bundle (3) (18:39). The bundle does not show whether the landed brief was pasted in.

### What they said about type, hierarchy and layout

- Landed brief, binding test **TA1**: *"The most emphasised thing on the run page is the CHECK lines and what decides each… Not the SKIP tail, not the run's identifiers, not the failed-read count."*
- Landed brief, **TD0-price-list-run**: *"Within five seconds of the page loading, a reader can state the T0 answer and the next thing to do: get the Spain → Leipzig freight quote from the supplier."*
- Landed brief, **TD1-price-list-run**: *"…then the run's bookkeeping, failed reads and provenance, secondary."*
- Landed brief, Part 2 rule 12: *"An identifier may not become the subject of a sentence or the label of a row."* Rule 15: *"Colour may not be used to mean 'important'. An accent means one thing: someone must act, and nobody is acting yet."*
- Landed brief, advisory style floor: *"No hero strip or banner above working content… Three font sizes or fewer on a surface. Grouping by proximity… At least one real data row visible at rest; the header block no more than about a third of the viewport, and reading as the top of the list rather than a thing before it."*
- Long brief (the one in the bundle), §5 floor, advisory: *"2. No hero strips, banner panels, or marketing-style intros above working content"*; §5a: *"Three font sizes or fewer on the surface… Monospace only for codes and identifiers."*

### What was left to Design, the "mystery"

- Landed brief: ***"What IS yours:** typography and scale, spacing and rhythm, how the answer is made loud, grouping and proximity, table treatment, page furniture, and the weight system that makes the hierarchy real. A monochrome page has not been disciplined; it has declined to say what matters."*
- Long brief, Part 2: *"None of them tells you how to pass it — that is yours."* And later: *"how a blank, an unknown or a refusal is treated — wording, weight, placement, type — is yours"*, and *"This half is advisory because it is a judgement about weight, and weight is yours."*
- Both: *"No project design policy exists… Aesthetic-specific rules (… type family, etc.) are project decisions and should be added to `docs/design-policy.md`"*. Nobody wrote that file, so no concrete scale was ever handed over.
- Landed brief, open question: *"How does the page lead with 'nothing is a buy until one quote arrives' without a banner?"*
- The fork's own advice (`controls-and-attention.md` §2a) says the same: *"The type scale that makes the order visible… The concrete scale is the project's own (policy or house format), never this file's. `[tradeable]`, candidate."*

So the brief asked for a hierarchy, named no sizes, pointed to a policy that does not exist, and made every style rule advisory.

### What Design's bundle actually used

- **v2** (`Price List Run v2.dc.html`): font-size 12px ×45, 14px ×74, 18px ×10, weights 400/500/600, all inline literals. **No amber callout.**
- **v3** (`Price List Run v3.dc.html`): 12px ×20, 14px ×29, 18px ×5, weights 500/600, all inline literals, and it **introduced the callout**, line 36:
  `border:1px solid oklch(0.62 0.13 70);border-radius:4px;background:oklch(0.98 0.02 85)`, with *"Next: get the Spain → Leipzig freight quote from the supplier."* in 14px/600.
  The shipped CSS copies those two colours exactly (`--plr-next-line`, `--plr-next-bg`).

Design obeyed the one numeric type rule (three sizes) and answered the "without a banner?" question with a banner.

---

## 4. Why it reads like a ledger (live page, 1440×900)

1. **The list starts at 82% of the way down the screen.** The headline sits at y=137, the column header at y=617, the first product at y=739 and the second is cut off at y=845. You see 1½ rows at rest. The brief's advice was a header of about a third of the viewport, roughly 300px. There are **288 words** above the search box.
2. **A headline with no figure in it.** *"Nothing on this list is worth buying yet. Every profit once delivered to Amazon UK is before Spain → Leipzig, which nobody has priced yet, so each is the most the line could make."* That is 33 words to the first figure, which is "17" in the next paragraph. Our own budget is 12 (`artifact-policy.md` §5, and the brief's *"Headline to first figure within about twelve words"*).
3. **Every row is a ledger line led by a code.** 17 rows open with `Row NN · CODE` in 12px monospace, *above* the product name. That breaks the brief's rule 12 (*"An identifier may not become… the label of a row"*) and repeats the "template micro-chrome" tell from the research note (middle-dot meta strings, monospace for small data labels).
4. **Six columns, and the headers are sentences.** *"Profit once delivered, before Spain → Leipzig: the most it can cost a unit"* is a 15-word column header set in 12px/600 over three lines. The other five are 12px/500 grey.
5. **The same small phrases repeat down every row.** *"over the £30 floor"* ×17, *"90-day average"* ×12, *"few sales"* ×6, *"typical high"* ×6, *"Compare boxes"* ×5, *"UK listing we matched, though no listing qualified"* ×4, *"not live"* ×4. This is the brief's TA2 (*"No fact is stated twice at rest"*) broken at row scale.
6. **No weight difference between the answer and the evidence.** The headline and each row's profit are both 18px/600, so the eye cannot tell the page's answer from 17 per-row figures. In the drawer, the headline and two figures share 18px/600, and section headings are 14px/600, the same size as the body.
7. **Monochrome by accident, not by choice.** Six greys between L 0.15 and L 0.52 (0.48 and 0.52 sit side by side) carry every distinction. The brief warned: *"A monochrome page has not been disciplined; it has declined to say what matters."*
8. **Bookkeeping ends the page as well as opening it.** The footer repeats the import time already shown at the top, and splits the FX source across the top and the footer (see §6).

---

## 5. The yellow box at the top

**What it is.** `<div class="plr-next" data-testid="sourcing-next">` in `frontend/src/components/SourcingRunView.tsx:900` (origin/main), styled by `.plr-next` in `frontend/src/styles/sourcing-run.css:259`. It has a 1px border in amber `oklch(0.62 0.13 70)` (70% alpha in dark mode), a cream fill `oklch(0.98 0.02 85)` (amber at 10% in dark mode), 4px radius and 12×16px padding. It says *"Next: get Spain → Leipzig priced. It is question 1 on the right. Until it is priced, no line can be worth buying. WhatsApp ↗"*.

**Who introduced it.** Claude Design's bundle (3), `Price List Run v3.dc.html` line 36, with identical colour values. Bundle (2) had no such box. The implementer carried it over as specified (PR #220, *"a Next callout"*).

**Why it reads as AI.** It is the alert/admonition box: a pastel tint, a matching 1px border, a small radius and a bold lead-in word, placed as its own block above the working content. It is also warm cream with amber, and the fork's `design-standards.md` already warns against *"Amber/brown/cream combinations (reads as 'warning' or 'institutional')"* and *"Neutral palette with single restrained accent (blue, indigo, or green — not amber)"*.

**The strongest case for it, stated fairly.** Our own rule for accents is *"A border or an accent colour means: someone must act, and nobody is acting yet"* (`artifact-policy.md` §3, and brief rule 15). The freight quote is owed and nobody is chasing it, so **one** bordered block is within that rule's budget (≤1 on a breach, §5). The *meaning* is allowed. The *construction* is the problem: a separate tinted panel rather than weight and position inside the header. The fork's own template names that exact construction as the thing to avoid: *"no distinct background, border, or elevation separating the header from the list… If the header could be lifted onto an unrelated page unchanged, it is a banner."* (`brief-template.md`, compressed operational stack, item 1–2).

**Does the anti-AI research name it?** **Partly, and not this form.**
- The research note names the **coloured left or top accent stripe** (*"3–4px coloured border on one edge of a card or callout"*), the **icon in a pale tinted chip**, and the **second-generation escape tell** (*"warm cream + serif + terracotta"*). The fully bordered, evenly tinted notice box is not a row of its own.
- The note's section (c) defends *pale tint with darker same-hue text* on a **status label** as *"mainstream good practice"*. A reader could stretch that to cover this box, even though it is a panel, not a label.
- The note's list of eleven "sourced patterns the catalogue is missing" (26 Sep) has **not been merged**. `design-standards.md` was last changed on 19 Sep and has 0 matches for micro-chrome, default font stacks, escape tells, nested cards or low-contrast grey.

**Why nothing caught it: written down, advisory, and never checked.**

| Layer | Says what about this box | Can it fail the design? |
|---|---|---|
| Brief style floor (both briefs) | *"No hero strips, banner panels… above working content"* | No, advisory by `brief-binding-contract.md` line 28 (*"the AI-fingerprint floor, the comfort floor"* are advisory) |
| Brief open question | *"…without a banner?"* | No, it is an invitation |
| `brief-template.md` compressed stack | *"no distinct background, border, or elevation"* | No, *"review notes it"* |
| `design-standards.md` fingerprint taxonomy | left-border accent only; amber/cream as prose | Only the left-border row, P1 at review |
| `design-fingerprint-scan.sh` | matches `border-left: 2–9px solid` and Tailwind `border-l-N` only | No, it does not match a 1px all-round border and lists *"general colored borders"* as advisory |
| TD0 / TD1 / TD2 | answer and next action in 5 s; reading order; say once | **No, and TD0 rewards it.** A loud next-action box makes the five-second test easier to pass. TD1 says *"How provenance is made secondary is not judged"* |
| On-screen copy screen (STD-COPY-SCREEN-001, `check-copy-screen.js`) | checks vocabulary, CHECK/SKIP codes, deck rows | No, it reads strings, never CSS |

**The box does break one binding test.** TA2/TD2 ask for no fact twice at rest. On opening, the freight question is stated three times: in the headline (*"which nobody has priced yet"*), in the box, and in the right-hand panel (*"What would freight cost from you…"*). The box even refers to the panel (*"It is question 1 on the right"*). A reviewer applying TA2 could have caught it on those grounds.

---

## 6. What competes for attention at the top

Everything above the search box, in reading order. The "reads it?" column is an inference from what the owner does on this page (decide what to buy); the rule broken is quoted.

| # | Element (live text) | Why it is here | Rule it breaks |
|---|---|---|---|
| 1 | *"sent 2026-09-23-price-list-of-oral-b-23-09.xlsx on 23 Sep 2026, checked 26 Sep 13:29 UTC (SR-20260926-005) · an earlier check of this list exists"*, with the file name in monospace | identity and provenance | `artifact-policy.md` §4: *"A filename, tariff code, box id or SKU goes in the footer or is cut"*; brief rule 12; TD1 (provenance secondary) |
| 2 | 33-word headline, no figure | the answer | headline to first figure ≤12 (`artifact-policy.md` §5; the brief) |
| 3 | amber *Next* box | the next action | banner above working content (advisory floor); TA2 (the freight question said three times) |
| 4 | *"Profit once delivered takes every priced cost… The profit at the supplier's price leaves out freight, prep, customs and duty."* | explains the columns | landed brief: *"If it only explains the page to itself, cut it"* (to the footer or a collapsed layer) |
| 5 | the VAT paragraph (*"No Spanish VAT is added… Ask them before ordering."*) | a caveat that changes every figure | **Legitimate here.** The brief says caveats like this are *"stated once where they govern"*. It is the one top item that earns its place. It is repeated in full in the drawer |
| 6 | *"€1 = £0.86045, ECB reference rate of 25 Sep 2026."* | FX basis | provenance at the top (TD1). The FX source appears again in the footer as *"FX: ECB, fetched 2026-09-26 11:00"*. That line carries a different fact (the fetch time), so under TD2 it is split provenance rather than a strict repeat |
| 7 | *"Lines selling for under £30 on Amazon UK are skipped."* | the floor rule | repeated ×17 in the rows as *"£N over the £30 floor"* (TA2) |
| 8 | *"UK prices and sales as Keepa read them on 25–26 Sep, not live."* | data freshness | this is the basis of the figures (`presented-figures-declare-their-basis`), so it can stay, but as one short qualifier and not a separate line of type |
| 9 | *"Buy, check and skip calls made by amazon-removal-assistant; imported 26 Sep 13:38."* | audit | provenance at the top (TD1, `artifact-policy.md` §2 *"Provenance… conditional: footer only"*); **said twice**, the footer has *"imported 2026-09-26 13:38:09"* |
| 10 | right-hand panel *"1 question for the supplier, not yet answered"* plus Copy all / WhatsApp, with an empty right column below it down to y≈525 | the supplier question | TA2 (the same question as the box); the compressed-stack advice *"No large empty right half"*; it pushes the list down with a column that is mostly blank |

The attention rules that apply are the fork's `controls-and-attention.md` §2 (*"Every control spends from a fixed attention budget, and so does every word"*), TA1 (the CHECK lines should be most emphasised) and TD1 (bookkeeping and provenance secondary). On the live page, the CHECK lines start below 82% of the viewport.

---

## 7. Policy drift: what the design-handoff and design-implement workflows cite and enforce

Checked against `~/bmad-method-v6/custom/workflows/design/` (design-handoff, shared/) and `…/implement/design-implement` and `design-ingest`. "Cites" means the file path or rule id appears. "Enforced" separates deterministic (a script or test that can fail) from prose.

| Policy | Where · date | Handoff cites it? | Implement cites it? | Enforced? |
|---|---|---|---|---|
| Attention: TA1/TA2, TD0/TD1/TD2 ("where do we want the user looking") | fork `shared/controls-and-attention.md`, amended 2026-09-26 | **Yes**: brief-template, state-variables, step-01c and 7 more | Yes, 1 file (step-01 ingest) | **Prose.** The one deterministic piece (`validate-prose-consumers.mjs`) only checks that consumers still *reference* the file. It says itself: *"PROBABILISTIC throughout."* |
| T0 five-second test | fork `shared/brief-binding-contract.md`, 2026-09-26 | Yes (17 files) | Yes (5) | Prose. The contract's line 28 also makes **tokens, colour, the AI-fingerprint floor and the comfort floor advisory** |
| `artifact-policy.md`: border means act-now, bordered-block budget, identifiers to the footer, headline ≤12 words | amazon-removal-assistant, 2026-09-09 → 09-25 | **Only the ≤12-word rule**, second-hand via controls-and-attention §2a. §3 (border meaning), §4 (identifiers to footer) and §5 (bordered-block budget) are **not** cited | No | Deterministic **in amazon-removal-assistant only** (`src/artifact-policy-check.ts`). Nothing in the fork or brand-source-finder |
| `artifact-brief-policy.md` (rules 10–15: first line true alone, caveat stays beside its figure, no ID as subject, colour ≠ important) | amazon-removal-assistant, 2026-09-13 → 09-24 | Yes, via controls-and-attention §2a (rules 10–11); rules 12 and 15 appear in the landed brief text | No | Deterministic in amazon-removal-assistant (`artifact-brief-check.ts`) for its own briefs; prose in the fork |
| `document-design-format.md` (house type scale: 9.5 / 10–11.5 / 12–13 / 31px) | amazon-removal-assistant, 2026-09-15 → 09-17 | Only as an *"open tension, recorded and not resolved… nothing here applies it"* | No | Deterministic for amazon-removal-assistant's outward PDFs (`src/document-design.test.ts`); not applicable to web pages as written |
| Anti-AI UI research | `~/.claude/docs/research/anti-ai-ui-patterns-2026-09-26.md`, 2026-09-26 | Yes, one advisory paragraph in controls-and-attention §2a; summarised as advice in the landed brief | No | **Not merged.** `design-standards.md` (last changed 09-19) lacks all 11 "missing patterns"; the fingerprint scan is unchanged |
| On-screen copy screen STD-COPY-SCREEN-001 | fork `shared/on-screen-copy-screen.md`, 2026-09-26 | Yes (step-03, step-03c gate 1) | Yes (step-04 §5b) | **Deterministic** for strings (`tools/check-copy-screen.js`). Blind to layout and CSS by design |
| `presented-figures-declare-their-basis` (spot / 30-day / 90-day / owner-stated) | amazon-removal-assistant memory, 2026-09-20 | **No.** The nearest is `bison-product-family-policy.md` *"Every figure declares its VAT basis"*, which covers VAT only | No | Prose (memory) |
| Transcript / "Every reference says WHICH ONE" | amazon-removal-assistant `docs/transcript-policy.md` and CLAUDE.md, 2026-09-15 | **No** | No | Deterministic in amazon-removal-assistant only (`forwardable()` on two status surfaces) |
| Supplier relationship (invoice-the-UK-company question only; never mention Amazon) | `docs/supplier-buyer-profile.md` 2026-09-25; memory `supplier-enquiries-leave-amazon-out` 2026-09-24/25 | **No** | No | Prose. Relevant because the page composes supplier questions and a WhatsApp link |
| `human-facing-documents.md` (R1 say it once, R7 first line not misleading, R9 no caps for emphasis) | amazon-removal-assistant, 2026-09-12 → 09-17 | Yes, R7 and R9 via controls-and-attention §2a | No | Deterministic in amazon-removal-assistant (the reading-policy checks in `artifact-policy-check.ts`: repeated sentences, shouting caps, WCAG contrast); not in the fork |
| Provenance goes in the footer | `artifact-policy.md` §2 (*"conditional: footer only"*) and §4 | **No.** TD1 says only *"collapsed or visibly secondary"* and *"How provenance is made secondary is not judged"* | No | Deterministic in amazon-removal-assistant (budgets); nothing in the fork |
| Three font sizes or fewer; spacing from one scale | fork `design-standards.md` (2026-09-19) → brief-template §5a | Yes, as advisory "comfort floor" | Checklist only | Prose. The fingerprint scan names "size hierarchy" as *advisory, no machine signature* |
| No banner or tinted panel above the list; header ≤ ⅓ viewport | fork `brief-template.md` compressed stack, 2026-09-26 | Yes, as advisory (*"review notes it"*) | No | Prose |

**Pattern:** every rule that would have caught the page's problems either lives only in amazon-removal-assistant (where it is tested, but only against that repo's own generated pages), or reaches the fork as *advisory* text that `brief-binding-contract.md` says can never fail a design.

---

## 8. What amazon-removal-assistant already has that could become a gate

All paths in `~/code/amazon-removal-assistant`.

| Check | What it does today | Reuse for brand-source-finder |
|---|---|---|
| `src/artifact-policy-check.ts` `borderedBlocks()` + `checkArtifactPolicy({ borderedAllowed })` | counts bordered/accent blocks in rendered HTML, 0 when nothing is wrong, ≤1 on a breach | Point it at the rendered `/product/:id` DOM. It would count the callout, and that count could be tied to "a real owed action exists" |
| `wordsToFirstFigure()` | headline → first figure ≤12 words | Drop-in for the headline (live: 33) |
| `proseWords()` with a derived budget | prose-word ceiling excluding tables/footer | Budget the header block (live: 288 words above the list) |
| `repeatedSentences()` | fails any sentence over 25 characters that appears twice | Catches the FX and imported lines appearing twice, and per-row phrase repetition with a threshold |
| `shoutingCaps()` | all-caps runs | Guards the old BUY/CHECK pills |
| `contrastRatio()` / `themeTokens()` + the WCAG floor assertion | every text colour against every ground, per theme, read from the rendered page | Would fail the dark-mode `--plr-subtle` 4.1:1 today. It needs an oklch reader (it parses hex) |
| `classesUsed()` vs `classesDefined()` | markup classes the stylesheet never defines | Cheap and generic |
| `src/document-design.ts` + `document-design.test.ts` `describe.each` | one shared stylesheet module, "every token painted", all pages tested as a set | The **shape** to copy: one type/colour module the page must import, and a test asserting no literal `font-size`/colour outside it. The house *sizes* are print sizes and do not transfer |
| `src/artifact-gate.test.ts` | fails any page builder with no test measuring it | Same idea: every page route must have a rendered-DOM budget test |

**What does not exist anywhere yet:** a check that computed font sizes on a rendered page map to named tokens, and a check that the answer is rendered larger or heavier than the evidence. Both are cheap on the rendered DOM. The probe used for this audit already collects every computed size, weight, family and colour.

**Ceiling, stated plainly.** These checks prove counts and presence. They cannot prove the page reads well. A page can pass every budget and still bury the answer. TD0 and TA1 stay a reader's judgement.

---

## Coverage

- **Checked:** the live page and one drawer (Row 24, a line to look at before buying), in both themes at 1440×900; brand-source-finder `origin/main` source; both Design bundles and the briefs inside bundle (3); the landed brief and copy deck in Downloads; the fork's design and implement workflows; amazon-removal-assistant's policies and checks; the research note.
- **Not checked:** a skipped-line drawer or a "Compare boxes" drawer (different content, probably the same type system); widths other than 1440; the supplier page's price-list entry; the rest of the rows below the fold. That rows below the fold share the first rows' styles is inferred, not measured.
- **Access note:** the delegation said to read the page with the account API key. The hosted frontend only accepts that key at build time, so a browser with the key lands on *Sign in*. The page was read by signing in as the owner instead. No secret was printed.

Scratch evidence (probe, raw computed-style dumps, screenshots) is in the session scratchpad under `ui-audit-0927/`. It is not committed and will not outlive the session.
