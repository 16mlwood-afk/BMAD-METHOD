---
name: hook-activation-standard
description: Git-hook deterministic gates must be both DISTRIBUTED and ACTIVATED by the fork — a synced gate script is worthless until core.hooksPath actually points at the tracked .githooks/ dir. Canonical mechanism + the honest enforcement ceiling.
contract_version: 1
---

# Hook activation standard (STD-HOOKACTIVATE-001)

## The rule

A git-hook deterministic gate (pre-push `tsc`/`vitest`/`use-server`, the blast-radius
backstop, etc.) is only real if it actually fires. Distributing the gate *script* is not
enough — the repo's git must be told to run it. The fork owns BOTH halves:

1. **Distribution** — gate scripts ride the `custom/scripts/` → `./scripts/` rail; the
   canonical hook **entrypoints** ride the new `custom/githooks/` → `./.githooks/` rail.
   The entrypoints are thin dispatchers that run the gates listed in `.githooks/gates.conf`
   (an absent gate is skipped, so the conf may name the full fleet set).
2. **Activation** — `sync-bmad-workflows.sh` and `onboard-project.sh` set
   `core.hooksPath=.githooks` and re-exec the entrypoints **idempotently, on every run**.
   So a synced gate is reliably WIRED instead of silently off. Manual escape hatch /
   self-heal: `scripts/activate-hooks.sh`.

## Canonical mechanism: tracked `.githooks/` + `core.hooksPath` (husky retired)

- `.githooks/` is tracked, so it travels with every checkout; `core.hooksPath` lives in the
  shared common git config, so it covers every **worktree** of a repo automatically.
- husky and `.githooks` both own `core.hooksPath` and are mutually exclusive — standardize
  on `.githooks` and migrate husky repos. The fork itself runs on `.githooks` (dogfood).

## Awareness

`check-hook-activation.sh` (SessionStart, registered via `install-global-assets.sh`) warns
when a repo ships a `.githooks/` gate but isn't activated (or husky↔githooks conflict).
Conservative: silent when wired, silent when no gate is present.

## The honest enforcement ceiling

- **Activation is DETERMINISTIC** (sync/onboard set it; the operator does not choose).
- **The local hook is a best-effort GATE** — bypassable by `git push --no-verify` (logged)
  or a manually unset `core.hooksPath`. Git fails *open* on a missing hook.
- **The only fail-closed tier is CI** — a required check re-running the same gate logic
  server-side, independent of local state. It is **deferred** (blocked on this fleet's GH
  Actions quota reliability). Until it lands, do NOT call a local git-hook gate
  "unbypassable." See `docs/hook-activation-rail-spec.md` for the full design + rollout.

Enforcement classification was done with `enforcement-expert`; this standard exists
precisely to avoid the *"authored the doc and called it enforced"* anti-pattern.
