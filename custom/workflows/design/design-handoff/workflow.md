---
name: design-handoff
description: 'Generate an unbiased Claude Design brief from a completed implementation. Gathers data model, user context, design tokens, and constraints — deliberately excludes current layout and component structure so the designer starts from a blank canvas. Use after building a feature when you want Claude Design to design or redesign the UI.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_agent_workflow: '{project-root}/_bmad/bmm/workflows/design/design-agent/workflow.md'
quick_dev_workflow: '{project-root}/_bmad/bmm/workflows/implement/quick-dev/workflow.md'
---

# Design Handoff Workflow

**Goal:** After an implementation is complete (or partially complete), produce a structured design brief that Claude Design can consume directly from the repo. The brief gives Claude Design everything it needs to design (or redesign) the UI without asking clarifying questions about architecture, data shape, or constraints.

**Your Role:** You are a bridge between engineering and design. You understand both the technical implementation and what a designer needs to produce great work. You extract the right context from code — not too much (overwhelming), not too little (ambiguous) — and structure it for a design tool that has repo access.

**Key Insight:** Claude Design can read files from the repo (GitHub is linked). The brief should reference file paths for deep context rather than inlining everything. But it MUST inline enough for Claude Design to start working immediately — don't require it to read 20 files before understanding the ask.

**Anti-Bias Principle — CRITICAL:** The current UI was built by a developer, not a designer. Its layout, information grouping, visual hierarchy, and component structure are *implementation choices*, not design requirements. The brief must **never** describe what the current page looks like or how information is currently organized. Instead, give the designer the raw materials — data model, user purpose, constraints, visual direction — and let them create their own vision. The brief describes the desired aesthetic (theme, reference products, tokens), not the current structure.

**Anti-Bias Principle II — policy defaults are bias too — CRITICAL:** The project design policy supplies two different things, and they carry different authority. The **visual system** (tokens, colour, type, component treatment, hard failures) is non-negotiable — the brief inherits it verbatim. But the policy also attaches a **default composition to each page-mode** (operational → table-first worklist + right-side detail drawer; analytical → chart-led; detail → record-view), and that default is *not* a certification that THIS surface's job fits it. Stamping the mode's default composition into the brief unquestioned is a bias as real as inheriting the legacy layout — and harder to catch, because it feels like correctly following the system. A pull-based dispensing queue, or a per-item comparison surface, can be fully "operational" and yet be actively harmed by a table-first worklist + right-side drawer. §5a (Composition Fit Check) decides the *primary composition* from the job, and surfaces a `recommended-alt` for veto when the default doesn't fit. **Inherit the visual system; verify the composition.**

**Brief Section Order:** The template follows this sequence for optimal handoff to Claude Design: Feature purpose → Domain data → User context → Visual direction → Hard constraints → Design ask. This order lets the designer understand the business problem before encountering visual constraints.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

When this workflow encounters conflicting guidance, the order of authority is:

1. **Project design policy** — `{project-root}/docs/design-policy.md` (canonical) or `{planning_artifacts}/brand-identity.md` (legacy slot). Hard failures, status rules, layout principles, and reference patterns are defined here.
2. **Shared BMAD design standards** — `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md`. Universal anti-AI-slop guardrails that the project policy can override but not contradict.
3. **Generated design briefs** — `{implementation_artifacts}/design-brief-*.md`. Derivative of (1) and (2). Briefs MAY restate, focus, or summarize the policy for one feature. Briefs MUST NOT introduce carve-outs, softenings, exceptions, parentheticals, or anti-patterns the policy does not contain.
4. **Review/refinement artifacts** — `{implementation_artifacts}/screen-review-*.md`, design-tuning state files. Derivative of (3). Cannot contradict higher levels.

**Implications for this workflow:**
- When step-03 generates the brief, sections quoted from the policy (visual identity, hard failures, AI sensitivity, component patterns) must appear **verbatim** — no inserted exceptions, no editorializing parentheticals, no "the codebase already does X so the designer may also" softenings.
- If the brief author (you) believes the policy is wrong or incomplete, surface that to the user as a `modify-design-policy` candidate. Do NOT route around the policy by patching the brief.
- A brief that fails the precedence check propagates the drift into every downstream design-review and design-tuning run, because those workflows treat the brief as authoritative for the feature. Catching drift here is the cheapest fix.

---

## BRIEF REVISION POLICY — CRITICAL

This workflow is the **producer** under `shared/brief-revision-policy.md`. Every brief written by step-03 must carry the provenance frontmatter block defined there. Step-03 is responsible for:

- Detecting whether an active predecessor brief already exists for this `target_slug` (§1a of step-03).
- Setting `change_class` to `original` (no predecessor) or `material_revision` (one predecessor) — a re-run of `design-handoff` on the same surface is material by definition.
- Halting if two or more active predecessors exist — that's a pre-existing invariant break that this workflow cannot silently paper over.
- Flipping the predecessor's `brief_status` to `superseded` and setting its `superseded_by` in the same run (§1b of step-03) when superseding.

Consumers (`design-artifact-loop`, `design-synthesize`) validate the provenance block at intake and halt on missing fields, broken invariants, or forbidden combinations. A brief that fails consumer validation is unconsumable — there is no fallback. See `shared/brief-revision-policy.md` for the full contract, the editing rules, and the halt diagnostics consumers emit.

---

## ANALYTICS PRESENTATION RATIONALE — companion artifact

When a brief carries an analytics band (`{has_analytics_band}` is `true`), this workflow emits a **second** artifact beside the brief: `design-rationale-{target_slug}-{date}.md`. It documents *how* the analytics presentation was decided — the page-mode signal, the band-belongs answers, the archetype candidates weighed, the shapes rejected, and the explicit time≠trend check. The brief records the winning choices; the rationale records the deliberation behind them.

This exists because the brief is a **bias filter** (it withholds the current layout so the designer starts blank) — so the reasoning cannot live inside the brief without breaking that mandate. Key rules (full spec in `shared/analytics-rationale.md`):

- **Conditional.** No band → no rationale file. Never emitted for a plain operational worklist.
- **Not a brief.** Out of scope for `brief-revision-policy.md` — no Block A, no 6 intake checks, no consumer validation. It carries only its own `rationale_status`/`supersedes`/`superseded_by` lineage, derived 1:1 from the brief it accompanies.
- **One-way linkage.** The rationale's `accompanies_brief` names the brief; the brief never references the rationale. Claude Design reads the brief, never the rationale.
- **Delivered together.** step-04 stages both in one commit/PR so a brief on `main` always has its rationale beside it.

The archetype reasoning is produced by the `analytics-surface-architect` skill (invoked in step-01 §5c — the single selection brain, so handoff, design-review-pr, and a human all reason the same way), captured at decision time, and rendered by step-03b. Capturing it where the decision is made is what turns a discarded deliberation into an auditable record. The skill is the preferred path; §5c falls back to applying `shared/analytics-archetypes.md` inline if the skill isn't synced into the project.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables (see below)
- Sequential progression: gather → audit → generate → deliver

**Step 4 (deliver)** is governed by `shared/delivery-to-main.md`. It commits the brief, opens a PR, merges to `main`, and surfaces the merged URL — closing the gap between "file written to disk" and "file accessible to external consumers (Claude Design, downstream synthesize, design-implement) via `origin/main`". Skippable via `--no-deliver` or `delivery.design-handoff: skip` in config.

### State Variables

- `{feature_name}` - Name of the feature being handed off
- `{feature_scope}` - "new" (design from scratch) or "redesign" (improve existing)
- `{feature_purpose}` - What the feature does and why it exists — NOT how it is currently laid out
- `{must_support_capabilities}` - The jobs the operator must be able to accomplish on this surface beyond the primary goals, captured as outcomes (NOT UI mechanics) in step-01 §4. These are requirements the blank-canvas redesign must satisfy even though the brief withholds the current layout — the anti-bias strip removes the *arrangement*, never the *capability*. Rendered into the brief's §1 (Feature Purpose). Guards the failure where a redesign returns "more basic" than the screen it replaced because a secondary capability (e.g. attach-source-receipt, verify-field-against-source, bypass-staging) was never named and so was silently dropped. Empty when the surface has none beyond the primary goals.
- `{data_shape}` - Domain entities and their primitive fields, in domain language — NOT the page server's return type. Captured by walking up from DB schema, not down from the UI response. See step-01 for procedural capture rules.
- `{api_surface}` - Endpoints and response shapes the frontend can call
- `{implementation_files}` - File paths for implementation reference only (designer may browse for technical context, not for layout inspiration)
- `{brand_identity_path}` - Path to the project's brand identity document (if it exists)
- `{brand_identity}` - Contents of the brand identity document — provides positive visual anchors, design tokens, component patterns, reference pages, and hard failures. When present, this is the PRIMARY source for design system context — it supersedes token extraction and generic guardrails.
- `{policy_version}` - Integer version of `docs/design-policy.md` at brief-generation time (parsed from frontmatter `version:` field; `1` if no version field; `0` if no policy file). Stamped into the generated brief's `policy_version_required:` frontmatter so downstream consumers (design-synthesize, design-implement) can detect when the policy has moved past the brief's pinned version.
- `{design_system}` - "branded" (brand identity exists) or "existing" (extract tokens from code) or "external" (external design system — e.g., created in Claude Design). Controls which variant of section 4 (Visual Direction) and section 5 (Hard Constraints) the brief uses.
- `{design_system_name}` - If external: the name of the design system (e.g., "Meridian"). Empty otherwise.
- `{design_tokens}` - Design tokens — from brand identity (preferred) or extracted from codebase
- `{existing_patterns}` - Component patterns — from brand identity (preferred) or observed in other pages
- `{page_mode}` - "operational" (process rows, review items, take actions), "analytical" (understand patterns, trends, anomalies across a dataset), or "detail" (read/edit one record — a drawer or full-page extension of an operational list). The full three-value enum the whole brief contract uses (`brief-revision-policy.md` Block B; consumed by `design-synthesize` / `design-implement`). Selected in step-01 §5; governs §4a composition and §4b analytics inclusion (detail never carries a band).
- `{composition_provenance}` - `policy-default` | `recommended-alt`. WHETHER the page-mode's default composition (operational→table-first; analytical→chart-led; detail→record-view) fits the job. Decided in step-01 §5a by the job — NOT inherited from the policy default or the legacy render. `recommended-alt` (veto-surfaced, like `recommended-new`) means §4a names a different *primary* composition; it does NOT change `{page_mode}` (work type and composition are orthogonal). Guards against the policy-default bias (Anti-Bias Principle II).
- `{composition_rationale}` - the three §5a answers (selection model / per-item cost / dominant loop) + the named alt composition + the veto outcome for `recommended-alt`. Rendered into §4a's composition-override block; keeps the deviation auditable. Empty (and no override block) when `{composition_provenance}` is `policy-default`.
- `{band_provenance}` - `inherited` | `recommended-new` | `recommended-drop` | `none`. WHY an analytics band exists (or doesn't). Decided in step-01 §5b by data + user job, NOT by inspecting the legacy render — `design-handoff`'s blank-canvas mandate means a bare-table feature whose job is pattern/coverage/ranking work gets a band recommendation (`recommended-new`, veto-surfaced) even when the current page has none. Drives §4b inclusion: present iff `inherited` or `recommended-new`.
- `{has_analytics_band}` - `true` iff `{band_provenance}` ∈ {`inherited`, `recommended-new`}. Gates whether section 4b (Analytics Structure) is emitted.
- `{analytics_archetype}` - The *shape* of the analytics band: one of `trend`, `distribution`, `composition`, `ranking`, `coverage`, `flow`, `single-metric`, `correlation` (or `unclear` → ask). Empty when there is no band. **Selected in step-01 §5c by invoking the `analytics-surface-architect` skill** (the single selection brain; `shared/analytics-archetypes.md` is its taxonomy SoT). Chosen from the user's question, never the data's availability. Prevents every band defaulting to the same trend-strip-of-small-multiples.
- **Analytics reasoning capture** — the `analytics-surface-architect` decision object, captured in step-01 §5c (populated iff `{has_analytics_band}`; rendered into the rationale artifact by step-03b and §4b; empty otherwise):
  - `{page_mode_rationale}` - the concrete signal that selected `operational` vs `analytical` (§5; not from the skill).
  - `{band_decision_log}` - the three band-belongs questions answered for this feature, plus the veto outcome for `recommended-new`/`recommended-drop` (§5b; not from the skill).
  - `{archetype_candidates}` - skill `candidates`: the archetypes weighed, each `chosen | secondary | rejected` + a one-line reason — the road not taken.
  - `{archetype_winner_reason}` - skill `winner_reason`: why the winner won, naming the data dimension AND the user question.
  - `{archetype_secondary}` - skill `secondary`: the subordinate archetype if a second co-occurs, else `none`.
  - `{time_present_check}` - skill `time_present_check`: when time is in the data, the explicit "this is / isn't a trend job" line — the anti-default record.
  - `{archetype_drill_map}` - skill `drill_map`: every band element → its drill target (feeds §4b C and the rationale evidence pass).
  - `{archetype_prohibited}` - skill `prohibited`: the page-specific shape bans (feeds §4b E and rationale §4).
- `{rationale_output_path}` / `{rationale_output_filename}` / `{rationale_path_relative_to_repo_root}` - the analytics rationale artifact written by step-03b (only when `{has_analytics_band}`). Companion to the brief; delivered in the same commit by step-04.
- `{constraints}` - Hard constraints the designer must respect (responsive breakpoints, data density, accessibility)
- `{user_context}` - Who uses this feature, what they're trying to accomplish, frequency of use
- `{reference_pages}` - Existing pages in the app that have good design to reference — from brand identity (preferred)
- `{hard_failures}` - Non-negotiable anti-patterns from brand identity — designs containing any of these fail review
- `{github_repo_url}` - GitHub HTTPS URL for the repository (no trailing `.git`)
- `{output_path}` - Absolute path where the brief is written on disk
- `{output_path_relative_to_repo_root}` - Brief path relative to the repo root (for GitHub URLs and Claude Design references)
- `{handoff_mode}` - `"fresh-design"` (default) or `"refine-screen"`. Refine-screen mode is triggered by the design-pm prompt-expansion or by the user passing `--refine-screen` / `--refine`. In refine-screen mode the workflow consumes a `screen-review` artifact (auto-running `design-review --artifact` first if none exists) and produces a tightly-scoped refinement brief instead of an open creative brief.
- `{review_artifact_path}` - Absolute path to the consumed `screen-review-*.md` artifact (only set in refine-screen mode)
- `{refine_focus}` - Violations parsed from the artifact (V1, V2, … — used to bound the brief's Design Ask in refine-screen mode; the brief may consume all or just the top N)
- `{required_variants}` - Edge states parsed from the artifact (required design variants in refine-screen mode)
- `{peer_steals}` - Peer-pattern transplants parsed from the artifact (used as visual references in refine-screen mode)
- `{already_fine}` - Keepers parsed from the artifact (things refine-screen must NOT break — folded into hard constraints. State-variable name kept for compatibility with step-03 templates.)

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`, `user_skill_level`
- `planning_artifacts`, `implementation_artifacts`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime
- `project_context` = `**/project-context.md` (load if exists)
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Autonomous Mode Override

If `autonomous_mode` is `true` in config:

- **Never halt or wait for user input.** Make expert-level decisions and proceed.
- **Infer feature scope from git history** — if the feature was just committed, it's "new" unless the user says otherwise.
- **Auto-detect design tokens** from CSS/style files without asking which file.

### Input

The user may provide:

- **A feature name or description** — "the outreach queue I just built"
- **A commit hash or branch** — the workflow will diff to understand what changed
- **A route** — `/outreach`, `/pipeline` — the page to design
- **A design system directive** — "use Meridian", "use the corporate design system", "external design system"
- **Nothing** — the workflow will look at the most recent commit(s) on the current branch

If the input is ambiguous, ask ONE clarifying question maximum, then proceed.

### Brand Identity & Design System Detection

**Step 1 — Check for a project design policy (highest priority):**

Projects may declare visual direction, layout principles, status systems, and hard failures in one of two locations. Check both, in order:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

If `{project-root}/docs/design-policy.md` exists, prefer it. Otherwise fall back to `{planning_artifacts}/brand-identity.md`. Both files play the same role — they describe the project's design system. `design-policy.md` is the canonical name; `brand-identity.md` is the legacy slot.

If either file exists:
- Read it and store as `{brand_identity}`
- Set `{brand_identity_path}` to the file path
- Set `{design_system}` = "branded"
- Extract `{design_tokens}`, `{existing_patterns}`, `{reference_pages}`, and `{hard_failures}` directly from the document
- **Skip design system questions entirely** — the project policy IS the design system

**Step 2 — If no brand identity, check for external directive:**

- If the user mentions an external design system by name → `{design_system}` = "external", `{design_system_name}` = that name
- If NOT in autonomous mode → ask: **"Should this design use the existing tokens from the codebase, or an external design system?"**
- If in autonomous mode → default to "existing"

**Step 3 — Fallback (no brand identity, no external directive):**

Set `{design_system}` = "existing" — tokens will be extracted from the codebase in step 02.

**Why brand identity first:** A brand identity document captures the project's ACTUAL visual language — not raw CSS tokens, not generic anti-patterns, but the specific decisions that make this app look like this app. When one exists, it provides both positive anchors (what we look like) and negative constraints (what we never do), which are far more effective than generic guardrails. Without it, Claude Design fills the vacuum with its strongest priors (generic SaaS templates).

### Refine-Screen Detection & Artifact Loading

The workflow handles two modes:

- **`fresh-design`** (default) — new page, new feature, structural redesign. The brief is open and creative. The rest of this section does not apply.
- **`refine-screen`** — iteration on an existing baseline screen. The brief is tightly scoped to the diagnostic from a `design-review` artifact. NO USER COMPLAINTS ARE COLLECTED — the diagnostic is automated.

**Detect mode** in this order:

1. If the user's invocation or prompt-expansion contains the literal `--refine-screen`, `--refine`, or starts with "refine"/"iterate"/"tighten"/"polish"/"second pass on" → `{handoff_mode}` = `"refine-screen"`.
2. If `design-pm` set `{handoff_mode}` in state when routing → honor it.
3. Otherwise → `{handoff_mode}` = `"fresh-design"`.

**If `{handoff_mode}` = `"refine-screen"`, run artifact loading BEFORE step-01:**

1. **Resolve target slug.** From the user's input identify the target route or feature slug. Same kebab-case rule as `design-review`: pathname → strip slashes → replace `/` with `-` → lowercase. Examples: `/reclaim/avask` → `reclaim-avask`; "iterate AVASK" + the AVASK page in context → `reclaim-avask`.

2. **Search for an existing artifact:**

   ```bash
   ls -t {implementation_artifacts}/screen-review-{target_slug}-*.md 2>/dev/null | head -1
   ```

   Pick the most recent. Also accept matches where the slug is a prefix (e.g., `reclaim-avask-v2-...md`).

3. **Branch on result:**

   - **Artifact found AND less than 24 hours old:** Load it. Set `{review_artifact_path}` to its absolute path. Parse the YAML frontmatter into state, then parse the body's Violations → `{refine_focus}` (preserve V-IDs, severities, and all per-violation fields), Edge States → `{required_variants}`, Peer Steals → `{peer_steals}`, Keepers → `{already_fine}`. Proceed to step-01.

   - **Artifact found but older than 24 hours:** The screen may have changed. Surface to the user: "Found a screen-review artifact from {age}. Use it as-is, or re-run design-review --artifact?" In autonomous mode, prefer fresh — re-run design-review.

   - **No artifact found AND `autonomous_mode` = true:** Auto-invoke `design-review` with `{output_mode}` = `"artifact"` and the same `{target_url}` / target context. Load the resulting artifact and proceed.

   - **No artifact found AND `autonomous_mode` = false:** Stop. Tell the user: "Refine-screen mode requires a screen-review artifact. Run `/bmad:bmm:workflows:design-review --artifact` on the target page first, then retry this workflow." Do NOT fall back to asking the user for complaints — the whole point of refine-screen mode is that the diagnostic is automated.

4. **Skip the "ask user what's wrong" prompt in step-01.** The artifact replaces it. The user-context question in step-01 still applies (who uses this, how often) since the artifact doesn't cover that.

5. **In step-03, the Design Ask section is rewritten** to the refine-screen variant — see step-03 for the bounded refinement template.

**Refine-screen rule:** The brief produced in this mode must be BOUNDED. It addresses the artifact's top 3 violations (by severity order) and requires variants for the artifact's edge states. It does NOT redesign the IA, does NOT introduce new components unless required to land one of those top 3, and does NOT propose a "get radical" alternative. Open creative freedom belongs in `fresh-design`. Lower-severity violations (V4+) remain in the artifact for visibility but are not in-scope for the brief unless the user explicitly asks.

**Collapse allowance (one collapse max).** Strict severity ordering can fill all three slots with mechanical token / class-swap violations (hex literal cleanup, `rounded-full` → `rounded-md`, `uppercase tracking-wide` removal, etc.) when a higher-leverage design-requiring violation sits at V4+. The brief is meant to drive design work, not enumerate find-and-replace. Therefore: **if two or more of the top 3 violations are mechanical (no design decision required — concrete class swap fully specified by the policy)**, collapse them into one combined fix labeled `Vx+Vy (combined)` and promote the next design-requiring hard failure into the freed slot.

Constraints on the collapse:
- **At most one collapse per brief.** Never collapse two pairs.
- **The collapsed entry must keep both V-IDs visible** so artifact-to-brief lineage stays traceable: `Vx+Vy (combined)` in the section header, both V-IDs cited in the body.
- **Only mechanical violations are collapsible.** Litmus test: if the Required Correction in the artifact gives an exact class swap or token table that an implementer can apply without a designer thinking, it is mechanical. If the correction requires choosing a layout, sizing, or interaction pattern, it is design-requiring and must keep its own slot.
- **Severity floor.** The promoted violation must be `hard failure` — never promote a `major` or `minor` into the top 3 just to fill the slot. If the next-highest hard failure also turns out to be mechanical, do NOT collapse a second time; emit the brief with only 2 design-requiring fixes and a combined entry, and surface to the user that the artifact's hard-failure list is mostly mechanical.
- **Document the collapse.** In the brief's `mode` / `targeted_changes` frontmatter (per `brief-revision-policy.md` §2), add a `collapse_note:` line stating which V-IDs were collapsed and why.

---

## EXECUTION

Read fully and follow each step file in sequence:

1. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01-gather.md` — gather feature purpose, data shape, user context. When an analytics band is in play, §5c **invokes the `analytics-surface-architect` skill** to select the archetype and capture its full decision object (candidates weighed, drill map, prohibited) — the reasoning, not just the conclusion.
2. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-02-audit-design.md` — audit the current design system / extract tokens / locate reference pages.
3. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03-generate-brief.md` — write the brief to `{output_path}` with full Block A + Block B frontmatter.
3b. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-03b-emit-rationale.md` — **conditional: only when `{has_analytics_band}` is `true`.** Write the analytics presentation rationale (`design-rationale-{target_slug}-{date}.md`) — the human-facing record of HOW the page-mode/band/archetype were chosen. Skipped entirely for no-band features.
4. `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-04-deliver.md` — commit, push, PR, merge to `main`, surface the merged URL. Stages the rationale alongside the brief when one was written. Skippable via `--no-deliver`.
