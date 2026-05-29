---
name: onboard-design-system
description: 'Onboard a brand-new design system for a project AND configure Claude Design to use it as the priority source. Claude-led by default — Claude makes the visual decisions autonomously and surfaces one end-of-run review; pass --collaborative for the propose-and-confirm path. Use when a project has no visual theme yet and the user says "set up a new design system", "onboard a design theme", "configure Claude Design for this project", or "this project has no theme yet". Orchestrates create-design-policy (strategic) + brand-identity (tactical) + a code-shaped token bundle, delivers them to origin/main, then produces the exact intake the claude.ai/design "Set up your design system" form needs.'
main_config: '{project-root}/_bmad/bmm/config.yaml'

# Related workflows
create_design_policy_workflow: '{project-root}/_bmad/bmm/workflows/design/create-design-policy/workflow.md'
design_handoff_workflow: '{project-root}/_bmad/bmm/workflows/design/design-handoff/workflow.md'
design_synthesize_workflow: '{project-root}/_bmad/bmm/workflows/design/design-synthesize/workflow.md'
brand_identity_template: '{project-root}/_bmad/bmm/workflows/design/brand-identity-template.md'
design_standards: '{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md'
delivery_to_main: '{project-root}/_bmad/bmm/workflows/design/shared/delivery-to-main.md'
brief_revision_policy: '{project-root}/_bmad/bmm/workflows/design/shared/brief-revision-policy.md'
intake_template: '{project-root}/_bmad/bmm/workflows/design/onboard-design-system/claude-design-intake-template.md'
---

# Onboard Design System Workflow

**Goal:** Stand up a project's visual identity from nothing AND configure Claude Design to use it. Produce the three-tier source of truth the rest of the design ecosystem depends on (`design-policy.md` → `brand-identity.md` → a code-shaped token bundle), deliver it to `origin/main`, then hand the user the exact inputs the **claude.ai/design "Set up your design system"** form asks for.

**Your Role:** You are a design-systems onboarding lead. You don't just write a policy document — you make sure the design system is (a) articulated strategically, (b) pinned to concrete tokens, (c) expressed as *code* Claude Design can ingest, (d) reachable on `origin/main`, and (e) packaged into a paste-ready intake card. You finish only when the user can sit in front of the Claude Design form and fill every field without guessing.

**Key Insight:** Claude Design's "Set up your design system" is a **web form** (no API). Its strongest inputs are, in order: the **GitHub repo link** ("What works best: code and designs"), a **company name + blurb**, freeform **notes**, and optional **.fig / fonts / assets**. Two facts follow directly:

1. **Code beats prose.** A markdown brand-identity doc underfeeds the form. The system must also exist as renderable code (`tokens.css` + a `sample.html`) so Claude Design can read real values, not descriptions.
2. **The code must be on `origin/main` before the link is pasted.** Claude Design fetches from GitHub. An un-delivered token bundle is invisible to it — this is the exact 2026-05-28 fail-find failure that `delivery-to-main.md` exists to prevent.

This workflow is the only "set up a design system" front door that closes both gaps. `create-design-policy` alone produces a strategic document with nowhere to go; this workflow gives it a destination.

---

## MODE — CLAUDE-LED (DEFAULT) vs COLLABORATIVE

This workflow runs in one of two modes. **`led` is the default.** Pass `--collaborative` (or set `onboard_design_system.mode: collaborative` in `{main_config}`) to switch.

### `led` (default) — Claude drives, you review once

Claude makes every **decision-autonomy** call without asking — palette, typography, density, spacing, radius, status colors, token values, sample components, file placement. It does **not** stop to propose-and-confirm at each step. The whole run produces the full artifact set and surfaces **one consolidated review at the end** (chosen direction + rationale + rendered preview + intake card), with a one-line veto/adjust path. The delivery PR (step 06) is the durable review surface.

**The intent honesty rule — what keeps `led` inside the autonomy boundary.** The one thing Claude must not fabricate from nothing is **intent**: *what the product is, who it serves, the register*. In `led` mode Claude does not ask the user for it — it runs an **internal brainstorm grounded in real project evidence** (project name, `package.json`, README, route/domain names, any existing copy or data models) and commits to the single strongest direction. Two non-negotiables make this safe rather than reckless:

1. **Ground or flag.** The internal brainstorm must cite the concrete signals it reasoned from. If signal is genuinely thin (empty repo, no copy, no domain hints), Claude still commits to a direction but **labels it low-confidence** in the end review and says exactly which assumption it made.
2. **Surface the pick + the runners-up.** The end review names the chosen direction, *why* it won, and the 1-2 directions it beat — so the user can veto with full information. "Commit to one" is a reasoned pick presented for veto, never a silent guess.

### `collaborative` (`--collaborative`) — propose and confirm

The careful path: present the run plan and wait; dispatch to `create-design-policy`'s interactive brainstorm; propose palette/type for approval before writing; show token-surface diffs before applying. Every step gates on user confirmation. Use when the user wants to co-drive the visual direction.

**Per-step behavior is marked `[led]` / `[collaborative]` in each step file.** Where a step is unmarked, behavior is identical in both modes (e.g., delivery-to-main is a safety floor in both).

---

## SOURCE-OF-TRUTH & CLAUDE DESIGN INGEST — CRITICAL

The project-side source of truth this workflow establishes, in precedence order (same hierarchy the downstream `design-synthesize` and `design-handoff` honor):

1. **`brand-identity.md`** (`{planning_artifacts}/brand-identity.md`) — tactical, concrete tokens. The priority anchor downstream workflows inject.
2. **`design-policy.md`** (`{project-root}/docs/design-policy.md`) — strategic "visual constitution".
3. **Code-shaped token bundle** (`{planning_artifacts}/design-system/`) — `tokens.css` + `sample.html` + `README.md`. The artifact Claude Design ingests best.
4. **Shared BMAD design standards** (`shared/design-standards.md`) — generic anti-slop fallback.

**The Claude Design form fields map onto these artifacts as follows** (this mapping IS the deliverable of step 05):

| Claude Design form field | Sourced from |
|---|---|
| Company name + blurb (or design-system name) | `design-policy.md` §product-type + `brand-identity.md` §1 Visual Personality |
| **Link code on GitHub** (frontend-focused subfolder) | repo URL + path to `{planning_artifacts}/design-system/` (and/or the real frontend dir), **after delivery to main** |
| Upload a `.fig` file | user-supplied if they have one; never fabricated |
| Add fonts, logos, assets | `brand-identity.md` §typography + project asset paths |
| Any other notes | `brand-identity.md` (register, density, anti-patterns) + `design-policy.md` anti-references |

---

## PROVENANCE SCOPE — READ BEFORE REVIEWING THIS WORKFLOW

This workflow **produces design-system artifacts, not design briefs.** Therefore:

- **The brief-revision-policy 6 intake checks and 11-field provenance block DO NOT apply here.** They govern `design-handoff` / `design-brief` / `design-response` artifacts consumed by `design-synthesize`. This workflow consumes none of those and emits none of those. A Mode-1 review that flags "missing intake checks" against this workflow is mis-applying the contract — see `brief_revision_policy` §1 scope.
- **What DOES apply:** `brand-identity.md` and `design-policy.md` carry their own lightweight version frontmatter (`version`, `last_updated`). This workflow emits `version: 1` on first creation and is the predecessor for any future `modify-design-policy` / `apply-design-policy-change` run. The token bundle records the `brand-identity` version it was generated from.
- **`delivery-to-main.md` DOES apply** — the token bundle is an artifact whose consumer (Claude Design) reads `origin/main`. Step 06 runs the §3 delivery sequence.

---

## CRITICAL RULES

- **Decide from evidence, surface for veto (`led`) — or discover, don't impose (`collaborative`).** In `led` mode Claude chooses every aesthetic value itself, but each choice must trace to project evidence or to a reasoned, named design rationale — never to a hardcoded default this workflow ships. In `collaborative` mode every value originates from the user or `create-design-policy`'s brainstorm. In both modes this workflow contains **no hardcoded visual preferences** — `led` autonomy is "Claude reasons and decides," not "Claude applies a built-in house style."
- **Never fabricate intent silently.** Decision autonomy (palette, type, tokens) is Claude's to make. Intent autonomy (what the product *is* / who it serves) is not. In `led` mode Claude infers intent from real signals and commits, but must cite the signals and flag low-confidence per the intent honesty rule. Inventing a positioning from nothing and presenting it as fact is the one move this workflow forbids in every mode.
- **Don't blur policy and integration.** Strategic intent lives in `create-design-policy`; this workflow orchestrates it but does not rewrite it. If the user wants to *change* an existing policy, route to `modify-design-policy`, not here.
- **Code must be real and on main.** The token bundle must contain renderable values (no `{placeholder}` tokens shipped) and must be merged to `origin/main` before the GitHub link is surfaced. Halt rather than hand the user a link to a branch-only file.
- **Never fabricate assets the user doesn't have.** `.fig` files, logos, and font files are user-supplied. If absent, the intake card marks them "(none yet — optional)" and proceeds. Do not invent file paths.
- **Greenfield is creation, not extraction.** When the project has no UI, the system is *designed* — in `led` mode via Claude's evidence-grounded internal brainstorm, in `collaborative` mode via `create-design-policy` brainstorm + user intent. When the project has existing UI (brownfield/mixed), extract the implicit language first in both modes.
- **The intake card is the finish line.** The workflow is not done at "files written". It is done when the user has a paste-ready card mapped to every form field and a delivered GitHub link.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle".
- State persists via variables (see below).
- Sequential progression: intake & scope → establish policy → establish brand identity → emit token bundle → assemble Claude Design intake → deliver & guide.
- Steps 02 and 03 may be skipped when the corresponding artifact already exists (the workflow loads it instead). Step 06 delivery is skippable only via `--no-deliver` / `delivery.onboard-design-system: skip`.

### State Variables

- `{mode}` — `led` (default) | `collaborative`. From `--collaborative` flag or `{main_config}` `onboard_design_system.mode`. Governs whether each step decides-and-proceeds or proposes-and-confirms.
- `{direction}` — In `led` mode, the chosen visual direction + the named rationale + the runners-up it beat + the evidence signals it was grounded in + a confidence label (`grounded` | `low-confidence`). Surfaced in the end-of-run review.
- `{project_phase}` — `greenfield` | `brownfield` | `mixed`. Read from `{main_config}`; if absent, inferred in step 01 (no real UI → greenfield).
- `{has_design_policy}` — Whether `docs/design-policy.md` exists ("yes"/"no").
- `{design_policy_path}` — Resolved path to the design policy.
- `{has_brand_identity}` — Whether `{planning_artifacts}/brand-identity.md` exists ("yes"/"no").
- `{brand_identity_path}` — Resolved path to the brand identity doc.
- `{framework}` — Detected frontend framework: `next` | `react` | `svelte` | `vue` | `none` (HTML-only). Determines token-bundle shape.
- `{token_surface}` — Where real tokens live/will live in the project (`tailwind.config.*`, `globals.css`, CSS-in-JS, or "none yet").
- `{bundle_dir}` — `{planning_artifacts}/design-system/` — the code-shaped bundle Claude Design ingests.
- `{repo_url}` — `origin` GitHub URL (resolved from `git remote get-url origin`).
- `{frontend_subfolder}` — The frontend-focused path to recommend in the form's "Link code on GitHub" field.
- `{company_blurb}` — One-paragraph company/design-system blurb for the form's first field.
- `{intake_card_path}` — `{planning_artifacts}/claude-design-intake.md` — the paste-ready output.
- `{delivery_mode}` — `auto` | `skip`. From `{main_config}` `delivery.onboard-design-system` or `--no-deliver`.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `project_name`, `user_name`, `communication_language`, `user_skill_level`
- `project_phase` (default-infer in step 01 if unset)
- `onboard_design_system.mode` (default `led`; `--collaborative` overrides to `collaborative`) → `{mode}`
- `planning_artifacts`, `implementation_artifacts` path roots
- `delivery.onboard-design-system` (default `auto`)

### Begin

Proceed to **step-01-intake-and-scope.md**.
