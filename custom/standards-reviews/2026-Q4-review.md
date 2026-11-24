---
review_date: 2026-10-01
quarter: 2026-Q4
reviewer: Claude Code (automated scheduled run)
branch: custom
scope: custom/workflows/shared/STANDARDS.md + all Home docs + memory-discipline catalog entries
method: lightweight — still-true / drifted-broke / who-uses-this
prior_review: custom/standards-reviews/2026-Q3-review.md (2026-07-01)
---

# 2026 Q4 Standards Governance Review

> Lightweight "still true? / what broke? / who actually uses this?" pass over every standard
> catalogued in `STANDARDS.md`. Includes all 23 machine-parsable index entries, the three
> memory-discipline catalog entries, and the `STANDARDS.md` self-assessment. Q3 NEEDS-UPDATE
> items are re-checked; newly added standards (STD-SRCCTX-001, 2026-08-31) and six standards
> omitted from the Q3 per-standard pass are assessed for the first time. File:line citations
> where relevant. No standards were edited — review only.

---

## Limitation — memory-doctrine homes not checkable remotely

> **memory-doctrine homes: NOT checkable remotely — flag for a local review.**
>
> The three memory-discipline catalog entries (`memory-library-discipline`,
> `memory-retrieval-policy`, `memory-hygiene`) reference Home docs in the operator's local
> `~/.claude/projects/-Users-masonwood/memory/` tree. Those paths are machine-local and are
> not present in this repository. Their content, drift, and usage cannot be verified from this
> cloud environment. The Q3 recommendation (local-session verification) remains open.

---

## Standards needing attention (summary)

| ID | Standard | Verdict | Primary issue |
|---|---|---|---|
| STD-DEPLOY-001 | deployment-to-prod | **NEEDS-UPDATE** | Q3 flag unresolved: index `Version: v1` vs home `contract_version: 3` |
| STD-DELIVERY-001 | delivery-to-main | **NEEDS-UPDATE** | Q3 flag unresolved: index `Version: v1` vs home `contract_version: 2` |
| STD-PARALLEL-001 | parallel-sessions | **NEEDS-UPDATE** | Q3 flag unresolved: index description omits §D (fork-authoring collision) and §E (wip-register) |
| STD-SKILLPROV-001 | skill-provenance | **NEEDS-UPDATE** | NEW: appears in BOTH the machine-parsable index and the Draft section — sections are meant to be mutually exclusive; Home path is non-standard (`../../docs/…` not `shared/…`) |
| STANDARDS.md | (self) | **NEEDS-UPDATE** | Q3 flag unresolved: `skills-native/_shared/` two-copy requirement references non-existent dir; NEW: STD-SKILLPROV-001 duplicate-section issue |
| STD-DEPLOY-002 | deploy-lane-standard | OK | First review; version match; 2 active consumers |
| STD-PRODREADY-001 | prod-readiness-charter | OK | Unchanged from Q3 |
| STD-WEBHOOK-001 | webhook-contract-charter | OK | Unchanged from Q3 |
| STD-DIAG-001 | diagnostics-gate | OK | Unchanged from Q3 |
| STD-SRCCTX-001 | source-context-gate | OK | First review; new 2026-08-31; golden suite exists; low ID-adoption expected |
| STD-WORKTREE-001 | worktree-portability | OK | Unchanged from Q3 |
| STD-WAVE-001 | wave-orchestration | OK | Unchanged from Q3 |
| STD-STACK-001 | detect-stack | OK | Unchanged from Q3 |
| STD-HOOKACTIVATE-001 | hook-activation | OK | Spot-checked; 13 refs; healthy |
| STD-ESCALATE-001 | escalation-on-class-change | OK | Spot-checked; 9 active consumers |
| STD-SCOPEROUTE-001 | scope-extension-routing | OK | First review; PROBABILISTIC by design; 0 workflow step ID-refs is expected |
| STD-SCOPEREG-001 | scope-register-routing | OK | First review; checker exists; correct-course wired |
| STD-PERSONA-001 | workflow-personas | OK | Spot-checked; 19 path-refs |
| STD-PERSONA-002 | persona-placement | OK | Unchanged from Q3 |
| STD-CLOSEOUT-001 | close-out-contract | OK | Spot-checked; gate tools confirmed; 14 refs |
| STD-COMPLETION-001 | completion-contract | OK | Spot-checked; `--strict` armed; 20 refs |
| STD-DIGEST-001 | behavior-update-digest | OK | Spot-checked; all 8 callers confirmed |
| STD-CLAUDE-001 | claude-md-standard | OK | Unchanged from Q3 |
| STD-DATAFLOW-001 | dataflow-standard | OK | First review; DEFERRED det. gate shipped as git-hook; 0 workflow step ID-refs |

---

## Per-standard findings

---

### STD-DEPLOY-001 — deployment-to-prod

**Verdict: NEEDS-UPDATE** *(carried from Q3)*

**Still true?**
Yes. Deploy-method modes, fallback ladder, dirty-tree filter, dep auto-heal, exit-code grammar
(0–19/99), and §1B cross-service round-trip clause are all coherent with `custom/scripts/bmad-deploy.sh`.

**Drifted/broke:**
`custom/workflows/shared/deployment-to-prod.md:3` — `contract_version: 3`
`custom/workflows/shared/STANDARDS.md:28` — `Version: v1`

Same two-version gap identified in Q3. **Not fixed.** Both v2 (deploy-method modes) and v3
(cross-service round-trip clause) are behavioral additions. Fix: bump index entry to `Version: v3`.

**Who uses it:** ~15 files (active). Key consumers: deliver steps, webhook-contract-check,
prod-readiness-charter, deploy.sh. Actively referenced.

---

### STD-DEPLOY-002 — deploy-lane-standard

**Verdict: OK** *(first review — omitted from Q3)*

**Still true?**
Yes. Self-identifies as STD-DEPLOY-002 v1 at `deploy-lane-standard.md:9`. Ten requirements with
mechanical probes, checker (`tools/check-deploy-lane.py`), and `bmad-health.py` integration are
accurate.

**Drifted/broke:** None. `contract_version: 1` matches `Version: v1` in index.

**Who uses it:** 2 non-self consumers — `custom/hooks/deploy_lane_guard.py` and
`custom/claude-global/hooks/deploy-lane-setup.sh`. References are infrastructure-only, consistent
with a checker-oriented standard. The standard is plumbed rather than cited by workflow step prose.

---

### STD-DELIVERY-001 — delivery-to-main

**Verdict: NEEDS-UPDATE** *(carried from Q3)*

**Still true?**
Yes. Nine-step delivery sequence is accurate and internally consistent.

**Drifted/broke:**
`custom/workflows/shared/delivery-to-main.md:3` — `contract_version: 2`
`custom/workflows/shared/STANDARDS.md:34` — `Version: v1`

One-version gap from Q3. **Not fixed.** The v2 behavioral change (`git add -f` mandatory with a
hard-halt check) closes a silent-no-stage failure. Fix: bump index entry to `Version: v2`.

**Who uses it:** 4 active non-review consumers (behavior-update-digest.md, completion-contract.md,
claude-md-standard.md, plus design/implement workflow deliver steps).

---

### STD-PRODREADY-001 — prod-readiness-charter

**Verdict: OK** *(unchanged from Q3)*

Phase 0–1 shipped accurately; Phases 2–3 correctly documented as designed. No version drift.
Machine-local hook files (`prod-readiness-probe.sh`, `prod-readiness-deploy-gate.sh`) confirmed.

---

### STD-WEBHOOK-001 — webhook-contract-charter

**Verdict: OK** *(unchanged from Q3)*

Sender/receiver duties, rollout order, breaking-change taxonomy and per-boundary template are
current. `contract_version: 1` matches index `Version: v1`. 7 active consumers.

---

### STD-DIAG-001 — diagnostics-gate

**Verdict: OK** *(unchanged from Q3)*

Prove-don't-assert rule and §2 "what does NOT satisfy the gate" table are accurate. `detect-stack.md`
pointer correct. `contract_version: 1` matches. 6 active implementation-workflow consumers.

---

### STD-SRCCTX-001 — source-context-gate

**Verdict: OK** *(first review — added 2026-08-31, after Q3)*

**Still true?**
Yes. Eight-field evidence block and six-state classification (`active` / `inactive` / `overridden` /
`dead` / `documentation-only` / `ambiguous`) match the index description. The explicit "NO broad
stop hook (owner instruction 2026-08-31)" note in the home doc is consistent with the STANDARDS.md
Recent Changes entry. Golden suite confirmed at `evals/source-context-gate.md`.

**Drifted/broke:** None. `contract_version: 1` matches `Version: v1`. The standard is 1 month old.

**Who uses it:** 2 active references outside the home doc — `diagnostics-gate.md` (sibling
cross-reference: "investigation-side sibling of STD-DIAG-001") and `behavior-update-digest.md`
(audit-lane wiring via STD-DIGEST-001 §2a). Zero consumer workflow step files reference it by
STD-ID, consistent with its PROBABILISTIC enforcement tier and owner's explicit decision against
a broad stop hook. Expected at this maturity.

---

### STD-PARALLEL-001 — parallel-sessions

**Verdict: NEEDS-UPDATE** *(carried from Q3)*

**Still true?**
Core §A–§C content is accurate. §D (fork-authoring collision prevention) and §E (wip-register /
quick-flow claim) are functional protocol sections with named hook files and a YAML register.

**Drifted/broke:**
The STANDARDS.md index description (`STANDARDS.md:65`) reads:
> "concurrent-session protocol (worktree-before-edit, integrate-advancing-main, named collision
> classes, story claim+reconcile)"

**Not fixed from Q3.** §D (`parallel-sessions.md:173–191`: three sub-rules D1–D3, including
`check-fork-authoring-collision` hook) and §E (`parallel-sessions.md:193–214`: five sub-rules
E1–E5, `wip-register.yaml`, SessionStart hook, quick-spec/quick-dev enrichment) are absent from
the index description. These are not minor additions — §E alone introduces a whole new claim
mechanism for non-sprint work.

Fix: update the STANDARDS.md description line to include fork-authoring collision prevention (§D)
and ad-hoc quick-flow claim/wip-register (§E). `contract_version: 1` in both — no version bump
required (additive).

**Who uses it:** Referenced by path (`parallel-sessions`) rather than by STD-ID across the corpus.
Active consumption confirmed in quick-dev, dev-story, dev-auto, code-review, create-epics-and-stories.

---

### STD-WORKTREE-001 — worktree-portability

**Verdict: OK** *(unchanged from Q3)*

Core path-resolution rule accurate. §7 (cwd-pinned session fallback) and §8 (per-worktree
`_bmad/` refresh opt-in) remain additive non-breaking additions. `contract_version: 1` matches.
23 references across design-handoff, quick-dev, design-review, implementation workflows.

---

### STD-WAVE-001 — wave-orchestration

**Verdict: OK** *(unchanged from Q3)*

§W0–§W5 internally consistent. `contract_version: 1` matches. 5 active consumers.

---

### STD-STACK-001 — detect-stack

**Verdict: OK** *(unchanged from Q3)*

Three profiles (`express-react-drizzle`, `python-fastapi-sse`, `nextjs-prisma`) + `unknown`.
Extension instructions reference correct downstream files. `contract_version: 1` matches. 7 consumers.

---

### STD-HOOKACTIVATE-001 — hook-activation-standard

**Verdict: OK** *(spot-checked Q4)*

Distribution + activation mechanism in place. `custom/githooks/pre-commit`, `pre-push`, and
`gates.d/design-brief-completeness.conf` confirmed. `activate-hooks.sh` present. CI tier honestly
deferred; husky retired confirmed. `contract_version: 1` matches. 13 active references including
7 githook infrastructure files. Healthy.

---

### STD-ESCALATE-001 — escalation-on-class-change

**Verdict: OK** *(spot-checked Q4)*

Four tripwire signals, four-step response contract (state → name gateway → propose → proceed),
gateway map (§3), and §4 halt-and-record for unattended runs — all current. `contract_version: 1`
matches. 9 active non-review consumers across quick-spec, quick-dev, maintenance-triage, design-router,
design-elevation, dev-story (slight drop from Q3's 11, plausibly due to workflow reorganization).

---

### STD-SCOPEROUTE-001 — scope-extension-routing

**Verdict: OK** *(first review — omitted from Q3)*

**Still true?**
Yes. Four-lane routing (design-elevation / correct-course + scope-register / correct-course →
PRD/Architecture → create-epics-and-stories / mixed), four-part answer shape, and two guardrails
(MATERIALITY / PREMISE-CHECK) are internally consistent and match the index description.
PROBABILISTIC enforcement tier honestly stated.

**Drifted/broke:** None. `contract_version: 1` matches `Version: v1`.

**Who uses it:** 1 active cross-reference (`scope-register-routing.md` as sibling). Zero consumer
workflow step files reference it by STD-ID. This is expected and by design — the standard's
PROBABILISTIC levers are a UserPromptSubmit hook (`bmad-scope-extension-router`, machine-local)
and an optional per-project `CLAUDE.md` pointer; neither is captured by STD-ID grepping. The golden
eval (`evals/router-shape.md`) is the correctness measure.

---

### STD-SCOPEREG-001 — scope-register-routing

**Verdict: OK** *(first review — omitted from Q3)*

**Still true?**
Yes. R1–R5 route enum, `next_artifact` requirement, `activation` block (mandatory on R5-parked),
and actionability ladder (REGISTERED → PROPOSED → DESCRIBED → SHAPED) are internally consistent.
R4 milestone-block vocabulary is present. WARN-only tier honestly stated.

**Drifted/broke:** None. `contract_version: 1` matches `Version: v1`.

**Deterministic tier:** `tools/check-scope-register.js` confirmed present.

**Who uses it:** 5 refs including `custom/skills/bmad-correct-course/SKILL.md` (the named producer
for Step 4.5), `custom/workflows/4-implementation/sprint-planning/instructions.md`, and
`sprint-status-template.yaml`. Core production path wired.

---

### STD-PERSONA-001 — workflow-personas

**Verdict: OK** *(spot-checked Q4)*

Three voices (Rhea/Sol/Mara), three sanctioned spots, subordination to STD-ESCALATE-001 confirmed.
`contract_version: 1` matches. **19 path-references** to `workflow-personas` across design-handoff,
quick-dev, quick-spec, escalation-on-class-change, create-agent, and others. STD-ID grep returns
lower counts because consumers cite by filename, not by ID — the standard is actively consumed.

---

### STD-SKILLPROV-001 — skill-provenance-and-external-discovery

**Verdict: NEEDS-UPDATE** *(first review; NEW finding)*

**Still true?**
Yes — the rule (discovery outward before build, adopt-over-build default, provenance frontmatter
with ≥1 `source_research` URL) is accurate and the home doc at
`/home/user/BMAD-METHOD/docs/skill-provenance-standard-DRAFT.md` exists and is consistent with
the index description.

**Drifted/broke — structural inconsistency:**
`STANDARDS.md` lists STD-SKILLPROV-001 in **two mutually-exclusive sections**:

1. **Machine-parsable index** (`STANDARDS.md:143–148`):
   ```
   ID: STD-SKILLPROV-001
   Version: v1
   Breaking: no
   Home: ../../docs/skill-provenance-standard-DRAFT.md
   Applies: all
   ```
2. **Draft / designed standards section** (`STANDARDS.md:199–202`):
   > "Reserved IDs for standards that are designed but deliberately kept out of the machine-parsable
   > index above..."
   > `STD-SKILLPROV-001 — skill-provenance standard — Status: DRAFT (enforcement wiring in progress)`

The Draft section header explicitly states entries there are "deliberately kept out of the
machine-parsable index." STD-SKILLPROV-001 is in both. This means `check-standards-drift.sh` WILL
expect a synced copy in projects (it scans the machine-parsable index), but the standard is still
DRAFT with no enforcement wired — a contradiction in the governance contract.

Additionally, the `Home:` path `../../docs/skill-provenance-standard-DRAFT.md` breaks from the
`Home: shared/<file>.md` convention that all promoted standards use (see the "Promote into the
index" instruction at the bottom of the Draft section).

**Fix options (owner decides):**
- **Option A (promote):** Remove the Draft section entry, move the home doc to
  `custom/workflows/shared/skill-provenance-standard.md`, update `Home:` in the index, and wire
  the deterministic tier. Consistent with `STANDARDS.md:236` promotion rule.
- **Option B (revert to Draft):** Remove the machine-parsable index entry for STD-SKILLPROV-001;
  keep only the Draft section entry. Update when enforcement is wired.

**Who uses it:** 53 files across `custom/` — largest corpus footprint of any standard, driven by
skills carrying provenance frontmatter. The rule is actively followed even in DRAFT state.

---

### STD-PERSONA-002 — persona-placement

**Verdict: OK** *(unchanged from Q3)*

Three-condition placement gate and §4 STD-ESCALATE-001 reconciliation current.
`contract_version: 1` matches. 6 references across workflow-personas, create-workflow, create-agent.

---

### STD-CLOSEOUT-001 — close-out-contract

**Verdict: OK** *(spot-checked Q4)*

Two-block shape (plain-language block 1 + optional `FOR YOUR LLM ADVISER` fenced block),
process-narration prohibition, and §4 workflow-patch routing rule current.
`tools/validate-close-out-contract.js` confirmed present. `contract_version: 1` matches.
14 active references.

---

### STD-COMPLETION-001 — completion-contract

**Verdict: OK** *(spot-checked Q4)*

Four-value disposition enum, invalid-exit rule, and §5 enforcement honesty current.
`tools/check-completion-disposition.js` confirmed present.
`check:completion -- --strict` **confirmed armed** in `package.json` test script.
`contract_version: 1` matches. 20 active references.

---

### STD-DIGEST-001 — behavior-update-digest

**Verdict: OK** *(spot-checked Q4)*

Five-field digest, §3 auto-execute mandate, and all **8 named callers** confirmed:
design-review, dispatch-followups, maintenance-triage, relational-coherence-audit, trace-flow,
data-quality-audit, scrape-coverage-audit, webhook-contract-check. `check:digest` tool exists and
correctly WARN-ONLY (not in `npm test`). `contract_version: 1` matches. 11 refs, full audit-lane
coverage.

---

### STD-CLAUDE-001 — claude-md-standard

**Verdict: OK** *(unchanged from Q3)*

Global-vs-project CLAUDE.md split, pointer-not-restate discipline, and edit rules current.
`contract_version: 2` matches `Version: v2`. Low in-repo reference count is expected for an
authoring-time governance standard.

---

### STD-DATAFLOW-001 — dataflow-standard

**Verdict: OK** *(first review — omitted from Q3)*

**Still true?**
Yes. Ingress Map entry definition (source · ingress path · payload · direction · authority), NF1
non-flow separation (leads ↔ inventory), and Amazon SP-API worked example are internally consistent.

**Drifted/broke:** None. `contract_version: 1` matches `Version: v1`.

The STANDARDS.md Recent Changes entry stated the deterministic gate (CI/pre-commit check requiring
a map update on cross-boundary schema changes) was DEFERRED at authoring time. The deployed state
shows `custom/githooks/check-dataflow-map.sh` and `custom/githooks/gates.d/dataflow-map.conf`
exist — the gate shipped as a git-hook. The standard should note the gate has shipped; the DEFERRED
language in the Recent Changes entry is now stale prose (not the standard itself, so no version
bump required — but worth noting in fork-gaps.md or the next standard update).

**Who uses it:** 2 non-self consumers — both githook infrastructure. Zero workflow step files
reference it by STD-ID. Consistent with a boundary-guard that fires on schema/webhook changes
rather than being cited in workflow prose.

---

### Memory-discipline catalog entries

**Verdict: NOT CHECKABLE REMOTELY**

Per the limitation stated above: `memory-library-discipline`, `memory-retrieval-policy`, and
`memory-hygiene` live in the operator's local `~/.claude/projects/-Users-masonwood/memory/`
tree. These are explicitly excluded from the fork's `check-standards-drift.sh` scan (no
`Home: shared/...` block). No assessment possible from this cloud environment.

**Recommendation:** run a local-session verification pass — re-open this review doc in a
local Claude Code session with access to `~/.claude/` and check each home doc for internal
consistency and whether the current memory-write/read behavior matches the written policy.

---

### STANDARDS.md self-assessment

**Verdict: NEEDS-UPDATE**

Two open issues:

**1. `skills-native/_shared/` reference — carried from Q3, unresolved.**
`STANDARDS.md:244` states:
> "Two physical copies of `shared/` (`custom/workflows/shared/` + the gitignored,
> sync-regenerated skills mirror `custom/skills-native/_shared/`) must carry the same versions"

`custom/skills-native/` does NOT exist. This directory was referenced from when a
`skills-native/_shared/` mirror was planned; the current delivery path uses `custom/skills/`
(post-v6.8 migration). The requirement now describes a state that never shipped.

Fix: remove or update the two-copy requirement in STANDARDS.md §"Versioning, drift & breaking
changes" to reflect the actual delivery architecture (or mark it as planned/not-yet-active).

**2. STD-SKILLPROV-001 dual-section listing — NEW in Q4.**
As described in the STD-SKILLPROV-001 finding above: the standard appears in both the
machine-parsable index and the Draft section. The Draft section header states its entries are
"deliberately kept out of the machine-parsable index" — the duplicate creates governance
ambiguity about whether `check-standards-drift.sh` should expect a synced copy in projects.

Fix: owner selects Option A (promote fully) or Option B (revert to Draft-only) and removes the
duplicate entry accordingly.

---

## Required actions

| # | File | Action |
|---|---|---|
| 1 | `custom/workflows/shared/STANDARDS.md:28` | Bump `Version: v1` → `Version: v3` for STD-DEPLOY-001 |
| 2 | `custom/workflows/shared/STANDARDS.md:34` | Bump `Version: v1` → `Version: v2` for STD-DELIVERY-001 |
| 3 | `custom/workflows/shared/STANDARDS.md:65` | Update description for STD-PARALLEL-001 to cover §D (fork-authoring collision) and §E (wip-register / quick-flow claim) |
| 4 | `custom/workflows/shared/STANDARDS.md:143–202` | Resolve STD-SKILLPROV-001 dual listing — either promote (move home to `shared/`, wire gate, remove Draft entry) or revert (remove machine-parsable index entry) |
| 5 | `custom/workflows/shared/STANDARDS.md:244` | Remove or update `skills-native/_shared/` two-copy requirement to match actual delivery architecture |
| 6 | Local only | Verify memory-doctrine home docs (`memory-library-discipline`, `memory-retrieval-policy`, `memory-hygiene`) in a local session with `~/.claude/` access |

---

## Notes on Q3 open items

All four Q3 Required Actions (STD-DEPLOY-001 bump, STD-DELIVERY-001 bump, STD-PARALLEL-001
description update, STANDARDS.md `skills-native/_shared/` fix) remain **open and unresolved** as
of this Q4 review. They carry forward as items 1–3 and 5 above.

---

*Review ran: 2026-10-01. Next scheduled review: 2027-Q1.*
