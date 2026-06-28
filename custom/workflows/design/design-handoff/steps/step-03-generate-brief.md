---
name: 'step-03-generate-brief'
description: 'Generate a bias-free Claude Design brief — domain data in entity-table form, visual direction as theme not layout, design ask as open questions'
---

# Step 3: Generate Design Brief

**Goal:** Write the final brief to disk. The brief gives Claude Design the business problem, domain data, visual direction, and hard constraints — nothing about the current page structure. It is a creative brief, not a reconstruction spec.

---

## RULES

1. **Self-contained.** Claude Design must be able to start without clarifying questions.
2. **No current UI.** No layout descriptions, component names, section headings, tab lists, or grouping structures from the existing page — in any section.
3. **Section 2 = domain-entity tables** walked up from the DB schema. Not a TypeScript interface. Not the page server's return type. No derived fields, rendering hints, grouped collections, or UI-control enums.
4. **Section 4 = visual direction as theme.** Describe the desired aesthetic and constraints, not the current UI structure. Reference products and visual anchors should come from the project's design policy (variant A) or, if absent, be omitted in favor of principles (variant C). Do not invent reference products.
5. **Section 6 = questions and outcomes.** Frame user problems the design must solve. Never prescribe UI primitives ("must group by X", "must contain a Y picker").
6. **Reconstructability test.** Read the finished brief. If a developer could rebuild the current page from it, it's leaking.
7. **Verbatim policy copy — no editorializing.** When the template directs you to "Copy section X from brand identity", reproduce the source text **byte-for-byte** within the quoted block. You may add the explicit attribution line ("From `{brand_identity_path}` §X:") preceding the block, and you may add a clearly-outside-the-quote sentence afterward that applies the rule to the current feature. You may NOT insert parentheticals into the rule itself, soften/narrow/broaden it, carve out exceptions the source does not contain, combine multiple policy bullets in a way that elides one, or substitute your own wording because it reads better. The policy's wording is the contract. If the policy needs a change, surface that to the user as a `modify-design-policy` candidate and write the brief against the **current** policy. See workflow.md "Source-of-Truth Precedence".
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

---

## AVAILABLE STATE

From steps 01–02:
- `{github_repo_url}`, `{feature_name}`, `{feature_scope}`, `{feature_purpose}`
- `{data_shape}`, `{api_surface}`, `{implementation_files}`, `{user_context}`
- `{linked_records_inventory}` — foreign-record references the surface displays (§3a); empty for a true leaf surface
- `{design_system}`, `{brand_identity}`, `{brand_identity_path}`
- `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, `{hard_failures}`, `{constraints}`
- `{page_mode}`, `{has_analytics_band}`
- `{handoff_mode}` — `"fresh-design"` or `"refine-screen"`
- If refine-screen: `{review_artifact_path}`, `{refine_focus}`, `{required_variants}`, `{peer_steals}`, `{already_fine}`

---

## EXECUTION SEQUENCE

### 1. Determine Output Path

**Resolve `{project-root}` to the current working tree.** Per `shared/worktree-portability.md` §1, `{project-root}` is the output of `git rev-parse --show-toplevel` from the session's current working directory — the worktree root when inside a worktree, the main checkout root otherwise. Do NOT use a cached resolution from earlier session state or an absolute path from `{main_config}` that points outside the current tree.

```
{project-root}            = $(git rev-parse --show-toplevel)
{implementation_artifacts} = {project-root}/_bmad-output/implementation-artifacts/
{output_path}             = {implementation_artifacts}/design-brief-{feature-slug}-{date}.md
{output_path_relative_to_repo_root} = path relative to {project-root}
```

If `{handoff_mode}` = `"refine-screen"`, use the slug `refine-{feature-slug}` instead of `{feature-slug}` so the refinement brief is visually distinct from any fresh-design brief on the same feature:

```
{output_path} = {implementation_artifacts}/design-brief-refine-{feature-slug}-{date}.md
```

Capture `{output_filename}` = basename of `{output_path}` (used in §1a and the frontmatter below). Capture `{target_slug}` = the kebab-case slug component of the filename — i.e., `{feature-slug}` for fresh-design or `refine-{feature-slug}` for refine-screen. `{target_slug}` names the FILE; it is **no longer the active-uniqueness key** (see §1a — uniqueness is now keyed on **surface identity**, route-normalised, because two differently-named slugs can target one surface — the slug-EXACT collision class in `docs/fork-gaps.md`).

Also resolve this brief's **surface identity** = `({normalised_route}, {surface_part})`, evaluated within `{handoff_mode}`:
- `{normalised_route}` = `{route}` lower-cased with any trailing `/` stripped (dynamic segments like `[id]` left verbatim).
- `{surface_part}` = the value already decided by `step-01c-topology.md` §5d-i (the topology-time sub-surface decision): the kebab name of the tab/section/panel when the handoff target is a sub-surface inside a page (e.g. a `raw-records` tab on the ingestion-run view → `route` = the parent page's route, `surface_part: raw-records`), else `""`. **Do not re-infer it here** — topology owns this decision; consume the variable. (A §13 expand-in-context lookup drawer is NOT a surface — it was redirected to its parent brief in `step-01-gather` §2a and carries no `surface_part`.)

Two briefs are the **same surface** iff they share `{normalised_route}` AND `{surface_part}` AND `{handoff_mode}` — fresh-design and refine-screen briefs on one route are deliberately distinct (the `refine-` slug rule above keeps them apart).

**Worktree refusal.** Before writing, verify `{output_path}` is a descendant of `{project-root}`. If not, halt with the diagnostic in `shared/worktree-portability.md` §4 — this catches the case where a stale absolute path leaked into state from an earlier session and would have caused the brief to land in the main checkout instead of the worktree.

**Bind every read AND every write to THIS tree — not just the computed `{output_path}` var.** The refusal above guards the variable, but an absolute path bypasses it. If you read the predecessor brief or `docs/design-policy.md` by an absolute main-checkout path (e.g. `/Users/.../<project>/_bmad-output/...`), the natural next move is to Write/Edit back against that same absolute path — landing the new brief, the rationale, AND the §1b superseded-flip edits in the **MAIN checkout** instead of this worktree. The split is silent: the artifacts dir is gitignored-but-force-tracked, so nothing surfaces until `git add` no-ops at delivery. Rule: resolve `repo = $(git rev-parse --show-toplevel)` of the CURRENT cwd once, and make EVERY predecessor/policy read and EVERY artifact write `{project-root}`-relative against that `repo`. If you have already read a predecessor by an absolute path, still write the new brief and the §1b flip into `{repo}/_bmad-output/...` — never the path you read from. (step-04 §3 carries a deterministic pre-stage guard that HALTS if this is violated.)

### 1a. Resolve Predecessor & Decide change_class

Per `shared/brief-revision-policy.md` §4, `design-handoff` must decide each new brief's `change_class` by checking for an existing **active** brief on the **same surface** — keyed on the surface identity captured in §1 (`normalise(route)` + `surface_part`, within `mode`), **not** on the filename slug, because two differently-named slugs can target one surface (the slug-EXACT collision logged in `docs/fork-gaps.md`).

Scan **every** brief, not just same-slug files:

```bash
ls -t {implementation_artifacts}/design-brief-*.md 2>/dev/null
```

For each candidate, parse its frontmatter and keep only those where `brief_status: active`. Compute each kept brief's surface identity (`normalise(route)`, `surface_part` — absent ⇒ `""`) and `mode`, and keep only those whose identity **matches THIS brief's surface identity within the same `mode`** (same `normalised_route` AND same `surface_part` AND same `mode`). Branch on the count of same-surface actives:

| Count | Resolution |
|---|---|
| 0 | `{change_class}` = `"original"`; `{supersedes_filename}` = `""`; `{predecessor_path}` = none. |
| 1, **same** `target_slug` | `{change_class}` = `"material_revision"`; `{supersedes_filename}` = basename of the predecessor; `{predecessor_path}` = absolute path. (Re-running `design-handoff` on a surface IS material by definition — minor edits don't go through this workflow.) |
| 1, **different** `target_slug` | **HALT.** A different-slug `active` brief already targets this surface — the slug-EXACT collision class (`docs/fork-gaps.md`). Surface its path and tell the user to reconcile **deliberately**: either supersede the existing brief (set its `brief_status: superseded` + `superseded_by`) and re-run, or align the two slugs. Do NOT auto-supersede across slugs — you cannot assume two independently-named briefs carry the same intent. |
| 2+ | **HALT.** The active-uniqueness invariant (`brief-revision-policy.md` §2.6) is already broken. Surface the list of conflicting paths and tell the user to fix the predecessor chain (set `brief_status: superseded` and `superseded_by` on the older briefs) before generating a new brief. Do NOT proceed and do NOT auto-pick a predecessor — the existing inconsistency must be resolved deliberately. |

The old exact-slug glob (`design-brief-{target_slug}-*.md`) is intentionally widened to all briefs: the predecessor is now recognised by **surface**, so a re-run that happens to compute a different slug still finds — and HALTs on — the prior active brief instead of silently forking a second one.

Capture `{source_run_date}` = `{date}` (the workflow's `date` variable; same value used in `last_modified_date`).

### 1b. Flip the Predecessor (only when `change_class == "material_revision"`)

When §1a found exactly one active predecessor, edit that file's frontmatter in-place BEFORE writing the new brief:

- Set `brief_status: superseded`
- Set `superseded_by: {output_filename}`
- Set `last_modified_by: workflow`
- Set `last_modified_date: {date}`

Leave every other field (including `source_workflow`, `source_run_date`, the body, and any prior changelog) untouched. This is the only edit `design-handoff` makes to an existing file.

If the predecessor's frontmatter is missing the provenance block entirely (a pre-policy brief), back-fill the full block at the same time per `brief-revision-policy.md` §7 — `revision_mode: workflow_generated`, `change_class: original`, `source_workflow: design-handoff`, `source_run_date` set to its existing top-level `date:` field if present (else its `last_modified_date`), and then apply the supersede edit above. The point is to leave the predecessor in a consumer-valid state so a later `--allow-superseded` lookup still works.

### 2. Generate the Brief

The brief is rendered from the canonical template at **`../brief-template.md`** (sibling to `steps/`). That file holds the full brief shape — the Block A/B provenance frontmatter and the brief body (§1 Feature Purpose → §2 Domain Data → §2a Linked records → §3 Who Uses This → §4 Visual Direction → §4a Page Mode → §4b Analytics → §4c Surface Topology → §4d Analytic depth → §4e Decision analysis → §5 Hard Constraints → §6 Design Ask → §7 Deliverable Format → §8 Implementation Files → Changelog). It was extracted from this step (2026-06-10) with no behaviour change — same template, verbatim.

To generate the brief:

1. **Read `../brief-template.md` in full.**
2. Substitute every `{variable}` from state, and honour the conditional `{if …}` / `{for …}` blocks: the refine-screen-only Block B fields; §4b only when `{has_analytics_band}`; §4c only when `{surface_topology_verdict}` ≠ `single-page-appropriate`; §4d only when `{has_decision_numbers}`; §4e only when `{is_capital_decision}`; §2a only when `{linked_records_inventory}` is non-empty; §2b (Finance semantics) only when `{is_finance_surface}`; the §4a composition-override block only when `{composition_provenance}` = `recommended-alt`. **§7's Surface Inventory** table renders one row per `{spawned_surfaces}` entry (§5f) — always ≥1 (the primary surface), plus the drilled detail-drawer frame and one lookup-drawer frame per `{linked_records_inventory}` entry; never collapse it to "design the page."
   - **Structural-contract fields (Block B — `design-implement` step-01 §SHARED.1b reads these to diff the bundle PROPOSAL against the brief CONTRACT instead of trusting it):** also emit (a) `frames` = the list of `{spawned_surfaces}` frame-name keys — the machine-readable mirror of the §7 rows, identical ids, never empty; (b) `composition` = the page-mode default key (`operational→worklist` | `analytical→chart-led` | `detail→record-view`) UNLESS `{composition_provenance}` = `recommended-alt`, then the kebab key of the §4a named job-fit composition (`scanner-terminal`, `single-item-stream`, `source-co-present`, …) — a non-default key is the signal that the gate must verify the bundle expresses the JOB LOOP, not a hero card; (c) `shell_role` ONLY when the app has a role/shell distinction (clerk vs owner — read from the app-shell / navigation context gathered in step-01 §4 VARIANT-B / §5d topology, NOT the current page layout): `required_shell` (route-group/layout this surface must render under), `required_chrome` (the chrome it must carry, verbatim), `forbidden_chrome` (chrome from another role that must NOT appear — e.g. owner global nav on a clerk surface). Omit the `shell_role` block entirely for a single-role app — never invent a role distinction that doesn't exist.
   - **Design Contract spine (the `## Design Contract for Claude — compile and obey` block, directly after "For Claude Design"):** this block is a HUMAN-FACING MIRROR of the Block B contract, not a second source of truth — `page_mode`, `composition`, `route`, `frames`, and the shell line carry the SAME values you emitted in Block B above; keep them identical. Additionally derive two short postures and one distilled invariant list:
     - `{mutation_posture}` — from the step-01 §3 mutation-derivation audit: `none (read-only)` when the surface invokes no server action, otherwise the actions it MUST keep (the `{must_support_capabilities}` mutations, verb-form). Never invent a mutation the audit did not find.
     - `{money_posture}` — `none` when no `Money` figure reaches the surface (a non-finance surface, or a counts-only observability surface), otherwise the money figures it carries, each basis-complete per `docs/design-policy.md` §15. Stay honest with `{is_finance_surface}`.
     - `{contract_must_preserve}` — 3–6 LOAD-BEARING domain invariants distilled from §1 / §2 / §2a / §2b / §5, phrased as outcomes NOT layout: e.g. a missing≠0 rule when the surface carries counts; the key-vs-attribute and distinct-signal rules from §2; the finance semantics from §2b; the least-privilege / no-money-or-PII boundary from §3. Each must be something a *correct-looking* design could still get wrong — never a restatement of a frame id or a layout instruction.
     - `{contract_free_to_change}` — optional; 0–3 feature-specific freedoms beyond the universal IA/layout/derivation freedoms already listed in the block. Empty is fine. The spine is ADDITIVE — it does not replace §§1–8; it is the compile-and-obey index into them.
3. Fill Block A/B provenance from §1 / §1a / §1b above and `shared/brief-revision-policy.md` §2 — `change_class` from §1a, `supersedes` from the predecessor lookup, `policy_version_required` from the policy frontmatter resolved in step-01. **Provenance hand:** for a normal (brownfield) run, `revision_mode: workflow_generated`, `last_modified_by: workflow`. **When `{is_greenfield}` (step-01 §1c):** `revision_mode: spec_derived`, `last_modified_by: human` — the brief was derived from specs/policy, not from built code by an automated workflow run (`brief-revision-policy.md` §4 producer rule + invariant 8). Either way `last_modified_date == source_run_date == {date}` and the §1a predecessor/`change_class` logic is identical.
4. Quote policy / brand-identity text **verbatim** — no carve-outs, softenings, or parentheticals the policy lacks (SOURCE-OF-TRUTH PRECEDENCE in workflow.md). The §3 Self-Review below string-matches these against the source.

The section order in the template is intentional — Claude Design should understand the business problem first, then the visual system, then the non-negotiables. Do not reorder.

### 3. Self-Review

Before writing, verify:

- [ ] **Block A (Provenance) is complete and consistent.** All 11 fields from `brief-revision-policy.md` §2 Block A are present. For a brownfield run `revision_mode` is `workflow_generated` and `last_modified_by` is `workflow`; for a greenfield run (`{is_greenfield}`) `revision_mode` is `spec_derived` and `last_modified_by` is `human` (invariants 2 + 8). `last_modified_date == source_run_date == {date}`. If `change_class == "material_revision"`, `supersedes` names an existing file in `{implementation_artifacts}`; if `change_class == "original"`, `supersedes` is empty. `superseded_by` is empty (it's set retroactively on the predecessor in §1b, never on a freshly generated brief).
- [ ] **Block B (Content) is complete for the run mode.** Always-required fields present: `mode`, `page_mode`, `route`. If `mode: refine-screen`, also present: `screen_review_ref` (resolvable path), `targeted_changes` (≥1 entry, each citing a V-ID), `unchanged_regions` (≥1 entry), `deferred_violations` (may be empty list but key present). If a collapse occurred per the design-handoff "Collapse allowance", `collapse_note` is present and names both collapsed V-IDs + the promoted one. If `mode: fresh-design`, the refine-screen-specific fields MUST be absent (not just empty).
- [ ] **Predecessor flipped (if applicable).** When `change_class == "material_revision"`, the predecessor file's frontmatter was edited in §1b: its `brief_status` is now `superseded`, its `superseded_by` is set to this brief's filename, and its `last_modified_date` is `{date}`. Re-read the predecessor to confirm — the active-uniqueness invariant must hold after this run completes.
- [ ] **No current UI anywhere.** The brief does not describe what sections, components, tabs, or groupings currently exist on the page. No phrases like "the current page has", "the left panel shows", "the table is currently placed under", "this section is a card grid." *(Refine-screen exception: section 6 cites the artifact's specific `file:line` references — that's expected, because the artifact IS the diagnostic.)*
- [ ] **Verbatim policy quotes — no drift.** For every section that quotes the brand identity / design policy (section 4 Visual Identity sub-sections, section 5 Hard Failures, AI Fingerprint Sensitivity), re-open `{brand_identity_path}` and string-match each quoted bullet against the source. Specifically check: (a) no parentheticals appear in your bullet that don't appear in the policy bullet, (b) no qualifying phrase ("usually", "primarily", "except when", "the codebase already uses X so …") softens a hard rule, (c) every bullet in the policy's hard-failure list appears in section 5 — none silently dropped, (d) no merged bullets where two policy items collapsed into one. If any bullet fails the match, replace it with the policy text verbatim. **This catches the single most common drift mode — softening a hard rule with a "but in this case …" parenthetical.**
- [ ] **Section 2 is entity tables from the DB schema.** No `interface PageData {...}`, no ```typescript blocks, no nested/grouped collections, no derived fields, no rendering hints, no UI-control enums.
- [ ] **Section 1 goals are outcomes, not UI actions.** No "click X" or "switch the Y tab."
- [ ] **Section 4 describes the desired aesthetic, not the current layout.** Reference products (where named by the project policy) describe a *direction*, not the existing implementation.
- [ ] **Section 6 variant is correct.** If `{handoff_mode}` = "refine-screen", section 6 uses the REFINE variant — fixes from `{refine_focus}`, variants from `{required_variants}`, peer steals from `{peer_steals}`, "do not break" from `{already_fine}`. If `{handoff_mode}` = "fresh-design", section 6 uses the FRESH variant — framing + scope directive + open questions, no diagnostic fixes.
- [ ] **Refine-screen scope is bounded.** The brief addresses exactly 3 fixes (not 4, not 2). It lists at least 2 edge-state variants. It does NOT instruct the designer to redesign the IA, replace components wholesale, or "get radical." If two top-3 violations are mechanical (token/class swaps with no design decision), the workflow.md "Collapse allowance" applies — one combined Vx+Vy entry plus a promoted design-requiring V-ID, with `collapse_note` in frontmatter. Never collapse twice; never collapse a design-requiring violation.
- [ ] **Fresh-design section 6 is questions, not primitives.** No "must group by", "must contain", "must have." Questions emerge from user goals + data shape, not from the current UI's solutions.
- [ ] **Reconstructability test (fresh-design only).** A developer could NOT rebuild the current page from this brief. Does not apply in refine-screen mode — that mode intentionally references the current page.
- [ ] **Design system variant is correct and complete:**
  - branded = full brand identity content (personality, typography, colors, components, spacing, reference pages, hard failures, AI sensitivity)
  - existing = visual direction statement + real tokens + anti-pattern list
  - external = names the system, no repo tokens
- [ ] **Positive before negative** — visual direction and reference products come BEFORE hard failures and anti-patterns.
- [ ] **Page mode is correct.** `{page_mode}` is one of the three contract values (`operational | analytical | detail`) — never a fourth. Section 4a (Page Mode) contains exactly the block for the resolved mode and no other (the operational, analytical, OR detail block). Frontmatter `page_mode` matches the 4a block. A `detail` page is *usually* `band_provenance: none` (a lone record has no aggregate dimension) — but the **analytics-rich detail exception** (a research / monitoring view whose one record carries genuine aggregates — price/rank over time, competitor share, ownership history) DOES carry analytics surfaces, ranked by §5e and specified in §4b.0; do not assert §4b is always absent on `detail`. What a detail page must never carry is a *dashboard* — KPI-card grid, bento, or mini-charts as a stat wall (§5/§7).
- [ ] **Section 4b is correct.** Section 4b (Analytics Structure) is present iff `{has_analytics_band}` is `true` (band_provenance ∈ inherited | recommended-new). When present, all five subsections (A archetype & job, B reading passes, C drill behaviour, D palette & status rules, E prohibited patterns) are filled with feature-specific values — no template placeholders remain. The archetype is named and matches `{analytics_archetype}` from step-01; subsection A grounds it (data dimension + user question); B's reading passes follow that archetype's form rather than a defaulted trend strip; every analytics element named in B or C has a stated drill target in C (no ornamental elements). When `{has_analytics_band}` is `false`, section 4b is omitted entirely. (Analytic *depth* is no longer a §4b subsection — it is the surface-level §4d, checked below.)
- [ ] **Section 4d is correct.** Section 4d (Analytic depth) is present iff `{has_decision_numbers}` is `true` (the surface carries figures the user acts on — verdict / score / ROI / KPI; broader than `{has_analytics_band}`, so it is present on a bandless `detail`/`analytical` decision surface and absent on pure data-entry/passive-review/CRUD). When present, it renders the §5c-2 rigor spec for **every** decision-bearing figure WHEREVER it sits (§4b band values AND §4a record/hero/verdict numbers): a lead read sentence (or explicit "none"), each decision number's uncertainty + base rate (or a named data gap), and the deciding field per chart. No fabricated interval stands in for a data gap (honesty gate). On multi-surface pages there is one §4d block per surface.
- [ ] **Section 4e is correct.** Section 4e (Decision analysis) is present iff `{is_capital_decision}` is `true` (the surface commits a scarce resource under uncertainty with a downside — buy / reorder / sizing; narrower than `{has_decision_numbers}`, so a dashboard/coverage/status surface has NO §4e). When present, it renders the §5c-3 decision spec: a framed bet (stake · horizon · downside), a modelled outcome distribution (P(success)/EV/P10/P90, or an honest `single-scenario` + VOI gap), a sizing read tied to the loss tail (a quantity with a basis, not BUY/PASS), the breakeven driver with its threshold, and the outside-view/regime/asymmetry context. No fabricated outcome distribution stands in for an un-modellable decision (model-honesty gate). When `{is_capital_decision}` is `false`, section 4e is omitted entirely.
- [ ] **band_provenance is honest.** Frontmatter `band_provenance` is set. If `recommended-new` or `recommended-drop`, the recommendation was surfaced to the user for veto (not silently injected/removed). `analytics_archetype` is present in frontmatter iff `{has_analytics_band}` is `true`.
- [ ] **composition_provenance is honest.** Frontmatter `composition_provenance` is set (`policy-default` or `recommended-alt`). If `recommended-alt`: §4a leads with the composition-override block naming the job-fit composition (no template placeholders remain), the override was veto-surfaced to the user (not silently imposed), and `{page_mode}` still honestly names the *work type* (the override changed composition, not mode — the page can be `operational` with a non-table composition). If `policy-default`: no override block appears and §4a is the plain page-mode block. The composition was decided from the §5a job questions, NOT inherited from the policy default or the legacy render.
- [ ] **Must-support capabilities are captured, not dropped.** §1 lists every job from `{must_support_capabilities}` as an outcome (not a UI mechanic), OR the subsection is omitted because the surface genuinely has none beyond the primary goals. A redesign-scope brief especially must not silently shed a capability the current screen has — the blank-canvas mandate strips the *arrangement*, never the *job* (step-01 §4). If a capability could not be expressed without naming current UI, it is still listed as an outcome, not discarded.
- [ ] **Finance semantics captured without leaking layout (finance surfaces only).** When `{is_finance_surface}`, §2b is present and renders `{finance_column_semantics}`, `{finance_exception_expectations}`, `{finance_must_not_infer}`, and `{finance_unresolved_assumptions}`; every item is an outcome / semantic / open question — **none names a bar, card, drawer, or composition** (a layout leak fails this check). Unresolved assumptions (status SoT, valuation basis, block/line semantics) appear as Open Questions and are NOT resolved or guessed anywhere in the brief. The pass's capabilities/surfaces appear via `{must_support_capabilities}` / `{spawned_surfaces}`, not duplicated in §2b. When `{is_finance_surface}` is false, §2b is omitted entirely (no heading).
- [ ] **Ingest / entry-point not dropped.** Cross-check the step-01 ingest audit: for each entity type the feature displays, was the source of new records captured? If a production page-level affordance seeds the pipeline (upload, import, manual-create), it appears as a capability in §1 (outcome, not mechanic) AND as a mutation in §2 API Surface. A brief that enables browsing records but omits their creation path is incomplete — and this gap survives "capabilities not dropped" scans because the capability was never added to `{must_support_capabilities}`, not removed from it.
- [ ] **Every current-surface action is accounted for (mutation-derivation audit).** For a redesign, cross-check step-01 §3's mutation-derivation audit: every server action the current surface's components invoke resolves to EITHER a `{must_support_capabilities}` / primary-goal entry (carried forward) OR a `{dropped_capabilities}` entry with a reason. No action is unaccounted for. This is the audit that catches mutations on *existing* records (resolve / remap / override / re-run / reprice) — the subclass the ingest audit and the recall-based capability list both miss (the EOS batch-detail EAN→ASIN remap loss). When `{dropped_capabilities}` is non-empty, the brief's §1 "Deliberately not carried forward" subsection renders it, and step-03 §5 surfaces it to the user as a vetoable decision.
- [ ] **Surface topology captured.** `{surface_topology_verdict}` is set from step-01 §5d. When not `single-page-appropriate`, §4c is present in the brief and describes the recommended topology correctly — which job each surface owns, whether related routes already exist, and whether a sub-brief is pending. When `single-page-appropriate`, §4c is omitted entirely — no heading, no placeholder text. In non-autonomous mode, the topology recommendation was surfaced to the user before the brief was written.
- [ ] **Section 2a (linked records) is correct.** Section 2a is present iff `{linked_records_inventory}` is non-empty. When present, every entry renders one table row (foreign reference · owning surface+route · **expand-in-context target (§7 drawer, not navigate-away)** · inline lookups), no template placeholders remain, and the §13 form guardrail + expand-in-context review-test are stated. The expand column must describe the foreign record opening in the §7 drawer **over the current surface** (its own fields shown), with "Open full {sibling} →" only as a secondary action — a row that frames the behavior as navigating away to the sibling page is the misinterpretation this check exists to catch. When the inventory is empty (a true leaf surface), section 2a is omitted entirely — no heading, no placeholder. A surface that displays a record another surface owns (ASIN, SKU, order/batch/shipment number, supplier, customs entry, listing) and has NO §2a entry for it is the silent miss this check exists to catch — `design-review-pr` §13/§12 will hard-fail it post-build.
- [ ] **Section 7 Surface Inventory is complete — every spawned frame is a required deliverable.** §7 leads with the Surface Inventory table, one row per `{spawned_surfaces}` entry (§5f): row 1 is the primary surface; a drilled detail-drawer row is present when the §5a composition spawns one (and for `page_mode: detail` the primary surface IS that drawer — no duplicate); one lookup-drawer row per `{linked_records_inventory}` entry. No template placeholders remain. **Richness floor:** no lookup-drawer's "Must contain" is a bare identity stub (code/type/status alone) when the record carries decision fields. **Depth-1:** no lookup drawer inlines the recursive lookup graph. **Money basis-complete:** every "Figures" cell follows `docs/design-policy.md` §15 (VAT + currency basis, GBP frame, no fragment). A brief whose §7 names only the page and omits its drawer frames is the silent miss this check exists to catch — `design-implement` §2f will flag any promised frame the bundle never drew, but the cheaper catch is here, before Claude Design ever runs.
- [ ] **Structural-contract frontmatter is emitted (Block B).** `frames` (machine-readable mirror of the §7 rows — identical ids, never empty), `composition` (the page-mode default key, or the §4a recommended-alt kebab key), and — when the app is multi-role — `shell_role` (`required_shell` / `required_chrome` / `forbidden_chrome`) are present in the frontmatter and consistent with the body (§7 / §4a / the app-shell context). These are exactly what `design-implement` step-01 §SHARED.1b diffs the bundle against — a brief that omits them ships `UNVERIFIED` and the gate cannot bite, so emission is required, not optional (`brief-revision-policy.md` §2 invariant 1a). `shell_role` is omitted (not blank) for a single-role app.
- [ ] **Design Contract spine is present and honest.** The `## Design Contract for Claude — compile and obey` block sits directly after "For Claude Design". Its `page_mode` / `composition` / `route` / `frames` / shell line match Block B exactly (the spine is a mirror, never a divergent second source of truth). `{mutation_posture}` matches the §3 mutation-derivation audit — no invented mutation; `none (read-only)` only when the audit found no server action. `{money_posture}` is honest with `{is_finance_surface}`. `{contract_must_preserve}` lists 3–6 LOAD-BEARING domain invariants (missing≠0, key-vs-attribute, distinct signals, finance semantics, least-privilege) as outcomes — none is a layout instruction or a bare frame restatement. The block cites `design-review-pr` as the enforcement point. A spine that drifts from Block B, fabricates a mutation, or fills MUST-PRESERVE with layout is the miss this check exists to catch.
- [ ] **Detail composition fit was checked (not assumed).** For `page_mode: detail`, `composition_provenance` reflects the §5a interaction-verb question: `policy-default` for data-entry / passive-review surfaces, `recommended-alt` (source-co-present verification layout) when the verb is verification-against-a-source. A verify-against-source detail surface left at `policy-default` is the miss this check exists to catch.
- [ ] **File paths are correct** and relative to repo root.

### 4. Write the Brief

Write the file to `{output_path}`.

### 5. Present to User

Show:
1. Where the file was written
2. A 3-line summary
3. **Dropped-capabilities disclosure (MANDATORY when `{dropped_capabilities}` is non-empty).** If this redesign deliberately drops or relocates any capability the current surface had, you MUST enumerate them here at the end of the run — never let a drop be silent. Emit:

   ```
   ⚠️ Capabilities NOT carried into this brief ({N}) — confirm these should be dropped, or re-run to include them:
     - {capability} — {reason: relocated to <sibling surface> | obsolete | out-of-scope-by-design}
     ...
   ```

   If `{dropped_capabilities}` is empty, state one line: "All capabilities the current surface exposes are carried forward — no drops." This disclosure is the *output* half of the anti-silent-drop contract (the *log* half is `{dropped_capabilities}` + the brief's §1 subsection); the drop must reach the user's eyes at hand-off, not just sit in a state variable.
4. Copy-paste prompt for Claude Design:

> **To hand off to Claude Design:**
>
> "Connect to **{github_repo_url}** and read `{output_path_relative_to_repo_root}` on `main`. This is a design brief for {feature_name}. Design the UI following the brief exactly."
>
> {If external, append: "Apply the {design_system_name} design system — ignore CSS tokens in the repo's style files."}

If `{has_analytics_band}` is `true`, add one line: "An analytics presentation rationale (the reasoning behind the page-mode, band, and archetype choices) will be written alongside this brief and delivered with it." Do NOT inline that reasoning into the brief or this summary — it lives in the rationale artifact.

### 6. Next Step

- **If `{has_analytics_band}` is `true`:** load and follow `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03b-emit-rationale.md` to write the analytics presentation rationale, THEN proceed to step-04.
- **If `{has_analytics_band}` is `false`:** skip step-03b entirely and proceed directly to step-04 (deliver).

---

## SUCCESS METRICS

- Brief written to `{output_path}`
- Claude Design can start without clarifying questions
- **Zero implementation echoes** — no layout, component, section, or tab references from the current page
- **Section 2** is domain-entity tables from the schema — not TS interfaces, not page server shapes
- **Section 4** describes the desired aesthetic (theme, reference products, tokens) — not the current structure
- **Section 6** poses open design problems as questions — not UI-primitive instructions
- **Reconstructability test passes** — the brief constrains the designer to solving the user's problem, not reproducing this specific UI
- Visual identity is complete for the variant (branded/existing/external)
- Positive anchors precede negative constraints
- **Analytics structure (section 4b) is filled when an analytics band exists** — the archetype is named and grounded (data dimension + user question), reading passes are derived from that archetype's form (not a defaulted trend strip), every interactive element has a defined drill target, palette rules and prohibited patterns are explicit. The designer cannot improvise the analytics layer.
- **Linked records carry the §13 mandate into the brief (section 2a)** — every on-screen value that IS a record another surface owns is captured with a named **expand-in-context target** (the foreign record opens in the §7 drawer over the current surface, its own fields shown — not a navigate-away to the sibling page), not left for the designer to rediscover from a layout the brief withholds. A shared-data surface is never handed off silent on §13; inert duplicated text for a foreign record — and a link that merely navigates away — are `design-review-pr` hard failures, so the brief names the expand-in-context behavior up front.
- **Band presence is a judgment, not an inheritance** — `band_provenance` is set; a `recommended-new` band reflects data + job (not the legacy render) and was veto-surfaced to the user. A bare-table feature whose job is pattern/coverage/ranking work is NOT silently shipped without a band.
