---
name: 'step-03-classify'
description: 'Classify each raw finding, resolving every ambiguous/duplicate case to RENDER GAP (data fine, UI hides it) or DATA ROT (values wrong). Assign severity.'
nextStepFile: './step-04-route.md'
---

# Step 3: Classify — Render Gap vs Data Rot

**Goal:** Convert `{raw_findings}` into classified findings. The load-bearing decision is made here: for every finding that *looks* like a duplicate or ambiguity, decide whether the data is correctly distinct (the UI just hides the distinguishing attribute) or the values genuinely collapsed/drifted.

---

## AVAILABLE STATE

- `{dimension}`, `{storage}`, `{normalizer}`, `{cross_field_rule}`, `{raw_findings}`

## STATE VARIABLES (set in this step)

- `{classified}` — list of findings, each with `{shape, verdict, severity, evidence}`

---

## THE CORE TEST: RENDER GAP vs DATA ROT

For each **ambiguous group** (one label spanning >1 distinguishing attribute on one entity):

- The distinguishing attributes are **genuinely distinct** (e.g. `amazon` → `AMAZON_FR` + `AMAZON_ES`) → **RENDER GAP.** The data is correct and distinguished in storage; the UI collapses it by rendering only the label. Evidence: the distinct attribute values.
- The attributes **all collapse to the same unresolved value** (e.g. two lanes both `UNKNOWN`) → **DATA ROT (data hole).** The rows are genuinely indistinguishable. Evidence: the shared unresolved attribute + the duplicate count.
- Mixed → split into one render-gap finding and one data-hole finding. Never average them into a single fuzzy verdict.

This is the verdict the operator actually needs: it decides whether the fix is a one-line UI change or a producer fix. Get it right per-finding.

## CLASSIFY THE OTHER SHAPES

- **Fall-throughs** → DATA ROT. A value that didn't resolve to a canonical identity is a producer/normalizer gap. Severity rises with count and with whether it leaves an entity unactionable.
- **Cross-field mismatches** → DATA ROT (or a normalizer gap if the normalizer should have caught it). Severity by blast radius (does a wrong currency corrupt downstream cost math?).
- **Source rot** → DATA ROT, located at the producer. This is the *root* of fall-throughs — flag the linkage so step-04 routes the producer fix, not a symptom patch.
- **No canonical normalizer** (`{normalizer} = NONE`) → P1 structural finding: the dimension is an uncontrolled vocabulary. The fix is to introduce a normalizer, not to clean values once.

## SEVERITY

- **P1 (critical):** corrupts downstream computation, leaves records unactionable, or no normalizer exists.
- **P2 (moderate):** user-visible confusion (render gaps live here — annoying, not corrupting), recoverable ambiguity.
- **P3 (low):** cosmetic, rare, or already-benign (state why it's benign — it still gets a row).

---

## NEXT STEP

Proceed to `{project-root}/_bmad/bmm/workflows/verify/data-quality-audit/steps/step-04-route.md`.

---

## SUCCESS METRICS

- Every ambiguous group resolved to render-gap, data-hole, or an explicit split
- Every finding carries `{shape, verdict, severity, evidence}`
- Source rot linked to the fall-throughs it causes
- `{normalizer} = NONE` surfaced as P1, not skipped

## FAILURE MODES

- Calling an ambiguous group "data rot" without checking whether the distinguishing attribute is actually distinct (the phantom-defect error)
- Calling a real collapse a "render gap" because two values *happened* to differ somewhere (the shipped-rot error)
- Averaging a mixed group into one fuzzy verdict instead of splitting it
- Severity inflation — flagging benign render gaps as P1 and drowning the real defects
