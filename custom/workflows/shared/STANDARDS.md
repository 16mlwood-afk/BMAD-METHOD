---
name: STANDARDS
description: 'The canon — the single index of every shared standard a BMAD-managed project follows (deploy, delivery, webhook boundaries, diagnostics, worktree/parallel-session safety, prod-readiness, AND memory discipline). One place to answer "what is the canonical way to do X?". Each standard lives once at its Home, syncs to projects, and is referenced BY PATH — never restated. Machine-parsable: each synced standard has an ID/Version/Home/Applies block that the SessionStart drift check (check-standards-drift.sh) scans.'
contract_version: 1
---

# STANDARDS — the canon

The single index of the standards every BMAD-managed project follows. If you're asking *"what is the canonical way to do X?"*, the answer is one of the blocks below — open its **Home** doc.

## How to use this

- **The Home doc is the source of truth.** A project's `CLAUDE.md` only *points at* a standard; its prose summary is a convenience, never authoritative. A restatement that disagrees with the Home doc is drift — log it in `docs/fork-gaps.md` and fix it.
- **Reference by path, don't copy.** `cash-recovery` is the reference project for this shape (thin CLAUDE.md pointer + the manual in `docs/`, citing the synced standard).
- **Drift is checked automatically.** `check-standards-drift.sh` (SessionStart, WARN-only) compares this canonical's `Version:` lines against the copy synced into the current project; a project behind a bumped standard is flagged. The project's synced `STANDARDS.md` copy IS its declaration of "what I last pulled" — no separate lock file or CLAUDE.md block to maintain.

## The standards (machine-parsable index)

Each block below is scanned line-by-line: `ID` then `Version` then `Home` then `Applies`, each on its own line. Keep it boring — no nesting, no inline prose on those four lines.

### deployment lifecycle

deployment-to-prod — the post-merge deploy contract (admin-merge rules, dirty-path filters, dep auto-heal, exit-code grammar).
ID: STD-DEPLOY-001
Version: v1
Home: shared/deployment-to-prod.md
Applies: all

delivery-to-main — getting an artifact from local disk to origin/<default-branch> so external consumers can read it.
ID: STD-DELIVERY-001
Version: v1
Home: shared/delivery-to-main.md
Applies: all

prod-readiness-charter — getting a project READY to deploy (the 3 states, detection, enforcement); the layer above the deploy contract.
ID: STD-PRODREADY-001
Version: v1
Home: shared/prod-readiness-charter.md
Applies: all

### boundaries & contracts

webhook-contract-charter — every webhook boundary (sender-strict/receiver-lenient rollout, breaking-change taxonomy, per-boundary template).
ID: STD-WEBHOOK-001
Version: v1
Home: shared/webhook-contract-charter.md
Applies: all

### implementation safety

diagnostics-gate — prove-don't-assert verification gate (a new diagnostic means RED until a clean re-run proves green).
ID: STD-DIAG-001
Version: v1
Home: shared/diagnostics-gate.md
Applies: all

parallel-sessions — concurrent-session protocol (worktree-before-edit, integrate-advancing-main, named collision classes, story claim+reconcile).
ID: STD-PARALLEL-001
Version: v1
Home: shared/parallel-sessions.md
Applies: all

worktree-portability — artifact paths resolve to the worktree root, not the main checkout.
ID: STD-WORKTREE-001
Version: v1
Home: shared/worktree-portability.md
Applies: all

wave-orchestration — fan-out-in-waves protocol for implement/review/create workflows (additive to solo parallel dev).
ID: STD-WAVE-001
Version: v1
Home: shared/wave-orchestration.md
Applies: all

detect-stack — shared utility: identify the project tech stack.
ID: STD-STACK-001
Version: v1
Home: shared/detect-stack.md
Applies: all

## Memory & knowledge — catalogued, NOT version-tracked here

Memory discipline is cross-project + machine-scoped, so it lives in global `~/.claude` and does **not** sync through the fork — there is no per-project copy to drift, so the drift check skips it (no `Home: shared/...` block). Its Home docs are authoritative:

- **memory-library-discipline** (write side) — `~/.claude/projects/-Users-masonwood/memory/memory-library-discipline.md`
- **memory-retrieval-policy** (read side) — `~/.claude/projects/-Users-masonwood/memory/memory-retrieval-policy.md`
- **memory-hygiene** (full procedure + changelog rule) — `~/.claude/projects/-Users-masonwood/memory/docs/memory-hygiene.md`

## How to author a NEW standard

1. **Frontmatter:** `name`, `description` (what it governs + which workflows reference it), `contract_version` (integer, start at 1).
2. **Body:** the rule, its rationale, a per-X template if it's a contract of record, and its **enforcement tier** — which hook / CI gate / marker makes it hold (prose alone is not enforcement; consult the `enforcement-expert` skill).
3. **Add a parsable block to this canon** — an `ID:` (`STD-<AREA>-NNN`), `Version: v1`, `Home: shared/<file>.md`, `Applies: all` (or a narrower scope), in that order, each on its own line.
4. **Reference it by path** from every consumer — never paste its body.
5. **Distribute:** `sync-bmad-workflows.sh` mirrors `shared/` into every project. Authoring the doc does NOT ship it — the sync does.

## Versioning & drift

- **`Version:` (here) + `contract_version:` (the doc's frontmatter) are the drift key.** `check-standards-drift.sh` compares this canonical's `Version:` against the project's synced copy each SessionStart (WARN-only). `prod-readiness-charter` State-3 is the same idea at the contract level.
- **Bump the version** (`v1` → `v2`, and `contract_version`) only on a BREAKING change — one a project's restatement or a consumer could now violate. Additive clarifications don't bump.
- **Enforcement is phased:** Phase 1 (now) everything WARN; Phase 2 missing-standard → hard-warn, mismatch → warn; Phase 3 (optional) a `Breaking: yes` marker on a block makes a mismatch BLOCK.
- **Two physical copies of `shared/` exist** — the command-layout source (`custom/workflows/shared/`) and the skills-layout mirror (`custom/skills-native/_shared/`, gitignored + regenerated by sync). They must carry the same versions; a divergence is itself drift.
