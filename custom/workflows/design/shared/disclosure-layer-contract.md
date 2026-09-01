# Disclosure layer contract — "inspectable" is the contract, "permanently displayed" is not

**Status:** shared design contract. Consumed by `design-handoff` (step-01 domain pass §3h, brief
template §4h, step-03 gate class **(i)**), `design-synthesize`, `design-artifact-loop`,
`design-review-pr`. Sibling of `operator-artifact-contract.md` — that one governs artifact SHAPE at
a canonical viewport; this one governs WHAT BELONGS IN THE DEFAULT VIEW at all.

**Origin:** owner ruling, 2026-08-31, on the cash-recovery Listing Composer. Verbatim:

> *"The old brief over-indexed on auditability being continuously visible and accidentally mandated
> a schema-shaped interface. That is not the intended product behaviour. 'Inspectable' is the
> contract. 'Permanently displayed' is not."*

---

## D0. When this contract applies

It applies to a surface carrying an **audit or provenance contract** — one where the design owes any
of: evidence for a displayed value · the source a value came from · freshness or staleness ·
derivation or a stated derived rule · conflicts · an override and who authored it · an audit history.

It does **not** apply to a surface with no such contract. A plain worklist, a settings page, a
marketing surface: nothing here fires, and a brief for one records `disclosure_model: n/a — no audit
contract`.

**The trigger is the CONTRACT, not the presence of metadata.** A column showing a timestamp is not an
audit contract. An operator being asked to *commit* to something the system asserted, with the
evidence for that assertion owed, is.

---

## D1. The three layers

Every surface under this contract declares which layer each element family sits in.

1. **Work layer — always visible.** The subject's identity, its readiness state, ONE dominant next
   action, and the fields the operator actually edits or commits. **This is the default workspace
   and it is the dominant visual region.**
2. **Confidence layer — compact and visible.** One overall evidence indicator near the commit
   control; an exception strip **only when action is needed**; at most one field-level signal where
   it carries material meaning. **Evidence that is healthy, current and uncontested gets NO signal
   at all.**
3. **Evidence layer — complete but disclosed.** Full provenance and source records, freshness detail,
   the original generated value, conflicts, derivation trace, override history with author,
   timestamp and before/after, the canonical record, audit history. It lives in an **inspector** —
   never a permanently visible third column — and is reachable from the overall indicator, from any
   field-level signal, from a `View evidence` / `Why this?` affordance, and from the controls that
   act on the evidence itself.

## D2. Silence is an assertion

The absence of a warning is the affirmative statement that a field is evidence-backed and within
policy. **A badge on everything destroys that meaning**, and destroying it is the specific defect
this contract exists to remove — a surface where every field is marked has told the operator nothing
and has spent the whole default view doing it.

## D3. Exception signals vs the neutral authorship signal

The field-level vocabulary splits in two, and only half of it is an issue.

| Signal | Kind | In the exception strip? | Counts toward the strip's number? |
|---|---|---|---|
| `Unverified` | exception | yes, named | yes |
| `N conflicts` | exception | yes, named | yes |
| `Stale` / `built on older data` | exception | yes, named | yes |
| `Owner edited` / `operator edited` | **neutral authorship** | **never** | **never** |

An override is a **fact about authorship, not a fault**. It carries a field-level signal and opens
the inspector like any other, but it never appears under *"needs attention"* and never inflates the
count. **Listing an operator's own deliberate edit as an issue is how a warning strip trains the
operator to dismiss it** — the same erosion a badge-on-everything causes, arriving by the other door.

## D4. A named exception is disclosure; a counted one is a collapse

This contract moves provenance behind a click. It does **not** license replacing meaningful issues
with an opaque aggregate. An exception strip names the affected element and the reason in plain
language, and each named item opens the exact relevant evidence.

    PASS   2 issues need attention
           Condition wording is unverified · Category confidence is low     [Review issues]

    FAIL   3 issues        FAIL   Warnings present        FAIL   Low confidence

**The inspector deep-links** to the field, source, conflict or override that was signalled. Landing
the operator at the top of a generic audit page is the aggregate failure in another costume.

## D5. What does NOT move — stated so this cannot be read as a general softening

- **A visual-judgement gate outranks this contract.** Where the judgement's *material is an image*,
  the images are on screen at the point of judgement, at judgement size, before the control that
  records the judgement is reachable. *"The photographs are one click away"* fails a visual-judgement
  gate exactly as it did before this contract existed. (Project design policies carry this as their
  own section — cash-recovery §4a; the ordering is: that section wins.)
- **A blocker is not evidence.** Anything that PREVENTS the commit stays in the work layer, named,
  with its route to resolution. Disclosure governs the *support* for a claim, never the *obstacle*
  to an action.
- **This is about metadata, not the values.** Outward-facing content the operator is approving stays
  fully visible. What moves is the apparatus around it — marks, captions, freshness sentences,
  compare lanes, derivation labels.
- **Type and spacing are not the lever.** Shrinking type or padding to fit a schema-shaped layout
  onto a screen is this failure treated cosmetically. The repair is moving elements to layer 3,
  never tightening layer 1. Floors: body ≥14px, field value 15px, field label 12px sentence case,
  group heading 11px tracked uppercase for major groups only, **nothing below 11px**.

## D6. The four invariants that survive the move, unchanged

1. Every approved outward-facing assertion remains traceable to evidence, a stated derived rule, or
   an operator override.
2. Every override remains attributable, timestamped, and comparable against what it replaced.
3. Conflicts and stale or unverified evidence **cannot be hidden from a commit decision**.
4. Committing over a non-blocking warning writes an explicit audit event carrying the warning state
   and the operator's decision.

---

## D7. What a brief must carry (the machine-checkable part)

Block B frontmatter:

    disclosure_model: three-layer          # three-layer | n/a — <why no audit contract>

…and, when `three-layer`, a **§4h Disclosure layers** section assigning every element family to a
layer, plus the exception/neutral signal split for that surface's vocabulary.

**A brief that declares an audit contract and assigns no layers is INCOMPLETE, not merely terse.**
The generator fills an unspecified slot with its default instinct, and its default instinct here is
to render the evidence model as the interface. That is exactly how the Listing Composer's 08-31
brief came to mandate permanent generated-beside-override lanes, per-ingredient provenance marks and
full-sentence freshness markers on a compose-and-approve surface — no field in the brief was wrong,
and the sum of them buried the decision.

**Nothing in this contract is a licence to withhold.** A brief may not answer §4h with *"disclosed"*
and leave the evidence layer unspecified: the inspector's contents are a §4h obligation, itemised,
because an unspecified inspector is how auditability actually gets lost.

## D8. Enforcement honesty

**PROBABILISTIC in its judgement half, irreducibly.** No check can tell a well-layered surface from a
buried one, or judge whether a named exception is the right name. A rendered comp is not a tool call,
so no hook can block one.

**Two slices ARE deterministic and are what actually ship:**

- `tools/check-brief-readiness.py` probe `disclosure-layers` — fires when a brief's own text
  indicates an audit contract and determines nothing about layering. Like every probe in that tool,
  **a fired probe is a QUESTION, not a defect.**
- `design-handoff` step-03 gate class **(i)** — hard-fails a brief carrying
  `disclosure_model: three-layer` with no §4h assignment, and hard-fails a brief with no
  `disclosure_model` line at all whose §2 names evidence, provenance, override or audit obligations.

Ceiling, stated plainly: both verify the brief **declared** its layers. Neither verifies the layering
is right, and neither can see the rendered artifact. The drift surface is prose, as always — any
workflow that produces a design artifact without reading this file is invisible to both slices.
