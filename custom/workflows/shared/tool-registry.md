---
name: tool-registry
contract_version: 1
description: 'Discoverable, governed registry of non-obvious tools/capabilities available to BMAD workflows across synced projects. A tool listed here is a SANCTIONED capability with a usage contract — when/when-not, how, and expected output — not a rumor. Consulted before saying "there is no tool for this" or "let us build one" (alongside the tool-discovery skill). First entry: Claude in Chrome as the live-site source-of-truth for finance-critical scraped values.'
---

# Tool Registry

A tool in here is a *sanctioned capability with a usage contract* — not a rumor. Before
you say "there's no tool for this" or "let's build one", check here first and run the
`tool-discovery` skill. Default to reuse before invention.

---

## Pasted images — the `[Image #N]` unreadable case (recovery path)

**Symptom.** The prompt carries `[Image #1] [Image #2]` and you cannot actually see them: no
description, no OCR, nothing to reason over. **The failure is SILENT** — nothing errors, so the
tempting move is to answer from the surrounding text and let the image go unmentioned. Dropping
screenshots in is a *primary* input mode here (design reviews, portal/shipment captures, error
screens), not an edge case, and a confident answer built on an image you never saw is the worst
possible outcome.

**This is a HARNESS limitation, not a fork bug** (`FG-2026-07-15-01`, `owner: harness-vendor`). Nothing
in this repo can fix the read path. What IS ours is the recovery, and never faking it:

1. **SAY SO IMMEDIATELY, before answering anything.** *"The images came through as `[Image #N]`
   placeholders — I can't read them."* Never proceed silently on the text alone. Never infer what a
   screenshot probably showed.
2. **Ask for a path, not a re-paste.** A file on disk is readable: `~/Downloads/shot.png`, or anywhere
   the `Read` tool can reach — it renders images. This is usually a one-line fix and is faster than a
   second paste, which often fails the same way.
3. **For a web page or app**, prefer Claude in Chrome (below) over a screenshot: the DOM is readable
   where a pasted pixel buffer is not.
4. **If the image is genuinely unavailable**, mark the answer **UNVERIFIED — image not read** and name
   what you would have checked in it. A conclusion is not "supported by a screenshot" you never saw.

---

## Claude in Chrome

Browser automation that drives the user's live Chrome session (`mcp__claude-in-chrome__*`).
Treat a live web app/page as the **source of truth** for values our systems scrape or ingest.

### Purpose
- Inspect live web apps/pages as the source of truth for values our systems scrape/ingest.
- Cross-check finance-critical fields (totals, fees, taxes, refunds) against what users
  actually see on the external site.

### When to use
- Producer fixes that change the *interpretation* of scraped money values (e.g. how a
  canonical `grand_total` is chosen).
- Contract disputes where internal systems disagree and the external site is the truth.
- Validating scraper correctness when defects involve "wrong totals" or "missing charges".

### When NOT to use
- High-volume scraping or primary ingestion — keep it targeted to a sample.
- Replacing APIs or normal data pipelines.
- Anything requiring sign-in/credentials the agent must not enter (financial logins,
  passwords, CAPTCHAs). If the relevant account/marketplace isn't already logged in,
  STOP and ask the user — do not authenticate.

### How to use (example flow — finance defect)
Given a defect brief with order IDs:
1. Open each order's page on the source site (try the most likely marketplace first;
   fall back across the user's other marketplaces per order).
2. Read the **labelled final amount** ("Grand Total" / amount actually paid), and confirm
   it reconciles against its own breakdown (items + shipping + VAT + import).
3. Compare against the producer's emitted value and the receiver's record.
4. Produce a short per-order comparison note: site total, emitted value, difference,
   and a DOM/text snippet or screenshot reference.

### Output expectations
- For finance defects, update the producer-defect brief's **Site verification** section
  (see `producer-defect-template.md` §7): orders checked, site totals, emitted values,
  and whether each matches.
- Treat this as **evidence for finance/contract decisions**, not a one-off comment.
- Mark orders you could not verify (e.g. a marketplace not logged in) as `n/a` with the
  reason — never assume a match you did not see.

### Connectivity gotchas (observed)
- The extension binds to ONE Chrome at a time. If tab actions land in the wrong window,
  the MCP session is bound to a different Chrome — use `list_connected_browsers` /
  `switch_browser`, or have the user open the Claude side panel in the correct window.
- Closing the bound Chrome drops the session; the replacement must reconnect (often a
  Chrome restart) before `tabs_context_mcp` works again.

### Example usage
- See `inbound-flow:docs/producer-defects/producer-defect-bison-ops-2026-06-28.md` →
  "Site verification (Claude in Chrome)" for a concrete validation pattern: 10 orders
  inspected on the live site, settled "Grand Total" compared to the canonical
  `grand_total`, results recorded as the permanent proof in the defect brief.

> **Originating case (source-of-truth doctrine).** A producer emitted `grand_total` via
> `max()` of divergent box-rows and over-stated spend; only live-site inspection caught it.
> Cross-border import/VAT estimates settle DOWNWARD, so the settled (lower) total is the
> amount paid. Full invariant: `inbound-flow:docs/financial-invariants/import-fee-settlement.md`.
