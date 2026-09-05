# Step 01 — Intake & Scope

**Goal:** Ground the request, detect the project's lifecycle phase, inventory what design-system artifacts already exist, and decide which sub-arcs (policy / brand-identity) this run must create versus load. Halt if intent is ambiguous.

---

## 1. Grounding gate

State **verb + target** from the invocation alone before doing anything else:

- **Verb:** `onboard` (stand up a new design system + configure Claude Design).
- **Target:** the project named in `{main_config}` (`{project_name}`).

If the user's request is actually "change how the existing theme feels" or "this looks too casual", this is the **wrong workflow** — halt and route:

```
This workflow onboards a NEW design system (none exists yet). You appear to
want to CHANGE an existing one. Use `modify-design-policy` instead. If you
genuinely want to start over, re-invoke with "set up a new design system from
scratch" and I'll proceed.
```

Do not infer a new visual direction the user did not ask for. Direction comes from step 02 (create-design-policy), the user, or — for brownfield — the existing code.

## 1b. Orientation — how Claude Design setup works (sets up the whole run)

Before scoping artifacts, fix the controlling fact: the claude.ai/design setup form is a **ONE-TIME seed of a persistent, self-generating workspace** whose **one-shot reusable UI kit is derived from whatever is connected** (see workflow.md → "HOW CLAUDE DESIGN SETUP ACTUALLY WORKS"). The consequent hard rule governs every later step:

- The seed = the **curated, current-UI-free bundle ONLY** (tokens + an idealized component sample). **Never** the live app repo, its `src/` frontend, or current product screens.
- For brownfield/mixed, extracting the existing UI's implicit language informs the **TOKENS/vocabulary** — it is NOT a license to seed the live frontend.

Carry this into every step: "connect the frontend" is NOT a neutral default here; the only thing connected at setup is `{bundle_dir}`.

## 2. Detect project phase

Read `project_phase` from `{main_config}`.

- If set (`greenfield` | `brownfield` | `mixed`), use it.
- If unset, infer: count real UI surfaces (route components / pages with rendered markup, not config). **Zero or near-zero → `greenfield`.** Substantial existing UI → `brownfield`. Some → `mixed`. Record the inference and the evidence; surface it to the user so they can correct it.

`{project_phase}` drives step 03's mode: **greenfield = design the identity; brownfield/mixed = extract the implicit identity first.**

## 3. Inventory existing artifacts

Check, and record path + existence:

- `docs/design-policy.md` → `{has_design_policy}`, `{design_policy_path}`
- `{planning_artifacts}/brand-identity.md` → `{has_brand_identity}`, `{brand_identity_path}`
- Token surface: `tailwind.config.{js,ts}`, `app/globals.css` / `src/**/globals.css`, CSS-in-JS theme, or none → `{token_surface}`
- Frontend framework (from `package.json`): `next` | `react` | `svelte` | `vue` | `none` → `{framework}`
- `git remote get-url origin` → `{repo_url}`. If no remote, flag it now — delivery (step 06) needs one for the GitHub link; the workflow can still produce a local-folder intake path but warn early.

## 4. Decide the run plan

Build the plan from the inventory and present it for confirmation:

| Sub-arc | Run if | Else |
|---|---|---|
| Step 02 — design policy | `{has_design_policy}` = no | load existing, skip creation |
| Step 03 — brand identity | `{has_brand_identity}` = no | load existing, skip creation |
| Step 04 — token bundle | always | regenerate from current brand-identity |
| Step 05 — intake card | always | — |
| Step 06 — deliver & guide | `{delivery_mode}` = auto | warn + emit local-only path |

Present a one-screen summary:

```
Onboarding plan for {project_name} ({project_phase}):
  - Design policy:   [CREATE | load existing at <path>]
  - Brand identity:  [CREATE | load existing at <path>]
  - Token bundle:    EMIT → {planning_artifacts}/design-system/
  - Claude Design intake card: EMIT → {planning_artifacts}/claude-design-intake.md
  - Delivery to main: [AUTO | SKIPPED (--no-deliver)]
  Framework: {framework} · Token surface: {token_surface} · Repo: {repo_url}

Proceed?
```

**`[led]`** — Print the plan as a one-line announcement (not a question) and **proceed immediately**. Do not wait. The user reviews everything once at the end (step 06) and the delivery PR is the durable veto surface.

**`[collaborative]`** — Wait for confirmation (or `--yes` to auto-proceed) before continuing.

## NEXT

→ If creating or loading a policy: **step-02-establish-design-policy.md**. Otherwise carry `{design_policy_path}` forward and go to **step-03-establish-brand-identity.md**.
