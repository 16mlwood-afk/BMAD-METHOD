---
name: scrape-coverage-audit
description: 'Read-only audit of a scraper''s record set for silent data loss. Derives the extraction contract — the fields a scraper is supposed to populate per record — from the app''s own export schema / record type (never a hand-invented list), runs a live scrape sample into a per-field coverage matrix (X/N populated), and surfaces silent gaps: a whole-column-empty (0/N) field is flagged P1, never normalized away. For each gap it drives Chrome to the live source page and renders a null-conflation verdict — present-but-dropped (extractor missed it → producer fix), genuinely-absent-on-source (benign → document), or fetch-failure/stub (load-error/JS-shell/deals-carousel → retry-fallback lane). Every field gets an explicit disposition. Detection + routing only — never edits the scraper or data.'
---

# Scrape Coverage Audit Workflow

**Goal:** A scraper is supposed to fill in a known set of fields on every record. This workflow checks whether it actually does, across a live sample, and for every field it doesn't fill, says why. The one discipline that makes it work: the field set comes from the **app's own export schema / record type**, not from a list you made up. Measure real coverage against that, and a column that's empty for 100% of rows can't slip past as "just empty data."

**Your Role:** Think of yourself as the auditor who counts what's there, not the crew that fixes what's missing. You read the scraper's declared output contract, run a sample scrape read-only, tally coverage field by field, and for each gap open the live source page in Chrome to decide one thing: was the field *dropped*, *genuinely absent*, or *never really fetched* (a stub or error page)? That decision is the gate — a silent gap isn't a finding until you know which of the three it is. An empty column where the source page plainly shows the value is a producer bug, not benign data. The flip side is a stub page whose deals-carousel prices nearly got counted as order data — that's noise wearing a record's clothes. Get either one wrong and the operator chases a phantom or ships the loss.

**Key Principle — make silent gaps loud, then settle them on the live page.** A `0/N` column (empty for every record) is a *hypothesis*, not a verdict. It looks exactly the same whether the source genuinely lacks the field, the extractor dropped it, or the whole fetch returned a shell. Open the live source page in Chrome and only then call it. Three very different outcomes: the value IS on the page and the extractor missed it (**present-but-dropped** — fix the producer); the page really doesn't carry it (**genuinely-absent** — document the suppression); the page never loaded and you're looking at a stub (**fetch-failure** — route to retry/fallback, and never treat its content as record data). That call is what the workflow exists to make.

**Sibling workflows — what scrape-coverage-audit is NOT.**

- **vs `trace-flow`:** trace-flow maps the pipeline for one anchor (page/endpoint/table) — one flow, every stage, does the field render. This workflow sits one level up, at the record set. It doesn't trace a single field through stages; it asks, across all contract fields and many records, which are populated and which silently aren't. It does borrow two of trace-flow's habits: "live values beat static types" (the matrix comes from a live sample, never the record type alone) and "name every gap, don't propose fixes."
- **vs `data-quality-audit`:** data-quality-audit checks one dimension — a controlled vocabulary like supplier, currency, or status — for value defects. This workflow fills the gap between trace-flow (one pipeline) and data-quality-audit (one dimension): coverage across the whole record set. Its three-way verdict is data-quality-audit's render-gap-vs-data-rot distinction re-aimed at scraping — same question, "is the data actually wrong or does it just look that way," now applied to whether a field got extracted at all.
- **vs `wire-check`:** wire-check *repairs* broken connections. This workflow is read-only. It finds coverage gaps and routes them; it never edits the scraper or the data.
- **vs the data-quality root-cause rule (`quick-spec` / `maintenance-triage`):** that rule governs the fix — a present-but-dropped field gets fixed at the producing extractor, never by a one-time backfill. This workflow is the detection front door that feeds it: present-but-dropped findings route into `quick-spec` / `maintenance-triage`, where the producer fix happens under that rule.

---

## CRITICAL RULES

- **Read-only. Never edits the scraper or the data.** The audit runs a sample scrape and inspects live pages. It changes nothing. If a finding needs an extractor fix, a retry path, or a backfill, that's the routed lane's job, not this one's.
- **Derive the contract from the app's OWN schema/type — never an approximated or hand-invented field list.** The fields a scraper owes per record come from the real declaration: the export schema, the record TypeScript type, the CSV/column definition the export writes. Re-inventing "the fields it should have" is how you end up measuring coverage against the wrong contract. If the scraper has no declared field schema/type, that absence is itself a P1 finding — an undeclared record contract — not a licence to approximate. (Mirrors how data-quality-audit treats a missing normalizer.)
- **Coverage is measured over a LIVE sample — live values are ground truth.** The matrix counts `X/N` populated per field across real scraped records, not what the record type *says* is required. Types describe intent; the sample describes reality. (Carries trace-flow's "live values beat static types.")
- **A whole-column-empty field is loud — P1, never normalized away.** `0/N` (empty for 100% of records) is the silent-failure signature this workflow exists to catch. Surface it as a **P1** hypothesis and drive it to a live-source verdict. Never quietly drop it, default it, or wave it off as "that field just isn't used."
- **The verdict REQUIRES the live-source Chrome check.** A `0/N` or low-coverage field can't be classified from the scrape output alone, because present-but-dropped, genuinely-absent, and fetch-failure all produce *identical* nulls. The verdict only holds once Chrome has been driven to the live source page and the field confirmed present or absent there. No live-source check, no verdict — just an unresolved hypothesis.
- **Every field gets an explicit disposition.** The output is a per-field table where every contract field — fully covered, gapped, benign alike — has a row that's classified and routed. Nothing is silently dropped, and a benign gap states *why* it's benign. (silent-partial-implementation guard.)
- **Detect and route — do not fix.** Repair belongs to the routed lane: producer fix via quick-spec/quick-dev for present-but-dropped, retry/fallback handling for fetch-failure. This workflow stops at "here's the verdict and where it goes."
- **Present-but-dropped routes as a PRODUCER fix, not a backfill.** Frame the spec around the *extractor* — the selector, locale, or parse path that missed the value. A one-time re-scrape of the affected rows is an adjunct, never the whole fix. (Carries the `data-quality` root-cause rule.) Stub and fetch-failure content is never treated as record data; route it to retry/fallback handling.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{anchor}`, `{scraper}`, `{export_schema}`, `{contract_fields}`, `{record_id_field}`, `{source_url_field}`, `{sample}`, `{coverage_matrix}`, `{gaps}`, `{verdicts}`, `{dispositions}`, `{server_live}`, `{tab_id}`, `{scrape_access}`
- Sequential progression through 4 phases: establish contract → run coverage matrix → live-source null-conflation verdict → classify + route

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.
- **Exception — the grounding gate in step-01 still fires.** If the scraper and record contract can't be resolved from the input, halt even in autonomous mode. Auditing the wrong scraper against an invented contract produces confident nonsense. This is the one gate autonomy does not bypass.

### Input

The user provides a **scraper/export anchor** — enough to name *which scraper* and *which export or record type*:

- **A scraper name / entry point** — "the amazon.es inbounds scraper", `src/content/inbounds-collector.ts` — the producer whose coverage is in question.
- **An export or record-type anchor** — the export the scraper feeds ("the inbounds CSV"), the record type it emits (`InboundOrderRecord`), or a column from that export ("the `Order Date` column is empty"). This names the contract.

The cleanest input names both: scraper plus its export/type. A symptom anchor like "the Order Date column is blank for every row" works too — step-01 resolves it to the scraper and contract.

If neither is provided, ask which scraper to audit. **The grounding gate (step-01) is hard.** The workflow must be able to state verb + target — "audit the coverage of the **{scraper}** record set against the **{export_schema}** contract" — from the input alone. If the input doesn't pin a single scraper and a single record contract, halt and ask rather than guess. Picking the target for the user is intent autonomy, which this workflow does not take.

### Worktree Requirement

This workflow is **read-only**. It produces a diagnostic report and routes findings; it never edits the scraper or the scraped data, so no worktree is needed. The discipline matters: an audit run that "just fixed the obvious selector while I was there" is not this workflow. Detection and routing only. The routed lane — quick-spec/quick-dev — does the editing, in its own worktree, under its own rules.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit`

### Read-Only Scrape Access

The audit runs a sample scrape and inspects live source pages. Get the project's **read-only** way to do both from its `CLAUDE.md`:

- **Scrape sample** — how to produce a small batch of records read-only: the extension's existing collect/scrape path against a live tab, a captured export the scraper already wrote, or a documented dry-run. Store as `{scrape_access}`. Never trigger writes, uploads, or destructive sync to get the sample.
- **Live source page** — Chrome on the actual page the scraper reads (the marketplace order/inbounds page). Reuse the design lane's live-Chrome mechanism: `mcp__claude-in-chrome__*` tools, loaded via ToolSearch if not present. Store the tab as `{tab_id}` when step-03 engages it.

If the project documents that the scraper can't be run locally, fall back to the most recent real export plus a Chrome visit to the live source page. That's still the full toolkit — the step-03 live-source verdict is non-negotiable either way. Use `{server_live}` only to note whether the sample was freshly scraped or read from a captured export.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit/steps/step-01-establish-contract.md` to begin the workflow.
