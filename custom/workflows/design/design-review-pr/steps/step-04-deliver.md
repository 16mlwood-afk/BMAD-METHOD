---
name: 'step-04-deliver'
description: 'Aggregate findings, evaluate the composite test, render the structured report, and optionally post it as a PR comment.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review-pr'
thisStepFile: './step-04-deliver.md'
---

# Step 4: Deliver

**Goal:** Take the accumulated `{findings}` from steps 02 and 03, evaluate the composite test, render the report in the format defined in `workflow.md`, and (optionally) post as a PR comment.

---

## AVAILABLE STATE

- `{findings}` — all findings from source-grep and dom-render lanes
- `{checklist.human_judgment}` — rules that require manual review
- `{affected_routes}` — surface scope
- `{chrome_available}` — for coverage-notes section
- `{pr_number}` — for optional `gh pr comment` invocation

---

## EXECUTION SEQUENCE

### 0. Classify every finding — truth (can fail) or advisory (a note)

Contract: `{project-root}/_bmad/bmm/workflows/design/shared/brief-binding-contract.md`. Owner, verbatim: *"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"*.

Before any severity is reported, give every finding in `{findings}` — and every finding the sections below add — a `binding` class:

- **`truth`** — the finding shows the surface could make a reader believe something false about the data, the money, the state of the work, or who may see what. Keeps its P0/P1 severity and is reported under **Fails**.
- **`advisory`** — everything else: styling, layout, composition, tokens, pills, colour, density, frame inventory, fingerprints. Reported under **Advisory notes** as `[advisory]`, severity capped at P2, never counted as a fail, never blocking.

**Fixed classes for the intrinsic checks:** `C-TRUTH-01` truth · `C-ANSWER-01` truth · `C-FIXTURE-01` truth (a fabricated surface that looks live) · `C-FINANCE-01` truth for a blended quantity+value cell, unlabelled mixed currency, or a representability/must-not-infer break — advisory for a leading-minus negative (a presentation convention) · `C-DECISION-01` truth for a stated probability/EV with no model behind it — advisory for a missing sizing basis · `C-RIGOR-01` truth only for a FABRICATED interval or baseline — advisory for a bare-but-honest figure · `C-ARCHETYPE-01` advisory · `C-IDENTFMT-01` advisory (truth only if the two forms would make a reader think they are different records) · `C-COMPOSITE-01` advisory · `F-FPSCAN-01` / fingerprint rules advisory.

**Checklist rules** (`docs/review-checklist.md`, not edited by this workflow): apply the one-question test above per rule and record the class next to the rule id in the report. When unsure, classify `advisory` and add one line to Coverage notes naming the rule — over-binding is the failure this step exists to prevent.

### 1. Evaluate C-COMPOSITE-01 (advisory)

Group `{findings}` by `route` (for dom-render lane) or by file (for source-grep lane). For each group:

- Count P1 findings.
- If ≥3 distinct advisory fingerprint rule IDs hit the same route/file, fire `C-COMPOSITE-01` as an `[advisory]` note with a recommendation:

> Composite fingerprint on `{route}` — {N} structural fingerprints detected: {rule_id_list}. A redesign pass would likely serve better than per-rule fixes; the compound effect won't be resolved by individual swaps. See `docs/design-policy.md` §5 Anti-default compositions. (Advisory — this does not fail the design.)

Roll the individual advisory fingerprints on that route into the composite note. Truth-class findings on that route are untouched.

### 1d. Evaluate C-TRUTH-01 — the brief's truth tests (truth — can fail)

For each route in `{brief_truth_map}`, for each test: apply its stated check to the changed render/diff (dom-render evidence when `{chrome_available}`, otherwise the source and a manual prompt). Record `pass | fail | not verifiable`.

- **fail** → a Fails entry: `**[fail] C-TRUTH-01 {test id}** — {statement}` · Evidence (what the surface shows) · Fix (the outcome to restore, never a prescribed layout) · Source: brief `{brief_filename}` Part 2.
- **not verifiable** (dom-render skipped and source is not decisive) → a manual prompt quoting the test and its check, answered pass/fail by the reviewer. Never report it as passing.

### 1e. Evaluate C-ANSWER-01 — the five-second answer (truth — can fail)

Always emitted for each affected route with a brief, as a reviewer prompt with a pass/fail answer:

```
**[manual → pass/fail] C-ANSWER-01** — Can a reader state this page's answer within five seconds?
- Route: {route}  ·  Brief: {brief_filename}  ·  Declared answer: "{page_answer}" (or "none — legacy brief")
- How to check: load the page, look for five seconds, look away, and say what it told you. Pass if that matches the declared answer (or, on a legacy brief, if you can say ANY clear answer). Fail if the answer is absent, below the fold, or crowded out by metadata, chrome or provenance.
- Frame inventory, column count and component choice are NOT part of this test.
```

A reviewer's `fail` is a Fails entry. When dom-render ran, the harvest's first-viewport text may be quoted to seed the prompt, but the verdict is a reader's, not a regex's.

### 1b. Evaluate C-ARCHETYPE-01 (advisory — every finding here goes to Advisory notes, per §0)

For each route in `{brief_archetype_map}`:

- **If dom-render ran** (`{chrome_available}`): step-03 §3b already emitted any contradiction as a P1 finding. Surface it in the P1 section with the declared archetype and brief filename:

  > Archetype mismatch on `{route}` — brief `{brief_filename}` declares `analytics_archetype: {archetype}`, but the rendered band ships {observed form}. {One-line expected form from `archetypes_path`.} Fix the band's form, or re-run `design-handoff` if the archetype itself is wrong (changing it is a material revision).

- **If dom-render was skipped** (Chrome unavailable): form-fit cannot be measured mechanically — emit a human-judgment manual prompt instead, so the report never implies the band was verified:

  ```
  **[manual] C-ARCHETYPE-01** — Band form must match declared archetype.
  - Route: {route}  ·  Brief: {brief_filename}  ·  Declared: {archetype}
  - What to check: does the band actually take the `{archetype}` form (see shared/analytics-archetypes.md)? A `coverage` brief must show gaps as content, not a trend strip; `ranking` must be sorted; every band element must drill. Verify in a browser — dom-render did not run.
  ```

**Reasoning check (rationale-aware).** The above verifies the rendered form matches the *declared* archetype. When the route's map entry has a `rationale` (resolved in step-01 §7), also verify the declaration itself was *sound* — a band can render exactly as declared while the declaration was an ungrounded guess. This consumes the `design-rationale-*` artifact; do it for each route whose `rationale != none`:

- **Cross-artifact consistency (P1 on mismatch).** The rationale's `analytics_archetype` MUST equal the brief's declared `analytics_archetype`, and its `accompanies_brief` MUST name this active brief. A mismatch means the artifacts diverged — typically the brief was hand-edited to a different archetype without re-running `design-handoff` (a forbidden material-change-as-hand-edit), or the rationale is stale:

  > Archetype record divergence on `{route}` — brief `{brief_filename}` declares `{archetype}` but its rationale `{rationale_filename}` records `{rationale_archetype}`. The decision record and the brief disagree; re-run `design-handoff` so the brief, rationale, and rendered band describe one archetype (changing the archetype is a material revision).

- **Reasoning completeness (note, not P1).** Confirm the rationale actually grounds the choice — the data-dimension + user-question pair is present, and the time-in-data check is present when the data carries time. If grounding is missing or the time-check is absent on time-bearing data, surface a `[note]` (not a hard finding — the band may still be correct; this flags an unaudited decision, not a defect):

  > {note} Archetype reasoning thin on `{route}` — rationale `{rationale_filename}` declares `{archetype}` without a grounded data-dimension + user-question pair{, and no time≠trend check despite time in the data}. Render matches, but the *choice* wasn't justified; worth a human look.

- **No rationale** (`rationale: none`): do nothing here — step-01 §7 already disclosed in coverage that reasoning was not verifiable for this route. Never emit a reasoning finding when there is no rationale to read.

### 1b-2. Evaluate C-RIGOR-01 (analytic depth, not shape — advisory, except a FABRICATED interval or baseline, which is truth; §0)

The *depth* counterpart to §1b. §1b checks the band took the right shape; this checks the surface reads like an analyst, not a schoolboy data-dump — and it fires on **any** decision surface in `{brief_rigor_map}`, band or not (a bandless `detail` buy page is the motivating case). For each route in `{brief_rigor_map}` (the rigor spec captured from the **brief §4d** in step-01 §7):

- **Hard finding (P1) — the unambiguous case ONLY.** A decision-bearing number the spec lists with a required `uncertainty` or `base_rate` renders with **neither** anywhere adjacent — no range, no confidence, no assumption, no baseline: a naked decision figure. This is the one rigor failure mechanical enough to assert — from a clear read of the changed render/diff (there is no dedicated rigor DOM harvest; rigor is judged semantically, and over-firing trains reviewers to ignore the check):

  > Naked decision number on `{route}` — the rigor spec (brief `{brief_filename}` §4d) requires `{metric}` to carry {its uncertainty / a base rate}, but it renders as a bare point estimate. Add the {range / confidence / assumption} and the {baseline} the spec names. If that data isn't available, surface it as the data gap the spec records — do NOT fabricate an interval. False precision is the worse failure.

- **Human-judgment prompt (always, when a spec exists).** Rigor is semantic — most of it cannot be asserted from the DOM. Emit a precise prompt seeded by the declared spec so the reviewer verifies depth against the actual render:

  ```
  **[manual] C-RIGOR-01** — Surface must read like an analyst's read, not a data dump.
  - Route: {route}  ·  Rationale: {rationale_filename}  ·  Rigor verdict at handoff: {rigor_verdict}
  - Lead read: does the surface state "{read_sentence}" (or its equivalent) BEFORE the evidence?
  - Decision numbers: does each of {list metrics} carry its uncertainty + base rate per the brief §4d spec?
  - Deciding field: do the charts show {deciding fields}, not the handy proxy?
  - Data gaps (do NOT treat as defects): {data_gaps or "none"} — these are enrichment requirements; a figure may honestly ship bare until the data exists.
  ```

- **No rigor spec** (route not in `{brief_rigor_map}`): do nothing here — step-01 §7 already disclosed in coverage that depth was not verifiable. Never emit a rigor finding when there is no spec to read, and never treat a named data gap as a rendering defect.

### 1b-3. Evaluate C-DECISION-01 (the executive layer — capital-commitment surfaces only; truth for an unmodelled probability/EV, advisory for a missing sizing basis; §0)

The *decision* counterpart, one rung above §1b-2 and the narrowest. §1b-2 checks the figures are an honest read; this checks the surface presents a **modelled, sized bet**. Runs ONLY for routes in `{brief_decision_map}` (those whose brief carries a §4e — a buy/reorder/sizing surface). Most routes have none → skip silently.

- **Hard finding (P1) — the unambiguous cases only.** From a clear read of the changed render/diff (there is no decision DOM harvest; decision quality is semantic):
  - a **buy / size recommendation rendered with no sizing basis** — a bare BUY/PASS or a suggested quantity with no tie to the loss tail / capital cap the §4e spec named; or
  - a **stated probability or expected value with no model behind it** — a "62% / E[ROI] X%" figure where §4e declared `verdict: single-scenario` (the decision was un-modellable), i.e. a confident distribution that the brief said cannot honestly exist.

  > Unmodelled decision on `{route}` — the decision spec (brief `{brief_filename}` §4e) frames a {modelled bet / single-scenario read}, but the surface renders {an unjustified BUY/PASS / a confident P(success) the spec flagged un-modellable}. Render the {sizing basis tied to the loss tail / honest single-scenario read + the named VOI gap}. A fabricated outcome distribution is the worse failure.

- **Human-judgment prompt (always, when a §4e spec exists).** Decision quality is mostly semantic — emit a precise prompt seeded by the spec:

  ```
  **[manual] C-DECISION-01** — Capital-decision surface must read like a modelled, sized bet.
  - Route: {route}  ·  Brief: {brief_filename} §4e  ·  Decision verdict at handoff: {decision_verdict}
  - Framed bet: does the surface state the stake + horizon + downside ({frame}), not just an ROI?
  - Outcome: is the decision a distribution (P(success)/EV/P10/P90) per §4e — or, if verdict is single-scenario, an HONEST point read with the VOI gap (and NOT a faked probability)?
  - Sizing: is the recommended quantity tied to the loss tail / capital cap ({sizing}), not a bare BUY/PASS?
  - Breakeven driver: is the swing input + its threshold shown ({sensitivity})?
  - Gaps (do NOT treat as defects): {decision_gaps or "none"} — enrichment requirements.
  ```

- **Not a decision route** (route not in `{brief_decision_map}`): do nothing — decision analysis does not apply (the norm). Never invent a decision finding on a dashboard/coverage/status surface.

### 1b-4. Evaluate C-FINANCE-01 (finance-semantics conformance — truth, except the parentheses-negative convention, which is advisory; §0)

The PR-time partner to `design-handoff`'s `finance-domain-pass`. Runs ONLY for routes in `{brief_finance_map}` (whose brief is `is_finance_surface` / carries §2b). Non-finance routes → skip silently. The mechanical sub-checks come from the step-03 §3d harvest; representability + accounting-truth are semantic.

- **Hard finding (P1) — unambiguous mechanical violations only** (from the §3d harvest): a monetary negative with a leading minus instead of parentheses; ≥2 currencies in one table with no per-row currency column; a cell blending a quantity and a monetary value.

  > Finance-semantics break on `{route}` — the brief (`{brief_filename}` §2b) requires {parentheses-negatives / single-currency-per-table / quantity-value separation}, but the surface renders {the offending cell, quoted}. {Render the negative as `(…)` / label currency per row / split quantity and value into separate columns.}

- **Human-judgment prompt (always, when a §2b contract exists):**

  ```
  **[manual] C-FINANCE-01** — Finance surface must preserve the brief's §2b semantics.
  - Route: {route}  ·  Brief: {brief_filename} §2b
  - Representability: for each required exception state ({exception_expectations}) — missing cost,
    negative/zero stock, reconciliation break, pending receipt, duplicate/exploded references — does
    the surface have somewhere to show it, or is it a silent gap?
  - Accounting truth: does the render honour {must_not_infer} (no invented figures/valuation; missing
    marked, not imputed)?
  - Open questions (do NOT treat as defects): {unresolved_assumptions or "none"} — surface, don't resolve.
  ```

- **Finance-shaped route with no §2b** (noted in coverage at step-01 §7): report "finance semantics not specified — not verifiable" + flag the possible handoff defect (`finance-domain-pass` may not have run). Never report it as passing.
- **Not a finance route** (not in `{brief_finance_map}`): do nothing — the norm.

### 1b-5. Evaluate C-FIXTURE-01 (fixture-backed production surface disclosure — truth; §0)

The PR-time guard for "fixture-backed surfaces are a governed state" (project `docs/design-policy.md` fixture-disclosure assertion + an optional `scripts/check-fixture-disclosure` gate). A production route rendering fabricated/mock data with no live read path must disclose it — an always-visible "not live data" affordance in page chrome plus a machine-readable fixture marker. Runs over `{fixture_backed_routes}` (built in step-02 §7). No fixture-backed route in scope → skip silently (the norm).

- **Hard finding (P1) — deterministic, ONLY where the project declares the contract.** Fires when `project_has_contract` is true (the project ships a `check-fixture-disclosure` script OR a design-policy fixture-disclosure assertion) AND the route is fixture-backed with `disclosure_present: false` — or the project's own `check-fixture-disclosure` exited non-zero for it. Never fire a hard finding where the project has NO declared contract (a project that has not adopted the policy cannot "violate" it — that is a human-judgment prompt below, not a P1; firing P1 there is the indiscriminate-gate failure):

  > Undisclosed fixture-backed surface on `{route}` — it renders the fixture module `{fixture_module}` with no live read path and no visible "not live data" disclosure, against the project's fixture-disclosure assertion (`docs/design-policy.md` / `scripts/check-fixture-disclosure`). Add the project's fixture banner + machine-readable marker, or wire the route to a live read-model. A fabricated surface that looks live is the failure.

- **Human-judgment prompt — the un-grep-able part, ALWAYS when a fixture-backed route exists.** Two things a regex cannot decide — disclosure-adequacy where the project has no declared contract, and the realistic-PII escalation:

  ```
  **[manual] C-FIXTURE-01** — Fixture-backed surface must be disclosed, and must not impersonate real records.
  - Route: {route}  ·  Fixture module: {fixture_module}  ·  Marker: {declared|heuristic}  ·  Project contract: {present|absent}
  - Disclosure: does the surface carry an unmistakable, always-visible "not live data" signal in page chrome (not a tooltip, not only a code comment)? {If contract absent: the project has no fixture-disclosure policy — is a live-looking fixture surface intended here, or should disclosure + a policy assertion be added?}
  - Realistic-PII escalation (FAIL unless waived): read {fixture_module}. Does it contain REALISTIC customer-like content — free-text comments, personal names, contactable identifiers (email/phone/address), order-linked PII — that could be mistaken for a real person's data? Fabricated PII MUST be obviously synthetic. If realistic → this FAILS: make it obviously synthetic or remove it, unless an explicit logged waiver (`// fixture-disclosure-ok: <reason>` or a PR note) justifies it.
  ```

- **No fixture-backed route** (`{fixture_backed_routes}` empty): do nothing — the norm. Never invent a fixture finding on a live or honest-empty surface.

### 1c. Evaluate C-IDENTFMT-01 (canonical-identifier formatting — advisory unless the forms would read as different records; §0)

For each route in `{affected_routes}`:

- **If dom-render ran** (`{chrome_available}`): step-03 §3c already emitted any contradiction as a P1 finding. Surface it in the P1 section quoting the divergent strings:

  > Identifier formatting inconsistent on `{route}` — the `{class}` record renders as {variant A} and {variant B} on the same surface (policy §13 "Canonical identifier": one consistent form everywhere; do not reformat per surface). Normalize at the render boundary to one form{, e.g. the label form already used for the sibling class}.

- **If dom-render was skipped** (Chrome unavailable): the cross-surface comparison cannot be made mechanically. If the step-02 source arm surfaced advisory C-IDENTFMT-01 candidates, fold them in; otherwise emit a human-judgment manual prompt so the report never implies identifier formatting was verified:

  ```
  **[manual] C-IDENTFMT-01** — Canonical identifiers must render one consistent form everywhere.
  - Routes: {affected_routes}  ·  Source-arm candidates: {list or "none surfaced"}
  - What to check: does each canonical-identifier class (supplier, marketplace, ASIN/SKU, order number) render in ONE casing/label form across cells and the list↔drawer? Any raw enum (AMAZON_ES) shown where a human label is expected? Policy §13. Verify in a browser — dom-render did not run.
  ```

### 2. Build manual-prompt section

For each rule in `{checklist.human_judgment}` whose `affected_routes` intersects `{affected_routes}`, emit a manual prompt:

```
**[manual] {rule_id}** — {statement}
- Affected pages: {routes}
- What to check: {detection guidance from checklist}
```

### 3. Render the report

Use the format from `workflow.md` §DELIVERABLE FORMAT. The report has these sections, in order, with empty sections OMITTED entirely:

1. **Summary** (always present) — verdict + counts table (Fails / five-second / Advisory / Manual).
2. **Fails — truth tests and the five-second answer** — only `truth`-class findings (step-04 §0), P0 before P1.
3. **Advisory notes** — every `advisory`-class finding, `[advisory]`, grouped by rule; `C-COMPOSITE-01` first when it fired.
4. **Manual reviewer prompts** — `C-ANSWER-01` first, then unresolved `C-TRUTH-01` checks, then `{checklist.human_judgment}` rules that intersect scope (each labelled truth or advisory).
5. **Coverage notes** (always present) — lanes that ran, lanes skipped (with reasons), rules with no diff context, and the checklist rules whose class was `advisory` by default because the one-question test was unsure.

### 4. Verdict line (in Summary)

Driven ONLY by truth-class findings and `C-ANSWER-01`. Pick one:

- **No fails, no advisory notes:** "✓ Design review clean — every truth test holds and the page's answer reads in five seconds."
- **No fails, advisory notes present:** "Design review passed — every truth test holds. {N} advisory note(s) for the designer to weigh; none blocks."
- **Five-second answer not yet judged:** append "The five-second answer check is waiting on a reviewer (C-ANSWER-01)."
- **Fails present:** "Design review found {N} truth failure(s){ and the five-second answer failed}. Merge should not proceed until these are resolved; {M} advisory note(s) do not block."

### 5. Coverage notes

Always emit a coverage section:

```
- source-grep: ran against {N} files, executed {M} rules, surfaced {K} findings.
- dom-render: {ran against {R} routes / skipped — Chrome not available}.
- human-judgment: {Q} rules surfaced as manual prompts.
- archetype conformance (C-ARCHETYPE-01): {checked {P} route(s) against declared briefs / deferred to manual — dom-render skipped / no brief-declared bands in scope}. {List any affected routes with no brief, which were NOT checked.} Reasoning verified against rationale for {S} of {P} route(s); {list routes with a declared band but no rationale artifact — reasoning NOT verifiable, only rendered form}.
- identifier formatting (C-IDENTFMT-01): {checked {R} route(s) in dom-render §3c / deferred to manual — dom-render skipped, source-arm surfaced {C} advisory candidate(s)}. §13(a) canonical-identifier consistency.
- analytic depth (C-RIGOR-01): {checked {Q} route(s) against a captured brief §4d rigor spec — {hard naked-number findings} + manual prompt(s) / no §4d specs in scope}. {List any affected routes that present decision figures but have no brief §4d — depth NOT specified (possible handoff defect).} Data gaps named in a spec are enrichment requirements, not defects.
- decision quality (C-DECISION-01): {checked {D} capital-decision route(s) against a captured brief §4e spec — {hard unmodelled/unsized findings} + manual prompt(s) / no §4e specs in scope (the norm — most routes commit nothing)}. A `single-scenario` verdict is honest, not a defect; a fabricated outcome distribution is the failure.
- finance semantics (C-FINANCE-01): {checked {F} finance-shaped route(s) against a captured brief §2b contract — {hard mechanical findings: parentheses-negative / mixed-currency / blended qty-value} + manual prompt(s) / no §2b in scope}. {List any finance-shaped routes with no brief §2b — semantics NOT specified (possible handoff defect).} Unresolved assumptions named in §2b are open questions, not defects.
- fixture disclosure (C-FIXTURE-01): {checked {X} fixture-backed route(s) — {Y} deterministic disclosure finding(s) (project contract present / check-fixture-disclosure script run) + manual prompt(s) for disclosure-adequacy + realistic-PII / no fixture-backed routes in scope}. The realistic-PII escalation is a human-judgment call, never asserted from grep; a hard P1 fires only where the project declares the disclosure contract.
- Rules with no diff context: {list of rule IDs that had nothing to check this PR}.
```

This section is critical for trust — it tells the reader exactly what the workflow did and didn't evaluate.

### 6. Optional: post as PR comment

If `--comment` flag was passed AND `{pr_number}` is set:

```bash
# Write report to a tempfile so the heredoc doesn't fight markdown
gh pr comment "$PR_NUMBER" --body-file /tmp/design-review-report.md
```

Otherwise, return the report as the workflow's final output.

---

## OUTPUT FORMAT — sample

```markdown
# Design Review (PR #1234)

## Summary

Design review passed — every truth test holds. 4 advisory note(s) for the designer to weigh; none blocks. The five-second answer check is waiting on a reviewer (C-ANSWER-01).

| Class | Count |
|---|---|
| Fails — broken truth test | 0 |
| Fails — five-second answer | not yet judged |
| Advisory notes | 4 |
| Manual | 3 |

## Advisory notes

**[advisory] S-STATUS-01** — Status pills are `rounded-md`, not `rounded-full`. (consistency rule — tradeable)
- File: `src/routes/(authed)/queries/[id]/+page.svelte:142`
- Evidence: `<Badge class="... rounded-full ...">`
- Suggestion: Replace `rounded-full` with `rounded-md`, or say why the departure is better.
- Source: policy §3

**[advisory] G-TYPO-03** — No `uppercase tracking-wide` labels.
- File: `src/lib/components/QueryHeader.svelte:24`
- Evidence: `class="uppercase tracking-wide ..."`
- Suggestion: sentence case with `text-sm font-medium text-muted-foreground`.
- Source: policy §4; standards Cat.2

...

## Manual reviewer prompts

**[manual → pass/fail] C-ANSWER-01** — Can a reader state this page's answer within five seconds?
- Route: `/queries` · Declared answer: "3 queries are waiting on you, oldest 4 days"

**[manual · advisory] T-TABLE-01** — Operational pages are table-first and full-width.
- Affected pages: `src/routes/(authed)/queries`
- What to check: Is the table the largest surface on the page? Do filters/summaries support it rather than competing?

...

## Coverage notes

- source-grep: ran against 12 files, executed 24 rules, surfaced 4 findings.
- dom-render: skipped — Chrome MCP not loadable in this session.
- human-judgment: 3 rules surfaced as manual prompts.
- Rules with no diff context: G-VISUAL-02, E-EXEMPLAR-01, E-EXEMPLAR-02 (no exemplar files in diff).
```

---

## FAILURE MODES

- **Reporting one finding per matched line when the same rule fires many times.** Group findings by `rule_id + file`. Show the first 3 occurrences with a "+N more" footer if there are more.
- **Hiding the composite note.** If `C-COMPOSITE-01` fires, it appears first in the Advisory notes. The individual fingerprints are secondary.
- **Failing a design on advice.** A style, layout, composition, token or frame-inventory finding reported as a fail. Classify first (§0); only `truth` findings and `C-ANSWER-01` can fail.
- **Reporting "everything's fine" when dom-render was skipped.** If dom-render didn't run, the report can't claim the page is clean — only that source-grep found nothing. The coverage-notes section must make this explicit.
- **Posting a PR comment without `--comment`.** This workflow defaults to printing the report; it only mutates GitHub state when the user explicitly opts in.
