---
name: 'step-02-fanout-enumerate'
description: 'Fan out one isolated agent per drawn frame to enumerate that frame''s COMPLETE top-level section list + component×property catalog. The frame is the fan-out unit; each agent is told to enumerate its frame exhaustively, never a named subset. An empty section list for a drawn frame HALTS (frame-completeness gate).'
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

Run the frame agents concurrently where the harness allows (independent reads). Collect each into `{frame_sections}[frame]` (the ordered section list) and `{section_catalog}[frame][section]` (copy + property rows + data fields).

## 2. FRAME-COMPLETENESS GATE  (the named structural check)

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
