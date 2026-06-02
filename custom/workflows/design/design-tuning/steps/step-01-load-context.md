---
name: 'step-01-load-context'
description: 'Load design brief, visual references, corporate guardrails, and previous iteration state'
---

# Step 1: Load Context

**Progress: Step 1 of 3** — Next: Analyze Screenshot (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- If a required file is missing, work with what's available — don't block.
- Extract constraints precisely from the brief — quote section numbers when possible.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## SEQUENCE OF INSTRUCTIONS

### 1. Locate and Read the Design Brief

Find `{brief_path}`:

- If the user specified a brief → use that path
- Otherwise, find the most recent design brief:
  ```bash
  ls -t {implementation_artifacts}/design-brief-*.md | head -1
  ```

**Worktree-resident briefs — CRITICAL (do NOT conclude "no brief" from the main-tree glob alone).** A brief authored via `design-handoff` is frequently written in a feature worktree and iterated on *before* it merges to main — so the glob above, which only sees the main checkout, returns nothing even though a current brief exists. The artifact under tuning is often built from exactly that unmerged brief. If (and only if) the main-tree glob finds nothing, sweep sibling worktrees before giving up:
```bash
ls -t {project-root}/.claude/worktrees/*/_bmad-output/implementation-artifacts/design-brief-*.md 2>/dev/null
# match by frontmatter target_slug / route / feature to the surface under review; prefer brief_status: active
```
If a worktree-resident brief matches the surface under review, **use it** — it still passes through §1a provenance validation unchanged — and record `{brief_provenance_caveat} = "brief is worktree-resident (<branch>), not yet merged to main"` so step-03 surfaces it. A worktree-resident brief is the same source of truth as a merged one; the only difference is the caveat.

Only after BOTH the main tree and the worktrees come up empty may you proceed brief-less — and a brief-less run is **degraded**, not normal. With no contract you have no list of legitimate fields, so before judging the artifact you MUST: (a) validate every field the artifact displays against the schema / `{project-root}` MCP, and (b) resolve documented **joins** (e.g. an order's import-account or route-warehouse name reached via an FK), not just the base table, before flagging any field as "invented." Calling a documented join "invented" is the brief-less failure this note exists to prevent.

Read the full brief. Extract and store:

- `{feature_name}` — from the brief's frontmatter `feature:` field
- `{brief_path}` — absolute path to the brief file

### 1a. Validate Brief Revision Provenance

Before extracting constraints, validate the brief's revision provenance per `{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md`. This is a **hard halt** override on §1's "don't block, work with what's available" rule — an invalid or superseded brief cannot drive an iteration loop, because every correction message would be anchored to the wrong contract.

Apply the consumer checks in the policy doc §5 (Checks 1–6) against the brief's frontmatter. The same diagnostics apply. The only differences from the other consumers:

- **Escape hatch:** `--allow-superseded` is honored only when the user passed the brief path explicitly (not when this step found it via the `ls -t` fallback). Auto-discovered briefs must be active.
- **No fallback:** if the most-recent brief is superseded, do NOT silently fall back to its predecessor. Halt and require the user to either pass the active brief's path explicitly or re-run `design-handoff`.

On success, capture `{brief_revision_mode}`, `{brief_change_class}`, `{brief_last_modified_by}`, `{brief_last_modified_date}`, and `{brief_supersedes}` into state. Step-03's correction message includes a provenance line so the next iteration of the design tool sees which brief revision the correction was anchored to.

### 1b. Load Project Design Policy (canonical source)

Check both possible locations for a project-level design system declaration, in order. `docs/design-policy.md` is the canonical location; `{planning_artifacts}/brand-identity.md` is the legacy slot. Prefer the first if both exist:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {implementation_artifacts}/../planning-artifacts/brand-identity.md 2>/dev/null
```

**Worktree-resident policy — same trap as the brief (§1 above).** A `docs/design-policy.md` created via `create-design-policy`/`onboard-design-system` is often authored in the same feature worktree as the brief and not yet merged. If both main-tree paths come up empty, sweep worktrees before declaring "no policy":
```bash
ls {project-root}/.claude/worktrees/*/docs/design-policy.md 2>/dev/null
```
If found, load it as `{brand_identity}`, set `{brand_identity_path}` to the worktree path, and append the same `worktree-resident, not yet on main` caveat. Concluding "no project policy" while one exists in a worktree is the loader-drift bug §5 of this step explicitly forbids — it silently drops every hard-failure check to brief-only/generic mode.

**If either is found:**
- Read the entire file and store as `{brand_identity}` (variable name retained for backward compatibility with downstream templates)
- Set `{brand_identity_path}` to the absolute path of whichever file was loaded
- Extract `{hard_failures}` from the policy's hard-failures section (numbered list in §5 of `docs/design-policy.md` or §8 of legacy `brand-identity.md`)
- Extract `{policy_constraints}` — the full set of testable rules from the policy (status palette, color count limits, badge shapes, layout principles, page-mode rules, detail-view rules). This is the source-of-truth set against which any brief-derived constraint will be contradiction-scanned in step-02.
- Extract `{visual_references}` from the policy's external-influences / reference-products section — these persist across iterations and don't need user re-input
- Report: "Project design policy loaded from `{brand_identity_path}` — evaluating against project visual language. Brief is derivative; policy wins on conflict."

**If neither is found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty, `{policy_constraints}` = empty
- Report: "No project design policy. Evaluating against brief constraints and generic guardrails. Consider running `create-design-policy` to make future runs deterministic."

### 1c. Ingest the Design Artifact Source (treatment-check baseline)

Treatment-level checks (ring/opacity, radius, padding, font, color, dot presence) must read the artifact's **actual CSS**, not the screenshot — a sub-visible detail like a `ring-rose-500/20` inset ring is invisible in a PNG. This step ingests that source. It is a degraded-mode switch, NOT a hard halt: with no source, treatment checks are flagged unverifiable and the composition lane still runs.

Resolve `{artifact_url}` from, in order: (a) a URL/share link or bundle path the user passed this invocation, (b) an `Artifact under review:` line in the existing `{state_file_path}` (the canvas ID/URL is recorded there across iterations), (c) absent.

**If a Claude Design artifact URL is available** — fetch and extract it using the **identical mechanism design-implement already documents** (do not reinvent it). Follow `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-01-ingest-design.md` §URL PATH (URL.1–URL.5):

```bash
curl -sL "{artifact_url}" -o /tmp/design-tuning-bundle.tar.gz
mkdir -p /tmp/design-tuning-bundle && cd /tmp/design-tuning-bundle
file ../design-tuning-bundle.tar.gz   # gzip tar | tar | bare HTML — branch as design-implement URL.1 describes
# extract, then: find /tmp/design-tuning-bundle -name "*.html" -type f
```

Set `{artifact_source_dir}` to the extracted directory. If the download fails, retry once; if it fails again, do NOT halt — fall through to the screenshot-degraded branch below and record the fetch error.

**If a local design-synthesize bundle directory is available** — set `{artifact_source_dir}` to it (no curl) and read `tokens.css` + the `<screen>.html` files per design-implement §BUNDLE PATH.

**Once `{artifact_source_dir}` is set (either path):** catalog `{artifact_css_catalog}` — but scoped to the components under review, not the exhaustive design-implement grid. For each status pill / badge / filter chip / drawer / button / row that the brief or policy treats as a shared treatment, extract the treatment properties: `border-radius`, `box-shadow` / ring class + opacity, `padding`, `font-size`, `font-weight`, `letter-spacing`, `text-transform`, exact background/text color (resolved through tokens), and presence/absence of a leading colored dot. Record each as `{ component, property, raw_value, resolved_value, source_file:line }`. Set `{treatment_evidence_mode} = bundle-exact`.

**If no artifact source is available** — set `{artifact_source_dir}` = empty, `{artifact_css_catalog}` = empty, `{treatment_evidence_mode} = screenshot-degraded`, and report:
> "No design artifact source — treatment-level checks (ring/opacity, radius, spacing, color, dot) cannot be verified from screenshots alone and will be marked `unverified-treatment`. Provide the Claude Design artifact URL to verify them exactly. Composition checks proceed normally."

### 1d. Resolve Canonical Codebase Components (the §13 cross-surface reference — read from code, not prose)

The policy's §13 cross-surface-coherence rule (and any "match the {sibling surface}" constraint) names a *shared component language* — but the **authoritative definition of that language is the live component in this project's codebase, not the policy's prose description of it.** Reading the prose instead of the component is the iter-4 V18 failure: the policy said "ring-inset"; the canonical `/expenses` pill shipped a flat-reading faint ring; the workflow certified against the prose and missed the divergence.

For each treatment-class the policy/brief marks as cross-surface-shared (status pill, badge, filter chip, drawer, button), locate the canonical component in the codebase and extract its real values into `{canonical_components}`. Search the project's actual source root (read it from config / repo layout — do NOT assume a stack; the example below is SvelteKit `src/`, adjust to the project):

```bash
# Status/badge primitives are usually centralized — start there, then the shared pill component, then the named sibling surface.
# Adjust the search root + style syntax to the project (Tailwind classes, CSS modules, styled-components, etc.).
grep -rIn "ring-1 ring-inset\|rounded-md\|rounded-full\|bg-.*-100 text-\|bg-.*-50 text-" <project-source-root> 2>/dev/null | grep -iE "badge|status|pill|chip"
```

Resolve, per class: the source file + the exact value the canonical component renders (for a Tailwind project, the class string, e.g. `status.ts badge() → bg-{c}-50 text-{c}-700 ring-1 ring-inset ring-{c}-500/30`; for CSS/other, the resolved declarations). When the codebase ships **more than one** treatment for the same class (e.g. a ring-inset primitive AND a flat sibling), that divergence is itself a finding — record BOTH in `{canonical_components}` and surface it: this is live policy↔code drift, and per `{project-root}` CLAUDE.md **code outranks the policy doc**. Do not pick the policy's version and move on; name the split so step-02 can flag it and the user can reconcile (`modify-design-policy`).

If the project has no implementation yet (greenfield, no component to read), `{canonical_components}` is empty for that class — step-02 §2a's cross-surface compare is skipped, and the treatment lane still checks absolute values (radius, dot presence) against the policy. Note it; do not invent a canonical value.

If no policy/brief constraint marks any treatment-class as cross-surface-shared, set `{canonical_components}` = empty and skip — there is no reference to compare against.

### 1e. Resolve Documented Identifier & Value Formats (the §13a content-lane anchor)

This is the companion to §1d. Where §1d reads the *treatment* (CSS) of cross-surface-shared components, this reads the documented *display form* of cross-surface-shared **identifiers** — what step-02 §2b compares the rendered strings against. It is cheap and best-effort; the §2b internal-consistency check (part a) does not depend on it, so an empty result here never blocks the content lane.

1. **Enumerate `{identifier_classes}`** — the canonical-identifier classes the surface renders, drawn from the brief's §2 Domain Data tables and the policy's §13 "Canonical identifier" examples: supplier, buy/sell marketplace, ASIN / SKU / product code, order / shipment / batch number, currency, date. These are the records §13 requires to read and format identically on every surface.

2. **Extract `{identifier_format_expectations}`** — a map of `{ class → documented display form }`, read from the brief §2 Notes column where it documents a human label form (e.g. `marketplaceBuy` → *"label, e.g. 'Amazon DE'"*; `asin` → *monospace code, verbatim*). Capture only what the brief/policy actually documents — do **not** invent a canonical form. Where a class has no documented form, leave it unset: §2b part (a) still enforces internal consistency across surfaces for it.

If the brief has no §2 Domain Data table (brief-less or minimal-brief run), set both to empty and note it — §2b runs on internal consistency alone.

### 2. Extract Constraints from the Brief (derivative — not authoritative)

Parse the brief and extract its stated constraints. **The brief is derivative of the policy loaded in step 1b.** Step-02 will contradiction-scan brief-derived constraints against `{policy_constraints}`; on conflict, policy wins.

**If a project design policy exists (`{brand_identity}` populated):**

The brief's section 4 (Visual Identity) and section 5 (Hard Constraints) were generated from the policy — but **the policy file itself is the authoritative source for everything covered there.** The brief may legitimately:
- Restate, focus, or summarize the policy for one feature.
- Add feature-specific constraints the policy doesn't cover (responsive targets for this page, data density expectations, navigation position, interaction model).

The brief MAY NOT:
- Introduce parentheticals or carve-outs that soften policy hard rules.
- Permit something the policy bans.
- Drop a hard-failure bullet the policy declares.

When the brief and policy disagree, the policy text is what step-02 evaluates against. Drift is logged, not honored.

Extract `{brief_constraints}` from:
- Section 5 (Hard Constraints) — capture the brief's full bullet list; step-02 will diff this against `{hard_failures}` from policy.
- Section 5's feature-specific tail — responsive targets, data density, navigation position, interaction model (these are net-new from the brief; no policy version to compare).
- Section 6 (Design Ask) — the specific design directive and scope.

Set `{corporate_guardrails}` from `{hard_failures}` (loaded from policy in step 1b) + the AI fingerprint sensitivity section of the policy + the standard AI fingerprint list. **Do NOT pull `{corporate_guardrails}` from the brief; the brief may have softened items.**

**If no project design policy exists (`{brand_identity}` empty):**

The brief is the only available source — there is nothing to contradiction-scan against. Be aware that brief-stated hard rules are unverifiable in this mode.

Extract `{brief_constraints}` from:
- Section 5 (Constraints) — responsive targets, data density, navigation position, interaction model
- Section 4 (Design System Context) — tokens, patterns, reference pages
- Section 6 (Design Ask) — the specific design directive and scope

Extract `{corporate_guardrails}` from:
- Section 4a (Corporate Design Guardrails) — if present
- If section 4a does not exist, check for a standalone corporate guidelines doc:
  ```bash
  ls {implementation_artifacts}/../planning-artifacts/corporate-design-system-guidelines.md 2>/dev/null
  ```

Store the anti-patterns as a numbered checklist — each one becomes a violation check in step 2.

### 3. Load Visual References

Check for visual references in this order:

1. **State file** — if `{state_file_path}` exists and contains a `## Visual References` section, load from there (persisted from a previous iteration)
2. **Companion file** — check for `{implementation_artifacts}/visual-references-{feature-slug}.md`
3. **User input** — if the user pasted visual reference research inline (e.g., Perplexity output), capture it as `{visual_references}`
4. **None found** — set `{visual_references}` to empty. The workflow still works using the brief's constraints alone, but correction messages will lack positive product anchors.

Store `{visual_references}` — should contain:
- Named products (e.g., Stripe, Linear, Ramp, Mercury)
- What to borrow from each (table structure, badge treatment, filter patterns, color strategy)
- Any concrete specs (row heights, chip sizes, spacing values)

### 4. Load Previous Iteration State

Resolve `{state_file_path}`:
```
{implementation_artifacts}/design-tuning-state-{feature-slug}.md
```

**If the file exists:**
- Read it and extract:
  - `{iteration_number}` — increment by 1
  - `{previous_violations}` — the violations list from the last iteration
  - `{visual_references}` — if not already loaded from a higher-priority source
- Report: "Iteration {N} — {X} violations from last round to check."

**If the file does not exist:**
- Set `{iteration_number}` = 1
- Set `{previous_violations}` = empty
- Report: "First iteration — establishing baseline."

### 5. Verify Minimum Context

Confirm at least these are populated:
- `{brief_path}` ✓ (required — cannot proceed without a brief)
- `{feature_name}` ✓
- `{brand_identity_path}` ✓ (path or explicit empty — must be a deliberate value, not unchecked)
- `{policy_constraints}` ✓ (populated if policy loaded; empty otherwise — must be a deliberate value)
- `{brief_constraints}` ✓
- `{corporate_guardrails}` ✓ (may be empty if not a corporate project — that's OK)
- `{iteration_number}` ✓
- `{treatment_evidence_mode}` ✓ (`bundle-exact` or `screenshot-degraded` — must be a deliberate value, set by §1c)
- `{artifact_css_catalog}` ✓ (populated in `bundle-exact` mode; empty in `screenshot-degraded` — deliberate value)
- `{canonical_components}` ✓ (populated if any treatment-class is cross-surface-shared; empty otherwise — deliberate value)
- `{identifier_classes}`, `{identifier_format_expectations}` ✓ (from §1e — populated where the brief §2 documents identifier classes/forms; empty otherwise — a deliberate value, not unchecked. §2b's internal-consistency check runs even when empty.)

**If `{brand_identity_path}` is empty in a project that appears to have a policy file you didn't find, STOP and report which paths you checked.** Silent fallback to brief-only mode is the loader-drift bug this workflow exists to prevent — surface it instead of swallowing it.

---

## COMPLETION

Load and follow: `{project-root}/_bmad/bmm/workflows/design/design-tuning/steps/step-02-analyze.md`

---

## SUCCESS METRICS

- Design brief located and read
- Constraints extracted as a checkable list
- Corporate guardrails extracted as a numbered checklist (if applicable)
- Visual references loaded from the best available source
- Previous iteration state loaded (if exists)
- Iteration number set correctly
- Artifact source resolved (§1c) — `{treatment_evidence_mode}` is a deliberate `bundle-exact` or `screenshot-degraded`, never unset; in `bundle-exact` mode `{artifact_css_catalog}` carries the treatment values for the components under review
- Canonical codebase components resolved (§1d) — `{canonical_components}` holds the real class strings of each cross-surface-shared treatment, read from code; any one-class-two-treatments split is recorded as policy↔code drift
- Documented identifier/value formats resolved (§1e) — `{identifier_classes}` enumerates the canonical-identifier classes on the surface and `{identifier_format_expectations}` holds any documented display form from the brief §2; both deliberate values (empty is allowed and does not block §2b)
