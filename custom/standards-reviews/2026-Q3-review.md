---
review_date: 2026-07-01
quarter: 2026-Q3
reviewer: Claude Code (automated scheduled run)
branch: custom
scope: custom/workflows/shared/STANDARDS.md + all Home docs
method: lightweight — still-true / drifted-broke / who-uses-this
---

# 2026 Q3 Standards Governance Review

> Lightweight "still true? / what broke? / who uses this?" pass over every standard in the
> `STANDARDS.md` canon. Each standard is assessed against (1) its Home doc content, (2) how
> the fork's workflows/hooks/config actually behave, and (3) active cross-references (grep over
> `custom/`). File:line citations where relevant.

---

## Limitation — memory-doctrine homes not checkable remotely

> **memory-doctrine homes: NOT checkable remotely — flag for a local review.**
>
> The three memory-discipline catalog entries reference Home docs in the operator's local
> `~/.claude/projects/-Users-masonwood/memory/` tree (`memory-library-discipline`,
> `memory-retrieval-policy`, `memory-hygiene`). Those paths are machine-local and are not
> present in this repository. Their content, drift, and usage cannot be verified from this
> cloud environment. Recommend a separate local-session pass over those three docs at the
> next convenient opportunity.

---

## Standards needing attention (summary)

| ID | Standard | Verdict | Primary issue |
|---|---|---|---|
| STD-DEPLOY-001 | deployment-to-prod | **NEEDS-UPDATE** | Index `Version: v1` but home doc at `contract_version: 3`; two behavioral additions not reflected |
| STD-DELIVERY-001 | delivery-to-main | **NEEDS-UPDATE** | Index `Version: v1` but home doc at `contract_version: 2`; `git add -f` requirement is v2 |
| STD-PARALLEL-001 | parallel-sessions | **NEEDS-UPDATE** | Index description stale: §D (fork-authoring collision) and §E (wip-register/quick-flow claim) are substantial additions not reflected in the index entry |
| STANDARDS.md | (self) | **NEEDS-UPDATE** | §Versioning references `custom/skills-native/_shared/` as a required second physical copy; that directory does not exist (v6.8 migration in-flight per `MIGRATION-v6.8-skills-plan.md`) |
| STD-PRODREADY-001 | prod-readiness-charter | OK | Phase 1 probe shipped accurately; phases 2–3 still "designed" |
| STD-WEBHOOK-001 | webhook-contract-charter | OK | Content current; referenced by 7 files |
| STD-DIAG-001 | diagnostics-gate | OK | Content current; referenced by 6 implementation workflows |
| STD-WORKTREE-001 | worktree-portability | OK | §7/§8 are additive; no contract_version bump needed; 23 references |
| STD-WAVE-001 | wave-orchestration | OK | Content current; referenced by 5 files |
| STD-STACK-001 | detect-stack | OK | 3 stack profiles; extension points documented; 7 references |
| STD-HOOKACTIVATE-001 | hook-activation-standard | OK | Mechanism in place; CI tier accurately deferred |
| STD-ESCALATE-001 | escalation-on-class-change | OK | 11 references; content and gateway map current |
| STD-PERSONA-001 | workflow-personas | OK | 11 references; three voices correctly wired |
| STD-PERSONA-002 | persona-placement | OK | 6 references; gate logic sound |
| STD-CLOSEOUT-001 | close-out-contract | OK | Deterministic gate armed (`validate:close-out` in `npm test` + pre-commit) |
| STD-COMPLETION-001 | completion-contract | OK | `check:completion --strict` armed in `npm test` + pre-commit; confirmed in `package.json:47` |
| STD-DIGEST-001 | behavior-update-digest | OK | `check:digest` correctly warn-only (not in test); 10 references across all 8 named callers |
| STD-CLAUDE-001 | claude-md-standard | OK | Low cross-reference count is expected for a governance meta-standard; nudge hooks machine-local |

---

## Per-standard findings

---

### STD-DEPLOY-001 — deployment-to-prod

**Verdict: NEEDS-UPDATE**

**Still true?**
Content is accurate and current. The three deploy modes (`push_auto`, `contract_script`, `manual_cli`), fallback ladder, dirty-tree filter, dep auto-heal, exit-code grammar (codes 0–19/99), and §1B cross-service round-trip clause are all coherent with `custom/scripts/bmad-deploy.sh` (present and referenced).

**Drifted/broke:**
`custom/workflows/shared/deployment-to-prod.md:3` — `contract_version: 3`
`custom/workflows/shared/STANDARDS.md:28` — `Version: v1`

These are out of sync by two increments. Per STANDARDS.md §"Versioning, drift & breaking changes": "Bump `Version` + `contract_version` only on a real change." The home doc records two changes:
- **v2 (2026-06-27):** Added §1A (deploy-method modes + fallback ladder + auth-failure branch). Behavioral — introduced `deploy.method` field.
- **v3 (2026-06-28):** Added §1B (cross-service payload changes — one verified round-trip). Behavioral.

Both are noted in STANDARDS.md's `## Recent changes` section (`deployment-to-prod.md:304–306`) but the parsable index block was never bumped. This is the exact gap `check-standards-drift.sh` is designed to flag when comparing fork-canonical to a project's synced copy — but it also shows the fork-canonical itself is inconsistent.

Fix: in STANDARDS.md, change `Version: v1` → `Version: v3` for STD-DEPLOY-001.

**Who uses it:**
15 files. Key consumers: `custom/workflows/verify/wire-check/steps/step-05-deliver.md`, `custom/workflows/verify/webhook-contract-check/workflow.md`, `custom/workflows/shared/prod-readiness-charter.md`, `custom/workflows/shared/webhook-contract-charter.md`, `custom/workflows/implement/quick-dev/steps/step-07-deliver.md`, `custom/workflows/implement/design-implement/steps/step-04-apply-and-deliver.md`, `custom/scripts/bmad-deploy.sh`. Actively referenced.

---

### STD-DELIVERY-001 — delivery-to-main

**Verdict: NEEDS-UPDATE**

**Still true?**
Content is accurate. The nine-step delivery sequence (verify in worktree → stage with `git add -f` → commit → rename branch → push → open PR → attempt merge → verify merge state → fast-forward main → surface URL) is internally consistent and cross-references worktree-portability correctly.

**Drifted/broke:**
`custom/workflows/shared/delivery-to-main.md:3` — `contract_version: 2`
`custom/workflows/shared/STANDARDS.md:34` — `Version: v1`

The home doc is at v2 but the index still shows v1. The v2 behavioral addition (not explicitly versioned in the doc's own changelog section, but visible in the `git add -f` rule in §3 Step 2) makes `git add -f` mandatory with a hard-halt check, closing the "artifact looks delivered but staged nothing" silent failure. This is a real behavioral change consumers should be aware of.

Fix: in STANDARDS.md, change `Version: v1` → `Version: v2` for STD-DELIVERY-001.

**Who uses it:**
15 files. Key consumers: `custom/workflows/design/design-handoff/steps/step-04-deliver.md`, `custom/workflows/design/onboard-design-system/workflow.md`, `custom/workflows/shared/parallel-sessions.md`, `custom/workflows/shared/wave-orchestration.md`. Actively referenced.

---

### STD-PRODREADY-001 — prod-readiness-charter

**Verdict: OK**

**Still true?**
Yes. The phase rollout in §6 is accurately documented:
- Phase 0 (charter): shipped — this doc.
- Phase 1 (deploy probe): SHIPPED — `custom/claude-global/hooks/prod-readiness-probe.sh` and `custom/claude-global/hooks/prod-readiness-deploy-gate.sh` are present.
- Phase 2/3 (setup lane / hard gate): accurately marked "designed."

The charter correctly identifies the three lifecycle states, conservative detection rules, and the Phase-1 probe's machine-local (`~/.claude`) distribution path.

**Drifted/broke:** None detected. `contract_version: 1` in both home doc and index.

**Who uses it:**
8 files: `custom/workflows/shared/STANDARDS.md`, `custom/workflows/shared/prod-readiness-charter.md` (self), `custom/workflows/shared/claude-md-standard.md`, `custom/prod-readiness-handoff.md`, `custom/prod-readiness-rollout-spec.md`, `custom/claude-global/skills/enforcement-expert/SKILL.md`, `custom/claude-global/hooks/prod-readiness-deploy-gate.sh`, `custom/claude-global/hooks/prod-readiness-probe.sh`.

---

### STD-WEBHOOK-001 — webhook-contract-charter

**Verdict: OK**

**Still true?**
Yes. Sender/receiver duties, rollout order (sender-strict/receiver-lenient), breaking-change taxonomy, ambiguity ownership, and the per-boundary template are all internally consistent. The charter correctly identifies `webhook-contract-check` as its enforcer and `quick-spec`/`quick-dev` as its pre-coding consulters.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
7 files: `custom/workflows/verify/webhook-contract-check/workflow.md`, `custom/workflows/verify/scrape-coverage-audit/steps/step-04-classify-and-route.md`, `custom/workflows/verify/data-quality-audit/steps/step-04-route.md`, `custom/workflows/shared/producer-defect-template.md`, `custom/agents/data-integrity-lead.md`. Actively used by verify audit lane.

---

### STD-DIAG-001 — diagnostics-gate

**Verdict: OK**

**Still true?**
Yes. The prove-don't-assert rule is clear and the "what does NOT satisfy the gate" §2 table is accurate. The reference to `detect-stack.md` for project-specific commands is correct.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
6 files: `custom/workflows/implement/quick-dev/steps/step-04-self-check.md`, `custom/workflows/implement/design-implement/steps/step-04-apply-and-deliver.md`, `custom/workflows/4-implementation/dev-story/workflow.md`, `custom/workflows/4-implementation/dev-auto/steps/step-04-review.md`. Actively referenced by implementation workflows.

---

### STD-PARALLEL-001 — parallel-sessions

**Verdict: NEEDS-UPDATE**

**Still true?**
The core content (§A worktree, §B artifact races, §C story claim+reconcile) is accurate and current. The collision classes (barrel re-exports, additive schema tables, Drizzle migration collision, sprint-status) match observable patterns.

**Drifted/broke:**
The STANDARDS.md index description (`STANDARDS.md:65`) reads:
> "concurrent-session protocol (worktree-before-edit, integrate-advancing-main, named collision classes, story claim+reconcile)"

But the home doc now includes two substantial additions that are entirely absent from this description:
- **§D — Fork-authoring collision prevention** (`parallel-sessions.md:173–191`): three sub-rules (D1 check for in-flight twins, D2 dedup convention, D3 atomic commit with `-o`). This was added after a live incident (two sessions independently authored `claude-md-charter.md` and `claude-md-standard.md`, caught only by lucky re-read).
- **§E — Ad-hoc quick-flow claim (wip-register)** (`parallel-sessions.md:193–214`): five sub-rules (E1 wip-register.yaml, E2 SessionStart hook, E3 quick-spec/quick-dev enrich+check, E4 distribution split, E5 spec-wip content-pin). Closes the feature-duplication blind spot for non-sprint work.
- **§B1a — Multi-line story prose** (`parallel-sessions.md:87–92`): added carve-out rule for multi-line comment blocks in sprint-status.yaml.

`contract_version` is still 1 in both the doc and index — the additions were apparently treated as non-breaking. The index description should be updated to reflect the expanded scope.

Fix: update the STANDARDS.md description line to include fork-authoring collision prevention and ad-hoc quick-flow claim. No version bump required if additive/non-breaking.

Note: §E hooks (`wip-register.sh`, `check-wip-register.sh`, `wip-claim-on-worktree.sh`) are on the global hooks track (machine-local `install-global-assets.sh`) per §E4 — not verifiable from this cloud environment.

**Who uses it:**
15 files. Very actively referenced: `custom/workflows/implement/quick-dev/steps/step-03-execute.md`, `custom/workflows/4-implementation/dev-story/workflow.md`, `custom/workflows/4-implementation/dev-auto/workflow.md`, `custom/workflows/4-implementation/code-review/instructions.xml`, `custom/workflows/3-solutioning/create-epics-and-stories/workflow.md`, and others.

---

### STD-WORKTREE-001 — worktree-portability

**Verdict: OK**

**Still true?**
Yes. The core path-resolution rule (`git rev-parse --show-toplevel`), producer rules, affected workflows, and halt-diagnostic format are all accurate.

**Drifted/broke:**
The home doc gained two additive sections after the initial authoring — both documented in `docs/fork-gaps.md`:
- **§7 — cwd-pinned session fallback** (`worktree-portability.md:107–122`): manual `git worktree add` + absolute-path Write/Edit when `EnterWorktree` refuses a repo-root-pinned session.
- **§8 — per-worktree `_bmad/` refresh opt-in** (`worktree-portability.md:123–130`): default-off; opt in with `BMAD_WORKTREE_SYNC=1`.

Both are additive guidance; `contract_version` was not bumped (still 1 in both places). The STANDARDS.md description ("artifact paths resolve to the worktree root, not the main checkout") is accurate for the core content. The §7/§8 additions could be mentioned in the description for completeness, but this is not a blocking issue.

**Who uses it:**
23 files. Broadly referenced across design-handoff, quick-dev, design-review, and implementation workflows.

---

### STD-WAVE-001 — wave-orchestration

**Verdict: OK**

**Still true?**
Yes. §W0 (additive invariant), §W1 (decompose), §W2 (batch / concurrency cap 6), §W3 (structured-result contract), §W4 (aggregate and gate), §W5 (composition with parallel-sessions) are all internally consistent and consistent with how code-review, create-epics-and-stories, and dev-story reference it.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
5 files: `custom/workflows/4-implementation/dev-story/workflow.md`, `custom/workflows/4-implementation/code-review/instructions.xml`, `custom/workflows/3-solutioning/create-epics-and-stories/workflow.md`, `custom/workflows/shared/parallel-sessions.md`, `custom/workflows/shared/STANDARDS.md`. Actively referenced.

---

### STD-STACK-001 — detect-stack

**Verdict: OK**

**Still true?**
Yes. Three profiles: `express-react-drizzle`, `python-fastapi-sse`, `nextjs-prisma` + `unknown`. Extension instructions reference the correct downstream files (wire-check/step-01-map-wires.md, wire-check/step-02-trace-wires.md). Detection script is functional bash.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
7 files: `custom/workflows/verify/wire-check/steps/step-01-map-wires.md`, `custom/workflows/verify/trace-flow/steps/step-01-map-stages.md`, `custom/workflows/4-implementation/code-review/instructions.xml`, `custom/workflows/4-implementation/code-review/checklist.md`. Actively referenced by verify workflows.

---

### STD-HOOKACTIVATE-001 — hook-activation-standard

**Verdict: OK**

**Still true?**
Yes. The two-part mechanism (distribution via `custom/githooks/` rail + activation via `sync-bmad-workflows.sh`/`onboard-project.sh` setting `core.hooksPath`) is in place:
- `custom/githooks/pre-commit` and `custom/githooks/pre-push` are present and carry the STD-HOOKACTIVATE-001 marker (`custom/githooks/pre-commit:3`).
- `custom/githooks/gates.d/design-brief-completeness.conf` is a fork-owned drop-in gate.
- `custom/scripts/activate-hooks.sh` is present for the self-heal escape hatch.
- `check-hook-activation.sh` (SessionStart awareness) is on the `install-global-assets.sh` machine-local track — not in the fork dir; not verifiable from cloud but consistent with the standard's documented distribution.

CI tier (fail-closed) correctly documented as deferred. "husky retired" — confirmed, no husky config in the fork. Best-effort ceiling ("bypassable via `git push --no-verify`") honestly stated.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
9 files including the hook entrypoints, gate configs, and the deployment contract (`custom/workflows/shared/deployment-to-prod.md`). Actively wired.

---

### STD-ESCALATE-001 — escalation-on-class-change

**Verdict: OK**

**Still true?**
Yes. The tripwire (§1 four signals a–d), the four-step response contract (state → name gateway → propose → proceed-unless-vetoed), the gateway map (§3), and the autonomy scoping rules (§4 halt-and-record under unattended runs) are all current and consistent with the workflows that implement it.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
11 files: `custom/workflows/implement/quick-spec/steps/step-01-understand.md`, `custom/workflows/implement/quick-dev/steps/step-03-execute.md`, `custom/workflows/implement/maintenance-triage/steps/step-03-emit-tech-specs.md`, `custom/workflows/design/design-router/steps/step-03-route.md`, `custom/workflows/design/design-elevation/steps/step-04-classify-and-route.md`, `custom/workflows/4-implementation/dev-story/workflow.md`. Actively referenced.

---

### STD-PERSONA-001 — workflow-personas

**Verdict: OK**

**Still true?**
Yes. The three voices (Rhea/design-handoff, Sol/quick-spec+quick-dev, Mara/escalation-on-class-change), the three sanctioned spots (opening re-orientation, risk acknowledgement, "I" for responsibility), and the placement-gate pointer to STD-PERSONA-002 are all current. The §6 binding table correctly maps each workflow to its persona.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
11 files: `custom/workflows/design/design-handoff/steps/step-01-gather.md`, `custom/workflows/design/design-handoff/steps/step-04-deliver.md`, `custom/workflows/implement/quick-spec/steps/step-01-understand.md`, `custom/workflows/implement/quick-spec/steps/step-04-review.md`, `custom/workflows/implement/quick-dev/steps/step-01-mode-detection.md`, `custom/workflows/implement/quick-dev/steps/step-07-deliver.md`, and `custom/workflows/meta/create-workflow/steps/step-03b-review.md`. Actively wired.

---

### STD-PERSONA-002 — persona-placement

**Verdict: OK**

**Still true?**
Yes. The three-condition gate (human-facing + distinct judgment + named-identity reduces confusion), the disqualifiers, and the §4 reconciliation with act-don't-menu are all sound and consistent with workflow-personas. The `create-agent` and `create-workflow` pointers are correct.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
6 files: `custom/workflows/shared/workflow-personas.md`, `custom/workflows/meta/create-workflow/steps/step-03b-review.md`, `custom/workflows/meta/create-agent/steps/step-01-brainstorm.md`, `custom/workflows/meta/create-agent/persona-content-contract.md`. Referenced by authoring-time gates.

---

### STD-CLOSEOUT-001 — close-out-contract

**Verdict: OK**

**Still true?**
Yes. The audience-first shape (active artifact → what changed → corrections → status → next-actor instructions), the process-narration prohibition, and the §4 workflow-patch routing rule are all current.

**Deterministic gate armed:**
`tools/validate-close-out-contract.js` runs as `npm run validate:close-out` AND in the pre-commit fast-path. Confirmed in `package.json:47`: `validate:close-out` is in the `test` script. Gate fires on narration phrases without adoption reference.

**Drifted/broke:** None detected. `contract_version: 1` in both places. The §2 owner-facing addendum (Outstanding design backlog) is correctly scoped as "PROBABILISTIC."

**Who uses it:**
12 files: `custom/workflows/design/design-handoff/steps/step-04-deliver.md`, `custom/workflows/design/design-handoff/workflow.md`, `custom/workflows/design/design-router/steps/step-03-route.md`, `custom/workflows/implement/quick-dev/steps/step-08-handoff.md`, `custom/workflows/4-implementation/dev-story/workflow.md`, and verify-lane close-outs. Actively referenced.

---

### STD-COMPLETION-001 — completion-contract

**Verdict: OK**

**Still true?**
Yes. The four-value enum (`pr_merged` / `pr_open` / `owner_gated_residue` / `advisory`), the invalid-exit rule (diagnosis with no disposition), the honest advisory escape hatch, and the enforcement honesty §5 are all current.

**Deterministic gate armed:**
`tools/check-completion-disposition.js` with `--strict` runs in `npm test` + pre-commit. Confirmed: `package.json:47` includes `check:completion -- --strict`. The arming provenance is honestly documented in the tool (`tools/check-completion-disposition.js:23–34`) — owner-directed ahead of elapsed soak; 0 likely gaps at arming.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
17 files. Broadly referenced: `custom/workflows/verify/webhook-contract-check/steps/step-04-report-and-route.md`, multiple audit-lane close-outs, design-handoff, quick-dev, dev-story, design-review, maintenance-triage. Heavily wired.

---

### STD-DIGEST-001 — behavior-update-digest

**Verdict: OK**

**Still true?**
Yes. The five-field Behavior Update Digest (`doctrine_delta` · `handoff_delta` · `story_candidate` · `owner_gated` · `completion_disposition`), the auto-execute mandate (§3), and the named callers are all current.

**Deterministic gate status:**
`check:digest` is WARN-ONLY, NOT in `npm test` (confirmed in `package.json`). Standard correctly documents this as "DEFERRED under warn-then-gate." The `check:digest` tool exists at `tools/check-digest-adoption.js`.

**Named callers verified:**
All 8 named callers reference STD-DIGEST-001: `custom/workflows/design/design-review/steps/step-01-audit.md`, `custom/workflows/verify/data-quality-audit/steps/step-04-route.md`, `custom/workflows/verify/scrape-coverage-audit/steps/step-04-classify-and-route.md`, `custom/workflows/verify/relational-coherence-audit/steps/step-04-classify-and-route.md`, `custom/workflows/verify/trace-flow/steps/step-06-suggest-ui.md`, `custom/workflows/verify/webhook-contract-check/steps/step-04-report-and-route.md`, `custom/workflows/implement/maintenance-triage/steps/step-03-emit-tech-specs.md`, `custom/workflows/meta/dispatch-followups/steps/step-04-generate-prompts.md`. Complete coverage confirmed.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
10 files. Complete audit-lane coverage.

---

### STD-CLAUDE-001 — claude-md-standard

**Verdict: OK**

**Still true?**
Yes. The global-vs-project CLAUDE.md split, the values-vs-contracts distinction, the canonical project shape, and the edit discipline are all sound. `cash-recovery` is correctly named as the reference project.

**Drifted/broke:**
Low cross-reference count within `custom/` (3 files: self + STANDARDS.md + parallel-sessions.md). This is expected for a governance meta-standard — it's consulted at authoring time, not invoked at runtime. The nudge hooks (`check-claude-md-drift.sh`, `check-claude-md-lint.sh`) are machine-local per the doc and not verifiable from cloud; their described behavior is consistent with the pattern established by other machine-local hooks.

**Drifted/broke:** None detected. `contract_version: 1` in both places.

**Who uses it:**
3 files within `custom/` (expected — authoring-time standard). The doc correctly notes the quarterly governance review as the cadence, which this review satisfies.

---

## STANDARDS.md self — additional finding

**The `skills-native/_shared/` two-copy requirement is stale.**

`STANDARDS.md:189` states:
> "Two physical copies of `shared/` (command-layout `custom/workflows/shared/` + the gitignored, sync-regenerated skills mirror `custom/skills-native/_shared/`) must carry the same versions; a divergence is itself drift."

`custom/skills-native/` does not exist in the current branch. The v6.8 skills architecture migration (`custom/MIGRATION-v6.8-skills-plan.md`) shows the pilot cutover (cash-recovery) uses `custom/skills/` delivery via the sync, not a `skills-native/_shared/` mirror. The STANDARDS.md statement is forward-looking prose from when that mirror was planned; it now describes something that has either been superseded or not yet implemented.

**Recommended fix:** Update STANDARDS.md §"Versioning, drift & breaking changes" to either (a) remove the `skills-native/_shared/` two-copy requirement if the architecture changed, or (b) note it as "planned, not yet active" per the fork's shipped-vs-designed discipline.

---

## Required actions

1. **STANDARDS.md** — bump `Version: v1` → `Version: v3` for STD-DEPLOY-001 (`STANDARDS.md:28`)
2. **STANDARDS.md** — bump `Version: v1` → `Version: v2` for STD-DELIVERY-001 (`STANDARDS.md:34`)
3. **STANDARDS.md** — update description for STD-PARALLEL-001 (`STANDARDS.md:65`) to include §D and §E
4. **STANDARDS.md** — fix or remove the `custom/skills-native/_shared/` two-copy requirement (`STANDARDS.md:189`)
5. **Local review only** — verify memory-doctrine home docs (`memory-library-discipline`, `memory-retrieval-policy`, `memory-hygiene`) against current behavior in a local session

---

*Review ran: 2026-07-01. Next scheduled review: 2026-Q4.*
