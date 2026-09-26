---
name: 'step-03-generate-correction'
description: 'Generate a paste-ready correction message for Claude Design and persist iteration state'
---

# Step 3: Generate Correction

**Progress: Step 3 of 4** — the correction/approval message. Gate 3 (step-04) follows.

**Close-out shape.** Emit the close-out per `shared/close-out-contract.md` — audience-first, process
narration forbidden by default, and the **§2a two-block shape**: plain answer first; at most one
fenced `FOR YOUR LLM ADVISER` block carrying actionable detail only (state-file path, violation
IDs, iteration number), never a voice and never raw trace. The `persona_slot` (workflow.md → OUTPUT
CONTRACT & VOICE SLOT) may speak in block 1 only. **The correction message to Claude Design is not
a close-out** — it is a directive to a downstream consumer and keeps its existing imperative form.

**Close-out shape.** Emit the close-out per `shared/close-out-contract.md` — audience-first, process
narration forbidden by default, and the **§2a two-block shape**: plain answer first; at most one
fenced `FOR YOUR LLM ADVISER` block carrying actionable detail only (state-file path, violation
IDs, iteration number), never a voice and never raw trace. The `persona_slot` (workflow.md → OUTPUT
CONTRACT & VOICE SLOT) may speak in block 1 only. **The correction message to Claude Design is not
a close-out** — it is a directive to a downstream consumer and keeps its existing imperative form.

**Close-out shape.** Emit the close-out per `shared/close-out-contract.md` — audience-first, process
narration forbidden by default, and the **§2a two-block shape**: plain answer first; at most one
fenced `FOR YOUR LLM ADVISER` block carrying actionable detail only (state-file path, violation
IDs, iteration number), never a voice and never raw trace. The `persona_slot` (workflow.md → OUTPUT
CONTRACT & VOICE SLOT) may speak in block 1 only. **The correction message to Claude Design is not
a close-out** — it is a directive to a downstream consumer and keeps its existing imperative form.

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- The correction message must be PASTE-READY — the user copies it directly into Claude Design with no editing.
- Write for Claude Design as the audience, not the user. Be direct and specific.
- **Two registers, never mixed** (`{project-root}/_bmad/bmm/workflows/design/shared/brief-binding-contract.md`). Truth failures are **required outcomes**, stated imperatively and as the outcome to restore, never as a layout. Advisory notes are **suggestions Claude Design may trade** — say what was noticed and why it may matter, and leave the call to the designer. Claude Design does the heavy lifting.
- Organize by binding — truth failures (and T0) first, advisory notes second (strong weight before normal).
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
- `{truth_results}`, `{page_answer}` — step-02 §2c; T0 and every truth test with pass / fail / not judgeable
- `{has_unresolved_issues}` — boolean set by step-02 §7; `true` when ≥1 advisory note is outstanding. Splits a PASS into PASS-CLEAN vs PASS-WITH-NOTES (approval that carries the notes forward as advice).

## SEQUENCE OF INSTRUCTIONS

### 1. Determine Output Type

Based on the overall assessment from step-02 §7:

- **Assessment = PASS** (0 truth failures AND T0 `pass` or `no declared answer` AND `{coverage_partial} = false`): Generate an APPROVAL message — section 5. Two sub-paths there, chosen by `{has_unresolved_issues}`:
  - **PASS-CLEAN** (`{has_unresolved_issues} = false`): an unqualified approval.
  - **PASS-WITH-NOTES** (`{has_unresolved_issues} = true`): an APPROVED-WITH-NOTES message — every truth test holds, and the advisory notes travel with the design in an **Advisory notes** block for Claude Design and the implementer to weigh. The notes are not conditions of approval. (Formerly PASS-WITH-ISSUES, which withheld a clean approval on advice.)
- **Assessment = FAIL** (1+ truth failures, or T0 `fail`): Generate a correction message. Continue to section 2. Advisory notes ride along in the same message, below the truth failures, as suggestions.
- **Assessment = PARTIAL** (0 truth failures BUT a truth test could not be judged — `{coverage_partial} = true`, or the page's first screen was missing so T0 could not be read): Generate a PARTIAL-STATUS message — list everything that's resolved, list the prior keepers that re-verified cleanly, and name each truth test waiting on a state that was not shown.

  `{treatment_unverified}` on its own is **not** a PARTIAL blocker any more — treatment (ring, radius, spacing, colour, dot) is advisory. It is listed among the notes: "treatment not read from source this round — paste the Claude Design artifact URL if you want it checked exactly." Never claim an unread treatment is resolved; equally, never hold an approval for it.

  The PARTIAL-STATUS path does NOT emit an APPROVAL and does NOT emit a corrective directive; it emits a "design is on track but cannot be approved until you provide X" status message. The user pastes that status message back to themselves (or to Claude Design as a "please render the missing state" request) — it is not a correction to send Claude Design. See section 5a for the PARTIAL-STATUS template.

Refusing to emit APPROVAL on PARTIAL is the workflow's defense against approval-by-omission **on truth**: a truth test that held on 3 screens is not evidence it holds in the state nobody rendered. A suggested frame nobody drew is not that case — it is a note.

### 2. Build the Correction Message

Use this structure for `{correction_message}`:

```markdown
**Iteration {iteration_number} feedback. {Y} truth failure(s){, and the five-second answer failed}. {W} advisory note(s).**

{If iteration > 1:}
**Progress from V{N-1}:** {count} fixed: {list fixed items}. {count} still remain.

**Must be true — fix these first:**

{If T0 failed:}
**T0. The page's answer.** A first-time reader must get *"{page_answer}"* within five seconds. Right now the first thing they read is {what the screen leads with}. How you make the answer dominate is yours to decide.

{For each binding: truth finding:}
**{ID}. {test id} — {test statement}** ({category})
{What the screen shows that breaks it — be specific.}
{The outcome to restore, in one sentence — never a prescribed layout.}

**Advisory — your call:**

{For each binding: advisory note, strong weight first:}
**{ID}. {Short title}** ({category}{, `[tradeable]` if the rule exists only for consistency})
{What was noticed and the rule or reference it departs from — quoted.}
{Why it may matter to the reader, in one line.} Keep your version if you have a better reason; it will not fail the design.
{If visual reference exists: "Reference: {product} does {X} — worth a look."}

**What to keep — do NOT change these:**
{For each kept element:}
- {Specific element that works and why}

**Visual direction reminder:**
{If visual_references populated, restate the product anchors and what to borrow from each — Claude Design may lose context across iterations.}

**All other constraints from the original brief still apply.** Re-read sections {relevant section numbers} if needed.
```

### 3. Self-Review the Correction Message

Before finalizing, verify:

- [ ] Every truth failure cites its test id (T0, T1…, or a legacy MUST PRESERVE item) or truth-class policy rule; every advisory note cites the rule or reference it departs from
- [ ] Every violation describes what the mockup shows (not just "this is wrong")
- [ ] No design opinions injected — every critique traces to a written constraint
- [ ] "What to keep" section is non-empty (even if the mockup is poor, something works)
- [ ] Visual references restated (if applicable) — Claude Design loses context between messages
- [ ] Message is addressed to Claude Design, not to the user
- [ ] Truth failures use imperatives about the **outcome** ("a reader must be able to tell…"), never a mechanism; advisory notes are plainly labelled as suggestions — no advisory note is worded as a requirement, and none sits under "Must be true"
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
Assessment: {PASS-CLEAN | PASS-WITH-NOTES | FAIL | PARTIAL}
Truth failures: {count} · Five-second answer: {pass | fail | no declared answer}
Advisory notes: {count}
Fixed this round: {count}

## Visual References

{visual_references — persisted here so subsequent iterations can load them without the user re-providing}

## Violation History

### Iteration {N}

| ID | Category | Binding | Severity | Description | Status |
|----|----------|---------|----------|-------------|--------|
{table of all violations with their status}

{Include previous iteration tables too — append-only history}

## Kept Elements

{List of elements that work well, accumulated across iterations}
```

### 5. Generate Approval Message (if assessment == PASS)

If `{assessment} == PASS` (0 truth failures AND T0 not failed AND `{coverage_partial} == false`), branch on `{has_unresolved_issues}`.

**5 (clean) — PASS-CLEAN (`{has_unresolved_issues} == false`):**

```markdown
**Design approved — iteration {iteration_number}.**

Every truth test holds and the five-second answer lands. No advisory notes outstanding. Every state a truth test needed was inspected.

**Approved elements:**
{List all kept_elements}

**Ready for implementation.** The design can now be handed to the dev workflow.
```

Update the state file with `status: approved`.

**5 (with notes) — PASS-WITH-NOTES (`{has_unresolved_issues} == true`):** every truth test holds, and ≥1 advisory note is outstanding (a fingerprint row, a treatment divergence, a craft or legibility row, a content slip, a frame not drawn). Emit this instead of the clean approval above:

```markdown
**Design approved — iteration {iteration_number}.** Every truth test holds; {N} advisory note(s) below.

The design answers *"{page_answer}"* and keeps every guarantee the brief asked for. The notes below are advice from the project's design policy and references — worth weighing, not conditions of approval. Claude Design or the implementer may take them, trade them, or decline them with a reason.

**Advisory notes:**
{For each advisory note, strong weight first:}
**{ID}. {Short title}** ({category}, {lane}{, `[tradeable]`})
{What the policy/reference says — quote the section.} {What the render shows.} {The one-line suggestion.}

**Approved elements — keep these:**
{List all kept_elements}

**Next:** hand to design-implement; it carries the notes as advice. Paste the notes to Claude Design first only if you want any of them reflected in the mock.
```

Update the state file with `status: approved-with-notes` and persist the note list so a re-run recognizes which notes were carried forward.

### 5a. Generate PARTIAL-STATUS Message (if assessment == PARTIAL)

If `{assessment} == PARTIAL` (0 truth failures BUT a truth test could not be judged):

```markdown
**Iteration {iteration_number}: PARTIAL — on track but cannot approve yet.**

No truth failures on what could be seen. Waiting on:
{For each item in missing_screens:}
- {state/screen} — needed to judge {test id}: "{test statement}"
{if T0 not judgeable:}- the page's first screen — needed for the five-second answer test

**Status of what WAS verified:**
{For each truth_results line that passed: "✓ {test id} holds ({evidence})"}
{For each fixed_violations item from §6: "✓ {ID} resolved on {screen} ({lane})"}
{For each previous keeper that re-verified in §6a: "✓ {keeper} held"}

{if has_unresolved_issues or treatment_unverified:}**Advisory notes so far (not blocking):**
{list the advisory notes; if treatment_unverified: "- treatment not read from source this round — paste the artifact URL if you want ring/radius/colour checked exactly"}

**Next step:** drop screenshots of the state(s) listed above here. I will not emit an approval until every truth test has been seen — approval on a truth test nobody could see is the silent-failure mode this workflow exists to prevent (step-02 §1a).
```

Update the state file with `status: partial-pending-coverage` and persist `{missing_screens}` (with their test ids) + `{treatment_evidence_mode}` so the next iteration recognizes the gap is closed when the missing states arrive.

### 5b. Brand Identity Feedback (on PASS-CLEAN approval only)

Run this ONLY on a PASS-CLEAN approval (`{has_unresolved_issues} == false`). A PASS-WITH-NOTES design may be excellent, but it is not nominated as a reference page until its notes are either taken or declined with a reason — recommending an undecided surface as the bar is how drift enters the policy. Where a note was declined because the design found a better answer than the policy's style rule, surface that in the brand-identity drift check below — it is a candidate improvement to the policy, not a defect.

When a design is approved AND `{brand_identity_path}` exists, evaluate whether the brand identity should be updated:

**Check for new reference page candidates:**
If the approved design is notably well-executed, suggest adding it to the brand identity's section 6 (Reference Pages):
> "Consider adding {feature_name} at {route} to the brand identity's reference pages — its {specific quality} sets a new bar."

**Check for new anti-patterns discovered:**
If any note persisted for 3+ iterations before being taken, it's a pattern Claude Design is strongly biased toward. Suggest adding it to the brand identity's section 9 (AI Fingerprint Sensitivity) — as advice, not as a new failure:
> "Claude Design repeatedly produced {pattern} despite the advisory note. Consider adding this to the brand identity's AI sensitivity table."

**Check for brand identity drift:**
If the approved design intentionally deviated from any brand identity value (e.g., used a different badge pattern that looked better), flag it:
> "The approved design uses {new pattern} instead of the brand identity's stated {old pattern}. If this is intentional, update the brand identity to reflect the new direction."

Output these suggestions in a `**Brand Identity Updates**` section after the approval message. Do NOT modify the brand identity file directly — surface the suggestions for the user to review.

### 6. Present to User

Display to the user:

1. **Summary line:** "Iteration {N}: {PASS-CLEAN | PASS-WITH-NOTES | FAIL | PARTIAL} — {Y} truth failure(s), five-second answer {pass | fail | no declared answer}, {W} advisory note(s), {Z} fixed from last round{, waiting on N state(s) if PARTIAL}". Never report a bare "PASS" when notes are outstanding — say "PASS-WITH-NOTES — N notes" so the count is in the headline. Never call a note a failure.
2. **The full correction / approval / approved-with-notes / partial-status message** inside a clearly marked block — ready to copy
3. **Brief drift report** (if `{policy_overrides_brief}` = true). For each item in `{brief_drift}`, print:
   > **Brief drift detected — policy wording wins.** The brief at `{brief_path}` softens or drops a rule from `{brand_identity_path}`. This run evaluated against the policy's wording, at the rule's own class ({truth | advisory}).
   > - Rule: `{rule}`
   > - Policy says: `{policy_text}`
   > - Brief says: `{brief_text}` *(drift type: {drift_type})*
   >
   > Fix the brief (edit the bullet to match the policy verbatim) OR if the policy itself should change, run `modify-design-policy`. Do not leave the brief drifted — every downstream review and tuning run will re-detect this.
4. **Brand identity update suggestions** (if any — PASS-CLEAN only)
5. **Next step instruction:**
   - If FAIL: "Paste the message above into Claude Design. Drop the next screenshot here when ready."
   - If PASS-CLEAN: "Design approved. Run the design-implement workflow to bring the approved design into the codebase. For a single, isolated component change, quick-dev may be sufficient."
   - If PASS-WITH-NOTES: "Approved, with {N} advisory note(s). Run design-implement — the notes travel as advice. Paste the notes to Claude Design first only if you want any of them in the mock."
   - If PARTIAL: "Drop screenshots of the missing states listed above and re-invoke design-tuning. The status message is for your records; do not send it to Claude Design as a correction."

---

## SUCCESS METRICS

- Correction message is paste-ready (no user editing needed)
- Every truth failure traces to a truth test or T0; every advisory note traces to a rule or reference and is labelled advisory
- "What to keep" section prevents Claude Design from starting over
- State file persisted with full violation history
- Visual references persisted for subsequent iterations
- User has clear next step

## FAILURE MODES

- Generating a correction that requires the user to edit it before pasting
- Forgetting to restate visual references (Claude Design loses context between messages)
- Writing a truth failure as "consider doing X" — a truth outcome is required, say so. The reverse is equally a failure: writing an advisory note as a demand, or putting it under "Must be true"
- **Failing or withholding approval on advice** — a card grid, a pill treatment, a token, an undrawn suggested frame or an unread treatment is a note, never a FAIL or a PARTIAL
- Not persisting state — losing iteration tracking between invocations
- Approving a design that still has a truth failure or a failed five-second answer
- **Approving on `{coverage_partial} == true`.** PASS requires 0 truth failures AND every truth test judged; emit PARTIAL-STATUS when a truth test is waiting on an unseen state and refuse to send Claude Design a correction (the gap is on the user's side, not the design's). See §5a.
- **Sending the PARTIAL-STATUS message to Claude Design as a correction.** That message is a status-for-the-user; Claude Design would treat it as a directive to redesign the screens it has already shown. The next step is the user dropping the missing screens, not Claude Design producing new ones.

---

## NEXT STEP

Read fully and follow `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-04-emit-critique.md` — **Gate 3 (design-closure)**. It classifies every finding this run produced into exactly one lane, emits the durable `design-critique-{target_slug}-{date}.md`, routes accepted brief-gap findings into Gate 2, and runs the one bounded correction pass. Do not end the workflow at this step: without step-04 the classification survives only as this conversation, which is the gap Gate 3 exists to close.
