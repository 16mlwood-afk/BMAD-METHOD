---
name: design-ingest
description: 'Decoupled, context-bounded INGEST half of design-implement. Takes a Claude Design URL (or a design-synthesize bundle), builds the frame inventory, then FANS OUT one isolated agent per frame to enumerate that frame''s COMPLETE top-level section list + a component×property catalog into a durable manifest on main, with a pre-seeded grid scaffold (every section already a row, status UNVERIFIED). Then PAUSES for a reviewable section-inventory handoff. design-implement consumes the manifest via input_kind: ingest_manifest and skips re-ingest. Use when a bundle is too large to ingest in one design-implement context, or whenever you want the section inventory reviewed before any apply.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
design_implement_workflow: '{project-root}/_bmad/bmm/workflows/implement/design-implement/workflow.md'
design_synthesize_workflow: '{project-root}/_bmad/bmm/workflows/design/design-synthesize/workflow.md'
---

# Design Ingest Workflow

**Goal:** Produce a durable, reviewable **ingest manifest** that enumerates EVERY frame the design delivers AND every top-level section within each frame, with a component×property catalog and a pre-seeded grid scaffold — so `design-implement` can consume a complete contract instead of re-ingesting a large bundle in one overloaded context. This workflow is the front-half of `design-implement` (step-01 ingest) extracted into its own phase, for two reasons: **context** (a ~140KB JSX bundle does not fit one context, so ingest fans out per-frame) and **completeness** (the section inventory becomes a persisted, reviewable artifact with a structural gate, not an in-context list that a narrow scope can silently truncate).

**Your Role:** You are the design cataloguer. You do not implement and you do not judge treatment — you ENUMERATE. Your output is a manifest whose value is its exhaustiveness: every frame, every section of every frame, every styled component within a section. A section you fail to enumerate is a section that ships wrong, because `design-implement`'s grid can only flag a row that exists. Enumeration completeness is the entire job.

**Key Insight — the frame-coverage check is too coarse to catch a missing SECTION inside a present frame.** `design-implement` step-03 §2f verifies frame coverage at frame granularity ("is the drawer built? yes → green"). It is structurally blind to a whole *section* (a Reconciliation block, a SellerSmart-dispatch section) dropped *inside* an otherwise-present frame — the section's inner primitives are shared and match elsewhere, so the component sweep greens out. The fix is not vigilance; it is a structural artifact: this workflow records each frame's complete top-level section list as a REQUIRED, non-empty field, and emits a grid scaffold where every section is already a row. An empty section list for a non-trivial frame is a gating defect here, surfaced before a line of code is touched. This is the same shape as the page-shell gate (PR #2017) and the §13-lookup frame-coverage gate (`56d44fc9`) — a blind spot promoted to a named, structural check after its miss.

---

## SOURCE-OF-TRUTH PRECEDENCE — CRITICAL

This workflow is non-interpretive about treatment, the same way `design-implement` is. It records what the design source contains; it does not decide what is correct.

1. **The design source** — the Claude Design bundle resolved from the URL, or the `design-synthesize` bundle directory. The frames, their sections, and their CSS values are read from here verbatim. This is the canonical input for *what the design contains*.
2. **Project `docs/design-policy.md`** — authoritative ONLY for the one statically-checkable framing rule (page-shell / layout intent, `{design_layout_constraints}`), captured for `design-implement` step-03 §2d. The rest of the policy contract (prohibitions, tone, motion, iconography) is NOT this workflow's to check — it is ceded downstream, same as in `design-implement`.
3. **Workflow defaults** — used only for operational defaults with no design meaning.

**Implication:** Every section and every property recorded in the manifest must trace to (1). This workflow invents nothing — an unreadable frame is recorded `drawn: false`, not inferred; a frame with no enumerable sections is a `frame-completeness` defect, not an empty success.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Steps 01–02 are autonomous. **Step 03 emits the manifest and PAUSES** — the section inventory is a reviewable handoff, not an auto-proceed. This is the one deliberate halt; it is what makes the section inventory auditable before apply.
- The per-frame enumeration in step-02 FANS OUT — one isolated sub-agent per frame — so no single context holds the whole bundle. Each agent returns structured rows; the orchestrator assembles the manifest. This is the context fix.
- State persists via variables (below) and, durably, via the emitted manifest on disk.

### State Variables

- `{input_kind}` — `claude_design_url` | `synthesize_bundle`. Same detection as `design-implement` Input Resolution.
- `{design_url}` / `{bundle_dir}` / `{bundle_manifest}` — per input kind (see Input Resolution).
- `{design_dir}` — Extracted/located bundle directory on disk.
- `{design_frame_inventory}` — The frames the target surface delivers or consumes: the primary frame, the drilled detail drawer(s), and each §13 expand-in-context lookup. Built in step-01 (same derivation as `design-implement` URL.3a — `<script src>` modules + their "… lookups consumed" comments, per-frame banners, lookup→target maps, sibling standalone `<frame>.html`). Each entry: `{ frame, role: primary|drilled-detail|§13-lookup, parent, declared_in, drawn }`.
- `{frame_sections}` — Map of frame → **complete ordered list of top-level sections** that frame renders, each with its heading/copy. Built in step-02 by the per-frame fan-out. **REQUIRED non-empty for every `drawn: true` frame** — the structural completeness gate.
- `{section_catalog}` — Per (frame, section): the component×state×property rows (radius/color/spacing/type), the verbatim copy strings, and the data fields the section reads. Built in step-02.
- `{design_tokens}` — Design system tokens (radii, type scale, colors, spacing).
- `{design_layout_constraints}` — Page-shell intent, sourced authoritatively from `docs/design-policy.md` (see `design-implement` URL.2). Carried for step-03 §2d downstream.
- `{target_slug}` — Kebab-case identifier for the target surface, derived in step-01 from the primary frame. Doubles as the manifest filename key (`design-ingest-<target_slug>.md`) AND the key for resolving this surface's brief in `{implementation_artifacts}` (the supersede check). Same slug semantics as `brief-revision-policy.md` Block A `target_slug` — prefer an exact match to an existing brief's `target_slug` when the surface clearly corresponds.
- `{handoff_supersede_status}` — `active` | `superseded` | `no_brief` | `ambiguous`. Resolved in step-01 by matching `{target_slug}` against the briefs in `{implementation_artifacts}` and reading their `brief_status`. `no_brief` = no matching brief on disk (a raw-URL run where supersede genuinely cannot be known); `ambiguous` = the active-uniqueness invariant (`brief-revision-policy.md` §2.6) is already broken upstream (>1 active). This workflow TOLERATES every value — it never refuses on supersede (ingest is non-destructive); it detects, stamps, and reports.
- `{superseded_by}` — Filename of the active successor brief, captured when `{handoff_supersede_status} == superseded` (from the matched brief's `superseded_by`). Empty otherwise.
- `{source_brief}` — The matched brief's filename + carried provenance (`brief_status`, `change_class`, `last_modified_by` / `last_modified_date`), or `none` on a `no_brief` run. Stamped into the manifest receipt so the supersede status travels with the artifact.
- `{manifest_path}` — Absolute path to the emitted ingest manifest on disk.

### Step Processing Rules

1. **READ COMPLETELY** before acting on any step file.
2. **FOLLOW SEQUENCE** — no skipping.
3. **Steps 01–02 autonomous; step 03 pauses** at the handoff.
4. **SAVE STATE** — carry variables between steps; the manifest is the durable carrier across the pause.
5. **Enumerate exhaustively** — a frame's section list is REQUIRED non-empty; an empty list halts step-02 with the frame-completeness diagnostic.

### Critical Rules

- **Every frame's top-level sections are a REQUIRED field — an empty list for a drawn frame is a gating defect.** This is the named structural gate this workflow exists to add. It fires in step-02 (per frame) and is re-asserted in step-03 before the manifest is emitted.
- **Enumerate by frame → section, never by feature-area.** The failure this workflow fixes was delegating by feature-area with narrow prompts, so a section fell in the seam between two agents' scopes. The fan-out unit is the FRAME; each frame agent is told to enumerate its frame COMPLETELY (every top-level section), not a named subset. There is no "the cost-recon section" prompt — there is "every section of the order drawer."
- **The manifest is a PROPOSAL-CATALOG, not an apply plan.** It records what the design contains and scaffolds the grid; it makes no keep/drop or treatment decisions. Those belong to `design-implement` step-02b and step-03/04. This workflow never edits implementation code.
- **Read source, not screenshots, for values.** Same as `design-implement`: exact values come from JSX inline styles / `<style>` blocks / `tokens.css`, never measured off an image.
- **The pause is non-negotiable.** Step-03 emits the manifest and stops with the next-step command. It does not chain into `design-implement`. The whole point is a reviewable section inventory between ingest and apply.
- **Cope with a superseded handoff — TOLERATE, don't refuse.** A handoff can be handed in after a newer brief has superseded it (the user has the old URL, a colleague passes it on, the work may already be applied). Ingest is the non-destructive half — it catalogs and pauses, it never applies — so it is the right place to surface supersede BEFORE any code moves, and the right reflex is tolerance, NOT the hard refuse that `brief-revision-policy.md` §5 Check 3 imposes on brief *consumers* (`design-synthesize`/`design-artifact-loop`). This workflow therefore: (1) **detects** supersede in step-01 by resolving `{target_slug}` against the briefs in `{implementation_artifacts}`; (2) **builds the manifest anyway** — you stay able to ingest a superseded handoff for review/audit/diff; (3) **stamps** `ingest.supersede_status` + `ingest.superseded_by` into the manifest so the status travels with it; (4) **leads the step-03 pause with the heads-up** — names the successor and notes the work may already be applied — rather than presenting a stale handoff as current truth. The one thing it must NEVER do is silently catalog a superseded handoff as if it were the active design. On a `no_brief` run it says so plainly ("no brief on disk for this slug — can't check supersede status"); it never infers `active`. See `brief-revision-policy.md` §8 (ingest-tolerance).
- **Talk to the user like a person at the three touchpoints — kickoff, frames-found, and the review handoff.** The spec in these files is dense and precise for YOU; what you SAY to the user is plain, first-person, and conversational. Do NOT dump a status box at them, read out `{variable}` names, or recite step numbers. At kickoff, say in your own words what you're about to do and why. When the frames are in, name them the way a colleague would ("the worklist, the order drawer, and six lookups") and flag anything that looks off. At the step-03 pause, hold a real conversation: walk them through what each screen contains, make clear nothing has been applied yet, and genuinely invite them to check the section list before you hand it on. The terse diagnostic boxes in the step files are fallbacks for the failure paths — the success-path narration is human.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve `user_name`, `communication_language`, `implementation_artifacts` path, and `date`. SPEAK OUTPUT in `{communication_language}`.

### Input Resolution

Same two input kinds as `design-implement`:

- **Claude Design artifact URL or paste-prompt** — `{input_kind} = "claude_design_url"`; store `{design_url}` and the `open_file` target. Same three shapes as `design-implement` Input Resolution: the modern `https://claude.ai/design/p/<uuid>?file=<path>` share-link (claude_design/DesignSync MCP), the legacy `https://api.anthropic.com/v1/design/h/...` tar, OR Claude Design's free-text paste-prompt (`Use the claude_design MCP … to import this project:` + a share-link + an `Implement: <file>` line). **Do not call the MCP and implement directly — that bypasses the design-implement safety layer this manifest feeds.** Lift the embedded share-link out as `{design_url}`; resolve the `open_file` target from the `Implement:` line (decoded), else the URL-decoded `?file=` param. Fetch itself is delegated to `design-implement` step-01 URL.1 (URL.1a tar / URL.1b MCP).
- **Local design-synthesize bundle directory** — an absolute path to a directory containing `manifest.yaml` → `{input_kind} = "synthesize_bundle"`, parse `{bundle_dir}` + `{bundle_manifest}`.

Detection: (1) the input CONTAINS the Claude Design paste-signature (a `claude.ai/design/p/` or `api.anthropic.com/v1/design/` URL + an `Implement:` line OR the phrase `claude_design MCP`) → URL, lifting the embedded share-link as `{design_url}`; (2) starts with `http(s)://` → URL; (3) else a filesystem directory containing `manifest.yaml` → bundle; else halt with `"input must be a Claude Design URL/paste-prompt (https://...) or a directory containing manifest.yaml. Got: <input>"`.

For `synthesize_bundle`, the same refusal gates apply as `design-implement` (`synthesis.dev_no_render`, `visual_review.needs_human_review`) — a bundle the synthesizer doesn't trust never becomes an ingest manifest. Halt with the equivalent diagnostic if either fires.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/design-ingest`
- `manifest-schema` = `{installed_path}/manifest-schema.md` — the durable artifact contract this workflow emits.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-ingest/steps/step-01-frame-inventory.md` to begin.
