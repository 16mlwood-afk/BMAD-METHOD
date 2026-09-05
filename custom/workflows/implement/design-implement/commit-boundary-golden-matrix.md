---
status: current
version: 1
scope: "design-implement step-02b §4e — the commit-boundary pass trigger and its required-field record"
policy_baseline: "steps/step-02b-regression-surface.md §4e; detector tools/check-commit-boundary.js"
run_state: "RUN 2026-08-09 — 12/12 green via `npm run test:commit-boundary`, plus a nine-surface probe against real cash-recovery routes. Rows G1 and G2 are the two required directions."
---

# Commit-boundary golden matrix (v1)

Golden-case contract for the **commit-boundary pass** (`steps/step-02b-regression-surface.md` §4e)
and its detector `tools/check-commit-boundary.js`. Executable: `npm run test:commit-boundary`
(`test/test-commit-boundary-check.js`).

## What the change is

| | Before | After |
|---|---|---|
| **Question asked of a write surface** | does the handoff drop or add a *capability*? (§4/§4b) | …and does the design carry the *lifecycle* behind the irreversible write? (§4e) |
| **Trigger** | none — no pass existed | outward write · durable mutation · approval · binding/merge · retry · pre-commit evidence review. Anything else SKIPS. |
| **Required output** | none | nine determinations in a `commit_boundary:` record: durable object · states · transitions · evidence snapshot · freshness · preconditions · success/failure/**unknown** outcomes · idempotency · the ONE commit control |
| **Classification of a shortfall** | would have read as copy/layout | **interaction-model gap** — remedied by the smallest stateful flow mapped to frames, never a relabel |
| **Machine tier** | — | `--scan` (trigger signals) · `--check` (field presence). Nothing else is claimed. |

## Why the origin case was invisible to every existing check

cash-recovery `/listings`: **"Preview what will be sent"** and **"Re-attempt publish"** pointed at
the same target around an irreversible external write to eBay.

- The **capability delta** (§3) saw "publish" present on both sides — no drop, no add.
- The **grid** (step-03) is component × state × property; a missing durable object is not a CSS cell.
- **UI-copy review** was structurally incapable of finding it: nothing was misworded. The labels
  were accurate descriptions of controls that should not both have existed.
- `design-handoff` §3d (interaction-model pass) is the nearest neighbour and does not reach it —
  it fires only on a **processing cockpit**, and captures the operator's momentum and
  consequence-preview, not the **durable attempt object** the write lives in.

The missing artifact was a state model. No gate asked for one, so nobody produced one.

## Golden cases

| # | Scenario | Expected | Result |
|---|---|---|---|
| **G1** | **Read-only review surface** — an ingestion-runs table with "Review the records", a **"Preview records"** button, a detail drawer and an export. Writes nothing. | **NOT-TRIGGERED.** Zero write-class hits. The `Preview` support signal is still **reported** (it is real) but never fires the pass on its own. | ✅ PASS |
| **G2** | **The eBay publish frame** — "Preview what will be sent", "Publish to eBay", "Re-attempt publish", all `data-target="publish"`. | **TRIGGERED**, classes `outward-write` + `retry`, with the pre-commit-review signal alongside. §4e must then determine all nine facts before the grid. | ✅ PASS |
| G3 | A triggered surface's preflight artifact carries **no** `commit_boundary:` record. | `F1-NO-RECORD` — a record that does not exist cannot be reviewed. | ✅ PASS |
| G4 | Record present, `freshness` and `idempotency` absent. | Two `F2-MISSING` findings, each **naming its field**. A generic "incomplete" would be unactionable. | ✅ PASS |
| G5 | `idempotency: TBD`. | `F2-PLACEHOLDER` — same discipline as §3f's viewport fields: `TBD` / `n/a` / `see design` are non-answers. | ✅ PASS |
| G6 | `outcomes` carries `success` and `failure` but no `unknown`. | `F3-OUTCOME` on `outcomes.unknown`. An unknown external outcome is not a failure; conflating them is how one publish becomes two. | ✅ PASS |
| G7 | All nine present and substantive. | `FIELDS-PRESENT`, 9/9. **Not** a claim that the model is right. | ✅ PASS |
| G8 | Default run on a triggering surface. | Exit **0**. Warn-only, so the tool is safe to run anywhere. | ✅ PASS |
| G9 | `--strict` on a triggering surface. | Exit **1**, for a caller that wants a hard signal. | ✅ PASS |
| G10 | Scan path does not exist / no scannable files. | **`NO-INPUT`**, never `NOT-TRIGGERED`. Seeing nothing is not evidence of absence, and a green from an empty read is the failure this fork names elsewhere. | ✅ PASS |
| G11 | An auth-guarded read-only page: a `request-authorized` route comment, a `requireSession()` call, an `onLookup: () => void` prop. | **NOT-TRIGGERED.** Access-control vocabulary is not a business approval, and `void` is a TypeScript keyword. | ✅ PASS |
| G12 | A 60-frame scan whose `--json` report exceeds 64KB, piped to a consumer. | Report **parses**. Pinned because it did not: an explicit `process.exit()` truncated the write mid-string, and a broken printer read as a broken surface. | ✅ PASS |

## Measured against real surfaces (not fixtures) — 2026-08-09

Nine cash-recovery routes, scanned as-is. This is the false-positive evidence; the fixtures above
only prove the logic.

| Fires | Quiet |
|---|---|
| `/listings` (publish, re-attempt) · `/pricing` · `/reimbursements` · `/staging` · `/approvals` | `/ingestion-runs` · `/lineage` · `/raw-records` · `/recovery` |

Five write-bearing surfaces fire, four read-only ones stay silent. **Two signal terms were removed
because this probe caught them false-firing, not because they looked risky:** `authorise/authorize`
(fired on three read-only routes from a `request-authorized` comment) and `void` (fired on every
`() => void` prop signature). Both omissions are pinned by G11.

## What is machine-checked and what is not

**DETERMINISTIC (the script decides):** whether a trigger signal is present (`--scan`), and whether
the nine fields exist and are non-placeholder in the emitted record (`--check`). Both directions are
pinned above, and the tool ships **warn-only** by default.

**JUDGEMENT ONLY (no script may claim it):** whether the state model is **correct** — whether those
are the right states, whether the transitions are legal, whether the snapshot is the one the
operator actually saw, whether the idempotency key dedupes the thing that needs deduping, and
whether the named `commit_control` is genuinely the only path to the write. A checker that guessed
at any of it would launder a judgement into a green tick. **A green `--check` means the record was
filled in, never that the boundary is safe.**

**Direction of the error, deliberately.** The write-class list is generous: a false fire costs one
bounded pass, a miss costs the `/listings` failure. Four terms are **left out** — `cancel` (dialog
dismissal), `assigned to` (a column header), `authorise/authorize` (access control, not approval)
and `void` (a TypeScript keyword). Those are ceded dimensions, stated rather than hidden. Words like
`Submitted` used purely as a *status label* on a read-only surface WILL still fire the scan; that is
the accepted cost, and the pass then skips in one line after the human trigger test.

**Not wired into any gate.** The suite runs under `npm test`; the detector is invoked by hand from
§4e. It is not in a pre-commit hook, not in CI on any consuming project, and it does not ship with
the fork sync until the sync is run — which is a separate, owner-gated decision.
