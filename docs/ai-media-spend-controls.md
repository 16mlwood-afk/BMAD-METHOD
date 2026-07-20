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
wrong model. None of it needed a better tool; it needed these six gates.

## The six preconditions — hard gates before ANY spend

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
