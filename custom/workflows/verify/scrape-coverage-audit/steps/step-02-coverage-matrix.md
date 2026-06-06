---
name: 'step-02-coverage-matrix'
description: 'Run a live scrape sample read-only and build the per-field COVERAGE MATRIX — for each contract field, X/N records populated. Surface whole-column-empty (0/N) and low-coverage fields as loud gaps. Live values are ground truth.'
nextStepFile: './step-03-null-conflation-verdict.md'
---

# Step 2: Run the Coverage Matrix

**Goal:** Produce a per-field coverage matrix by running the scraper over a live sample of records read-only, then counting — for each contract field — how many of the `N` sampled records actually populated it. Turn the silent gaps loud: whole-column-empty (`0/N`) and low-coverage fields are surfaced, not normalized away.

---

## AVAILABLE STATE

- `{scraper}`, `{export_schema}`, `{contract_fields}`, `{record_id_field}`, `{source_url_field}`, `{scrape_access}`, `{server_live}`

## STATE VARIABLES (set in this step)

- `{sample}` — the sampled records (with `{record_id_field}` and `{source_url_field}` retained per record)
- `{coverage_matrix}` — per field: `{populated}/{N}` count + a representative populated value and a representative empty record id
- `{gaps}` — the subset of `{contract_fields}` that are whole-column-empty (`0/N`) or low-coverage, carried to step-03 for the live-source verdict

---

## GET A LIVE SAMPLE — READ-ONLY

Produce `N` real records using `{scrape_access}` from step-01. Prefer the freshest source that does not mutate anything:

1. **Fresh scrape (preferred).** Run the scraper's existing collect path against live tabs read-only — the same path the user runs, stopped at "records produced," never triggering upload/sync/write. Set `{server_live} = true`.
2. **Captured export fallback.** If a fresh local scrape isn't possible per `CLAUDE.md`, read the most recent real export the scraper already wrote. Set `{server_live} = false` and note the capture is static.

`N` should be large enough that a `0/N` is meaningful and small enough to inspect — a sample on the order of the records on one source page/listing is enough; the signal this workflow chases (a column empty for *100%* of rows) shows at small N. Retain `{record_id_field}` and `{source_url_field}` on every sampled record — step-03 needs them to drive Chrome to the exact source page.

**Sample-health pre-check (guards against the stub trap).** Before counting coverage, sanity-check that the sample is *records*, not stub/error content. If the sampled rows look like load-error shells, a JS app-shell, or carousel/deals content rather than orders (e.g. every row is `Unknown`, prices that match a promo carousel, no `{record_id_field}`), do **not** count them as populated records. Flag the suspect rows; they become a **fetch-failure** hypothesis carried into step-03, never coverage data. (This is the deals-carousel-nearly-leaked-in case: stub content must never inflate a coverage count.)

---

## BUILD THE COVERAGE MATRIX

For each field in `{contract_fields}`, count across the `N` sampled records how many are **populated** — and be precise about what "populated" means, because null-conflation starts here:

- A field is **empty** if it is `null`, `undefined`, `''`, whitespace-only, or a known sentinel the scraper emits on failure (`Unknown`, `N/A`, `-`). Treat those sentinels as empty, not populated — an extraction-failure sentinel is exactly the silent loss this workflow exists to catch.
- A field is **populated** if it carries a real extracted value.

Record per field: `{populated}/{N}`, one representative populated value (or "—" if none), and one representative *empty* record id (so step-03 knows which row to re-check on the live page).

```markdown
| Field            | Coverage | Sample value                          | Empty example (id) |
|------------------|----------|---------------------------------------|--------------------|
| Order ID         | 24/24    | 701-1234567-1234567                    | —                  |
| Order Date       | 0/24     | —                                     | 701-1234567-…      |
| Status           | 22/24    | Recibido                              | 701-7654321-…      |
| Item             | 24/24    | Echo Dot (5.ª generación)             | —                  |
| Price            | 23/24    | 31,99 €                               | 701-0000000-…      |
```

## FLAG THE GAPS — LOUD

From the matrix, carry forward to `{gaps}`:

- **Whole-column-empty (`0/N`)** — the core silent-failure signature. Every `0/N` field is a loud gap, surfaced as a P1 *hypothesis*. It is never normalized away, defaulted, or dismissed as "that field just isn't used here" — that judgement requires the live-source check in step-03, which has not run yet.
- **Low-coverage (`<N/N` but `>0`)** — a partial gap. The field works for some records and silently fails for others; the empty examples are exactly the rows step-03 re-checks against the live page.
- **Sample-health suspects** — rows the pre-check flagged as stub/error/carousel content; carried as a fetch-failure hypothesis.

A field at `N/N` is fully covered — it still gets a disposition row in step-04 (`accepted`), but it is not a gap and does not need a live-source verdict.

Do not classify any gap here. `0/N` looks identical whether the field is genuinely-absent, present-but-dropped, or a fetch artefact — distinguishing them is step-03's job, and it is invalid without the live-source check.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit/steps/step-03-null-conflation-verdict.md`.

---

## SUCCESS METRICS

- A live sample of `N` records was produced read-only (or a captured export was read, explicitly noted via `{server_live}`)
- Every `{contract_fields}` field has a `{populated}/{N}` coverage count over real values — live values, not the record type's "required" flags
- Failure sentinels (`Unknown`, `N/A`, `''`) counted as empty, not populated
- Every `0/N` and low-coverage field is in `{gaps}`; stub/carousel rows flagged as fetch-failure suspects, never counted as coverage
- No write, upload, or sync was triggered to obtain the sample

## FAILURE MODES

- Counting a failure sentinel (`Unknown`, blank) as a populated value — hides the exact silent loss being hunted
- Letting stub / deals-carousel / load-error rows inflate the coverage count (the carousel-leak case)
- Classifying a `0/N` here as "genuinely unused" without the step-03 live-source check (the silent-normalize-away error this whole workflow exists to prevent)
- Triggering an upload/sync while obtaining the sample (read-only violation)
- Sampling so few records that a real `0/N` can't be distinguished from chance, or so many that the sample can't be inspected
