---
name: close-out-contract
contract_version: 1
description: 'Shared policy for the SHAPE of a workflow''s terminal close-out / hand-off message, and for routing feedback about output shape. A close-out is written for the NEXT actor (consumer / the user''s next decision / the downstream workflow), never as a narration of what the agent did; and a critique of output shape is a workflow-PATCH request, not a memory or a one-off rewrite. Sibling of delivery-to-main.md (which owns the delivery MECHANICS; this owns the MESSAGE). Referenced by any step that emits a final user- or consumer-facing message — design-handoff (step-04 §10), design-synthesize, design-implement, design-review-pr, quick-dev, onboard-design-system, maintenance-triage, and peers.'
---

# Close-Out Contract — Terminal-Message Policy

**Why this exists.** A workflow's last step emits a final message — the hand-off. Left unspecified, terminal steps default to **narrating what the agent did**: "I gathered X, then ran Y, then merged Z." That process recap raises the reader's cognitive load, buries the one thing the next actor actually needs, and reads as a diary instead of an instruction. Worse, when a user pushes back on that shape ("stop narrating history", "lead with the active artifact"), the feedback gets absorbed at the **wrong abstraction layer** — as a conversational preference, a project-memory entry, or a one-off rewrite of the current message — leaving the workflow template (and every other project that syncs it) still wrong.

This policy fixes both at the root: it defines the default message shape, and it routes shape-feedback to a workflow patch.

`delivery-to-main.md` is the sibling standard — it owns the *mechanics* of getting an artifact onto `main` (commit → push → PR → merge). This standard owns the *message* a step emits once the work is done. A deliver step typically implements both.

---

## 1. Scope

Applies to any workflow step that emits a **final user- or consumer-facing message** after the work is done — a deliver step, a close-out, a hand-off prompt, a "done / next step" summary.

Does NOT apply to:
- A terminal step whose only job is to **write an artifact to disk** with no narrated message (the shape is the artifact's own; `delivery-to-main.md` governs its delivery).
- Mid-workflow progress or step-boundary notes.
- A turn where the **user explicitly asked for the trace** (see §3).

---

## 2. The close-out shape — audience-first, never process narration

**Write the close-out for the NEXT actor, not as an account of yourself.** The next actor is whoever acts on the output: a downstream consumer (Claude Design, `design-synthesize`, `design-implement`), the user's next decision, or a sibling workflow. Lead with what now holds and what they do next.

**Default structure** (workflows MAY rename sections to fit their domain, but keep the audience-first ordering and omit any line whose source is empty — never pad):

1. **Active artifact / result** — what now exists or is true that didn't before (the file, the merged change, the verdict).
2. **What changed** — the material delta, in plain language. Not the steps that produced it.
3. **Substantive corrections / scope deltas** — the real fixes or scope changes the next actor must know (e.g. a data-boundary or least-privilege correction). Skip the heading entirely if none.
4. **Status** — delivery / verification state (PR merged, tests green, deploy pending), stated faithfully — a skipped or failed step is named, not softened. **For a completion-oriented workflow** (one whose job is to deliver code or a consumable artifact), this element carries a structured `completion_disposition` per `shared/completion-contract.md` (STD-COMPLETION-001): `pr_merged` / `pr_open` with the PR, `owner_gated_residue` with each remaining blocker named, or `advisory` with a why. Diagnosis with no disposition is an invalid exit (the commentator failure). Advisory-only flows (audits, reviews, routers, triage) declare `advisory` once and are exempt from a PR disposition.
5. **Next-actor instructions** — what the consumer does next. When the next actor is an external design consumer, include the short interpretation block: which artifact is active, revision vs new, how to read composition / page-mode, what NOT to import from the prior implementation.

`design-handoff`'s `step-04-deliver.md` §10 is the canonical design-lane instantiation of this shape; other deliver steps mirror it in their own domain terms.

A workflow MAY append a domain-specific **owner-facing addendum** after the next-actor block when it carries forward-looking signal the owner needs (not a process recap). The sanctioned design-lane example: design-handoff §10 and design-router both append an **Outstanding (design backlog)** triage — top candidates in priority order (designed-not-built → built-no-brief reconcile → unowned concept gaps), register-optional (read `docs/surface-register.*` if present, else derive from briefs + built routes). It is owner-facing (distinct from the consumer block), forward-looking (not narration, so §3 does not forbid it), and PROBABILISTIC (no gate).

---

## 2a. The two-block close-out — plain answer, then at most one paste-back block

**Every close-out is one or two blocks, in this order, never interleaved.**

**Block 1 — the plain answer (always).** The §2 shape above, in plain language, for the human
reading it. No house vocabulary, no ID soup, no fenced structures. If a voice is bound to the
workflow's `persona_slot` (`shared/workflow-personas.md` §1), block 1 is the **only** block it
may touch.

**Block 2 — one fenced `FOR YOUR LLM ADVISER` block (only when earned).** Emit it when, and only
when, the close-out carries **actionable technical detail** — file paths, artifact IDs, mechanism
or gate names, commands to re-run, dispositions, structured findings, provenance tokens — that
another *model* would act on. It is written to be pasted onward, not read.

- **Exactly one block, at the end.** Never two, never interleaved with the prose.
- **Neutral, imperative, machine-shaped.** No persona voice, no first person, no warmth, no
  re-orientation line. A bound voice speaks in block 1 and is **silent** here — block 2 is a
  payload, not a speech.
- **Omit it entirely when nothing actionable exists.** A manufactured block is a defect, not a
  courtesy; "nothing to hand on" is a complete close-out.
- **It is NOT the trace.** Verbose command output, logs, stack traces, file dumps and long diffs
  stay behind an explicit "show details" ask (§3). Block 2 carries conclusions and handles; the
  trace carries scroll. A close-out that pastes raw output into block 2 is wrong twice — it
  buries the handles and leaks the scroll.

**Why the split is by ACTIONABILITY, not by lane or length.** A reader asking "is this technical
enough to hide?" draws the line differently every time, which is how a close-out drifts into
either a wall of jargon or a summary with the handles missing. "Could a second model act on this
without the transcript?" has one answer.

---

## 3. Process narration is forbidden by default

Unless the user *explicitly* asks for the trace, the close-out MUST NOT contain:

- "I did X, then Y, then Z" — step-by-step recap of your own actions.
- Branch / PR / git choreography or other delivery mechanics.
- Workflow history, a decision diary, or provenance bookkeeping.
- Re-explaining a tool call or a file you read.

Say each thing once. A one-line re-orientation and a genuine risk worth flagging are allowed; a process essay is not.

**Trace on demand.** When the user asks "show the trace", "what did you run", "show details", or similar, switch fully to detail mode **for that turn** — surface the commands, the evidence, the step-by-step. Detail is gated, never withheld.

---

## 4. Output-shape feedback is a WORKFLOW-PATCH request — route it to the fork, not to memory

When the user critiques the **shape** of a workflow's output — e.g. "stop narrating workflow history", "speak in terms of active artifact / material delta / next-consumer instructions", "this should be fixed at the workflow root" — treat it as a **defect in the workflow definition**. NOT a conversational preference, NOT a one-off rewrite of the current message, NOT a project-memory entry. The required response:

1. **Patch the template first.** Edit the relevant step definition in the fork (`~/bmad-method-v6/custom/workflows/…` — the deliver/close-out step, or this shared contract if the rule itself is wrong) so the fix propagates to every project on the next `sync-bmad-workflows.sh`.
2. **Then regenerate** the in-flight output from the updated contract. Fix the template, then re-emit — never re-emit without patching.
3. **Memory is a soft backstop only.** A `*-completion-note-shape` style memory may exist as a preference, but it is NEVER the primary remediation: a memory does not propagate by sync and leaves the root template wrong for every other project. **If the only artifact produced is a memory, the defect was not fixed.**

This routing is itself part of the contract: a context-free agent reading a deliver step must come away knowing that "your output shape is wrong" means "patch this workflow," not "remember my preference."

---

## 5. Enforcement honesty

Runtime conformance — the agent's actual emitted close-out message — is **PROBABILISTIC**: it shapes model output, and no file-based gate can read a conversational message. The durable lever for runtime drift is §4: when the shape drifts, the feedback patches the template, so the corpus converges over time rather than re-litigating per session.

The **template files** ARE deterministically guarded. `tools/validate-close-out-contract.js` (npm `validate:close-out`, in the fork's pre-commit fast-path + `npm test`) is a **DETERMINISTIC GATE** over `custom/workflows/`: it fails the commit when a workflow file *instructs* narration (a high-precision phrase like "summarize key accomplishments", "recap of what you did", "narrate the workflow") **without** adopting this contract. Adopting it — referencing `close-out-contract.md` / `STD-CLOSEOUT-001` — is the logged, in-file escape hatch (a contract-aware file quotes those phrases as negative examples, not instructions). The gate is deliberately NOT "every close-out must reference the contract" — most close-outs are consumer-aware by their own design and never reference it, so demanding a reference would be the indiscriminate-gate anti-pattern. It guards against *template drift* (a new or edited step that re-introduces a narration instruction), which is the failure that propagates to every project.

What is NOT linted, on purpose: the runtime message (not a file; a Stop-hook "first-person recap" scan would be an indiscriminate detector), and "did the agent obey the shape this turn" (probabilistic — §4 is its lever).

---

## 6. How a step references this

Mirror the `delivery-to-main.md` convention. In the close-out step:

- Frontmatter `description:` — "… Implements `shared/close-out-contract.md` for `<workflow>`."
- Body, at the close-out section — one line: "Emit the close-out per `shared/close-out-contract.md` (audience-first; process narration forbidden by default; shape-feedback routes to a workflow patch)."

Do not duplicate the full shape into each step — point to this contract and add only the workflow-specific section names / interpretation block (as `design-handoff` §10 does).
