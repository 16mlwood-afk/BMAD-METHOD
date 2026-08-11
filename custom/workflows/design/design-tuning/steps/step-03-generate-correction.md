---
name: 'step-03-generate-correction'
description: 'Generate a paste-ready correction message for Claude Design and persist iteration state'
---

# Step 3: Generate Correction

**Progress: Step 3 of 4** — the correction/approval message. Gate 3 (step-04) follows.

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- The correction message must be PASTE-READY — the user copies it directly into Claude Design with no editing.
- Write for Claude Design as the audience, not the user. Be direct, specific, and imperative.
- Organize violations by priority — hard failures first, issues second.
- Always include "what to keep" — Claude Design tends to throw everything out and start over if it only receives criticism.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## AVAILABLE STATE

From steps 01–02:
- `{feature_name}`, `{brief_path}`, `{iteration_number}`
- `{brand_identity_path}`, `{policy_constraints}` — policy loaded directly in step-01
- `{brief_constraints}`, `{corporate_guardrails}`, `{visual_references}`
- `{brief_drift}` — list of drift items found by step-02 contradiction scan (may be empty)
- `{policy_overrides_brief}` — boolean set by step-02 when brief drifted from policy
- `{current_violations}`, `{fixed_violations}`, `{kept_elements}`
- `{previous_violations}`
- `{has_unresolved_issues}` — boolean set by step-02 §7; `true` when ≥1 issue-severity finding is outstanding. Splits a PASS into PASS-CLEAN (clean approval) vs PASS-WITH-ISSUES (approval that carries the issues into implementation).

## SEQUENCE OF INSTRUCTIONS

### 1. Determine Output Type

Based on the overall assessment from step-02 §7:

- **Assessment = PASS** (0 hard failures AND `{coverage_partial} = false` AND `{treatment_unverified} = false`): Generate an APPROVAL message — section 5. Two sub-paths there, chosen by `{has_unresolved_issues}`:
  - **PASS-CLEAN** (`{has_unresolved_issues} = false`): an unqualified approval.
  - **PASS-WITH-ISSUES** (`{has_unresolved_issues} = true`): an APPROVED-WITH-ISSUES message — no hard failure blocks the design, but the issue-severity findings are carried in a mandatory **Issues to resolve** block so they get fixed at implementation rather than silently shipped. A clean approval is NOT permitted while any issue is outstanding; this is the gate that stops a polished render from auto-passing on "0 hard failures."
- **Assessment = FAIL** (1+ hard failures, regardless of coverage): Generate a correction message. Continue to section 2.
- **Assessment = PARTIAL** (0 hard failures BUT `{coverage_partial} = true` OR `{treatment_unverified} = true`): Generate a PARTIAL-STATUS message — list everything that's resolved, list the prior keepers that re-verified cleanly, and explicitly name what blocks approval. Two blockers can land here:
  - **Missing screens** (`{coverage_partial}`) — name the screens that must be rendered.
  - **Treatment unverified** (`{treatment_unverified}`) — the artifact source was absent, so the treatment lane (ring/opacity, radius, spacing, color, dot) ran blind. Name it: "treatment checks unverified — provide the Claude Design artifact URL so ring/radius/color are read exactly, not eyeballed." This is the iter-4 V18 blocker: never certify a treatment from pixels.

  The PARTIAL-STATUS path does NOT emit an APPROVAL and does NOT emit a corrective directive; it emits a "design is on track but cannot be approved until you provide X" status message. The user pastes that status message back to themselves (or to Claude Design as a "please render the missing screens" request) — it is not a correction to send Claude Design. See section 5a for the PARTIAL-STATUS template.

Refusing to emit APPROVAL on PARTIAL is the workflow's defense against approval-by-omission: a clean record on 3 of 5 screens is not evidence that screens 4 and 5 are clean — and a pixel-eyeballed pill is not evidence the treatment matches.

### 2. Build the Correction Message

Use this structure for `{correction_message}`:

```markdown
**Iteration {iteration_number} feedback. {X} violations found — {Y} are hard failures.**

{If iteration > 1:}
**Progress from V{N-1}:** {count} violations fixed: {list fixed items}. {count} still remain.

**Violations — fix these before iterating on anything else:**

{For each violation, ordered by severity (hard-failure first):}
**{ID}. {Short title}** ({category})
{What the brief/guardrail says — quote the constraint.}
{What the mockup shows instead — be specific about what you see.}
{If visual reference exists: "Reference: {product} does {X} — match that pattern."}

**What to keep — do NOT change these:**
{For each kept element:}
- {Specific element that works and why}

**Visual direction reminder:**
{If visual_references populated, restate the product anchors and what to borrow from each — Claude Design may lose context across iterations.}

**All other constraints from the original brief still apply.** Re-read sections {relevant section numbers} if needed.
```

### 3. Self-Review the Correction Message

Before finalizing, verify:

- [ ] Every violation cites a specific constraint from the brief (section number or guardrail name)
- [ ] Every violation describes what the mockup shows (not just "this is wrong")
- [ ] No design opinions injected — every critique traces to a written constraint
- [ ] "What to keep" section is non-empty (even if the mockup is poor, something works)
- [ ] Visual references restated (if applicable) — Claude Design loses context between messages
- [ ] Message is addressed to Claude Design, not to the user
- [ ] No ambiguous language ("consider", "maybe", "you might want to") — use imperatives ("fix", "remove", "change to")
- [ ] Content-lane (§13a identifier/value-formatting) findings are phrased as **render-boundary display-format normalization** ("render `marketplaceBuy` as the label form 'Amazon ES', matching the sell-side 'Amazon UK'"), naming one consistent target form per identifier class — NOT as a data/schema change (stored enums are untouched). Quote the divergent rendered strings.

### 4. Persist Iteration State

Write (or update) the state file at `{state_file_path}`:

```markdown
---
feature: {feature_name}
brief: {brief_path}
iteration: {iteration_number}
date: {date}
status: {iterating | approved}
---

# Design Tuning State: {feature_name}

## Current Status

Iteration: {iteration_number}
Assessment: {PASS | FAIL}
Violations: {count}
Fixed this round: {count}

## Visual References

{visual_references — persisted here so subsequent iterations can load them without the user re-providing}

## Violation History

### Iteration {N}

| ID | Category | Severity | Description | Status |
|----|----------|----------|-------------|--------|
{table of all violations with their status}

{Include previous iteration tables too — append-only history}

## Kept Elements

{List of elements that work well, accumulated across iterations}
```

### 5. Generate Approval Message (if assessment == PASS)

If `{assessment} == PASS` (0 hard failures AND `{coverage_partial} == false` AND `{treatment_unverified} == false`), branch on `{has_unresolved_issues}`.

**5 (clean) — PASS-CLEAN (`{has_unresolved_issues} == false`):**

```markdown
**Design approved — iteration {iteration_number}.**

All constraints from the design brief are satisfied. No corporate guardrail violations. No craft or legibility issues. Visual direction aligns with references. All required screens were inspected.

**Approved elements:**
{List all kept_elements}

**Ready for implementation.** The design can now be handed to the dev workflow.
```

Update the state file with `status: approved`.

**5 (with issues) — PASS-WITH-ISSUES (`{has_unresolved_issues} == true`):** the design has no hard failures, but ≥1 issue-severity finding (a §2 Craft & legibility row, a §4 typography/monospace issue, a §11 dropdown issue, a non-systemic content slip). Do NOT emit the clean approval above. Emit this instead:

```markdown
**Design approved with issues — iteration {iteration_number}.** {N} issue(s) to resolve at implementation; 0 hard failures.

No hard failure blocks this design — the composition, treatment, and §13 coherence hold. But the following issue-severity findings must be resolved when the design is implemented (or fed back to Claude Design if you want them fixed in the mock first). They are real policy deviations, just not page-failing ones — shipping them is the "polished but thoughtless" miss this gate exists to catch.

**Issues to resolve (do not ship as-is):**
{For each issue-severity item in current_violations, ordered most-impactful first:}
**{ID}. {Short title}** ({category}, {lane})
{What the policy says — quote the section.} {What the render shows.} {The one-line fix.}

**Approved elements — keep these:**
{List all kept_elements}

**Next:** these are implementation-time fixes, not a redesign. Hand to design-implement (it folds the issue fixes into the build), or paste the issue list to Claude Design first if you want the mock corrected before implementation.
```

Update the state file with `status: approved-with-issues` and persist the issue list so a re-run recognizes which issues were carried forward.

### 5a. Generate PARTIAL-STATUS Message (if assessment == PARTIAL)

If `{assessment} == PARTIAL` (0 hard failures BUT `{coverage_partial} == true` and/or `{treatment_unverified} == true`):

```markdown
**Iteration {iteration_number}: PARTIAL — on track but cannot approve.**

No hard failures on what could be verified. The blocker(s):
{if coverage_partial:}— coverage: {N} screen(s) from the brief's required edge-state list were not rendered or not included.
{if treatment_unverified:}— treatment unverified: no design artifact source this round, so ring/opacity, radius, spacing, color, and dot-presence could not be read exactly — they were eyeballed-only and are NOT certified.

{if coverage_partial:}**Missing screens (block approval):**
{For each item in missing_screens:}
- {screen name as listed in the brief}

{if treatment_unverified:}**Treatment checks blocked (block approval):**
- Provide the Claude Design artifact URL (the share link / canvas). I'll fetch the bundle and compare ring/radius/color exactly against the canonical component, instead of guessing from the PNG. {list the treatment-class surfaces left unverified, e.g. "status pill, filter chip"}

**Status of what WAS verified:**
{For each fixed_violations item from §6: "✓ {ID} resolved on {screen} ({lane})"}
{For each previous keeper that re-verified in §6a: "✓ {keeper} held"}

**Next step:** {if coverage_partial: "drop screenshots of the missing screens"}{if both: " and "}{if treatment_unverified: "paste the Claude Design artifact URL"} here. I will not emit an approval until every required screen is inspected and every treatment is read from source — partial-coverage approval and pixel-eyeballed treatment are the silent-failure modes this workflow exists to prevent (see workflow.md SOURCE-OF-TRUTH PRECEDENCE, step-02 §1a and §0a).
```

Update the state file with `status: partial-pending-coverage` (or `partial-pending-treatment` if coverage is complete but treatment is unverified; `partial-pending-coverage-and-treatment` if both) and persist `{missing_screens}` + `{treatment_evidence_mode}` so the next iteration recognizes the gap is closed when the screens and/or the artifact URL arrive.

### 5b. Brand Identity Feedback (on PASS-CLEAN approval only)

Run this ONLY on a PASS-CLEAN approval (`{has_unresolved_issues} == false`). A PASS-WITH-ISSUES design has outstanding craft/legibility deviations — do not nominate it as a new reference page or exemplar until those are resolved; recommending a flawed surface as the bar is how drift enters the policy.

When a design is approved AND `{brand_identity_path}` exists, evaluate whether the brand identity should be updated:

**Check for new reference page candidates:**
If the approved design is notably well-executed, suggest adding it to the brand identity's section 6 (Reference Pages):
> "Consider adding {feature_name} at {route} to the brand identity's reference pages — its {specific quality} sets a new bar."

**Check for new anti-patterns discovered:**
If any violation persisted for 3+ iterations before being fixed, it's a pattern Claude Design is strongly biased toward. Suggest adding it to the brand identity's section 9 (AI Fingerprint Sensitivity):
> "Claude Design repeatedly produced {pattern} despite explicit prohibition. Consider adding this to the brand identity's AI sensitivity table."

**Check for brand identity drift:**
If the approved design intentionally deviated from any brand identity value (e.g., used a different badge pattern that looked better), flag it:
> "The approved design uses {new pattern} instead of the brand identity's stated {old pattern}. If this is intentional, update the brand identity to reflect the new direction."

Output these suggestions in a `**Brand Identity Updates**` section after the approval message. Do NOT modify the brand identity file directly — surface the suggestions for the user to review.

### 6. Present to User

Display to the user:

1. **Summary line:** "Iteration {N}: {PASS-CLEAN | PASS-WITH-ISSUES | FAIL | PARTIAL} — {X} violations ({Y} hard failures, {W} issues), {Z} fixed from last round{, missing N screen(s) if PARTIAL}". Never report a bare "PASS" when issues are outstanding — say "PASS-WITH-ISSUES — N issues to resolve" so the issue count is in the headline, not buried.
2. **The full correction / approval / approved-with-issues / partial-status message** inside a clearly marked block — ready to copy
3. **Brief drift report** (if `{policy_overrides_brief}` = true). For each item in `{brief_drift}`, print:
   > **Brief drift detected — policy wins.** The brief at `{brief_path}` softens a rule from `{brand_identity_path}`. This run evaluated against the policy, not the brief.
   > - Rule: `{rule}`
   > - Policy says: `{policy_text}`
   > - Brief says: `{brief_text}` *(drift type: {drift_type})*
   >
   > Fix the brief (edit the bullet to match the policy verbatim) OR if the policy itself should change, run `modify-design-policy`. Do not leave the brief drifted — every downstream review and tuning run will re-detect this.
4. **Brand identity update suggestions** (if any — PASS-CLEAN only)
5. **Next step instruction:**
   - If FAIL: "Paste the message above into Claude Design. Drop the next screenshot here when ready."
   - If PASS-CLEAN: "Design approved. Run the design-implement workflow to bring the approved design into the codebase. For a single, isolated component change, quick-dev may be sufficient."
   - If PASS-WITH-ISSUES: "Approved with {N} issue(s). Run design-implement — it folds the listed issue fixes into the build. Or paste the Issues block to Claude Design first if you'd rather correct the mock before implementing. Do not ship the design without resolving the issues."
   - If PARTIAL: "Drop screenshots of the missing screens listed above and re-invoke design-tuning. The status message is for your records; do not send it to Claude Design as a correction."

---

## SUCCESS METRICS

- Correction message is paste-ready (no user editing needed)
- Every violation traces to a specific brief constraint
- "What to keep" section prevents Claude Design from starting over
- State file persisted with full violation history
- Visual references persisted for subsequent iterations
- User has clear next step

## FAILURE MODES

- Generating a correction that requires the user to edit it before pasting
- Forgetting to restate visual references (Claude Design loses context between messages)
- Writing "consider doing X" instead of "do X" — Claude Design responds better to direct imperatives
- Not persisting state — losing iteration tracking between invocations
- Approving a design that still has hard failures
- **Approving on `{coverage_partial} == true`.** PASS requires both 0 hard failures AND full screen coverage; emit PARTIAL-STATUS when coverage is incomplete and refuse to send Claude Design a correction (the gap is on the user's side, not the design's). See §5a.
- **Sending the PARTIAL-STATUS message to Claude Design as a correction.** That message is a status-for-the-user; Claude Design would treat it as a directive to redesign the screens it has already shown. The next step is the user dropping the missing screens, not Claude Design producing new ones.

---

## NEXT STEP

Read fully and follow `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-04-emit-critique.md` — **Gate 3 (design-closure)**. It classifies every finding this run produced into exactly one lane, emits the durable `design-critique-{target_slug}-{date}.md`, routes accepted brief-gap findings into Gate 2, and runs the one bounded correction pass. Do not end the workflow at this step: without step-04 the classification survives only as this conversation, which is the gap Gate 3 exists to close.
