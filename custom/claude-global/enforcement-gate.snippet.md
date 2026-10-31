## Enforcement Gate Before Trusting a Rule — CRITICAL

Before authoring, reviewing, or strengthening any mechanism meant to make a **context-free Claude agent** comply with a required behavior — a hook, a CLAUDE.md guardrail, a workflow/skill halt, a CI/pre-commit gate, an acknowledgment marker — **invoke the `enforcement-expert` skill first.** It owns the one axis that matters: **DETERMINISTIC** (the harness/tooling enforces — the model *can't* skip) vs **PROBABILISTIC** (the model must choose to comply). A non-negotiable rule (safety, correctness, irreversibility, money, partner-facing write, data loss) MUST have a deterministic tier; **prose alone is not enforcement.**

**Triggers:** "make Claude always X" · "enforce X" · "agents keep skipping X" · "how do I force the agent to read/run/not-do X" — or any time you catch yourself *trusting a rule that is currently only prose*. Do NOT let "we wrote it in CLAUDE.md" pass as "it's enforced": run the skill and label each proposed tier deterministic or probabilistic before claiming the behavior is guaranteed.

