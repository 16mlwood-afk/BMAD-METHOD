---
title: "Decision — the design brief shows what good looks like (2026-10-04)"
---

# Decision — the design brief shows what good looks like (2026-10-04)

**Owner instruction, 2026-10-04, verbatim:** *"we've narrowed it down to the brief being the problem. Take
this feedback and solve the gap."*

**What prompted it.** Claude Design, after several rejected iterations of one surface, wrote two notes
about the brief it had been given. They are quoted in full in §1 as evidence. In short: the brief said
what was forbidden and what had to be true and never showed what good looks like; its copy rules banned
the labels a professional interface relies on; it ranked no fact above another; it set type by kind of
datum; it said nothing about how a missing value should look; and at about 2,500 lines with checker
counts it read as a compliance exercise. The second note was about the words: every data sentence had
to be split by hand into a value, a qualifier and a basis.

**Where the live rules now sit.** `custom/workflows/design/shared/presentation-floor.md` §12 (the picture
of good and the five rules) and §13 (the words on screen); `shared/on-screen-copy-screen.md` §1a (claims
and chrome); `design-handoff/brief-template.md` (the opening, the Reference divider, the checker
appendix); `shared/brief-gap-ledger.md` G14–G28; Gate 1 checks B25–B35 in
`tools/check-rendered-page.js`.

**This file is the archive required before owner-tuned rule text is reduced.** The fork keeps no
`docs/decisions/owner-tuning-log.md`, so the archive is here, beside the two earlier design-brief
decision records. §2 holds every passage that was removed, compressed or moved out of the designer's
copy, verbatim, taken by script from commit `909460ec2401e61294f830ddddc0291f3d9d3a86`. Each whole file is also recoverable with
`git -C ~/bmad-method-v6 show 909460ec2401e61294f830ddddc0291f3d9d3a86:<path>`.

## 1. The designer's two notes, verbatim (evidence, not instruction)

> The brief told me what was forbidden and what had to be true, but never what good looks like, and I
> aimed at passing its checks rather than at a mature product. Most of your pointing-out was filling
> that gap.
>
> What was missing from the brief:
>
> There was no picture of good. You kept the existing page from me so I wouldn't anchor on it, which
> also removed the product's visual vocabulary. With only bans and budgets, the safest answer is a stack
> of compliant text, which is the ledger you kept seeing. One reference, like v7 now, would have done
> more than pages of rules.
>
> Copy rules blocked structure. 'Copy verbatim' and 'no heading or label may be added' are good rules
> for claims, but they also banned the chrome a professional UI relies on: column headers, section
> labels, 'Not counted'. The brief needed to split claims (verbatim, binding) from structural labels
> (the designer's call).
>
> Facts had no ranking. It listed about 15 facts per lead and said every caveat must stay beside its
> figure, but never which one fact leads. So everything rendered at the same weight. What fixed it was
> one focal line per lead and one leading value per block.
>
> Type roles followed data type, not position. 'Figure 16, body 14, mono for codes' means a single line
> naturally mixes three styles. The rule that works is one face, and size set by where the text sits in
> the hierarchy, never by what kind of datum it is.
>
> Nothing said how absence should look. Half the slots held 'no figure in this sample', and the brief
> made me print those words at full weight. One line saying an absent value is set small and grey would
> have removed a lot of noise.
>
> Over-specification hid the real job. At about 2,500 lines, with checker counts, the brief read as a
> compliance exercise, so I spent effort satisfying counts, like rewording sentences to stay under 25
> characters.
>
> My part: I checked my drafts against the brief, not against the question 'would this ship at a good
> product company?' I should have screenshot each draft and judged it as a product before handing it to
> you.
>
> To get one shot next time, add to the brief: One reference screen and a short list of components (a
> grouped table with aligned columns; an expandable record sheet of label and value rows; a status dot
> with the stage in text). A split between claims and chrome: claims verbatim, labels and headers free.
> A focal rule: each item leads with one value, and everything else is secondary. Type by position: one
> face, four sizes, never two sizes on one line. An absence rule: placeholders small and grey. A
> required self-review: render, screenshot, critique against those five points, then deliver.

The second note, on the words:

> I split each data sentence into three parts: a value: what a buyer would say, in 1-4 words; an
> optional qualifier of three words or fewer, only where the value could be misread; the full basis
> sentence, shown only when the lead is opened. Then I rewrote each part by fixed rules: states from a
> short closed list; actions as instructions and questions as questions; 'you' instead of 'the owner';
> no system terms, short dates, grey words for missing values; one idea per line; the words that tell
> look-alike states apart kept in the visible value, not buried in the basis. What the brief needs next
> time: the value/qualifier/basis split for every field, plus the state words for each field and their
> colours; an action phrase for each of the reader's moves; the labels for the opened record; voice
> rules; what 'verbatim' covers; a distinction check for each pair the page must never confuse; worked
> examples from the real data; a read-it-aloud check before delivery.

The designer's own write-up, `brief-guidance-screen-values.md`, was read before the change was finished
and is filed word for word at `docs/design-brief-screen-values-evidence-2026-10-04.md`. Where it
differs from the summary above, the file was followed. Three differences mattered: **value and qualifier
are the verbatim parts**, and the basis must appear in the opened record but is placed and styled by
the designer; **the producer writes the split** and the designer never derives it; and the file adds a
tone per state, a fixed grey vocabulary for the kinds of missing value, bad states as one word plus a
grey reason, a word for whose move it is, labels written as the reader's questions, and no semicolon in
a value.

## 1a. Conflicts with project policies — recorded, not resolved

No project policy was edited. Two conflicts are the owner's to settle:

1. **Type by datum.** `inbound-flow/docs/design-policy.md` (*"Monospace (`font-data` / JetBrains Mono)
   only for tabular numbers, IDs… and currency amounts in tables"*), `accounting-tools/docs/design-policy.md`
   (the same rule) and `cash-recovery/docs/design-policy.md` (*"monospace + `tabular-nums` for amounts"*)
   mandate a second typeface for a kind of datum. The fork's rule is now one typeface, size by position.
   A brief for those projects carries the project's rule and lists the conflict in its Part 5. The
   fork's own ledger-archetype text in the template (§2d, *"right-aligned, monospace, `tabular-nums`"*)
   was left as it is for the same reason: it restates those policies.
2. **"No content may be added."** `amazon-removal-assistant/docs/artifact-brief-policy.md` rule 13
   reads *"No content may be added. Not a heading, not a caption, not an explanatory sentence…"*, and
   §2 of the same file restates it. That is the rule the designer met as *"no heading or label may be
   added"*. The fork now carries only its claims half: no CLAIM may be added, and structural labels are
   the designer's. The project's own text still says headings may not be added.

## 2. Archive — prior text, verbatim, from `909460ec2401e61294f830ddddc0291f3d9d3a86`

### A1 · `custom/workflows/design/design-handoff/brief-template.md` lines 153–175

The "How this brief binds you" block — rewritten shorter and moved behind the Reference divider; its checker ids (P1–P9) moved to the checker appendix.

`````text
## How this brief binds you — read this first

> **"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"** — the product owner, 2026-09-19.

You do the heavy lifting on composition and wording. This brief binds you in two places: **Part 2, "What must be true"** — a short list of tests your finished design either passes or fails — and **Part 2b, the presentation floor**, which fixes the type scale (one size per job), the spacing and colours, what sits at the top of the page, the summary-then-items layout, and a list of banned patterns. Those are decided for you, and a rendered-page check fails a design that departs from them. Everything from the **Advisory guidance** heading down (suggested frames, composition, visual direction, the style parts of the design policy Part 2b does not name) is advice: take it, trade it, or ignore it for a better idea, and say what you did in your notes. A rule kept only for consistency with the rest of the product is marked **[tradeable]**.

> **Owner, 2026-09-27:** *"we've left basic gaps to Claude Design... no font size enforcement... that yellow thing at the top, the most AI pattern I've ever seen."* Part 2b closes those gaps. It is binding (`shared/presentation-floor.md`, STD-PRESENTATION-FLOOR-001).

```
  answer:       {page_answer}              # T0 — a reader states this within 5 seconds of the page loading
  dominant:     {dominant}                 # the ONE thing that leads; everything else is available-on-demand
  binding:      {truth_test_ids}           # the Part 2 tests
  floor:        Part 2b · P1–P9            # type scale, spacing, colours, attention plan, layout, banned patterns, sections below the fold, label/value row groups — binding, checked on the rendered page
  route:        {route}
  mutations:    {mutation_posture}         # none (read-only) | the jobs the operator must still be able to do (each is a Part 2 test)
  suggested:    frames {frames_list} · composition {composition} · page_mode {page_mode}   # ADVISORY — yours to change
```

Contract: `shared/brief-binding-contract.md` (STD-BRIEF-BINDING-001, v2). Reviewers downstream (`design-review-pr`, the `design-implement` conformance gate and its rendered-page check) may fail your design on a Part 2 test or a Part 2b floor item; every other departure is reported as a note.

**Five of the Part 2 tests are on every brief and are worth reading first — TC1, TC2, TA1, TA2, TF1.** They govern whether a control exists, how loud anything is, and what the page treats as work: every action control can say what its press tells the system that the system does not already know · no sentence instructs an action the page gives no way to perform · the most emphasised thing is the most consequential thing and no consequential control is dressed as chrome · no fact is said twice at rest · no system fault is rendered as a category of the operator's work. Source: `shared/controls-and-attention.md` (STD-CONTROLS-ATTENTION-001), which holds **no** colour, shape, placement, spacing or wording rule — those are yours, as always. §4f-c carries the evidence they are judged against.

{if {detail_surface_orders}}**And every drawer or panel answers its own question — TD0, TD1, TD2, once per detail surface.** A detail surface is judged when it opens, not only when the page loads: within five seconds a reader can say that item's answer and the one thing to do next; it reads answer → evidence (ranked by how much each would change the decision) → provenance and audit, the last collapsible or visibly secondary; and no fact appears on it twice unless the brief says why. The Part 2 "Detail surfaces" block names each surface's answer and order. How you make provenance secondary is yours.{endif}
`````

### A2 · `custom/workflows/design/design-handoff/brief-template.md` lines 212–218

Part 2 table header — the "How a reviewer checks it" and "Why (source)" columns moved to the checker appendix.

`````text
## Part 2 · What must be true — the binding tests

These are the ONLY things in this brief that can fail your design. Each is a test a finished design passes or fails. None of them tells you how to pass it — that is yours. A test written as a mechanism ("annotate every figure inline", "a permanent band at the top") is a brief defect; say so.

| Id | A finished design passes if… | How a reviewer checks it | Why (source) |
|---|---|---|---|
| T0 | A reader who has not seen the page can state **{page_answer}** within five seconds of it loading. | Show the render to a fresh reader for five seconds; ask what the page is telling them. | Owner, 2026-09-19 — the page must answer something. |
`````

### A3 · `custom/workflows/design/design-handoff/brief-template.md` lines 260–265

Detail-surface advisory type paragraph — the monospace sentence replaced by the one-typeface rule.

`````text
*Advisory, `[tradeable]`, and candidates for the owner's pending decision on binding style (none can
fail your design): emphasis by weight or size rather than capitals, with capitals kept for a lead-in
clause and for references; a type scale in which the answer is larger than the evidence and a label
quieter than its value. Monospace is best kept for codes a reader compares character by character;
money and counts in proportional type with tabular figures is a candidate, not a rule. Cited in
`controls-and-attention.md` §2a.*
`````

### A4 · `custom/workflows/design/design-handoff/brief-template.md` lines 370–393

Part 2b intro and the five-role type scale (answer / section heading / figure / body / caption; "Monospace only for codes") — replaced by four sizes set by position.

`````text
## Part 2b · The presentation floor — binding, and specified for you

*Standard: `shared/presentation-floor.md` (STD-PRESENTATION-FLOOR-001, 2026-09-27). This part is not a
suggestion and it is not yours to choose. The owner rejected a page in September 2026 because the brief
left type, colour and the top of the page to the designer: three font sizes did nine jobs, the headline
and every row's figure were the same size, provenance filled the top, and an amber notice box said the
next action a third time. So this brief decides those things, and a rendered-page check fails any design
that departs from them. Composition, wording and everything not named here are still yours.*

**Values from:** {floor_source — "project design policy §N" | "project tokens `{design_system_pointer}`, mapped role by role" | "fork default (the project declares no scale — see Part 5)"}

### 1. Type scale — one size, one job

| Role | Size | Weight | Used for | Never used for |
|---|---|---|---|---|
| answer | {type_scale.answer.size}px | {type_scale.answer.weight} | {type_scale.answer.use} | anything else — no figure, heading or label shares this size |
| section heading | {type_scale.sectionHeading.size}px | {type_scale.sectionHeading.weight} | {type_scale.sectionHeading.use} | figures, the answer |
| figure | {type_scale.figure.size}px | {type_scale.figure.weight}, tabular numerals | {type_scale.figure.use} | the answer; prose |
| body | {type_scale.body.size}px | {type_scale.body.weight} | {type_scale.body.use} | provenance, which is caption |
| caption / footnote | {type_scale.caption.size}px | {type_scale.caption.weight} | {type_scale.caption.use} | column headers that are sentences; methodology at the top |

No other size exists on this surface. **The answer is visually heavier than the evidence**: larger than
every figure and heading, and never the size a row's figure is set at. Monospace only for codes, and a
code is never a row's label.
`````

### A5 · `custom/workflows/design/design-handoff/brief-template.md` lines 442–471

Part 2b §6 markers, §7 policy table, §8 machine copy and the P1–P9 table — moved to the checker appendix.

`````text
### 6. Markers the design must carry

`data-answer` on the answer · `data-first-item` on the first actionable item · `data-item` on every item
card or group · `data-page` on the surface root. The rendered-page check reads them; a page without them
fails as unchecked.

### 7. The policies behind this part — cited so a reviewer can check the source

| Policy | Path | The rule you are held to |
|---|---|---|
{for p in {floor_citations}}| {p.id} | `{p.path}` | {p.rule} |
{endfor}

### 8. The machine copy — the checker reads this block; it must agree with the tables above

```json presentation-floor
{presentation_floor_json}
```

| Id | A finished design passes if… | How it is checked |
|---|---|---|
| P1 | Every text size is a role size above, and the answer size is used by the answer alone | `check-rendered-page.js` R1 |
| P2 | The answer is the largest text on the surface | R2 |
| P3 | No tinted callout, no edge stripe, bordered prose blocks within {bordered_allowed} | R3, R4, R5 |
| P4 | The answer reaches a figure within 12 words, and ≤ {prose_above_first_item} words sit above the first item | R6, R7 |
| P5 | Nothing is said twice | R8 |
| P6 | Every text colour meets AA in both themes, and nothing is in capitals for emphasis | R9, R10 |
| P7 | At 1440×900 the first item is fully visible in the top 40% | R11 |
| P8 | Below the first item every section is in its declared form (§10): no more than 2 paragraphs in a row, none over 40 words; caveats as labelled rows; held, provenance, method, skipped and message sections collapsed; the footer 2 lines at rest | R12, R13, R14 |
| P9 | Every label/value list is a grid (§11): one value and at most one badge per row, values right-aligned in tabular numerals on one edge, no sentence as a value, notes of 12 words or fewer, rows spaced apart, no internal words, a partial total labelled so | R15, R16, R17, R18 |
`````

### A6 · `custom/workflows/design/design-handoff/brief-template.md` lines 473–547

Part 2b §9–§11 with their checker ids and word counts in the designer's copy — the forms stay; the counts and ids moved to the checker appendix.

`````text
### 9. Completeness — what you would otherwise have to guess

*Standard: `shared/presentation-floor.md` §8 (G1–G9). Each item below is a gap a designer found in an
earlier brief that this template had let through (`shared/brief-gap-ledger.md`). The machine copy
above carries each one; Gate 1 fails the brief without it (B12–B20).*

1. **Order of every ranked list** — evidence first, then size. {for o in {ordering}}**{o.list}:**
   {o.tiers joined " → "}; within a tier, {o.thenBy}.{endfor} {or "No list on this surface is ranked."}
2. **Truncation** — {for t in {truncation}}**{t.field}** may be shortened; **{t.mustSurvive}** is
   never cut. Near-identical items in the data: {t.nearDuplicates}.{endfor} {or "Nothing on this
   surface is truncated."}
3. **Every state in every view** — one row per state × view; a cell is a layout, "same as <state>",
   or "cannot arise: <why>". Empty, loading and error are always rows.

   | State | View | Layout |
   |---|---|---|
{for s in {states_matrix}}   | {s.state} | {s.view} | {s.layout} |
{endfor}
4. **Widths** — {for r in {responsive}}**{r.width}px:** {r.layout}{if drawer} The drawer
   {r.drawer}s the page.{endif} {endfor}
5. **Feedback after an action** — {feedback.position}; {feedback.look}; stays {feedback.duration};
   wording: {feedback.wording}. {or "Nothing on this surface is an action."}
6. **Words above the first item** — this design puts **{words_above_first_item}** there, of a
   budget of {prose_above_first_item}: at most 85%, so your heading or label has room.
7. **This brief's notation is not the page's.** {notation.notLiteral}. On the page:
   {notation.separators}.

**The brief is self-contained (G4).** Every string you ship is in the Copy deck, and every view this
brief mentions is described here. Nothing is "as it is" and nothing is "in the earlier brief": if you
find a view or a string you cannot draw from this document alone, that is a brief defect — say so.

### 10. Below the first item — every section has a form, none is running prose

*Standard: `shared/presentation-floor.md` §9 (G10). The owner, on a design that met every check above
and still ended in six paragraphs of caveats, five open questions and a six-line footer: "looks like
text printed on a screen with no thought." Gate 1 fails the brief without the `sections` entry (B21);
the rendered page fails R12–R14.*

| Section (`data-section`) | Kind | Form | Words at rest | What shows at rest |
|---|---|---|---|---|
{for s in {sections}}| {s.name} | {s.kind} | {s.form} | ≤ {s.wordBudget} | {s.at_rest — rows: "≤ {s.maxRows} rows, a label then ≤ {s.rowMaxWords} words, the why on open" · disclosure: "{s.summary}" · message-block: "{s.summary}, with {s.controls}" · footer: "{s.linesAtRest} lines, then {s.disclosure}"} |
{endfor}

Every section below the items also carries `sample` in the machine copy: its at-rest strings for this
brief's worked instance, each written in this brief, whose words fit the budget (B24).
{if exemptions}**Declared exemptions** (§11 of the presentation floor; each prints on the check report):
{quoted_sources} are that source's own words, marked `data-source="<source>"` on the page and exempt from
{their checks}; {exemptions}; {internal_word_exceptions}.{endif} No provenance caption in the body
(*Named from…*, *Known because…*, *· the supplier's list*): the footer or a closed disclosure (R19).

Never, anywhere on the page: more than two paragraphs in a row, or one paragraph over 40 words.
Caveats are at most five labelled rows. Held questions, provenance, method notes and skipped lines are
collapsed behind a one-line summary. A message to send is a collapsed message block with Copy and its
channel. The footer is two lines at rest. A note about this brief (*sample*, *stand-in*) is never a
section of the page. Markers: `data-section` on each section, `data-row` and `data-row-label` on each
row, `data-footer` on the footer.

### 11. Label/value lists — a grid, not text in rows

*Standard: `shared/presentation-floor.md` §10 (G11). Gate 1 fails a `facts` section not specified this
way (B22); the rendered page fails R15–R18.*

{for g in {row_groups}}**{g.name}** (`data-row-group="{g.name}"`{if g.view}, on `{g.view}`{endif}):
columns {g.columns}; value right-aligned in tabular numerals, money, a count or at most
{g.valueMaxWords} words; {if note}an explanation of at most {g.noteMaxWords} words in caption under the
label; {endif}{if status}a status badge from {g.statusValues}, never the value's own words; {endif}rows
{g.rowGap}px apart, lines inside a row {g.innerGap}px apart; total: {g.total}.

| Label | Value | Status | Explanation |
|---|---|---|---|
{for r in {g.rows}}| {r.label} | {r.value} | {r.status or "—"} | {r.note} |
{endfor}
{endfor}
Never in a row group: {internal_words}. Markers: `data-row`, `data-cell="label|value|status|note"`,
`data-row-total` (and `data-total="partial"`).
`````

### A7 · `custom/workflows/design/design-handoff/brief-template.md` lines 1010–1021

The Copy deck section ("Use these words… every heading, group title, column head, label…") — split into claims and chrome.

`````text
## Copy deck — every string a person reads on this surface, screened

**Use these words.** Every heading, group title, column head, label, status, empty state, refusal, button, link, tooltip, toast and caption on this surface, one row each, with the words it ships as. A string built from data is listed once as its template (`{n} lines need a look`); a family of sentences a producer system writes is listed once per shape. You may reword a string, but any string you add or change goes through the same screen, and design-implement screens every string again before merge (`shared/on-screen-copy-screen.md`, STD-COPY-SCREEN-001).

**The screen, per row:** (a) humanized under the `writing:humanize-text` rules · (b) the owner, who was not in the build, can say what it means and what to do from the string alone · (c) none of: verdict, disposition, lane, gate, route, provenance, identity test, figure-listing, precondition, settle, rests on, `CHECK`/`SKIP` as bare codes, an ID as the subject · (d) the replacement adds no claim or cause that *What it means* does not carry.

| # | Where | Current | What it means | Ships as | Screen |
|---|---|---|---|---|---|
{for s in {copy_deck}}| {s.n} | {s.where} | {s.current or "—"} | {s.means} | {s.ships_as} | {s.screen: e.g. "a✓ b✓ c✓ d✓"} |
{endfor}

{State the count: "{copy_deck_count} strings; {copy_deck_changed} reworded from the current surface." A surface with no text says so in a sentence; the section is never omitted.}
`````

### B1 · `custom/workflows/design/shared/presentation-floor.md` lines 36–56

Presentation floor §1 — F1 "five named roles" and F7.

`````text
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
`````

### B2 · `custom/workflows/design/shared/presentation-floor.md` lines 58–91

Presentation floor §2 — the fork default five-role scale and "supersedes three font sizes".

`````text
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
`````

### B3 · `custom/workflows/design/shared/presentation-floor.md` lines 103–105

Presentation floor §3 "Also banned" — "monospace for anything but codes".

`````text
Also banned, carried from the fork's existing floor and now binding for a Part 2b surface: a hero strip
or banner above working content; a separate summary card or stat-card grid as the opener; monospace for
anything but codes; an identifier as the label of a row or the subject of a sentence.
`````

### B4 · `custom/workflows/design/shared/presentation-floor.md` lines 116–116

Presentation floor §4 — the artifact-brief-policy citation row ("nothing added").

`````text
| `artifact-brief-policy` | `docs/artifact-brief-policy.md` rules 10–15 | The first line and every heading stay true alone; a caveat stays beside the figure it qualifies; no identifier as a subject or a row label; nothing added; no chart where a number was given; colour never means "important". |
`````

### B5 · `custom/workflows/design/shared/presentation-floor.md` lines 274–287

Presentation floor §10 — the row-group rules table (values "at the figure role").

`````text
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
`````

### C1 · `custom/workflows/design/design-handoff/steps/step-03-generate-brief.md` lines 16–16

step-03 rule 00 (five roles).

`````text
00. **Part 2b SPECIFIES the presentation floor — it never delegates it (2026-09-27, `../../shared/presentation-floor.md`, STD-PRESENTATION-FLOOR-001).** Owner, verbatim: *"treat Claude Design like an idiot... we've left basic gaps to Claude Design... no font size enforcement"*. The type scale (five roles, one size each), spacing, colours with meanings, the attention plan, the item layout and the banned patterns are DECIDED in the brief with concrete values and bind. Rule 0's "token and colour detail is not copied" and rule 4's "point, do not copy" no longer apply to these seven things; they still apply to everything else in the design system. A sentence telling the designer that typography, scale, spacing or the weight system "is yours" is a HARD defect — Gate 1 fails it.
`````

### C2 · `custom/workflows/design/design-handoff/steps/step-03-generate-brief.md` lines 132–134

step-03 §2 Part 2b bullet, Part 3 bullet and Copy deck bullet.

`````text
   - **Part 2b — the presentation floor, EVERY run (`../../shared/presentation-floor.md`).** Fill every value; nothing in Part 2b is left to the designer. (a) **Source** `{floor_source}`: the project design policy / brand identity if it declares a scale, else the project token file (`{design_system_pointer}`) mapped role by role, else the fork default in presentation-floor.md §2 — and in that last case add a Part 5 line "the project should adopt or replace the default presentation floor". (b) **Type scale** `{type_scale}`: five roles — answer, sectionHeading, figure, body, caption — each one size, one weight, one `use` sentence; five DISTINCT sizes, answer largest. Two roles landing on one project token is resolved here (pick the neighbouring token), never handed over. (c) `{spacing_scale}` and `{colour_set}` (name · value · means · never means; one secondary grey; every text colour ≥ 4.5:1 on its ground in both themes). (d) **Attention plan:** `{next_action_once}` (the next action, said once, in the answer's line), `{first_item}`, `{prose_above_first_item}` (default 60), `{provenance_to}` (footer | disclosure) and `{provenance_items}` — name EVERY provenance and audit string this surface carries (FX rate and source, data dates, import stamps, file names, run ids, "figures before freight"-type bookkeeping); a caveat that changes a figure's meaning stays beside that figure instead. (e) **Layout:** `{item_pattern}` (cards | groups), `{at_rest_fields}` and `{at_rest_field_names}`. (f) `{repeat_risks}` — the facts this surface is most tempted to repeat (the TA2 list). (g) `{bordered_allowed}` — 0, or 1 only when an owed action nobody is chasing exists, with the reason in Part 5. (h) `{floor_citations}` — all ten rows of presentation-floor.md §4, verbatim. (i) **Completeness — Part 2b §9, from presentation-floor.md §8 (G1–G9, `shared/brief-gap-ledger.md`).** `{ordering}`: every ranked list, its evidence tiers strongest first (confirmed and live → unconfirmed → stale or absent) and `thenBy` its magnitude — never magnitude alone. `{truncation}`: every field that can be cut, the token that must survive it, and the near-duplicate items in the data (search the data for them; "none: <how checked>" when there are none). `{states_matrix}`: every state × every view with a layout, "same as <state>" or "cannot arise: <why>" — empty, loading and error always present (the binding twin of §2g's advisory state material). `{responsive}`: 1440, 1280 and one narrow width, each with a layout, and overlay or push for any drawer. `{feedback}`: where feedback after an action appears, how it looks, how long it stays and its wording (taken from the deck's toast rows). `{words_above_first_item}`: count the words this design puts above the first item; at most 85% of `{prose_above_first_item}`. `{notation}`: a sentence saying the brief's own marks are not printed, and the separators the page prints. **Self-contained:** no deck row may be a placeholder or pointer, no view may be kept "as it is", nothing may be "in the earlier brief" — write it out. (i2) **Sections below the first item — Part 2b §10, presentation-floor.md §9 (G10).** `{sections}`: EVERY section of the surface, the items included, each with a `kind` (items · caveats · held · provenance · method · skipped · message · footer · other), a `form` (cards · rows · disclosure · message-block) and a `wordBudget` at rest (≤ 60 for anything but the items). Caveats are `rows` (≤ 5, a label then ≤ 12 words, the why on open); held questions, provenance, method notes and skipped lines are a `disclosure` with a one-line `summary` (≤ 12 words); a verbatim outbound message is a `message-block` with its `controls`; the footer declares `linesAtRest` ≤ 2 and its `disclosure`. **Never write a section as "body text, in this order: …"** — that sentence is how the price-list v6 design ended in a wall of prose. (i3) **Label/value lists — Part 2b §11, presentation-floor.md §10 (G11).** `{row_groups}`: every cost breakdown, fact list or drawer money section is a `facts` / `value-rows` section with its columns, `valueMaxWords` ≤ 4, `noteMaxWords` ≤ 12, `valueAlign` right, `numerals` tabular, `rowGap` > `innerGap`, `statusValues` (never a word that says the figure is missing: the value says that), and `total` (partial, labelled so, when any row is unpriced). Write every row out with its value and note in those caps. `{internal_words}` → `internalWords`: at least export, handoff, pipeline, record, run, plus the project's own. **Never give a leg the same words as its standing and its figure.** (i4) **Exemptions and the brief's own budgets — presentation-floor.md §11 (G12, G13).** Every section below the items gets `sample`: its at-rest strings for the worked instance, copied from this brief's own prose; count them against the budget before handing over. Where the brief itself requires another party's words verbatim (supplier codes and titles, a listing's title), declare `quotedSources` and tell the designer to mark them `data-source`; where it requires a figureless answer on one view, or two real items that share a sentence, declare the narrow `exemptions` with the reason. Never reword the brief's own copy to get past a check. Put no provenance caption in the body. (j) `{presentation_floor_json}` — the machine copy of (b)–(i) in the shape of presentation-floor.md §5 and §8 (`standard`, `viewport` 1440×900, `typeScale`, `spacing`, `colours`, `attention` with `wordsAboveFirstItem`, `layout`, `banned` with all five keys, `budgets`, `citations`, and `ordering`, `truncation`, `states`, `responsive`, `feedback`, `notation`, `sections`, `internalWords` where a row group exists, optional `sayOnceExceptions`), agreeing value-for-value with the tables. **HARD FAIL (`unverified`, NOT deliverable)** if any value is missing or left as a placeholder — Gate 1 runs `check-rendered-page.js --validate-brief`.
   - **Part 3 — `{dominant}` and `{on_demand}`.** Exactly ONE dominant thing. `{on_demand}` names everything else the page carries, explicitly, so demoting it is legal. Two dominants is a defect: pick one and put the other in `{on_demand}`.
   - **Copy deck — EVERY run (`../../shared/on-screen-copy-screen.md`, STD-COPY-SCREEN-001).** Build `{copy_deck}`: every string a person reads on each §7 frame, from the source (component literals AND producer-written sentences the surface shows as-is), one row per string or per template/shape, with *What it means* in one true sentence and *Ships as* screened on all four parts. Record each part `✓` or `✗ <reason>`; a row with a `✗` is rewritten, never shipped. **HARD FAIL (`unverified`, NOT deliverable)** if the section is absent or any row is unscreened — Gate 1 runs `tools/check-copy-screen.js --deck` over it.
`````

### C3 · `custom/workflows/design/design-handoff/steps/step-01-gather.md` lines 14–14

step-01 blank-canvas rule.

`````text
- **NEVER describe the current page layout, component structure, or information grouping.** The current UI was built by a developer. Describing it anchors the designer to implementation choices.
`````

### C4 · `custom/workflows/design/design-handoff/steps/step-02-audit-design.md` lines 76–76

step-02 "Set {reference_pages} from observing which pages look best".

`````text
Set `{reference_pages}` from observing which pages look best.
`````

### C5 · `custom/workflows/design/design-handoff/steps/step-05-design-prebuild-review.md` lines 28–43

step-05 pre-build review paste.

`````text

Hand the owner (or the Claude Design session) this paste, filled in. It is the whole of the first
message; the build prompt waits for §3.

```
Connect to {github_repo_url} and read `{output_path_relative_to_repo_root}` on main. Do NOT design
anything yet.

Review this brief against its own tests, as the person who has to build from it:
- Part 2 (T0, T1…Tn, TD0–TD2, TC1, TC2, TA1, TA2, TF1) and Part 2b (P1–P9, §9 completeness, §10 sections below the first item and §11 label/value lists).
- For each frame the brief asks for: could you draw it from this document alone?

List every place you would have to GUESS, one numbered line each, saying what is missing and where:
a state with no layout, a view referred to but not described, a string not in the Copy deck, a list
whose order is not stated, a truncation with no rule for what survives, a width with no layout,
feedback after an action with no position or duration, a word budget with no room left, a mark in
`````

### C6 · `custom/workflows/design/design-handoff/steps/step-04-deliver.md` lines 429–436

step-04 build paste ("For {consumer}").

`````text
For {consumer}
{If {consumer} is Claude Design: the FIRST paste is the pre-build review in `step-05-design-prebuild-review.md` §1, not the build. Give that paste here instead of the lines below; the lines below are the build paste, handed over after step-05 has folded the review back into the brief.}
- Connect to {github_repo_url} and use `{output_path_filename}` on main as the SOLE active source brief for `{route}`.
- Interpret it as a {page_mode} {scope: redesign | new} of `{route}`.
{If scope is redesign / change_class material_revision:}
- Do NOT treat the prior implementation or any superseded brief as binding layout precedent — recompose freely.
- Preserve the brief's required frames (§ Surface Inventory), state semantics, and any data/least-privilege boundaries it names.
- {Composition guardrail from the brief: e.g. "It is a station, not a dashboard — avoid worklist/owner/analytics chrome." Derive this one line from {page_mode} + {composition_provenance} + the brief's hard constraints; do not invent constraints the brief doesn't carry.}
`````

### D1 · `custom/workflows/design/shared/claude-design-prompt.md` lines 29–29

claude-design-prompt.md item 6 PRESENTATION FLOOR ("paste the five-role type scale").

`````text
   - **PRESENTATION FLOOR — must hold, and SPECIFIED, never left to the designer** (`presentation-floor.md`, STD-PRESENTATION-FLOOR-001, binding since 2026-09-27): paste the five-role type scale with sizes (answer · section heading · figure · body · caption, one size each, answer largest), the spacing scale, the colours with their one meaning each, the attention plan (answer at the top with a figure within 12 words; next action said once, never in a box; first item fully visible at 1440×900 in the top 40%; provenance and audit text in the footer or a disclosure), the layout (summary, then cards or groups, detail on open), the banned patterns (tinted callout boxes, coloured edge stripes, stacked badges, all-caps labels, the same fact twice), and the markers `data-answer`, `data-first-item`, `data-item`. Below the first item (§9): every section in its declared form — caveats as at most five short labelled rows, held questions, provenance, method notes and skipped lines collapsed behind a one-line summary, a message to send as a collapsed message block with Copy, a two-line footer — never more than two paragraphs in a row; markers `data-section`, `data-row`, `data-row-label`, `data-footer`. A label/value list (§10) is a grid: one value and at most one badge per row, values right-aligned in tabular numerals on one edge, no sentence as a value, notes of at most 12 words, rows spaced apart, none of our own tooling's words, a partial total labelled partial; markers `data-row-group`, `data-cell`, `data-row-total`. Mark another party's verbatim words (a supplier's code or title, a listing's title) `data-source="<source>"` as the brief names them, and put no provenance caption in the body (§11). Never write "typography and scale are yours".
`````

### D2 · `custom/workflows/design/shared/design-standards.md` lines 59–66

design-standards.md §4 Typography ("Monospace only for codes… Maximum 3 font sizes").

`````text
### 4. Typography Is 80% Of Design

- System font stack for UI: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Monospace only for codes, IDs, technical values
- Maximum 3 font sizes per component. If you need 4+, the hierarchy is wrong.
- Body: 14-15px, `line-height: 1.5-1.6`, color `#333` or `#374151`
- Secondary: 12-13px, color `#6B7280` or `#9CA3AF`
- Headings: differentiated by weight (600-700) and size, not color or decoration
`````

### D3 · `custom/workflows/design/shared/on-screen-copy-screen.md` lines 33–50

on-screen-copy-screen.md §1 The copy deck.

`````text
## 1 · The copy deck

A table, one row per distinct string. A string built from data is listed once as its template, with
the variable parts in braces (`{n} lines need a look`), and a family of producer sentences is listed
once per shape.

| # | Where | Current | What it means | Ships as | Screen |
|---|---|---|---|---|---|
| 1 | group heading, CHECK rows with a box record | Check · {n} — boxes compared, something else to settle | these lines have had their boxes compared, but each still has an open point before buying | {n} more to look at before buying: the boxes have been compared, but each has one more thing to confirm | a✓ b✓ c✓ d✓ |

- **Current** is what the surface says today (`—` for a new surface).
- **What it means** is written by someone who knows the system, in one sentence. It is the source the
  replacement is checked against for part (d), so it must be true and complete.
- **Ships as** is the string the page will carry. It is the only column the checker screens.
- **Screen** records the four parts below, each `✓` or `✗ <reason>`. A row with any `✗` is not ready.

A brief with no copy deck is not ready. A surface with genuinely no text is impossible in practice;
if one exists, the section says so in a sentence rather than being omitted.
`````

### D4 · `custom/workflows/design/shared/brief-binding-contract.md` lines 50–62

brief-binding-contract.md §1a — the seven bound things, including "a type scale of five named roles".

`````text
Version 1 of this contract put tokens, colour, the AI-fingerprint floor and the comfort floor in the
advisory column, *"a note, never a failure"*. The price-list page audit of 2026-09-27 traced a rejected
page straight to that line: the brief told the designer *"What IS yours: typography and scale, spacing
and rhythm… and the weight system"*, only the five-second tests bound, and a tinted notice box is the
cheapest way to pass a five-second test. So v2 moves seven things into the binding column, **specified
in the brief rather than delegated**, and checked on the rendered page:

1. a type scale of five named roles (answer, section heading, figure, body, caption), one size each;
2. spacing tokens; 3. a colour set, each colour with one meaning; 4. the attention plan — the answer at
the top, the first actionable item above the fold at 1440×900, a word budget above it, provenance and
audit text in the footer or behind a disclosure; 5. the layout — a summary, then items as cards or
groups, detail on open; 6. the banned patterns — tinted callouts, coloured edge stripes, stacked badges,
all-caps labels, the same fact twice; 7. the answer visually heavier than the evidence.
`````
