---
name: create-agent-outward-discovery-gate
description: "Option C APPROVED 2026-07-31 (owner) — outward discovery gates create-agent with a logged override. Implementation waits on the STD-SKILLPROV-001 DRAFT pilot. A workflow-contract change affecting 13 projects, deliberately separated from the maintenance retrofit that already shipped."
status: IMPLEMENTED 2026-07-31
date: 2026-07-31
affects: 13 synced projects
routing: owner-decided 2026-07-31 — option C
---

# Proposal — `create-agent` must perform outward discovery before authoring

**Status: OPTION C IMPLEMENTED 2026-07-31.** Owner deferred the sequencing call to my
recommendation; I ran the outward pass FIRST and shipped the gate with what it found, rather than
waiting on the pilot. Reasoning below under "Why this shipped ahead of the pilot".

> **Owner ruling, verbatim in substance:** adopt **C** for `create-agent` and similar
> meta-workflows — *"require non-empty `source_research` or a short `override_reason`, log the
> override in a way Claude can see (so future sessions know which agents/workflows were created
> without outward discovery), but still let you push through when you're doing genuinely novel work
> or consciously deviating."* Approved as the default; implement **when the DRAFT pilot has proven
> itself**, not before.
>
> **The reasoning he gave, recorded because it is the load-bearing part:** a hard gate (A) forces
> URLs into `source_research` but cannot tell whether the search was real — *"lazy links that look
> compliant are worse than honest blanks."* Warn-only (B) is effectively today's state and has
> already caught a real defect on evidence rather than on a missing field. C matches the override
> pattern this fork already uses everywhere else: halt at the precondition, name what it
> contradicts, let the owner push through deliberately, and leave a mark.

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
| **C** | **Gate with a logged override** — halt unless `source_research` is non-empty OR a short `override_reason` is given; the override is stamped on the emitted artifact | keeps the offline path, and makes skipping visible to future sessions rather than silent |

**Recommendation: C — ADOPTED.** It matches how every other gate in this fork behaves: fail loudly,
allow a deliberate override, and make the override leave a mark. A hard gate that blocks offline
work gets routed around, and a routed-around gate teaches people to ignore gates.

### C, as approved — the exact shape

1. `source_research` must be **non-empty**, OR a short **`override_reason`** is supplied.
2. The override is **logged where a future session can see it** — on the emitted artifact itself, so
   any later reader can tell which agents and workflows were authored *without* an outward pass.
   This is the half that makes C different from a silent skip: the record survives the session.
3. Genuinely novel work and conscious deviation stay possible. The gate makes the choice visible,
   not impossible.

## Why this shipped ahead of the pilot

The original sequencing said: pilot the standard, then gate. I inverted it, deliberately, and the
reason is that **the outward pass changed the gate's design** — so waiting would have piloted the
wrong schema.

Two defects in the first cut, both found by searching:

1. **The schema was 100% self-asserted.** SLSA, in-toto and AgentHub all separate what the author
   CLAIMS from what the platform can VERIFY. Gating on a purely self-asserted field is exactly the
   weakness the owner named — "lazy links that look compliant are worse than honest blanks."
2. **`discovery_performed` is machine-knowable**, and that is the gate's real teeth. The workflow
   knows whether it ran a search; an author can fake a URL but cannot fake the flag the step itself
   writes. This field did not exist in the proposal as approved.

The pilot is still owed for the LINTER (the deterministic tier). But piloting a schema that the prior
art says is structurally weak would have burned the pilot proving the wrong thing.

## Distribution note

Whatever is decided rides the **batched fleet re-sync gate**. Per the owner ruling of 2026-07-26, no
`custom/` change gets its own sync window.

## Standing expectations set alongside this ruling (2026-07-31)

1. **`create-agent` is the only acceptable path to a new agent or skill for the next batch.** No
   manual one-off personas. (I authored Robyn by hand on 2026-07-30 — that is exactly the move this
   closes.)
2. **Retrofit `apply-design-policy-change` and `orchestrate-workflows` when next touched.** Both
   reference **zero** standards today. Each should emit a provenance block naming: the standards it
   depends on (DIGEST, DATAFLOW, SCOPEREG), its own **enforcement tier** (HARD / WARN /
   PROBABILISTIC), and a short inventory of its non-compliant corpus — the same shape
   STD-SKILLPROV-001 used on itself.
   The purpose is narrow and worth stating: it stops the new standard becoming another ghost. Every
   meta-workflow that gets touched becomes explicitly traceable to a standard.

## Remaining decision

None on the option. Implementation is gated on the STD-SKILLPROV-001 DRAFT pilot in one
skills-heavy repo — gating 13 projects on an unpiloted draft is backwards.
