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
4. **Status** — delivery / verification state (PR merged, tests green, deploy pending), stated faithfully — a skipped or failed step is named, not softened.
5. **Next-actor instructions** — what the consumer does next. When the next actor is an external design consumer, include the short interpretation block: which artifact is active, revision vs new, how to read composition / page-mode, what NOT to import from the prior implementation.

`design-handoff`'s `step-04-deliver.md` §10 is the canonical design-lane instantiation of this shape; other deliver steps mirror it in their own domain terms.

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

This is a **PROBABILISTIC** standard — it shapes model output; there is no deterministic harness gate that can enforce "wrote it for the consumer, not as a recap." The durable lever is §4: when the shape drifts, the feedback patches the template, so the corpus converges over time rather than re-litigating per session. A deterministic close-out linter (e.g. a heuristic flag on first-person process-recap phrasing in a terminal step's emitted block) is a possible future tier; not built.

---

## 6. How a step references this

Mirror the `delivery-to-main.md` convention. In the close-out step:

- Frontmatter `description:` — "… Implements `shared/close-out-contract.md` for `<workflow>`."
- Body, at the close-out section — one line: "Emit the close-out per `shared/close-out-contract.md` (audience-first; process narration forbidden by default; shape-feedback routes to a workflow patch)."

Do not duplicate the full shape into each step — point to this contract and add only the workflow-specific section names / interpretation block (as `design-handoff` §10 does).
