---
name: 'step-03-null-conflation-verdict'
description: 'For each gap, drive Chrome to the live SOURCE page and render the null-conflation verdict: present-but-dropped (field is on the page, extractor missed it), genuinely-absent-on-source (page really lacks it — benign), or fetch-failure/stub (load-error/JS-shell/deals-carousel). The verdict is invalid without the live-source check.'
nextStepFile: './step-04-classify-and-route.md'
---

# Step 3: Null-Conflation Verdict — Resolve Each Gap on the Live Source Page

**Goal:** Turn each `{gaps}` hypothesis into a verdict by opening the live source page in Chrome and seeing *why* the field is empty. This is the classification that matters: an empty column, a dropped field, and a failed fetch all produce identical nulls in the matrix — only the live page tells them apart. It's data-quality-audit's render-gap-vs-data-rot distinction, re-aimed at scraping.

---

## AVAILABLE STATE

- `{scraper}`, `{contract_fields}`, `{coverage_matrix}`, `{gaps}`, `{record_id_field}`, `{source_url_field}`, `{sample}`

## STATE VARIABLES (set in this step)

- `{tab_id}` — the Chrome tab driven to the live source page
- `{verdicts}` — per gap: `{field, verdict, evidence}` where `verdict ∈ {present-but-dropped, genuinely-absent, fetch-failure}`

---

## THE THREE-WAY VERDICT

For every field in `{gaps}`, a `0/N` (or low-coverage) result stays a *hypothesis* until you confirm present-vs-absent on the live page. Exactly one of three things is true:

- **present-but-dropped** — the field **IS** on the source page and the extractor missed it. The value is visibly there — in another language, a moved DOM node, a different label — and the scraper's selector/parse path failed to read it. This is data rot, at the producer.
- **genuinely-absent-on-source** — the source page **really doesn't carry** the field for these records. The empty column is correct. Benign; document the suppression.
- **fetch-failure / stub page** — the page the scraper read was a **load-error shell, JS app-shell, or carousel/deals content**, not a real record page. The "nulls" aren't about the field at all; the whole fetch failed. Route to retry/fallback, and its content is never record data.

No live-source check, no verdict. A gap you can't check against a live page stays an *unresolved hypothesis* into step-04 — never quietly promoted to "genuinely-absent" just because the page wasn't reached.

---

## DRIVE CHROME TO THE SOURCE PAGE

Reuse the design lane's live-Chrome mechanism rather than reinventing it. Make sure the `mcp__claude-in-chrome__*` tools are available (load via ToolSearch if not), then for each gap:

### 1. Open the record's source page

Take a representative *empty* record from `{sample}` — the empty-example id step-02 recorded. Resolve its live source URL via `{source_url_field}`, navigate Chrome to it, and store the tab as `{tab_id}`.

### 2. Read the page

- Call `mcp__claude-in-chrome__read_page` on `{tab_id}` for visible text plus DOM structure.
- When the field's value needs precise locating, call `mcp__claude-in-chrome__javascript_tool` to query the specific node(s) — the order-date label and its sibling, the price block — and report the text actually present.

### 3. Read the verdict off what the page shows

- The value **is visibly on the page**, maybe under a different label or locale than the extractor expects → **present-but-dropped.** Evidence: the exact on-page text and where it sits. *This is the amazon.es `Order Date` case. The matrix shows `0/N`; the live page plainly reads "Pedido realizado 17 de abril de 2026." The extractor only knew the English "Order placed" and silently returned `''` on the Spanish label. Verdict: present-but-dropped → producer fix.*
- The value is **genuinely not on the page** for this record type → **genuinely-absent-on-source.** Evidence: the page region where it would appear, confirmed empty. Re-check a second empty record to be sure it isn't record-specific.
- The page itself is **a load-error / app-shell / deals-carousel** rather than a real record page → **fetch-failure / stub.** Evidence: the stub markers — error banner, empty app root, promo-carousel DOM, missing `{record_id_field}`. *This is the cancelled / load-error stub case. The row emitted a blank `Unknown`, and the carousel's prices nearly leaked in as order data. Verdict: fetch-failure → retry/fallback, never record data.*

### Fallback when Chrome can't reach the page

If `{source_url_field} = NONE` or the live page won't load, try the most recent captured HTML the scraper saw, if the project keeps one. If neither is available, the gap stays an **unresolved hypothesis** — record it as such for step-04. Don't default it to genuinely-absent; the fact that you couldn't check is itself worth surfacing.

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/scrape-coverage-audit/steps/step-04-classify-and-route.md`.

---

## SUCCESS METRICS

- Every `{gaps}` field has a verdict backed by a live-source observation (or is explicitly carried as an unresolved hypothesis when the page couldn't be reached)
- present-but-dropped verdicts cite the exact on-page text the extractor missed (locale/label/DOM-move evidence)
- genuinely-absent verdicts confirmed against ≥2 empty records, not one
- fetch-failure verdicts cite the stub markers and are kept strictly out of the record data

## FAILURE MODES

- Reading a verdict off the scrape output alone, without driving Chrome to the live page — the verdict is invalid, since present-but-dropped, genuinely-absent, and fetch-failure are indistinguishable in the matrix
- Defaulting an un-checkable gap to "genuinely-absent" instead of carrying it as an unresolved hypothesis (re-introduces the silent loss)
- Calling a present-but-dropped field "genuinely-absent" because the extractor's expected label wasn't found, when the value is right there under a different locale (the amazon.es Order Date error)
- Treating stub / carousel / load-error content as a real (genuinely-absent) record instead of a fetch-failure (the carousel-leak error)
