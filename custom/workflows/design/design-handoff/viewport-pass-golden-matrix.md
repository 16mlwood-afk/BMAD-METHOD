---
status: current
version: 4
v4_addition: "Gate class (f) — the ARTIFACT-COMPOSITION half (rows 15–20). v3's rows 8–14 test whether the deliverable is DRAWN AND READ at the canonical viewport; they structurally cannot catch an artifact that labels the phone canonical, groups the additive renders correctly, preserves the interaction model — and is still a REVIEW BOARD (rationale opening/interleaving the artifact, state variants as peer mini-products, explanatory prose outranking the primary action). Row 17 is the regression row: it fails on composition alone with every viewport field correct. Rows 15–20 are SPECIFIED, NOT YET RUN — do not cite a '20/20 PASS'. Contract: shared/operator-artifact-contract.md (B1–B6, C1–C4). Project binding: cash-recovery docs/design-policy.md §8.2d + §5 #14 (v11, 2026-07-25)."
v3_addition: "Gate class (e) — the ARTIFACT-LABELING half (rows 8–14). v2's rows 1–7 test whether the viewport POSTURE is recorded in brief §4g; they structurally cannot catch an artifact that records the posture correctly and still renders/reads desktop-first, because an unlabelled multi-viewport comp set contradicts no §4g field. Rows 8–14 are SPECIFIED, NOT YET RUN — do not cite a '14/14 PASS'. Policy baseline for the new rows: cash-recovery docs/design-policy.md §8.2c + §5 #13 (v10, 2026-07-25)."
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

---

## v3 addition — gate class (e): the ARTIFACT-LABELING half

Rows 1–7 test whether the viewport **posture is recorded** (the §4g contract). They cannot catch the
defect below, and that is the point: an artifact showing phone / tablet / desktop as co-equal comps
**contradicts no §4g field**, so rows 1–7 all pass while the deliverable reads desktop-first. Class
(e) (step-01 §3f.4b + gate step 5) adds the second question — *will the deliverable be **drawn and
read** at the recorded posture?*

Policy baseline for these rows: cash-recovery `docs/design-policy.md` **§8.2c** (canonical-vs-additive
labeling contract) + **§5 #13** (the matching hard failure), v10 / 2026-07-25.

| # | Input artifact & state | Gate class | Expected outcome |
|---|---|---|---|
| 8 | Clerk **receiving** handoff: `{canonical_viewport}` = phone 375×812, §4g renders the canonical/additive block, §7 item 1 names the phone render primary; the artifact labels the phone comp canonical in-page, groups tablet+desktop under "Additive verification viewports" **after** it, and the desktop render keeps the scan-first single-column model (reflowed, no new controls) | — (clean) | **PASS** — the only shape that passes. Deliverable. |
| 9 | Clerk **receiving** handoff: §4g contract complete and correct, but §7 item 1 still says *"Visual designs at desktop width (1280px)"* (the pre-v3 hardcoded template line) | **(e)** | **FAIL** — hard, brief NOT deliverable. **The regression row.** Rows 1–7 pass it (§4g is flawless); the designer acts on §7 and renders desktop-first. This is the exact defect the class exists for. |
| 10 | Clerk **receiving** artifact: phone / tablet / desktop rendered side-by-side at equal prominence, no canonical label anywhere in-page (posture discoverable only from the brief's §4g table) | **(e)** | **FAIL** — §8.2c A1 + A2, §5 #13. Contradicts no contract field; a cold reader defaults to "desktop is the design, phone is the shrink." **Still FAILS when the phone column is leftmost** — reading order is not a label. |
| 11 | Clerk **receiving** artifact with **no phone frame at all** — desktop + tablet only | **(e)** | **FAIL** — a missing canonical render is not a partial deliverable, it is a desktop-premised one (§5 #13, fourth bullet). Requires revision, never "ship it and add phone later." |
| 12 | Clerk **receiving** artifact: phone correctly labelled canonical, but the desktop additive render becomes a wide multi-column table with hover-revealed row actions absent from the phone render | **(e)** | **FAIL** — §8.2c A3. Labeling alone is not compliance: an additive render that re-premises the interaction model reintroduces the desktop premise **under a correct label**, which is worse than an honest omission. A handheld-first desktop render is *a wider phone*. |
| 13 | Clerk **grading** (`/clerk`, §8.2b desktop-only): desktop 1440×900 labelled canonical, no phone comp produced | — (clean) | **PASS** — canonical is desktop **for this class**; phone sits in `device_exclusions` so it is neither canonical nor additive and is correctly **not rendered**. Guards against reading (e) as "always want a phone frame." |
| 14 | **Owner** surface, §8.3 ambition still OPEN, no canonical viewport declared | (d) only | **WARN — (e) does NOT fire.** No decided posture ⇒ nothing to declare. The false-positive guard: (e) must never become a back door that hard-fails owner work the warn-only (d) path deliberately lets continue. |

**Rows 9–12 are the new blocking set; 8, 13, 14 are the false-positive guards.** A class (e) that
fires on 13 or 14 is over-firing and must be fixed before it is trusted — an over-firing gate on
owner surfaces would freeze exactly the work (d) was designed to keep moving.

**Status: SPECIFIED, NOT YET RUN.** Rows 8–14 are the authored contract for class (e); they have not
been executed against a real handoff. Do **not** cite a "14/14 PASS" — rows 1–7 were verified against
§8 v8, rows 8–14 are unverified until a clerk-receiving handoff runs under v3. The first `/receive`
or `/inbound` handoff after this lands is the pilot.

> Live re-delivery: the fix (`23f60c20`) reaches the cash-recovery checkout on the next porter + sync;
> until then the pilot checkout still carries the pre-fix pass. This v2 verdict is verified against the
> fixed pass logic + the real §8 v8 policy; the live cash-recovery re-render confirms it on delivery.

---

## v4 addition — gate class (f): the ARTIFACT-COMPOSITION half

Rows 8–14 test whether the deliverable will be **drawn and read at** the canonical viewport. They
cannot catch the defect below, and that is the point: an artifact can label the phone canonical,
group tablet/desktop after it, and preserve the interaction model — and still be a **review board**,
because *which render wins* and *what shape the artifact is* are different questions. Class (f)
(step-01 §3f.4c + gate step 5) adds the third: *is this an operator surface, or a presentation about
one?*

Contract, rules B1–B6, the four review-board tells, and checks C1–C4:
**`shared/operator-artifact-contract.md`**. Project binding for the pilot: cash-recovery
`docs/design-policy.md` §8.2d + §5 #14, v11 / 2026-07-25.

| # | Input artifact & state | Gate class | Expected outcome |
|---|---|---|---|
| 15 | Clerk **receiving** handoff: five-field Handheld-First Declaration complete in §4g; §7 carries the composition sequence; artifact opens with ONE phone render (first, largest, above the fold, labelled), then a subordinate "States of this surface" strip, then "Additive verification viewports", then a notes/rationale block LAST | — (clean) | **PASS** — the only shape that passes. Deliverable. (Golden case **G1**.) |
| 16 | Clerk **receiving** artifact: phone/tablet/desktop side-by-side at equal size, phone leftmost, no in-page canonical label | **(e)** + **(f)** | **FAIL** — fires on BOTH halves (A1/A2 and B2/C1/C2). Kept in the matrix under (f) as well because the co-equal board is tell #1 of the review-board shape, not only a labeling miss. (**G2**; overlaps row 10 deliberately.) |
| 17 | Clerk **receiving** artifact: canonical phone render present, correctly labelled and first — but the artifact opens with three paragraphs of IA rationale and a principles list, each comp is followed by two paragraphs of explanation, and the primary action is smaller than the surrounding section headings | **(f)** | **FAIL** — B1/B4/B5, C3+C4. **The regression row for (f).** Rows 8–14 pass it cleanly: the viewport contract is flawless. Correct labeling does not rescue a document-with-figures; the squint test resolves to a heading, not the action. (**G3**.) |
| 18 | Clerk **receiving** artifact: one canonical phone render, then `--offline-queued` / `--stale` / `--tracking-unavailable` / `--exception` as a subordinate strip — same skeleton, same chrome, same primary-action position, one changed region each, captioned with the producing condition and what the operator can still do; no variant has its own nav or hero | — (clean) | **PASS** — B3 satisfied. The false-positive guard for state variants: a handheld-first artifact SHOULD show degraded states; (f) must never read "several frames" as "peer designs." (**G4**.) |
| 19 | Clerk **receiving** artifact: phone correctly canonical and first — but the desktop additive render becomes a wide multi-column table with hover-revealed row actions and a persistent filter rail with no phone equivalent | **(e)** + **(f)** | **FAIL** — A3/B2, C2. The desktop premise returns *under a compliant label*, and downstream implementation treats the richer render as the real design. A handheld-first desktop render is *a wider phone*. (**G5**; overlaps row 12 deliberately — row 12 judges it as a viewport violation, row 19 as a composition one.) |
| 20 | Clerk **grading** (`/clerk`, §8.2b desktop-only) or an **owner** surface with an OPEN §8.3 ambition | — / (d) | **(f) does NOT fire.** The false-positive guard, same shape as row 14: (f) binds handheld-first DECIDED classes only. An over-firing (f) on desktop-only or owner work would freeze exactly what (d) keeps moving. |

**Rows 16, 17, 19 are the new blocking set; 15, 18, 20 are the false-positive guards.** Row 17 is the
one that matters most — it is the only row in the whole matrix that fails on composition alone, with
every viewport field and label correct. A class (f) that cannot fail row 17 has not been implemented;
a class (f) that fires on 18 or 20 is over-firing and must be fixed before it is trusted.

**Status: SPECIFIED, NOT YET RUN.** Rows 15–20 are the authored contract for class (f); they have not
been executed against a real handoff. Do **not** cite a "20/20 PASS" — rows 1–7 were verified against
§8 v8; rows 8–20 are unverified. The first handheld-first `design-handoff` after this lands is the
pilot for both (e) and (f).

## Notes

- Distribution: §3f is fork-canonical (`custom/workflows/design/design-handoff/`); it reaches projects
  by sync + porter. cash-recovery is the pilot — the 12-project fan-out is HELD pending owner go, and
  now additionally gated on the mobile `/receive` being designed + staged with policy alignment proven.
- Enforcement tier (per `enforcement-expert`): the §3f pass + gate are PROBABILISTIC (ship via sync).
  The deterministic companion — a per-project brief-artifact CI validator asserting a `page` brief
  carries a complete §4g contract — is a separate hooks/CI-track follow-up, not yet built.
- Flipping the owner-OPEN row (7) from WARN to a hard HALT is a one-line change (step-01 §3f step-3)
  once the owner sets the §8.3 mobile ambition.
