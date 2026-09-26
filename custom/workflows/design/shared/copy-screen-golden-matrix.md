# Copy-screen golden matrix — the owner's example, and its fixed form

**Rule:** `on-screen-copy-screen.md` (STD-COPY-SCREEN-001).
**Checker:** `tools/check-copy-screen.js` · **suite:** `npm run test:copy-screen`.

**Why this file exists.** A rule nobody has tested against the case that produced it is not known to
work. G1 is the owner's own words about a live page on 2026-09-26; the suite asserts it fails and its
fixed form passes, so the matrix cannot drift from what the checker does. G2–G4 are the same page's
neighbouring strings. G5 is the silence case: ordinary plain copy must cost nothing, or the screen is
switched off within a week.

| # | Current (fails) | What it means | Ships as (passes) | What fires on the current form |
|---|---|---|---|---|
| G1 | `Check · 13 — boxes compared, something else to settle` | CHECK lines whose boxes have been compared, where something other than the box is still open | `13 more to look at before buying: the boxes have been compared, but each has one more thing to confirm` | V2 (`Check ·` as a label) · V1 (`settle`) · P2 (`· 13`) |
| G2 | `Also settle: thin market; priced from a dated last offer` | besides comparing the boxes, this line sells slowly and its price comes from an old offer | `Also worth knowing: it sells slowly, and its price is from an old offer` | V1 (`settle`) |
| G3 | `UK (matched; the verdict rests on no listing) · Oral-B iO3 · B0C6NBPWG5` | this is the listing we matched, but no listing passed, so the decision is not based on any listing's figures | `UK listing we matched, though no listing qualified · Oral-B iO3 · B0C6NBPWG5` | V1 (`verdict`, `rests on`) |
| G4 | `B0C6MDD8V6 may be the supplier's product, but the identity test could not decide` | we could not tell whether this listing is the same product as the supplier's line | `This listing may be the supplier's product; we could not tell for sure (B0C6MDD8V6)` | V1 (`identity test`) · P1 (ID as the first word) |
| G5 | `Show all 38 with their reasons` | — | unchanged | nothing: plain copy stays silent |

**The added-clause check on G1–G4 (part d).** Each replacement was read against *What it means*. G1
says "one more thing to confirm" and not "the boxes match": a compared box can be UNCLEAR, so
"match" would have been an added claim. G3 keeps "no listing qualified" and adds no reason why.
