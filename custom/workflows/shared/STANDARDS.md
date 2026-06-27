---
name: STANDARDS
description: 'The canon — the single index of every shared standard a BMAD-managed project follows (deploy, delivery, webhook boundaries, diagnostics, worktree/parallel-session safety, prod-readiness, AND memory discipline). One place to answer "what is the canonical way to do X?". Each standard lives once at its Home, syncs to projects, and is referenced BY PATH — never restated. Machine-parsable: each synced standard has an ID/Version/Breaking/Home/Applies block that the SessionStart drift check (check-standards-drift.sh) scans.'
contract_version: 1
---

# STANDARDS — the canon

The single index of the standards every BMAD-managed project follows. If you're asking *"what is the canonical way to do X?"*, the answer is one of the blocks below — open its **Home** doc.

## How to use this

- **Starting a deploy flow?** Check `STD-DEPLOY-001` (and `STD-PRODREADY-001` if the project isn't deploy-ready yet) before writing anything.
- **Changing how memory is written/read?** See the memory section below (`memory-library-discipline` / `memory-retrieval-policy`).
- **Touching a webhook boundary?** `STD-WEBHOOK-001` is the contract of record.
- **The Home doc is the source of truth.** A project's `CLAUDE.md` only *points at* a standard; a restatement that disagrees is drift — log it in `docs/fork-gaps.md` and fix it. Reference by path, never copy (`cash-recovery` is the reference shape).
- **Drift is checked automatically.** `check-standards-drift.sh` (SessionStart, WARN-only) compares this canonical against the copy synced into the current project. The synced copy IS the project's declaration of "what I last pulled" — no lock file or CLAUDE.md block to maintain.

## The standards (machine-parsable index)

Each block is scanned line-by-line: `ID` → `Version` → `Breaking` → `Home` → `Applies`, each on its own line. Keep it boring — no nesting, no inline prose on those lines. `Breaking` is the latest version's nature (`yes` = a behavioral shift a consumer could violate; `no` = a safe/clarifying edit safe to auto-upgrade).

### deployment lifecycle

deployment-to-prod — the post-merge deploy contract (admin-merge rules, dirty-path filters, dep auto-heal, exit-code grammar).
ID: STD-DEPLOY-001
Version: v1
Breaking: no
Home: shared/deployment-to-prod.md
Applies: all

delivery-to-main — getting an artifact from local disk to origin/<default-branch> so external consumers can read it.
ID: STD-DELIVERY-001
Version: v1
Breaking: no
Home: shared/delivery-to-main.md
Applies: all

prod-readiness-charter — getting a project READY to deploy (the 3 states, detection, enforcement); the layer above the deploy contract.
ID: STD-PRODREADY-001
Version: v1
Breaking: no
Home: shared/prod-readiness-charter.md
Applies: all

### boundaries & contracts

webhook-contract-charter — every webhook boundary (sender-strict/receiver-lenient rollout, breaking-change taxonomy, per-boundary template).
ID: STD-WEBHOOK-001
Version: v1
Breaking: no
Home: shared/webhook-contract-charter.md
Applies: all

### implementation safety

diagnostics-gate — prove-don't-assert verification gate (a new diagnostic means RED until a clean re-run proves green).
ID: STD-DIAG-001
Version: v1
Breaking: no
Home: shared/diagnostics-gate.md
Applies: all

parallel-sessions — concurrent-session protocol (worktree-before-edit, integrate-advancing-main, named collision classes, story claim+reconcile).
ID: STD-PARALLEL-001
Version: v1
Breaking: no
Home: shared/parallel-sessions.md
Applies: all

worktree-portability — artifact paths resolve to the worktree root, not the main checkout.
ID: STD-WORKTREE-001
Version: v1
Breaking: no
Home: shared/worktree-portability.md
Applies: all

wave-orchestration — fan-out-in-waves protocol for implement/review/create workflows (additive to solo parallel dev).
ID: STD-WAVE-001
Version: v1
Breaking: no
Home: shared/wave-orchestration.md
Applies: all

detect-stack — shared utility: identify the project tech stack.
ID: STD-STACK-001
Version: v1
Breaking: no
Home: shared/detect-stack.md
Applies: all

hook-activation — git-hook gates must be DISTRIBUTED and ACTIVATED by the fork: sync-bmad-workflows.sh + onboard-project.sh set core.hooksPath=.githooks (tracked dispatchers reading .githooks/gates.conf) idempotently, so a synced gate is reliably wired, not silently off. A SessionStart liveness probe warns on un-activated/conflicted repos. Local hook = best-effort gate (bypassable via --no-verify); the fail-closed CI tier is deferred. husky retired in favor of .githooks (worktree-safe).
ID: STD-HOOKACTIVATE-001
Version: v1
Breaking: no
Home: shared/hook-activation-standard.md
Applies: all

### workflow behavior & routing

escalation-on-class-change — when work changes class mid-flow (scope outgrew the unit / missing keystone / planning-not-execution / wrong lane), state it, name the BMAD-default gateway, propose it, and proceed unless vetoed — never a numbered menu, never silent wrong-lane continuation. Implemented by dev-story; conformed-to by correct-course / design-router / maintenance-triage / design-elevation / quick-dev.
ID: STD-ESCALATE-001
Version: v1
Breaking: no
Home: shared/escalation-on-class-change.md
Applies: all

workflow-personas — a thin PRESENTATION layer giving three human-facing families a named voice (Rhea/design-handoff, Sol/quick-spec+quick-dev, Mara/escalation-on-class-change). Voice appears in three sanctioned spots only — opening re-orientation, risk acknowledgement, "I" for responsibility — and never drives decisions, narration, menus, or output structure. Subordinate to STD-ESCALATE-001 and answer-shape-and-autonomy. Not an agent.
ID: STD-PERSONA-001
Version: v1
Breaking: no
Home: shared/workflow-personas.md
Applies: all

### documentation & doctrine

claude-md-standard — CLAUDE.md structure & discipline: global doctrine (machine-local) vs a thin, pointer-based project CLAUDE.md; canonical section shape; pointer-not-restate; edit discipline.
ID: STD-CLAUDE-001
Version: v1
Breaking: no
Home: shared/claude-md-standard.md
Applies: all

## Related registries (not versioned standards)

- **Hooks & gates** → `docs/hooks-registry.md` (fork-local): every Claude Code hook — name, event, purpose, source-of-truth path, enforcement level, owner — plus the "hooks only live in the two homes" rule. Governed alongside this canon by the quarterly review.

## Memory & knowledge — catalogued, NOT version-tracked here

Cross-project + machine-scoped, so it lives in global `~/.claude` and does **not** sync through the fork — no per-project copy to drift, so the check skips it (no `Home: shared/...` block). Home docs are authoritative:

- **memory-library-discipline** (write) — `~/.claude/projects/-Users-masonwood/memory/memory-library-discipline.md`
- **memory-retrieval-policy** (read) — `~/.claude/projects/-Users-masonwood/memory/memory-retrieval-policy.md`
- **memory-hygiene** (procedure + changelog rule) — `~/.claude/projects/-Users-masonwood/memory/docs/memory-hygiene.md`

## Recent changes

The "did anything important change since v0?" answer — one line per version bump, newest first. (Breaking changes are also flagged `Breaking: yes` on the block above so the drift check escalates them.)

- **2026-06-27 — STD-PERSONA-001 added (v1):** three human-facing workflow families gained a named voice (Rhea/design-handoff, Sol/quick-spec+quick-dev, Mara/escalation-on-class-change) via a single shared presentation snippet. Voice is restricted to three sanctioned spots and is explicitly subordinate to STD-ESCALATE-001 + answer-shape-and-autonomy, so "humanising" can't reintroduce narration/diary-voice/menus. Mara rides the existing escalation-snippet reference (no per-workflow wiring). Non-breaking (new standard, presentation-only).
- **2026-06-27 — STD-HOOKACTIVATE-001 added (v1):** git-hook gates are now a governed standard — the fork OWNS both distribution (`custom/githooks/` rail) and activation (`sync`/`onboard` set `core.hooksPath=.githooks` idempotently), with a SessionStart liveness probe. Closes the "deterministic gate silently off because nobody ran the activation step" gap. Local hook = best-effort; fail-closed CI tier deferred. husky retired in the fork. Non-breaking (new standard).
- **2026-06-27 — STD-CLAUDE-001 added (v1):** CLAUDE.md is now a governed standard — defines the global-doctrine vs thin-pointer-project split, the canonical project shape, and edit discipline. Added the hooks & gates registry pointer. Non-breaking (new standard, nothing changed for existing ones).
- **2026-06-26 — v1 (all standards):** initial canon — IDs, versions, and the drift check introduced. No behavioral change to any standard's content.

## How to author a NEW standard

1. **Frontmatter:** `name`, `description`, `contract_version` (integer, start at 1).
2. **Body:** the rule + rationale + (if a contract of record) a per-X template + its **enforcement tier** (which hook/CI/marker makes it hold — prose isn't enforcement; consult `enforcement-expert`).
3. **Add a parsable block here** — `ID:` (`STD-<AREA>-NNN`), `Version: v1`, `Breaking: no`, `Home: shared/<file>.md`, `Applies: all`, in that order.
4. **Add a `Recent changes` line.**
5. **Reference by path** from every consumer; **`sync-bmad-workflows.sh`** distributes it (authoring ≠ shipping).

## Versioning, drift & breaking changes

- **Bump `Version` + `contract_version`** only on a real change; set **`Breaking: yes`** when the change is a behavioral shift a project's restatement or a consumer could now violate (e.g. *how deploys work* or *how memory is written* changes), **`no`** for a safe/clarifying edit.
- **The drift check is Breaking-aware:** a version mismatch on a `Breaking: no` standard is a light "safe to auto-upgrade" note; on `Breaking: yes` it's a strong warning (and, in a later phase, a soft block on deploy-class actions). WARN-only today.
- **Two physical copies of `shared/`** (command-layout `custom/workflows/shared/` + the gitignored, sync-regenerated skills mirror `custom/skills-native/_shared/`) must carry the same versions; a divergence is itself drift.

## Governance (right-sized for a solo operator)

Team design-system governance (named owner per standard, quarterly review *meetings*, drift dashboards) is overhead when one person owns all 9. The lean equivalents:

- **Owner:** the fork maintainer (Mason) owns the baseline; changes land via the normal fork flow (edit `custom/workflows/shared/`, self-review, push, sync). No per-standard owner table.
- **Periodic review:** a lightweight "still true? / what broke? / who actually uses this?" pass over the 9 — right-sized as a `/schedule` reminder, not a meeting. (Cadence TBD — quarterly is fine.)
- **Explicit deviations (convention; enforcement is a later phase):** a project that must break a standard logs a conscious exception in `docs/standards-deviations.md` at its root — one block per deviation: `Standard:` (the ID), `Reason:`, `Date:`, `Expires:`. A logged, unexpired deviation is an *approved* drift; a quiet fork is a defect. The drift check will be taught to read these and suppress the WARN for an unexpired deviation (and re-WARN once it expires).
