---
title: Hook distribution + activation rail — implementation spec
description: Fork-owned rail that makes git-hook deterministic gates reliably WIRED (not silently off) across all sync targets. Ceiling C — local-hook+awareness now (A), CI fail-closed tracked (B). Authored via mason-bmad-workflow-expert; routes deterministic-tier decisions through enforcement-expert. NOT YET BUILT — owner-review artifact.
status: proposed — awaiting owner sign-off before the fleet (Phase 1) step
related: docs/fork-gaps.md ("Deterministic enforcement gates … have no fork-managed distribution/activation path"), custom/workflows/shared/escalation-on-class-change.md (Tier-3 rides this), inbound-flow PR #2446 (reference impl)
---

# Hook distribution + activation rail — implementation spec

## Problem (the gap this closes)

The fork keeps shipping **deterministic git-hook gates** — pre-push `tsc`/`vitest`,
`check-use-server-exports`, nav/drift validators, the blast-radius backstop. The gate
SCRIPT distributes fine (the `custom/scripts/` → project `./scripts/` per-file rail). But
the thing that makes `.git/hooks/pre-push` actually CALL the script — `core.hooksPath`
pointed at a tracked hooks dir, scripts executable — is a **manual per-repo step nobody
runs**. So `core.hooksPath` is unset, `.git/hooks/` is empty, and the gate is **silently
OFF**: a deterministic tier that is, in practice, probabilistic. Worse, two activation
systems fight (the fork + some targets use **husky**; inbound-flow consolidated on
**`.githooks/` + `core.hooksPath`**) and they are mutually exclusive — both set
`core.hooksPath`, so whichever ran last wins and the other silently dies.

This is the `enforcement-expert` anti-pattern *"authoring the doc and calling it
enforced — the hook didn't ship (separate distribution track)."*

## Enforceability classification (the honest ceiling)

The load-bearing honesty point, decided with `enforcement-expert`:

> **A local git hook can never be truly fail-closed.** Git fails *open* on a missing hook
> (no hook → push allowed), and `git push --no-verify` is bypass-by-design. The ONLY
> deterministic, unbypassable gate is a **CI required check** that re-runs the same gate
> logic server-side, independent of local repo state.

So the rail's honest ceiling is split, and **ceiling C** is what we build:

| Tier | Mechanism | Class | Ceiling | Where it fails |
|---|---|---|---|---|
| **A1 · Sync owns activation** | `sync-bmad-workflows.sh` sets `core.hooksPath=.githooks` + `chmod +x`, idempotent, every run | **DETERMINISTIC activation** (on sync) | Repo is reliably WIRED — operator doesn't choose | Only as fresh as the last sync; a dev can unset `core.hooksPath` after |
| **A2 · Onboard provisions** | `onboard-project.sh` does the same at bootstrap | **DETERMINISTIC** at bootstrap | Fresh repos start wired | Already-onboarded repos rely on A1 re-running |
| **A3 · Liveness probe** | `check-hook-activation.sh` SessionStart warns "gate script present, no active wiring" | **DETERMINISTIC delivery of AWARENESS**, probabilistic action | Dead/conflicted state becomes visible between syncs | Cannot activate anything; warns only |
| **A4 · The local gate itself** | `.githooks/pre-push` runs the gate scripts | **best-effort GATE** (deterministic *if wired*, bypassable) | Fast feedback at push time | `--no-verify`, unset hooksPath — bypass by design (override-with-logging) |
| **B · CI required check** | GitHub Actions re-runs the gate logic server-side | **DETERMINISTIC GATE** (unbypassable) | The true fail-closed guarantee | **Blocked** on this fleet's GH Actions quota reliability — TRACKED, not built now |

**Honest label for what ships in A:** *deterministic activation + best-effort gate +
awareness.* This is a real jump from "silently off" to "reliably on unless deliberately
bypassed" — but it is **not** a fail-closed guarantee. Do not let anyone read A as
unbypassable; B is the only thing that earns that word, and B is deferred.

## Canonical per-repo mechanism

**Tracked `.githooks/` + `core.hooksPath` — retire husky.** Rationale:

- **Worktree-safe.** `core.hooksPath` lives in the shared common git config, so activating
  once covers every worktree of the repo; a tracked `.githooks/` travels with every
  checkout. Husky's `prepare` depends on `npm install` running, which worktrees don't do
  reliably (aligns with `worktree-portability.md`).
- **Single source of truth.** husky and `.githooks` both own `core.hooksPath` → they
  cannot coexist. Standardize on `.githooks`, migrate husky repos (incl. the fork itself,
  which still uses `.husky/pre-commit`). Reference migration: inbound-flow PR #2446.

`.githooks/` entrypoints are **thin dispatchers**: `pre-push` / `pre-commit` just invoke
the real gate scripts in `./scripts/` (which already distribute). Keeps the gate logic in
the one rail that already works; the entrypoint is boilerplate.

## Build (Phase 0 — fork-local, reversible, NO sync run)

All in `~/bmad-method-v6` (allowlisted for direct fork edits). Nothing leaves the fork
until Phase 1.

1. **`custom/githooks/`** (new source dir) — canonical entrypoints:
   - `pre-push` — dispatcher: for each registered gate script in `./scripts/`, run it; non-zero → block the push with a legible reason + the `--no-verify` override note (logged).
   - `pre-commit` — same shape if/when commit-time gates exist.
   - Entrypoints are gate-agnostic: they discover which `./scripts/*` gates to run from a
     small manifest (`.githooks/gates.conf`) so adding a gate is a one-line edit, not an
     entrypoint rewrite.

2. **`custom/scripts/activate-hooks.sh`** (new, ships via the existing scripts rail) —
   idempotent: `git config core.hooksPath .githooks` + `chmod +x .githooks/*`. Safe to run
   anywhere, any number of times. Also the manual escape hatch for a developer.

3. **`sync-bmad-workflows.sh`** — two additions, mirroring `sync_scripts_for_project`:
   - `sync_githooks_for_project(root, mode)` — per-file copy `custom/githooks/*` →
     `root/.githooks/*`, exec-preserving, non-destructive (same shape as the scripts rail;
     removal handling can later ride the new `sync-manifest.txt` — minor open item).
   - `activate_hooks_for_project(root, mode)` — **check mode**: drift if
     `core.hooksPath != .githooks` OR `.githooks/` missing OR entrypoints not executable.
     **sync mode**: run the activation (`git -C root config core.hooksPath .githooks`,
     `chmod +x`).
   - Wire both at the existing call sites: main sync loop (~L1382), worktree sync (~L738),
     skills-native path (~L927), and the `--check` drift accounting (~L1253) so
     un-activated repos surface in `/project-health` and the SessionStart BMAD-DRIFT probe.

4. **`check-hook-activation.sh`** (new SessionStart probe, sibling of
   `check-claude-md-drift.sh`) — in project cwd: if a gate is expected (`.githooks/` or a
   known gate script present) but `core.hooksPath != .githooks` or an entrypoint isn't
   executable, emit one awareness line naming the repo + the one-command fix
   (`scripts/activate-hooks.sh`). Also detect a husky↔githooks conflict. **Conservative:
   silent when wired, and silent when no gate is present** (no false fire on gate-less
   repos). Register in `hooks.json` SessionStart (jq-merged, distributes via the hooks
   rail). Add a fixture to `check-hooks-smoke.sh`.

5. **`onboard-project.sh`** — call `activate_hooks_for_project` (+ githooks sync) at
   bootstrap so a fresh repo starts wired; stamp `hooks-activated` in the onboarding marker.

6. **Retire husky in the fork** — move `.husky/pre-commit` logic into
   `custom/githooks/pre-commit`, set `core.hooksPath=.githooks` on the fork, drop husky +
   its `prepare`. The fork becomes its own first consumer (dogfood).

7. **Self-review (Mode 1)** + register a `STD-HOOKACTIVATE-001` block in `STANDARDS.md`
   (cross-cutting shared rule, 14-repo blast radius → traceable canon) + STATUS.md
   changelog entry.

## Rollout (staged)

- **Phase 0 — fork-local build above.** Reversible; touches only `~/bmad-method-v6`. No
  fleet effect. ← *the most I do before your sign-off.*
- **Phase 1 — the gated fleet step (OWNER SIGN-OFF REQUIRED).** `git push myfork custom`
  → `sync-bmad-workflows.sh` distributes `.githooks/` + activates across all 14 targets.
  Then a sweep: confirm each target reports `core.hooksPath=.githooks` and
  `check-hook-activation.sh` is silent. This is a **new activation contract + cross-repo
  rollout** — owner-gated by the autonomy ladder; warn-only posture first (the probe
  warns, the gate runs but nothing new hard-blocks until proven quiet).
- **Phase 2 — B (tracked, deferred).** CI required-check tier re-running gate logic
  server-side = the fail-closed guarantee. Blocked on GH Actions quota reliability
  (the fleet's structural zero-step failures). Logged as a fork-gap follow-up so the
  ceiling can rise later without re-litigating the design.
- **Phase 3 — Tier-3 gates ride the rail.** Only AFTER Phase 1 is proven live: the
  deterministic escalation backstop (`escalation-on-class-change.md` Tier 3) and any
  other deterministic gate distribute + activate through this rail, warn-only first. **No
  bespoke 15th hook before then** (your standing instruction).

## Self-review (Mode 1 on this spec)

- ✅ **Enforcement honesty** — every tier labelled; A is not sold as fail-closed; B named as
  the only unbypassable tier and explicitly deferred with its blocker. Avoids the
  doc-called-enforced trap by construction.
- ✅ **Distribution stated** — rides the existing scripts + hooks rails, not a new track;
  activation owned by sync/onboard, not a manual step. (The exact failure the gap names.)
- ✅ **Conservative detector** — the probe is silent when wired and when gate-less; bias to
  no-fire (a missed warning is recoverable; a false fire erodes trust).
- ✅ **Override-with-logging** — `--no-verify` is the inherent, logged escape; A4 keeps it.
- ✅ **Worktree-safe** — `core.hooksPath` (shared common config) + tracked `.githooks/`.
- ⚠️ **Concern (not blocking)** — removed-entrypoint purge isn't handled by the additive
  per-file copy; fold into the `sync-manifest.txt` deletion mechanism in a follow-up.
- ⚠️ **Concern (not blocking)** — husky migration touches each repo's `package.json`
  (`prepare`); per-repo, not a doc sync. Sequence it INTO Phase 1's sweep, repo by repo.

## What needs an owner call

1. **Phase 1 go/no-go** — sign off to distribute + activate across the 14 (warn-only).
2. **Confirm ceiling C** (assumed from "go ahead"): ship A now, track B — i.e. accept
   "reliably-wired local hook + awareness" as today's ceiling, with CI fail-closed as a
   tracked follow-up rather than a blocker.
