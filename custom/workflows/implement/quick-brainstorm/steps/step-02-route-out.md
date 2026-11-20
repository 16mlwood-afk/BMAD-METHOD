---
name: 'step-02-route-out'
description: 'Convergent branch: emit the exact handoff to the owning lane, then STOP — no ideation machinery runs'
---

# Step 2: Route Out (Convergent Branch — Terminal)

**Progress: Step 2 of 4 (terminal on this branch)** — Steps 3-4 do NOT run.

## RULES — read before acting

- **This step DELEGATES; it never does the downstream work.** For quick-spec / design-router routes, emit the handoff — do not start speccing or designing here.
- **Exception — `inline-deliberation` IS done here.** A pure judgment call needs no other workflow; answer it now under answer-shape.
- **No menus.** One route was already decided in step-01; emit it. Alternatives get at most one secondary line.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Execute the route

Per `{route_target}`:

| Route | Action |
|-------|--------|
| `inline-deliberation` | Answer the question NOW, answer-shape compliant: clear verdict first → 2-4 weighted bullets → ONE biased recommendation → at most one follow-up question. Ground claims in the repo (read the relevant files) before asserting. |
| `quick-spec` | Set `{handoff_command}` = invoke `quick-spec` with `{ask}` + `{ask_target}` as the feature description. |
| `design-router` | Set `{handoff_command}` = invoke `design-router` carrying the surface (`{ask_target}`) and the felt want (`{ask}`, user's words). design-router owns ALL further design-lane routing — depth, specialist, placement. Do not pre-pick any of them. |

### 2. Emit and stop

The veto window already happened — step-01 ended the turn on the verdict line and the user affirmed (or `autonomous_mode` is on). So invoke directly, without re-asking — per `answer-shape-and-autonomy`, an affirmed route is executed, not re-offered:

```
Routing {ask_target} to {route_target}: {one-clause reason}.
```

Then invoke `{handoff_command}`. For `inline-deliberation`, the answer itself is the deliverable — finish after delivering it.

**No session artifact is written on this branch** — a routing decision is one line of chat, not a document. The downstream workflow owns its own artifacts.

---

## SUCCESS METRICS

- Exactly one route executed; steps 3-4 never loaded
- Inline deliberations answered verdict-first with one biased recommendation
- Non-inline routes invoked (not just suggested) with `{ask}` context carried over

## FAILURE MODES

- Doing the specialist's work inline ("here's a quick spec...") instead of invoking it
- Emitting the handoff as a question ("shall I run quick-spec?") — the step-01 turn boundary already provided the veto window
- Pre-picking a design specialist (design-handoff, design-elevation, placement) — that is design-router's decision
- Writing a session document for a routing decision
