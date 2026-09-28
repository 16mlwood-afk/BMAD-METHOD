---
name: brief-gap-ledger
description: 'Append-only record of every gap a designer found in a design brief that the brief template and Gate 1 had let through. Each row names the rule added to the template and the check added to the validator, so the template learns from every review instead of being patched one brief at a time.'
standard: STD-PRESENTATION-FLOOR-001 §8
---

# Brief gap ledger — what designers found that the template let through

> **Owner, 2026-09-28, verbatim:** *"ensure this is systematic brief workflow fix not a one time brief
> patch."*

**What this is.** Claude Design reviews every brief before it builds anything
(`design-handoff/steps/step-05-design-prebuild-review.md`). Most findings are about one brief and
are fixed in that brief. Some reveal that the **template** had no rule for the thing at all, so
the next brief for another page, in another project, would have the same gap. Those are written
here, one row each. A row is only closed when the template carries a rule and, wherever the rule
can be checked by a machine, `tools/check-rendered-page.js --validate-brief` fails a brief that
breaks it.

**How to add a row.** Append, never rewrite. Give it the next `G` number, the date, the gap in one
sentence as the reviewer found it, the brief it was found in, the rule you added (and where), and
the check you added. The check column may say `none — <why a machine cannot judge this>`. A row with
no rule has not been closed and is not written here until it has one.

**The test that keeps it honest.** `test/test-rendered-page-check.js` asserts every seeded row names
its check, and the reconstructed brief the first nine were found in
(`test/fixtures/rendered-page/brief-v4-pre-review.md`) fails each check.

| # | Date | Gap, as the reviewer found it | Found in | Rule added | Check added |
|---|---|---|---|---|---|
| G1 | 2026-09-28 | The list was ranked by the size of the figure alone, so the weakest evidence (an unconfirmed listing, a stale price) led the page. | brand-source-finder price-list v4 brief | presentation-floor.md §8 G1; brief-template Part 2b §9: every ranked list orders by evidence-strength tiers first (confirmed and live, then unconfirmed, then stale or absent), then by magnitude | B12 — a brief that ranks a list must carry `ordering` with at least two tiers and a `thenBy` |
| G2 | 2026-09-28 | A product name was truncated with an ellipsis, and the part cut off was the only difference between two near-identical lines. | brand-source-finder price-list v4 brief | §8 G2; Part 2b §9: every truncated field names the token that must survive, and the brief lists the near-duplicate items in the data | B13 — truncation mentioned ⇒ `truncation` with `mustSurvive` and `nearDuplicates` (or `none: <how checked>`) |
| G3 | 2026-09-28 | The brief's own Copy deck said the same thing more than once ("before freight and prep" in three strings). | brand-source-finder price-list v4 brief | §8 G3: say-once applies to the deck itself; an unavoidable repeat is declared in `sayOnceExceptions` with its reason | B14 — a four-word phrase in more than one at-rest deck string (different slots) fails |
| G4 | 2026-09-28 | The brief was not self-contained: a deck row said "carried forward from the landed brief", and two views were to be kept "as it is". | brand-source-finder price-list v4 brief | §8 G4: every string and every referenced view is written out in this brief | B15 — placeholder deck rows, "as it is / as they are", and a pointer to another brief fail |
| G5 | 2026-09-28 | A state had no layout: nothing said what the drawer shows for a skipped line. | brand-source-finder price-list v4 brief | §8 G5; Part 2b §9: a states × views matrix, every cell a layout, "same as X" or "cannot arise: why"; empty, loading and error always present | B16 — `states` must cover every state × view and include empty, loading and error |
| G6 | 2026-09-28 | There was no responsive spec at all. | brand-source-finder price-list v4 brief | §8 G6; Part 2b §9: layouts at 1440, 1280 and one narrow width; drawer overlays or pushes | B17 — `responsive` needs 1440, 1280 and ≤ 1024, each with a layout, and a drawer mode where there is a drawer |
| G7 | 2026-09-28 | Feedback after an action (the toasts) was named but never designed: no position, look or duration. | brand-source-finder price-list v4 brief | §8 G7; Part 2b §9: actions ⇒ feedback position, look, duration and wording | B18 — actions present ⇒ `feedback` with position, look, duration and wording |
| G8 | 2026-09-28 | The brief spent 56 of its 60-word budget above the first item, so any designer's heading or label broke it. | brand-source-finder price-list v4 brief | §8 G8: the brief declares its own count and leaves 15% headroom | B19 — `attention.wordsAboveFirstItem` declared and ≤ 85% of the budget |
| G9 | 2026-09-28 | The brief's own notation ("·" between fields) was read as something to print. | brand-source-finder price-list v4 brief | §8 G9; Part 2b §9: the brief states its notation is not literal and specifies the separators the page prints | B20 — `notation` with `notLiteral` and `separators` |
| G10 | 2026-09-28 | Below the first item the page was text printed on a screen: six paragraphs of caveats under "Before you order", five long held questions each open with its trigger line, a stand-in note, and a six-line provenance footer. The floor limited prose only above the first item. Owner: *"not too happy when I scrolled down.. looks like text printed on a screen with no thought."* | brand-source-finder price-list v4 brief, as drawn in Claude Design v6 | presentation-floor.md §9; brief-template Part 2b §10: every section declares a form (cards / rows / disclosure / message-block) and a word budget; caveats are at most 5 labelled rows of ≤ 12 words; held, provenance, method and skipped sections are collapsed behind a disclosure with a one-line summary; an outbound message is a collapsed message block; the footer is at most 2 lines at rest | B21 — `sections` spec required, forms and budgets checked; R12 prose-wall (≤ 2 paragraphs in a row, ≤ 40 words each), R13 section-form, R14 footer-at-rest on the rendered page |
| G11 | 2026-09-28 | A label/value list was text printed in rows: in the drawer's *journey, cost by cost* a status column repeated the value (*not priced · not priced*), the status sat at a different x on every row, a bold sentence about our own tooling filled a value cell (*in the export; not in this handoff*), two-line explanations sat under each row, rows were as close as the lines inside a row, and the unpriced journey had no total. Owner: *"reads as a mess printed on a screen, not much thought about font size, spacing."* | brand-source-finder price-list v4 brief, as drawn in Claude Design bundle 6 (line drawer) | presentation-floor.md §10; brief-template Part 2b §11: a label/value row group is the named form `value-rows`: one value cell and one optional status badge per row, a fixed column grid, values right-aligned in tabular numerals, a value of money, a count or at most 4 words, an explanation of at most 12 words in the secondary style, rows further apart than the lines inside one, no internal vocabulary, a partial total labelled as partial | B22 — a `facts` / `value-rows` section declares columns, word caps, alignment, gaps, status values, total and `internalWords`; R15 row-cells, R16 row-grid, R17 internal-words, R18 row-total on the rendered page |
