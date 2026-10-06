---
name: 'step-01-triage'
description: 'Ground the ask, INFER convergent vs divergent, announce a one-line verdict + route, proceed unless vetoed'
---

# Step 1: Triage — Inferred, Not Asked

**Progress: Step 1 of 4** — Next: Route Out (convergent) OR Ground & Ideate (divergent)

## RULES — read before acting

- **GROUNDING GATE (intent autonomy boundary).** You must be able to name the `{ask_target}` — WHAT is being brainstormed about — from the input alone. If you cannot, HALT and ask exactly ONE question. Do NOT invent the target. Fires even under `autonomous_mode`.
- **The triage is INFERRED.** Never present a menu, never run discovery questions ("what outcomes are you hoping for?"). You classify; the user only confirms or vetoes.
- **One verdict line, then a REAL veto window.** In interactive mode the verdict line ENDS THE TURN — the user's reply is the veto window, and nothing downstream fires before it. Under `autonomous_mode: true` only, proceed in the same turn (silence-of-objection). Only an explicit veto changes the route.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Ground the ask

From the input, set `{ask}` (the user's words) and `{ask_target}` (the concrete thing it's about — a feature, surface, dataset, name, product direction). Repo context (CLAUDE.md, the named file/route, recent planning artifacts) may SHARPEN a target the input already names — it may never ESTABLISH one the input doesn't. Do not launch a broad investigation here.

If the input alone does not name `{ask_target}` → HALT: *"What's the brainstorm about — which feature, surface, or decision?"* (This is the only permitted question in this step.)

### 2. Classify — convergent or divergent

Infer `{triage_verdict}` from the shape of the ask:

| Signal | Verdict |
|--------|---------|
| A bounded choice: "which option", "A or B", "how should X work", "is Y worth it", "what's the risk of Z" | `convergent` (route: inline-deliberation) |
| The outcome is clearly a code change or spec ("brainstorm how to implement/fix/migrate X") | `convergent` (route: quick-spec) |
| ANY design-shaped want — "brainstorm the layout", "ideas to make this page feel better", "what would make X even better"; **and any IA/convergence/dashboard-shape ask — regroup a set of surfaces, partner-centric dashboard, override the existing IA** | `convergent` (route: design-router — it owns ALL further design-lane routing: depth, specialist, placement, **and the `topology` altitude / frame-first-halt handling for IA-override asks**; never resolve those here) |
| A genuinely open space: new directions, feature discovery, naming, roadmap shaping, "what could we build with X" — no bounded option set exists yet | `divergent` |

**Tiebreaker:** if a bounded option set can be written down in one sitting, it's convergent. Divergent is reserved for asks where enumerating the space IS the work. When genuinely torn, prefer `convergent` — routing to a decision costs less than ceremony, and the user's veto flips it.

### 3. Announce the verdict — and open the veto window

One line, verdict + route + veto affordance. Formats:

```
Convergent — this is a bounded decision. Taking it straight to {route_target} unless you say otherwise.
```
```
Divergent — genuinely open space. Running a quick grounded session (~20-30 ideas, converging to a shortlist) unless you say otherwise.
```

**Turn boundary (the veto window is real, not decorative):** in interactive mode, END THE TURN after the verdict line — do not load any next step in the same turn. The user's reply decides: any affirmative ("yes", "go", "y") → branch immediately, no re-deliberation, no re-confirmation; an explicit veto → flip to the vetoed-in route/branch and proceed. Under `autonomous_mode: true` only, skip the wait and branch in the same turn.

### 4. Branch

- `{triage_verdict}` = `convergent` → set `{route_target}` per the table above, then read fully and follow: `{installed_path}/steps/step-02-route-out.md`
- `{triage_verdict}` = `divergent` → read fully and follow: `{installed_path}/steps/step-03-ground-and-ideate.md`

---

## SUCCESS METRICS

- `{ask}`, `{ask_target}`, `{triage_verdict}` populated; `{route_target}` set when convergent
- Verdict announced in ONE line; zero menus, zero discovery questions
- Halted only if the target was ungroundable, with exactly one question

## FAILURE MODES

- Asking the user to classify ("is this open-ended or a decision?") — the classification is YOUR job
- Running the core brainstorming setup questionnaire — that's the ceremony this workflow exists to remove
- Re-confirming after the user already affirmed (affirmative-execution violation)
