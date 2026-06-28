---
name: 'step-01-intake'
description: 'Ground the design request — the surface (or system-wide) and the felt want — and halt if neither can be named from the input'
---

# Step 1: Intake & Ground

**Progress: Step 1 of 3** — Next: Classify (autonomous)

## RULES — read before acting

- **GROUNDING GATE (intent autonomy boundary).** You must be able to name a **target** (a surface/route, or `system-wide` for a policy change) AND the **felt want** from the input. **If EITHER cannot be named, HALT and ask** — do NOT invent the missing half. Fires even under `autonomous_mode`.
- This step only grounds. Do NOT classify or pick a specialist here — that is step-02.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Ground the target

From the input, resolve `{request_surface}`:
- A concrete route/surface ("the orders page", "/held", "the held drawer") → set it.
- A system-wide visual change ("make the whole app more corporate", "tighten density everywhere") → set `{request_surface}` = `system-wide`.
- Neither nameable → HALT: *"Which surface is this for (or is it a system-wide visual change)?"*

### 2. Ground the felt want

Capture `{felt_want}` — the user's want **in their words**, not a pre-classified verb. Examples: "redesign it", "tighten it", "add analytics", "it feels wrong but I don't know why", "make it more corporate", "what would make this better". If the input gives no want, HALT and ask. Do NOT guess the want — the want drives the depth axis in step-02, and a guessed want routes to the wrong specialist.

### 2.5 Prerequisite check — is the target's basis built or settled? (overrides autonomous_mode)

Naming a surface + want (above) is necessary but not sufficient: a target the user can *name* may not yet *exist* or be *decided*. Before routing to any build/handoff specialist, confirm `{request_surface}` resolves to EITHER an existing implementation (a matching route/component on disk) OR a settled spec (a PRD/architecture artifact fixing its data-model + intent).

If **neither** — no matching route/component on disk AND the feature is an open PRD Open-Question / unmet FR (or has no PRD coverage) — HALT and reroute; do NOT classify it as a design task: *"{request_surface} has no implementation and its data-model/intent is an open upstream decision — run `bmad-prd` → `bmad-architecture` to settle it, then return to the design lane."* (`system-wide` policy changes are exempt — no per-surface basis to ground.) Fires even under `autonomous_mode`; routing a fabrication is an intent violation.

### 3. Confirm and proceed

Confirm in one short line:

```
Routing: {felt_want} on {request_surface}. Classifying now.
```

Then read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-router/steps/step-02-classify.md`

---

## SUCCESS METRICS

- `{request_surface}` (a route or `system-wide`) and `{felt_want}` (user's words) both populated
- Halted cleanly if either could not be grounded from the input

## FAILURE MODES

- Inventing the surface or the want instead of halting (intent-autonomy violation)
- Pre-classifying the want into a verb/specialist here (that biases step-02's axis walk)
