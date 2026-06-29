---
name: 'step-04-apply-and-deliver'
description: 'Apply all deltas from the comparison grid to the implementation, run build, commit, push, create PR, and merge. Deploy is delegated to the BMAD deploy contract (see shared/deployment-to-prod.md) and is not part of this workflow.'
---

# Step 4: Apply and Deliver

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Fix EVERY delta from Step 3's grid — Tier 1, Tier 2, and Tier 3. No "good enough."
- **Apply is GRID-DRIVEN, never holistic.** Every fix traces to a specific `{comparison_grid}` row. "Rebuild the page until it looks like the design" is FORBIDDEN — it is the exact shortcut that silently drops enumerated deltas: it satisfies "looks right" at composition scale while leaving individual grid rows (a sender clause, a kbd hint, a sort control, a secondary label) unapplied. Walk the grid row by row; do not eyeball the whole.
- **Every grid row ends this step with an explicit disposition: `applied` | `deferred(reason)` | `dropped(reason)`.** A row left with no disposition means the run is INCOMPLETE — you cannot declare done. `deferred`/`dropped` are legitimate (needs server data the load doesn't provide, genuinely out of scope, a judgment call) — but only when *named with a reason*, never by omission. This is the apply ledger (§5).
- **The completion report MUST enumerate every non-applied delta with its reason (§9).** Zero non-applied deltas is stated explicitly ("all N deltas applied"); it is never left implicit. Silent partial implementation — shipping a count like "47/47" while the grid under-enumerated, or applying most rows and never listing the skipped ones — is the precise failure this step exists to prevent (accounting-tools /queries #900: 6 detail deltas dropped, caught only by user review, fixed in #903).
- After applying fixes, re-verify by re-reading the modified files. Do not trust that the edit was correct without checking.
- **On an `ingest_manifest` run, the apply is RESUMABLE and CHECKPOINTED — proceed frame by frame, persist each frame's dispositions back into the manifest the moment it is done, and STOP at a frame boundary before the context budget is at risk** (workflow.md Critical Rule "Resumable apply on an ingest manifest"). Pre-dispose rows from `{resume_prior_dispositions}` that are already `✓ applied` (carry as `✓ applied (prior pass)` — do not re-apply) and, if `{frame_scope}` is set, rows outside it (`⊘ deferred(out-of-scope: not in {frame_scope})`). Walk only the remaining UNVERIFIED in-scope rows. A checkpointed pass is a CLEAN exit that still delivers the slice it built — it is not a failure and not a wait-for-input halt. URL and bundle runs are unaffected (single-pass as before).
- Follow the project's CLAUDE.md for commit, PR, and merge procedures. Deploy is NOT part of this workflow — see the BMAD deploy contract at `_bmad/bmm/workflows/shared/deployment-to-prod.md` and run `./scripts/bmad-deploy.sh` after merge.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## CONTEXT

From Step 3 you have:
- `{comparison_grid}` — the full delta table with severity tiers
- `{delta_count}` — number of properties to fix
- `{impl_components}` — paths to all implementation files
- `{impl_config}` — Tailwind config and class resolution table
- `{baseline_commit}` — Git SHA before changes

## SEQUENCE OF INSTRUCTIONS

### 1. Plan Fix Strategy

For each delta, determine the correct fix approach:

| Fix Type | When | Example |
|----------|------|---------|
| Tailwind class swap | A Tailwind class maps to the wrong value | `rounded-lg` → `rounded` (when config maps `rounded` to `4px`) |
| Tailwind arbitrary value | No Tailwind class matches the design value | `rounded-[3px]`, `text-[22px]`, `tracking-[-0.015em]` |
| Inline style change | Property is set via `style` attribute | `width="20"` → `width="24"` |
| Grid template edit | Column widths differ | `grid-cols-[28px_1fr_auto]` → `grid-cols-[32px_1fr_auto]` |
| Content text change | Label or sub-text differs | `{count} invoices scored` → `vs previous batch` |
| New component | Design has a component the implementation lacks | Create the component file |
| Capability build | A `capability-build` row (step-03 §2h) — the net-new structure of an ADDED/DEEPENED capability from `{uplift_capabilities}` (a new band, lane segmentation, action column, drawer) | Construct it — wire its data + actions, not just its markup. This is feature work, not a CSS swap; it is `✓ applied (built)` in the ledger, never deferred as "MISSING component, out of scope." |

### 2. Apply Fixes Component by Component

Process one component at a time. For each:

1. Read the current implementation file
2. Apply all fixes for that component
3. Re-read the file to verify the edits landed correctly
4. Check that no adjacent code was broken by the edit

**Order:** Fix Tier 1 (structural) first, then Tier 2 (visual), then Tier 3 (micro). Within a component, apply all tiers together — the ordering is for prioritization if something goes wrong, not for separate passes.

**Sibling-implementation divergence (step-03 §2a Tier-1) is fixed by consolidation, not by patching each copy.** When a primitive has ≥2 implementations that disagree, the fix is to make every render site use ONE implementation (promote a shared component, delete the inline reimplementations), then align that single implementation to the design. Patching each copy toward the design separately leaves the duplication in place and the next edit re-forks it — you would be back here next run. If consolidation is genuinely out of scope for this pass, say so explicitly in the delivery notes and leave the divergence Tier-1-open rather than silently patching one copy.

### 3. Handle Tailwind Config Conflicts

If the design requires a value that conflicts with the project's Tailwind config:

- **Prefer arbitrary values** (`rounded-[4px]`) over changing the Tailwind config
- **Never modify `tailwind.config.js`** unless the user explicitly requested it — the config affects the entire project, not just this page
- If a Tailwind utility class happens to resolve correctly through the existing config, use the class (e.g., `rounded` if it maps to `4px`)

### 4. Run Build Check

```bash
npm run build
```

If the build fails:
1. Read the error output
2. Fix the issue (likely a template nesting error from edits)
3. Re-run `npm run build`
4. If it fails again, diagnose more carefully — read the affected file region

### 5. Apply Ledger — disposition every grid row

Re-read each modified file, then walk the Step-3 grid **row by row** and give EVERY row an explicit disposition. The ledger is the proof the apply was grid-driven, not holistic — a grid with `{delta_count}` rows must end with `{delta_count}` dispositions.

| Disposition | Meaning | Required note |
|---|---|---|
| `✓ applied` | The delta is now fixed in the implementation (re-verified by re-reading the file). | — |
| `⊘ deferred` | Intentionally not applied this pass. | **Reason, one of:** `needs-data` (the page load / server doesn't provide the value — name the field), `out-of-scope` (explicitly outside this run's target), `judgment` (a product decision the implementer made — state it), `content-lane` (a formatter/enum-driven identifier cell from step-03 §2c — its rendered value cannot be verified against a mock-data bundle; routed to design-review / design-tuning on the LIVE page), `foundation-token-drift` (a step-03 §2i Foundation-token row — the app's canonical token VALUE diverges from the design system AND/OR `docs/design-policy.md`'s declared scale; routed to `apply-design-policy-change` for a single-source token migration, NEVER patched in-component and NEVER encoded as a dead `var(--token, <literal>)` fallback), `capability-protected` (the row would remove a production capability the user chose to KEEP at step-02b — `{capability_dispositions}` marks it `keep`; the handoff's treatment is applied around it, the capability is not deleted). |
| `✗ dropped` | Cannot or will not apply at all. | **Reason** — why it's not implementable as specified. |

Every `content-lane` row from step-03 §2c (`{content_unverified_count}` of them) is disposed `⊘ deferred(content-lane)` — its CSS may well have been applied, but its *value-formatting* is explicitly NOT certified here. Do not silently `✓` it; do not drop it. It carries into §9 under "Content-lane verification owed (live page)" with the routing command, so the run hands the content lane off out loud instead of implying the grid covered it.

Rules:
- **A `capability-build` row (step-03 §2h) must be `✓ applied (built)` — never `⊘ deferred(out-of-scope: MISSING component)`.** The step-02b uplift inventory makes the net-new structure in-scope by definition; a `capability-build` row left deferred-as-out-of-scope is the exact "read the uplift as a reskin" failure, just relocated to the ledger. Build it, or carry it as an explicit `✗ dropped` with a named reason the user will see in §9 — never let it lapse silently. An UNBUILT uplift capability surfaces in the §9 "Capabilities built" section as a Tier-1 incompletion.
- **No row without a disposition.** A grid row you neither applied nor explicitly deferred/dropped means the run is incomplete — go back and resolve it. "I didn't get to it" is not a disposition.
- **`deferred`/`dropped` must carry a reason from the table above.** A bare "deferred" is the silent-drop in disguise.
- Write the disposition into the grid artifact next to each row, and update the summary line at the bottom:
  `Applied: {A}/{delta_count} · Deferred: {D} · Dropped: {X}` (A + D + X must equal `{delta_count}`).
- The deferred + dropped rows are carried verbatim into the §9 completion report's mandatory "Deltas not applied" section — they are NOT allowed to live only in the artifact where the user won't see them.

### 5a. Resumable manifest apply — persist-as-you-go + frame-boundary checkpoint

**This sub-section applies ONLY when `{input_kind} == "ingest_manifest"`.** On a URL/bundle run, skip it — there is no durable manifest to checkpoint into, the pass is single-window, and §5 above is the whole ledger.

The manifest's grid scaffold is the durable ledger (workflow.md Critical Rule "Resumable apply on an ingest manifest"). Execute the apply as a sequence of frames, not one undifferentiated walk:

1. **Pre-dispose carried rows (no work).** Rows in `{resume_prior_dispositions}` already `✓ applied` → write `✓ applied (prior pass)`; rows outside `{frame_scope}` (if set) → `⊘ deferred(out-of-scope: not in {frame_scope})`. These are already terminal — do not read their component files.
2. **Apply one frame at a time.** For each in-scope frame with UNVERIFIED rows: apply every section's deltas (the §2–§5 ledger discipline, unchanged), re-verify by re-reading, then **write that frame's dispositions back into the manifest file on disk immediately** (`Edit`/`Write` the scaffold rows from `UNVERIFIED` → `✓ applied` / `⊘ deferred(reason)` / `✗ dropped(reason)`). Durable progress lands at each frame boundary, BEFORE any auto-summarization can drop it — this is the whole point.
3. **Checkpoint decision (after each completed frame).** Ask: can I apply AND re-verify another full frame without my recall of earlier frames' exact values degrading? Soft budget (per the context-budget principle — thresholds, not cliffs): do not attempt more than ~one heavy frame or ~10–12 sections in a pass; checkpoint sooner the moment recall feels lossy. If continuing is safe, take the next frame. If not, **checkpoint**: set `{run_completion_mode} = checkpointed`, stop taking new frames (never mid-frame), and proceed to deliver what you built. Otherwise, when no in-scope UNVERIFIED rows remain, set `{run_completion_mode} = complete`.
4. **A checkpointed pass still delivers.** The frames you DID apply are real code changes — commit → push → PR → merge them in §6/§7 as normal, AND include the updated manifest in the commit (force-add; it lives under gitignored `_bmad-output/`) so the persisted progress travels to main and a fresh session/worktree resumes from it. Then report per §9 with the resume command.

### 5b. Copy & chrome fidelity, then the render-compare done-gate

The apply ledger above dispositions every *grid* row — but the grid has no row for **copy** or for **frame chrome** (workflow.md Critical Rules: the grid is CSS-only). Those are exactly the deltas that ship looking "done": every radius/colour cell matched, so the run felt exhaustive, while the header, breadcrumb, footer, and wording silently drifted via small "I'll improve this" substitutions. Close that gap here, with two passes that are NOT optional.

**1. Transcription pass (copy + chrome).** Walk the design frame's wrapper and its literal text. For each, the impl must reproduce it **verbatim** OR carry a logged deviation — same bar as the grid rows:

- **Frame chrome:** the drawer/page header, the `‹ Back to …` breadcrumb, the footer (its caption AND its cross-link label/target), the close affordance. Substituting a generic shell primitive (e.g. a stock `SheetHeader`) for the design's breadcrumbed header is a deviation, not a free "match the siblings" call.
- **Copy:** every group title, button/link label, sub-caption, and phrasing — e.g. "deferred import" (not "import"), "Open full cost record" (not "Open full order"), "EUR → GBP @ 0.855" (not "€ → £"). A paraphrase, a relabel, or a code↔symbol swap is a deviation.
- Each deviation gets a ledger row — `⊘ deferred(judgment: …)` or `✗ dropped(reason)` — under the SAME forced-and-logged bar as Critical Rules: allowed only when *forced* (e.g. "design links to `Order Cost Reconciliation.html`; no such route exists → linked to `/orders?order=…`"), never as a silent "I'll improve this." These rows flow into the §9 "Deltas not applied" list like any other — no new report section.

**2. Render-compare (the done-gate).** Render the built surface and place it **beside the design render** — the bundle is runnable HTML; a synthesize bundle ships a screenshot; a handoff run has the design image. Step through it top to bottom: header, every group, every figure, the footer. Any visible difference (missing header, changed label, paraphrased copy, off spacing) is a delta — resolve it, or log it per pass 1. **This, not the green grid, is the gate on "done."** (The bundle README's "don't render/screenshot" governs *reading values during ingest*, not verification — render to verify.)

**Fallback ladder when the BUILT surface cannot be rendered in this run** (a recurring case — a prod-only repo with no local dev server, an auth-walled deploy whose creds aren't in-session, or no bootable surface; gap "done-check unreachable on prod-only auth-walled"):

1. **Render the BUNDLE beside the design image (primary fallback, not a skip).** On a `claude_design_url` or `synthesize_bundle` run the *bundle* HTML is always present and runnable — render IT beside the design render and step through it top-to-bottom exactly as above. The bundle is the design made concrete, so this still catches copy / chrome / layout / spacing drift even when the built app can't be booted. Then state plainly in §9 that the *built* surface was verified by the transcription pass + green build + token parity (NOT a live render), and that the bundle render stood in for the built-surface compare.
2. **The built-surface render-compare is then OWED, not skipped** — route it (`verify` skill, or design-review live Chrome once the surface is reachable/auth'd) in the §9 report, exactly as the content-lane and behavior cedes do.

Declaring "done" off the grid alone — no render-compare, no bundle-render fallback, no owed-disclosure — is non-conformant. It is the precise false-green this section exists to stop: the supply-order cost drawer shipped with a generic header, a relabeled footer, and paraphrased copy while every CSS cell matched.

### 6. Commit and Push

Follow the project's CLAUDE.md commit procedures:

```bash
git add {list of modified files}
git commit -m "$(cat <<'EOF'
fix: align data-quality page with Meridian design spec

Resolves {delta_count} design deltas identified by component × property
comparison grid. Key changes: border-radius (tokens.radius → Tailwind
arbitrary values), font sizes, grid column widths, SVG dimensions,
and content text.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

Push and create a PR:

```bash
git push -u origin {branch-name}
gh pr create --title "fix: align {page-name} with Meridian design spec" --body "$(cat <<'EOF'
## Summary
- Resolves {delta_count} design deltas found by exhaustive comparison grid
- Key areas: border-radius, font sizes, grid column widths, icon dimensions
- Comparison grid artifact: {artifact_path}

## Changes
{list of files changed with one-line summary each}

## Test plan
- [ ] Visual comparison against design artifact
- [ ] Build passes (`npm run build`) — diagnostics gate: any new diagnostic (incl. after a merge/worktree teardown) is RED until a re-run in the current checkout proves zero errors; quote the result, never reason it away as "stale" (`shared/diagnostics-gate.md`)
- [ ] No regressions on adjacent pages

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 7. Merge and Deploy

```bash
gh pr merge --squash --admin
```

After merge, the BMAD deploy contract handles deploy: run `./scripts/bmad-deploy.sh` (see `_bmad/bmm/workflows/shared/deployment-to-prod.md`). The contract decides whether to deploy or skip based on the project's `_bmad/bmm/config.yaml` `deploy:` block — this workflow does not.

### 8. Brand Identity Feedback

After successful delivery, check if a brand identity document exists:

```bash
ls {project-root}/_bmad-output/planning-artifacts/brand-identity.md 2>/dev/null
```

If it exists, evaluate:

1. **Reference page candidate:** If this page is now at the same quality level as the brand identity's listed reference pages, suggest adding it.
2. **Token drift:** If any deltas required values outside the brand identity's documented system (e.g., a new color, a new font size, a border radius not in the scale), flag them — the brand identity may need updating.
3. **Component pattern evolution:** If the design introduced a new component pattern (e.g., a new type of card, a new badge variant), suggest adding it to the brand identity's component language section.

Output these as a `**Brand Identity Updates**` section in the completion report. Do NOT modify the brand identity file directly.

### 9. Report Completion

Output — the **"Deltas not applied" section is mandatory and never omitted.** If everything was applied, say so explicitly; if anything was deferred or dropped, every such delta is listed here with its reason (pulled from the §5 apply ledger). The user must be able to see, from the completion report alone and without opening the artifact, exactly what did NOT make it in.

```
{if run_completion_mode == "checkpointed":}
Design implementation CHECKPOINTED — slice delivered, more frames remain.

This pass applied {frames_applied} of {frames_in_scope} in-scope frames and stopped at a
frame boundary to stay inside the context budget (a single pass over the whole manifest would
risk auto-summarization silently dropping rows). Progress is persisted in the manifest. Resume
in a FRESH session — same command, no flags — to continue from here:

  /bmad:bmm:workflows:design-implement {ingest_manifest_path}

Remaining (still UNVERIFIED in the manifest): {comma-separated remaining frame ids}
{else:}
Design implementation complete.
{/if}

Baseline: {baseline_commit}
Implementation strategy (step-02b): {implementation_strategy}
{if dropped_capabilities was non-empty:}
  Regression surface vs production: {N} capabilit(y/ies) the handoff dropped —
  {for each: capability — KEPT (protected) | DROPPED (removed, confirmed clean below)}
{else:}
  Regression surface vs production: none — handoff retained every production capability.
{if uplift_capabilities was non-empty:}
  Uplift surface vs production: {N} net-new/deepened capabilit(y/ies) the handoff added —
  {for each: capability — BUILT (constructed, see "Capabilities built" below) | UNBUILT (Tier-1 failure — must not ship)}
{else:}
  Uplift surface vs production: none — handoff added no capability the live page lacked (a true restyle).
Deltas: applied {A}/{delta_count} · deferred {D} · dropped {X}
PR: {pr_url}
Completion: {completion_disposition} (STD-COMPLETION-001) — {if run_completion_mode == "complete": `pr_merged`} {if run_completion_mode == "checkpointed": `pr_merged` for the delivered slice; remaining frames are agent-resumable via the command above (a budget checkpoint, NOT owner_gated_residue); name owner_gated_residue only for blockers the owner alone can clear (a credential, a prod mutation)}
Deploy: handled by ./scripts/bmad-deploy.sh — run after merge per the BMAD contract

Comparison grid: {artifact_path}

Deltas not applied:
{if D + X == 0:}
  None — all {delta_count} deltas applied.
{else, one bullet per deferred/dropped row:}
  - ⊘ {grid row id / short description} — deferred ({reason}: {detail})
  - ✗ {grid row id / short description} — dropped ({reason})

Frame coverage ({brief §7 Surface Inventory | bundle frame inventory (URL) | manifest}):
{Mandatory whenever step-03 §2f resolved a frame contract from ANY of its three sources — the
 brief §7, OR (raw-URL run, no brief) the bundle's declared `{design_frame_inventory}`, OR the
 manifest. Never omitted. Enumerate EVERY frame in the contract by name (from step-03 §2f).
 "There was no brief" does NOT license skipping this on the URL path: the bundle declares its own
 lookup frames (§2f source 2) — that IS the contract. If NO source yielded a frame set, say so
 and mark the section needs-human-confirmation. "All green" is only legitimate when every frame
 in the contract is accounted for here; a report that declares the run complete without this
 section — when a frame contract exists — is non-conformant, re-emit it. On a no-brief URL run the
 §13 lookup drawers (warehouse / inbound-batch / import-run / accounting-outcome / catalog /
 supply-source) are exactly the frames this section exists to keep from vanishing.}
{Lookup reconciliation (§2f) — state the AUTHORITATIVE denominator first: the detail drawer
 renders `{len(design_linked_record_rows)}` linked-record rows ({comma-separated labels}), so that
 many §13-lookup frames must be accounted for. Every rendered row maps to a Frame-coverage line
 below; a row whose lookup frame the harvest missed is LOOKUP UNDER-ENUMERATED, NOT silently absent.}
{if every contract frame is present (and deep) in both bundle and impl:}
  All {N} contract frames built — {frame_1}, {frame_2}, … present in impl and component-swept.
  §13 lookups: all {len(design_linked_record_rows)} linked-record rows covered & swept for depth.
{else, one bullet per gap:}
  - {frame} — FRAME MISSING in impl (Tier-1: designed-but-unbuilt) → carried in "Deltas not applied" above; this is feature work, not a CSS apply
  - {lookup} — LOOKUP UNDER-ENUMERATED (rendered as a Linked-records row, no harvested frame) → re-trace the bundle for this lookup's frame; if absent, needs human confirmation. This is the "often missed" lookup (e.g. Shipping lane); counted in {frame_uncovered_count}
  - {frame} — PRESENT BUT THIN in impl (Tier-1: drawer opens, interior under-built vs the bundle) → its missing interior rows are in "Deltas not applied" above; "the drawer exists" is not "the drawer matches"
  - {frame} — FRAME NOT DRAWN in bundle (routed, NOT inferred) → /bmad:bmm:workflows:design-handoff (re-render the frame); counted in {frame_uncovered_count}
Frames in contract: {N} · built & swept: {B} · missing-in-impl (Tier-1): {M} · thin-in-impl (Tier-1): {T} · under-enumerated (routed): {U} · not-drawn (routed): {frame_uncovered_count}
Linked-records rows (authoritative §13-lookup denominator): {len(design_linked_record_rows)} · §13-lookup frames accounted: {must be ≥ the row count}

Foundation-token reconciliation owed (token migration):
{Mandatory whenever step-03 §2i emitted any Foundation-token row. Never omitted.}
{if foundation_token_drift_count == 0:}
  None — the app's canonical foundation (type scale / control heights / radii / status colours) agrees with the design system and docs/design-policy.md.
{else, one bullet per drift + the headline caveat:}
  ⚠ {foundation_token_drift_count} foundational token(s) diverge — component type/radius rows were
     compared at the app's foundation scale, which is NOT the design system / policy scale, so their
     green verdicts are NOT proven parity until the tokens are reconciled.
  - {token} — app canonical {app_value} vs design {design_value} / policy {policy_value} ({kind}) →
    route to /bmad:bmm:workflows:apply-design-policy-change (single-source token migration of src/styles/tokens.css)
  {if any dead_fallback_sites:}
  - DEAD-FALLBACK (inert): {site} writes var(--{token}, {literal}) but the global is defined → the
    literal never applies; remove it and reconcile the token, do NOT add more.
  This is NOT fixable in this workflow — patching each component (or adding a var(--token, <literal>)
  fallback) is the #2412 anti-pattern. The fix is one token migration owned by apply-design-policy-change.

Content-lane verification owed (live page):
{if content_unverified_count == 0:}
  None — no formatter/enum-driven identifier cells on this surface.
{else:}
  {content_unverified_count} identifier cell(s) had their CSS aligned but their RENDERED VALUE
  not certified (mock-data bundle cannot exercise the real enum/label variants). Verify on the
  live page before trusting them:
  - {cell} — {identifier_class}, value from {formatter_ref}
  → run:  /bmad:bmm:workflows:design-review   (live Chrome §13(a) check)
     or:  /bmad:bmm:workflows:design-tuning   (step-02 §2b, live screenshots)

Token provenance (non-canonical — resolved but not from the canonical token surface):
{if token_noncanonical_count == 0:}
  None — every design-mapped token resolves from the canonical surface (tokens.css / @theme).
{else:}
  {token_noncanonical_count} shared-semantic token(s) (status / colour / type) resolve ONLY from a
  per-screen stylesheet, not the canonical token surface (docs/design-policy.md §8). The render
  works on this screen, but the token is not a system token — a sibling surface that doesn't load
  that CSS won't reproduce the value (§3/§13 cross-surface drift). Promotion is a token-architecture
  call, NOT gated here:
  - {token} — resolves from {source_file}, not tokens.css / @theme
  → run:  /bmad:bmm:workflows:design-review   (decide promote-to-canonical vs leave; token architecture)
  (This is a disclosure, not a delta — the run did NOT collapse it into "tokens map 1:1.")

Policy-conformance & behavior (ceded — NOT certifiable from a generated bundle-diff):
  Treatment + structure + page-shell were verified against the bundle/policy. These were NOT,
  because the bundle is a Claude-Design-generated proposal that can itself violate the policy:
  - Prohibitions / tone / motion / iconography (docs/design-policy.md "never" list) →
    /bmad:bmm:workflows:design-review   (live audit)  ·  enforced at PR-time by design-review-pr
  - Behavior / interaction wiring (drawer stack, Esc, mutation flow, live-feed, sort/filter) →
    the `verify` skill (drive the live app and exercise it)  ·  or design-review (live Chrome)
  Do not let "implementation complete" imply these were checked here.

Capabilities built (uplift — net-new / deepened structure the handoff added):
{Mandatory whenever step-02b's `{uplift_capabilities}` was non-empty. Enumerate EVERY added/deepened
 capability and confirm it was CONSTRUCTED — the mirror of the "Capabilities removed" disclosure below.
 An uplift item that did not get built is a Tier-1 failure: the run must NOT declare done while a
 capability the handoff specified ships unbuilt. This is the section that stops an uplift redesign from
 being silently delivered as a reskin (the inbound-flow supply-orders miss: lanes + analytics/disposition
 band + action column + co-views, read as "treatment alignment" and never built).}
{if uplift_capabilities was empty:}
  None — handoff added no capability (pure restyle/regression run).
{else, one bullet per added/deepened capability:}
  - {capability} ({ADDED | DEEPENED}) — built at {file(s)} ⇒ {one-line: what the operator can now do}.
  {or, if any was NOT built:}
  - {capability} ({ADDED | DEEPENED}) — ✗ UNBUILT (Tier-1) ⇒ the handoff specified it and it is not in the impl. This run is INCOMPLETE — build it or carry it as an explicit, named deferral, never ship silently as "done."

Capabilities removed (orphaned actions):
{Derive this MECHANICALLY, do not recall it. If the apply DELETED or REPLACED any component
file (a redesign that swaps the surface — not a pure in-place restyle), then for every server
action / mutation those removed files imported or called, grep the post-apply tree for remaining
callers. Any action now with ZERO callers is a capability the redesign dropped — list it.}
{if no components were deleted/replaced, OR every action the removed code called still has a caller:}
  None — no capability lost (no components removed, or every action the removed code called is still wired).
{else, one bullet per now-orphaned action:}
  - {action name} — was called by {deleted file}; now has zero callers ⇒ the {one-line capability, e.g. "manual EAN→ASIN remap"} is no longer reachable in the UI.
  → If the drop is intended, confirm it. If not, it was a silent capability loss — restore the affordance (the backend action is intact) or route it through /bmad:bmm:workflows:design-handoff to redesign the capability deliberately.

Entry point / discoverability (can a user reach the built surface at all?):
{Mandatory whenever this run MOUNTED A NEW ROUTE or built a surface that did not previously exist in
 the app. The grid certifies the frames; it is structurally blind to whether anything LINKS to them —
 a surface the pipeline builds but nothing points at is an UNLINKED ISLAND, reachable only by typing
 the URL. That is how an owner discovers a shipped surface is invisible (the §L recovery-cross-check
 miss: /recovery/cross-check shipped URL-only; the owner had to add the link by hand, #195). Resolve
 the intended entry point from the brief's §7 `entry_point` (the primary frame's "Opens from / trigger")
 if present, else infer from page_mode + route.}
{Decide the SHAPE first — a sub-surface is NOT a nav peer:}
  - a top-level operational / analytical PAGE → a global-nav entry is the right entry point
  - a detail / drawer / record-view / §13 SUB-SURFACE → its entry point is a LINK or ROW-DRILL from its
    named parent surface, NEVER a global-nav peer (that is nav-bloat and misrepresents a sub-surface as a sibling page)
{Verify the affordance actually EXISTS in the impl — a nav <Link>, a link/drill from the parent surface's
 component, or a row onClick that opens this surface. Do not assume it; grep for it.}
{if at least one reachable affordance is present:}
  Reachable — entry point: {global-nav "X" | link from {parent route} | row-drill from {worklist}} (verified present in {file}).
{else:}
  ⚠ UNLINKED ISLAND — surface mounted at {route} but nothing links to it (reachable only by URL).
    Add the entry point now in the correct shape (above), or carry it as an explicit, named deferral —
    never report "complete" while the surface is unreachable. If a full entry-point wiring is a separate
    epic (e.g. the parent worklist is live-data-wired and the drawer-over-parent merge is deferred), a
    quiet link from the parent surface is the minimum bridge and ships in THIS run.
```

A completion report that prints a fixed-count but omits the "Deltas not applied" section is non-conformant — re-emit it. The whole point of this section is that a partial implementation announces itself instead of shipping silently as "done." The **"Frame coverage" section is equally mandatory** whenever step-03 §2f resolved a frame contract from ANY source — the brief §7, the bundle's declared `{design_frame_inventory}` on a raw-URL run, or the manifest — and it is the gate on the most expensive false-green this workflow produces: a grid that ran the component sweep only over the frames that already exist in the impl, matched them, and reported "0 deltas — green" while frames the bundle *did* draw were never built. Two shapes of this miss: (a) the inbound-flow `/orders` run that passed 5 of 9 §7 frames and called it green — 4 designed-but-unbuilt drawers, inbound-batch / import / shipping-lane / comms-case, silently absent; and (b) the **no-brief URL run** where, with no §7 to consult, the §13 lookup drawers (warehouse / inbound-batch / import-run / accounting-outcome / catalog / supply-source — the "link to records (lookups)") fell out entirely because their shared inner primitives matched elsewhere in the impl. "All green" is a claim about the whole frame contract — not about whatever frames the sweep happened to find, and NOT excused by the absence of a brief — so the report must enumerate the whole list and account for every frame as built / missing-in-impl (Tier-1) / not-drawn (routed), or it is non-conformant. The **"Content-lane verification owed" section is equally mandatory** and never omitted: design-implement aligning a marketplace/supplier/ASIN cell's CSS is NOT the same as certifying it renders the right value on real data — that lane belongs to the live-page workflows, and the report must say so rather than let "implementation complete" imply the identifier values were checked. The **"Capabilities removed (orphaned actions)" section is equally mandatory** whenever the apply deleted or replaced components: a redesign that swaps the surface can silently strip a capability whose action call lived in a removed file and was never a grid delta (the EOS batch-detail EAN→ASIN remap — `overrideWholesaleAsinAction` left with zero callers — is the canonical miss). The grid-driven apply ledger cannot catch this because the lost capability was never a row in the grid; the orphaned-action grep is the backstop, and it must reach the report, not stay silent. The **"Entry point / discoverability" section is equally mandatory** whenever the run mounted a new route: the grid certifies the frames but is blind to whether anything LINKS to the surface, so a built surface can ship as an unlinked island reachable only by URL (the §L recovery-cross-check miss — `/recovery/cross-check` shipped URL-only, the owner added the link by hand in #195). The report must state the verified entry point or flag the island, and the entry point's shape obeys the sub-surface rule — a detail/drawer/§13 sub-surface is reached by a link or row-drill from its named parent, never a global-nav peer.

---

## SUCCESS METRICS

- **Every grid row has an explicit disposition** (`applied` / `deferred(reason)` / `dropped(reason)`) — `A + D + X == {delta_count}`, no undisposed rows
- Apply was grid-driven (every fix traces to a row), not a holistic rebuild
- Every applied delta is fixed and re-verified by re-reading the file
- **The completion report's "Deltas not applied" section is present** — enumerating every deferred/dropped delta with its reason, or stating "None — all N applied"
- **The completion report's "Frame coverage" section is present whenever step-03 §2f resolved a frame contract from ANY source** (brief §7, or the bundle's `{design_frame_inventory}` on a raw-URL run, or the manifest) — every contract frame accounted for as built / missing-in-impl (Tier-1) / not-drawn (routed); a "green" report that never enumerated the frame contract is non-conformant, including the no-brief URL run where the §13 lookup drawers are the contract
- **The completion report's "Content-lane verification owed (live page)" section is present** — every `content-lane` deferral (step-03 §2c) enumerated with its formatter ref + the design-review / design-tuning routing, or stating "None"
- **The completion report's "Token provenance (non-canonical)" section is present** — every shared-semantic token that resolved only from a per-screen stylesheet (step-03 §2g) enumerated with its source file + the design-review cede, or stating "None". A run must never report token mapping as "1:1 / matches" while a per-screen-only shared-semantic token is unsurfaced
- **The completion report's "Capabilities built (uplift)" section is present whenever step-02b's `{uplift_capabilities}` was non-empty** — every added/deepened capability enumerated and confirmed BUILT (with its file + what the operator can now do), or any UNBUILT one flagged Tier-1 incomplete. A run that read an uplift redesign as "treatment alignment" and shipped without constructing the net-new surface is non-conformant — this is the mirror of the orphaned-action disclosure.
- **The completion report's "Capabilities removed (orphaned actions)" section is present whenever the apply deleted/replaced components** — derived by grepping for now-zero-caller actions among those the removed files invoked, or stating "None — no capability lost". A surface-swapping redesign never ships without this disclosure.
- **Copy & frame chrome are transcribed verbatim or logged as a forced deviation (§5b)** — every literal string and wrapper element (header / breadcrumb / footer) matches the design, or its deviation is in the ledger with a reason; and the **render-compare done-gate was run** (built surface beside the design render), or explicitly marked owed-and-routed. "Done" is never declared off the green grid alone.
- Build passes; PR created and merged; grid artifact updated with dispositions; no regressions introduced
- **Every drilled frame (detail/create/§13-lookup) has a Frame-composition row (§2d-bis), and every `{frame_composition_deltas}` entry from step-02b became one** — section order + group naming + header/footer chrome compared against the design; a renamed/regrouped/reordered drawer or a black-vs-blue footer button is surfaced Tier-1, never passed because each inner component matched
- **On an `ingest_manifest` run: dispositions were persisted into the manifest frame-by-frame (not only at the end), prior-pass `✓ applied` rows were skipped, and if the pass stopped early it set `{run_completion_mode} = checkpointed` and printed the exact resume command** — a large manifest is never attempted as one undifferentiated single-window pass

## FAILURE MODES

- **Holistic rebuild instead of grid-driven apply** — "make the page look like the design" satisfies composition while silently dropping enumerated rows (band sender clause, kbd hints, a sort control). This is the dominant leak and the reason the apply ledger exists (accounting-tools /queries #900).
- **Reporting a count without the "Deltas not applied" list** — "47/47" or "deltas fixed: X" with no enumeration of what was deferred/dropped. A partial that omits the disclosure ships looking complete. The §9 section is mandatory.
- **Declaring "0 deltas / green" off a sweep of only the frames that already exist in the impl.** The component grid is structurally blind to a whole frame the impl never built — it produces zero rows for an absent frame, so "all matched" reads as "all present." Without the §7 Frame-coverage enumeration (step-03 §2f → the §9 Frame-coverage section), a run greens out having silently skipped every designed-but-unbuilt drawer. This is the inbound-flow `/orders` miss: 9 §7 frames promised, 5 swept and matched, 4 (inbound-batch / import / shipping-lane / comms-case) never built and never surfaced — "green" meant "we only looked at what was already there." The §7 list, not the found-frame set, is the denominator for a green claim. The **no-brief URL variant** is the same leak without a brief to consult: the bundle's own declared frame inventory (`{design_frame_inventory}`, step-01 URL.3a — the §13 lookup drawers Orders.html consumes) is the denominator, and skipping coverage because "there was no brief" lets those lookups vanish exactly as the 4 `/orders` drawers did.
- **A bare `deferred` with no reason** — the silent drop wearing a label. Every deferral names `needs-data` / `out-of-scope` / `judgment` / `content-lane` + detail.
- **Letting "implementation complete" imply the identifier *values* were checked.** design-implement aligns a marketplace/supplier/ASIN cell's CSS against the bundle; it does NOT verify the formatter renders the right value on real data (the bundle is mock data). Omitting the "Content-lane verification owed" section ships that false implication — it is the design-implement counterpart of the inbound-flow `/orders` raw-enum leak that the grid's mock-data comparison could never catch.
- **Collapsing a per-screen-only token into "tokens map ~1:1."** A shared-semantic token (status / colour / type) that resolves only from a per-screen stylesheet is design debt per `docs/design-policy.md` §8, not a clean canonical mapping — and "the bundle was generated from that same CSS" does not launder it (the bundle is a generated proposal, §2e). Declaring 1:1 because the token is "defined somewhere" buries the §3/§13 cross-surface-drift risk. Disclose it (§2g / §9) and cede promotion to design-review; do NOT gate the render on it either — the token works, placement is an architecture call this workflow does not own.
- **Shipping an uplift redesign as a reskin — the net-new capability never built.** The mirror of the orphaned-action miss: step-02b inventoried `{uplift_capabilities}` (a new analytics/disposition band, lane-by-handler segmentation, an action column, a co-view, a drawer), step-03 tagged them `capability-build`, and the apply restyled the existing shell while never constructing them — then declared done off a green-ish grid. The "Capabilities built" §9 disclosure is the backstop: every added/deepened capability must be confirmed built, or flagged Tier-1 incomplete. This is the inbound-flow supply-orders failure that read lanes + the disposition band + the action column as "treatment/token alignment, production is a superset."
- **Deleting/replacing components without the orphaned-action check.** A surface-swapping redesign removes files that called server actions; if the new surface doesn't re-wire one, that capability is silently gone — and because it was never a grid row, the apply ledger can't catch it. The grid-driven apply makes this *more* likely, not less, by focusing attention on enumerated deltas. The orphaned-action grep + the "Capabilities removed" disclosure is the backstop; skipping it is how the EOS batch-detail EAN→ASIN remap shipped as a silent loss.
- **Interpreting where transcription was required — copy & chrome drift.** The grid has no row for a literal string or a wrapper element, so relabeling a footer, paraphrasing a sub-caption, swapping currency codes for symbols, or substituting a stock shell for the design's breadcrumbed header all leave the CSS grid all-green while the surface reads visibly worse than the handoff. Each is a small "I'll improve this" the workflow gives no license for (workflow.md Critical Rules). The grid's CSS-exhaustiveness *manufactures* the false confidence — "every cell matched" feels done. The §5b transcription pass + render-compare done-gate is the backstop; declaring done off the green grid is the leak (the supply-order cost drawer: generic header, relabeled footer, "import" for "deferred import", "€ → £" for "EUR → GBP" — every cell green).
- **A recomposed drawer passing on an all-green component grid (the §2d-bis miss).** Each section's inner pixels match and §2f-bis confirms each section exists, so the grid greens out — while the drawer's *arrangement* is wrong: renamed groups (`Cost & sourcing`→`Economics`), a standalone group folded away (`Lifecycle`→header), a split/merged group (`Related records` + Lifecycle → `Routing & source`), reordered sections, or a footer the design draws black and the impl ships blue. No single component owns the arrangement, so without the Frame-composition row (§2d-bis) "the drawer looks completely different" never becomes a delta. This is the page-shell blind spot (PR #2017) inside a drawer — the inbound-flow supply-order miss. The frame's footer is the sharpest edge: not being a cataloged section, it has no other grid row.
- **Forcing a whole large manifest through one pass (`context-budget-overflow`).** Attempting all frames × all sections in a single window hits the harness auto-summarization boundary, which drops the exact CSS values and per-row dispositions first — so rows get marked `✓ applied` that were never really verified, and the run reads "green." The fix is structural, not vigilance: apply frame-by-frame, persist into the manifest at each frame boundary, and checkpoint (§5a). Not checkpointing a large manifest "because the step says fully autonomous" is the misread — the checkpoint is a clean terminal exit that delivers a slice, not a wait-for-input halt.
- **Re-applying prior-pass rows on resume.** A fresh resume session that re-reads and re-applies rows already `✓ applied` in the manifest wastes the budget it was trying to save and risks re-forking consolidated components. Honor `{resume_prior_dispositions}` — skip them.
- Fixing some deltas but not all ("the rest are minor" — fix them all, or defer-with-reason)
- Editing without re-reading to verify (edits can silently fail or land in the wrong location)
- Changing `tailwind.config.js` when an arbitrary value would work
- Committing without running `npm run build`
