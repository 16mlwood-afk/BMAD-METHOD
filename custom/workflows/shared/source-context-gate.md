---
name: source-context-gate
contract_version: 1
description: 'Context-before-conclusion rule for CONFIGURATION, WORKFLOW, POLICY, HOOK, SCHEMA and ROUTE-BEHAVIOUR investigations: a search hit is a LEAD, never a finding. Before claiming a file/rule/config CAUSES behaviour, establish the full governing block, every conditional branch / exception / mode flag / override / precedence rule, whether that condition is actually enabled in the live target, and whether the behaviour is observed in execution or test evidence — then classify it active / inactive / overridden / dead / documentation-only / ambiguous. Shared behaviour is never changed on phrase matching alone. Carries a required per-claim evidence block; a missing field makes the result a HYPOTHESIS, not a defect and not a change request. The INVESTIGATION-side sibling of STD-DIAG-001 (which governs VERIFICATION). Consumed by the verify/* audits and any audit/change plan via STD-DIGEST-001 §2a. Deliberately NO broad stop hook (owner instruction 2026-08-31) — the levers are the required evidence block, the golden suite at evals/source-context-gate.md, and the grep-origin review trigger.'
---

# Source-Context Gate — a search hit is a lead, never a finding

**Why this exists.** `grep` answers *"where does this string appear?"*. It does not answer *"does this rule fire?"* — and the distance between those two questions is where a whole class of confident, wrong, shared-infrastructure edits comes from. The matched line is usually real; what is missing is the branch three lines below it that exempts the case, the mode flag that skips it, the override that supersedes it, or the fact that the whole block is a comment.

**The owner-named defect (2026-08-31).** An audit of shared BMAD workflow prose alleged two behavioural defects — option menus that stall autonomous execution — on the strength of phrase matches. Both were disproved: the menus carry an explicit `autonomous_mode` bypass, and a sibling workflow names "presenting an option menu when `autonomous_mode` is true" as an anti-pattern of its own. The proposed edits would have written a contradiction into prose that syncs to every project. Owner ruling: *"You are sometimes treating a grep/search hit as proof of live behaviour before reading the governing context, exceptions, precedence rules, and live configuration. This is not a one-off workflow mistake. It is a reusable investigation-method defect."*

**Relationship to STD-DIAG-001.** The diagnostics gate governs **verification** — a claim about a *result* ("tests pass", "build green") is RED until a re-run proves it. This gate governs **investigation** — a claim about a *cause* ("this rule makes it behave that way") is a HYPOTHESIS until the governing context proves it. Same discipline at opposite ends of the work: there, prove before you assert; here, read before you conclude.

---

## 1. Scope

Applies to any investigation whose conclusion is a claim about **behaviour caused by a file, rule, or setting**:

- configuration (env vars, settings files, package scripts, CI wiring)
- workflow / skill / policy prose that instructs an agent
- hooks and gates (present vs wired vs firing)
- schemas and cross-boundary contracts
- route, menu, mode-flag and precedence behaviour

Does NOT apply to: ordinary code navigation, locating a symbol, reading a file you are about to edit for its own sake, or a claim about a *result* (that is STD-DIAG-001).

---

## 2. The rule

**A search hit is a lead, never a finding.** Before claiming that a file, rule, or configuration **causes** behaviour, establish all five:

1. **The full governing block** around the matched text — not the line, the construct that owns it.
2. **Any conditional branch, exception, mode flag, override, or precedence rule** that applies to it.
3. **Whether the relevant condition is actually enabled** in the live target / configuration.
4. **Whether the behaviour is observed** in execution, test evidence, or a reproducible path.
5. **Which of six states it is in** — the classification IS the finding, not the match:

| Verdict | Means |
|---|---|
| `active` | The behaviour fires in the live target, on the path under audit. |
| `inactive` | The construct exists but its condition is not met (mode flag, guard, unreached branch). |
| `overridden` | It fires, but a higher-precedence source supersedes its effect. |
| `dead` | Legacy or unreachable — nothing invokes it, or it was superseded and left in place. |
| `documentation-only` | The phrase describes, cites, or plans behaviour; it does not instruct it. |
| `ambiguous` | Live state could not be established. **Stays unresolved — it is not a defect.** |

**Do not change shared behaviour on phrase matching alone.** "Shared" means anything that reaches another project, another session, or production: the fork's `custom/workflows/**` and `shared/**`, hooks, CI wiring, schemas, and any synced doctrine.

**`ambiguous` is a complete answer.** Forcing an unreadable case into `active` to make the audit productive is this gate's failure mode in the other direction. Report it unresolved and name what would resolve it.

---

## 3. The required evidence block — one per claimed defect

Every claimed behavioural defect carries this block. Emit it as given; do not compress it into prose.

```text
Claim:
Matched text:
Governing source block:
Exceptions/precedence checked:
Live configuration/state checked:
Observed execution or test evidence:
Verdict: active / inactive / overridden / dead / ambiguous
Proposed action:
```

**If any field is missing, the result is a HYPOTHESIS — not a defect and not a change request.** A hypothesis may be reported, and it may justify further investigation. It may not justify an edit to shared behaviour, and it must not be written into a register, digest, or status line in the grammar of a confirmed finding.

Field notes:

- **Governing source block** — quote or cite `path:line-range` for the construct, not for the match.
- **Exceptions/precedence checked** — name what you looked for and did *not* find. "None found — checked for a mode-flag guard, a sibling override, and a superseding standard" is a pass. Silence is not.
- **Live configuration/state checked** — the actual read: the settings entry, the flag value, the `npm test` line, the deployed revision. *Existence is not execution* — a wired hook with no file, a linter that ships warn-only, and a standard cited before its Home was written have each read as "working" from configuration alone.
- **Observed execution or test evidence** — a run, a test, or a named reproducible path. `none — static only` is an allowed value, and it drives the verdict toward `ambiguous` rather than toward `active`.

---

## 4. The review trigger

**When a proposed change originates in grep, search output, or a phrase match, one source-context review is required before shared infrastructure may be changed.** The review is the §3 block for each claim, produced *before* the edit — not reconstructed after it.

The trigger is the **origin of the proposal**, not its size. A one-line prose edit to a synced workflow is a shared-infrastructure change; a fifty-line refactor of a project-local script is not.

---

## 5. Enforcement honesty

**PROBABILISTIC, deliberately.** A broad Stop hook that interrupts ordinary work was considered and **declined** (owner instruction, 2026-08-31): *"do not build a broad stop hook that interrupts ordinary work."* "Is this conclusion grounded in its governing context?" is an unenforceable semantic classification, and a matcher keyed on grep usage would fire on nearly every engineering turn — the indiscriminate-detector anti-pattern that gets a hook switched off. Do not build one.

The three real levers, in order of strength:

1. **The required evidence block** in audit and change plans (§3), carried into the audit lane by `shared/behavior-update-digest.md` (STD-DIGEST-001 §2a) — an artifact-shaped requirement, which is the only kind that survives a cold session.
2. **The golden suite** — `evals/source-context-gate.md`, seven cases spanning all six verdicts, including one that must remain `ambiguous` and one live unguarded behaviour that must NOT be softened into a false negative. Replay it on any change to §2 or §3. Verdict correctness is **measured** there, never gated.
3. **The origin trigger** (§4) as a review habit at the moment of proposing a shared edit.

A deterministic template lever is available if adoption proves quiet and misses recur: a `check:srcctx` sibling of `check:digest` that flags an audit-lane step emitting defect language with no STD-SRCCTX-001 reference. It is **not built**; do not describe this standard as gated.

---

## 6. How a step references this

Mirror the STD-DIGEST-001 / STD-CLOSEOUT-001 convention — reference, never restate.

- Frontmatter `description:` — "… Claimed behavioural defects carry the source-context evidence block per `shared/source-context-gate.md` (STD-SRCCTX-001)."
- Body, at the finding/claim section — one line: "Before a match becomes a finding, apply `shared/source-context-gate.md` (STD-SRCCTX-001): establish the governing block, exceptions and precedence, live state, and observed evidence, then classify. A block with a missing field is a hypothesis, not a defect."

Do not duplicate the eight-field block into each step.
