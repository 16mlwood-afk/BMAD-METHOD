---
name: operator-artifact-contract
description: 'Canonical fork doctrine for the SHAPE of a design artifact on a handheld-first / mobile-primary / phone-canonical operator surface. Owns the COMPOSITION axis (B1-B6): canonical operational surface first, state variants as degraded states of that surface, rationale after the surface, action hierarchy over explanatory prose, operator copy compression. Sibling of the VIEWPORT axis (canonical-vs-additive labeling) which the project design policy owns. Consumed by design-handoff (gate class (f)), design-synthesize, design-review-pr, design-review, design-artifact-loop, and the claude-design-prompt paste route.'
---

# Operator-Artifact Contract — handheld-first surfaces

**One line.** A project's design policy declares *which surface class this is*. This file defines
*what shape the artifact for that class must take*. Claude Design / `design-synthesize` implement it.

## Why this exists — the first broken step, named precisely

A handheld-first surface came back as a **review board**: a symmetric row of sibling comps, heavy
explanatory prose, state variants drawn as peer mini-products, and a weak canonical/additive
hierarchy. Where that actually went wrong:

1. **Design policy captured the viewport STANCE correctly.** The surface class was decided
   handheld-first / mobile-primary / scan-first, desktop additive. Nothing in the policy was wrong or
   missing on the posture question.
2. **`design-handoff` did not require a canonical-viewport ARTIFACT CONTRACT.** The brief carried a
   correct viewport *table* and a deliverable instruction that said nothing about the artifact's
   *shape*. Nothing forced *one canonical operational surface, drawn first, with everything else
   subordinate to it*.
3. **So Claude Design filled the unspecified gap with its default rendering instinct** — a
   presentation-grade review board, the industry-default output shape for "show me the design." The
   result is **valid-looking and wrong-shaped**: it contradicts no field in the brief, so every
   existing gate passes it.

**This is not mainly a taste failure. It is an enforcement / artifact-shape failure.** The generator
was not wrong to fill an unspecified slot; the handoff was wrong to leave the slot unspecified. A
taste fix ("make it feel more operational") corrects one artifact. Only an artifact-shape contract
that the handoff *requires* and the review *checks* makes the next handheld-first surface one-shot.

## The two axes — do not conflate them

| Axis | Question | Home | Rules |
|---|---|---|---|
| **Viewport** | *Which* render is the design, and which are checks? | project design policy's canonical-vs-additive subsection (cash-recovery `docs/design-policy.md` §8.2c) | A1 in-page canonical label · A2 additive grouped + subordinate · A3 additive preserves the interaction model · A4 missing label ⇒ UNVERIFIED |
| **Composition** | *What shape* is the artifact at that viewport? | **this file** (project binding: cash-recovery §8.2d) | **B1–B6 below** |

An artifact can satisfy every A-rule — phone labelled canonical, tablet/desktop grouped after it,
interaction model preserved — and still be a review board: three correctly-labelled comps floating in
a sea of rationale, with the operator's next action smaller than the paragraph explaining it. **A
governs which render wins; B governs whether the artifact is an operator surface at all.**

## Trigger — which surfaces this binds

Binds any surface whose class is DECIDED as **handheld-first**, **mobile-primary**, or
**phone-viewport-canonical** (`primary_viewport_class: mobile-first`). It does **not** bind:

- a **desktop-only** DECIDED class — its canonical viewport is desktop; A-rules and B1/B3/B4/B5 still
  apply, but B6's one-handed operator-copy compression is calibrated for a phone in an aisle and is
  advisory there;
- an **owner / content surface whose viewport ambition is still OPEN** — nothing is decided, so there
  is no canonical surface to compose around. Never use a B-rule as a back door to hard-fail work the
  viewport pass deliberately lets continue as `pending-policy`.

---

## The contract — B1 to B6

### B1 — One canonical operational surface, first and dominant

The artifact opens with **one** render: the canonical-viewport operational surface in its resting
state. It is first in reading order, largest on the page, and is the only thing above the fold.
Everything else — additive renders, state variants, component specs, rationale — sits *after* it and
*smaller* than it.

A reader who stops after the first screenful must have seen the surface the operator actually uses.

### B2 — Additive renders stay subordinate (defers to the viewport axis)

Tablet/desktop renders, when shown at all, appear under a single **"Additive verification viewports"**
heading, after the canonical render, visually subordinate — never a co-equal column, never larger,
never first. This restates A2 so B reads standalone; the viewport axis owns it. A symmetric row of
three same-size comps **fails**, phone-leftmost included.

### B3 — State variants are DEGRADED STATES of the canonical surface, never peer designs

Stale data, tracking unavailable, offline/queued, sync conflict, exception, empty, error — each is
drawn as **the same surface in a different condition**, not as a separate product.

Concretely, a state-variant frame:

- **keeps the canonical frame's identity** — same frame-name stem (`{primary}--{state}`), same chrome,
  same layout skeleton, same primary-action position;
- **differs in one legible region** — a status strip, a replaced content block, a disabled control
  with an explicit reason — so a reader sees *what changed* by comparing, not by re-reading;
- **is presented as a strip/sequence beneath the canonical render**, in operator-encounter order,
  under one heading (e.g. "States of this surface") — not as a gallery of headline comps;
- **never introduces new navigation, a new page premise, or its own hero.** A state variant that needs
  its own nav has become a second product, which means the state was mis-modelled.

The failure this kills: `--stale` and `--tracking-unavailable` drawn as two full-page designs at the
same size as the canonical frame, so the artifact reads as *three products* rather than *one surface
with three conditions*.

### B4 — Rationale comes AFTER the operational surface, never competing with it

IA rationale, component specs, interaction notes, policy commentary, and open questions live in a
clearly labelled block **below** the canonical render and its state strip. Prose must not:

- open the artifact (no rationale preamble before the first render);
- sit *between* the canonical render and its additive/state group, splitting the operational reading;
- be interleaved paragraph-by-comp so the artifact reads as an essay illustrated by screenshots.

The artifact is an operator surface with an appendix, not a document with figures.

### B5 — Action hierarchy dominates explanatory text — measurably

Inside the canonical render, the **primary operator action and the next-step loop** must be the most
prominent elements: largest type, strongest contrast, most reachable position (thumb zone on a
handheld surface). The scan → feedback → next-scan loop (or the class's equivalent primary loop) must
be legible at a glance without reading a sentence.

The test, applied by the reviewer: *squint at the canonical render — what reads first?* If it is a
paragraph, a heading, a legend, or a caption rather than the action and its loop, B5 **fails**.
Explanatory text inside the operational surface is a supporting label, never a headline.

### B6 — Main-surface copy is compressed to operator register

On-surface copy is written for someone holding a phone in an aisle: short, imperative, scannable at
arm's length. Prefer the verb. Cut the hedge, the restatement, and the sentence explaining what the
button already says. Long-form explanation moves into the B4 notes/spec block — it is **relocated,
not deleted**.

If a piece of copy exists to explain the design to a *reviewer*, it belongs in the notes block. If it
exists to tell the *operator* what to do next, it belongs on the surface — short.

---

## The named failure shape: REVIEW BOARD

An artifact that presents **co-equal comps plus explanatory prose as the deliverable**, instead of one
operational surface with everything else subordinate to it. Four tells, any one of which is a finding:

1. co-equal viewport comps with no dominant canonical render (A2 / B2);
2. state variants drawn as peer full-page designs (B3);
3. rationale opening or interleaving the artifact (B4);
4. explanatory text outranking the primary action in the canonical render (B5).

"Review board" is the diagnosis to name in a finding — a shape defect, not a formatting nit, and the
shape a generator defaults to whenever the handoff leaves composition unspecified.

---

## Enforcement

### Layer A — the handoff gate: class (f), the Handheld-First Declaration

A `page` handoff on a handheld-first DECIDED class is **invalid** unless the brief names all five:

| # | Field | Source |
|---|---|---|
| 1 | **surface class** | the project design policy's route table — read, never invented |
| 2 | **canonical viewport** | derived from `primary_viewport_class` (viewport axis) — exactly one |
| 3 | **additive viewports** (if any) | the other breakpoints, each marked additive; `none` is a legal value |
| 4 | **scan / next-step loop** | the primary operator loop this surface exists to run, stated as a *loop* (trigger → feedback → next), not as a feature list |
| 5 | **offline / degraded state treatment** | which degraded states are first-class, plus the B3 statement that they are drawn as states *of this surface* |

Missing, blank, or hand-waved (`TBD`, `responsive`, `see policy`) on any of the five ⇒ **HARD FAIL**,
brief not deliverable. Fields 1–3 overlap gate class (e) deliberately: **(e) asks *is the canonical
viewport declared and carried into the deliverable?*; (f) asks *does the brief also specify the SHAPE
of the artifact at that viewport?*** A brief can pass (e) with a perfect canonical label and still
commission a review board.

**"Responsive" is an invalid answer to fields 2–3.** A handoff that says the surface is "responsive",
"works on mobile", or "mobile-friendly" has declared nothing: it names a technique, not a canonical
viewport, and it is the exact phrasing that lets a generator pick desktop as the design. The
declaration must name **one** canonical viewport and mark the rest additive.

**(f) never fires on an owner class whose viewport ambition is OPEN** — the same false-positive guard
(e) carries. No decided posture ⇒ no canonical surface ⇒ nothing to compose around.

### Layer B — the review gate

`design-review-pr` (and any artifact-mode `design-review`) **FAILs** the artifact when:

| Check | Fails when |
|---|---|
| **C1 canonical dominance** | the phone/canonical render is not visually canonical — absent, not first, not largest, or unlabelled |
| **C2 no peers** | tablet/desktop read as peers of the canonical render (equal size, equal prominence, ungrouped, or placed before it) |
| **C3 not a review board** | the artifact reads as a review board rather than an operator surface — any tell from the four above |
| **C4 action outranks prose** | explanatory prose outranks the action hierarchy in the canonical render (the squint test, B5), or state variants are drawn as peer designs (B3) |

Each finding names the rule id (A1–A3 / B1–B6) and the artifact location. **C3 is a judgment-lane
check and must cite at least one of the four concrete tells** — "feels like a review board" with no
tell is not a finding.

### Layer C — the generator rule (Claude Design / `design-synthesize`)

Any instruction that commissions a handheld-first artifact carries these three, verbatim in spirit:

1. **Generate the canonical phone surface FIRST and structure the whole artifact around it.** It is
   the deliverable; everything else is subordinate to it.
2. **Do NOT default to a symmetric row of comps.** A phone/tablet/desktop board is the wrong shape
   here even when the phone is leftmost and correctly labelled.
3. **Do NOT let variant states become separate mini-products.** Draw them as degraded states of the
   one canonical surface — same skeleton, one changed region — beneath it, not beside it.

### Honest tiering

| Tier | Mechanism | Class | What it actually guarantees |
|---|---|---|---|
| Workflow halt | `design-handoff` §3f gate class (f) | **PROBABILISTIC** | The brief cannot silently commission a review board — *if the workflow runs*. Skipping the workflow skips the gate. |
| Artifact gate (commit-time) | `custom/githooks/check-design-brief-completeness.sh` declaration check | **DETERMINISTIC detection, WARN-only phase** | Fires on the staged brief file outside the agent, whether or not the workflow ran. Today it reports; it does **not** block. Promotion follows the standing warn-then-gate rule. |
| Review | `design-review-pr` C1–C4 | **PROBABILISTIC** | Catches a wrong-shaped artifact at PR time; depends on the reviewer running it. |
| Generator instruction | brief §7 · `claude-design-prompt.md` · `design-synthesize` | **PROBABILISTIC** | Steers the generator at the moment it composes. This is where the shape is actually decided. |
| Prose | this file + the project policy binding | **PROBABILISTIC** | Awareness. Prose alone is not enforcement. |

**There is no harness-level block, and there cannot be one: a rendered comp is not a tool call**, so
no `PreToolUse` hook can deny it. The strongest tier touching the *brief* is the commit-time check;
the strongest tier touching the *rendered output* is review. Say so — never describe composition as
"gated."

### Prose consumers — the drift surfaces (audit these, not just the gate)

A gate constrains a tool call; it cannot constrain the prose that tells the model what to do. Every
consumer below can independently reintroduce the review-board shape, and each is invisible to the
gates above:

| Consumer | Role | Bound by |
|---|---|---|
| `design-handoff` (step-01 §3f, step-03 checklist, brief-template §4g/§7) | commissions the artifact | gate (f) + §7 deliverable rules |
| `design-synthesize` (step-04 synthesize, step-05 render, step-06 self-critique) | terminal-native generator | Layer C |
| `shared/claude-design-prompt.md` | the paste route (`design-elevation`, `maintenance-triage`) | Layer C |
| `design-artifact-loop` | brief / screen-review authoring | A + B by reference |
| `design-review` / `design-review-pr` | audit | Layer B |
| `design-ingest` / `design-implement` | consume frames | frame identity from B3 (`{primary}--{state}`) |

When this contract changes, walk this table. **A rule with six prose consumers has six drift
surfaces** — enumerate them when the rule is written, not after.

---

## Golden cases

Five reference shapes. The matrix rows with gate classes live in
`design-handoff/viewport-pass-golden-matrix.md` **v4, rows 15–19**; this is the readable version.

**G1 — CORRECT: canonical phone + additive siblings.**
Artifact opens with one phone 375×812 portrait render of the resting operational surface, labelled
in-page *"Canonical viewport: phone-primary clerk receiving — 375×812 portrait."* Beneath it, a
"States of this surface" strip: same skeleton, one changed region each. Beneath that, "Additive
verification viewports" — tablet and desktop at reduced size, same scan-first single column. Rationale
and component specs last, in a labelled notes block. → **PASS.** The only shape that passes clean.

**G2 — INCORRECT: co-equal row of three comps.**
Phone, tablet and desktop side by side at equal size, phone leftmost, each with its own caption; no
dominant render, no in-page canonical label. → **FAIL A1/A2/B2 · C1+C2.** Contradicts no brief field,
which is why only this contract catches it. Reading order is not a label; leftmost is not canonical.
The cold reader defaults to *desktop is the design, phone is the shrink*.

**G3 — INCORRECT: prose-heavy board.**
Opens with three paragraphs of IA rationale and a design-principles list; comps appear below, each
followed by two paragraphs of explanation; the canonical phone render is present and correctly
labelled but is one figure among many, and its primary action is smaller than the section headings
around it. → **FAIL B1/B4/B5 · C3+C4.** Correct labelling does not rescue a document-with-figures; the
squint test resolves to a heading, not the action.

**G4 — CORRECT: degraded states inside one canonical surface.**
One canonical phone render; beneath it a strip of `--offline-queued`, `--stale`,
`--tracking-unavailable`, `--exception` — each the *same* frame, same chrome, same primary-action
position, differing in one status region, each captioned with the condition that produces it and what
the operator can still do. No variant has its own nav or hero. → **PASS B3.** Reads as one surface
under four conditions.

**G5 — INCORRECT: desktop premise reintroduced through additive renders.**
Phone correctly labelled canonical and correctly first; the desktop additive render, however, becomes
a wide multi-column table with hover-revealed row actions and a persistent filter rail the phone
render has no equivalent of. → **FAIL A3/B2 · C2.** Worse than an honest omission: the desktop premise
returns *under a compliant label*, and downstream implementation treats the richer render as the real
design. On a handheld-first surface the desktop render is **a wider phone**.

**Status of the suite: SPECIFIED, NOT YET RUN.** G1–G5 are the authored contract for gate class (f)
and checks C1–C4; they have not been executed against a real handoff. **Do not cite a pass rate.** The
first handheld-first `design-handoff` after this lands is the pilot.

---

## What this does NOT change

No surface's form factor moves. Receiving stays handheld-first where a policy decided it; grading
stays desktop-only where a policy decided it; every viewport-contract field value is untouched. This
file governs the **shape of the artifact** that renders an already-decided posture — nothing more. A
form-factor change still requires the project's own policy amendment plus a fresh handoff, and is
**never** implied by artifact work.

## Where the root fix lives — the three-layer split

| Layer | Owns | Example |
|---|---|---|
| **Project design policy** | *declares the surface class* — which routes, which posture, which canonical viewport | cash-recovery `docs/design-policy.md` §8.1 route table, §8.2a/b posture, §8.2c viewport labeling, §8.2d the binding to this file |
| **Shared handoff / review doctrine (the fork)** | *defines the artifact contract for that class* — B1–B6, gate (f), C1–C4, the golden suite | **this file**, plus its wiring in `design-handoff`, `design-synthesize`, `design-review-pr` |
| **Claude / generator instructions** | *implements it* — the sentence the generator acts on at compose time | brief §7 per-frame outputs · `claude-design-prompt.md` · `design-synthesize` step-04/06 |

The class declaration is project-specific and belongs in the project. The artifact contract is
generic — any handheld-first operator surface in any project needs the same shape — and belongs in the
fork so it fans out. **Never re-derive B1–B6 in a project policy**; bind to this file and add only the
project-specific values (routes, canonical viewport reference size, which degraded states are
first-class).
