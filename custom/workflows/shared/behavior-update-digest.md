---
name: behavior-update-digest
contract_version: 1
description: 'The terminal shape for any AUDIT / OBSERVATION / behavioral-review workflow: its close-out must not stop at findings — it emits a structured Behavior Update Digest (doctrine_delta · handoff_delta · story_candidate · owner_gated · completion_disposition) AND auto-executes the safe stages (record doctrine, re-issue the brief on the allowed path, draft the story), handing back only owner-gated steps. The audit-lane SPECIALIZATION of STD-CLOSEOUT-001 (terminal-message shape) that REUSES STD-COMPLETION-001 for the disposition field; it does not redefine either. Closes the observation→(nothing enforced)→text-pool gap. Named callers: design-review, data-quality-audit, scrape-coverage-audit, relational-coherence-audit, trace-flow, investigate, maintenance-triage (classify+route), dispatch-followups (auto-execute). PROBABILISTIC at runtime; template-adoption is the lever.'
---

# Behavior Update Digest — Terminal Contract for Audit / Observation Workflows

**Why this exists.** An audit or behavioral observation that ends at a write-up is unfinished work. The failure mode (owner-named, 2026-06-29, after the Chrome clerk receive/grade audit): `observation → (nothing enforced) → text pool`. Findings get captured into prose and memory but are not reliably turned into doctrine changes, design-handoff updates, or stories/PRs. The behavior is *observed*, *sometimes documented*, but not *registered and digested*. This contract makes closing that loop a **standard shape**, not best-effort.

This is the **audit-lane specialization of `shared/close-out-contract.md` (STD-CLOSEOUT-001)**: the generic standard says a close-out is audience-first and forbids process narration; this one fixes *what the next-actor block must contain* when the workflow's output is an audit/observation result. It does **not** restate STD-CLOSEOUT-001 (audience-first, narration-forbidden, shape-feedback-routes-to-a-patch all still apply) and it **reuses** `shared/completion-contract.md` (STD-COMPLETION-001) for the disposition field rather than redefining it.

---

## 1. Scope

Applies to any workflow whose deliverable is an **audit, observation, review, or behavioral finding** — `design-review`, the `verify/*` audits (`data-quality-audit`, `scrape-coverage-audit`, `relational-coherence-audit`, `trace-flow`), `investigate`, and `maintenance-triage` when it ingests a raw observation. Also applies to **any session turn** that produces such a result outside a named workflow (the upstream doctrine is the `behavior-update-digest` global memory).

Does NOT apply to: a build/deliver workflow (its terminal contract is STD-DELIVERY-001 + STD-COMPLETION-001), a pure mechanical sub-step, or a turn the user explicitly scoped to "findings only, don't act."

---

## 2. The Digest — the required next-actor block

When an audit/observation result is produced, the close-out's next-actor element (STD-CLOSEOUT-001 element 5) MUST be a **Behavior Update Digest** with these five fields. Omit a field's heading only if genuinely empty — never pad, never silently drop.

- **`doctrine_delta`** — what behavior RULE changed (global vs project-local), recorded per `memory-library-discipline` / the right policy file. REUSE the nearest existing memory/policy rather than spawning a near-duplicate.
- **`handoff_delta`** — which brief/spec must change and how. Routed through `design-router` → `design-artifact-loop` / `design-handoff` on the ALLOWED path (`shared/` brief-revision-policy — re-issue, never hand-edit a superseded brief).
- **`story_candidate`** — the next buildable, scoped unit with acceptance criteria DERIVED from the audit (`create-story` / `quick-spec`, or `correct-course` if mid-sprint).
- **`owner_gated`** — anything needing explicit approval (prod-data mutation, destructive migration, cross-repo fork doctrine, scope/plan change). NAME each, with why it is gated.
- **`completion_disposition`** — per STD-COMPLETION-001: declare what was ACTUALLY done this turn (doctrine only? + story drafted? PR opened?) vs what remains. For an audit flow this is the `advisory` disposition specialized to enumerate the four deltas' real state, so the digest cannot masquerade as complete. Diagnosis with no disposition is the invalid commentator exit.

## 3. Auto-execute the safe stages — don't just list them

The digest is not a menu. Within guardrails (the `do-all-batch-autonomy` / `finisher-drive-to-completion` posture), the terminal step **executes the safe stages immediately** and reports them as done:

- **Record** the `doctrine_delta` (memory/policy write) — safe, do it.
- **Draft** the `story_candidate` as an open story/quick-spec — safe, do it (leaves it for owner review; does not start the build).
- **Re-issue** the `handoff_delta` brief on the allowed path when the surface intent changed — safe to draft/re-issue; the build is separate.
- Then route the remainder: `maintenance-triage` classifies anything unrouted; `dispatch-followups` auto-runs the critical follow-ups and presents the optional ones.

Hand back ONLY the genuinely `owner_gated` items. A digest that records doctrine but leaves an obvious, safe story un-drafted is the under-execution failure this contract closes.

---

## 4. Enforcement honesty

Runtime conformance — does the agent actually emit + execute the digest this turn — is **PROBABILISTIC**, exactly as STD-CLOSEOUT-001/STD-COMPLETION-001 are: no file gate can read a conversational close-out, and there is no harness "an audit finished" event to hang a deterministic hook on. The durable levers are (a) the **named-caller references** in each audit workflow's terminal step (so the contract fires in-flow, where the agent is already executing that workflow — the strongest available anchor), and (b) STD-CLOSEOUT-001 §4: when the shape drifts, the feedback patches the template, so the corpus converges rather than re-litigating per session.

The **deterministic template lever** is deferred under the fork's own warn-then-gate discipline: a future `check:digest` validator (sibling of `validate:close-out` / `check:completion`) can fail the commit when an audit-lane workflow file carries audit/finding signals but does not adopt STD-DIGEST-001 — armed only after the contract's adoption across the audit lane is proven quiet. Until then this is named callers + probabilistic awareness; say so in the `completion_disposition`.

---

## 5. How a step references this

Mirror the STD-CLOSEOUT-001 / STD-ESCALATE-001 convention. In the audit workflow's terminal (audit/route/classify) step:

- Frontmatter `description:` — "… Emits the Behavior Update Digest per `shared/behavior-update-digest.md` (STD-DIGEST-001)."
- Body, at the close-out section — one line: "This is an audit-lane terminal step: emit the Behavior Update Digest and auto-execute the safe stages per `shared/behavior-update-digest.md` (STD-DIGEST-001) — findings alone are an invalid exit."

Do not duplicate the five-field shape into each step — point to this contract and add only the workflow-specific routing (which downstream skill each delta lands in).
