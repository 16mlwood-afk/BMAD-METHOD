---
name: 'step-04-classify-and-route'
description: 'Emit a per-field disposition table and route each finding: present-but-dropped to the producer-fix lane (quick-spec/quick-dev) framed under the data-quality root-cause rule; fetch-failure to retry/fallback handling; genuinely-absent documented as benign. Every contract field gets a disposition. Detection ends here; no fixes applied.'
---

# Step 4: Classify + Route

**Goal:** Turn `{coverage_matrix}` + `{verdicts}` into a report the operator can act on. Every contract field gets an explicit disposition — covered, gapped, benign alike — and every gap routes to its fix lane. Nothing is silently dropped. The workflow ends at the routing boundary; it applies no fixes.

---

## AVAILABLE STATE

- `{scraper}`, `{export_schema}`, `{contract_fields}`, `{coverage_matrix}`, `{gaps}`, `{verdicts}`, `{server_live}`, `{autonomous_mode}`

## STATE VARIABLES (set in this step)

- `{dispositions}` — the per-field disposition table

---

## ASSIGN SEVERITY

- **P1 (critical):** a whole-column-empty (`0/N`) field that came back **present-but-dropped** — silent total loss of a real field; or **no declared record contract** (`{export_schema} = NONE`); or a systemic **fetch-failure** putting stub rows in the record set.
- **P2 (moderate):** a **low-coverage** present-but-dropped field (partial silent loss), or an isolated fetch-failure on a few records.
- **P3 (low):** a **genuinely-absent** field (benign — state why), or a cosmetic gap. Benign still gets a row.

A genuinely-absent field is benign *only because the live page confirmed it.* That confirmation is the justification for the disposition, not an assumption.

---

## ROUTING RULES

| Verdict | Route | Framing |
|---|---|---|
| **present-but-dropped** | `maintenance-triage` (if a cluster of fields) or `quick-spec` → `quick-dev` | Frame the spec around the **extractor** (the selector / locale-matching / parse path that missed the value). A re-scrape of the affected rows is an adjunct, never the whole fix — per the `data-quality` root-cause rule. Cite the on-page text the extractor must learn to read. |
| **fetch-failure / stub** | `quick-spec` → `quick-dev`, framed on **retry/fallback handling** | "The scraper read a load-error/app-shell/carousel page and emitted record-shaped junk. Add load-success detection + retry/skip; never let stub content become a record." Explicitly call out keeping carousel/deals content out of the record path. |
| **genuinely-absent-on-source** | none (document) | "Confirmed empty on the live source for these records. Suppress without alarm; record the suppression so the next audit doesn't re-flag it." |
| **no declared record contract (P1)** | `quick-spec` | "Declare a record type / export schema for `{scraper}`; without it, coverage gaps can't be told from intentional shape changes — cleaning one run doesn't prevent recurrence." |
| **unresolved hypothesis** (live page unreachable) | re-run this audit once the source page is reachable | Do not route as a fix and do not mark benign — the gap is real but unclassified. Name what blocked the live-source check. |

For **present-but-dropped**, prefer `maintenance-triage` when several fields dropped together — usually one root cause, a locale or a page-layout change — and `quick-spec` for a single field. When in doubt, route to the producer fix rather than guess benign.

### Extractor lane — internal vs external (cross-repo)

A scraper's extractor frequently lives in **another repo** — a browser extension (e.g. bison-ops), a standalone scraper service — not in the consuming project. So for **present-but-dropped** and **fetch-failure** verdicts, set `producer_fix_lane`:

- **`internal`** — the extractor/parse path is in THIS repo → `quick-spec` → `quick-dev` as above.
- **`external:<producer_id>`** — the extractor is another repo/team (resolve `<producer_id>` against the registry in `shared/producer-defect-template.md`). **HARD never-drop branch**: do NOT route to in-repo `quick-spec`; you MUST emit (create-or-update) the producer-defect report per `shared/producer-defect-template.md`, judged against `shared/webhook-contract-charter.md`. A consumer-side boundary-harden (reject/flag stub-or-dropped values instead of ingesting them) is a **separate** in-repo `quick-spec`, never a substitute. Still stop at the routing boundary — the consumer cannot edit the extension's repo.

## EMIT THE DISPOSITION TABLE

Every contract field becomes one row, **including the fully-covered and benign ones** (disposition `accepted`, with the reason). This is the silent-partial-implementation guard: a reader can see at a glance that nothing was quietly skipped. Lead each row with the plain disposition the operator acts on; the verdict class and severity ride along as the audit trail.

```markdown
## Scrape Coverage Audit — {scraper}

**Contract:** {export_schema} | **Sample:** {N} records, {server_live ? "fresh scrape" : "captured export"}

| # | Field | Coverage | Verdict | Severity | Route | Disposition |
|---|-------|----------|---------|----------|-------|-------------|
| 1 | Order ID   | 24/24 | covered            | —  | —                     | accepted |
| 2 | Order Date | 0/24  | present-but-dropped | P1 | quick-spec → extractor | route → teach extractor the es-ES "Pedido realizado" label |
| 3 | Status     | 22/24 | fetch-failure (2 rows) | P2 | quick-spec → retry/fallback | route → detect stub page, retry/skip; 2 `Unknown` rows were load-errors |
| 4 | Gift Note  | 0/24  | genuinely-absent    | P3 | document               | accepted — confirmed not present on es source pages |
| … |

### Summary
- Present-but-dropped (producer fix): {n}
- Fetch-failure / stub (retry-fallback fix): {n}
- Genuinely-absent (documented benign): {n}
- Structural (no declared contract): {n}
- Unresolved (live page unreachable): {n}
- Fully covered: {n}

### Top priority
1. {one-line highest-severity finding + its route}
```

Write the report to `{implementation_artifacts}/scrape-coverage-audit-{scraper-slug}-{date}.md`.

## HAND-OFF

- **Autonomous mode:** don't halt. Present the report and, for each non-benign finding, give the exact next workflow to run, copy-paste-ready — e.g. *"Run `/bmad:bmm:workflows:quick-spec` framed on the `Order Date` extractor — teach it the es-ES `Pedido realizado` label."* Don't invoke them; routing is the boundary.
- **Interactive mode:** present the report, then offer to kick off the top-priority route and let the user choose.

Either way, the routed lane owns the actual change, in its own worktree under its own rules. This workflow has delivered its three things — the coverage matrix, the per-field verdict, the route — and stops.

---

## SUCCESS METRICS

- Every contract field (covered, gapped, and benign) has a disposition row — nothing silently dropped
- present-but-dropped routes to the producer-fix lane framed on the extractor, not a row backfill
- fetch-failure routes to retry/fallback handling; its content kept out of the record set
- genuinely-absent documented with the live-source justification; unresolved hypotheses named, not buried
- Report written to `{implementation_artifacts}`
- No fixes applied by this workflow; the scraper and the data are untouched

## FAILURE MODES

- Dropping fully-covered or benign fields from the table, so the reader can't tell what was skipped
- Routing present-but-dropped as a one-time re-scrape/backfill instead of an extractor fix (violates the `data-quality` root-cause rule)
- Routing fetch-failure content into the producer-fix lane as if it were real record data (the carousel-leak error)
- Marking an unresolved hypothesis benign because the live page couldn't be reached
- Invoking the routed workflow instead of handing off — this workflow detects and routes; it does not fix
