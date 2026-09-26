---
name: STANDARDS
description: 'The canon — the single index of every shared standard a BMAD-managed project follows (deploy, delivery, webhook boundaries, diagnostics, worktree/parallel-session safety, prod-readiness, AND memory discipline). One place to answer "what is the canonical way to do X?". Each standard lives once at its Home, syncs to projects, and is referenced BY PATH — never restated. Machine-parsable: each synced standard has an ID/Version/Breaking/Home/Applies block that the SessionStart drift check (check-standards-drift.sh) scans.'
contract_version: 1
---

# STANDARDS — the canon

The single index of the standards every BMAD-managed project follows. If you're asking *"what is the canonical way to do X?"*, the answer is one of the blocks below — open its **Home** doc.

## How to use this

- **Starting a deploy flow?** Check `STD-DEPLOY-001` (and `STD-PRODREADY-001` if the project isn't deploy-ready yet) before writing anything. **Building or changing the thing that deploys?** `STD-DEPLOY-002` is what it must be able to prove — run `python3 tools/check-deploy-lane.py --project .` before calling a lane done.
- **Changing how memory is written/read?** See the memory section below (`memory-library-discipline` / `memory-retrieval-policy`).
- **Touching a webhook boundary?** `STD-WEBHOOK-001` is the contract of record.
- **The Home doc is the source of truth.** A project's `CLAUDE.md` only *points at* a standard; a restatement that disagrees is drift — log it in `docs/fork-gaps.md` and fix it. Reference by path, never copy (`cash-recovery` is the reference shape).
- **Drift is checked automatically.** `check-standards-drift.sh` (SessionStart, WARN-only) compares this canonical against the copy synced into the current project. The synced copy IS the project's declaration of "what I last pulled" — no lock file or CLAUDE.md block to maintain.

## The standards (machine-parsable index)

Each block is scanned line-by-line: `ID` → `Version` → `Breaking` → `Home` → `Applies`, each on its own line. Keep it boring — no nesting, no inline prose on those lines. `Breaking` is the latest version's nature (`yes` = a behavioral shift a consumer could violate; `no` = a safe/clarifying edit safe to auto-upgrade).

### deployment lifecycle

deployment-to-prod — the post-merge deploy contract (admin-merge rules, dirty-path filters, dep auto-heal, exit-code grammar).
ID: STD-DEPLOY-001
Version: v1
Breaking: no
Home: shared/deployment-to-prod.md
Applies: all

deploy-lane-standard — the minimum a project's DEPLOY LANE must prove before a deploy is called verified (ten requirements with mechanical probes; checker `tools/check-deploy-lane.py`; feeds `bmad-health.py`). The layer inside STD-DEPLOY-001.
ID: STD-DEPLOY-002
Version: v1
Breaking: no
Home: shared/deploy-lane-standard.md
Applies: all

delivery-to-main — getting an artifact from local disk to origin/<default-branch> so external consumers can read it.
ID: STD-DELIVERY-001
Version: v1
Breaking: no
Home: shared/delivery-to-main.md
Applies: all

prod-readiness-charter — getting a project READY to deploy (the 3 states, detection, enforcement); the layer above the deploy contract.
ID: STD-PRODREADY-001
Version: v1
Breaking: no
Home: shared/prod-readiness-charter.md
Applies: all

### boundaries & contracts

webhook-contract-charter — every webhook boundary (sender-strict/receiver-lenient rollout, breaking-change taxonomy, per-boundary template).
ID: STD-WEBHOOK-001
Version: v1
Breaking: no
Home: shared/webhook-contract-charter.md
Applies: all

### implementation safety

diagnostics-gate — prove-don't-assert verification gate (a new diagnostic means RED until a clean re-run proves green).
ID: STD-DIAG-001
Version: v1
Breaking: no
Home: shared/diagnostics-gate.md
Applies: all

source-context-gate — context-before-conclusion rule for configuration / workflow / policy / hook / schema / route-behaviour investigations: a search hit is a LEAD, never a finding. Establish the governing block, exceptions and precedence, live enablement, and observed execution before claiming a file or rule CAUSES behaviour; then classify active / inactive / overridden / dead / documentation-only / ambiguous. Shared behaviour is never changed on phrase matching alone, and a claim missing any field of the eight-field evidence block is a HYPOTHESIS, not a defect. Investigation-side sibling of STD-DIAG-001 (verification). Golden suite: evals/source-context-gate.md.
ID: STD-SRCCTX-001
Version: v1
Breaking: no
Home: shared/source-context-gate.md
Applies: all

parallel-sessions — concurrent-session protocol (worktree-before-edit, integrate-advancing-main, named collision classes, story claim+reconcile).
ID: STD-PARALLEL-001
Version: v1
Breaking: no
Home: shared/parallel-sessions.md
Applies: all

worktree-portability — artifact paths resolve to the worktree root, not the main checkout.
ID: STD-WORKTREE-001
Version: v1
Breaking: no
Home: shared/worktree-portability.md
Applies: all

wave-orchestration — fan-out-in-waves protocol for implement/review/create workflows (additive to solo parallel dev).
ID: STD-WAVE-001
Version: v1
Breaking: no
Home: shared/wave-orchestration.md
Applies: all

detect-stack — shared utility: identify the project tech stack.
ID: STD-STACK-001
Version: v1
Breaking: no
Home: shared/detect-stack.md
Applies: all

hook-activation — git-hook gates must be DISTRIBUTED and ACTIVATED by the fork: sync-bmad-workflows.sh + onboard-project.sh set core.hooksPath=.githooks (tracked dispatchers reading .githooks/gates.conf) idempotently, so a synced gate is reliably wired, not silently off. A SessionStart liveness probe warns on un-activated/conflicted repos. Local hook = best-effort gate (bypassable via --no-verify); the fail-closed CI tier is deferred. husky retired in favor of .githooks (worktree-safe).
ID: STD-HOOKACTIVATE-001
Version: v1
Breaking: no
Home: shared/hook-activation-standard.md
Applies: all

### workflow behavior & routing

escalation-on-class-change — when work changes class mid-flow (scope outgrew the unit / missing keystone / planning-not-execution / wrong lane), state it, name the BMAD-default gateway, propose it, and proceed unless vetoed — never a numbered menu, never silent wrong-lane continuation. Implemented by dev-story; conformed-to by correct-course / design-router / maintenance-triage / design-elevation / quick-dev.
ID: STD-ESCALATE-001
Version: v1
Breaking: no
Home: shared/escalation-on-class-change.md
Applies: all

scope-extension-routing — route a scope-extension ask (add / deepen / extend) to the correct BMAD mechanism BEFORE discussing the idea, and answer in a fixed 4-part shape (mechanism · lead lane + why · downstream artifacts · exact next step). Lanes: design-elevation (settled surface, no new capability/source/model) · correct-course + scope-register (owner-added scope mid-work) · correct-course → PRD/Architecture → create-epics-and-stories (new table / new external source / schema-level model / architecture / PRD FR / epic-level capability); mixed → name BOTH + which LEADS. Two guardrails: MATERIALITY (a small clerk-writable field / single enum value is quick-spec + scope-register, NOT the capability lane) and PREMISE-CHECK (verify we don't already ingest/build a claimed "new source" before escalating). The at-INTAKE counterpart of STD-ESCALATE-001 (mid-flow class change). References (does not duplicate) the upstream `scope-extension-bmad-router` / `answer-shape-and-autonomy` memory — it is that doctrine's canonical Home. PROBABILISTIC awareness tier (a prose answer has no artifact to gate on): carried by the global memory one-liner + a `bmad-scope-extension-router` UserPromptSubmit hook (additive/contextual, never gates) + optional per-project CLAUDE.md pointer (not auto-synced). Correctness is MEASURED by a golden eval (cash-recovery: `evals/router-shape.md`; validation to date 6/8→8/8→8/8), not enforced.
ID: STD-SCOPEROUTE-001
Version: v1
Breaking: no
Home: shared/scope-extension-routing.md
Applies: all

scope-register-routing — what a scope-register ROW must carry so registered scope cannot sit inert. Every row declares a `route` from a closed enum (`R1-capability` / `R2-bounded-local` / `R3-design` / `R4-operational-milestone` / `R5-parked`) plus a `next_artifact` naming the ONE artifact that makes it actionable — first story file at `ready-for-dev` (R1) · quick-spec (R2) · active provenance-valid design brief (R3) · owned milestone block (R4) — or, for `R5-parked` only, a complete `activation` (owner + observable trigger + why-not-now). Carries the ACTIONABILITY LADDER: a register row (REGISTERED), a sprint-change-proposal (PROPOSED — owner decision only), an epic in `epics.md`, and a `backlog` story line are all DESCRIBED, never ACTIONED; SHAPED is the state a different workflow can consume cold without a human re-deciding scope. Adds the R4 milestone-block vocabulary the sprint-status enums lacked (milestone status + per-item `owner: operator|agent|external`). The WRITE-side counterpart of STD-SCOPEROUTE-001 (which routes the ASK at intake; this makes the resulting ROW carry that route as a field) and the scope-level instantiation of STD-COMPLETION-001 §3 — "recorded in the register" is not a completion. Producer: correct-course Step 4.5. Consumers write their artifact path back on consumption. Unlike its sibling this standard governs a FILE, so it HAS a deterministic tier: `tools/check-scope-register.js` (`--register` row lint · `--audit` inert-scope sweep · bare = fork adoption scan), shipping WARN-ONLY under warn-then-gate, plus a PostToolUse re-lint on register writes (hooks track). Route CORRECTNESS is explicitly ceded to a golden eval (`evals/scope-register-routing.md`) — measured, not gated.
ID: STD-SCOPEREG-001
Version: v1
Breaking: no
Home: shared/scope-register-routing.md
Applies: all

workflow-personas — a thin PRESENTATION layer giving three human-facing families a named voice (Rhea/the design lane, Sol/quick-spec+quick-dev, Mara/escalation-on-class-change). Voice appears in three sanctioned spots only — opening re-orientation, risk acknowledgement, "I" for responsibility — and never drives decisions, narration, menus, or output structure. Subordinate to STD-ESCALATE-001 and answer-shape-and-autonomy. Not an agent.
ID: STD-PERSONA-001
Version: v1
Breaking: no
Home: shared/workflow-personas.md
Applies: all

skill-provenance-and-external-discovery — discovery goes OUTWARD before anything is built (external web AND GitHub/MCP search, sources named with URLs), adopt-over-build is the default (a `build-original` needs a named reason: licence, security/privacy, candidate quality, or poor fit), and every skill/agent carries provenance frontmatter with >=1 `source_research` URL — missing it makes the skill UNVERIFIED, not banned. Retrofit when touched; no fleet-wide backfill. Applies to skills, custom agents, and the workflows that AUTHOR them (`create-agent` / `create-workflow` are consumers, not exceptions). PROBABILISTIC — the linter and new-skill gate are UNBUILT and named as such; DRAFT until piloted in one skills-heavy repo. Written 2026-07-31 at its long-cited-but-missing home: enforced by citation since 2026-07-24 while the file did not exist, which is the drift it exists to prevent.
ID: STD-SKILLPROV-001
Version: v1
Breaking: no
Home: ../../docs/skill-provenance-standard-DRAFT.md
Applies: all

persona-placement — the placement gate that decides WHETHER a flow earns a named persona at all (the upstream half of the persona contract). Rule: personas are for human-facing judgment, not plumbing — a name is added only when the flow acts as a router/owner/advisor AND a reader benefits from knowing who is speaking; mechanical/sub-step/machine-to-machine flows stay anonymous. Reconciles with STD-ESCALATE-001 (a persona changes who speaks, never whether the flow acts). Consulted by workflow-personas (which families earn a voice) and create-agent / persona-content-contract (is this an agent at all).
ID: STD-PERSONA-002
Version: v1
Breaking: no
Home: shared/persona-placement.md
Applies: all

close-out-contract — the SHAPE of a workflow's terminal close-out / hand-off message + how to route feedback about it. A close-out is written for the NEXT actor (consumer / the user's next decision / the downstream workflow), audience-first (active artifact → what changed → substantive corrections → status → next-actor instructions); process narration ("I did X then Y", branch/PR choreography, decision diary, provenance bookkeeping) is forbidden by default — trace on demand only. §2a fixes the two-BLOCK shape: a plain-language block 1 always, plus AT MOST ONE fenced `FOR YOUR LLM ADVISER` block carrying actionable technical detail only (paths, IDs, commands, dispositions) — neutral, machine-shaped, voiceless, omitted entirely when nothing is actionable, and never the trace (raw output stays behind "show details"). A critique of output SHAPE is a workflow-PATCH request: patch the step in the fork FIRST so it propagates by sync, then regenerate — memory is a soft backstop, never the primary remediation. Sibling of STD-DELIVERY-001 (delivery owns the mechanics; this owns the message). PROBABILISTIC at runtime (the emitted message can't be file-linted); the workflow TEMPLATES are deterministically gated by `validate:close-out` (`tools/validate-close-out-contract.js`, in the pre-commit fast-path + `npm test`) — a file instructing narration without adopting the contract fails the commit.
ID: STD-CLOSEOUT-001
Version: v1
Breaking: no
Home: shared/close-out-contract.md
Applies: all

completion-contract — the DISPOSITION a completion-oriented workflow declares at its terminal step: the "finisher, not commentator" contract. A completion workflow (carries scoped work to a deliverable) MUST emit a `completion_disposition` — `pr_merged` / `pr_open` (with the PR), `owner_gated_residue` (with each remaining blocker NAMED + why it is owner-gated), or `advisory` (with a one-line why; for audit/review/triage flows or an owner-scoped analysis run). Diagnosis with no disposition is an INVALID exit — the commentator failure this closes. Third sibling of the close-out family: STD-DELIVERY-001 owns the MECHANICS, STD-CLOSEOUT-001 owns the MESSAGE shape, this owns WHETHER it was driven to done + what remains. References (does not duplicate) the upstream `finisher-drive-to-completion` / `answer-shape-and-autonomy` / `lead-dont-ask` doctrine — it makes that behaviour declarable at a workflow boundary. PROBABILISTIC at runtime (completion is a judgment, not file-checkable; the convergence lever is the close-out feedback-patch rule). Template coverage is checked deterministically: `check:completion -- --strict` (`tools/check-completion-disposition.js`) is **ARMED in `npm test` + the pre-commit fast-path** — a STD-CLOSEOUT-001 adopter with a delivery signal but no STD-COMPLETION-001 reference exits 1 and blocks the commit (escape hatch: reference the contract, incl. `advisory`). Default `check:completion` (no flag) stays warn-only. Armed at owner direction ahead of the warn-then-gate soak default (quiet at arming = precondition, not elapsed soak); fully reversible. The on-disk handoff-artifact check remains a separate per-project track.
ID: STD-COMPLETION-001
Version: v1
Breaking: no
Home: shared/completion-contract.md
Applies: all

behavior-update-digest — the terminal shape for an AUDIT / OBSERVATION / behavioral-review workflow: its close-out must not stop at findings. It emits a five-field **Behavior Update Digest** (`doctrine_delta` · `handoff_delta` · `story_candidate` · `owner_gated` · `completion_disposition`) AND auto-executes the safe stages (record the doctrine, draft the story, re-issue the brief on the allowed path), handing back only owner-gated steps. The audit-lane SPECIALIZATION of STD-CLOSEOUT-001 (it fixes WHAT the next-actor block contains for an audit result) that REUSES STD-COMPLETION-001 for the disposition field — redefines neither. Closes the `observation → (nothing enforced) → text-pool` gap (owner-named after the 2026-06-29 clerk audit). Named callers: design-review, the verify/* audits (data-quality-audit, scrape-coverage-audit, relational-coherence-audit, trace-flow), investigate, maintenance-triage (classify+route), dispatch-followups (auto-execute). PROBABILISTIC at runtime (no harness "audit finished" event to gate on); the levers are the in-flow named-caller references + STD-CLOSEOUT-001 §4 feedback-patch convergence. Deterministic template gate (`check:digest`, sibling of `validate:close-out`/`check:completion`) DEFERRED under warn-then-gate until adoption is proven quiet.
ID: STD-DIGEST-001
Version: v1
Breaking: no
Home: shared/behavior-update-digest.md
Applies: all

### documentation & doctrine

claude-md-standard — CLAUDE.md structure & discipline: global doctrine (machine-local) vs a thin, pointer-based project CLAUDE.md; canonical section shape; reference-not-restate (surface-agnostic — applies to any budgeted always-loaded context file: CLAUDE.md, SKILL.md, MEMORY.md-as-file, external Space instructions; operation = context-compaction skill); edit discipline.
ID: STD-CLAUDE-001
Version: v2
Breaking: no
Home: shared/claude-md-standard.md
Applies: all

dataflow-standard — every data flow crossing a system/repo boundary is a code-anchored map entry (source · ingress path · payload · direction · authority) + the hard non-flow separations; the single answer to "where does X data come from?". Ingress Map worked instance = inbound-flow (5 sources, Amazon SP-API as the pull/push example). Non-flow NF1 = leads ↔ inventory.
ID: STD-DATAFLOW-001
Version: v1
Breaking: no
Home: shared/dataflow-standard.md
Applies: all

## Related registries (not versioned standards)

- **Hooks & gates** → `docs/hooks-registry.md` (fork-local): every Claude Code hook — name, event, purpose, source-of-truth path, enforcement level, owner — plus the "hooks only live in the two homes" rule. Governed alongside this canon by the quarterly review.

## Draft / designed standards (NOT yet synced or enforced)

Reserved IDs for standards that are designed but deliberately kept out of the machine-parsable index above until their Home is finalized and enforcement is wired — so the drift check does not expect a synced copy. Promote into the index (with `Home: shared/...`) when they ship.

- **STD-SKILLPROV-001 — skill-provenance standard — Status: DRAFT (enforcement wiring in progress).** The skills-side sibling of the brief-provenance contract: every skill carries provenance frontmatter (`id, version, created_at, author, source_research[≥1 URL], origin_type, exemption_reason?, predecessor_id?, superseded_by?, last_reviewed_at, review_notes`), gated by a MANDATORY external-discovery pass (web + GitHub/MCP) before build, an adopt-over-build default, and a per-skill changelog + review cadence. DRAFT home → `docs/skill-provenance-standard-DRAFT.md`. Global behavioural half is LIVE now (Mason's global CLAUDE.md discovery-gate + `skill-provenance-and-external-discovery` memory); the FORK enforcement (provenance linter + new-skill CI/hook gate) is phased — piloted in ONE skills-heavy repo (fork itself) before fork-wide promotion, per Mason 2026-07-24. Author the deterministic tier via `enforcement-expert`.

## Memory & knowledge — catalogued, NOT version-tracked here

Cross-project + machine-scoped, so it lives in global `~/.claude` and does **not** sync through the fork — no per-project copy to drift, so the check skips it (no `Home: shared/...` block). Home docs are authoritative:

- **memory-library-discipline** (write) — `~/.claude/projects/-Users-masonwood/memory/memory-library-discipline.md`
- **memory-retrieval-policy** (read) — `~/.claude/projects/-Users-masonwood/memory/memory-retrieval-policy.md`
- **memory-hygiene** (procedure + changelog rule) — `~/.claude/projects/-Users-masonwood/memory/docs/memory-hygiene.md`

## Recent changes

The "did anything important change since v0?" answer — one line per version bump, newest first. (Breaking changes are also flagged `Breaking: yes` on the block above so the drift check escalates them.)

- **2026-08-31 — STD-SRCCTX-001 added (v1):** the **source-context gate** — "a search hit is a lead, never a finding." Owner-directed after an audit of shared workflow prose alleged two behavioural defects (option menus stalling autonomous execution) from phrase matches alone; both were disproved on reading the governing context — the menus carry an explicit `autonomous_mode` bypass, and `design-artifact-loop` already names "presenting an option menu when `autonomous_mode` is true" as an anti-pattern, so the proposed edits would have synced a contradiction to every project. Owner: *"This is not a one-off workflow mistake. It is a reusable investigation-method defect."* The standard requires four things established before a match becomes a causal claim (full governing block · conditional branch / exception / mode flag / override / precedence · whether that condition is enabled in the LIVE target · observed execution or test evidence) and a six-state classification (`active` / `inactive` / `overridden` / `dead` / `documentation-only` / `ambiguous`, the last of which stays unresolved rather than being forced). Carries an eight-field evidence block per claimed defect; **a missing field makes the result a HYPOTHESIS, not a defect and not a change request.** Authored as the INVESTIGATION-side sibling of STD-DIAG-001 (verification) — same prove-before-assert discipline, opposite end of the work — and wired into the audit lane through STD-DIGEST-001 §2a rather than into each of the eight audit workflows separately. Enforcement is PROBABILISTIC **by owner instruction**: a broad stop hook was explicitly declined ("do not build a broad stop hook that interrupts ordinary work"), because grep-usage is the indiscriminate-detector anti-pattern; the levers are the required evidence block, the grep-origin review trigger, and a 7-case golden suite (`evals/source-context-gate.md`) covering all six verdicts — including one live unguarded behaviour that must NOT be softened into a false negative, and one case that must remain `ambiguous`. A `check:srcctx` template detector is named and NOT built. Non-breaking (new standard).
- **2026-07-31 — STD-SKILLPROV-001 added (v1, DRAFT):** skill provenance & outward discovery. The rule was ratified 2026-07-24 and cited as authority by `human-writing-capabilities.md` and a fork-gap entry, but its Home file **was never written** and it was **never registered here** — five weeks of a standard enforceable only from memory. This entry and the DRAFT doc record what was already being enforced; no rule is new. Names its own corpus non-compliance (outreach-email, the humanizer, property-appraisal) and the compounding case: `create-agent`/`create-workflow` emit skills with no provenance support, so everything they author is born UNVERIFIED. Enforcement is PROBABILISTIC and says so — linter + new-skill gate unbuilt. Non-breaking (new standard, DRAFT).
- **2026-07-25 — STD-SCOPEREG-001 added (v1):** scope-register rows are now a governed artifact — the fix for **registered-but-inert** scope. The first broken step was that the fork had **no producer**: `correct-course` is the scope-change front door but never wrote a register row (`scope-register` appeared in `bmad-correct-course/SKILL.md` exactly once, in a parenthetical describing a use it did not implement), so the row was hand-maintained, its route lived in prose outside the table, and `disposition: accepted` + an empty linked-artifact was indistinguishable from delivered. Now every row carries `route` (closed enum R1–R5) + `next_artifact` (the SHAPED artifact, per route) + `activation` (owner · observable trigger · why-not-now, mandatory and only on `R5-parked`), written by a new `correct-course` **Step 4.5**; consumers write their artifact path back on consumption. Adds the **actionability ladder** (REGISTERED / PROPOSED / DESCRIBED / SHAPED) that names the conflation directly: a proposal is actionable for an owner *decision* only, and an epic with N `backlog` story lines is ONE described item, not N actionable ones. Adds the **R4 milestone-block** vocabulary the `sprint-status.yaml` enums never had (milestone status + per-item `owner: operator|agent|external`) so operational proof work stops being mis-encoded as build stories. Unlike its intake-side sibling STD-SCOPEROUTE-001 (prose answer → honestly probabilistic), this governs a FILE and therefore takes a real deterministic tier: `tools/check-scope-register.js`, shipping **WARN-ONLY** under warn-then-gate. Route *correctness* is explicitly ceded to a golden eval rather than faked in the linter. Non-breaking (new standard).
- **2026-07-24 — STD-SKILLPROV-001 registered as DRAFT (not in the parsable index yet):** the skill-provenance standard — the skills-side sibling of the brief-provenance contract (external-discovery gate before build · adopt-over-build default · provenance frontmatter with ≥1 `source_research` URL · per-skill changelog + review cadence). Owner-directed 2026-07-24 after discovery was shown to be inward-only ("no Outlook connection" reported without any web/GitHub search, while an official Anthropic M365 connector + GitHub Outlook MCPs existed). Split by scope: the GLOBAL behavioural half is LIVE now (Mason's global CLAUDE.md discovery-gate + `skill-provenance-and-external-discovery` memory); the FORK enforcement (provenance linter + new-skill CI/hook gate) is soft-but-committed and phased — piloted in one skills-heavy repo before fork-wide, deterministic tier to be authored via `enforcement-expert`. DRAFT home `docs/skill-provenance-standard-DRAFT.md`; kept out of the machine-parsable index (no synced Home) until it ships. See "Draft / designed standards".
- **2026-07-23 — STD-CLAUDE-001 v2 (non-breaking):** generalised pointer-not-restate to **"reference-not-restate is surface-agnostic"** — the discipline applies to any budgeted always-loaded context file (SKILL.md, MEMORY.md-as-file, external Space-instruction fields), with STANDARDS.md's STD registry and MEMORY.md's `[[name]]` index named as sibling instances of one method. The invocable *operation* is the new `context-compaction` skill (`custom/skills/context-compaction/`) — doctrine stays single-homed here; the skill cites it and does not redefine it. Enforcement classified with `enforcement-expert`: PROBABILISTIC awareness tier (skill + memory + one CLAUDE.md pointer line); no deterministic char-budget gate now (a warn-then-gate lint is a later lever only if the skill is skipped, mirroring STD-DATAFLOW-001 / STD-CLOSEOUT-001 staging). No behavioural shift for existing consumers (a thin pointer-style CLAUDE.md already complies).
- **2026-07-01 — STD-DATAFLOW-001 added (v1):** cross-system data flows are now a governed, code-anchored standard — every seam crossing a system/repo boundary (producer→consumer, new cross-boundary schema/webhook, pull/push integration) is documented as an **Ingress Map** entry (source · ingress path · payload · direction · authority) plus the hard **non-flow** separations (`NF1`: leads ↔ inventory). Owner-driven after the mifarma incident (9 supplier invoices silently un-ingested ~2 months in an undocumented mifarma → accounting-tools → inbound-flow seam). Amazon SP-API is the worked example (pull catalog/listing-status + push listing feeds; "acceptance ≠ existence"; NOT the primary order source — bison-ops webhooks are). Enforcement classified with `enforcement-expert`: AWARENESS probabilistic (the map + CLAUDE.md pointer); the deterministic tier guards the ARTIFACT — a warn-then-gate CI/pre-commit check that a cross-boundary schema/webhook change carries a matching map update (DEFERRED until authored+verified, mirroring STD-CLOSEOUT-001's template gate). Non-breaking (new standard).

- **2026-06-29 — STD-DIGEST-001 added (v1):** the **Behavior Update Digest** — the terminal shape for an audit/observation/behavioral-review workflow, closing the owner-named `observation → (nothing enforced) → text-pool` gap (after the 2026-06-29 clerk receive/grade audit pooled as memory text with no enforced next-action). An audit's close-out must emit five fields (`doctrine_delta` · `handoff_delta` · `story_candidate` · `owner_gated` · `completion_disposition`) AND auto-execute the safe stages (record doctrine, draft story, re-issue brief on the allowed path), handing back only owner-gated steps. Authored as the audit-lane SPECIALIZATION of STD-CLOSEOUT-001 that REUSES STD-COMPLETION-001 for the disposition — not a parallel pipeline (the classify/record/handoff/story/dispatch stages already exist in maintenance-triage / memory-library-discipline / design-router / create-story / dispatch-followups; the digest is the missing terminal contract that chains them; confirmed via tool-discovery). All 8 fork audit-lane callers wired: `design-review`, `data-quality-audit`, `scrape-coverage-audit`, `relational-coherence-audit`, `trace-flow`, `webhook-contract-check`, `maintenance-triage` (front door — its triage-specs ARE the story_candidate), `dispatch-followups` (the auto-execute engine for §3). (`investigate` is an upstream BMAD workflow, not forked — out of scope.) skills-native layout regenerated via `tools/port-workflows-to-skills.sh`. PROBABILISTIC tier — no harness "audit finished" event to gate on; the levers are the in-flow named-caller references + STD-CLOSEOUT-001 §4 feedback-patch. A WARN-ONLY detector `check:digest` (`tools/check-digest-adoption.js`) ships now — it flags an audit-lane terminal step (detect/route/diagnostic signals) missing the STD-DIGEST-001 reference; it caught `webhook-contract-check` as a real gap during this very pass (8th caller), and is quiet (10 adopters, 0 gaps) at landing. The deterministic `--strict` ARMING (into `npm test` + pre-commit) is DEFERRED under warn-then-gate until an elapsed soak, exactly as `check:completion` was staged. Non-breaking (new standard).
- **2026-06-27 — STD-CLOSEOUT-001 deterministic template gate added:** `tools/validate-close-out-contract.js` (npm `validate:close-out`, in the pre-commit fast-path + `npm test`) fails the commit when a `custom/workflows` file *instructs* narration (high-precision phrase list) WITHOUT adopting the contract — referencing it is the in-file escape hatch. Enforcement-expert-shaped: the runtime MESSAGE stays probabilistic (not file-lintable; a Stop-hook recap-scan would be the indiscriminate-detector anti-pattern), so the gate guards the TEMPLATES (where drift propagates to every project), NOT "every close-out must reference the contract" (which would false-positive the 24 already-consumer-aware close-outs). Fork-local tooling (guards the source of record; not synced). Green on the current corpus (226 files, 9 adopters).
- **2026-06-27 — STD-CLOSEOUT-001 added (v1):** the terminal close-out / hand-off message now has a governed SHAPE + a feedback-routing rule. A close-out is written audience-first for the NEXT actor (active artifact → what changed → corrections → status → next-actor instructions), and process narration is forbidden by default (trace on demand). Critically, a critique of output SHAPE routes to a workflow PATCH (fork step → propagates by sync), not to project memory or a one-off rewrite — closing the wrong-abstraction-layer gap where shape-feedback was absorbed as a memory and left the template wrong for every other project. Sibling of STD-DELIVERY-001 (mechanics vs message). design-handoff §10 is the canonical instantiation; adjacent deliver steps wired to reference it. PROBABILISTIC tier (no deterministic gate; the feedback-routing is the convergence lever). Non-breaking (new standard).
- **2026-06-27 — STD-PERSONA-002 added (v1):** the persona *placement* gate — "personas are for human-facing judgment, not plumbing." Decides WHETHER a flow earns a named persona at all (router/owner/advisor + human-facing + genuine speaker-ambiguity), the upstream half of the persona contract that STD-PERSONA-001 (voice) and create-agent/persona-content-contract (content) assumed but never stated. §4 reconciles it with STD-ESCALATE-001: four quadrants, two legal — the `pick 1–4` terminal-step fork-gap is the illegal corner that fails both axes. Consulted by workflow-personas + create-agent + create-workflow. Non-breaking (new standard, authoring-time judgment).
- **2026-06-27 — STD-PERSONA-001 added (v1):** three human-facing workflow families gained a named voice (Rhea/design-handoff, Sol/quick-spec+quick-dev, Mara/escalation-on-class-change) via a single shared presentation snippet. Voice is restricted to three sanctioned spots and is explicitly subordinate to STD-ESCALATE-001 + answer-shape-and-autonomy, so "humanising" can't reintroduce narration/diary-voice/menus. Mara rides the existing escalation-snippet reference (no per-workflow wiring). Non-breaking (new standard, presentation-only).
- **2026-06-27 — STD-HOOKACTIVATE-001 added (v1):** git-hook gates are now a governed standard — the fork OWNS both distribution (`custom/githooks/` rail) and activation (`sync`/`onboard` set `core.hooksPath=.githooks` idempotently), with a SessionStart liveness probe. Closes the "deterministic gate silently off because nobody ran the activation step" gap. Local hook = best-effort; fail-closed CI tier deferred. husky retired in the fork. Non-breaking (new standard).
- **2026-06-27 — STD-CLAUDE-001 added (v1):** CLAUDE.md is now a governed standard — defines the global-doctrine vs thin-pointer-project split, the canonical project shape, and edit discipline. Added the hooks & gates registry pointer. Non-breaking (new standard, nothing changed for existing ones).
- **2026-06-26 — v1 (all standards):** initial canon — IDs, versions, and the drift check introduced. No behavioral change to any standard's content.

## How to author a NEW standard

1. **Frontmatter:** `name`, `description`, `contract_version` (integer, start at 1).
2. **Body:** the rule + rationale + (if a contract of record) a per-X template + its **enforcement tier** (which hook/CI/marker makes it hold — prose isn't enforcement; consult `enforcement-expert`).
3. **Add a parsable block here** — `ID:` (`STD-<AREA>-NNN`), `Version: v1`, `Breaking: no`, `Home: shared/<file>.md`, `Applies: all`, in that order.
4. **Add a `Recent changes` line.**
5. **Reference by path** from every consumer; **`sync-bmad-workflows.sh`** distributes it (authoring ≠ shipping).

## Versioning, drift & breaking changes

- **Bump `Version` + `contract_version`** only on a real change; set **`Breaking: yes`** when the change is a behavioral shift a project's restatement or a consumer could now violate (e.g. *how deploys work* or *how memory is written* changes), **`no`** for a safe/clarifying edit.
- **The drift check is Breaking-aware:** a version mismatch on a `Breaking: no` standard is a light "safe to auto-upgrade" note; on `Breaking: yes` it's a strong warning (and, in a later phase, a soft block on deploy-class actions). WARN-only today.
- **Two physical copies of `shared/`** (command-layout `custom/workflows/shared/` + the gitignored, sync-regenerated skills mirror `custom/skills-native/_shared/`) must carry the same versions; a divergence is itself drift.

## Governance (right-sized for a solo operator)

Team design-system governance (named owner per standard, quarterly review *meetings*, drift dashboards) is overhead when one person owns all 9. The lean equivalents:

- **Owner:** the fork maintainer (Mason) owns the baseline; changes land via the normal fork flow (edit `custom/workflows/shared/`, self-review, push, sync). No per-standard owner table.
- **Periodic review:** a lightweight "still true? / what broke? / who actually uses this?" pass over the 9 — right-sized as a `/schedule` reminder, not a meeting. (Cadence TBD — quarterly is fine.)
- **Explicit deviations (convention; enforcement is a later phase):** a project that must break a standard logs a conscious exception in `docs/standards-deviations.md` at its root — one block per deviation: `Standard:` (the ID), `Reason:`, `Date:`, `Expires:`. A logged, unexpired deviation is an *approved* drift; a quiet fork is a defect. The drift check will be taught to read these and suppress the WARN for an unexpired deviation (and re-WARN once it expires).
