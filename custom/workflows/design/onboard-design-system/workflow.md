---
name: onboard-design-system
description: 'Onboard a brand-new design system for a project AND configure Claude Design to use it as the priority source. Use when a project has no visual theme yet and the user says "set up a new design system", "onboard a design theme", "configure Claude Design for this project", or "this project has no theme yet". Orchestrates create-design-policy (strategic) + brand-identity (tactical) + a code-shaped token bundle, delivers them to origin/main, then produces the exact intake the claude.ai/design "Set up your design system" form needs.'
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

- **Discover, don't impose.** Every aesthetic value originates from the user, from `create-design-policy`'s brainstorm, or from auditing existing code — never from this workflow's defaults. This workflow contains no hardcoded visual preferences.
- **Don't blur policy and integration.** Strategic intent lives in `create-design-policy`; this workflow orchestrates it but does not rewrite it. If the user wants to *change* an existing policy, route to `modify-design-policy`, not here.
- **Code must be real and on main.** The token bundle must contain renderable values (no `{placeholder}` tokens shipped) and must be merged to `origin/main` before the GitHub link is surfaced. Halt rather than hand the user a link to a branch-only file.
- **Never fabricate assets the user doesn't have.** `.fig` files, logos, and font files are user-supplied. If absent, the intake card marks them "(none yet — optional)" and proceeds. Do not invent file paths.
- **Greenfield is creation, not extraction.** When the project has no UI, the system is *designed* (via `create-design-policy` brainstorm + user intent), not extracted. When the project has existing UI (brownfield/mixed), extract the implicit language first.
- **The intake card is the finish line.** The workflow is not done at "files written". It is done when the user has a paste-ready card mapped to every form field and a delivered GitHub link.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle".
- State persists via variables (see below).
- Sequential progression: intake & scope → establish policy → establish brand identity → emit token bundle → assemble Claude Design intake → deliver & guide.
- Steps 02 and 03 may be skipped when the corresponding artifact already exists (the workflow loads it instead). Step 06 delivery is skippable only via `--no-deliver` / `delivery.onboard-design-system: skip`.

### State Variables

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
- `planning_artifacts`, `implementation_artifacts` path roots
- `delivery.onboard-design-system` (default `auto`)

### Begin

Proceed to **step-01-intake-and-scope.md**.
