# Step 02 — Establish Design Policy (strategic)

**Goal:** Ensure `docs/design-policy.md` exists and reflects the user's strategic intent. This step **dispatches to `create-design-policy`** — it does not reimplement it. The boundary matters: strategic "what we want to be" is owned by `create-design-policy`; this workflow only orchestrates and consumes it.

---

## 1. If a policy already exists

`{has_design_policy}` = yes → load `{design_policy_path}`, confirm with the user it still reflects current intent, and skip to NEXT. Do **not** edit it here; if it needs changes, that's a `modify-design-policy` run.

## 2. If no policy exists — create it

### `[led]` — Claude authors the policy from an evidence-grounded internal brainstorm

Do **not** enter `create-design-policy`'s interactive brainstorm (it gates on user input). Instead:

1. **Gather evidence.** Read `package.json` (name, deps, scripts), README, route/page/directory names, any existing copy, data models / schema, and the project domain. For brownfield/mixed, also audit existing pages for the implicit visual language.
2. **Brainstorm internally.** Reason out 2-3 plausible visual directions with tradeoffs (the same thinking `create-design-policy` would surface as a menu) — but keep it in your head.
3. **Commit to one.** Pick the single strongest direction. Record `{direction}` = {chosen, named rationale, the 1-2 runners-up it beat, the evidence signals it was grounded in, confidence `grounded` | `low-confidence`}. If signal was thin, mark `low-confidence` and name the assumption.
4. **Write the policy.** Author `docs/design-policy.md` directly, following `create-design-policy`'s `design-policy-template.md` structure and emitting `version: 1` frontmatter. The committed direction populates product-type, tone/register, and anti-references.

This is decision autonomy grounded in evidence — not a hardcoded house style. `{direction}` is surfaced for veto in step 06.

### `[collaborative]` — dispatch to create-design-policy

Invoke the `create_design_policy_workflow`. Pass the phase context so it picks the right mode:

- **`{project_phase}` = greenfield** → signal `create-design-policy` to enter its **brainstorming mode** (presents plausible directions with tradeoffs) unless the user already has a clear direction. The user's chosen direction becomes the policy.
- **`{project_phase}` = brownfield | mixed** → `create-design-policy` extracts the implicit visual language from existing pages first, then fills gaps. Do not override what the product already is.

`create-design-policy` writes `docs/design-policy.md` with its own `version: 1` frontmatter. Capture the resulting `{design_policy_path}`.

## 3. Hand-back validation

After `create-design-policy` returns, confirm the policy contains the fields step 05 will need for the Claude Design form:

- A product-type / one-line "what this is" statement (→ company blurb).
- A tone/register descriptor (→ notes field).
- Anti-references / "what it's NOT" (→ notes field).

If any are thin or missing: **`[led]`** fill the gap yourself from the evidence in §2.1 and record it as part of `{direction}` (flag low-confidence if you had to stretch); **`[collaborative]`** ask the user the one targeted question needed and append via `modify-design-policy`. These three fields are load-bearing for the intake card — a vague policy produces a vague Claude Design system.

## NEXT

→ **step-03-establish-brand-identity.md**
