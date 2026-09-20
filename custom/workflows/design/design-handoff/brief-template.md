<!--
  Canonical design-brief template — rendered by steps/step-03-generate-brief.md §2.
  Extracted from the inline step on 2026-06-10 to shrink the step to its procedural
  shell (the digestibility fix from orchestration-tuning-2026-06-10-design-lane).
  Behaviour is unchanged: this is the same template text, verbatim.

  OUTCOME-FIRST SHAPE (2026-09-19, STD-BRIEF-BINDING-001 — shared/brief-binding-contract.md).
  Governing principle, owner's words verbatim: "the biggest takeaway is claude design should do the
  heavy lifting everything else is mostly advisory". The brief binds the designer ONLY through its
  Part 2 "What must be true" tests (T0 five-second answer + T1..Tn truth tests). Everything else is
  labelled advisory. The pre-2026-09-19 template is recoverable verbatim from git:
    git -C ~/bmad-method-v6 show 85d5a189:custom/workflows/design/design-handoff/brief-template.md
  Evidence: docs/design-brief-notes-evidence-2026-09-19.md in the fork.

  How to render:
  - Substitute every {variable}; honour the conditional {if …} / {for …} blocks.
  - Section order is intentional: the five parts (moment → what must be true → what must dominate
    → data and its defects → open questions), THEN the advisory appendix. Existing section numbers
    (§1, §2, §2a–§2d, §3, §4–§4h, §5–§5b, §6, §7, §8) are KEPT because consumers cite them; the
    parts group them.
  - Block A/B provenance fields are decided in step-03 §1/§1a/§1b and
    shared/brief-revision-policy.md §2.
  - Quoted policy/brand-identity text is VERBATIM — no carve-outs, softenings, or
    parentheticals the policy lacks (SOURCE-OF-TRUTH PRECEDENCE, workflow.md).
  The brief's own YAML frontmatter begins at the first --- below.
  (The template is wrapped in a ````markdown fence — it is a literal to render,
  exactly as it was inside step-03 before extraction.)
-->

````markdown
---
type: design-brief
feature: {feature_name}
scope: {feature_scope}
date: {date}
author: {user_name} via design-handoff workflow
status: ready-for-design

# Block A — Revision Provenance (see shared/brief-revision-policy.md §2)
target_slug: {target_slug}               # kebab-case slug; doubles as the active-uniqueness key. Refine-screen runs use the "refine-{feature-slug}" form.
brief_status: active
revision_mode: workflow_generated
change_class: {change_class}             # original | material_revision (decided in §1a)
supersedes: {supersedes_filename}        # empty when change_class is original
superseded_by:                           # always empty on a freshly generated brief
source_workflow: design-handoff
source_run_date: {source_run_date}
policy_version_required: {policy_version}     # version of docs/design-policy.md this brief was authored against. Downstream (design-synthesize, design-implement) MUST halt or warn if the current policy version exceeds this value, since rules ratified after this brief may invalidate its assumptions. Populate from the frontmatter of the policy file resolved in step-01 (default to `0` if no policy exists — `existing` design_system variant).
last_modified_by: workflow
last_modified_date: {date}

# Surface admission — WHY this surface is entitled to exist (rendered only when {is_new_surface}).
# A brief for a route that already ships carries `surface_admission: pre-existing` and nothing more:
# this field governs ADMISSION, and re-litigating the standing estate is what makes such a policy a
# form nobody reads. Where the project keeps a scope register, `record:` points at the row that holds
# the argument and names its READER — the answers must be evaluated by someone other than their
# author, and no field here can verify that. `not-a-route` never reaches this template: step-01 §5d
# halts on it.
surface_admission:                       # `pre-existing`, or the five answers below
  outcome: {admission_outcome}           # what outcome does this surface change? (a surface that changes none is a liability)
  instead_of: {admission_instead_of}     # why a route rather than a section, a drawer, or a link on an existing surface
  standing: {admission_standing}         # who the operator is, and when they are standing in a position to open it
  already_answered: {admission_already}  # which existing surface answers this today, and why it is not enough
  retire_when: {admission_retire_when}   # the OBSERVABLE that triggers review or retirement — without it the policy governs only growth
  record: {admission_record}             # pointer to the register row carrying the argument, and who read it

# Block B — Content (see shared/brief-revision-policy.md §2)
brief_shape: outcome-first               # outcome-first | (absent ⇒ legacy). Consumers apply shared/brief-binding-contract.md either way.
page_answer: "{page_answer}"             # the one line a reader must be able to state within five seconds of the page loading (T0)
dominant: "{dominant}"                   # the ONE thing that must dominate the page; everything else is available-on-demand
truth_tests: {truth_test_ids}            # ids of the Part 2 binding tests, e.g. [T0, T1, T2, T3]. Never empty — T0 is always present. These are the ONLY things that can fail a design.
mode: {handoff_mode}                     # fresh-design | policy-delta | elevation | refine-screen — the REAL {handoff_mode}, never fresh-design as a stand-in
surface_class: {surface_class}           # page | chrome (absent ⇒ page). chrome = app-shell (nav/top-bar/sidebar/shell): page_mode is n/a and the composition/band lines below are OMITTED ENTIRELY — see brief-revision-policy.md Block B surface_class row
page_mode: {page_mode}                   # operational | analytical | detail — or n/a iff surface_class: chrome
route: {route}                           # primary route this brief targets (chrome: the shell's scope anchor, normally "/")
surface_part: {surface_part}             # sub-surface within route — a tab/section/panel inside the page (kebab, e.g. raw-records); "" when this brief IS the route's whole primary surface. With route (normalised) + mode it forms the surface identity that keys the active-uniqueness invariant (brief-revision-policy.md §2.6). §13 lookup drawers are NOT surfaces — never give them a surface_part.
{# When surface_class == chrome: OMIT the composition_provenance, composition, and band_provenance lines entirely (absent by design — policy invariant 1a). #}
composition_provenance: {composition_provenance}   # policy-default | recommended-alt (decided in §5a; recommended-alt names a job-fit composition in §4a and was veto-surfaced)
composition: {composition}               # ADVISORY — a suggested starting composition, never a pass/fail contract (brief-binding-contract.md §4). Machine-readable key the design-implement bundle→brief conformance gate (step-01 §SHARED.1b) reports a departure from AS A NOTE. Default = the page_mode default (operational→worklist | analytical→chart-led | detail→record-view). When composition_provenance is recommended-alt, set the named job-fit composition from §4a as a kebab key (e.g. scanner-terminal, single-item-stream, source-co-present). A NON-default composition (e.g. a clerk scan station) is the signal that the gate must verify the bundle expresses the JOB LOOP (scan→feedback→tally→close), not a centered hero card.
band_provenance: {band_provenance}       # inherited | recommended-new | recommended-drop | none
disclosure_model: {disclosure_model}     # three-layer | n/a — <why this surface carries no audit contract>. Decided in step-01 §3h (disclosure pass). `three-layer` REQUIRES a rendered §4h assigning every element family to a layer — see shared/disclosure-layer-contract.md D7. The trigger is an AUDIT/PROVENANCE CONTRACT (the design owes evidence, source, freshness, derivation, conflicts, override authorship or audit history for a value the operator commits to), NOT the mere presence of metadata: a timestamp column is not an audit contract. Absent on a surface whose §2 names those obligations is gate class (i) in step-03.
{# analytics_archetype is REQUIRED iff band_provenance ∈ {inherited, recommended-new}; omit the line entirely otherwise. #}
{if has_analytics_band}
analytics_archetype: {analytics_archetype}   # trend | distribution | composition | ranking | coverage | flow | waterfall | single-metric | correlation
{endif}
{# shell_role is the page-shell & role contract. REQUIRED whenever the app has more than one role/shell (e.g. clerk vs owner); OMIT the whole block for a single-role app where every surface shares one shell. The chrome fields are ADVISORY for the DESIGN; the data-protecting half of forbidden_chrome (e.g. "a clerk never sees owner money or approvals") MUST ALSO be written as a Part 2 truth test — that test is what binds. design-implement's IMPLEMENTATION-side check (an ancestor layout injecting forbidden chrome at runtime, step-02 §1a / step-03 §2d) is build fidelity and is unchanged. #}
{if has_shell_role}
shell_role:
  required_shell: {required_shell}       # the layout / route-group the surface MUST render under (e.g. clerk | owner | authenticated). Verbatim where the design draws it.
  required_chrome: {required_chrome}     # the chrome this surface MUST carry (e.g. "clerk header — 'Bison Management / Receiving — receive station' + role chip 'Clerk'"). Reproduce verbatim on the rendered frame.
  forbidden_chrome: {forbidden_chrome}   # chrome that MUST NOT appear on this surface (e.g. owner global nav, financial/approvals views). An ancestor layout injecting any of these OVER this surface is a Tier-1 shell violation — the owner-nav-on-a-clerk-station case.
{endif}
frames: {frames_list}                    # SUGGESTED frames — ADVISORY (brief-binding-contract.md §4). Machine-readable list of the §7 Surface Inventory ids (e.g. [receive-station, active-session-workspace, matched-shipment-lookup]). Which frames to draw is the designer's call; a suggested frame not drawn is a NOTE downstream, never a failure. Keep ids identical to the §7 table. NEVER empty: at minimum the primary frame.
{# In refine-screen mode the following four fields are REQUIRED. In every other mode (fresh-design, policy-delta, elevation) they MUST be omitted entirely. #}
{if handoff_mode == "refine-screen"}
screen_review_ref: {review_artifact_path_relative_to_repo_root}
targeted_changes:
  {for each entry in {targeted_changes_list}}
  - region: {region_name}
    rationale: "{V-ID} — {one-line summary}"
  {end for}
{if collapse_occurred}collapse_note: "{which V-IDs collapsed and why}"{end if}
unchanged_regions:
  {for each entry in {unchanged_regions_list}}
  - region: {region_name}
    note: "{one-line reason this region is protected}"
  {end for}
deferred_violations:
  {for each V-ID in {deferred_violations_list}}
  - {V-ID}: "{reason deferred — out of scope, mechanical-only, IA decision, etc.}"   # advisory V-IDs ONLY — a Binding: truth violation is never deferred
  {end for}
{end if}
---

# Design Brief: {feature_name}

## For Claude Design

> **Repository:** **{github_repo_url}** (branch: `main`). Connect to THIS repository: Claude Design reads THIS brief from the repo **by the path below** (do NOT paste the brief body into a chat) and reads the files it references. Terminal-native alternative: `design-synthesize` reads this brief locally with no Claude Design round-trip.
>
> **This brief:** `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
>
> **Revision provenance** follows `brief-revision-policy.md` in the shared design workflow docs. Consumers (design-artifact-loop, design-synthesize) validate the provenance frontmatter at intake; do not hand-edit this brief into a scope or intent change — re-run `design-handoff` instead.
>
> **Repo read protocol (the bias filter — obey exactly):** this brief deliberately omits the current layout; **the repo does NOT** — it contains the current UI's implementation. {If feature_scope == "redesign": Read ONLY the files named in §8. The current view's markup/component files are listed there as **DO-NOT-READ** — opening one to "understand the feature" anchors you to the exact layout this brief withholds, and the failure mode is invisible (a re-skin renders as confidently as a fresh design). Everything the design needs is in this brief; if something is missing, that is a brief defect — say so rather than reading the view.}{If feature_scope == "new": there is no existing screen for this surface, so repo reading cannot anchor you — read the brief and the files it names, then design fresh.} This is distinct from Claude Design **system setup** (`onboard-design-system`), where the live repo / current screens must NEVER be the seed. *(This rule is kept because it is about bias, not over-constraint — it governs what you read, not what you draw.)*

**Scope:** {feature_scope — "new" = design from scratch, "redesign" = rethink existing}

---

## How this brief binds you — read this first

> **"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"** — the product owner, 2026-09-19.

You do the heavy lifting. This brief binds you in exactly one place: **Part 2, "What must be true"** — a short list of tests your finished design either passes or fails. Nothing else in this document can fail your design. Everything from the **Advisory guidance** heading down (suggested frames, layout, composition, visual direction, tokens, style floors, the style parts of the design policy) is advice: take it, trade it, or ignore it for a better idea, and say what you did in your notes. A rule kept only for consistency with the rest of the product is marked **[tradeable]**.

```
  answer:       {page_answer}              # T0 — a reader states this within 5 seconds of the page loading
  dominant:     {dominant}                 # the ONE thing that leads; everything else is available-on-demand
  binding:      {truth_test_ids}           # the Part 2 tests — the only pass/fail items in this brief
  route:        {route}
  mutations:    {mutation_posture}         # none (read-only) | the jobs the operator must still be able to do (each is a Part 2 test)
  suggested:    frames {frames_list} · composition {composition} · page_mode {page_mode}   # ADVISORY — yours to change
```

Contract: `shared/brief-binding-contract.md` (STD-BRIEF-BINDING-001). Reviewers downstream (`design-review-pr`, the `design-implement` conformance gate) may fail your design only on a Part 2 test; every other departure is reported as a note.

**Five of the Part 2 tests are on every brief and are worth reading first — TC1, TC2, TA1, TA2, TF1.** They govern whether a control exists, how loud anything is, and what the page treats as work: every action control can say what its press tells the system that the system does not already know · no sentence instructs an action the page gives no way to perform · the most emphasised thing is the most consequential thing and no consequential control is dressed as chrome · no fact is said twice at rest · no system fault is rendered as a category of the operator's work. Source: `shared/controls-and-attention.md` (STD-CONTROLS-ATTENTION-001), which holds **no** colour, shape, placement, spacing or wording rule — those are yours, as always. §4f-c carries the evidence they are judged against.

---

## Part 1 · The moment

**Who opens this page, after what, to decide what:** {page_moment — one paragraph. The operator, the event that sends them here, the question in their head when the page loads, and the action they take next. Written as a moment, never as a list of outputs. E.g. "The operator opens this page because they suspect the prep is holding less than they paid for. They need to know how many purchases are missing and which ones to chase."}

**The page's answer (T0):** {page_answer} — if a first-time reader cannot say this within five seconds of the page loading, the design has failed, however complete it is.

## 1. Feature Purpose

**What this feature does:** {feature_purpose — the problem it solves, NOT what the page looks like}

**Route:** `{route path}`

**What the user needs to accomplish:**
{user_goals — domain outcomes, NOT UI actions. "Spot invoices near deadline" not "click the overdue tab."}

**Capabilities the design must support:**
{must_support_capabilities — jobs the operator must be able to accomplish, as outcomes. Each one is carried into Part 2 as a reachability test ("the operator can …"); WHERE and HOW it is reached is yours. If the design cannot express one of these, that is a gap to flag — not to drop silently. Omit this subsection only when the surface genuinely has no capabilities beyond the primary goals above.}

**Deliberately not carried forward (logged drops):**
{Render this subsection ONLY when `{dropped_capabilities}` is non-empty (a redesign that consciously sheds or relocates a capability the current surface had). One bullet per entry: the capability (outcome phrasing) · why (`relocated` to which sibling surface / `obsolete` / `out-of-scope-by-design`). This makes every drop an explicit, on-the-record decision the designer and the user can see — the design need NOT build these, but they are documented, not silently absent. Omit the subsection entirely when `{dropped_capabilities}` is empty.}

**Typical data volume:** {counts in domain terms}

**List rendering (§5g — advisory):** {if list_rendering_verdict and list_rendering_verdict != "single-render"}**{list_rendering_verdict}** is suggested for the primary list — {list_rendering_rationale}. How you keep a growing list usable is yours; what is binding is the Part 2 test that no row is silently cut off.{else}{if list_rendering_verdict == "single-render"}single-render — {list_rendering_rationale} (a hard ceiling justifies rendering all rows).{else}n/a — not a list surface.{endif}{endif}

## 3. Who Uses This

{user_context — role, job-to-be-done, frequency, emotional state}

**Design implication:** {one sentence connecting user context to design priority}

---

## Part 2 · What must be true — the binding tests

These are the ONLY things in this brief that can fail your design. Each is a test a finished design passes or fails. None of them tells you how to pass it — that is yours. A test written as a mechanism ("annotate every figure inline", "a permanent band at the top") is a brief defect; say so.

| Id | A finished design passes if… | How a reviewer checks it | Why (source) |
|---|---|---|---|
| T0 | A reader who has not seen the page can state **{page_answer}** within five seconds of it loading. | Show the render to a fresh reader for five seconds; ask what the page is telling them. | Owner, 2026-09-19 — the page must answer something. |
| TC1 | {tc1_statement — every action control on THIS surface can name what its press tells the system that the system does not already know. Name this surface's controls from §4f-c, and name the `{background_work}` the design must not turn into a control, e.g. "no control on this page re-runs the marketplace check — that runs on its own and the page says when it last ran".} | List every action control on the render. For each, say what the press tells the system. A control whose answer is "nothing — the system could run this itself" fails. | Owner, 2026-09-20 — `controls-and-attention.md` §1. |
| TC2 | {tc2_statement — no sentence on THIS surface instructs an action the surface gives no way to perform. Name the instructions this surface's data forces it to write, e.g. "where a row says the price is below the floor, the row carries the control that changes it — or the sentence states the fact and stops".} | Read every instruction in the prose. For each, find the control that performs it on the same surface. No control and the sentence still instructs → fail. | Owner, 2026-09-20 — `controls-and-attention.md` §1. |
| TA1 | {ta1_statement — the most emphasised thing on THIS surface is the most consequential thing on it, and no consequential control is dressed as an inconsequential one. Name the surface's single most consequential control (usually an irreversible one from §4f-c).} | Rank what the eye reaches first; rank what costs most if pressed or missed; compare the two orders. Then find the most consequential control and check it does not read as chrome. | Owner, 2026-09-20 — `controls-and-attention.md` §2. |
| TA2 | {ta2_statement — no fact is stated twice on THIS surface at rest. Name the two or three facts this surface will be most tempted to repeat — a group's blocking reason restated per row, a two-authority disagreement said in two voices, a per-figure caveat that belongs to the page.} | Pick the page's three loudest facts. Count where each is said before anything is opened. Twice is a fail; a decomposition carrying a *different* fact is a pass. | Owner, 2026-09-20 — `controls-and-attention.md` §2. |
| TF1 | {tf1_statement — no system fault is presented as a category of the operator's work on THIS surface, and no control exists only to compensate for one. Name each `{fault_categories}` entry and its non-operator owner.} | For each category the page counts as work, ask who must act for it to stop recurring. An engineer, a rule or a producing system → it is a fault: named as one, owned elsewhere, counted separately. | Owner, 2026-09-20 — `controls-and-attention.md` §3. |
{for t in {truth_tests}}| {t.id} | {t.statement — an outcome, e.g. "A reader can never mistake a stale or partial figure for a current one, including when they screenshot a single row."} | {t.check — what a reviewer looks at to decide pass/fail} | {t.source — the §2 / §2b / §2c / §4d / §4e / policy rule / capability it protects} |
{endfor}

**Where these come from (so nothing binding is invented and nothing true is dropped):** the data's own defects (§2: missing ≠ zero, observed vs declared vs assumed, two authorities kept apart), the finance truth constraints (§2b `must_not_infer`), the runtime honesty budget (§2c — the page never claims more liveness than its transport delivers), analytic and decision honesty (§4d/§4e — no fabricated interval or distribution, derived never shown as stored), the audit contract (§4h obligations restated as outcomes — "every figure's source is inspectable"), the capabilities in §1 (reachability), a data-protecting role boundary (from `shell_role`), and the truth-and-data rules of the project design policy (money basis, no invented figures). **TC1 · TC2 · TA1 · TA2 · TF1 are present on every brief** and come from `shared/controls-and-attention.md` (STD-CONTROLS-ATTENTION-001) — they govern whether a control exists, how loud anything is, and what the page treats as work. Style, layout and composition rules from the policy are NOT here — they are in the Advisory guidance, and `controls-and-attention.md` deliberately holds no colour, shape, placement, spacing or wording rule.

---

## Part 3 · What must dominate

**The one thing that leads:** {dominant}

**Available on demand — demoting these is legal, and expected:** {on_demand — everything else the page carries, named plainly. E.g. "the 598 matched rows, the full mirror, every document date, VAT basis, lot ids, raw exchanges — all reachable, none competing." Hierarchy is made by demoting things; this list is your permission to demote them.}

---

## Part 4 · The data, and its defects

Facts about the world, not instructions about pixels. What each feed contains, what it cannot tell you, which figures are derived, and where the gaps are.

## 2. Domain Data

Fields are in domain language. Grouping, derivation, and presentation are design decisions — not prescribed here.

### {EntityName}
{one-line purpose}

| Field | Type | Nullable | Notes |
|---|---|---|---|
| ... | ... | ... | {only genuine notes: units, value domains, FK targets} |

{Repeat per entity. Minimal set — only entities this feature touches.}

**Volumes:** {real-world counts in domain terms}

**Relationships:** {plain-English facts about how entities relate — NOT grouping structures}

**Derivation inputs:** {raw fields the designer can derive from — NOT pre-computed outputs}
- {e.g., "deadline date per country — the design can derive urgency however it sees fit"}
- {e.g., "row-level status enum — the design can derive progress rollups however it sees fit"}
- {e.g., "row-level net + vat amounts in a currency — the design can derive totals however it sees fit"}

**Nullable fields needing empty-state treatment:** {list}

### API Surface

{api_surface — endpoints, methods, brief response descriptions. Implementation reference only.}

---

## 2a. Linked records & lookups

{Render this section ONLY when `{linked_records_inventory}` is non-empty. Omit entirely — no heading, no placeholder — for a true leaf surface that references no record owned by another surface.}

**What binds here (carried into Part 2):** every value below IS a record owned by another surface. A reader must be able to reach that record's own fields from here without losing their place, and any related field shown on this surface is **read through the relation, never re-keyed** — so it can never disagree with the record it came from. That is a data-truth test.

**What is advice (§13 of the project design policy, style half — [tradeable]):** the product's usual way of meeting that test is expand-in-context — acting on the reference opens the foreign record in a right-side drawer *over* this surface, with its own fields and links, and "Open full {sibling} page →" as a quiet secondary action; the affordance is a quiet link, never a button, pill or chip. Use it, or propose something better and say why.

| Foreign reference | Owns it (surface · route) | Suggested way to reach it (advisory) | Inline lookups (read-only, read through the relation) |
|---|---|---|---|
| {identifier as shown} | {sibling surface · `/route`} | {acting on it → the {foreign record} expands in the §7 drawer over this surface, its own fields shown; "Open full {sibling} →" secondary inside it} | {related fields pulled through the relation, or "—"} |

{One row per entry in `{linked_records_inventory}`.}

**Richness (advisory):** where you give a foreign record its own drawer, show the fields the relation actually needs (a `warehouse` opened from an order shows code/type/status/location AND what is routed through it for this order), not identity alone. The "Inline lookups" column is that field set; `—` means the record genuinely carries nothing past identity. Each suggested lookup drawer appears in §7 as a suggested frame — drawing it is your call.

---

{if {is_finance_surface}}
## 2b. Finance semantics & accounting truth

*This surface is finance-shaped ({finance_report_type}). The semantics below MUST survive the
blank-canvas redesign — they describe meaning the design must preserve, never how to lay it out.*

**Column semantics (what each value means):**
{for s in {finance_column_semantics}}
- `{s.column}` — {s.group} · {s.meaning}
{endfor}
Quantities and monetary values are distinct concepts — never present them blended in one field.

**Exception states the design must be able to represent** (somewhere in the journey — these are
outcomes, not a prescribed panel):
{for e in {finance_exception_expectations}}
- {e}
{endfor}

**Accounting-truth constraints (must NOT be inferred):**
{for m in {finance_must_not_infer}}
- {m}
{endfor}

**Open questions — unresolved definitions (do NOT guess these; surface them in the user's journey
or as workflow questions):**
{for u in {finance_unresolved_assumptions}}
- {u}
{endfor}

**Terminology — use consistently:** {finance_terminology}


---
{endif}

{if {ledger_view}}
## 2d. Ledger archetype — which view this is

**This surface is: `{ledger_view}`** — one of `not-a-ledger` · `register` · `running-balance`.

*The archetype test that produced it: are the rows **movements over time on an account**, and is a column
**meant to be summed**? A table that merely sorts by a date is a worklist, and a route's NAME is not evidence.*

{if {ledger_archetype_policy_source}}
Archetype rules are defined in **`{ledger_archetype_policy_source}`** and apply to this surface in full.
Read that section — it is the source of truth; the notes below are the shape, not a substitute.

{if ledger_view == "running-balance"}
- **Sort: OLDEST-FIRST (date-ascending).** A cumulative column only builds correctly reading DOWN the page.
  This is the one sanctioned exception to a most-recent-first default — state it on the artifact.
- **The running balance is per-account, per-currency, chronological — or it is not shown.** Where the active
  sort or a mixed account/currency would make it wrong, show the honest not-applicable token, never a
  confidently-wrong number.
{endif}
{if ledger_view == "register"}
- **Sort: MOST-RECENT-FIRST**, and **no running balance is shown, by design.** Say so on the artifact —
  a suppressed balance that is merely absent reads as an oversight. Do not add a cumulative column without
  re-testing it against the per-account / per-currency rule.
{endif}

- **Money and balance columns:** right-aligned, monospace, `tabular-nums`, fixed decimals — the decimal
  points must form ONE vertical rule. That alignment is what makes it read as a ledger and not a grid.
- **A true zero and a not-applicable are DIFFERENT FACTS** and must render differently. A blank that could
  mean either is dishonest.
- **Corrections are appended, never applied in place.** A wrong line is corrected by a NEW entry that points
  back at what it corrects; the design must have somewhere for that linkage to be seen. A correction that
  does not point back is an orphaned figure.
- **Direction is never carried by colour alone** — two columns, or Dr/Cr, or parentheses. Colour-only fails
  the status system and WCAG 1.4.1.
{else}
**No ledger archetype is defined in this project's design-policy chain.** The classification above is
recorded because it is true regardless of policy; **no archetype rules are asserted here**, and none have
been imported from another project. See Open Questions.
{endif}
{endif}

{if {is_live_process_surface}}
## 2c. Runtime behavior contract

*This surface's primary job is watching/controlling a **long-running in-flight process**. The temporal
semantics below MUST survive the blank-canvas redesign — they describe what changes over time and what
the operator can do about it, never how to lay it out. The binding half is carried into Part 2 (the page
never claims more liveness than its transport delivers; "done with exceptions" is never presentable as
"done clean"). Each lifecycle state is offered in §7 as a SUGGESTED state-variant frame — drawing the
states that change what the operator sees is strongly advised; which ones you draw is your call.*

**Run lifecycle (from the implementation's own state machine):**

| State | What is true in it | Operator's question | Legal control verbs |
|---|---|---|---|
| {state} | {what the process is doing / has done} | {e.g. "is it still working?", "what failed?"} | {pause / resume / cancel / retry / none} |

{One row per lifecycle state in `{runtime_behavior_contract}`. Transitions and triggers as a short plain-English list below the table.}

**Per-item states (including every failure/partial lane):** {per-item states — throttled, held, load-error, retrying, skipped, missing-at-source, … Partial failure is the normal case, not an edge case; the design must make "done with exceptions" distinguishable from "done clean" at a glance.}

**Update transport & staleness (honesty constraint):** {how the surface learns of change — pushed message / storage listener / poll — and its cadence. The design may only promise the liveness this transport delivers: if the display can be N seconds stale, the design must not present itself as real-time. State the staleness budget explicitly.}

**Control verbs (outcomes, with real semantics):** {each verb the operator has over a run in flight, with what it actually does — e.g. "stop the run without losing completed work (cancel drains in-flight items)", "resume a paused run from where it stopped". Never buttons — jobs.}

**Progress signals available (derive from these — presentation is the design's):** {the raw signals — counts by state, per-item/per-marketplace telemetry, timing data, run-report/history data. No progress-bar, spinner, or log-panel prescription here.}

**Unresolved runtime semantics:** {the unresolved entries from `{runtime_behavior_contract}` — e.g. what cancel does to in-flight items, whether a run is resumable. Do not resolve them by guessing the data; they are also listed in Part 5, where sketching two options is invited. Omit the block when none.}

---
{endif}

## Part 5 · Open questions — unfenced

These are undecided. **Do not skip them, and do not hold back from drawing them.** Where the honest answer is a sketch rather than a sentence, sketch it: pick **two** of the questions below and show two options for each, side by side, with a line on what each option costs. A reviewer resolves a question fastest by seeing it answered two ways.

{for q in {open_questions}}- **{q.question}** — {q.why_open: what is unknown, and what would settle it}
{endfor}
{Collect every open question the passes produced — finance unresolved assumptions (§2b), runtime semantics (§2c), interaction semantics (§4f), operator/policy collisions (§4f), ledger archetype gaps (§2d), viewport ambition pending (§4g), and any design policy rule whose binding/advisory classification was ambiguous (brief-binding-contract.md §2). Never fence one off with "do not draw anything for this".}

## 6. Design Ask

{Use ONE of the following based on `{handoff_mode}`.}

**--- VARIANT REFINE: `{handoff_mode}` = "refine-screen" ---**

> This is a refinement, not a redesign. The information architecture and task model are stable. The fixes below come from the screen review, each marked with its binding: a **truth** fix restores a Part 2 test and must be met; an **advisory** fix is the review's recommendation and your call — say where you took a different route. Produce variants for the listed edge states. Do not propose new IA, new components, or alternate layouts unless required to land one of the three fixes. The page should remain recognizable.

**Source diagnostic:** `{review_artifact_path}` — generated by `design-review --artifact` on `{date}`. This is the ground truth; do not invent additional issues.

### Fixes (truth first, then advisory; in priority order)

{For each item in `{refine_focus}`:}

**{N}. {short-name}** *(binding: {truth — Part 2 {test id} | advisory — your call}; severity: {hard failure|major|minor})*

- Location: `{file:line}`
- Question this fix unblocks: {question_blocked from artifact}
- Direction: {before_class} → {after_class}
- {why this is the top fix — one sentence from artifact}

### Suggested edge-state variants

{For each item in `{required_variants}` (the screen-review names these; drawing them is strongly advised, and each is advisory unless it is also a Part 2 test):}

- **{state}** — design implication: {why this needs explicit treatment}

### Peer patterns to port

{For each item in `{peer_steals}`:}

- From `{peer_path}`: {pattern} — port by {action}.

### Do NOT break

The audit found these aspects already work. The refinement must preserve them:

{Bullet list from `{already_fine}`}

### Scope guardrails (refine-screen)

- Do NOT redesign the IA, the task model, or the navigation. Those are out of scope for this round.
- Do NOT propose new components unless one of the three fixes genuinely requires it.
- Do NOT add a "get radical" alternative — see step-01 of `design-review` for that conversation; refine-screen is bounded by design.
- DO produce the edge-state variants where they help — the review asked for them, and a variant that changes what the operator sees is the cheapest way to show a fix works.
- These guardrails bound the SCOPE of this refinement round; they are not pass/fail criteria for the design. Only Part 2 is.

**--- VARIANT FRESH: `{handoff_mode}` = "fresh-design", "policy-delta" or "elevation" (or unset) ---**

{Write the ask using the mode-specific pattern below, then append 3-5 feature-specific questions.}

**Structure:**

> {Mode-specific framing sentence (see below).}
> {Scope directive (see below).}
>
> Questions your design should answer:
> {3-5 feature-specific questions derived from user goals + data shape}

**Mode-specific framing:**

If `{page_mode}` = **operational:**
> Design this page for a user whose main job is to process work accurately and efficiently.

If `{page_mode}` = **analytical:**
> Design this page for a user whose main job is to understand what changed, why it changed, and where to investigate further.

If `{page_mode}` = **detail:**
> Design this page for a user whose main job is to read and act on one record — understand its current state, edit its fields, and take the next action on it — having arrived here from a worklist.

**Scope directives (append after the framing sentence):**

- **new + branded:** "Answer the moment in Part 1 and pass the tests in Part 2. The product's visual identity (section 4 points to it) is the natural starting point; everything else is yours."
- **redesign + branded:** "The current implementation was developer-built without a design process. Start fresh from the moment, the tests and the data. The product's visual identity and reference pages (section 4) are the natural starting point, not a cage."
- **new + existing:** "Answer the moment and pass the Part 2 tests. The visual direction in section 4 and the style floor in section 5 are advice. Everything else is yours."
- **redesign + existing:** "Start fresh from the moment, the tests and the data. The visual direction and style floor below are advice."
- **new + external:** "Apply **{design_system_name}** as your starting system."
- **redesign + external:** "Apply **{design_system_name}** as your starting system. Ignore existing CSS tokens in the repo."

---

**Hard rule: questions must be derived from the data model and user goals only — never from current UI sections, labels, or grouping structure.** If a question names the current grouping logic, the current tabs, the current panels, the current summary blocks, or the current page breakdown, it is leaking. If it names the job to be done, it is safe.

**Page-mode rule for questions:**
- Operational questions should be about processing, review, exception handling, and workflow progress.
- Analytical questions should be about trend detection, comparison, anomaly diagnosis, and drill-to-evidence.
- Detail questions should be about single-record legibility, field grouping, inline edit/action affordances, and how state and next-action are surfaced on one record.
- Questions must not mention current tabs, panels, cards, sections, or grouping structures from the existing implementation.

**Good questions for operational pages:**
- "How does the user quickly find items needing action among a dense set of records?"
- "How does the interface make workflow state and exceptions immediately understandable?"
- "How does the design support both precise row-level review and efficient bulk throughput?"
- "How does filtering help the user narrow the work queue without clutter or loss of context?"
- "How does the page remain calm and trustworthy while supporting operational urgency?"

**Good questions for analytical pages:**
- "How does the page help the user spot trends, changes, or anomalies quickly?"
- "How does the interface support comparison across time periods, segments, categories, or entities?"
- "How does the user move from summary insight to underlying evidence without losing context?"
- "How does filtering define the scope of the analysis without turning the page into a control panel?"
- "How does the page maintain visual consistency with the rest of the product while still feeling analytical?"

**Bad questions** name the current UI's structure (disguised layout instructions — do NOT use):
- "How should the per-country view work?" ← names the current grouping
- "How should the quarter tabs behave?" ← names the current tab structure
- "Where should the sidebar grouping be arranged?" ← names the current panel layout
- "How should the bulk action toolbar work?" ← presupposes a toolbar

**Questions and Part 5 are one list to the designer.** The 3–5 questions above and the Part 5 open questions are both invitations: the designer may answer any of them in sketch form, and two options for two of them is the invited default.

---

## Advisory guidance — the designer's call

**Everything from here to §7 is ADVISORY** (`shared/brief-binding-contract.md`). It is here because it is useful: the product's visual system, suggested frames, the page-mode default composition, and the style floors the product usually holds to. None of it can fail your design. Where you depart from it, say so in your notes and say why — a departure is reported downstream as a note, never as a failure. Rules marked **[tradeable]** exist for consistency across the product rather than for correctness: trade them against a better idea when you have one.

**Token, pill and colour detail is not restated in this brief.** It lives in the project's design system — `{design_system_pointer}` — and you read it there.

## 4. Visual Direction

{Use ONE of the following variants based on `{design_system}`:}

**--- VARIANT A: `{design_system}` = "branded" (brand identity document exists) ---**

> This project has an established visual identity, and it is the natural starting point — advisory, not a cage. **The system itself — type scale, colour and status tokens, badge/pill pattern, component patterns, spacing and radius — lives in `{design_system_pointer}` and is not restated here.** Read it there. Where you depart from it, say so in your notes; a departure is a note downstream, never a failure. Truth rules the policy carries (money basis, no invented figures, and the like) are not here — they are Part 2 tests.

### Visual Personality

{Copy section 1 from brand identity verbatim — personality statement, register, density, "what it's NOT". This is direction, not tokens; it helps the designer more than a token list does.}

### Where the system lives (read these, they are not copied here)

- **Typography, colour and status tokens, component patterns, spacing:** `{design_system_pointer}` — sections {brand_identity_system_sections, e.g. "§2 Typography · §3 Colour & status · §4 Components · §5 Spacing"}.
- **Status mapping for THIS feature [tradeable]:** the product usually expresses every state through its small fixed status set (e.g. danger / warning / success / neutral) rather than a unique colour per state. The feature's states are: {feature_states — plain list, e.g. "failed read · missing from the prep · matched · waiting"}. Map them through the system, or — as the owner's review of the TheFBAPrep page found — say most of them in a sentence instead of a pill. Either is legitimate; what is binding is only a Part 2 test such as "a failed read is never mistakable for a successful one".

### Reference Pages

{Copy section 6 from brand identity — internal gold-standard pages with routes and why}

### External Influences

{Copy section 7 from brand identity — named products and what to borrow/avoid}

**--- VARIANT B: `{design_system}` = "external" ---**

> This page uses the **{design_system_name}** design system as its starting system ({design_system_pointer}). Do NOT use the CSS tokens in the codebase — those are developer placeholders.

**Structural constraints (still apply):**
- App shell: {fixed shell elements}
- Navigation: {where this page lives}

**--- VARIANT C: `{design_system}` = "existing" (no brand identity, no external system) ---**

> No project design policy was found. The existing product's tokens live in `{design_system_pointer}` (the token file) and the patterns observed on other pages are listed below — advisory starting points for **visual continuity with the existing product**. Where the existing system has gaps, restraint usually serves: neutral surfaces, sparing colour, type and density appropriate to the data.
>
> **Note for the project team:** Creating a `docs/design-policy.md` will replace this generic fallback with the project's actual visual language. Without one, the designer must reverse-engineer intent from raw CSS values.

### Tokens

Read them from `{design_system_pointer}` — not restated here.

### Patterns from Other Pages

{existing_patterns — from OTHER pages in the app, NOT the target feature}

### Reference Pages

{reference_pages — internal pages to reference for visual consistency}

---

## 4a. Page Mode — a suggested starting composition (advisory)

*Everything in §4a is a suggested starting point from the job analysis. Layer, order, persistence, and whether the page is table-first, chart-led, a station or a stream are the designer's call. The binding half — what the operator must be able to decide and never be asked blind — is in Part 2.*

{First, if `{composition_provenance}` = "recommended-alt", emit the composition-override block below — it leads §4a and supersedes the "Composition:" line of the page-mode block that follows. If `{composition_provenance}` = "policy-default", OMIT the override block entirely and emit only the page-mode block.}

**--- Composition override (include ONLY if `{composition_provenance}` = "recommended-alt") ---**

> **Primary composition for this surface: {named job-fit composition from `{composition_rationale}`} — NOT the `{page_mode}` default.**
>
> This surface is `{page_mode}` (it {one-line work description}), but its job is {dispensed / comparison-first / single-item / verification-against-a-source — from the §5a answers}, so the policy's default {table-first worklist / chart-led / record-view} composition is the wrong *primary* shape. Design the primary surface as **{named composition}**. {One or two sentences making it concrete for this feature — e.g. for an operational override: "a full-width single-item decision surface the operator streams through, with the worklist demoted to a deliberate triage/backlog view, not the home screen." For a `detail` verify-against-source override: "a source-co-present verification layout — the extracted record and its source document (receipt / email / PDF) rendered together with the source sticky, so the operator's eye moves value ↔ source; the source must NOT collapse once extraction completes."} This is a suggestion from the job analysis (design-handoff §5a, confirmed with the user on {date}); where the page-mode block below states a default "Composition:", THIS suggestion is the better starting point. Both are yours to replace.

**--- Operational cockpit checklist (include ONLY if `{composition}` = "operational-cockpit") ---**

> **Operational cockpit — apply the `operational-cockpit` skill (canonical doctrine).** This surface is a triage queue feeding a single-item decision workspace (project design-policy §6 "Operational cockpit"). The **`operational-cockpit` skill is the single source of truth** for this archetype — design, synthesize, and review against that skill; do NOT restate a partial checklist here. Its floor (M1–M6) is the product's best current thinking for this archetype — **advisory here**, except where a line is also a Part 2 test (M5 "never commit an irreversible write blind" and M6 "never decide without the evidence" usually are):
> - **M1 — classify first.** Decide-one, not a table-first + drawer-as-workspace composition.
> - **M2 — queue + workspace co-present.** Queue rail = triage (compact, subordinate, not the home screen); workspace = the full-width star (image / candidates / evidence side-by-side, not a ~400px drawer); tools rail = secondary.
> - **M3 — per-item momentum.** After a commit, auto-advance to the next actionable item, with an undo/toast safety window — never commit → return to list → re-hunt.
> - **M4 — keyboard-first.** Every per-item commit reachable and committable from the keyboard, with a persistent shortcut affordance.
> - **M5 — consequence-visibility.** Before an irreversible commit, show the resulting record/figure that will be written (rendered, basis-labelled) — not a prose description.
> - **M6 — no working blind.** The workspace surfaces the evidence the decision requires; a commit control without its evidence is a form, not a cockpit.
>
> Heuristics **H1–H5** (confidence-scaled fast path · geometry flexibility · one-viewport · reversibility calibration · inert-control checks) live in the skill — apply from there. The **truthful-labels** and **waiting ≠ actionable** IA rules are carried directly by the `operational-cockpit` skill (labels match the real destination + operator action; a no-op waiting state never sits in an actionable bucket) — they are not in the family overlay or project residue, so the skill is their only home.

{Then include ONE of the following based on `{page_mode}`:}

**--- If `{page_mode}` = "operational" ---**

This is an operational page. The design should optimize for row-level work, exception handling, and workflow progress. Prioritize dense scanning, explicit state visibility, and fast narrowing of large record sets.

**Composition:** Use table-first composition for workflow, review, and exception handling pages. Visual treatment of tables, badges, filters, and density follows the visual system defined in section 4 — this section governs mode, not aesthetic.

**--- If `{page_mode}` = "analytical" ---**

This is an analytical page. The design should help the user understand patterns, compare segments, detect anomalies, and move from summary insight to supporting evidence.

**Design principles:**
- Maintain visual consistency with the rest of the product — the visual system is defined in section 4.
- Charts and summary metrics exist to support understanding, not to decorate. Avoid promotional or BI-template-driven treatments.
- Filters should remain compact and persistent so the user can understand the scope of the analysis at all times.
- Charts may lead the page when they genuinely help the user see patterns faster, but there must always be a clear path to underlying records or evidence.
- Tables are supporting evidence on analytical pages unless row-level processing is the dominant task.

**Composition:** Use chart-led composition for analytical pages. Even on analytical pages, avoid KPI-card walls, decorative dashboards, and disconnected widgets.

**Evidence rule:** Analytics pages may be chart-led, but they must still preserve a clear path to underlying records or evidence. Every chart, metric, or summary should let the user drill into the rows behind it. An analytical page that cannot show its working is a dashboard.

**--- If `{page_mode}` = "detail" ---**

This is a detail page — a drawer or full-page view of **one record**. The design should optimize for reading and editing a single record's fields, not for processing a queue or analyzing a dataset. The user arrived here by drilling from a worklist; this view is the extension of that list, never a re-skin of it.

**Design principles:**
- Group fields by the user's mental model of the record, not by database table order. Make the record's identity and current state legible at the top.
- Inline edit and per-record actions are first-class — surface them where the field lives, not in a distant toolbar.
- Density is moderate (between a dense worklist row and a relaxed analytical page) — the user is reading one record carefully, not scanning hundreds.
- Usually no analytics band: most single records have no aggregate dimension, and child collections (line items, history) are supporting tables, not an analytics surface. **Exception:** an analytics-rich detail page — a research or monitoring view whose one entity carries genuine aggregates (price/rank over time, competitor share, ownership history) — does have analytics surfaces, often several. When two or more are present, §5e ranks them (hero / supporting / drill) instead of stacking them flat; do not suppress them just because the page is `detail`.

**Composition:** Record-view composition — neither table-first nor chart-led. The visual treatment (typography, badges, spacing) follows the visual system in section 4; this section governs mode. Per project policy §6/§7, a detail view is an extension of its operational list, not a standalone redesign.

---

## 4b. Analytics Structure (if present) — advisory

*A suggested analytical shape from the job analysis. The binding half — no fabricated figure, the deciding field not swapped for a proxy — is in Part 2. Form, placement and whether a band exists at all are yours.*

{Include this section ONLY if `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). Skip entirely for `none` and `recommended-drop`. This section defines what the analytics layer is FOR and what *shape* it takes, so the designer does not improvise — and does not default every band to the same trend-strip-of-small-multiples. The shape is governed by `{analytics_archetype}`, selected in step-01 §5c by the `analytics-surface-architect` skill (its taxonomy SoT is `shared/analytics-archetypes.md`). The fields below are rendered from that skill's captured decision object — do NOT re-derive them here.}

### 0. Analytics hierarchy (only when the page has ≥2 analytics surfaces — from §5e)

{Include this sub-section ONLY when `{analytics_hierarchy}` is non-empty (the §5e gate fired — the page carries two or more distinct analytics surfaces). Skip entirely for single-surface pages. It ranks the surfaces so the designer assigns visual weight deliberately instead of stacking them flat — policy §6 (one or two lead charts + supporting), §5 (no card-grid-as-structure). Rendered from the captured §5e decision; do NOT re-rank here.}

- **Primary question of the page:** {from `{hierarchy_rationale}` — the one job that decides the ranking}
- **Hero (full-weight, 1–2):** {the surface(s) tagged `hero` + archetype — the chart that answers the primary question}
- **Supporting (compact — sparkline / strip / mini):** {each `supporting` surface + archetype, demoted to a compact form, NOT a full panel}
- **Drill (collapsed behind expand):** {each `drill` surface + archetype, available on demand, not in the default scan}
- **Why this ranking (demoted, not deleted):** {from `{hierarchy_rationale}` — why the hero leads and why each other surface is kept but subordinated; a research/detail page keeps all of it, ranked}

When this sub-section is present, the A–E spec below is written **per surface**, in hero → supporting → drill order, each at the visual weight its tier dictates (the hero gets the full A–E treatment; supporting/drill surfaces get a compact form + drill path, not a full-panel spec).

### A. Archetype & job

- **Archetype:** {analytics_archetype} — {one of: trend | distribution | composition | ranking | coverage | flow | waterfall | single-metric | correlation}
- **Band provenance:** {band_provenance} — {if recommended-new: "net-new — confirmed with user on {date}"}
- **The one question this band answers (1 sentence):** {state it in the user's words — e.g. "which weeks are we missing statements for, and in which region?" Do NOT restate as a generic "show trends."}
- **Why this archetype (grounding):** {from `{archetype_winner_reason}` — names the data dimension AND the user question that selected it, e.g. "coverage: data has per-week × per-region completeness; the job is finding gaps, not reading a trend."}

### B. Reading passes (derived from the archetype)

Do not impose a fixed headline → trend-strip → table sequence. Read `shared/analytics-archetypes.md` for the selected archetype and let its **form** drive the passes. Specify each pass the band actually needs:

- **Lead pass — the form that answers the question fastest:** {the archetype's form, made concrete for this feature. For `coverage`: a completeness strip where the gaps are the content. For `ranking`: a sorted top-N bar list capped and labelled. For `composition`: a single 100%-bar. For `flow`: a funnel/stage strip with drop deltas. For `waterfall`: an anchored opening bar, signed labelled steps, an anchored closing bar — deltas reconcile to the close, reasons live in the step's drill (not a duplicate chip). For `single-metric`: one value + sparkline + threshold. For `trend`: small-multiples with a stated Y-axis rule — **and for a two-magnitude trend (a realised primary like committed/actual/spent plus a subordinate projection like provisional/forecast/pipeline/budget), a solid primary line/area + a ghosted/dashed subordinate reference band, never stacked and never two co-equal lines, with rounded axis ticks and exact figures in the drill (not per-bar labels).** State dimensions, ordering, and what is emphasised.}
- **Secondary pass (only if a second archetype genuinely co-occurs):** {from `{archetype_secondary}` — name it and keep it subordinate, e.g. "coverage is dominant; a faint per-region trend is secondary, not co-equal." Omit if `{archetype_secondary}` is `none`.}
- **Evidence pass — path to the rows:** {what the underlying records show that the lead pass cannot — exact values, states, drill affordances. Every band must preserve a path to evidence; a band that can't show its working is a dashboard.}

### C. Drill behaviour

Every analytics element must have a defined drill target — no ornamental elements (the cross-cutting rule from the archetypes file). Render this from `{archetype_drill_map}` (the skill's element → drill-target map); for each element the band contains, state exactly where interaction goes:

- **Lead element(s):** {from `{archetype_drill_map}` — e.g. for coverage: "a gap mark opens the missing record's import action at `/route?week=…&region=…`"; for ranking: "a bar opens that entity at `/route?entity=…`"}
- **Value / label / delta affordances:** {what each click does, in this feature's routes}
- **Empty / inactive / gap state:** {what a no-data or gap cell does — open the resolving action, not a dead tooltip}

### D. Palette & status rules

Specify whether the operational status palette extends into the analytics surface:

- **Can the band use status colors?**
  - No — status palette is reserved for operational states only.
  - Yes, but only for: {describe scope — e.g. "gap marks in the coverage strip may use the warning color, since a gap IS an actionable exception state."}
- **How are movement / category encoded?** {prefer position, glyph, and typographic weight over hue — e.g. "direction by arrow glyph + typographic color; categories by label and position, never by fill hue. No colored pills, no tinted delta backgrounds."}

### E. Prohibited analytics patterns (page-specific)

Render the page-specific bans from `{archetype_prohibited}` (the skill's `prohibited` list), plus the cross-cutting bans from `shared/analytics-archetypes.md`, beyond the global hard constraints in section 5:

- No KPI / stat-card row above the table (dashboard fingerprint).
- {from `{archetype_prohibited}` — archetype-specific, e.g. for trend: "no single multi-series line chart; each series its own small multiple; **no stacked columns — absolute for a trend, including a committed+provisional stack (do NOT soften this to 'unless it is the composition'); no per-bar value labels standing in for an axis; a two-magnitude actuals-vs-forecast trend stays distinct (solid primary + ghosted subordinate), never collapsed to one series nor inflated to two co-equal lines.**" For composition: "no pie/donut; no time-stacked bars." For coverage: "'all good' must not look identical to 'gaps present' at a glance." For ranking: "do not render all N — cap and label the cut."}

---

## 4c. Surface Topology — advisory

{Include this section ONLY when `{surface_topology_verdict}` is NOT `single-page-appropriate`. Omit entirely — no heading, no placeholder — when the verdict is `single-page-appropriate`.}

{`{surface_topology_notes}` — the recommended topology for this feature, as assessed in step-01 §5d. This section informs the designer that the feature they are designing is one surface in a multi-surface feature — not the whole story. The surrounding context shapes composition, navigation affordances, and what belongs on THIS surface vs. another.}

**This brief covers:** `{route}` — {one-line job description for the primary route only}.

{Render only the applicable conditional block below; omit the others:}

{If `needs-detail-route`:}
**Recommended: detail route (separate brief):** `{feature_prefix}/[id]` — the per-item deep-dive; full evaluation evidence, record-level actions, field-depth content that does not fit a drawer or list row. This brief does not cover that surface. {Note whether a second brief was generated in this session or is pending.}

{If `needs-tab-views`:}
**View structure within this route:** {List the tab names and the operator job each one owns. The designer must accommodate this view structure in the IA. Tab names should describe the operator job, not just the content category.}

{If `needs-sibling-route`:}
**Recommended: sibling route (separate brief):** `{sibling_route}` — {the operator job it owns, distinct from the primary route}. This brief does not cover that surface. {Note whether a second brief was generated in this session or is pending.}

---

## 4d. Analytic depth (decision-bearing figures — render like an analyst, not a schoolboy)

*Binding half (carried into Part 2): no fabricated interval or baseline; a derived figure is never presented as stored. Everything else here — the lead read, which uncertainty to show and how — is advisory.*

{Include this section ONLY if `{has_decision_numbers}` is `true` (the surface presents figures the user acts on — verdict, score, ROI / margin / profit, KPI). Omit entirely for pure data-entry / passive-review / list-only surfaces. This is **surface-level, not band-only**: it governs the depth of every decision-bearing figure WHEREVER it sits — the §4b band's values AND the §4a record / hero / verdict numbers (a `detail` buy page's `ROI 42%` / `+£840` hero figures are exactly the case a band-only check misses). A correctly-shaped surface still fails if its figures are naked point estimates with no baseline and no read — *correct and useless*. Rendered from the `analytics-rigor` skill's captured decision (step-01 §5c-2; one block **per surface** on multi-surface pages) — do NOT re-derive.}

- **`rigor_source`: {skill | inline-fallback | not-applicable}** {REQUIRED — never omit. `skill` = the `analytics-rigor` skill was invoked this run (name its version if reported). `inline-fallback` = §5c-2's by-hand path produced this section — **state the reason** (skill absent / older sync / invocation failed); this is sanctioned, not a failure, and must not be hidden. Both paths render an identical-looking §4d, and every consumer treats a populated §4d as evidence the pass ran — so an undeclared fallback manufactures the evidence that enforcement succeeded, and `C-RIGOR-01` (which takes this section as ground truth) cannot catch it. This line is SELF-REPORTED: it makes the fallback visible, it does not make a `skill` claim true. A §4d with no `rigor_source` is malformed and is warned at commit time by `.githooks/check-design-brief-completeness.sh`.}
- **Lead with this read:** {rigor_read_sentence — the one-line conclusion the surface states BEFORE the evidence, e.g. "Buy: 47% ROI, top quartile — but the buy-box is a coin-flip, so size small." / OR "— none: this surface carries no single decision."}
- **Decision-bearing numbers — each carries uncertainty AND a base rate:** {render `{rigor_decision_numbers}` — per metric (a §4b band value OR a §4a hero/verdict figure), the range / confidence / assumption it must show AND the baseline it's shown against (portfolio median / category norm / own history). A bare point estimate on any of these is a defect, not a style choice.}
- **Basis — every cost / KPI figure states DERIVED vs PERSISTED:** {for each money / cost / KPI figure, state whether it is **persisted** (stored as-is) or **derived** (computed at render — e.g. a pack-split implied unit cost = total ÷ pack qty). On a finance-shaped surface this is carried from the finance-domain-pass `basis` field (§3b); on any other surface that still shows a cost/KPI (an operational cockpit is the common case — the pack-cost figure lives on a non-finance surface) classify it here from the data / API source — the requirement does NOT depend on the finance pass having run. A derived figure MUST be labelled as derived wherever it is shown, so the operator never reads a computed number as a stored fact. Basis left unstated on a cost / KPI figure is a defect. / OR "— none: this surface has no cost/KPI figures."}
- **Deciding field per chart (not the handy proxy):** {render `{rigor_deciding_fields}` — for each series, the field that actually answers the question, e.g. "share of *sales* (sold-30d), NOT share of on-hand stock." A proxy substituted for the deciding field is a defect.}
- **Data gaps (surface, NEVER fabricate):** {render `{rigor_data_gaps}` — metrics not yet in the data; until enrichment supplies them the figure ships as an honest bare number with the gap noted, never a faked interval or invented baseline. / OR "none — every figure is satisfiable from current data."}

---

## 4e. Decision analysis (capital-commitment surfaces — render like a quant desk, not a report)

*Binding half (carried into Part 2): no stated probability or expected value without a model behind it; an un-modellable decision is never shown as a confident distribution. How the bet, sizing and breakeven are presented is advisory.*

{Include this section ONLY if `{is_capital_decision}` is `true` (the surface's job is to commit a scarce resource — capital / inventory slots / time — under uncertainty with a real downside: a buy / reorder / sizing / go-no-go-with-stake). Omit entirely for every other surface — a dashboard, coverage strip, status worklist, or report carries decision *numbers* (handled by §4d) but commits nothing, so it stops at §4d. §4d made the figures honest (senior-analyst grade); this models and sizes the *decision* (executive grade). Rendered from the `decision-analysis` skill (step-01 §5c-3; one block **per decision surface**) — do NOT re-derive. The visual system in §4 still governs all treatment: a modelled outcome distribution and a sizing read render flat and dense, never as a chrome-y "risk dashboard."}

- **`decision_source`: {skill | inline-fallback | not-applicable}** {REQUIRED — never omit. Same contract as §4d's `rigor_source`, higher stakes: this section carries a modelled distribution and a position size, so an undeclared hand-rolled block is a *sizing* recommendation with no model behind it, and `C-DECISION-01` takes it as ground truth. `inline-fallback` does NOT license inventing a distribution — the §5c-3 model-honesty gate still outranks it (honest `single-scenario` + named VOI gap).}
- **Frame the bet:** {render `{decision_frame}` — action · capital at risk · horizon · payoff (what is won, what is lost and for how long). e.g. "Commit £620 / 8 units, ~45-day hold; win = net margin, lose = capital tied up + return costs." The surface must state the stake and downside, not just an ROI.}
- **Modelled outcome (distribution, not a point):** {render `{decision_outcome}` — method (Monte-Carlo / scenario / closed-form / single-scenario) + P(success) · expected value · P10 · P90, with the model's assumptions named. e.g. "P(profit) 62%, E[ROI] 24%, P10 −£1.10, P90 +£4.30 — 4,000 GBM paths off the current price regime." If un-modellable, an honest `single-scenario` read + the VOI gap, NEVER a fabricated distribution.}
- **Sizing (to the loss tail, not the mean):** {render `{decision_sizing}` — the recommended quantity and the basis (loss-distribution / capital-cap / fractional-Kelly) and the downside it survives. e.g. "Buy 8, not 24 — at 24 the P10 outcome breaches the per-lead capital cap." A binary BUY/PASS or an unjustified quantity is a defect.}
- **Breakeven driver (the threshold that flips the call):** {render `{decision_sensitivity}` — the single most decision-sensitive input and its tipping point. e.g. "Breakeven buy-box-win rate is 22%; below that this loses money." This is the highest-value single read.}
- **Outside view + regime + asymmetry:** {render `{decision_context}` — the computed reference class (an owned-history base rate, the outside view beside the modelled inside view); the decision-relevant time window (regime-weighted, stale window excluded); and the payoff asymmetry that tilts the recommendation (cost of a wrong commitment vs a missed one). Compute reference classes from owned data; do not declare them gaps.}
- **Value-of-information & gaps (surface, NEVER fabricate):** {render `{decision_gaps}` + the VOI ranking — the missing input that would most move the decision (so the operator knows whether to act or wait), and any probabilistic input absent today. An un-modellable decision ships as an honest `single-scenario` read with the gap named — never a confident P(success) off an invented input. / OR "none — the decision is fully modellable from current data."}
- **Decision verdict at handoff:** `{decision_verdict}` (decision-grade | risk-modelled | single-scenario)

---

{if {is_processing_cockpit}}
## 4f. Interaction model — advisory (the binding half is in Part 2)

*This surface's job is **repetitive per-item processing at speed** by expert, high-frequency operators
(a queue/cockpit worked one item at a time). How the operator DRIVES the surface is a load-bearing
requirement, not decoration — a beautiful surface with no operation model ships as a click-only form and
the speed goals silently fail. The signals for this section are already in the brief (§3 "keyboard-first
/ high-frequency", §1 success metrics about time-to-decision / fewer stuck defers); this section turns
them into requirements. Describe the OPERATION, never widgets or key bindings' visual chrome. Each
requirement below is derived from `{interaction_model_contract}`, never invented.*

- **Operation surface (keyboard-first is a requirement, not a nicety):** {is the primary driver the
  keyboard or the pointer? For an expert high-frequency processing cockpit it is keyboard-first: every
  per-item action (§1 capabilities) must be reachable and committable without leaving the keyboard, and
  a persistent shortcut affordance must exist. State it as an outcome ("clear a lane without touching the
  mouse"), never a specific key map — the bindings are the designer's.}
- **Per-item action set & commit semantics:** {the operator's per-item verbs (from §1's must-support
  capabilities), each classed by commit weight: **reversible** (skip, defer, claim) vs **irreversible /
  high-stakes** (writes an immutable key, money, or a partner-facing record). The irreversible ones REQUIRE
  a consequence-preview (below). These verbs cross-check the §3 mutation-derivation audit — a commit that
  invokes a server action must already be in `{must_support_capabilities}`.}
- **Momentum / flow after a commit:** {what happens the instant an item is decided — does the operator
  advance to the next actionable item, and how (auto-advance vs manual), with what safety window (an
  undo/toast). Clearing a lane must be continuous motion, not commit → hunt → click. Derived from the §1
  speed metrics; auto-advance must skip items the operator cannot act on (claimed-by-other, read-only).}
- **Consequence-preview before an irreversible commit:** {for any commit that writes something hard to
  undo (an immutable join key, a money figure, a partner write), the operator must be able to see WHAT the
  commit will write — the resulting record and any derived figure (§2b basis) — BEFORE committing. Seeing
  the outcome is the correctness lever; a blind irreversible commit is a defect. Name which per-item
  verbs need it.}
- **Confidence-scaled effort (fast path vs forced decision):** {where the machine is confident and
  unambiguous, a one-action fast path (the uncontested case costs one key/tap); where it is ambiguous or
  the detectors disagree, the full decision is FORCED (no rubber-stamp). Derived from the §1
  "fewer stuck defers / faster decisions" metrics — the design must let the easy case be fast without
  letting the hard case be skipped.}
- **Open questions — unresolved interaction semantics (do NOT guess these):** {any per-item verb whose
  commit weight, momentum behaviour, or preview need is not derivable from the code/context — carried to
  the brief's Open Questions verbatim, never resolved here.}

{if {operator_domain_present}}
### Operator domain

*Who the operator is, and what this surface must SHOW before it ASKS. §4f (above) captured how the
operator DRIVES the surface; this captures the operator's ROLE semantics so the evidence layer (the
cockpit's M6 floor) is grounded in the operator's real job, not generic cockpit doctrine. The failure
this prevents: a surface that asks the operator for input the system could have resolved and shown
first (asking for an identifier the system already holds). Every requirement below is lifted from
`docs/{operator}-operational-profile.md` via `{operator_role}` / `{operator_trust_boundary}` /
`{operator_decides}` / `{operator_known_before_ask}` / `{operator_evidence_required}` /
`{operator_forbidden_asks}` / `{operator_must_not_infer}` / `{operator_ordering_invariants}` — never
invented, never read from the current UI.*

- **Operator & trust boundary:** {`{operator_role}` — identity, trust relationship, expertise,
  frequency. Then the boundary from `{operator_trust_boundary}`: what the operator **may decide**, what
  they **may not decide** (owner-gated / verification-required), and which of their writes are
  verifiable vs. taken on trust. A required ask that would force a *may-not-decide* outcome is a defect.}
- **Per-decision — show before ask:** {for each decision in `{operator_decides}`: the one outcome the
  operator commits, the facts the system must RESOLVE AND SURFACE FIRST (`{operator_known_before_ask}`),
  the evidence that must be on-screen for that decision (`{operator_evidence_required}` — this fills the
  cockpit M6 "which evidence"), and the asks the surface must NOT make at that point
  (`{operator_forbidden_asks}`). State as outcomes, never widgets.}
- **Ordering invariants (the design must honour these):** {`{operator_ordering_invariants}` —
  expected-contents-first → identity-before-identifier → evidence-before-input, plus any
  operator-specific ordering. No decision may require operator input before the evidence/knowledge it
  depends on is surfaced.}
- **Must not infer (operator-truth constraints):** {`{operator_must_not_infer}` — e.g. don't guess an
  identity the operator can't confirm; don't ask the operator to decide outside the trust boundary.}
- **Open questions — operator/policy collisions (do NOT resolve here):** {`{operator_policy_collisions}`
  — any place operator meaning collides with `docs/design-policy.md`, carried to the brief's Open
  Questions verbatim for a human to decide and record; `none` when clean.}
{endif}

---
{endif}

## 4f-c. Controls, attention and faults — the evidence for TC1/TC2/TA1/TA2/TF1 (this table is advisory; the five tests are not)

*Rendered on every run from step-01 §3j. Contract: `shared/controls-and-attention.md` (STD-CONTROLS-ATTENTION-001). This section is **evidence, not instruction** — it tells you which controls this surface is expected to need and why each one earns its press, so the five Part 2 tests can be checked against something concrete. **Whether to draw a control here, where to put it, what it looks like and what it says are all yours.** If a control below turns out not to earn its press in your design, say so in your notes — removing it is a legitimate design decision, not a dropped requirement.*

**Controls this surface is expected to need**

| Control (the operator's verb) | What the press tells the system that the system does not already know | Class | Consequence |
|---|---|---|---|
{for c in {expected_controls}}| {c.verb} | {c.earns — decides / supplies / authorises / the operator knows the world just changed} | {c.class — reversible \| irreversible} | {c.consequence} |
{endfor}

**Work the system does on its own — do NOT turn these into controls (TC1)**

{for b in {background_work}}- **{b.name}** — the page says {b.says: what it is doing, and when it last ran}. A press here would tell the system nothing it does not have. Where the operator genuinely knows the world just changed, a quiet *do it now*, once per group, is legitimate — never a filled button repeated per row. `[tradeable]`
{endfor}

**Categories that look like work and are faults — name them, own them elsewhere, count them apart (TF1)**

| Category | Owner (never the operator) | Why it recurs | What actually fixes it |
|---|---|---|---|
{for f in {fault_categories}}| {f.name} | {f.owner} | {f.why} | {f.fix} |
{endfor}

**Text weight — advisory repair for TA2.** The repair for a text-heavy surface is not shorter sentences; it is depth. Carry on the row the shortest phrase that distinguishes it from its neighbours, and put the reasoning, the dates and the other side's exact words one layer down. `[tradeable]`

## 4g. Viewport & responsive — advisory

{Render on EVERY `page` run (required; `chrome` runs skip — nav breakpoints are in step-01 §0). If `{viewport_present}` — fill the table from policy. If `{viewport_pending_policy}` (an owner class whose §8.3 mobile ambition is still OPEN) — STILL render, but show the ⚠ PENDING POLICY banner below and leave the six fields as `pending`; never render a guessed posture.}

The per-surface viewport posture, sourced from `docs/design-policy.md §8` — not invented. **Advisory** (a layout rule, brief-binding-contract.md §2): design for the posture the policy names unless you have a better idea, and say so if you depart.

| Field | Value |
|---|---|
| `surface_class` | {viewport_surface_class} |
| `primary_viewport_class` | {primary_viewport_class} |
| `breakpoints` | {viewport_breakpoints} |
| `min_tap_target` | {viewport_min_tap_target} |
| `overflow_rules` | {viewport_overflow_rules} |
| `device_exclusions` | {viewport_device_exclusions} |

{if `{canonical_viewport}` is set (a DECIDED class — omit this whole block on an OPEN owner ambition):}

**Canonical vs additive viewports — how to render and label this surface.** The table above says which viewport this surface is DESIGNED FOR. This block says how your deliverable must MARK it, so no reader has to infer it:

| | Viewport | Status |
|---|---|---|
| **Canonical** | {canonical_viewport} | The interaction model is designed here and judged here. Draw this first, largest, and label it. |
| **Additive** | {additive_viewports} | Verification renders — proof the canonical model survives a different container. A check on the design, not a design. |
| **Not rendered** | {viewport_device_exclusions} | Excluded by policy. Do not produce a comp at these widths at all. |

Three suggestions for labelling the deliverable (advisory — a departure is a note, not a failure):

1. **Label the canonical viewport in-page** — a visible heading or caption on the artifact itself, not a manifest field, not a code comment. Form: *"Canonical viewport: {canonical_viewport}. Tablet/desktop below are additive verification renders, not co-equal designs."*
2. **Group additive renders after it, subordinate** — under a single **"Additive verification viewports"** heading, placed after the canonical render, never side-by-side at equal prominence, never larger, never first in reading order. Equal-weight phone/tablet/desktop columns read as three designs rather than one; avoid them unless that is the point.
3. **Additive renders preserve the interaction model, never re-premise it** — describe what the extra (or reduced) width does with the SAME model: reflow, more rows visible, a persistent rather than overlaid drawer. Do NOT convert a phone-primary scan-first single column into a wide multi-column table premise, add hover-dependent affordances, or introduce controls the canonical render lacks. On a handheld-first surface the desktop render is **a wider phone**, not a desktop app.

> **Why this is spelled out.** An unlabelled three-viewport comp set contradicts no field in the table above, so it passes every viewport check — while a cold reader (a fresh design session, a PR reviewer) resolves the ambiguity with the industry default: *desktop is the design, phone is the shrink*. On a handheld-first surface that silently reinstates the desktop-only premise the policy forbids.
{endif}

{if `{primary_viewport_class}` is `mobile-first`/handheld-first — omit this whole block otherwise; it does NOT apply to a desktop-only class or an OPEN owner ambition:}

**Handheld-First Declaration — what this surface IS, and what shape the artifact must take.** The block above settles *which* render is the design. This settles *what shape* the deliverable is. Both are required; neither substitutes for the other.

| # | Field | Value |
|---|---|---|
| 1 | Surface class | {viewport_surface_class} |
| 2 | Canonical viewport | {canonical_viewport} |
| 3 | Additive viewports | {additive_viewports} |
| 4 | Scan / next-step loop | {the primary operator loop as a LOOP — trigger → feedback → next; never a feature list} |
| 5 | Offline / degraded state treatment | {which degraded states are first-class, and the statement that each is drawn as a state OF this surface} |

**Suggested composition for your deliverable (advisory — `operator-artifact-contract.md` B1–B7 is the product's best current thinking, not a pass/fail list):**

1. **B1 — one canonical operational surface, first and dominant.** The artifact opens with ONE render: this surface at {canonical_viewport} in its resting state — first in reading order, largest, the only thing above the fold. A reader who stops after the first screenful must have seen the surface the operator actually uses.
2. **B2 — additive renders stay subordinate** (as rule 2 of the block above).
3. **B3 — state variants are DEGRADED STATES of this surface, never peer designs.** Same frame-name stem (`{primary}--{state}`), same chrome, same skeleton, same primary-action position; ONE legible region differs; presented as a strip beneath the canonical render under a single "States of this surface" heading, in operator-encounter order. A variant with its own nav or hero has become a second product — which means the state was mis-modelled.
4. **B4 — rationale comes AFTER the operational surface.** IA rationale, component specs, interaction notes and open questions live in a labelled block BELOW the canonical render and its state strip. Prose must not open the artifact, must not sit between the canonical render and its state/additive groups, and must not be interleaved paragraph-by-comp. This is an operator surface with an appendix, not a document with figures.
5. **B5 — the primary action and the next-step loop outrank explanatory text, measurably.** Largest type, strongest contrast, most reachable position (thumb zone). The squint test: squint at the canonical render — if a heading, paragraph, legend, or caption reads first instead of the action and its loop, the hierarchy is worth another look. (The binding version is T0: can a reader state the page's answer in five seconds?)
6. **B6 — main-surface copy is operator register.** Short, imperative, scannable at arm's length by someone holding a phone in an aisle. Long-form explanation is RELOCATED to the notes block, not deleted.
7. **B7 — the canonical surface is a COMPRESSED OPERATIONAL STACK, not a dashboard opener** (table-first surfaces — list/table/queue/worklist). A compact header block that reads as the top of the list, then data immediately: the count and primary action loud but **inline in the worklist header** (no hero band, no billboard CTA row, no large empty half, no separate summary card); secondary counts, caveats, filters and sorts collapsed into the same vertical rhythm at label weight (**no chip wall**); **at least one real data row visible at rest**. Full rules and the §7 composition spec below.

> **B7 is why rules 1–6 are not sufficient.** Rules 1–6 govern the artifact; B7 governs the inside of the canonical render. B5 is satisfied *by construction* by a billboard CTA — the action really is the loudest thing on the page. Loudness was never the question; **shape** is. Review reports a dashboard opener as a note.

> **The failure shape these prevent has a name: REVIEW BOARD** — co-equal comps plus explanatory prose presented AS the deliverable, instead of one operational surface with everything subordinate to it. It is the default shape a generator produces whenever composition is left unspecified, and it contradicts no field in this brief — which is exactly why these rules are written down.

{if `{viewport_pending_policy}`:}
> **⚠ PENDING POLICY — owner mobile ambition not set.** The owner has not chosen the mobile ambition for this surface-class in `docs/design-policy.md §8.3` (tablet-down desktop-primary · mobile-first · desktop-only). This brief is **unverified / pending-policy**; the viewport fields above are `pending` and must NOT be designed against a guessed posture. Set the ambition in §8.3, then re-run to fill them. (Work continues — this is a warn, not a freeze.)
{endif}
{if `{viewport_surface_class}` is DECIDED in policy §8.2 — render the banner matching ITS decided posture, never a hardcoded one:}
> **Decided surface (policy §8.2) — the policy's decided posture (advisory; a departure is a note).** If **desktop-only** (e.g. a grading/bench class): ≥1280px, landscape, keyboard + hardware scanner, scanner-first; a mobile / faux-mobile card here is a policy VIOLATION (the project's clerk-web-mode hard-failure). If **handheld-first / mobile-primary** (e.g. a roaming receiving clerk): phone viewport, portrait, one-handed, mobile scanner, offline-capable per policy; a desktop-only, mouse-dependent layout is the VIOLATION here. Do NOT invert the class's decided posture.
{endif}

---

## 4h. Disclosure layers — what is on screen at rest, and what is one action away (layer assignment advisory)

{# RENDERED ONLY when disclosure_model == three-layer. When the surface carries no audit contract,
   OMIT this whole section — Block B already records `disclosure_model: n/a — <why>` and an empty
   layering section on a settings page is noise. Contract:
   shared/disclosure-layer-contract.md — read it; do NOT restate its doctrine here, render the
   surface-specific ASSIGNMENT. #}
{if `{disclosure_model}` == "three-layer"}

**The contract, in one line: *"inspectable" is what this surface owes; "permanently displayed" is
not.*** Complete provenance, freshness, derivation, conflicts and override history are all owed and
all reachable — that obligation is binding and is carried into Part 2 as tests ("every figure's source,
freshness and derivation is inspectable"; "a reader can never mistake a stale or partial figure for a
current one"). **The layer assignment below is ADVISORY** — a suggested way to keep the evidence model
from becoming the interface (`shared/disclosure-layer-contract.md`). The owner's review of the
TheFBAPrep page found a better one than per-figure annotation: a stale read rewrites the headline.

**Layer 1 — WORK. Always visible, and the dominant visual region.**
{`{work_layer_elements}` — identity · readiness state · the ONE dominant next action · every field
the operator edits or commits. Name them.}

**Layer 2 — CONFIDENCE. Compact and visible.**
- Overall evidence indicator: {`{evidence_indicator_placement}` — near the commit control.}
- Exception strip: rendered **only when action is needed**. It NAMES the affected element and the
  reason in plain language; a bare count with nothing named FAILS (D4).
- Field-level signals, and the split that matters (D3):
  - **Exception signals** — {`{exception_signals}`, e.g. `Unverified` · `N conflicts` · `Stale`}.
    Each earns a named strip entry and counts toward the strip's number.
  - **Neutral authorship signal** — {`{neutral_signals}`, e.g. `Owner edited`}. Carries a field
    signal, opens the inspector, and **never enters the strip or its count.**
- **Healthy, current, uncontested evidence gets NO signal.** Silence is the affirmative statement.

**Layer 3 — EVIDENCE. Complete, disclosed, one action away.**
{`{evidence_layer_contents}` — itemise. Full provenance and source records · freshness detail with
every state distinguished · the original generated value · conflicts and their resolution status ·
derivation trace · override history with author, timestamp, reason and before/after · the canonical
record · audit history. **"Disclosed" is not an answer** — an unspecified inspector is how
auditability actually gets lost (D7).}
- Reachable from: the overall indicator · any field-level signal · a `View evidence` / `Why this?`
  affordance · the controls that act on the evidence itself.
- **Deep-links** to the field, source, conflict or override that was signalled — never the top of a
  generic audit page.
- Never a permanently visible third column.

**What the disclosure model does not licence (D5 — where a line is also a Part 2 test, the test binds):**
- {`{visual_judgement_gates}` — wherever the judgement's material is an IMAGE, the images are on
  screen at the point of judgement, at judgement size. This OUTRANKS the disclosure model; "one
  click away" never satisfies it. Name the frames it applies to, or state `none on this surface`.}
- Blockers stay in layer 1, named, with their route to resolution. A blocker is not evidence.
- Type/spacing are not the lever [tradeable]: body ≥14px, field value 15px, field label 12px, group
  heading 11px tracked uppercase for major groups only, nothing below 11px. Shrinking to fit is the same
  failure treated cosmetically.

{endif}

---

## 5. Style floor — advisory

*These are the product's style and anti-AI-slop floors. They are ADVISORY (brief-binding-contract.md §2). Any item that is really a truth rule (a reader could come away believing something false) has already been carried into Part 2 and binds there; what remains here is look and feel. Items that exist only for consistency across the product are **[tradeable]**.*

{Use ONE of the following variants based on `{design_system}`:}

**--- If `{design_system}` = "branded" ---**

The project's own list (advisory here; truth-class items moved to Part 2):

{Copy section 8 from brand identity — numbered hard failure list, verbatim, EXCEPT items the step-03 classification moved to Part 2 as truth tests (list those by number: "moved to Part 2 as T{n}"). Mark consistency-only items [tradeable].}

**AI fingerprint sensitivity:**

{Copy section 9 from brand identity — sensitivity table, verbatim}

Additionally, the FULL canonical AI-fingerprint taxonomy applies — it is embedded verbatim in §5b
below (machine-copied from `shared/design-standards.md`, never hand-excerpted; the brief carries
the whole taxonomy because the designer receives this brief, not that file).

**Self-test (advisory):** if someone would guess AI was involved, it is worth another pass.

**--- If `{design_system}` = "external" ---**

{constraints — responsive, data density, accessibility, performance, navigation position}

**--- If `{design_system}` = "existing" ---**

> No project design policy exists, so only **universal anti-AI-slop guardrails** apply. Aesthetic-specific rules (status color count, sidebar policy, status fill treatment, accent color, type family, etc.) are project decisions and should be added to `docs/design-policy.md` rather than asserted here.

**Universal anti-AI-slop guardrails (advisory — the product's floor, reported as notes):**

1. No bento or asymmetric "magazine" grid layouts
2. No hero strips, banner panels, or marketing-style intros above working content
3. No dashboard stat-card grids as page openers (classic AI fingerprint)
4. No 3-feature icon rows or colored-icon-circle clusters (classic AI fingerprint)
5. No gradient text, gradient backgrounds, or glassmorphism
6. No oversized container border-radius (>12px on panels/cards)
7. No animated number counters, hover lift/scale transforms, or other decoration effects
8. No purple/violet as default primary accent (`indigo-600` / `violet-500` are the AI default — pick a deliberate brand accent instead)
9. No icon on every label or heading — icons earn their place by adding information
10. No chatty empty states with illustrations
11. No invented branding (logos, taglines, product names) the project has not specified
12. No marketing copy or enthusiastic language in operational UI

{constraints — responsive breakpoints, data density, accessibility, performance, navigation position}

**Self-test (advisory):** if someone would guess AI-generated, it is worth another pass. Anything beyond the universal guardrails above (color counts, sidebar vs full-width, status treatment, type family, etc.) is the **project's** decision — when those decisions are made, capture them in `docs/design-policy.md` so future briefs include them as branded constraints rather than re-deriving them per feature.

The guardrail list above is the compact floor; the FULL canonical AI-fingerprint taxonomy is
embedded verbatim in §5b below and applies in every variant.

---

## 5a. Comfort Floor — advisory

{Emit this section for EVERY `{design_system}` variant. It is the product's comfort floor — ADVISORY for the designer (brief-binding-contract.md §2). "Colour is never the sole differentiator of meaning" is also a truth concern; where it matters on this surface, step-03 carries it into Part 2 as a test.}

Everything in §5 is a prohibition, and prohibitions have no lower bound. A design can satisfy every rule above, follow this project's density preference exactly, and still be uncomfortable to look at — because nothing above says how tight is too tight. **Density is the house style; cramped is a defect.** They are not the same thing, and this section is where the difference is decided.

Restated from `shared/design-standards.md` § Quality Checklist — the designer receives this brief, not that file.

**Spacing**
- Grouping reads through proximity: the gap *between* two groups is visibly larger than the gap *inside* a group.
- Uniform padding everywhere is a failure, not a neutral choice — it removes the only cue the eye uses to group, and reads as suffocating.
- Every spacing value comes from one scale (multiples of 4 or 8). No ad-hoc values.
- If rows, labels, or controls collide, or must be re-read to be told apart, density has passed its floor.

**Typography**
- Primary, secondary and tertiary content are identifiable in under 2 seconds.
- Three font sizes or fewer on the surface. More is a hierarchy failure, not richness.
- Monospace only for codes and identifiers.

**Accessibility**
- WCAG AA contrast: 4.5:1 body text, 3:1 large text.
- Keyboard focus visible — 2px minimum, high contrast.
- Colour is never the sole differentiator of meaning.
- Touch targets ≥ 44px on any handheld-class surface.

**States**
- Hover, focus, empty and error states are designed, not left to framework defaults.

**The squint test — how to check the 2-second rule:** blur your eyes at the screen. Something must read first. If nothing dominates, hierarchy has failed, regardless of every rule above being satisfied.

---

## 5b. AI-Fingerprint Taxonomy — canonical, machine-embedded (advisory)

{Emit this section for EVERY `{design_system}` variant. It is a MACHINE COPY, not authored prose:
at generation time, copy the canonical `## AI Fingerprint Detection` section — from that heading
through the end of `### The Composite Test` — VERBATIM from
`{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md` into this section, preceded
by the stamp comment below. Never hand-type, summarize, trim, or "adapt" it: a hand-copied excerpt
is exactly the drift channel that shipped an undetected fingerprint on 2026-08-24. If the standards
file cannot be read, this brief is NOT deliverable — HALT and report the unreadable path; do not
substitute a from-memory list.}

<!-- embedded-from: design-standards.md § AI Fingerprint Detection · run: {date} · this block is machine-copied; edit the source file, never this copy -->

{VERBATIM COPY GOES HERE}

{After the copy, close with:} If this project's brand identity declares an exception to any row
above (a named identity treatment with construction + scope), that declaration appears in §5's
brand-identity copy and overrides the row FOR THE DECLARED SCOPE ONLY. No other softening of this
section is legitimate — the taxonomy is the product's floor the project policy can tighten but not
silently relax. For the DESIGNER it is advisory: a fingerprint is reported downstream as a note, never
as a failure (brief-binding-contract.md §4).

---

## 7. Deliverable Format

### Surface Inventory — suggested frames (advisory)

This page spawns secondary surfaces at runtime — the detail drawer the operator drills into, and the lookup drawers (§2a) that open over it. **The rows below are SUGGESTIONS — which frames you draw is your call**, and a suggested frame you do not draw is reported downstream as a note, never as a failure. One practical reason to draw the ones that matter: `design-implement` builds from the frames you draw, and a drawer nobody drew gets built from inference. Where you do draw a suggested frame, keep its **Frame** name on it so the build matches by name. Where a better set of frames answers the moment, draw that set and say why.

| Frame (suggested) | Opens from / trigger | Suggested render | What it would carry | Figures (§4d) | Lookups (§2a, depth-1) |
|---|---|---|---|---|---|
| {frame_name} | {trigger} | {full-bleed \| drawer-over-{parent}} | {must_contain} | {the §4d decision numbers this frame carries, basis-complete per policy §15 — or "—"} | {depth-1 §2a fields — or "—"} |

{One row per entry in `{spawned_surfaces}`. The primary surface is always row 1; the drilled detail drawer is a row when the §5a composition spawns one; each `{linked_records_inventory}` entry is one lookup-drawer row.}

**Notes on the suggestions (advisory unless a line says it is a Part 2 test):**
- **No bare stubs.** A suggested lookup-drawer's "What it would carry" must name the fields the relation actually needs (a `warehouse-lookup` opened from an order shows code/type/status/location AND what's routed through it for this order), never identity alone. If the record genuinely carries nothing past identity, state that explicitly.
- **Depth-1 only.** A lookup drawer lists its own immediate lookups; the foreign record's own §2a owns the next level. Do not inline the recursive order→catalog→supplier graph.
- **Money is basis-complete — this one is a Part 2 test wherever money appears.** Every figure in a "Figures" cell follows `docs/design-policy.md` §15 — VAT basis, native currency framed against GBP, no decontextualised fragment; rendered as the detail surface, not a bare-number dump. **A derived figure (computed at render — e.g. a pack-split implied unit cost) is labelled DERIVED, never shown as a persisted value** (per §4d basis, carried from the finance-domain-pass `basis` field).
- **Entry point — how the operator REACHES this surface.** (Reachability of each §1 capability is a Part 2 test; the route to it is advice.) The first row's "Opens from / trigger" cell must state how the operator gets to THIS surface from the rest of the app — a global-nav entry, a link from a *named* parent surface, or a row-drill from a *named* worklist — so `design-implement` can VERIFY the ingress was actually wired (its step-04 flags an "unlinked island" when a built surface is reachable only by URL — the §L recovery-cross-check miss). **A sub-surface is NOT a nav peer:** a detail / drawer / record-view / §13 sub-surface is reached by a link or row-drill from its parent, **never** a global-nav entry (that is nav-bloat and misrepresents it as a sibling page). A top-level operational/analytical *page* is the only kind that earns a global-nav entry.

### Per-frame outputs

For **every frame you draw**, deliver:

1. **Visual designs at the CANONICAL viewport — `{canonical_viewport}` — as the primary render**, with `{additive_viewports}` shown after it, grouped under an "Additive verification viewports" heading and visually subordinate (§4g rules 1–3). Each drawer is rendered **open over its parent frame**, never as a standalone page. Label the canonical viewport in-page so no reader has to infer which render is the design.
   {if `{canonical_viewport}` is unset — an owner class whose §8.3 mobile ambition is still OPEN:} *Viewport posture is `pending-policy`; render at desktop width (1280px) as a working default and mark the deliverable pending the owner's ambition decision — do NOT treat that default as a decided posture.*
   {— never emit a bare "at desktop width (1280px)" instruction on a DECIDED class: on a handheld-first surface that single line silently reinstates the desktop premise the policy's posture avoids.}
2. **Component specs** for new UI patterns
3. **Interaction notes** — hover states, transitions, empty states, loading states; for drawers, the open/close/return-up-the-stack behaviour (§13 round-trip)
4. **Information architecture rationale** — why you grouped and prioritized information this way

{if `{primary_viewport_class}` is `mobile-first`/handheld-first:}
**Artifact composition — a suggested arrangement (handheld-first only; `operator-artifact-contract.md` B1–B7, advisory).** The list above is what to produce; this is the order that usually reads best:

1. **The canonical operational surface** — one render at {canonical_viewport}, resting state, first and largest, the only thing above the fold, labelled in-page (B1).
2. **"States of this surface"** — the state-variant frames as a subordinate strip beneath it: same skeleton, same primary-action position, one changed region each, in operator-encounter order (B3). Not a gallery of headline comps; not separate mini-products.
3. **"Additive verification viewports"** — {additive_viewports}, grouped, after, smaller, same interaction model (B2 / §4g rule 3).
4. **Notes & spec block, LAST** — items 2–4 above (component specs, interaction notes, IA rationale) plus open questions (B4). Rationale never opens the artifact, never splits the canonical render from its state/additive groups, and is never interleaved paragraph-by-comp.

Inside the canonical render: the primary action and the next-step loop are the most prominent elements — they must survive the squint test against every heading and caption on the surface (B5) — and on-surface copy is operator register, short and imperative, with long-form explanation relocated to the notes block (B6).

**Avoid a symmetric row of phone/tablet/desktop comps.** That shape reads as a **review board**, not an operator surface; review notes it.

{if this surface is table-first — its primary content is a list, table, queue, or worklist:}
**In-surface composition — a suggestion: a COMPRESSED OPERATIONAL STACK, not a dashboard opener (B7, advisory; review notes a departure).** The suggestions above are about how the ARTIFACT is arranged. This one is about how the SURFACE itself is composed: a render can satisfy every rule above — first, dominant, correctly labelled, primary action unmistakably loudest — and still open with a hero band and a wall of chips. Compose it as a compact header block, then data, immediately:

1. **Keep the header as ONE compact operational block** — not a banner, hero, opener card, or summary card above the list. It shares the worklist's horizontal grid and vertical rhythm and reads as the **top of the list, not a thing before the list**. If the header could be lifted onto an unrelated page unchanged, it is a banner.
2. **The loud count and the primary action ({the surface's primary action, e.g. "Go receive"}) may dominate — but only INLINE within the worklist header.** No large empty right half. No billboard CTA row of its own. No separate summary-card feel: no distinct background, border, or elevation separating the header from the list. Exactly ONE element carries display weight — the count and its action read as a single unit.
3. **Secondary counts, caveats, filters and sort controls collapse into the same vertical rhythm** at label/body weight, and must not visually compete with the primary action. **No chip wall** — no wrapping grid of pills, status chips, or metric tiles as an opener band. If secondary status needs more room than one collapsed line, it belongs in a filter control or in the rows themselves.
4. **At least one real data row is visible at rest** on {canonical_viewport} without scrolling, with the header block occupying no more than roughly a third of the viewport height. This is the measurable form of 1–3: *count the rows visible in your canonical render — zero rows means the composition is wrong.*

> **"Make the action loud" means loud WITHIN the header — never "give the action its own billboard."** The correction for a dashboard opener is always **compression, never deletion**: the count, the action, and the secondary status all stay, collapsed into the header block. The shape it avoids has a name — **DASHBOARD OPENER** — and review notes it.
{endif}
{endif}

---

## 8. Implementation Files (Reference Only)

Technical context only — NOT layout or design references.

{If `{design_system}` = "external": omit CSS/style files.}

| File | What it contains |
|------|-----------------|
| {3-5 key files} | {type definitions, API handlers, CSS tokens if applicable} |

{If `{design_system}` = "branded" AND `docs/design-policy.md` contains migration notes flagging non-compliant components, add this block immediately after the file table:

⚠️ **Token values only — do NOT anchor to existing component styling.** The policy flags these implementations as currently non-compliant; reading their code will bias Claude Design toward the wrong patterns:
{For each non-compliance named in the policy migration notes, e.g.:}
- `StatusBadge` — currently `rounded-full` with a leading Lucide icon; policy §3 requires `rounded-md`, no icon, no dot
- Categorical `--tag-*` palette in `tokens.css` — exceeds the 4-color operational status cap; status communication uses only `--status-danger/warning/success/neutral`

Read token VALUES (colors, `--radius-md`) from `tokens.css` — anchor to those. Do NOT anchor to the shape, size, icon, or decoration pattern of any component whose compliance is a migration target.}

{If feature_scope == "redesign", add this block after the file table (and after the token-values warning when present) — it is the enforcement half of the "Repo read protocol" in the preamble:

🚫 **DO-NOT-READ — current view implementation.** The files below render the CURRENT layout of this surface. Reading any of them defeats this brief's blank-canvas premise (structure, grouping, and control order will anchor you even if you only meant to check a detail). They are listed so the boundary is explicit, not discoverable by accident:
{For each entry in `{do_not_read_files}` (gathered in step-01 §3), one line:}
- `{file path}` — {what it renders, e.g. "the current view markup" / "current state→DOM rendering"}

If a fact you need lives only in a DO-NOT-READ file, STOP and report the gap as a brief defect — the fix is a brief revision, never reading the view.}

---

## Changelog

Minor revisions (clarifications only — see `brief-revision-policy.md` §1) append one line here. Material revisions re-run `design-handoff` instead; they do NOT append to this changelog — they live in a new brief file.

{If change_class is "material_revision", the first changelog entry below records the supersession; otherwise this section starts empty and is populated by future hand-edits.}

- {date} — {if change_class == "material_revision": "Material revision; supersedes `{supersedes_filename}`. Author: design-handoff workflow."; if change_class == "original": leave the bullet OUT entirely and the section will be empty until a clarification is added.}
````
