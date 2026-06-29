---
name: completion-contract
contract_version: 1
description: 'Shared policy for the DISPOSITION a completion-oriented workflow must declare at its terminal step — the "finisher, not commentator" contract. A completion workflow (one whose job is to carry scoped work to a deliverable) MUST end by emitting a completion_disposition: it either delivered (pr_open / pr_merged), or it names what it could not safely do (owner_gated_residue, with the named blockers), or — for an explicitly advisory-only flow — it declares advisory with a one-line why. Stopping at commentary ("here is what is wrong / what is missing") with no disposition is an INVALID exit. Third sibling of the close-out family: delivery-to-main.md (STD-DELIVERY-001) owns the MECHANICS of reaching main; close-out-contract.md (STD-CLOSEOUT-001) owns the SHAPE of the terminal message; this owns WHETHER the work was driven to done and what remains. Does NOT duplicate the upstream behavioural doctrine (the global finisher-drive-to-completion / answer-shape-and-autonomy / lead-dont-ask rules) — it makes that doctrine declarable and checkable at a workflow boundary. Referenced by the terminal deliver/handoff step of completion workflows: quick-dev, dev-story, design-handoff, design-implement, and peers.'
---

# Completion Contract — Finisher Disposition

**Why this exists.** A completion-oriented workflow exists to *move work to a deliverable* — a merged PR, or, when something genuinely blocks that, a clearly-named residue for the owner. The failure this contract closes is the **commentator exit**: a workflow that diagnoses the problem, explains what is missing, and then *stops* — handing back analysis where a finisher would have either delivered or named exactly what it could not safely do. Commentary-instead-of-completion is invisible at the close-out: a well-written "here is what is wrong" reads as a finished turn while leaving the safe work undone.

This contract makes "did we finish, and if not, what remains?" a **declared, structured field** at the terminal step, so the absence of completion is no longer silent. It does not try to legislate the judgment of *what* counts as done — it forces the workflow to *state its disposition* in a fixed vocabulary, which is the part a fresh, context-free agent reliably skips.

**Relationship to the existing doctrine (reference, do not duplicate).** The *behaviour* — drive the shortest dependency chain, act on all safe/reversible steps before returning, reserve questions for genuine owner-gated forks — is already owned upstream by the global `finisher-drive-to-completion`, `answer-shape-and-autonomy`, and `lead-dont-ask` doctrine. This contract is the **workflow-boundary instantiation** of that doctrine: the single place a completion workflow declares the *outcome* of having (or not having) applied it. When the doctrine and this contract appear to disagree, the doctrine is the source of truth; this contract is its checkable shadow.

**Relationship to its siblings.**
- `delivery-to-main.md` (STD-DELIVERY-001) — the MECHANICS: commit → push → PR → merge an artifact onto the default branch.
- `close-out-contract.md` (STD-CLOSEOUT-001) — the MESSAGE SHAPE: the terminal message is audience-first for the next actor, never a process recap.
- **this (STD-COMPLETION-001)** — the DISPOSITION: whether the work was driven to done, and what (if anything) remains.

A terminal deliver/close-out step typically implements all three: it delivers (DELIVERY), it speaks audience-first (CLOSEOUT), and it declares its disposition (COMPLETION).

---

## 1. Scope

Applies to any **completion-oriented workflow** — one whose job is to carry a scoped unit of work to a deliverable. The canonical fork instances: `quick-dev`, `dev-story`, `design-handoff`, `design-implement`, and peers whose terminal step delivers code or a consumable artifact.

Such a workflow's terminal step MUST emit a `completion_disposition` (§2) before it is considered complete.

Does NOT apply to:
- **Advisory-only workflows** — audits, reviews, triage, routers, and research flows whose contract is *to report*, not to deliver (`design-review`, `data-quality-audit`, `relational-coherence-audit`, `maintenance-triage`, the `*-audit` family, `investigate`, `trace-flow`). These declare `advisory` once, in their own terminal step, as a standing property — see §4. Their "no PR" is correct by design, not a missed completion.
- Mid-workflow progress notes or step-boundary handoffs.
- A pure artifact-write step with no terminal message (its delivery is governed by STD-DELIVERY-001; its disposition rides whatever step emits the close-out).

---

## 2. The `completion_disposition` block

At the terminal step, after the audience-first close-out (STD-CLOSEOUT-001 §2 — this disposition IS the structured form of that contract's "Status" element), emit a `completion_disposition`. Exactly ONE value, from this enum:

| Value | Meaning | Required companion |
|---|---|---|
| `pr_merged` | The scoped work reached `origin/<default-branch>` via a merged PR. | the PR number / URL |
| `pr_open` | The work is on a pushed branch with an open PR, not yet merged (merge blocked, or awaiting review the workflow cannot self-approve). | the PR number / URL **and** the one-line reason it is not merged |
| `owner_gated_residue` | Safe/reversible work was delivered (or there was none to deliver), and what remains is genuinely owner-gated — a credential to provision, a production-data mutation, a destructive migration, a cross-repo fan-out, a scope decision. | a **named** list of each residual item + *why it is owner-gated* (not "more work remains" — the specific blocker, e.g. "needs `EBAY_*` credentials provisioned") |
| `advisory` | This workflow's contract is to report, not deliver (§1 advisory-only set), OR the owner explicitly scoped this run to analysis-only. | a one-line *why advisory* (e.g. "audit lane — detection only", or "owner requested diagnosis only") |

**The disposition is not the message — it is a declared field beneath it.** The close-out prose stays audience-first per STD-CLOSEOUT-001; the disposition is a short, fixed-vocabulary line (or frontmatter field on a written handoff artifact) the next actor and any checker can read without parsing prose.

A run may legitimately split: deliver the safe slice (`pr_merged`) **and** carry residue. In that case emit the most-delivered value that is true *plus* the residue — e.g. `pr_merged` with an explicit "Owner-gated residue:" list. The point is that the residue is **named**, never dropped silently.

---

## 3. The invalid exit — commentary with no disposition

A completion workflow that ends with *only* an explanation of what is wrong / missing / blocked — and no `completion_disposition` — has **not completed its contract**. "I'll explain the problem and stop" is the commentator failure this standard exists to kill.

The rule for a context-free agent at a completion workflow's terminal step:

> Before you finish, you MUST emit a `completion_disposition`. If you delivered, say `pr_merged` / `pr_open` with the PR. If you couldn't safely deliver, say `owner_gated_residue` and **name each blocker and why it is owner-gated**. The only way to finish without a PR or a named residue is `advisory` — and only if this workflow is advisory-only or the owner scoped the run to analysis. Diagnosis without one of these dispositions is an unfinished turn, not a delivered one.

Naming residue is not the same as doing the owner-gated work — the contract never pushes an agent past a genuine gate (a credential, a prod mutation, a destructive migration). It forbids *stopping short of the gate while pretending the turn is done*.

---

## 4. `advisory` — the logged escape, never silent

`advisory` is the sanctioned opt-out, and it is **never silent**: it always carries its one-line *why*. Two paths reach it:

1. **Standing advisory workflows** (§1 set) declare `advisory` as a fixed property of their terminal step — their job is to report. They reference this contract once and state the reason inline ("audit lane — detection and routing only, no deliver").
2. **A run scoped to analysis by the owner** — the owner explicitly asked for diagnosis only on a workflow that would normally deliver. The disposition records that: `advisory` + "owner requested diagnosis only at <when>".

What `advisory` must NOT become is a lazy exit hatch for a delivery workflow that simply didn't finish. A `quick-dev` run that *could* have shipped a safe change but stopped at "here's what I'd do" and stamped `advisory` is abusing the escape — that is `owner_gated_residue` at best (and usually just an unfinished `pr_*`). The *why* line is what makes the difference auditable.

---

## 5. Enforcement honesty

Per the DETERMINISTIC-vs-PROBABILISTIC axis (`enforcement-expert`):

- **Runtime conformance is PROBABILISTIC.** Whether the agent actually drove the work to completion vs. stopped at commentary is a *judgment*, not a file-checkable state — no gate can read "should this have been a PR?". The disposition reframes the enforceable part: not "did you judge completion correctly" (un-gateable) but "did you **declare** a disposition at all" (checkable). The convergence lever for runtime drift is the same as STD-CLOSEOUT-001 §4 — shape/behaviour feedback patches the workflow template in the fork, so the corpus converges rather than re-litigating per session.

- **Template coverage is DETERMINISTICALLY checkable — and is shipping WARN-ONLY first.** `tools/check-completion-disposition.js` (npm `check:completion`) walks `custom/workflows/` and **warns** when a file that adopts the terminal-message shape (references STD-CLOSEOUT-001) does NOT also reference this contract (STD-COMPLETION-001) — i.e. a close-out step that declares its message shape but not its completion disposition. It is **warn-only by default** (exit 0 always, NOT in the pre-commit gate or `npm test`) during the soak phase, so its precision can be observed before it is trusted to block. The flip is **pre-staged**: `check:completion -- --strict` exits 1 on a likely gap (the escape hatch is unchanged — a delivering close-out adopts the contract by reference, including `advisory` for a genuine no-deliver case), so the Phase-2 promotion is the one-line act of adding `check:completion -- --strict` to the `test` script / pre-commit. **Promotion criterion (warn-then-gate):** the static scan being quiet (0 likely gaps) is the *precondition*, NOT the soak — arm the gate only after the default warn output has stayed quiet across an elapsed window of real completion-workflow runs and corpus edits by other sessions, where a heuristic misfire would surface before it can break a legitimate commit. Running `--strict` manually during soak previews exactly what the armed gate would block.

- **The on-disk artifact check is a SEPARATE distribution track.** Verifying that a *written* handoff/disposition artifact (e.g. `quick-dev`'s `handoff-*.md`, which lives under a project's gitignored `_bmad-output/`) actually carries a `completion_disposition` is a *project*-side check (project CI / pre-commit), not a fork-tooling one — the fork linter cannot see project artifacts. That tier ships per-project on the hooks/onboarding track, warn-only first, and is out of scope for this Phase-1 fork wave.

What is NOT checked, on purpose: the runtime message (not a file; a Stop-hook "did it really finish?" scan would be the indiscriminate-detector anti-pattern — completion is not heuristically detectable), and the *correctness* of a declared disposition (whether `advisory` was honest) — §4's *why* line makes that auditable by a human, not by a gate.

---

## 6. How a step references this

Mirror the `close-out-contract.md` / `delivery-to-main.md` convention. In the terminal deliver/close-out step:

- Frontmatter `description:` — add "… Declares `completion_disposition` per `shared/completion-contract.md` (STD-COMPLETION-001)."
- Body, at the close-out section — one line: "Emit a `completion_disposition` per `shared/completion-contract.md` (STD-COMPLETION-001): `pr_merged` / `pr_open` with the PR, `owner_gated_residue` with each blocker named, or `advisory` with a why — diagnosis with no disposition is an invalid exit."
- Do NOT duplicate the enum table into each step — point to this contract and add only the workflow-specific disposition values that apply (e.g. `design-handoff` delivers a brief, so its `pr_*` is the brief PR; `design-implement`'s `checkpointed` run maps to `pr_merged` for the delivered slice + `owner_gated_residue` naming the remaining frames).
