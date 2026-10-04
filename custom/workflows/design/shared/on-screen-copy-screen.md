---
name: on-screen-copy-screen
description: 'Every string a person reads on a screen we design or build gets a plain-English screen before it ships: humanized, readable cold by the owner, free of internal vocabulary, and adding no claim its source did not make. The design-handoff brief carries it as a COPY DECK; design-implement runs the same screen on every user-visible string before merge.'
standard: STD-COPY-SCREEN-001
version: 2
ratified: 2026-09-26
amended: 2026-10-04 (v2 — §1a claims and chrome, §1b value, qualifier and basis)
---

# The on-screen copy screen

> **The owner, 2026-09-26, reading a price-list page:**
> *"It's the LLM language on the screen that makes no sense to a human... our humanizing email skill
> is really handy, but I want to broaden it basically, so we can do... a humanizing screening every
> time we do a UI or something... it could do this at a handoff level, but also this could also work
> like this. But it's just statements like this that is just, it makes absolutely no sense.
> 'Check · 13 — boxes compared, something else to settle'"*

**What this governs.** Every string a person reads on a surface we design or build: headings, group
titles, column heads, labels, statuses, empty states, error and refusal text, buttons, links,
tooltips, toasts, captions, and any sentence a producer system writes that the page shows as-is.
It does **not** govern code identifiers, log lines, commit messages, or data the user typed.

**Where it runs.** Twice, and the second is not optional because the first ran:

1. **design-handoff** — the brief carries a **Copy deck** (§1 below). Every string is screened before
   Gate 1 marks the brief ready (`../design-handoff/steps/step-03c-gate1-brief-ready.md` §1).
2. **design-implement** — the same screen runs on every user-visible string before merge, **including
   any string the implementation added that the deck never listed**
   (`../../implement/design-implement/steps/step-04-apply-and-deliver.md` §5b pass 4).

---

## 1 · The copy deck

A table, one row per distinct string. A string built from data is listed once as its template, with
the variable parts in braces (`{n} lines need a look`), and a family of producer sentences is listed
once per shape.

| # | Where | Kind | Current | What it means | Ships as | Screen |
|---|---|---|---|---|---|---|
| 1 | group heading, CHECK rows with a box record | claim | Check · {n} — boxes compared, something else to settle | these lines have had their boxes compared, but each still has an open point before buying | {n} more to look at before buying: the boxes have been compared, but each has one more thing to confirm | a✓ b✓ c✓ d✓ |
| 2 | marker over the lines left out of the total | chrome | — | a label for the group of lines that are not in the total | Not counted | a✓ b✓ c✓ d✓ |

- **Kind** is `claim` or `chrome` (§1a). It says who owns the wording.

- **Current** is what the surface says today (`—` for a new surface).
- **What it means** is written by someone who knows the system, in one sentence. It is the source the
  replacement is checked against for part (d), so it must be true and complete.
- **Ships as** is the string the page will carry. It is the only column the checker screens.
- **Screen** records the four parts below, each `✓` or `✗ <reason>`. A row with any `✗` is not ready.

## 1a · Claims and chrome — who owns the wording (v2, 2026-10-04)

> **Claude Design, 2026-10-04:** *"'Copy verbatim' and 'no heading or label may be added' are good rules
> for claims, but they also banned the chrome a professional UI relies on: column headers, section
> labels, 'Not counted'. The brief needed to split claims (verbatim, binding) from structural labels
> (the designer's call)."*

| | **Claim** | **Chrome** |
|---|---|---|
| What it is | Text that asserts a fact: a field's value and qualifier, a figure, a caveat, a status or state word, an empty-state or refusal sentence | Text that structures the page: a section heading, a column header, a row label, a group name, a marker such as *Not counted* |
| Who owns the wording | The brief. It ships word for word. | The designer. The deck's chrome rows are a starting point. |
| May the designer add one the deck never listed? | No. A claim the brief does not carry is an invented fact. | Yes. That is what a professional interface needs. |
| Is it screened? | All four parts, in the deck and again before merge | Part (c) always (our own vocabulary never reaches a screen); the other parts when design-implement screens the built strings |

**The boundary.** A label that carries a figure, a count or a status has become a claim (`13 not
counted` is a claim; `Not counted` is chrome). A column header that is a sentence is prose, not chrome.

**What "word for word" covers, said once so nobody has to guess:** every screen value and qualifier
(§1b), the action phrases, and deck rows marked `claim`. A basis sentence must appear in the opened
record; where it sits and how it is styled are the designer's. Section headings, column headers and row
labels are the designer's, within the label list the brief supplies. Nothing else is frozen.

**A count is never a reason to reword a claim.** If a claim does not fit a space or a checker's number,
the claim stays and the designer says so; the number is ours to fix or exempt
(`presentation-floor.md` §11).

## 1b · Value, qualifier and basis — the words for a data field (v2, 2026-10-04)

A data field is not one sentence on screen. It arrives split (`presentation-floor.md` §13), for
every state it can be in, into a **value** (what a buyer would say: 1–4 words or a number with its
unit, no semicolon), an optional **qualifier** (three words or fewer, small and grey under the value,
only where the value could be misread) and a **basis** (the original sentence, which appears only in the
opened record). **The producer writes the split. The designer never derives it**, and a field that
reaches a brief as one sentence is a brief defect. Each state has a tone from four (ink, muted, warning,
destructive); a bad state is one word plus its reason in grey. The words that tell two look-alike
states apart stay in the value or the qualifier.

**A missing value is a fixed word in grey**, one per kind: nobody looked · we asked and there is
nothing · does not apply · nothing set yet. Never a sentence, never a dash.

**Voice, for every string:** *you*, never *the owner* · none of the system's own words · short dates on
screen · one idea per line · an action is an instruction and a question is a question · a label is the
reader's question, not a field name · one word for whose move it is.

**The read-aloud test, applied to every row:** read it as if on the phone to a colleague. If it sounds
like a log entry, a sentence defending itself or a field name, rewrite it.

Every value, qualifier, state and worked example is derived from the real source data. One that cannot
be derived is written `cannot derive: <why>`; it is never invented.

A brief with no copy deck is not ready. A surface with genuinely no text is impossible in practice;
if one exists, the section says so in a sentence rather than being omitted.

---

## 2 · The four parts of the screen

**(a) Humanize.** Run the string through the `writing:humanize-text` rules: no AI vocabulary, no
em-dash stacking, no sycophantic or promotional register, sentence case, plain verbs. For short UI
strings the rules that fire most are em-dash pile-ups, noun stacks, and the colon-list shorthand that
reads like a log line. The `plain-english-outcome-editor` agent may be used as a read-only second
reader on the whole deck; it proposes, it never changes a fact.

**(b) The cold-reader test.** Could the owner, who was not in the build, say **what the string means
and what to do** from the string alone, with the rest of the page covered? A string that needs the
data model, the pipeline or the brief to decode fails. Counts need a noun (`13 lines`, never `· 13`).

**(c) No internal vocabulary.** These words and shapes never reach a screen, in any inflection:

| Banned | Why it fails |
|---|---|
| verdict · disposition · lane · gate · route · provenance | build vocabulary for how we reason, not what the reader decides |
| identity test · figure-listing · precondition | names of our own mechanisms |
| settle (settled, settling) · rests on | describe our bookkeeping, not the reader's next step |
| `CHECK` / `SKIP` as bare codes, or `Check ·` / `Skip ·` used as a label | an enum is not a sentence |
| an ID as the subject (`SR-20260926-003 …`, `B0C6MDD8V6 is …`, `search #188 …`) | a lookup key is not information; say the thing, put the ID after it if at all |

Any other upper-case code (`UNCLEAR`, `DORMANT-WEAK`, `EAN-UK`) is flagged for a look: common
acronyms a reader knows (VAT, EAN, ASIN, UK) pass.

**(d) The added-clause rule.** A rewrite may remove and reshape; it may never explain. Every clause the
replacement has that **What it means** does not — especially `because`, `so`, `which means` — is cut,
not softened. This is the same rule the global CLAUDE.md applies to every rewrite, applied here per
string.

---

## 3 · What is deterministic and what is not

`tools/check-copy-screen.js` checks **part (c)** mechanically over the **Ships as** column (and over a
plain list of strings for design-implement), plus labelled proxies: an ID-shaped first word, the
`label · number` shorthand, and (P4) a row marked chrome that carries a figure or a data value. Where
the deck has a `Kind` column, a row that is neither `claim` nor `chrome` is a hard finding (K1); Gate 1
requires the column of a new brief (B28). It cannot tell a claim from chrome by reading the words. It checks that every row records all four parts and that none is `✗`.
It **cannot** judge (a), (b) or (d): those are the screener's, and a green run means the words are
clean and the marks are present, never that the copy is good.

```bash
node ~/bmad-method-v6/tools/check-copy-screen.js --deck "<brief.md>" --strict
node ~/bmad-method-v6/tools/check-copy-screen.js --strings "<strings.txt>" --strict
```

Fixture: `copy-screen-golden-matrix.md` (the owner's own example as the failing case, with its fixed
form, and G6–G8 for claims against chrome). Suite: `npm run test:copy-screen`.
