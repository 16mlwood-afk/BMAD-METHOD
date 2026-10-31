---
title: "Evidence — Claude Design's write-up on screen values (2026-10-04)"
---

# Evidence — Claude Design's write-up on screen values (2026-10-04)

**What this is.** Claude Design's own account of how it turned one project's audit sentences into
screen text, and what it says a brief must cover so the designer never has to do that again. The owner
supplied it on 2026-10-04 as `brief-guidance-screen-values.md`. It is filed here word for word, below
the line, as the evidence behind `custom/workflows/design/shared/presentation-floor.md` §13 and gaps
G21–G28 in `brief-gap-ledger.md`.

**How to read it.** Its METHOD and its CHECKLIST are what the fork adopted. Its WORDS are one project's
(a supplier price-list surface): *Transparency*, *Your pick*, *Supplier*, *Brand Source Finder* and the
rest are examples, not vocabulary for any other surface. A brief derives its own values and state words
from its own project's real data.

---

# Turning audit text into screen text: the method, and what the brief must cover

## Part 1. What I did to every field

Each data string held three things in one sentence: the value, a caveat, and the evidence behind them. I split them apart and rewrote each part by fixed rules.

**1. Split every string into three parts**
- **value**: what a buyer would say. 1–4 words, or a number with its unit. It goes in the row.
- **qualifier**: at most 3 words. Use one only when the value could be misread without it. It sits small and grey under the value.
- **basis**: the original sentence: source, date, what was or wasn't checked. It appears only in the opened record, under the value.

| Data string | value | qualifier |
|---|---|---|
| "read as per unit; the supplier has not confirmed it" | Per unit | unconfirmed |
| "no listing restriction reported; this reading does not cover Transparency" | None reported | Transparency not covered |
| "the supplier's own figure on the list" (stock 24) | 24 | their figure |
| "a draft message exists and has not been sent; sending it is the owner's act" | Send draft to supplier | — |

**2. Name the state, not the evidence**
Use a closed list of words for each field:
- Listing: Matched · Your pick · None held
- Restriction: None reported · Transparency codes · Brand approval needed · Can't list · Not checked
- Quantity: the figure · Not set · Range ready · Blocked · No recommendation

**3. Write actions as instructions and questions as questions**
- "Send draft to supplier", "Send the order", "Take a quantity"
- "Can they supply units with Transparency codes?", not "whether the supplier can provide units carrying…"

**4. Speak to the reader**
- "you" and "your", never "the owner"
- "Your pick", "set by you", "Your words"

**5. Strip the system's plumbing**
- Drop: rungs, sync, export, run, ledger, overlay, "the owner's act", "in this sample", "as read from the app".
- Where plumbing is the real cause, say it in the buyer's terms. "No longer saved in brand-source-finder" became "Unsaved in Brand Source Finder".

**6. Use fixed words for missing values, in grey**
- Not checked (nobody looked)
- None (we asked; there is nothing)
- n/a (doesn't apply)
- Not in sample (a sample slot with no figure)
- Not set (no quantity yet)

Never a sentence, never a dash.

**7. Bad states get one word, plus the reason**
- "Blocked" with "by Transparency"
- "No recommendation" with "order cadence not set"
- "Can't list" with "Amazon, 3 Oct"

The word goes in the destructive colour; the reason is grey.

**8. Keep the words that tell two states apart**
The must-never-claim pairs stay distinct in the value or qualifier, not in the basis:
- "Not checked" vs "None reported" + "Transparency not covered"
- "Your pick" vs "Matched"
- "Per unit" + "unconfirmed"

**9. Short dates**
"4 Oct" on screen. "received 2026-10-01" became "List of 1 Oct". ISO dates stay in the basis and in exports.

**10. Labels are a buyer's questions, not field names**
- Detail sections: Where it stands, UK listing, Restriction, Cost and stock, Quantity.
- Rows: Now, Asking, Raised, Reply, Status, Source, Before, Quoted, Set by.
- Never: Authority, Against, Standing, Basis.

**11. One idea per line**
No semicolons in a value. "drafted 4 Oct; drafted only; no correction disowns it" became three labelled rows: Drafted 4 Oct, Order ref, Corrections None.

**12. Name whose move it is with four words**
You · Supplier · Us · Nobody. "Your move" is the only one in the warning colour.

**Test applied to every value:** read the row aloud as if on the phone to a colleague. If it sounds like a log entry, rewrite it.

---

## Part 2. What the brief must cover next time

### A. The data contract
Every field the page shows carries `value`, an optional `qualifier` and `basis`. The producer writes them. The designer never derives them.

### B. A closed list of state words for each field
Give a table for each field: every state it can be in, the exact `value` and `qualifier` words, and the tone (ink, muted, warning, destructive). For example:

| Field | State | value | qualifier | Tone |
|---|---|---|---|---|
| restriction | none-found | None reported | Transparency not covered | ink |
| restriction | not-checked | Not checked | — | muted |
| restriction | not-eligible | Can't list | Amazon, {date} | destructive |
| sellAsin | owner-declared | Your pick | auto-match differed | ink |
| quantity | refused | No recommendation | {missing term} | destructive |

### C. An action phrase for each stage and move
One instruction per state where the move is the reader's: "Send draft to supplier", "Send the order", "Take a quantity". Plus the four whose-move words.

### D. The labels for the opened record
List the section names and row labels the designer uses, written as a buyer's questions.

### E. Voice rules
Second person. Short dates. None of the internal words on the brief's own banned list. No semicolons in values. Values of 1–4 words; qualifiers of 3 words or fewer.

### F. What "verbatim" covers
`value` and `qualifier` are verbatim. `basis` must appear in the opened record, but its placement and styling are the designer's. Section headings, column headers and row labels are the designer's, within the label list in D.

### G. A distinction check for each must-never-claim rule
For each pair the page must never confuse, give the two `value` strings and confirm they differ at rest. For example, "Not checked" vs "None reported".

### H. Worked examples
One row per field and state, taken from the real data, showing data string → value / qualifier / basis. The table in Part 1 is the model.

### I. The self-check before delivery
Read every row aloud. If any row sounds like a log entry, a sentence defending itself, or a field name, it fails.
