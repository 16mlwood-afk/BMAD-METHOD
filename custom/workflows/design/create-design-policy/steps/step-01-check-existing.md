# Step 1: Check for Existing Design Policy & Brand Identity

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Do NOT skip this step even in autonomous mode — the check determines downstream behavior

## YOUR TASK:

Detect whether the project already has a design policy and/or brand identity document, and determine the correct action.

## CHECK SEQUENCE:

### 1. Check for existing design policy

```bash
ls {project_knowledge}/design-policy.md 2>/dev/null
find {project-root} -name "design-policy.md" -not -path "*node_modules*" -not -path "*.claude/worktrees*" 2>/dev/null | head -5
```

If found:
- Read the file completely
- Set `{has_existing_policy}` = "yes"
- Set `{existing_policy_path}` to the file path
- Present to user: "Found an existing design policy at `{existing_policy_path}`. Would you like to **update** it or **replace** it with a fresh one?"
  - If **update**: proceed to step-02 with the existing policy as context — gather only what's missing or needs changing
  - If **replace**: proceed to step-02 as if no policy exists (but reference the old one for context)

If NOT found:
- Set `{has_existing_policy}` = "no"

### 2. Check for existing brand identity

```bash
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

If found:
- Read the file completely
- Set `{has_brand_identity}` = "yes"
- Set `{brand_identity_path}` to the file path
- Extract relevant context: visual personality, color system, component language, reference pages, hard failures
- This pre-populates many design policy fields — the user only needs to confirm or adjust

If NOT found:
- Set `{has_brand_identity}` = "no"

### 3. Scan for implicit visual signals

Even without explicit policy documents, the codebase communicates visual intent. Scan:

- `tailwind.config.*` — custom colors, fonts, spacing
- `src/app.css` or global CSS — CSS custom properties, theme variables
- `src/lib/utils/status.ts` or equivalent — how status colors are managed
- 2-3 representative pages — what does the app actually look like today?
- Any `design-*.md` or `style-*.md` files in the docs directory

Summarize what you find: "The app currently uses [font], [color palette], [layout pattern]. The implicit visual language is [assessment]."

**CRITICAL INFERENCE GUARD:** Existing UI may provide implementation clues, but must NOT be treated as evidence of intended design policy unless documented elsewhere. The current UI reflects developer decisions, not design intent. Extract factual observations (which font is loaded, which colors are in the config) — do not infer strategic preferences from them. A developer choosing `rounded-lg` everywhere does not mean the project's policy is "rounded corners" — it means nobody wrote a policy yet.

### 4. Present findings

**If existing policy found:**
"You already have a design policy at `{existing_policy_path}`. It covers [sections found]. [Update or replace?]"

**If brand identity found but no policy:**
"No design policy found, but you have a brand identity document at `{brand_identity_path}` that captures your current visual language. I'll use it as a starting point — the design policy will be the strategic layer on top of these tactical tokens."

**If neither found:**
"No design policy or brand identity found. I'll help you create one from scratch. I'll ask about your visual intent — if you're not sure what you want, I can run a brainstorming mode that presents a few plausible directions for your product type."

## NEXT STEP:

After presenting findings, proceed to `{project-root}/_bmad/bmm/workflows/design/create-design-policy/steps/step-02-gather-visual-intent.md`.

In autonomous mode: proceed immediately without waiting for user input.
