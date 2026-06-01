# analytics-surface-architect

A [Claude](https://claude.com/claude-code) **skill** that decides *how* a dataset should be presented — which analytics shape fits the question a user is actually trying to answer, why, and what was rejected.

It exists to break one stubborn failure mode: analytics surfaces all coming back looking the same — a coverage strip, a row of sparklines, a few KPI tiles — regardless of what the user needed to learn. The skill starts from the **question, not the data**; it refuses to default to a time-series chart just because the data has dates; and it returns a written, auditable rationale.

## What it does

Given a dataset shape and the user's question, it returns a structured decision:

```
archetype:        coverage
user_question:    "which weeks are we missing statements for, and in which region?"
grounding:
  data_dimension: "per-week × per-region completeness"
  user_question:  "find the gaps that need chasing"
candidates:
  - { archetype: coverage, verdict: chosen,    why: "the gaps ARE the content" }
  - { archetype: trend,    verdict: rejected,  why: "weeks exist, but the job isn't reading movement" }
  - { archetype: ranking,  verdict: secondary, why: "region with most gaps, kept subordinate" }
winner_reason:    "coverage — data carries per-week×region completeness; the question is 'what's missing'"
secondary:        ranking
time_present_check: "time is present, but the job is completeness not movement → NOT a trend job"
drill_map:
  - { element: "gap mark",   drill_target: "/statements?week=…&region=…" }
  - { element: "region row", drill_target: "/statements?region=… (sorted by gap count)" }
prohibited:       [ "no trend strip of small multiples", "no KPI/stat-card row" ]
```

It picks from **eight archetypes** — `trend`, `distribution`, `composition`, `ranking`, `coverage`, `flow`, `single-metric`, `correlation` — each defined by the question it answers, the form that answers it fastest, its drill path, and what to avoid.

## What it deliberately does *not* do

- **Visual treatment** (color, type, spacing, component chrome) — that's your design system's job. This skill picks the *shape*; you render it.
- **Whether a screen needs analytics at all** — an upstream product decision. If no archetype honestly fits, it says so.
- **Backend / schema / data-pipeline work.**

## Install

Drop the skill into your Claude skills directory:

```
.claude/skills/analytics-surface-architect/SKILL.md
```

(project-level) or `~/.claude/skills/analytics-surface-architect/SKILL.md` (user-level). Claude loads it automatically when a request matches its description — e.g. "what shape should this data be?", "audit this analytics band", "pick a chart for this dataset". It has three modes: **select** (default), **critique**, **explain**.

## Modes

| Mode | Use it for |
|---|---|
| `select` | Choose the shape for a new or unknown surface. Returns the decision object above. |
| `critique` | Check an existing/proposed surface — is the shape right for the question? Flags trend-on-a-coverage-question, undrillable elements, KPI-card walls. |
| `explain` | Teach which archetype fits and why — onboarding, design reviews. |

## Why a separate skill

Selecting the right analytics shape is a *reasoning* task with a strong wrong-default (time in the data → reach for a line chart). Isolating it as one skill means the decision is made the same way every time, is grounded in both the data and the question, and leaves a rationale you can challenge — rather than being re-improvised on every screen.

## License

[MIT](./LICENSE) © 2026 Mason Wood. Use it, fork it, ship it — just keep the copyright notice.

## Provenance

Extracted and decoupled from an internal design-workflow toolkit, where the same selection logic is invoked during design handoff and enforced at review time. This standalone copy inlines the archetype taxonomy and removes all toolkit-specific references so it stands on its own.
