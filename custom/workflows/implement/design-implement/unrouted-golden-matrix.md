---
status: current
version: 1
scope: "design-implement step-04 — the entry-point / discoverability check and the `◐ transcribed · UNROUTED` manifest disposition"
policy_baseline: "docs/fork-gaps.md FG-2026-07-26-05 (owner-approved 2026-07-26); manifest-schema.md `status` vocabulary (four values)"
run_state: "SPECIFIED, NOT YET RUN — do not cite a pass rate"
---

# Unrouted-component golden matrix (v1)

Golden-case contract for the widened **entry point / discoverability** check in
`steps/step-04-apply-and-deliver.md` and the fourth manifest disposition
`◐ transcribed · UNROUTED` in `../design-ingest/manifest-schema.md`.

> **These rows are SPECIFIED, NOT YET RUN.** Do not cite a pass rate for them. The first
> `design-implement` run that creates a component is the pilot.

## What the change is

| | Old | New |
|---|---|---|
| **Trigger** | *"whenever the run mounted a new route"* | *"whenever the run CREATED ANY COMPONENT FILE"* — plus when a change removed a component's last non-test importer |
| **Evidence** | the route's entry point | per created entry surface: **WHERE** from + **HOW** the operator arrives |
| **Unreachable outcome** | flag the island | flag it, and if not wired now, every affected grid row becomes `◐ transcribed · UNROUTED` with a named follow-up |
| **Dispositions** | 3 (`UNVERIFIED` / `✓ applied` / `⊘ deferred`) | 4 (adds `◐`, the only NON-terminal one) |

**The trigger is mechanical.** It does not ask whether a component *should* be reachable. That
judgement is re-litigable per component and is what turns a check into a suggestion; the
deliberately-not-wired-yet case is carried by `◐` **plus a declared follow-up**, not by skipping the
question. Detection is mechanical; deliberateness is DECLARED.

## Why the old trigger could not catch the origin case

The route-scoped trigger's **condition was a route**; the **failure is a component**. cash-recovery
`/receive` frames 2 and 3 (`ScanMatched.tsx` 551 LOC, `ScanException.tsx` 690 LOC) mounted no route —
they were components inside an existing one — so the check was not skipped, it was **structurally
blind**. Both shipped `✓ applied` with zero non-test importers and stayed unreachable for six days,
their own file headers asserting an importer that did not exist. `tsc`, `eslint`, 22 unit tests and two
merged PRs were green throughout.

## Golden cases

| # | Scenario | Expected outcome |
|---|---|---|
| 1 | Run mounts a **new route**, nav link present | **PASS** — `Reachable — entry point: global-nav "X" (verified present in …)`. Unchanged from the old behaviour; the widening must not regress it. |
| 2 | Run mounts a **new route**, nothing links to it | **FAIL → `⚠ UNLINKED ISLAND`**. Unchanged from the old behaviour. |
| 3 | **REGRESSION ROW — the origin case.** Run creates a component inside an **existing** route; no non-test file imports it | **FAIL → `⚠ UNROUTED COMPONENT`**; its grid rows become `◐`, never `✓ applied`. **Under the old trigger this case PASSED silently** — it is the row that proves the widening. |
| 4 | Same as 3, but a **test file** imports the component | **FAIL — identical to 3.** A test importer is not reachability. This is the precise false green that held for six days. |
| 5 | Run creates a component; a non-test file imports it, but that importer is **itself unimported** | **FAIL** — reachability is a chain terminating at a route entry, not a single hop. |
| 6 | Run creates a component wired into an existing route's render tree | **PASS** — evidence names WHERE (parent component/route) and HOW (render, link, or row-drill). |
| 7 | Run creates a **named drawer/sheet** reachable only by a row-drill from its parent worklist | **PASS** — a sub-surface's entry point is a link/row-drill from its named parent, never a global-nav peer (the sub-surface rule is unchanged). |
| 8 | Run creates a component, leaves it unwired, and marks its rows `◐` **with** a named follow-up (who wires it, into what) | **PASS with obligation** — a legitimate checkpoint. The frame is **NOT fully applied**; the `◐` rows are listed **above** the grid. |
| 9 | Same as 8 but the `◐` rows carry **no** follow-up | **NON-CONFORMANT** — re-emit the report with one. `◐` without a follow-up is silent staging under a new symbol. |
| 10 | A pass reports a frame `✓ applied` / counts it as built in frame coverage while it holds a `◐` row | **REFUSE** — a frame holding any `◐` is not fully applied. |
| 11 | A pass relabels a `◐` row to `⊘ deferred` to close out | **REFUSE — misreport.** `⊘ deferred` means nothing was built; `◐` means code exists and cannot be reached. The swap leaves live unreachable code no row is tracking. |
| 12 | A resume walk encounters `◐` rows from a prior pass | **Treated as outstanding work**, not terminal — `◐` is the only non-terminal disposition. `UNVERIFIED` = not looked at; `◐` = built, wiring owed. |
| 13 | `◐` rows exist but are written only in narrative **below** the grid | **NON-CONFORMANT** — the origin case did exactly this ("not yet wired — the largest un-owed piece", 60 lines under nine green ticks) and three later sessions read past it. `◐` is listed above the grid. |
| 14 | A change **removes** a component's last non-test importer | **FAIL → `⚠ UNROUTED COMPONENT`** — the mirror of the orphaned-action grep (that finds an action with zero callers; this finds a component with zero importers). |
| 15 | Run creates **no** component file and mounts no route | **N/A** — the section does not fire. The widening must not make every pass carry an irrelevant section. |

## Reference implementation

`cash-recovery/scripts/check-reachability.mjs` (`npm run check-reachability`) is the project-local
deterministic tier: it walks the module graph from Next.js route entries and exits non-zero on an
undeclared unreachable `.tsx`, with a declaration file (`reachability-allowlist.json`) requiring a
reason + owner, stale-declaration reporting, and a regression test pinning both directions. On its
first run it found **four further** unreachable components with **zero false positives**.

It is **framework-specific** (it keys on Next.js route conventions), so it is cited here as the
**pattern** step-04 requires — a mechanical importer check with a declared-exception file — not as a
file to sync. A project on another framework satisfies the same contract with its own equivalent.

## Deliberately NOT covered

- **Whether a reachable component renders correctly, matches its design, or sits on a path an operator
  would actually take.** This check proves a path EXISTS. Everything past that belongs to the
  render/done-check (§5b) and the live-page workflows.
- **`.ts`/non-component modules.** Types, helpers and domain modules are legitimately consumed only by
  tests or by other packages; flagging them is the noise that gets a check switched off.
- **"Substantially modified" components generally.** Modifying a component does not change whether
  anything imports it. Only the importer-REMOVING case (row 14) is in scope — the rest would widen the
  trigger without widening coverage.
