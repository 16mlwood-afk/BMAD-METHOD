# Step 2b: Regression-Surface Preflight — what does this handoff DROP vs production, and how should we implement it?

## MANDATORY EXECUTION RULES (READ FIRST)

- This step runs after the implementation is mapped (step-02) and **before** any grid is built or any code is changed (step-03/04). It is the proactive front end to the post-hoc "Capabilities removed (orphaned actions)" backstop in step-04 §9 — catch a dropped capability at intake, by intent, not after the apply already removed it.
- **A handoff is a PROPOSAL about treatment and composition, NOT an authorization to delete what production does.** A redesign frequently omits a capability the live page has — sometimes deliberately (a genuine simplification), sometimes incidentally (the designer never saw it, the bundle's mock data didn't exercise it). Which one it is, is **intent** — design-implement cannot infer it and must not guess. So when the handoff drops a production capability, this step **HALTS and asks** (grounding gate / halt-by-default), it does not silently reproduce the omission.
- **Skip cleanly when there is no production to regress.** If `{impl_page}` is a brand-new surface with no existing built page (nothing in step-02 to inventory), there is no regression surface — record "new surface, no production capabilities to compare" and proceed to step-03. This step only bites on a **redesign of an existing page**.

## YOUR TASK

Compare what the **current production page does** against what the **handoff delivers**, surface every capability the handoff would drop, and — if any — halt for the user's implementation-strategy choice. "Production" here means the **currently-built page** (the impl on the working branch / main — the code step-02 just read), not a live scrape; the built code IS the capability set users have today.

## SEQUENCE

### 1. Inventory the PRODUCTION capability surface — feature-level, not CSS

From step-02's outputs (`{impl_components}`, `{impl_render_sites}`, the page + its layouts, the server actions those files import/call, the §13 lookup drawers, the route tree) enumerate what the page **does and shows today** — the *functional* surface, distinct from treatment. Capability classes to walk (not exhaustive — add any the page has):

- **Routing & sub-surfaces** — drilled detail routes/drawers, tabs, sibling routes, expand-in-context (§13) lookups the page opens.
- **Linked records (§13)** — every foreign record the page resolves/expands in context (the "link to records (lookups)"); each is a capability, not decoration.
- **Economics / cost surfaces** — full cost-recon, fee breakdown, landed cost, the §15 basis-complete money path to the owning record.
- **Composite header / status** — a dual-status (or multi-signal) header, derived flags, the status model the row/page carries.
- **Activity / history / audit** — an activity timeline, audit trail, raw request/response (§7) disclosure, pull-audit.
- **Bulk actions, filters, sort/chronology, search** — the operational machinery (§6) the worklist provides.
- **Server actions / mutations** — every capability wired to an action the page's files call (this overlaps the step-04 §9 orphaned-action grep; capture it here proactively).

Store as `{production_capabilities}` — a list of `{ capability, class, evidence (file/component/action), reached_via }`.

### 2. Inventory the HANDOFF capability surface

From the design side (`{design_components}`, `{design_frame_inventory}`, brief §7 Surface Inventory if a brief exists) enumerate what the **new design delivers** — its frames, drilled drawers, §13 lookups, the sections/affordances it draws. Store as `{handoff_capabilities}` (same shape). Be careful with the bundle's blindness: a capability the design *intends* but didn't draw (a frame consumed from a sibling brief, a behavior the static bundle can't show) is **present-in-intent** — use the brief §7 / `{design_frame_inventory}` to avoid scoring an undrawn-but-promised frame as "dropped." When unsure whether the handoff carries a capability, mark it `handoff: unclear` rather than `handoff: absent`.

### 3. Compute the delta

- **DROPPED (the regression surface)** = capabilities in `{production_capabilities}` with no match in `{handoff_capabilities}` (and not merely `handoff: unclear`). These are what the redesign would remove.
- **ADDED** = capabilities in the handoff with no production match (informational — what the redesign introduces).
- **CHANGED** = same capability, materially different shape (note it; it flows through the normal grid).

Store `{dropped_capabilities}` (the DROPPED list). Each entry: `{ capability, class, prod_evidence, why_it_matters (one line), handoff_status: absent | unclear }`.

### 4. Branch on the dropped set

**If `{dropped_capabilities}` is empty:**
Record one line — "Regression surface: none — the handoff retains every production capability; proceeding additively." Set `{implementation_strategy} = additive` (nothing to drop, so additive and replacement are equivalent) and continue to step-03. No halt.

**If `{dropped_capabilities}` is non-empty → HALT and present the regression report + strategy choice.** Do not proceed to the grid until the user chooses. Present:

**Be ADVISORY, not interrogative.** The analysis is YOURS to do — give a per-capability verdict (keep / safe-to-drop) with a one-line reason each, then a single recommended plan the user can approve in one word. Do **not** hand the user a blank menu and ask "which of these do you want?" — making them assemble the keep/drop list is the offload this step exists to avoid. The user's job is to approve or adjust your recommendation, not to enumerate it.

```
Regression check — this handoff DROPS {N} capabilit(y/ies) the live page has today.
My read on each, then a recommended plan:

  1. {capability} ({class}) — KEEP. {why it's load-bearing}.        prod: {evidence}
  2. {capability} ({class}) — KEEP. {why}.                          prod: {evidence}
  3. {capability} ({class}) — SAFE TO DROP. {why it's genuinely droppable here}.   prod: {evidence}
  …

Recommended: {strategy} — keep {…}, drop {…}. {one-line rationale}.
I'll apply this unless you'd rather change it (e.g. "also keep 3", "drop 1 too", "restyle only").
```

Rules for the advisory:

- **Every dropped capability gets YOUR verdict — KEEP or SAFE-TO-DROP — with a grounded one-line reason.** A §13 linked record, a §15 economics/cost-recon path, an audit/history/raw-exchange surface, an action-wired mutation → almost always **KEEP** (these are functional capabilities operators rely on). A genuinely redundant, decorative, or superseded element → **SAFE TO DROP**. Reason from what the capability *does*, not from whether the handoff happened to draw it.
- **Default the recommendation non-destructive; when in doubt on a capability, advise KEEP.** Never lean toward dropping a load-bearing surface. The recommended `{implementation_strategy}` falls out of the per-capability verdicts: all KEEP ⇒ `restyle-only` (or `additive` if the new composition is adopted); a genuine subset droppable ⇒ `partial` (the advised mix you just proposed); everything droppable ⇒ `replacement` (rare).
- **State the plan as a decision you're ready to execute, then invite adjustment.** "I'll apply this unless you'd rather change it" — a confirm-or-tweak, not an open question. The strategy names are shorthand for what the plan resolves to; the user replies in plain language.

### 5. Record the approved plan

- `{implementation_strategy}` ∈ `restyle-only | additive | partial | replacement` — the strategy your recommendation resolved to, as approved or adjusted by the user.
- `{capability_dispositions}` — the per-capability `keep | drop` map. For `partial` this is **the advised mix you proposed** (AI-authored, user-confirmed), NOT a list the user assembled; for the others it is derived (restyle-only/additive ⇒ all `keep`; replacement ⇒ all `drop`). If the user adjusted the recommendation, record the adjusted map.

**Autonomous mode does NOT override this.** A capability-drop decision is *intent*, outside decision autonomy (see autonomy scoping). In autonomous mode, default to the **non-destructive** strategy — `restyle-only` (keep every capability) — and disclose loudly in the run output (`autonomous: kept all {N} dropped capabilities — confirm if replacement was intended`). Autonomous mode never silently drops a production capability.

### 6. How the choice constrains step-03 / step-04

- For every capability marked **keep** (`restyle-only`, `additive`, kept rows of `partial`): the apply must **preserve** it. Its render sites / actions / lookup drawers are **protected** — the redesign's treatment is applied *around* them; they are not deleted just because the handoff frame omits them. A grid row that would remove a kept capability is re-classified `deferred(capability-protected)` with the reason, never silently applied.
- For every capability marked **drop** (`replacement`, dropped rows of `partial`): the handoff governs; the capability is removed — AND step-04 §9's "Capabilities removed (orphaned actions)" check runs over exactly these, confirming the removal is clean (no orphaned action, no half-loss) and disclosing it in the completion report.
- Carry `{implementation_strategy}` + `{capability_dispositions}` into step-03 (the grid notes protected capabilities) and step-04 (the apply ledger honors keep/drop and the §9 report states the chosen strategy + every kept/dropped capability).

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-03-build-grid.md`

## SUCCESS METRICS

- `{production_capabilities}` and `{handoff_capabilities}` inventoried at the feature level (routing, §13 lookups, economics, status/header, activity/audit, actions) — not CSS.
- `{dropped_capabilities}` computed; an undrawn-but-promised handoff frame (brief §7 / `{design_frame_inventory}`) is NOT mis-scored as dropped.
- If the dropped set is non-empty, the run **halted** with the regression report + strategy menu and recorded `{implementation_strategy}` + `{capability_dispositions}` — it did NOT proceed to the grid on an unconfirmed replacement.
- Kept capabilities are marked protected for step-03/04; dropped capabilities are routed to the step-04 §9 orphaned-action confirmation.

## FAILURE MODES

- **Reproducing the handoff's omission as fact.** Treating "the new design doesn't show the cost-recon / the activity timeline / the linked records" as "remove them" without asking. The redesign is a proposal; the drop is an intent decision that belongs to the user.
- **Offloading the keep/drop analysis to the user.** Presenting a bare strategy menu and asking "which of these do you want to keep?" is the failure §4 exists to prevent. You read the page and the handoff — so YOU advise, per capability, with reasons, and propose a single plan to approve. Make the user assemble the list and you've handed back the work that was yours to do.
- **Skipping the halt because the grid looked clean.** The component sweep greens out on a redesign that drops a whole capability (its inner primitives exist elsewhere) — exactly why this preflight runs before the grid, not after.
- **Mis-scoring an undrawn-but-promised frame as dropped.** A §13 lookup the brief §7 / frame inventory promises but the static bundle didn't render is present-in-intent, not a regression — check the contract before flagging.
- **Letting autonomous mode pick `replacement`.** Intent autonomy is out of scope; autonomous defaults to keep-all and discloses.
- **Inventorying treatment instead of capability.** "The button is a different colour" is a grid delta (step-03), not a capability. This step is about what the page *does*, not how it looks.
