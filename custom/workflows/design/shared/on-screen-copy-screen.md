---
name: on-screen-copy-screen
description: 'Every string a person reads on a screen we design or build gets a plain-English screen before it ships: humanized, readable cold by the owner, free of internal vocabulary, and adding no claim its source did not make. The design-handoff brief carries it as a COPY DECK; design-implement runs the same screen on every user-visible string before merge.'
standard: STD-COPY-SCREEN-001
version: 1
ratified: 2026-09-26
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
plain list of strings for design-implement), plus two labelled proxies: an ID-shaped first word, and
the `label · number` shorthand. It checks that every row records all four parts and that none is `✗`.
It **cannot** judge (a), (b) or (d): those are the screener's, and a green run means the words are
clean and the marks are present, never that the copy is good.

```bash
node ~/bmad-method-v6/tools/check-copy-screen.js --deck "<brief.md>" --strict
node ~/bmad-method-v6/tools/check-copy-screen.js --strings "<strings.txt>" --strict
```

Fixture: `copy-screen-golden-matrix.md` (the owner's own example as the failing case, with its fixed
form). Suite: `npm run test:copy-screen`.
