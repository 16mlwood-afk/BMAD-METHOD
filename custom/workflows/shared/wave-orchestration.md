---
name: wave-orchestration
description: 'Shared protocol for running an implementation/review/creation workflow as WAVES of fanned-out subagents instead of one linear pass. Decompose the job into independent units (stories / diffs / review-dimensions), batch them into waves (default: by epic, concurrency cap 6), fan out one subagent per unit returning a STRUCTURED result (never a shared-file edit), then aggregate-and-act and GATE the next wave on the prior wave''s results. Composes with parallel-sessions.md: every implement-wave subagent enters its own worktree (§A1) and atomically claims its story (§C) — so an orchestrated wave and free-roaming solo parallel devs use the SAME primitives and coexist without colliding. Invariant W0: wave mode is ADDITIVE and never removes a dev''s ability to parallel-develop independently in a worktree. Referenced by code-review (wave review — default-on for >1 unit), create-epics-and-stories (wave create — default-on for >1 story, + dedup pass), dev-story (wave implement — OPT-IN flag only, §C-claimed).'
---

# Wave Orchestration — Fan-Out-in-Batches Protocol

**Why this exists.** The fork's implement/review/create workflows run one unit at a time: review one story, write one story, build one story, then the next. When the backlog is wide — 28 merged stories awaiting review, 6 ready-for-dev stories, a whole epic to draft — a linear pass is slow and loses the leverage of independent work that has no ordering dependency. The *wave method* is the missing pattern: split the job into independent units, run a bounded batch of them concurrently as subagents, collect structured results, act on them as a batch, then let the next batch start with the prior batch's learnings already in hand.

Observed to work well (cash-recovery, 2026-06): a code-review pass over Epic-1's merged stories fanned out one reviewer per story, each returning a `PASS/CHANGES/BLOCKER` verdict + per-AC check + findings; the orchestrator promoted the clean ones and queued the rest — four stories reviewed in the wall-clock of one, with no story's reviewer racing another. This protocol generalizes that.

It composes with — does not duplicate — `parallel-sessions.md` (§A worktree, §B artifact races, §C story claim) and `worktree-portability.md` (path mechanics). Wave orchestration is *how a single workflow run fans itself out*; parallel-sessions is *how concurrent sessions avoid colliding*. An implement-wave needs both: the wave decides the batch, §A/§C keep each fanned-out unit isolated and claimed.

---

## §W0 — Invariant: wave mode is ADDITIVE, never a replacement

**This is a hard requirement, not a nicety.** Turning a workflow into wave mode must NEVER remove a developer's ability to parallel-develop independently:

- **Solo / independent parallel dev is always available and unchanged.** Any dev or session can still pick one story, enter its own worktree (parallel-sessions §A1), atomically claim it (§C2), implement, and deliver — exactly as today. Wave mode does not gate, funnel, or serialize that path through a coordinator.
- **A wave and free-roaming devs coexist.** Because every implement-wave subagent uses the SAME primitives a solo dev uses — its own worktree (§A1) and its own §C claim token in `sprint-status.yaml` — the coordination layer cannot tell a wave-spawned implementer from a hand-driven one. A human can be mid-story in their own worktree while a wave runs other stories; §C claiming keeps them off each other's story, and §A worktrees keep their edits isolated.
- **Wave mode is opt-in where it carries collision risk.** For `dev-story` (parallel *implementation*), wave mode is an explicit flag — never the silent default. The default `dev-story` run is still one story, one worktree. For read-only or artifact passes (`code-review`, `create-epics-and-stories`) wave mode may default on when there is more than one unit, because those do not race code.

If a wave mode cannot honor W0, do not ship it — fall back to the linear path.

---

## When it applies

- **Wave review** — `code-review` invoked over MORE THAN ONE story/diff (e.g. "review all stories in `review`"). Default-on at >1 unit; a single-target review stays linear.
- **Wave create** — `create-epics-and-stories` (or any story-drafting workflow) drafting MORE THAN ONE story in a run. Default-on at >1 unit, with the mandatory dedup/consistency pass (§W5) — because creation is normally sequential to absorb prior-story learnings, the wave variant must reconcile cross-story overlap before finalizing.
- **Wave implement** — `dev-story` ONLY when the user passes the explicit wave flag (e.g. `wave` / `--parallel`) AND more than one `ready-for-dev` story exists. OPT-IN by W0. Each unit is §C-claimed and built in its own §A worktree.
- A run with one unit, or any workflow not in this list, ignores wave orchestration and runs linearly. **The protocol is safe to skip when the job is a single unit** — a wave of one is just the linear path with overhead.

---

## §W1 — Decompose into independent units

Split the job into units that have NO ordering dependency on each other within a wave:

- **review** → one unit per story (or per file/diff, or per review-dimension when one story is large).
- **create** → one unit per planned story (the epics file's next-needed stories).
- **implement** → one unit per `ready-for-dev` story.

A unit must be self-contained: a subagent given the unit's spec (a story file, a diff, an epic slice) can complete it without waiting on a sibling unit's output. If two candidate units DO depend on each other (story B's spec needs story A merged first), they belong in **different waves**, in dependency order — not the same wave.

---

## §W2 — Batch into waves (grouping + concurrency cap)

- **Default grouping: by epic.** One wave per epic keeps each batch coherent, makes the aggregated report digestible, and lets an epic's learnings inform the next. When there is no epic structure, fall back to **fixed batches** of the concurrency cap.
- **Concurrency cap: default 6 concurrent subagents.** Heavy subagents (each may read broadly, reason, and — for implement — build) contend for CPU and shared infra; more than ~6 at once degrades rather than speeds. If a wave holds more units than the cap, run it as sub-batches of ≤ cap and aggregate across them.
- **Order waves by dependency and by leverage.** Foundation first (defects there ripple), then dependents. In review, Epic 1 (schema/ingestion substrate) before the epics built on it.
- **Announce the wave plan up front** so the user sees the batching and can redirect before tokens are spent: which units, grouped how, in what order.

---

## §W3 — Structured-result contract (subagents return, they do not write shared state)

Each fanned-out subagent **returns a structured result as its final message** and does **NOT** edit shared coordination files (`sprint-status.yaml`, sibling story files, the epics file). This is the load-bearing rule — it is what keeps a wave race-free against itself and against concurrent sessions:

- **review unit** → `VERDICT: PASS | CHANGES | BLOCKER`, a per-AC check (AC# → met/unmet/partial), and findings (`[severity] file:line — problem — suggested fix`). Read-only on the repo.
- **create unit** → the drafted story content (returned, or written to its OWN per-item `<id>.md` file, never appended to a shared doc), plus any cross-story assumptions it made (so §W5 can reconcile them).
- **implement unit** → the §C claim it took, the branch/PR it produced, its gate result, and a completion summary. It DOES write its own story's code (in its own §A worktree) and its own story file's Dev Agent Record — but never a sibling's story file or the shared board beyond its own §C/§B1 per-key edit.

The orchestrator — the single coordinating run — is the ONLY writer of shared aggregate state (promoting statuses, queuing follow-ups, merging). One writer, many readers: no aggregate-state races.

---

## §W4 — Aggregate, act, and GATE the next wave

After a wave's subagents return:

1. **Aggregate** the structured results into one batch summary (e.g. a verdict table, a findings list, a per-story claim/PR list).
2. **Act on the batch** (orchestrator-owned writes, via parallel-sessions §B1 per-key edits where they touch `sprint-status.yaml`):
   - review → promote `PASS` units (`review` → `done`), queue `CHANGES`/`BLOCKER` findings as concrete review-follow-up tasks (or fix the cheap ones inline).
   - create → after §W5 dedup, finalize the drafted stories and mark them `ready-for-dev`.
   - implement → merge/PR each completed unit per parallel-sessions §A5 / `delivery-to-main.md`, release its §C claim (set `review`), record results.
3. **GATE the next wave on this one.** Do not fire all waves at once. Start wave N+1 only after wave N is aggregated and acted on, so (a) learnings and merges propagate (a fix found in Epic 1 informs the Epic 2 wave; an Epic-1 merge is in `main` before Epic 2 integrates), and (b) the user gets a digestible batch report between waves and can redirect. Report each wave's outcome before launching the next.

---

## §W5 — Composition rules

### With parallel-sessions §C (implement waves)
Every implement-wave subagent runs §C **CLAIM** before any work: re-read `sprint-status.yaml` fresh, claim its target story with a §C1 token, refuse-and-skip any story a live session already holds (§C2/§C4). The orchestrator must hand each subagent a DISTINCT `ready-for-dev` story; the per-subagent §C claim is the backstop that makes a handoff race or an overlap with a free-roaming solo dev safe. Each subagent enters its own §A1 worktree (from local `main`), and its §C `session=` signature reuses that worktree's branch slug — one identity, no double-warn (§C2.3).

### With parallel-sessions §A (worktree isolation)
Implement-wave subagents edit code, so each gets its own worktree (`isolation: worktree` when spawned via the Agent tool, or §A1 manually). Review-wave and create-wave subagents are read-only on `src/` (review) or write only their own `_bmad-output/` artifact (create), so they need no worktree (parallel-sessions §B). This preserves W0: the wave reuses the exact isolation a solo dev uses.

### With create-story's sequential learning (create waves)
Linear `create-epics-and-stories` drafts stories in order so each absorbs the prior's decisions. A create wave loses that, so it MUST run a **dedup/consistency aggregation pass** after the wave returns: detect cross-story overlap (two stories claiming the same component), contradictions (incompatible assumptions about a shared seam), and gaps (a dependency neither story owns), and reconcile them into the finalized set before any story is marked `ready-for-dev`. Without this pass, do not run create in wave mode — fall back to linear.

---

## Costs

- N subagents per wave instead of one linear pass — more tokens up front, far less wall-clock, and (for review) genuinely independent verdicts. Scale the wave to the ask: a quick check is a small wave or none; "review everything" / "be thorough" earns a full fan-out.
- The concurrency cap and the gate-between-waves cost some parallelism on purpose — they buy digestible batches, propagated learnings, and contention safety. Do not remove them to "go faster"; an ungated all-at-once fan-out floods shared infra and returns one indigestible report.
- The structured-result contract (subagents return, don't write shared state) costs an aggregation step in the orchestrator. It buys race-freedom: it is the same single-writer discipline that lets a wave run alongside the live fleet without a board-war.
