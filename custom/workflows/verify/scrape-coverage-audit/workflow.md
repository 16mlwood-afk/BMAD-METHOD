---
name: scrape-coverage-audit
description: 'Read-only audit of a SCRAPER''S RECORD SET for silent data loss. Derives the extraction contract — the fields a scraper is supposed to populate per record — from the app''s OWN export schema / record type (never a hand-invented list), runs a live scrape sample into a per-field COVERAGE MATRIX (X/N populated), and turns silent gaps loud: a whole-column-empty (0/N) field is surfaced as P1, never normalized away. For each gap it drives Chrome to the live SOURCE page and renders a null-conflation verdict — present-but-dropped (extractor missed it → producer fix), genuinely-absent-on-source (benign → document), or fetch-failure/stub (load-error/JS-shell/deals-carousel → retry-fallback lane). Every field gets an explicit disposition. Detection + routing only — never edits the scraper or data.'
---

# Scrape Coverage Audit Workflow

**Goal:** Given a scraper and the record set it produces, audit whether every field the scraper is *supposed* to populate is actually being populated across a live sample of records — and for every field that isn't, render an honest verdict on *why*. The defining discipline: derive the field set the scraper owes from the **app's own export schema / record type**, then measure real coverage against it, so a column that is empty for 100% of rows can never hide as "just empty data."

**Your Role:** You are a coverage auditor, not a repair crew. You read the scraper's declared output contract, run a live scrape sample read-only, build a per-field coverage matrix, and for each gap drive Chrome to the live source page to decide whether the field was *dropped*, *genuinely absent*, or *never really fetched* (a stub/error page). You hold one distinction above all others: **a silent gap is not a finding until you know which of those three it is.** An empty column where the source page clearly shows the value is a producer bug masquerading as benign data; a stub page's deals-carousel prices that almost leaked in as order data are the inverse — content masquerading as records. Mislabel either and the operator either chases a phantom or ships the loss.

**Key Principle — turn silent gaps loud, then resolve them on the live page.** A 0/N (whole-column-empty) coverage result is a *hypothesis*, never a verdict. The empty column looks identical whether the field is genuinely absent on the source, the extractor silently dropped it, or the whole fetch failed and returned a shell. Resolve it against the live source page in Chrome and only then say which of three very different things is true: the field IS on the page and the extractor missed it (**present-but-dropped** — fix the producer), the page genuinely doesn't carry it (**genuinely-absent** — document the suppression), or the page never loaded and you're staring at a stub (**fetch-failure** — route to retry/fallback, never treat its content as record data). Producing that verdict honestly is the whole value.

**Sibling workflows — what scrape-coverage-audit is NOT.**

- **vs `trace-flow`:** trace-flow maps the *pipeline topology* for one anchor (page/endpoint/table) — one flow, every stage, does the field render. scrape-coverage-audit operates one altitude up: the **record set**. It does not trace a single field through stages; it asks, across *all* contract fields and *many* records, which are populated and which silently aren't. It borrows trace-flow's "live values beat static types" discipline (the coverage matrix is built from a live sample, never from the record type alone) and its "name every gap explicitly / don't propose fixes" stance.
- **vs `data-quality-audit`:** data-quality-audit interrogates *one dimension* (a controlled vocabulary — supplier, currency, status) for value defects. scrape-coverage-audit is the missing **altitude between trace-flow (one pipeline) and data-quality-audit (one dimension): the whole record set's field coverage.** Its present-but-dropped / genuinely-absent / fetch-failure verdict is data-quality-audit's render-gap-vs-data-rot distinction re-pointed at scraping — same load-bearing "is the data actually wrong, or does it just look that way" judgement, applied to whether a field was extracted at all.
- **vs `wire-check`:** wire-check *repairs* broken connections. This workflow is read-only — it detects coverage gaps and routes them; it never edits the scraper or the data.
- **vs the data-quality root-cause rule (`quick-spec` / `maintenance-triage`):** that rule governs the *fix* — a present-but-dropped field must be fixed at the producing extractor, never by a one-time backfill of the affected rows. This workflow is the **detection front door** that feeds it: present-but-dropped findings route into `quick-spec` / `maintenance-triage` so the producer fix happens there under that rule.

---

## CRITICAL RULES

- **Read-only. Never edits the scraper or the data.** The audit runs a scrape sample and inspects live pages; it changes nothing. If a finding needs an extractor fix, a retry path, or a backfill, that is the *routed lane's* job, not this workflow's.
- **Derive the contract from the app's OWN schema/type — never an approximated or hand-invented field list.** The field set a scraper owes per record comes from the app's export schema, the record TypeScript type, the CSV/column definition the export writes — the real declaration. Re-inventing "the fields it should have" is how an audit ends up measuring coverage against the wrong contract. If the scraper has **no** declared field schema/type, that absence is itself a P1 finding (an undeclared record contract), not a licence to approximate. (Mirrors how data-quality-audit treats a missing normalizer.)
- **Coverage is measured over a LIVE sample — live values are ground truth.** The matrix is `X/N` populated per field across real scraped records, not what the record type *says* is required. Types describe intent; the sample describes reality. (Carries trace-flow's "live values beat static types.")
- **Whole-column-empty is loud — P1, never normalized away.** A field that is `0/N` (empty for 100% of records) is the core silent-failure signature this workflow exists to catch. It is surfaced as a P1 hypothesis and driven to a live-source verdict. It is never quietly dropped, defaulted, or treated as "that field just isn't used."
- **The null-conflation verdict REQUIRES the live-source Chrome check.** A 0/N (or low-coverage) field cannot be classified from the scrape output alone — present-but-dropped, genuinely-absent, and fetch-failure produce *identical* nulls. The verdict is only valid once Chrome has been driven to the live source page and the field's presence-vs-absence confirmed there. No live-source check → no verdict, only an unresolved hypothesis.
- **Every field gets an explicit disposition.** Output a per-field table where every contract field — fully-covered, gapped, and benign alike — has a row, classified AND routed. Nothing is silently dropped; a benign gap states *why* it's benign. (silent-partial-implementation guard.)
- **Detect and route — do not fix.** Repair belongs to the routed lane (producer fix via quick-spec/quick-dev for present-but-dropped; retry/fallback handling for fetch-failure). This workflow stops at "here is the verdict and where it goes."
- **Present-but-dropped routes as a PRODUCER fix, not a backfill.** When routing a dropped field, frame the spec around fixing the *extractor* (the selector/locale/parse path that missed it); a one-time re-scrape of the affected rows is an adjunct, never the whole fix. (Carries the `data-quality` root-cause rule.) Stub/fetch-failure content is **never** treated as record data — route it to retry/fallback handling.

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
- **Exception — the grounding gate in step-01 still fires.** If the scraper + record contract cannot be resolved from the input even in autonomous mode, halt: auditing the wrong scraper's coverage against an invented contract produces confident nonsense. This is the one gate autonomy does not bypass.

### Input

The user provides a **scraper/export anchor** — enough to name *which scraper* and *which export or record type*:

- **A scraper name / entry point** — "the amazon.es inbounds scraper", `src/content/inbounds-collector.ts` — the producer whose coverage is in question.
- **An export or record-type anchor** — the export the scraper feeds ("the inbounds CSV"), the record type it emits (`InboundOrderRecord`), or a column from that export ("the `Order Date` column is empty"). This names the contract.

The cleanest input names both (scraper + its export/type). A symptom anchor ("the Order Date column is blank for every row") is also valid — the workflow resolves it to the scraper and contract in step-01.

If neither is provided, ask which scraper to audit. **The grounding gate (step-01) is hard:** the workflow must be able to state *verb + target* — "audit the coverage of the **{scraper}** record set against the **{export_schema}** contract" — from the input alone. If the input doesn't pin a single scraper and a single record contract, halt and ask rather than guessing (that is intent autonomy, which this workflow does not take).

### Worktree Requirement

This workflow is **read-only** — it produces a diagnostic report and routes findings; it never edits the scraper or the scraped data. No worktree is needed. The discipline matters: a scrape-coverage-audit run that "just fixed the obvious selector while I was there" is not this workflow. Detection and routing only. The routed lane (quick-spec/quick-dev) does the editing, in its own worktree, under its own rules.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit`

### Read-Only Scrape Access

The audit runs a live scrape sample and inspects live source pages. Resolve the project's **read-only** way to do both from its `CLAUDE.md`:

- **Scrape sample** — how a small batch of records can be produced read-only: the extension's existing collect/scrape path against a live tab, a captured export the scraper already wrote, or a documented dry-run. Store as `{scrape_access}`. Never trigger writes, uploads, or destructive sync to obtain the sample.
- **Live source page** — Chrome driving the actual page the scraper reads (the marketplace order/inbounds page). This reuses the design lane's live-Chrome mechanism: `mcp__claude-in-chrome__*` tools (load via ToolSearch if not present). Store the tab as `{tab_id}` when engaged in step-03.

If the project documents that the scraper cannot be run locally, the audit falls back to the most recent real export plus a Chrome visit to the live source page — that is still the toolkit; the live-source verdict in step-03 is non-negotiable. Store `{server_live}` only to note whether the sample was freshly scraped vs read from a captured export.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit/steps/step-01-establish-contract.md` to begin the workflow.
