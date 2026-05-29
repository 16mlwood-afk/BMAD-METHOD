# Step 02 — Establish Design Policy (strategic)

**Goal:** Ensure `docs/design-policy.md` exists and reflects the user's strategic intent. This step **dispatches to `create-design-policy`** — it does not reimplement it. The boundary matters: strategic "what we want to be" is owned by `create-design-policy`; this workflow only orchestrates and consumes it.

---

## 1. If a policy already exists

`{has_design_policy}` = yes → load `{design_policy_path}`, confirm with the user it still reflects current intent, and skip to NEXT. Do **not** edit it here; if it needs changes, that's a `modify-design-policy` run.

## 2. If no policy exists — dispatch create-design-policy

Invoke the `create_design_policy_workflow`. Pass the phase context so it picks the right mode:

- **`{project_phase}` = greenfield** → there is no implicit language to extract. Signal `create-design-policy` to enter its **brainstorming mode** (it presents plausible visual directions with tradeoffs) unless the user already has a clear direction in mind. The user's chosen direction becomes the policy.
- **`{project_phase}` = brownfield | mixed** → `create-design-policy` extracts the implicit visual language from existing pages first, then fills gaps. Do not override what the product already is.

`create-design-policy` writes `docs/design-policy.md` with its own `version: 1` frontmatter. Capture the resulting `{design_policy_path}`.

## 3. Hand-back validation

After `create-design-policy` returns, confirm the policy contains the fields step 05 will need for the Claude Design form:

- A product-type / one-line "what this is" statement (→ company blurb).
- A tone/register descriptor (→ notes field).
- Anti-references / "what it's NOT" (→ notes field).

If any are thin or missing, ask the user the one targeted question needed to fill the gap and append it to the policy via `modify-design-policy` (not by hand-editing here). These three fields are load-bearing for the intake card — a vague policy produces a vague Claude Design system.

## NEXT

→ **step-03-establish-brand-identity.md**
