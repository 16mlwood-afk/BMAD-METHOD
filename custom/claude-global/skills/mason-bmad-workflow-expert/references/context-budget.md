# Context Budget & Workflow Decomposition

The durable principle behind reviewing, authoring, and diagnosing workflows for **AI ingestibility**. A workflow that is correct on paper can still ship the wrong thing if it overruns the model's usable context — the failure looks like the model "compressing" the workflow and dropping detail. This reference names that phenomenon precisely, states the fork's budget, and gives the decomposition decision-rule the expert applies.

This is grounded in external research (sources at the bottom), not folklore. Where a number is quoted it traces to a cited study.

---

## 1. The phenomenon, named precisely

"Context fatigue" is not one thing — it is four distinct failure modes that compound. Conflating them leads to the wrong fix, so name the one you mean.

- **Context rot** — a *length* effect. As tokens accumulate, recall and reasoning quality decline **monotonically, well before the window is full**. A "200K" model degrades measurably at 30–50K tokens; you never hit the limit. (Chroma, *Context Rot*, 2025 — 18 frontier models.)
- **Curse of instructions** — a *density* effect, largely independent of token count. As the number of simultaneous constraints rises, the fraction the model honors falls: near-peak at **1–10 instructions**, noticeable decline by 50–100, severe by 200+. (IFScale / ManyIFEval, 2025.) **This is the dominant failure mode for instruction-heavy markdown workflows** — it's not that the model can't *find* a rule, it's that it can't honor all of them at once.
- **Lost in the middle** — a *position* effect on top of both. Instructions at the start/end of a context are followed reliably; those buried mid-document lose 30–50% compliance. (Liu et al., 2023.)
- **Effective vs. advertised window** — models reliably use only **~50–65%** of their labelled window for real work; a "1M" model behaves like ~500–650K. (NVIDIA RULER.) Treat the advertised number as an upper bound you should not approach.

**The compaction trap (the one most specific to long agentic runs).** When a harness auto-summarizes its own running context to keep going, it drops the *highest-value, lowest-redundancy* material first: exact numbers, edge cases, exceptions to rules, the precise wording of constraints. In an instruction-heavy workflow, **the dropped exceptions *are* the spec.** Reversible *compaction* (re-reading a file that still exists) is safe; lossy *summarization* (an LLM rewrite that replaces the original) is not.

**Critical nuance — don't trust green needle-in-a-haystack numbers.** Literal keyword retrieval survives long context fine, which is why vendor NIAH scores look rosy. But workflows do *reasoning over many constraints*, the regime that collapses early: on associative (non-literal) retrieval, half of tested models lose half their accuracy by **32K** (NoLiMa). The pessimistic curves apply to us, not the rosy ones.

---

## 2. Why this is a fork concern, not a generic one

Fork workflows are dense instruction documents executed step-by-step. The two knobs above map directly:

- **Length** → a `workflow.md` that inlines every step body, or a step that pulls in a whole codebase / large artifact, drives context rot.
- **Density** → a single step with 15–20 hard must-dos drives the curse of instructions, regardless of length.

Both produce the same surface symptom the user reported: the model "compresses too much and drops detail." Length and density are *separate* knobs — shortening helps the first, reducing live constraints-per-step helps the second. **Attack the one that's actually overrun, not both reflexively.**

## 3. What the fork already does right (keep doing it)

The fork's house architecture is, by accident or instinct, textbook context engineering. Name this when reviewing so it isn't "improved" away:

- **Orchestrator + `steps/` split** = *progressive disclosure / just-in-time loading*. `workflow.md` names steps and points to per-step files loaded only when that step runs. This is the same three-tier model Anthropic's Agent Skills use (metadata → body → bundled refs). Mutually-exclusive branches in separate files cost zero tokens until used.
- **Handoff artifacts** (design-handoff, screen-review, brief-as-artifact-of-record, the §2f manifest) = *externalized state / structured note-taking*. The next step reads a compact artifact, not the prior step's full reasoning trace. This survives compaction — a 30-step run doesn't lose step 3's decision by step 28.
- **Checklists as compact state** = a short re-readable status list instead of re-derived prose.

The gap the fork has *not* historically exploited: **sub-agent fan-out** — pushing token-heavy reading into an isolated child context that returns only a distilled result, so the orchestrating workflow's own context never absorbs the raw material.

---

## 4. The budget (concrete, checkable)

Soft thresholds, not cliffs — degradation is continuous, so these are "danger zone past here" markers:

- **≤ ~10 hard must-dos per step.** Past 10, instruction-following starts to slip (IFScale). If a step has 15+ distinct must-dos, it is doing more than one job — split it.
- **One step = one job.** A step's instructions should serve a single responsibility. Multiple responsibilities = multiple steps.
- **Load-bearing constraints go at the top of the step file, and are restated next to the action they govern.** Never rely on a constraint stated only in a distant global preamble (lost-in-the-middle). Re-anchoring a critical rule near its point of use has lifted long-context compliance dramatically in the literature.
- **Pointer over inline.** Reference a file/query the agent dereferences on demand; reserve inlining for the few high-signal tokens the step truly needs up front.
- **Treat the usable window as ~50–65% of advertised, and the reliable *reasoning* zone as far smaller — low tens of thousands of tokens.** Never design a step whose correctness depends on the model integrating fine detail scattered across 100K+ tokens; for reasoning tasks that capability is largely fictional.
- **A step that must read many files or a large corpus should delegate to a sub-agent** and consume its ~1–2k-token distilled return, rather than inlining the reads into its own context.

---

## 5. The decomposition decision-rule

When a workflow (or a step) overruns the budget, there are **three** remedies, and picking the wrong one is its own failure. The deciding axis is **read-heavy/parallelizable vs. write-heavy/coherence-critical** — this is the reconciliation of the field's two camps (Anthropic's pro-fan-out multi-agent research system, which beat single-agent by ~90% on a *read-heavy* task; vs. Cognition's *Don't Build Multi-Agents*, which shows fan-out fragments intent on *write-heavy* build tasks). Both camps agree the failure mode is always lost/partitioned context; they disagree only on whether distilled handoffs preserve enough for the task class.

| Step shape | Remedy | Why |
|---|---|---|
| **Read / explore / audit / research** — gathering, searching, multi-file scans, summarizing; output *informs* rather than *mutates* a shared artifact | **Sub-agent fan-out** — spawn isolated workers, each with a fresh clean window, each returning a distilled artifact | Independent, parallelizable, and the heavy token cost stays out of the orchestrator's context. This is the fork's missing lever. |
| **Long sequential build that exceeds one window** | **Per-phase fresh-context steps** with a durable progress/manifest artifact between them — an initializer phase writes scaffolding + state, later phases open fresh and read it (the Anthropic long-harness pattern; Magentic-One's Task/Progress ledgers) | Keeps continuity through an external artifact instead of one ever-growing transcript. **Not** fan-out — the phases are coupled. |
| **Write one coherent artifact** — building/editing a single file, doc, or UI where sub-outputs must cohere | **Keep single-threaded.** Use compaction (re-readable files), not sub-agents | Fan-out here produces conflicting implicit decisions the coordinator must reconcile — Cognition's central failure case. Anthropic agrees coding is a *poor* multi-agent fit. |

**Default posture:** start with the simplest structure that fits the budget; reach for fan-out only when a step is demonstrably read-heavy *and* parallelizable *and* over budget. Multi-agent costs ~3–15× the tokens of a single thread — justified only when the step's value warrants it.

### The non-negotiable handoff contract (any split)

This is the single point of agreement between both camps: **the failure mode is always lost/partitioned context, and the fix is always making the handoff explicit and complete.** Any delegated step — sub-agent or per-phase — must carry:

1. **Objective** — what the worker is to produce.
2. **Output schema** — the exact shape of the artifact it returns (so the consumer reads, never re-derives).
3. **Tools / sources** — what it may use and where to look.
4. **Boundaries** — what is out of scope.

And durable state **must live in a file**, not in chat memory that evaporates at the window boundary. Persist exact figures, exclusion rules, and constraint wording to a re-readable artifact **before** any compaction boundary — assume the harness will summarize mid-run and silently drop precisely those.

---

## 6. How the expert applies this, per mode

- **Mode 1 (Review).** Add a context-budget check to the durable-principle sweep: does any step exceed ~10 hard must-dos or inline content it could point to? Are load-bearing constraints buried mid-document? Does a read-heavy step inline a large corpus instead of delegating? Budget overruns are **Concerns** (likely to degrade), escalating to **Blocking** only when a step is so dense the workflow cannot reliably execute its own contract. Praise existing progressive-disclosure / handoff-artifact structure so it isn't refactored away.
- **Mode 2 (Author).** Apply the decision-rule at design time: classify each step (read-heavy / sequential-build / write-coherent), keep one-job-per-step, place constraints at the top + point of use, and specify the handoff contract for any delegated step. A new workflow should never be born as one mega-step.
- **Mode 3 (Diagnose).** Use the `context-budget-overflow` root-cause class when a workflow shipped wrong/partial output and the chain shows a single overlong or over-dense step (or an auto-summarization boundary) where detail was dropped — not a logic error. The fix is structural (split the step, externalize state, re-anchor constraints), not a wording tweak.
- **Closing-out (Delivery Audit).** A wave that lengthened a step or added must-dos should note the budget impact and whether a split is now warranted.

---

## Sources

- Liu et al., *Lost in the Middle* — https://arxiv.org/abs/2307.03172
- NVIDIA, *RULER* (effective vs. advertised window) — https://github.com/NVIDIA/RULER
- Modarressi et al., *NoLiMa* (reasoning-retrieval collapse by 32K) — https://arxiv.org/html/2502.05167v1
- Chroma, *Context Rot* — https://www.trychroma.com/research/context-rot
- Jaroslawicz et al., *IFScale: How Many Instructions Can LLMs Follow at Once?* — https://arxiv.org/abs/2507.11538
- Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, *How we built our multi-agent research system* — https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, *Effective harnesses for long-running agents* — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, *Equipping agents with Agent Skills* (progressive disclosure) — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Cognition, *Don't Build Multi-Agents* — https://cognition.ai/blog/dont-build-multi-agents
- Microsoft, *Magentic-One* (Task/Progress ledgers) — https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/
