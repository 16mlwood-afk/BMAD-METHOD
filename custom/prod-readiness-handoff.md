# Production-Readiness Enforcement — Developer Handoff

A self-contained handoff for a developer with **zero prior context**. Read top to bottom;
by the end you can operate it, debug it when it fires, and extend it without breaking its guarantees.

---

## 1. What this is, in one paragraph

A system that makes sure every project has a **written, correct deploy process** (and a notes/memory
setup) by the time it runs in production — and that a **fresh AI coding agent actually follows that**,
rather than hoping it reads a doc. It also ships a reusable **`enforcement-expert` skill** that codifies
*how* to make an agent comply with any rule. It targets ~13 projects that share tooling from a
customized **BMAD-METHOD fork**, where AI agents (Claude Code) start every session **cold** — no memory
of previous sessions.

## 2. The problem it solves

Three facts collide: (1) a cold agent doesn't know a project's rules unless something tells it that
session; (2) rules written only as prose are **probabilistic** — the agent might read them, might not,
and reliability decays as context fills; (3) deploys are irreversible and user-facing. Trigger incident:
a project's `CLAUDE.md` deploy instructions were simply **wrong** (run `railway up` from the wrong
directory) and nothing caught it — ~8 failed deploys. Generalized: nothing required a deploy process at
go-live, detected a live project lacking one, or reconciled one that had drifted.

**Core principle (the whole philosophy):** every enforcement mechanism is **DETERMINISTIC** (a
hook/tool physically blocks the agent — it cannot skip) or **PROBABILISTIC** (the agent must choose to
comply). Anything that must not fail needs a deterministic tier. "We wrote it in CLAUDE.md" is **not**
enforcement.

## 3. The pieces

- **A. Charter (the "what")** — `custom/workflows/shared/prod-readiness-charter.md` (fork; syncs to
  projects). Defines "production-ready" = a deploy contract/doc **and** memory discipline, and the three
  lifecycle states (crossing-to-prod-with-none · live-and-never-had-one · set-up-but-drifted).
- **B. `enforcement-expert` skill** — `~/.claude/skills/enforcement-expert/SKILL.md`. The deterministic-
  vs-probabilistic axis, the enforcement ladder, the three jobs (awareness/gate/proof), a decision
  procedure, composition patterns, anti-patterns, the Claude Code hook reference. Consult it before
  building any enforcement (and that is itself enforced — §6).
- **C. Detector — SessionStart probe (warn-only)** — `~/.claude/hooks/prod-readiness-probe.sh`. Warns
  (never blocks) when a **live** project lacks a deploy doc and/or memory. Conservative.
- **D. Blocker — deploy gate (dry-run)** — `~/.claude/hooks/prod-readiness-deploy-gate.sh`, a
  `PreToolUse(Bash)` hook. On a deploy command against a gap project: dry-run (current default) logs
  `WOULD-BLOCK` and allows; enforce denies.
- **E. Shared detection** — `~/.claude/hooks/lib/prod-readiness-detect.sh`. The functions both C and D
  use, so the warning and the block can never disagree.

## 4. Normative definitions (what the detector actually checks)

Surfaced in prose so future edits don't silently diverge from the code (`prod-readiness-detect.sh`).

A project is **LIVE** if `_bmad/bmm/config.yaml` has `project_phase: brownfield` or `project_phase: mixed`.
(`greenfield` or unset → not live → never flagged.)

A project **HAS A DEPLOY DOC** if ANY of:
- a `deploy:` block (line starting `deploy:`) in `_bmad/bmm/config.yaml`, OR
- `scripts/bmad-deploy.sh` exists, OR
- the project `CLAUDE.md` (repo root or app subdir) has a Markdown heading matching `deploy` (e.g. `## Deployment`), OR
- any `docs/*deploy*` file exists.

A project **HAS MEMORY** if ANY of:
- a `MEMORY.md` exists in the project's memory dir (`~/.claude/projects/<root-path-with-"/"→"-">/memory/MEMORY.md`), OR
- the project `CLAUDE.md` has a Markdown heading matching `memory` (e.g. `## Memory policy`).

A **GAP** is: LIVE **and** missing one or both. `deploy.bmad_contract: skip` is a deliberate choice, not a
gap — but a skip still requires a CLAUDE.md deploy section (skip defers to it).

## 5. How to operate it

| Task | Command |
|---|---|
| See what the gate *would* block | `cat ~/.claude/prod-readiness-gate.log` |
| Turn enforcement ON | `echo enforce > ~/.claude/prod-readiness-gate.mode` |
| Back to watch-only | `rm ~/.claude/prod-readiness-gate.mode` |
| Deploy a gap project on purpose | create `<project>/_bmad/.prod-readiness-override` (see §9) |
| Install on a fresh machine | `bash ~/bmad-method-v6/install-global-assets.sh` |
| Silence a flagged project | give it a deploy doc and/or memory per §4 |

## 6. The discipline — "warn, then gate"

The blocker ships in **dry-run on purpose.** It runs live, logging exactly what it *would* block, so we
gather real false-positive evidence **before** it can ever wrongly stop a deploy. Promotion to a hard
block is a deliberate flip, done only once the log is clean. A hard gate that false-fires gets disabled —
so we earn the right to enforce.

## 7. How the `enforcement-expert` skill is itself enforced (dogfooding)

Three layers: (1) **awareness** — a section + summary bullet in global `~/.claude/CLAUDE.md`
("Enforcement Gate Before Trusting a Rule"); (2) **scoped pointer** — charter §5 says consult it before
authoring any tier; (3) **deterministic nudge** — a `PreToolUse(Edit|Write)` hook
(`enforcement-expert-nudge.sh`) injects a reminder when you edit an enforcement surface (settings, hooks,
a CLAUDE.md guardrail). A nudge, not a block — hard-blocking config edits would be the "indiscriminate
gate" anti-pattern.

## 8. Worked example — how a gap shows up (and how to clear it)

Project `foo-service` has `project_phase: brownfield` in `_bmad/bmm/config.yaml`, **no** deploy doc, and
**no** memory doc.

1. **On SessionStart**, `prod-readiness-probe.sh` prints two warning lines — one naming the missing deploy
   contract, one naming the missing memory discipline (with the exact signals it looked for).
2. **On `railway up`**, `prod-readiness-deploy-gate.sh` appends to `~/.claude/prod-readiness-gate.log`:
   `<ts> WOULD-BLOCK foo-service :: railway up` — and **allows** the command (dry-run). In enforce mode it
   would instead deny with a reason pointing here.
3. **To fix:** add a deploy doc (a `deploy:` block in `_bmad/bmm/config.yaml`, or `scripts/bmad-deploy.sh`,
   or a `## Deployment` section in `CLAUDE.md`, or a `docs/deploy.md`) **and** memory (a `## Memory` section
   in `CLAUDE.md`, or a project `MEMORY.md`). Next session the warning is gone and the gate stops logging
   `foo-service` as a gap.

That's the "I can debug this when it fires at 4 p.m. on a Thursday" path.

## 9. Overrides — design intent (read before you create one)

The override file `<project>/_bmad/.prod-readiness-override` makes the gate **allow** a deploy and logs an
`OVERRIDE` line. **Intent: it is for temporarily shipping when you understand the risk — NOT for bypassing
the requirement to document deploys/memory.** Each override file MUST contain:
- a human-readable **reason**,
- the specific **gap** it covers (deploy, memory, or both),
- an **expiry date or condition** ("remove after the deploy doc lands in PR #123").

An override is a visible, logged, deliberate act. Dropping one into every repo to silence the system is an
abuse the audit log is designed to expose.

## 10. If you need to change it (governance playbook)

**Before adding a new rule or gate:**
1. Read `enforcement-expert/SKILL.md`.
2. Decide explicitly: **deterministic vs probabilistic**, and at which tier of the ladder. Write that
   decision down (a non-negotiable rule needs a deterministic tier — not prose).

**Before tightening the gate (dry-run → enforce):** see §11 (the promotion plan).

**Before weakening or removing a gate:**
1. Add a short note to `prod-readiness-charter.md` explaining *why*.
2. If the change is project-specific (one repo, not the standard), record it in that project's
   `docs/standards-deviations.md` instead of weakening the global rule.

**If you change the detection signals** (§4): update them in **one** place —
`prod-readiness-detect.sh` — and update §4 of this doc to match. The probe and gate both source that lib,
so they stay in lockstep; this doc is the only prose that can drift.

## 11. Not done — two concrete follow-ons

Spelled out so a future dev doesn't reverse-engineer what was "in someone's head."

**(a) Standards drift check (charter State 3 / `contract_version`) — designed, not built.**
- *Goal:* detect that a project's deploy doc is *outdated* vs the fork canonical (the railway-up-bug class).
- *Why it's not trivial:* the probe needs a per-project **conformed version** to compare against the
  canonical. The charter already carries `contract_version: 1`; what's missing is `sync-bmad-workflows.sh`
  stamping each project's conformed version into its `_bmad/bmm/config.yaml` at sync time. That sync change
  touches all 13 projects, so it's a careful, separate pass — not a quick add.
- *Build sketch:* add `contract_version` to `deployment-to-prod.md`; have sync write `deploy.contract_version`
  into each project; add a `pr_drift` check to `prod-readiness-detect.sh` + a warning line in the probe.

**(b) Promotion plan: dry-run → enforce — a decision, not code.**
- *Criteria to flip:* the gate log (`~/.claude/prod-readiness-gate.log`) shows **at least 10 real deploy
  attempts across the fleet, with every `WOULD-BLOCK` entry being a genuine gap project** (zero entries
  that name a project which actually had a deploy doc). Equivalently, ~2 weeks of dry-run with no false
  WOULD-BLOCK.
- *How to flip:* `echo enforce > ~/.claude/prod-readiness-gate.mode` (and add the same to a fresh-machine
  install if you want it on by default).
- *Owner:* the system owner (§12) makes the call and records the date the gate went enforce.

## 12. Ownership

- **System owner:** the BMAD fork maintainer (role; currently Mason). Approves changes to the charter,
  the gates, the detection library, and the dry-run→enforce flip.
- **Contributors:** any project owner can add deploy/memory docs to their own repo, create a logged
  override, or propose changes to the global system via PR to the fork.

## 13. File map

| File | Role | Tracked? |
|---|---|---|
| `custom/workflows/shared/prod-readiness-charter.md` | policy (the "what"); syncs to projects | fork git |
| `custom/prod-readiness-rollout-spec.md` | build plan (the "how + order") | fork git (not synced) |
| `custom/prod-readiness-handoff.md` | this doc | fork git (not synced) |
| `~/.claude/skills/enforcement-expert/SKILL.md` | strategy skill | backed up in fork |
| `~/.claude/hooks/lib/prod-readiness-detect.sh` | shared detection (§4 in code) | backed up in fork |
| `~/.claude/hooks/prod-readiness-probe.sh` | SessionStart warn (deploy + memory) | backed up in fork |
| `~/.claude/hooks/prod-readiness-deploy-gate.sh` | PreToolUse deploy gate (dry-run) | backed up in fork |
| `~/.claude/hooks/enforcement-expert-nudge.sh` | PreToolUse skill nudge | backed up in fork |
| `install-global-assets.sh` | restores the above to a fresh machine | fork git |
| `~/.claude/prod-readiness-gate.log` | the dry-run watch log | runtime |
| `~/.claude/prod-readiness-gate.mode` | `enforce` to activate | runtime (absent = dry-run) |

## 14. Caveats / known limits

- **Coverage:** the gate only catches deploys that run **through Bash** (railway/git/the deploy script). A
  non-Bash deploy path would bypass it — acceptable because all fleet deploys are Bash commands.
- **git-push match** is space-anchored (`" main"`), so `feature/main` won't false-match; `HEAD:main` is a
  deliberate false-negative (bias to allow).
- **Per-call cost:** the gate runs on every Bash call, but one `grep` short-circuits ~99% (non-deploy)
  before any heavier work.
- **The enforce flip is global** — it affects every project/session at once; that's why it waits on the
  clean-log evidence (§11b).
- **Memory detection** assumes the project-memory path encoding (`/`→`-`); if that internal convention
  changes, `pr_has_memory` needs updating.
- **Distribution:** the hooks live in `~/.claude` (not the synced workflow tree); they're distributed via
  `install-global-assets.sh`, *not* the project sync. Authoring the charter does **not** ship the
  enforcement.
