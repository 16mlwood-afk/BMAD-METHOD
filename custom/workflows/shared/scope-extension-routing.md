---
name: scope-extension-routing
contract_version: 1
description: 'Shared policy for ROUTING a scope-extension ask (add / deepen / extend) to the correct BMAD mechanism BEFORE the idea is discussed. On any "let''s add / deepen / extend X" the first job is to name the lane — design-elevation (settled surface, no new capability/source/model), correct-course (owner-added scope mid-work), or correct-course → PRD/Architecture → create-epics-and-stories (new table / new external source / schema-level model / architecture / PRD FR / epic-level capability) — and answer in a fixed 4-part shape (mechanism · lead lane + why · downstream artifacts · exact next step). Carries two guardrails: a MATERIALITY clause (a small clerk-writable field / single enum value is quick-spec + scope-register, NOT the capability lane) and a PREMISE-CHECK clause (before calling something a new source/capability, verify we do not already ingest or build it). The at-INTAKE counterpart of STD-ESCALATE-001 (which fires mid-flow when work changes class). Does NOT duplicate the upstream behavioural doctrine (the global scope-extension-bmad-router / answer-shape-and-autonomy memory) — it gives that doctrine a canonical, referenceable Home. PROBABILISTIC awareness tier: a prose answer has no artifact to gate on, so correctness is measured by a golden eval, not enforced by a hook.'
---

# Scope-Extension Routing — route the ask before you discuss it

**Why this exists.** When an owner says *"let's add / deepen / extend X"*, the failure this closes is answering the *idea* before routing the *work* — free-styling an edit, opening a brainstorm, or (worst) saying "there isn't one button" and stopping. The fork already owns purpose-built mechanisms for every shape of scope change; treating a scope-extension ask as an open conversation wastes them and loses scope provenance. This standard makes "which BMAD mechanism owns this, and what changes downstream" the **first** move, in a fixed answer shape a fresh, context-free agent reliably skips.

**Relationship to the doctrine (reference, do not duplicate).** The *behaviour* — route add/deepen/extend to a mechanism first, lead with a verdict, never hand back a menu — is owned upstream by the global `scope-extension-bmad-router` memory and the `answer-shape-and-autonomy` / `lead-dont-ask` doctrine. This standard is the **canonical Home** that doctrine points at: the single place the router, the two guardrails, and the answer shape are stated. When the doctrine and this standard appear to disagree, the doctrine is the source of truth; this is its referenceable shadow.

**Relationship to its sibling.** `escalation-on-class-change.md` (STD-ESCALATE-001) fires **mid-flow**, when work already underway outgrows its lane. This fires **at intake**, when the ask itself is a scope extension. Same spirit (name the lane, propose the gateway, proceed unless vetoed), different trigger.

---

## 1. Scope

Applies to any turn where the owner proposes **adding, deepening, or extending** a capability, surface, dataset, or model. The response MUST route to a mechanism (§2) and answer in the 4-part shape (§5) before discussing the idea's merits.

Does NOT apply to: pure bug reports, defect triage, or a straightforward implementation of already-planned scope (those are quick-dev / dev-story / maintenance-triage).

## 2. The router (pick the lane)

- **Pure improvement to an already-settled surface; NO new capability / data source / model** → **design-elevation**, then **design-handoff** if a candidate is selected.
- **Owner-added scope during active work, or a change that alters planned scope/artifacts** → **correct-course** first, with **scope-register** provenance.
- **New external source, persisted model, architecture decision, PRD FR, or epic-level capability** → **correct-course** leading into **PRD / Architecture**, then **create-epics-and-stories**.
- **Mixed** → say it is mixed, name **BOTH** lanes, and state which lane **LEADS**.

## 3. Materiality (guardrail on "persisted model")

Not every persisted field is the capability lane. A **small clerk-writable field or single new enum value** (e.g. a damage-cause tag) routes through **quick-spec + scope-register**, NOT correct-course → PRD/Architecture. The capability lane fires only on a **new table, a new external source, or a schema-level / structural model change**. Escalate a small field to the capability lane only if it grows a new status vocabulary/table or gets wired into a downstream money/claim decision.

## 4. Premise-check (guardrail on "new source")

Before routing something as a **new external source / new capability**, verify we do not **already ingest or build it**. A dimension already sitting in a table we pull — or a capability already shipped under an existing PRD FR / architecture decision — is a **design / analytics-lane** surfacing job, not a new-capability epic. A PASS requires checking the premise before escalating; "the owner called it new" is not proof it is new.

## 5. Required answer shape

1. Name the BMAD mechanism(s) explicitly.
2. State the lead lane and why (and if mixed, name BOTH lanes + which LEADS).
3. Name the downstream artifacts that will change (brief, PRD FR, architecture spine, epics/stories, scope-register entry, screen-review).
4. Recommend the exact next workflow step — do not leave it an open brainstorm.

**Banned:** "there isn't one button" / conversational framing UNLESS immediately followed by the exact lane(s) to run. Do not wait to be reminded of the workflow names — proactively name correct-course / design-elevation / create-epics-and-stories.

## 6. Enforcement (honest tier)

**PROBABILISTIC awareness.** This fires on natural-language intent and its "action" is the model composing a reply — there is no artifact for the harness to gate on, so no deterministic tier is possible. The surfaces that carry it are all awareness-tier:

- the global `scope-extension-bmad-router` memory one-liner (loads in every session, points Home here);
- a `bmad-scope-extension-router` **UserPromptSubmit** hook in the fork `hooks.json` template — additive/contextual only: on an add/deepen/extend match it injects this router as `additionalContext`; on no match it exits 0 silently. It **never gates, never fails a turn**, and false positives are an accepted cost (a little extra context on an unrelated turn);
- optionally, a per-project `## Scope-Extension Router` block in `CLAUDE.md` (not auto-synced — see §7).

Correctness is therefore **measured, not enforced.** The reference validation is a golden eval (`cash-recovery: evals/router-shape.md`) — 8 add/deepen/extend cases scored on lane + answer shape, replayed to detect drift. Validation to date: 3 sub-agent runs against that eval (6/8 true → 8/8 → 8/8 frozen-key), which exercised the memory-one-liner condition. The hook layer is not exercised by a sub-agent eval (sub-agents don't fire hooks) — validate it with one interactive session before relying on it.

## 7. Distribution notes

- The **doctrine** (this file) syncs to every project via the `_bmad/bmad-shared` lane; projects reference it BY PATH, never restate it (a disagreeing restatement is drift — log in `docs/fork-gaps.md`).
- The **hook** ships via the `hooks.json` template merge into project settings (fork-managed / gate-less repos; bespoke repos left intact).
- A project **CLAUDE.md** block is NOT auto-synced (the sync excludes CLAUDE.md). The doctrine is "fork official" via this standard + the memory + the hook; explicit per-project CLAUDE.md pointers, if ever wanted, are a single deliberate cross-repo pass, not part of the sync.
