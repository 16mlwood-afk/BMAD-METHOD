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

> **Originating case (source-of-truth doctrine).** A producer emitted `grand_total` via
> `max()` of divergent box-rows and over-stated spend; only live-site inspection caught it.
> Cross-border import/VAT estimates settle DOWNWARD, so the settled (lower) total is the
> amount paid. Full invariant: `inbound-flow:docs/financial-invariants/import-fee-settlement.md`.
