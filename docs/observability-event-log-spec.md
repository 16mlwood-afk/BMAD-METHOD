---
title: Workflow Observability Event Log — one-page spec
description: A tiny, append-only JSONL log of workflow runs so orchestrate-workflows and maintenance-triage can produce workflow-health reports from data instead of memory or hand-kept notes.
status: proposed (2026-06-27)
---

# Workflow Observability Event Log — spec

## Problem

Today every workflow run, halt, override, and escalation is invisible the moment the
session ends. `orchestrate-workflows` audits the ecosystem **point-in-time**; `fork-gaps.md`
only captures what an agent *thinks* to write down. There is no answer to "how often does
quick-dev halt at step N", "which gate escalates most", "are humans overriding the
ask-vs-decide default". This spec adds the smallest durable substrate that turns those
point-in-time audits into trend-aware ones — **not** a dashboard.

## The artifact

**File:** `~/.claude/logs/workflow-events.jsonl` — append-only, one JSON object per line,
never rewritten. Global (not per-project): it spans fork workflows *and* personal global
skills like `maintenance-session`. Rotated by month if it grows (`workflow-events-YYYY-MM.jsonl`).

**One line per run:**

```json
{
  "ts": "2026-06-27T11:40:00Z",       // ISO-8601 UTC
  "workflow": "quick-dev",            // workflow or skill name
  "mode": "implement",                // sub-mode if the flow has one, else null
  "outcome": "halted_at_step",        // completed | halted_at_step | escalated | vetoed
  "step": "step-04-self-check",       // populated when outcome=halted_at_step, else null
  "key_gate": "blast-radius_blocked", // the gate that fired, if any (else null)
  "override": false,                  // human overrode the gate/default this run
  "bhv_id": "BHV-2026-06-27-04",      // set iff this run wrote a BHV changelog entry
  "project": "inbound-flow",          // cwd-derived project slug (canonicalized, not worktree)
  "session": "bf48b230"               // short session id, for correlating multi-run sessions
}
```

Fields are deliberately flat and low-cardinality so `jq`/`grep` aggregation is trivial.
`outcome` and `key_gate` are **closed vocabularies** — extend them in this spec, not ad hoc,
so reports don't fragment (the same lesson as the data-quality controlled-vocabulary audits).

> **`project` slug — reuse the onboarding-v2 canonicalization.** A run inside a worktree must
> log the *canonical* project slug, not the worktree-cwd slug. Reuse the same
> `git --git-common-dir → main checkout → slug` move that `onboard-project.sh` v2 uses, or this
> log reproduces the worktree-slug-leak bug already open in `fork-gaps.md`.

### Closed vocabularies (v1)

- `outcome`: `completed` · `halted_at_step` · `escalated` (handed to a human/another flow) · `vetoed` (human said no at a fork).
- `key_gate` (nullable): `blast-radius_blocked` · `ask-vs-decide_escalated` · `design_gateway_reroute` · `use-server_blocked` · `context-budget_exceeded` · `worktree_required` · `null`.

## The write path — the crux (and the enforcement honesty)

A log is only as good as how reliably lines get written, and **prose in each workflow ("append
a line to the event log at the end") is the weakest tier** — it rides on every cold agent
remembering, degrades under context pressure (context rot / curse of instructions), and silently
under-fires. Per the `enforcement-expert` axis, the reliable writer is **deterministic**, not
probabilistic:

- **Primary (deterministic):** a `Stop` / `SubagentStop` hook — sibling of the existing
  fork-gaps reflection hook — that, when a workflow/skill ran this session, appends one line
  from session state. The hook owns the write; no workflow has to remember. It infers
  `workflow`/`mode`/`outcome` from the flow's own halt/handoff markers and the transcript.
- **Secondary (probabilistic, optional):** a workflow may emit a richer line itself at a
  natural checkpoint (it knows its own `step`/`key_gate` best). The hook deduplicates by
  `(session, workflow, ts-bucket)` so a self-emitted line isn't double-counted.
- **Append-only + conservative:** never block on a write failure (observability must not
  gate real work), never rewrite history, and when the hook is unsure what happened, write
  `outcome: "completed"` rather than guessing a halt — a missed nuance is recoverable, a
  wrong alarm erodes trust.

**Distribution caveat (the real constraint).** The hook lives in `settings.json`, which
distributes on the **hooks/onboarding track, not the workflow-sync track** — so shipping this
spec does *not* ship the writer. This is the same unresolved gap as the top open `fork-gaps.md`
entry (*deterministic enforcement gates have no fork-managed distribution/activation path*). The
event-log writer should ride that fix when it lands — `sync-bmad-workflows.sh` portable-script
rail + `onboard-project.sh` hook provisioning — rather than be hand-wired per repo.

## The readers (the payoff)

No new reporting tool — extend two that already exist:

- **`orchestrate-workflows`** — already the "workflow ecosystem tuner". Add a read of the last
  N days of the log to ground its health audit in frequencies: most-halted step, noisiest gate,
  override rate, flows that never run (dead) vs flows that always escalate (mis-scoped). Turns
  "I think quick-dev is fine" into "quick-dev halted at self-check 4× this week."
- **`maintenance-triage`** — already takes telemetry/observations and routes. Feed it the log so
  a spike in one `key_gate` becomes a triageable signal, not something Mason has to notice.

Both readers stay read-only over the log; neither writes it (the hook does).

## Scope guard (what this is NOT)

- Not a live dashboard, not metrics infra, not per-tool tracing — one line per *run*.
- Not a new standing audit obligation — it *feeds* existing audits, it doesn't add a step Mason runs.
- Not a hard gate — nothing blocks on the log; it is pure observability.

## Smallest shippable slice

1. Define the file + v1 schema above (this doc).
2. Write the `Stop`-hook writer (deterministic primary) and wire it into the global settings layer.
3. Add a ~10-line "read the log" section to `orchestrate-workflows` (one reader proves the loop).
4. Soak for a week; only then extend vocab / add the `maintenance-triage` reader.

Steps 2–3 are the real build; step 1 is this page. Recommend slicing it that way so the
writer and one reader prove value before any vocabulary expansion.
