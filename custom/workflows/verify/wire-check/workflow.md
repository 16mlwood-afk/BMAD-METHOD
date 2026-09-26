---
name: wire-check
description: 'Trace data flow end-to-end from a quick-dev handoff artifact. Catches loose wires, format mismatches, and dead counters between backend and frontend. Autonomously fixes all issues found.'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Wire Check Workflow

**Goal:** Take a quick-dev handoff artifact and verify that every data field the implementation touches flows correctly from backend generation through SSE/API transport to frontend state and UI rendering. Report loose wires — places where the chain breaks — then **autonomously fix all issues**, regardless of severity.

**Your Role:** You are the integration-layer specialist who doesn't trust any single layer. You read the chain end-to-end, watching for the subtle name/type/shape mismatches that pass type-check, survive unit tests, and only fail in the browser as a stuck "0" or a placeholder string. The whole job is the chain, not any one layer.

**Key Insight — Loose wires are silent.** They don't throw. They don't fail type-check. The producer sends `processedCount`, the consumer reads `processed_count`, the receiving side gets `undefined` — and `undefined` renders fine. Unit tests pass because each side tests against its own type. The only way to find these is to walk the chain field-by-field, top to bottom, comparing what each side names and shapes the same thing. That walk *is* wire-check. Nothing fancier; just refusing to skip a layer.

---

## CRITICAL RULES

- **The chain is the unit of correctness, not any single layer.** A green test on the producer side and a green test on the consumer side prove nothing if they're testing two different shapes. Verify producer-output against consumer-input at every junction.
- **Format mismatch is the canonical failure.** `camelCase` vs `snake_case`, `string` vs `number`, `Date` vs ISO string, `[]` vs `null` — these are the bugs this workflow catches. Be exact about casing and shape; "looks similar" is not equivalent.
- **Live the field, don't infer it.** When a server is running, capture the actual wire value at each stage. Static analysis hallucinates; live data doesn't. Type definitions are a hypothesis until the wire carries them.
- **Fix every issue, even tiny ones.** A known-loose wire left in place teaches future agents that loose wires are acceptable. Treat low-severity wires the same as high-severity ones: snip and reconnect.
- **Honest report first, fixes second.** Step-03 reports what's loose before step-04 fixes it. Don't rewrite the report after fixing — the original honesty is the record.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{handoff_path}`, `{wires}`, `{findings}`, `{baseline_commit}`
- Sequential progression through 6 phases: map → trace → report → fix → deliver → handoff

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input.** All menus, selection prompts, and approval gates are bypassed.
- **Make expert-level decisions automatically.** Choose the most productive option and proceed.
- **Fix ALL issues found** — including low-severity ones. Every loose, mismatched, or dead wire gets resolved.
- **Complete the full workflow end-to-end** without deferring any decision back to the user.

### Worktree Requirement

**Before editing any files**, enter a worktree via `EnterWorktree`. Step-04 actually rewires code — this is not a read-only audit — and a parallel session writing the same files would silently overwrite the repair. Follow the project's worktree rules from CLAUDE.md:

- Enter worktree before any file edits
- Use descriptive branch names: `fix/wire-check-{slug}`
- Deliver work to main before ending the session — a fix that never reaches `origin/main` is a wire still loose in production

### Input

The user provides a handoff artifact path (e.g., `_bmad-output/implementation-artifacts/handoff-screenshot-pipeline-2026-05-06.md`). If no path is provided, check `{implementation_artifacts}` for the most recent `handoff-*.md` file and confirm with the user.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/wire-check`

### Baseline Commit

Capture `{baseline_commit}` = `git rev-parse HEAD` at workflow start.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/wire-check/steps/step-01-map-wires.md` to begin the workflow.
