# Step 4: Decide Actions Per Level

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Every page must get exactly ONE action — no "maybe" or "TBD"
- In autonomous mode: assign actions for all pages and proceed to step 05 without pausing

## CONTEXT BOUNDARIES:

- `{page_impact_map}` from step 03 tells you each page's impact level
- `{section_diffs}` tells you what specifically changed
- `{policy_current}` is the target state all pages must comply with

## YOUR TASK:

Translate impact levels into concrete actions. Each action type has a defined deliverable.

**Check for a FOUNDATIONAL-TOKEN change FIRST (Level 0), before any per-page action.** If `{section_diffs}` touches a foundational token (type scale / control heights / radii / status colours), the Level-0 canonical-token migration is the primary action — and it DISSOLVES the per-page restyle work for every token-trusting surface (one canonical edit corrects them all). Assign Level 0 first, apply/scope it, THEN classify only the residual pages (the ones that hardcoded px and so don't benefit). Skipping this is exactly how policy v3's 13px shipped "flagged, not auto-migrated."

## ACTION RULES:

### Level 0 → Foundation-Token Migration (the canonical-token edit — runs BEFORE per-page actions)

**Deliverable:** A single-source edit to the canonical token surface — `src/styles/tokens.css` (+ the `globals.css @theme inline` block) — bringing the **foundational tokens** into agreement with the scale `{policy_current}` declares. NOT a per-page brief: one edit corrects every token-trusting surface at once.

**When it fires:** `{section_diffs}` changes a **foundational token** — the **type scale** (`--font-size-base/-sm/-xs/-md`), **control heights** (`--control-h/-sm`), the **radius scale** (`--radius/-md/-lg`), or the **status-colour set** (`--status-*`) — the tokens no page owns but every page inherits. This is the action whose ABSENCE left policy v3's "13px denser default body" *"flagged, not auto-migrated"*: the canonical `src/styles/tokens.css` kept its old scale, every ported surface rendered at the wrong size, and `design-implement` had nowhere to route the drift (its §2i Foundation-token row, and `design-review-pr` F-FOUNDTOKEN-01, both route HERE).

**It runs FIRST and reshapes the per-page map.** Once the canonical token is migrated, every page that *trusts the token* (`var(--font-size-base)`) is corrected automatically and needs NO Level-1 restyle for that property. The per-page passes then cover only (a) pages that **hardcoded px** (bypassing the token — they don't shift with the migration and now need a real Level-1/2 cleanup) and (b) genuine structural changes.

**Scope + guardrails:**
- Edit the **canonical surface only** (`src/styles/tokens.css` + `@theme`). Do NOT fix a foundational drift per-page, and NEVER as a `var(--token, <literal>)` fallback — inert when the global is defined, the #2412 anti-pattern that `design-implement` §2i and `design-review-pr` F-FOUNDTOKEN-01 forbid.
- **A canonical-token change is app-wide — a visual regression pass is owed.** Every token-trusting surface shifts. In the action-map Notes, list the *hardcoded-px* surfaces (they will NOT shift and now diverge from the migrated token → a follow-up cleanup) and confirm the token-trusting surfaces were spot-checked.

**Template signals:**
- "Migrate `src/styles/tokens.css` to policy v{N}: `--font-size-base` {old} → {new}, …"
- "App-wide — token-trusting surfaces shift; hardcoded-px surfaces ({list}) need a separate cleanup"
- "Do NOT per-page-patch or dead-fallback this; the canonical token is the single source"

### Level 1 → Restyle Brief

**Deliverable:** A short brief (< 1 page) that tells the implementer exactly what to change visually without touching structure.

**Scope:**
- CSS/Tailwind class changes only — no component restructuring
- Color, spacing, font-size, font-weight adjustments
- Tone/copy updates (error messages, empty states, labels)
- No new components, no layout changes, no information architecture changes

**Template signals:**
- "Restyle to policy v{N}"
- "Keep IA and workflow intact"
- "Change only: {specific properties}"

### Level 2 → Component Refresh

**Deliverable:** A component-scoped brief listing which components need updating and what the new pattern is.

**Scope:**
- Specific component patterns need to change (badges, filters, tables, buttons)
- May require shared component updates (affects multiple pages)
- Page layout stays the same — components within it change
- May include new hard-failure compliance fixes

**Template signals:**
- "Update {component} to match policy v{N} pattern"
- "Shared component: changes will affect pages {list}"
- "Hard failure fix: {what was violating, what it should be}"

**Shared component detection:**
If multiple pages use the same component and it needs updating, consolidate into a single component-level task rather than per-page tasks. List the shared component once, then reference it from each page's brief.

### Level 3 → Full Handoff Rerun

**Deliverable:** Trigger the `design-handoff` workflow for this page with the new policy version.

**Scope:**
- The page needs fresh design thinking — layout, IA, or mode behavior has changed
- The existing brief is obsolete — a new brief must be generated
- The designer should start from the policy, domain data, and user context — NOT from the current implementation

**Template signals:**
- "Rerun design-handoff for {route} under policy v{N}"
- "Previous brief at {path} is obsolete — do not reference its layout or structure"
- "Page mode changed from {old} to {new}"

## BUILD ACTION MAP:

`{page_action_map}`:

| Page / Route | Action | Deliverable | Priority | Notes |
|-------------|--------|------------|----------|-------|
| **(app-wide, do first)** | **foundation_migration** | **Canonical `tokens.css` edit** | **P1** | **{which foundational tokens; hardcoded-px surfaces needing follow-up cleanup}** |
| {route} | restyle | Restyle brief | {P1/P2/P3} | {what specifically changes} |
| {route} | component_refresh | Component brief | {P1/P2/P3} | {which components, shared?} |
| {route} | full_handoff | Design-handoff rerun | {P1/P2/P3} | {why structure is misaligned} |

### Priority rules:

- **P1:** Page violates a new hard failure — must be fixed before next deploy
- **P2:** Page is visually inconsistent with new policy — fix in current sprint
- **P3:** Page would benefit from update but isn't broken — schedule for next sprint

## PRESENT ACTION MAP:

"**Action plan for policy v{policy_version_previous} → v{policy_version_current}:**

**Immediate (P1):**
{list — hard failure violations}

**This sprint (P2):**
{list — visual inconsistencies}

**Next sprint (P3):**
{list — beneficial updates}

**Shared components to update first:**
{list of components used by multiple pages, with affected page count}

Ready to generate briefs?"

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/steps/step-05-emit-briefs.md`.

In autonomous mode: proceed immediately.
