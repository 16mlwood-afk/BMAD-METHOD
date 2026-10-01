# AI-Media Spend Controls — fork default

**Status:** ratified 2026-07-20 (origin: cash-recovery clerk photo-step video programme).
**Scope:** any **optional** AI-generated media — video, imagery, audio — produced to enhance a surface
that already functions without it. Coaching clips, illustrative stills, decorative or instructional
assets. Does **not** apply to media that IS the product.

**Reference standard, not a sync-distributed workflow.** Lives in `docs/` deliberately so
`sync-bmad-workflows.sh` does NOT fan it into project repos. Nothing changes in any project until that
project points at this file. Point a prompt pack, brief, or design policy here rather than restating it.

## Why this exists

A 2026-07-19/20 programme in cash-recovery generated 6 clips across 3 angles for **45 credits** and
shipped **zero** — no assets in the repo, no UI, no scope change, and the running application byte-
identical to before. Every failure was **structural**: sequencing and missing gates, not bad luck or the
wrong model. None of it needed a better tool; it needed these gates.

## The seven preconditions — hard gates before ANY spend

1. **Gate before generation.** No spend until (a) an acceptance rubric exists in writing, and (b) at
   least one candidate passes that rubric's top-tier utility test **on paper**, against a plausible,
   evidence-backed problem. *(Failure mode observed: the rubric was written after three clips existed;
   had it come first it would have predicted at zero cost that two of the three were weak candidates.)*
2. **Probe the make-or-break capability FIRST.** If the case hinges on one hard capability, spend a
   single sacrificial generation testing **that** before committing to a programme. Never test the
   headline requirement last. *(Observed: the headline capability was tested 4th and 6th, for 15 credits,
   and the conclusion drawn was still wrong — see §Inference discipline.)*
3. **No generation while inspection is broken.** If the artifact cannot be objectively scored — frame
   extraction, playback, whatever the rubric needs — it does not get generated. Repair the tooling
   first; it is usually free and takes one command. *(Observed: three clips generated and handed over
   unviewable and ungated.)*
4. **Price the integration path up front.** Estimate storage/compression + contract or test changes +
   UI work + any scope-change cycle **before** the first run. If integration cost exceeds creation cost,
   state that explicitly and confirm the spend deliberately. *(Observed: integration cost surfaced only
   after the credits were gone, and exceeded generation cost.)*
5. **Re-run the STRATEGIC gate, not just the sequencing gate.** When conditions change, re-ask
   "*should we do this at all?*" — not merely "*is it correctly sequenced now?*". A deferral that lapses
   because its precondition cleared is a technicality, not a decision. *(Observed: an earlier review
   concluded "this is a v2 concern for a v0 surface"; when the sequencing objection cleared, the
   strategic objection was never re-asked.)*
6. **Evidence-first for optional enhancement.** Require at least one of: observed errors in logs or
   support, pilot feedback, or measured confusion in testing. **Absent evidence, the default is NO
   spend.** Scoring what a medium *can* do is not evidence that anyone needs it. *(Observed: every
   utility score was a judgement about the medium; no operator failure was ever demonstrated.)*

7. **Articulated question, and the cheapest medium that can answer it.** No generated visual artifact
   ships unless it answers a **real, written-down question about hierarchy or behaviour** — and the
   question must be one the **cheaper medium one rung down cannot answer**. Climb the ladder
   deliberately, never skip a rung:

   | Rung | Medium | Answers |
   |---|---|---|
   | 0 | prose / a spec table | what the thing *is* — vocabulary, states, naming, rules |
   | 1 | hand-authored HTML + real tokens | **static hierarchy and density** — how it composes, at a real viewport, in real type, pixel-accurate and diffable |
   | 2 | generated still | composition or illustration that hand-authoring genuinely can't reach (photographic scenes, physical context, texture) |
   | 3 | generated motion | change over time — a gesture, a transition, a sequence a still cannot hold |

   **Write the question down before choosing the rung**, and name the rung you rejected and why. "It
   would be useful to see it" is not a question. A vocabulary or naming question is rung 0 and must never
   be bought at rung 2. **For any question about a UI's own hierarchy, density, or emphasis, rung 1 is
   the default and rung 2 is almost always wrong** — a generative model cannot be held to a token
   contract, so the artifact it returns is un-diffable and non-binding on the very properties the
   question was about. *(Owner framing, video tier: "no new visual artifact ships unless it answers a
   real, articulated question about hierarchy or behaviour that a still cannot.")*

   **The bar is the one the references actually meet.** "Stripe-esque" / "Linear-esque" means high
   density, clear hierarchy, restrained emphasis — evaluate the artifact against *that*, not against
   "it looks nice." A well-rendered element on an empty canvas passes no hierarchy test, because there
   is no hierarchy in it to test.

**Standing caution — do not launder a bad process with a good result.** A clip that later passes does
not retire these gates. The programme above produced one genuinely good asset and was still run backwards.

## Gated ≠ rejected

When these gates stop a programme, record it as **GATED**, and record **which precondition is unmet**.
Never record it as "parked", "rejected", or "the model can't". A future session reading "parked" will
treat the capability as closed; reading "gated on precondition 6" will know exactly what would reopen it.

## Inference discipline for negative capability claims

Do **not** record "the model cannot do X" unless the failing runs were **free of confounds you
introduced**. In the programme above, two failures were logged as proof a model could not synthesise a
moving light source. Both prompts had asked for a camera that was simultaneously *"roughly still"* and
*"handheld with small natural jitter"* — contradictory instructions — so the model resolved the conflict
by moving the camera, crowding out the light motion. The controlled case was never run and the claim was
retracted.

**A fabricated capability limit is worse than a wasted run**: the run costs credits once, the false fact
suppresses every future attempt for free.

## Prompt hygiene (transferable)

- **Mutually exclusive instructions must not share a prompt.** Handheld realism and a locked-off
  demonstration are incompatible; pick one per generation.
- **Never describe the defect you are trying to avoid.** Briefing a move as "drift, settle, ease in"
  produces exactly the smooth glide that a realism rubric then fails.
- **Fix wrong-task output with constraints, not adjectives.** When a model performs a different action
  than asked, the cure is a named allowed behaviour, an occlusion ceiling, and a minimum count of frames
  in which the subject must be visible — not more evocative verbs.

## Case study — the mis-scoped swatch (2026-07-20, cash-recovery `/inbound` carrier chips)

**What was asked for:** a reference asset for a newly-designed per-row carrier monogram chip
(`RM` · `UPS` · `AMZL` · `DPD`) on a clerk arrivals board.

**What was generated:** a swatch board — five chips floating on an otherwise empty 16:9 canvas with
captions underneath. 4 credits, `nano_banana_2`, two near-identical variants. The **capability probe
passed** cleanly: exact monogram spelling, and zero logos / brand colours / carrier trade dress, which
was the make-or-break risk. The owner's verdict on the artifact itself was nonetheless *"my god they're
awful."*

**Root cause — mis-scoped artifact, not a bad model.** The model rendered precisely what the prompt
specified. The prompt specified the wrong thing: it front-loaded pixel values the model reliably ignores
(4px radius, exact hex, 1px border, 10px captions) and under-specified the one dimension a diffusion
model *does* honour — **composition**. The result was ~90% dead canvas at marketing scale, which tells a
reader nothing they did not already know from reading the four strings. The unexamined assumption was
that the useful artifact was a **vocabulary swatch**; the actual open question was **behavioural** — how
a carrier monogram sits in a dense phone worklist row without competing with arrival state, and what
occupies the slot when the ship-method code does not resolve. A swatch board is structurally incapable
of answering that.

**Corrected spec (the artifact that should have been built):** a **375px-wide column of 5–6 real parcel
rows** — order ref, expected contents, arrival state, carrier chip — with the chip as one small quiet
element among competing ones, and one row showing the unresolved slot. Context is the deliverable; the
original crop removed it.

**Correct rung: 1, not 2.** The question was about the app's own hierarchy and density, so it belonged in
hand-authored HTML against real tokens — free, pixel-accurate, diffable, and bindable to the design
policy. The generated still could not be held to the token contract at all: its radius, shadow, and scale
all violated the project policy, so the asset had to ship marked *vocabulary-only, non-binding on every
visual property* — which is the tell that rung 2 was never the right purchase.

**Durable lessons:** (a) precondition 7 exists because of this run — write the question down, then pick
the cheapest rung that can answer it; (b) a passing *capability* probe is not a passing *artifact* —
score both, separately, and do not let the probe's success imply the artifact's; (c) when a UI reference
is wanted, reach for the token render first and reserve credits for motion and illustration that cannot
be authored cleanly by hand.
