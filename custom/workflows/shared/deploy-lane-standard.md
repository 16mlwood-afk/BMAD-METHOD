---
name: deploy-lane-standard
contract_version: 1
description: 'STD-DEPLOY-002 — the minimum a project''s DEPLOY LANE must satisfy before Claude may call a deploy verified. Ten requirements, each with a mechanical probe (tools/check-deploy-lane.py), a declared-vs-verified distinction, and a stated ceiling. The layer INSIDE STD-DEPLOY-001: that contract says when and whether to deploy; this one says what the thing that deploys must be able to prove.'
---

# Deploy Lane Standard (STD-DEPLOY-002)

**ID:** STD-DEPLOY-002 · **Version:** v1 · **Applies:** every project that ships to a
production environment · **Home:** `shared/deploy-lane-standard.md` · **Checker:**
`tools/check-deploy-lane.py` (fork) · **Health:** feeds `tools/bmad-health.py`.

## Why this exists — the finding it encodes (2026-09-04, cash-recovery)

A deploy script stamped the newest commit id onto production, uploaded, read the stamp back
off the running container and printed *"LIVE SHA … read back off the container, not inferred
from the build."* Production was serving a page from three weeks earlier. The stamp was a
variable the script itself had set; the upload had come from a different directory than the
one the script stood in, because the provider's CLI uploads the *linked* directory rather than
the current one. Every check in the lane was green. The owner noticed; the lane did not.

The lane had grown one check at a time, each after its own incident (stale stamp 07-25,
upload race 08-03, orphaned stamp 08-03, wrong-directory upload 09-04). Nothing said what a
lane must be able to prove *before* the incident that proves it cannot. This standard is that
list. It is short on purpose: ten things, each machine-checkable, each with its ceiling stated.

## The one rule

> **A deploy is verified when the lane has proven — not asserted — that the running
> environment holds the source tree named by the commit it reports.** Everything below is in
> service of that sentence. A lane that cannot prove it reports `UNVERIFIED`, never `LIVE`.

## Requirements

Each requirement has an ID, a plain statement, and the **probe** `check-deploy-lane.py` runs.
A probe answers `verified` (the artefact shows the behaviour), `declared` (the lane carries a
marker comment `# STD-DEPLOY-002 R<n>: <how>` but the probe could not see the behaviour
itself), or `missing`. **`declared` is a claim, not a proof** — it is how a lane on a provider
this checker does not know can still be assessed, and it is reported as such.

| ID | Requirement | Probe (over the lane script unless stated) |
|---|---|---|
| **R1** | **One lane.** Exactly one executable script ships the project; docs and agents invoke it, never the provider's ship command directly. | `deploy.lane` (default `scripts/deploy.sh`) exists and is executable. |
| **R2** | **Pinned.** The lane refuses unless `HEAD` is exactly the remote default branch tip and every shipping path is clean. | script compares `HEAD` with `origin/<branch>` via `rev-parse`, and runs a dirty check. |
| **R3** | **Derived stamp.** The running commit id is derived from `git rev-parse HEAD` on every deploy and written where the app can report it. Never hand-set. | `rev-parse HEAD` feeds a commit/stamp variable. |
| **R4** | **Upload root asserted.** The lane proves the directory the provider will upload or build from is the directory it stands in, and passes the path explicitly where the CLI allows it. | `upload_root` assertion present (or marker). |
| **R5** | **Convergence read-back.** After the upload, the lane reads the running environment's reported commit and classifies it: converged · superseded (descendant, benign) · behind · diverged · unreadable. `behind`/`diverged` are failures; `unreadable` is `UNVERIFIED`. | `converg` loop reading the live commit, with the verdict words present. |
| **R6** | **Source fingerprint.** After convergence the lane recomputes a fingerprint of the *shipping paths* inside the running environment and compares it with the uploaded tree. Mismatch is fatal and not overridable. The stamp is a variable; this is the code. | `scripts/deploy-fingerprint.sh` present in the project AND invoked by the lane. |
| **R7** | **One at a time.** Concurrent deploys from any working copy of the repo are serialised by a lock the lane takes and releases; a stale lock is taken over with a warning, never silently. | lock in the common git dir (`deploy.lock`) or `flock`, or marker. |
| **R8** | **Stamp never lies on failure.** If the stamp lands and the upload does not, the lane restores the previous stamp on exit. | exit trap restoring the stamp (or marker). |
| **R9** | **Golden tests, both directions.** The pure decisions (pin, ancestry, convergence, restore, lock, upload root) are driven by a test file that asserts what must refuse AND what must stay silent. | `scripts/deploy*.test.sh` exists and runs green when invoked by the checker with `--run-tests`. |
| **R10** | **Guard on the raw command.** A bare provider ship command in an agent's shell is caught by `deploy_lane_guard.py` (fork-distributed, warn by default, `deploy.guard_mode: deny` to promote). | `.claude/hooks/deploy_lane_guard.py` present AND wired in `.claude/settings*.json`. |

Two things the standard deliberately does **not** require, and why: a provider-specific
rollback command (rollback is "re-pin at an older commit and run the lane with the logged
override", which R2 + R5 already govern), and a pre-deploy migration gate (that is
`STD-DEPLOY-001` §1B / the project's own release-set check — a different layer).

## Declaring a project

The checker reads `_bmad/bmm/config.yaml → deploy:`:

```yaml
deploy:
  method: manual_cli        # or push-auto, ci, none  — `none` ⇒ this project does not ship
  lane: scripts/deploy.sh   # the ONE script (R1); default scripts/deploy.sh
  guard_mode: warn          # deploy_lane_guard.py: warn (default) | deny
```

A project with a `deploy:` block that names no `method`, `platform` or `lane`, and no
`scripts/deploy.sh`, is **NOT DECLARED**: it has not said whether it ships. That is a repair
item for Claude (inspect the project, then declare `method: none` or build the lane) — not an
owner question, unless the inspection cannot tell.

## Verdicts

Per project: **MET** (every applicable requirement `verified`; `declared` rows are listed) ·
**GAPS** (any `missing`) · **N/A** (`method: none`) · **NOT DECLARED** · **UNKNOWN** (the
checker could not read the project). Fleet: `STANDARD MET` only when every declared-shipping
project is MET and nothing is NOT DECLARED.

`tools/bmad-health.py` folds this in: a fleet that is not `STANDARD MET` cannot be
`HEALTHY`; it reports `REPAIRING` with the projects named, and the repair is Claude's.

## Ceiling — read before trusting a green

- A probe proves a *pattern exists in a file*. It cannot prove the lane runs it in the right
  order, that the fingerprint covers every shipping path for that stack, or that a provider
  has not changed what its CLI uploads. `verified` means "the artefact shows the behaviour";
  it is not a deploy.
- `declared` rows are the lane author's word. They exist so a lane on an unfamiliar provider
  is assessable at all; a fleet that is MET only through `declared` rows is MET on trust, and
  the checker says so.
- R10 proves the guard file is present and *named in settings*; whether the settings file is
  the one this machine loads is a per-machine fact the checker cannot see.
- The standard governs the LANE. It cannot stop a session from bypassing the lane with a raw
  provider command outside a Claude shell, and does not try.

## Enforcement, honestly

| Tier | Mechanism | Class |
|---|---|---|
| Awareness | this doc, indexed in `STANDARDS.md`; the health line at session start | PROBABILISTIC |
| Awareness, first-priority | `~/.claude/hooks/deploy-lane-setup.sh` (SessionStart, global, installed from `custom/claude-global/hooks/` by `install-global-assets.sh`): when the project a session opens is GAPS / NOT DECLARED / UNKNOWN, injects a bounded "FIRST PRIORITY THIS SESSION" instruction naming the state, the missing rows, the reference, and the done-condition. Silent when MET / N/A / non-BMAD. Dated snooze ≤14 days, logged. | DETERMINISTIC delivery, PROBABILISTIC action |
| Gate | `deploy_lane_guard.py` on the raw ship command (PreToolUse; warn → deny per project) | DETERMINISTIC (delivery); action is denied only in `deny` mode |
| Gate | the lane's own refusals (R2, R4, R5-behind/diverged, R6) | DETERMINISTIC, inside the lane |
| Proof | R6 fingerprint · R5 read-back · the checker's `verified` rows | DETERMINISTIC over artefacts |
| Verification | `check-deploy-lane.py --all` · `bmad-health.py` | DETERMINISTIC |
| Correction | `bmad-health.py` reports REPAIRING with the project named; Claude repairs | PROBABILISTIC (Claude acts) |

Reference implementation: `cash-recovery/scripts/deploy.sh` (Railway; R1–R9 verified) with
`scripts/deploy-upload-root.test.sh` and `scripts/deploy-concurrency.test.sh`.

## Changelog

- **v1 (2026-09-04)** — created from the wrong-directory-upload finding. Ten requirements,
  checker, health integration, generic guard.
- **v1.1 (2026-09-05)** — first-priority SessionStart nudge (`deploy-lane-setup.sh`), owner
  instruction: "the next agent in the relevant directory will auto-setup as their first
  priority".
