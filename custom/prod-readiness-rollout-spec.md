# Prod-Readiness Rollout — Implementation Spec

Build plan for the remaining phases of `custom/workflows/shared/prod-readiness-charter.md`.
**Fork-internal planning — NOT under `workflows/`, so it is not synced to the 13.**
The charter is the *what*; this is the *how + in what order*. Enforcement design follows
the `enforcement-expert` skill (required by the charter §5 gate).

## Status snapshot

- **Phase 0 — charter:** shipped (`53a8d810`).
- **Phase 1 — deploy probe (warn-only):** shipped — `~/.claude/hooks/prod-readiness-probe.sh`, a global SessionStart hook, conservative, never blocks.
- **Remaining:** Items A–E below.

## Shared foundation (do first — both probe and gate depend on it)

The Phase-1 probe currently inlines its detection. The gate (Item B) must use the **same**
criteria, or the block and the warning diverge (the agent gets blocked on different rules
than it was warned about — confusing and trust-eroding). **Extract the detection into one
sourced helper** `~/.claude/hooks/lib/prod-readiness-detect.sh` exposing:
`pr_find_root <start>` (walk up for `_bmad/bmm/config.yaml`), `pr_is_live <root>`
(`project_phase` ∈ brownfield|mixed), `pr_has_deploy_doc <root>` (`deploy:` block ·
`scripts/bmad-deploy.sh` · CLAUDE.md deploy section · `docs/*deploy*`). Refactor the probe
to source it (behavior-preserving; re-run the existing tests). One definition of "ready",
two consumers.

## Item A — Phase-1 false-positive watch  *(process, not a build)*

- **Objective:** prove the deploy probe never warns on a healthy project before any gate is added. (Per the doctrine: warn-then-gate; a gate built on a noisy detector gets disabled.)
- **Method:** over the next sessions across the 13, collect any probe output. A warning on a project that genuinely has a deploy doc = a detection bug → fix the signal list, don't proceed.
- **Exit criterion (gates Item B):** the 13 projects opened at least once with **zero false warnings**; any real gaps it surfaced are either fixed or acknowledged.
- **No code** unless a false positive appears.

## Item B — Phase-3 deploy blocker  *(the gate)*

- **B + verdict:** don't deploy a live project with no deploy contract → irreversible, user/partner-facing → **non-negotiable → deterministic tier required.**
- **Mechanism (DETERMINISTIC GATE, tier 5):** a global **PreToolUse hook, matcher `Bash`** — `~/.claude/hooks/prod-readiness-deploy-gate.sh`. Reads `tool_input.command`; if it matches a deploy pattern, runs `pr_*` detection; on a confirmed gap with no override, returns `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"<project> is live with no deploy contract — author one (prod-readiness-charter.md) or create _bmad/.prod-readiness-override with a reason."}}`.
- **Deploy-command patterns (tight — bias to allow on ambiguity):** `railway up`, `railway redeploy`, `railway up --ci`, `scripts/bmad-deploy.sh`, and `git push` whose target resolves to the default branch on an auto-deploy remote (railway/vercel/fly). When the pattern is uncertain, **do not deny.**
- **Override (logged, deliberate):** allow when `_bmad/.prod-readiness-override` exists; append `<date> <project> <reason>` to `~/.claude/prod-readiness-overrides.log`. A *file*, not an inline flag, so a context-free agent can't casually self-bypass; an agent must get explicit user approval before creating it.
- **Composition:** SessionStart warning (Item A, AWARENESS) + this deny (GATE) → belt-and-suspenders; the warning makes the block legible.
- **False-positive guard:** shares `pr_*` (already conservative) AND only fires on a tightly-matched deploy command; `bmad_contract: skip` + a CLAUDE.md deploy section passes.
- **Test plan:** (1) deny on a gap-project deploy command; (2) allow on a healthy project; (3) allow + log with the override file present; (4) allow on non-deploy Bash; (5) allow on an ambiguous command.
- **Gating dependency:** Item A clean.
- **Distribution:** global `~/.claude/settings.json` PreToolUse (auto-covers all projects). Add the install to `onboard-project.sh` so a fresh machine gets the probe + gate.

## Item C — Memory probe  *(Phase-1 for the memory domain)*

- Extend the SessionStart probe with a second, independent check: a live project with **no `memory/` dir AND no CLAUDE.md memory-policy section** → warn (one line, like deploy). Conservative; silent if memory is deliberately disabled (`autoMemoryEnabled: false` or a documented opt-out).
- Same warn-then-gate path as deploy; the memory *gate* is deferred until both probes are proven accurate.
- **Gating dependency (charter rule):** start only after deploy detection (Item A) is proven accurate.

## Item D — State-3 drift check  *(contract_version)*

- Stamp `contract_version: N` in `deployment-to-prod.md` frontmatter; record the conformed version per project (e.g. `deploy.contract_version` in `_bmad/bmm/config.yaml`, written at sync time).
- Probe compares project-conformed vs canonical; warns on a lag. MVP is the version-number lag only.
- **Later enhancement (not MVP):** the semantic "project CLAUDE.md contradicts the synced contract" check (the live `railway up` doc-bug class) — needs content analysis; defer.

## Item E — Distribution / rollout

- Probe + gate live in `~/.claude` (global) → cover every project with **no per-project sync**. The only distribution work is making a **fresh machine/onboarding** install them: add a hooks-install step to `onboard-project.sh` (and document it), since `~/.claude` is not git-tracked.
- Reminder: none of this is in the synced `workflows/` tree — authoring the charter/spec does NOT ship the enforcement.

## Sequencing

```
Shared foundation (detect.sh)  ─┐
                                ├─→  A (watch, deploy)  ─→  B (deploy gate)
                                └─→  C (memory probe) ─ and ─ D (drift)  [after A clean]
E (onboarding install + docs) runs alongside once B exists.
```

Deploy first, memory second, the hard gate last and only on a proven-quiet detector — exactly the charter's warn-then-gate discipline.
