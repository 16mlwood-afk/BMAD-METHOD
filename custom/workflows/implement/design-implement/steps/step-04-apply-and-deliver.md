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
| `⊘ deferred` | Intentionally not applied this pass. | **Reason, one of:** `needs-data` (the page load / server doesn't provide the value — name the field), `out-of-scope` (explicitly outside this run's target), `judgment` (a product decision the implementer made — state it), `content-lane` (a formatter/enum-driven identifier cell from step-03 §2c — its rendered value cannot be verified against a mock-data bundle; routed to design-review / design-tuning on the LIVE page). |
| `✗ dropped` | Cannot or will not apply at all. | **Reason** — why it's not implementable as specified. |

Every `content-lane` row from step-03 §2c (`{content_unverified_count}` of them) is disposed `⊘ deferred(content-lane)` — its CSS may well have been applied, but its *value-formatting* is explicitly NOT certified here. Do not silently `✓` it; do not drop it. It carries into §9 under "Content-lane verification owed (live page)" with the routing command, so the run hands the content lane off out loud instead of implying the grid covered it.

Rules:
- **No row without a disposition.** A grid row you neither applied nor explicitly deferred/dropped means the run is incomplete — go back and resolve it. "I didn't get to it" is not a disposition.
- **`deferred`/`dropped` must carry a reason from the table above.** A bare "deferred" is the silent-drop in disguise.
- Write the disposition into the grid artifact next to each row, and update the summary line at the bottom:
  `Applied: {A}/{delta_count} · Deferred: {D} · Dropped: {X}` (A + D + X must equal `{delta_count}`).
- The deferred + dropped rows are carried verbatim into the §9 completion report's mandatory "Deltas not applied" section — they are NOT allowed to live only in the artifact where the user won't see them.

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
- [ ] Build passes (`npm run build`)
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
Design implementation complete.

Baseline: {baseline_commit}
Deltas: applied {A}/{delta_count} · deferred {D} · dropped {X}
PR: {pr_url}
Deploy: handled by ./scripts/bmad-deploy.sh — run after merge per the BMAD contract

Comparison grid: {artifact_path}

Deltas not applied:
{if D + X == 0:}
  None — all {delta_count} deltas applied.
{else, one bullet per deferred/dropped row:}
  - ⊘ {grid row id / short description} — deferred ({reason}: {detail})
  - ✗ {grid row id / short description} — dropped ({reason})

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
```

A completion report that prints a fixed-count but omits the "Deltas not applied" section is non-conformant — re-emit it. The whole point of this section is that a partial implementation announces itself instead of shipping silently as "done." The **"Content-lane verification owed" section is equally mandatory** and never omitted: design-implement aligning a marketplace/supplier/ASIN cell's CSS is NOT the same as certifying it renders the right value on real data — that lane belongs to the live-page workflows, and the report must say so rather than let "implementation complete" imply the identifier values were checked.

---

## SUCCESS METRICS

- **Every grid row has an explicit disposition** (`applied` / `deferred(reason)` / `dropped(reason)`) — `A + D + X == {delta_count}`, no undisposed rows
- Apply was grid-driven (every fix traces to a row), not a holistic rebuild
- Every applied delta is fixed and re-verified by re-reading the file
- **The completion report's "Deltas not applied" section is present** — enumerating every deferred/dropped delta with its reason, or stating "None — all N applied"
- **The completion report's "Content-lane verification owed (live page)" section is present** — every `content-lane` deferral (step-03 §2c) enumerated with its formatter ref + the design-review / design-tuning routing, or stating "None"
- Build passes; PR created and merged; grid artifact updated with dispositions; no regressions introduced

## FAILURE MODES

- **Holistic rebuild instead of grid-driven apply** — "make the page look like the design" satisfies composition while silently dropping enumerated rows (band sender clause, kbd hints, a sort control). This is the dominant leak and the reason the apply ledger exists (accounting-tools /queries #900).
- **Reporting a count without the "Deltas not applied" list** — "47/47" or "deltas fixed: X" with no enumeration of what was deferred/dropped. A partial that omits the disclosure ships looking complete. The §9 section is mandatory.
- **A bare `deferred` with no reason** — the silent drop wearing a label. Every deferral names `needs-data` / `out-of-scope` / `judgment` / `content-lane` + detail.
- **Letting "implementation complete" imply the identifier *values* were checked.** design-implement aligns a marketplace/supplier/ASIN cell's CSS against the bundle; it does NOT verify the formatter renders the right value on real data (the bundle is mock data). Omitting the "Content-lane verification owed" section ships that false implication — it is the design-implement counterpart of the inbound-flow `/orders` raw-enum leak that the grid's mock-data comparison could never catch.
- Fixing some deltas but not all ("the rest are minor" — fix them all, or defer-with-reason)
- Editing without re-reading to verify (edits can silently fail or land in the wrong location)
- Changing `tailwind.config.js` when an arbitrary value would work
- Committing without running `npm run build`
