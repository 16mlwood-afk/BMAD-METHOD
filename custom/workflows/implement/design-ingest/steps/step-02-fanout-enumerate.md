---
name: 'step-02-fanout-enumerate'
description: 'Fan out one isolated agent per drawn frame (in capped waves) to enumerate that frame''s COMPLETE top-level section list + component×property catalog. The frame is the fan-out unit; each agent is told to enumerate its frame exhaustively, never a named subset, and a frame sharing a source file with a sibling also gets its resolved state selectors. An empty section list for a drawn frame HALTS; an agent that NEVER RETURNS takes the transport ladder (bounded retry, resume-missing, then ask) and never becomes a silently absent frame.'
---

# Step 2: Fan-out Section Enumeration

**Progress: Step 2 of 3** — Next: Emit manifest + handoff pause.

## RULES

- Autonomous.
- **The fan-out unit is the FRAME, not a feature-area.** This is the durable fix for the failure that motivated this workflow: delegating by feature-area with narrow prompts ("the cost-recon section") let a whole section (Reconciliation, SellerSmart dispatch) fall in the seam between two agents' scopes. Here, one agent per `drawn: true` frame, each instructed to enumerate the frame COMPLETELY.
- Context is bounded by construction: each frame agent reads only its frame's source files, not the whole bundle.

---

## 1. Fan out — one agent per drawn frame

For each `{design_frame_inventory}` entry with `drawn: true`, launch an isolated sub-agent (read-only; `Agent` tool). Each agent's mandate, verbatim in spirit:

> **Enumerate this ONE frame COMPLETELY.** First, read the frame's source fully and list EVERY top-level section it renders, in render order, with the heading/copy of each. Do not stop at the sections you were told about — find them all; a section you fail to list is a section that ships wrong. Then, for each section, catalog: (a) the verbatim copy strings it renders, (b) the component×state×property rows (radius/color/spacing/type — exact values from inline styles / `<style>` blocks / tokens), and (c) the data fields the section reads. Return a structured per-section report. You do NOT implement and you do NOT judge correctness — you catalog.

Give each agent: the frame's source file(s) under `{design_dir}` (the traced module(s) for that frame, or the sibling `<frame>.html`), `{design_tokens}` for value resolution, and the frame's role/parent. Do NOT give it the whole bundle.

**When more than one frame shares a source file, the file is NOT enough — pass the frame's RESOLVED STATE SELECTORS too.** "The frame's source file" presumes one file per frame. That presumption breaks routinely: state variants of one surface live in one module, so several agents get a byte-identical file and **no way to know which variant they are enumerating.** Whatever selects the variant — an `sc-if`/prop map in a `.dc.html`, or a `pickFor`/`goFrame`-style chooser in a *third* module on the legacy JSX path — is invisible from inside the shared file. So for every frame whose source file is shared with a sibling, state in the prompt: the exact selector values that make this frame the rendered one (claim/record state, prop values, window class, status), and which sections consequently take a different branch. Resolve them yourself from the selecting module before you fan out; an agent that has to guess its own variant will silently catalog the default. **Trigger is `frames-per-file > 1`, not the bundle shape** — the legacy shape reaches it as soon as a surface has state variants. (Observed 2026-07-27: 9 of 11 frames shared a file; the 5 workspace variants were selected from a third module. Related: `FG-2026-07-26-09`, whose fan-out-unit redefinition remains owner-gated — this is the coherence repair that makes the CURRENT unit usable, not that redefinition.)

**Launch in WAVES, not all at once.** Run frame agents concurrently, but cap concurrency (~4–6 in flight) and start the next wave as slots free. This workflow is deliberately routed the LARGEST surfaces (the size preflight sends anything >=5 frames here), so "launch one per frame" on a wide bundle means a big simultaneous burst — which can itself provoke provider-side load-shedding and take out most of the fan-out at once. Waves also make §2's resume cheap: a failed wave is a handful of frames to re-dispatch, not the whole set. (Observed 2026-07-27: 11 launched at once, 8 died on API 529, and retries issued into the already-shedding API also failed.)

Collect each into `{frame_sections}[frame]` (the ordered section list) and `{section_catalog}[frame][section]` (copy + property rows + data fields).

## 2. FRAME-COMPLETENESS GATE  (the named structural check)

**Two different failures reach this gate, and only one of them used to be modelled.** Separate them before recovering — the remedies are not the same:

- **RETURNED-BUT-EMPTY** — the agent came back and its section list is empty or absent. Handled below; it is an under-read.
- **NEVER RETURNED** — the agent died (transport/API error, timeout, killed mid-run) and produced no result at all. This is a **transport** failure, not an under-read, and it says nothing about the frame. Ladder, in order:
  1. **Re-dispatch that frame** (bounded: 2 attempts, spaced). Do not re-dispatch the whole fan-out — completed catalogs are independent and re-running them wastes the spend and risks a fresh burst.
  2. **If a whole wave died, wait before the next attempt.** Simultaneous deaths across unrelated frames mean the provider is shedding load, not that the frames are hard; immediate retries into that condition fail too.
  3. **RESUME, don't restart:** dispatch only the frames still missing, in a smaller wave.
  4. **If frames are still missing after that, STOP and ask the user.** Do not quietly substitute a different enumeration method. Put the choice to them plainly: (a) wait and resume the missing frames later, (b) declare an honest partial — emit with `completeness.frames_not_enumerated` naming exactly the missing frames, which `design-implement` must refuse unless the operator accepts the partial, or (c) enumerate the missing frames in the orchestrator context. **(c) is NOT a default and must never be taken silently:** it trades away the per-frame isolation the fan-out exists for, so it is only defensible when the orchestrator ALREADY holds the source (e.g. the URL-path mirror had to pull the bundle through context anyway — see `design-implement` step-01a §URL.1b). If (c) is chosen, the manifest MUST record which frames were enumerated which way and what the deviation cost. Whether (c) is legal at all is an OPEN owner question (`FG-2026-07-27-05`) — until it is ruled on, surface it as a choice, never as your own call.

**Never let a dead agent become a silently absent frame.** A frame with no catalog and no record of why is the exact "a whole section goes missing" failure this workflow exists to prevent, arriving through a different door. (Observed 2026-07-27: 8 of 11 agents died on sustained API 529s; the gate below had no branch for it.)

For every `drawn: true` frame, after its agent returns:

- If `{frame_sections}[frame]` is **empty or absent**, the gate has tripped — a drawn primary or detail frame always has top-level sections, so an empty list means the agent under-read it, not that the frame is genuinely blank. **First, try to recover quietly:** re-run that one frame's agent with the full frame source. Most empty lists are a missed read and come back fine on the retry, so there's no need to involve the user for that.
- **If it STILL comes back empty after the retry, stop and talk to the user** — plainly, not in a gate-failure box. Tell them what happened in your own words: you read `{frame}` twice and couldn't pull any sections out of it, which usually means the source didn't load properly or that screen really is an empty stub. Ask them how they want to play it — point you at the right source for that screen, or confirm it's a stub so you can mark it `drawn: false`. Don't carry on with an empty section list: this is exactly the "a whole section goes missing inside a present frame" failure the workflow exists to catch, so it's worth a real check-in.

Do not proceed to step-03 with an empty section list on a drawn frame. (A `drawn: false` frame legitimately has no sections — it is recorded as not-drawn and skipped here.)

- **Soft check (warn, don't halt):** a `drilled-detail` drawer with only 1 section is suspicious (drawers are usually multi-section). Surface it in the summary as `thin-frame: {frame} (1 section)` so the reviewer eyes it at the handoff.

## 3. Self-critique — "what's missing?"

Before assembling, run one completeness critic over the collected inventory: for each drawn frame, ask "is there a section in the design source that no agent listed?" (e.g. a `<h4>` heading, a `grp`/`data-region` block, a conditionally-rendered banner). Anything found is added; if the critic finds a systematically missed class, re-fan the affected frame. This is the loop-until-dry tail that a single pass misses.

## 4. Tell the user you're through the screens

A quick, human update — you've been through every screen and here's the shape of what you found. Lead with a sentence, give the per-screen counts plainly, and call out anything that looked thin (a detail drawer with only one section is worth a mention — you'll flag it for them at the review). Keep it short; the detailed walkthrough comes at the step-03 pause. For example: *"Done — went through all eight screens. The order drawer's the big one (10 sections); the worklist has 4, and the lookups run 2–3 each. Nothing came back empty. The dispatch lookup looked a bit thin, I'll point that out when you review."*

What you're conveying (not a format to print): `{M}` drawn frames enumerated · `{sum}` sections total · per-frame counts · any thin-frame warnings · empty section lists (must be none — step-02 would have stopped above otherwise).

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-ingest/steps/step-03-emit-manifest-and-handoff.md`

## SUCCESS METRICS

- One agent ran per `drawn: true` frame; each was scoped to its frame only (context bounded).
- `{frame_sections}` non-empty for EVERY drawn frame (gate passed).
- `{section_catalog}` populated per (frame, section) with copy + property rows + data fields.
- The completeness critic ran; any systematically-missed class was re-fanned.

## FAILURE MODES

- **Delegating by feature-area instead of by frame** — reintroduces the exact seam-blindness this workflow fixes. The fan-out unit is the frame; the prompt says "enumerate this frame completely," never "look at the X section."
- **Accepting an empty section list on a drawn frame** — the gate exists precisely to stop this; an empty list is a defect, not an empty success.
- **Loading the whole bundle into the orchestrator** — defeats the context fix. Each frame agent reads only its frame.
- **Letting a DEAD agent become a silently absent frame** — a frame with no catalog and no record of why is the same "whole section goes missing" failure arriving through the transport door. Take the §2 ladder; if frames remain missing, either declare them in `completeness.frames_not_enumerated` or ask — never omit.
- **Silently switching enumeration method when the fan-out fails** — orchestrator-inline enumeration trades away the isolation the fan-out exists for. It is a choice to put to the user, recorded on the manifest, not a fallback to take quietly (`FG-2026-07-27-05`, open).
- **Handing a shared source file to several agents with no state selectors** — each one sees the same bytes and cannot tell which variant it is enumerating, so they all catalog the default and the variants' real deltas vanish. Resolve the selectors before fanning out.
- **Launching one agent per frame all at once on a wide bundle** — the burst can provoke provider load-shedding and take out most of the fan-out simultaneously. Cap concurrency and run waves.

---

## Resolve every vocabulary you dereference — a reference is not a value

A frame's copy is often driven by a lookup table in the design source — `DECISION[decision].label`,
`DEFECT[defect].note`, `GAPS[k].label`, `LIFECYCLE[claim.lifecycle].label`. **Recording the
expression is not recording the copy.** The row then looks complete and specific while the string
the surface renders exists nowhere in the manifest.

**Do this, per frame, before you emit:**

1. When a cell you are writing dereferences an ALL-CAPS vocabulary, open its definition in the
   design source and **resolve every member you can reach** — the full `label` (and `note`, where a
   row renders one) for each key.
2. Put them **once** in a `### Vocabulary: <NAME>` block alongside the property catalogue, and let
   rows dereference it exactly as they dereference `→ §6/<id>`. Do not copy a vocabulary per row —
   that is the same self-drift the normalised catalogue exists to prevent.
3. List `<NAME>` in `completeness.resolved_vocabularies`.
4. If a vocabulary genuinely cannot be resolved, declare it in `completeness.unresolved_references`
   as `"<NAME>: <why>"`. **Declared is fine. Silent is not** — the consumer cannot distinguish a
   deferral from an omission, and one of those it is allowed to act on.

**Why this is your job and not the consumer's.** `design-implement` is required to reproduce copy
VERBATIM; a paraphrase is prohibited. So an unresolved reference leaves it two legal moves — re-read
the design source, or halt — and the re-read is exactly what a **delegated sub-agent cannot do**: the
design MCP is session-bound and absent from sub-agent contexts (`FG-2026-07-26-01` / `-06`), which is
the documented way a large surface is handled. You are the last context that can reach the source
cheaply. Leaving the reference unresolved exports an impossible task and invites an invented string.

Machine-checked at emit by `tools/check-ingest-manifest.js` **C11** (step-03 §2 runs it `--strict`).
It fires only on the `NAME[...].field` shape, so lowercase accessors and `.length` are invisible to
it. On the sweep that introduced the check, **four of eight** delivered manifests carried at least
one unresolved vocabulary while declaring value-exact grain — treat this as the normal failure, not
an exotic one.
