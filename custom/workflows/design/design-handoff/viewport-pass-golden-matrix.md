# §3f Viewport & Responsive Pass — Golden Matrix

Golden-case contract for the design-handoff **§3f viewport pass** (`ba3188a1`). The pass fires on
every `page` surface, auto-fills clerk bench as desktop-only from the project `docs/design-policy.md`
§8.2, and requires a viewport contract for owner surfaces — **warn-only** while the owner mobile
ambition (§8.3) is still an open product decision, hard-fail otherwise.

The gate has four classes (step-01 §3f, validation gate step 5). Three hard-fail; one warns.

| Class | Condition | Outcome |
|---|---|---|
| **(a)** | `{viewport_surface_class}` unresolved | HARD FAIL |
| **(b)** | missing/partial — a field blank on a clerk surface, or on an owner surface whose ambition is **SET** | HARD FAIL |
| **(c)** | policy contradiction — a field contradicts §8 (incl. a desktop-only bench surface marked mobile/tablet) | HARD FAIL |
| **(d)** | owner surface whose §8.3 mobile ambition is **OPEN**, contract complete-as-scaffold | WARN-ONLY (deliverable, `pending-policy`, §4g PENDING banner) |

## The 4-row golden matrix

| # | Input surface & state | Gate class | Expected outcome |
|---|---|---|---|
| 1 | Clerk bench surface marked mobile / tablet-supported | (c) | **FAIL** (hard) — contradicts §8.2 decided desktop-only |
| 2 | Owner surface, ambition SET, contract field(s) missing/partial | (b) | **FAIL** (hard) — required contract incomplete |
| 3 | Owner surface, contract field contradicts §8 | (c) | **FAIL** (hard) — policy contradiction |
| 4 | Owner surface, ambition OPEN, contract complete-as-scaffold (pending marked) | (d) | **WARN** — deliverable, `{viewport_pending_policy}`=true, §4g PENDING banner renders |

A run passes the matrix when each row produces its expected outcome (rows 1–3 block the brief; row 4
emits it marked `pending-policy` and continues).

## Pilot result — cash-recovery (2026-07-19)

Pilot delivered §3f into cash-recovery via the porter (scoped to design-handoff), verified against
`docs/design-policy.md` §8 (v7) with the owner mobile ambition **OPEN** (§8.3 ⚠ OPEN ITEM present).

| # | Gate class | Expected | Result | Evidence |
|---|---|---|---|---|
| 1 | (c) | FAIL | ✅ PASS | step-01 §3f step-5 (c): "a desktop-only bench-class surface marked mobile/tablet-supported … fails, it never warns" |
| 2 | (b) | FAIL | ✅ PASS | step-01 §3f step-5 (b): "a field blank … on an owner surface whose ambition is SET" → HARD FAIL |
| 3 | (c) | FAIL | ✅ PASS | step-01 §3f step-5 (c): "a field contradicts §8" → HARD FAIL |
| 4 | (d) | WARN | ✅ PASS | step-01 §3f step-3 (owner + §8.3 OPEN) → WARN-ONLY; brief-template §4g renders the ⚠ PENDING POLICY banner |

**Live owner-surface render check (row 4):** owner route `/dashboard` (policy §8.1 "Owner dashboards &
worklists" class, ambition UNDECIDED) drives §3f → class (d): `{viewport_pending_policy}` = true,
brief marked `unverified` / `pending-policy`, §4g renders the six owner fields as `pending` under the
**⚠ PENDING POLICY — owner mobile ambition not set** banner, handoff continues (no freeze). Matches
contract. ✅

Pass count: **4 / 4.**

## Notes

- Distribution: §3f is fork-canonical (`custom/workflows/design/design-handoff/`); it reaches projects
  by sync + porter. cash-recovery is the **pilot** — the 12-project fan-out is HELD pending owner go.
- Enforcement tier (per `enforcement-expert`): the §3f pass + gate are PROBABILISTIC (ship via sync).
  The deterministic companion — a per-project brief-artifact CI validator asserting a `page` brief
  carries a complete §4g contract — is a separate hooks/CI-track follow-up, not yet built.
- Flipping row 4 from WARN to a hard HALT is a one-line change (step-01 §3f step-3) once the owner sets
  the §8.3 mobile ambition.
