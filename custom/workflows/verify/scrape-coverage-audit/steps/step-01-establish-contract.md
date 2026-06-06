---
name: 'step-01-establish-contract'
description: 'Resolve the input (a scraper/export anchor or a coverage symptom) to a concrete extraction contract: the scraper entry point, the field set it owes per record derived from the app''s own export schema / record type, and the record-id + source-url fields the coverage matrix and live-source check need. Enforces the grounding gate.'
nextStepFile: './step-02-coverage-matrix.md'
---

# Step 1: Establish the Extraction Contract

**Goal:** Turn the input into a precisely-scoped audit target. By the end of this step you can state *"audit the coverage of the **{scraper}** record set against the **{export_schema}** contract"* and you hold the exact field set the scraper is supposed to populate per record — derived from the app's own declaration, never hand-invented.

---

## STATE VARIABLES (set in this step)

- `{anchor}` — the raw input (scraper name, export/type anchor, or the coverage symptom described)
- `{scraper}` — the resolved scraper / producer (file:export or entry point, e.g. `src/content/inbounds-collector.ts`)
- `{export_schema}` — the app's own declaration of the record shape (file:export), e.g. the record TypeScript type, the export's column definition, the CSV header builder — or `NONE`
- `{contract_fields}` — the ordered field set the scraper owes per record, read out of `{export_schema}` (e.g. `Order ID`, `Order Date`, `Status`, `Item`, `Price`, …)
- `{record_id_field}` — the field that identifies a record (lets the coverage matrix and the live-source check address a specific row, e.g. `Order ID`)
- `{source_url_field}` — the field (or derivation) that yields the live source page URL for a record, so step-03 can drive Chrome to it; or `NONE` if the URL must be reconstructed

---

## THE GROUNDING GATE (fires first, even in autonomous mode)

State **verb + target** from the input alone: the verb is always *audit coverage*; the target is the scraper's record set measured against a named contract. You must resolve the input to **one scraper AND one record contract**:

- If the input names a scraper and its export/type → both are explicit; proceed.
- If the input is a coverage symptom ("the `Order Date` column is blank for every row"):
  1. Identify the export/surface the symptomatic column belongs to.
  2. Trace that column back to the record type / export schema that declares it, and to the scraper that populates it — read the export writer, the record type, the collector.
  3. Name the scraper and the contract.

If the input cannot be pinned to a single scraper and a single record contract — it's too vague, or it implicates several scrapers/exports with no clear primary — **HALT** with:

```
Cannot ground this audit. The input "{anchor}" doesn't resolve to a single
scraper + record contract. Which scraper should I audit, and against which
export/record type? (e.g. "the amazon.es inbounds scraper, InboundOrderRecord")
```

Do not guess which scraper or contract the user meant. Choosing the target for them is intent autonomy, which this workflow does not take — and auditing the wrong scraper against an invented contract produces confident nonsense.

---

## DERIVE THE CONTRACT — FROM THE APP'S OWN DECLARATION

Once the scraper is named, resolve the field set it owes. This is the load-bearing input to the whole audit: get the contract wrong and the coverage matrix measures the wrong thing.

### 1. The scraper

Locate the producer entry point and the function that emits a record. Capture as `{scraper}` (file:export). Note where it writes its output (the export path, the in-memory record array) — step-02 reads a sample from there.

### 2. The export schema / record type — the contract source

Find the app's **own** declaration of the record shape. In priority order:

1. The exported record **TypeScript type / interface** the scraper emits (`InboundOrderRecord`, `OrderRow`, …).
2. The **export writer's column definition** — the CSV header array, the column-map, the spreadsheet schema the export builds.
3. The serializer/DTO the record passes through on the way out.

Read the field set out of it verbatim into `{contract_fields}` — same names, same order the export uses. Record `{export_schema}` as `file:export`.

- If a declaration exists → `{contract_fields}` is the contract. Carry it forward.
- If **no** declaration exists (the scraper builds ad-hoc objects with no type and the export has no fixed column set) → set `{export_schema} = NONE`. This is itself a finding: an **undeclared record contract**. There is no authoritative field set to measure coverage against, which means coverage gaps cannot be distinguished from intentional shape changes. Carry it forward; step-04 records it as P1. (Mirrors data-quality-audit's missing-normalizer finding.) For the sample to be inspectable at all, fall back to the **union of keys observed across the sample** as a degraded contract — and mark it degraded so step-02/04 weight it accordingly.

### 3. Record id + source url

For the matrix to address rows and for step-03 to drive Chrome to the right page:

- `{record_id_field}` — the field that uniquely names a record (so a gap can be pinned to specific rows and re-checked on the live page).
- `{source_url_field}` — the field (or derivation rule) that yields the live source-page URL per record. If the URL isn't stored on the record, note how it's reconstructed (order-detail URL pattern + id). Set `NONE` only if no live source page can be reached — and flag that, because the step-03 verdict depends on reaching it.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit/steps/step-02-coverage-matrix.md`.

---

## SUCCESS METRICS

- `{scraper}` named and grounded (verb + target stated from input)
- `{contract_fields}` read verbatim out of the app's own `{export_schema}` — not hand-invented
- `{export_schema}` is either a concrete `file:export` or an explicit `NONE` (carried as a P1 finding, with a degraded union-of-keys contract noted)
- `{record_id_field}` and `{source_url_field}` resolved so step-03 can reach the live source page

## FAILURE MODES

- Guessing the scraper or contract from a vague symptom instead of halting (intent-autonomy violation)
- Hand-inventing "the fields it should have" instead of reading the app's own export schema / record type — the cardinal sin; the matrix then measures the wrong contract
- Treating "no declared schema" as "no problem" instead of as a P1 finding
- Skipping `{source_url_field}` — step-03's live-source verdict then has nowhere to drive Chrome
