---
name: create-agent-outward-discovery-gate
description: "PROPOSAL (owner-gated) — make outward discovery a BLOCKING step in create-agent before step-03 authors a persona. A workflow-contract change affecting 13 projects, deliberately separated from the 2026-07-31 maintenance retrofit."
status: PROPOSED
date: 2026-07-31
affects: 13 synced projects
routing: owner-decision-required
---

# Proposal — `create-agent` must perform outward discovery before authoring

**Status: PROPOSED. Not shipped. This is a workflow-CONTRACT change, not maintenance.**

## What already landed (and what did not)

On 2026-07-31 `create-agent` was retrofitted to **emit** the STD-SKILLPROV-001 §3 provenance block —
`source_research`, `origin_type`, `adoption_reason`. That is maintenance: it wires an existing
ratified standard into a workflow that never carried it.

**It deliberately does not block.** Step-03 emits whatever step-01 produced. If step-01 did no
outward search, the block is emitted with a thin or exempted `source_research` and the persona is
honestly marked rather than silently passed.

This proposal is the other half: **make the search mandatory, and halt without it.**

## The proposal

Insert a gate between step-01 (brainstorm) and step-03 (build):

1. Run an external **web** search and a **GitHub / MCP / extension** search for existing agents or
   skills covering the requested lane.
2. Record the sources as URLs.
3. Make the explicit **adopt / adapt / build-original** call, with a named reason when original.
4. **HALT** if the pass did not run, naming what is missing — the same halt-with-diagnostic shape the
   brief intake checks already use.

## Why it is a contract change, not a tweak

`create-agent` is fork canon. It syncs to **13 projects**. Adding a blocking step changes what every
one of those projects experiences when they author an agent:

- A workflow that previously always completed can now **halt**. Any caller assuming it terminates
  needs re-checking.
- It introduces a **network dependency** in a workflow that had none. Offline or sandboxed sessions
  currently succeed; after this they stop.
- It adds real latency and cost to every agent-authoring run, including trivial ones.

Per the fork's own routing rule, changing what a rule **is** gets proposed. Only the owner decides
whether 13 projects take that friction.

## The case for

The standard already requires the outward pass — §1 is not optional. Today `create-agent` neither
performs nor prompts it, so the standard is satisfied only when the operator happens to remember.
That is exactly the enforcement gap STD-SKILLPROV-001's own honesty section names: **prose is not
enforcement.**

And the failure it prevents is measured, not hypothetical: the standard's origin ruling records a
capability reported absent from an inward-only check while an official connector existed unsearched.
An agent-authoring workflow is the highest-leverage place to catch that, because everything it emits
inherits the omission.

## The case against, honestly

- **A blocking network step is a real availability regression.** Sandboxed and offline sessions
  currently author agents fine.
- **The gate cannot verify quality.** It can force URLs into a field; it cannot tell whether the
  search was good. A determined operator satisfies it with one lazy link, and the field then *looks*
  compliant — arguably worse than an honest blank.
- **Cost falls on every run, including obvious originals** where the answer was never in doubt.
- The same friction argument sank per-workflow sync windows; it deserves weighing here too.

## Options

| # | option | effect |
|---|---|---|
| **A** | **Hard gate** — halt without the pass | strongest; the availability regression is real |
| **B** | **Warn-only** — prompt, record, never halt | no regression; enforcement stays probabilistic |
| **C** | **Gate with a logged override** — halt, but `--no-discovery` proceeds and stamps `exemption_reason` on the record | keeps the offline path, makes skipping visible and auditable |

**Recommendation: C.** It matches how every other gate in this fork behaves — fail loudly, allow a
deliberate override, and make the override leave a mark. A hard gate that blocks offline work gets
routed around, and a routed-around gate teaches people to ignore gates.

## Sequencing

This should NOT ship before the STD-SKILLPROV-001 pilot runs. The standard is DRAFT and its
deterministic tier is unbuilt; gating 13 projects on a draft is backwards. Pilot the provenance
linter in one skills-heavy repo first, then decide this.

## Distribution note

Whatever is decided rides the **batched fleet re-sync gate**. Per the owner ruling of 2026-07-26, no
`custom/` change gets its own sync window.

## Decision owed

Mason: **A, B, or C** — and whether it waits on the pilot.
