---
name: prod-readiness-charter
description: 'Lifecycle contract of record for getting a BMAD-managed project READY to deploy — the layer above deployment-to-prod. Codifies the three states a project can be caught in (greenfield crossing to prod with no contract; live brownfield that never had one; a contract that has drifted from the fork canonical), the conservative signals that detect each, the artifacts that satisfy each, and the three-tier enforcement (SessionStart awareness, PreToolUse gate, CLAUDE.md reactive guardrail) that makes a context-free fresh agent act. deployment-to-prod / delivery-to-main own the choreography ONCE a contract exists; this charter owns the moment it should come into existence, be detected as missing, or be reconciled. The same shape is declared for memory discipline.'
---

# Production Readiness Charter

**Why this exists.** `deployment-to-prod.md` is precise about *how* a project deploys — admin-merge rules, dirty-tree filters, exit codes — but its §1 Scope only engages "any project that **has** a populated `deploy:` block." That leaves a silent hole on the other side of the boundary: nothing ensures the contract gets **authored** when a project first goes to production, nothing **detects** a project that's been live for months without one, and nothing **reconciles** a contract that has quietly drifted from the fork standard. The same hole exists for memory discipline. A context-free fresh agent — the normal case, since most sessions start cold — will not notice any of this on its own, because the absence of a thing is invisible unless something points at the hole. This charter points at the hole, declaratively, so the same standard is held everywhere.

This charter is the **lifecycle sibling** of `deployment-to-prod.md` (deploy choreography) and `delivery-to-main.md` (artifact/code delivery): those two own the project *once it is set up*; this one owns the transitions *into* being set up, the detection of *not* being set up, and the reconciliation of being set up *wrong*. All three live in top-level `workflows/shared/` because readiness, deploy, and delivery are universal in scope.

**Status — phased.** Per the fork's shipped-vs-designed discipline (`lifecycle-phases.md`), only **Phase 0 (this charter)** is shipped. The detection probes, the `maintenance-triage` setup lane, and the enforcement hooks are **designed, not yet built** — see § Rollout. Do not assume an enforcement mechanism exists because this document describes it; verify against STATUS.md.

---

## 1. The model — what "production-ready" means

A project is **production-ready** when, by the time real users depend on it, it has BOTH:

- **A deploy contract of record** — either an active `deployment-to-prod` contract (`_bmad/bmm/config.yaml` → `deploy:` block + `scripts/bmad-deploy.sh`), OR a deliberate `deploy.bmad_contract: skip` whose choreography is written down in the project's own CLAUDE.md (skip *defers to* the CLAUDE.md per `deployment-to-prod.md §4` — it does not mean "no rules").
- **Memory discipline** — a `memory/` library + `MEMORY.md` index governed by a project memory policy that conforms to the global `memory-library-discipline`. (Declared here; see § Memory parallel for shipped status.)

"Ready" is not "deployed." A project can be ready and undeployed. The charter governs whether the *standard exists*, never whether a given deploy should run — that distinction is load-bearing (see § Enforcement, caution 1).

---

## 2. The three lifecycle states

Each state names a trigger signal, the artifact that satisfies it, and the action. The **deploy** column is fully specified; the **memory** parallel is in § Memory parallel.

| State | Trigger signal (conservative) | Satisfied by | Action |
|---|---|---|---|
| **1. Crossing to prod** | `project_phase: greenfield` in config **and** a prod signal appears (a `deploy:` block being added, a platform link, a production URL/env, a first deploy command) — OR the `project_phase` flag itself flips `greenfield → brownfield \| mixed` | An authored deploy contract (active or deliberate-skip-with-CLAUDE.md) **before** the first production deploy | Recommend/require authoring the contract first; do not let the first deploy be the moment the standard is invented |
| **2. Live, never set up** | `project_phase ∈ {brownfield, mixed}` (or a live signal: deploy script / platform config / CI deploy job / production URL) **and** no `deploy:` block **and** no project deploy doc **and** no `scripts/bmad-deploy.sh` | Standing up the contract (or a deliberate skip + CLAUDE.md deploy section) | Detect and prioritize setup — this is rot that compounds (the project ships by tribal memory, and the lesson one session learns never reaches the next) |
| **3. Set up, but drifted** | A contract/config exists but its `contract_version` is behind the fork canonical, OR the project's CLAUDE.md deploy section contradicts the synced contract (e.g. a stale manual-deploy instruction) | Reconciling the project to the current canonical and re-stamping the version | Detect drift and reconcile + re-enforce |

State 3's version-stamp comparison requires `deployment-to-prod.md` to carry a `contract_version` and each project's config to record the version it conforms to. The CLAUDE.md-contradiction variant (semantic, harder) is a Phase-1+ enhancement; the version stamp is the MVP signal.

---

## 3. Conservative detection — what is NOT a gap

Detection fires in every session across all 13 projects, so a false positive is high-friction and erodes trust in the mechanism. Match the fork's conservative-reaper posture: **when uncertain, do not flag.** Specifically, the following are deliberate choices, not gaps:

- **`deploy.bmad_contract: skip` is set.** That is a project owner's decision (auto-deploy-on-push platforms, multi-step deploys). It is NOT a missing contract. The ONLY residual requirement under skip is that the project's CLAUDE.md actually carries a deploy section (skip defers to it) — flag a skip with no CLAUDE.md deploy section, nothing else.
- **A genuinely greenfield, never-deployed project.** No prod signal, no users → State 1 has not triggered. Pre-launch projects are not "missing" a contract; they have not crossed yet.
- **A project whose `contract_version` matches the canonical.** Not drift.

Bias the probes toward silence. A missed flag is recoverable next session; a wrong flag that blocks a legitimate deploy teaches the team to distrust the gate.

---

## 4. The memory parallel (declared; shipped status per STATUS.md)

The same three states apply to memory discipline, measured against the global `memory-library-discipline` and the project memory policy:

1. **Crossing to prod** — once durable domain facts exist (a live project accumulates business context not derivable from code), require a `memory/` library + `MEMORY.md` + a project memory policy.
2. **Live, never set up** — a brownfield/live project with no `memory/` dir and no memory policy section in CLAUDE.md → detect and stand it up.
3. **Drifted** — the project's memory policy diverges from the global `memory-library-discipline` → reconcile.

Deploy is the fully-specified domain in this charter's first cut; memory is declared so the structure is coherent, and is built only after the deploy detection has proven accurate (§ Rollout). The two domains share one charter because they share one failure shape: a standard that should exist by prod, invisible to a cold agent until something points at its absence.

---

## 5. Enforcement — three tiers that survive a context-free agent

Prose does not enforce; hooks do. A fresh session will not read a guide it is merely *told* to read. The fork has already proven the pattern (SessionStart drift reminders; the PreToolUse worktree edit-guard that hard-blocks). Readiness uses the same three tiers, in the global `always-on-vs-pointer-rules` spirit (non-negotiable gates inline + hook-enforced, never hidden behind a pointer):

> **Before authoring any tier below — the Phase-1 probe or the Phase-3 gate — invoke the `enforcement-expert` skill.** It owns the deterministic-vs-probabilistic strategy choice (which primitive, at which dangerous moment, awareness vs gate vs proof, the logged override, the false-positive cost, and the separate hook-distribution track). This charter defers to it rather than re-deriving enforcement design inline; the design here is the *what*, the skill is the *how*.

1. **SessionStart probe — awareness.** Injects the readiness finding into *every* session's context, alongside the existing fork-drift / PROJECT HEALTH / HANDOFF BACKLOG lines. This is the only tier a context-free agent cannot miss. Warn-only.
2. **PreToolUse gate — action.** Hard-block the first production deploy (`railway up` / `bmad-deploy.sh` / push-to-default-branch) when State 1 or 2 holds, until a contract exists — same shape as the existing Edit/Write worktree guard. Must carry a clean, logged override.
3. **CLAUDE.md — reactive guardrail, not a pointer.** A one-line inline gate ("before any production deploy, confirm a deploy contract of record exists; if not, STOP and run the setup lane"), with the hook as the real enforcer. "Actually read the guide" is enforceable ONLY as a hook precondition (deploy blocked until contract/ack marker present) — never as prose alone.

**Caution 1 — do not recreate the friction `deployment-to-prod.md §4` removed.** State 1's "a contract must exist before first prod deploy" gates on the *contract existing*, NOT on asking permission each deploy. The §4 skip posture deliberately killed the per-session "Want me to deploy?" question. Keep "the standard must exist" and "should this deploy run" strictly separate.

**Caution 2 — the hook is a separate distribution track.** The charter and the setup lane distribute via `sync-bmad-workflows.sh`. Hooks live in `.claude/settings`, which sync does NOT carry — the SessionStart probe and PreToolUse gate need their own distribution path (`onboard-project.sh` or a dedicated hooks-sync). Authoring the charter does not deploy the enforcement.

---

## 6. Rollout — phased, each step independently revertible

- **Phase 0 — this charter.** Policy only, zero blast radius. *(shipped — this document)*
- **Phase 1 — detection, warn-only.** SessionStart probes (prod-readiness; later memory) emit reminders, block nothing. Observe the false-positive rate across the 13 before any gate. Requires `contract_version` on `deployment-to-prod.md` for State 3. *(designed)*
- **Phase 2 — action lane.** A `maintenance-triage` lane (not a new top-level workflow) that authors the contract/config or reconciles drift per this charter. *(designed)*
- **Phase 3 — hard gate.** PreToolUse deploy block + the CLAUDE.md reactive guardrail + the hook-distribution track — gated on Phase 1 proving detection is quiet and accurate. *(designed)*

Memory rides the same four phases, started only after the deploy path is validated once.

---

## 7. Where this lives in each project

After `sync-bmad-workflows.sh` runs:

- `_bmad/bmm/workflows/shared/prod-readiness-charter.md` — this document (read-only mirror; agent reads, does not edit).
- The detection probes live in the global/project hook config (separate track — § Enforcement caution 2), NOT in the synced workflow tree.
- Per-project state (which state a project is in, the conformed `contract_version`) is read live from `_bmad/bmm/config.yaml` + the working tree, never cached in this document.

Project CLAUDE.md, once Phase 3 ships, carries the one-line reactive guardrail above its Deployment pointer block.

---

## 8. Charter evolution

Changes propagate to every targeted project on the next `sync-bmad-workflows.sh` run. Because the enforcement tiers (hooks) distribute on a separate track, a change to the *policy* here is inert until the matching probe/gate is distributed — note in the STATUS.md changelog whether a charter change is policy-only or requires a hook redistribution. Breaking changes to the detection contract (renaming a signal, changing what counts as "ready") require a migration note appended here and a one-line entry in each project's CLAUDE.md memory changelog at sync time.
