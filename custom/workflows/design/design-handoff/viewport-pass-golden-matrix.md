---
status: current
version: 2
supersedes: "v1 — the pre-#293 '4/4 PASS' verdict (verified against design-policy §8 v7, with pass ba3188a1 which hardcoded clerk=desktop). SUPERSEDED: v1 did not cover the handheld-first receiving class introduced by #293 / §8 v8, and its matrix row 1 ('clerk marked mobile = FAIL') is wrong for a mobile-first-decided clerk class. Do NOT treat the v1 4/4 as current."
pass_commit: 23f60c20
policy_baseline: "docs/design-policy.md §8 v8 (#293 — clerk RECEIVING handheld-first, grading desktop-only)"
---

# §3f Viewport & Responsive Pass — Golden Matrix (v2 — handheld-first aware)

> **v2 supersedes the pre-#293 v1 "4/4 PASS".** v1 was verified against §8 v7 with a pass
> (`ba3188a1`) that **hardcoded "clerk = desktop-only"**. Policy #293 (§8 v8, 2026-07-19) reversed
> **clerk receiving** to handheld-first/mobile-primary, and the pass was fixed (`23f60c20`) to read
> the **per-class decided posture** from §8.2. This v2 re-runs the pilot with that fix + policy. The
> v1 4/4 is stale — do not cite it.

Golden-case contract for the design-handoff **§3f viewport pass** (`23f60c20`). The pass fires on
every `page` surface and auto-fills a **DECIDED** class from ITS `docs/design-policy.md` §8.2 block —
**desktop-only OR mobile-first, per class** (never hardcoded) — and requires a viewport contract for
owner surfaces: **warn-only** while the owner mobile ambition (§8.3) is an open product decision,
hard-fail otherwise.

Gate classes (step-01 §3f, validation gate step 5):

| Class | Condition | Outcome |
|---|---|---|
| **(a)** | `{viewport_surface_class}` unresolved | HARD FAIL |
| **(b)** | missing/partial — a field blank on a clerk surface, or an owner surface whose ambition is **SET** | HARD FAIL |
| **(c)** | policy contradiction — a field contradicts the class's OWN §8.2 posture (a desktop-only class marked mobile, OR a mobile-first class forced desktop-only) | HARD FAIL |
| **(d)** | owner surface whose §8.3 mobile ambition is **OPEN**, contract complete-as-scaffold | WARN-ONLY (deliverable, `pending-policy`, §4g PENDING banner) |

## The golden matrix (handheld-first aware — §8 v8)

| # | Input surface & state | Gate class | Expected outcome |
|---|---|---|---|
| 1 | Clerk **grading** (`/clerk`, §8.2b **desktop-only** decided) → auto-fill | decided auto-fill | **PASS** — fills desktop-only ≥1280px from §8.2b |
| 2 | Clerk **receiving** (`/receive`, §8.2a **handheld-first** decided) → auto-fill | decided auto-fill | **PASS** — fills mobile-first / phone viewport / offline from §8.2a (NOT desktop) |
| 3 | Clerk **grading** marked mobile/tablet-supported | (c) | **FAIL** — contradicts its decided desktop-only posture |
| 4 | Clerk **receiving** forced desktop-only, mouse-dependent | (c) | **FAIL** — contradicts its decided handheld-first posture (the #293 case v1 missed) |
| 5 | Owner surface, ambition SET, field(s) missing/partial | (b) | **FAIL** — required contract incomplete |
| 6 | Owner surface, contract field contradicts §8 | (c) | **FAIL** — policy contradiction |
| 7 | Owner surface, ambition OPEN, contract complete-as-scaffold | (d) | **WARN** — deliverable, `{viewport_pending_policy}`=true, §4g PENDING banner |

Rows 3–6 block the brief; row 7 emits it marked `pending-policy` and continues; rows 1–2 pass by
auto-filling the class's decided posture.

## Pilot result — cash-recovery (2026-07-19, re-run against §8 v8 + the fixed pass)

Re-verified against `docs/design-policy.md` §8 v8 (#293 — receiving handheld-first, grading
desktop-only) with the owner mobile ambition **OPEN** (§8.3 ⚠ OPEN ITEM present), using the fixed
per-class-posture pass (`23f60c20`).

| # | Case | Expected | Result | Evidence |
|---|---|---|---|---|
| 1 | grading → desktop-only auto-fill | PASS | ✅ | §3f step 2 reads §8.2b desktop-only |
| 2 | receiving → mobile-first auto-fill | PASS | ✅ | §3f step 2 reads §8.2a handheld-first (the fix — v1 wrongly forced desktop) |
| 3 | grading marked mobile | FAIL | ✅ | §3f step 5(c) — contradicts class's desktop-only posture |
| 4 | receiving forced desktop | FAIL | ✅ | §3f step 5(c) — contradicts class's handheld-first posture |
| 5 | owner ambition-SET, missing field | FAIL | ✅ | §3f step 5(b) |
| 6 | owner contradiction | FAIL | ✅ | §3f step 5(c) |
| 7 | owner ambition OPEN | WARN | ✅ | §3f step 3 → WARN, §4g PENDING banner |

**Verdict: 7 / 7 PASS under the current handheld-first policy (§8 v8 / #293).**

> Live re-delivery: the fix (`23f60c20`) reaches the cash-recovery checkout on the next porter + sync;
> until then the pilot checkout still carries the pre-fix pass. This v2 verdict is verified against the
> fixed pass logic + the real §8 v8 policy; the live cash-recovery re-render confirms it on delivery.

## Notes

- Distribution: §3f is fork-canonical (`custom/workflows/design/design-handoff/`); it reaches projects
  by sync + porter. cash-recovery is the pilot — the 12-project fan-out is HELD pending owner go, and
  now additionally gated on the mobile `/receive` being designed + staged with policy alignment proven.
- Enforcement tier (per `enforcement-expert`): the §3f pass + gate are PROBABILISTIC (ship via sync).
  The deterministic companion — a per-project brief-artifact CI validator asserting a `page` brief
  carries a complete §4g contract — is a separate hooks/CI-track follow-up, not yet built.
- Flipping the owner-OPEN row (7) from WARN to a hard HALT is a one-line change (step-01 §3f step-3)
  once the owner sets the §8.3 mobile ambition.
