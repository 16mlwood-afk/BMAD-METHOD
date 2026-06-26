---
name: STANDARDS
description: 'The canon — the single index of every shared standard a BMAD-managed project follows (deploy, delivery, webhook boundaries, diagnostics, worktree/parallel-session safety, prod-readiness, AND memory discipline). One place to answer "what is the canonical way to do X?". Each standard lives once at its Home, syncs to projects under _bmad/bmad-shared/, and is referenced BY PATH — never restated. Carries the contract_version key that drift-detection compares against.'
contract_version: 1
---

# STANDARDS — the canon

The single index of the standards every BMAD-managed project follows. If you're asking *"what is the canonical way to do X?"*, the answer is one of the rows below — open its **Home** doc.

## How to use this

- **The Home doc is the source of truth.** A project's `CLAUDE.md` only *points at* a standard; its prose summary is a convenience, never authoritative.
- **A restatement that disagrees with the Home doc is drift** — the Home doc wins, and the stale restatement should be logged (`docs/fork-gaps.md`) and fixed. The wrong "`railway up` from `inventory-manager/`" deploy note was exactly this class.
- **Reference by path, don't copy.** Workflows and CLAUDE.md sections cite the standard (`_bmad/bmad-shared/<name>.md`); they never paste its body. `cash-recovery` is the reference project for this shape (thin CLAUDE.md pointer + the manual in `docs/`, citing `bmad-shared/`).

## The standards

### Deploy & delivery lifecycle
| Standard | Governs | Home | Version |
|---|---|---|---|
| `prod-readiness-charter` | Getting a project READY to deploy — the 3 states (greenfield-no-contract / live-brownfield-never-had-one / drifted-from-canonical), detection, enforcement. The layer *above* the deploy contract. | `shared/prod-readiness-charter.md` | 1 |
| `deployment-to-prod` | The post-merge deploy contract — admin-merge rules, dirty-path filters, dep auto-heal, `bmad-deploy.sh` exit-code grammar. Per-project values in `config.yaml → deploy:`. | `shared/deployment-to-prod.md` | 1 |
| `delivery-to-main` | Getting an artifact from local disk to `origin/<default-branch>` so external consumers can read it. | `shared/delivery-to-main.md` | 1 |

### Boundaries & contracts
| Standard | Governs | Home | Version |
|---|---|---|---|
| `webhook-contract-charter` | Every webhook boundary — sender-strict/receiver-lenient rollout order, breaking-change taxonomy, fail-loud, per-boundary template. | `shared/webhook-contract-charter.md` | 1 |

### Implementation safety
| Standard | Governs | Home | Version |
|---|---|---|---|
| `diagnostics-gate` | Prove-don't-assert: a new diagnostic after edit/merge/teardown means the gate is RED until a re-run in the current checkout proves green. | `shared/diagnostics-gate.md` | 1 |
| `parallel-sessions` | Concurrent-session protocol — worktree-before-edit, integrate-advancing-main, named collision classes, story claim+reconcile. | `shared/parallel-sessions.md` | 1 |
| `worktree-portability` | Artifact paths resolve to the worktree root, not the main checkout. | `shared/worktree-portability.md` | 1 |
| `wave-orchestration` | Fan-out-in-waves protocol for implement/review/create workflows (additive to solo parallel dev). | `shared/wave-orchestration.md` | 1 |
| `detect-stack` | Shared utility — identify the project tech stack. | `shared/detect-stack.md` | 1 |

### Memory & knowledge — Home is global `~/.claude`, NOT the fork
Memory discipline is cross-project + machine-scoped, so it lives in global memory and does **not** sync through the fork. It is catalogued here so the canon answers "what's the standard for X?" in one place — but its Home docs are authoritative and `contract_version` does not apply (there is no per-project synced copy to drift).

| Standard | Governs | Home |
|---|---|---|
| `memory-library-discipline` | How memory is WRITTEN — shelves, one stable slug each, backing-file-first-then-index. | `~/.claude/projects/-Users-masonwood/memory/memory-library-discipline.md` |
| `memory-retrieval-policy` | How memory is READ — small task-specific retrieval, default cap of 3. | `~/.claude/projects/-Users-masonwood/memory/memory-retrieval-policy.md` |
| `memory-hygiene` | Full procedure — global-vs-project scope, the `memory-changelog.md` breadcrumb rule, what never belongs in memory. | `~/.claude/projects/-Users-masonwood/memory/docs/memory-hygiene.md` |

## How to author a NEW standard

A standard in this system is a markdown doc under `shared/` with:

1. **Frontmatter:** `name`, `description` (one paragraph — what it governs + which workflows reference it), `contract_version` (integer, start at `1`).
2. **Body:** the rule, its rationale, a per-X template if it's a contract of record, and — critically — its **enforcement tier**: which hook / CI gate / marker makes it actually hold. Prose alone is not enforcement; consult the `enforcement-expert` skill to classify DETERMINISTIC vs PROBABILISTIC before relying on it.
3. **Add a row to this canon.**
4. **Reference it by path** from every consumer (workflow step, CLAUDE.md section) — never paste its body.
5. **Distribute:** `sync-bmad-workflows.sh` mirrors `shared/` into every project's `_bmad/bmad-shared/`. Authoring the doc does NOT ship it — the sync does.

## Versioning & drift

- **`contract_version` is the drift key.** A project records the version it synced; `prod-readiness-charter` State-3 compares that against this canonical to detect a stale copy. (The comparison probe is charter Phase-1 — designed, not yet built; see `prod-readiness-charter.md` §Rollout.)
- **Bump `contract_version`** on a BREAKING change — one a project's restatement or a consumer could now violate. Additive clarifications don't bump.
- **Two physical copies of `shared/` exist** today: the command-layout source (`custom/workflows/shared/`) and the skills-layout mirror (`custom/skills-native/_shared/`). They must carry the same `contract_version`; a divergence between them is itself drift. Keeping these in lockstep is an open hardening item.
