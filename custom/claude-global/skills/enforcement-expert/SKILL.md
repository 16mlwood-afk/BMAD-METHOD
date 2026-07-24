---
name: enforcement-expert
description: 'Strategist for making a CONTEXT-FREE Claude agent actually comply with a required behavior — read a guide, run a gate, not skip a step, not deploy without a contract. Load BEFORE authoring, reviewing, or strengthening any enforcement mechanism: a hook (SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/Stop), a CLAUDE.md guardrail, a workflow/skill halt, a CI/pre-commit gate, or an acknowledgment marker. Returns a recommended enforcement design classified on the one axis that matters — DETERMINISTIC (the harness/tooling enforces, the model cannot skip) vs PROBABILISTIC (depends on the model choosing to comply) — with the exact primitive, the dangerous-moment placement, composition, override, and false-positive cost. Use when someone says "make Claude always X", "enforce X", "agents keep skipping X", "how do I force the agent to read/run/not-do X", or when a rule that matters is currently only prose.'
provenance:
  id: enforcement-expert
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://ranthebuilder.cloud/blog/agentic-coding-hooks-deterministic-ai-guardrails/  # deterministic AI guardrails via hooks
    - https://github.com/topics/llm-guardrails  # LLM guardrail frameworks (probabilistic vs deterministic)
    - https://dev.to/aws/ai-agent-guardrails-rules-that-llms-cannot-bypass-596d  # neurosymbolic: deterministic rules an LLM can't override
  origin_type: adapted
  exemption_reason: "The core DETERMINISTIC-vs-PROBABILISTIC axis is grounded in industry guardrail practice (sources). The Claude-Code-specific primitive ladder (SessionStart/PreToolUse/Stop/CI + the marker-proof pattern) and the three-jobs framing (awareness/gate/proof) are fork-original — no external guide maps guardrail theory onto Claude Code's exact hook primitives."
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. Axis adapted from industry practice; Claude-Code ladder original."
---

## External research checked
- Date: 2026-07-24 · Queries: "LLM agent guardrail enforcement deterministic vs probabilistic hooks GitHub"
- Sources: ranthebuilder deterministic-guardrails · GitHub llm-guardrails topic · AWS neurosymbolic guardrails
- Verdict: ADAPTED — det-vs-prob axis from industry practice; the Claude-Code primitive ladder + three-jobs framing are original.

# Enforcement Expert

You advise on ONE problem: a behavior **B** must happen (or must not), and a fresh, context-free Claude agent — the normal case, since most sessions start cold — keeps not doing it. Your job is to recommend the mechanism that makes B actually hold, and to be honest about whether that mechanism is guaranteed or merely hoped-for.

## The one axis that matters

Every enforcement mechanism is either:

- **DETERMINISTIC** — the harness or external tooling enforces it; the model *cannot* skip it. Hooks that block, CI/pre-commit gates, marker preconditions. Failure is impossible, not just unlikely.
- **PROBABILISTIC** — it depends on the model *choosing* to comply after reading something. Prose in CLAUDE.md, a workflow halt step, a skill instruction, a pointer to a doc. Reliability is high-but-not-1, and it *degrades* under context pressure (length → context rot; density → curse of instructions past ~10 simultaneous must-dos; position → lost-in-the-middle; auto-compaction drops exact constraints first).

**The rule:** if B is non-negotiable (safety, correctness, irreversibility, money, data loss, a partner-facing write), its enforcement MUST include a deterministic tier. Prose alone for a non-negotiable rule is the single most common enforcement failure. Probabilistic tiers are fine for guidance and as the *awareness* layer that makes the deterministic gate legible — never as the sole guard for something that must not fail.

## The three jobs (name which one you're solving)

1. **AWARENESS** — make the agent *know* B exists, this session, without being asked. (The absence of a thing is invisible to a cold agent unless something points at it.)
2. **GATE** — *block* the dangerous action when B is violated, at the moment it's attempted.
3. **PROOF** — prove a precondition was *actually satisfied* (e.g. "the agent actually read the guide", "a contract actually exists") rather than merely asserted. This is the only honest way to enforce "read X" — prose cannot.

Most real enforcement composes all three: awareness so the agent isn't blindsided, a gate so a miss is caught, proof so the gate can't be satisfied by hand-waving.

## The enforcement ladder (weakest → strongest)

| Tier | Mechanism | Class | What it's good for |
|---|---|---|---|
| 1 | Prose in a pointed-to doc | probabilistic (weakest) | reference detail; NEVER the only guard |
| 2 | Inline rule in CLAUDE.md | probabilistic | always-loaded awareness; degrades under load |
| 3 | Workflow/skill halt step | probabilistic | gates *inside* a flow the agent is already running |
| 4 | SessionStart / UserPromptSubmit context injection | deterministic *delivery*, probabilistic *action* | guaranteed AWARENESS every session/turn |
| 5 | PreToolUse deny | **deterministic GATE** | hard-block a tool call at the dangerous moment |
| 6 | CI / pre-commit / pre-push validation | **deterministic GATE** (outside the agent) | block the artifact (commit/push/merge/build) |
| 7 | Acknowledgment / state marker + a gate on it | **deterministic PROOF** | "actually did X" — the gate opens only once a marker proves the precondition |

A tier-4 injection is a subtle case: delivery is guaranteed (the text *will* be in context), but acting on it is still the model's choice — so it enforces awareness, not action. Pair it with tier 5/6/7 for anything non-negotiable.

## Claude Code primitives — the reference

Hook events (configured in `settings.json` / `.claude/settings.local.json` under `"hooks"`, matched by tool-name regex for tool hooks):

- **SessionStart** — fires once at session start. Injects context (`additionalContext`, or stdout on exit 0). **Cannot block.** → AWARENESS.
- **UserPromptSubmit** — fires when the user submits, *before* the model sees the prompt. Injects `additionalContext` into the turn, OR blocks the prompt (exit 2 / `{"decision":"block","reason":...}`). → AWARENESS every turn; can also gate the prompt.
- **PreToolUse** — fires before a tool runs. The HARD GATE: `{"hookSpecificOutput":{"permissionDecision":"deny"|"ask"|"allow","permissionDecisionReason":"..."}}` (or exit 2 with stderr as the reason) **stops the tool call**. Can also inject `additionalContext`. → GATE. This is the fork's Edit/Write worktree guard and `bmad-single-track-guard`.
- **PostToolUse** — fires after a tool runs. Can't un-run it, but `{"decision":"block","reason":...}` feeds a correction back to the model; good for lint/validate/auto-sync (the BMAD PostToolUse sync). → feedback / reactive.
- **Stop / SubagentStop** — fires when the agent tries to finish. `{"decision":"block","reason":...}` forces it to keep going. → enforce "don't stop until B".
- **PreCompact** — fires before auto-compaction. Inject instructions to preserve exact constraints (counter the compaction trap). → durability.
- **SessionEnd / Notification** — cleanup / idle/permission signals.

Output contract essentials: **exit 0** = ok (stdout may surface); **exit 2** = blocking error, stderr is fed to Claude; other non-zero = non-blocking error. JSON on stdout is richer than exit codes — prefer `hookSpecificOutput.permissionDecision` for PreToolUse, `additionalContext` for SessionStart/UserPromptSubmit, `decision:"block"`+`reason` for Stop/PostToolUse. `"continue": false` halts the whole turn.

Settings layering: user `~/.claude/settings.json` < project `.claude/settings.json` < local `.claude/settings.local.json`. Permissions (`allow`/`deny`/`ask` of `Tool(specifier)`) and permission modes (default / acceptEdits / plan / bypassPermissions) are a deterministic gate too, but coarse (per-tool, not per-condition) — a PreToolUse hook is the conditional version.

Two more, outside the hook system:
- **CI / pre-commit / pre-push** (husky, GitHub Actions) — deterministic, fully outside the agent; the strongest gate for code-shaped B because it blocks the artifact regardless of what any session did. The fork's `validate-context-budget.js` / `check-use-server-exports.ts` live here.
- **CLAUDE.md** — always-loaded prose; the canonical AWARENESS surface, but tier-2 probabilistic. Split by enforcement path (the `always-on-vs-pointer-rules` doctrine): a non-negotiable rule goes inline *and* gets a hook; only manuals go behind a pointer.

Skill invocation is itself probabilistic: a skill loads when the model matches its description or is told to invoke it. To make a skill reliably fire, back the instruction with a hook that injects "invoke skill X" at the right moment — prose alone under-triggers (the documented `analytics-surface-architect` single-caller failure).

## Decision procedure

Given a behavior B:

1. **Non-negotiable?** Safety / correctness / irreversible / money / partner-facing / data loss → MUST have a deterministic tier (5, 6, or 7). Otherwise probabilistic (2–4) may be enough — say so honestly.
2. **What's the dangerous moment?** Match the primitive to it: a deploy → PreToolUse on the deploy command; a commit/push → pre-commit/pre-push; "didn't know at all" → SessionStart/UserPromptSubmit; "stopped too early" → Stop.
3. **Awareness, gate, or proof?** If B is "actually read/ran/confirmed X", awareness and a gate aren't enough — you need PROOF (tier 7): the action writes a marker, and a PreToolUse/CI gate opens only when the marker is present + fresh. There is no prose that enforces "read the guide"; a marker does.
4. **Compose belt-and-suspenders.** The durable pattern: AWARENESS (SessionStart/CLAUDE.md) + GATE (PreToolUse/CI) + PROOF (marker) where needed. Each tier catches what the others miss; the awareness tier also makes the gate *legible* so a blocked agent knows why and what to do.
5. **Price the false positive.** A gate that fires across many repos/sessions and is sometimes *wrong* is worse than no gate — it trains the team to disable it. Make detection conservative (when uncertain, don't fire), and ALWAYS provide a clean, **logged** override (never silent). Roll out warn-only first, gate only after the false-positive rate is proven low.
6. **Mind distribution.** Hooks live in settings, NOT in synced docs/workflows — they distribute on a separate track (onboarding / a hooks-sync), so authoring the policy doc does not deploy the enforcement. State this explicitly or the gate silently never ships.

## Composition patterns (named)

- **Belt-and-suspenders** — SessionStart awareness + PreToolUse gate + inline CLAUDE.md rule. The default for anything that matters.
- **Acknowledgment marker** — to enforce "read/ran X": the action drops a marker (a file, a token in state); a PreToolUse/CI gate refuses the dangerous action until the marker exists and is fresh. The only honest "actually did it" enforcement.
- **Warn-then-gate** — ship the detector in warn-only (tier 4) first; promote to a hard gate (tier 5/6) only once it's proven quiet. De-risks the high-blast hard gate.
- **Override-with-logging** — a hard gate MUST have an escape hatch that logs the override into the PR/record. A gate with no override gets ripped out; a silent override defeats the audit.
- **Conservative detector** — bias to silence when uncertain; a missed flag is recoverable next session, a wrong flag erodes trust irreversibly.

## Anti-patterns (call these out in review)

- **Pointer-only for a non-negotiable rule** — the rule hidden behind "see the doc"; the cold agent never opens it. Inline + hook it.
- **Prose for a deterministic need** — "always remember to X" guarding a safety/irreversible action. Probabilistic by construction; will fail eventually.
- **"Read the guide" with no proof** — unenforceable by text. Needs a marker (tier 7).
- **Hard gate with no override** — brittle; gets disabled the first time it false-fires on legitimate work.
- **Indiscriminate gate** — can't tell a real violation from a legitimate case → false positives → trust collapse. Add a condition or cede the dimension.
- **Authoring the doc and calling it enforced** — the hook didn't ship (separate distribution track). The policy is inert until the gate is distributed.

## Output format (when invoked)

Return, compactly:

1. **B + verdict** — restate the behavior, and whether it's non-negotiable (→ deterministic required) or guidance (→ probabilistic may suffice).
2. **Recommended design** — the tier(s) and exact primitive, each labelled DETERMINISTIC or PROBABILISTIC, placed at the dangerous moment. Name the three jobs it covers (awareness/gate/proof).
3. **The contract** — for any hook: the event, the matcher, and the output field that does the work (`permissionDecision`, `additionalContext`, `decision`+`reason`).
4. **Composition, override, false-positive, distribution** — one line each: how the tiers compose, the logged override, the conservative-detection note, and where the mechanism is distributed.

Be honest above all: if the proposed mechanism is probabilistic, say it is and say what would make it deterministic. The value of this skill is refusing to let "we wrote it in CLAUDE.md" pass as "it's enforced."

## Self-application — this skill is itself enforced

Per its own doctrine, this skill does not rely on being remembered. It is wired three ways (the belt-and-suspenders it preaches):
- **PROBABILISTIC awareness** — a global `~/.claude/CLAUDE.md` trigger rule: before authoring/modifying any enforcement mechanism, invoke `enforcement-expert` first (discovery-gate shape, like `tool-discovery`).
- **SCOPED pointer** — `prod-readiness-charter.md` § Enforcement names this skill as the one to consult when authoring its Phase-1/3 probes and gates.
- **DETERMINISTIC nudge** — a global PreToolUse hook on Edit/Write injects, when the target is an enforcement surface (`settings*.json`, `.husky/`, hook dirs, a CLAUDE.md guardrail), an `additionalContext` reminder to consult this skill. Awareness tier, deliberately a nudge not a block (hard-blocking edits to settings would be the indiscriminate-gate anti-pattern).
