---
deferred_work_file: '{implementation_artifacts}/deferred-work.md'
---

# Step 4: Review

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- No human interaction: do not ask questions or wait for approval in this step.
- Review subagents get no prior session context.
- All review subagents must run at the same model capability as the current session.
- **The commit at the end of this step is GATED (safety layer rule 5).** It runs only after the COMMIT GATE below passes. A failed gate item HALTs the run `blocked` — it does NOT commit and hope a follow-up review catches it.

## INSTRUCTIONS

Change `{spec_file}` status to `in-review` in the frontmatter before continuing.

### Construct Diff

Read `{baseline_revision}` from `{spec_file}` frontmatter. If `{baseline_revision}` is missing or `NO_VCS`, use best effort to determine what changed. Otherwise, construct `{diff_output}` covering all changes — tracked and untracked — since `{baseline_revision}`.

Do NOT `git add` anything — this is read-only inspection.

### Review

Launch each reviewer as a SEPARATE subagent via the Agent tool, in parallel (one message, multiple Agent calls), with no prior session context. Both run at the same model capability as this session.

**Mechanism — read before launching.** A subagent is launched with a `subagent_type` drawn from the AGENT registry (e.g. `general-purpose`). A SKILL name is NOT an agent type — never pass `bmad-review-*` (or any skill name) as `subagent_type`; the launch errors with "Agent type not found". Each reviewer's method is one of the fork's review skills, which the subagent invokes via its own Skill tool.

- **Blind hunter** — `subagent_type: general-purpose`. Receives inline `{diff_output}` only (no spec, no context docs). Its prompt: invoke the `bmad-review-adversarial-general` skill on `{diff_output}`, and read no other project file (diff-only judgment).
- **Edge case hunter** — `subagent_type: general-purpose` (it needs project read access to confirm/refute edge cases). Receives `{diff_output}` and read access to the project. Its prompt: invoke the `bmad-review-edge-case-hunter` skill on `{diff_output}`.

If subagents are not available at all, HALT with status `blocked` and blocking condition `no subagents` (see workflow.md Subagents).

### Classify

1. Deduplicate all review findings.
2. Assign severity to each finding by consequence for the artifact's main consumer (software user, document reader, etc).
   Disregard any severity assigned by a reviewing subagent. Review subagents operate under by-design information asymmetry and do not have enough context to set final severity for this workflow.
   - `low`: none or cosmetic
   - `medium`: tolerable
   - `high`: intolerable
3. Route each finding into exactly one triage category. The first three categories are **this story's problem** — caused or exposed by the current change. The last two are **not this story's problem**.
   - **intent_gap** — caused by the change; cannot be resolved from the spec because the captured intent is incomplete. Do not infer intent unless there is exactly one possible reading.
   - **bad_spec** — caused by the change, including direct deviations from spec. The spec should have been clear enough to prevent it. When in doubt between bad_spec and patch, prefer bad_spec — a spec-level fix is more likely to produce coherent code.
   - **patch** — caused by the change; trivially fixable without human input. Just part of the diff.
   - **defer** — pre-existing issue not caused by this story, surfaced incidentally by the review. Collect for later focused attention.
   - **reject** — noise. Drop silently. When unsure between defer and reject, prefer reject — only defer findings you are confident are real.
4. Append a new entry to the `## Review Triage Log` section in `{spec_file}`, in this format:
   ```markdown
   ### {date} — Review pass
   - intent_gap: count
   - bad_spec: count
   - patch: count
   - defer: count
   - reject: count
   - addressed_findings:
     - `[high|medium|low]` `[patch|bad_spec]` <finding summary and action taken in this pass>
   ```
   Where `count` is either just `0`, or total with breakdown by severity `N: (high Nhigh, medium Nmedium, low Nlow)`.
   If no patch was fixed and no bad_spec repair loopback was triggered in this pass, write:
   ```markdown
   - addressed_findings:
     - none
   ```
5. Process findings in cascading order. If intent_gap exists, lower findings are moot; follow the intent_gap branch below. If bad_spec exists, lower findings are moot since code will be re-derived. If neither exists, process patch and defer normally. Before each bad_spec loopback, read `{spec_file}` frontmatter `review_loop_iteration` (missing means `0`), increment it by 1, and write it back. If it exceeds 5, append the triage-log entry for this pass with `addressed_findings: none`, then HALT with status `blocked` and blocking condition `review repair loop exceeded 5 iterations (non-convergence)`.
   - **intent_gap** — Root cause is inside `<intent-contract>`. Revert code changes. Append the triage-log entry for this pass with `addressed_findings: none`, then HALT with status `blocked`, blocking condition `intent gap in intent contract`, and include the intent-gap findings.
   - **bad_spec** — Root cause is outside `<intent-contract>`. Do not modify content inside `<intent-contract>`. Before reverting code: extract KEEP instructions for positive preservation (what worked well and must survive re-derivation). Revert code changes. Read the `## Spec Change Log` in `{spec_file}` and strictly respect all logged constraints when amending the sections outside `<intent-contract>` that contain the root cause. Append a new change-log entry recording: the triggering finding, what was amended, the known-bad state avoided, and the KEEP instructions. Append the triage-log entry for this pass, listing every bad_spec finding that triggered the spec amendment and implementation loopback under `addressed_findings`. Read fully and follow `{project-root}/_bmad/bmm/workflows/4-implementation/dev-auto/steps/step-03-implement.md` to re-derive the code, then this step will run again.
   - **patch** — Auto-fix. These are the only findings that survive loopbacks. After auto-fixing, append the triage-log entry for this pass, listing every patch fixed in this pass under `addressed_findings`.
   - **defer** — Append one new entry to `{deferred_work_file}` using this format. Do not modify existing entries or look for duplicates.
     ```markdown
     - source_spec: `{spec_file}`
       summary: <one sentence>
       evidence: <why this is real>
     ```
   - **reject** — Drop silently.

---

## COMMIT GATE (safety layer rule 5 — run before Finalize, every pass that would commit)

The commit below is the loop's only side effect on the codebase. It runs ONLY when every applicable item here passes. Any failure → HALT with status `blocked` and the named blocking condition. Do NOT commit a change that fails a gate item and rely on a later review to catch it — there is no human in this loop.

1. **Grounding held.** The run cleared step-01's grounding gate (verb + target) and no intent_gap remained unresolved. (An unresolved intent_gap already HALTed above — this is the final confirmation that what was built matches grounded intent, not an inferred one.)

2. **Provenance respected.** For every existing line this change modified or removed, the step-03 existing-code provenance pre-flight was honored: any deliberate guard touched has its originating commit SHA + preserved invariant recorded, and the protected case is still covered by a passing test. If a deliberate guard was undone without coverage → HALT with blocking condition `would undo a deliberate guard without coverage`.

3. **Brownfield regression surface (REQUIRED for `project_phase: brownfield` or `mixed`; skip only for `greenfield`).** For each function, component, or schema field this change modified:
   - **Callers identified** — grep the symbol / trace imports; list every caller or dependent that consumed the old behavior.
   - **No callers broken** — type-checked or compiled with no new errors; if the affected files have tests, they pass; if not, the absence of tests is itself noted.
   - **Behavior contract documented** — for a non-trivial change, a one-sentence "before → after" of the contract (recorded in `{spec_file}` `## Design Notes`).
   - **Rollback path known** — one sentence on how to revert if production breaks (the `baseline_revision` is the anchor).

   Record the result in `{spec_file}` as a Regression Surface table:
   ```markdown
   | Symbol Touched | Callers | Tests Pass? | Rollback |
   |---|---|---|---|
   | matchSupplier() | invoices.tsx, queries.tsx, admin/match-batch | yes (3 unit) | revert to baseline_revision; no schema change |
   ```
   If you cannot satisfy every box, the change is not done: HALT with status `blocked` and blocking condition `regression surface not clean`. Do NOT commit.

4. **Tests & diagnostics proven, not asserted** (`{project-root}/_bmad/bmm/workflows/shared/diagnostics-gate.md`). Run the project's test and type/compile checks. If ANY new diagnostic surfaced (type error, "cannot find module", lint/compile failure) — including after a bad_spec re-derivation loop — re-run the relevant check in the current tree and confirm zero errors. Quote the result. Do NOT reason a diagnostic away as "stale": a true-stale diagnostic disappears on re-run, and that disappearance is the proof. If a real diagnostic remains → HALT with status `blocked` and blocking condition `diagnostics not green`.

Only when items 1–4 all pass may you proceed to Finalize and commit.

---

## Finalize

Prepare `Auto Run Result` details:
- Summary of implemented change
- Files changed with one-line descriptions
- Review findings breakdown: patches applied, items deferred, items rejected
- COMMIT GATE result: grounding/provenance/regression-surface/diagnostics, each pass/skip(greenfield) with one-line evidence
- Follow-up review recommendation: `true` when the final review pass made review-driven changes significant enough to benefit from an independent follow-up review; otherwise `false`. Use judgment, not a fixed numeric threshold. Base the judgment on the final pass's triage log and fixes, including patched-finding volume, consequence/severity, breadth, behavior/API/security/data impact, and implementation complexity. Many low-severity patched findings can be significant by volume. Do not recommend follow-up for only a few localized low-consequence fixes.
- Verification performed, including command outcomes or manual inspection notes
- Any residual risks

Set `{spec_file}` frontmatter `followup_review_recommended` from the judgment above.

If version control is available, commit (the COMMIT GATE passed). Include in the commit message any preserved-guard SHA + invariant recorded in step-03. **Do not push** — distribution beyond the local commit is reserved for `on_complete` on a `done` status (see workflow.md HALT, on_complete distribution gate).

HALT with status `done`.
