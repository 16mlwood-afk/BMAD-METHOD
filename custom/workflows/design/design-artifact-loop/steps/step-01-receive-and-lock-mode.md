---
name: 'step-01-receive-and-lock-mode'
description: 'Parse the handoff block, classify the artifact, lock one of four modes, and restate the run context block'
---

# Step 1: Receive Handoff & Lock Mode

**Progress: Step 1 of 4** — Next: Load Sources & Build Evidence (autonomous)

## RULES:

- This is the ONLY conditionally-interactive step. Halt for mode disambiguation only when the mode-detection rules below produce a genuine tie AND `autonomous_mode` is `false`.
- Do NOT present option menus, do NOT ask the user to "tell us what you want." If the handoff block is parseable, parse it and proceed.
- Once `{mode}` is set, it is LOCKED for the run. Mid-run scope expansion requires terminating this run and starting a new one.

---

## SEQUENCE OF INSTRUCTIONS

### 1. Parse the Handoff Block

The handoff block (in the user's message that triggered this workflow, or in the message immediately prior) has these expected components. Extract each:

| Component | How to find it |
|---|---|
| `{repo_url}` | The `https://github.com/ORG/REPO` URL, no trailing `.git` |
| `{artifact_path}` | Repo-relative path on `main`, e.g. `_bmad/bmm/implementation-artifacts/design-brief-foo-2026-05-26.md` |
| `{user_summary}` | The 1–3 line bullet list under "Summary (3 lines):" — convenience only, NOT authoritative |
| `{user_instruction}` | The free-text directive after "Hand off to design-artifact-loop:" (e.g., "Design the UI following the brief exactly") |
| `{screenshot_paths}` | Any image paths/URLs the user attached; empty if none |

**If the handoff block is malformed** (no artifact path resolvable, or the file does not exist on disk), STOP and emit a one-paragraph diagnostic that names the missing field. Do NOT guess paths or fall back to "the most recent brief" — that defeats the artifact-first contract.

### 2. Resolve the Artifact

Convert `{artifact_path}` (repo-relative) to `{artifact_abs_path}` using the current `{project-root}`:

```bash
{artifact_abs_path} = {project-root}/{artifact_path}
```

Read the file fully into `{artifact_content}`. Parse its YAML frontmatter (if any) to determine `{artifact_type}`:

| Frontmatter `type:` field | `{artifact_type}` |
|---|---|
| `design-brief` | `design-brief` |
| `screen-review` | `screen-review` |
| `policy-delta` (rare; emitted by `apply-design-policy-change`) | `policy-delta` |
| anything else, or no frontmatter | infer from filename prefix: `design-brief-*` → `design-brief`; `screen-review-*` → `screen-review`; `design-policy-change-*` → `policy-delta` |

If neither frontmatter nor filename resolves the type, set `{artifact_type}` = `unknown` and surface the file path to the user — do NOT proceed.

### 3. Extract Target Identity

From the artifact's frontmatter and body, extract:

- `{target_label}` — `target:` frontmatter field, or the H1 of the artifact (e.g., "AVASK VAT reclaim")
- `{target_route}` — `target_route:` frontmatter field, or scan the body for the first `/route/path` token under "Route:" or "Target:"
- `{target_slug}` — `target_slug:` frontmatter field if present; otherwise derive from `{target_route}` by stripping leading slash, replacing `/` with `-`, and lowercasing (e.g., `/reclaim/avask` → `reclaim-avask`)

Extract the **context block** fields if the artifact carries them:

- `{user_role}` — "User:" line, "Persona:" line, or first paragraph of a "Who uses this" section
- `{frequency}` — "Frequency:" line or "How often:" mention
- `{stakes}` — "Stakes:" line, "Consequence:" line, or "What's at stake" mention
- `{out_of_scope}` — "Out of scope:" line, "Boundaries:" line, or explicit "Do not change" list

If any field is missing from the artifact, set the variable to the literal string `"(not specified in artifact)"` — do NOT invent a value. The context block in step 3's output will surface the gap.

### 4. Classify Mode

Apply the mode-detection table in order. The FIRST rule that matches wins.

| Rule | Signal | `{mode}` |
|---|---|---|
| 1 | `{artifact_type}` = `policy-delta`, OR `{user_instruction}` contains "policy lift", "raise to policy", "apply policy change" | `policy-lift` |
| 2 | `{user_instruction}` contains "review only", "critique", "audit", "pass/fail", or asks for an assessment without proposed changes | `review-only` |
| 3 | `{artifact_type}` = `screen-review`, OR `{user_instruction}` contains "refine", "iterate", "tighten", "polish", "second pass on", "fix the top issues" | `refine-screen` |
| 4 | `{artifact_type}` = `design-brief` AND `{user_instruction}` is silent on refinement | `design-from-brief` |
| 5 | Tie or no rule matched | see "Tie-break" below |

**Tie-break:**

- If `autonomous_mode` = `true`, default to the first mode listed in this priority: `design-from-brief` → `refine-screen` → `review-only` → `policy-lift`. The first sentence of the output's context block must state the chosen mode AND the priority-default reason.
- If `autonomous_mode` = `false`, halt with this one-paragraph question:

  ```
  Mode is ambiguous from the handoff. The artifact is a {artifact_type}, the instruction says "{user_instruction}", and the rules support both {mode_A} and {mode_B}. Which mode? Reply with one of: design-from-brief, refine-screen, review-only, policy-lift. Mode locks for the rest of the run.
  ```

  Do NOT volunteer a recommendation; the user picks. Once they reply, lock `{mode}` and proceed.

### 5. Lock the Mode

Set `{mode}` to the resolved value. From this point in the run, every later step rejects work that violates the mode's scope (see workflow.md → "Mode scope" matrix).

If the user later asks for work that crosses a "no" cell mid-run, do NOT silently expand. Terminate the current run and instruct the user to restate the handoff under the new mode:

```
That change is out of scope for {mode}. Mode-locked runs do not silently expand. To do {requested-work}, restate the handoff block under {target_mode} and rerun design-artifact-loop.
```

### 6. Restate the Run Context Block

Emit a single short message to the user — this is the ONLY output of step 1. It is not a menu, not a checklist, just a paragraph and a quoted block:

```
Locked mode: {mode}. Target: {target_label} ({target_route}). Source of truth: {artifact_path} ({artifact_type}, {N} lines). Proceeding autonomously.

Context block:
- Mode: {mode}
- Target: {target_label} ({target_route} / slug {target_slug})
- Source artifact: {artifact_path}
- User / role: {user_role}
- Frequency: {frequency}
- Stakes: {stakes}
- Out of scope: {out_of_scope}
- Sister skills available: design-policy-canonical, operational-analytics-band, operational-finance-ui
```

Any field with the value `"(not specified in artifact)"` is rendered exactly as that string so the gap is visible to the user.

### 7. Proceed to Step 2

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-artifact-loop/steps/step-02-load-sources.md`

---

## SUCCESS METRICS

- The handoff block was parsed into all named state variables, or the user was told exactly which field was missing.
- `{artifact_type}` was resolved deterministically — no guessing.
- `{mode}` was set by the first matching rule, or by an explicit user choice if the auto-rules tied.
- The context block was restated in a single short message, and every field is either populated or explicitly marked as missing.

## FAILURE MODES

- Falling back to "the most recent design-brief" when the handoff's artifact path doesn't exist. The artifact-first contract is broken — STOP instead.
- Picking `refine-screen` because there's a screenshot in the handoff, when the actual artifact is a `design-brief` and the instruction is "design the UI." The artifact wins; the screenshot is evidence, not the input.
- Presenting an option menu when `autonomous_mode` is true.
- Silently morphing the mode after step 1. If the user asks for IA changes in `refine-screen`, terminate the run; do not stretch the scope.
