# Step 2b: Capability-Delta Preflight — what does this handoff DROP *and ADD* vs production, and how should we implement it?

## MANDATORY EXECUTION RULES (READ FIRST)

- This step runs after the implementation is mapped (step-02) and **before** any grid is built or any code is changed (step-03/04). It is the proactive front end to the post-hoc "Capabilities removed (orphaned actions)" backstop in step-04 §9 — catch a dropped capability at intake, by intent, not after the apply already removed it.
- **The capability delta runs BOTH ways — DROPPED and ADDED — and they are equally load-bearing.** A redesign that *removes* a production capability is one failure mode (silent regression); a redesign that *adds* capability the live page lacks is the equal-and-opposite one (silent under-build — the workflow reads the uplift as a reskin and never constructs the new surface). The DROP axis halts for intent; the ADD/uplift axis does not halt (building what the design draws is the unambiguous contract) but it MUST be inventoried, foregrounded, and turned into a BUILD plan — never collapsed into "treatment alignment." An empty DROP set is **not** evidence the job is a restyle; an uplift redesign drops nothing yet is mostly net-new construction.
- **You may NOT conclude the implementation is "restyle-only / treatment-only / token-alignment / a structural superset / no net-new capability" until BOTH `{production_capabilities}` and `{handoff_capabilities}` are fully inventoried and the bidirectional delta (§3) is computed.** That verdict is a *capability-scope* claim; a token-level observation (raw-hex → canonical-token debt, a `var(--*)` mapping) is *treatment* evidence that belongs to step-03's grid, and it can never license a scope conclusion. Forming "just tokens / production is a superset" from treatment evidence — especially while the map (step-02) is still resolving — is the **running-blind** failure this gate exists to forbid. Inventory first; the scope verdict is an *output* of §3, not an intuition that precedes it.
- **A handoff is a PROPOSAL about treatment and composition, NOT an authorization to delete what production does.** A redesign frequently omits a capability the live page has — sometimes deliberately (a genuine simplification), sometimes incidentally (the designer never saw it, the bundle's mock data didn't exercise it). Which one it is, is **intent** — design-implement cannot infer it and must not guess. So when the handoff drops a production capability, this step **HALTS and asks** (grounding gate / halt-by-default), it does not silently reproduce the omission.
- **Skip cleanly when there is no production to regress.** If `{impl_page}` is a brand-new surface with no existing built page (nothing in step-02 to inventory), there is no regression surface — record "new surface, no production capabilities to compare" and proceed to step-03. (The ADD side is then trivially "everything is net-new" — still inventory `{handoff_capabilities}` so step-03/04 build it all.) This step's DROP halt only bites on a **redesign of an existing page**.

## YOUR TASK

Reconcile what the **current production page does** against what the **handoff delivers**, BOTH ways: surface every capability the handoff would **drop** (→ halt for the user's strategy choice if any), AND every capability the handoff **adds or materially deepens** (→ name it, set a build plan, never let it read as a reskin). "Production" here means the **currently-built page** (the impl on the working branch / main — the code step-02 just read), not a live scrape; the built code IS the capability set users have today. The handoff is the spec for what the page must *become*.

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

### 3. Compute the delta — BOTH directions

- **DROPPED (the regression surface)** = capabilities in `{production_capabilities}` with no match in `{handoff_capabilities}` (and not merely `handoff: unclear`). These are what the redesign would remove. → `{dropped_capabilities}`.
- **ADDED (the uplift surface)** = capabilities in the handoff with no production match. These are **not "informational"** — they are the net-new construction the redesign exists to deliver (a new analytics/disposition band, a lane-by-handler segmentation, a disposition action column, co-view tabs, a drilled drawer the live page never had). → `{added_capabilities}`.
- **DEEPENED** = a capability present in BOTH but **materially richer** in the handoff — same capability *class*, fundamentally more capable shape (a country-filter that became handler-lane segmentation with per-lane counts + capital; a flat status column that became a disposition band with a verdict vocabulary + per-row action). A deepening is a **build task, not a treatment delta** — its net-new sub-structure cannot "flow through the grid" because the grid is CSS-only (component × state × property) and will at best score the new sub-components `MISSING in impl` while the agent reads the parent as "same component, restyle." → `{deepened_capabilities}`.
- **CHANGED (treatment-only)** = same capability, same shape, different *treatment* (colour/spacing/radius). THIS is what flows through the normal grid — and only this.

Store all three lists. Each entry: `{ capability, class, evidence, why_it_matters (one line), status }`.
- `{dropped_capabilities}` — `status: absent | unclear` (handoff side).
- `{added_capabilities}` and `{deepened_capabilities}` — `evidence` is the handoff side (`{design_components}` / `{design_frame_inventory}` / brief §7); for DEEPENED also carry `prod_evidence` (the thinner production form it replaces).

Compute the combined **`{uplift_capabilities}` = `{added_capabilities}` ∪ `{deepened_capabilities}`** — the net-new construction surface. This is the symmetric twin of `{dropped_capabilities}` and drives §4b.

**The scope verdict is computed HERE, from these three lists — it is not an intuition:** restyle-only is licensable ONLY when `{dropped_capabilities}`, `{added_capabilities}`, and `{deepened_capabilities}` are ALL empty (pure treatment delta — CHANGED rows only). A non-empty `{uplift_capabilities}` means the job is **substantially a build**, regardless of how clean the token mapping looks. "Production is a structural superset" is true ONLY when `{added_capabilities}` AND `{deepened_capabilities}` are both empty — assert it only after checking, never as a prior.

**Frame RECOMPOSITION is a fourth signal — surface it, do NOT bury it in "CHANGED treatment-only."** A present frame (a detail/create/lookup drawer) can keep all its capabilities yet be **recomposed**: sections renamed, regrouped, reordered, or its header/footer chrome changed. That is what a user reads as "the drawer looks completely different," but classified as CHANGED it silently "flows through the grid" — where the per-component sweep cannot see arrangement (the grouping/order is owned by no single component). So when you compare each present frame's design composition (section order + group headings + header/footer chrome — from the manifest section inventory or the frame source) against the impl frame's, record a `{frame_composition_deltas}` entry for every frame that is materially recomposed: `{ frame, renamed_groups[], reordered: bool, regrouped[], chrome_delta (header/footer) }`. This is NOT a capability (it adds/drops nothing) — it is a **structural treatment** axis, and step-03 §2d-bis emits a Frame-composition grid row for each entry. **Name it in the preflight output**, so a scope halt shows the visual magnitude instead of a one-line "drawer · DEEPENED/treatment · buildable: yes" that reads as trivial (the real inbound-flow supply-order miss: Cost & sourcing→Economics, standalone Lifecycle→folded, Related records→Routing & source, black footer button→blue — all hidden behind one "treatment" line).

### 3b. Already-shipped recall — has this design ALREADY been applied? (SURFACE, never gate)

**The symmetric twin of Input Resolution's net-new preflight.** That check asks *"is there anything to diff against?"* and exits when the answer is nothing. This asks the other end of the same lifecycle — ***"is there anything LEFT to diff?"*** — and until it existed, the two ends were policed very differently: intake could spot a run that HALTED (Prior-halt recall), one that CHECKPOINTED (`{resume_prior_dispositions}` + the pending-checkpoint detector), and a surface with nothing built yet — but **not a design that was already fully applied and shipped.**

**This is the same trigger the Prior-halt recall was built for, not an edge case.** That block's own rationale is that the "Send to local coding agent" panel emits a *stable* prompt per file, so the identical input arrives again each time the owner revisits the design — and any project `design-handoff-detect` hook routes every such paste straight back here. That is as true *after* the work ships as while it is blocked; arguably more so, since revisiting a design you just shipped is the normal thing to do. Only the halted branch was implemented.

**Runs HERE — post-map, pre-grid — deliberately, and the placement is an honest trade.** It needs step-02's resolved impl paths and §3's computed delta to say anything trustworthy, so it cannot live in the cheap pre-ingest lane with the net-new preflight. **That bounds the saving to the grid + apply, not the ingest** — say so rather than implying it saves the whole run.

**Read two signals. Neither is new evidence — both are already in hand:**

- **Signal A — PROVENANCE (git).** `git log --oneline origin/main -- <the impl paths step-02 already resolved>`, looking for a commit naming the design, the `{target_slug}`, or a design-implement/design-ingest pass over this surface. Optionally extend to deployment: if the project records a live commit (a `/api/status`-style endpoint, a deploy log, a platform deployments tab), test ancestry — `git merge-base --is-ancestor <that commit> <live sha>` — and report **shipped vs merely merged**, which are different claims on this fork's projects (merge ≠ deploy in several of them).
- **Signal B — DELTA (already computed in §3).** Are `{dropped_capabilities}`, `{added_capabilities}` and `{deepened_capabilities}` **all empty**? An all-empty delta is precisely "nothing left to build."

**Three outcomes — this is a taxonomy, not a boolean, and the middle one is the valuable case:**

| A (git provenance) | B (delta all-empty) | Verdict | What the run does |
|---|---|---|---|
| ✅ | ✅ | **ALREADY SHIPPED** | Surface it and **recommend exiting** without a grid. Treatment deltas may still exist, so this is a recommendation, not a refusal — see the rule below. |
| ✅ | ❌ | **PRIOR PASS + RESIDUAL DELTAS** | **Continue — but re-frame the run as a RESIDUAL-DELTA pass, not a build.** The most valuable outcome: a prior pass applied most of the design and left specific gaps. |
| ❌ | ✅ | **MATCHES, NO PROVENANCE** | Note it and continue. The impl may match by convergence, or the design may have been applied by a route that left no traceable commit. Do not assert a prior pass you cannot evidence. |

Record `{prior_applied}` = `{ verdict, commit, subject, deployed: bool|unknown, evidence }`, or `none` when neither signal fires. **Absent / unreadable git history is a silent no-op** — same posture as the Prior-halt recall.

Surface it in the preflight output:

```
◇ This design appears to have been applied already.
  commit:    {sha} {subject}
  deployed:  {yes — ancestor of live {sha} | merged, not deployed | unknown}
  delta:     {no capability delta remains | N residual item(s): …}
  verdict:   {ALREADY SHIPPED | PRIOR PASS + RESIDUAL DELTAS | MATCHES, NO PROVENANCE}
```

Rules:

- **SURFACE, never GATE — and this one especially.** It does not halt, refuse, or skip a step, *including* on the ALREADY-SHIPPED verdict. A re-run to verify residual deltas is legitimate and productive: the run that motivated this section found a real one that way (a missing identifier row in an otherwise-complete 9-frame surface — cash-recovery PR #525). **The failure mode to avoid is blocking a legitimate verification re-run, not permitting one.** An owner who re-pastes and says "check it anyway" gets a full pass.
- **A capability delta is NOT a treatment delta — an all-empty §3 does not mean the grid would be all-green.** §3 compares *capabilities*; the grid compares *pixels*, plus copy and frame chrome the grid is itself blind to. So the ALREADY-SHIPPED verdict must never be phrased as "the implementation matches the design" — only as "the design's capabilities are all present." Recommending an exit is a **cost** judgement (a full grid to confirm a shipped surface is expensive), never a correctness claim.
- **The verdict changes the REPORT's framing, and that is most of its value.** On either provenance verdict, step-04 §9 must open by saying the design was already applied — naming the commit and its deployed state — and describe this run as a *verification / residual-delta* pass. A report that says "all N rows applied" over an already-shipped surface reads as *this run did the work*, which is the more misleading of the two failure modes: no wrong output, but a false claim of authorship.
- **Never let this become a reason to skip §4 / §4c.** The DROP halt and the fixture-to-prod checkpoint are about *intent and authorization*, and both remain live regardless of what was shipped before. In particular a prior pass does not authorize a fixture-to-prod ship.
- **Do not spend a new artifact on it.** Signals A and B are git plus a list §3 already computed. If it ever needs more than that, it is doing too much.

### 4. Branch on the DROPPED set (regression → halt for intent)

**If `{dropped_capabilities}` is empty:**
Record one line — "Regression surface: none — the handoff retains every production capability." Do **NOT** infer a strategy from this alone: an empty DROP set means nothing is being *removed*, it says nothing about what is being *built*. Proceed to §4b to settle the uplift surface and the strategy. No halt.

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

### 4b. Settle the UPLIFT set (net-new → build plan, NOT a halt)

This runs whether or not §4 halted — the drop and uplift axes are independent. Building what the handoff draws is the unambiguous job (no intent to infer, so **no halt**), but the uplift must be NAMED and turned into a build plan, never silently flattened into "treatment alignment."

**If `{uplift_capabilities}` is empty:** Record "Uplift surface: none — the handoff adds no capability the live page lacks." Combined with an empty `{dropped_capabilities}`, this is the *only* state in which `restyle-only` is licensed. Continue.

**If `{uplift_capabilities}` is non-empty → state it plainly and set a build strategy.** Do not present a menu — this is not a keep/drop intent decision, it is the spec. Announce:

```
Capability delta — this handoff is an UPLIFT: it adds/deepens {N} capabilit(y/ies) the live page does NOT have today.
The bulk of this implementation is BUILDING these, not restyling. Net-new structure, not token alignment:

  ADDED (net-new — no production equivalent):
  1. {capability} ({class}) — {what it is / what it does}.        design: {evidence}
  …
  DEEPENED (exists, but the handoff is materially more capable):
  1. {capability} ({class}) — {prod form} → {handoff form}.       prod: {prod_evidence} → design: {evidence}
  …

Strategy: additive — apply the handoff's full composition; every ADDED/DEEPENED item is a build task carried into
the grid (step-03) and the apply (step-04), protected from being scored as a mere treatment delta or "MISSING component" note.
```

Rules for the uplift report:

- **Never let a non-empty uplift resolve to `restyle-only`.** A redesign that adds a band / lane segmentation / action column / drawer is a build job; `restyle-only` would ship the old structure with new paint and silently drop the redesign's entire point. The minimum strategy for a non-empty uplift is `additive`.
- **A DEEPENED capability is a build task, not a treatment row.** Carry each into `{uplift_capabilities}` so step-03 §2h tags its net-new sub-structure `capability-build` (not collapsed to "MISSING component → restyle"), and step-04 constructs it. The treatment of the *shared* shell still flows through the grid normally; the *new sub-structure* does not.
- **Autonomous mode BUILDS the uplift — it does not skip it.** Adding capability the design specifies is the decision-autonomy lane (implement what was handed off), unlike dropping a capability (intent, out of scope). In autonomous mode, default to `additive`, build every ADDED/DEEPENED item, and disclose (`autonomous: built {N} net-new/deepened capabilities per the handoff`). Never default an uplift to `restyle-only`.

### 4c. Fixture-to-prod permission checkpoint (authorization, not disclosure)

Independent of the drop/uplift axes — this catches the OTHER silent default. design-implement faithfully transcribes whatever the handoff specifies; when the surface being built has **no live read path**, the unflagged default is to wire it to a fixture/mock module and ship it, so mock data reaches a production route as an unremarked side-effect of "just implementing the design." Whether shipping a fixture-backed surface to prod is acceptable is **authorization** — the owner's call — NOT something faithful transcription gets to decide.

**Fires when BOTH hold:**

1. The surface being applied is — or will be — **fixture-backed**: its data render reaches a module the project marks as mock (commonly a module exporting `DATA_STATE = "fixture"`, or the project's documented mock-data marker) with **no live read-model / DB path**. For a *redesign*, step-02 already mapped this (`{impl_page}`'s data source); for a *new surface*, it is the build decision you are about to make because no live reader exists yet (the brief's data / API-surface section usually flags this — "read model partial / not served today / OPEN QUESTION").
2. The **target is a production route** — a real shipped app route, not a storybook / preview / sandbox / disabled route.

**If it does NOT fire** (a live read path exists, or the target is not a prod route): record one line — "Fixture-to-prod: n/a — {live read path | non-prod target}." Proceed.

**If it fires → HALT advisory BEFORE the apply pipeline. Do NOT proceed to the grid/apply until the owner confirms.** Be advisory, not interrogative — state the situation + your recommendation, ready to execute on confirm:

```
Fixture-to-prod checkpoint — this surface would ship to a PRODUCTION route ({route}) backed by MOCK data, not a live read model.
  Data source: {the fixture/mock module} — no live read path today ({why: reader unwired / Epic N / OPEN QUESTION}).
Shipping a disclosed fixture to prod is a conscious authorization, not a default of implementing the design.

Recommended: {if a live reader exists → wire it (then this surface is NOT fixture-backed); ELSE ship disclosed-fixture
ONLY IF the project's disclosure floor is honored — the mock module self-declares (the DATA_STATE / mock marker), the
surface renders the always-visible fixture banner, and (where the project enforces it) the disclosure CI gate is green —
AND it is not the default landing of its route}.
I'll {proceed with the disclosed fixture | wire the live reader | hold} on your go.
```

Rules:

- **This is the AWARENESS / authorization tier — PROBABILISTIC (a halt the agent must honor), NOT a deterministic block.** The deterministic companion is the project's DISCLOSURE floor (the mock-data marker + the always-visible fixture banner, enforced by the project's fixture-disclosure CI gate where one exists): that guarantees a shipped fixture is *labelled*. §4c guarantees the *decision to ship one* is *conscious*. **Disclosure ≠ authorization — both are required**; do not treat a green disclosure gate as permission to ship unasked.
- **Autonomous mode does NOT auto-proceed past this** — same posture as the synthesize-bundle refusals (`dev_no_render` / `needs_human_review`) and the §4 drop halt. Shipping mock data to a prod route is intent/authorization, outside decision autonomy. Disclose and hold.
- **Generalize — do not hardcode any one project.** The trigger is the project's mock-data convention (`DATA_STATE = "fixture"` is the common marker) + a production route; the disclosure floor's exact mechanism (banner component, marker comment, CI gate) belongs to the consuming project — name it where known, never assume it is identical across the 13.
- **Forced-and-honest is fine; silent is not.** A disclosed fixture shipped after explicit confirmation, behind the disclosure floor and off the default landing, is a legitimate "designed-on-fixtures, awaits its wiring epic" surface. The prohibited move is wiring mock data into a prod route as an unremarked default and declaring the run done.

### 4d. PERSIST the halt verdict before halting (§4 or §4c) — the report must outlive the session

**A halt at §4 or §4c is the most expensive verdict this workflow produces, and until now it evaporated with the session.** The regression report was presented in chat and nowhere else — so the next session, handed the SAME Claude Design prompt (the "Send to local coding agent" panel emits a *stable* prompt per file, and any `design-handoff-detect` hook routes every paste straight back here), re-derived the identical halt from zero after a full ingest + map. The verdict already existed; nothing could find it.

**So: whenever §4 or §4c halts, WRITE THE REPORT TO DISK FIRST, then halt.** Write before you present, not after — the durable artifact must land before the session can end or compact, the same discipline the apply ledger uses.

Path: `{implementation_artifacts}/design-implement-preflight-{target_slug}-{date}.md`.

Frontmatter — these fields are what Input Resolution's **Prior-halt recall** matches and displays, so emit them even when a value is unknown (write `unknown`, never omit silently):

```yaml
---
type: design-implement-preflight
workflow: design-implement (step-02b capability-delta preflight)
target_slug: {target_slug}
route: {the impl route}
design_source: {design_url | bundle_dir | ingest_manifest_path}   # the matching key — verbatim
design_file: {design_file}
brief: {matched brief filename + brief_status, or "none"}
handoff_supersede_status: {handoff_supersede_status}
baseline_commit: {baseline_commit}                                 # the still-valid? signal reads from here
outcome: HALTED at step-02b — {which gate(s): §4 capability drop | §4c fixture-to-prod}
blocked_on: {ONE line naming the real blocker — e.g. "read model: 11 of 18 handoff capabilities have no live read path"}
blocking_paths: [{the files/modules that must change for the blocker to clear}]
date: {date}
session: {session id}
---
```

Body: the full report you were about to present — the ingest summary, `{production_capabilities}`, `{handoff_capabilities}`, the both-way delta with the per-capability KEEP / SAFE-TO-DROP verdicts and reasons, `{frame_composition_deltas}`, the computed scope verdict, and the recommended unblock plan. **Write the report you would have shown, not a summary of it** — a next session reading this must be able to skip the ingest entirely, which it cannot do from a précis.

Rules:

- **`blocked_on` and `blocking_paths` are the two fields that make this worth reading.** `blocking_paths` is what the recall check runs `git log <baseline_commit>..origin/main --` against to tell the next session whether the blocker has moved. A halt recorded without them is still useful prose but yields no staleness signal — name them concretely (the read-model module, the schema file, the projection), never "various".
- **Persist on EVERY halting exit, including an owner-confirmed one.** If the owner then says "proceed anyway", record that resolution in the artifact rather than deleting it — the next session needs to know the halt happened *and* how it was settled.
- **This is a REPORT, not yet a contract.** The recall check reads it opportunistically and treats a missing, malformed, or unparseable artifact as a silent no-op. Whether it should become a machine-consumed contract with an enforced schema (and whether the recall check should ever GATE on it) is an **open owner decision** — do not tighten it here.
- **Never overwrite another day's artifact.** The filename carries `{date}`; a second halt on the same slug the same day appends a new record rather than replacing the file (same append-only discipline as the ingest manifest).

### 5. Record the approved plan

- `{implementation_strategy}` ∈ `restyle-only | additive | partial | replacement` — resolved from BOTH axes: `restyle-only` ONLY when DROPPED **and** `{uplift_capabilities}` are empty; `additive` whenever the uplift is non-empty (new structure built, dropped capabilities retained); `partial` / `replacement` as the §4 drop-disposition resolved. A non-empty uplift can never resolve below `additive`.
- `{capability_dispositions}` — the per-capability `keep | drop` map. For `partial` this is **the advised mix you proposed** (AI-authored, user-confirmed), NOT a list the user assembled; for the others it is derived (restyle-only/additive ⇒ all `keep`; replacement ⇒ all `drop`). If the user adjusted the recommendation, record the adjusted map.

**Autonomous mode does NOT override this.** A capability-drop decision is *intent*, outside decision autonomy (see autonomy scoping). In autonomous mode, default to the **non-destructive** strategy — `restyle-only` (keep every capability) — and disclose loudly in the run output (`autonomous: kept all {N} dropped capabilities — confirm if replacement was intended`). Autonomous mode never silently drops a production capability.

### 6. How the choice constrains step-03 / step-04

- For every capability marked **keep** (`restyle-only`, `additive`, kept rows of `partial`): the apply must **preserve** it. Its render sites / actions / lookup drawers are **protected** — the redesign's treatment is applied *around* them; they are not deleted just because the handoff frame omits them. A grid row that would remove a kept capability is re-classified `deferred(capability-protected)` with the reason, never silently applied.
- For every capability marked **drop** (`replacement`, dropped rows of `partial`): the handoff governs; the capability is removed — AND step-04 §9's "Capabilities removed (orphaned actions)" check runs over exactly these, confirming the removal is clean (no orphaned action, no half-loss) and disclosing it in the completion report.
- For every capability in **`{uplift_capabilities}`** (ADDED / DEEPENED): it is a **BUILD task**. Step-03 §2h tags it `capability-build` so its net-new structure is NOT scored as a treatment delta or a stray "MISSING component" note; step-04 constructs it and the §9 report enumerates each built capability (`built: {capability}`) alongside the kept/dropped lists. An uplift item that ships unbuilt is a step-04 failure, the exact mirror of a kept capability that ships removed.
- Carry `{implementation_strategy}` + `{capability_dispositions}` + `{uplift_capabilities}` into step-03 (the grid notes protected capabilities AND build tasks) and step-04 (the apply ledger honors keep/drop/build and the §9 report states the chosen strategy + every kept/dropped/built capability).

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-03-build-grid.md`

## SUCCESS METRICS

- `{production_capabilities}` and `{handoff_capabilities}` inventoried at the feature level (routing, §13 lookups, economics, status/header, activity/audit, actions) — not CSS.
- The delta is computed **both ways**: `{dropped_capabilities}` (regression), `{added_capabilities}` + `{deepened_capabilities}` → `{uplift_capabilities}` (net-new build). An undrawn-but-promised handoff frame (brief §7 / `{design_frame_inventory}`) is NOT mis-scored as dropped; a thinner production form replaced by a richer handoff form IS scored DEEPENED (not "same component, restyle").
- The scope verdict was computed from the three lists, NOT asserted before them. `restyle-only` was licensed ONLY when DROPPED and uplift were both empty; "production is a structural superset" was asserted ONLY after confirming the uplift is empty. No "just tokens / superset / no net-new" conclusion was drawn from treatment evidence or while the map was still resolving (running-blind gate).
- If the dropped set is non-empty, the run **halted** with the regression report + strategy menu and recorded `{implementation_strategy}` + `{capability_dispositions}` — it did NOT proceed to the grid on an unconfirmed replacement.
- If the uplift set is non-empty, the run **named it** (ADDED / DEEPENED), set strategy to at least `additive`, and carried `{uplift_capabilities}` to step-03/04 as build tasks — it did NOT flatten the uplift into "treatment alignment."
- Kept capabilities are marked protected for step-03/04; dropped capabilities are routed to the step-04 §9 orphaned-action confirmation; uplift capabilities are routed to step-03 §2h / step-04 as `capability-build`.
- **Any halting exit (§4 or §4c) PERSISTED its verdict to `{implementation_artifacts}/design-implement-preflight-{target_slug}-{date}.md` BEFORE halting (§4d)** — full report in the body, and frontmatter carrying `design_source`, `baseline_commit`, `outcome`, `blocked_on` and `blocking_paths` so Input Resolution's Prior-halt recall can match it and compute whether the blocker has moved. A halt presented only in chat is a **failed** exit: the next identical paste re-derives it from zero after a full ingest.
- The **fixture-to-prod permission checkpoint (§4c)** ran: when the surface would ship to a production route backed by a mock module (`DATA_STATE = "fixture"` / the project's mock marker) with no live read path, the run **halted** for explicit owner authorization and did NOT auto-proceed (autonomous mode included) — disclosure (the fixture banner + the project's CI gate) is not treated as permission; otherwise it recorded `Fixture-to-prod: n/a`.

## FAILURE MODES

- **Running blind — concluding scope from treatment evidence.** Emitting "just token alignment / production is a structural superset / no net-new capability" from a clean token mapping (raw-hex → canonical-token debt) — *especially before the map finished resolving production*. The scope verdict is an OUTPUT of the §3 bidirectional delta, never a prior. This is the exact failure that read the inbound-flow supply-orders uplift (lane segmentation + analytics/disposition band + action column + co-views — all net-new) as a reskin.
- **Treating an empty DROP set as "nothing to build."** An uplift redesign drops nothing yet is mostly net-new construction. "Nothing to remove" is not "nothing to add" — §4 must hand off to §4b, never short-circuit to `restyle-only`/`additive-means-equivalent`.
- **Letting a DEEPENED capability flow through the grid as a treatment delta.** A country-filter that became handler-lane segmentation, or a flat status column that became a disposition band, is a build task — the grid (CSS-only) will green the shared shell and at most flag the new sub-components `MISSING`, while the agent reads the parent as "restyle." Score it DEEPENED and route it to `capability-build`.
- **Reproducing the handoff's omission as fact.** Treating "the new design doesn't show the cost-recon / the activity timeline / the linked records" as "remove them" without asking. The redesign is a proposal; the drop is an intent decision that belongs to the user.
- **Offloading the keep/drop analysis to the user.** Presenting a bare strategy menu and asking "which of these do you want to keep?" is the failure §4 exists to prevent. You read the page and the handoff — so YOU advise, per capability, with reasons, and propose a single plan to approve. Make the user assemble the list and you've handed back the work that was yours to do.
- **Skipping the halt because the grid looked clean.** The component sweep greens out on a redesign that drops a whole capability (its inner primitives exist elsewhere) — exactly why this preflight runs before the grid, not after.
- **Mis-scoring an undrawn-but-promised frame as dropped.** A §13 lookup the brief §7 / frame inventory promises but the static bundle didn't render is present-in-intent, not a regression — check the contract before flagging.
- **Letting autonomous mode pick `replacement`.** Intent autonomy is out of scope; autonomous defaults to keep-all and discloses. (Conversely, autonomous mode BUILDS the uplift — implementing what the handoff drew is decision autonomy, not intent.)
- **Inventorying treatment instead of capability.** "The button is a different colour" is a grid delta (step-03), not a capability. This step is about what the page *does*, not how it looks.
